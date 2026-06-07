"""
CSV 파싱 · 가맹점 정규화 · 카테고리 분류 · 집계 모듈.

== 컬럼 매핑 수정 방법 ==
COLUMN_MAP 딕셔너리에서 각 키(date/merchant/amount)에 해당하는
후보 컬럼명 리스트를 우선순위 순으로 나열하세요.

== 카테고리 매핑 수정 방법 ==
CATEGORY_MAP 딕셔너리에서 카테고리명(키)에 키워드 리스트(값)를 추가/수정하세요.
키워드는 소문자로, 가맹점명도 소문자로 변환하여 부분 일치 검색합니다.
"""

import re
import io
from datetime import date, timedelta

import pandas as pd

# ─── 컬럼 매핑 (파일마다 다른 컬럼명 대응) ──────────────────────────────────
COLUMN_MAP = {
    'date':     ['거래일시', '거래일자', '거래일', '날짜', '일자', 'date', 'Date', '거래날짜'],
    'merchant': ['내용', '가맹점명', '가맹점', '적요', '거래처', '거래구분', 'merchant', 'Merchant', '상호명'],
    'amount':   ['거래금액', '출금액', '금액', '사용금액', '지출금액', '이용금액', 'amount', 'Amount'],
}

# 출금/입금 구분 컬럼 후보
DEBIT_COL_CANDIDATES = ['구분', '입출금구분', '거래유형', 'type']
DEBIT_KEYWORDS = ['출금', '출', 'debit', 'withdrawal', 'wd']

# ─── 제외 키워드 (개인 이체·충전·저축 등 실질 소비/수입 아닌 것) ─────────────
# 내용(merchant)에 아래 키워드가 포함된 행은 집계에서 완전 제외
EXCLUDE_KEYWORDS = [
    '정수환',       # 개인 이체
    '황정희',       # 개인 이체
    '동백전충전',   # 지역화폐 충전 (자기 자신에게)
    '저금통',       # 자체 저축
]

# ─── 카테고리 매핑 (키워드 → 카테고리) ─────────────────────────────────────
CATEGORY_MAP = {
    '카페':    ['스타벅스', '카페', '커피', '이디야', '할리스', '투썸', '메가커피', '빽다방', 'coffee',
               '커피빈', '폴바셋', '엔제리너스', '던킨', '파스쿠찌', '컴포즈'],
    '식비':    ['식당', '한식', '삼겹', '갈비', '치킨', '피자', '버거', '맥도날드', '버거킹',
               '롯데리아', '파리바게뜨', '뚜레쥬르', '김밥', '국밥', '냉면', '돈까스', '도시락', '피자헛', 'bbq',
               '배달의민족', '쿠팡이츠', '요기요', '한솥', '서브웨이', '맘스터치', '노브랜드버거',
               '포차', '횟집', '족발', '보쌈', '찜닭', '분식', '떡볶이', '초밥', '라멘', '우동', '덮밥',
               '곱창', '회식', '식사', '점심', '저녁', '아침', '쌀국수', '샌드위치',
               '장터', '시장', '전통시장', '슈퍼', '먹거리', '푸드'],
    '편의점':  ['gs25', 'cu편의점', 'cu', '씨유', '세븐일레븐', '미니스톱', '이마트24', 'seven', 'gs 25'],
    '교통':    ['버스', '지하철', '택시', 't-money', '카카오택시', 'ktx', '고속버스', 'korail', '주유',
               '카카오t', 'sr', '기차', '항공', '공항', '티머니', '지하철역', '교통카드',
               '후불교통', '교통대금', '교통요금'],
    '쇼핑':    ['쿠팡', '네이버쇼핑', '마켓컬리', 'ssg', '롯데쇼핑', '이마트', '홈플러스', '코스트코', '올리브영',
               '무신사', '지그재그', '에이블리', '위메프', '티몬', '11번가', 'g마켓', '옥션', '당근', '번개장터',
               '롯데마트', '하이마트', '다이소', '유니클로', '자라', '아디다스', '나이키'],
    '의료':    ['병원', '약국', '의원', '치과', '한의원', '클리닉', '피부과', '안과', '이비인후과',
               '정형외과', '내과', '산부인과', '소아과', '응급', '건강검진'],
    '문화':    ['cgv', '메가박스', '롯데시네마', '교보문고', '알라딘', 'yes24', '영화',
               '코인노래', '노래방', '볼링', '당구', 'pc방', '방탈출', '공연', '전시', '뮤지컬'],
    '구독':    ['넷플릭스', '유튜브', 'spotify', '왓챠', '티빙', 'netflix', 'youtube', 'apple',
               '웨이브', '시즌', '디즈니', '밀리의서재', '리디북스', 'naver plus', '네이버플러스'],
    '통신':    ['skt', 'kt ', 'lg u+', '통신요금', 'sk텔레콤', '01075380266'],
    '현금출금': ['atm', '현금자동화기기', '현금자동'],
    '이체':    ['자동이체자신', '타행이체', '당행이체', '카카오페이머니', '토스머니', '페이머니',
               '뱅크샐러드', '네이버페이머니', '인터넷이체'],
}


# ─── 내부 함수 ──────────────────────────────────────────────────────────────

def _resolve_columns(df: pd.DataFrame) -> dict[str, str]:
    """CSV 컬럼명 → 내부 키 매핑. 매칭 실패 시 ValueError."""
    cols = {c.strip() for c in df.columns}
    result = {}
    for key, candidates in COLUMN_MAP.items():
        for c in candidates:
            if c in cols:
                result[key] = c
                break
        if key not in result:
            raise ValueError(
                f"'{key}' 컬럼을 찾을 수 없습니다. "
                f"CSV 컬럼: {list(cols)} / 후보: {candidates}"
            )
    return result


def _parse_amount(val) -> int:
    """'1,234원', '"-29,000"', '₩1234' 등 다양한 금액 문자열 → 정수(절댓값).
    출금 금액이 음수로 표기된 은행 포맷 대응."""
    if pd.isna(val):
        return 0
    s = re.sub(r'[₩,\s원"]', '', str(val))
    try:
        v = int(float(s))
    except ValueError:
        return 0
    return abs(v)


def _parse_date(val) -> pd.Timestamp | None:
    """YYYY-MM-DD HH:MM:SS / YYYY-MM-DD / YYYYMMDD 등 날짜 파싱."""
    if pd.isna(val):
        return None
    s = str(val).strip()
    # 날짜 부분의 구분자(. /)만 -로 변환, 시간 부분 공백은 보존
    s = re.sub(r'(?<=\d)[./](?=\d)', '-', s)
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d', '%Y%m%d', '%m-%d-%Y'):
        try:
            return pd.to_datetime(s, format=fmt)
        except Exception:
            continue
    try:
        return pd.to_datetime(s)
    except Exception:
        return None


def _normalize_merchant(name: str) -> str:
    """(주), 지점명, 괄호 등 노이즈 제거."""
    if not isinstance(name, str):
        return ''
    s = re.sub(r'\(주\)|\(유\)|\(합\)', '', name)   # 법인 접두어
    s = re.sub(r'\([^)]*\)', '', s)                   # 괄호 내용 제거
    s = re.sub(r'\s+(점|지점|매장|센터|마트)$', '', s)  # 말미 단어
    return s.strip()


def _categorize(merchant: str) -> str:
    """정규화된 가맹점명 → 카테고리. 제외 대상은 '_exclude', 미분류는 '기타'."""
    lower = merchant.lower()
    if any(kw in lower for kw in EXCLUDE_KEYWORDS):
        return '_exclude'
    for category, keywords in CATEGORY_MAP.items():
        if any(kw in lower for kw in keywords):
            return category
    return '기타'


def _build_df(raw: pd.DataFrame) -> pd.DataFrame:
    """원시 DataFrame → 정제된 DataFrame (date/merchant/category/amount/direction)."""
    col = _resolve_columns(raw)

    df = pd.DataFrame()
    df['date']     = pd.to_datetime(raw[col['date']].apply(_parse_date), errors='coerce')
    df['merchant'] = raw[col['merchant']].apply(_normalize_merchant)
    df['amount']   = raw[col['amount']].apply(_parse_amount)

    # 구분 컬럼 → direction('out'=출금, 'in'=입금)
    found = False
    for cand in DEBIT_COL_CANDIDATES:
        actual = next((c for c in raw.columns if c.strip().lower() == cand.lower()), None)
        if actual:
            raw_dir = raw[actual].astype(str).str.strip().str.lower()
            df['direction'] = raw_dir.apply(lambda x: 'out' if x in DEBIT_KEYWORDS else 'in')
            found = True
            break
    if not found:
        df['direction'] = 'out'

    df = df.dropna(subset=['date'])
    df = df[df['amount'] > 0]
    df['category'] = df['merchant'].apply(_categorize)
    df = df.sort_values('date').reset_index(drop=True)
    return df


# ─── 공개 함수 ──────────────────────────────────────────────────────────────

def load_csv(path) -> pd.DataFrame:
    """파일 경로에서 CSV 로드 → 정제 DataFrame."""
    for enc in ('utf-8-sig', 'utf-8', 'euc-kr', 'cp949'):
        try:
            raw = pd.read_csv(path, encoding=enc, dtype=str)
            return _build_df(raw)
        except (UnicodeDecodeError, LookupError):
            continue
    raise ValueError('CSV 파일 인코딩을 읽을 수 없습니다.')


def parse_csv(content: str) -> pd.DataFrame:
    """문자열(업로드된 CSV 내용) → 정제 DataFrame."""
    raw = pd.read_csv(io.StringIO(content), dtype=str)
    return _build_df(raw)


def _period_range(period: str) -> tuple[date, date]:
    today = date.today()
    if period == 'this_month':
        return today.replace(day=1), today
    if period == 'last_month':
        last = today.replace(day=1) - timedelta(days=1)
        return last.replace(day=1), last
    if period == 'this_week':
        start = today - timedelta(days=today.weekday())  # 월요일
        return start, today
    if period == 'last_3months':
        m, y = today.month - 3, today.year
        if m <= 0:
            m += 12; y -= 1
        return today.replace(year=y, month=m, day=1), today
    return today.replace(day=1), today


def aggregate_data(df: pd.DataFrame, period: str = 'this_month',
                   start_str: str | None = None, end_str: str | None = None,
                   direction: str = 'out') -> dict:
    """정제 DataFrame + 기간 + 방향 → 차트 데이터 dict.
    direction: 'out'=출금, 'in'=입금, 'all'=전체
    """
    if start_str and end_str:
        try:
            start = date.fromisoformat(start_str)
            end   = date.fromisoformat(end_str)
        except ValueError:
            start, end = _period_range(period)
    else:
        start, end = _period_range(period)

    mask = (df['date'].dt.date >= start) & (df['date'].dt.date <= end)
    fdf = df[mask].copy()

    if direction in ('in', 'out') and 'direction' in fdf.columns:
        fdf = fdf[fdf['direction'] == direction]

    # 제외 대상(개인 이체·충전·저축) 필터링
    fdf = fdf[fdf['category'] != '_exclude']

    if fdf.empty:
        return {
            'summary':     {'total': 0, 'daily_avg': 0, 'max_day': None, 'count': 0},
            'daily':       [],
            'weekly':      [],
            'monthly':     [],
            'by_category': [],
        }

    # 일별
    daily = (
        fdf.groupby(fdf['date'].dt.date)['amount']
        .sum().reset_index()
        .rename(columns={'date': 'date', 'amount': 'amount'})
    )
    daily['date'] = daily['date'].astype(str)

    # 주별 (ISO)
    fdf['week'] = fdf['date'].dt.strftime('%G-W%V')
    weekly = fdf.groupby('week')['amount'].sum().reset_index()

    # 월별
    fdf['month'] = fdf['date'].dt.strftime('%Y-%m')
    monthly = fdf.groupby('month')['amount'].sum().reset_index()

    # 카테고리별
    by_cat = fdf.groupby('category')['amount'].sum().reset_index()
    total  = by_cat['amount'].sum()
    by_cat['ratio'] = (by_cat['amount'] / total * 100).round(1)
    by_cat = by_cat.sort_values('amount', ascending=False)

    # 카테고리별 가맹점 상세 (클릭 시 상세보기용)
    cat_count = fdf.groupby('category').size().to_dict()
    category_details = {}
    for cat in fdf['category'].unique():
        sub = fdf[fdf['category'] == cat]
        merch = (
            sub.groupby('merchant')['amount']
            .agg(amount='sum', count='size')
            .reset_index()
            .sort_values('amount', ascending=False)
            .head(30)
        )
        category_details[cat] = [
            {'merchant': r['merchant'], 'amount': int(r['amount']), 'count': int(r['count'])}
            for _, r in merch.iterrows()
        ]

    # 요약
    total_amt  = int(fdf['amount'].sum())
    num_days   = (end - start).days + 1
    daily_avg  = int(total_amt / num_days)
    max_row    = daily.loc[daily['amount'].idxmax()]

    return {
        'summary': {
            'total':     total_amt,
            'daily_avg': daily_avg,
            'max_day':   {'date': max_row['date'], 'amount': int(max_row['amount'])},
            'count':     len(fdf),
        },
        'daily':   [{'date': r['date'], 'amount': int(r['amount'])} for _, r in daily.iterrows()],
        'weekly':  [{'week': r['week'], 'amount': int(r['amount'])} for _, r in weekly.iterrows()],
        'monthly': [{'month': r['month'], 'amount': int(r['amount']),
                     'label': r['month'][5:].lstrip('0') + '월'} for _, r in monthly.iterrows()],
        'by_category': [
            {'category': r['category'], 'amount': int(r['amount']), 'ratio': float(r['ratio']),
             'count': cat_count.get(r['category'], 0)}
            for _, r in by_cat.iterrows()
        ],
        'category_details': category_details,
    }
