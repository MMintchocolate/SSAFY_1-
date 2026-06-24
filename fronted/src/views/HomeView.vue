<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement,
  Title, Tooltip, Legend, Filler,
} from 'chart.js'
import NavBar from '@/components/NavBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import {
  ShieldCheck, TrendingUp, TrendingDown, MapPin, Receipt, PhoneOff,
  ChartBarBig, Users, ArrowRight, Newspaper, ExternalLink,
  Zap, AlertTriangle, Loader2, Flame, BarChart2,
} from '@lucide/vue'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

// ─── 서비스 메뉴 ──────────────────────────────────────────────────────────────
const services = [
  { to: '/products',     icon: TrendingUp,  label: '금융상품',    desc: '예·적금 금리 비교',   color: 'bg-blue-50',    iconColor: 'text-blue-600',    border: 'border-blue-100' },
  { to: '/branches',     icon: MapPin,       label: '지점찾기',    desc: '인근 금융기관 검색',   color: 'bg-emerald-50', iconColor: 'text-emerald-600', border: 'border-emerald-100' },
  { to: '/receipts',     icon: Receipt,      label: '영수증 장부', desc: 'AI 자동 지출 분류',   color: 'bg-purple-50',  iconColor: 'text-purple-600',  border: 'border-purple-100' },
  { to: '/voicephishing',icon: PhoneOff,     label: '피싱탐지',    desc: '보이스피싱 AI 분석',   color: 'bg-red-50',     iconColor: 'text-red-600',     border: 'border-red-100' },
  { to: '/spending',     icon: ChartBarBig,  label: '지출분석',    desc: 'CSV 소비 시각화',     color: 'bg-violet-50',  iconColor: 'text-violet-600',  border: 'border-violet-100' },
  { to: '/community',    icon: Users,        label: '커뮤니티',    desc: '피싱 제보·금융 팁',    color: 'bg-orange-50',  iconColor: 'text-orange-600',  border: 'border-orange-100' },
]

// ─── Top3 뉴스 ────────────────────────────────────────────────────────────────
const top3        = ref({ 유출: [], 해킹: [] })
const top3Loading = ref(true)
const top3Error   = ref(false)

const KEYWORDS = [
  { key: '유출', label: '유출 뉴스', barColor: 'bg-orange-500', badgeClass: 'bg-orange-100 text-orange-700' },
  { key: '해킹', label: '해킹 뉴스', barColor: 'bg-red-500',    badgeClass: 'bg-red-100 text-red-700' },
]

async function loadTop3() {
  top3Loading.value = true
  top3Error.value   = false
  try {
    const res = await fetch('/api/news/top3/')
    if (!res.ok) throw new Error()
    top3.value = await res.json()
  } catch {
    top3Error.value = true
  } finally {
    top3Loading.value = false
  }
}

const hasAnyNews = () => KEYWORDS.some(k => (top3.value[k.key] || []).length > 0)

function fmtDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('ko-KR', { month: 'long', day: 'numeric' })
}

const RANK_ICONS = ['🥇', '🥈', '🥉']

// ─── 시장 현황 ────────────────────────────────────────────────────────────────
const movers        = ref({ volume: [], up: [], down: [] })
const moversLoading = ref(true)
const activeIdx     = ref(0)
const chartHistory  = ref([])
const chartLoading  = ref(false)
const historyCache  = new Map()
let cycleTimer = null

const allStocks = computed(() => [
  ...movers.value.volume.map(s => ({ ...s, cat: 'volume' })),
  ...movers.value.up.map(s    => ({ ...s, cat: 'up' })),
  ...movers.value.down.map(s  => ({ ...s, cat: 'down' })),
])
const activeStock = computed(() => allStocks.value[activeIdx.value] ?? null)

watch(activeIdx, async (idx) => {
  const s = allStocks.value[idx]
  if (!s) return
  if (historyCache.has(s.symbol)) {
    chartHistory.value = historyCache.get(s.symbol)
    return
  }
  chartLoading.value = true
  try {
    const res  = await fetch(`/api/stocks/${s.symbol}/history/?period=1mo`)
    const data = await res.json()
    historyCache.set(s.symbol, Array.isArray(data) ? data : [])
    chartHistory.value = historyCache.get(s.symbol)
  } catch { chartHistory.value = [] }
  finally  { chartLoading.value = false }
})

function startCycle() {
  if (cycleTimer) clearInterval(cycleTimer)
  cycleTimer = setInterval(() => {
    if (!allStocks.value.length) return
    activeIdx.value = (activeIdx.value + 1) % allStocks.value.length
  }, 4000)
}

async function loadMovers() {
  moversLoading.value = true
  try {
    const res  = await fetch('/api/stocks/market-movers/')
    movers.value = await res.json()
  } catch { movers.value = { volume: [], up: [], down: [] } }
  finally { moversLoading.value = false }
  if (allStocks.value.length) {
    activeIdx.value = 0
    startCycle()
  }
}

function pickStock(s) {
  const i = allStocks.value.findIndex(x => x.symbol === s.symbol)
  if (i >= 0) activeIdx.value = i
  startCycle()
}

const chartData = computed(() => {
  const prices = chartHistory.value.map(d => d.close)
  const labels = chartHistory.value.map(d => (d.date || '').slice(5))
  const isUp   = prices.length >= 2 && prices[prices.length - 1] >= prices[0]
  return {
    labels,
    datasets: [{
      label: activeStock.value?.name || '',
      data: prices,
      borderColor:     isUp ? '#22c55e' : '#ef4444',
      backgroundColor: isUp ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)',
      borderWidth: 2,
      pointRadius: 0,
      tension: 0.3,
      fill: true,
    }],
  }
})

const chartOpts = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false } },
  scales: {
    x: { grid: { display: false }, ticks: { maxTicksLimit: 5, font: { size: 10 } } },
    y: { grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { font: { size: 10 } } },
  },
  animation: { duration: 300 },
}

// ─── 코스피/코스닥 지수 ───────────────────────────────────────────────────────
const indexData    = ref(null)
const indexLoading = ref(false)

async function loadIndex() {
  indexLoading.value = true
  try {
    const res = await fetch('/api/stocks/index/')
    indexData.value = await res.json()
  } catch { indexData.value = null }
  finally { indexLoading.value = false }
}

function makeIndexChart(history = []) {
  const prices = history.map(d => d.close)
  const labels = history.map(d => (d.date || '').slice(5))
  const isUp   = prices.length >= 2 && prices[prices.length - 1] >= prices[0]
  return {
    labels,
    datasets: [{
      data: prices,
      borderColor:     isUp ? '#22c55e' : '#ef4444',
      backgroundColor: isUp ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)',
      borderWidth: 1.5,
      pointRadius: 0,
      tension: 0.3,
      fill: true,
    }],
  }
}

const kospiChart  = computed(() => makeIndexChart(indexData.value?.kospi?.history  ?? []))
const kosdaqChart = computed(() => makeIndexChart(indexData.value?.kosdaq?.history ?? []))

const indexChartOpts = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false }, tooltip: { enabled: false } },
  scales: { x: { display: false }, y: { display: false } },
  animation: false,
}

onMounted(() => {
  loadTop3()
  loadMovers()
  loadIndex()
})

onUnmounted(() => {
  if (cycleTimer) clearInterval(cycleTimer)
})
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <NavBar />

    <!-- ─── 히어로 ──────────────────────────────────────────────────── -->
    <section
      class="pt-16 min-h-[52vh] flex flex-col justify-center"
      style="background: linear-gradient(135deg, #0f1f47 0%, #1e3a8a 50%, #2563eb 100%)"
    >
      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-16 text-white text-center">
        <div class="inline-flex items-center gap-2 text-xs font-bold px-3 py-1.5 rounded-full mb-6 uppercase tracking-widest border"
          style="background:rgba(29,78,216,0.4);color:#93c5fd;border-color:rgba(59,130,246,0.4)"
        >
          <Zap class="w-3 h-3" />AI 금융보안 플랫폼
        </div>
        <h1 class="text-4xl sm:text-5xl lg:text-6xl font-black leading-tight mb-5 tracking-tight">
          내 자산을<br />
          <span style="color:#93c5fd">보이스피싱</span>으로부터<br />
          안전하게
        </h1>
        <p class="text-base sm:text-lg max-w-xl mx-auto mb-8 leading-relaxed" style="color:rgba(219,234,254,0.8)">
          실시간 AI 탐지로 금융사기를 차단하고, 최신 보안 이슈를 한눈에 확인하세요.
        </p>
        <div class="flex flex-wrap justify-center gap-3">
          <RouterLink to="/voicephishing"
            class="flex items-center gap-2 px-6 py-3 bg-white font-bold rounded-xl text-sm shadow-lg hover:bg-blue-50 transition-all"
            style="color:#1e3a8a"
          >
            <ShieldCheck class="w-4 h-4" />피싱 탐지 시작
          </RouterLink>
          <RouterLink to="/news"
            class="flex items-center gap-2 px-6 py-3 font-semibold rounded-xl border text-sm transition-all"
            style="background:rgba(255,255,255,0.1);color:white;border-color:rgba(255,255,255,0.25)"
          >
            <Newspaper class="w-4 h-4" />보안 뉴스 보기
          </RouterLink>
        </div>
      </div>

      <!-- 웨이브 -->
      <svg viewBox="0 0 1440 56" fill="none" class="w-full block -mb-px">
        <path d="M0,28 C360,56 720,0 1080,28 C1260,42 1380,14 1440,28 L1440,56 L0,56 Z" fill="#f8fafc"/>
      </svg>
    </section>

    <!-- ─── 시장 현황 ──────────────────────────────────────────────────── -->
    <section class="py-14 bg-slate-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6">

        <div class="flex items-end justify-between mb-7">
          <div>
            <div class="flex items-center gap-2 mb-1">
              <BarChart2 class="w-5 h-5 text-blue-600" />
              <h2 class="text-xl font-black text-gray-900">시장 현황</h2>
            </div>
            <p class="text-sm text-gray-500">KRX 최신 거래일 기준 · 4초마다 자동 전환</p>
          </div>
          <RouterLink to="/stocks"
            class="flex items-center gap-1 text-sm font-semibold text-blue-600 hover:text-blue-800 transition-colors"
          >
            전체 보기 <ArrowRight class="w-4 h-4" />
          </RouterLink>
        </div>

        <!-- 로딩 -->
        <div v-if="moversLoading" class="flex justify-center py-16">
          <Loader2 class="w-7 h-7 animate-spin text-blue-400" />
        </div>

        <!-- 콘텐츠: [거래량] [코스피] [상승] [하락] [자동차트] -->
        <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">

          <!-- 거래량 TOP5 -->
          <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            <div class="flex items-center gap-1.5 px-3 py-2.5 bg-orange-50 border-b border-orange-100">
              <Flame class="w-3.5 h-3.5 text-orange-500" />
              <span class="text-xs font-black text-orange-700 tracking-wide">거래량 TOP</span>
            </div>
            <div class="divide-y divide-gray-50">
              <button
                v-for="(s, i) in movers.volume" :key="s.symbol"
                @click="pickStock(s)"
                class="w-full flex items-center gap-2 px-3 py-2.5 text-left transition-colors"
                :class="activeStock?.symbol === s.symbol ? 'bg-orange-50' : 'hover:bg-gray-50'"
              >
                <span class="text-xs font-black w-3.5 flex-shrink-0 text-center"
                  :class="i < 3 ? 'text-orange-400' : 'text-gray-300'">{{ i + 1 }}</span>
                <span class="flex-1 text-xs font-semibold text-gray-900 truncate min-w-0">{{ s.name }}</span>
                <span class="text-xs font-bold tabular-nums flex-shrink-0"
                  :class="(s.change_pct ?? 0) >= 0 ? 'text-emerald-600' : 'text-red-500'">
                  {{ s.change_pct != null ? (s.change_pct >= 0 ? '+' : '') + s.change_pct.toFixed(1) + '%' : '-' }}
                </span>
              </button>
            </div>
          </div>

          <!-- 코스피 지수 -->
          <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden flex flex-col">
            <div class="px-3 py-2.5 border-b border-gray-100">
              <p class="text-xs font-black text-gray-500 tracking-wide mb-0.5">KOSPI</p>
              <template v-if="indexData?.kospi">
                <p class="text-lg font-black tabular-nums leading-tight"
                  :class="(indexData.kospi.change ?? 0) >= 0 ? 'text-gray-900' : 'text-gray-900'">
                  {{ indexData.kospi.value.toLocaleString() }}
                </p>
                <p class="text-xs font-bold tabular-nums"
                  :class="(indexData.kospi.change ?? 0) >= 0 ? 'text-emerald-600' : 'text-red-500'">
                  {{ (indexData.kospi.change >= 0 ? '+' : '') + indexData.kospi.change.toFixed(2) }}
                  ({{ (indexData.kospi.change_pct >= 0 ? '+' : '') + indexData.kospi.change_pct.toFixed(2) }}%)
                </p>
              </template>
              <div v-else class="flex items-center gap-1.5 py-1">
                <Loader2 class="w-3.5 h-3.5 animate-spin text-gray-300" />
                <span class="text-xs text-gray-400">로딩 중</span>
              </div>
            </div>
            <!-- 미니 차트 -->
            <div class="flex-1 px-1 py-2" style="min-height:110px">
              <Line
                v-if="indexData?.kospi?.history?.length"
                :data="kospiChart"
                :options="indexChartOpts"
                style="height:100%;width:100%"
              />
            </div>
            <!-- 코스닥 보조 표시 -->
            <div v-if="indexData?.kosdaq" class="px-3 py-2 border-t border-gray-50 flex items-center justify-between">
              <span class="text-xs text-gray-400 font-semibold">KOSDAQ</span>
              <span class="text-xs font-bold tabular-nums"
                :class="(indexData.kosdaq.change ?? 0) >= 0 ? 'text-emerald-600' : 'text-red-500'">
                {{ indexData.kosdaq.value.toLocaleString() }}
                {{ (indexData.kosdaq.change_pct >= 0 ? '+' : '') + indexData.kosdaq.change_pct.toFixed(2) }}%
              </span>
            </div>
          </div>

          <!-- 상승 TOP5 -->
          <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            <div class="flex items-center gap-1.5 px-3 py-2.5 bg-emerald-50 border-b border-emerald-100">
              <TrendingUp class="w-3.5 h-3.5 text-emerald-500" />
              <span class="text-xs font-black text-emerald-700 tracking-wide">상승 TOP</span>
            </div>
            <div class="divide-y divide-gray-50">
              <button
                v-for="(s, i) in movers.up" :key="s.symbol"
                @click="pickStock(s)"
                class="w-full flex items-center gap-2 px-3 py-2.5 text-left transition-colors"
                :class="activeStock?.symbol === s.symbol ? 'bg-emerald-50' : 'hover:bg-gray-50'"
              >
                <span class="text-xs font-black w-3.5 flex-shrink-0 text-center"
                  :class="i < 3 ? 'text-emerald-500' : 'text-gray-300'">{{ i + 1 }}</span>
                <span class="flex-1 text-xs font-semibold text-gray-900 truncate min-w-0">{{ s.name }}</span>
                <span class="text-xs font-bold tabular-nums text-emerald-600 flex-shrink-0">
                  {{ s.change_pct != null ? '+' + s.change_pct.toFixed(1) + '%' : '-' }}
                </span>
              </button>
            </div>
          </div>

          <!-- 하락 TOP5 -->
          <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            <div class="flex items-center gap-1.5 px-3 py-2.5 bg-red-50 border-b border-red-100">
              <TrendingDown class="w-3.5 h-3.5 text-red-400" />
              <span class="text-xs font-black text-red-600 tracking-wide">하락 TOP</span>
            </div>
            <div class="divide-y divide-gray-50">
              <button
                v-for="(s, i) in movers.down" :key="s.symbol"
                @click="pickStock(s)"
                class="w-full flex items-center gap-2 px-3 py-2.5 text-left transition-colors"
                :class="activeStock?.symbol === s.symbol ? 'bg-red-50' : 'hover:bg-gray-50'"
              >
                <span class="text-xs font-black w-3.5 flex-shrink-0 text-center"
                  :class="i < 3 ? 'text-red-400' : 'text-gray-300'">{{ i + 1 }}</span>
                <span class="flex-1 text-xs font-semibold text-gray-900 truncate min-w-0">{{ s.name }}</span>
                <span class="text-xs font-bold tabular-nums text-red-500 flex-shrink-0">
                  {{ s.change_pct != null ? s.change_pct.toFixed(1) + '%' : '-' }}
                </span>
              </button>
            </div>
          </div>

          <!-- 자동전환 차트 -->
          <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 flex flex-col">

            <!-- 현재 종목 정보 -->
            <div v-if="activeStock" class="flex items-start justify-between mb-3">
              <div class="min-w-0">
                <p class="text-xs text-gray-400 font-medium truncate">{{ activeStock.symbol }}</p>
                <p class="font-extrabold text-gray-900 text-base leading-tight truncate">{{ activeStock.name }}</p>
              </div>
              <div class="text-right flex-shrink-0 ml-3">
                <p class="text-xl font-black text-gray-900 tabular-nums leading-tight">
                  {{ activeStock.close != null ? Math.round(activeStock.close).toLocaleString() : '-' }}
                </p>
                <p class="text-sm font-bold tabular-nums"
                  :class="(activeStock.change_pct ?? 0) >= 0 ? 'text-emerald-600' : 'text-red-500'">
                  {{ activeStock.change_pct != null
                    ? (activeStock.change_pct >= 0 ? '+' : '') + activeStock.change_pct.toFixed(2) + '%'
                    : '' }}
                </p>
              </div>
            </div>

            <!-- 차트 영역 -->
            <div class="flex-1 relative" style="min-height: 180px">
              <div v-if="chartLoading" class="absolute inset-0 flex items-center justify-center">
                <Loader2 class="w-6 h-6 animate-spin text-gray-300" />
              </div>
              <Line
                v-else-if="chartHistory.length > 0"
                :data="chartData"
                :options="chartOpts"
                style="height:100%;width:100%"
              />
              <div v-else class="absolute inset-0 flex items-center justify-center text-xs text-gray-400">
                차트 데이터 없음
              </div>
            </div>

            <!-- 4초 진행바 -->
            <div class="mt-4 h-0.5 bg-gray-100 rounded-full overflow-hidden">
              <div :key="activeIdx" class="h-full rounded-full progress-bar"
                :class="activeStock?.cat === 'up' ? 'bg-emerald-500'
                       : activeStock?.cat === 'down' ? 'bg-red-400'
                       : 'bg-orange-400'"
              />
            </div>

            <!-- 카테고리 + 순서 표시 -->
            <div class="flex items-center justify-between mt-2 text-xs text-gray-400">
              <div class="flex gap-3">
                <span :class="activeStock?.cat === 'volume' ? 'text-orange-500 font-bold' : ''">거래량</span>
                <span :class="activeStock?.cat === 'up'     ? 'text-emerald-600 font-bold' : ''">상승</span>
                <span :class="activeStock?.cat === 'down'   ? 'text-red-500 font-bold' : ''">하락</span>
              </div>
              <span class="tabular-nums">{{ (activeIdx % 5) + 1 }} / 5</span>
            </div>

          </div>
        </div>
      </div>
    </section>

    <!-- ─── 이슈 뉴스 Top 3 ──────────────────────────────────────────── -->
    <section class="py-14 bg-white border-t border-gray-100">
      <div class="max-w-7xl mx-auto px-4 sm:px-6">

        <div class="flex items-end justify-between mb-7">
          <div>
            <div class="flex items-center gap-2 mb-1">
              <Newspaper class="w-5 h-5 text-blue-600" />
              <h2 class="text-xl font-black text-gray-900">최신 이슈 뉴스 Top 3</h2>
            </div>
            <p class="text-sm text-gray-500">유출·해킹 키워드 최신 보안 이슈 각 3건</p>
          </div>
          <RouterLink to="/news"
            class="flex items-center gap-1 text-sm font-semibold text-blue-600 hover:text-blue-800 transition-colors"
          >
            전체 보기 <ArrowRight class="w-4 h-4" />
          </RouterLink>
        </div>

        <!-- 로딩 -->
        <div v-if="top3Loading" class="flex justify-center py-16">
          <Loader2 class="w-7 h-7 animate-spin text-blue-400" />
        </div>

        <!-- 오류 / 뉴스 없음 -->
        <div v-else-if="top3Error || !hasAnyNews()"
          class="flex flex-col items-center justify-center py-14 gap-3 bg-white rounded-2xl border border-dashed border-gray-200"
        >
          <Newspaper class="w-10 h-10 text-gray-300" />
          <p class="text-sm text-gray-400">
            {{ top3Error ? '뉴스를 불러올 수 없습니다.' : '아직 수집된 뉴스가 없습니다.' }}
          </p>
          <RouterLink to="/news" class="text-xs font-semibold text-blue-600 hover:underline">
            보안뉴스 페이지에서 크롤링 시작하기 →
          </RouterLink>
        </div>

        <!-- 키워드별 2열 -->
        <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div v-for="kw in KEYWORDS" :key="kw.key">
            <div class="flex items-center gap-2 mb-4">
              <span class="w-3 h-3 rounded-full flex-shrink-0" :class="kw.barColor"></span>
              <h3 class="font-bold text-gray-800">{{ kw.label }}</h3>
              <span class="text-xs text-gray-400 ml-auto">최신순</span>
            </div>

            <div v-if="!(top3[kw.key] || []).length"
              class="flex items-center justify-center h-32 bg-white rounded-xl border border-dashed border-gray-200 text-sm text-gray-400"
            >
              수집된 뉴스가 없습니다
            </div>

            <div v-else class="space-y-3">
              <a
                v-for="(article, idx) in top3[kw.key]" :key="article.id"
                :href="article.url" target="_blank" rel="noopener noreferrer"
                class="group flex items-start gap-3 p-4 bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
              >
                <span class="text-base font-black flex-shrink-0 mt-0.5">{{ RANK_ICONS[idx] }}</span>
                <div class="flex-1 min-w-0">
                  <h4 class="text-sm font-semibold text-gray-900 leading-snug line-clamp-2 group-hover:text-blue-700 transition-colors mb-1.5">
                    {{ article.title }}
                  </h4>
                  <p v-if="article.summary"
                    class="text-xs text-gray-500 leading-relaxed line-clamp-2 mb-1.5"
                  >{{ article.summary }}</p>
                  <span class="text-xs text-gray-400">{{ fmtDate(article.published_date) }}</span>
                </div>
                <ExternalLink class="w-3.5 h-3.5 flex-shrink-0 text-gray-300 group-hover:text-blue-500 transition-colors mt-1" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ─── 주요 서비스 ──────────────────────────────────────────────── -->
    <section class="py-14 bg-slate-50 border-t border-gray-100">
      <div class="max-w-7xl mx-auto px-4 sm:px-6">
        <h2 class="text-xl font-black text-gray-900 mb-7 flex items-center gap-2">
          <Zap class="w-5 h-5 text-blue-600" />주요 서비스
        </h2>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          <RouterLink
            v-for="svc in services" :key="svc.to"
            :to="svc.to"
            class="group flex flex-col items-center text-center gap-3 p-5 rounded-2xl border hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
            :class="[svc.color, svc.border]"
          >
            <div class="w-12 h-12 rounded-xl bg-white shadow-sm flex items-center justify-center">
              <component :is="svc.icon" class="w-5 h-5" :class="svc.iconColor" />
            </div>
            <div>
              <p class="text-sm font-bold text-gray-900">{{ svc.label }}</p>
              <p class="text-xs text-gray-500 mt-0.5 leading-snug">{{ svc.desc }}</p>
            </div>
            <ArrowRight class="w-3.5 h-3.5 text-gray-300 group-hover:text-current group-hover:translate-x-0.5 transition-all" />
          </RouterLink>
        </div>
      </div>
    </section>

    <!-- ─── 보안 팁 배너 ─────────────────────────────────────────────── -->
    <section class="py-10 bg-white border-t border-gray-100">
      <div class="max-w-7xl mx-auto px-4 sm:px-6">
        <div class="rounded-2xl p-6 sm:p-8 flex flex-col sm:flex-row items-start sm:items-center gap-5"
          style="background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%)"
        >
          <div class="flex-shrink-0 w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
            <AlertTriangle class="w-6 h-6 text-yellow-300" />
          </div>
          <div class="flex-1 text-white">
            <p class="font-bold text-base mb-1">금융사기 의심될 땐 즉시 신고</p>
            <p class="text-sm" style="color:rgba(219,234,254,0.8)">
              금융감독원 1332 · 경찰청 182 · 한국인터넷진흥원 118
            </p>
          </div>
          <RouterLink to="/voicephishing"
            class="flex-shrink-0 flex items-center gap-2 px-5 py-2.5 bg-white font-bold text-sm rounded-xl hover:bg-blue-50 transition-all"
            style="color:#1e3a8a"
          >
            <PhoneOff class="w-4 h-4" />지금 분석하기
          </RouterLink>
        </div>
      </div>
    </section>

    <AppFooter />
  </div>
</template>

<style scoped>
@keyframes progressBar {
  from { width: 0% }
  to   { width: 100% }
}
.progress-bar {
  animation: progressBar 4s linear forwards;
}
</style>
