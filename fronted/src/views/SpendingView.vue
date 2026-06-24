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
import { TrendingUp, CloudUpload, CircleCheck, CircleAlert, Search, ChevronDown, ChevronRight, Sparkles, FileDown, BrainCircuit, Loader2 } from '@lucide/vue'
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

// ── AI 소비 리포트 ────────────────────────────────────────────────────────
const reportLoading  = ref(false)
const reportError    = ref(null)
const reportText     = ref('')
const reportLabel    = ref('')
const pdfLoading     = ref(false)

const reportSections = computed(() => {
  if (!reportText.value) return []
  const sections = []
  let title = null, lines = []
  for (const line of reportText.value.split('\n')) {
    if (line.startsWith('## ')) {
      if (title !== null) sections.push({ title, content: lines.join('\n').trim() })
      title = line.slice(3).trim(); lines = []
    } else { lines.push(line) }
  }
  if (title !== null) sections.push({ title, content: lines.join('\n').trim() })
  return sections
})

const SECTION_ICONS = { '소비 요약': '📊', '주목할 카테고리': '🔍', '소비 패턴': '📅', '절약 팁': '💡', '총평': '⭐' }

async function generateReport() {
  reportLoading.value = true; reportError.value = null; reportText.value = ''
  const params = new URLSearchParams({ direction: direction.value })
  if (isCustom.value) {
    params.set('start', customStart.value); params.set('end', customEnd.value)
  } else {
    params.set('period', period.value)
  }
  try {
    const res  = await authFetch(`/api/spending/ai-report/?${params}`)
    const json = await res.json()
    if (!res.ok) throw new Error(json.error ?? `HTTP ${res.status}`)
    reportText.value  = json.report
    reportLabel.value = json.period_label
  } catch (e) { reportError.value = e.message }
  finally { reportLoading.value = false }
}

async function downloadPdf() {
  if (!reportText.value) return
  pdfLoading.value = true
  const body = { direction: direction.value, report: reportText.value, period_label: reportLabel.value }
  if (isCustom.value) {
    body.start = customStart.value; body.end = customEnd.value
  } else {
    body.period = period.value
  }
  try {
    const res = await authFetch('/api/spending/report-pdf/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) { const j = await res.json(); throw new Error(j.error ?? 'PDF 생성 실패') }
    const blob = await res.blob()
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `소비리포트_${reportLabel.value}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) { reportError.value = e.message }
  finally { pdfLoading.value = false }
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
  <div class="min-h-screen bg-white" style="font-family:'Pretendard','Noto Sans KR',sans-serif">
    <NavBar />
    <main class="pt-24 pb-16 max-w-5xl mx-auto px-4 sm:px-6">

      <!-- 헤더 -->
      <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-6">
        <div>
          <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-bold mb-3" style="background:#DFFAF4;color:#0D9B7A;font-size:0.72rem">
            <TrendingUp class="w-3 h-3" />지출 분석
          </div>
          <h1 class="font-black" style="font-size:1.8rem;color:#0F122B">소비 대시보드</h1>
          <p class="mt-1" style="color:#6F7485;font-size:0.9rem">거래 내역 CSV를 업로드하면 자동으로 분석합니다</p>
        </div>

        <!-- CSV 업로드 -->
        <label class="flex items-center gap-2 px-4 py-2.5 rounded-xl cursor-pointer transition-colors text-sm font-bold shrink-0" style="border:2px dashed #57E0C3;color:#0D9B7A">
          <CloudUpload class="w-4 h-4" />
          {{ uploading ? '분석 중...' : 'CSV 교체' }}
          <input type="file" accept=".csv" class="hidden" :disabled="uploading" @change="onCsvUpload" />
        </label>
      </div>

      <!-- 업로드 결과 -->
      <div v-if="uploadMsg" class="flex items-center gap-2 text-sm rounded-xl px-4 py-2.5 mb-4" style="background:#DFFAF4;border:1px solid #57E0C3;color:#0D9B7A">
        <CircleCheck class="w-4 h-4 shrink-0" />{{ uploadMsg }}
      </div>
      <div v-if="uploadErr" class="flex items-center gap-2 text-sm rounded-xl px-4 py-2.5 mb-4" style="background:#FFF5F5;border:1px solid #FFD0D0;color:#E5323B">
        <CircleAlert class="w-4 h-4 shrink-0" />{{ uploadErr }}
      </div>

      <!-- 입금 / 출금 토글 -->
      <div class="flex gap-2 mb-4">
        <button
          v-for="d in DIRECTIONS" :key="d.key"
          @click="direction = d.key"
          class="px-5 py-2 rounded-xl text-sm font-bold transition-all"
          :style="direction === d.key
            ? d.key === 'out'
              ? 'background:#E5323B;color:white'
              : 'background:#57E0C3;color:#0F122B'
            : 'background:white;color:#6F7485;border:1.5px solid #EEF1F5'"
        >{{ d.label }}</button>
      </div>

      <!-- 기간 토글 + 직접 설정 -->
      <div class="flex flex-wrap items-center gap-3 mb-6">
        <div class="flex gap-1 p-1 rounded-xl" style="background:white;border:1px solid #EEF1F5">
          <button
            v-for="p in PERIODS" :key="p.key"
            @click="period = p.key"
            class="px-3.5 py-1.5 rounded-lg text-sm font-bold transition-colors"
            :style="period === p.key
              ? 'background:#0F122B;color:white'
              : 'color:#6F7485'"
          >{{ p.label }}</button>
        </div>

        <Transition name="slide">
          <div v-if="isCustom" class="flex items-center gap-2">
            <input type="date" v-model="customStart"
              class="text-sm rounded-lg px-3 py-1.5 focus:outline-none"
              style="border:1.5px solid #EEF1F5;color:#0F122B"
            />
            <span class="font-bold" style="color:#6F7485">~</span>
            <input type="date" v-model="customEnd"
              class="text-sm rounded-lg px-3 py-1.5 focus:outline-none"
              style="border:1.5px solid #EEF1F5;color:#0F122B"
            />
            <button
              @click="fetchStats"
              :disabled="!customStart || !customEnd"
              class="flex items-center gap-1.5 px-3.5 py-1.5 text-sm font-bold rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              style="background:#0F122B;color:white"
            >
              <Search class="w-3.5 h-3.5" />조회
            </button>
          </div>
        </Transition>
      </div>

      <!-- 로딩 / 에러 -->
      <div v-if="loading" class="flex justify-center py-20 text-sm" style="color:#6F7485">분석 중...</div>
      <div v-else-if="error" class="rounded-2xl p-6 text-sm mb-4" style="background:#FFF5F5;border:1px solid #FFD0D0;color:#E5323B">{{ error }}</div>
      <div v-else-if="isCustom && (!customStart || !customEnd)" class="flex justify-center py-16 text-sm" style="color:#6F7485">날짜 범위를 선택하고 조회를 눌러주세요</div>

      <template v-else-if="stats">

        <!-- ── 요약 카드 ── -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <div class="rounded-2xl p-5" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
            <p class="font-bold mb-1" style="font-size:0.72rem;color:#6F7485;letter-spacing:0.08em">{{ isOut ? '총 지출' : '총 수입' }}</p>
            <p class="font-extrabold" style="font-size:1.5rem" :style="{ color: isOut ? '#E5323B' : '#0D9B7A' }">
              {{ fmt(stats.summary.total) }}<span style="font-size:1rem;font-weight:700;margin-left:4px">원</span>
            </p>
            <p class="mt-1" style="font-size:0.75rem;color:#6F7485">{{ stats.summary.count }}건 거래</p>
          </div>
          <div class="rounded-2xl p-5" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
            <p class="font-bold mb-1" style="font-size:0.72rem;color:#6F7485;letter-spacing:0.08em">일 평균</p>
            <p class="font-extrabold" style="font-size:1.5rem;color:#0F122B">{{ fmt(stats.summary.daily_avg) }}<span style="font-size:1rem;font-weight:700;margin-left:4px">원</span></p>
          </div>
          <div class="rounded-2xl p-5" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
            <p class="font-bold mb-1" style="font-size:0.72rem;color:#6F7485;letter-spacing:0.08em">{{ isOut ? '최다 지출일' : '최다 수입일' }}</p>
            <template v-if="stats.summary.max_day">
              <p class="font-extrabold" style="font-size:1.5rem;color:#FFA726">{{ fmt(stats.summary.max_day.amount) }}<span style="font-size:1rem;font-weight:700;margin-left:4px">원</span></p>
              <p class="mt-1" style="font-size:0.75rem;color:#6F7485">{{ stats.summary.max_day.date }}</p>
            </template>
            <p v-else style="font-size:1.1rem;color:#EEF1F5;margin-top:4px">-</p>
          </div>
        </div>

        <!-- ── 차트 행 ── -->
        <div class="grid grid-cols-1 lg:grid-cols-5 gap-4 mb-6">
          <div class="lg:col-span-3 rounded-2xl p-5" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
            <p class="font-bold mb-4" style="font-size:0.9rem;color:#0F122B">
              {{ period === 'last_3months' ? '월별' : '일별' }} {{ isOut ? '지출' : '수입' }}
            </p>
            <div v-if="barData.labels.length" style="height:220px">
              <Bar :data="barData" :options="barOptions" />
            </div>
            <div v-else class="flex items-center justify-center h-48 text-sm" style="color:#EEF1F5">데이터 없음</div>
          </div>

          <div class="lg:col-span-2 rounded-2xl p-5" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
            <p class="font-bold mb-4" style="font-size:0.9rem;color:#0F122B">카테고리별 비중</p>
            <div v-if="donutData.labels.length" style="height:220px">
              <Doughnut :data="donutData" :options="donutOptions" />
            </div>
            <div v-else class="flex items-center justify-center h-48 text-sm" style="color:#EEF1F5">데이터 없음</div>
          </div>
        </div>

        <!-- ── 달력 히트맵 ── -->
        <div v-if="heatmap" class="rounded-2xl p-5 mb-4" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
          <p class="font-bold mb-4" style="font-size:0.9rem;color:#0F122B">{{ heatmap.title }} 달력 히트맵</p>
          <div class="grid grid-cols-7 gap-1 mb-1">
            <div v-for="d in DAY_KO" :key="d"
              class="text-center text-xs font-bold py-1"
              :style="d === '일' ? 'color:#E5323B' : d === '토' ? 'color:#3B7FED' : 'color:#6F7485'"
            >{{ d }}</div>
          </div>
          <div class="grid grid-cols-7 gap-1">
            <div v-for="i in heatmap.firstDow" :key="`e${i}`" style="min-height:52px"></div>
            <div
              v-for="day in heatmap.days" :key="day.key"
              class="rounded-xl p-1.5 flex flex-col justify-between transition-all"
              :style="{ backgroundColor: heatBg(day.intensity), minHeight: '52px' }"
            >
              <span class="text-xs font-bold" :style="{ color: heatText(day.intensity) }">{{ day.d }}</span>
              <span v-if="day.amt > 0" class="text-[10px] font-semibold leading-tight" :style="{ color: heatText(day.intensity) }">
                {{ fmtW(day.amt) }}
              </span>
            </div>
          </div>
          <div class="mt-3 flex items-center gap-2" style="font-size:0.75rem;color:#6F7485">
            <span>적음</span>
            <div class="flex gap-0.5">
              <div v-for="(a, i) in [0.15, 0.35, 0.55, 0.75, 0.95]" :key="i"
                class="w-4 h-4 rounded" :style="{ backgroundColor: isOut ? `rgba(229,50,59,${a})` : `rgba(87,224,195,${a})` }" />
            </div>
            <span>많음</span>
            <span class="ml-auto">최대: {{ fmt(heatmap.maxAmt) }}원</span>
          </div>
        </div>

        <!-- ── 카테고리 상세 ── -->
        <div class="rounded-2xl p-5" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
          <p class="font-bold mb-1" style="font-size:0.9rem;color:#0F122B">카테고리 상세</p>
          <p class="mb-4" style="font-size:0.75rem;color:#6F7485">카테고리를 클릭하면 상세 내역을 볼 수 있습니다</p>
          <div class="space-y-1">
            <div v-for="(c, i) in stats.by_category" :key="c.category">
              <div
                @click="toggleCategory(c.category)"
                class="flex items-center gap-3 px-2 py-2 rounded-xl cursor-pointer transition-colors hover:bg-[#F8F9FF]"
              >
                <component :is="expandedCategory === c.category ? ChevronDown : ChevronRight"
                  class="w-3.5 h-3.5 flex-shrink-0 transition-transform" style="color:#6F7485" />
                <span class="w-2.5 h-2.5 rounded-full flex-shrink-0" :style="{ backgroundColor: COLORS[i % COLORS.length] }"></span>
                <span class="font-semibold w-16 flex-shrink-0" style="font-size:0.85rem;color:#0F122B">{{ c.category }}</span>
                <div class="flex-1 rounded-full h-2 overflow-hidden" style="background:#EEF1F5">
                  <div class="h-2 rounded-full transition-all" :style="{ width: c.ratio + '%', backgroundColor: COLORS[i % COLORS.length] }"></div>
                </div>
                <span class="tabular-nums" style="font-size:0.75rem;color:#6F7485">{{ c.count }}건</span>
                <span class="font-bold w-24 text-right tabular-nums" style="font-size:0.85rem;color:#0F122B">{{ fmt(c.amount) }}원</span>
                <span class="w-10 text-right" style="font-size:0.75rem;color:#6F7485">{{ c.ratio }}%</span>
              </div>

              <Transition name="accordion">
                <div
                  v-if="expandedCategory === c.category"
                  class="ml-10 mt-1 mb-2 rounded-xl overflow-hidden"
                  style="border:1px solid #EEF1F5"
                >
                  <div v-if="c.category === '기타'" class="px-3 py-3" style="background:#F8F9FF;border-bottom:1px solid #EEF1F5">
                    <p v-if="classifyMsg" class="font-semibold mb-2" style="font-size:0.75rem;color:#0D9B7A">✓ {{ classifyMsg }}</p>
                    <p v-else-if="classifyErr" class="mb-2" style="font-size:0.75rem;color:#E5323B">{{ classifyErr }}</p>
                    <p v-else class="mb-2" style="font-size:0.75rem;color:#6F7485">
                      저장된 분류: <strong style="color:#0F122B">{{ savedMapSize }}개</strong>
                      <span class="ml-1" style="color:#6F7485">· 미분류만 골라 Gemini 호출해 API를 아낄 수 있습니다</span>
                    </p>
                    <div class="flex gap-2">
                      <button
                        @click.stop="classifyMisc(true)"
                        :disabled="classifying || savedMapSize === 0"
                        class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-colors disabled:opacity-40"
                        style="background:white;border:1.5px solid #EEF1F5;color:#0F122B"
                      >저장 분류 적용</button>
                      <button
                        @click.stop="classifyMisc(false)"
                        :disabled="classifying"
                        class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-colors disabled:opacity-50"
                        style="background:#0F122B;color:white"
                      >
                        <Sparkles class="w-3.5 h-3.5" :class="{ 'animate-spin': classifying }" />
                        {{ classifying ? '분류 중...' : 'AI 재분류 (미분류만)' }}
                      </button>
                    </div>
                  </div>

                  <div class="px-3 py-1.5 flex font-bold" style="background:#F8F9FF;font-size:0.72rem;color:#6F7485;border-bottom:1px solid #EEF1F5">
                    <span class="flex-1">가맹점</span>
                    <span class="w-10 text-center">건수</span>
                    <span class="w-28 text-right">금액</span>
                  </div>
                  <div
                    v-for="m in (stats.category_details?.[c.category] ?? [])"
                    :key="m.merchant"
                    class="flex items-center px-3 py-2 transition-colors hover:bg-[#F8F9FF]"
                    style="border-bottom:1px solid #EEF1F5"
                  >
                    <span class="flex-1 text-sm truncate" style="color:#0F122B">{{ m.merchant || '(미확인)' }}</span>
                    <span class="w-10 text-center" style="font-size:0.75rem;color:#6F7485">{{ m.count }}건</span>
                    <span class="w-28 text-right text-sm font-semibold tabular-nums" :style="{ color: COLORS[i % COLORS.length] }">
                      {{ fmt(m.amount) }}원
                    </span>
                  </div>
                  <div v-if="!(stats.category_details?.[c.category]?.length)" class="py-4 text-center" style="font-size:0.75rem;color:#6F7485">
                    내역 없음
                  </div>
                </div>
              </Transition>
            </div>
            <div v-if="!stats.by_category.length" class="text-sm text-center py-4" style="color:#6F7485">데이터 없음</div>
          </div>
        </div>

        <!-- ── AI 소비 리포트 ── -->
        <div class="mt-8">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-2">
              <BrainCircuit class="w-5 h-5" style="color:#57E0C3" />
              <h2 class="font-black" style="font-size:1rem;color:#0F122B">AI 소비 리포트</h2>
              <span class="font-bold px-2 py-0.5 rounded-full" style="font-size:0.72rem;background:#DFFAF4;color:#0D9B7A">Gemini</span>
            </div>
            <div class="flex items-center gap-2">
              <button
                v-if="reportText"
                @click="downloadPdf"
                :disabled="pdfLoading"
                class="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-colors disabled:opacity-50"
                style="background:#0F122B;color:white"
              >
                <Loader2 v-if="pdfLoading" class="w-3.5 h-3.5 animate-spin" />
                <FileDown v-else class="w-3.5 h-3.5" />
                {{ pdfLoading ? 'PDF 생성 중...' : 'PDF 다운로드' }}
              </button>
              <button
                @click="generateReport"
                :disabled="reportLoading || !stats"
                class="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all disabled:opacity-50"
                style="background:#57E0C3;color:#0F122B"
              >
                <Loader2 v-if="reportLoading" class="w-3.5 h-3.5 animate-spin" />
                <Sparkles v-else class="w-3.5 h-3.5" />
                {{ reportLoading ? 'AI 분석 중...' : (reportText ? '리포트 재생성' : 'AI 리포트 생성') }}
              </button>
            </div>
          </div>

          <div v-if="reportError" class="flex items-center gap-2 p-3 rounded-xl text-sm mb-4" style="background:#FFF5F5;border:1px solid #FFD0D0;color:#E5323B">
            <CircleAlert class="w-4 h-4 flex-shrink-0" />{{ reportError }}
          </div>

          <div v-if="reportLoading" class="rounded-2xl p-8 text-center" style="background:white;border:1px solid #EEF1F5">
            <Loader2 class="w-8 h-8 animate-spin mx-auto mb-3" style="color:#57E0C3" />
            <p class="font-semibold text-sm" style="color:#6F7485">Gemini AI가 소비 패턴을 분석하고 있습니다...</p>
            <p class="mt-1" style="font-size:0.75rem;color:#6F7485">약 10~20초 소요됩니다</p>
          </div>

          <div v-else-if="reportSections.length" class="space-y-3">
            <div
              v-for="sec in reportSections" :key="sec.title"
              class="rounded-2xl overflow-hidden"
              style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)"
            >
              <div class="flex items-center gap-2 px-5 py-3" style="background:#F8F9FF;border-bottom:1px solid #EEF1F5">
                <span class="text-base">{{ SECTION_ICONS[sec.title] ?? '✦' }}</span>
                <h3 class="font-black text-sm" style="color:#0F122B">{{ sec.title }}</h3>
              </div>
              <div class="px-5 py-4 text-sm leading-relaxed whitespace-pre-line" style="color:#0F122B">{{ sec.content }}</div>
            </div>
          </div>

          <div v-else-if="!reportLoading && !reportError" class="rounded-2xl p-10 text-center" style="background:white;border:2px dashed #EEF1F5">
            <BrainCircuit class="w-10 h-10 mx-auto mb-3" style="color:#EEF1F5" />
            <p class="font-semibold text-sm" style="color:#6F7485">AI 리포트 생성 버튼을 눌러</p>
            <p class="text-sm" style="color:#6F7485">현재 기간의 소비 인사이트를 확인하세요.</p>
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
