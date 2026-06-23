<script setup>
// @ts-nocheck
import { ref, onMounted } from 'vue'
import NavBar from '@/components/NavBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import { Star, TrendingUp, TrendingDown, Activity, BarChart2, AlertCircle, RefreshCw, HelpCircle, ChevronDown, ChevronLeft, ChevronRight, Newspaper, ExternalLink, Play } from '@lucide/vue'
import { useAuth } from '@/composables/useAuth'

const { authFetch } = useAuth()
const API = '/api/stocks'

const watchlist   = ref([])
const selected    = ref(null)
const indicators  = ref(null)
const loading     = ref(false)
const error       = ref('')

// ── 종목 뉴스 ─────────────────────────────────────────────────────
const stockNews        = ref([])
const newsLoading      = ref(false)
const newsError        = ref('')

// 종목 유튜브 데이터
const stock_youtube_data = ref([])
const youtubeIndex       = ref(0)

// 각 지표 설명 토글
const infoOpen = ref({ ma: false, rsi: false, macd: false, bollinger: false })

const INFO = {
  ma: {
    title: '이동평균선 (MA) 이란?',
    desc: '일정 기간의 종가 평균을 이어 그린 선입니다. 주가의 큰 방향성(추세)을 파악하는 데 사용합니다.',
    items: [
      { label: 'MA50 > 현재가', meaning: '단기 하락세. 현재가가 50일 평균 아래에 있음' },
      { label: 'MA50 < 현재가', meaning: '단기 상승세. 현재가가 50일 평균 위에 있음' },
      { label: '골든크로스', meaning: 'MA50이 MA200을 위로 돌파 → 강한 매수 신호' },
      { label: '데드크로스', meaning: 'MA50이 MA200을 아래로 이탈 → 강한 매도 신호' },
    ],
  },
  rsi: {
    title: 'RSI (상대강도지수) 란?',
    desc: '최근 14일간 상승 폭과 하락 폭의 비율로 매수세·매도세의 강도를 0~100 사이 수치로 나타냅니다.',
    items: [
      { label: 'RSI < 30', meaning: '과매도 — 매도가 과도하게 진행됨, 반등 가능성 ↑ (매수 신호)' },
      { label: 'RSI 30~70', meaning: '중립 — 특별한 신호 없음' },
      { label: 'RSI > 70', meaning: '과매수 — 매수가 과도하게 진행됨, 조정 가능성 ↑ (매도 신호)' },
    ],
  },
  macd: {
    title: 'MACD 란?',
    desc: '단기(12일) 지수이동평균과 장기(26일) 지수이동평균의 차이로 주가 모멘텀(방향성)을 측정합니다. 시그널선(9일 EMA)과의 교차가 매매 신호입니다.',
    items: [
      { label: 'MACD선 > 시그널선', meaning: '상승 모멘텀. 히스토그램이 양수(+)' },
      { label: 'MACD선 < 시그널선', meaning: '하락 모멘텀. 히스토그램이 음수(-)' },
      { label: 'MACD 골든크로스', meaning: 'MACD선이 시그널선을 위로 돌파 → 매수 신호' },
      { label: 'MACD 데드크로스', meaning: 'MACD선이 시그널선을 아래로 이탈 → 매도 신호' },
    ],
  },
  bollinger: {
    title: '볼린저 밴드 란?',
    desc: '20일 이동평균선(중심)을 기준으로 ±2 표준편차 범위의 상·하단 밴드를 그립니다. 가격 변동성과 과매도·과매수를 파악합니다.',
    items: [
      { label: '가격 ≤ 하단 밴드', meaning: '과매도 — 밴드 밖으로 이탈, 반등 가능성 ↑ (매수 신호)' },
      { label: '가격 ≥ 상단 밴드', meaning: '과매수 — 밴드 밖으로 이탈, 조정 가능성 ↑ (매도 신호)' },
      { label: '가격 = 중심선', meaning: '밴드 내 중립 위치' },
      { label: '밴드 폭 좁아짐', meaning: '변동성 감소 — 곧 큰 움직임이 올 수 있음(스퀴즈)' },
    ],
  },
}

async function loadWatchlist() {
  try {
    const res = await authFetch(`${API}/watchlist/`)
    if (res.ok) watchlist.value = await res.json()
  } catch { /* ignore */ }
}

async function selectStock(item) {
  selected.value   = item
  indicators.value = null
  error.value      = ''
  loading.value    = true
  stockNews.value  = []
  newsError.value  = ''
  stock_youtube_data.value = []
  youtubeIndex.value       = 0
  try {
    const res  = await authFetch(`${API}/${item.symbol}/indicators/`)
    const data = await res.json()
    if (data.error) throw new Error(data.error)
    indicators.value = data
  } catch (e) {
    error.value = e.message || '지표 계산 실패'
  } finally {
    loading.value = false
  }
  // 종목 이름을 백엔드로 전송
  const res = await fetch(`/api/stocks/stock-name/?stock_name=${encodeURIComponent(item.name || item.symbol)}`)
  console.log("프론트 조회 완료", res)  
  const data = await res.json()
  stock_youtube_data.value = data['videos']
  console.log("데이터 조회 완료", data['videos'])  
  // 지표 로딩과 병렬로 뉴스 조회
  fetchStockNews(item.name || item.symbol)
}

async function fetchStockNews(query) {
  newsLoading.value = true
  newsError.value   = ''
  try {
    const res  = await fetch(`/api/news/stock/?q=${encodeURIComponent(query)}&display=5`)
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || '뉴스 조회 실패')
    stockNews.value = data.results ?? []
  } catch (e) {
    newsError.value = e.message || '뉴스 조회 실패'
  } finally {
    newsLoading.value = false
  }
}

// ── 포맷 헬퍼 ────────────────────────────────────────────────────
function fmt(n, digits = 2) {
  if (n == null) return '-'
  return Number(n).toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits })
}

function signalLabel(sig) {
  return { buy: '매수', sell: '매도', oversold: '과매도(매수)', overbought: '과매수(매도)', neutral: '중립', golden: '골든크로스', dead: '데드크로스' }[sig] ?? sig
}

function nearCurrent(i) {
  return Math.abs(i - youtubeIndex.value) <= 2
}

function signalClass(sig) {
  if (['buy', 'oversold', 'golden'].includes(sig))  return 'bg-emerald-50 text-emerald-700 border-emerald-200'
  if (['sell', 'overbought', 'dead'].includes(sig)) return 'bg-red-50 text-red-700 border-red-200'
  return 'bg-gray-100 text-gray-500 border-gray-200'
}

onMounted(loadWatchlist)
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <NavBar />

    <main class="pt-16">
      <!-- Header -->
      <div class="bg-white border-b border-gray-100">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 py-10">
          <div class="inline-flex items-center gap-2 bg-blue-50 text-blue-700 text-xs font-bold px-3 py-1.5 rounded-full mb-3 uppercase tracking-widest border border-blue-100">
            <Activity class="w-3 h-3" />기술적 분석
          </div>
          <h1 class="text-3xl font-extrabold text-gray-900 mb-1">매수 타이밍 지표</h1>
          <p class="text-gray-400">관심 종목의 MA · RSI · MACD · 볼린저 밴드를 한눈에</p>
        </div>
      </div>

      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-8 flex gap-6">

        <!-- ── 왼쪽: 관심종목 목록 ── -->
        <aside class="w-56 flex-shrink-0">
          <div class="bg-white rounded-2xl border border-gray-100 p-4 shadow-sm sticky top-20">
            <div class="flex items-center gap-2 mb-3">
              <Star class="w-4 h-4 text-amber-400 fill-amber-400" />
              <span class="text-sm font-bold text-gray-900">관심 종목</span>
              <span class="ml-auto text-xs text-gray-400">{{ watchlist.length }}개</span>
            </div>

            <div v-if="watchlist.length === 0" class="text-center py-6">
              <Star class="w-7 h-7 text-gray-200 fill-gray-200 mx-auto mb-2" />
              <p class="text-xs text-gray-400">관심 종목이 없습니다<br>주식 페이지에서 추가하세요</p>
            </div>

            <div v-else class="space-y-1">
              <button
                v-for="item in watchlist"
                :key="item.symbol"
                @click="selectStock(item)"
                class="w-full flex items-center gap-2.5 p-2.5 rounded-xl text-left transition-all"
                :class="selected?.symbol === item.symbol
                  ? 'bg-blue-50 border border-blue-200'
                  : 'hover:bg-gray-50 border border-transparent'"
              >
                <div class="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-600 to-blue-900 flex items-center justify-center text-white text-xs font-black flex-shrink-0">
                  {{ item.symbol.slice(0, 3) }}
                </div>
                <div class="min-w-0">
                  <p class="text-xs font-bold text-gray-900 truncate">{{ item.symbol }}</p>
                  <p class="text-xs text-gray-400 truncate">{{ item.name }}</p>
                </div>
              </button>
            </div>
          </div>
        </aside>

        <!-- ── 오른쪽: 지표 패널 ── -->
        <div class="flex-1 min-w-0">

          <!-- 미선택 -->
          <div v-if="!selected" class="bg-white rounded-2xl border border-gray-100 p-16 text-center shadow-sm">
            <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-100 to-blue-200 flex items-center justify-center mx-auto mb-4">
              <Activity class="w-8 h-8 text-blue-500" />
            </div>
            <p class="font-bold text-gray-900 mb-1">왼쪽 관심 종목을 선택하세요</p>
            <p class="text-sm text-gray-400">4가지 기술 지표가 표시됩니다</p>
          </div>

          <!-- 로딩 -->
          <div v-else-if="loading" class="bg-white rounded-2xl border border-gray-100 p-16 text-center shadow-sm">
            <RefreshCw class="w-8 h-8 text-blue-400 animate-spin mx-auto mb-3" />
            <p class="text-sm text-gray-400">지표 계산 중...</p>
          </div>

          <!-- 에러 -->
          <div v-else-if="error" class="bg-white rounded-2xl border border-red-100 p-10 text-center shadow-sm">
            <AlertCircle class="w-8 h-8 text-red-400 mx-auto mb-3" />
            <p class="font-semibold text-red-600">{{ error }}</p>
          </div>

          <!-- 지표 결과 -->
          <div v-else-if="indicators" class="space-y-4">

            <!-- 종목 헤더 -->
            <div class="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm flex items-center gap-4">
              <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-700 to-blue-900 flex items-center justify-center text-white text-sm font-black">
                {{ selected.symbol.slice(0, 4) }}
              </div>
              <div>
                <p class="text-xs text-gray-400">{{ selected.symbol }}</p>
                <p class="text-lg font-extrabold text-gray-900">{{ selected.name }}</p>
              </div>
              <div class="ml-auto text-right">
                <p class="text-xs text-gray-400 mb-0.5">현재가</p>
                <p class="text-2xl font-black tabular-nums text-gray-900">{{ indicators.price?.toLocaleString() }}</p>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">

              <!-- ── MA ── -->
              <div class="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
                <div class="flex items-center gap-2 mb-1">
                  <TrendingUp class="w-4 h-4 text-blue-500" />
                  <h3 class="font-bold text-gray-900 text-sm">이동평균선 (MA)</h3>
                  <span v-if="indicators.ma.cross"
                    class="text-xs font-bold px-2 py-0.5 rounded-full border"
                    :class="signalClass(indicators.ma.cross)"
                  >{{ signalLabel(indicators.ma.cross) }}</span>
                  <button @click="infoOpen.ma = !infoOpen.ma"
                    class="ml-auto flex items-center gap-0.5 text-xs text-gray-400 hover:text-blue-500 transition-colors"
                  >
                    <HelpCircle class="w-4 h-4" />
                    <ChevronDown class="w-3 h-3 transition-transform" :class="{ 'rotate-180': infoOpen.ma }" />
                  </button>
                </div>
                <!-- 설명 패널 -->
                <div v-if="infoOpen.ma" class="mb-4 p-3 bg-blue-50 rounded-xl border border-blue-100 text-xs text-blue-800 space-y-2">
                  <p class="font-bold text-blue-900">{{ INFO.ma.title }}</p>
                  <p class="text-blue-700 leading-relaxed">{{ INFO.ma.desc }}</p>
                  <ul class="space-y-1 mt-2">
                    <li v-for="i in INFO.ma.items" :key="i.label" class="flex gap-2">
                      <span class="font-bold whitespace-nowrap text-blue-900">{{ i.label }}</span>
                      <span class="text-blue-700">→ {{ i.meaning }}</span>
                    </li>
                  </ul>
                </div>
                <div class="mt-3"></div>

                <div class="space-y-3">
                  <!-- 현재가 -->
                  <div class="flex justify-between items-center py-2 border-b border-gray-50">
                    <span class="text-xs text-gray-500 font-medium">현재가</span>
                    <span class="text-sm font-bold text-gray-900 tabular-nums">{{ indicators.price?.toLocaleString() }}</span>
                  </div>
                  <!-- MA50 -->
                  <div class="flex justify-between items-center py-2 border-b border-gray-50">
                    <span class="text-xs text-gray-500 font-medium">MA 50일</span>
                    <div class="flex items-center gap-2">
                      <span class="text-sm font-bold tabular-nums"
                        :class="indicators.price > indicators.ma.ma50 ? 'text-emerald-600' : 'text-red-500'"
                      >{{ fmt(indicators.ma.ma50) }}</span>
                      <TrendingUp v-if="indicators.price > indicators.ma.ma50" class="w-3 h-3 text-emerald-500" />
                      <TrendingDown v-else class="w-3 h-3 text-red-500" />
                    </div>
                  </div>
                  <!-- MA200 -->
                  <div class="flex justify-between items-center py-2">
                    <span class="text-xs text-gray-500 font-medium">MA 200일</span>
                    <div class="flex items-center gap-2">
                      <span v-if="indicators.ma.ma200" class="text-sm font-bold tabular-nums"
                        :class="indicators.price > indicators.ma.ma200 ? 'text-emerald-600' : 'text-red-500'"
                      >{{ fmt(indicators.ma.ma200) }}</span>
                      <span v-else class="text-sm text-gray-400">데이터 부족</span>
                      <TrendingUp v-if="indicators.ma.ma200 && indicators.price > indicators.ma.ma200" class="w-3 h-3 text-emerald-500" />
                      <TrendingDown v-else-if="indicators.ma.ma200" class="w-3 h-3 text-red-500" />
                    </div>
                  </div>
                </div>

                <div class="mt-4 p-3 rounded-xl text-xs font-medium"
                  :class="indicators.ma.above200 ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'"
                >
                  {{ indicators.ma.above200 ? '📈 MA50이 MA200 위 — 장기 상승 추세' : '📉 MA50이 MA200 아래 — 장기 하락 추세' }}
                </div>
              </div>

              <!-- ── RSI ── -->
              <div class="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
                <div class="flex items-center gap-2 mb-1">
                  <Activity class="w-4 h-4 text-purple-500" />
                  <h3 class="font-bold text-gray-900 text-sm">RSI (14일)</h3>
                  <span class="text-xs font-bold px-2 py-0.5 rounded-full border"
                    :class="signalClass(indicators.rsi.signal)"
                  >{{ signalLabel(indicators.rsi.signal) }}</span>
                  <button @click="infoOpen.rsi = !infoOpen.rsi"
                    class="ml-auto flex items-center gap-0.5 text-xs text-gray-400 hover:text-purple-500 transition-colors"
                  >
                    <HelpCircle class="w-4 h-4" />
                    <ChevronDown class="w-3 h-3 transition-transform" :class="{ 'rotate-180': infoOpen.rsi }" />
                  </button>
                </div>
                <div v-if="infoOpen.rsi" class="mb-4 p-3 bg-purple-50 rounded-xl border border-purple-100 text-xs text-purple-800 space-y-2">
                  <p class="font-bold text-purple-900">{{ INFO.rsi.title }}</p>
                  <p class="text-purple-700 leading-relaxed">{{ INFO.rsi.desc }}</p>
                  <ul class="space-y-1 mt-2">
                    <li v-for="i in INFO.rsi.items" :key="i.label" class="flex gap-2">
                      <span class="font-bold whitespace-nowrap text-purple-900">{{ i.label }}</span>
                      <span class="text-purple-700">→ {{ i.meaning }}</span>
                    </li>
                  </ul>
                </div>
                <div class="mt-3"></div>

                <!-- RSI 게이지 -->
                <div class="mb-4">
                  <div class="flex justify-between text-xs text-gray-400 mb-1">
                    <span>0</span><span>30</span><span>70</span><span>100</span>
                  </div>
                  <div class="relative h-4 rounded-full overflow-hidden flex">
                    <div class="w-[30%] bg-emerald-100"></div>
                    <div class="w-[40%] bg-gray-100"></div>
                    <div class="w-[30%] bg-red-100"></div>
                    <!-- 포인터 -->
                    <div
                      class="absolute top-0 bottom-0 w-1 bg-gray-800 rounded-full shadow"
                      :style="{ left: `calc(${indicators.rsi.value}% - 2px)` }"
                    ></div>
                  </div>
                  <div class="flex justify-between text-xs mt-1 text-gray-400">
                    <span class="text-emerald-600 font-semibold">과매도</span>
                    <span>중립</span>
                    <span class="text-red-500 font-semibold">과매수</span>
                  </div>
                </div>

                <div class="text-center">
                  <span class="text-4xl font-black tabular-nums"
                    :class="indicators.rsi.signal === 'oversold' ? 'text-emerald-600'
                           : indicators.rsi.signal === 'overbought' ? 'text-red-600'
                           : 'text-gray-800'"
                  >{{ fmt(indicators.rsi.value) }}</span>
                </div>

                <div class="mt-4 p-3 rounded-xl bg-gray-50 text-xs text-gray-600">
                  RSI {{ fmt(indicators.rsi.value) }} —
                  <span v-if="indicators.rsi.signal === 'oversold'" class="text-emerald-700 font-semibold">30 미만: 과매도 구간, 반등 가능성</span>
                  <span v-else-if="indicators.rsi.signal === 'overbought'" class="text-red-600 font-semibold">70 초과: 과매수 구간, 조정 가능성</span>
                  <span v-else class="text-gray-500">중립 구간 (30~70)</span>
                </div>
              </div>

              <!-- ── MACD ── -->
              <div class="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
                <div class="flex items-center gap-2 mb-1">
                  <BarChart2 class="w-4 h-4 text-indigo-500" />
                  <h3 class="font-bold text-gray-900 text-sm">MACD (12, 26, 9)</h3>
                  <span v-if="indicators.macd.cross"
                    class="text-xs font-bold px-2 py-0.5 rounded-full border"
                    :class="signalClass(indicators.macd.cross)"
                  >{{ indicators.macd.cross === 'buy' ? '매수 크로스' : '매도 크로스' }}</span>
                  <button @click="infoOpen.macd = !infoOpen.macd"
                    class="ml-auto flex items-center gap-0.5 text-xs text-gray-400 hover:text-indigo-500 transition-colors"
                  >
                    <HelpCircle class="w-4 h-4" />
                    <ChevronDown class="w-3 h-3 transition-transform" :class="{ 'rotate-180': infoOpen.macd }" />
                  </button>
                </div>
                <div v-if="infoOpen.macd" class="mb-4 p-3 bg-indigo-50 rounded-xl border border-indigo-100 text-xs text-indigo-800 space-y-2">
                  <p class="font-bold text-indigo-900">{{ INFO.macd.title }}</p>
                  <p class="text-indigo-700 leading-relaxed">{{ INFO.macd.desc }}</p>
                  <ul class="space-y-1 mt-2">
                    <li v-for="i in INFO.macd.items" :key="i.label" class="flex gap-2">
                      <span class="font-bold whitespace-nowrap text-indigo-900">{{ i.label }}</span>
                      <span class="text-indigo-700">→ {{ i.meaning }}</span>
                    </li>
                  </ul>
                </div>
                <div class="mt-3"></div>

                <div class="space-y-3">
                  <div class="flex justify-between items-center py-2 border-b border-gray-50">
                    <span class="text-xs text-gray-500">MACD선</span>
                    <span class="text-sm font-bold tabular-nums"
                      :class="indicators.macd.macd >= 0 ? 'text-emerald-600' : 'text-red-500'"
                    >{{ fmt(indicators.macd.macd, 4) }}</span>
                  </div>
                  <div class="flex justify-between items-center py-2 border-b border-gray-50">
                    <span class="text-xs text-gray-500">시그널선</span>
                    <span class="text-sm font-bold tabular-nums text-gray-700">{{ fmt(indicators.macd.signal, 4) }}</span>
                  </div>
                  <div class="flex justify-between items-center py-2">
                    <span class="text-xs text-gray-500">히스토그램</span>
                    <span class="text-sm font-bold tabular-nums"
                      :class="indicators.macd.histogram >= 0 ? 'text-emerald-600' : 'text-red-500'"
                    >{{ fmt(indicators.macd.histogram, 4) }}</span>
                  </div>
                </div>

                <div class="mt-4 p-3 rounded-xl text-xs font-medium"
                  :class="indicators.macd.macd > indicators.macd.signal ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'"
                >
                  {{ indicators.macd.macd > indicators.macd.signal
                    ? '📈 MACD > 시그널 — 상승 모멘텀'
                    : '📉 MACD < 시그널 — 하락 모멘텀' }}
                </div>
              </div>

              <!-- ── Bollinger ── -->
              <div class="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
                <div class="flex items-center gap-2 mb-1">
                  <Activity class="w-4 h-4 text-orange-500" />
                  <h3 class="font-bold text-gray-900 text-sm">볼린저 밴드 (20일)</h3>
                  <span class="text-xs font-bold px-2 py-0.5 rounded-full border"
                    :class="signalClass(indicators.bollinger.signal)"
                  >{{ signalLabel(indicators.bollinger.signal) }}</span>
                  <button @click="infoOpen.bollinger = !infoOpen.bollinger"
                    class="ml-auto flex items-center gap-0.5 text-xs text-gray-400 hover:text-orange-500 transition-colors"
                  >
                    <HelpCircle class="w-4 h-4" />
                    <ChevronDown class="w-3 h-3 transition-transform" :class="{ 'rotate-180': infoOpen.bollinger }" />
                  </button>
                </div>
                <div v-if="infoOpen.bollinger" class="mb-4 p-3 bg-orange-50 rounded-xl border border-orange-100 text-xs text-orange-800 space-y-2">
                  <p class="font-bold text-orange-900">{{ INFO.bollinger.title }}</p>
                  <p class="text-orange-700 leading-relaxed">{{ INFO.bollinger.desc }}</p>
                  <ul class="space-y-1 mt-2">
                    <li v-for="i in INFO.bollinger.items" :key="i.label" class="flex gap-2">
                      <span class="font-bold whitespace-nowrap text-orange-900">{{ i.label }}</span>
                      <span class="text-orange-700">→ {{ i.meaning }}</span>
                    </li>
                  </ul>
                </div>
                <div class="mt-3"></div>

                <div class="space-y-2 mb-4">
                  <div class="flex justify-between text-xs">
                    <span class="text-red-500 font-semibold">상단 밴드</span>
                    <span class="font-bold tabular-nums text-gray-800">{{ fmt(indicators.bollinger.upper) }}</span>
                  </div>
                  <div class="flex justify-between text-xs">
                    <span class="text-gray-500">중심선 (MA20)</span>
                    <span class="font-bold tabular-nums text-gray-800">{{ fmt(indicators.bollinger.middle) }}</span>
                  </div>
                  <div class="flex justify-between text-xs">
                    <span class="text-emerald-600 font-semibold">하단 밴드</span>
                    <span class="font-bold tabular-nums text-gray-800">{{ fmt(indicators.bollinger.lower) }}</span>
                  </div>
                </div>

                <!-- 밴드 내 위치 바 -->
                <div class="mb-3">
                  <div class="flex justify-between text-xs text-gray-400 mb-1">
                    <span class="text-emerald-600">하단(매수)</span>
                    <span>중심</span>
                    <span class="text-red-500">상단(매도)</span>
                  </div>
                  <div class="relative h-3 bg-gradient-to-r from-emerald-100 via-gray-100 to-red-100 rounded-full">
                    <div
                      class="absolute top-0 bottom-0 w-2 h-2 m-auto rounded-full bg-gray-800 shadow border-2 border-white"
                      :style="{ left: `calc(${Math.min(Math.max(indicators.bollinger.position, 2), 98)}% - 4px)` }"
                    ></div>
                  </div>
                  <p class="text-xs text-center text-gray-500 mt-1">밴드 내 위치 {{ indicators.bollinger.position }}%</p>
                </div>

                <div class="p-3 rounded-xl bg-gray-50 text-xs text-gray-600">
                  <span v-if="indicators.bollinger.signal === 'buy'" class="text-emerald-700 font-semibold">하단 밴드 도달 — 과매도, 반등 가능성</span>
                  <span v-else-if="indicators.bollinger.signal === 'sell'" class="text-red-600 font-semibold">상단 밴드 도달 — 과매수, 조정 가능성</span>
                  <span v-else>현재가 밴드 내 위치: {{ indicators.bollinger.position }}% (0%=하단, 100%=상단)</span>
                </div>
              </div>

            </div><!-- /grid -->

            <!-- ── 관련 뉴스 ── -->
            <div class="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
              <div class="flex items-center gap-2 mb-4">
                <Newspaper class="w-4 h-4 text-blue-500" />
                <h3 class="font-bold text-gray-900 text-sm">관련 뉴스</h3>
                <span class="text-xs text-gray-400 ml-1">{{ selected.name }}</span>
                <span v-if="newsLoading" class="ml-auto">
                  <RefreshCw class="w-4 h-4 text-blue-400 animate-spin" />
                </span>
              </div>

              <!-- 에러 -->
              <p v-if="newsError" class="text-xs text-red-500 py-3 text-center">{{ newsError }}</p>

              <!-- 결과 없음 -->
              <p v-else-if="!newsLoading && stockNews.length === 0" class="text-xs text-gray-400 py-3 text-center">뉴스 결과가 없습니다</p>

              <!-- 뉴스 목록 -->
              
              <ul v-else class="divide-y divide-gray-50">
              
                <li v-for="(item, i) in stockNews" :key="i" class="py-3 first:pt-0 last:pb-0">
                  <a :href="item.url" target="_blank" rel="noopener noreferrer"
                    class="group flex items-start gap-3 hover:opacity-80 transition-opacity"
                  >
                    <div class="flex-1 min-w-0">
                      <p class="text-sm font-semibold text-gray-900 group-hover:text-blue-600 transition-colors line-clamp-2">
                        {{ item.title }}
                      </p>
                      <p v-if="item.description" class="text-xs text-gray-400 mt-0.5 line-clamp-1">{{ item.description }}</p>
                      <p class="text-xs text-gray-300 mt-1">{{ item.pub_date }}</p>
                    </div>
                    <ExternalLink class="w-3.5 h-3.5 text-gray-300 group-hover:text-blue-400 flex-shrink-0 mt-0.5 transition-colors" />
                  </a>
                </li>
              </ul>
            </div>

            <!-- ── 관련 영상 ── -->
            <div class="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
              <div class="flex items-center gap-2 mb-4">
                <Play class="w-4 h-4 text-red-500" />
                <h3 class="font-bold text-gray-900 text-sm">관련 영상</h3>
                <span class="text-xs text-gray-400 ml-1">{{ selected.name }}</span>
                <span v-if="stock_youtube_data.length > 0" class="ml-auto text-xs text-gray-400">
                  {{ youtubeIndex + 1 }} / {{ stock_youtube_data.length }}
                </span>
              </div>

              <!-- 로딩 -->
              <div v-if="stock_youtube_data.length === 0 && loading" class="py-10 text-center">
                <RefreshCw class="w-6 h-6 text-gray-300 animate-spin mx-auto" />
              </div>

              <!-- 결과 없음 -->
              <p v-else-if="stock_youtube_data.length === 0" class="text-xs text-gray-400 py-6 text-center">영상 결과가 없습니다</p>

              <!-- 플레이어 -->
              <div v-else>
                <!-- iframe 임베드 -->
                <div class="aspect-video rounded-xl overflow-hidden mb-3 bg-black">
                  <iframe
                    :src="`https://www.youtube.com/embed/${stock_youtube_data[youtubeIndex].video_id}`"
                    class="w-full h-full"
                    frameborder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowfullscreen
                  />
                </div>

                <!-- 제목 -->
                <p class="text-sm font-semibold text-gray-900 mb-4 line-clamp-2">
                  {{ stock_youtube_data[youtubeIndex].title }}
                </p>

                <!-- 이전 / 다음 -->
                <div class="flex items-center justify-between gap-2">
                  <button
                    @click="youtubeIndex--"
                    :disabled="youtubeIndex === 0"
                    class="flex items-center gap-1 px-4 py-2 rounded-xl text-sm font-semibold transition-all border"
                    :class="youtubeIndex === 0
                      ? 'border-gray-100 text-gray-300 cursor-not-allowed'
                      : 'border-gray-200 text-gray-600 hover:bg-gray-50'"
                  >
                    <ChevronLeft class="w-4 h-4" /> 이전
                  </button>

                  <!-- 썸네일 목록 (현재 ±2) -->
                  <div class="flex gap-1.5 overflow-hidden">
                    <button
                      v-for="(v, i) in stock_youtube_data"
                      :key="i"
                      v-show="nearCurrent(i)"
                      @click="youtubeIndex = i"
                      class="w-12 h-9 rounded-lg overflow-hidden flex-shrink-0 border-2 transition-all"
                      :class="i === youtubeIndex ? 'border-blue-500' : 'border-transparent opacity-60 hover:opacity-100'"
                    >
                      <img :src="v.thumbnail_url" class="w-full h-full object-cover" />
                    </button>
                  </div>

                  <button
                    @click="youtubeIndex++"
                    :disabled="youtubeIndex === stock_youtube_data.length - 1"
                    class="flex items-center gap-1 px-4 py-2 rounded-xl text-sm font-semibold transition-all border"
                    :class="youtubeIndex === stock_youtube_data.length - 1
                      ? 'border-gray-100 text-gray-300 cursor-not-allowed'
                      : 'border-gray-200 text-gray-600 hover:bg-gray-50'"
                  >
                    다음 <ChevronRight class="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

          </div><!-- /indicators -->

        </div><!-- /main -->
      </div>
    </main>
    <AppFooter />
  </div>
</template>
