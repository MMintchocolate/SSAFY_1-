import html
import FinanceDataReader as fdr
import httpx
import io
import math
import numpy as np
import re
import yfinance as yf
from datetime import datetime, timedelta
from googleapiclient.discovery import build

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import WatchlistItem

VALID_PERIODS = {'1mo', '3mo', '6mo', '1y', '2y', '5y'}
PERIOD_DAYS   = {'1mo': 30, '3mo': 90, '6mo': 180, '1y': 365, '2y': 730, '5y': 1825}

_vol_top_df = None
_vol_top_ts = None
_index_df   = None
_index_ts   = None


def _parse_kis_symbol(symbol: str):
    """
    '005930.KS' → ('005930', 'KOSPI')
    '035420.KQ' → ('035420', 'KOSDAQ')
    '005930'    → ('005930', 'KOSPI')
    그 외        → None
    """
    m = re.match(r'^(\d{6})\.(KS|KQ)$', symbol, re.I)
    if m:
        return m.group(1), 'KOSPI' if m.group(2).upper() == 'KS' else 'KOSDAQ'
    if re.match(r'^\d{6}$', symbol):
        return symbol, 'KOSPI'
    return None


# ── KRX 종목 목록 캐시 ────────────────────────────────────────────────
_krx_df = None


def _get_krx_df():
    global _krx_df
    if _krx_df is not None:
        return _krx_df
    try:
        df = fdr.StockListing('KRX')[['Code', 'Name', 'Market', 'Marcap']].dropna(subset=['Code', 'Name'])
        df['Code'] = df['Code'].astype(str).str.zfill(6)
        _krx_df = df
        return _krx_df
    except Exception:
        import traceback; traceback.print_exc()
        return None


def _krx_row(ticker: str):
    df = _get_krx_df()
    if df is None:
        return None
    rows = df[df['Code'] == ticker]
    return rows.iloc[0] if not rows.empty else None

def _krx_name(ticker: str) -> str:
    row = _krx_row(ticker)
    return row['Name'] if row is not None else ticker

def _krx_marcap(ticker: str):
    row = _krx_row(ticker)
    if row is None:
        return None
    v = row.get('Marcap')
    return int(v) if v and v == v else None  # NaN 체크


def _search_krx(q: str) -> list:
    df = _get_krx_df()
    if df is None:
        return []
    matches = df[df['Name'].str.contains(q, na=False)].head(10)
    results = []
    for _, row in matches.iterrows():
        suffix = '.KS' if row['Market'] == 'KOSPI' else '.KQ'
        results.append({
            'symbol':   f"{row['Code']}{suffix}",
            'name':     row['Name'],
            'type':     'EQUITY',
            'exchange': row['Market'],
        })
    return results


# ── 한글 종목명 → 미국 주식 티커 딕셔너리 ────────────────────────────
KR_TO_TICKER: dict[str, str] = {
    # ── 빅테크 ──────────────────────────────────────────────────────
    '애플': 'AAPL', '마이크로소프트': 'MSFT', '구글': 'GOOGL', '알파벳': 'GOOGL',
    '아마존': 'AMZN', '테슬라': 'TSLA', '메타': 'META', '페이스북': 'META',
    '엔비디아': 'NVDA', '넷플릭스': 'NFLX',
    # ── 반도체 ──────────────────────────────────────────────────────
    'AMD': 'AMD', '에이엠디': 'AMD', '인텔': 'INTC', 'TSMC': 'TSM', '퀄컴': 'QCOM',
    '마이크론': 'MU', '브로드컴': 'AVGO', '텍사스인스트루먼트': 'TXN', '어플라이드머티리얼즈': 'AMAT',
    'ASML': 'ASML', '아스엠엘': 'ASML', '람리서치': 'LRCX', 'KLA': 'KLAC',
    # ── 자동차 ──────────────────────────────────────────────────────
    '포드': 'F', 'GM': 'GM', '제너럴모터스': 'GM', '리비안': 'RIVN',
    '루시드': 'LCID', '도요타': 'TM', '혼다': 'HMC', '폭스바겐': 'VWAGY',
    '페라리': 'RACE', '스텔란티스': 'STLA',
    # ── 금융 ────────────────────────────────────────────────────────
    'JP모건': 'JPM', '제이피모건': 'JPM', '골드만삭스': 'GS', '뱅크오브아메리카': 'BAC',
    '씨티그룹': 'C', '웰스파고': 'WFC', '모건스탠리': 'MS', '블랙록': 'BLK',
    '비자': 'V', '마스터카드': 'MA', '페이팔': 'PYPL', '스퀘어': 'SQ', '블록': 'SQ',
    '찰스슈왑': 'SCHW', '아메리칸익스프레스': 'AXP',
    # ── 소비재 / 유통 ────────────────────────────────────────────────
    '코카콜라': 'KO', '펩시': 'PEP', '펩시코': 'PEP', '맥도날드': 'MCD',
    '스타벅스': 'SBUX', '나이키': 'NKE', '월마트': 'WMT', '코스트코': 'COST',
    '타겟': 'TGT', '홈디포': 'HD', '나이키': 'NKE', '룰루레몬': 'LULU',
    '에어비앤비': 'ABNB', '부킹홀딩스': 'BKNG', '익스피디아': 'EXPE',
    # ── 헬스케어 / 제약 ──────────────────────────────────────────────
    '존슨앤존슨': 'JNJ', '화이자': 'PFE', '모더나': 'MRNA', '애브비': 'ABBV',
    '머크': 'MRK', '일라이릴리': 'LLY', '노보노디스크': 'NVO', '유나이티드헬스': 'UNH',
    '애브비': 'ABBV', '암젠': 'AMGN', '길리어드': 'GILD', '리제네론': 'REGN',
    # ── 에너지 ──────────────────────────────────────────────────────
    '엑손모빌': 'XOM', '셰브론': 'CVX', '코노코필립스': 'COP',
    '옥시덴탈': 'OXY', '슐럼버거': 'SLB',
    # ── 통신 ────────────────────────────────────────────────────────
    '버라이즌': 'VZ', 'AT&T': 'T', '티모바일': 'TMUS', '컴캐스트': 'CMCSA',
    '월트디즈니': 'DIS', '디즈니': 'DIS', '워너브라더스': 'WBD', '파라마운트': 'PARA',
    # ── 소프트웨어 / 클라우드 ────────────────────────────────────────
    '세일즈포스': 'CRM', '어도비': 'ADBE', '오라클': 'ORCL', '인튜이트': 'INTU',
    '서비스나우': 'NOW', '워크데이': 'WDAY', '스노우플레이크': 'SNOW',
    '팔란티어': 'PLTR', '코인베이스': 'COIN', '클라우드플레어': 'NET',
    '줌': 'ZM', '줌비디오': 'ZM', '슬랙': 'CRM', '데이터독': 'DDOG',
    '몽고디비': 'MDB', '유아이패스': 'PATH', '허브스팟': 'HUBS',
    # ── 항공 / 여행 ──────────────────────────────────────────────────
    '델타항공': 'DAL', '유나이티드항공': 'UAL', '아메리칸항공': 'AAL',
    '사우스웨스트항공': 'LUV', '보잉': 'BA', '에어버스': 'EADSY',
    # ── ETF ─────────────────────────────────────────────────────────
    'QQQ': 'QQQ', 'SPY': 'SPY', 'VOO': 'VOO', 'TQQQ': 'TQQQ',
    '나스닥ETF': 'QQQ', 'S&P500': 'SPY', '레버리지나스닥': 'TQQQ',
    # ── 기타 ────────────────────────────────────────────────────────
    '버크셔해서웨이': 'BRK-B', '버핏': 'BRK-B', '스페이스엑스': 'TSLA',
    '우버': 'UBER', '리프트': 'LYFT', '도어대시': 'DASH', '인스타카트': 'CART',
    '로블록스': 'RBLX', '유니티': 'U', '일렉트로닉아츠': 'EA', '액티비전': 'MSFT',
    '넥스트에라에너지': 'NEE', '듀크에너지': 'DUK',
    '스트라이프': 'HOOD', '로빈후드': 'HOOD', '어펌': 'AFRM', '클라나': 'KLAR',
}


def _search_us(q: str) -> list:
    """yfinance로 영문 종목명/티커 검색"""
    quotes = yf.Search(q).quotes
    results = []
    for item in quotes[:10]:
        symbol = item.get('symbol', '')
        if not symbol:
            continue
        results.append({
            'symbol':   symbol,
            'name':     item.get('longname') or item.get('shortname', symbol),
            'type':     item.get('quoteType', 'EQUITY'),
            'exchange': item.get('exchange', ''),
        })
    return results


def _gemini_translate(q: str) -> str:
    """한글 종목명 → 영어 회사명 (Gemini 폴백)"""
    gms_key = getattr(settings, 'GMS_KEY', '')
    gms_model = getattr(settings, 'GMS_MODEL', 'gemini-2.5-flash')
    if not gms_key:
        return ''
    try:
        url = f'https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com/v1beta/models/{gms_model}:generateContent'
        res = httpx.post(url,
            headers={'Content-Type': 'application/json', 'x-goog-api-key': gms_key},
            json={'contents': [{'parts': [{'text':
                f'다음 한글 주식/회사 이름의 영어 이름만 반환하세요. 설명 없이 영어 이름 하나만: {q}'
            }]}]},
            timeout=5,
        )
        return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception:
        return ''


def _has_korean(text: str) -> bool:
    return bool(re.search(r'[가-힣ᄀ-ᇿ㄰-㆏]', text))


# ── Views ─────────────────────────────────────────────────────────────
@api_view(['GET'])
def search_stocks(request):
    q = request.query_params.get('q', '').strip()
    if not q:
        return Response([])
    try:
        if not _has_korean(q):
            return Response(_search_us(q))

        # 1) KRX 한국 주식 검색
        krx_results = _search_krx(q)
        if krx_results:
            return Response(krx_results)

        # 2) 딕셔너리 매핑 (해외 주식 한글명)
        ticker = KR_TO_TICKER.get(q)
        if ticker:
            return Response(_search_us(ticker))

        # 3) Gemini 번역 → yfinance 검색
        en_name = _gemini_translate(q)
        if en_name:
            return Response(_search_us(en_name))

        return Response([])
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def stock_detail(request, symbol):
    # ── 한국 주식: FinanceDataReader ─────────────────────────────────
    kis = _parse_kis_symbol(symbol)
    if kis:
        ticker, market = kis
        try:
            start = (datetime.today() - timedelta(days=365)).strftime('%Y-%m-%d')
            df = fdr.DataReader(ticker, start)
            if df.empty:
                raise ValueError('시세 데이터 없음')
            row    = df.iloc[-1]
            close  = int(row['Close'])
            chg_rt = float(row['Change'])
            prev   = round(close / (1 + chg_rt)) if chg_rt != -1 else close
            change = close - prev

            return Response({
                'symbol':     symbol.upper(),
                'name':       _krx_name(ticker),
                'price':      close,
                'prev_close': prev,
                'change':     change,
                'change_pct': round(chg_rt * 100, 2),
                'currency':   'KRW',
                'exchange':   market,
                'market_cap': _krx_marcap(ticker),
                'w52_high':   int(df['High'].max()),
                'w52_low':    int(df['Low'].min()),
                'avg_volume': int(df['Volume'].mean()),
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ── 미국 주식: yfinance ──────────────────────────────────────────
    try:
        obj     = yf.Ticker(symbol.upper())
        info    = obj.info
        fast    = obj.fast_info
        last    = fast.last_price
        prev    = fast.previous_close
        chg     = (last - prev) if (last is not None and prev) else None
        chg_pct = (chg / prev * 100) if (chg is not None and prev) else None
        return Response({
            'symbol':     symbol.upper(),
            'name':       info.get('longName') or info.get('shortName', symbol),
            'price':      last,
            'prev_close': prev,
            'change':     round(chg, 4) if chg is not None else None,
            'change_pct': round(chg_pct, 2) if chg_pct is not None else None,
            'market_cap': info.get('marketCap'),
            'currency':   info.get('currency', 'USD'),
            'exchange':   info.get('exchange', ''),
            'sector':     info.get('sector', ''),
            'industry':   info.get('industry', ''),
            'w52_high':   fast.year_high,
            'w52_low':    fast.year_low,
            'avg_volume': fast.three_month_average_volume,
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def stock_history(request, symbol):
    period = request.query_params.get('period', '3mo')
    if period not in VALID_PERIODS:
        period = '3mo'

    # ── 한국 주식: FinanceDataReader ─────────────────────────────────
    kis = _parse_kis_symbol(symbol)
    if kis:
        ticker, _ = kis
        try:
            start = (datetime.today() - timedelta(days=PERIOD_DAYS[period])).strftime('%Y-%m-%d')
            end   = datetime.today().strftime('%Y-%m-%d')
            hist  = fdr.DataReader(ticker, start, end)
            data  = [
                {
                    'date':   idx.strftime('%Y-%m-%d'),
                    'close':  int(row['Close']),
                    'open':   int(row['Open']),
                    'high':   int(row['High']),
                    'low':    int(row['Low']),
                    'volume': int(row['Volume']),
                }
                for idx, row in hist.iterrows()
            ]
            return Response(data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ── 미국 주식: yfinance ──────────────────────────────────────────
    try:
        hist = yf.Ticker(symbol.upper()).history(period=period)
        data = [
            {
                'date':   str(idx.date()),
                'close':  round(float(row['Close']), 4),
                'open':   round(float(row['Open']), 4),
                'high':   round(float(row['High']), 4),
                'low':    round(float(row['Low']), 4),
                'volume': int(row['Volume']),
            }
            for idx, row in hist.iterrows()
        ]
        return Response(data)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stock_indicators(request, symbol):
    """MA50/200, RSI14, MACD(12,26,9), Bollinger(20) 계산"""
    def safe(v):
        try:
            f = float(v)
            return None if (math.isnan(f) or math.isinf(f)) else round(f, 4)
        except Exception:
            return None

    try:
        kis = _parse_kis_symbol(symbol)
        if kis:
            ticker, _ = kis
            start = (datetime.today() - timedelta(days=350)).strftime('%Y-%m-%d')
            df = fdr.DataReader(ticker, start)
            closes = df['Close'].astype(float)
        else:
            closes = yf.Ticker(symbol.upper()).history(period='2y')['Close'].astype(float)

        if len(closes) < 26:
            raise ValueError(f'데이터 부족 ({len(closes)}일)')

        # ── MA ────────────────────────────────────────────────────
        ma50_s  = closes.rolling(50).mean()
        ma200_s = closes.rolling(200).mean()
        ma50    = safe(ma50_s.iloc[-1])
        ma200   = safe(ma200_s.iloc[-1])

        cross = None
        if len(closes) >= 2:
            vals = [safe(ma50_s.iloc[-2]), safe(ma50_s.iloc[-1]),
                    safe(ma200_s.iloc[-2]), safe(ma200_s.iloc[-1])]
            if all(v is not None for v in vals):
                p50, c50, p200, c200 = vals
                if p50 <= p200 and c50 > c200:
                    cross = 'golden'
                elif p50 >= p200 and c50 < c200:
                    cross = 'dead'

        # ── RSI(14) ───────────────────────────────────────────────
        delta = closes.diff()
        gain  = delta.clip(lower=0).rolling(14).mean()
        loss  = (-delta.clip(upper=0)).rolling(14).mean()
        rsi   = safe((100 - (100 / (1 + gain / loss))).iloc[-1])

        # ── MACD(12, 26, 9) ───────────────────────────────────────
        ema12       = closes.ewm(span=12, adjust=False).mean()
        ema26       = closes.ewm(span=26, adjust=False).mean()
        macd_line   = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram   = macd_line - signal_line

        macd_cross = None
        if len(closes) >= 2:
            pm, cm = safe(macd_line.iloc[-2]),   safe(macd_line.iloc[-1])
            ps, cs = safe(signal_line.iloc[-2]), safe(signal_line.iloc[-1])
            if all(v is not None for v in [pm, cm, ps, cs]):
                if pm <= ps and cm > cs:
                    macd_cross = 'buy'
                elif pm >= ps and cm < cs:
                    macd_cross = 'sell'

        # ── Bollinger(20, 2) ──────────────────────────────────────
        bb_mid   = closes.rolling(20).mean()
        bb_std   = closes.rolling(20).std()
        bb_upper = (bb_mid + 2 * bb_std).iloc[-1]
        bb_lower = (bb_mid - 2 * bb_std).iloc[-1]
        bb_mid_v = bb_mid.iloc[-1]
        price    = float(closes.iloc[-1])
        bb_range = float(bb_upper) - float(bb_lower)
        bb_pos   = round((price - float(bb_lower)) / bb_range * 100, 1) if bb_range > 0 else 50

        return Response({
            'symbol': symbol.upper(),
            'price':  safe(price),
            'ma': {
                'ma50':     ma50,
                'ma200':    ma200,
                'cross':    cross,
                'above200': ma50 is not None and ma200 is not None and ma50 > ma200,
            },
            'rsi': {
                'value':  rsi,
                'signal': ('oversold' if rsi < 30 else 'overbought' if rsi > 70 else 'neutral') if rsi else 'neutral',
            },
            'macd': {
                'macd':      safe(macd_line.iloc[-1]),
                'signal':    safe(signal_line.iloc[-1]),
                'histogram': safe(histogram.iloc[-1]),
                'cross':     macd_cross,
            },
            'bollinger': {
                'upper':    safe(bb_upper),
                'middle':   safe(bb_mid_v),
                'lower':    safe(bb_lower),
                'position': bb_pos,
                'signal':   'buy' if price <= float(bb_lower) else ('sell' if price >= float(bb_upper) else 'neutral'),
            },
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


_GOLD_PERIOD_DAYS = {'1D': 1, '1W': 7, '1M': 30, '3M': 90, '6M': 180, '1Y': 365}
_GOLD_URL = 'https://www.koreagoldx.co.kr/api/price/chart/list'
_GOLD_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Referer': 'https://www.koreagoldx.co.kr/',
}
# API 응답 필드 → 프론트 키 매핑
_METAL_FIELD = {
    'pure':   ('s_pure',   'p_pure'),   # 순금 24K  매도/매입
    '18k':    ('s_18k',    'p_18k'),
    '14k':    ('s_14k',    'p_14k'),
    'white':  ('s_white',  'p_white'),  # 백금
    'silver': ('s_silver', 'p_silver'), # 은
}


@api_view(['GET'])
def index_data(request):
    """코스피/코스닥 지수 현황 + 30일 히스토리"""
    global _index_df, _index_ts

    now = datetime.now()
    if _index_df is None or _index_ts is None or (now - _index_ts).total_seconds() > 300:
        try:
            start = (datetime.today() - timedelta(days=45)).strftime('%Y-%m-%d')
            _index_df = {
                'kospi':  fdr.DataReader('KS11',  start),
                'kosdaq': fdr.DataReader('KQ11', start),
            }
            _index_ts = now
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def df_to_payload(df):
        if df is None or df.empty:
            return None
        close_col = 'Close' if 'Close' in df.columns else df.columns[0]
        latest    = float(df[close_col].iloc[-1])
        prev      = float(df[close_col].iloc[-2]) if len(df) > 1 else latest
        change    = latest - prev
        history   = [
            {'date': str(idx.date()), 'close': round(float(row[close_col]), 2)}
            for idx, row in df.iterrows()
        ]
        return {
            'value':      round(latest, 2),
            'change':     round(change, 2),
            'change_pct': round(change / prev * 100, 2) if prev else 0,
            'history':    history[-30:],
        }

    return Response({
        'kospi':  df_to_payload(_index_df['kospi']),
        'kosdaq': df_to_payload(_index_df['kosdaq']),
    })


@api_view(['GET'])
def market_movers(request):
    """홈 화면: 시가총액·상승·하락 TOP5 한 번에"""
    global _vol_top_df, _vol_top_ts

    now = datetime.now()
    if _vol_top_df is None or _vol_top_ts is None or (now - _vol_top_ts).total_seconds() > 1800:
        try:
            _vol_top_df = fdr.StockListing('KRX')
            _vol_top_ts = now
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    df = _vol_top_df
    chg_col = next((c for c in ['ChagesRatio', 'ChangesRatio'] if c in df.columns), None)
    marcap_col = 'Marcap' if 'Marcap' in df.columns else None

    def sf(v):
        try:
            f = float(v)
            return None if (f != f) or math.isinf(f) else f
        except (TypeError, ValueError):
            return None

    def to_dict(row):
        code   = str(row.get('Code', '')).zfill(6)
        mkt    = str(row.get('Market', ''))
        suffix = '.KS' if 'KOSPI' in mkt.upper() else '.KQ'
        marcap = row.get('Marcap')
        return {
            'symbol':     f"{code}{suffix}",
            'name':       str(row.get('Name', '')),
            'close':      sf(row.get('Close')),
            'change_pct': sf(row.get(chg_col)) if chg_col else None,
            'marcap':     int(marcap) if marcap is not None and not math.isnan(float(marcap)) else 0,
        }

    result = {'marcap': [], 'up': [], 'down': []}

    if marcap_col:
        mdf = df[df[marcap_col].notna() & (df[marcap_col] > 0)]
        result['marcap'] = [to_dict(r) for _, r in mdf.sort_values(marcap_col, ascending=False).head(5).iterrows()]

    if chg_col:
        cdf = df[df[chg_col].notna()]
        result['up']   = [to_dict(r) for _, r in cdf.sort_values(chg_col, ascending=False).head(5).iterrows()]
        result['down'] = [to_dict(r) for _, r in cdf.sort_values(chg_col, ascending=True).head(5).iterrows()]

    return Response(result)


@api_view(['GET'])
def volume_top(request):
    """거래량 상위 종목 (KRX 전체, 최신 거래일 기준)"""
    global _vol_top_df, _vol_top_ts
    limit = min(int(request.query_params.get('limit', 20)), 50)

    now = datetime.now()
    if _vol_top_df is None or _vol_top_ts is None or (now - _vol_top_ts).total_seconds() > 1800:
        try:
            _vol_top_df = fdr.StockListing('KRX')
            _vol_top_ts = now
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    df = _vol_top_df
    vol_col = next((c for c in ['Volume', 'volume'] if c in df.columns), None)
    if vol_col is None:
        return Response({'error': '거래량 데이터를 지원하지 않습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    df = df[df[vol_col].notna() & (df[vol_col] > 0)]
    df = df.sort_values(vol_col, ascending=False).head(limit)

    def sf(v):
        try:
            f = float(v)
            return None if (f != f) or math.isinf(f) else f
        except (TypeError, ValueError):
            return None

    results = []
    for _, row in df.iterrows():
        code = str(row.get('Code', row.get('code', ''))).zfill(6)
        mkt  = str(row.get('Market', row.get('market', '')))
        suffix = '.KS' if 'KOSPI' in mkt.upper() else '.KQ'
        chg_ratio = sf(row.get('ChagesRatio', row.get('ChangesRatio', row.get('change_rate'))))
        results.append({
            'symbol':     f"{code}{suffix}",
            'code':       code,
            'name':       str(row.get('Name', row.get('name', ''))),
            'market':     mkt,
            'close':      sf(row.get('Close', row.get('close'))),
            'change':     sf(row.get('Changes', row.get('change'))),
            'change_pct': chg_ratio,
            'volume':     int(row.get(vol_col, 0)),
        })
    return Response(results)


@api_view(['GET'])
def gold_price(request):
    """
    GET /api/stocks/gold/?period=3M&metal=pure
    period: 1D | 1W | 1M | 3M | 6M | 1Y  (기본 3M)
    metal:  pure | 18k | 14k | white | silver  (기본 pure)
    """
    period = request.query_params.get('period', '3M').upper()
    metal  = request.query_params.get('metal', 'pure').lower()

    if period not in _GOLD_PERIOD_DAYS:
        period = '3M'
    if metal not in _METAL_FIELD:
        metal = 'pure'

    days  = _GOLD_PERIOD_DAYS[period]
    end   = datetime.today()
    start = end - timedelta(days=days)

    try:
        res = httpx.post(_GOLD_URL, json={
            'srchDt':       period,
            'type':         'Au',
            'dataDateStart': start.strftime('%Y.%m.%d'),
            'dataDateEnd':   end.strftime('%Y.%m.%d'),
        }, headers=_GOLD_HEADERS, timeout=10)
        res.raise_for_status()

        sell_key, buy_key = _METAL_FIELD[metal]
        rows = res.json().get('list', [])
        data = sorted(
            [
                {
                    'date': row['date'],
                    'sell': row.get(sell_key),   # 매도가 (살 때)
                    'buy':  row.get(buy_key),    # 매입가 (팔 때)
                }
                for row in rows
                if row.get(sell_key) and row.get(buy_key)
            ],
            key=lambda x: x['date'],  # 오름차순: 과거 → 최신
        )
        return Response({'metal': metal, 'period': period, 'data': data})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ── ML 데이터셋 ────────────────────────────────────────────────────────
_ML_SCRIPT = '''\
#!/usr/bin/env python3
"""
삼성전자 매수/매도/관망 타이밍 예측 데이터셋 생성 스크립트
Triple Barrier Method 적용 | 기간: 최근 5년 일별 데이터
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ── 1. 데이터 수집 ───────────────────────────────────────────────────
end   = datetime.today()
start = end - timedelta(days=5 * 365 + 60)  # 롤링 여유분 포함

print("데이터 수집 중...")
samsung = yf.download("005930.KS", start=start, end=end, auto_adjust=True, progress=False)
dxy     = yf.download("DX-Y.NYB",  start=start, end=end, auto_adjust=True, progress=False)
tnx     = yf.download("^TNX",      start=start, end=end, auto_adjust=True, progress=False)

# MultiIndex 처리 (yfinance 최신 버전 대응)
def get_close(df, ticker):
    if isinstance(df.columns, pd.MultiIndex):
        return df["Close"][ticker]
    return df["Close"]

def get_ohlcv(df, ticker):
    if isinstance(df.columns, pd.MultiIndex):
        d = df.xs(ticker, axis=1, level=1)
    else:
        d = df
    return d[["Open","High","Low","Close","Volume"]]

# ── 2. 병합 (결측치 ffill) ──────────────────────────────────────────
base = get_ohlcv(samsung, "005930.KS").copy()
base = base.join(get_close(dxy, "DX-Y.NYB").rename("DXY"), how="left")
base = base.join(get_close(tnx, "^TNX").rename("TNX"),    how="left")
base["DXY"] = base["DXY"].ffill()
base["TNX"] = base["TNX"].ffill()

# ── 3. 피처 엔지니어링 ──────────────────────────────────────────────
close = base["Close"]

# 이동평균 비율 (장기 추세 정배열 여부)
base["feat_ma_ratio"]    = close.rolling(50).mean() / close.rolling(200).mean()

# RSI (14일)
delta = close.diff()
gain  = delta.clip(lower=0).rolling(14).mean()
loss  = (-delta.clip(upper=0)).rolling(14).mean()
base["feat_rsi"]         = 100 - (100 / (1 + gain / loss))

# MACD 히스토그램
ema12  = close.ewm(span=12, adjust=False).mean()
ema26  = close.ewm(span=26, adjust=False).mean()
macd   = ema12 - ema26
signal = macd.ewm(span=9, adjust=False).mean()
base["feat_macd_hist"]   = macd - signal

# 볼린저 밴드 내 위치 (0%=하단, 100%=상단)
bb_mid   = close.rolling(20).mean()
bb_std   = close.rolling(20).std()
bb_upper = bb_mid + 2 * bb_std
bb_lower = bb_mid - 2 * bb_std
base["feat_bb_pos"]      = (close - bb_lower) / (bb_upper - bb_lower) * 100

# 가격 모멘텀 (수익률 %)
base["feat_return_1d"]   = close.pct_change(1) * 100
base["feat_return_3d"]   = close.pct_change(3) * 100
base["feat_return_5d"]   = close.pct_change(5) * 100

# 거래량 비율 (당일 / 5일 평균)
base["feat_vol_ratio"]   = base["Volume"] / base["Volume"].rolling(5).mean()

# 거시경제 변동률
base["feat_usd_idx_chg"] = base["DXY"].pct_change(1) * 100
base["feat_us_10y_chg"]  = base["TNX"].pct_change(1) * 100

# ── 4. Triple Barrier Method ─────────────────────────────────────────
TAKE_PROFIT = 0.02   # +2% 익절
STOP_LOSS   = -0.01  # -1% 손절
TIME_LIMIT  = 5      # 5영업일

print("Triple Barrier 레이블링 중...")
closes = close.values
labels = []

for i in range(len(closes)):
    if i + TIME_LIMIT >= len(closes):
        labels.append(np.nan)
        continue
    entry = closes[i]
    label = 0  # 관망(타임아웃)
    for j in range(1, TIME_LIMIT + 1):
        ret = (closes[i + j] - entry) / entry
        if ret >= TAKE_PROFIT:
            label = 1; break   # 매수
        elif ret <= STOP_LOSS:
            label = 2; break   # 매도/보류
    labels.append(label)

base["label"] = labels

# ── 5. 정제 및 저장 ──────────────────────────────────────────────────
feat_cols = [c for c in base.columns if c.startswith("feat_")]
df_final  = base[feat_cols + ["label"]].dropna()
df_final["label"] = df_final["label"].astype(int)

df_final.to_csv("samsung_dataset_5y.csv")
print(f"\\n저장 완료: samsung_dataset_5y.csv")
print(f"총 행 수: {len(df_final):,}개")
print("\\n클래스별 분포:")
dist = df_final["label"].value_counts().sort_index()
dist.index = dist.index.map({0: "0 (관망)", 1: "1 (매수)", 2: "2 (매도/보류)"})
print(dist)
'''


@api_view(['GET'])
def ml_download_script(request):
    """데이터셋 생성 Python 스크립트 다운로드"""
    res = HttpResponse(_ML_SCRIPT, content_type='text/x-python; charset=utf-8')
    res['Content-Disposition'] = 'attachment; filename="samsung_dataset_builder.py"'
    return res


@api_view(['POST'])
def ml_generate_dataset(request):
    """데이터셋 생성 후 CSV 반환 (서버에서 직접 계산)"""
    try:
        end   = datetime.today()
        start = end - timedelta(days=5 * 365 + 60)

        import pandas as pd

        def _get_close(df, ticker):
            if isinstance(df.columns, pd.MultiIndex):
                return df['Close'][ticker]
            return df['Close']

        def _get_ohlcv(df, ticker):
            if isinstance(df.columns, pd.MultiIndex):
                d = df.xs(ticker, axis=1, level=1)
            else:
                d = df
            return d[['Open', 'High', 'Low', 'Close', 'Volume']]

        samsung = yf.download('005930.KS', start=start, end=end, auto_adjust=True, progress=False)
        dxy     = yf.download('DX-Y.NYB',  start=start, end=end, auto_adjust=True, progress=False)
        tnx     = yf.download('^TNX',      start=start, end=end, auto_adjust=True, progress=False)

        base = _get_ohlcv(samsung, '005930.KS').copy()
        base = base.join(_get_close(dxy, 'DX-Y.NYB').rename('DXY'), how='left')
        base = base.join(_get_close(tnx, '^TNX').rename('TNX'),     how='left')
        base['DXY'] = base['DXY'].ffill()
        base['TNX'] = base['TNX'].ffill()

        close = base['Close']
        base['feat_ma_ratio']    = close.rolling(50).mean() / close.rolling(200).mean()
        delta = close.diff()
        gain  = delta.clip(lower=0).rolling(14).mean()
        loss  = (-delta.clip(upper=0)).rolling(14).mean()
        base['feat_rsi']         = 100 - (100 / (1 + gain / loss))
        ema12  = close.ewm(span=12, adjust=False).mean()
        ema26  = close.ewm(span=26, adjust=False).mean()
        macd   = ema12 - ema26
        base['feat_macd_hist']   = macd - macd.ewm(span=9, adjust=False).mean()
        bb_mid   = close.rolling(20).mean()
        bb_std   = close.rolling(20).std()
        base['feat_bb_pos']      = (close - (bb_mid - 2*bb_std)) / (4*bb_std) * 100
        base['feat_return_1d']   = close.pct_change(1) * 100
        base['feat_return_3d']   = close.pct_change(3) * 100
        base['feat_return_5d']   = close.pct_change(5) * 100
        base['feat_vol_ratio']   = base['Volume'] / base['Volume'].rolling(5).mean()
        base['feat_usd_idx_chg'] = base['DXY'].pct_change(1) * 100
        base['feat_us_10y_chg']  = base['TNX'].pct_change(1) * 100

        closes = close.values
        labels = []
        for i in range(len(closes)):
            if i + 5 >= len(closes):
                labels.append(np.nan); continue
            entry = closes[i]; label = 0
            for j in range(1, 6):
                ret = (closes[i+j] - entry) / entry
                if ret >= 0.02:   label = 1; break
                elif ret <= -0.01: label = 2; break
            labels.append(label)
        base['label'] = labels

        feat_cols = [c for c in base.columns if c.startswith('feat_')]
        df_final  = base[feat_cols + ['label']].dropna()
        df_final['label'] = df_final['label'].astype(int)

        buf = io.StringIO()
        df_final.to_csv(buf)
        res = HttpResponse(buf.getvalue(), content_type='text/csv; charset=utf-8')
        res['Content-Disposition'] = 'attachment; filename="samsung_dataset_5y.csv"'
        return res
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_analysis(request, symbol):
    """
    GET /api/stocks/{symbol}/ai-analysis/
    stock_indicators 결과를 GMS(Gemini)에 넘겨 기술적 분석 요약 생성.
    """
    def safe(v):
        try:
            f = float(v)
            return None if (math.isnan(f) or math.isinf(f)) else round(f, 4)
        except Exception:
            return None

    # 1) 지표 계산 (stock_indicators와 동일 로직)
    try:
        kis = _parse_kis_symbol(symbol)
        if kis:
            ticker, _ = kis
            start  = (datetime.today() - timedelta(days=350)).strftime('%Y-%m-%d')
            df     = fdr.DataReader(ticker, start)
            closes = df['Close'].astype(float)
            name   = _krx_name(ticker)
        else:
            closes = yf.Ticker(symbol.upper()).history(period='2y')['Close'].astype(float)
            name   = symbol.upper()

        if len(closes) < 26:
            return Response({'error': '데이터 부족'}, status=400)

        price  = float(closes.iloc[-1])
        ma50   = safe(closes.rolling(50).mean().iloc[-1])
        ma200  = safe(closes.rolling(200).mean().iloc[-1])

        delta  = closes.diff()
        gain   = delta.clip(lower=0).rolling(14).mean()
        loss   = (-delta.clip(upper=0)).rolling(14).mean()
        rsi    = safe((100 - (100 / (1 + gain / loss))).iloc[-1])

        ema12  = closes.ewm(span=12, adjust=False).mean()
        ema26  = closes.ewm(span=26, adjust=False).mean()
        macd_l = safe((ema12 - ema26).iloc[-1])
        sig_l  = safe((ema12 - ema26).ewm(span=9, adjust=False).mean().iloc[-1])
        hist   = safe(macd_l - sig_l) if macd_l and sig_l else None

        bb_mid   = closes.rolling(20).mean()
        bb_std   = closes.rolling(20).std()
        bb_upper = float((bb_mid + 2 * bb_std).iloc[-1])
        bb_lower = float((bb_mid - 2 * bb_std).iloc[-1])
        bb_pos   = round((price - bb_lower) / (bb_upper - bb_lower) * 100, 1) if (bb_upper - bb_lower) > 0 else 50

        rsi_sig  = 'oversold' if rsi and rsi < 30 else ('overbought' if rsi and rsi > 70 else 'neutral')
        bb_sig   = 'buy' if price <= bb_lower else ('sell' if price >= bb_upper else 'neutral')
        above200 = ma50 is not None and ma200 is not None and ma50 > ma200

    except Exception as e:
        return Response({'error': str(e)}, status=500)

    sig_kr = {'oversold': '과매도(매수신호)', 'overbought': '과매수(매도신호)', 'neutral': '중립',
              'buy': '매수(하단이탈)', 'sell': '매도(상단이탈)'}

    # 2) 문자열 사전 계산 (f-string 내 조건식+포맷 혼용 방지)
    ma50_s   = f'{ma50:,.2f}' if ma50 is not None else '데이터 부족'
    ma200_s  = f'{ma200:,.2f}' if ma200 is not None else '데이터 부족'
    rsi_s    = f'{rsi:.2f}' if rsi is not None else 'N/A'
    trend_s  = 'MA50 > MA200 (상승 추세)' if above200 else 'MA50 < MA200 (하락 추세)'
    mom_s    = '상승 (MACD > 시그널)' if (macd_l and sig_l and macd_l > sig_l) else '하락 (MACD < 시그널)'
    bb_mid_s = f'{float(bb_mid.iloc[-1]):,.2f}'

    prompt = f"""당신은 주식 기술적 분석 전문가입니다.
{name} ({symbol.upper()}) 의 현재 기술 지표를 분석하고 매수 타이밍에 대한 의견을 제시해 주세요.

[현재 주가] {price:,.0f}

[이동평균선]
- MA 50일: {ma50_s} / MA 200일: {ma200_s}
- 장기 추세: {trend_s}

[RSI 14일]
- RSI 값: {rsi_s} → {sig_kr.get(rsi_sig, '')}

[MACD 12/26/9]
- MACD: {macd_l} / 시그널: {sig_l} / 히스토그램: {hist}
- 모멘텀: {mom_s}

[볼린저 밴드 20일]
- 상단: {bb_upper:,.2f} / 중심: {bb_mid_s} / 하단: {bb_lower:,.2f}
- 밴드 내 위치: {bb_pos}% → {sig_kr.get(bb_sig, '')}

다음 형식으로 분석해 주세요:

## 종합 분석
현재 4가지 지표의 전반적인 상태를 3~4문장으로 요약합니다.

## 매수 지지 시그널
매수를 지지하는 지표와 근거를 설명합니다.

## 주의해야 할 점
매수에 불리하거나 리스크가 있는 지표를 설명합니다.

## 투자 의견
현재 시점의 기술적 분석 기반 매수 타이밍 판단을 간결하게 정리합니다. 마지막에 '본 분석은 기술적 지표 기반 참고용이며 투자 조언이 아닙니다.'라고 명시하세요."""

    try:
        import requests as req
        gms_base = 'https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com/v1beta/models'
        res = req.post(
            f'{gms_base}/{settings.GMS_MODEL}:generateContent',
            headers={'Content-Type': 'application/json', 'x-goog-api-key': settings.GMS_KEY},
            json={'contents': [{'parts': [{'text': prompt}]}]},
            timeout=60,
        )
        res.raise_for_status()
        text = res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception as e:
        return Response({'error': f'AI 분석 실패: {e}'}, status=502)

    return Response({'symbol': symbol.upper(), 'name': name, 'analysis': text})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def watchlist(request):
    if request.method == 'GET':
        items = WatchlistItem.objects.filter(user=request.user)
        return Response([
            {'symbol': i.symbol, 'name': i.name, 'added_at': i.added_at.isoformat()}
            for i in items
        ])
    symbol = request.data.get('symbol', '').upper().strip()
    name   = request.data.get('name', '')
    if not symbol:
        return Response({'error': 'symbol required'}, status=status.HTTP_400_BAD_REQUEST)
    _, created = WatchlistItem.objects.get_or_create(
        user=request.user, symbol=symbol, defaults={'name': name},
    )
    if not created:
        return Response({'error': '이미 관심 종목에 추가됨'}, status=status.HTTP_409_CONFLICT)
    return Response({'symbol': symbol, 'name': name}, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def watchlist_delete(request, symbol):
    deleted, _ = WatchlistItem.objects.filter(user=request.user, symbol=symbol.upper()).delete()
    if not deleted:
        return Response({'error': '관심 종목에 없습니다'}, status=status.HTTP_404_NOT_FOUND)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def receive_stock_name(request):
    """
    GET /api/stocks/stock-name/?stock_name=삼성전자
    프론트에서 선택한 종목 이름을 받는 엔드포인트
    """
    stock_name = request.query_params.get('stock_name', '').strip()
    if not stock_name:
        return Response({'error': 'stock_name 파라미터가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
    # print(stock_name)
    youtube = build('youtube', 'v3', developerKey=settings.YOUTUBE_API_KEY)

    # "stock_name 주가 전망" 검색 요청
    request = youtube.search().list(
        q=stock_name + "주가 전망",
        part="snippet",
        type="video",
        maxResults=10,
        order="viewCount" # 조회수 높은 순
    )
    response = request.execute()
    refined_videos = []
    for item in response.get('items', []):
        video_id = item['id']['videoId']
        
        # html.unescape로 &quot; 등을 원래 특수문자로 복원
        raw_title = item['snippet']['title']
        clean_title = html.unescape(raw_title)
        
        # 썸네일은 보편적으로 쓰이는 medium(중형) 사이즈를 기본으로 채택
        thumbnail_url = item['snippet']['thumbnails']['medium']['url']
        
        # 구조화하여 리스트에 추가
        refined_videos.append({
            "title": clean_title,
            "video_id": video_id,
            "url": f"https://youtu.be/{video_id}",
            "thumbnail_url": thumbnail_url
        })

    # 결과 파싱
    # for item in response['items']:
    #     title = item['snippet']['title']
    #     video_id = item['id']['videoId']
        # print(f"제목: {title} / 링크: https://youtu.be/{video_id}")
    
    response_data = {
        "status": "success",
        "count": len(refined_videos),
        "videos": refined_videos
    }
    
    return Response(response_data, status=status.HTTP_200_OK)
