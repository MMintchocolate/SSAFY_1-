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
  <div class="min-h-screen bg-white" style="font-family:'Pretendard','Noto Sans KR',sans-serif">
    <NavBar />

    <main class="pt-16">
      <!-- Header -->
      <div style="background:linear-gradient(90deg,#fffdf9 0%,#ffffff 50%,#f2fffb 100%);border-bottom:1px solid #EEF1F5">
        <div class="max-w-5xl mx-auto px-4 sm:px-6 py-10">
          <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-bold mb-3" style="background:#FFF8E6;color:#B8860B;font-size:0.72rem">
            ✦ 한국금거래소 실시간 시세
          </div>
          <h1 class="font-black mb-1" style="font-size:1.8rem;color:#0F122B">금 · 귀금속 시세</h1>
          <p style="color:#6F7485;font-size:0.9rem">한국금거래소 기준 매도가(살 때) · 매입가(팔 때)</p>
        </div>
      </div>

      <div class="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-5">

        <!-- 품목 선택 -->
        <div class="flex gap-2 flex-wrap">
          <button
            v-for="m in METALS" :key="m.value"
            @click="metal = m.value"
            class="px-4 py-2 rounded-xl text-sm font-bold transition-all"
            :style="metal === m.value
              ? 'background:#FFD76A;color:#0F122B;border:1.5px solid #FFD76A'
              : 'background:white;color:#6F7485;border:1.5px solid #EEF1F5'"
          >{{ m.label }}</button>
        </div>

        <!-- 현재가 카드 -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="rounded-2xl p-6" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
            <p class="font-medium mb-1" style="font-size:0.75rem;color:#6F7485">매도가 (살 때)</p>
            <div class="flex items-end gap-3">
              <span class="font-black tabular-nums" style="font-size:2.2rem;color:#0F122B">
                {{ latest?.sell?.toLocaleString() ?? '-' }}
              </span>
              <span class="mb-1" style="font-size:0.85rem;color:#6F7485">{{ unitLabel }}</span>
            </div>
            <div v-if="sellChange !== null" class="flex items-center gap-1.5 mt-2">
              <span class="flex items-center gap-1 font-bold text-sm" :style="sellChange >= 0 ? 'color:#E5323B' : 'color:#3B7FED'">
                <TrendingUp v-if="sellChange >= 0" class="w-4 h-4" />
                <TrendingDown v-else class="w-4 h-4" />
                {{ sellChange >= 0 ? '+' : '' }}{{ sellChange.toLocaleString() }}원
              </span>
              <span style="font-size:0.75rem;color:#6F7485">
                ({{ sellChange >= 0 ? '+' : '' }}{{ sellChangePct }}%)
              </span>
            </div>
          </div>

          <div class="rounded-2xl p-6" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
            <p class="font-medium mb-1" style="font-size:0.75rem;color:#6F7485">매입가 (팔 때)</p>
            <div class="flex items-end gap-3">
              <span class="font-black tabular-nums" style="font-size:2.2rem;color:#0F122B">
                {{ latest?.buy?.toLocaleString() ?? '-' }}
              </span>
              <span class="mb-1" style="font-size:0.85rem;color:#6F7485">{{ unitLabel }}</span>
            </div>
            <div v-if="latest && prev" class="mt-2">
              <span style="font-size:0.75rem;color:#6F7485">
                전일 대비
                <span class="font-bold" :style="(latest.buy - prev.buy) >= 0 ? 'color:#E5323B' : 'color:#3B7FED'">
                  {{ (latest.buy - prev.buy) >= 0 ? '+' : '' }}{{ (latest.buy - prev.buy).toLocaleString() }}원
                </span>
              </span>
            </div>
          </div>
        </div>

        <!-- 차트 카드 -->
        <div class="rounded-2xl p-6" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
          <div class="flex items-center justify-between mb-5 flex-wrap gap-2">
            <p class="font-bold" style="font-size:0.9rem;color:#0F122B">
              {{ METALS.find(m => m.value === metal)?.label }} 시세 추이
            </p>
            <div class="flex gap-1.5">
              <button
                v-for="p in PERIODS" :key="p.value"
                @click="period = p.value"
                class="px-3 py-1.5 rounded-xl text-xs font-bold transition-all"
                :style="period === p.value
                  ? 'background:#FFD76A;color:#0F122B'
                  : 'background:#F8F9FF;color:#6F7485'"
              >{{ p.label }}</button>
            </div>
          </div>

          <div class="relative h-72">
            <div v-if="loading" class="absolute inset-0 flex items-center justify-center">
              <div class="w-8 h-8 border-4 rounded-full animate-spin" style="border-color:#EEF1F5;border-top-color:#FFD76A"></div>
            </div>
            <div v-else-if="error" class="absolute inset-0 flex items-center justify-center text-sm" style="color:#E5323B">
              {{ error }}
            </div>
            <Line
              v-else-if="data.length > 0"
              :data="chartData"
              :options="chartOptions"
              style="height:100%;width:100%"
            />
            <div v-else class="absolute inset-0 flex items-center justify-center text-sm" style="color:#6F7485">
              데이터 없음
            </div>
          </div>
        </div>

        <!-- 최근 데이터 표 -->
        <div class="rounded-2xl overflow-hidden" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
          <div class="px-5 py-4" style="border-bottom:1px solid #EEF1F5">
            <p class="font-bold" style="font-size:0.9rem;color:#0F122B">최근 시세 내역</p>
          </div>
          <div class="overflow-auto max-h-72">
            <table class="w-full text-xs">
              <thead class="sticky top-0" style="background:#F8F9FF;border-bottom:1px solid #EEF1F5">
                <tr>
                  <th class="px-4 py-2.5 text-left font-bold" style="color:#6F7485">날짜·시간</th>
                  <th class="px-4 py-2.5 text-right font-bold" style="color:#E5323B">매도가 (살 때)</th>
                  <th class="px-4 py-2.5 text-right font-bold" style="color:#3B7FED">매입가 (팔 때)</th>
                  <th class="px-4 py-2.5 text-right font-bold" style="color:#6F7485">스프레드</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(row, i) in [...data].reverse().slice(0, 50)"
                  :key="i"
                  class="transition-colors hover:bg-[#FFFDF5]"
                  style="border-bottom:1px solid #EEF1F5"
                >
                  <td class="px-4 py-2 tabular-nums" style="color:#6F7485">{{ row.date }}</td>
                  <td class="px-4 py-2 text-right font-bold tabular-nums" style="color:#0F122B">{{ row.sell?.toLocaleString() }}</td>
                  <td class="px-4 py-2 text-right tabular-nums" style="color:#0F122B">{{ row.buy?.toLocaleString() }}</td>
                  <td class="px-4 py-2 text-right tabular-nums" style="color:#6F7485">{{ (row.sell - row.buy).toLocaleString() }}</td>
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
