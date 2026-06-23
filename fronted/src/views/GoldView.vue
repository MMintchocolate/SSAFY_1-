<script setup>
// @ts-nocheck
import { ref, computed, watch, onMounted } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement,
  Title, Tooltip, Legend, Filler,
} from 'chart.js'
import NavBar from '@/components/NavBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import { TrendingUp, TrendingDown } from '@lucide/vue'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const API = '/api/stocks/gold/'

const METALS = [
  { label: '순금 24K', value: 'pure' },
  { label: '18K',      value: '18k'  },
  { label: '14K',      value: '14k'  },
  { label: '백금',      value: 'white' },
  { label: '은',        value: 'silver' },
]

const PERIODS = [
  { label: '1일',  value: '1D' },
  { label: '1주',  value: '1W' },
  { label: '1개월', value: '1M' },
  { label: '3개월', value: '3M' },
  { label: '6개월', value: '6M' },
  { label: '1년',  value: '1Y' },
]

const metal   = ref('pure')
const period  = ref('3M')
const data    = ref([])
const loading = ref(false)
const error   = ref('')

async function fetchGold() {
  loading.value = true
  error.value   = ''
  try {
    const res  = await fetch(`${API}?period=${period.value}&metal=${metal.value}`)
    const json = await res.json()
    if (json.error) throw new Error(json.error)
    data.value = json.data ?? []
  } catch (e) {
    error.value = e.message || '데이터 로딩 실패'
    data.value  = []
  } finally {
    loading.value = false
  }
}

watch([metal, period], fetchGold)
onMounted(fetchGold)

// ── 최신 / 이전 가격 ────────────────────────────────────────────
const latest = computed(() => data.value.at(-1) ?? null)
const prev   = computed(() => data.value.at(-2) ?? null)

const sellChange = computed(() => {
  if (!latest.value || !prev.value) return null
  return latest.value.sell - prev.value.sell
})
const sellChangePct = computed(() => {
  if (!sellChange.value || !prev.value?.sell) return null
  return (sellChange.value / prev.value.sell * 100).toFixed(2)
})

// ── 차트 ────────────────────────────────────────────────────────
const chartData = computed(() => {
  const labels    = data.value.map(d => d.date.slice(0, 10))
  const sellPrices = data.value.map(d => d.sell)
  const buyPrices  = data.value.map(d => d.buy)

  const isUp = sellPrices.length >= 2 &&
    sellPrices.at(-1) >= sellPrices[0]

  const sellColor = isUp ? 'rgb(239,68,68)'   : 'rgb(59,130,246)'
  const sellFill  = isUp ? 'rgba(239,68,68,0.07)' : 'rgba(59,130,246,0.07)'

  return {
    labels,
    datasets: [
      {
        label:           '매도가 (살 때)',
        data:            sellPrices,
        borderColor:     sellColor,
        backgroundColor: sellFill,
        borderWidth:     2,
        pointRadius:     0,
        tension:         0.3,
        fill:            true,
      },
      {
        label:       '매입가 (팔 때)',
        data:        buyPrices,
        borderColor: 'rgba(156,163,175,0.8)',
        borderWidth: 1.5,
        pointRadius: 0,
        tension:     0.3,
        fill:        false,
        borderDash:  [4, 3],
      },
    ],
  }
})

const chartOptions = {
  responsive:          true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { display: true, position: 'top', labels: { font: { size: 11 }, boxWidth: 14 } },
    tooltip: {
      callbacks: {
        label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y?.toLocaleString()}원`,
      },
    },
  },
  scales: {
    x: {
      grid:  { display: false },
      ticks: { maxTicksLimit: 8, font: { size: 10 } },
    },
    y: {
      grid:  { color: 'rgba(0,0,0,0.04)' },
      ticks: {
        font:     { size: 10 },
        callback: v => v.toLocaleString(),
      },
    },
  },
}

// ── 단위 ────────────────────────────────────────────────────────
const unitLabel = computed(() =>
  metal.value === 'silver' ? '원/g' : '원/3.75g(1돈)'
)
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <NavBar />

    <main class="pt-16">
      <!-- Header -->
      <div class="bg-white border-b border-gray-100">
        <div class="max-w-5xl mx-auto px-4 sm:px-6 py-10">
          <div class="inline-flex items-center gap-2 bg-amber-50 text-amber-700 text-xs font-bold px-3 py-1.5 rounded-full mb-3 uppercase tracking-widest border border-amber-200">
            ✦ 한국금거래소 실시간 시세
          </div>
          <h1 class="text-3xl font-extrabold text-gray-900 mb-1">금 · 귀금속 시세</h1>
          <p class="text-gray-400 text-sm">한국금거래소 기준 매도가(살 때) · 매입가(팔 때)</p>
        </div>
      </div>

      <div class="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-5">

        <!-- 품목 선택 -->
        <div class="flex gap-2 flex-wrap">
          <button
            v-for="m in METALS" :key="m.value"
            @click="metal = m.value"
            class="px-4 py-2 rounded-xl text-sm font-bold border transition-all"
            :class="metal === m.value
              ? 'bg-amber-500 text-white border-amber-500 shadow-sm'
              : 'bg-white text-gray-600 border-gray-200 hover:border-amber-300 hover:text-amber-600'"
          >{{ m.label }}</button>
        </div>

        <!-- 현재가 카드 -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <!-- 매도가 (살 때) -->
          <div class="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <p class="text-xs text-gray-400 font-medium mb-1">매도가 (살 때)</p>
            <div class="flex items-end gap-3">
              <span class="text-4xl font-black tabular-nums text-gray-900">
                {{ latest?.sell?.toLocaleString() ?? '-' }}
              </span>
              <span class="text-gray-400 text-sm mb-1">{{ unitLabel }}</span>
            </div>
            <div v-if="sellChange !== null" class="flex items-center gap-1.5 mt-2">
              <span
                class="flex items-center gap-1 text-sm font-bold"
                :class="sellChange >= 0 ? 'text-red-500' : 'text-blue-500'"
              >
                <TrendingUp v-if="sellChange >= 0" class="w-4 h-4" />
                <TrendingDown v-else class="w-4 h-4" />
                {{ sellChange >= 0 ? '+' : '' }}{{ sellChange.toLocaleString() }}원
              </span>
              <span class="text-xs text-gray-400">
                ({{ sellChange >= 0 ? '+' : '' }}{{ sellChangePct }}%)
              </span>
            </div>
          </div>

          <!-- 매입가 (팔 때) -->
          <div class="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <p class="text-xs text-gray-400 font-medium mb-1">매입가 (팔 때)</p>
            <div class="flex items-end gap-3">
              <span class="text-4xl font-black tabular-nums text-gray-900">
                {{ latest?.buy?.toLocaleString() ?? '-' }}
              </span>
              <span class="text-gray-400 text-sm mb-1">{{ unitLabel }}</span>
            </div>
            <div v-if="latest && prev" class="mt-2">
              <span class="text-xs text-gray-400">
                전일 대비
                <span
                  class="font-bold"
                  :class="(latest.buy - prev.buy) >= 0 ? 'text-red-500' : 'text-blue-500'"
                >
                  {{ (latest.buy - prev.buy) >= 0 ? '+' : '' }}{{ (latest.buy - prev.buy).toLocaleString() }}원
                </span>
              </span>
            </div>
          </div>
        </div>

        <!-- 차트 카드 -->
        <div class="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
          <!-- 기간 선택 -->
          <div class="flex items-center justify-between mb-5 flex-wrap gap-2">
            <p class="text-sm font-bold text-gray-700">
              {{ METALS.find(m => m.value === metal)?.label }} 시세 추이
            </p>
            <div class="flex gap-1.5">
              <button
                v-for="p in PERIODS" :key="p.value"
                @click="period = p.value"
                class="px-3 py-1.5 rounded-lg text-xs font-bold transition-all"
                :class="period === p.value
                  ? 'bg-amber-500 text-white'
                  : 'bg-gray-100 text-gray-500 hover:bg-amber-50 hover:text-amber-600'"
              >{{ p.label }}</button>
            </div>
          </div>

          <!-- 차트 영역 -->
          <div class="relative h-72">
            <div v-if="loading" class="absolute inset-0 flex items-center justify-center">
              <div class="w-8 h-8 border-4 border-amber-200 border-t-amber-500 rounded-full animate-spin"></div>
            </div>
            <div v-else-if="error" class="absolute inset-0 flex items-center justify-center text-red-400 text-sm">
              {{ error }}
            </div>
            <Line
              v-else-if="data.length > 0"
              :data="chartData"
              :options="chartOptions"
              style="height:100%;width:100%"
            />
            <div v-else class="absolute inset-0 flex items-center justify-center text-gray-400 text-sm">
              데이터 없음
            </div>
          </div>
        </div>

        <!-- 최근 데이터 표 -->
        <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <div class="px-5 py-4 border-b border-gray-100">
            <p class="text-sm font-bold text-gray-700">최근 시세 내역</p>
          </div>
          <div class="overflow-auto max-h-72">
            <table class="w-full text-xs">
              <thead class="sticky top-0 bg-gray-50 border-b border-gray-200">
                <tr>
                  <th class="px-4 py-2.5 text-left font-bold text-gray-500">날짜·시간</th>
                  <th class="px-4 py-2.5 text-right font-bold text-red-400">매도가 (살 때)</th>
                  <th class="px-4 py-2.5 text-right font-bold text-blue-400">매입가 (팔 때)</th>
                  <th class="px-4 py-2.5 text-right font-bold text-gray-400">스프레드</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(row, i) in [...data].reverse().slice(0, 50)"
                  :key="i"
                  class="border-b border-gray-50 hover:bg-amber-50 transition-colors"
                >
                  <td class="px-4 py-2 text-gray-500 tabular-nums">{{ row.date }}</td>
                  <td class="px-4 py-2 text-right font-bold text-gray-800 tabular-nums">{{ row.sell?.toLocaleString() }}</td>
                  <td class="px-4 py-2 text-right text-gray-600 tabular-nums">{{ row.buy?.toLocaleString() }}</td>
                  <td class="px-4 py-2 text-right text-gray-400 tabular-nums">{{ (row.sell - row.buy).toLocaleString() }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </main>

    <AppFooter />
  </div>
</template>
