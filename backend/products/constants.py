import urllib.parse

# 은행명(부분 일치) → 상품 안내 페이지
BANK_URLS = {
    'KB국민':   'https://www.kbstar.com',
    '신한':     'https://www.shinhan.com',
    '하나':     'https://www.kebhana.com',
    '우리':     'https://www.wooribank.com',
    'IBK기업':  'https://www.ibk.co.kr',
    '기업':     'https://www.ibk.co.kr',
    'NH농협':   'https://banking.nonghyup.com',
    '농협':     'https://banking.nonghyup.com',
    '수협':     'https://www.suhyup-bank.com',
    'SC제일':       'https://www.standardchartered.co.kr',
    '스탠다드차타드': 'https://www.standardchartered.co.kr',
    '씨티':     'https://www.citibank.co.kr',
    'KDB산업':  'https://www.kdb.co.kr',
    '대구':     'https://www.dgb.co.kr',
    '부산':     'https://www.busanbank.co.kr',
    '광주':     'https://www.kjbank.com',
    '전북':     'https://www.jbbank.co.kr',
    '제주':     'https://www.jejubank.com',
    '경남':     'https://www.knbank.co.kr',
    '케이뱅크': 'https://www.kbanknow.com',
    '카카오뱅크': 'https://www.kakaobank.com',
    '토스뱅크': 'https://www.tossbank.com',
}


def resolve_product_url(kor_co_nm: str, fin_prdt_nm: str) -> str:
    for keyword, url in BANK_URLS.items():
        if keyword in kor_co_nm:
            return url
    # 매핑 없으면 네이버 검색으로 폴백
    query = urllib.parse.quote(f'{kor_co_nm} {fin_prdt_nm}')
    return f'https://search.naver.com/search.naver?query={query}'
