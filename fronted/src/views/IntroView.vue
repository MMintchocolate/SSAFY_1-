<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const canvasEl     = ref(null)
const descriptorOn = ref(false)
const lettersOn    = ref(0)
const accentOn     = ref(false)
const taglineOn    = ref(false)
const scrollOn     = ref(false)

let raf           = null
let cleanupResize = () => {}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)) }

function initParticles() {
  const el = canvasEl.value
  if (!el) return
  const ctx = el.getContext('2d')
  let W = el.width  = el.offsetWidth
  let H = el.height = el.offsetHeight
  const onResize = () => { W = el.width = el.offsetWidth; H = el.height = el.offsetHeight }
  window.addEventListener('resize', onResize)
  const N = 90, MAX = 175
  const pts = Array.from({ length: N }, () => ({
    x: Math.random() * W, y: Math.random() * H,
    vx: (Math.random() - 0.5) * 0.35, vy: (Math.random() - 0.5) * 0.35,
    r: Math.random() * 1.2 + 0.4,
  }))
  function tick() {
    ctx.clearRect(0, 0, W, H)
    for (const p of pts) {
      p.x += p.vx; p.y += p.vy
      if (p.x < 0 || p.x > W) p.vx *= -1
      if (p.y < 0 || p.y > H) p.vy *= -1
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
      ctx.fillStyle = 'rgba(87,224,195,0.5)'; ctx.fill()
    }
    for (let i = 0; i < N; i++) {
      for (let j = i + 1; j < N; j++) {
        const dx = pts[i].x - pts[j].x, dy = pts[i].y - pts[j].y
        const d = Math.sqrt(dx*dx + dy*dy)
        if (d < MAX) {
          ctx.beginPath(); ctx.moveTo(pts[i].x, pts[i].y); ctx.lineTo(pts[j].x, pts[j].y)
          ctx.strokeStyle = `rgba(87,224,195,${(1 - d/MAX) * 0.18})`
          ctx.lineWidth = 0.55; ctx.stroke()
        }
      }
    }
    raf = requestAnimationFrame(tick)
  }
  tick()
  return () => window.removeEventListener('resize', onResize)
}

onMounted(async () => {
  cleanupResize = initParticles() ?? (() => {})
  await sleep(150)
  descriptorOn.value = true
  await sleep(200)
  for (let i = 1; i <= 4; i++) { lettersOn.value = i; await sleep(80) }
  await sleep(300)
  accentOn.value = taglineOn.value = true
  await sleep(250)
  scrollOn.value = true
})

onUnmounted(() => {
  cleanupResize()
  if (raf) cancelAnimationFrame(raf)
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
    accent: '#FFD76A',
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
    badgeBg: '#F0EDFF',
    badgeColor: '#7C3AED',
    accent: '#A78BFA',
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
    badgeBg: '#FFF5F5',
    badgeColor: '#E5323B',
    accent: '#E5323B',
    title: '영수증·장부를 PDF로 즉시 출력',
    desc: '입력된 영수증 데이터를 깔끔한 PDF 장부로 자동 생성합니다.\n지출 내역을 보고서 형태로 저장하고 언제든 다운로드할 수 있습니다.',
    img: '/screenshots/pdf.png',
    to: '/app/receipts',
    features: ['영수증 자동 파싱', 'PDF 장부 생성', '다운로드 & 공유'],
    reverse: true,
  },
]

const simple = [
  { emoji: '📊', title: '금융상품 비교', desc: '예금·적금 최고금리 TOP 상품을 한눈에', to: '/app/products', accent: '#57E0C3' },
  { emoji: '📈', title: '실시간 주식',   desc: '국내 주식 시세·차트 실시간 확인',        to: '/app/stocks',   accent: '#FFD76A' },
  { emoji: '🥇', title: '금 시세',       desc: '국제 금 시세와 환율 실시간 추적',         to: '/app/gold',     accent: '#FFA726' },
  { emoji: '📰', title: '금융 뉴스',     desc: 'AI 요약 금융·경제 뉴스 모아보기',        to: '/app/news',     accent: '#A78BFA' },
  { emoji: '💬', title: '커뮤니티',      desc: '주식 토론과 자유로운 이야기',             to: '/app/community',accent: '#4ECBA8' },
  { emoji: '📍', title: '지점 찾기',     desc: '내 주변 은행·ATM 위치 검색',             to: '/app/branches', accent: '#60A5FA' },
]
</script>

<template>
  <div class="page">

    <!-- ══════════ HERO 인트로 ══════════ -->
    <section class="intro">
      <canvas ref="canvasEl" class="stars" />
      <div class="bg-glow" />
      <div class="center-block">
        <p class="descriptor" :class="{ show: descriptorOn }">PERSONAL FINANCE PLATFORM</p>
        <div class="moni-text" aria-label="moni">
          <span v-for="(l, i) in ['m','o','n','i']" :key="i" class="lc">
            <span class="lt" :class="{ show: lettersOn > i }">{{ l }}</span>
          </span>
        </div>
        <div class="accent-line" :class="{ show: accentOn }" />
        <p class="tagline" :class="{ show: taglineOn }">내 돈의 흐름을 더 똑똑하게, <em>moni</em></p>
      </div>
      <div class="scroll-hint" :class="{ show: scrollOn }">
        <span class="scroll-label">SCROLL</span>
        <svg class="scroll-mouse" viewBox="0 0 24 38" fill="none">
          <rect x="1" y="1" width="22" height="36" rx="11" stroke="rgba(87,224,195,0.25)" stroke-width="1.5"/>
          <rect x="10.5" y="7" width="3" height="7" rx="1.5" fill="rgba(87,224,195,0.4)">
            <animate attributeName="y" values="7;14;7" dur="1.6s" repeatCount="indefinite"/>
            <animate attributeName="opacity" values="1;0.1;1" dur="1.6s" repeatCount="indefinite"/>
          </rect>
        </svg>
        <svg class="scroll-arrow" viewBox="0 0 18 10" fill="none">
          <path d="M1 1L9 9L17 1" stroke="rgba(87,224,195,0.25)" stroke-width="1.6" stroke-linecap="round"/>
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
          <p class="feat-label" :style="`color:${item.accent}`">{{ item.label }}</p>
          <h3 class="feat-title">{{ item.title }}</h3>
          <p class="feat-desc">{{ item.desc }}</p>
          <ul class="feat-chips">
            <li v-for="f in item.features" :key="f" class="feat-chip" :style="`border-color:${item.accent}33;color:${item.accent}`">
              <span class="feat-dot" :style="`background:${item.accent}`"></span>{{ f }}
            </li>
          </ul>
          <RouterLink :to="item.to" class="feat-btn" :style="`background:${item.accent};color:${item.id === 'indicators' ? '#0F122B' : item.id === 'spending' ? '#0F122B' : 'white'}`">
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
              <div class="ph-icon">📸</div>
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
        <h2 class="features-title">모든 금융 정보를 <em>한 곳에서</em></h2>
      </div>
      <div class="simple-grid">
        <RouterLink v-for="s in simple" :key="s.title" :to="s.to" class="simple-card">
          <div class="simple-icon" :style="`background:${s.accent}18`">
            <span>{{ s.emoji }}</span>
          </div>
          <p class="simple-title">{{ s.title }}</p>
          <p class="simple-desc">{{ s.desc }}</p>
          <span class="simple-arrow" :style="`color:${s.accent}`">→</span>
        </RouterLink>
      </div>
    </section>

    <!-- ══════════ CTA ══════════ -->
    <section class="cta-wrap">
      <div class="cta-glow" />
      <svg class="cta-logo-svg" width="52" height="42" viewBox="0 0 46 38" fill="none">
        <circle cx="15" cy="9" r="6" fill="#FFA726"/>
        <circle cx="31" cy="9" r="6" fill="#4ECBA8"/>
        <path d="M7 20 Q23 36 39 20" stroke="#57E0C3" stroke-width="6" stroke-linecap="round" fill="none"/>
      </svg>
      <h2 class="cta-title">지금 바로 시작해보세요</h2>
      <p class="cta-sub">moni와 함께 더 스마트한 금융 생활을 경험하세요</p>
      <div class="cta-btns">
        <button class="cta-primary" @click="goStart">시작하기</button>
        <RouterLink to="/app/home" class="cta-secondary">홈으로</RouterLink>
      </div>
    </section>

  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@900&display=swap');

.page {
  font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
  background: #07080f;
  color: #c8d0e8;
  width: 100%;
  overflow-x: hidden;
}

/* ─── INTRO ─────────────────────────── */
.intro {
  height: 100dvh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #07080f;
  position: relative;
  overflow: hidden;
}
.stars {
  position: absolute; inset: 0;
  width: 100%; height: 100%; z-index: 0;
}
.bg-glow {
  position: absolute; inset: 0;
  pointer-events: none; z-index: 1;
  background:
    radial-gradient(ellipse 70% 50% at 50% 44%, rgba(87,224,195,0.06) 0%, transparent 65%),
    radial-gradient(ellipse 40% 30% at 50% 44%, rgba(200,208,232,0.03) 0%, transparent 70%);
}
.center-block {
  position: relative; z-index: 2;
  display: flex; flex-direction: column;
  align-items: center; gap: 0;
}
.descriptor {
  font-size: 10px; font-weight: 700;
  letter-spacing: 0.42em; color: rgba(87,224,195,0.35);
  text-transform: uppercase; margin: 0 0 20px;
  opacity: 0; transition: opacity 0.7s ease;
}
.descriptor.show { opacity: 1; }
.moni-text { display: flex; align-items: flex-end; }
.lc { display: block; }
.lt {
  display: block;
  font-family: 'M PLUS Rounded 1c', sans-serif;
  font-size: clamp(80px, 14vw, 112px);
  font-weight: 900; line-height: 1.0;
  color: #c8d0e8; letter-spacing: 0.02em;
  opacity: 0; transform: translateY(10px);
  transition: opacity 0.5s ease-out, transform 0.5s ease-out;
}
.lt.show { opacity: 1; transform: translateY(0); }
.accent-line {
  width: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(87,224,195,0.6), transparent);
  margin: 20px auto 18px;
  transition: width 1.0s cubic-bezier(0.4,0,0.2,1) 0.1s;
}
.accent-line.show { width: 72px; }
.tagline {
  font-size: 13.5px; color: rgba(200,208,232,0.38);
  letter-spacing: 0.025em; text-align: center;
  margin: 0; opacity: 0; transform: translateY(6px);
  transition: opacity 0.8s ease 0.2s, transform 0.8s ease 0.2s;
}
.tagline.show { opacity: 1; transform: none; }
.tagline em { font-style: normal; color: #57E0C3; font-weight: 700; }
.scroll-hint {
  position: absolute; z-index: 2; bottom: 34px;
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  opacity: 0; pointer-events: none; transition: opacity 0.9s ease;
}
.scroll-hint.show { opacity: 1; }
.scroll-label { font-size: 9px; letter-spacing: 0.26em; color: rgba(87,224,195,0.3); font-weight: 700; }
.scroll-mouse { width: 20px; }
.scroll-arrow { width: 14px; margin-top: 2px; }

/* ─── FEATURED SERVICES ─────────────── */
.features-wrap {
  background: #0b0c18;
  padding: 100px 5% 80px;
}
.features-header {
  text-align: center;
  margin-bottom: 72px;
}
.features-badge {
  display: inline-block;
  padding: 4px 14px; border-radius: 999px;
  font-size: 0.72rem; font-weight: 700;
  background: rgba(87,224,195,0.12); color: #57E0C3;
  margin-bottom: 16px; letter-spacing: 0.05em;
}
.features-title {
  font-size: clamp(1.6rem, 4vw, 2.4rem);
  font-weight: 900; color: #dde1ef;
  margin: 0 0 12px; line-height: 1.25;
}
.features-title em { font-style: normal; color: #57E0C3; }
.features-sub { font-size: 0.95rem; color: rgba(200,208,232,0.4); margin: 0; }

.feat-row {
  display: flex;
  align-items: center;
  gap: 64px;
  max-width: 1100px;
  margin: 0 auto 100px;
}
.feat-row.reverse { flex-direction: row-reverse; }

.feat-text {
  flex: 1;
  min-width: 0;
}
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
  font-weight: 900; color: #dde1ef;
  margin: 0 0 16px; line-height: 1.25;
}
.feat-desc {
  font-size: 0.9rem; color: rgba(200,208,232,0.5);
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
  padding: 10px 24px; border-radius: 12px;
  font-size: 0.88rem; font-weight: 700;
  text-decoration: none; transition: opacity 0.2s, transform 0.2s;
}
.feat-btn:hover { opacity: 0.85; transform: translateY(-1px); }

/* 스크린샷 영역 */
.feat-shot { flex: 1.2; min-width: 0; }

.shot-wrap {
  position: relative;
  border-radius: 20px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.07);
  box-shadow: 0 24px 64px rgba(0,0,0,0.5), 0 0 0 1px var(--accent, #57E0C3) inset;
  aspect-ratio: 16/10;
  background: rgba(255,255,255,0.03);
}
.shot-img {
  width: 100%; height: 100%;
  object-fit: cover; display: block;
}
/* 이미지 로드 실패 시 */
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
/* 이미지가 없어도 기본 placeholder 보임 (img가 로드 전까지) */
.shot-wrap:not(.no-image) .shot-placeholder { display: flex; }
.shot-wrap:not(.no-image) .shot-img { position: absolute; inset: 0; }
.ph-icon { font-size: 2.5rem; opacity: 0.3; }
.ph-text { font-size: 0.9rem; font-weight: 700; color: rgba(200,208,232,0.4); margin: 0; }
.ph-hint {
  font-size: 0.72rem; color: rgba(200,208,232,0.2);
  font-family: monospace; margin: 0;
  background: rgba(255,255,255,0.04);
  padding: 4px 10px; border-radius: 6px;
}

/* ─── SIMPLE SERVICE GRID ────────────── */
.simple-wrap {
  background: #07080f;
  padding: 100px 5% 80px;
  border-top: 1px solid rgba(255,255,255,0.05);
}
.simple-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
  max-width: 1100px;
  margin: 0 auto;
}
.simple-card {
  display: flex; flex-direction: column; gap: 10px;
  padding: 24px; border-radius: 20px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
  text-decoration: none;
  transition: background 0.25s, border-color 0.25s, transform 0.25s;
}
.simple-card:hover {
  background: rgba(255,255,255,0.06);
  border-color: rgba(255,255,255,0.12);
  transform: translateY(-3px);
}
.simple-icon {
  width: 48px; height: 48px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px;
}
.simple-title { font-size: 0.95rem; font-weight: 800; color: #dde1ef; margin: 0; }
.simple-desc  { font-size: 0.8rem; color: rgba(200,208,232,0.4); margin: 0; line-height: 1.55; flex: 1; }
.simple-arrow { font-size: 1rem; font-weight: 700; margin-top: 4px; }

/* ─── CTA ────────────────────────────── */
.cta-wrap {
  position: relative;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 20px;
  padding: 120px 24px;
  background: #0b0c18;
  border-top: 1px solid rgba(255,255,255,0.05);
  text-align: center;
  overflow: hidden;
}
.cta-glow {
  position: absolute; inset: 0; pointer-events: none;
  background: radial-gradient(ellipse 60% 50% at 50% 50%, rgba(87,224,195,0.07) 0%, transparent 70%);
}
.cta-logo-svg { position: relative; z-index: 1; margin-bottom: 4px; }
.cta-title {
  position: relative; z-index: 1;
  font-size: clamp(1.8rem, 4vw, 2.8rem);
  font-weight: 900; color: #dde1ef; margin: 0;
}
.cta-sub {
  position: relative; z-index: 1;
  font-size: 1rem; color: rgba(200,208,232,0.4); margin: 0;
}
.cta-btns {
  position: relative; z-index: 1;
  display: flex; gap: 12px; flex-wrap: wrap;
  justify-content: center; margin-top: 8px;
}
.cta-primary {
  padding: 14px 48px; border-radius: 14px;
  background: #57E0C3; color: #0F122B;
  border: none; font-size: 1rem; font-weight: 800;
  cursor: pointer; font-family: inherit;
  transition: opacity 0.2s, transform 0.2s;
}
.cta-primary:hover { opacity: 0.88; transform: translateY(-2px); }
.cta-secondary {
  padding: 14px 32px; border-radius: 14px;
  border: 1.5px solid rgba(255,255,255,0.1); color: rgba(200,208,232,0.6);
  font-size: 1rem; font-weight: 700;
  text-decoration: none;
  transition: border-color 0.2s, color 0.2s;
}
.cta-secondary:hover { border-color: rgba(255,255,255,0.2); color: #dde1ef; }

@media (max-width: 768px) {
  .feat-row, .feat-row.reverse { flex-direction: column; gap: 36px; }
  .feat-shot { width: 100%; }
  .features-wrap, .simple-wrap { padding: 72px 5% 60px; }
}
</style>
