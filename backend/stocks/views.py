import FinanceDataReader as fdr
import httpx
import math
import re
import yfinance as yf
from pathlib import Path
from datetime import datetime, timedelta

from django.conf import settings
from dotenv import load_dotenv
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import WatchlistItem

load_dotenv(Path(__file__).parent.parent / '.env')

VALID_PERIODS = {'1mo', '3mo', '6mo', '1y', '2y', '5y'}
PERIOD_DAYS   = {'1mo': 30, '3mo': 90, '6mo': 180, '1y': 365, '2y': 730, '5y': 1825}


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
