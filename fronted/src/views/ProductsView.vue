<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import NavBar from '@/components/NavBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import { PiggyBank, Landmark, RefreshCw, Info, ChevronDown, ExternalLink } from '@lucide/vue'

// ── 상수 ──────────────────────────────────────────────────────
const TERMS = ['6', '12', '24', '36']
const API_BASE = '/api/products'

// ── 상태 ──────────────────────────────────────────────────────
const selectedTerm   = ref('12')                // 기본: 12개월
const activeTab      = ref('deposit')           // 'deposit' | 'savings'

const depositRaw   = ref([])   // 예금 전체 상품 (API 원본)
const savingsRaw   = ref([])   // 적금 전체 상품 (API 원본)
const loading      = ref(false)
const error        = ref(null)
const expandedId   = ref(null) // 상세 펼침 상품 ID

// ── API 호출 ──────────────────────────────────────────────────
/**
 * FSS 금융상품비교 API 호출
 * - 개발: Vite 프록시 → /api/fss/...  →  https://finlife.fss.or.kr/finlifeapi/...
 * - 응답 구조: result.products[].baseinfo / result.products[].options[]
 */
async function fetchProducts(type) {
  const res = await fetch(`${API_BASE}/${type}/`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function loadAll() {
  loading.value = true
  error.value   = null
  try {
    const [dep, sav] = await Promise.all([
      fetchProducts('deposit'),
      fetchProducts('savings'),
    ])
    depositRaw.value = dep
    savingsRaw.value = sav
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(loadAll)

// ── 데이터 가공 ───────────────────────────────────────────────
/**
 * 선택된 기간에 맞는 옵션을 찾아 Top 3 정렬
 * - intr_rate2(최고금리) 기준 내림차순
 * - 같은 기간 옵션이 여러 개면 가장 높은 것 선택
 */
function processTopN(rawList, term, n = 10) {
  return rawList
    .map(product => {
      const opts = (product.options ?? []).filter(o => String(o.save_trm) === term)
      if (!opts.length) return null
      const best = opts.reduce((a, b) => (b.intr_rate2 > a.intr_rate2 ? b : a))
      return { ...product.baseinfo, ...best }
    })
    .filter(Boolean)
    .sort((a, b) => b.intr_rate2 - a.intr_rate2)
    .slice(0, n)
}

const allDeposits  = computed(() => processTopN(depositRaw.value, selectedTerm.value))
const allSavings   = computed(() => processTopN(savingsRaw.value,  selectedTerm.value))
const topDeposits  = computed(() => allDeposits.value.slice(0, 3))
const topSavings   = computed(() => allSavings.value.slice(0, 3))
const restDeposits = computed(() => allDeposits.value.slice(3))
const restSavings  = computed(() => allSavings.value.slice(3))

// ── 유틸 ──────────────────────────────────────────────────────
function bankInitials(name = '') {
  const map = {
    '국민': 'KB', '신한': 'SH', '하나': 'HN', '우리': 'WR',
    '기업': 'IB', '농협': 'NH', '카카오': 'KK', '토스': 'TS',
    '케이': 'K뱅', '씨티': 'CT', '산업': 'KD', 'SC': 'SC',
    '대구': 'DG', '부산': 'BS', '광주': 'GJ', '경남': 'KN',
    '전북': 'JB', '제주': 'JJ', '수협': 'SH', '저축': '저축',
  }
  for (const [k, v] of Object.entries(map)) {
    if (name.includes(k)) return v
  }
  return name.slice(0, 2)
}

function parseJoinWay(joinWay = '') {
  const map = { '인터넷': '온라인', '스마트폰': '모바일', '영업점': '영업점', 'ARS': 'ARS' }
  return joinWay.split(',').map(w => map[w.trim()] ?? w.trim()).filter(Boolean)
}

function bankColor(name = '') {
  const colors = [
    'from-blue-700 to-blue-900', 'from-indigo-600 to-purple-800',
    'from-orange-500 to-amber-700', 'from-emerald-500 to-teal-700',
    'from-sky-500 to-blue-700', 'from-yellow-500 to-orange-600',
  ]
  let hash = 0
  for (const c of name) hash = (hash * 31 + c.charCodeAt(0)) & 0xffff
  return colors[hash % colors.length]
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <NavBar />

    <main class="pt-16">
      <!-- 페이지 헤더 -->
      <div class="bg-white border-b border-gray-100">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 py-10">
          <div class="inline-flex items-center gap-2 bg-blue-50 text-blue-700 text-xs font-bold px-3 py-1.5 rounded-full mb-3 uppercase tracking-widest border border-blue-100">
            <RefreshCw class="w-3 h-3" />매일 업데이트 · 금감원 공시
          </div>
          <h1 class="text-3xl font-extrabold text-gray-900 mb-1">인기 금융상품</h1>
          <p class="text-gray-400">금융감독원 금융상품통합비교공시 기준 최고금리 상위 상품</p>
        </div>
      </div>

      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-10">

        <!-- 에러 -->
        <div v-if="error" class="mb-8 flex items-start gap-3 bg-red-50 border border-red-200 rounded-2xl p-5">
          <Info class="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p class="font-bold text-red-700 text-sm">데이터를 불러오지 못했습니다</p>
            <p class="text-red-600 text-sm mt-0.5">{{ error }}</p>
            <button @click="loadAll" class="mt-2 text-xs font-semibold text-red-600 underline">다시 시도</button>
          </div>
        </div>

        <!-- 컨트롤: 탭 + 기간 필터 -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <!-- 상품 탭 -->
          <div class="flex gap-2">
            <button
              @click="activeTab = 'deposit'"
              class="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold transition-all"
              :class="activeTab === 'deposit' ? 'bg-blue-800 text-white shadow-md' : 'bg-white text-gray-600 border border-gray-200 hover:border-blue-300'"
            >
              <Landmark class="w-4 h-4" />정기예금
            </button>
            <button
              @click="activeTab = 'savings'"
              class="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold transition-all"
              :class="activeTab === 'savings' ? 'bg-blue-800 text-white shadow-md' : 'bg-white text-gray-600 border border-gray-200 hover:border-blue-300'"
            >
              <PiggyBank class="w-4 h-4" />적금
            </button>
          </div>

          <!-- 기간 필터 -->
          <div class="flex items-center gap-2">
            <span class="text-sm text-gray-500 font-medium">기간</span>
            <div class="flex gap-1.5">
              <button
                v-for="t in TERMS"
                :key="t"
                @click="selectedTerm = t"
                class="px-3 py-1.5 rounded-lg text-xs font-bold transition-all"
                :class="selectedTerm === t ? 'bg-blue-700 text-white' : 'bg-white text-gray-500 border border-gray-200 hover:border-blue-300'"
              >
                {{ t }}개월
              </button>
            </div>
          </div>
        </div>

        <!-- 로딩 스켈레톤 -->
        <div v-if="loading" class="grid gap-4">
          <div v-for="i in 3" :key="i" class="bg-white rounded-2xl p-6 border border-gray-100 animate-pulse">
            <div class="flex items-start gap-4 mb-5">
              <div class="w-12 h-12 bg-gray-200 rounded-xl"></div>
              <div class="flex-1 space-y-2">
                <div class="w-24 h-3 bg-gray-200 rounded"></div>
                <div class="w-48 h-5 bg-gray-200 rounded"></div>
              </div>
            </div>
            <div class="w-36 h-10 bg-gray-200 rounded mb-2"></div>
            <div class="w-56 h-4 bg-gray-200 rounded"></div>
          </div>
        </div>

        <!-- 예금 Top 3 -->
        <div v-else-if="activeTab === 'deposit'">
          <div v-if="topDeposits.length === 0" class="text-center py-20 text-gray-400">
            <Landmark class="w-10 h-10 mx-auto mb-3 opacity-30" />
            <p class="font-medium">{{ selectedTerm }}개월 기준 데이터가 없습니다</p>
          </div>

          <div v-else class="grid gap-4">
            <p class="text-xs font-bold text-gray-400 uppercase tracking-wider px-1">TOP 3</p>
            <div
              v-for="(product, idx) in topDeposits"
              :key="product.fin_prdt_cd"
              class="bg-white rounded-2xl border border-gray-100 overflow-hidden transition-all duration-200 hover:shadow-md hover:border-blue-200"
            >
              <!-- 카드 메인 -->
              <div class="p-6">
                <div class="flex items-start justify-between mb-4">
                  <div class="flex items-center gap-3">
                    <!-- 순위 -->
                    <span
                      class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-black text-white flex-shrink-0"
                      :class="idx === 0 ? 'bg-amber-400' : idx === 1 ? 'bg-gray-400' : 'bg-orange-400'"
                    >{{ idx + 1 }}</span>
                    <!-- 은행 이니셜 -->
                    <div
                      class="w-12 h-12 rounded-xl flex items-center justify-center text-white text-sm font-black shadow-sm bg-gradient-to-br flex-shrink-0"
                      :class="bankColor(product.kor_co_nm)"
                    >
                      {{ bankInitials(product.kor_co_nm) }}
                    </div>
                    <div>
                      <p class="text-xs text-gray-400 font-medium">{{ product.kor_co_nm }}</p>
                      <p class="font-bold text-gray-900 text-base leading-tight">{{ product.fin_prdt_nm }}</p>
                    </div>
                  </div>
                  <!-- 금리 유형 -->
                  <span class="text-xs font-semibold bg-indigo-50 text-indigo-700 px-2.5 py-1 rounded-full border border-indigo-100">
                    {{ product.intr_rate_type_nm }}
                  </span>
                </div>

                <!-- 금리 표시 -->
                <div class="flex items-end gap-6 mb-4">
                  <div>
                    <p class="text-xs text-gray-400 mb-0.5">최고 우대금리</p>
                    <div class="flex items-end gap-1.5">
                      <span class="text-4xl font-black text-blue-700 leading-none">{{ product.intr_rate2?.toFixed(2) }}</span>
                      <span class="text-lg text-blue-500 font-bold mb-0.5">%</span>
                      <span class="text-sm text-gray-400 mb-1">/ 연</span>
                    </div>
                  </div>
                  <div class="pb-1.5">
                    <p class="text-xs text-gray-400 mb-0.5">기본금리</p>
                    <p class="text-xl font-bold text-gray-500">{{ product.intr_rate?.toFixed(2) }}<span class="text-sm font-normal">%</span></p>
                  </div>
                  <div class="pb-1.5">
                    <p class="text-xs text-gray-400 mb-0.5">저축기간</p>
                    <p class="text-xl font-bold text-gray-700">{{ product.save_trm }}<span class="text-sm font-normal">개월</span></p>
                  </div>
                </div>

                <!-- 가입 방법 태그 -->
                <div class="flex flex-wrap items-center gap-2">
                  <span
                    v-for="way in parseJoinWay(product.join_way)"
                    :key="way"
                    class="bg-blue-50 text-blue-700 text-xs font-semibold px-2.5 py-0.5 rounded-full"
                  >#{{ way }}</span>
                  <span v-if="product.join_deny === '2'" class="bg-orange-50 text-orange-600 text-xs font-semibold px-2.5 py-0.5 rounded-full">#서민전용</span>
                  <span v-if="product.join_deny === '3'" class="bg-red-50 text-red-600 text-xs font-semibold px-2.5 py-0.5 rounded-full">#가입제한</span>
                  <div class="ml-auto flex items-center gap-3">
                    <a
                      :href="product.product_url"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-semibold transition-colors"
                    >
                      바로가기 <ExternalLink class="w-3 h-3" />
                    </a>
                    <button
                      @click="expandedId = expandedId === product.fin_prdt_cd ? null : product.fin_prdt_cd"
                      class="flex items-center gap-1 text-xs text-gray-400 hover:text-blue-600 transition-colors font-medium"
                    >
                      우대조건
                      <ChevronDown
                        class="w-3.5 h-3.5 transition-transform"
                        :class="expandedId === product.fin_prdt_cd ? 'rotate-180' : ''"
                      />
                    </button>
                  </div>
                </div>
              </div>

              <!-- 상세 펼침 -->
              <div
                v-show="expandedId === product.fin_prdt_cd"
                class="border-t border-gray-100 bg-slate-50 px-6 py-5 space-y-3"
              >
                <div v-if="product.spcl_cnd">
                  <p class="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5">우대 조건</p>
                  <p class="text-sm text-gray-700 leading-relaxed whitespace-pre-line">{{ product.spcl_cnd }}</p>
                </div>
                <div v-if="product.join_member" class="flex gap-6">
                  <div>
                    <p class="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">가입 대상</p>
                    <p class="text-sm text-gray-700">{{ product.join_member }}</p>
                  </div>
                  <div v-if="product.max_limit">
                    <p class="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">최고 한도</p>
                    <p class="text-sm text-gray-700">{{ Number(product.max_limit).toLocaleString() }}원</p>
                  </div>
                </div>
                <div v-if="product.mtrt_int">
                  <p class="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">만기 후 이자율</p>
                  <p class="text-sm text-gray-700">{{ product.mtrt_int }}</p>
                </div>
              </div>
            </div>

            <!-- 4~10위 -->
            <template v-if="restDeposits.length > 0">
              <p class="text-xs font-bold text-gray-400 uppercase tracking-wider px-1 mt-4">4위 ~ {{ restDeposits.length + 3 }}위</p>
              <div class="bg-white rounded-2xl border border-gray-100 shadow-sm divide-y divide-gray-50">
                <div
                  v-for="(product, idx) in restDeposits"
                  :key="product.fin_prdt_cd"
                  class="flex items-center gap-3 px-5 py-3.5 hover:bg-blue-50 transition-colors"
                >
                  <span class="w-6 text-xs font-bold text-gray-400 text-center flex-shrink-0">{{ idx + 4 }}</span>
                  <div
                    class="w-9 h-9 rounded-xl flex items-center justify-center text-white text-xs font-black bg-gradient-to-br flex-shrink-0"
                    :class="bankColor(product.kor_co_nm)"
                  >{{ bankInitials(product.kor_co_nm) }}</div>
                  <div class="flex-1 min-w-0">
                    <p class="text-xs text-gray-400">{{ product.kor_co_nm }}</p>
                    <p class="text-sm font-semibold text-gray-900 truncate">{{ product.fin_prdt_nm }}</p>
                  </div>
                  <div class="text-right flex-shrink-0">
                    <p class="text-xs text-gray-400">최고금리</p>
                    <p class="text-base font-black text-blue-700">{{ product.intr_rate2?.toFixed(2) }}<span class="text-xs font-normal text-gray-400">%</span></p>
                  </div>
                  <div class="text-right flex-shrink-0 w-16">
                    <p class="text-xs text-gray-400">기본금리</p>
                    <p class="text-sm font-bold text-gray-500">{{ product.intr_rate?.toFixed(2) }}<span class="text-xs font-normal">%</span></p>
                  </div>
                  <a
                    :href="product.product_url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="flex-shrink-0 text-blue-500 hover:text-blue-700 transition-colors"
                  >
                    <ExternalLink class="w-4 h-4" />
                  </a>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- 적금 Top 3 -->
        <div v-else>
          <div v-if="topSavings.length === 0" class="text-center py-20 text-gray-400">
            <PiggyBank class="w-10 h-10 mx-auto mb-3 opacity-30" />
            <p class="font-medium">{{ selectedTerm }}개월 기준 데이터가 없습니다</p>
          </div>

          <div v-else class="grid gap-4">
            <p class="text-xs font-bold text-gray-400 uppercase tracking-wider px-1">TOP 3</p>
            <div
              v-for="(product, idx) in topSavings"
              :key="product.fin_prdt_cd"
              class="bg-white rounded-2xl border border-gray-100 overflow-hidden transition-all duration-200 hover:shadow-md hover:border-blue-200"
            >
              <div class="p-6">
                <div class="flex items-start justify-between mb-4">
                  <div class="flex items-center gap-3">
                    <span
                      class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-black text-white flex-shrink-0"
                      :class="idx === 0 ? 'bg-amber-400' : idx === 1 ? 'bg-gray-400' : 'bg-orange-400'"
                    >{{ idx + 1 }}</span>
                    <div
                      class="w-12 h-12 rounded-xl flex items-center justify-center text-white text-sm font-black shadow-sm bg-gradient-to-br flex-shrink-0"
                      :class="bankColor(product.kor_co_nm)"
                    >
                      {{ bankInitials(product.kor_co_nm) }}
                    </div>
                    <div>
                      <p class="text-xs text-gray-400 font-medium">{{ product.kor_co_nm }}</p>
                      <p class="font-bold text-gray-900 text-base leading-tight">{{ product.fin_prdt_nm }}</p>
                    </div>
                  </div>
                  <span class="text-xs font-semibold bg-blue-50 text-blue-700 px-2.5 py-1 rounded-full border border-blue-100">
                    {{ product.intr_rate_type_nm }}
                  </span>
                </div>

                <div class="flex items-end gap-6 mb-4">
                  <div>
                    <p class="text-xs text-gray-400 mb-0.5">최고 우대금리</p>
                    <div class="flex items-end gap-1.5">
                      <span class="text-4xl font-black text-blue-700 leading-none">{{ product.intr_rate2?.toFixed(2) }}</span>
                      <span class="text-lg text-blue-500 font-bold mb-0.5">%</span>
                      <span class="text-sm text-gray-400 mb-1">/ 연</span>
                    </div>
                  </div>
                  <div class="pb-1.5">
                    <p class="text-xs text-gray-400 mb-0.5">기본금리</p>
                    <p class="text-xl font-bold text-gray-500">{{ product.intr_rate?.toFixed(2) }}<span class="text-sm font-normal">%</span></p>
                  </div>
                  <div class="pb-1.5">
                    <p class="text-xs text-gray-400 mb-0.5">저축기간</p>
                    <p class="text-xl font-bold text-gray-700">{{ product.save_trm }}<span class="text-sm font-normal">개월</span></p>
                  </div>
                </div>

                <div class="flex flex-wrap items-center gap-2">
                  <span
                    v-for="way in parseJoinWay(product.join_way)"
                    :key="way"
                    class="bg-blue-50 text-blue-700 text-xs font-semibold px-2.5 py-0.5 rounded-full"
                  >#{{ way }}</span>
                  <div class="ml-auto flex items-center gap-3">
                    <a
                      :href="product.product_url"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-semibold transition-colors"
                    >
                      바로가기 <ExternalLink class="w-3 h-3" />
                    </a>
                    <button
                      @click="expandedId = expandedId === product.fin_prdt_cd ? null : product.fin_prdt_cd"
                      class="flex items-center gap-1 text-xs text-gray-400 hover:text-blue-600 transition-colors font-medium"
                    >
                      우대조건
                      <ChevronDown class="w-3.5 h-3.5 transition-transform" :class="expandedId === product.fin_prdt_cd ? 'rotate-180' : ''" />
                    </button>
                  </div>
                </div>
              </div>

              <div v-show="expandedId === product.fin_prdt_cd" class="border-t border-gray-100 bg-slate-50 px-6 py-5 space-y-3">
                <div v-if="product.spcl_cnd">
                  <p class="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5">우대 조건</p>
                  <p class="text-sm text-gray-700 leading-relaxed whitespace-pre-line">{{ product.spcl_cnd }}</p>
                </div>
                <div v-if="product.join_member" class="flex gap-6">
                  <div>
                    <p class="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">가입 대상</p>
                    <p class="text-sm text-gray-700">{{ product.join_member }}</p>
                  </div>
                  <div v-if="product.max_limit">
                    <p class="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">최고 한도</p>
                    <p class="text-sm text-gray-700">{{ Number(product.max_limit).toLocaleString() }}원</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- 4~10위 -->
            <template v-if="restSavings.length > 0">
              <p class="text-xs font-bold text-gray-400 uppercase tracking-wider px-1 mt-4">4위 ~ {{ restSavings.length + 3 }}위</p>
              <div class="bg-white rounded-2xl border border-gray-100 shadow-sm divide-y divide-gray-50">
                <div
                  v-for="(product, idx) in restSavings"
                  :key="product.fin_prdt_cd"
                  class="flex items-center gap-3 px-5 py-3.5 hover:bg-blue-50 transition-colors"
                >
                  <span class="w-6 text-xs font-bold text-gray-400 text-center flex-shrink-0">{{ idx + 4 }}</span>
                  <div
                    class="w-9 h-9 rounded-xl flex items-center justify-center text-white text-xs font-black bg-gradient-to-br flex-shrink-0"
                    :class="bankColor(product.kor_co_nm)"
                  >{{ bankInitials(product.kor_co_nm) }}</div>
                  <div class="flex-1 min-w-0">
                    <p class="text-xs text-gray-400">{{ product.kor_co_nm }}</p>
                    <p class="text-sm font-semibold text-gray-900 truncate">{{ product.fin_prdt_nm }}</p>
                  </div>
                  <div class="text-right flex-shrink-0">
                    <p class="text-xs text-gray-400">최고금리</p>
                    <p class="text-base font-black text-blue-700">{{ product.intr_rate2?.toFixed(2) }}<span class="text-xs font-normal text-gray-400">%</span></p>
                  </div>
                  <div class="text-right flex-shrink-0 w-16">
                    <p class="text-xs text-gray-400">기본금리</p>
                    <p class="text-sm font-bold text-gray-500">{{ product.intr_rate?.toFixed(2) }}<span class="text-xs font-normal">%</span></p>
                  </div>
                  <a
                    :href="product.product_url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="flex-shrink-0 text-blue-500 hover:text-blue-700 transition-colors"
                  >
                    <ExternalLink class="w-4 h-4" />
                  </a>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- 출처 -->
        <p class="text-center text-xs text-gray-400 mt-10">
          데이터 출처: <span class="font-medium text-gray-500">금융감독원 금융상품통합비교공시</span> · 매일 업데이트
        </p>
      </div>
    </main>
    <AppFooter />
  </div>
</template>
