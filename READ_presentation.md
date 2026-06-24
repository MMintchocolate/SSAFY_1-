# moni — 스마트 금융 플랫폼 발표 자료

> Vue 3 + Django REST Framework 기반 통합 금융 서비스

---

## 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [기술 스택](#2-기술-스택)
3. [외부 API 및 서비스](#3-외부-api-및-서비스)
4. [기능별 상세 설명](#4-기능별-상세-설명)
   - 4-1. 회원 인증 (JWT + Google OAuth)
   - 4-2. 실시간 주식 시세
   - 4-3. 기술적 지표 분석 (매수신호)
   - 4-4. ML 매수타이밍 예측 모델
   - 4-5. 금융상품 비교 (정기예금·적금)
   - 4-6. 금 시세
   - 4-7. 금융 뉴스 크롤링·군집화·요약
   - 4-8. 지출 분석
   - 4-9. 영수증 OCR 및 PDF 장부 생성
   - 4-10. 보이스피싱 탐지
   - 4-11. AI 챗봇
   - 4-12. 투자 성향 테스트
   - 4-13. 포트폴리오 관리 대시보드
   - 4-14. 커뮤니티 게시판
   - 4-15. 지점 찾기
5. [프론트엔드 구조](#5-프론트엔드-구조)
6. [백엔드 구조](#6-백엔드-구조)
7. [데이터베이스 모델](#7-데이터베이스-모델)
8. [인증 흐름](#8-인증-흐름)
9. [전체 시스템 아키텍처](#9-전체-시스템-아키텍처)

---

## 1. 프로젝트 개요

| 항목 | 내용 |
|------|------|
| 프로젝트명 | **moni** |
| 개발 언어 | Python (Django), JavaScript (Vue 3) |
| 데이터베이스 | SQLite |
| AI 모델 | LightGBM (주식 예측), Gemini 2.5-flash (자연어) |
| 주요 특징 | 머신러닝 주식 예측 · 지출 분석 · 보이스피싱 탐지 · 투자성향 진단 |

### 서비스 구성 (15개 기능)
- 실시간 주식 시세 / 기술적 지표 / ML 예측
- 금융상품(예금·적금) 금리 비교
- 금 시세 실시간 조회
- 금융 뉴스 크롤링 + AI 요약 + DBSCAN 군집화
- 지출 분석 (CSV 자동 분류 + AI 리포트)
- 영수증 OCR → PDF 자동 생성
- 보이스피싱 탐지 (딥러닝 모델)
- AI 챗봇 / 투자성향 진단
- 포트폴리오 대시보드
- 커뮤니티 게시판
- 주변 지점 찾기 (카카오 지도)

---

## 2. 기술 스택

### Backend
| 라이브러리 | 용도 |
|-----------|------|
| Django 5 + DRF | REST API 서버 |
| djangorestframework-simplejwt | JWT 인증 |
| LightGBM | 주식 매수타이밍 분류 모델 |
| yfinance | 미국/글로벌 주식 OHLCV 데이터 |
| FinanceDataReader | 한국 KRX 주식 데이터 |
| pandas / numpy | 데이터 처리·피처 계산 |
| scikit-learn | 혼동행렬, DBSCAN 군집화 |
| joblib | 모델 직렬화 (.pkl) |
| requests / BeautifulSoup | 뉴스 HTTP 크롤링 |
| Playwright | HTML → PDF 변환 (headless browser) |
| FastAPI (별도 서버) | 보이스피싱 딥러닝 모델 추론 서버 |

### Frontend
| 라이브러리 | 용도 |
|-----------|------|
| Vue 3 (Composition API) | UI 프레임워크 |
| Vue Router 4 | SPA 라우팅 |
| Vite | 빌드 도구 |
| TailwindCSS | 유틸리티 CSS |
| Chart.js + vue-chartjs | 차트 (라인, 도넛, 캔들스틱) |
| Lucide Vue | 아이콘 |

---

## 3. 외부 API 및 서비스

| 서비스 | API | 용도 |
|--------|-----|------|
| **Gemini 2.5-flash** (Google) | GMS 프록시 | 뉴스 요약, 기술적 분석, 지출 분류, 투자성향, 챗봇 |
| **FSS 금융감독원** | finlifeapi | 정기예금·적금 금리 정보 |
| **네이버 뉴스 API** | `v1/search/news.json` | 키워드 기반 뉴스 검색 |
| **카카오 Local API** | `v2/local/search/keyword` | 주변 은행 지점·ATM 검색 |
| **카카오 Geocode** | `v2/local/geo/coord2address` | 좌표 → 주소 변환 |
| **YouTube Data API v3** | `search.list` | 종목별 주가 전망 영상 검색 |
| **Naver Clova OCR** | INVOKE_URL | 영수증 이미지 텍스트 인식 |
| **Google OAuth 2.0** | tokeninfo | 소셜 로그인 |
| **Gmail SMTP** | smtp.gmail.com:587 | 비밀번호 재설정 이메일 발송 |
| **Korea Gold X** | koreagoldx.co.kr | 순금·18K·14K·백금·은 시세 |
| **FinanceDataReader** | KRX | 코스피·코스닥 종목 리스트, 시세 |
| **yfinance** | Yahoo Finance | 글로벌 주식·인덱스·DXY·TNX |

---

## 4. 기능별 상세 설명

---

### 4-1. 회원 인증 (JWT + Google OAuth)

#### 기능 요약
- 이메일·비밀번호 회원가입/로그인
- Google 계정 소셜 로그인
- 이메일 기반 비밀번호 재설정

#### 백엔드 (`backend/accounts/`)

| 엔드포인트 | 메서드 | 기능 |
|-----------|--------|------|
| `/api/accounts/register/` | POST | 회원가입 (username, email, password) |
| `/api/accounts/login/` | POST | 로그인 → Access/Refresh 토큰 반환 |
| `/api/accounts/logout/` | POST | Refresh 토큰 블랙리스트 처리 |
| `/api/accounts/google/` | POST | Google ID 토큰 검증 → JWT 발급 |
| `/api/accounts/me/` | GET/PATCH | 내 정보 조회·수정 |
| `/api/accounts/me/password/` | POST | 비밀번호 변경 |
| `/api/accounts/password-reset/confirm/` | POST | 이메일 토큰으로 비밀번호 재설정 |
| `/api/accounts/token/refresh/` | POST | Access 토큰 자동 갱신 |

#### JWT 설정
```
Access Token 유효시간  : 1시간
Refresh Token 유효시간 : 14일
Rotate Refresh Tokens : True (사용 시 새 Refresh 발급)
Blacklist after rotation : True (이전 Refresh 무효화)
```

#### 프론트엔드 통신 흐름 (`fronted/src/composables/useAuth.js`)
```
1. 로그인 POST /api/accounts/login/
   → { access, refresh, user } 반환
   → localStorage에 access / refresh / user 저장

2. 인증 필요 API 호출 시 authFetch() 사용
   → Authorization: Bearer {access} 헤더 자동 주입

3. API 응답이 401이면
   → POST /api/accounts/token/refresh/ (refresh 토큰 전송)
   → 새 access 토큰으로 원래 요청 재시도

4. Refresh도 만료되면 localStorage 초기화 → 로그인 페이지 이동
```

#### Google OAuth 흐름
```
1. 프론트: Google 버튼 클릭 → Google Identity Services SDK 실행
2. Google → credential (ID 토큰) 반환
3. POST /api/accounts/google/ { credential }
4. 백엔드: Google tokeninfo 엔드포인트로 토큰 검증
5. User 생성 또는 조회 → JWT 발급 → 프론트에 반환
```

---

### 4-2. 실시간 주식 시세

#### 기능 요약
- 국내(코스피·코스닥) / 해외 종목 검색
- 종목 현재가·전일대비·등락률
- 1개월~5년 가격 히스토리 차트
- 관심 종목 등록·해제
- YouTube 주가 전망 영상 검색

#### 백엔드 (`backend/stocks/views.py`)

| 엔드포인트 | 메서드 | 기능 |
|-----------|--------|------|
| `/api/stocks/search/?q=삼성전자` | GET | 종목명·코드 검색 |
| `/api/stocks/<symbol>/` | GET | 현재가·변동 (yfinance Ticker.fast_info) |
| `/api/stocks/<symbol>/history/?period=3mo` | GET | 일별 OHLCV (1mo/3mo/6mo/1y/2y/5y) |
| `/api/stocks/market-movers/` | GET | 시가총액·상승·하락 TOP5 |
| `/api/stocks/index/` | GET | KOSPI·KOSDAQ 지수 |
| `/api/stocks/stock-name/?stock_name=삼성전자` | GET | YouTube 주가 전망 영상 |
| `/api/stocks/watchlist/` | GET/POST | 관심 종목 조회·추가 |
| `/api/stocks/watchlist/<symbol>/` | DELETE | 관심 종목 삭제 |

#### 데이터 소스
- **한국 주식:** `FinanceDataReader.StockListing('KRX')` → 종목 리스트 (종목명, 시가총액)
- **글로벌 주식·지수·ETF:** `yfinance.Ticker(symbol)`
  - 시세: `Ticker.fast_info` (currentPrice, previousClose, volume)
  - 히스토리: `Ticker.history(period=...)` → date, open, high, low, close, volume

#### 프론트엔드 통신 흐름
```
StocksView.vue
  ├── 검색창 입력 (400ms 디바운스)
  │     → GET /api/stocks/search/?q={query}
  │     → 드롭다운 결과 표시
  ├── 종목 클릭
  │     → GET /api/stocks/{symbol}/         (현재가)
  │     → GET /api/stocks/{symbol}/history/ (차트 데이터)
  │     → Chart.js Line/Candlestick 렌더링
  └── 관심 종목 버튼
        → authFetch POST /api/stocks/watchlist/ { symbol, name }
```

---

### 4-3. 기술적 지표 분석 (매수신호)

#### 기능 요약
관심 종목의 MA·RSI·MACD·볼린저밴드를 계산하고 매수/매도/중립 신호를 시각화

#### 백엔드 엔드포인트
```
GET /api/stocks/<symbol>/indicators/
GET /api/stocks/<symbol>/ai-analysis/   (Gemini 기술적 분석 요약)
```

#### 지표 계산 로직 (`backend/stocks/views.py`)
| 지표 | 계산 방법 | 신호 조건 |
|------|----------|----------|
| **MA 교차** | MA50 / MA200 이동평균 | MA50 > MA200 → 골든크로스(매수) / MA50 < MA200 → 데드크로스(매도) |
| **RSI(14)** | 14일 평균 상승폭 / (상승폭+하락폭) × 100 | RSI < 30 → 과매도(매수) / RSI > 70 → 과매수(매도) |
| **MACD(12,26,9)** | EMA12 - EMA26 = MACD, MACD - Signal(EMA9) = Histogram | Histogram > 0 & 증가 → 매수 / 감소 → 매도 |
| **Bollinger(20,2)** | MA20 ± 2×표준편차 | 종가 < 하단밴드 → 매수 / > 상단밴드 → 매도 |

#### Gemini AI 분석 프롬프트 구조
```
오늘의 지표 값 4가지 + 각 신호 상태를 입력
→ 투자자가 이해하기 쉬운 3~5문장 종합 분석 출력
→ "본 분석은 투자 권유가 아닙니다" 면책 문구 포함
```

#### 프론트엔드 통신 흐름
```
IndicatorsView.vue
  ├── 관심 종목 로드 (authFetch /api/stocks/watchlist/)
  ├── 종목 선택 시
  │     → GET /api/stocks/{symbol}/indicators/
  │     → { ma_cross, rsi, macd, bollinger } + 각 신호 반환
  │     → 신호별 컬러 카드 (빨강/초록/회색) 렌더링
  └── AI 분석 버튼 클릭
        → authFetch GET /api/stocks/{symbol}/ai-analysis/
        → Gemini 텍스트 스트리밍 없이 단건 반환
```

---

### 4-4. ML 매수타이밍 예측 모델

#### 기능 요약
종목별 LightGBM 모델을 직접 학습하고 오늘의 매수/매도/관망 신호를 예측

#### 알고리즘: LightGBM 3-class Classifier

**Triple Barrier Method 레이블링**
```
각 날짜 i에서 이후 5거래일 관찰:
  +5% 이상 도달 → label = 1 (매수)
  -2.5% 이하 도달 → label = 2 (매도/보류)
  5일 내 미도달  → label = 0 (관망)
```

**10가지 피처**
| 피처 | 설명 |
|------|------|
| feat_ma_ratio | MA50 / MA200 (장기 추세 방향) |
| feat_rsi | RSI 14일 (모멘텀 과열 여부) |
| feat_macd_hist | MACD 히스토그램 (단기 모멘텀) |
| feat_bb_pos | 볼린저밴드 내 위치 (0=하단, 1=상단) |
| feat_return_1d | 1일 수익률 |
| feat_return_3d | 3일 수익률 |
| feat_return_5d | 5일 수익률 |
| feat_vol_ratio | 거래량 / 5일 평균 거래량 |
| feat_usd_idx_chg | 달러지수(DXY) 일변화율 |
| feat_us_10y_chg | 미국 10년 국채금리 일변화율 |

**LightGBM 하이퍼파라미터**
```python
n_estimators=100, learning_rate=0.05,
max_depth=4, num_leaves=15,
class_weight='balanced', random_state=42
```

**학습 데이터**
- 기간: 최근 5년 (1825일 + 여유분)
- 분할: 80% 학습 / 20% 테스트
- 추가 외부 데이터: DXY (달러지수), ^TNX (미국 10년 금리)

#### 백엔드 엔드포인트

| 엔드포인트 | 메서드 | 기능 |
|-----------|--------|------|
| `/api/stocks/ml/train/?symbol=TSLA` | POST | LightGBM 학습 → pkl + meta.json 저장 |
| `/api/stocks/ml/predict/?symbol=TSLA` | GET | 최신 피처로 예측 → 로그인 시 DB 저장 |
| `/api/stocks/ml/explain/?symbol=TSLA` | GET | 예측 + Gemini AI 해설 생성 |
| `/api/stocks/ml/saved/` | GET | 로그인 유저의 저장된 예측 조회 |
| `/api/stocks/ml/status/` | GET | 학습된 모든 모델 목록·정확도 |

**모델 저장 위치:** `backend/ml_models/{symbol}_lgbm.pkl` + `{symbol}_lgbm_meta.json`

#### 프론트엔드 통신 흐름 (`DatasetView.vue`)
```
1. 페이지 진입
   → GET /api/stocks/ml/status/        (학습된 모델 목록)
   → GET /api/stocks/watchlist/        (관심 종목)
   → authFetch GET /api/stocks/ml/saved/  (저장된 예측 결과 복원)

2. 학습 버튼 클릭
   → POST /api/stocks/ml/train/?symbol=TSLA
   → 응답: { accuracy, total_rows, feat_imp, per_class, confusion_matrix }
   → 정확도·혼동행렬·피처 중요도 시각화

3. 오늘 예측 버튼 클릭
   → GET /api/stocks/ml/predict/?symbol=TSLA
   → 응답: { signal, signal_label, probabilities, latest_date }
   → 신호 카드 표시 (초록=매수, 빨강=매도, 회색=관망)
   → authFetch GET /api/stocks/ml/explain/  (AI 보고서 병렬 호출)
   → DB에 예측 결과 자동 저장 (재방문 시 복원됨)
```

#### Gemini AI 해설 프롬프트 구조
```
입력:
  - 예측 신호·확률 (관망X% / 매수X% / 매도X%)
  - 오늘의 10가지 피처 값
  - 모델 피처 중요도 TOP5

출력 섹션:
  ## 예측 근거   (중요도 높은 피처 3~4개 수치 기반 설명)
  ## 시그널 신뢰도   (확률 분포 기반 평가)
  ## 반대 시그널 주의   (예측 반대 방향 지표 경고)
  + 면책 문구
```

---

### 4-5. 금융상품 비교 (정기예금·적금)

#### 기능 요약
금융감독원 FSS API로 정기예금·적금 상품 정보를 DB에 캐싱하고, 금리 순 정렬·필터 제공

#### 백엔드 엔드포인트

| 엔드포인트 | 메서드 | 기능 |
|-----------|--------|------|
| `/api/products/deposit/` | GET | 캐싱된 정기예금 목록 반환 |
| `/api/products/savings/` | GET | 캐싱된 적금 목록 반환 |
| `/api/products/refresh/` | POST | FSS API 재호출 → DB 갱신 (로그인 필요) |

#### FSS API 호출 방식
```
Base URL: https://finlife.fss.or.kr/finlifeapi
엔드포인트:
  - depositProductsSearch.json  (정기예금)
  - savingProductsSearch.json   (적금)
파라미터:
  - auth: FSS_API_KEY (환경변수)
  - topFinGrpNo: 020000 (은행)
  - pageNo: 1
```

#### DB 캐싱 구조 (`FinancialProductCache` 모델)
```
product_type : 'deposit' | 'savings'
data         : JSON (상품 목록 전체)
updated_at   : DateTimeField (auto_now=True)
```

- GET 요청: DB에서 즉시 반환 (FSS API 불필요)
- POST refresh: FSS API 호출 후 `update_or_create`

#### 프론트엔드 통신 흐름 (`ProductsView.vue`)
```
1. 페이지 진입
   → GET /api/products/deposit/  → { products, updated_at }
   → GET /api/products/savings/  → { products, updated_at }
   → 금리 내림차순 정렬, 기간·금융기관 필터 UI

2. "데이터 업데이트" 버튼 클릭 (로그인 필요)
   → authFetch POST /api/products/refresh/
   → 새 데이터로 화면 갱신 + 업데이트 시각 표시
```

---

### 4-6. 금 시세

#### 기능 요약
한국금거래소 API를 통해 순금(24K)·18K·14K·백금·은 실시간 시세 및 기간별 차트 제공

#### 백엔드 엔드포인트
```
GET /api/stocks/gold/?period=3M&metal=pure
```

**파라미터**
- `period`: 1M / 3M / 6M / 1Y / 3Y
- `metal`: pure(순금24K) / 18k / 14k / platinum / silver

**데이터 출처:** `https://www.koreagoldx.co.kr/api/price/chart/list`

#### 프론트엔드 통신 흐름 (`GoldView.vue`)
```
1. 페이지 진입 → GET /api/stocks/gold/?period=3M&metal=pure
2. 기간·금속 탭 선택 → 파라미터 변경 후 재요청
3. Chart.js Line Chart로 기간별 시세 렌더링
4. 현재 시세·전일대비·등락률 카드 표시
```

---

### 4-7. 금융 뉴스 크롤링·군집화·요약

#### 기능 요약
네이버 뉴스 API로 금융 뉴스를 수집하고, DBSCAN 군집화로 유사 뉴스를 묶고, Gemini로 요약 생성

#### 백엔드 엔드포인트

| 엔드포인트 | 메서드 | 기능 |
|-----------|--------|------|
| `/api/news/crawl/` | POST | 뉴스 크롤링 (유출·해킹·주식) |
| `/api/news/` | GET | 저장된 뉴스 목록 |
| `/api/news/cluster/` | GET | DBSCAN 군집화 |
| `/api/news/<id>/summarize/` | GET | Gemini AI 요약 생성 |
| `/api/news/stock/?q=삼성전자` | GET | 종목명 실시간 뉴스 검색 |

#### 크롤링 흐름
```
1. POST /api/news/crawl/
2. 네이버 뉴스 API (Client-ID/Secret) 호출
   - URL: https://openapi.naver.com/v1/search/news.json
   - 키워드: 유출, 해킹, 주식
3. ThreadPoolExecutor (workers=10) 병렬 본문 스크래핑
   - BeautifulSoup으로 네이버 기사 본문 파싱
4. 중복 제거 후 DB 저장
```

#### DBSCAN 군집화 흐름
```
1. GET /api/news/cluster/?eps=0.45&min_samples=6
2. 뉴스 제목 + 요약 → TF-IDF 벡터화
3. DBSCAN(eps, min_samples) 적용
4. 클러스터별 대표 뉴스 선정 (centroid 최근접)
5. 클러스터 번호 -1 = 노이즈 (독립 뉴스)
```

**사용자별 클러스터 파라미터:** `accounts.User.cluster_eps` / `cluster_min_samples`

#### Gemini 뉴스 요약 프롬프트
```
입력: 기사 제목 + 본문 (최대 2000자)
출력: 3~5문장 순수 텍스트 (마크다운 금지)
"이 기사가 무엇에 관한 내용인지, 주요 사실과 맥락을 독자가 이해하기 쉽게 풀어서 설명"
```

#### 프론트엔드 통신 흐름 (`NewsView.vue`)
```
1. "크롤링" 버튼 → POST /api/news/crawl/
2. 뉴스 목록 → GET /api/news/?keyword=유출
3. "군집화" 버튼 → GET /api/news/cluster/?eps=0.45&min_samples=6
   → 클러스터별 색상 구분 표시
4. 뉴스 클릭 → "요약" 버튼 → GET /api/news/{id}/summarize/
   → Gemini 응답 표시 (로딩 스피너 포함)
5. 종목명 검색 → GET /api/news/stock/?q=삼성전자
```

---

### 4-8. 지출 분석

#### 기능 요약
카드사 CSV 파일을 업로드하면 가맹점명을 카테고리로 자동 분류하고 통계·차트·AI 리포트 제공

#### 백엔드 엔드포인트

| 엔드포인트 | 메서드 | 기능 |
|-----------|--------|------|
| `/api/spending/upload/` | POST | CSV 파일 업로드 및 파싱 |
| `/api/spending/stats/?period=this_month` | GET | 기간별 지출 통계 |
| `/api/spending/classify-misc/` | POST | Gemini 미분류 항목 카테고리 추천 |
| `/api/spending/ai-report/` | GET | AI 지출 분석 리포트 (Gemini) |
| `/api/spending/report-pdf/` | GET | PDF 리포트 다운로드 |
| `/api/spending/map-status/` | GET | 가맹점→카테고리 매핑 현황 |
| `/api/spending/add-mapping/` | POST | 새 매핑 추가 |

#### 분류 흐름
```
1. CSV 업로드 (인코딩 자동 감지: utf-8-sig / utf-8 / euc-kr / cp949)
2. 컬럼 파싱: 거래일시, 가맹점명, 이용금액
3. merchant_map.json에서 기존 매핑 조회
   - 매핑 있음: 즉시 카테고리 할당
   - 매핑 없음: '기타' 분류
4. POST /api/spending/classify-misc/
   - 미분류 가맹점 리스트를 Gemini에 전송
   - 카테고리 제안 받아 merchant_map.json에 저장
5. 이후 동일 가맹점은 매핑 재사용 (API 호출 없음)
```

**카테고리:** 식비 / 교통 / 쇼핑 / 의료 / 엔터테인먼트 / 기타

#### Gemini AI 리포트 프롬프트
```
입력: 카테고리별 지출 요약 + 전월 대비
출력:
  - 지출 패턴 분석 (3~5가지 인사이트)
  - 절감 가능 항목 추천
  - 다음 달 예산 계획 제안
```

#### 프론트엔드 통신 흐름 (`SpendingView.vue`)
```
1. CSV 드래그앤드롭 → authFetch POST /api/spending/upload/
2. GET /api/spending/stats/?period=this_month
   → Chart.js 도넛·막대차트 렌더링
3. "AI 분석" 버튼 → GET /api/spending/ai-report/
   → Gemini 리포트 텍스트 표시
4. PDF 다운로드 → GET /api/spending/report-pdf/
   → Blob 처리 → 브라우저 다운로드 트리거
```

---

### 4-9. 영수증 OCR 및 PDF 장부 생성

#### 기능 요약
영수증 이미지를 Naver Clova OCR로 인식하고 Gemini로 구조화한 뒤 Playwright로 PDF 장부를 생성

#### 백엔드 엔드포인트

| 엔드포인트 | 메서드 | 기능 |
|-----------|--------|------|
| `/api/receipts/upload/` | POST | 영수증 이미지 업로드 + OCR |
| `/api/receipts/` | GET | 저장된 영수증 목록 |
| `/api/forms/classify/` | POST | OCR 텍스트 → JSON 구조화 (Gemini) |
| `/api/forms/render/` | POST | 구조화 JSON → PDF 생성 (Playwright) |

#### OCR → PDF 생성 흐름
```
1. POST /api/receipts/upload/ (multipart/form-data)
2. Naver Clova OCR API 호출
   - URL: CLOVA_OCR_INVOKE_URL
   - Secret: CLOVA_OCR_SECRET
   - 응답: 인식된 텍스트 블록 배열
3. POST /api/forms/classify/ { text: OCR 결과 }
   - Gemini 프롬프트:
     "아래 OCR 텍스트를 지출결의서 JSON 형식으로 구조화:
      { 부서, 신청자, 지출목적, 항목: [{내용, 금액}], 합계 }"
4. POST /api/forms/render/ { data: 구조화 JSON }
   - Django 템플릿(expense_report.html)에 데이터 바인딩
   - Playwright headless browser로 HTML → PDF 변환
   - PDF 바이너리 반환 (application/pdf)
```

---

### 4-10. 보이스피싱 탐지

#### 기능 요약
오디오(.wav/.mp3/.m4a) 또는 텍스트(.txt) 파일을 별도 FastAPI 딥러닝 서버에 분석 요청

#### 시스템 구성
```
[Vue 프론트] → [Django 백엔드] → [FastAPI 모델 서버 :8001]
```

#### 백엔드 엔드포인트

| 엔드포인트 | 메서드 | 기능 |
|-----------|--------|------|
| `/api/voicephishing/analyze/` | POST | 파일 업로드 → 모델 서버 프록시 |
| `/api/voicephishing/history/` | GET | 이전 분석 이력 |

#### 분석 흐름
```
1. POST /api/voicephishing/analyze/ (파일 최대 50MB)
2. Django → FastAPI 모델 서버 포워딩
   - URL: MODEL_SERVER_URL/predict/ (기본: http://localhost:8001)
   - 타임아웃: 60초
3. FastAPI 모델 서버 처리:
   - 오디오 파일: STT(음성→텍스트) → 텍스트 분류
   - 텍스트 파일: 직접 분류 모델 추론
   - 출력: 위험 확률값 0.0 ~ 1.0
4. Django: 결과 DB 저장 + 라벨 판정
```

**위험도 분류**
| 확률 범위 | 라벨 | 의미 |
|-----------|------|------|
| 0.0 ~ 0.4 | 안전 (Safe) | 정상 통화 |
| 0.4 ~ 0.7 | 의심 (Suspicious) | 주의 필요 |
| 0.7 ~ 1.0 | 위험 (Danger) | 보이스피싱 의심 |

---

### 4-11. AI 챗봇

#### 기능 요약
moni 서비스 전반을 안내하는 Gemini 기반 금융 AI 챗봇 (대화 히스토리 유지)

#### 백엔드 엔드포인트
```
POST /api/chat/
Body: { message: "질문", history: [{role, text}, ...] }
```

#### Gemini 호출 방식
```python
# Gemini는 system role 미지원
# → system prompt를 첫 번째 user/model 쌍으로 주입

contents = [
  { "role": "user",  "parts": [{"text": SYSTEM_PROMPT}] },
  { "role": "model", "parts": [{"text": "네, 안내해 드리겠습니다."}] },
  # 이후 실제 대화 히스토리
  *[ {"role": r, "parts": [{"text": t}]} for r, t in history ],
  { "role": "user", "parts": [{"text": message}] }
]
```

**시스템 프롬프트 주요 내용**
```
- moni의 10가지 서비스 메뉴 설명 (금융상품비교, 실시간주식, 매수신호, ML데이터,
  지출분석, 영수증장부, 금시세, 금융뉴스, 커뮤니티, 지점찾기)
- URL/경로 언급 금지 → 메뉴명으로만 안내
- 마크다운 기호 없이 순수 텍스트 답변
- 금융 관련 질문에만 답변
```

#### 프론트엔드 통신 흐름 (`ChatbotView.vue`)
```
1. 사용자 메시지 입력 + Enter
2. history 배열에 { role:'user', text } 추가
3. POST /api/chat/ { message, history }
4. 응답 텍스트 → history에 { role:'model', text } 추가
5. 대화 목록 스크롤 최하단으로 이동
```

---

### 4-12. 투자 성향 테스트

#### 기능 요약
7문항 퀴즈 후 Gemini가 A·B·C·D 4가지 투자성향을 분석하고 맞춤 종목을 추천

#### 백엔드 엔드포인트
```
POST /api/chat/investment-type/
Body: { answers: ["1", "3", "2", "4", "2", "1", "3"] }
```

#### 7문항 구성
```
Q1. 투자 목표 (안정적 이자 / 시장 수익률 / 고성장 / 퀀트 전략)
Q2. 손실 허용 범위 (5% / 15% / 30% / 손익 관계없음)
Q3. 투자 기간 (1년 이내 / 1~3년 / 3~7년 / 단기매매)
Q4. 선호 종목 유형 (배당주 / 우량주 / 성장주 / 퀀트 지표 기반)
Q5. 시장 급락 시 반응 (즉시 매도 / 관망 / 추가매수 / 알고리즘 신호 대기)
Q6. 포트폴리오 다각화 (채권 중심 / ETF / 테마주 혼합 / 지표 기반 분산)
Q7. 정보 탐색 방식 (전문가 추천 / 시장 지수 / 뉴스/트렌드 / 수치 지표)
```

#### 투자 성향 4가지 유형
| 코드 | 유형명 | 특징 |
|------|--------|------|
| A | 안정 제일형 | 배당·채권 선호, 원금 보전 중시 |
| B | 시장 추종형 | ETF·우량주, 시장 수익률 추구 |
| C | 성장 트렌드형 | 미래 혁신 기업, 높은 변동성 수용 |
| D | 데이터 퀀트형 | 지표 기반 알고리즘적 투자 |

#### Gemini 분석 프롬프트
```
입력: 7개 답변 JSON
출력 JSON:
{
  "type_code": "A|B|C|D",
  "type_name": "유형명",
  "type_description": "특징 2~3문장",
  "animal_match": "대표 동물 캐릭터",
  "recommendations": [
    { "asset_name": "종목/ETF명", "asset_type": "국내주식|해외주식|ETF|채권", "reason": "추천 이유" }
    // 3개
  ],
  "investment_tip": "리스크 관리 조언 1~2문장"
}
```

#### 프론트엔드 통신 흐름 (`InvestmentTypeView.vue`)
```
4단계 흐름:
  intro (시작) → quiz (7문항) → loading (AI 분석 중) → result (결과)

quiz 단계:
  - 진행 바 + 도트 인디케이터
  - 이전/다음/제출 버튼

loading 단계:
  - POST /api/chat/investment-type/ { answers }
  - Gemini JSON 응답 파싱 (```json 마크다운 제거)

result 단계:
  - 유형 카드 (이모지 + 이름 + 설명)
  - 추천 종목 3개 카드
  - 투자 팁
  - 다시 시작 버튼
```

---

### 4-13. 포트폴리오 관리 대시보드

#### 기능 요약
보유 종목의 현재 가치·손익을 실시간으로 계산하고 도넛 차트·라인 차트로 시각화

#### 백엔드 엔드포인트

| 엔드포인트 | 메서드 | 기능 |
|-----------|--------|------|
| `/api/portfolio/` | GET | 보유 종목 목록 조회 |
| `/api/portfolio/` | POST | 종목 추가 (symbol, name, quantity, avg_price) |
| `/api/portfolio/<id>/` | PUT | 수량·단가 수정 |
| `/api/portfolio/<id>/` | DELETE | 종목 삭제 |

**데이터 모델 (`PortfolioItem`)**
```
user      : FK(User)  → 유저별 격리
symbol    : CharField  (예: 005930.KS)
name      : CharField  (예: 삼성전자)
quantity  : DecimalField(12,4)
avg_price : DecimalField(14,2)
unique_together: (user, symbol)  → 동일 종목 중복 불가
```

#### 대시보드 계산 로직 (`PortfolioView.vue`)
```javascript
// 각 종목별
close = prices[symbol].price || prices[symbol].close
value = close × quantity
cost  = avg_price × quantity
pnl   = value - cost
pnlPct = (value - cost) / cost × 100
dayPnl = close × quantity × (chgPct / 100) / (1 + chgPct/100)

// 포트폴리오 전체
totalValue = Σ(value)  // 현재가 없는 종목은 원가로 대체
totalPnl   = totalValue - Σ(cost)
todayPnl   = Σ(dayPnl)
```

#### 프론트엔드 통신 흐름 (`PortfolioView.vue`)
```
1. 페이지 진입
   → authFetch GET /api/portfolio/            (보유 종목 목록)
   → Promise.all: 종목별 GET /api/stocks/{symbol}/ (현재가 병렬 조회)
   → 요약 카드 3개: 총평가금액 / 총손익(%) / 오늘손익

2. 도넛 차트 (종목 비중)
   → Chart.js Doughnut: 종목별 평가금액 / 총평가금액 × 100 (%)

3. 라인 차트 (포트폴리오 가치 추이)
   → 종목별 GET /api/stocks/{symbol}/history/?period=1mo 병렬 호출
   → 날짜별 (close × quantity) 합산 → 30일 추이 차트

4. 종목별 상세 테이블
   → 수량 / 평균단가 / 현재가 / 평가금액 / 손익(%) / 오늘등락

5. 마이페이지에서 종목 추가/수정/삭제 관리
```

---

### 4-14. 커뮤니티 게시판

#### 기능 요약
주식 토론 게시판과 자유 게시판, 댓글 기능을 제공하는 커뮤니티

#### 백엔드 엔드포인트

| 엔드포인트 | 메서드 | 기능 |
|-----------|--------|------|
| `/api/community/posts/?board_type=stock` | GET | 게시글 목록 (stock/free, 페이지네이션 20개) |
| `/api/community/posts/create/` | POST | 게시글 작성 (로그인 필요) |
| `/api/community/posts/<id>/` | GET | 게시글 상세 |
| `/api/community/posts/<id>/update/` | PUT | 게시글 수정 (본인만) |
| `/api/community/posts/<id>/delete/` | DELETE | 게시글 삭제 (본인만) |
| `/api/community/posts/<id>/comments/` | GET | 댓글 조회 |
| `/api/community/posts/<id>/comments/create/` | POST | 댓글 작성 |
| `/api/community/my/posts/` | GET | 내 게시글 목록 |
| `/api/community/my/comments/` | GET | 내 댓글 목록 |

---

### 4-15. 지점 찾기

#### 기능 요약
카카오 Local API를 이용한 주변 은행 지점·ATM 검색 (지역명 또는 현재 위치 기반)

#### 백엔드 엔드포인트

| 엔드포인트 | 메서드 | 기능 |
|-----------|--------|------|
| `/api/branches/search/?region=강남구&keyword=국민은행` | GET | 지역명 기반 검색 |
| `/api/branches/search-by-location/?lat=37.5&lng=127.0&radius=1000` | GET | 좌표+반경 검색 |
| `/api/branches/reverse-geocode/?lat=37.5&lng=127.0` | GET | 좌표 → 주소 변환 |

#### 카카오 API 호출 방식
```
URL: https://dapi.kakao.com/v2/local/search/keyword.json
Headers: Authorization: KakaoAK {KAKAO_REST_API_KEY}
파라미터:
  - query: "{region} {keyword}"
  - page: 1~3  (최대 45개 결과)
  - size: 15   (페이지당 15개)
  - sort: distance (좌표 검색 시)
```

#### 프론트엔드 통신 흐름 (`BranchesView.vue`)
```
1. 현재 위치 버튼 → navigator.geolocation.getCurrentPosition()
   → GET /api/branches/reverse-geocode/?lat=...&lng=...  (주소 표시용)
   → GET /api/branches/search-by-location/?lat=...&lng=...&radius=1000

2. 지역명 검색
   → GET /api/branches/search/?region=강남구&keyword=국민은행

3. 결과 → 카카오 지도 SDK 마커 표시
   → 마커 클릭 → 지점명·주소·전화번호 말풍선 표시
```

---

## 5. 프론트엔드 구조

### 라우터 (`fronted/src/router/index.js`)

#### 블랭크 레이아웃 (NavBar 없음)
| 경로 | 뷰 |
|------|-----|
| `/` | LandingView |
| `/intro` | IntroView |
| `/login` | LoginView |
| `/register` | RegisterView |
| `/reset-password` | ResetPasswordView |

#### 앱 레이아웃 (NavBar 포함, `/app/` 프리픽스)
| 경로 | 뷰 | 로그인 필요 |
|------|-----|:----------:|
| `home` | HomeView | |
| `products` | ProductsView | |
| `branches` | BranchesView | |
| `stocks` | StocksView | |
| `gold` | GoldView | |
| `news` | NewsView | |
| `community` | CommunityView | |
| `chatbot` | ChatbotView | |
| `investment-type` | InvestmentTypeView | |
| `dataset` | DatasetView | ✓ |
| `indicators` | IndicatorsView | ✓ |
| `receipts` | ReceiptsView | ✓ |
| `voicephishing` | VoicePhishingView | ✓ |
| `spending` | SpendingView | ✓ |
| `notify-sim` | NotifySimView | ✓ |
| `mypage` | MyPageView | ✓ |
| `portfolio` | PortfolioView | ✓ |

#### 라우터 가드
```javascript
router.beforeEach((to) => {
  const token = localStorage.getItem('access')
  if (to.meta.requiresAuth && !token) {
    return { path: '/app/home', query: { loginRequired: '1' } }
  }
})
```

### NavBar 메뉴 구성
- 금융상품 · 지점찾기 · 지출분석 · 금 시세 · 뉴스 · 내 포트폴리오 (단순 링크)
- **주식** 드롭다운: 주식 검색 / 매수신호 / ML 데이터 / 투자 성향 테스트
- **커뮤니티** 드롭다운: 주식 게시판 / 자유게시판

---

## 6. 백엔드 구조

```
backend/
├── config/
│   ├── settings.py   (INSTALLED_APPS 13개, 외부 API 설정)
│   └── urls.py       (API 라우트 14개)
├── accounts/         (JWT + Google OAuth 인증)
├── stocks/           (주식 시세 + LightGBM ML)
│   ├── views.py      (시세·검색·관심종목)
│   └── ml_views.py   (학습·예측·설명·저장)
├── products/         (금융상품, FSS API 캐싱)
├── news/             (크롤링·DBSCAN·Gemini 요약)
├── spending/         (CSV 분석, Gemini 분류)
├── chatbot/          (챗봇·투자성향 - Gemini)
├── branches/         (카카오 Local API)
├── voicephishing/    (FastAPI 모델 서버 프록시)
├── docforms/         (OCR 구조화·Playwright PDF)
├── portfolio/        (포트폴리오 CRUD)
├── community/        (게시판·댓글)
├── receipts/         (Clova OCR)
└── ml_models/        (LightGBM .pkl 저장소)
```

### API 라우트 전체 목록 (`config/urls.py`)
```
/api/accounts/    → accounts.urls
/api/products/    → products.urls
/api/receipts/    → receipts.urls
/api/branches/    → branches.urls
/api/voicephishing/ → voicephishing.urls
/api/forms/       → docforms.urls
/api/spending/    → spending.urls
/api/news/        → news.urls
/api/stocks/      → stocks.urls
/api/community/   → community.urls
/api/chat/        → chatbot.urls
/api/portfolio/   → portfolio.urls
```

---

## 7. 데이터베이스 모델

| 앱 | 모델 | 주요 필드 |
|----|------|---------|
| accounts | User | username, email, nickname, cluster_eps, cluster_min_samples |
| stocks | WatchlistItem | user(FK), symbol, name |
| stocks | UserPredictionCache | user(FK), symbol, signal, probabilities, explanation, predicted_at |
| products | FinancialProductCache | product_type(unique), data(JSON), updated_at |
| news | NewsArticle | title, url, content, crawled_at |
| spending | SpendingRecord | user(FK), date, merchant, amount, category |
| voicephishing | PhishingAnalysis | user(FK), filename, text, probability, label |
| community | Post | author(FK), board_type, title, content |
| community | Comment | post(FK), author(FK), content |
| portfolio | PortfolioItem | user(FK), symbol, name, quantity, avg_price |

---

## 8. 인증 흐름

```
┌─────────────────────────────────────────────────────┐
│                  프론트엔드 (Vue 3)                    │
│                                                      │
│  로그인 → POST /api/accounts/login/                   │
│         ← { access(1h), refresh(14d), user }         │
│  localStorage: access / refresh / user 저장           │
│                                                      │
│  API 호출 시 authFetch() 사용                          │
│    → Authorization: Bearer {access} 자동 주입          │
│                                                      │
│  401 에러 발생 시:                                     │
│    → POST /api/accounts/token/refresh/               │
│      { refresh } → 새 access 토큰                     │
│    → 원래 요청 재시도                                   │
│                                                      │
│  Refresh도 만료:                                       │
│    → localStorage 전체 삭제 → /login 리다이렉트          │
└─────────────────────────────────────────────────────┘

Google OAuth 흐름:
  1. Google Identity Services SDK → credential (ID 토큰)
  2. POST /api/accounts/google/ { credential }
  3. Django: Google tokeninfo API로 토큰 검증
  4. User 자동 생성 또는 기존 계정 연결
  5. JWT 발급 → 프론트 저장
```

---

## 9. 전체 시스템 아키텍처

```
┌──────────────────────────────────────────────────────────────────┐
│                        사용자 브라우저                              │
│                   Vue 3 SPA (fronted/:5173)                       │
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTPS (Vite proxy)
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│               Django REST Framework (:8000)                      │
│                                                                  │
│  /api/accounts/   JWT 인증 · Google OAuth · 이메일               │
│  /api/stocks/     시세·지표·관심종목·ML 모델                        │
│  /api/products/   FSS API 캐싱                                   │
│  /api/news/       크롤링·군집화·요약                               │
│  /api/spending/   CSV 분석·AI 분류                                │
│  /api/chat/       챗봇·투자성향                                   │
│  /api/branches/   카카오 지도                                     │
│  /api/voicephishing/ 모델 서버 프록시                              │
│  /api/forms/      OCR→PDF 생성                                   │
│  /api/portfolio/  포트폴리오 CRUD                                 │
│  /api/community/  게시판·댓글                                     │
└────┬──────┬──────┬──────┬──────┬──────┬──────┬──────────────────┘
     │      │      │      │      │      │      │
     ▼      ▼      ▼      ▼      ▼      ▼      ▼
  SQLite  Gemini  FSS   Naver  Kakao  yfinance FastAPI
  (DB)   (LLM)   API   API    API    FinData  Model
                              YouTube  Reader  Server
                              Data API        (:8001)
                              Clova OCR
                              Korea Gold X
                              Gmail SMTP
```

---

## 부록: 환경 변수 목록 (`.env`)

```
DJANGO_SECRET_KEY=...

# AI
GMS_KEY=...                   # Gemini API 키 (GMS 프록시)
GMS_MODEL=gemini-2.5-flash    # Gemini 모델명

# 금융
FSS_API_KEY=...               # 금융감독원 금융상품 API

# OCR
CLOVA_OCR_INVOKE_URL=...      # 네이버 Clova OCR URL
CLOVA_OCR_SECRET=...          # Clova OCR 시크릿

# 검색·지도
KAKAO_REST_API_KEY=...        # 카카오 Local API
NAVER_SEARCH_CLIENT_ID=...    # 네이버 검색 API
NAVER_SEARCH_CLIENT_SECRET=...

# 영상
YOUTUBE_API_KEY=...           # YouTube Data API v3

# 이메일
EMAIL_HOST_USER=...           # Gmail 계정
EMAIL_HOST_PASSWORD=...       # Gmail 앱 비밀번호

# 보이스피싱 모델 서버
MODEL_SERVER_URL=http://localhost:8001

# 디버그
DEBUG=True
```
