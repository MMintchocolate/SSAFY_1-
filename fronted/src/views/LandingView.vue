<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Wallet, Sparkles, TrendingUp, PieChart } from '@lucide/vue'

const router = useRouter()

// ── 인트로 애니메이션 상태 ──────────────────────────────
const cloudOn   = ref(false)  // 배경 블러 (로고와 함께 생성)
const yellowOn  = ref(false)  // Step1: 노란 점
const mintOn    = ref(false)  // Step2: 민트 점
const smileOn   = ref(false)  // Step3: 웃는 곡선
const lettersOn = ref(0)      // Step4: moni 로고 텍스트 (한 글자씩)
const taglineOn = ref(false)  // Step5: 슬로건
const scrollOn  = ref(false)  // 스크롤 아이콘

// ── 서비스 섹션 ────────────────────────────────────────
const svcOn = ref(false)
let obs = null

function sleep(ms) { return new Promise(r => setTimeout(r, ms)) }

onMounted(async () => {
  // 전체 로고 애니메이션 (여유 있는 템포)
  await sleep(400)            // 진입 직후 짧은 정적
  cloudOn.value = true        // 배경 블러도 로고와 함께 서서히 생성
  yellowOn.value = true       // 노란 점
  await sleep(450)
  mintOn.value = true         // 민트 점
  await sleep(330)
  smileOn.value = true        // 웃는 곡선 (천천히 그려짐)
  await sleep(560)
  // moni 로고 — 한 글자씩 써지듯 등장
  for (let i = 1; i <= 4; i++) {
    lettersOn.value = i
    await sleep(165)
  }
  await sleep(360)
  taglineOn.value = true      // 슬로건
  await sleep(480)
  scrollOn.value = true       // 스크롤 아이콘

  // 서비스 섹션 스크롤 트리거
  const el = document.getElementById('svc')
  if (el) {
    obs = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) { svcOn.value = true; obs.disconnect() } },
      { threshold: 0.15 }
    )
    obs.observe(el)
  }
})

onUnmounted(() => obs?.disconnect())

// ── 서비스 데이터 ──────────────────────────────────────
const services = [
  { icon: Wallet,     text: '+200 금융상품',   accent: '#57E0C3' },
  { icon: Sparkles,   text: 'AI 투자 인사이트', accent: '#FFC62A' },
  { icon: TrendingUp, text: '실시간 주식 정보', accent: '#57E0C3' },
  { icon: PieChart,   text: '소비 패턴 분석',   accent: '#FFC62A' },
]

function goStart() {
  router.push('/app/home')
}
</script>

<template>
  <div class="page">

    <!-- ════════════════ SECTION 1: HERO ════════════════ -->
    <section class="hero">
      <!-- Background blur clouds (로고와 함께 생성) -->
      <div class="cloud cloud-yellow hero-cloud-1" :class="{ show: cloudOn }"></div>
      <div class="cloud cloud-mint hero-cloud-2" :class="{ show: cloudOn }"></div>

      <div class="hero-inner">
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
        <p class="tagline" :class="{ show: taglineOn }">
          내 돈의 흐름을 더 똑똑하게, <em>moni</em>
        </p>
      </div>

      <!-- 스크롤 아이콘 -->
      <div class="scroll-icon" :class="{ show: scrollOn }">
        <svg viewBox="0 0 26 42" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="1" y="1" width="24" height="40" rx="12"
                stroke="#cfcfcf" stroke-width="1.5" />
          <circle class="wheel" cx="13" cy="11" r="2.6" fill="#bdbdbd" />
        </svg>
      </div>
    </section>

    <!-- ════════════════ SECTION 2: SERVICE INTRO ════════════════ -->
    <section id="svc" class="svc" :class="{ visible: svcOn }">
      <!-- Background blur clouds -->
      <div class="cloud cloud-yellow svc-cloud-1"></div>
      <div class="cloud cloud-mint svc-cloud-2"></div>

      <!-- 제목 -->
      <h2 class="svc-title">
        <span class="t-dark">모든 금융을</span>
        <span class="t-yellow"> 한 곳에서, </span>
        <span class="t-mint">moni</span>
      </h2>

      <!-- 서비스 4컬럼 -->
      <div class="svc-row">
        <template v-for="(s, i) in services" :key="i">
          <div class="svc-col" :style="`--d: ${i * 0.28}s`">
            <component :is="s.icon" class="svc-icon" :size="68" :stroke-width="1.4"
                       :style="`color: ${s.accent}`" />
            <p class="svc-text">{{ s.text }}</p>
          </div>
          <div v-if="i < services.length - 1" class="svc-divider"></div>
        </template>
      </div>

      <!-- 시작하기 버튼 -->
      <button class="cta-btn" @click="goStart">시작하기</button>
    </section>

  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@500;600;700&display=swap');

/* ─── 기본 ──────────────────────────────────────────────── */
.page {
  font-family: 'Nunito', 'Pretendard', sans-serif;
  background: #fafafa;
  width: 100%;
  overflow-x: hidden;
}

/* ─── Background blur clouds ─────────────────────────────── */
.cloud {
  position: absolute;
  width: 1180px;
  height: 620px;
  filter: blur(85px);
  opacity: 0.34;
  pointer-events: none;
  z-index: 0;
  /* 여러 개의 둥근 덩어리를 좌우로 넓게 겹쳐 구름(뭉게구름) 실루엣 만들기 */
  background:
    radial-gradient(150px 150px at 14% 64%, var(--c) 68%, transparent 100%),
    radial-gradient(190px 190px at 33% 48%, var(--c) 68%, transparent 100%),
    radial-gradient(205px 205px at 52% 56%, var(--c) 68%, transparent 100%),
    radial-gradient(180px 180px at 70% 50%, var(--c) 68%, transparent 100%),
    radial-gradient(150px 150px at 87% 64%, var(--c) 68%, transparent 100%),
    radial-gradient(180px 95px  at 50% 80%, var(--c) 68%, transparent 100%);
  background-repeat: no-repeat;
  /* 그 자리에서 두둥실 떠다니는 느낌 (제자리 부유) */
  animation: floatCloud 6s ease-in-out infinite;
}
.cloud-yellow { --c: #FFD24D; }
.cloud-mint   { --c: #6CE9CF; }

/* 히어로 블러: 로고와 함께 서서히 생성 */
.hero .cloud { opacity: 0; transition: opacity 1.8s ease; }
.hero .cloud.show { opacity: 0.34; }

/* 크기 변화 없이 상하좌우로 두둥실 떠다니는 느낌 (제자리 부유, 한 바퀴 돌고 복귀) */
@keyframes floatCloud {
  0%   { transform: translateX(0); }
  25%  { transform: translateX(110px); }
  50%  { transform: translateX(0); }
  75%  { transform: translateX(-110px); }
  100% { transform: translateX(0); }
}

/* ─── HERO ──────────────────────────────────────────────── */
.hero {
  position: relative;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #fafafa;
  overflow: hidden;
}
.hero-cloud-1 { top: -200px; left: -340px; }
.hero-cloud-2 { bottom: -220px; right: -340px; animation-delay: -8s; }

.hero-inner {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 28px;
}

.logo-icon { width: 168px; }

/* 점 등장: scale + opacity (0.4s) */
.dot {
  transform-origin: center;
  transform: scale(0);
  opacity: 0;
  transition:
    transform 0.4s cubic-bezier(0.34, 1.45, 0.64, 1),
    opacity   0.3s ease;
}
.dot.show { transform: scale(1); opacity: 1; }

/* 웃는 곡선 그리기 (천천히) */
.smile {
  stroke-dasharray: 170;
  stroke-dashoffset: 170;
  transition: stroke-dashoffset 0.95s cubic-bezier(0.4, 0, 0.2, 1);
}
.smile.drawn { stroke-dashoffset: 0; }

/* 브랜드명 — 한 글자씩 써지듯 등장 (Fredoka: 둥근 지오메트릭 로고체) */
.brand {
  display: flex;
  font-family: 'Fredoka', 'Baloo 2', 'M PLUS Rounded 1c', sans-serif;
  font-size: 84px;
  font-weight: 600;
  color: #111827;
  letter-spacing: 0.005em;
  line-height: 1;
  margin: 0;
}
.bltr {
  display: inline-block;
  opacity: 0;
  transform: translateY(8px) scale(0.82);
  filter: blur(4px);
  transition:
    opacity   0.45s ease,
    transform 0.45s cubic-bezier(0.34, 1.3, 0.64, 1),
    filter    0.45s ease;
}
.bltr.show { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }

/* 슬로건 (0.3s) */
.tagline {
  font-size: 19px;
  color: #6b7280;
  letter-spacing: 0.01em;
  text-align: center;
  margin: 0;
  opacity: 0;
  transform: translateY(8px);
  transition: opacity 0.6s ease, transform 0.6s ease;
}
.tagline.show { opacity: 1; transform: none; }
.tagline em { font-style: normal; color: #57E0C3; font-weight: 700; }

/* 스크롤 아이콘 */
.scroll-icon {
  position: absolute;
  bottom: 36px;
  z-index: 1;
  opacity: 0;
  transition: opacity 1s ease;
}
.scroll-icon.show { opacity: 1; }
.scroll-icon svg { width: 26px; height: 42px; }

/* 마우스 휠 점이 천천히 내려갔다 올라옴 */
.wheel { animation: scrollWheel 2s ease infinite; }
@keyframes scrollWheel {
  0%   { transform: translateY(0);    opacity: 1; }
  50%  { transform: translateY(11px); opacity: 0.2; }
  100% { transform: translateY(0);    opacity: 1; }
}

/* ─── SERVICE INTRO ─────────────────────────────────────── */
.svc {
  position: relative;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 64px;
  padding: 100px 28px;
  background: #fafafa;
  overflow: hidden;
}
.svc-cloud-1 { top: -180px; left: -360px; animation-delay: -4s; }
.svc-cloud-2 { bottom: -200px; right: -360px; animation-delay: -12s; }

/* 제목 */
.svc-title {
  position: relative;
  z-index: 1;
  font-size: clamp(30px, 6vw, 48px);
  font-weight: 900;
  text-align: center;
  margin: 0;
  letter-spacing: -0.01em;
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 1.1s ease, transform 1.1s cubic-bezier(0.22, 1, 0.36, 1);
}
.svc.visible .svc-title { opacity: 1; transform: none; }
.t-dark   { color: #111827; }
.t-yellow { color: #FFC62A; }
.t-mint   { color: #57E0C3; }

/* 서비스 4컬럼 (배경/박스 없음) */
.svc-row {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 0;
}

.svc-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
  padding: 0 40px;
  text-align: center;
  opacity: 0;
  transform: translateY(24px);
  transition:
    opacity   1.1s ease var(--d, 0s),
    transform 1.1s cubic-bezier(0.22, 1, 0.36, 1) var(--d, 0s);
}
.svc.visible .svc-col { opacity: 1; transform: none; }

.svc-icon { display: block; }
.svc-text {
  font-size: 19px;
  font-weight: 700;
  color: #111827;
  margin: 0;
  white-space: nowrap;
}

/* 매우 연한 구분선 */
.svc-divider {
  width: 1px;
  height: 84px;
  background: #ececec;
  flex-shrink: 0;
}

/* 시작하기 버튼 */
.cta-btn {
  position: relative;
  z-index: 1;
  width: 148px;
  height: 50px;
  background: #FFC62A;
  color: #111827;
  border: none;
  border-radius: 14px;
  font-size: 16px;
  font-weight: 700;
  font-family: 'Nunito', sans-serif;
  letter-spacing: 0.01em;
  cursor: pointer;
  box-shadow: 0 8px 24px rgba(255, 198, 42, 0.28);
  opacity: 0;
  transform: translateY(24px);
  transition:
    opacity 1.1s ease 1.4s,
    transform 0.3s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.3s ease;
}
.svc.visible .cta-btn { opacity: 1; transform: translateY(0); transition-delay: 1.4s, 0s, 0s; }
.cta-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(255, 198, 42, 0.36);
}
.cta-btn:active { transform: translateY(0); }

/* 반응형: 좁은 화면에서 구분선 숨김 + 2x2 정렬 */
@media (max-width: 720px) {
  .svc-row { gap: 36px 12px; }
  .svc-col { padding: 0 8px; flex-basis: 40%; }
  .svc-divider { display: none; }
}
</style>
