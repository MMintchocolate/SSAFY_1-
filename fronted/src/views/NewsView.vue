<script setup>
// @ts-nocheck
import { ref, computed, onMounted } from 'vue'
import NavBar from '@/components/NavBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import {
  Newspaper, ExternalLink, ChevronDown, ChevronUp, ChevronLeft, ChevronRight,
  Loader2, AlertTriangle, DatabaseZap, Search, X,
  Sparkles, BookOpen, Crown,
} from '@lucide/vue'

// ─── 키워드 관리 ────────────────────────────────────────────────────────────
const DEFAULT_KWS = ['유출', '해킹', '주식']
const MAX_KWS = 3

function _loadKws() {
  try { const s = localStorage.getItem('news_keywords'); if (s) return JSON.parse(s) } catch {}
  return [...DEFAULT_KWS]
}
const userKeywords = ref(_loadKws())
const kwInput      = ref('')
const kwPanelOpen  = ref(false)

function saveKws() { localStorage.setItem('news_keywords', JSON.stringify(userKeywords.value)) }

function addKeyword() {
  const k = kwInput.value.trim()
  if (!k || userKeywords.value.includes(k) || userKeywords.value.length >= MAX_KWS) return
  userKeywords.value = [...userKeywords.value, k]
  saveKws(); kwInput.value = ''
}
function removeKeyword(kw) {
  userKeywords.value = userKeywords.value.filter(k => k !== kw)
  saveKws()
  if (clusterKeyword.value === kw) clusterKeyword.value = ''
  loadStats()
}
function resetKeywords() {
  userKeywords.value = [...DEFAULT_KWS]
  saveKws()
  clusterKeyword.value = ''
  loadStats()
}

// ─── 요약 상태 ───────────────────────────────────────────────────────────────
const summaryState = ref({})

// ─── 뉴스 목록 상태 ──────────────────────────────────────────────────────────
const newsList      = ref([])
const stats         = ref({ total: 0 })
const loading       = ref(false)
const crawling      = ref(false)
const errorMsg      = ref('')
const expandedTopId = ref(null)
const activeSection = ref(userKeywords.value[0] ?? '')
const selectedNews  = ref(null)

function openModal(news)  { selectedNews.value = news }
function closeModal()     { selectedNews.value = null }

// ─── Top 3 + 주제별 그룹 ─────────────────────────────────────────────────────
const topNews = computed(() => newsList.value.slice(0, 3))

const byKeyword = computed(() => {
  const groups = {}
  for (const kw of userKeywords.value) {
    groups[kw] = newsList.value.filter(n => n.keyword === kw)
  }
  return groups
})

// ─── 주제별 페이지네이션 ──────────────────────────────────────────────────────
const KWITEMS = 6
const kwPages = ref({})

function getPage(kw)  { return kwPages.value[kw] ?? 1 }
function totalPages(kw) {
  return Math.max(1, Math.ceil((byKeyword.value[kw]?.length ?? 0) / KWITEMS))
}
function pagedItems(kw) {
  const p = getPage(kw)
  return (byKeyword.value[kw] ?? []).slice((p - 1) * KWITEMS, p * KWITEMS)
}
function prevPage(kw) { if (getPage(kw) > 1) kwPages.value[kw] = getPage(kw) - 1 }
function nextPage(kw) { if (getPage(kw) < totalPages(kw)) kwPages.value[kw] = getPage(kw) + 1 }

function toggleExpandTop(id) {
  expandedTopId.value = expandedTopId.value === id ? null : id
}

// ─── 뉴스 목록 API ─────────────────────────────────────────────────────────────
async function loadNews() {
  loading.value  = true
  errorMsg.value = ''
  try {
    const res = await fetch('/api/news/')
    if (!res.ok) throw new Error(`서버 오류 (${res.status})`)
    newsList.value = await res.json()
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    const qs  = `?keywords=${encodeURIComponent(userKeywords.value.join(','))}`
    const res = await fetch(`/api/news/stats/${qs}`)
    if (res.ok) stats.value = await res.json()
  } catch {}
}

async function startCrawl() {
  if (crawling.value) return
  crawling.value = true
  errorMsg.value = ''
  try {
    const res = await fetch('/api/news/crawl/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keywords: userKeywords.value }),
    })
    if (!res.ok) {
      const ct  = res.headers.get('content-type') || ''
      const msg = ct.includes('json') ? (await res.json()).error : null
      throw new Error(msg || `서버 오류 (${res.status}) — Django 서버가 실행 중인지 확인하세요.`)
    }
    await res.json()
    await Promise.all([loadNews(), loadStats()])
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    crawling.value = false
  }
}

// ─── AI 요약 ──────────────────────────────────────────────────────────────────
async function requestSummary(news) {
  if (summaryState.value[news.id]?.loading) return
  summaryState.value[news.id] = { loading: true, error: '' }
  try {
    const res = await fetch(`/api/news/${news.id}/summarize/`, { method: 'POST' })
    if (!res.ok) {
      const ct  = res.headers.get('content-type') || ''
      const msg = ct.includes('json') ? (await res.json()).error : `서버 오류 (${res.status})`
      throw new Error(msg)
    }
    const data = await res.json()
    const target = newsList.value.find(n => n.id === news.id)
    if (target) target.summary = data.summary
    summaryState.value[news.id] = { loading: false, error: '' }
  } catch (e) {
    summaryState.value[news.id] = { loading: false, error: e.message }
  }
}

// ─── 유틸 ────────────────────────────────────────────────────────────────────
function fmtDate(iso) {
  if (!iso) return '날짜 없음'
  return new Date(iso).toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })
}

const KW_COLORS = [
  'bg-orange-100 text-orange-700 border-orange-200',
  'bg-red-100 text-red-700 border-red-200',
  'bg-blue-100 text-blue-700 border-blue-200',
]
function keywordColor(kw) {
  const idx = userKeywords.value.indexOf(kw)
  return KW_COLORS[idx >= 0 ? idx % KW_COLORS.length : 0]
}

const KW_SECTION_COLORS = [
  { border: 'border-orange-300', bg: 'bg-orange-500', text: 'text-orange-700', light: 'bg-orange-50' },
  { border: 'border-red-300',    bg: 'bg-red-500',    text: 'text-red-700',    light: 'bg-red-50'    },
  { border: 'border-blue-300',   bg: 'bg-blue-500',   text: 'text-blue-700',   light: 'bg-blue-50'   },
]
function sectionColor(kw) {
  const idx = userKeywords.value.indexOf(kw)
  return KW_SECTION_COLORS[idx >= 0 ? idx % KW_SECTION_COLORS.length : 0]
}

const TOP_STYLES = [
  { outer: 'border-amber-200 bg-gradient-to-b from-amber-50 to-white', badge: 'bg-amber-500 text-white', sep: 'border-amber-100' },
  { outer: 'border-slate-200 bg-gradient-to-b from-slate-50 to-white', badge: 'bg-slate-500 text-white', sep: 'border-slate-100' },
  { outer: 'border-orange-200 bg-gradient-to-b from-orange-50 to-white', badge: 'bg-orange-400 text-white', sep: 'border-orange-100' },
]
const TOP_RANKS = ['1위', '2위', '3위']

onMounted(() => { loadNews(); loadStats() })
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <NavBar />

    <main class="max-w-5xl mx-auto px-4 sm:px-6 pt-24 pb-20">

      <!-- ─── 헤더 ───────────────────────────────────────────────────────── -->
      <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-6">
        <div>
          <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-blue-100 mb-3">
            <Newspaper class="w-7 h-7 text-blue-700" />
          </div>
          <h1 class="text-3xl font-black text-gray-900">뉴스</h1>
          <p class="text-gray-500 text-sm mt-1">
            네이버 뉴스에서 수집한 최신 이슈 ({{ userKeywords.join(' · ') }})
          </p>
        </div>

        <div class="flex flex-col items-end gap-2">
          <div class="flex flex-wrap gap-2 text-sm justify-end">
            <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-slate-100 text-gray-600">
              전체 <strong class="text-gray-800">{{ stats.total }}</strong>건
            </span>
            <span
              v-for="(kw, i) in userKeywords" :key="kw"
              class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-sm font-medium"
              :class="i === 0 ? 'bg-orange-50 text-orange-700' : i === 1 ? 'bg-red-50 text-red-700' : 'bg-blue-50 text-blue-700'"
            >
              {{ kw }} <strong>{{ stats[kw] ?? 0 }}</strong>건
            </span>
          </div>
          <button
            @click="startCrawl"
            :disabled="crawling"
            class="flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm transition-all shadow-sm"
            :class="crawling ? 'bg-gray-200 text-gray-400 cursor-not-allowed' : 'bg-gradient-to-r from-blue-900 to-blue-600 text-white hover:from-blue-950 hover:to-blue-700'"
          >
            <Loader2 v-if="crawling" class="w-4 h-4 animate-spin" />
            <DatabaseZap v-else class="w-4 h-4" />
            {{ crawling ? '크롤링 중... (최대 1분 소요)' : '뉴스 크롤링' }}
          </button>
        </div>
      </div>

        <!-- 오류 배너 -->
        <div v-if="errorMsg"
          class="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-xl mb-5 text-red-700 text-sm"
        >
          <AlertTriangle class="w-5 h-5 flex-shrink-0" />{{ errorMsg }}
        </div>

        <!-- 키워드 관리 버튼 -->
        <div class="flex justify-end mb-4">
          <button
            @click="kwPanelOpen = !kwPanelOpen"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold border transition-all"
            :class="kwPanelOpen ? 'border-blue-300 bg-blue-50 text-blue-700' : 'border-gray-200 bg-white text-gray-500 hover:border-blue-200 hover:text-blue-600'"
          >
            <Search class="w-3.5 h-3.5" />키워드 설정
          </button>
        </div>

        <!-- 키워드 관리 패널 -->
        <div v-if="kwPanelOpen"
          class="bg-white border border-blue-100 rounded-2xl shadow-sm p-4 mb-5 space-y-3"
        >
          <div class="flex items-center justify-between">
            <p class="text-sm font-bold text-gray-800">
              크롤링 키워드 설정
              <span class="ml-1.5 text-xs font-normal text-gray-400">(최대 {{ MAX_KWS }}개)</span>
            </p>
            <button @click="resetKeywords"
              class="text-xs text-gray-400 hover:text-blue-600 transition-colors font-medium">기본값 복원</button>
          </div>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="kw in userKeywords" :key="kw"
              class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold border"
              :class="keywordColor(kw)"
            >
              {{ kw }}
              <button @click="removeKeyword(kw)" class="hover:opacity-70 transition-opacity ml-0.5">
                <X class="w-3 h-3" />
              </button>
            </span>
            <span v-if="userKeywords.length === 0" class="text-xs text-gray-400">키워드 없음</span>
          </div>
          <div v-if="userKeywords.length < MAX_KWS" class="flex gap-2">
            <input
              v-model="kwInput"
              @keydown.enter="addKeyword"
              placeholder="새 키워드 입력 후 Enter"
              class="flex-1 text-sm border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
            />
            <button
              @click="addKeyword"
              :disabled="!kwInput.trim() || userKeywords.length >= MAX_KWS"
              class="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white text-sm font-bold rounded-xl transition-all"
            >추가</button>
          </div>
          <p v-else class="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
            최대 {{ MAX_KWS }}개입니다. 기존 키워드를 삭제 후 추가하세요.
          </p>
        </div>

        <!-- 로딩 -->
        <div v-if="loading" class="space-y-6">
          <!-- Top 3 스켈레톤 -->
          <div>
            <div class="h-5 w-36 bg-gray-200 rounded-lg animate-pulse mb-4"></div>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div v-for="i in 3" :key="i" class="h-52 bg-gray-100 rounded-2xl animate-pulse"></div>
            </div>
          </div>
          <!-- 섹션 스켈레톤 -->
          <div v-for="i in 2" :key="i">
            <div class="h-4 w-32 bg-gray-200 rounded-lg animate-pulse mb-4"></div>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              <div v-for="j in 6" :key="j" class="h-28 bg-gray-100 rounded-2xl animate-pulse"></div>
            </div>
          </div>
        </div>

        <!-- 빈 상태 -->
        <div v-else-if="newsList.length === 0" class="text-center py-20 text-gray-400">
          <Newspaper class="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p class="text-sm">저장된 뉴스가 없습니다. 상단 "뉴스 크롤링" 버튼을 눌러 뉴스를 가져오세요.</p>
        </div>

        <template v-else>

          <!-- ── TOP 3 ──────────────────────────────────────────────────── -->
          <section class="mb-10">
            <h2 class="flex items-center gap-2 text-base font-black text-gray-900 mb-4">
              <Crown class="w-5 h-5 text-amber-500" />주목 뉴스 Top 3
            </h2>

            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div
                v-for="(news, idx) in topNews" :key="news.id"
                class="rounded-2xl border shadow-sm overflow-hidden flex flex-col"
                :class="TOP_STYLES[idx].outer"
              >
                <!-- 카드 상단 -->
                <div class="flex items-center gap-2 px-4 pt-4 pb-2">
                  <span class="text-xs font-black px-2.5 py-1 rounded-full" :class="TOP_STYLES[idx].badge">
                    {{ TOP_RANKS[idx] }}
                  </span>
                  <span class="text-xs font-bold px-2 py-0.5 rounded-full border" :class="keywordColor(news.keyword)">
                    {{ news.keyword }}
                  </span>
                  <a
                    :href="news.url" target="_blank" rel="noopener noreferrer"
                    @click.stop
                    class="ml-auto p-1 text-gray-300 hover:text-blue-500 transition-colors"
                  >
                    <ExternalLink class="w-3.5 h-3.5" />
                  </a>
                </div>

                <!-- 제목 / 날짜 -->
                <div class="px-4 pb-3 flex-1 cursor-pointer" @click="toggleExpandTop(news.id)">
                  <h3 class="text-sm font-bold text-gray-900 leading-snug line-clamp-3 mb-2">{{ news.title }}</h3>
                  <p class="text-xs text-gray-400">{{ fmtDate(news.published_date) }}</p>
                </div>

                <!-- 확장 영역 (AI 요약 + 본문) -->
                <div
                  v-if="expandedTopId === news.id"
                  class="px-4 pb-4 border-t space-y-3"
                  :class="TOP_STYLES[idx].sep"
                >
                  <!-- AI 요약 -->
                  <div class="pt-3">
                    <button
                      v-if="!news.summary && !summaryState[news.id]?.loading"
                      @click.stop="requestSummary(news)"
                      class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-violet-600 text-white hover:bg-violet-700 transition-colors"
                    >
                      <Sparkles class="w-3.5 h-3.5" />AI 요약 생성
                    </button>
                    <div v-if="summaryState[news.id]?.loading" class="flex items-center gap-2 text-xs text-indigo-600">
                      <Loader2 class="w-3.5 h-3.5 animate-spin" />요약 생성 중...
                    </div>
                    <p v-if="summaryState[news.id]?.error" class="text-xs text-red-500">
                      {{ summaryState[news.id].error }}
                    </p>
                    <div v-if="news.summary" class="bg-indigo-50 border border-indigo-200 rounded-xl p-3">
                      <p class="text-xs font-bold text-indigo-600 mb-1.5 flex items-center gap-1">
                        <Sparkles class="w-3 h-3" />AI 요약
                      </p>
                      <p class="text-xs text-gray-700 leading-relaxed">{{ news.summary }}</p>
                    </div>
                  </div>

                  <!-- 본문 미리보기 -->
                  <div>
                    <p class="text-xs font-semibold text-gray-400 mb-1 flex items-center gap-1">
                      <BookOpen class="w-3 h-3" />본문
                    </p>
                    <p class="text-xs text-gray-600 leading-relaxed line-clamp-5">
                      {{ news.content || '본문 없음' }}
                    </p>
                  </div>
                </div>

                <!-- 접기/펼치기 버튼 -->
                <button
                  @click="toggleExpandTop(news.id)"
                  class="flex items-center justify-center gap-1 text-xs text-gray-400 hover:text-gray-700 py-2.5 border-t transition-colors"
                  :class="TOP_STYLES[idx].sep"
                >
                  <ChevronUp   v-if="expandedTopId === news.id" class="w-3.5 h-3.5" />
                  <ChevronDown v-else                            class="w-3.5 h-3.5" />
                  {{ expandedTopId === news.id ? '접기' : '자세히 보기' }}
                </button>
              </div>
            </div>
          </section>

          <!-- ── 주제별 섹션 ──────────────────────────────────────────── -->
          <div>
            <!-- 키워드 선택 버튼 -->
            <div class="flex items-center gap-2 mb-5 flex-wrap">
              <button
                v-for="kw in userKeywords" :key="kw"
                @click="activeSection = kw"
                class="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-bold border transition-all"
                :class="activeSection === kw
                  ? [sectionColor(kw).bg, 'text-white border-transparent shadow-sm']
                  : ['bg-white border-gray-200', sectionColor(kw).text, 'hover:border-current']"
              >
                {{ kw }}
                <span class="text-xs font-semibold opacity-70 bg-white/20 px-1.5 py-0.5 rounded-full">
                  {{ byKeyword[kw]?.length ?? 0 }}
                </span>
              </button>
            </div>

            <!-- 선택된 키워드 기사 -->
            <section v-if="activeSection && byKeyword[activeSection]?.length > 0">
              <!-- 섹션 헤더 -->
              <div class="flex items-center gap-3 mb-4">
                <div class="w-1 h-6 rounded-full flex-shrink-0" :class="sectionColor(activeSection).bg"></div>
                <h2 class="text-base font-black text-gray-900">{{ activeSection }} 관련 뉴스</h2>
                <span class="ml-auto text-xs font-semibold text-gray-400">
                  {{ byKeyword[activeSection].length }}건 · {{ getPage(activeSection) }}/{{ totalPages(activeSection) }} 페이지
                </span>
              </div>

              <!-- 기사 그리드 -->
              <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                <div
                  v-for="news in pagedItems(activeSection)" :key="news.id"
                  @click="openModal(news)"
                  class="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 hover:shadow-md hover:border-blue-200 transition-all group flex flex-col gap-2 cursor-pointer"
                >
                  <div class="flex items-start justify-between gap-2">
                    <span class="text-xs font-bold px-2 py-0.5 rounded-full border flex-shrink-0"
                      :class="keywordColor(news.keyword)">{{ news.keyword }}</span>
                    <a :href="news.url" target="_blank" rel="noopener noreferrer" @click.stop
                      class="p-0.5 text-gray-200 hover:text-blue-500 transition-colors flex-shrink-0">
                      <ExternalLink class="w-3.5 h-3.5" />
                    </a>
                  </div>
                  <h3 class="text-sm font-semibold text-gray-900 leading-snug line-clamp-2 flex-1">{{ news.title }}</h3>
                  <p class="text-xs text-gray-400">{{ fmtDate(news.published_date) }}</p>
                </div>
              </div>

              <!-- 페이지네이션 -->
              <div v-if="totalPages(activeSection) > 1" class="flex items-center justify-center gap-2 mt-5">
                <button
                  @click="prevPage(activeSection)"
                  :disabled="getPage(activeSection) <= 1"
                  class="w-8 h-8 flex items-center justify-center rounded-xl border bg-white text-gray-600 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                >
                  <ChevronLeft class="w-4 h-4" />
                </button>
                <div class="flex gap-1">
                  <button
                    v-for="p in totalPages(activeSection)" :key="p"
                    @click="kwPages[activeSection] = p"
                    class="w-8 h-8 flex items-center justify-center rounded-xl text-sm font-bold transition-all"
                    :class="getPage(activeSection) === p
                      ? [sectionColor(activeSection).bg, 'text-white shadow-sm']
                      : 'border bg-white text-gray-500 hover:bg-blue-50 hover:border-blue-200'"
                  >{{ p }}</button>
                </div>
                <button
                  @click="nextPage(activeSection)"
                  :disabled="getPage(activeSection) >= totalPages(activeSection)"
                  class="w-8 h-8 flex items-center justify-center rounded-xl border bg-white text-gray-600 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                >
                  <ChevronRight class="w-4 h-4" />
                </button>
              </div>
            </section>

            <!-- 빈 상태 -->
            <div v-else class="text-center py-12 text-gray-400">
              <Newspaper class="w-10 h-10 mx-auto mb-2 opacity-20" />
              <p class="text-sm">{{ activeSection }} 관련 뉴스가 없습니다.</p>
            </div>
          </div>

        </template>

    </main>
    <AppFooter />
  </div>

  <!-- ── 기사 상세 모달 ───────────────────────────────────────────────── -->
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="selectedNews"
        class="fixed inset-0 z-50 flex items-end sm:items-center justify-center"
        @click.self="closeModal"
      >
        <!-- 배경 블러 -->
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="closeModal"></div>

        <!-- 모달 본체 -->
        <div class="relative bg-white rounded-t-3xl sm:rounded-2xl shadow-2xl w-full sm:max-w-xl max-h-[85vh] flex flex-col overflow-hidden">

          <!-- 헤더 -->
          <div class="flex items-start gap-3 px-5 py-4 border-b border-gray-100 flex-shrink-0">
            <span
              class="text-xs font-bold px-2.5 py-1 rounded-full border flex-shrink-0 mt-0.5"
              :class="keywordColor(selectedNews.keyword)"
            >{{ selectedNews.keyword }}</span>
            <h2 class="flex-1 text-sm font-bold text-gray-900 leading-snug">{{ selectedNews.title }}</h2>
            <button
              @click="closeModal"
              class="flex-shrink-0 p-1 ml-1 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X class="w-5 h-5" />
            </button>
          </div>

          <!-- AI 요약 -->
          <div class="px-5 py-4 border-b border-gray-100 flex-shrink-0 bg-slate-50/60">
            <button
              v-if="!selectedNews.summary && !summaryState[selectedNews.id]?.loading"
              @click="requestSummary(selectedNews)"
              class="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-bold bg-gradient-to-r from-violet-600 to-indigo-500 text-white hover:from-violet-700 hover:to-indigo-600 transition-all shadow-sm"
            >
              <Sparkles class="w-4 h-4" />AI 요약 생성
            </button>
            <div v-if="summaryState[selectedNews.id]?.loading" class="flex items-center gap-2 text-sm text-indigo-600">
              <Loader2 class="w-4 h-4 animate-spin" />요약 생성 중...
            </div>
            <p v-if="summaryState[selectedNews.id]?.error" class="text-xs text-red-500 mt-1">
              {{ summaryState[selectedNews.id].error }}
            </p>
            <div v-if="selectedNews.summary" class="bg-indigo-50 border border-indigo-200 rounded-xl p-4">
              <p class="text-xs font-bold text-indigo-600 mb-2 flex items-center gap-1">
                <Sparkles class="w-3.5 h-3.5" />AI 요약
              </p>
              <p class="text-sm text-gray-700 leading-relaxed">{{ selectedNews.summary }}</p>
            </div>
          </div>

          <!-- 본문 스크롤 영역 -->
          <div class="flex-1 overflow-y-auto px-5 py-4">
            <p class="text-xs font-semibold text-gray-400 mb-2 flex items-center gap-1">
              <BookOpen class="w-3.5 h-3.5" />본문
            </p>
            <p class="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">
              {{ selectedNews.content || '본문 내용이 없습니다.' }}
            </p>
          </div>

          <!-- 푸터 -->
          <div class="flex items-center justify-between px-5 py-4 border-t border-gray-100 flex-shrink-0">
            <p class="text-xs text-gray-400">{{ fmtDate(selectedNews.published_date) }}</p>
            <a
              :href="selectedNews.url" target="_blank" rel="noopener noreferrer"
              class="flex items-center gap-1.5 text-sm font-bold text-blue-600 hover:text-blue-800 transition-colors"
            >
              <ExternalLink class="w-4 h-4" />원문 기사 읽기
            </a>
          </div>

        </div>
      </div>
    </Transition>
  </Teleport>
</template>
