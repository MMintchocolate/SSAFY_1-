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
  <div class="min-h-screen bg-white" style="font-family:'Pretendard','Noto Sans KR',sans-serif">
    <NavBar />

    <main class="pt-16">
      <!-- 페이지 헤더 -->
      <div style="background:linear-gradient(90deg,#fffdf9 0%,#ffffff 50%,#f2fffb 100%);border-bottom:1px solid #EEF1F5">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 py-10">
          <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-bold mb-3" style="background:#DFFAF4;color:#0D9B7A;font-size:0.72rem">
            <BarChart2 class="w-3 h-3" />Yahoo Finance 실시간 데이터
          </div>
          <h1 class="font-black mb-1" style="font-size:1.8rem;color:#0F122B">주식 검색</h1>
          <p style="color:#6F7485;font-size:0.9rem">종목명 또는 티커로 검색하세요 (예: Apple, AAPL, 삼성전자, 005930.KS)</p>
        </div>
      </div>

      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-8">

        <!-- 검색 바 -->
        <div class="relative mb-8 max-w-2xl">
          <div class="flex items-center gap-2 px-4 py-3 rounded-2xl transition-all" style="background:white;border:1.5px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
            <Search class="w-5 h-5 flex-shrink-0" style="color:#6F7485" />
            <input
              v-model="query"
              @input="onInput"
              @keydown.enter="doSearch"
              placeholder="종목명 또는 티커 입력 (예: AAPL, Tesla)"
              class="flex-1 outline-none text-sm bg-transparent"
              style="color:#0F122B"
            />
            <button v-if="query" @click="clearSearch" style="color:#6F7485">
              <X class="w-4 h-4" />
            </button>
          </div>

          <div
            v-if="searchResults.length > 0 || searchLoading"
            class="absolute top-full mt-1 left-0 right-0 rounded-2xl z-20 overflow-hidden"
            style="background:white;border:1px solid #EEF1F5;box-shadow:0 8px 24px rgba(15,18,43,0.1)"
          >
            <div v-if="searchLoading" class="px-4 py-3 text-sm" style="color:#6F7485">검색 중...</div>
            <button
              v-for="r in searchResults"
              :key="r.symbol"
              @click="selectStock(r.symbol, r.name)"
              class="w-full flex items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-[#F8F9FF]"
              style="border-bottom:1px solid #EEF1F5"
            >
              <div class="w-10 h-10 rounded-xl flex items-center justify-center font-black flex-shrink-0" style="background:#0F122B;color:white;font-size:0.72rem">
                {{ r.symbol.slice(0, 4) }}
              </div>
              <div class="flex-1 min-w-0">
                <p class="font-semibold text-sm" style="color:#0F122B">{{ r.symbol }}</p>
                <p class="text-xs truncate" style="color:#6F7485">{{ r.name }}</p>
              </div>
              <span class="text-xs px-2 py-0.5 rounded-full flex-shrink-0" style="background:#F8F9FF;color:#6F7485">{{ r.exchange }}</span>
            </button>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

          <!-- 메인: 상세 + 차트 -->
          <div class="lg:col-span-2 space-y-4">

            <!-- 로딩 스켈레톤 -->
            <div v-if="detailLoading" class="rounded-2xl p-6 animate-pulse space-y-4" style="background:white;border:1px solid #EEF1F5">
              <div class="flex gap-3">
                <div class="w-14 h-14 rounded-xl" style="background:#EEF1F5"></div>
                <div class="flex-1 space-y-2 pt-1">
                  <div class="w-28 h-3 rounded" style="background:#EEF1F5"></div>
                  <div class="w-52 h-5 rounded" style="background:#EEF1F5"></div>
                </div>
              </div>
              <div class="w-44 h-10 rounded" style="background:#EEF1F5"></div>
              <div class="h-64 rounded-xl" style="background:#F8F9FF"></div>
            </div>

            <!-- 주식 상세 카드 -->
            <div v-else-if="stockDetail && !stockDetail.error" class="rounded-2xl p-6" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">

              <div class="flex items-start justify-between mb-5">
                <div class="flex items-center gap-3">
                  <div class="w-14 h-14 rounded-xl flex items-center justify-center font-black flex-shrink-0" style="background:#0F122B;color:white;font-size:0.85rem">
                    {{ selectedSymbol.slice(0, 4) }}
                  </div>
                  <div>
                    <p class="font-medium" style="font-size:0.72rem;color:#6F7485">{{ selectedSymbol }} · {{ stockDetail.exchange }}</p>
                    <p class="font-extrabold leading-tight" style="font-size:1.2rem;color:#0F122B">{{ stockDetail.name }}</p>
                    <p v-if="stockDetail.sector" class="mt-0.5" style="font-size:0.72rem;color:#6F7485">
                      {{ stockDetail.sector }}<span v-if="stockDetail.industry"> · {{ stockDetail.industry }}</span>
                    </p>
                  </div>
                </div>

                <button
                  v-if="isLoggedIn"
                  @click="toggleWatchlist(selectedSymbol, stockDetail.name)"
                  class="flex items-center gap-1.5 px-3 py-2 rounded-xl transition-all text-sm font-semibold flex-shrink-0"
                  :style="watchlistSet.has(selectedSymbol)
                    ? 'background:#FFF8E6;border:1.5px solid #FFD76A;color:#B8860B'
                    : 'background:white;border:1.5px solid #EEF1F5;color:#6F7485'"
                >
                  <Star class="w-4 h-4 transition-all" :class="watchlistSet.has(selectedSymbol) ? 'fill-amber-400 text-amber-400' : ''" />
                  {{ watchlistSet.has(selectedSymbol) ? '관심 해제' : '관심 종목' }}
                </button>
              </div>

              <div class="flex items-end gap-4 mb-5">
                <div>
                  <p class="mb-0.5" style="font-size:0.72rem;color:#6F7485">현재가</p>
                  <div class="flex items-end gap-1.5">
                    <span class="font-black leading-none tabular-nums" style="font-size:2.4rem;color:#0F122B">
                      {{ fmtPrice(stockDetail.price) }}
                    </span>
                    <span class="mb-0.5" style="font-size:1rem;color:#6F7485">{{ stockDetail.currency }}</span>
                  </div>
                </div>
                <div
                  v-if="stockDetail.change != null"
                  class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-sm font-bold mb-1"
                  :style="stockDetail.change >= 0 ? 'background:#FFF5F5;color:#E5323B' : 'background:#EBF1FF;color:#3B7FED'"
                >
                  <TrendingUp v-if="stockDetail.change >= 0" class="w-4 h-4" />
                  <TrendingDown v-else class="w-4 h-4" />
                  {{ stockDetail.change >= 0 ? '+' : '' }}{{ fmtChange(stockDetail.change) }}
                  ({{ stockDetail.change_pct >= 0 ? '+' : '' }}{{ stockDetail.change_pct?.toFixed(2) }}%)
                </div>
              </div>

              <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4 p-4 rounded-xl" style="background:#F8F9FF">
                <div>
                  <p class="mb-0.5" style="font-size:0.72rem;color:#6F7485">시가총액</p>
                  <p class="font-bold text-sm tabular-nums" style="color:#0F122B">{{ fmtCap(stockDetail.market_cap) }}</p>
                </div>
                <div>
                  <p class="mb-0.5" style="font-size:0.72rem;color:#6F7485">전일 종가</p>
                  <p class="font-bold text-sm tabular-nums" style="color:#0F122B">{{ fmtPrice(stockDetail.prev_close) }}</p>
                </div>
                <div>
                  <p class="mb-0.5" style="font-size:0.72rem;color:#6F7485">52주 고가</p>
                  <p class="font-bold text-sm tabular-nums" style="color:#E5323B">{{ fmtPrice(stockDetail.w52_high) }}</p>
                </div>
                <div>
                  <p class="mb-0.5" style="font-size:0.72rem;color:#6F7485">52주 저가</p>
                  <p class="font-bold text-sm tabular-nums" style="color:#3B7FED">{{ fmtPrice(stockDetail.w52_low) }}</p>
                </div>
              </div>

              <div class="flex gap-2 mb-5">
                <RouterLink to="/indicators" class="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all" style="background:#57E0C3;color:#0F122B">
                  <TrendingUp class="w-3.5 h-3.5" />매수신호 보러가기
                </RouterLink>
                <RouterLink to="/dataset" class="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all" style="background:#F8F9FF;color:#0F122B;border:1.5px solid #EEF1F5">
                  <BarChart2 class="w-3.5 h-3.5" />ML 데이터 보러가기
                </RouterLink>
              </div>

              <div class="flex items-center gap-2 mb-4 flex-wrap">
                <span class="font-medium" style="font-size:0.75rem;color:#6F7485">기간</span>
                <div class="flex gap-1.5">
                  <button
                    v-for="p in PERIODS" :key="p.value"
                    @click="period = p.value"
                    class="px-3 py-1.5 rounded-xl text-xs font-bold transition-all"
                    :style="period === p.value ? 'background:#0F122B;color:white' : 'background:#F8F9FF;color:#6F7485'"
                  >{{ p.label }}</button>
                </div>
                <div class="ml-auto flex gap-1 p-0.5 rounded-lg" style="background:#F8F9FF">
                  <button @click="viewMode = 'chart'" class="px-3 py-1 rounded-md text-xs font-bold transition-all"
                    :style="viewMode === 'chart' ? 'background:white;color:#0F122B;box-shadow:0 1px 4px rgba(15,18,43,0.08)' : 'color:#6F7485'"
                  >차트</button>
                  <button @click="viewMode = 'table'" class="px-3 py-1 rounded-md text-xs font-bold transition-all"
                    :style="viewMode === 'table' ? 'background:white;color:#0F122B;box-shadow:0 1px 4px rgba(15,18,43,0.08)' : 'color:#6F7485'"
                  >표</button>
                </div>
              </div>

              <div v-if="viewMode === 'chart'" class="relative h-64">
                <div v-if="historyLoading" class="absolute inset-0 flex items-center justify-center rounded-xl" style="background:#F8F9FF">
                  <span class="text-sm" style="color:#6F7485">차트 로딩 중...</span>
                </div>
                <Line v-else-if="history.length > 0" :data="chartData" :options="chartOptions" style="height:100%;width:100%" />
                <div v-else class="absolute inset-0 flex items-center justify-center text-sm" style="color:#6F7485">차트 데이터 없음</div>
              </div>

              <div v-else class="overflow-auto max-h-64 rounded-xl" style="border:1px solid #EEF1F5">
                <div v-if="historyLoading" class="py-8 text-center text-sm" style="color:#6F7485">로딩 중...</div>
                <table v-else-if="history.length > 0" class="w-full text-xs">
                  <thead class="sticky top-0" style="background:#F8F9FF;border-bottom:1px solid #EEF1F5">
                    <tr>
                      <th class="px-3 py-2 text-left font-bold" style="color:#6F7485">날짜</th>
                      <th class="px-3 py-2 text-right font-bold" style="color:#6F7485">시가</th>
                      <th class="px-3 py-2 text-right font-bold" style="color:#E5323B">고가</th>
                      <th class="px-3 py-2 text-right font-bold" style="color:#3B7FED">저가</th>
                      <th class="px-3 py-2 text-right font-bold" style="color:#0F122B">종가</th>
                      <th class="px-3 py-2 text-right font-bold" style="color:#6F7485">거래량</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="row in historyReversed" :key="row.date" class="transition-colors hover:bg-[#F8F9FF]" style="border-bottom:1px solid #EEF1F5">
                      <td class="px-3 py-1.5 tabular-nums" style="color:#6F7485">{{ row.date }}</td>
                      <td class="px-3 py-1.5 text-right tabular-nums font-mono" style="color:#0F122B">{{ row.open?.toLocaleString() }}</td>
                      <td class="px-3 py-1.5 text-right tabular-nums font-mono" style="color:#E5323B">{{ row.high?.toLocaleString() }}</td>
                      <td class="px-3 py-1.5 text-right tabular-nums font-mono" style="color:#3B7FED">{{ row.low?.toLocaleString() }}</td>
                      <td class="px-3 py-1.5 text-right font-bold tabular-nums font-mono" style="color:#0F122B">{{ row.close?.toLocaleString() }}</td>
                      <td class="px-3 py-1.5 text-right tabular-nums font-mono" style="color:#6F7485">{{ row.volume?.toLocaleString() }}</td>
                    </tr>
                  </tbody>
                </table>
                <div v-else class="py-8 text-center text-sm" style="color:#6F7485">데이터 없음</div>
              </div>
            </div>

            <!-- 에러 -->
            <div v-else-if="stockDetail?.error" class="rounded-2xl p-8 text-center" style="background:white;border:1px solid #FFD0D0">
              <p class="font-semibold" style="color:#E5323B">데이터를 불러오지 못했습니다</p>
              <p class="text-sm mt-1" style="color:#E5323B">{{ stockDetail.error }}</p>
            </div>

            <!-- 빈 상태 -->
            <div v-else class="rounded-2xl p-16 text-center" style="background:white;border:1px solid #EEF1F5">
              <div class="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4" style="background:#DFFAF4">
                <BarChart2 class="w-8 h-8" style="color:#57E0C3" />
              </div>
              <p class="font-bold mb-2" style="color:#0F122B">종목을 검색하세요</p>
              <p class="text-sm" style="color:#6F7485">티커(AAPL) 또는 회사명(Apple, 삼성전자)으로 검색</p>
            </div>

            <!-- 실시간 체결가 -->
            <div v-if="trade" class="rounded-2xl p-5" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
              <div class="flex items-center gap-2 mb-4">
                <span class="w-2 h-2 rounded-full animate-pulse" style="background:#57E0C3"></span>
                <span class="font-bold" style="font-size:0.72rem;color:#6F7485;letter-spacing:0.08em">실시간 체결</span>
                <span class="ml-auto tabular-nums" style="font-size:0.72rem;color:#6F7485">{{ trade.time }}</span>
              </div>
              <div class="flex items-center gap-5 flex-wrap">
                <div>
                  <p class="mb-0.5" style="font-size:0.72rem;color:#6F7485">체결가</p>
                  <span class="font-black tabular-nums" style="font-size:1.8rem" :class="signColor(trade.sign)">{{ trade.price.toLocaleString() }}</span>
                </div>
                <div>
                  <p class="mb-0.5" style="font-size:0.72rem;color:#6F7485">대비</p>
                  <p class="font-bold text-lg tabular-nums" :class="signColor(trade.sign)">
                    {{ trade.change >= 0 ? '+' : '' }}{{ trade.change.toLocaleString() }}
                    <span class="text-sm">({{ trade.change_rate >= 0 ? '+' : '' }}{{ trade.change_rate }}%)</span>
                  </p>
                </div>
                <div>
                  <p class="mb-0.5" style="font-size:0.72rem;color:#6F7485">체결량</p>
                  <p class="font-bold tabular-nums" style="color:#0F122B">{{ trade.volume.toLocaleString() }}</p>
                </div>
                <div>
                  <p class="mb-0.5" style="font-size:0.72rem;color:#6F7485">누적거래량</p>
                  <p class="font-bold tabular-nums" style="color:#0F122B">{{ trade.acc_volume.toLocaleString() }}</p>
                </div>
                <div>
                  <p class="mb-0.5" style="font-size:0.72rem;color:#6F7485">체결강도</p>
                  <p class="font-bold tabular-nums" :style="trade.strength >= 100 ? 'color:#E5323B' : 'color:#3B7FED'">{{ trade.strength }}%</p>
                </div>
                <div class="ml-auto">
                  <span class="text-xs font-bold px-2.5 py-1 rounded-full"
                    :style="trade.trade_type === '1' ? 'background:#FFF5F5;color:#E5323B' : 'background:#EBF1FF;color:#3B7FED'"
                  >{{ trade.trade_type === '1' ? '매수 체결' : '매도 체결' }}</span>
                </div>
              </div>
            </div>

            <!-- 실시간 호가 잔량 -->
            <div v-if="orderbook" class="rounded-2xl overflow-hidden" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
              <div class="flex items-center gap-2 px-4 py-3" style="border-bottom:1px solid #EEF1F5">
                <span class="w-2 h-2 rounded-full animate-pulse" style="background:#57E0C3"></span>
                <span class="font-bold" style="font-size:0.72rem;color:#6F7485;letter-spacing:0.08em">호가 잔량 (10호가)</span>
                <span class="ml-auto tabular-nums" style="font-size:0.72rem;color:#6F7485">{{ orderbook.time }}</span>
              </div>
              <div class="grid grid-cols-3 font-bold px-4 py-1.5" style="background:#F8F9FF;font-size:0.72rem;border-bottom:1px solid #EEF1F5">
                <span style="color:#E5323B">매도 잔량</span>
                <span class="text-center" style="color:#6F7485">가격</span>
                <span class="text-right" style="color:#3B7FED">매수 잔량</span>
              </div>
              <div v-for="ask in asksReversed" :key="ask.price"
                class="grid grid-cols-3 items-center px-4 py-1 transition-colors hover:bg-[#FFF5F5]"
                style="border-bottom:1px solid #EEF1F5"
              >
                <div class="relative h-6 flex items-center">
                  <div class="absolute right-0 top-1 bottom-1 rounded-sm transition-all duration-150" style="background:rgba(229,50,59,0.12)" :style="{ width: qtyBarWidth(ask.qty, orderbook.asks) + '%' }"></div>
                  <span class="relative z-10 font-mono tabular-nums" style="font-size:0.72rem;color:#E5323B">{{ ask.qty.toLocaleString() }}</span>
                </div>
                <span class="text-center font-bold tabular-nums" style="font-size:0.85rem;color:#E5323B">{{ ask.price.toLocaleString() }}</span>
                <div></div>
              </div>
              <div class="grid grid-cols-3 px-4 py-1.5 font-semibold" style="background:#F8F9FF;font-size:0.72rem">
                <span class="tabular-nums" style="color:#E5323B">총 {{ orderbook.total_ask_qty.toLocaleString() }}</span>
                <span class="text-center" style="color:#6F7485">[ 스프레드 ]</span>
                <span class="text-right tabular-nums" style="color:#3B7FED">총 {{ orderbook.total_bid_qty.toLocaleString() }}</span>
              </div>
              <div v-for="(bid, i) in orderbook.bids" :key="'bid-' + i"
                class="grid grid-cols-3 items-center px-4 py-1 transition-colors hover:bg-[#EBF1FF]"
                style="border-bottom:1px solid #EEF1F5"
              >
                <div></div>
                <span class="text-center font-bold tabular-nums" style="font-size:0.85rem;color:#3B7FED">{{ bid.price.toLocaleString() }}</span>
                <div class="relative h-6 flex items-center justify-end">
                  <div class="absolute left-0 top-1 bottom-1 rounded-sm transition-all duration-150" style="background:rgba(59,127,237,0.12)" :style="{ width: qtyBarWidth(bid.qty, orderbook.bids) + '%' }"></div>
                  <span class="relative z-10 font-mono tabular-nums" style="font-size:0.72rem;color:#3B7FED">{{ bid.qty.toLocaleString() }}</span>
                </div>
              </div>
            </div>

          </div>

          <!-- 사이드바: 관심 종목 -->
          <div>
            <div class="rounded-2xl p-5 sticky top-20" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
              <div class="flex items-center gap-2 mb-4">
                <Star class="w-4 h-4 fill-amber-400 text-amber-400" />
                <h2 class="font-bold text-sm" style="color:#0F122B">관심 종목</h2>
                <span v-if="watchlist.length > 0" class="ml-auto font-medium" style="font-size:0.75rem;color:#6F7485">{{ watchlist.length }}개</span>
              </div>

              <div v-if="!isLoggedIn" class="text-center py-8">
                <Star class="w-8 h-8 mx-auto mb-3" style="color:#EEF1F5;fill:#EEF1F5" />
                <p class="text-sm mb-4" style="color:#6F7485">로그인하면 관심 종목을<br>저장할 수 있습니다</p>
                <RouterLink to="/login" class="inline-block px-4 py-2 rounded-xl text-sm font-semibold transition-all" style="background:#0F122B;color:white">로그인</RouterLink>
              </div>

              <div v-else-if="watchlist.length === 0" class="text-center py-8">
                <Star class="w-8 h-8 mx-auto mb-3" style="color:#EEF1F5;fill:#EEF1F5" />
                <p class="text-sm" style="color:#6F7485">관심 종목이 없습니다<br>종목 검색 후 ☆ 버튼으로 추가하세요</p>
              </div>

              <div v-else class="space-y-1">
                <button
                  v-for="item in watchlist" :key="item.symbol"
                  @click="selectStock(item.symbol, item.name)"
                  class="w-full flex items-center gap-3 p-3 rounded-xl transition-colors text-left group"
                  :style="selectedSymbol === item.symbol ? 'background:#DFFAF4;border:1px solid #57E0C3' : 'border:1px solid transparent'"
                >
                  <div class="w-10 h-10 rounded-xl flex items-center justify-center font-black flex-shrink-0" style="background:#0F122B;color:white;font-size:0.72rem">
                    {{ item.symbol.slice(0, 4) }}
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="font-bold text-sm" style="color:#0F122B">{{ item.name }}</p>
                    <p class="text-xs truncate" style="color:#6F7485">{{ item.symbol }}</p>
                  </div>
                  <button @click.stop="toggleWatchlist(item.symbol, item.name)"
                    class="opacity-0 group-hover:opacity-100 p-1 rounded-lg transition-all"
                    style="color:#6F7485"
                  ><X class="w-3.5 h-3.5" /></button>
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
