<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Wallet, TrendingUp, Coins, Newspaper, MessagesSquare, MapPin } from '@lucide/vue'

const router = useRouter()

// ── 인트로 애니메이션 상태 (랜딩페이지와 동일) ──────────
const cloudOn   = ref(false)  // 배경 블러
const yellowOn  = ref(false)  // 노란 점
const mintOn    = ref(false)  // 민트 점
const smileOn   = ref(false)  // 웃는 곡선
const lettersOn = ref(0)      // moni 로고 텍스트 (한 글자씩)
const taglineOn = ref(false)  // 슬로건
const scrollOn  = ref(false)  // 스크롤 아이콘

function sleep(ms) { return new Promise(r => setTimeout(r, ms)) }

onMounted(async () => {
  await sleep(300)
  cloudOn.value = true        // 배경 블러도 로고와 함께 서서히 생성
  yellowOn.value = true       // 노란 점
  await sleep(450)
  mintOn.value = true         // 민트 점
  await sleep(330)
  smileOn.value = true        // 웃는 곡선
  await sleep(560)
  for (let i = 1; i <= 4; i++) {   // moni 한 글자씩
    lettersOn.value = i
    await sleep(165)
  }
  await sleep(300)
  taglineOn.value = true      // 슬로건
  await sleep(420)
  scrollOn.value = true       // 스크롤 아이콘
})

function goStart() {
  router.push(localStorage.getItem('access') ? '/app/home' : '/login')
}

// 스크린샷이 없을 때 placeholder 처리
function onImgError(e) {
  e.target.closest('.shot-wrap').classList.add('no-image')
}

const featured = [
  {
    id: 'spending',
    label: '지출 분석',
    badge: 'AI 분석',
    badgeBg: '#DFFAF4',
    badgeColor: '#0D9B7A',
    accent: '#57E0C3',
    title: '내 소비 패턴을 한눈에',
    desc: '카드·영수증 데이터를 분석해 지출 카테고리를 자동 분류합니다.\n월별 트렌드와 과소비 항목을 시각화해 스마트한 절약을 도와드립니다.',
    img: '/screenshots/spending.png',
    to: '/app/spending',
    features: ['자동 카테고리 분류', '월별 지출 트렌드', '과소비 알림'],
  },
  {
    id: 'indicators',
    label: '매수 신호',
    badge: 'ML 기반',
    badgeBg: '#FFF8E6',
    badgeColor: '#B8860B',
    accent: '#FFC62A',
    title: 'AI가 포착하는 매수 타이밍',
    desc: 'RSI, MACD, 이동평균 등 핵심 기술적 지표를 종합 분석합니다.\n머신러닝 모델이 실시간으로 매수·매도 신호를 계산해 드립니다.',
    img: '/screenshots/indicators.png',
    to: '/app/indicators',
    features: ['RSI · MACD · 볼린저밴드', '매수/매도 신호 자동 산출', 'AI 종합 판단'],
    reverse: true,
  },
  {
    id: 'dataset',
    label: 'ML 데이터',
    badge: '모델 학습',
    badgeBg: '#DFFAF4',
    badgeColor: '#0D9B7A',
    accent: '#57E0C3',
    title: '직접 학습시키는 AI 예측 모델',
    desc: '원하는 종목의 과거 데이터로 LightGBM 모델을 직접 학습시킵니다.\n학습된 모델로 다음 날 주가 방향을 예측하고 정확도를 확인할 수 있습니다.',
    img: '/screenshots/dataset.png',
    to: '/app/dataset',
    features: ['종목별 데이터셋 구성', 'LightGBM 학습·평가', '상승/하락 방향 예측'],
  },
  {
    id: 'pdf',
    label: 'PDF 생성',
    badge: '자동화',
    badgeBg: '#FFF8E6',
    badgeColor: '#B8860B',
    accent: '#FFC62A',
    title: '소비 내역을 PDF로 즉시 출력',
    desc: '입력된 소비 내역 데이터를 깔끔한 PDF 리포트로 자동 생성합니다.\n지출 내역을 보고서 형태로 저장하고 언제든 다운로드할 수 있습니다.',
    img: '/screenshots/pdf.png',
    to: '/app/receipts',
    features: ['PDF 리포트 생성', '다운로드 & 공유'],
    reverse: true,
  },
]

const simple = [
  { icon: Wallet,         title: '금융상품 비교', desc: '예금·적금 최고금리 TOP 상품을 한눈에', to: '/app/products', accent: '#57E0C3' },
  { icon: TrendingUp,     title: '실시간 주식',   desc: '국내 주식 시세·차트 실시간 확인',        to: '/app/stocks',   accent: '#FFC62A' },
  { icon: Coins,          title: '금 시세',       desc: '국제 금 시세와 환율 실시간 추적',         to: '/app/gold',     accent: '#57E0C3' },
  { icon: Newspaper,      title: '금융 뉴스',     desc: 'AI 요약 금융·경제 뉴스 모아보기',        to: '/app/news',     accent: '#FFC62A' },
  { icon: MessagesSquare, title: '커뮤니티',      desc: '주식 토론과 자유로운 이야기',             to: '/app/community',accent: '#57E0C3' },
  { icon: MapPin,         title: '지점 찾기',     desc: '내 주변 은행·ATM 위치 검색',             to: '/app/branches', accent: '#FFC62A' },
]
</script>

<template>
  <div class="page">

    <!-- ══════════ HERO 인트로 (랜딩페이지와 동일한 로고/스크롤) ══════════ -->
    <section class="intro">
      <!-- Background blur clouds -->
      <div class="cloud cloud-yellow hero-cloud-1" :class="{ show: cloudOn }"></div>
      <div class="cloud cloud-mint hero-cloud-2" :class="{ show: cloudOn }"></div>

      <div class="center-block">
        <p class="descriptor" :class="{ show: cloudOn }">PERSONAL FINANCE PLATFORM</p>

        <!-- 로고: 점 + 점 + 웃는 곡선 -->
        <svg class="logo-icon" viewBox="0 0 100 80" xmlns="http://www.w3.org/2000/svg">
          <circle class="dot" :class="{ show: yellowOn }" cx="28" cy="24" r="14" fill="#FFC62A" />
          <circle class="dot" :class="{ show: mintOn }"   cx="72" cy="24" r="14" fill="#57E0C3" />
          <path class="smile" :class="{ drawn: smileOn }"
                d="M 10,56 Q 50,82 90,56"
                stroke="#111827" stroke-width="7" fill="none" stroke-linecap="round" />
        </svg>

        <!-- 브랜드명 — 한 글자씩 등장 -->
        <h1 class="brand">
          <span v-for="(l, i) in ['m','o','n','i']" :key="i"
                class="bltr" :class="{ show: lettersOn > i }">{{ l }}</span>
        </h1>

        <!-- 슬로건 -->
        <p class="tagline" :class="{ show: taglineOn }">내 돈의 흐름을 더 똑똑하게, <em>moni</em></p>
      </div>

      <!-- 스크롤 아이콘 (랜딩페이지와 동일) -->
      <div class="scroll-icon" :class="{ show: scrollOn }">
        <svg viewBox="0 0 26 42" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="1" y="1" width="24" height="40" rx="12" stroke="#cfcfcf" stroke-width="1.5" />
          <circle class="wheel" cx="13" cy="11" r="2.6" fill="#bdbdbd" />
        </svg>
      </div>
    </section>

    <!-- ══════════ FEATURED 서비스 (스크린샷) ══════════ -->
    <section class="features-wrap">
      <div class="features-header">
        <div class="features-badge">핵심 기능</div>
        <h2 class="features-title">moni의 <em>강력한 기능</em>을 경험하세요</h2>
        <p class="features-sub">AI와 머신러닝이 결합된 스마트 금융 분석 도구</p>
      </div>

      <div v-for="item in featured" :key="item.id"
        class="feat-row" :class="{ reverse: item.reverse }">

        <!-- 텍스트 -->
        <div class="feat-text">
          <span class="feat-badge" :style="`background:${item.badgeBg};color:${item.badgeColor}`">{{ item.badge }}</span>
          <p class="feat-label" :style="`color:${item.badgeColor}`">{{ item.label }}</p>
          <h3 class="feat-title">{{ item.title }}</h3>
          <p class="feat-desc">{{ item.desc }}</p>
          <ul class="feat-chips">
            <li v-for="f in item.features" :key="f" class="feat-chip" :style="`border-color:${item.accent}55;color:${item.badgeColor}`">
              <span class="feat-dot" :style="`background:${item.accent}`"></span>{{ f }}
            </li>
          </ul>
          <RouterLink :to="item.to" class="feat-btn" :style="`background:${item.accent};color:#111827`">
            바로가기 →
          </RouterLink>
        </div>

        <!-- 스크린샷 -->
        <div class="feat-shot">
          <div class="shot-wrap" :style="`--accent:${item.accent}`">
            <img
              :src="item.img"
              :alt="item.label + ' 화면'"
              class="shot-img"
              @error="onImgError"
            />
            <!-- 이미지 없을 때 placeholder -->
            <div class="shot-placeholder">
              <p class="ph-text">{{ item.label }} 스크린샷</p>
              <p class="ph-hint">fronted/public/screenshots/{{ item.id }}.png</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ══════════ 기타 서비스 카드 ══════════ -->
    <section class="simple-wrap">
      <div class="features-header">
        <div class="features-badge">더 많은 기능</div>
        <h2 class="features-title">모든 금융 정보를 <em class="accent-yellow">한 곳에서</em></h2>
      </div>
      <div class="simple-grid">
        <RouterLink v-for="s in simple" :key="s.title" :to="s.to" class="simple-card">
          <component :is="s.icon" class="simple-icon" :size="40" :stroke-width="1.5"
                     :style="`color:${s.accent}`" />
          <p class="simple-title">{{ s.title }}</p>
          <p class="simple-desc">{{ s.desc }}</p>
          <span class="simple-arrow" :style="`color:${s.accent}`">→</span>
        </RouterLink>
      </div>
    </section>

    <!-- ══════════ CTA ══════════ -->
    <section class="cta-wrap">
      <div class="cloud cloud-mint cta-cloud-1"></div>
      <div class="cloud cloud-yellow cta-cloud-2"></div>

      <!-- 로고: 랜딩페이지와 동일 -->
      <svg class="cta-logo-svg" viewBox="0 0 100 80" fill="none">
        <circle cx="28" cy="24" r="14" fill="#FFC62A"/>
        <circle cx="72" cy="24" r="14" fill="#57E0C3"/>
        <path d="M 10,56 Q 50,82 90,56" stroke="#111827" stroke-width="7" stroke-linecap="round" fill="none"/>
      </svg>
      <h2 class="cta-title">지금 바로 시작해보세요</h2>
      <p class="cta-sub">moni와 함께 더 스마트한 금융 생활을 경험하세요</p>
      <div class="cta-btns">
        <button class="cta-primary" @click="goStart">홈으로</button>

      </div>
    </section>

  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@500;600;700&display=swap');

.page {
  font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
  background: #fafafa;
  color: #111827;
  width: 100%;
  overflow-x: hidden;
}

/* ─── Background blur clouds (랜딩페이지와 동일) ─────────── */
.cloud {
  position: absolute;
  width: 1180px;
  height: 620px;
  filter: blur(85px);
  opacity: 0.34;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(150px 150px at 14% 64%, var(--c) 68%, transparent 100%),
    radial-gradient(190px 190px at 33% 48%, var(--c) 68%, transparent 100%),
    radial-gradient(205px 205px at 52% 56%, var(--c) 68%, transparent 100%),
    radial-gradient(180px 180px at 70% 50%, var(--c) 68%, transparent 100%),
    radial-gradient(150px 150px at 87% 64%, var(--c) 68%, transparent 100%),
    radial-gradient(180px 95px  at 50% 80%, var(--c) 68%, transparent 100%);
  background-repeat: no-repeat;
  animation: floatCloud 6s ease-in-out infinite;
}
.cloud-yellow { --c: #FFD24D; }
.cloud-mint   { --c: #6CE9CF; }

@keyframes floatCloud {
  0%   { transform: translateX(0); }
  25%  { transform: translateX(110px); }
  50%  { transform: translateX(0); }
  75%  { transform: translateX(-110px); }
  100% { transform: translateX(0); }
}

/* ─── INTRO ─────────────────────────── */
.intro {
  height: 100dvh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #fafafa;
  position: relative;
  overflow: hidden;
}
.intro .cloud { opacity: 0; transition: opacity 1.8s ease; }
.intro .cloud.show { opacity: 0.34; }
.hero-cloud-1 { top: -200px; left: -340px; }
.hero-cloud-2 { bottom: -220px; right: -340px; animation-delay: -3s; }

.center-block {
  position: relative; z-index: 2;
  display: flex; flex-direction: column;
  align-items: center; gap: 0;
}
.descriptor {
  font-size: 11px; font-weight: 700;
  letter-spacing: 0.42em; color: #0D9B7A;
  text-transform: uppercase; margin: 0 0 26px;
  opacity: 0; transition: opacity 0.9s ease;
}
.descriptor.show { opacity: 0.65; }

.logo-icon { width: 150px; }
/* 점 등장 */
.dot {
  transform-origin: center;
  transform: scale(0); opacity: 0;
  transition: transform 0.4s cubic-bezier(0.34,1.45,0.64,1), opacity 0.3s ease;
}
.dot.show { transform: scale(1); opacity: 1; }
/* 웃는 곡선 그리기 */
.smile {
  stroke-dasharray: 170; stroke-dashoffset: 170;
  transition: stroke-dashoffset 0.95s cubic-bezier(0.4,0,0.2,1);
}
.smile.drawn { stroke-dashoffset: 0; }

/* 브랜드명 — 한 글자씩 써지듯 등장 (Fredoka) */
.brand {
  display: flex; margin: 14px 0 0;
  font-family: 'Fredoka', 'Baloo 2', sans-serif;
  font-size: clamp(64px, 11vw, 88px);
  font-weight: 600; line-height: 1;
  color: #111827; letter-spacing: 0.005em;
}
.bltr {
  display: inline-block;
  opacity: 0; transform: translateY(8px) scale(0.82); filter: blur(4px);
  transition: opacity 0.45s ease, transform 0.45s cubic-bezier(0.34,1.3,0.64,1), filter 0.45s ease;
}
.bltr.show { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }

.tagline {
  font-size: 16px; color: #6b7280;
  letter-spacing: 0.01em; text-align: center;
  margin: 18px 0 0; opacity: 0; transform: translateY(8px);
  transition: opacity 0.7s ease, transform 0.7s ease;
}
.tagline.show { opacity: 1; transform: none; }
.tagline em { font-style: normal; color: #57E0C3; font-weight: 700; }

/* 스크롤 아이콘 (랜딩페이지와 동일) */
.scroll-icon {
  position: absolute; z-index: 2; bottom: 36px;
  opacity: 0; transition: opacity 1s ease;
}
.scroll-icon.show { opacity: 1; }
.scroll-icon svg { width: 26px; height: 42px; }
.wheel { animation: scrollWheel 2s ease infinite; }
@keyframes scrollWheel {
  0%   { transform: translateY(0);    opacity: 1; }
  50%  { transform: translateY(11px); opacity: 0.2; }
  100% { transform: translateY(0);    opacity: 1; }
}

/* ─── FEATURED SERVICES ─────────────── */
.features-wrap {
  background: #ffffff;
  padding: 100px 5% 80px;
}
.features-header {
  text-align: center;
  margin-bottom: 72px;
}
.features-badge {
  display: inline-block;
  padding: 5px 15px; border-radius: 999px;
  font-size: 0.72rem; font-weight: 700;
  background: #DFFAF4; color: #0D9B7A;
  margin-bottom: 16px; letter-spacing: 0.05em;
}
.features-title {
  font-size: clamp(1.6rem, 4vw, 2.4rem);
  font-weight: 900; color: #111827;
  margin: 0 0 12px; line-height: 1.25;
}
.features-title em { font-style: normal; color: #0D9B7A; }
.features-title em.accent-yellow { color: #FFC62A; }
.features-sub { font-size: 0.95rem; color: #9ca3af; margin: 0; }

.feat-row {
  display: flex;
  align-items: center;
  gap: 64px;
  max-width: 1100px;
  margin: 0 auto 100px;
}
.feat-row.reverse { flex-direction: row-reverse; }

.feat-text { flex: 1; min-width: 0; }
.feat-badge {
  display: inline-block;
  padding: 3px 10px; border-radius: 999px;
  font-size: 0.7rem; font-weight: 700;
  margin-bottom: 10px;
}
.feat-label {
  font-size: 0.8rem; font-weight: 700;
  letter-spacing: 0.08em; margin: 0 0 8px;
  text-transform: uppercase;
}
.feat-title {
  font-size: clamp(1.4rem, 2.5vw, 1.9rem);
  font-weight: 900; color: #111827;
  margin: 0 0 16px; line-height: 1.25;
}
.feat-desc {
  font-size: 0.9rem; color: #6b7280;
  line-height: 1.75; margin: 0 0 24px;
  white-space: pre-line;
}
.feat-chips { list-style: none; padding: 0; margin: 0 0 28px; display: flex; flex-direction: column; gap: 8px; }
.feat-chip {
  display: flex; align-items: center; gap: 8px;
  font-size: 0.82rem; font-weight: 600;
  padding: 6px 12px; border-radius: 8px;
  border: 1px solid;
  width: fit-content;
}
.feat-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.feat-btn {
  display: inline-flex; align-items: center;
  padding: 11px 26px; border-radius: 14px;
  font-size: 0.88rem; font-weight: 700;
  text-decoration: none; transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 6px 18px rgba(0,0,0,0.08);
}
.feat-btn:hover { transform: translateY(-2px); box-shadow: 0 10px 24px rgba(0,0,0,0.12); }

/* 스크린샷 영역 */
.feat-shot { flex: 1.2; min-width: 0; }
.shot-wrap {
  position: relative;
  border-radius: 20px;
  overflow: hidden;
  border: 1px solid #ececec;
  box-shadow: 0 20px 50px rgba(17,24,39,0.10);
  aspect-ratio: 16/10;
  background: #f4f6f8;
}
.shot-img { width: 100%; height: 100%; object-fit: cover; display: block; }
.shot-wrap.no-image .shot-img { display: none; }
.shot-placeholder {
  display: none;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%; height: 100%;
  padding: 24px;
  text-align: center;
}
.shot-wrap.no-image .shot-placeholder { display: flex; }
.shot-wrap:not(.no-image) .shot-placeholder { display: flex; }
.shot-wrap:not(.no-image) .shot-img { position: absolute; inset: 0; }
.ph-icon { font-size: 2.5rem; opacity: 0.35; }
.ph-text { font-size: 0.9rem; font-weight: 700; color: #9ca3af; margin: 0; }
.ph-hint {
  font-size: 0.72rem; color: #bcc2cc;
  font-family: monospace; margin: 0;
  background: #eef0f3;
  padding: 4px 10px; border-radius: 6px;
}

/* ─── SIMPLE SERVICE GRID ────────────── */
.simple-wrap {
  background: #fafafa;
  padding: 100px 5% 80px;
  border-top: 1px solid #ececec;
}
.simple-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  max-width: 1100px;
  margin: 0 auto;
}
.simple-card {
  display: flex; flex-direction: column; gap: 10px;
  padding: 24px; border-radius: 20px;
  background: #ffffff;
  border: 1px solid #ececec;
  text-decoration: none;
  transition: border-color 0.25s, transform 0.25s, box-shadow 0.25s;
}
.simple-card:hover {
  border-color: #d8dbe0;
  transform: translateY(-3px);
  box-shadow: 0 14px 30px rgba(17,24,39,0.08);
}
.simple-icon {
  display: block;
  margin-bottom: 4px;
}
.simple-title { font-size: 0.95rem; font-weight: 800; color: #111827; margin: 0; }
.simple-desc  { font-size: 0.8rem; color: #9ca3af; margin: 0; line-height: 1.55; flex: 1; }
.simple-arrow { font-size: 1rem; font-weight: 700; margin-top: 4px; }

/* ─── CTA ────────────────────────────── */
.cta-wrap {
  position: relative;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 18px;
  padding: 120px 24px;
  background: #ffffff;
  border-top: 1px solid #ececec;
  text-align: center;
  overflow: hidden;
}
.cta-cloud-1 { top: -260px; left: -380px; opacity: 0.22; }
.cta-cloud-2 { bottom: -260px; right: -380px; opacity: 0.22; animation-delay: -3s; }
.cta-logo-svg { position: relative; z-index: 1; width: 66px; margin-bottom: 6px; }
.cta-title {
  position: relative; z-index: 1;
  font-size: clamp(1.8rem, 4vw, 2.8rem);
  font-weight: 900; color: #111827; margin: 0;
}
.cta-sub {
  position: relative; z-index: 1;
  font-size: 1rem; color: #9ca3af; margin: 0;
}
.cta-btns {
  position: relative; z-index: 1;
  display: flex; gap: 12px; flex-wrap: wrap;
  justify-content: center; margin-top: 8px;
}
.cta-primary {
  padding: 15px 48px; border-radius: 16px;
  background: #FFC62A; color: #111827;
  border: none; font-size: 1rem; font-weight: 700;
  cursor: pointer; font-family: inherit;
  box-shadow: 0 8px 24px rgba(255,198,42,0.28);
  transition: transform 0.2s, box-shadow 0.2s;
}
.cta-primary:hover { transform: translateY(-2px); box-shadow: 0 12px 28px rgba(255,198,42,0.36); }
.cta-secondary {
  padding: 15px 32px; border-radius: 16px;
  border: 1.5px solid #e5e7eb; color: #6b7280;
  font-size: 1rem; font-weight: 700;
  text-decoration: none;
  transition: border-color 0.2s, color 0.2s;
}
.cta-secondary:hover { border-color: #cbd0d8; color: #111827; }

@media (max-width: 768px) {
  .feat-row, .feat-row.reverse { flex-direction: column; gap: 36px; }
  .feat-shot { width: 100%; }
  .features-wrap, .simple-wrap { padding: 72px 5% 60px; }
  .simple-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 480px) {
  .simple-grid { grid-template-columns: 1fr; }
}
</style>
