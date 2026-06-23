<script setup>
// @ts-nocheck
import { ref, computed, onMounted } from 'vue'
import NavBar from '@/components/NavBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import { useAuth } from '@/composables/useAuth'
import { Search, RefreshCw, Zap, Loader, CheckCircle, AlertCircle, X } from '@lucide/vue'

const { authFetch, isLoggedIn } = useAuth()
const API       = '/api/stocks/ml'
const STOCK_API = '/api/stocks'

// ── 상태 ──────────────────────────────────────────────────────────────
const watchlist     = ref([])   // [{symbol, name}]  관심종목
const extraStocks   = ref([])   // [{symbol, name}]  검색으로 추가한 종목
const modelMetas    = ref({})   // { TSLA: { trained, accuracy, ... } }
const trainResults  = ref({})   // { TSLA: { per_class, confusion_matrix, feat_imp } }
const predictions   = ref({})   // { TSLA: { signal, signal_label, probabilities } }
const trainingFor   = ref(null)
const predictingFor = ref(null)
const trainErrors   = ref({})
const predErrors    = ref({})
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
  await Promise.all([loadWatchlist(), loadAllModels()])
})

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
  try {
    const res  = await fetch(`${API}/predict/?symbol=${symbol}`)
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || `서버 오류 (${res.status})`)
    predictions.value[symbol] = data
  } catch (e) {
    predErrors.value[symbol] = e.message || '예측 실패'
  } finally {
    predictingFor.value = null
  }
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
  <div class="min-h-screen bg-gray-50">
    <NavBar />
    <main class="pt-16">

      <!-- Header -->
      <div class="bg-white border-b border-gray-100">
        <div class="max-w-5xl mx-auto px-4 sm:px-6 py-8">
          <div class="inline-flex items-center gap-2 bg-violet-50 text-violet-700 text-xs font-bold px-3 py-1.5 rounded-full mb-3 uppercase tracking-widest border border-violet-200">
            ML Pipeline
          </div>
          <h1 class="text-2xl font-extrabold text-gray-900 mb-1">종목별 매수 타이밍 예측 모델</h1>
          <p class="text-gray-400 text-sm">종목을 검색해 추가하고, 종목별 LightGBM 모델을 학습하여 오늘의 신호를 예측합니다. (Triple Barrier +5% / -2.5%)</p>
        </div>
      </div>

      <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6 space-y-5">

        <!-- 종목 검색 -->
        <div class="bg-white rounded-2xl border border-gray-100 p-4 shadow-sm">
          <div class="relative">
            <div class="flex items-center gap-2 border border-gray-200 rounded-xl px-4 py-2.5 focus-within:border-violet-400 focus-within:ring-2 focus-within:ring-violet-100 transition-all bg-white">
              <Search class="w-4 h-4 text-gray-400 flex-shrink-0" />
              <input
                v-model="searchQuery"
                @input="onSearchInput"
                @focus="searchQuery && (showDropdown = true)"
                @blur="hideDropdown"
                placeholder="종목 검색 (한글·영어·코드 모두 가능 — 테슬라, TSLA, 삼성전자, 005930)"
                class="flex-1 text-sm bg-transparent outline-none placeholder-gray-400"
              />
              <button v-if="searchQuery" @click="clearSearchBox" class="text-gray-300 hover:text-gray-500">
                <X class="w-4 h-4" />
              </button>
            </div>

            <!-- 드롭다운 -->
            <div v-if="showDropdown && (searchLoading || searchResults.length > 0)"
              class="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-xl z-50 overflow-hidden">
              <div v-if="searchLoading" class="flex items-center gap-2 px-4 py-3 text-sm text-gray-400">
                <Loader class="w-4 h-4 animate-spin" />검색 중...
              </div>
              <button
                v-for="r in searchResults" :key="r.symbol"
                @mousedown.prevent="selectSearchResult(r)"
                class="w-full flex items-center justify-between px-4 py-3 hover:bg-violet-50 transition-colors border-b border-gray-50 last:border-0 text-left"
                :class="trackedStocks.some(t => t.symbol === r.symbol) ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'"
              >
                <div>
                  <span class="font-bold text-gray-900 text-sm">{{ r.symbol }}</span>
                  <span v-if="r.name" class="text-gray-500 text-sm ml-2">{{ r.name }}</span>
                </div>
                <div class="flex items-center gap-2">
                  <span v-if="r.market || r.exchange" class="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
                    {{ r.market || r.exchange }}
                  </span>
                  <span v-if="trackedStocks.some(t => t.symbol === r.symbol)"
                    class="text-xs text-emerald-600 font-semibold">추가됨</span>
                  <span v-else class="text-xs text-violet-600 font-semibold">+ 추가</span>
                </div>
              </button>
            </div>
          </div>
        </div>

        <!-- 로그인 안내 -->
        <div v-if="!isLoggedIn" class="flex items-center gap-2 text-sm text-amber-600 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
          <AlertCircle class="w-4 h-4 flex-shrink-0" />
          로그인하면 관심 종목이 자동으로 표시됩니다.
        </div>

        <!-- 빈 상태 -->
        <div v-if="trackedStocks.length === 0" class="text-center py-14 text-gray-400">
          <Search class="w-10 h-10 mx-auto mb-3 text-gray-200" />
          <p class="text-sm">위 검색창에서 종목을 검색해 추가하세요.</p>
          <p v-if="isLoggedIn" class="text-xs mt-1 text-gray-300">관심 종목으로 등록된 종목은 자동으로 표시됩니다.</p>
        </div>

        <!-- 종목 카드 그리드 -->
        <div v-if="trackedStocks.length > 0" class="grid sm:grid-cols-2 gap-4">
          <div v-for="item in trackedStocks" :key="item.symbol"
            class="bg-white rounded-2xl border shadow-sm overflow-hidden transition-all"
            :class="activeResult === item.symbol ? 'border-violet-300 ring-2 ring-violet-100' : 'border-gray-100'">

            <!-- 카드 상단 -->
            <div class="flex items-start justify-between px-4 pt-4 pb-3">
              <div>
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="font-black text-gray-900">{{ item.symbol }}</span>
                  <span v-if="item.name" class="text-xs text-gray-400 truncate max-w-32">{{ item.name }}</span>
                </div>
                <div v-if="modelMetas[item.symbol]?.trained" class="flex items-center gap-1.5 mt-1">
                  <CheckCircle class="w-3 h-3 text-emerald-500" />
                  <span class="text-xs text-emerald-600 font-semibold">
                    정확도 {{ ((modelMetas[item.symbol].accuracy || 0) * 100).toFixed(1) }}%
                  </span>
                  <span class="text-xs text-gray-300">·</span>
                  <span class="text-xs text-gray-400">{{ modelMetas[item.symbol].trained_at }}</span>
                </div>
                <div v-else class="text-xs text-gray-400 mt-1">미학습</div>
              </div>
              <!-- 추가한 종목만 제거 가능 -->
              <button v-if="isExtra(item.symbol)" @click="removeExtra(item.symbol)"
                class="p-1 rounded-lg hover:bg-gray-100 text-gray-300 hover:text-gray-500 transition-colors flex-shrink-0">
                <X class="w-4 h-4" />
              </button>
            </div>

            <!-- 학습 에러 -->
            <div v-if="trainErrors[item.symbol]"
              class="mx-4 mb-2 text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
              {{ trainErrors[item.symbol] }}
            </div>

            <!-- 예측 결과 인라인 -->
            <div v-if="predictions[item.symbol]" class="mx-4 mb-3">
              <div class="rounded-xl border p-3"
                :class="[signalStyle(predictions[item.symbol].signal).bg, signalStyle(predictions[item.symbol].signal).border]">
                <div class="flex items-center justify-between flex-wrap gap-2">
                  <div class="flex items-center gap-2">
                    <span class="text-white text-xs font-black px-2.5 py-0.5 rounded-full"
                      :class="signalStyle(predictions[item.symbol].signal).badge">
                      {{ predictions[item.symbol].signal_label }}
                    </span>
                    <span class="font-bold text-sm" :class="signalStyle(predictions[item.symbol].signal).text">
                      {{ predictions[item.symbol].signal === 1 ? '매수 타이밍' : predictions[item.symbol].signal === 2 ? '매도·보류' : '관망' }}
                    </span>
                  </div>
                  <div class="flex gap-3 text-xs">
                    <div class="text-center">
                      <p class="text-gray-400">관망</p>
                      <p class="font-bold text-gray-700">{{ ((predictions[item.symbol].probabilities?.[0] || 0) * 100).toFixed(0) }}%</p>
                    </div>
                    <div class="text-center">
                      <p class="text-emerald-500">매수</p>
                      <p class="font-bold text-emerald-700">{{ ((predictions[item.symbol].probabilities?.[1] || 0) * 100).toFixed(0) }}%</p>
                    </div>
                    <div class="text-center">
                      <p class="text-red-400">매도</p>
                      <p class="font-bold text-red-600">{{ ((predictions[item.symbol].probabilities?.[2] || 0) * 100).toFixed(0) }}%</p>
                    </div>
                  </div>
                </div>
                <p class="text-xs text-gray-400 mt-1.5">기준일: {{ predictions[item.symbol].latest_date }}</p>
              </div>
            </div>
            <div v-if="predErrors[item.symbol]"
              class="mx-4 mb-3 text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
              {{ predErrors[item.symbol] }}
            </div>

            <!-- 액션 버튼 행 -->
            <div class="border-t border-gray-50 px-4 py-3 flex gap-2">
              <!-- 학습 -->
              <button @click="trainStock(item.symbol)"
                :disabled="trainingFor === item.symbol || predictingFor === item.symbol"
                class="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                :class="trainingFor === item.symbol ? 'bg-violet-100 text-violet-500' : 'bg-violet-600 hover:bg-violet-700 text-white shadow-sm'">
                <Loader v-if="trainingFor === item.symbol" class="w-3.5 h-3.5 animate-spin" />
                <RefreshCw v-else class="w-3.5 h-3.5" />
                {{ trainingFor === item.symbol ? '학습 중...' : modelMetas[item.symbol]?.trained ? '재학습' : '학습 시작' }}
              </button>
              <!-- 결과 토글 -->
              <button v-if="modelMetas[item.symbol]?.trained"
                @click="activeResult = activeResult === item.symbol ? null : item.symbol"
                class="px-3 py-2 rounded-xl text-xs font-bold border transition-all"
                :class="activeResult === item.symbol
                  ? 'border-violet-300 bg-violet-50 text-violet-700'
                  : 'border-gray-200 bg-gray-50 text-gray-500 hover:border-violet-200 hover:text-violet-600'">
                결과
              </button>
              <!-- 예측 -->
              <button v-if="modelMetas[item.symbol]?.trained"
                @click="predictStock(item.symbol)"
                :disabled="predictingFor === item.symbol || trainingFor === item.symbol"
                class="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                :class="predictingFor === item.symbol ? 'bg-blue-100 text-blue-500' : 'bg-blue-600 hover:bg-blue-700 text-white shadow-sm'">
                <Loader v-if="predictingFor === item.symbol" class="w-3.5 h-3.5 animate-spin" />
                <Zap v-else class="w-3.5 h-3.5" />
                {{ predictingFor === item.symbol ? '예측 중...' : '오늘 예측' }}
              </button>
            </div>
          </div>
        </div>

        <!-- ── 상세 결과 패널 ── -->
        <template v-if="activeResult && (trainResults[activeResult] || modelMetas[activeResult]?.trained)">
          <div class="bg-white rounded-2xl border border-violet-200 p-5 shadow-sm space-y-5">
            <div class="flex items-center justify-between">
              <h3 class="font-black text-gray-900">
                <span class="text-violet-600">{{ activeResult }}</span> 학습 결과
              </h3>
              <button @click="activeResult = null" class="p-1 rounded-lg hover:bg-gray-100 text-gray-400">
                <X class="w-4 h-4" />
              </button>
            </div>

            <!-- 요약 스탯 -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div class="text-center p-3 rounded-xl bg-violet-50 border border-violet-100">
                <p class="text-xl font-black text-violet-700">{{ ((modelMetas[activeResult]?.accuracy || 0) * 100).toFixed(1) }}%</p>
                <p class="text-xs text-gray-400 mt-1">정확도</p>
              </div>
              <div class="text-center p-3 rounded-xl bg-gray-50 border border-gray-100">
                <p class="text-xl font-black text-gray-800">{{ (modelMetas[activeResult]?.total_rows || 0).toLocaleString() }}</p>
                <p class="text-xs text-gray-400 mt-1">총 행수</p>
              </div>
              <div class="text-center p-3 rounded-xl bg-blue-50 border border-blue-100">
                <p class="text-xl font-black text-blue-700">{{ (modelMetas[activeResult]?.train_rows || 0).toLocaleString() }}</p>
                <p class="text-xs text-gray-400 mt-1">학습 (80%)</p>
              </div>
              <div class="text-center p-3 rounded-xl bg-indigo-50 border border-indigo-100">
                <p class="text-xl font-black text-indigo-700">{{ (modelMetas[activeResult]?.test_rows || 0).toLocaleString() }}</p>
                <p class="text-xs text-gray-400 mt-1">검증 (20%)</p>
              </div>
            </div>

            <!-- 클래스별 성능 + 혼동 행렬 -->
            <template v-if="trainResults[activeResult]">
              <div class="grid sm:grid-cols-2 gap-4">
                <div class="bg-gray-50 rounded-xl p-4 border border-gray-100">
                  <h4 class="font-bold text-gray-800 text-sm mb-3">클래스별 성능</h4>
                  <table class="w-full text-xs">
                    <thead>
                      <tr class="text-gray-400 border-b border-gray-200">
                        <th class="text-left pb-2 font-semibold">클래스</th>
                        <th class="text-right pb-2 font-semibold">P</th>
                        <th class="text-right pb-2 font-semibold">R</th>
                        <th class="text-right pb-2 font-semibold">F1</th>
                        <th class="text-right pb-2 font-semibold">N</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(v, label) in trainResults[activeResult].per_class" :key="label"
                        class="border-b border-gray-100 last:border-0">
                        <td class="py-1.5 font-bold text-gray-700">{{ label }}</td>
                        <td class="py-1.5 text-right text-gray-500">{{ v.precision }}</td>
                        <td class="py-1.5 text-right text-gray-500">{{ v.recall }}</td>
                        <td class="py-1.5 text-right font-bold"
                          :class="v.f1 >= 0.6 ? 'text-emerald-600' : v.f1 >= 0.4 ? 'text-amber-600' : 'text-red-500'">
                          {{ v.f1 }}
                        </td>
                        <td class="py-1.5 text-right text-gray-400">{{ v.support }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <div class="bg-gray-50 rounded-xl p-4 border border-gray-100">
                  <h4 class="font-bold text-gray-800 text-sm mb-3">혼동 행렬</h4>
                  <div class="flex gap-1 justify-center mb-1 ml-5">
                    <div v-for="l in ['관망','매수','매도']" :key="l"
                      class="w-12 text-center text-xs text-gray-400">{{ l }}</div>
                  </div>
                  <div v-for="(row, ri) in (trainResults[activeResult].confusion_matrix || [])" :key="ri"
                    class="flex gap-1 justify-center mb-1 items-center">
                    <div class="w-5 text-xs text-gray-400 text-right pr-1">{{ ['관','매','도'][ri] }}</div>
                    <div v-for="(cell, ci) in row" :key="ci"
                      class="w-12 h-8 rounded-lg flex items-center justify-center text-sm font-bold"
                      :class="ri === ci ? 'bg-violet-100 text-violet-700 border border-violet-200' : 'bg-white text-gray-500 border border-gray-100'">
                      {{ cell }}
                    </div>
                  </div>
                  <p class="text-xs text-gray-400 mt-2 text-center">대각선 = 정답</p>
                </div>
              </div>
            </template>

            <!-- 피처 중요도 -->
            <div v-if="(trainResults[activeResult] || modelMetas[activeResult])?.feat_imp?.length">
              <h4 class="font-bold text-gray-800 text-sm mb-3">피처 중요도</h4>
              <div class="space-y-2">
                <div v-for="f in (trainResults[activeResult] || modelMetas[activeResult]).feat_imp"
                  :key="f.feature" class="flex items-center gap-3">
                  <span class="w-28 text-xs text-gray-400 text-right flex-shrink-0">{{ featLabel(f.feature) }}</span>
                  <div class="flex-1 bg-gray-100 rounded-full h-2">
                    <div class="h-2 rounded-full bg-violet-500 transition-all"
                      :style="{ width: (f.importance / maxImp(activeResult) * 100) + '%' }"></div>
                  </div>
                  <span class="w-8 text-xs text-gray-400 text-right flex-shrink-0">{{ f.importance }}</span>
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
