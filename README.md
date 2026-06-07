# SafeFinance

한국 금융 보안 플랫폼. 보이스피싱 탐지, 지출 분석, 영수증 관리 등을 제공합니다.

---

## 실행 방법

서버는 총 3개를 각각 터미널에서 실행합니다.

### 1. 백엔드 (Django) — port 8000

```bash
cd backend
venv\Scripts\activate        # Windows
python manage.py runserver
```

> 처음 실행 시
> ```bash
> pip install -r requirements.txt
> python manage.py migrate
> ```

### 2. 프론트엔드 (Vue 3 + Vite) — port 5173

```bash
cd fronted
npm install      # 처음 한 번만
npm run dev
```

### 3. AI 모델 서버 (FastAPI) — port 8001

보이스피싱 탐지 모델 서버입니다. 보이스피싱 탐지 기능을 사용할 때만 필요합니다.

```bash
cd model_server
venv\Scripts\activate        # Windows
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

> 처음 실행 시
> ```bash
> pip install -r requirements.txt
> ```

> **모델 파일 별도 다운로드 필요**
>
> `model_server/model/model.safetensors` (422MB) 는 용량 문제로 git에서 제외되어 있습니다.
> 팀원에게 직접 전달받아 아래 경로에 넣어주세요.
> ```
> model_server/
> └── model/
>     ├── model.safetensors   ← 여기에 배치
>     ├── config.json
>     ├── tokenizer.json
>     └── threshold.txt
> ```

---

## 프로젝트 구조

```
voice/
├── backend/          # Django REST Framework 백엔드
│   ├── accounts/     # 회원가입 · 로그인 (JWT)
│   ├── products/     # 금융상품 조회
│   ├── branches/     # 지점 찾기
│   ├── receipts/     # 영수증 장부
│   ├── voicephishing/# 보이스피싱 탐지
│   ├── spending/     # 지출 분석
│   │   └── data/
│   │       └── merchant_map.json  # AI 가맹점 분류 결과 영구 저장
│   ├── docforms/     # 문서 양식
│   └── config/       # Django 설정 · 루트 URL
├── fronted/          # Vue 3 + Vite + Tailwind CSS 4 프론트엔드
│   └── src/
│       ├── views/    # 페이지 컴포넌트
│       ├── components/
│       └── composables/
│           └── useAuth.js  # JWT 자동 갱신 fetch 래퍼
└── model_server/     # FastAPI 보이스피싱 탐지 모델 서버
    └── model/        # HuggingFace 모델 파일
```

---

## 기능 목록

### 인증
- 회원가입 / 로그인 / 로그아웃
- JWT (access + refresh) 자동 갱신

### 금융상품 (`/products`)
- 예금·적금 상품 목록 조회 및 비교

### 지점 찾기 (`/branches`)
- 은행 지점 위치 검색

### 영수증 장부 (`/receipts`)
- 영수증 이미지 업로드 및 관리

### 보이스피싱 탐지 (`/voicephishing`)
- 텍스트(통화 스크립트) 입력 → 보이스피싱 여부 판별
- 오디오 파일 업로드 → STT 후 자동 분석
- 탐지 이력 조회
- AI 모델: HuggingFace fine-tuned 분류기 (FastAPI 서버 분리 운영)

### 지출 분석 (`/spending`)
- 은행 CSV 파일 업로드 (거래일시 / 구분 / 거래금액 / 내용 컬럼 자동 감지)
- 입금 / 출금 전환 토글
- 기간 필터: 이번달 / 지난달 / 이번주 / 최근 3개월 / 직접 입력
- 카테고리 자동 분류 (키워드 매핑)
  - 카페 / 식비 / 편의점 / 교통 / 쇼핑 / 의료 / 문화 / 구독 / 통신 / 현금출금 / 이체
  - 개인 이체·충전·저축 항목 자동 제외 (정수환, 황정희, 동백전충전, 저금통)
- AI 분류 (Gemini via GMS API)
  - 미분류(기타) 가맹점만 골라서 API 호출 → 결과를 `merchant_map.json`에 영구 저장
  - 저장된 분류만 적용 / AI 재호출 선택 가능
- 차트: 일별 바 차트, 카테고리 도넛 차트, 캘린더 히트맵
- 카테고리 클릭 → 가맹점 상세 내역 펼치기

### 결제 시뮬레이터 (`/notify-sim`)
- 가맹점명 + 금액 입력 → 알림 카드 UI로 표시
- 카테고리 버튼 탭 → 즉시 분류 + `merchant_map.json`에 자동 저장
- 이번 세션 분류 내역 및 카테고리별 합계 표시
- CSV 업로드 전에 미리 가맹점을 분류해두는 용도로 활용 가능

### 보안 커뮤니티 (`/community`)
- 금융 보안 관련 게시글 작성 및 열람

### 마이페이지 (`/mypage`)
- 내 정보 확인 및 수정

---

## 기술 스택

| 구분 | 기술 |
|------|------|
| 백엔드 | Django 6.0.5 · Django REST Framework · SQLite · SimpleJWT |
| 프론트엔드 | Vue 3 · Vite · Tailwind CSS 4 · vue-chartjs · lucide-vue |
| AI 모델 서버 | FastAPI · HuggingFace Transformers · Whisper (STT) |
| 외부 API | GMS (Gemini 프록시) — 지출 가맹점 자동 분류 |

---

## 환경 변수

`backend/.env` 파일에 아래 항목이 필요합니다.

```
SECRET_KEY=...
GMS_KEY=...          # Gemini API 키
GMS_MODEL=...        # 사용할 Gemini 모델명
```

---

## 데이터 저장 방식

| 데이터 | 저장 위치 |
|--------|-----------|
| 사용자 계정 · 게시글 등 | SQLite DB (`backend/db.sqlite3`) |
| CSV 거래 내역 | 메모리 (서버 재시작 시 초기화, CSV 재업로드 필요) |
| 가맹점 분류 결과 | `backend/spending/data/merchant_map.json` (영구) |
