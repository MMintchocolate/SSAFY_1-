<script setup>
import { ref, computed, onMounted } from 'vue'
import NavBar from '@/components/NavBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import { Scatter } from 'vue-chartjs'
import {
  Chart as ChartJS,
  LinearScale, PointElement, Tooltip, Legend,
} from 'chart.js'
import {
  Newspaper, ExternalLink, ChevronDown, ChevronUp,
  Loader2, AlertTriangle, DatabaseZap, Search,
  Layers, TrendingUp, CircleDot, Sparkles, BookOpen,
} from '@lucide/vue'

ChartJS.register(LinearScale, PointElement, Tooltip, Legend)

// ─── 페이지 탭 ─────────────────────────────────────────────────────────────────
const PAGE_TABS = [
  { key: 'list',    label: '뉴스 목록' },
  { key: 'cluster', label: '군집 분석' },
]
const pageTab = ref('list')

// ─── 요약 상태 (id → { loading, error }) ────────────────────────────────────
const summaryState = ref({})   // { [newsId]: { loading: bool, error: str } }

// ─── 뉴스 목록 상태 ────────────────────────────────────────────────────────────
const KEYWORD_TABS = [
  { key: '',    label: '전체' },
  { key: '유출', label: '유출' },
  { key: '해킹', label: '해킹' },
]
const activeKeyword = ref('')
const newsList      = ref([])
const stats         = ref({ total: 0, 유출: 0, 해킹: 0 })
const loading       = ref(false)
const crawling      = ref(false)
const errorMsg      = ref('')
const expandedId    = ref(null)
const searchQ       = ref('')

// ─── 군집 분석 상태 ────────────────────────────────────────────────────────────
const clusterKeyword  = ref('')
const clusterResult   = ref(null)
const clusterLoading  = ref(false)
const clusterError    = ref('')
const clusterEps      = ref(0.45)
const clusterMinSamp  = ref(2)

// ─── 뉴스 목록 API ─────────────────────────────────────────────────────────────
async function loadNews() {
  loading.value  = true
  errorMsg.value = ''
  try {
    const qs  = activeKeyword.value ? `?keyword=${encodeURIComponent(activeKeyword.value)}` : ''
    const res = await fetch(`/api/news/${qs}`)
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
    const res = await fetch('/api/news/stats/')
    if (res.ok) stats.value = await res.json()
  } catch {}
}

async function startCrawl() {
  if (crawling.value) return
  crawling.value = true
  errorMsg.value = ''
  try {
    const res = await fetch('/api/news/crawl/', { method: 'POST' })
    if (!res.ok) {
      const ct   = res.headers.get('content-type') || ''
      const msg  = ct.includes('json') ? (await res.json()).error : null
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

async function setKeywordTab(key) {
  activeKeyword.value = key
  expandedId.value    = null
  await loadNews()
}

function toggleExpand(id) {
  expandedId.value = expandedId.value === id ? null : id
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
    // newsList에서 해당 항목의 summary 업데이트
    const target = newsList.value.find(n => n.id === news.id)
    if (target) target.summary = data.summary
    summaryState.value[news.id] = { loading: false, error: '' }
  } catch (e) {
    summaryState.value[news.id] = { loading: false, error: e.message }
  }
}

const filtered = computed(() => {
  const q = searchQ.value.trim().toLowerCase()
  if (!q) return newsList.value
  return newsList.value.filter(
    n => n.title.toLowerCase().includes(q) || n.content.toLowerCase().includes(q)
  )
})

// ─── 군집 분석 API ─────────────────────────────────────────────────────────────
async function runCluster() {
  clusterLoading.value = true
  clusterError.value   = ''
  clusterResult.value  = null
  try {
    const params = new URLSearchParams({
      eps:         clusterEps.value,
      min_samples: clusterMinSamp.value,
    })
    if (clusterKeyword.value) params.set('keyword', clusterKeyword.value)
    const res  = await fetch(`/api/news/cluster/?${params}`)
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || '군집화 실패')
    clusterResult.value = data
  } catch (e) {
    clusterError.value = e.message
  } finally {
    clusterLoading.value = false
  }
}

// ─── Scatter 차트 데이터 ──────────────────────────────────────────────────────
const scatterData = computed(() => {
  if (!clusterResult.value) return { datasets: [] }

  const byCluster = {}
  for (const p of clusterResult.value.points) {
    const key = p.cluster
    if (!byCluster[key]) {
      byCluster[key] = {
        label:           key < 0 ? '노이즈' : `군집 ${key}`,
        data:            [],
        backgroundColor: p.color + 'cc',
        borderColor:     p.color,
        pointRadius:     key < 0 ? 4 : 6,
        pointHoverRadius: 8,
      }
    }
    byCluster[key].data.push({ x: p.x, y: p.y, title: p.title, keyword: p.keyword })
  }

  // 노이즈(-1) 를 맨 마지막으로
  const ordered = Object.entries(byCluster)
    .sort(([a], [b]) => Number(a) - Number(b))
    .map(([, ds]) => ds)
  const noiseIdx = ordered.findIndex(d => d.label === '노이즈')
  if (noiseIdx > -1) ordered.push(ordered.splice(noiseIdx, 1)[0])

  return { datasets: ordered }
})

const scatterOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: { boxWidth: 12, font: { size: 11 } },
    },
    tooltip: {
      callbacks: {
        label: (ctx) => {
          const { title, keyword } = ctx.raw
          return [`[${keyword}] ${title.length > 50 ? title.slice(0, 50) + '…' : title}`]
        },
      },
    },
  },
  scales: {
    x: { display: false },
    y: { display: false },
  },
}

// ─── 공통 유틸 ────────────────────────────────────────────────────────────────
function fmtDate(iso) {
  if (!iso) return '날짜 없음'
  return new Date(iso).toLocaleDateString('ko-KR', {
    year: 'numeric', month: 'long', day: 'numeric',
  })
}

function keywordColor(kw) {
  return kw === '유출'
    ? 'bg-orange-100 text-orange-700 border-orange-200'
    : 'bg-red-100 text-red-700 border-red-200'
}

const RANK_LABELS = ['1위', '2위', '3위']
const RANK_STYLES = [
  'from-blue-50 border-blue-200',
  'from-emerald-50 border-emerald-200',
  'from-amber-50 border-amber-200',
]
const RANK_BADGE  = [
  'bg-blue-600 text-white',
  'bg-emerald-600 text-white',
  'bg-amber-500 text-white',
]

onMounted(() => {
  loadNews()
  loadStats()
})
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <NavBar />

    <main class="max-w-5xl mx-auto px-4 sm:px-6 pt-24 pb-20">

      <!-- ─── 헤더 ────────────────────────────────────────────────────────── -->
      <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-6">
        <div>
          <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-blue-100 mb-3">
            <Newspaper class="w-7 h-7 text-blue-700" />
          </div>
          <h1 class="text-3xl font-black text-gray-900">보안 뉴스</h1>
          <p class="text-gray-500 text-sm mt-1">네이버 뉴스에서 수집한 최신 보안 이슈 (유출 · 해킹)</p>
        </div>

        <div class="flex flex-col items-end gap-2">
          <div class="flex gap-2 text-sm">
            <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-slate-100 text-gray-600">
              전체 <strong class="text-gray-800">{{ stats.total }}</strong>건
            </span>
            <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-orange-50 text-orange-700">
              유출 <strong>{{ stats['유출'] }}</strong>건
            </span>
            <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-red-50 text-red-700">
              해킹 <strong>{{ stats['해킹'] }}</strong>건
            </span>
          </div>
          <button
            @click="startCrawl"
            :disabled="crawling"
            class="flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm transition-all shadow-sm"
            :class="crawling
              ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-blue-900 to-blue-600 text-white hover:from-blue-950 hover:to-blue-700'"
          >
            <Loader2 v-if="crawling" class="w-4 h-4 animate-spin" />
            <DatabaseZap v-else class="w-4 h-4" />
            {{ crawling ? '크롤링 중... (최대 1분 소요)' : '뉴스 크롤링' }}
          </button>
        </div>
      </div>

      <!-- ─── 페이지 탭 ──────────────────────────────────────────────────── -->
      <div class="flex gap-1 p-1 bg-white border border-gray-200 rounded-xl shadow-sm mb-6 w-fit">
        <button
          v-for="tab in PAGE_TABS" :key="tab.key"
          @click="pageTab = tab.key"
          class="flex items-center gap-1.5 px-5 py-2 rounded-lg text-sm font-semibold transition-all"
          :class="pageTab === tab.key
            ? 'bg-blue-700 text-white shadow'
            : 'text-gray-600 hover:bg-gray-100'"
        >
          <Newspaper v-if="tab.key === 'list'"    class="w-4 h-4" />
          <Layers    v-if="tab.key === 'cluster'" class="w-4 h-4" />
          {{ tab.label }}
        </button>
      </div>

      <!-- ═══════════════════════════════════════════════════════════════════ -->
      <!--  뉴스 목록 탭                                                       -->
      <!-- ═══════════════════════════════════════════════════════════════════ -->
      <template v-if="pageTab === 'list'">

        <!-- 오류 배너 -->
        <div v-if="errorMsg"
          class="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-xl mb-5 text-red-700 text-sm"
        >
          <AlertTriangle class="w-5 h-5 flex-shrink-0" />{{ errorMsg }}
        </div>

        <!-- 키워드 탭 + 검색 -->
        <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-5">
          <div class="flex gap-1 p-1 bg-white border border-gray-200 rounded-xl shadow-sm">
            <button
              v-for="tab in KEYWORD_TABS" :key="tab.key"
              @click="setKeywordTab(tab.key)"
              class="px-4 py-1.5 rounded-lg text-sm font-semibold transition-all"
              :class="activeKeyword === tab.key
                ? 'bg-blue-700 text-white shadow'
                : 'text-gray-600 hover:bg-gray-100'"
            >{{ tab.label }}</button>
          </div>
          <div class="relative w-full sm:w-64">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input v-model="searchQ" type="text" placeholder="제목 / 본문 검색..."
              class="w-full pl-9 pr-4 py-2 text-sm rounded-xl border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-blue-300"
            />
          </div>
        </div>

        <!-- 로딩 -->
        <div v-if="loading" class="flex justify-center py-20">
          <Loader2 class="w-8 h-8 animate-spin text-blue-500" />
        </div>

        <!-- 빈 상태 -->
        <div v-else-if="filtered.length === 0" class="text-center py-20 text-gray-400">
          <Newspaper class="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p class="text-sm">
            {{ newsList.length === 0
              ? '저장된 뉴스가 없습니다. 상단 "뉴스 크롤링" 버튼을 눌러 뉴스를 가져오세요.'
              : '검색 결과가 없습니다.' }}
          </p>
        </div>

        <!-- 뉴스 카드 -->
        <div v-else class="space-y-3">
          <div
            v-for="news in filtered" :key="news.id"
            class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden hover:shadow-md transition-shadow"
          >
            <div class="flex items-start gap-4 p-5 cursor-pointer" @click="toggleExpand(news.id)">
              <span class="flex-shrink-0 text-xs font-bold px-2.5 py-1 rounded-full border"
                :class="keywordColor(news.keyword)"
              >{{ news.keyword }}</span>
              <div class="flex-1 min-w-0">
                <h2 class="text-base font-bold text-gray-900 leading-snug line-clamp-2 mb-1">{{ news.title }}</h2>
                <p class="text-xs text-gray-400">{{ fmtDate(news.published_date) }}</p>
              </div>
              <div class="flex-shrink-0 flex items-center gap-2">
                <a :href="news.url" target="_blank" rel="noopener noreferrer" @click.stop
                  class="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                ><ExternalLink class="w-4 h-4" /></a>
                <ChevronUp   v-if="expandedId === news.id" class="w-4 h-4 text-gray-400" />
                <ChevronDown v-else                        class="w-4 h-4 text-gray-400" />
              </div>
            </div>
            <div v-if="expandedId === news.id" class="px-5 pb-5 border-t border-gray-100">

              <!-- AI 요약 영역 -->
              <div class="mt-4">
                <!-- 요약 없을 때: 버튼 -->
                <button v-if="!news.summary && !summaryState[news.id]?.loading"
                  @click.stop="requestSummary(news)"
                  class="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold bg-gradient-to-r from-violet-600 to-indigo-500 text-white hover:from-violet-700 hover:to-indigo-600 transition-all shadow-sm"
                >
                  <Sparkles class="w-4 h-4" />AI 요약 생성
                </button>

                <!-- 로딩 -->
                <div v-if="summaryState[news.id]?.loading"
                  class="flex items-center gap-2 text-sm text-indigo-600"
                >
                  <Loader2 class="w-4 h-4 animate-spin" />요약 생성 중...
                </div>

                <!-- 요약 오류 -->
                <p v-if="summaryState[news.id]?.error"
                  class="text-xs text-red-500 mt-1"
                >{{ summaryState[news.id].error }}</p>

                <!-- 요약 결과 -->
                <div v-if="news.summary"
                  class="bg-indigo-50 border border-indigo-200 rounded-xl p-4"
                >
                  <p class="text-xs font-bold text-indigo-600 mb-2 flex items-center gap-1">
                    <Sparkles class="w-3.5 h-3.5" />AI 요약
                  </p>
                  <p class="text-sm text-gray-700 leading-relaxed">{{ news.summary }}</p>
                </div>
              </div>

              <!-- 본문 -->
              <div class="mt-4">
                <p class="text-xs font-semibold text-gray-400 mb-2 flex items-center gap-1">
                  <BookOpen class="w-3.5 h-3.5" />본문
                </p>
                <p class="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap max-h-72 overflow-y-auto">
                  {{ news.content || '본문 내용이 없습니다.' }}
                </p>
              </div>

              <div class="mt-4 flex justify-end">
                <a :href="news.url" target="_blank" rel="noopener noreferrer"
                  class="flex items-center gap-1.5 text-sm font-semibold text-blue-600 hover:text-blue-800 transition-colors"
                ><ExternalLink class="w-4 h-4" />원문 기사 읽기</a>
              </div>
            </div>
          </div>
        </div>

        <p v-if="!loading && filtered.length > 0" class="text-center text-xs text-gray-400 mt-6">
          총 {{ filtered.length }}건 {{ searchQ ? `(검색: "${searchQ}")` : '' }}
        </p>
      </template>

      <!-- ═══════════════════════════════════════════════════════════════════ -->
      <!--  군집 분석 탭                                                       -->
      <!-- ═══════════════════════════════════════════════════════════════════ -->
      <template v-else>

        <!-- 컨트롤 패널 -->
        <div class="bg-white border border-gray-200 rounded-2xl shadow-sm p-5 mb-6">
          <div class="flex flex-wrap items-end gap-4">
            <!-- 키워드 필터 -->
            <div>
              <label class="block text-xs font-semibold text-gray-500 mb-1.5">대상 키워드</label>
              <div class="flex gap-1">
                <button
                  v-for="tab in KEYWORD_TABS" :key="tab.key"
                  @click="clusterKeyword = tab.key"
                  class="px-3.5 py-1.5 rounded-lg text-sm font-semibold transition-all border"
                  :class="clusterKeyword === tab.key
                    ? 'bg-blue-700 text-white border-blue-700'
                    : 'text-gray-600 border-gray-200 hover:bg-gray-50'"
                >{{ tab.label || '전체' }}</button>
              </div>
            </div>

            <!-- eps -->
            <div>
              <label class="block text-xs font-semibold text-gray-500 mb-1.5">
                eps (반경) &nbsp;<span class="text-blue-600 font-bold">{{ clusterEps }}</span>
              </label>
              <input type="range" v-model.number="clusterEps" min="0.1" max="0.9" step="0.05"
                class="w-32 accent-blue-600"
              />
            </div>

            <!-- min_samples -->
            <div>
              <label class="block text-xs font-semibold text-gray-500 mb-1.5">
                min_samples &nbsp;<span class="text-blue-600 font-bold">{{ clusterMinSamp }}</span>
              </label>
              <input type="range" v-model.number="clusterMinSamp" min="2" max="10" step="1"
                class="w-32 accent-blue-600"
              />
            </div>

            <!-- 실행 버튼 -->
            <button
              @click="runCluster"
              :disabled="clusterLoading"
              class="flex items-center gap-2 px-6 py-2.5 rounded-xl font-bold text-sm transition-all shadow-sm ml-auto"
              :class="clusterLoading
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-indigo-700 to-blue-600 text-white hover:from-indigo-800 hover:to-blue-700'"
            >
              <Loader2 v-if="clusterLoading" class="w-4 h-4 animate-spin" />
              <Layers  v-else                class="w-4 h-4" />
              {{ clusterLoading ? '분석 중...' : '군집 분석 실행' }}
            </button>
          </div>

          <p class="text-xs text-gray-400 mt-3">
            TF-IDF (음절 n-gram) + DBSCAN(cosine) + TruncatedSVD 2D 시각화.
            eps가 작을수록 더 세밀하게 분리됩니다.
          </p>
        </div>

        <!-- 오류 -->
        <div v-if="clusterError"
          class="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-xl mb-5 text-red-700 text-sm"
        >
          <AlertTriangle class="w-5 h-5 flex-shrink-0" />{{ clusterError }}
        </div>

        <!-- 로딩 -->
        <div v-if="clusterLoading" class="flex flex-col items-center justify-center py-24 gap-3">
          <Loader2 class="w-9 h-9 animate-spin text-indigo-500" />
          <p class="text-sm text-gray-500">군집 분석 중입니다...</p>
        </div>

        <!-- 결과 없음 -->
        <div v-else-if="!clusterResult && !clusterError" class="text-center py-24 text-gray-400">
          <Layers class="w-12 h-12 mx-auto mb-3 opacity-25" />
          <p class="text-sm">군집 분석 실행 버튼을 눌러 시작하세요.</p>
          <p class="text-xs mt-1">뉴스를 먼저 크롤링해야 합니다.</p>
        </div>

        <!-- 분석 결과 -->
        <template v-else-if="clusterResult">

          <!-- 요약 통계 -->
          <div class="grid grid-cols-3 gap-4 mb-6">
            <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 text-center">
              <p class="text-2xl font-black text-gray-900">{{ clusterResult.total }}</p>
              <p class="text-xs text-gray-500 mt-0.5">분석 기사</p>
            </div>
            <div class="bg-white rounded-2xl border border-indigo-100 shadow-sm p-4 text-center">
              <p class="text-2xl font-black text-indigo-700">{{ clusterResult.n_clusters }}</p>
              <p class="text-xs text-gray-500 mt-0.5">발견된 군집</p>
            </div>
            <div class="bg-white rounded-2xl border border-slate-100 shadow-sm p-4 text-center">
              <p class="text-2xl font-black text-slate-500">{{ clusterResult.noise_count }}</p>
              <p class="text-xs text-gray-500 mt-0.5">노이즈 (미분류)</p>
            </div>
          </div>

          <!-- Scatter 차트 -->
          <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 mb-6">
            <h2 class="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
              <CircleDot class="w-4 h-4 text-indigo-500" />
              군집 분포 시각화 &nbsp;
              <span class="text-xs font-normal text-gray-400">(각 점 = 기사 1건, 색상 = 군집)</span>
            </h2>
            <div class="h-80">
              <Scatter :data="scatterData" :options="scatterOptions" />
            </div>
          </div>

          <!-- Top-3 군집 카드 -->
          <div v-if="clusterResult.clusters.length" class="mb-4">
            <h2 class="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
              <TrendingUp class="w-4 h-4 text-blue-500" />
              가장 많이 등장한 뉴스 주제 Top {{ clusterResult.clusters.length }}
            </h2>
            <div class="grid gap-4">
              <div
                v-for="(cl, idx) in clusterResult.clusters" :key="cl.id"
                class="bg-gradient-to-r border rounded-2xl shadow-sm overflow-hidden"
                :class="RANK_STYLES[idx]"
              >
                <!-- 군집 헤더 -->
                <div class="flex items-center gap-3 px-5 py-3 border-b border-white/60">
                  <span class="text-xs font-black px-2.5 py-1 rounded-full"
                    :class="RANK_BADGE[idx]"
                  >{{ RANK_LABELS[idx] }}</span>
                  <span class="text-sm font-bold text-gray-800">군집 {{ cl.id }}</span>
                  <span class="ml-auto text-xs text-gray-500">기사 {{ cl.size }}건</span>
                  <span class="w-3 h-3 rounded-full flex-shrink-0" :style="{ background: cl.color }"></span>
                </div>

                <!-- 대표 기사 목록 -->
                <ul class="divide-y divide-white/50">
                  <li
                    v-for="article in cl.articles" :key="article.id"
                    class="flex items-start gap-3 px-5 py-3 hover:bg-white/40 transition-colors"
                  >
                    <span class="flex-shrink-0 text-xs font-bold px-2 py-0.5 rounded-full border mt-0.5"
                      :class="keywordColor(article.keyword)"
                    >{{ article.keyword }}</span>
                    <div class="flex-1 min-w-0">
                      <a :href="article.url" target="_blank" rel="noopener noreferrer"
                        class="text-sm font-medium text-gray-800 hover:text-blue-700 leading-snug line-clamp-2 transition-colors"
                      >{{ article.title }}</a>
                      <p class="text-xs text-gray-400 mt-0.5">{{ fmtDate(article.published_date) }}</p>
                    </div>
                    <a :href="article.url" target="_blank" rel="noopener noreferrer"
                      class="flex-shrink-0 p-1 text-gray-400 hover:text-blue-600 transition-colors mt-0.5"
                    ><ExternalLink class="w-3.5 h-3.5" /></a>
                  </li>
                </ul>
              </div>
            </div>
          </div>

        </template>
      </template>

    </main>
    <AppFooter />
  </div>
</template>
