# moni — 개인 금융 분석 플랫폼

금융상품 비교 · 주식 분석 · 소비 리포트 · 금 시세 · 금융 뉴스를 한 곳에서 제공하는 개인 금융 플랫폼입니다.

---

## 실행 방법

### 1. 백엔드 (Django) — port 8000

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### 2. 프론트엔드 (Vue 3 + Vite) — port 5173

```bash
cd fronted
npm install
npm run dev
```

### 3. 실시간 주식 서버 (FastAPI + WebSocket) — port 8002

한국투자증권 KIS API를 통해 실시간 체결가를 WebSocket으로 중계합니다.

```bash
cd backend
venv\Scripts\activate
uvicorn kis_broker:app --host 0.0.0.0 --port 8002 --reload
```

---

## 기능 목록

### 홈 (`/app/home`)
- 코스피 · 코스닥 지수 실시간 현황 및 30일 히스토리
- 거래량 · 상승률 · 하락률 TOP 5 종목

### 금융상품 (`/app/products`)
- 예금 · 적금 상품 목록 조회 및 금리 비교
- 가입 기간 · 우대금리 필터링
- 데이터: **금융감독원 금융상품통합비교공시 API (FSS)**

### 지점찾기 (`/app/branches`)
- **지역 검색**: 지역명 + 은행명 조합 검색 (지오로케이션 불필요)
- **내 위치 검색**: GPS 좌표 기반 반경 3km 내 지점 검색, 거리순 정렬
- 지도 위 번호 마커, 마커 클릭 인포윈도우, 목록 클릭 지도 포커스
- 길찾기 버튼 → 카카오맵 앱/웹 길찾기 연동
- 데이터 · API: **Kakao Local Search API** (장소 검색), **Kakao Maps JavaScript SDK** (지도 렌더링), **Kakao 좌표→주소 API** (위치 기반 지역명 변환)

### 소비분석 (`/app/spending`) — 로그인 필요
- 은행 CSV 파일 업로드 (거래일시 / 구분 / 금액 / 내용 컬럼 자동 감지)
- 기간 필터: 이번 주 / 이번 달 / 지난 달 / 최근 3개월 / 직접 입력
- 지출 · 수입 전환
- 카테고리 자동 분류 (카페 · 식비 · 교통 · 쇼핑 · 의료 · 구독 등)
- AI 가맹점 분류: 미분류(기타) 가맹점만 Gemini 호출 → `merchant_map.json` 영구 저장
- 차트: 일별 바 차트, 카테고리 도넛 차트, 캘린더 히트맵
- **AI 소비 리포트**: 기간별 지출 데이터를 Gemini에 전달 → 자연어 인사이트 생성 (소비 요약 / 주목 카테고리 / 소비 패턴 / 절약 팁 / 총평)
- PDF 다운로드: AI 리포트 + 통계 차트를 A4 PDF로 내보내기
- 결제 시뮬레이터 (`/app/notify-sim`): 가맹점 + 금액 입력 → 카테고리 즉시 분류 · 저장
- API: **GMS (Gemini 프록시)** — 가맹점 분류 · AI 리포트 생성, **Playwright** — PDF 렌더링

### 주식 — 드롭다운 메뉴

#### 주식 검색 (`/app/stocks`)
- 종목명 / 티커 검색 (한국 KRX + 미국 NYSE/NASDAQ)
- 현재가 · 등락률 · 시가총액 · 52주 고저가 · 평균 거래량
- 기간별 주가 차트 (1개월 ~ 5년)
- 관심 종목 등록 / 삭제
- 관련 유튜브 영상 (조회수 순, 임베드 플레이어)
- 데이터 · API: **FinanceDataReader** (한국 주식 · 코스피/코스닥 지수), **yfinance** (미국 주식), **한국투자증권 KIS API** (WebSocket 실시간 체결가), **YouTube Data API v3** (관련 영상)

#### 매수타이밍 지표 (`/app/indicators`) — 로그인 필요
- 관심 종목의 기술적 지표 계산 및 시각화
  - 이동평균선 MA50 / MA200 (골든크로스 · 데드크로스 감지)
  - RSI 14일 (과매도 / 과매수 게이지)
  - MACD (12, 26, 9) 히스토그램 · 크로스 신호
  - 볼린저 밴드 20일 (밴드 내 위치 바)
- **AI 기술적 분석**: 4개 지표를 Gemini에 전달 → 종합 분석 / 매수 시그널 / 주의사항 / 투자 의견
- **ML 모델 예측 근거**: 학습된 LightGBM 모델의 오늘 예측(매수/매도/관망)을 Gemini가 피처 값 기반으로 설명
- 관련 뉴스 (네이버 뉴스 검색)
- 관련 유튜브 영상 (임베드)
- API: **GMS (Gemini 프록시)** — AI 분석 · ML 근거 설명, **Naver Search API** — 종목 관련 뉴스

#### ML 데이터 (`/app/dataset`) — 로그인 필요
- 삼성전자 기반 Triple Barrier Method 학습 데이터셋 소개
- 피처 엔지니어링 설명 (MA비율 · RSI · MACD · 볼린저 · 수익률 · 거래량비율 · DXY · 미국채금리)
- 데이터셋 CSV 다운로드 / 서버 직접 생성
- LightGBM 모델 학습 (종목별), 예측 결과 조회
- 데이터: **yfinance** (005930.KS · DX-Y.NYB · ^TNX)

#### 투자 성향 테스트 (`/app/investment-type`)
- 투자 성향 설문 (5개 문항) → 공격형 / 성장형 / 중립형 / 안정추구형 / 안정형 분류

### 금 시세 (`/app/gold`)
- 순금 24K · 18K · 14K · 백금 · 은 실시간 매도/매입 가격
- 기간별 시세 차트 (1일 ~ 1년)
- 데이터: **한국금거래소 (koreagoldx.co.kr) API**

### 뉴스 (`/app/news`)
- 금융 키워드별 뉴스 크롤링 및 목록 표시
- 데이터: **Naver Search API** (뉴스 검색)

### 내 포트폴리오 (`/app/portfolio`) — 로그인 필요
- 보유 자산 구성 및 수익률 관리

### 커뮤니티 (`/app/community`)
- 주식 게시판 / 자유게시판
- 게시글 작성 · 열람 · 댓글 (로그인 필요)

### 챗봇 (`/app/chatbot`)
- AI 금융 상담 챗봇
- API: **GMS (Gemini 프록시)**

### 마이페이지 (`/app/mypage`) — 로그인 필요
- 닉네임 · 비밀번호 변경
- 내 게시글 · 관심 종목 조회

---

## 사용 데이터 & API

| 분류 | API / 데이터 | 용도 |
|------|-------------|------|
| 금융상품 | **금융감독원 FSS** `finlife.fss.or.kr` | 예금 · 적금 상품 금리 공시 |
| 지도 | **Kakao Maps JavaScript SDK** | 지점찾기 지도 렌더링 |
| 장소 검색 | **Kakao Local Search API** `dapi.kakao.com` | 은행 지점 키워드 · 좌표 검색 |
| 좌표 변환 | **Kakao 좌표→주소 API** `dapi.kakao.com` | 내 위치 기반 검색 시 지역명 표시 |
| 한국 주식 | **FinanceDataReader** | KRX 종목 목록, 코스피/코스닥 지수, 일별 시세 |
| 미국 주식 | **yfinance** | NYSE/NASDAQ 시세 · 히스토리, DXY, 미국채금리(^TNX) |
| 실시간 주식 | **한국투자증권 KIS API** (WebSocket) | 실시간 체결가 스트리밍 |
| 금 시세 | **한국금거래소** `koreagoldx.co.kr` | 순금/백금/은 매도·매입가 |
| 뉴스 | **Naver Search API** `openapi.naver.com` | 금융·종목 관련 뉴스 |
| 영상 | **YouTube Data API v3** | 종목 관련 유튜브 영상 |
| AI 분석 | **GMS (Gemini 프록시)** `gms.ssafy.io` | 가맹점 분류, 소비 리포트, 주식 기술적 분석, ML 근거 설명, 챗봇 |
| PDF | **Playwright** (Chromium) | 소비 리포트 PDF 렌더링 |

---

## 기술 스택

| 구분 | 기술 |
|------|------|
| 백엔드 | Django 6 · Django REST Framework · SQLite · SimpleJWT |
| 실시간 서버 | FastAPI · WebSocket (KIS 실시간 중계) |
| 프론트엔드 | Vue 3 · Vite · Tailwind CSS 4 · vue-chartjs · lucide-vue |
| ML | LightGBM · scikit-learn · joblib (Triple Barrier Method) |
| 데이터 | FinanceDataReader · yfinance · pandas · numpy |
| 외부 AI | GMS / Gemini 2.5 Flash |

---

## 프로젝트 구조

```
SSAFY_1-/
├── backend/
│   ├── accounts/       # 회원가입 · 로그인 (JWT)
│   ├── products/       # 금융상품 (FSS API)
│   ├── branches/       # 지점찾기 (Kakao API)
│   ├── spending/       # 소비분석 · AI 리포트 · PDF
│   │   └── data/
│   │       └── merchant_map.json   # AI 가맹점 분류 결과 (영구)
│   ├── stocks/         # 주식 · 금 시세 · ML
│   │   └── ml_models/  # 학습된 LightGBM 모델 (.pkl)
│   ├── news/           # 뉴스 크롤러
│   ├── community/      # 게시판
│   ├── chatbot/        # AI 챗봇
│   ├── kis_broker.py   # KIS WebSocket 중계 서버
│   └── config/         # Django 설정 · 루트 URL
├── fronted/
│   └── src/
│       ├── views/          # 페이지 컴포넌트
│       ├── components/     # 공통 컴포넌트 (NavBar, AppFooter 등)
│       ├── layouts/        # AppLayout (NavBar 포함)
│       ├── router/         # Vue Router
│       └── composables/
│           └── useAuth.js  # JWT 자동 갱신 fetch 래퍼
└── README.md
```

---

## 환경 변수

`backend/.env` 에 아래 항목을 설정합니다.

```env
DJANGO_SECRET_KEY=...

# GMS (Gemini 프록시)
GMS_KEY=...
GMS_MODEL=gemini-2.5-flash

# 금융감독원 FSS
fss_api_key=...

# 한국투자증권 KIS (실시간 주식)
KIS_APP_KEY=...
KIS_APP_SECRET=...
KIS_MOCK=false

# Kakao — 지점찾기
VITE_KAKAO_MAP_JS_KEY=...   # 프론트 지도 SDK (JavaScript 앱 키)
KAKAO_REST_API_KEY=...       # 백엔드 장소 검색 (REST API 키)

# Naver Search — 뉴스
NAVER_SEARCH_CLIENT_ID=...
NAVER_SEARCH_CLIENT_SECRET=...

# YouTube Data API v3
YOUTUBE_API_KEY=...

# Gmail SMTP (비밀번호 재설정)
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...

# CLOVA OCR (선택)
CLOVA_OCR_INVOKE_URL=...
CLOVA_OCR_SECRET=...
```

---

## 데이터 저장 방식

| 데이터 | 저장 위치 |
|--------|-----------|
| 사용자 계정 · 게시글 · 관심 종목 | SQLite (`backend/db.sqlite3`) |
| CSV 거래 내역 | 메모리 (서버 재시작 시 초기화, 재업로드 필요) |
| AI 가맹점 분류 결과 | `backend/spending/data/merchant_map.json` (영구) |
| ML 학습 모델 | `backend/ml_models/{symbol}_lgbm.pkl` (영구) |
