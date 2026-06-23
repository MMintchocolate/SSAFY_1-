<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// ── 인트로 애니메이션 상태 ──────────────────────────────
const yellowOn  = ref(false)
const mintOn    = ref(false)
const smileOn   = ref(false)
const lettersOn = ref(0)      // 0~4: 나타난 글자 수
const compact   = ref(false)  // 빌드 → 소형 로고 전환
const taglineOn = ref(false)
const scrollOn  = ref(false)

// ── 서비스 섹션 ────────────────────────────────────────
const svcOn = ref(false)
let obs = null

function sleep(ms) { return new Promise(r => setTimeout(r, ms)) }

onMounted(async () => {
  await sleep(500)           // 0.5s 정적 상태

  yellowOn.value = true      // 노란 점
  await sleep(370)
  mintOn.value = true        // 민트 점
  await sleep(320)
  smileOn.value = true       // 입 그려짐
  await sleep(670)

  for (let i = 1; i <= 4; i++) {   // m → o → n → i 순서
    lettersOn.value = i
    await sleep(190)
  }

  await sleep(310)
  compact.value = true       // 로고 축소 + 글자 오른쪽 이동
  await sleep(760)
  taglineOn.value = true
  await sleep(560)
  scrollOn.value = true

  // 서비스 섹션 스크롤 트리거
  const el = document.getElementById('svc')
  if (el) {
    obs = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) { svcOn.value = true; obs.disconnect() } },
      { threshold: 0.12 }
    )
    obs.observe(el)
  }
})

onUnmounted(() => obs?.disconnect())

// ── 서비스 데이터 ──────────────────────────────────────
const services = [
  { emoji: '📋', bg: '#FFF8E1', accent: '#F59E0B', stat: '1,245+', label: '등록 금융상품', desc: '다양한 상품 비교' },
  { emoji: '📈', bg: '#E8F5E9', accent: '#10B981', stat: '실시간',  label: '주식 정보',    desc: '실시간 시세 분석' },
  { emoji: '💳', bg: '#E3F2FD', accent: '#3B82F6', stat: '지출',    label: '관리',         desc: '소비 패턴 한눈에' },
  { emoji: '🛡️', bg: '#F3E8FD', accent: '#8B5CF6', stat: 'AI',     label: '자산 분석',    desc: '스마트 어시스턴트' },
]

function goStart() {
  router.push(localStorage.getItem('access') ? '/app/home' : '/login')
}
</script>

<template>
  <div class="page">

    <!-- ════════════════ SECTION 1: INTRO ════════════════ -->
    <section class="intro">

      <!-- 로고 스테이지: 빌드 상태 ↔ 소형 상태 교차 -->
      <div class="logo-stage">

        <!-- 빌드 상태: 큰 아이콘 + 아래에 글자 -->
        <div class="logo-build" :class="{ hidden: compact }">
          <svg class="build-icon" viewBox="0 0 100 80" xmlns="http://www.w3.org/2000/svg">
            <circle class="dot" :class="{ show: yellowOn }" cx="28" cy="24" r="14" fill="#FFC108" />
            <circle class="dot" :class="{ show: mintOn }"   cx="72" cy="24" r="14" fill="#26C6A2" />
            <path class="smile" :class="{ drawn: smileOn }"
                  d="M 10,56 Q 50,80 90,56"
                  stroke="#1a1a2e" stroke-width="7" fill="none" stroke-linecap="round" />
          </svg>

          <div class="build-letters">
            <span v-for="(l, i) in ['m','o','n','i']" :key="i"
                  class="bltr" :class="{ show: lettersOn > i }">{{ l }}</span>
          </div>
        </div>

        <!-- 소형 상태: 아이콘 왼쪽 + 글자 오른쪽 -->
        <div class="logo-compact" :class="{ show: compact }">
          <svg class="compact-icon" viewBox="0 0 100 80" xmlns="http://www.w3.org/2000/svg">
            <circle cx="28" cy="24" r="14" fill="#FFC108" />
            <circle cx="72" cy="24" r="14" fill="#26C6A2" />
            <path d="M 10,56 Q 50,80 90,56"
                  stroke="#1a1a2e" stroke-width="7" fill="none" stroke-linecap="round" />
          </svg>
          <span class="compact-text">moni</span>
        </div>

      </div>

      <!-- 슬로건 -->
      <p class="tagline" :class="{ show: taglineOn }">
        내 돈의 흐름을 더 똑똑하게, <em>moni</em>
      </p>

      <!-- 스크롤 유도 -->
      <div class="scroll-hint" :class="{ show: scrollOn }">
        <span class="scroll-label">SCROLL</span>
        <svg class="scroll-mouse" viewBox="0 0 24 38" fill="none">
          <rect x="1" y="1" width="22" height="36" rx="11"
                stroke="#ccc" stroke-width="1.5"/>
          <rect x="10.5" y="7" width="3" height="7" rx="1.5" fill="#ccc">
            <animate attributeName="y"       values="7;14;7"  dur="1.6s" repeatCount="indefinite"/>
            <animate attributeName="opacity" values="1;0.1;1" dur="1.6s" repeatCount="indefinite"/>
          </rect>
        </svg>
        <svg class="scroll-arrow" viewBox="0 0 18 10" fill="none">
          <path d="M1 1L9 9L17 1" stroke="#ccc" stroke-width="1.6" stroke-linecap="round"/>
        </svg>
      </div>

    </section>

    <!-- ════════════════ SECTION 2: SERVICES ════════════════ -->
    <section id="svc" class="svc" :class="{ visible: svcOn }">

      <!-- 메인 문구 -->
      <div class="svc-headline">
        <h2>똑똑한 금융 생활의 시작,</h2>
        <h2><em>MONI</em>와 함께하세요</h2>
      </div>

      <!-- 서비스 카드 -->
      <div class="svc-cards">
        <div v-for="(s, i) in services" :key="i"
             class="svc-card" :style="`--d: ${i * 0.13 + 0.35}s`">
          <div class="svc-icon-box" :style="`background: ${s.bg}`">
            <span class="svc-emoji">{{ s.emoji }}</span>
          </div>
          <strong class="svc-stat" :style="`color: ${s.accent}`">{{ s.stat }}</strong>
          <p class="svc-label">{{ s.label }}</p>
          <p class="svc-desc">{{ s.desc }}</p>
        </div>
      </div>

      <!-- 시작하기 버튼 -->
      <button class="cta-btn" @click="goStart">시작하기 →</button>

    </section>

  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;900&display=swap');

/* ─── 기본 ──────────────────────────────────────────────── */
.page {
  font-family: 'Nunito', sans-serif;
  background: #fff;
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
  gap: 20px;
  background: #fff;
  position: relative;
}

/* 두 로고 상태가 겹치는 고정 높이 영역 */
.logo-stage {
  position: relative;
  width: 100%;
  height: 188px;
}

/* 빌드 / 소형 공통: 절대 위치로 가운데 고정 */
.logo-build,
.logo-compact {
  position: absolute;
  top: 50%;
  left: 50%;
  display: flex;
  align-items: center;
}

/* ── 빌드 상태 ── */
.logo-build {
  flex-direction: column;
  gap: 10px;
  transform: translate(-50%, -50%);
  transition: opacity 0.55s ease;
}
.logo-build.hidden {
  opacity: 0;
  pointer-events: none;
}

.build-icon { width: 116px; }

/* 점 등장: 스프링 스케일 */
.dot {
  transform-origin: center;
  transform: scale(0);
  opacity: 0;
  transition:
    transform 0.45s cubic-bezier(0.34, 1.56, 0.64, 1),
    opacity   0.3s  ease;
}
.dot.show { transform: scale(1); opacity: 1; }

/* 스마일 획 그리기 */
.smile {
  stroke-dasharray: 160;
  stroke-dashoffset: 160;
  transition: stroke-dashoffset 0.65s cubic-bezier(0.4, 0, 0.2, 1);
}
.smile.drawn { stroke-dashoffset: 0; }

/* 글자: 아래에서 올라오며 한 자씩 등장 */
.build-letters { display: flex; gap: 1px; }
.bltr {
  display: inline-block;
  font-size: 54px;
  font-weight: 900;
  color: #1a1a2e;
  letter-spacing: -1px;
  opacity: 0;
  transform: translateY(10px) scale(0.88);
  transition:
    opacity   0.32s ease,
    transform 0.38s cubic-bezier(0.34, 1.2, 0.64, 1);
}
.bltr.show { opacity: 1; transform: translateY(0) scale(1); }

/* ── 소형 상태 ── */
.logo-compact {
  flex-direction: row;
  gap: 14px;
  transform: translate(-50%, -50%);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.65s ease;
}
.logo-compact.show { opacity: 1; pointer-events: auto; }

.compact-icon { width: 80px; }
.compact-text {
  font-size: 44px;
  font-weight: 900;
  color: #1a1a2e;
  letter-spacing: -1px;
  line-height: 1;
}

/* ── 슬로건 ── */
.tagline {
  font-size: 14.5px;
  color: #777;
  letter-spacing: 0.01em;
  text-align: center;
  margin: 0;
  opacity: 0;
  transform: translateY(8px);
  transition: opacity 0.7s ease, transform 0.7s ease;
}
.tagline.show { opacity: 1; transform: none; }
.tagline em { font-style: normal; color: #26C6A2; font-weight: 700; }

/* ── 스크롤 유도 ── */
.scroll-hint {
  position: absolute;
  bottom: 32px;
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
  letter-spacing: 0.22em;
  color: #bbb;
  font-weight: 700;
}
.scroll-mouse { width: 20px; }
.scroll-arrow { width: 14px; margin-top: 2px; }


/* ─── SERVICES ──────────────────────────────────────────── */
.svc {
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 52px;
  padding: 80px 28px;
  background: #f9fafb;
}

/* 메인 문구 */
.svc-headline {
  text-align: center;
  line-height: 1.25;
  opacity: 0;
  transform: translateY(26px);
  transition: opacity 0.7s ease, transform 0.7s ease;
}
.svc.visible .svc-headline { opacity: 1; transform: none; }
.svc-headline h2 {
  font-size: clamp(24px, 5vw, 38px);
  font-weight: 900;
  color: #1a1a2e;
  margin: 0;
}
.svc-headline em { font-style: normal; color: #26C6A2; }

/* 서비스 카드 */
.svc-cards {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  justify-content: center;
}

.svc-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  width: 136px;
  text-align: center;
  opacity: 0;
  transform: translateY(28px);
  transition:
    opacity   0.5s ease var(--d, 0s),
    transform 0.5s ease var(--d, 0s);
}
.svc.visible .svc-card { opacity: 1; transform: none; }

.svc-icon-box {
  width: 64px;
  height: 64px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.svc-emoji { font-size: 29px; }

.svc-stat {
  display: block;
  font-size: 22px;
  font-weight: 900;
  line-height: 1;
}
.svc-label { font-size: 13px; font-weight: 700; color: #2a2a2a; margin: 0; }
.svc-desc  { font-size: 12px; color: #999; margin: 0; }

/* 시작하기 버튼 */
.cta-btn {
  padding: 15px 56px;
  background: #FFC108;
  color: #fff;
  border: none;
  border-radius: 14px;
  font-size: 16px;
  font-weight: 800;
  font-family: 'Nunito', sans-serif;
  letter-spacing: 0.03em;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.7s ease 0.9s, background 0.2s, transform 0.2s;
}
.svc.visible .cta-btn { opacity: 1; }
.cta-btn:hover  { background: #FFB300; transform: translateY(-2px); }
.cta-btn:active { transform: translateY(0); }
</style>
