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
const svcOn        = ref(false)

let raf            = null
let cleanupResize  = () => {}
let obs            = null

function sleep(ms) { return new Promise(r => setTimeout(r, ms)) }

// ── 파티클(별자리) 캔버스 ────────────────────────────────
function initParticles() {
  const el = canvasEl.value
  if (!el) return
  const ctx = el.getContext('2d')

  let W = el.width  = el.offsetWidth
  let H = el.height = el.offsetHeight

  const onResize = () => {
    W = el.width  = el.offsetWidth
    H = el.height = el.offsetHeight
  }
  window.addEventListener('resize', onResize)

  const N = 90, MAX = 175
  const pts = Array.from({ length: N }, () => ({
    x:  Math.random() * W,
    y:  Math.random() * H,
    vx: (Math.random() - 0.5) * 0.35,
    vy: (Math.random() - 0.5) * 0.35,
    r:  Math.random() * 1.2 + 0.4,
  }))

  function tick() {
    ctx.clearRect(0, 0, W, H)

    for (const p of pts) {
      p.x += p.vx; p.y += p.vy
      if (p.x < 0 || p.x > W) p.vx *= -1
      if (p.y < 0 || p.y > H) p.vy *= -1
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
      ctx.fillStyle = 'rgba(175, 212, 240, 0.7)'
      ctx.fill()
    }

    for (let i = 0; i < N; i++) {
      for (let j = i + 1; j < N; j++) {
        const dx = pts[i].x - pts[j].x
        const dy = pts[i].y - pts[j].y
        const d  = Math.sqrt(dx * dx + dy * dy)
        if (d < MAX) {
          const a = (1 - d / MAX) * 0.27
          ctx.beginPath()
          ctx.moveTo(pts[i].x, pts[i].y)
          ctx.lineTo(pts[j].x, pts[j].y)
          ctx.strokeStyle = `rgba(105, 160, 215, ${a})`
          ctx.lineWidth   = 0.55
          ctx.stroke()
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

  await sleep(600)

  descriptorOn.value = true      // "PERSONAL FINANCE" 레이블 페이드인
  await sleep(480)

  for (let i = 1; i <= 4; i++) { // m → o → n → i 천천히 등장
    lettersOn.value = i
    await sleep(200)
  }

  await sleep(1100)              // 마지막 글자 트랜지션 완료 대기

  accentOn.value  = true         // 액센트 라인 + 슬로건 동시 등장
  taglineOn.value = true

  await sleep(620)
  scrollOn.value = true

  const el = document.getElementById('svc-dark')
  if (el) {
    obs = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) { svcOn.value = true; obs.disconnect() } },
      { threshold: 0.1 }
    )
    obs.observe(el)
  }
})

onUnmounted(() => {
  cleanupResize()
  if (raf) cancelAnimationFrame(raf)
  obs?.disconnect()
})

const services = [
  { emoji: '📋', iconBg: 'rgba(255,193,8,0.10)',   accent: '#FFC108', stat: '1,245+', label: '등록 금융상품', desc: '다양한 상품을 한눈에 비교' },
  { emoji: '📈', iconBg: 'rgba(38,198,162,0.10)',  accent: '#26C6A2', stat: '실시간',  label: '주식 정보',   desc: '실시간 시세와 심층 분석' },
  { emoji: '💳', iconBg: 'rgba(107,142,255,0.10)', accent: '#6B8EFF', stat: '지출',    label: '관리',        desc: '소비 패턴을 시각화' },
  { emoji: '🛡️', iconBg: 'rgba(167,139,250,0.10)',accent: '#A78BFA', stat: 'AI',      label: '자산 분석',   desc: '스마트한 금융 어시스턴트' },
]

function goStart() {
  router.push(localStorage.getItem('access') ? '/app/home' : '/login')
}
</script>

<template>
  <div class="page">

    <!-- ════════════ INTRO ════════════ -->
    <section class="intro">
      <!-- 파티클 캔버스: 맨 아래 레이어 -->
      <canvas ref="canvasEl" class="stars" />
      <div class="bg-glow" />

      <div class="center-block">

        <!-- 상단 디스크립터 레이블 -->
        <p class="descriptor" :class="{ show: descriptorOn }">
          PERSONAL FINANCE
        </p>

        <!-- moni: 글자별 클립 리빌 -->
        <div class="moni-text" aria-label="moni">
          <span v-for="(l, i) in ['m','o','n','i']" :key="i" class="lc">
            <span class="lt" :class="{ show: lettersOn > i }">{{ l }}</span>
          </span>
        </div>

        <!-- 액센트 구분선 -->
        <div class="accent-line" :class="{ show: accentOn }" />

        <!-- 슬로건 -->
        <p class="tagline" :class="{ show: taglineOn }">
          내 돈의 흐름을 더 똑똑하게, <em>moni</em>
        </p>

      </div>

      <!-- 스크롤 유도 -->
      <div class="scroll-hint" :class="{ show: scrollOn }">
        <span class="scroll-label">SCROLL</span>
        <svg class="scroll-mouse" viewBox="0 0 24 38" fill="none">
          <rect x="1" y="1" width="22" height="36" rx="11"
                stroke="rgba(255,255,255,0.18)" stroke-width="1.5"/>
          <rect x="10.5" y="7" width="3" height="7" rx="1.5"
                fill="rgba(255,255,255,0.3)">
            <animate attributeName="y"       values="7;14;7"  dur="1.6s" repeatCount="indefinite"/>
            <animate attributeName="opacity" values="1;0.1;1" dur="1.6s" repeatCount="indefinite"/>
          </rect>
        </svg>
        <svg class="scroll-arrow" viewBox="0 0 18 10" fill="none">
          <path d="M1 1L9 9L17 1"
                stroke="rgba(255,255,255,0.18)" stroke-width="1.6" stroke-linecap="round"/>
        </svg>
      </div>

    </section>

    <!-- ════════════ SERVICES ════════════ -->
    <section id="svc-dark" class="svc" :class="{ visible: svcOn }">
      <div class="svc-glow" />
      <div class="svc-divider" />

      <div class="svc-headline">
        <h2>똑똑한 금융 생활의 시작,</h2>
        <h2><em>MONI</em>와 함께하세요</h2>
      </div>

      <div class="svc-cards">
        <div v-for="(s, i) in services" :key="i"
             class="svc-card" :style="`--d: ${i * 0.14 + 0.3}s`">
          <div class="svc-icon-box" :style="`background: ${s.iconBg}`">
            <span class="svc-emoji">{{ s.emoji }}</span>
          </div>
          <strong class="svc-stat" :style="`color: ${s.accent}`">{{ s.stat }}</strong>
          <p class="svc-label">{{ s.label }}</p>
          <p class="svc-desc">{{ s.desc }}</p>
        </div>
      </div>

      <button class="cta-btn" @click="goStart">시작하기 →</button>
    </section>

  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@900&display=swap');

/* ─── 기본 ──────────────────────────────────────────────── */
.page {
  font-family: 'Nunito', sans-serif;
  background: #07080f;
  color: #c8d0e8;
  width: 100%;
  overflow-x: hidden;
}

/* ─── INTRO ─────────────────────────────────────────────── */
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

/* ── 파티클 캔버스 ── */
.stars {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
}

/* 배경 환경광: 캔버스 위, 텍스트 아래 */
.bg-glow {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 1;
  background:
    radial-gradient(ellipse 70% 50% at 50% 44%,
      rgba(38, 198, 162, 0.048) 0%,
      transparent 65%),
    radial-gradient(ellipse 40% 30% at 50% 44%,
      rgba(200, 208, 232, 0.028) 0%,
      transparent 70%);
}

/* 중앙 블록: 파티클·글로우 위에 표시 */
.center-block {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
}

/* ── 디스크립터 레이블 ── */
.descriptor {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.48em;
  color: rgba(200, 208, 232, 0.28);
  text-transform: uppercase;
  margin: 0 0 20px;
  opacity: 0;
  transition: opacity 0.7s ease;
}
.descriptor.show { opacity: 1; }

/* ── moni 클립 리빌 ── */
.moni-text {
  display: flex;
  align-items: flex-end;
  /* 글자 간격은 폰트 어드밴스 그대로 사용 */
}

/* 클리핑 없이 그냥 인라인 블록 — 뿅 없는 페이드 */
.lc {
  display: block;
}

.lt {
  display: block;
  font-family: 'M PLUS Rounded 1c', 'Nunito', sans-serif;
  font-size: clamp(80px, 14vw, 112px);
  font-weight: 900;
  line-height: 1.0;
  color: #c8d0e8;
  letter-spacing: 0.02em;
  opacity: 0;
  transform: translateY(14px);
  /* 은은하게 천천히: 1.4s ease-out */
  transition:
    opacity   1.4s ease-out,
    transform 1.4s ease-out;
  will-change: opacity, transform;
}
.lt.show {
  opacity: 1;
  transform: translateY(0);
}

/* ── 액센트 라인 ── */
.accent-line {
  width: 0;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(38, 198, 162, 0.55),
    transparent
  );
  margin: 20px auto 18px;
  transition: width 1.0s cubic-bezier(0.4, 0, 0.2, 1) 0.1s;
}
.accent-line.show { width: 60px; }

/* ── 슬로건 ── */
.tagline {
  font-size: 13.5px;
  color: rgba(200, 208, 232, 0.38);
  letter-spacing: 0.025em;
  text-align: center;
  margin: 0;
  opacity: 0;
  transform: translateY(6px);
  transition: opacity 0.8s ease 0.2s, transform 0.8s ease 0.2s;
}
.tagline.show { opacity: 1; transform: none; }
.tagline em {
  font-style: normal;
  color: #26C6A2;
  font-weight: 700;
}

/* ── 스크롤 유도 ── */
.scroll-hint {
  position: absolute;
  z-index: 2;
  bottom: 34px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.9s ease;
}
.scroll-hint.show { opacity: 1; }
.scroll-label {
  font-size: 9px;
  letter-spacing: 0.26em;
  color: rgba(255, 255, 255, 0.18);
  font-weight: 700;
}
.scroll-mouse { width: 20px; }
.scroll-arrow { width: 14px; margin-top: 2px; }


/* ─── SERVICES ──────────────────────────────────────────── */
.svc {
  min-height: 100dvh;
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 56px;
  padding: 88px 28px;
  background: #0b0c18;
  overflow: hidden;
}

.svc-glow {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: radial-gradient(ellipse 55% 35% at 50% 55%,
    rgba(255, 193, 8, 0.038) 0%, transparent 70%);
}
.svc-divider {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 160px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(38,198,162,0.4), transparent);
}

/* 메인 문구 */
.svc-headline {
  position: relative;
  z-index: 1;
  text-align: center;
  line-height: 1.28;
  opacity: 0;
  transform: translateY(28px);
  transition: opacity 0.8s ease, transform 0.8s ease;
}
.svc.visible .svc-headline { opacity: 1; transform: none; }
.svc-headline h2 {
  font-size: clamp(24px, 5vw, 38px);
  font-weight: 900;
  color: #dde1ef;
  margin: 0;
}
.svc-headline em {
  font-style: normal;
  background: linear-gradient(135deg, #26C6A2 0%, #2dd4bf 55%, #6ee7b7 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

/* 서비스 카드 */
.svc-cards {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  justify-content: center;
}
.svc-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  width: 148px;
  padding: 28px 16px 24px;
  background: rgba(255, 255, 255, 0.034);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 20px;
  text-align: center;
  opacity: 0;
  transform: translateY(30px);
  transition:
    opacity      0.55s ease var(--d, 0s),
    transform    0.55s ease var(--d, 0s),
    background   0.3s,
    border-color 0.3s,
    box-shadow   0.3s;
}
.svc.visible .svc-card { opacity: 1; transform: none; }
.svc-card:hover {
  background: rgba(255,255,255,0.065);
  border-color: rgba(255,255,255,0.13);
  box-shadow: 0 14px 44px rgba(0,0,0,0.36);
  transform: translateY(-4px);
}
.svc-icon-box {
  width: 60px; height: 60px;
  border-radius: 18px;
  display: flex; align-items: center; justify-content: center;
}
.svc-emoji  { font-size: 27px; }
.svc-stat   { display: block; font-size: 21px; font-weight: 900; line-height: 1; }
.svc-label  { font-size: 13px; font-weight: 700; color: rgba(221,225,239,0.82); margin: 0; }
.svc-desc   { font-size: 11.5px; color: rgba(221,225,239,0.36); margin: 0; line-height: 1.5; }

/* CTA */
.cta-btn {
  position: relative; z-index: 1;
  padding: 15px 58px;
  background: #FFC108;
  color: #07080f;
  border: none;
  border-radius: 14px;
  font-size: 15px; font-weight: 800;
  font-family: 'Nunito', sans-serif;
  letter-spacing: 0.04em;
  cursor: pointer;
  opacity: 0;
  box-shadow: 0 0 32px rgba(255,193,8,0);
  transition: opacity 0.8s ease 1.0s, background 0.25s, transform 0.25s, box-shadow 0.25s;
}
.svc.visible .cta-btn { opacity: 1; }
.cta-btn:hover {
  background: #ffd740;
  transform: translateY(-2px);
  box-shadow: 0 0 36px rgba(255,193,8,0.32);
}
.cta-btn:active { transform: translateY(0); box-shadow: none; }
</style>
