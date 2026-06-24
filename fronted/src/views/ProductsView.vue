<script setup>
import { ref, computed, onMounted } from 'vue'
import NavBar from '@/components/NavBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import { PiggyBank, Landmark, RefreshCw, Info, ChevronDown, ExternalLink, Loader2 } from '@lucide/vue'
import { useAuth } from '@/composables/useAuth'

const { authFetch } = useAuth()

// ── 상수 ──────────────────────────────────────────────────────
const TERMS = ['6', '12', '24', '36']
const API_BASE = '/api/products'

// ── 상태 ──────────────────────────────────────────────────────
const selectedTerm   = ref('12')
const activeTab      = ref('deposit')

const depositRaw     = ref([])
const savingsRaw     = ref([])
const depositUpdated = ref(null)   // 마지막 업데이트 시각 (ISO string)
const savingsUpdated = ref(null)
const loading        = ref(false)
const error          = ref(null)
const expandedId     = ref(null)

// ── DB 읽기 ──────────────────────────────────────────────────
async function loadFromDb(type) {
  const res = await fetch(`${API_BASE}/${type}/`)
  if (res.status === 404) return { products: [], updated_at: null }
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function loadAll() {
  loading.value = true
  error.value   = null
  try {
    const [dep, sav] = await Promise.all([
      loadFromDb('deposit'),
      loadFromDb('savings'),
    ])
    depositRaw.value     = dep.products ?? []
    savingsRaw.value     = sav.products ?? []
    depositUpdated.value = dep.updated_at
    savingsUpdated.value = sav.updated_at
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

// ── FSS API 갱신 (업데이트 버튼) ─────────────────────────────
const refreshing = ref(false)
const refreshError = ref(null)

async function refreshProducts() {
  refreshing.value   = true
  refreshError.value = null
  try {
    const res = await authFetch(`${API_BASE}/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: 'all' }),
    })
    if (!res.ok) {
      const data = await res.json()
      throw new Error(data.error ?? `HTTP ${res.status}`)
    }
    await loadAll()
  } catch (e) {
    refreshError.value = e.message
  } finally {
    refreshing.value = false
  }
}

function fmtUpdated(iso) {
  if (!iso) return null
  const d = new Date(iso)
  return d.toLocaleString('ko-KR', { month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })
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
  <div class="min-h-screen bg-white" style="font-family:'Pretendard','Noto Sans KR',sans-serif">
    <NavBar />

    <main class="pt-16">
      <!-- 페이지 헤더 -->
      <div style="background:linear-gradient(90deg,#fffdf9 0%,#ffffff 50%,#f2fffb 100%);border-bottom:1px solid #EEF1F5">
        <div class="max-w-3xl mx-auto px-6 py-10">
          <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-bold mb-3" style="background:#DFFAF4;color:#0D9B7A;font-size:0.72rem">
            <RefreshCw class="w-3 h-3" />매일 업데이트 · 금감원 공시
          </div>
          <div class="flex items-end justify-between gap-4">
            <div>
              <h1 class="font-black mb-1" style="font-size:1.8rem;color:#0F122B">인기 금융상품</h1>
              <p style="color:#6F7485;font-size:0.9rem">금융감독원 금융상품통합비교공시 기준 최고금리 상위 상품</p>
            </div>
            <div class="flex flex-col items-end gap-1 flex-shrink-0">
              <button
                @click="refreshProducts"
                :disabled="refreshing"
                class="inline-flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-sm transition-all disabled:opacity-50"
                style="background:#0F122B;color:white"
              >
                <RefreshCw class="w-3.5 h-3.5" :class="refreshing ? 'animate-spin' : ''" />
                {{ refreshing ? '업데이트 중...' : '데이터 업데이트' }}
              </button>
              <span v-if="fmtUpdated(activeTab === 'deposit' ? depositUpdated : savingsUpdated)" style="font-size:0.7rem;color:#6F7485">
                마지막 업데이트 {{ fmtUpdated(activeTab === 'deposit' ? depositUpdated : savingsUpdated) }}
              </span>
              <span v-else style="font-size:0.7rem;color:#6F7485">업데이트 이력 없음</span>
            </div>
          </div>
        </div>
      </div>

      <div class="max-w-3xl mx-auto px-6 py-8">

        <!-- 로드 에러 -->
        <div v-if="error" class="mb-6 flex items-start gap-3 rounded-2xl p-5" style="background:#FFF5F5;border:1px solid #FFD0D0">
          <Info class="w-5 h-5 flex-shrink-0 mt-0.5" style="color:#E5323B" />
          <div>
            <p class="font-bold text-sm" style="color:#E5323B">데이터를 불러오지 못했습니다</p>
            <p class="text-sm mt-0.5" style="color:#E5323B">{{ error }}</p>
            <button @click="loadAll" class="mt-2 text-xs font-semibold underline" style="color:#E5323B">다시 시도</button>
          </div>
        </div>

        <!-- 업데이트 에러 -->
        <div v-if="refreshError" class="mb-6 flex items-start gap-3 rounded-2xl p-5" style="background:#FFF5F5;border:1px solid #FFD0D0">
          <Info class="w-5 h-5 flex-shrink-0 mt-0.5" style="color:#E5323B" />
          <div>
            <p class="font-bold text-sm" style="color:#E5323B">업데이트에 실패했습니다</p>
            <p class="text-sm mt-0.5" style="color:#E5323B">{{ refreshError }}</p>
          </div>
        </div>

        <!-- DB 데이터 없음 안내 -->
        <div v-if="!loading && !error && depositRaw.length === 0 && savingsRaw.length === 0"
          class="mb-6 flex items-start gap-3 rounded-2xl p-5" style="background:#FFF8E6;border:1px solid #FFD76A">
          <Info class="w-5 h-5 flex-shrink-0 mt-0.5" style="color:#B8860B" />
          <div>
            <p class="font-bold text-sm" style="color:#B8860B">저장된 데이터가 없습니다</p>
            <p class="text-sm mt-0.5" style="color:#B8860B">우측 상단의 <b>데이터 업데이트</b> 버튼을 눌러 금감원 API에서 최신 데이터를 가져오세요.</p>
          </div>
        </div>

        <!-- 컨트롤: 탭 + 기간 필터 -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div class="flex gap-2">
            <button
              @click="activeTab = 'deposit'"
              class="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold transition-all"
              :style="activeTab === 'deposit'
                ? 'background:#0F122B;color:white'
                : 'background:white;color:#6F7485;border:1.5px solid #EEF1F5'"
            >
              <Landmark class="w-4 h-4" />정기예금
            </button>
            <button
              @click="activeTab = 'savings'"
              class="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold transition-all"
              :style="activeTab === 'savings'
                ? 'background:#0F122B;color:white'
                : 'background:white;color:#6F7485;border:1.5px solid #EEF1F5'"
            >
              <PiggyBank class="w-4 h-4" />적금
            </button>
          </div>

          <div class="flex items-center gap-2">
            <span class="text-sm font-medium" style="color:#6F7485">기간</span>
            <div class="flex gap-1.5">
              <button
                v-for="t in TERMS"
                :key="t"
                @click="selectedTerm = t"
                class="px-3 py-1.5 rounded-xl text-xs font-bold transition-all"
                :style="selectedTerm === t
                  ? 'background:#57E0C3;color:#0F122B'
                  : 'background:white;color:#6F7485;border:1.5px solid #EEF1F5'"
              >
                {{ t }}개월
              </button>
            </div>
          </div>
        </div>

        <!-- 로딩 스켈레톤 -->
        <div v-if="loading" class="grid gap-3">
          <div v-for="i in 3" :key="i" class="rounded-2xl p-6 animate-pulse" style="background:white;border:1px solid #EEF1F5">
            <div class="flex items-start gap-4 mb-5">
              <div class="w-12 h-12 rounded-xl" style="background:#EEF1F5"></div>
              <div class="flex-1 space-y-2">
                <div class="w-24 h-3 rounded" style="background:#EEF1F5"></div>
                <div class="w-48 h-5 rounded" style="background:#EEF1F5"></div>
              </div>
            </div>
            <div class="w-36 h-10 rounded mb-2" style="background:#EEF1F5"></div>
          </div>
        </div>

        <!-- 공통 카드 렌더러 -->
        <template v-else>
          <div v-for="(list, key) in { deposit: { top: topDeposits, rest: restDeposits, empty: Landmark }, savings: { top: topSavings, rest: restSavings, empty: PiggyBank } }" :key="key">
            <div v-if="activeTab === key">
              <div v-if="list.top.length === 0" class="text-center py-20" style="color:#6F7485">
                <component :is="list.empty" class="w-10 h-10 mx-auto mb-3 opacity-30" />
                <p class="font-medium">{{ selectedTerm }}개월 기준 데이터가 없습니다</p>
              </div>

              <div v-else class="grid gap-3">
                <!-- TOP 3 -->
                <p class="text-xs font-bold px-1 mb-1" style="color:#6F7485;letter-spacing:0.08em">TOP 3</p>
                <div
                  v-for="(product, idx) in list.top"
                  :key="product.fin_prdt_cd"
                  class="rounded-2xl overflow-hidden transition-all duration-200 hover:-translate-y-0.5"
                  style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)"
                >
                  <div class="p-6">
                    <div class="flex items-start justify-between mb-4">
                      <div class="flex items-center gap-3">
                        <span
                          class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-black flex-shrink-0"
                          :style="idx === 0 ? 'background:#FFD76A;color:#0F122B' : idx === 1 ? 'background:#EEF1F5;color:#0F122B' : 'background:#DFFAF4;color:#0D9B7A'"
                        >{{ idx + 1 }}</span>
                        <div
                          class="w-11 h-11 rounded-xl flex items-center justify-center text-sm font-black flex-shrink-0"
                          :style="idx === 0 ? 'background:#FFF8E6;color:#B8860B' : idx === 1 ? 'background:#EEF1F5;color:#0F122B' : 'background:#DFFAF4;color:#0D9B7A'"
                        >{{ bankInitials(product.kor_co_nm) }}</div>
                        <div>
                          <p class="font-medium" style="font-size:0.72rem;color:#6F7485">{{ product.kor_co_nm }}</p>
                          <p class="font-bold" style="font-size:0.95rem;color:#0F122B">{{ product.fin_prdt_nm }}</p>
                        </div>
                      </div>
                      <span class="px-2.5 py-1 rounded-full font-semibold" style="font-size:0.7rem;background:#F4F5F8;color:#6F7485">
                        {{ product.intr_rate_type_nm }}
                      </span>
                    </div>

                    <div class="flex items-end gap-8 mb-4">
                      <div>
                        <p class="mb-0.5" style="font-size:0.72rem;color:#6F7485">최고 우대금리</p>
                        <div class="flex items-end gap-1">
                          <span class="font-black leading-none" style="font-size:2.4rem;color:#57E0C3">{{ product.intr_rate2?.toFixed(2) }}</span>
                          <span class="font-bold mb-0.5" style="font-size:1rem;color:#57E0C3">%</span>
                          <span class="mb-1" style="font-size:0.8rem;color:#6F7485">/ 연</span>
                        </div>
                      </div>
                      <div class="pb-1">
                        <p class="mb-0.5" style="font-size:0.72rem;color:#6F7485">기본금리</p>
                        <p class="font-bold" style="font-size:1.1rem;color:#0F122B">{{ product.intr_rate?.toFixed(2) }}<span style="font-size:0.8rem;font-weight:400">%</span></p>
                      </div>
                      <div class="pb-1">
                        <p class="mb-0.5" style="font-size:0.72rem;color:#6F7485">저축기간</p>
                        <p class="font-bold" style="font-size:1.1rem;color:#0F122B">{{ product.save_trm }}<span style="font-size:0.8rem;font-weight:400">개월</span></p>
                      </div>
                    </div>

                    <div class="flex flex-wrap items-center gap-2">
                      <span
                        v-for="way in parseJoinWay(product.join_way)"
                        :key="way"
                        class="px-2.5 py-0.5 rounded-full font-semibold"
                        style="background:#DFFAF4;color:#0D9B7A;font-size:0.72rem"
                      >#{{ way }}</span>
                      <span v-if="product.join_deny === '2'" class="px-2.5 py-0.5 rounded-full font-semibold" style="background:#FFF8E6;color:#B8860B;font-size:0.72rem">#서민전용</span>
                      <span v-if="product.join_deny === '3'" class="px-2.5 py-0.5 rounded-full font-semibold" style="background:#FFF5F5;color:#E5323B;font-size:0.72rem">#가입제한</span>
                      <div class="ml-auto flex items-center gap-3">
                        <a :href="product.product_url" target="_blank" rel="noopener noreferrer"
                          class="flex items-center gap-1 font-semibold transition-colors"
                          style="font-size:0.75rem;color:#57E0C3"
                        >바로가기 <ExternalLink class="w-3 h-3" /></a>
                        <button
                          @click="expandedId = expandedId === product.fin_prdt_cd ? null : product.fin_prdt_cd"
                          class="flex items-center gap-1 font-medium transition-colors"
                          style="font-size:0.75rem;color:#6F7485"
                        >
                          우대조건
                          <ChevronDown class="w-3.5 h-3.5 transition-transform" :class="expandedId === product.fin_prdt_cd ? 'rotate-180' : ''" />
                        </button>
                      </div>
                    </div>
                  </div>

                  <div v-show="expandedId === product.fin_prdt_cd" class="px-6 py-5 space-y-3" style="border-top:1px solid #EEF1F5;background:#F8F9FF">
                    <div v-if="product.spcl_cnd">
                      <p class="font-bold mb-1.5" style="font-size:0.7rem;color:#6F7485;letter-spacing:0.08em">우대 조건</p>
                      <p class="leading-relaxed whitespace-pre-line" style="font-size:0.85rem;color:#0F122B">{{ product.spcl_cnd }}</p>
                    </div>
                    <div v-if="product.join_member" class="flex gap-8">
                      <div>
                        <p class="font-bold mb-1" style="font-size:0.7rem;color:#6F7485;letter-spacing:0.08em">가입 대상</p>
                        <p style="font-size:0.85rem;color:#0F122B">{{ product.join_member }}</p>
                      </div>
                      <div v-if="product.max_limit">
                        <p class="font-bold mb-1" style="font-size:0.7rem;color:#6F7485;letter-spacing:0.08em">최고 한도</p>
                        <p style="font-size:0.85rem;color:#0F122B">{{ Number(product.max_limit).toLocaleString() }}원</p>
                      </div>
                    </div>
                    <div v-if="product.mtrt_int">
                      <p class="font-bold mb-1" style="font-size:0.7rem;color:#6F7485;letter-spacing:0.08em">만기 후 이자율</p>
                      <p style="font-size:0.85rem;color:#0F122B">{{ product.mtrt_int }}</p>
                    </div>
                  </div>
                </div>

                <!-- 4~10위 -->
                <template v-if="list.rest.length > 0">
                  <p class="text-xs font-bold px-1 mt-3 mb-1" style="color:#6F7485;letter-spacing:0.08em">4위 ~ {{ list.rest.length + 3 }}위</p>
                  <div class="rounded-2xl overflow-hidden" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
                    <div
                      v-for="(product, idx) in list.rest"
                      :key="product.fin_prdt_cd"
                      class="flex items-center gap-3 px-5 py-3.5 transition-colors hover:bg-[#F8F9FF]"
                      style="border-bottom:1px solid #EEF1F5"
                    >
                      <span class="flex-shrink-0 font-bold text-center tabular-nums" style="width:20px;font-size:0.75rem;color:#6F7485">{{ idx + 4 }}</span>
                      <div class="w-9 h-9 rounded-xl flex items-center justify-center font-black flex-shrink-0" style="background:#EEF1F5;color:#0F122B;font-size:0.75rem">
                        {{ bankInitials(product.kor_co_nm) }}
                      </div>
                      <div class="flex-1 min-w-0">
                        <p style="font-size:0.72rem;color:#6F7485">{{ product.kor_co_nm }}</p>
                        <p class="font-semibold truncate" style="font-size:0.85rem;color:#0F122B">{{ product.fin_prdt_nm }}</p>
                      </div>
                      <div class="text-right flex-shrink-0">
                        <p style="font-size:0.72rem;color:#6F7485">최고금리</p>
                        <p class="font-black tabular-nums" style="font-size:1rem;color:#57E0C3">{{ product.intr_rate2?.toFixed(2) }}<span style="font-size:0.72rem;color:#6F7485;font-weight:400">%</span></p>
                      </div>
                      <div class="text-right flex-shrink-0" style="width:60px">
                        <p style="font-size:0.72rem;color:#6F7485">기본금리</p>
                        <p class="font-bold tabular-nums" style="font-size:0.85rem;color:#0F122B">{{ product.intr_rate?.toFixed(2) }}<span style="font-size:0.72rem;font-weight:400">%</span></p>
                      </div>
                      <a :href="product.product_url" target="_blank" rel="noopener noreferrer" class="flex-shrink-0 transition-colors" style="color:#57E0C3">
                        <ExternalLink class="w-4 h-4" />
                      </a>
                    </div>
                  </div>
                </template>
              </div>
            </div>
          </div>
        </template>

        <p class="text-center mt-10" style="font-size:0.75rem;color:#6F7485">
          데이터 출처: <span class="font-medium" style="color:#0F122B">금융감독원 금융상품통합비교공시</span> · 매일 업데이트
        </p>
      </div>
    </main>
    <AppFooter />
  </div>
</template>
