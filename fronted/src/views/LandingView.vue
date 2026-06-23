<script setup>
// @ts-nocheck
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router    = useRouter()
const canvasEl  = ref(null)
const svgEl     = ref(null)
const breathing = ref(false)
const showBtn   = ref(false)

let raf = null
let cleanupResize = () => {}

function initParticles() {
  const el  = canvasEl.value
  if (!el) return
  const ctx = el.getContext('2d')
  let W = el.width  = window.innerWidth
  let H = el.height = window.innerHeight
  const onResize = () => { W = el.width  = window.innerWidth; H = el.height = window.innerHeight }
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
      ctx.fillStyle = 'rgba(175,212,240,0.7)'; ctx.fill()
    }
    for (let i = 0; i < N; i++) {
      for (let j = i + 1; j < N; j++) {
        const dx = pts[i].x - pts[j].x, dy = pts[i].y - pts[j].y
        const d = Math.sqrt(dx * dx + dy * dy)
        if (d < MAX) {
          const a = (1 - d / MAX) * 0.27
          ctx.beginPath(); ctx.moveTo(pts[i].x, pts[i].y); ctx.lineTo(pts[j].x, pts[j].y)
          ctx.strokeStyle = 'rgba(105,160,215,' + a + ')'; ctx.lineWidth = 0.55; ctx.stroke()
        }
      }
    }
    raf = requestAnimationFrame(tick)
  }
  tick()
  return () => window.removeEventListener('resize', onResize)
}

function sleep(ms) { return new Promise(function(r) { setTimeout(r, ms) }) }

async function animateLogo() {
  if (!svgEl.value) return
  try { await document.fonts.load('900 90px Nunito') } catch(e) {}
  await sleep(200)

  const svg      = svgEl.value
  const strokeEl = svg.querySelector('.ls')
  const fillEl   = svg.querySelector('.lf')
  const scanEls  = Array.from(svg.querySelectorAll('.scan'))

  // 외곽 stroke: 실제 path 길이 측정 후 dasharray 설정
  let strokeLen = 4000
  try { strokeLen = Math.ceil(strokeEl.getTotalLength()) } catch(e) {}
  strokeEl.style.strokeDasharray  = strokeLen
  strokeEl.style.strokeDashoffset = strokeLen

  // scan lines: viewBox 너비 460
  scanEls.forEach(function(el) {
    el.style.strokeDasharray  = '460'
    el.style.strokeDashoffset = '460'
  })

  await sleep(50)

  // 모든 라인 동시 시작
  strokeEl.style.transition = 'stroke-dashoffset 2.8s cubic-bezier(0.4,0,0.2,1)'
  strokeEl.style.strokeDashoffset = '0'

  scanEls.forEach(function(el, i) {
    el.style.transition = 'stroke-dashoffset 2.8s cubic-bezier(0.4,0,0.2,1) ' + (i * 30) + 'ms'
    el.style.strokeDashoffset = '0'
  })

  // 모든 선이 endpoint 도착 후 fill 채워짐
  await sleep(2950)
  fillEl.style.transition = 'opacity 0.95s ease'
  fillEl.style.opacity    = '1'

  // fill 완성 후 stroke 라인 fade-out
  await sleep(800)
  strokeEl.style.transition = 'opacity 0.5s ease'
  strokeEl.style.opacity    = '0'
  scanEls.forEach(function(el) {
    el.style.transition = 'opacity 0.5s ease'
    el.style.opacity    = '0'
  })

  await sleep(600)
  breathing.value = true
  showBtn.value   = true
}

onMounted(function() {
  const fn = initParticles()
  if (fn) cleanupResize = fn
  animateLogo()
})

onUnmounted(function() {
  cleanupResize()
  if (raf) cancelAnimationFrame(raf)
})

function enter() {
  router.push(localStorage.getItem('access') ? '/app/home' : '/login')
}
</script>

<template>
  <div class="splash">
    <canvas ref="canvasEl" class="net" />
    <div class="vignette" />

    <svg ref="svgEl" class="logo-svg" viewBox="0 0 460 115">
      <defs>
        <linearGradient id="gs" x1="0" y1="0" x2="0" y2="115" gradientUnits="userSpaceOnUse">
          <stop offset="0%"   stop-color="#e2f2ff" />
          <stop offset="100%" stop-color="#78afc8" />
        </linearGradient>
        <linearGradient id="gf" x1="0" y1="0" x2="0" y2="115" gradientUnits="userSpaceOnUse">
          <stop offset="0%"   stop-color="#cce0f2" />
          <stop offset="50%"  stop-color="#90b8d0" />
          <stop offset="100%" stop-color="#5688a8" />
        </linearGradient>
        <clipPath id="cp">
          <text x="18" y="100" font-size="90" font-family="Nunito,sans-serif" font-weight="900">moni</text>
        </clipPath>
      </defs>

      <!-- 채워지는 fill 텍스트 (초기 opacity 0, 마지막에 채워짐) -->
      <text class="lf" :class="{ breathing }"
            x="18" y="100" font-size="90" font-family="Nunito,sans-serif" font-weight="900"
            fill="url(#gf)">moni</text>

      <!-- 외곽 stroke 텍스트 (선이 그려지는 효과) -->
      <text class="ls"
            x="18" y="100" font-size="90" font-family="Nunito,sans-serif" font-weight="900"
            fill="none" stroke="url(#gs)" stroke-width="2">moni</text>

      <!-- 내부 scan lines — 글자 채워진 영역에만 clip -->
      <g clip-path="url(#cp)" stroke="url(#gs)" stroke-width="1.1">
        <line class="scan" x1="0" y1="41" x2="460" y2="41" />
        <line class="scan" x1="0" y1="55" x2="460" y2="55" />
        <line class="scan" x1="0" y1="65" x2="460" y2="65" />
        <line class="scan" x1="0" y1="75" x2="460" y2="75" />
        <line class="scan" x1="0" y1="85" x2="460" y2="85" />
        <line class="scan" x1="0" y1="95" x2="460" y2="95" />
      </g>
    </svg>

    <button v-show="showBtn" class="enter-btn" @click="enter">
      시작하기
    </button>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@900&display=swap');

.splash {
  position: fixed;
  inset: 0;
  background: #000811;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.net {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.vignette {
  position: fixed;
  inset: 0;
  background: radial-gradient(ellipse at center, transparent 25%, #000811 78%);
  pointer-events: none;
}

.logo-svg {
  position: relative;
  z-index: 10;
  width: clamp(300px, 55vw, 780px);
  height: auto;
}

/* fill 텍스트: 초기 invisible */
.lf {
  opacity: 0;
}

/* fill 완성 후 숨쉬기 */
.lf.breathing {
  animation: breathe 3s ease-in-out infinite;
}

/* 외곽 stroke: 초기에 전부 숨겨둠 (JS로 정확한 길이 측정 후 덮어씀) */
.ls {
  stroke-dasharray: 4000;
  stroke-dashoffset: 4000;
}

/* 내부 scan lines: 초기 invisible */
.scan {
  stroke-dasharray: 460;
  stroke-dashoffset: 460;
}

@keyframes breathe {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.5; }
}

.enter-btn {
  position: relative;
  z-index: 10;
  margin-top: 2.5rem;
  padding: 0.65rem 2.4rem;
  background: transparent;
  border: 1px solid rgba(155, 198, 235, 0.22);
  border-radius: 2rem;
  color: rgba(185, 218, 245, 0.72);
  font-size: 0.875rem;
  letter-spacing: 0.18em;
  cursor: pointer;
  animation: fadein 1.2s ease forwards;
  transition: border-color 0.35s, color 0.35s, background 0.35s, box-shadow 0.35s;
}

.enter-btn:hover {
  border-color: rgba(155, 198, 235, 0.55);
  color: #ddf0ff;
  background: rgba(155, 198, 235, 0.06);
  box-shadow: 0 0 24px rgba(90, 155, 220, 0.13);
}

@keyframes fadein {
  from { opacity: 0; }
  to   { opacity: 1; }
}
</style>
