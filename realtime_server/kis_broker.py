"""
한국투자증권 실시간 WebSocket 브로커

흐름: KIS WS 서버 → 파싱 → FastAPI WS → Vue 클라이언트

실행 (모의투자):
  uvicorn realtime_server.kis_broker:app --host 0.0.0.0 --port 8002 --reload

backend/.env 에 추가 필요:
  KIS_APP_KEY=발급받은앱키
  KIS_APP_SECRET=발급받은앱시크릿
  KIS_MOCK=true   # 모의투자면 true, 실전이면 false
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Set

import httpx
import websockets
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(Path(__file__).parent.parent / 'backend' / '.env')

KIS_APP_KEY    = os.getenv('KIS_APP_KEY', '')
KIS_APP_SECRET = os.getenv('KIS_APP_SECRET', '')
IS_MOCK        = os.getenv('KIS_MOCK', 'true').lower() == 'true'

# 모의투자 / 실전 주소 분기
if IS_MOCK:
    KIS_WS_URL   = 'ws://ops.koreainvestment.com:31000'
    KIS_REST_URL = 'https://openapivts.koreainvestment.com:29443'
else:
    KIS_WS_URL   = 'ws://ops.koreainvestment.com:21000'
    KIS_REST_URL = 'https://openapi.koreainvestment.com:9443'

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

# symbol → 연결된 Vue 클라이언트 집합
_clients: Dict[str, Set[WebSocket]] = {}
# symbol → 최신 데이터 캐시 {TR_ID: parsed_dict}
_latest:  Dict[str, Dict[str, dict]] = {}
# symbol → KIS 구독 asyncio Task
_tasks:   Dict[str, asyncio.Task] = {}
# 승인키 (한 번 발급 후 재사용)
_apv_key: str = ''


# ── 승인키 발급 ──────────────────────────────────────────────────────
async def _get_approval_key() -> str:
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f'{KIS_REST_URL}/oauth2/Approval',
            json={
                'grant_type': 'client_credentials',
                'appkey':     KIS_APP_KEY,
                'secretkey':  KIS_APP_SECRET,
            },
            timeout=10,
        )
        res.raise_for_status()
        return res.json()['approval_key']


# ── 데이터 파서 ──────────────────────────────────────────────────────
def _parse_trade(body: str) -> dict:
    """H0STCNT0 실시간 체결가"""
    f = body.split('^')
    return {
        'type':        'trade',
        'symbol':      f[0],
        'time':        f[1],
        'price':       int(f[2]),
        'sign':        f[3],          # 1상한 2상승 3보합 4하한 5하락
        'change':      int(f[4]),
        'change_rate': float(f[5]),
        'open':        int(f[7]),
        'high':        int(f[8]),
        'low':         int(f[9]),
        'ask1':        int(f[10]),
        'bid1':        int(f[11]),
        'volume':      int(f[12]),    # 체결량
        'acc_volume':  int(f[13]),    # 누적거래량
        'strength':    float(f[18]),  # 체결강도
        'trade_type':  f[21],         # 1:매수체결 5:매도체결
    }


def _parse_orderbook(body: str) -> dict:
    """H0STASP0 실시간 10호가"""
    f = body.split('^')
    asks, bids = [], []
    for i in range(10):
        asks.append({'price': int(f[3 + i]),  'qty': int(f[23 + i])})
        bids.append({'price': int(f[13 + i]), 'qty': int(f[33 + i])})
    return {
        'type':          'orderbook',
        'symbol':        f[0],
        'time':          f[1],
        'asks':          asks,           # index 0 = 1위(최우선 매도 / 가장 낮은 매도가)
        'bids':          bids,           # index 0 = 1위(최우선 매수 / 가장 높은 매수가)
        'total_ask_qty': int(f[43]),
        'total_bid_qty': int(f[44]),
    }


# ── KIS WebSocket 구독 메시지 ────────────────────────────────────────
def _sub_msg(approval_key: str, tr_id: str, symbol: str) -> str:
    return json.dumps({
        'header': {
            'approval_key': approval_key,
            'custtype':     'P',
            'tr_type':      '1',      # 1:구독 2:해제
            'content-type': 'utf-8',
        },
        'body': {'input': {'tr_id': tr_id, 'tr_key': symbol}},
    })


# ── KIS WS 구독 태스크 (자동 재연결) ─────────────────────────────────
async def _kis_task(symbol: str, approval_key: str):
    while True:
        try:
            async for ws in websockets.connect(
                KIS_WS_URL,
                ping_interval=None,   # KIS 자체 PINGPONG 사용
            ):
                try:
                    # 체결가 + 호가 구독
                    await ws.send(_sub_msg(approval_key, 'H0STCNT0', symbol))
                    await ws.send(_sub_msg(approval_key, 'H0STASP0', symbol))

                    async for raw in ws:
                        # ① JSON 제어 메시지 (구독확인, PINGPONG 등)
                        try:
                            ctrl = json.loads(raw)
                            tr_id = ctrl.get('header', {}).get('tr_id', '')
                            if tr_id == 'PINGPONG':
                                await ws.send(raw)   # pong 응답
                            continue
                        except (json.JSONDecodeError, TypeError, AttributeError):
                            pass

                        # ② 실시간 파이프 데이터: "flag|TR_ID|count|body"
                        parts = raw.split('|')
                        if len(parts) < 4:
                            continue
                        flag, tr_id, body = parts[0], parts[1], parts[3]
                        if flag == '1':
                            continue   # 암호화 데이터 스킵 (개인계정은 보통 0)

                        try:
                            if tr_id == 'H0STCNT0':
                                parsed = _parse_trade(body)
                            elif tr_id == 'H0STASP0':
                                parsed = _parse_orderbook(body)
                            else:
                                continue

                            _latest.setdefault(symbol, {})[tr_id] = parsed
                            await _broadcast(symbol, parsed)
                        except Exception:
                            pass

                except websockets.ConnectionClosed:
                    await asyncio.sleep(3)

        except Exception:
            await asyncio.sleep(5)


async def _broadcast(symbol: str, data: dict):
    if symbol not in _clients:
        return
    dead: Set[WebSocket] = set()
    msg = json.dumps(data, ensure_ascii=False)
    for client in list(_clients[symbol]):
        try:
            await client.send_text(msg)
        except Exception:
            dead.add(client)
    _clients[symbol] -= dead


async def _ensure_subscription(symbol: str):
    global _apv_key
    task = _tasks.get(symbol)
    if task and not task.done():
        return
    if not KIS_APP_KEY:
        return   # 키 미설정 시 구독 생략
    if not _apv_key:
        _apv_key = await _get_approval_key()
    _tasks[symbol] = asyncio.create_task(_kis_task(symbol, _apv_key))


# ── FastAPI WebSocket 엔드포인트 ─────────────────────────────────────
@app.websocket('/ws/{symbol}')
async def ws_endpoint(websocket: WebSocket, symbol: str):
    await websocket.accept()
    _clients.setdefault(symbol, set()).add(websocket)

    await _ensure_subscription(symbol)

    # 캐시된 최신 데이터 즉시 전송 (페이지 새로고침 직후에도 즉시 표시)
    for cached in _latest.get(symbol, {}).values():
        try:
            await websocket.send_text(json.dumps(cached, ensure_ascii=False))
        except Exception:
            pass

    try:
        while True:
            await websocket.receive_text()   # 클라이언트 ping 수신 (keep-alive)
    except WebSocketDisconnect:
        _clients[symbol].discard(websocket)


@app.get('/health')
def health():
    return {
        'status': 'ok',
        'mock':   IS_MOCK,
        'subscribed': list(_tasks.keys()),
        'connected_clients': {k: len(v) for k, v in _clients.items()},
    }
