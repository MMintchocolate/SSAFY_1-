<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import NavBar from '@/components/NavBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import { Doughnut, Line } from 'vue-chartjs'
import {
  Chart as ChartJS, ArcElement, Tooltip, Legend,
  CategoryScale, LinearScale, PointElement, LineElement, Filler,
} from 'chart.js'
import { TrendingUp, TrendingDown, Wallet, RefreshCw, Loader2 } from '@lucide/vue'
import { useAuth } from '@/composables/useAuth'

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, PointElement, LineElement, Filler)

const { authFetch } = useAuth()

// ── 포트폴리오 보유 종목 ─────────────────────────────────────────
const holdings   = ref([])
const prices     = ref({})
const loading    = ref(true)
const refreshing = ref(false)

async function fetchPrice(symbol) {
  try {
    const res = await fetch(`/api/stocks/${encodeURIComponent(symbol)}/`)
    if (!res.ok) return null
    return await res.json()
  } catch { return null }
}

async function loadPrices(items) {
  const results = await Promise.all(items.map(h => fetchPrice(h.symbol)))
  const map = {}
  items.forEach((h, i) => {
    if (results[i]) map[h.symbol] = results[i]
  })
  prices.value = map
}

async function loadPortfolio() {
  loading.value = true
  try {
    const res = await authFetch('/api/portfolio/')
    holdings.value = await res.json()
    await loadPrices(holdings.value)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function refresh() {
  refreshing.value = true
  await loadPrices(holdings.value)
  refreshing.value = false
}

onMounted(loadPortfolio)

// ── 계산 ─────────────────────────────────────────────────────────
const enriched = computed(() =>
  holdings.value.map(h => {
    const p      = prices.value[h.symbol]
    const close  = p?.price ?? p?.close ?? null
    const chgPct = p?.change_pct ?? null
    const value  = close != null ? close * h.quantity : null
    const cost   = h.avg_price * h.quantity
    const pnl    = value != null ? value - cost : null
    const pnlPct = value != null ? ((value - cost) / cost) * 100 : null
    const dayPnl = (close != null && chgPct != null)
      ? close * h.quantity * (chgPct / 100) / (1 + chgPct / 100)
      : null
    return { ...h, close, chgPct, value, cost, pnl, pnlPct, dayPnl }
  })
)

const totalCost  = computed(() => enriched.value.reduce((s, h) => s + h.cost, 0))
const totalValue = computed(() => {
  const items = enriched.value.filter(h => h.value != null)
  if (!items.length) return null
  const known   = items.reduce((s, h) => s + h.value, 0)
  const unknown = enriched.value.filter(h => h.value == null).reduce((s, h) => s + h.cost, 0)
  return known + unknown
})
const totalPnl    = computed(() => totalValue.value != null ? totalValue.value - totalCost.value : null)
const totalPnlPct = computed(() => totalPnl.value != null && totalCost.value > 0 ? (totalPnl.value / totalCost.value) * 100 : null)
const todayPnl    = computed(() => {
  const vals = enriched.value.map(h => h.dayPnl).filter(v => v != null)
  return vals.length ? vals.reduce((a, b) => a + b, 0) : null
})

// ── 도넛 차트 ────────────────────────────────────────────────────
const PALETTE = ['#57E0C3','#FFD76A','#0F122B','#A78BFA','#E5323B','#3B7FED','#FFA726','#4ECBA8','#60A5FA','#F472B6']

// 현재가 없으면 원가로 대체 → 전 종목 동일 기준 표시
const donutItems = computed(() => enriched.value.map(h => ({
  ...h,
  displayValue: h.value ?? h.cost,
})))

const donutTotal = computed(() => donutItems.value.reduce((s, h) => s + h.displayValue, 0))

const donutData = computed(() => {
  if (!donutItems.value.length || donutTotal.value === 0) return null
  return {
    labels: donutItems.value.map(h => h.name),
    datasets: [{
      data: donutItems.value.map(h => parseFloat((h.displayValue / donutTotal.value * 100).toFixed(1))),
      backgroundColor: PALETTE.slice(0, donutItems.value.length),
      borderWidth: 2,
      borderColor: '#ffffff',
    }],
  }
})
const donutOpts = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '68%',
  plugins: {
    legend: { display: false },
    tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.raw}%` } },
  },
}

// ── 포트폴리오 가치 추이 ─────────────────────────────────────────
const historyData = ref(null)
const histLoading = ref(false)

async function loadHistory() {
  if (!holdings.value.length) return
  histLoading.value = true
  try {
    const results = await Promise.all(
      holdings.value.map(async h => {
        const res = await fetch(`/api/stocks/${encodeURIComponent(h.symbol)}/history/?period=1mo`)
        if (!res.ok) return null
        const rows = await res.json()
        return { quantity: h.quantity, rows: Array.isArray(rows) ? rows : [] }
      })
    )
    const dateMap = {}
    for (const r of results.filter(Boolean)) {
      for (const row of r.rows) {
        const d = (row.date || '').slice(0, 10)
        if (!d) continue
        dateMap[d] = (dateMap[d] ?? 0) + row.close * r.quantity
      }
    }
    const dates  = Object.keys(dateMap).sort()
    const values = dates.map(d => Math.round(dateMap[d]))
    const first  = values[0] ?? 0
    historyData.value = {
      labels: dates.map(d => d.slice(5)),
      datasets: [{
        label: '포트폴리오 가치',
        data: values,
        borderColor: values[values.length - 1] >= first ? '#E5323B' : '#3B7FED',
        backgroundColor: values[values.length - 1] >= first ? 'rgba(229,50,59,0.07)' : 'rgba(59,127,237,0.07)',
        borderWidth: 2, pointRadius: 0, tension: 0.3, fill: true,
      }],
    }
  } catch (e) { console.error(e) }
  finally { histLoading.value = false }
}

const lineOpts = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false } },
  scales: {
    x: { grid: { display: false }, ticks: { maxTicksLimit: 8, font: { size: 10 }, color: '#6F7485' }, border: { display: false } },
    y: { grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { font: { size: 10 }, color: '#6F7485', callback: v => (v / 10000).toFixed(0) + '만' }, border: { display: false } },
  },
  animation: { duration: 300 },
}

let histLoaded = false
watch(holdings, (val) => {
  if (val.length && !histLoaded) { histLoaded = true; loadHistory() }
}, { immediate: true })

// ── 포맷 ─────────────────────────────────────────────────────────
function fmtPct(n) {
  if (n == null) return '-'
  return (n >= 0 ? '+' : '') + n.toFixed(2) + '%'
}
function pnlColor(n) {
  if (n == null || n === 0) return '#6F7485'
  return n > 0 ? '#E5323B' : '#3B7FED'
}
</script>

<template>
  <div class="min-h-screen bg-white" style="font-family:'Pretendard','Noto Sans KR',sans-serif">
    <NavBar />

    <main class="pt-16">
      <!-- 헤더 -->
      <div style="background:linear-gradient(90deg,#fffdf9 0%,#ffffff 50%,#f2fffb 100%);border-bottom:1px solid #EEF1F5">
        <div class="max-w-5xl mx-auto px-6 py-10">
          <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-bold mb-3" style="background:#DFFAF4;color:#0D9B7A;font-size:0.72rem">
            <Wallet class="w-3 h-3" />내 포트폴리오
          </div>
          <div class="flex items-end justify-between gap-4">
            <div>
              <h1 class="font-black mb-1" style="font-size:1.8rem;color:#0F122B">포트폴리오 대시보드</h1>
              <p style="color:#6F7485;font-size:0.9rem">보유 종목의 현재 가치와 손익을 한눈에</p>
            </div>
            <button @click="refresh" :disabled="refreshing"
              class="inline-flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-sm disabled:opacity-50"
              style="background:#0F122B;color:white">
              <RefreshCw class="w-3.5 h-3.5" :class="refreshing ? 'animate-spin' : ''" />현재가 갱신
            </button>
          </div>
        </div>
      </div>

      <div class="max-w-5xl mx-auto px-6 py-8">

        <!-- 로딩 -->
        <div v-if="loading" class="flex items-center justify-center py-32">
          <Loader2 class="w-8 h-8 animate-spin" style="color:#57E0C3" />
        </div>

        <!-- 종목 없음 -->
        <div v-else-if="!holdings.length" class="text-center py-24">
          <div class="text-5xl mb-4">📂</div>
          <p class="font-bold mb-2" style="color:#0F122B">보유 종목이 없습니다</p>
          <p class="text-sm mb-6" style="color:#6F7485">마이페이지 → 포트폴리오 설정에서 종목을 추가해 보세요</p>
          <RouterLink to="/app/mypage"
            class="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl font-bold text-sm"
            style="background:#0F122B;color:white">
            마이페이지로 이동
          </RouterLink>
        </div>

        <template v-else>
          <!-- 요약 카드 3종 -->
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            <div class="rounded-2xl p-5" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
              <p class="text-sm mb-1" style="color:#6F7485">총 평가금액</p>
              <p class="font-black" style="font-size:1.5rem;color:#0F122B">
                {{ totalValue != null ? Math.round(totalValue).toLocaleString() : '-' }}<span class="text-sm font-normal ml-1" style="color:#6F7485">원</span>
              </p>
              <p class="text-xs mt-1" style="color:#6F7485">투자원금 {{ Math.round(totalCost).toLocaleString() }}원</p>
            </div>

            <div class="rounded-2xl p-5" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
              <p class="text-sm mb-1" style="color:#6F7485">총 손익</p>
              <div class="flex items-end gap-2">
                <p class="font-black" style="font-size:1.5rem" :style="`color:${pnlColor(totalPnl)}`">
                  {{ totalPnl != null ? (totalPnl >= 0 ? '+' : '') + Math.round(totalPnl).toLocaleString() : '-' }}<span class="text-sm font-normal ml-1">원</span>
                </p>
                <p class="font-bold mb-0.5 text-sm" :style="`color:${pnlColor(totalPnl)}`">{{ fmtPct(totalPnlPct) }}</p>
              </div>
              <div class="flex items-center gap-1 mt-1">
                <component :is="totalPnl != null && totalPnl >= 0 ? TrendingUp : TrendingDown" class="w-3.5 h-3.5" :style="`color:${pnlColor(totalPnl)}`" />
                <p class="text-xs" :style="`color:${pnlColor(totalPnl)}`">전체 손익</p>
              </div>
            </div>

            <div class="rounded-2xl p-5" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
              <p class="text-sm mb-1" style="color:#6F7485">오늘 손익</p>
              <p class="font-black" style="font-size:1.5rem" :style="`color:${pnlColor(todayPnl)}`">
                {{ todayPnl != null ? (todayPnl >= 0 ? '+' : '') + Math.round(todayPnl).toLocaleString() : '-' }}<span class="text-sm font-normal ml-1">원</span>
              </p>
              <div class="flex items-center gap-1 mt-1">
                <component :is="todayPnl != null && todayPnl >= 0 ? TrendingUp : TrendingDown" class="w-3.5 h-3.5" :style="`color:${pnlColor(todayPnl)}`" />
                <p class="text-xs" :style="`color:${pnlColor(todayPnl)}`">당일 등락 반영</p>
              </div>
            </div>
          </div>

          <!-- 차트 행 -->
          <div class="grid grid-cols-1 lg:grid-cols-5 gap-4 mb-6">
            <!-- 도넛 차트 -->
            <div class="lg:col-span-2 rounded-2xl p-5" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
              <p class="font-bold text-sm mb-4" style="color:#0F122B">종목 비중</p>
              <div v-if="donutData" style="height:180px;position:relative">
                <Doughnut :data="donutData" :options="donutOpts" />
              </div>
              <div class="mt-4 space-y-1.5">
                <div v-for="(h, i) in donutItems" :key="h.symbol" class="flex items-center gap-2">
                  <div class="w-2.5 h-2.5 rounded-sm flex-shrink-0" :style="`background:${PALETTE[i]}`"></div>
                  <span class="text-xs flex-1 truncate" style="color:#0F122B">{{ h.name }}</span>
                  <span class="text-xs font-bold" style="color:#6F7485">
                    {{ donutTotal > 0 ? (h.displayValue / donutTotal * 100).toFixed(1) : '-' }}%
                    <span v-if="h.value == null" class="ml-0.5" style="color:#A78BFA;font-size:0.65rem">원가</span>
                  </span>
                </div>
              </div>
            </div>

            <!-- 라인 차트 -->
            <div class="lg:col-span-3 rounded-2xl p-5" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
              <p class="font-bold text-sm mb-4" style="color:#0F122B">포트폴리오 가치 추이 (최근 1개월)</p>
              <div v-if="histLoading" class="flex items-center justify-center" style="height:200px">
                <Loader2 class="w-5 h-5 animate-spin" style="color:#57E0C3" />
              </div>
              <div v-else-if="historyData" style="height:200px">
                <Line :data="historyData" :options="lineOpts" style="height:100%;width:100%" />
              </div>
              <div v-else class="flex items-center justify-center text-sm" style="height:200px;color:#6F7485">
                차트 데이터를 불러오지 못했습니다
              </div>
            </div>
          </div>

          <!-- 종목별 상세 테이블 -->
          <div class="rounded-2xl overflow-hidden" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
            <div class="px-5 py-4" style="border-bottom:1px solid #EEF1F5">
              <p class="font-bold text-sm" style="color:#0F122B">보유 종목 상세</p>
            </div>
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr style="background:#F8F9FF;border-bottom:1px solid #EEF1F5">
                    <th class="px-5 py-3 text-left font-bold" style="color:#6F7485;font-size:0.72rem">종목</th>
                    <th class="px-4 py-3 text-right font-bold" style="color:#6F7485;font-size:0.72rem">수량</th>
                    <th class="px-4 py-3 text-right font-bold" style="color:#6F7485;font-size:0.72rem">평균단가</th>
                    <th class="px-4 py-3 text-right font-bold" style="color:#6F7485;font-size:0.72rem">현재가</th>
                    <th class="px-4 py-3 text-right font-bold" style="color:#6F7485;font-size:0.72rem">평가금액</th>
                    <th class="px-4 py-3 text-right font-bold" style="color:#6F7485;font-size:0.72rem">손익</th>
                    <th class="px-4 py-3 text-right font-bold" style="color:#6F7485;font-size:0.72rem">등락</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="h in enriched" :key="h.symbol"
                    class="transition-colors hover:bg-[#F8F9FF]"
                    style="border-bottom:1px solid #EEF1F5">
                    <td class="px-5 py-3.5">
                      <p class="font-bold" style="color:#0F122B">{{ h.name }}</p>
                      <p style="font-size:0.7rem;color:#6F7485">{{ h.symbol }}</p>
                    </td>
                    <td class="px-4 py-3.5 text-right font-medium tabular-nums" style="color:#0F122B">{{ Number(h.quantity).toLocaleString() }}</td>
                    <td class="px-4 py-3.5 text-right font-medium tabular-nums" style="color:#0F122B">{{ Math.round(h.avg_price).toLocaleString() }}</td>
                    <td class="px-4 py-3.5 text-right font-bold tabular-nums" style="color:#0F122B">
                      {{ h.close != null ? Math.round(h.close).toLocaleString() : '-' }}
                    </td>
                    <td class="px-4 py-3.5 text-right font-bold tabular-nums" style="color:#0F122B">
                      {{ h.value != null ? Math.round(h.value).toLocaleString() : '-' }}
                    </td>
                    <td class="px-4 py-3.5 text-right font-bold tabular-nums">
                      <span :style="`color:${pnlColor(h.pnl)}`">
                        {{ h.pnl != null ? (h.pnl >= 0 ? '+' : '') + Math.round(h.pnl).toLocaleString() : '-' }}
                      </span>
                      <br>
                      <span class="text-xs" :style="`color:${pnlColor(h.pnlPct)}`">{{ fmtPct(h.pnlPct) }}</span>
                    </td>
                    <td class="px-4 py-3.5 text-right font-bold tabular-nums">
                      <span :style="`color:${pnlColor(h.chgPct)}`">{{ h.chgPct != null ? fmtPct(h.chgPct) : '-' }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </template>
      </div>
    </main>

    <AppFooter />
  </div>
</template>
