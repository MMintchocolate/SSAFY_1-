<script setup>
// @ts-nocheck
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement,
  Title, Tooltip, Legend, Filler,
} from 'chart.js'
import NavBar from '@/components/NavBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import { Search, Star, TrendingUp, TrendingDown, X, BarChart2 } from '@lucide/vue'
import { useAuth } from '@/composables/useAuth'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const API = '/api/stocks'
const { isLoggedIn, authFetch } = useAuth()

// Search
const query = ref('')
const searchResults = ref(/** @type {{symbol:string,name:string,type:string,exchange:string}[]} */ ([]))
const searchLoading = ref(false)
let searchTimer = null

// Selected stock
const selectedSymbol = ref('')
const stockDetail = ref(/** @type {any} */ (null))
const detailLoading = ref(false)

// Chart / History
const history = ref([])
const historyLoading = ref(false)
const period = ref('3mo')
const PERIODS = [
  { label: '1개월', value: '1mo' },
  { label: '3개월', value: '3mo' },
  { label: '6개월', value: '6mo' },
  { label: '1년',   value: '1y'  },
  { label: '5년',   value: '5y'  },
]

// Chart / Table view toggle
const viewMode = ref('chart') // 'chart' | 'table'

// Realtime (WS 객체는 반응형 불필요 → plain let)
/** @type {WebSocket|null} */
let _ws = null
const trade     = ref(/** @type {Record<string,any>|null} */ (null))
const orderbook = ref(/** @type {Record<string,any>|null} */ (null))

// Watchlist
const watchlist = ref([])
const watchlistSet = computed(() => new Set(watchlist.value.map(w => w.symbol)))

// ── Search ──────────────────────────────────────────────────────
function onInput() {
  clearTimeout(searchTimer)
  if (!query.value.trim()) { searchResults.value = []; return }
  searchTimer = setTimeout(doSearch, 400)
}

async function doSearch() {
  if (!query.value.trim()) return
  searchLoading.value = true
  try {
    const res = await fetch(`${API}/search/?q=${encodeURIComponent(query.value)}`)
    const data = await res.json()
    searchResults.value = Array.isArray(data) ? data : []
  } catch {
    searchResults.value = []
  } finally {
    searchLoading.value = false
  }
}

function clearSearch() {
  query.value = ''
  searchResults.value = []
}

async function selectStock(symbol, name) {
  selectedSymbol.value = symbol
  clearSearch()
  trade.value     = null
  orderbook.value = null
  await Promise.all([fetchDetail(symbol), fetchHistory(symbol, period.value)])
  connectRealtime(symbol)
}

// ── Detail ───────────────────────────────────────────────────────
async function fetchDetail(symbol) {
  detailLoading.value = true
  stockDetail.value = null
  try {
    const res = await fetch(`${API}/${symbol}/`)
    stockDetail.value = await res.json()
  } finally {
    detailLoading.value = false
  }
}

// ── History / Chart ──────────────────────────────────────────────
async function fetchHistory(symbol, p) {
  historyLoading.value = true
  history.value = []
  try {
    const res = await fetch(`${API}/${symbol}/history/?period=${p}`)
    history.value = await res.json()
  } finally {
    historyLoading.value = false
  }
}

watch(period, p => {
  if (selectedSymbol.value) fetchHistory(selectedSymbol.value, p)
})

const chartData = computed(() => {
  const labels = history.value.map(d => d.date)
  const prices = history.value.map(d => d.close)
  const isUp = prices.length >= 2 && prices[prices.length - 1] >= prices[0]
  const color  = isUp ? 'rgb(34,197,94)'       : 'rgb(239,68,68)'
  const fill   = isUp ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)'
  return {
    labels,
    datasets: [{
      label: '종가',
      data: prices,
      borderColor: color,
      backgroundColor: fill,
      borderWidth: 2,
      pointRadius: 0,
      tension: 0.3,
      fill: true,
    }],
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: { mode: 'index', intersect: false },
  },
  scales: {
    x: { grid: { display: false }, ticks: { maxTicksLimit: 6, font: { size: 11 } } },
    y: { grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { font: { size: 11 } } },
  },
}

// ── Watchlist ────────────────────────────────────────────────────
async function fetchWatchlist() {
  if (!isLoggedIn.value) return
  try {
    const res = await authFetch(`${API}/watchlist/`)
    if (res.ok) watchlist.value = await res.json()
  } catch { /* ignore */ }
}

async function toggleWatchlist(symbol, name) {
  if (!isLoggedIn.value) return
  if (watchlistSet.value.has(symbol)) {
    await authFetch(`${API}/watchlist/${symbol}/`, { method: 'DELETE' })
    watchlist.value = watchlist.value.filter(w => w.symbol !== symbol)
  } else {
    const res = await authFetch(`${API}/watchlist/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol, name }),
    })
    if (res.ok) watchlist.value.push({ symbol, name })
  }
}

// ── Utils ─────────────────────────────────────────────────────────
function fmtPrice(n) {
  if (n == null) return '-'
  return stockDetail.value?.currency === 'KRW'
    ? Math.round(n).toLocaleString()
    : Number(n).toFixed(2)
}

function fmtChange(n) {
  if (n == null) return '-'
  return stockDetail.value?.currency === 'KRW'
    ? Math.round(n).toLocaleString()
    : Number(n).toFixed(2)
}

function fmtCap(n) {
  if (n == null) return '-'
  if (n >= 1e12) return (n / 1e12).toFixed(2) + 'T'
  if (n >= 1e9)  return (n / 1e9).toFixed(2)  + 'B'
  if (n >= 1e6)  return (n / 1e6).toFixed(2)  + 'M'
  return n.toLocaleString()
}

onMounted(fetchWatchlist)

// ── Realtime WebSocket ───────────────────────────────────────────
/** @param {string} symbol */
function connectRealtime(symbol) {
  if (_ws) { _ws.close(); _ws = null }

  // 한국 주식은 005930.KS / 035420.KQ 형태 → KIS는 순수 6자리 코드만 사용
  const kisCode = symbol.replace(/\.(KS|KQ)$/i, '')

  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const ws = new WebSocket(`${proto}//${location.host}/ws/${kisCode}`)

  ws.onmessage = (evt) => {
    try {
      const data = JSON.parse(evt.data)
      if (data.type === 'trade')          trade.value     = data
      else if (data.type === 'orderbook') orderbook.value = data
    } catch { /* ignore */ }
  }

  ws.onclose = () => {
    setTimeout(() => {
      if (selectedSymbol.value === symbol) connectRealtime(symbol)
    }, 3000)
  }

  _ws = ws
}

const historyReversed = computed(() => [...history.value].reverse())

// 매도호가를 높은가→낮은가 순으로 뒤집어 표시 (spread를 template 밖으로)
const asksReversed = computed(() => {
  if (!orderbook.value) return []
  // @ts-ignore
  return [...orderbook.value.asks].reverse()
})

function qtyBarWidth(qty, list) {
  const max = Math.max(...list.map(x => x.qty), 1)
  return Math.round(qty / max * 100)
}

function signColor(sign) {
  if (sign === '1' || sign === '2') return 'text-red-600'
  if (sign === '4' || sign === '5') return 'text-blue-600'
  return 'text-gray-700'
}

onUnmounted(() => {
  if (_ws) _ws.close()
})
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <NavBar />

    <main class="pt-16">
      <!-- Page header -->
      <div class="bg-white border-b border-gray-100">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 py-10">
          <div class="inline-flex items-center gap-2 bg-emerald-50 text-emerald-700 text-xs font-bold px-3 py-1.5 rounded-full mb-3 uppercase tracking-widest border border-emerald-100">
            <BarChart2 class="w-3 h-3" />Yahoo Finance 실시간 데이터
          </div>
          <h1 class="text-3xl font-extrabold text-gray-900 mb-1">주식 검색</h1>
          <p class="text-gray-400">종목명 또는 티커로 검색하세요 (예: Apple, AAPL, 삼성전자, 005930.KS)</p>
        </div>
      </div>

      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-8">

        <!-- Search bar -->
        <div class="relative mb-8 max-w-2xl">
          <div class="flex items-center gap-2 bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-sm focus-within:border-blue-400 focus-within:ring-2 focus-within:ring-blue-100 transition-all">
            <Search class="w-5 h-5 text-gray-400 flex-shrink-0" />
            <input
              v-model="query"
              @input="onInput"
              @keydown.enter="doSearch"
              placeholder="종목명 또는 티커 입력 (예: AAPL, Tesla)"
              class="flex-1 outline-none text-sm text-gray-800 placeholder-gray-400 bg-transparent"
            />
            <button v-if="query" @click="clearSearch" class="text-gray-400 hover:text-gray-600">
              <X class="w-4 h-4" />
            </button>
          </div>

          <!-- Search dropdown -->
          <div
            v-if="searchResults.length > 0 || searchLoading"
            class="absolute top-full mt-1 left-0 right-0 bg-white rounded-2xl border border-gray-200 shadow-xl z-20 overflow-hidden"
          >
            <div v-if="searchLoading" class="px-4 py-3 text-sm text-gray-400">검색 중...</div>
            <button
              v-for="r in searchResults"
              :key="r.symbol"
              @click="selectStock(r.symbol, r.name)"
              class="w-full flex items-center gap-3 px-4 py-3 hover:bg-blue-50 transition-colors text-left border-b border-gray-50 last:border-0"
            >
              <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-blue-900 flex items-center justify-center text-white text-xs font-black flex-shrink-0">
                {{ r.symbol.slice(0, 4) }}
              </div>
              <div class="flex-1 min-w-0">
                <p class="font-semibold text-gray-900 text-sm">{{ r.symbol }}</p>
                <p class="text-xs text-gray-500 truncate">{{ r.name }}</p>
              </div>
              <span class="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full flex-shrink-0">{{ r.exchange }}</span>
            </button>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

          <!-- ── Main: detail + chart ── -->
          <div class="lg:col-span-2 space-y-4">

            <!-- Loading skeleton -->
            <div v-if="detailLoading" class="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm animate-pulse space-y-4">
              <div class="flex gap-3">
                <div class="w-14 h-14 rounded-xl bg-gray-200"></div>
                <div class="flex-1 space-y-2 pt-1">
                  <div class="w-28 h-3 bg-gray-200 rounded"></div>
                  <div class="w-52 h-5 bg-gray-200 rounded"></div>
                </div>
              </div>
              <div class="w-44 h-10 bg-gray-200 rounded"></div>
              <div class="h-64 bg-gray-100 rounded-xl"></div>
            </div>

            <!-- Stock detail card -->
            <div v-else-if="stockDetail && !stockDetail.error" class="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">

              <!-- Header -->
              <div class="flex items-start justify-between mb-5">
                <div class="flex items-center gap-3">
                  <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-blue-700 to-blue-900 flex items-center justify-center text-white text-sm font-black shadow-sm flex-shrink-0">
                    {{ selectedSymbol.slice(0, 4) }}
                  </div>
                  <div>
                    <p class="text-xs text-gray-400 font-medium">{{ selectedSymbol }} · {{ stockDetail.exchange }}</p>
                    <p class="font-extrabold text-gray-900 text-xl leading-tight">{{ stockDetail.name }}</p>
                    <p v-if="stockDetail.sector" class="text-xs text-gray-500 mt-0.5">
                      {{ stockDetail.sector }}<span v-if="stockDetail.industry"> · {{ stockDetail.industry }}</span>
                    </p>
                  </div>
                </div>

                <button
                  v-if="isLoggedIn"
                  @click="toggleWatchlist(selectedSymbol, stockDetail.name)"
                  class="flex items-center gap-1.5 px-3 py-2 rounded-xl border transition-all text-sm font-semibold flex-shrink-0"
                  :class="watchlistSet.has(selectedSymbol)
                    ? 'bg-amber-50 border-amber-200 text-amber-600 hover:bg-amber-100'
                    : 'bg-gray-50 border-gray-200 text-gray-500 hover:border-amber-300 hover:text-amber-500'"
                >
                  <Star
                    class="w-4 h-4 transition-all"
                    :class="watchlistSet.has(selectedSymbol) ? 'fill-amber-400 text-amber-400' : ''"
                  />
                  {{ watchlistSet.has(selectedSymbol) ? '관심 해제' : '관심 종목' }}
                </button>
              </div>

              <!-- Price & change -->
              <div class="flex items-end gap-4 mb-5">
                <div>
                  <p class="text-xs text-gray-400 mb-0.5">현재가</p>
                  <div class="flex items-end gap-1.5">
                    <span class="text-4xl font-black text-gray-900 leading-none tabular-nums">
                      {{ fmtPrice(stockDetail.price) }}
                    </span>
                    <span class="text-lg text-gray-400 mb-0.5">{{ stockDetail.currency }}</span>
                  </div>
                </div>
                <div
                  v-if="stockDetail.change != null"
                  class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-sm font-bold mb-1"
                  :class="stockDetail.change >= 0 ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-600'"
                >
                  <TrendingUp v-if="stockDetail.change >= 0" class="w-4 h-4" />
                  <TrendingDown v-else class="w-4 h-4" />
                  {{ stockDetail.change >= 0 ? '+' : '' }}{{ fmtChange(stockDetail.change) }}
                  ({{ stockDetail.change_pct >= 0 ? '+' : '' }}{{ stockDetail.change_pct?.toFixed(2) }}%)
                </div>
              </div>

              <!-- Stats grid -->
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4 p-4 bg-gray-50 rounded-xl">
                <div>
                  <p class="text-xs text-gray-400 mb-0.5">시가총액</p>
                  <p class="font-bold text-gray-800 text-sm tabular-nums">{{ fmtCap(stockDetail.market_cap) }}</p>
                </div>
                <div>
                  <p class="text-xs text-gray-400 mb-0.5">전일 종가</p>
                  <p class="font-bold text-gray-800 text-sm tabular-nums">
                    {{ fmtPrice(stockDetail.prev_close) }}
                  </p>
                </div>
                <div>
                  <p class="text-xs text-gray-400 mb-0.5">52주 고가</p>
                  <p class="font-bold text-emerald-700 text-sm tabular-nums">
                    {{ fmtPrice(stockDetail.w52_high) }}
                  </p>
                </div>
                <div>
                  <p class="text-xs text-gray-400 mb-0.5">52주 저가</p>
                  <p class="font-bold text-red-600 text-sm tabular-nums">
                    {{ fmtPrice(stockDetail.w52_low) }}
                  </p>
                </div>
              </div>

              <!-- 빠른 이동 버튼 -->
              <div class="flex gap-2 mb-5">
                <RouterLink
                  to="/indicators"
                  class="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 text-white text-xs font-bold rounded-xl hover:bg-emerald-700 transition-colors shadow-sm"
                >
                  <TrendingUp class="w-3.5 h-3.5" />
                  매수신호 보러가기
                </RouterLink>
                <RouterLink
                  to="/dataset"
                  class="flex items-center gap-1.5 px-4 py-2 bg-violet-600 text-white text-xs font-bold rounded-xl hover:bg-violet-700 transition-colors shadow-sm"
                >
                  <BarChart2 class="w-3.5 h-3.5" />
                  ML 데이터 보러가기
                </RouterLink>
              </div>

              <!-- Period selector + view toggle -->
              <div class="flex items-center gap-2 mb-4 flex-wrap">
                <span class="text-xs text-gray-500 font-medium">기간</span>
                <div class="flex gap-1.5">
                  <button
                    v-for="p in PERIODS"
                    :key="p.value"
                    @click="period = p.value"
                    class="px-3 py-1.5 rounded-lg text-xs font-bold transition-all"
                    :class="period === p.value
                      ? 'bg-blue-700 text-white'
                      : 'bg-gray-100 text-gray-500 hover:bg-blue-50 hover:text-blue-700'"
                  >
                    {{ p.label }}
                  </button>
                </div>
                <div class="ml-auto flex gap-1 bg-gray-100 p-0.5 rounded-lg">
                  <button
                    @click="viewMode = 'chart'"
                    class="px-3 py-1 rounded-md text-xs font-bold transition-all"
                    :class="viewMode === 'chart' ? 'bg-white text-blue-700 shadow-sm' : 'text-gray-400 hover:text-gray-600'"
                  >차트</button>
                  <button
                    @click="viewMode = 'table'"
                    class="px-3 py-1 rounded-md text-xs font-bold transition-all"
                    :class="viewMode === 'table' ? 'bg-white text-blue-700 shadow-sm' : 'text-gray-400 hover:text-gray-600'"
                  >표</button>
                </div>
              </div>

              <!-- Chart -->
              <div v-if="viewMode === 'chart'" class="relative h-64">
                <div v-if="historyLoading" class="absolute inset-0 flex items-center justify-center bg-gray-50 rounded-xl">
                  <span class="text-sm text-gray-400">차트 로딩 중...</span>
                </div>
                <Line
                  v-else-if="history.length > 0"
                  :data="chartData"
                  :options="chartOptions"
                  style="height: 100%; width: 100%"
                />
                <div v-else class="absolute inset-0 flex items-center justify-center text-gray-400 text-sm">
                  차트 데이터 없음
                </div>
              </div>

              <!-- Table -->
              <div v-else class="overflow-auto max-h-64 rounded-xl border border-gray-100">
                <div v-if="historyLoading" class="py-8 text-center text-sm text-gray-400">로딩 중...</div>
                <table v-else-if="history.length > 0" class="w-full text-xs">
                  <thead class="sticky top-0 bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th class="px-3 py-2 text-left font-bold text-gray-500">날짜</th>
                      <th class="px-3 py-2 text-right font-bold text-gray-500">시가</th>
                      <th class="px-3 py-2 text-right font-bold text-gray-500">고가</th>
                      <th class="px-3 py-2 text-right font-bold text-gray-500">저가</th>
                      <th class="px-3 py-2 text-right font-bold text-gray-500">종가</th>
                      <th class="px-3 py-2 text-right font-bold text-gray-500">거래량</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="row in historyReversed"
                      :key="row.date"
                      class="border-b border-gray-50 hover:bg-gray-50 transition-colors"
                    >
                      <td class="px-3 py-1.5 text-gray-500 tabular-nums">{{ row.date }}</td>
                      <td class="px-3 py-1.5 text-right text-gray-800 tabular-nums font-mono">{{ row.open?.toLocaleString() }}</td>
                      <td class="px-3 py-1.5 text-right text-emerald-700 tabular-nums font-mono">{{ row.high?.toLocaleString() }}</td>
                      <td class="px-3 py-1.5 text-right text-red-600 tabular-nums font-mono">{{ row.low?.toLocaleString() }}</td>
                      <td class="px-3 py-1.5 text-right font-bold text-gray-900 tabular-nums font-mono">{{ row.close?.toLocaleString() }}</td>
                      <td class="px-3 py-1.5 text-right text-gray-500 tabular-nums font-mono">{{ row.volume?.toLocaleString() }}</td>
                    </tr>
                  </tbody>
                </table>
                <div v-else class="py-8 text-center text-sm text-gray-400">데이터 없음</div>
              </div>
            </div>

            <!-- Error -->
            <div v-else-if="stockDetail?.error" class="bg-white rounded-2xl border border-red-100 p-8 text-center">
              <p class="text-red-500 font-semibold">데이터를 불러오지 못했습니다</p>
              <p class="text-sm text-red-400 mt-1">{{ stockDetail.error }}</p>
            </div>

            <!-- Empty state -->
            <div v-else class="bg-white rounded-2xl border border-gray-100 p-16 text-center">
              <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-100 to-emerald-200 flex items-center justify-center mx-auto mb-4">
                <BarChart2 class="w-8 h-8 text-emerald-500" />
              </div>
              <p class="font-bold text-gray-900 mb-2">종목을 검색하세요</p>
              <p class="text-sm text-gray-400">티커(AAPL) 또는 회사명(Apple, 삼성전자)으로 검색</p>
            </div>

            <!-- ── 실시간 체결가 ── -->
            <div v-if="trade" class="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
              <div class="flex items-center gap-2 mb-4">
                <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span class="text-xs font-bold text-gray-500 uppercase tracking-wider">실시간 체결</span>
                <span class="ml-auto text-xs text-gray-400 tabular-nums">{{ trade.time }}</span>
              </div>
              <div class="flex items-center gap-5 flex-wrap">
                <div>
                  <p class="text-xs text-gray-400 mb-0.5">체결가</p>
                  <span class="text-3xl font-black tabular-nums" :class="signColor(trade.sign)">
                    {{ trade.price.toLocaleString() }}
                  </span>
                </div>
                <div>
                  <p class="text-xs text-gray-400 mb-0.5">대비</p>
                  <p class="text-lg font-bold tabular-nums" :class="signColor(trade.sign)">
                    {{ trade.change >= 0 ? '+' : '' }}{{ trade.change.toLocaleString() }}
                    <span class="text-sm">({{ trade.change_rate >= 0 ? '+' : '' }}{{ trade.change_rate }}%)</span>
                  </p>
                </div>
                <div>
                  <p class="text-xs text-gray-400 mb-0.5">체결량</p>
                  <p class="text-base font-bold text-gray-800 tabular-nums">{{ trade.volume.toLocaleString() }}</p>
                </div>
                <div>
                  <p class="text-xs text-gray-400 mb-0.5">누적거래량</p>
                  <p class="text-base font-bold text-gray-800 tabular-nums">{{ trade.acc_volume.toLocaleString() }}</p>
                </div>
                <div>
                  <p class="text-xs text-gray-400 mb-0.5">체결강도</p>
                  <p class="text-base font-bold tabular-nums" :class="trade.strength >= 100 ? 'text-red-600' : 'text-blue-600'">
                    {{ trade.strength }}%
                  </p>
                </div>
                <div class="ml-auto">
                  <span
                    class="text-xs font-bold px-2.5 py-1 rounded-full"
                    :class="trade.trade_type === '1' ? 'bg-red-50 text-red-600' : 'bg-blue-50 text-blue-600'"
                  >
                    {{ trade.trade_type === '1' ? '매수 체결' : '매도 체결' }}
                  </span>
                </div>
              </div>
            </div>

            <!-- ── 실시간 호가 잔량 ── -->
            <div v-if="orderbook" class="bg-white rounded-2xl border border-gray-100 overflow-hidden shadow-sm">
              <!-- 헤더 -->
              <div class="flex items-center gap-2 px-4 py-3 border-b border-gray-100">
                <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span class="text-xs font-bold text-gray-500 uppercase tracking-wider">호가 잔량 (10호가)</span>
                <span class="ml-auto text-xs text-gray-400 tabular-nums">{{ orderbook.time }}</span>
              </div>

              <!-- 컬럼 레이블 -->
              <div class="grid grid-cols-3 text-xs font-bold text-gray-400 bg-gray-50 px-4 py-1.5 border-b border-gray-100">
                <span class="text-red-400">매도 잔량</span>
                <span class="text-center">가격</span>
                <span class="text-right text-blue-400">매수 잔량</span>
              </div>

              <!-- 매도 10호가 (10위→1위, 높은 가격이 위) -->
              <div
                v-for="ask in asksReversed"
                :key="ask.price"
                class="grid grid-cols-3 items-center px-4 py-1 border-b border-gray-50 hover:bg-red-50 transition-colors"
              >
                <!-- 매도 잔량 바 (오른쪽→왼쪽 방향) -->
                <div class="relative h-6 flex items-center">
                  <div
                    class="absolute right-0 top-1 bottom-1 bg-red-100 rounded-sm transition-all duration-150"
                    :style="{ width: qtyBarWidth(ask.qty, orderbook.asks) + '%' }"
                  ></div>
                  <span class="relative z-10 text-xs font-mono text-red-700 tabular-nums">
                    {{ ask.qty.toLocaleString() }}
                  </span>
                </div>
                <!-- 매도가 -->
                <span class="text-center text-sm font-bold text-red-600 tabular-nums">
                  {{ ask.price.toLocaleString() }}
                </span>
                <div></div>
              </div>

              <!-- 총계 구분선 -->
              <div class="grid grid-cols-3 bg-gray-100 px-4 py-1.5 text-xs font-semibold">
                <span class="text-red-500 tabular-nums">총 {{ orderbook.total_ask_qty.toLocaleString() }}</span>
                <span class="text-center text-gray-500">[ 스프레드 ]</span>
                <span class="text-right text-blue-500 tabular-nums">총 {{ orderbook.total_bid_qty.toLocaleString() }}</span>
              </div>

              <!-- 매수 10호가 (1위→10위, 높은 가격이 위) -->
              <div
                v-for="(bid, i) in orderbook.bids"
                :key="'bid-' + i"
                class="grid grid-cols-3 items-center px-4 py-1 border-b border-gray-50 hover:bg-blue-50 transition-colors"
              >
                <div></div>
                <!-- 매수가 -->
                <span class="text-center text-sm font-bold text-blue-600 tabular-nums">
                  {{ bid.price.toLocaleString() }}
                </span>
                <!-- 매수 잔량 바 (왼쪽→오른쪽 방향) -->
                <div class="relative h-6 flex items-center justify-end">
                  <div
                    class="absolute left-0 top-1 bottom-1 bg-blue-100 rounded-sm transition-all duration-150"
                    :style="{ width: qtyBarWidth(bid.qty, orderbook.bids) + '%' }"
                  ></div>
                  <span class="relative z-10 text-xs font-mono text-blue-700 tabular-nums">
                    {{ bid.qty.toLocaleString() }}
                  </span>
                </div>
              </div>
            </div>

          </div>

          <!-- ── Sidebar: Watchlist ── -->
          <div>
            <div class="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm sticky top-20">
              <div class="flex items-center gap-2 mb-4">
                <Star class="w-4 h-4 text-amber-400 fill-amber-400" />
                <h2 class="font-bold text-gray-900 text-sm">관심 종목</h2>
                <span v-if="watchlist.length > 0" class="ml-auto text-xs text-gray-400 font-medium">{{ watchlist.length }}개</span>
              </div>

              <!-- Not logged in -->
              <div v-if="!isLoggedIn" class="text-center py-8">
                <Star class="w-8 h-8 text-gray-200 fill-gray-200 mx-auto mb-3" />
                <p class="text-sm text-gray-400 mb-4">로그인하면 관심 종목을<br>저장할 수 있습니다</p>
                <RouterLink
                  to="/login"
                  class="inline-block px-4 py-2 bg-blue-700 text-white text-sm font-semibold rounded-xl hover:bg-blue-800 transition-colors"
                >
                  로그인
                </RouterLink>
              </div>

              <!-- Empty watchlist -->
              <div v-else-if="watchlist.length === 0" class="text-center py-8">
                <Star class="w-8 h-8 text-gray-200 fill-gray-200 mx-auto mb-3" />
                <p class="text-sm text-gray-400">관심 종목이 없습니다<br>종목 검색 후 ☆ 버튼으로 추가하세요</p>
              </div>

              <!-- Watchlist items -->
              <div v-else class="space-y-1">
                <button
                  v-for="item in watchlist"
                  :key="item.symbol"
                  @click="selectStock(item.symbol, item.name)"
                  class="w-full flex items-center gap-3 p-3 rounded-xl transition-colors text-left group"
                  :class="selectedSymbol === item.symbol
                    ? 'bg-blue-50 border border-blue-200'
                    : 'hover:bg-gray-50 border border-transparent'"
                >
                  <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-blue-900 flex items-center justify-center text-white text-xs font-black flex-shrink-0">
                    {{ item.symbol.slice(0, 4) }}
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="font-bold text-gray-900 text-sm">{{ item.name }}</p>
                    <p class="text-xs text-gray-500 truncate">{{ item.symbol }}</p>
                  </div>
                  <button
                    @click.stop="toggleWatchlist(item.symbol, item.name)"
                    class="opacity-0 group-hover:opacity-100 text-gray-300 hover:text-red-400 transition-all p-1 rounded-lg hover:bg-red-50"
                  >
                    <X class="w-3.5 h-3.5" />
                  </button>
                </button>
              </div>
            </div>

          </div>

        </div>
      </div>
    </main>

    <AppFooter />
  </div>
</template>
