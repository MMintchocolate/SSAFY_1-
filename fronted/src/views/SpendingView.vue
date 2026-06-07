<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import NavBar from '@/components/NavBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import { Bar, Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, BarElement,
  ArcElement, Title, Tooltip, Legend,
} from 'chart.js'
import { TrendingUp, CloudUpload, CircleCheck, CircleAlert, Search, ChevronDown, ChevronRight, Sparkles } from '@lucide/vue'
import { useAuth } from '@/composables/useAuth'

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend)

const { authFetch } = useAuth()

// ── 기간 토글 ─────────────────────────────────────────────────────────────
const PERIODS = [
  { key: 'this_week',    label: '이번 주' },
  { key: 'this_month',   label: '이번 달' },
  { key: 'last_month',   label: '지난 달' },
  { key: 'last_3months', label: '최근 3개월' },
  { key: 'custom',       label: '직접 설정' },
]
const period      = ref('this_month')
const customStart = ref('')
const customEnd   = ref('')
const isCustom    = computed(() => period.value === 'custom')

// ── 입금/출금 방향 ────────────────────────────────────────────────────────
const DIRECTIONS = [
  { key: 'out', label: '지출 (출금)', color: 'rose' },
  { key: 'in',  label: '수입 (입금)', color: 'emerald' },
]
const direction = ref('out')
const isOut     = computed(() => direction.value === 'out')

// ── 데이터 ────────────────────────────────────────────────────────────────
const loading = ref(false)
const stats   = ref(null)
const error   = ref(null)

async function fetchStats() {
  if (isCustom.value && (!customStart.value || !customEnd.value)) return
  loading.value = true; error.value = null
  const params = new URLSearchParams({ direction: direction.value })
  if (isCustom.value) {
    params.set('start', customStart.value)
    params.set('end',   customEnd.value)
  } else {
    params.set('period', period.value)
  }
  try {
    const res  = await authFetch(`/api/spending/stats/?${params}`)
    const json = await res.json()
    if (!res.ok) throw new Error(json.error ?? `HTTP ${res.status}`)
    stats.value = json
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
}

// ── 카테고리 상세 아코디언 ────────────────────────────────────────────────
const expandedCategory = ref(null)
function toggleCategory(cat) {
  expandedCategory.value = expandedCategory.value === cat ? null : cat
}

// ── AI 자동 분류 ──────────────────────────────────────────────────────────
const classifying   = ref(false)
const classifyMsg   = ref(null)
const classifyErr   = ref(null)
const savedMapSize  = ref(0)

async function fetchMapStatus() {
  try {
    const res  = await authFetch('/api/spending/map-status/')
    const json = await res.json()
    if (res.ok) savedMapSize.value = json.saved_map_size ?? 0
  } catch {}
}

async function classifyMisc(onlySaved = false) {
  classifying.value = true; classifyMsg.value = null; classifyErr.value = null
  try {
    const res  = await authFetch('/api/spending/classify-misc/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ only_saved: onlySaved }),
    })
    const json = await res.json()
    if (!res.ok) throw new Error(json.error ?? `HTTP ${res.status}`)

    if (json.message) {
      classifyMsg.value = json.message
    } else if (onlySaved) {
      classifyMsg.value = `저장된 분류 ${json.count}개 적용 완료`
    } else {
      classifyMsg.value = `총 ${json.count}개 분류 완료 (저장분 ${json.from_saved ?? 0} + AI신규 ${json.from_ai ?? 0}개, Gemini 요청 ${json.asked_gemini ?? 0}건)`
    }
    savedMapSize.value = json.saved_map_size ?? savedMapSize.value
    await fetchStats()
    expandedCategory.value = '기타'
  } catch (e) { classifyErr.value = e.message }
  finally { classifying.value = false }
}

onMounted(fetchMapStatus)

watch(period,    () => { if (!isCustom.value) fetchStats() })
watch(direction, fetchStats)
onMounted(fetchStats)

// ── CSV 업로드 ────────────────────────────────────────────────────────────
const uploading = ref(false)
const uploadMsg = ref(null)
const uploadErr = ref(null)

async function onCsvUpload(e) {
  const file = e.target.files[0]
  if (!file) return
  uploading.value = true; uploadMsg.value = null; uploadErr.value = null
  const form = new FormData()
  form.append('file', file)
  try {
    const res  = await authFetch('/api/spending/upload/', { method: 'POST', body: form })
    const json = await res.json()
    if (!res.ok) throw new Error(json.error ?? `HTTP ${res.status}`)
    uploadMsg.value = `${json.rows.toLocaleString()}건 로드 완료 (저장된 분류 ${json.saved_map_size ?? 0}개 자동 적용)`
    savedMapSize.value = json.saved_map_size ?? savedMapSize.value
    await fetchStats()
  } catch (e) { uploadErr.value = e.message }
  finally { uploading.value = false; e.target.value = '' }
}

// ── 포맷 유틸 ────────────────────────────────────────────────────────────
const fmt  = (n) => (n ?? 0).toLocaleString('ko-KR')
const fmtW = (n) => n >= 10000 ? `${(n / 10000).toFixed(1)}만` : fmt(n)

// ── 색상 (카테고리별 구분이 명확하도록 고채도 팔레트) ─────────────────────
const COLORS = [
  '#6366f1', // indigo
  '#f43f5e', // rose
  '#f59e0b', // amber
  '#10b981', // emerald
  '#3b82f6', // blue
  '#a855f7', // purple
  '#ef4444', // red
  '#14b8a6', // teal
  '#f97316', // orange
  '#84cc16', // lime
  '#ec4899', // pink
  '#06b6d4', // cyan
]

// ── 막대그래프 ────────────────────────────────────────────────────────────
const barData = computed(() => {
  if (!stats.value) return { labels: [], datasets: [] }
  const rows = period.value === 'last_3months'
    ? stats.value.monthly
    : stats.value.daily
  const labelFn = period.value === 'last_3months'
    ? r => r.label
    : r => r.date.slice(5)
  return {
    labels: rows.map(labelFn),
    datasets: [{
      label: isOut.value ? '지출 (원)' : '수입 (원)',
      data: rows.map(r => r.amount),
      backgroundColor: isOut.value ? 'rgba(244,63,94,0.8)' : 'rgba(16,185,129,0.8)',
      borderRadius: 5,
      borderSkipped: false,
    }],
  }
})

const barOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: { callbacks: { label: ctx => `${ctx.raw.toLocaleString()}원` } },
  },
  scales: {
    y: {
      ticks: { callback: v => fmtW(v) },
      grid: { color: '#f3f4f6' },
    },
    x: {
      ticks: { maxRotation: 45, font: { size: 11 } },
      grid: { display: false },
    },
  },
}))

// ── 도넛 차트 ─────────────────────────────────────────────────────────────
const donutData = computed(() => {
  const cats = stats.value?.by_category ?? []
  return {
    labels: cats.map(c => c.category),
    datasets: [{
      data: cats.map(c => c.amount),
      backgroundColor: cats.map((_, i) => COLORS[i % COLORS.length]),
      borderWidth: 2,
      borderColor: '#fff',
      hoverOffset: 8,
    }],
  }
})

const donutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'right',
      labels: { font: { size: 12 }, padding: 14, usePointStyle: true, pointStyleWidth: 10 },
    },
    tooltip: {
      callbacks: {
        label: ctx => {
          const total = ctx.dataset.data.reduce((a, b) => a + b, 0)
          const pct   = total > 0 ? ((ctx.raw / total) * 100).toFixed(1) : 0
          return `${ctx.label}: ${ctx.raw.toLocaleString()}원 (${pct}%)`
        },
      },
    },
  },
}

// ── 달력 히트맵 ──────────────────────────────────────────────────────────
const DAY_KO = ['일', '월', '화', '수', '목', '금', '토']

const heatmap = computed(() => {
  const daily = stats.value?.daily ?? []
  if (!daily.length) return null

  // 히트맵을 표시할 연/월 결정
  let year, month
  if (period.value === 'this_month') {
    const t = new Date(); year = t.getFullYear(); month = t.getMonth()
  } else if (period.value === 'last_month') {
    const t = new Date(new Date().getFullYear(), new Date().getMonth() - 1, 1)
    year = t.getFullYear(); month = t.getMonth()
  } else if (period.value === 'custom' && customStart.value && customEnd.value) {
    // 커스텀: 시작 ~ 종료가 같은 달이면 표시
    const s = new Date(customStart.value), e = new Date(customEnd.value)
    if (s.getFullYear() !== e.getFullYear() || s.getMonth() !== e.getMonth()) return null
    year = s.getFullYear(); month = s.getMonth()
  } else {
    return null
  }

  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const firstDow    = new Date(year, month, 1).getDay()

  const amtMap = {}
  for (const d of daily) amtMap[d.date] = d.amount
  const maxAmt = Math.max(...Object.values(amtMap), 1)

  const days = Array.from({ length: daysInMonth }, (_, i) => {
    const d   = i + 1
    const key = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    const amt = amtMap[key] ?? 0
    return { d, key, amt, intensity: amt / maxAmt }
  })

  return { title: `${year}년 ${month + 1}월`, firstDow, days, maxAmt }
})

function heatBg(intensity) {
  if (intensity === 0) return '#f3f4f6'
  const a = (0.15 + intensity * 0.80).toFixed(2)
  return isOut.value ? `rgba(244,63,94,${a})` : `rgba(16,185,129,${a})`
}
function heatText(intensity) { return intensity > 0.5 ? '#fff' : '#374151' }
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <NavBar />
    <main class="pt-24 pb-16 max-w-5xl mx-auto px-4 sm:px-6">

      <!-- 헤더 -->
      <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-6">
        <div>
          <div class="inline-flex items-center gap-2 bg-indigo-50 text-indigo-700 text-xs font-bold px-3 py-1.5 rounded-full mb-3 border border-indigo-100">
            <TrendingUp class="w-3 h-3" />지출 분석
          </div>
          <h1 class="text-3xl font-extrabold text-gray-900">소비 대시보드</h1>
          <p class="text-gray-400 text-sm mt-1">거래 내역 CSV를 업로드하면 자동으로 분석합니다</p>
        </div>

        <!-- CSV 업로드 -->
        <label class="flex items-center gap-2 px-4 py-2.5 rounded-xl border-2 border-dashed border-indigo-300 hover:border-indigo-500 hover:bg-indigo-50 cursor-pointer transition-colors text-sm font-bold text-indigo-600 shrink-0">
          <CloudUpload class="w-4 h-4" />
          {{ uploading ? '분석 중...' : 'CSV 교체' }}
          <input type="file" accept=".csv" class="hidden" :disabled="uploading" @change="onCsvUpload" />
        </label>
      </div>

      <!-- 업로드 결과 -->
      <div v-if="uploadMsg" class="flex items-center gap-2 text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-2.5 mb-4">
        <CircleCheck class="w-4 h-4 shrink-0" />{{ uploadMsg }}
      </div>
      <div v-if="uploadErr" class="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-2.5 mb-4">
        <CircleAlert class="w-4 h-4 shrink-0" />{{ uploadErr }}
      </div>

      <!-- 입금 / 출금 토글 -->
      <div class="flex gap-2 mb-4">
        <button
          v-for="d in DIRECTIONS" :key="d.key"
          @click="direction = d.key"
          class="px-5 py-2 rounded-xl text-sm font-bold border-2 transition-all"
          :class="direction === d.key
            ? d.key === 'out'
              ? 'bg-rose-500 border-rose-500 text-white shadow-md'
              : 'bg-emerald-500 border-emerald-500 text-white shadow-md'
            : 'bg-white border-gray-200 text-gray-500 hover:border-gray-300'"
        >{{ d.label }}</button>
      </div>

      <!-- 기간 토글 + 직접 설정 -->
      <div class="flex flex-wrap items-center gap-3 mb-6">
        <div class="flex gap-1 bg-white border border-gray-200 rounded-xl p-1 shadow-sm">
          <button
            v-for="p in PERIODS" :key="p.key"
            @click="period = p.key"
            class="px-3.5 py-1.5 rounded-lg text-sm font-bold transition-colors"
            :class="period === p.key
              ? 'bg-indigo-600 text-white shadow'
              : 'text-gray-500 hover:text-gray-800'"
          >{{ p.label }}</button>
        </div>

        <!-- 커스텀 날짜 입력 -->
        <Transition name="slide">
          <div v-if="isCustom" class="flex items-center gap-2">
            <input
              type="date" v-model="customStart"
              class="text-sm border border-gray-300 rounded-lg px-3 py-1.5 text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
            <span class="text-gray-400 font-bold">~</span>
            <input
              type="date" v-model="customEnd"
              class="text-sm border border-gray-300 rounded-lg px-3 py-1.5 text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
            <button
              @click="fetchStats"
              :disabled="!customStart || !customEnd"
              class="flex items-center gap-1.5 px-3.5 py-1.5 bg-indigo-600 text-white text-sm font-bold rounded-lg hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <Search class="w-3.5 h-3.5" />조회
            </button>
          </div>
        </Transition>
      </div>

      <!-- 로딩 / 에러 -->
      <div v-if="loading" class="flex justify-center py-20 text-gray-400 text-sm">분석 중...</div>
      <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-2xl p-6 text-red-600 text-sm mb-4">{{ error }}</div>
      <div v-else-if="isCustom && (!customStart || !customEnd)" class="flex justify-center py-16 text-gray-400 text-sm">날짜 범위를 선택하고 조회를 눌러주세요</div>

      <template v-else-if="stats">

        <!-- ── 요약 카드 ── -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
            <p class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">{{ isOut ? '총 지출' : '총 수입' }}</p>
            <p class="text-2xl font-extrabold" :class="isOut ? 'text-rose-600' : 'text-emerald-600'">
              {{ fmt(stats.summary.total) }}<span class="text-base font-bold ml-1">원</span>
            </p>
            <p class="text-xs text-gray-400 mt-1">{{ stats.summary.count }}건 거래</p>
          </div>
          <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
            <p class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">일 평균</p>
            <p class="text-2xl font-extrabold text-gray-800">{{ fmt(stats.summary.daily_avg) }}<span class="text-base font-bold ml-1">원</span></p>
          </div>
          <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
            <p class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">{{ isOut ? '최다 지출일' : '최다 수입일' }}</p>
            <template v-if="stats.summary.max_day">
              <p class="text-2xl font-extrabold text-orange-500">{{ fmt(stats.summary.max_day.amount) }}<span class="text-base font-bold ml-1">원</span></p>
              <p class="text-xs text-gray-400 mt-1">{{ stats.summary.max_day.date }}</p>
            </template>
            <p v-else class="text-lg text-gray-300 mt-1">-</p>
          </div>
        </div>

        <!-- ── 차트 행 ── -->
        <div class="grid grid-cols-1 lg:grid-cols-5 gap-4 mb-6">
          <!-- 막대그래프 -->
          <div class="lg:col-span-3 bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
            <p class="text-sm font-bold text-gray-700 mb-4">
              {{ period === 'last_3months' ? '월별' : '일별' }} {{ isOut ? '지출' : '수입' }}
            </p>
            <div v-if="barData.labels.length" style="height:220px">
              <Bar :data="barData" :options="barOptions" />
            </div>
            <div v-else class="flex items-center justify-center h-48 text-gray-300 text-sm">데이터 없음</div>
          </div>

          <!-- 도넛 차트 -->
          <div class="lg:col-span-2 bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
            <p class="text-sm font-bold text-gray-700 mb-4">카테고리별 비중</p>
            <div v-if="donutData.labels.length" style="height:220px">
              <Doughnut :data="donutData" :options="donutOptions" />
            </div>
            <div v-else class="flex items-center justify-center h-48 text-gray-300 text-sm">데이터 없음</div>
          </div>
        </div>

        <!-- ── 달력 히트맵 ── -->
        <div v-if="heatmap" class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 mb-4">
          <p class="text-sm font-bold text-gray-700 mb-4">{{ heatmap.title }} 달력 히트맵</p>
          <div class="grid grid-cols-7 gap-1 mb-1">
            <div v-for="d in DAY_KO" :key="d"
              class="text-center text-xs font-bold py-1"
              :class="d === '일' ? 'text-red-400' : d === '토' ? 'text-blue-400' : 'text-gray-400'"
            >{{ d }}</div>
          </div>
          <div class="grid grid-cols-7 gap-1">
            <div v-for="i in heatmap.firstDow" :key="`e${i}`" style="min-height:52px"></div>
            <div
              v-for="day in heatmap.days" :key="day.key"
              class="rounded-xl p-1.5 flex flex-col justify-between transition-all hover:ring-2 hover:ring-indigo-300"
              :style="{ backgroundColor: heatBg(day.intensity), minHeight: '52px' }"
            >
              <span class="text-xs font-bold" :style="{ color: heatText(day.intensity) }">{{ day.d }}</span>
              <span v-if="day.amt > 0" class="text-[10px] font-semibold leading-tight" :style="{ color: heatText(day.intensity) }">
                {{ fmtW(day.amt) }}
              </span>
            </div>
          </div>
          <div class="mt-3 flex items-center gap-2 text-xs text-gray-400">
            <span>적음</span>
            <div class="flex gap-0.5">
              <div v-for="(a, i) in [0.15, 0.35, 0.55, 0.75, 0.95]" :key="i"
                class="w-4 h-4 rounded" :style="{ backgroundColor: `rgba(99,102,241,${a})` }" />
            </div>
            <span>많음</span>
            <span class="ml-auto">최대: {{ fmt(heatmap.maxAmt) }}원</span>
          </div>
        </div>

        <!-- ── 카테고리 상세 ── -->
        <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
          <p class="text-sm font-bold text-gray-700 mb-1">카테고리 상세</p>
          <p class="text-xs text-gray-400 mb-4">카테고리를 클릭하면 상세 내역을 볼 수 있습니다</p>
          <div class="space-y-1">
            <div v-for="(c, i) in stats.by_category" :key="c.category">

              <!-- 카테고리 행 (클릭 토글) -->
              <div
                @click="toggleCategory(c.category)"
                class="flex items-center gap-3 px-2 py-2 rounded-xl cursor-pointer hover:bg-gray-50 transition-colors group"
              >
                <component
                  :is="expandedCategory === c.category ? ChevronDown : ChevronRight"
                  class="w-3.5 h-3.5 text-gray-400 flex-shrink-0 transition-transform"
                />
                <span class="w-2.5 h-2.5 rounded-full flex-shrink-0" :style="{ backgroundColor: COLORS[i % COLORS.length] }"></span>
                <span class="text-sm font-semibold text-gray-700 w-16 flex-shrink-0">{{ c.category }}</span>
                <div class="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
                  <div class="h-2 rounded-full transition-all" :style="{ width: c.ratio + '%', backgroundColor: COLORS[i % COLORS.length] }"></div>
                </div>
                <span class="text-xs text-gray-400 tabular-nums">{{ c.count }}건</span>
                <span class="text-sm font-bold text-gray-800 w-24 text-right tabular-nums">{{ fmt(c.amount) }}원</span>
                <span class="text-xs text-gray-400 w-10 text-right">{{ c.ratio }}%</span>
              </div>

              <!-- 가맹점 상세 아코디언 -->
              <Transition name="accordion">
                <div
                  v-if="expandedCategory === c.category"
                  class="ml-10 mt-1 mb-2 rounded-xl border border-gray-100 overflow-hidden"
                >
                  <!-- 기타 카테고리일 때 AI 분류 버튼 -->
                  <div v-if="c.category === '기타'" class="px-3 py-3 bg-violet-50 border-b border-violet-100">
                    <!-- 상태 메시지 -->
                    <p v-if="classifyMsg" class="text-xs text-emerald-600 font-semibold mb-2">✓ {{ classifyMsg }}</p>
                    <p v-else-if="classifyErr" class="text-xs text-red-500 mb-2">{{ classifyErr }}</p>
                    <p v-else class="text-xs text-violet-500 mb-2">
                      저장된 분류: <strong>{{ savedMapSize }}개</strong>
                      <span class="text-gray-400 ml-1">· 미분류만 골라 Gemini 호출해 API를 아낄 수 있습니다</span>
                    </p>
                    <!-- 버튼 2개 -->
                    <div class="flex gap-2">
                      <button
                        @click.stop="classifyMisc(true)"
                        :disabled="classifying || savedMapSize === 0"
                        class="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-violet-300 hover:bg-violet-50 disabled:opacity-40 text-violet-700 text-xs font-bold rounded-lg transition-colors"
                        title="API 호출 없이 저장된 분류만 적용"
                      >
                        저장 분류 적용
                      </button>
                      <button
                        @click.stop="classifyMisc(false)"
                        :disabled="classifying"
                        class="flex items-center gap-1.5 px-3 py-1.5 bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white text-xs font-bold rounded-lg transition-colors"
                        title="아직 미분류된 가맹점만 Gemini에 요청"
                      >
                        <Sparkles class="w-3.5 h-3.5" :class="{ 'animate-spin': classifying }" />
                        {{ classifying ? '분류 중...' : 'AI 재분류 (미분류만)' }}
                      </button>
                    </div>
                  </div>

                  <div class="bg-gray-50 px-3 py-1.5 flex text-xs font-bold text-gray-400 border-b border-gray-100">
                    <span class="flex-1">가맹점</span>
                    <span class="w-10 text-center">건수</span>
                    <span class="w-28 text-right">금액</span>
                  </div>
                  <div
                    v-for="m in (stats.category_details?.[c.category] ?? [])"
                    :key="m.merchant"
                    class="flex items-center px-3 py-2 border-b border-gray-50 last:border-0 hover:bg-white transition-colors"
                  >
                    <span class="flex-1 text-sm text-gray-700 truncate">{{ m.merchant || '(미확인)' }}</span>
                    <span class="w-10 text-center text-xs text-gray-400">{{ m.count }}건</span>
                    <span class="w-28 text-right text-sm font-semibold tabular-nums"
                      :style="{ color: COLORS[i % COLORS.length] }">
                      {{ fmt(m.amount) }}원
                    </span>
                  </div>
                  <div v-if="!(stats.category_details?.[c.category]?.length)" class="py-4 text-center text-xs text-gray-300">
                    내역 없음
                  </div>
                </div>
              </Transition>

            </div>
            <div v-if="!stats.by_category.length" class="text-sm text-gray-300 text-center py-4">데이터 없음</div>
          </div>
        </div>

      </template>
    </main>
    <AppFooter />
  </div>
</template>

<style scoped>
.slide-enter-active, .slide-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.slide-enter-from, .slide-leave-to {
  opacity: 0;
  transform: translateX(-8px);
}

.accordion-enter-active, .accordion-leave-active {
  transition: opacity 0.2s, max-height 0.25s ease;
  max-height: 600px;
  overflow: hidden;
}
.accordion-enter-from, .accordion-leave-to {
  opacity: 0;
  max-height: 0;
}
</style>
