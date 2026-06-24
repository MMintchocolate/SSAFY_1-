<script setup>
// @ts-nocheck
import { ref, computed, onMounted } from 'vue'
import NavBar from '@/components/NavBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import { useAuth } from '@/composables/useAuth'
import { Search, RefreshCw, Zap, Loader, CheckCircle, AlertCircle, X, BrainCircuit } from '@lucide/vue'

const { authFetch, isLoggedIn } = useAuth()
const API       = '/api/stocks/ml'
const STOCK_API = '/api/stocks'

// ── 상태 ──────────────────────────────────────────────────────────────
const watchlist     = ref([])   // [{symbol, name}]  관심종목
const extraStocks   = ref([])   // [{symbol, name}]  검색으로 추가한 종목
const modelMetas    = ref({})   // { TSLA: { trained, accuracy, ... } }
const trainResults  = ref({})   // { TSLA: { per_class, confusion_matrix, feat_imp } }
const predictions   = ref({})   // { TSLA: { signal, signal_label, probabilities } }
const trainingFor      = ref(null)
const predictingFor    = ref(null)
const trainErrors      = ref({})
const predErrors       = ref({})
const mlExplainResults = ref({})
const mlExplainLoading = ref({})
const mlExplainErrors  = ref({})
const activeResult  = ref(null) // 상세 패널 열린 symbol

// ── 검색 ──────────────────────────────────────────────────────────────
const searchQuery   = ref('')
const searchResults = ref([])
const searchLoading = ref(false)
const showDropdown  = ref(false)
let   searchTimer   = null

function onSearchInput() {
  clearTimeout(searchTimer)
  if (!searchQuery.value.trim()) { searchResults.value = []; showDropdown.value = false; return }
  searchTimer = setTimeout(doSearch, 400)
}

async function doSearch() {
  if (!searchQuery.value.trim()) return
  searchLoading.value = true
  showDropdown.value  = true
  try {
    const res  = await fetch(`${STOCK_API}/search/?q=${encodeURIComponent(searchQuery.value)}`)
    const data = await res.json()
    searchResults.value = Array.isArray(data) ? data : []
  } catch {
    searchResults.value = []
  } finally {
    searchLoading.value = false
  }
}

function selectSearchResult(result) {
  const symbol = result.symbol
  const name   = result.name || ''
  // 이미 추적 중이면 무시
  if (trackedStocks.value.some(t => t.symbol === symbol)) {
    clearSearchBox(); return
  }
  extraStocks.value.push({ symbol, name })
  clearSearchBox()
}

function clearSearchBox() {
  searchQuery.value   = ''
  searchResults.value = []
  showDropdown.value  = false
}

function hideDropdown() {
  setTimeout(() => { showDropdown.value = false }, 150)
}

function removeExtra(sym) {
  extraStocks.value = extraStocks.value.filter(s => s.symbol !== sym)
  if (activeResult.value === sym) activeResult.value = null
}

// ── 마운트 ────────────────────────────────────────────────────────────
onMounted(async () => {
  await Promise.all([loadWatchlist(), loadAllModels(), loadSavedPredictions()])
})

async function loadSavedPredictions() {
  if (!isLoggedIn.value) return
  try {
    const res  = await authFetch('/api/stocks/ml/saved/')
    if (!res.ok) return
    const list = await res.json()
    for (const item of list) {
      predictions.value[item.symbol] = {
        signal:        item.signal,
        signal_label:  item.signal_label,
        probabilities: item.probabilities,
        latest_date:   item.latest_date,
        predicted_at:  item.predicted_at,
        _saved: true,
      }
      if (item.explanation) {
        mlExplainResults.value[item.symbol] = { explanation: item.explanation }
      }
    }
  } catch { /* 저장된 예측 없으면 무시 */ }
}

async function loadWatchlist() {
  if (!isLoggedIn.value) return
  try {
    const res  = await authFetch('/api/stocks/watchlist/')
    const data = await res.json()
    watchlist.value = Array.isArray(data) ? data : []
  } catch { watchlist.value = [] }
}

async function loadAllModels() {
  try {
    const res  = await fetch(`${API}/status/`)
    const data = await res.json()
    const metas = {}
    for (const m of (data.models || [])) {
      if (m.symbol) metas[m.symbol] = { trained: true, ...m }
    }
    modelMetas.value = metas
  } catch { modelMetas.value = {} }
}

// ── 통합 목록 (관심 종목 + 추가 종목, 중복 제거) ─────────────────────
const trackedStocks = computed(() => {
  const fromWl  = watchlist.value.map(w => ({ symbol: w.symbol || w, name: w.name || '' }))
  const fromExt = extraStocks.value
  const seen = new Set()
  return [...fromWl, ...fromExt].filter(item => {
    if (seen.has(item.symbol)) return false
    seen.add(item.symbol); return true
  })
})

// ── 학습 ──────────────────────────────────────────────────────────────
async function trainStock(symbol) {
  trainingFor.value = symbol
  delete trainErrors.value[symbol]
  delete trainResults.value[symbol]
  delete predictions.value[symbol]
  activeResult.value = symbol
  try {
    const res  = await fetch(`${API}/train/?symbol=${symbol}`, { method: 'POST' })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || `서버 오류 (${res.status})`)
    trainResults.value[symbol] = data
    modelMetas.value[symbol]   = { trained: true, ...data }
  } catch (e) {
    trainErrors.value[symbol] = e.message || '학습 실패'
  } finally {
    trainingFor.value = null
  }
}

// ── 예측 ──────────────────────────────────────────────────────────────
async function predictStock(symbol) {
  predictingFor.value = symbol
  delete predErrors.value[symbol]
  delete predictions.value[symbol]
  delete mlExplainResults.value[symbol]
  delete mlExplainErrors.value[symbol]
  try {
    const res  = await fetch(`${API}/predict/?symbol=${symbol}`)
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || `서버 오류 (${res.status})`)
    predictions.value[symbol] = data
    fetchMlExplain(symbol)
  } catch (e) {
    predErrors.value[symbol] = e.message || '예측 실패'
  } finally {
    predictingFor.value = null
  }
}

async function fetchMlExplain(symbol) {
  mlExplainLoading.value[symbol] = true
  try {
    const res  = await authFetch(`${API}/explain/?symbol=${symbol}`)
    const data = await res.json()
    if (!res.ok || data.error) throw new Error(data.error || 'AI 보고서 생성 실패')
    mlExplainResults.value[symbol] = data
  } catch (e) {
    mlExplainErrors.value[symbol] = e.message
  } finally {
    mlExplainLoading.value[symbol] = false
  }
}

function parseExplanation(text) {
  if (!text) return []
  return text.split(/\n## /).filter(Boolean).map(s => {
    const nl = s.indexOf('\n')
    return { title: s.slice(0, nl).replace(/^## /, '').trim(), body: s.slice(nl + 1).trim() }
  })
}

// ── 헬퍼 ──────────────────────────────────────────────────────────────
function signalStyle(signal) {
  if (signal === 1) return { bg: 'bg-emerald-50', border: 'border-emerald-300', text: 'text-emerald-700', badge: 'bg-emerald-600' }
  if (signal === 2) return { bg: 'bg-red-50',     border: 'border-red-300',     text: 'text-red-700',     badge: 'bg-red-600' }
  return                   { bg: 'bg-gray-50',    border: 'border-gray-300',    text: 'text-gray-700',    badge: 'bg-gray-500' }
}

function featLabel(key) {
  const m = {
    feat_ma_ratio: 'MA50/MA200', feat_rsi: 'RSI 14',
    feat_macd_hist: 'MACD 히스토그램', feat_bb_pos: '볼린저 위치',
    feat_return_1d: '1일 수익률', feat_return_3d: '3일 수익률',
    feat_return_5d: '5일 수익률', feat_vol_ratio: '거래량 비율',
    feat_usd_idx_chg: '달러 인덱스', feat_us_10y_chg: '미국 10년 금리',
  }
  return m[key] || key
}

function maxImp(symbol) {
  const imp = (trainResults.value[symbol] || modelMetas.value[symbol])?.feat_imp
  if (!imp?.length) return 1
  return Math.max(...imp.map(f => f.importance))
}

function isExtra(sym) {
  return extraStocks.value.some(s => s.symbol === sym)
}
</script>

<template>
  <div class="min-h-screen bg-white" style="font-family:'Pretendard','Noto Sans KR',sans-serif">
    <NavBar />
    <main class="pt-16">

      <!-- 헤더 -->
      <div style="background:linear-gradient(90deg,#fffdf9 0%,#ffffff 50%,#f2fffb 100%);border-bottom:1px solid #EEF1F5">
        <div class="max-w-5xl mx-auto px-4 sm:px-6 py-8">
          <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-bold mb-3" style="background:#DFFAF4;color:#0D9B7A;font-size:0.72rem">
            ML Pipeline
          </div>
          <h1 class="font-black mb-1" style="font-size:1.6rem;color:#0F122B">종목별 매수 타이밍 예측 모델</h1>
          <p class="text-sm" style="color:#6F7485">종목을 검색해 추가하고, 종목별 LightGBM 모델을 학습하여 오늘의 신호를 예측합니다. (Triple Barrier +5% / -2.5%)</p>
        </div>
      </div>

      <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6 space-y-5">

        <!-- 종목 검색 -->
        <div class="rounded-2xl p-4" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
          <div class="relative">
            <div class="flex items-center gap-2 px-4 py-2.5 rounded-xl transition-all" style="border:1.5px solid #EEF1F5;background:white">
              <Search class="w-4 h-4 flex-shrink-0" style="color:#6F7485" />
              <input
                v-model="searchQuery"
                @input="onSearchInput"
                @focus="searchQuery && (showDropdown = true)"
                @blur="hideDropdown"
                placeholder="종목 검색 (한글·영어·코드 모두 가능 — 테슬라, TSLA, 삼성전자, 005930)"
                class="flex-1 text-sm bg-transparent outline-none"
                style="color:#0F122B"
              />
              <button v-if="searchQuery" @click="clearSearchBox" style="color:#6F7485">
                <X class="w-4 h-4" />
              </button>
            </div>

            <div v-if="showDropdown && (searchLoading || searchResults.length > 0)"
              class="absolute top-full left-0 right-0 mt-1 rounded-xl z-50 overflow-hidden"
              style="background:white;border:1px solid #EEF1F5;box-shadow:0 8px 24px rgba(15,18,43,0.1)">
              <div v-if="searchLoading" class="flex items-center gap-2 px-4 py-3 text-sm" style="color:#6F7485">
                <Loader class="w-4 h-4 animate-spin" />검색 중...
              </div>
              <button
                v-for="r in searchResults" :key="r.symbol"
                @mousedown.prevent="selectSearchResult(r)"
                class="w-full flex items-center justify-between px-4 py-3 text-left transition-colors hover:bg-[#F8F9FF]"
                style="border-bottom:1px solid #EEF1F5"
                :class="trackedStocks.some(t => t.symbol === r.symbol) ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'"
              >
                <div>
                  <span class="font-bold text-sm" style="color:#0F122B">{{ r.symbol }}</span>
                  <span v-if="r.name" class="text-sm ml-2" style="color:#6F7485">{{ r.name }}</span>
                </div>
                <div class="flex items-center gap-2">
                  <span v-if="r.market || r.exchange" class="text-xs px-2 py-0.5 rounded-full" style="background:#F8F9FF;color:#6F7485">{{ r.market || r.exchange }}</span>
                  <span v-if="trackedStocks.some(t => t.symbol === r.symbol)" class="text-xs font-semibold" style="color:#0D9B7A">추가됨</span>
                  <span v-else class="text-xs font-semibold" style="color:#57E0C3">+ 추가</span>
                </div>
              </button>
            </div>
          </div>
        </div>

        <!-- 로그인 안내 -->
        <div v-if="!isLoggedIn" class="flex items-center gap-2 text-sm px-4 py-3 rounded-xl" style="background:#FFF8E6;border:1px solid #FFD76A;color:#B8860B">
          <AlertCircle class="w-4 h-4 flex-shrink-0" />
          로그인하면 관심 종목이 자동으로 표시됩니다.
        </div>

        <!-- 빈 상태 -->
        <div v-if="trackedStocks.length === 0" class="text-center py-14" style="color:#6F7485">
          <Search class="w-10 h-10 mx-auto mb-3" style="color:#EEF1F5" />
          <p class="text-sm">위 검색창에서 종목을 검색해 추가하세요.</p>
          <p v-if="isLoggedIn" class="text-xs mt-1" style="color:#6F7485;opacity:0.6">관심 종목으로 등록된 종목은 자동으로 표시됩니다.</p>
        </div>

        <!-- 종목 카드 그리드 -->
        <div v-if="trackedStocks.length > 0" class="grid sm:grid-cols-2 gap-4">
          <div v-for="item in trackedStocks" :key="item.symbol"
            class="rounded-2xl overflow-hidden transition-all"
            :style="activeResult === item.symbol
              ? 'background:white;border:1.5px solid #57E0C3;box-shadow:0 0 0 4px rgba(87,224,195,0.12)'
              : 'background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)'"
          >
            <!-- 카드 상단 -->
            <div class="flex items-start justify-between px-4 pt-4 pb-3">
              <div>
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="font-black" style="color:#0F122B">{{ item.name }}</span>
                  <span v-if="item.name" class="truncate max-w-32" style="font-size:0.72rem;color:#6F7485">{{ item.symbol }}</span>
                </div>
                <div v-if="modelMetas[item.symbol]?.trained" class="flex items-center gap-1.5 mt-1">
                  <CheckCircle class="w-3 h-3" style="color:#57E0C3" />
                  <span class="font-semibold" style="font-size:0.72rem;color:#0D9B7A">정확도 {{ ((modelMetas[item.symbol].accuracy || 0) * 100).toFixed(1) }}%</span>
                  <span style="font-size:0.72rem;color:#EEF1F5">·</span>
                  <span style="font-size:0.72rem;color:#6F7485">{{ modelMetas[item.symbol].trained_at }}</span>
                </div>
                <div v-else style="font-size:0.72rem;color:#6F7485" class="mt-1">미학습</div>
              </div>
              <button v-if="isExtra(item.symbol)" @click="removeExtra(item.symbol)"
                class="p-1 rounded-lg transition-colors flex-shrink-0" style="color:#6F7485">
                <X class="w-4 h-4" />
              </button>
            </div>

            <!-- 학습 에러 -->
            <div v-if="trainErrors[item.symbol]" class="mx-4 mb-2 text-xs px-3 py-2 rounded-lg" style="color:#E5323B;background:#FFF5F5;border:1px solid #FFD0D0">
              {{ trainErrors[item.symbol] }}
            </div>

            <!-- 예측 결과 -->
            <div v-if="predictions[item.symbol]" class="mx-4 mb-3">
              <div class="rounded-xl p-3"
                :style="predictions[item.symbol].signal === 1 ? 'background:#DFFAF4;border:1px solid #57E0C3'
                       : predictions[item.symbol].signal === 2 ? 'background:#FFF5F5;border:1px solid #FFD0D0'
                       : 'background:#F8F9FF;border:1px solid #EEF1F5'"
              >
                <div class="flex items-center justify-between flex-wrap gap-2">
                  <div class="flex items-center gap-2">
                    <span class="text-white text-xs font-black px-2.5 py-0.5 rounded-full"
                      :style="predictions[item.symbol].signal === 1 ? 'background:#57E0C3;color:#0F122B'
                             : predictions[item.symbol].signal === 2 ? 'background:#E5323B'
                             : 'background:#6F7485'"
                    >{{ predictions[item.symbol].signal_label }}</span>
                    <span class="font-bold text-sm"
                      :style="predictions[item.symbol].signal === 1 ? 'color:#0D9B7A'
                             : predictions[item.symbol].signal === 2 ? 'color:#E5323B'
                             : 'color:#6F7485'"
                    >{{ predictions[item.symbol].signal === 1 ? '매수 타이밍' : predictions[item.symbol].signal === 2 ? '매도·보류' : '관망' }}</span>
                  </div>
                  <div class="flex gap-3 text-xs">
                    <div class="text-center">
                      <p style="color:#6F7485">관망</p>
                      <p class="font-bold" style="color:#0F122B">{{ ((predictions[item.symbol].probabilities?.[0] || 0) * 100).toFixed(0) }}%</p>
                    </div>
                    <div class="text-center">
                      <p style="color:#0D9B7A">매수</p>
                      <p class="font-bold" style="color:#0D9B7A">{{ ((predictions[item.symbol].probabilities?.[1] || 0) * 100).toFixed(0) }}%</p>
                    </div>
                    <div class="text-center">
                      <p style="color:#E5323B">매도</p>
                      <p class="font-bold" style="color:#E5323B">{{ ((predictions[item.symbol].probabilities?.[2] || 0) * 100).toFixed(0) }}%</p>
                    </div>
                  </div>
                </div>
                <p class="mt-1.5" style="font-size:0.72rem;color:#6F7485">
                  기준일: {{ predictions[item.symbol].latest_date }}
                  <span v-if="predictions[item.symbol]._saved" class="ml-2" style="color:#A78BFA">· 저장된 결과 {{ predictions[item.symbol].predicted_at }}</span>
                </p>
              </div>
            </div>
            <div v-if="predErrors[item.symbol]" class="mx-4 mb-3 text-xs px-3 py-2 rounded-lg" style="color:#E5323B;background:#FFF5F5;border:1px solid #FFD0D0">
              {{ predErrors[item.symbol] }}
            </div>

            <!-- AI 예측 보고서 -->
            <div v-if="mlExplainLoading[item.symbol]" class="mx-4 mb-3 flex items-center gap-2 text-xs px-4 py-3 rounded-xl" style="background:#DFFAF4;border:1px solid #57E0C3;color:#0D9B7A">
              <Loader class="w-3.5 h-3.5 animate-spin flex-shrink-0" />AI 예측 근거 분석 중...
            </div>
            <div v-if="mlExplainErrors[item.symbol]" class="mx-4 mb-3 text-xs px-3 py-2 rounded-lg" style="color:#E5323B;background:#FFF5F5;border:1px solid #FFD0D0">
              AI 보고서: {{ mlExplainErrors[item.symbol] }}
            </div>
            <div v-if="mlExplainResults[item.symbol]" class="mx-4 mb-3 space-y-2">
              <div class="flex items-center gap-1.5 font-bold mb-2" style="font-size:0.72rem;color:#0D9B7A">
                <BrainCircuit class="w-3.5 h-3.5" />AI 예측 보고서
              </div>
              <div
                v-for="(section, i) in parseExplanation(mlExplainResults[item.symbol].explanation)"
                :key="i"
                class="p-3 rounded-xl text-xs"
                :style="[
                  'background:#DFFAF4;border:1px solid #57E0C3',
                  'background:#F8F9FF;border:1px solid #EEF1F5',
                  'background:#FFF8E6;border:1px solid #FFD76A',
                  'background:#F8F9FF;border:1px solid #EEF1F5',
                ][i] || 'background:#F8F9FF;border:1px solid #EEF1F5'"
              >
                <p class="font-bold mb-1"
                  :style="['color:#0D9B7A','color:#0F122B','color:#B8860B','color:#6F7485'][i] || 'color:#6F7485'"
                >{{ section.title }}</p>
                <p class="leading-relaxed whitespace-pre-line" style="color:#0F122B">{{ section.body }}</p>
              </div>
            </div>

            <!-- 액션 버튼 -->
            <div class="px-4 py-3 flex gap-2" style="border-top:1px solid #EEF1F5">
              <button @click="trainStock(item.symbol)"
                :disabled="trainingFor === item.symbol || predictingFor === item.symbol"
                class="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                :style="trainingFor === item.symbol ? 'background:#DFFAF4;color:#0D9B7A' : 'background:#0F122B;color:white'"
              >
                <Loader v-if="trainingFor === item.symbol" class="w-3.5 h-3.5 animate-spin" />
                <RefreshCw v-else class="w-3.5 h-3.5" />
                {{ trainingFor === item.symbol ? '학습 중...' : modelMetas[item.symbol]?.trained ? '재학습' : '학습 시작' }}
              </button>
              <button v-if="modelMetas[item.symbol]?.trained"
                @click="activeResult = activeResult === item.symbol ? null : item.symbol"
                class="px-3 py-2 rounded-xl text-xs font-bold transition-all"
                :style="activeResult === item.symbol
                  ? 'border:1.5px solid #57E0C3;background:#DFFAF4;color:#0D9B7A'
                  : 'border:1.5px solid #EEF1F5;background:white;color:#6F7485'"
              >결과</button>
              <button v-if="modelMetas[item.symbol]?.trained"
                @click="predictStock(item.symbol)"
                :disabled="predictingFor === item.symbol || trainingFor === item.symbol"
                class="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                :style="predictingFor === item.symbol ? 'background:#DFFAF4;color:#0D9B7A' : 'background:#57E0C3;color:#0F122B'"
              >
                <Loader v-if="predictingFor === item.symbol" class="w-3.5 h-3.5 animate-spin" />
                <Zap v-else class="w-3.5 h-3.5" />
                {{ predictingFor === item.symbol ? '예측 중...' : predictions[item.symbol]?._saved ? '다시 예측' : '오늘 예측' }}
              </button>
            </div>
          </div>
        </div>

        <!-- 상세 결과 패널 -->
        <template v-if="activeResult && (trainResults[activeResult] || modelMetas[activeResult]?.trained)">
          <div class="rounded-2xl p-5 space-y-5" style="background:white;border:1.5px solid #57E0C3;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
            <div class="flex items-center justify-between">
              <h3 class="font-black" style="color:#0F122B">
                <span style="color:#57E0C3">{{ activeResult }}</span> 학습 결과
              </h3>
              <button @click="activeResult = null" class="p-1 rounded-lg" style="color:#6F7485">
                <X class="w-4 h-4" />
              </button>
            </div>

            <!-- 요약 스탯 -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div class="text-center p-3 rounded-xl" style="background:#DFFAF4;border:1px solid #57E0C3">
                <p class="text-xl font-black" style="color:#0D9B7A">{{ ((modelMetas[activeResult]?.accuracy || 0) * 100).toFixed(1) }}%</p>
                <p class="text-xs mt-1" style="color:#6F7485">정확도</p>
              </div>
              <div class="text-center p-3 rounded-xl" style="background:#F8F9FF;border:1px solid #EEF1F5">
                <p class="text-xl font-black" style="color:#0F122B">{{ (modelMetas[activeResult]?.total_rows || 0).toLocaleString() }}</p>
                <p class="text-xs mt-1" style="color:#6F7485">총 행수</p>
              </div>
              <div class="text-center p-3 rounded-xl" style="background:#F8F9FF;border:1px solid #EEF1F5">
                <p class="text-xl font-black" style="color:#0F122B">{{ (modelMetas[activeResult]?.train_rows || 0).toLocaleString() }}</p>
                <p class="text-xs mt-1" style="color:#6F7485">학습 (80%)</p>
              </div>
              <div class="text-center p-3 rounded-xl" style="background:#FFF8E6;border:1px solid #FFD76A">
                <p class="text-xl font-black" style="color:#B8860B">{{ (modelMetas[activeResult]?.test_rows || 0).toLocaleString() }}</p>
                <p class="text-xs mt-1" style="color:#6F7485">검증 (20%)</p>
              </div>
            </div>

            <!-- 클래스별 성능 + 혼동 행렬 -->
            <template v-if="trainResults[activeResult]">
              <div class="grid sm:grid-cols-2 gap-4">
                <div class="rounded-xl p-4" style="background:#F8F9FF;border:1px solid #EEF1F5">
                  <h4 class="font-bold text-sm mb-3" style="color:#0F122B">클래스별 성능</h4>
                  <table class="w-full text-xs">
                    <thead>
                      <tr style="border-bottom:1px solid #EEF1F5">
                        <th class="text-left pb-2 font-semibold" style="color:#6F7485">클래스</th>
                        <th class="text-right pb-2 font-semibold" style="color:#6F7485">P</th>
                        <th class="text-right pb-2 font-semibold" style="color:#6F7485">R</th>
                        <th class="text-right pb-2 font-semibold" style="color:#6F7485">F1</th>
                        <th class="text-right pb-2 font-semibold" style="color:#6F7485">N</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(v, label) in trainResults[activeResult].per_class" :key="label" style="border-bottom:1px solid #EEF1F5">
                        <td class="py-1.5 font-bold" style="color:#0F122B">{{ label }}</td>
                        <td class="py-1.5 text-right" style="color:#6F7485">{{ v.precision }}</td>
                        <td class="py-1.5 text-right" style="color:#6F7485">{{ v.recall }}</td>
                        <td class="py-1.5 text-right font-bold"
                          :style="v.f1 >= 0.6 ? 'color:#0D9B7A' : v.f1 >= 0.4 ? 'color:#B8860B' : 'color:#E5323B'"
                        >{{ v.f1 }}</td>
                        <td class="py-1.5 text-right" style="color:#6F7485">{{ v.support }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <div class="rounded-xl p-4" style="background:#F8F9FF;border:1px solid #EEF1F5">
                  <h4 class="font-bold text-sm mb-3" style="color:#0F122B">혼동 행렬</h4>
                  <div class="flex gap-1 justify-center mb-1 ml-5">
                    <div v-for="l in ['관망','매수','매도']" :key="l" class="w-12 text-center text-xs" style="color:#6F7485">{{ l }}</div>
                  </div>
                  <div v-for="(row, ri) in (trainResults[activeResult].confusion_matrix || [])" :key="ri" class="flex gap-1 justify-center mb-1 items-center">
                    <div class="w-5 text-xs text-right pr-1" style="color:#6F7485">{{ ['관','매','도'][ri] }}</div>
                    <div v-for="(cell, ci) in row" :key="ci"
                      class="w-12 h-8 rounded-lg flex items-center justify-center text-sm font-bold"
                      :style="ri === ci ? 'background:#DFFAF4;color:#0D9B7A;border:1px solid #57E0C3' : 'background:white;color:#6F7485;border:1px solid #EEF1F5'"
                    >{{ cell }}</div>
                  </div>
                  <p class="text-xs text-center mt-2" style="color:#6F7485">대각선 = 정답</p>
                </div>
              </div>
            </template>

            <!-- 피처 중요도 -->
            <div v-if="(trainResults[activeResult] || modelMetas[activeResult])?.feat_imp?.length">
              <h4 class="font-bold text-sm mb-3" style="color:#0F122B">피처 중요도</h4>
              <div class="space-y-2">
                <div v-for="f in (trainResults[activeResult] || modelMetas[activeResult]).feat_imp" :key="f.feature" class="flex items-center gap-3">
                  <span class="w-28 text-xs text-right flex-shrink-0" style="color:#6F7485">{{ featLabel(f.feature) }}</span>
                  <div class="flex-1 rounded-full h-2" style="background:#EEF1F5">
                    <div class="h-2 rounded-full transition-all" style="background:#57E0C3" :style="{ width: (f.importance / maxImp(activeResult) * 100) + '%' }"></div>
                  </div>
                  <span class="w-8 text-xs text-right flex-shrink-0" style="color:#6F7485">{{ f.importance }}</span>
                </div>
              </div>
            </div>
          </div>
        </template>

      </div>
    </main>
    <AppFooter />
  </div>
</template>
