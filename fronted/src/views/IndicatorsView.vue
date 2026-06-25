<script setup>
// @ts-nocheck
import { ref, onMounted } from 'vue'
import NavBar from '@/components/NavBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import { Star, TrendingUp, TrendingDown, Activity, BarChart2, AlertCircle, RefreshCw, HelpCircle, ChevronDown, ChevronLeft, ChevronRight, Newspaper, ExternalLink, Play, BrainCircuit, Loader2 } from '@lucide/vue'
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

// AI 기술적 분석
const aiText    = ref('')
const aiLoading = ref(false)
const aiError   = ref('')

async function generateAiAnalysis() {
  if (!selected.value) return
  aiLoading.value = true
  aiError.value   = ''
  aiText.value    = ''
  try {
    const res  = await authFetch(`${API}/${selected.value.symbol}/ai-analysis/`)
    const data = await res.json()
    if (!res.ok || data.error) throw new Error(data.error || 'AI 분석 실패')
    aiText.value = data.analysis
  } catch (e) {
    aiError.value = e.message
  } finally {
    aiLoading.value = false
  }
}

// 종목 변경 시 분석 초기화
function resetAi() {
  aiText.value = ''
  aiError.value = ''
}

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
  resetAi()
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
  <div class="min-h-screen bg-white" style="font-family:'Pretendard','Noto Sans KR',sans-serif">
    <NavBar />

    <main class="pt-16">
      <!-- 헤더 -->
      <div style="background:linear-gradient(90deg,#fffdf9 0%,#ffffff 50%,#f2fffb 100%);border-bottom:1px solid #EEF1F5">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 py-10">
          <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-bold mb-3" style="background:#DFFAF4;color:#0D9B7A;font-size:0.72rem">
            <Activity class="w-3 h-3" />기술적 분석
          </div>
          <h1 class="font-black mb-1" style="font-size:1.8rem;color:#0F122B">매수 타이밍 지표</h1>
          <p style="color:#6F7485;font-size:0.9rem">관심 종목의 MA · RSI · MACD · 볼린저 밴드를 한눈에</p>
        </div>
      </div>

      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-8 flex gap-6">

        <!-- 왼쪽: 관심종목 목록 -->
        <aside class="w-56 flex-shrink-0">
          <div class="rounded-2xl p-4 sticky top-20" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
            <div class="flex items-center gap-2 mb-3">
              <Star class="w-4 h-4 fill-amber-400 text-amber-400" />
              <span class="text-sm font-bold" style="color:#0F122B">관심 종목</span>
              <span class="ml-auto font-medium" style="font-size:0.72rem;color:#6F7485">{{ watchlist.length }}개</span>
            </div>

            <div v-if="watchlist.length === 0" class="text-center py-6">
              <Star class="w-7 h-7 mx-auto mb-2" style="color:#EEF1F5;fill:#EEF1F5" />
              <p style="font-size:0.72rem;color:#6F7485">관심 종목이 없습니다<br>주식 페이지에서 추가하세요</p>
            </div>

            <div v-else class="space-y-1">
              <button
                v-for="item in watchlist" :key="item.symbol"
                @click="selectStock(item)"
                class="w-full flex items-center gap-2.5 p-2.5 rounded-xl text-left transition-all"
                :style="selected?.symbol === item.symbol
                  ? 'background:#DFFAF4;border:1px solid #57E0C3'
                  : 'border:1px solid transparent'"
              >
                <div class="w-9 h-9 rounded-lg flex items-center justify-center font-black flex-shrink-0" style="background:#0F122B;color:white;font-size:0.65rem">
                  {{ item.symbol.slice(0, 3) }}
                </div>
                <div class="min-w-0">
                  <p class="font-bold truncate" style="font-size:0.72rem;color:#0F122B">{{ item.name }}</p>
                  <p class="truncate" style="font-size:0.72rem;color:#6F7485">{{ item.symbol }}</p>
                </div>
              </button>
            </div>
          </div>
        </aside>

        <!-- 오른쪽: 지표 패널 -->
        <div class="flex-1 min-w-0">

          <!-- 미선택 -->
          <div v-if="!selected" class="rounded-2xl p-16 text-center" style="background:white;border:1px solid #EEF1F5">
            <div class="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4" style="background:#DFFAF4">
              <Activity class="w-8 h-8" style="color:#57E0C3" />
            </div>
            <p class="font-bold mb-1" style="color:#0F122B">왼쪽 관심 종목을 선택하세요</p>
            <p class="text-sm" style="color:#6F7485">4가지 기술 지표가 표시됩니다</p>
          </div>

          <!-- 로딩 -->
          <div v-else-if="loading" class="rounded-2xl p-16 text-center" style="background:white;border:1px solid #EEF1F5">
            <RefreshCw class="w-8 h-8 animate-spin mx-auto mb-3" style="color:#57E0C3" />
            <p class="text-sm" style="color:#6F7485">지표 계산 중...</p>
          </div>

          <!-- 에러 -->
          <div v-else-if="error" class="rounded-2xl p-10 text-center" style="background:white;border:1px solid #FFD0D0">
            <AlertCircle class="w-8 h-8 mx-auto mb-3" style="color:#E5323B" />
            <p class="font-semibold" style="color:#E5323B">{{ error }}</p>
          </div>

          <!-- 지표 결과 -->
          <div v-else-if="indicators" class="space-y-4">

            <!-- 종목 헤더 -->
            <div class="rounded-2xl p-5 flex items-center gap-4" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
              <div class="w-12 h-12 rounded-xl flex items-center justify-center font-black" style="background:#0F122B;color:white;font-size:0.85rem">
                {{ selected.symbol.slice(0, 4) }}
              </div>
              <div>
                <p style="font-size:0.72rem;color:#6F7485">{{ selected.name }}</p>
                <p class="font-extrabold" style="font-size:1.1rem;color:#0F122B">{{ selected.symbol }}</p>
              </div>
              <div class="ml-auto text-right">
                <p class="mb-0.5" style="font-size:0.72rem;color:#6F7485">현재가</p>
                <p class="font-black tabular-nums" style="font-size:1.5rem;color:#0F122B">{{ indicators.price?.toLocaleString() }}</p>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">

              <!-- MA -->
              <div class="rounded-2xl p-5" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
                <div class="flex items-center gap-2 mb-1">
                  <TrendingUp class="w-4 h-4" style="color:#57E0C3" />
                  <h3 class="font-bold text-sm" style="color:#0F122B">이동평균선 (MA)</h3>
                  <span v-if="indicators.ma.cross" class="text-xs font-bold px-2 py-0.5 rounded-full border" :class="signalClass(indicators.ma.cross)">{{ signalLabel(indicators.ma.cross) }}</span>
                  <button @click="infoOpen.ma = !infoOpen.ma" class="ml-auto flex items-center gap-0.5 transition-colors" style="font-size:0.72rem;color:#6F7485">
                    <HelpCircle class="w-4 h-4" />
                    <ChevronDown class="w-3 h-3 transition-transform" :class="{ 'rotate-180': infoOpen.ma }" />
                  </button>
                </div>
                <div v-if="infoOpen.ma" class="mb-4 p-3 rounded-xl space-y-2" style="background:#F8F9FF;border:1px solid #EEF1F5;font-size:0.72rem">
                  <p class="font-bold" style="color:#0F122B">{{ INFO.ma.title }}</p>
                  <p class="leading-relaxed" style="color:#6F7485">{{ INFO.ma.desc }}</p>
                  <ul class="space-y-1 mt-2">
                    <li v-for="i in INFO.ma.items" :key="i.label" class="flex gap-2">
                      <span class="font-bold whitespace-nowrap" style="color:#0F122B">{{ i.label }}</span>
                      <span style="color:#6F7485">→ {{ i.meaning }}</span>
                    </li>
                  </ul>
                </div>
                <div class="mt-3 space-y-3">
                  <div class="flex justify-between items-center py-2" style="border-bottom:1px solid #EEF1F5">
                    <span class="font-medium" style="font-size:0.72rem;color:#6F7485">현재가</span>
                    <span class="text-sm font-bold tabular-nums" style="color:#0F122B">{{ indicators.price?.toLocaleString() }}</span>
                  </div>
                  <div class="flex justify-between items-center py-2" style="border-bottom:1px solid #EEF1F5">
                    <span class="font-medium" style="font-size:0.72rem;color:#6F7485">MA 50일</span>
                    <div class="flex items-center gap-2">
                      <span class="text-sm font-bold tabular-nums" :style="indicators.price > indicators.ma.ma50 ? 'color:#E5323B' : 'color:#3B7FED'">{{ fmt(indicators.ma.ma50) }}</span>
                      <TrendingUp v-if="indicators.price > indicators.ma.ma50" class="w-3 h-3" style="color:#E5323B" />
                      <TrendingDown v-else class="w-3 h-3" style="color:#3B7FED" />
                    </div>
                  </div>
                  <div class="flex justify-between items-center py-2">
                    <span class="font-medium" style="font-size:0.72rem;color:#6F7485">MA 200일</span>
                    <div class="flex items-center gap-2">
                      <span v-if="indicators.ma.ma200" class="text-sm font-bold tabular-nums" :style="indicators.price > indicators.ma.ma200 ? 'color:#E5323B' : 'color:#3B7FED'">{{ fmt(indicators.ma.ma200) }}</span>
                      <span v-else class="text-sm" style="color:#6F7485">데이터 부족</span>
                      <TrendingUp v-if="indicators.ma.ma200 && indicators.price > indicators.ma.ma200" class="w-3 h-3" style="color:#E5323B" />
                      <TrendingDown v-else-if="indicators.ma.ma200" class="w-3 h-3" style="color:#3B7FED" />
                    </div>
                  </div>
                </div>
                <div class="mt-4 p-3 rounded-xl text-xs font-medium"
                  :style="indicators.ma.above200 ? 'background:#DFFAF4;color:#0D9B7A' : 'background:#FFF5F5;color:#E5323B'"
                >{{ indicators.ma.above200 ? '📈 MA50이 MA200 위 — 장기 상승 추세' : '📉 MA50이 MA200 아래 — 장기 하락 추세' }}</div>
              </div>

              <!-- RSI -->
              <div class="rounded-2xl p-5" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
                <div class="flex items-center gap-2 mb-1">
                  <Activity class="w-4 h-4" style="color:#57E0C3" />
                  <h3 class="font-bold text-sm" style="color:#0F122B">RSI (14일)</h3>
                  <span class="text-xs font-bold px-2 py-0.5 rounded-full border" :class="signalClass(indicators.rsi.signal)">{{ signalLabel(indicators.rsi.signal) }}</span>
                  <button @click="infoOpen.rsi = !infoOpen.rsi" class="ml-auto flex items-center gap-0.5 transition-colors" style="font-size:0.72rem;color:#6F7485">
                    <HelpCircle class="w-4 h-4" />
                    <ChevronDown class="w-3 h-3 transition-transform" :class="{ 'rotate-180': infoOpen.rsi }" />
                  </button>
                </div>
                <div v-if="infoOpen.rsi" class="mb-4 p-3 rounded-xl space-y-2" style="background:#F8F9FF;border:1px solid #EEF1F5;font-size:0.72rem">
                  <p class="font-bold" style="color:#0F122B">{{ INFO.rsi.title }}</p>
                  <p class="leading-relaxed" style="color:#6F7485">{{ INFO.rsi.desc }}</p>
                  <ul class="space-y-1 mt-2">
                    <li v-for="i in INFO.rsi.items" :key="i.label" class="flex gap-2">
                      <span class="font-bold whitespace-nowrap" style="color:#0F122B">{{ i.label }}</span>
                      <span style="color:#6F7485">→ {{ i.meaning }}</span>
                    </li>
                  </ul>
                </div>
                <div class="mt-3 mb-4">
                  <div class="flex justify-between mb-1" style="font-size:0.72rem;color:#6F7485">
                    <span>0</span><span>30</span><span>70</span><span>100</span>
                  </div>
                  <div class="relative h-4 rounded-full overflow-hidden flex">
                    <div class="w-[30%]" style="background:#DFFAF4"></div>
                    <div class="w-[40%]" style="background:#EEF1F5"></div>
                    <div class="w-[30%]" style="background:#FFF5F5"></div>
                    <div class="absolute top-0 bottom-0 w-1 rounded-full shadow" style="background:#0F122B" :style="{ left: `calc(${indicators.rsi.value}% - 2px)` }"></div>
                  </div>
                  <div class="flex justify-between mt-1" style="font-size:0.72rem">
                    <span class="font-semibold" style="color:#0D9B7A">과매도</span>
                    <span style="color:#6F7485">중립</span>
                    <span class="font-semibold" style="color:#E5323B">과매수</span>
                  </div>
                </div>
                <div class="text-center">
                  <span class="font-black tabular-nums" style="font-size:2.4rem"
                    :style="indicators.rsi.signal === 'oversold' ? 'color:#0D9B7A' : indicators.rsi.signal === 'overbought' ? 'color:#E5323B' : 'color:#0F122B'"
                  >{{ fmt(indicators.rsi.value) }}</span>
                </div>
                <div class="mt-4 p-3 rounded-xl text-xs" style="background:#F8F9FF;color:#6F7485">
                  RSI {{ fmt(indicators.rsi.value) }} —
                  <span v-if="indicators.rsi.signal === 'oversold'" class="font-semibold" style="color:#0D9B7A">30 미만: 과매도 구간, 반등 가능성</span>
                  <span v-else-if="indicators.rsi.signal === 'overbought'" class="font-semibold" style="color:#E5323B">70 초과: 과매수 구간, 조정 가능성</span>
                  <span v-else>중립 구간 (30~70)</span>
                </div>
              </div>

              <!-- MACD -->
              <div class="rounded-2xl p-5" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
                <div class="flex items-center gap-2 mb-1">
                  <BarChart2 class="w-4 h-4" style="color: rgb(255, 215, 106);" />
                  <h3 class="font-bold text-sm" style="color:#0F122B">MACD (12, 26, 9)</h3>
                  <span v-if="indicators.macd.cross" class="text-xs font-bold px-2 py-0.5 rounded-full border" :class="signalClass(indicators.macd.cross)">{{ indicators.macd.cross === 'buy' ? '매수 크로스' : '매도 크로스' }}</span>
                  <button @click="infoOpen.macd = !infoOpen.macd" class="ml-auto flex items-center gap-0.5 transition-colors" style="font-size:0.72rem;color:#6F7485">
                    <HelpCircle class="w-4 h-4" />
                    <ChevronDown class="w-3 h-3 transition-transform" :class="{ 'rotate-180': infoOpen.macd }" />
                  </button>
                </div>
                <div v-if="infoOpen.macd" class="mb-4 p-3 rounded-xl space-y-2" style="background:#F8F9FF;border:1px solid #EEF1F5;font-size:0.72rem">
                  <p class="font-bold" style="color:#0F122B">{{ INFO.macd.title }}</p>
                  <p class="leading-relaxed" style="color:#6F7485">{{ INFO.macd.desc }}</p>
                  <ul class="space-y-1 mt-2">
                    <li v-for="i in INFO.macd.items" :key="i.label" class="flex gap-2">
                      <span class="font-bold whitespace-nowrap" style="color:#0F122B">{{ i.label }}</span>
                      <span style="color:#6F7485">→ {{ i.meaning }}</span>
                    </li>
                  </ul>
                </div>
                <div class="mt-3 space-y-3">
                  <div class="flex justify-between items-center py-2" style="border-bottom:1px solid #EEF1F5">
                    <span style="font-size:0.72rem;color:#6F7485">MACD선</span>
                    <span class="text-sm font-bold tabular-nums" :style="indicators.macd.macd >= 0 ? 'color:#E5323B' : 'color:#3B7FED'">{{ fmt(indicators.macd.macd, 4) }}</span>
                  </div>
                  <div class="flex justify-between items-center py-2" style="border-bottom:1px solid #EEF1F5">
                    <span style="font-size:0.72rem;color:#6F7485">시그널선</span>
                    <span class="text-sm font-bold tabular-nums" style="color:#0F122B">{{ fmt(indicators.macd.signal, 4) }}</span>
                  </div>
                  <div class="flex justify-between items-center py-2">
                    <span style="font-size:0.72rem;color:#6F7485">히스토그램</span>
                    <span class="text-sm font-bold tabular-nums" :style="indicators.macd.histogram >= 0 ? 'color:#E5323B' : 'color:#3B7FED'">{{ fmt(indicators.macd.histogram, 4) }}</span>
                  </div>
                </div>
                <div class="mt-4 p-3 rounded-xl text-xs font-medium"
                  :style="indicators.macd.macd > indicators.macd.signal ? 'background:#DFFAF4;color:#0D9B7A' : 'background:#FFF5F5;color:#E5323B'"
                >{{ indicators.macd.macd > indicators.macd.signal ? '📈 MACD > 시그널 — 상승 모멘텀' : '📉 MACD < 시그널 — 하락 모멘텀' }}</div>
              </div>

              <!-- 볼린저 밴드 -->
              <div class="rounded-2xl p-5" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
                <div class="flex items-center gap-2 mb-1">
                  <Activity class="w-4 h-4" style="color:#FFD76A" />
                  <h3 class="font-bold text-sm" style="color:#0F122B">볼린저 밴드 (20일)</h3>
                  <span class="text-xs font-bold px-2 py-0.5 rounded-full border" :class="signalClass(indicators.bollinger.signal)">{{ signalLabel(indicators.bollinger.signal) }}</span>
                  <button @click="infoOpen.bollinger = !infoOpen.bollinger" class="ml-auto flex items-center gap-0.5 transition-colors" style="font-size:0.72rem;color:#6F7485">
                    <HelpCircle class="w-4 h-4" />
                    <ChevronDown class="w-3 h-3 transition-transform" :class="{ 'rotate-180': infoOpen.bollinger }" />
                  </button>
                </div>
                <div v-if="infoOpen.bollinger" class="mb-4 p-3 rounded-xl space-y-2" style="background:#F8F9FF;border:1px solid #EEF1F5;font-size:0.72rem">
                  <p class="font-bold" style="color:#0F122B">{{ INFO.bollinger.title }}</p>
                  <p class="leading-relaxed" style="color:#6F7485">{{ INFO.bollinger.desc }}</p>
                  <ul class="space-y-1 mt-2">
                    <li v-for="i in INFO.bollinger.items" :key="i.label" class="flex gap-2">
                      <span class="font-bold whitespace-nowrap" style="color:#0F122B">{{ i.label }}</span>
                      <span style="color:#6F7485">→ {{ i.meaning }}</span>
                    </li>
                  </ul>
                </div>
                <div class="mt-3 space-y-2 mb-4">
                  <div class="flex justify-between text-xs">
                    <span class="font-semibold" style="color:#E5323B">상단 밴드</span>
                    <span class="font-bold tabular-nums" style="color:#0F122B">{{ fmt(indicators.bollinger.upper) }}</span>
                  </div>
                  <div class="flex justify-between text-xs">
                    <span style="color:#6F7485">중심선 (MA20)</span>
                    <span class="font-bold tabular-nums" style="color:#0F122B">{{ fmt(indicators.bollinger.middle) }}</span>
                  </div>
                  <div class="flex justify-between text-xs">
                    <span class="font-semibold" style="color:#3B7FED">하단 밴드</span>
                    <span class="font-bold tabular-nums" style="color:#0F122B">{{ fmt(indicators.bollinger.lower) }}</span>
                  </div>
                </div>
                <div class="mb-3">
                  <div class="flex justify-between mb-1" style="font-size:0.72rem">
                    <span style="color:#3B7FED">하단(매수)</span>
                    <span style="color:#6F7485">중심</span>
                    <span style="color:#E5323B">상단(매도)</span>
                  </div>
                  <div class="relative h-3 rounded-full" style="background:linear-gradient(to right,#EBF1FF,#EEF1F5,#FFF5F5)">
                    <div class="absolute top-0 bottom-0 w-2 h-2 m-auto rounded-full border-2 border-white" style="background:#0F122B;box-shadow:0 1px 4px rgba(15,18,43,0.2)"
                      :style="{ left: `calc(${Math.min(Math.max(indicators.bollinger.position, 2), 98)}% - 4px)` }"
                    ></div>
                  </div>
                  <p class="text-center mt-1" style="font-size:0.72rem;color:#6F7485">밴드 내 위치 {{ indicators.bollinger.position }}%</p>
                </div>
                <div class="p-3 rounded-xl text-xs" style="background:#F8F9FF;color:#6F7485">
                  <span v-if="indicators.bollinger.signal === 'buy'" class="font-semibold" style="color:#0D9B7A">하단 밴드 도달 — 과매도, 반등 가능성</span>
                  <span v-else-if="indicators.bollinger.signal === 'sell'" class="font-semibold" style="color:#E5323B">상단 밴드 도달 — 과매수, 조정 가능성</span>
                  <span v-else>현재가 밴드 내 위치: {{ indicators.bollinger.position }}% (0%=하단, 100%=상단)</span>
                </div>
              </div>

            </div>

            <!-- AI 지표 분석 -->
            <div class="rounded-2xl p-5" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
              <div class="flex items-center gap-2 mb-4">
                <BrainCircuit class="w-4 h-4" style="color:#57E0C3" />
                <h3 class="font-bold text-sm" style="color:#0F122B">지표 수치 해설</h3>
                <span class="ml-1" style="font-size:0.72rem;color:#6F7485">{{ selected.name }}</span>
                <button @click="generateAiAnalysis" :disabled="aiLoading"
                  class="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all disabled:opacity-50"
                  style="background:#0F122B;color:white"
                >
                  <Loader2 v-if="aiLoading" class="w-3.5 h-3.5 animate-spin" />
                  <BrainCircuit v-else class="w-3.5 h-3.5" />
                  {{ aiLoading ? '해설 중...' : (aiText ? '재해설' : '지표 해설 시작') }}
                </button>
              </div>
              <div v-if="!aiText && !aiLoading && !aiError" class="py-8 text-center text-sm" style="color:#6F7485">
                <BrainCircuit class="w-8 h-8 mx-auto mb-2 opacity-20" />
                <p>버튼을 누르면 현재 수치를 바탕으로 각 지표의 의미를 해설합니다.</p>
                <p class="mt-1" style="font-size:0.72rem;color:#6F7485">매수·매도 판단은 <RouterLink to="/dataset" style="color:#57E0C3" class="hover:underline">ML 예측 페이지</RouterLink>의 AI 보고서를 참고하세요.</p>
              </div>
              <p v-if="aiError" class="text-xs py-3 text-center" style="color:#E5323B">{{ aiError }}</p>
              <div v-if="aiLoading" class="space-y-3 animate-pulse">
                <div v-for="i in 4" :key="i" class="h-4 rounded" style="background:#EEF1F5" :style="{ width: (85 - i * 8) + '%' }" />
              </div>
              <div v-if="aiText && !aiLoading" class="space-y-4">
                <div
                  v-for="(section, i) in aiText.split(/\n## /).filter(Boolean).map(s => {
                    const nl = s.indexOf('\n')
                    return { title: s.slice(0, nl).replace(/^## /, '').trim(), body: s.slice(nl + 1).trim() }
                  })"
                  :key="i"
                  class="p-4 rounded-xl"
                  :style="[
                    'background:#DFFAF4;border:1px solid #57E0C3',
                    'background:#F8F9FF;border:1px solid #EEF1F5',
                    'background:#FFF8E6;border:1px solid #FFD76A',
                    'background:#F8F9FF;border:1px solid #EEF1F5',
                  ][i] || 'background:#F8F9FF;border:1px solid #EEF1F5'"
                >
                  <p class="text-xs font-bold mb-1.5"
                    :style="['color:#0D9B7A','color:#0F122B','color:#B8860B','color:#6F7485'][i] || 'color:#6F7485'"
                  >{{ section.title }}</p>
                  <p class="text-xs leading-relaxed whitespace-pre-line" style="color:#0F122B">{{ section.body }}</p>
                </div>
              </div>
            </div>

            <!-- 관련 뉴스 -->
            <div class="rounded-2xl p-5" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
              <div class="flex items-center gap-2 mb-4">
                <Newspaper class="w-4 h-4" style="color:#57E0C3" />
                <h3 class="font-bold text-sm" style="color:#0F122B">관련 뉴스</h3>
                <span class="ml-1" style="font-size:0.72rem;color:#6F7485">{{ selected.name }}</span>
                <span v-if="newsLoading" class="ml-auto">
                  <RefreshCw class="w-4 h-4 animate-spin" style="color:#57E0C3" />
                </span>
              </div>
              <p v-if="newsError" class="text-xs py-3 text-center" style="color:#E5323B">{{ newsError }}</p>
              <p v-else-if="!newsLoading && stockNews.length === 0" class="text-xs py-3 text-center" style="color:#6F7485">뉴스 결과가 없습니다</p>
              <ul v-else class="space-y-0" style="border-top:1px solid #EEF1F5">
                <li v-for="(item, i) in stockNews" :key="i" style="border-bottom:1px solid #EEF1F5" class="py-3">
                  <a :href="item.url" target="_blank" rel="noopener noreferrer" class="group flex items-start gap-3 hover:opacity-80 transition-opacity">
                    <div class="flex-1 min-w-0">
                      <p class="text-sm font-semibold line-clamp-2 transition-colors group-hover:underline" style="color:#0F122B">{{ item.title }}</p>
                      <p v-if="item.description" class="mt-0.5 line-clamp-1" style="font-size:0.72rem;color:#6F7485">{{ item.description }}</p>
                      <p class="mt-1" style="font-size:0.72rem;color:#6F7485">{{ item.pub_date }}</p>
                    </div>
                    <ExternalLink class="w-3.5 h-3.5 flex-shrink-0 mt-0.5 transition-colors group-hover:text-[#57E0C3]" style="color:#6F7485" />
                  </a>
                </li>
              </ul>
            </div>

            <!-- 관련 영상 -->
            <div class="rounded-2xl p-5" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
              <div class="flex items-center gap-2 mb-4">
                <Play class="w-4 h-4" style="color:#E5323B" />
                <h3 class="font-bold text-sm" style="color:#0F122B">관련 영상</h3>
                <span class="ml-1" style="font-size:0.72rem;color:#6F7485">{{ selected.name }}</span>
                <span v-if="stock_youtube_data.length > 0" class="ml-auto" style="font-size:0.72rem;color:#6F7485">{{ youtubeIndex + 1 }} / {{ stock_youtube_data.length }}</span>
              </div>
              <div v-if="stock_youtube_data.length === 0 && loading" class="py-10 text-center">
                <RefreshCw class="w-6 h-6 animate-spin mx-auto" style="color:#EEF1F5" />
              </div>
              <p v-else-if="stock_youtube_data.length === 0" class="text-xs py-6 text-center" style="color:#6F7485">영상 결과가 없습니다</p>
              <div v-else>
                <div class="aspect-video rounded-xl overflow-hidden mb-3 bg-black">
                  <iframe
                    :src="`https://www.youtube.com/embed/${stock_youtube_data[youtubeIndex].video_id}`"
                    class="w-full h-full" frameborder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowfullscreen
                  />
                </div>
                <p class="text-sm font-semibold mb-4 line-clamp-2" style="color:#0F122B">{{ stock_youtube_data[youtubeIndex].title }}</p>
                <div class="flex items-center justify-between gap-2">
                  <button @click="youtubeIndex--" :disabled="youtubeIndex === 0"
                    class="flex items-center gap-1 px-4 py-2 rounded-xl text-sm font-semibold transition-all"
                    :style="youtubeIndex === 0 ? 'border:1.5px solid #EEF1F5;color:#6F7485;cursor:not-allowed;opacity:0.5' : 'border:1.5px solid #EEF1F5;color:#0F122B'"
                  ><ChevronLeft class="w-4 h-4" /> 이전</button>
                  <div class="flex gap-1.5 overflow-hidden">
                    <button
                      v-for="(v, i) in stock_youtube_data" :key="i"
                      v-show="nearCurrent(i)"
                      @click="youtubeIndex = i"
                      class="w-12 h-9 rounded-lg overflow-hidden flex-shrink-0 border-2 transition-all"
                      :style="i === youtubeIndex ? 'border-color:#57E0C3' : 'border-color:transparent;opacity:0.6'"
                    ><img :src="v.thumbnail_url" class="w-full h-full object-cover" /></button>
                  </div>
                  <button @click="youtubeIndex++" :disabled="youtubeIndex === stock_youtube_data.length - 1"
                    class="flex items-center gap-1 px-4 py-2 rounded-xl text-sm font-semibold transition-all"
                    :style="youtubeIndex === stock_youtube_data.length - 1 ? 'border:1.5px solid #EEF1F5;color:#6F7485;cursor:not-allowed;opacity:0.5' : 'border:1.5px solid #EEF1F5;color:#0F122B'"
                  >다음 <ChevronRight class="w-4 h-4" /></button>
                </div>
              </div>
            </div>

          </div>

        </div>
      </div>
    </main>
    <AppFooter />
  </div>
</template>
