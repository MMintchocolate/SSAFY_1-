<script setup>
// @ts-nocheck
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import { Line } from "vue-chartjs";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import NavBar from "@/components/NavBar.vue";
import AppFooter from "@/components/AppFooter.vue";
import {
  TrendingUp,
  MapPin,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Star,
  Search,
  Loader2,
  Newspaper,
} from "@lucide/vue";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

// ─── 주요 기능 카드 ───────────────────────────────────────────────────────────
const features = [
  {
    to: "/app/products",
    title: "금융상품 비교",
    desc: "다양한 금융상품을 한눈에 비교해보세요",
    icon: Search,
    bg: "#DFFAF4",
    iconColor: "#0D9B7A",
  },
  {
    to: "/app/products",
    title: "맞춤형 금융 추천",
    desc: "AI가 분석한 맞춤형 금융상품을 추천해드려요",
    icon: Star,
    bg: "#FFF8E6",
    iconColor: "#B8860B",
  },
  {
    to: "/app/stocks",
    title: "실시간 주식 정보",
    desc: "국내외 주식 정보를 실시간으로 확인할 수 있어요",
    icon: TrendingUp,
    bg: "#EEF1F5",
    iconColor: "#3B4FD8",
  },
  {
    to: "/app/branches",
    title: "은행 및 ATM 찾기",
    desc: "내 주변 은행과 ATM 위치를 쉽게 찾아보세요",
    icon: MapPin,
    bg: "#F5F0FF",
    iconColor: "#7C3AED",
  },
];

// 우선주 등 로고가 없는 종목 → 모종목 코드로 대체
const LOGO_CODE_MAP = { '005935': '005930' }
function logoCode(symbol) {
  const code = symbol.replace('.KS', '').replace('.KQ', '')
  return LOGO_CODE_MAP[code] ?? code
}

// ─── 실시간 주식 (시가총액 상위) ──────────────────────────────────────────────
const movers = ref({ marcap: [], up: [], down: [] });
const moversLoading = ref(true);
const activeIdx = ref(0);
let cycleTimer = null;

const topStocks = computed(() => movers.value.marcap.slice(0, 5));
const activeStock = computed(() => topStocks.value[activeIdx.value] ?? null);
const otherStocks = computed(() =>
  topStocks.value
    .map((s, i) => ({ ...s, rank: i }))
    .filter((s) => s.rank !== activeIdx.value)
);

function startCycle() {
  if (cycleTimer) clearInterval(cycleTimer);
  cycleTimer = setInterval(() => {
    if (!topStocks.value.length) return;
    activeIdx.value = (activeIdx.value + 1) % topStocks.value.length;
  }, 5000);
}

async function loadMovers() {
  moversLoading.value = true;
  try {
    const res = await fetch("/api/stocks/market-movers/");
    movers.value = await res.json();
  } catch {
    movers.value = { volume: [], up: [], down: [] };
  } finally {
    moversLoading.value = false;
  }
  if (topStocks.value.length) startCycle();
}

function prevStock() {
  activeIdx.value =
    (activeIdx.value - 1 + topStocks.value.length) % topStocks.value.length;
  startCycle();
}
function nextStock() {
  activeIdx.value = (activeIdx.value + 1) % topStocks.value.length;
  startCycle();
}

// ─── 코스피 지수 차트 ─────────────────────────────────────────────────────────
const indexData = ref(null);
const kospiHistory = ref([]);
const kospiPeriod = ref("1mo");
const kospiLoading = ref(false);
const kospiCache = new Map();

const KOSPI_PERIODS = [
  { label: "1일", value: "1d" },
  { label: "1주", value: "1wk" },
  { label: "1개월", value: "1mo" },
  { label: "3개월", value: "3mo" },
  { label: "1년", value: "1y" },
];

async function loadIndex() {
  try {
    const res = await fetch("/api/stocks/index/");
    indexData.value = await res.json();
    const hist = indexData.value?.kospi?.history;
    if (hist?.length) {
      kospiHistory.value = hist;
      kospiCache.set("index", hist);
    }
  } catch {
    indexData.value = null;
  }
}

async function fetchKospiHistory(period) {
  if (kospiCache.has(period)) {
    kospiHistory.value = kospiCache.get(period);
    return;
  }
  kospiLoading.value = true;
  try {
    const res = await fetch(`/api/stocks/%5EKS11/history/?period=${period}`);
    const data = await res.json();
    const list = Array.isArray(data) ? data : [];
    if (list.length) {
      kospiCache.set(period, list);
      kospiHistory.value = list;
    } else {
      // 실패 시 index 데이터 fallback
      const fallback = indexData.value?.kospi?.history;
      if (fallback?.length) kospiHistory.value = fallback;
    }
  } catch {
    const fallback = indexData.value?.kospi?.history;
    if (fallback?.length) kospiHistory.value = fallback;
  } finally {
    kospiLoading.value = false;
  }
}

watch(kospiPeriod, (period) => fetchKospiHistory(period));

const kospiIsUp = computed(() => {
  const p = kospiHistory.value.map((d) => d.close);
  return p.length >= 2 && p[p.length - 1] >= p[0];
});

const kospiChartData = computed(() => {
  const prices = kospiHistory.value.map((d) => d.close);
  const labels = kospiHistory.value.map((d) => (d.date || "").slice(5));
  return {
    labels,
    datasets: [
      {
        label: "KOSPI",
        data: prices,
        borderColor: kospiIsUp.value ? "#E5323B" : "#3B7FED",
        backgroundColor: kospiIsUp.value
          ? "rgba(229,50,59,0.07)"
          : "rgba(59,127,237,0.07)",
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.3,
        fill: true,
      },
    ],
  };
});

const chartOpts = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: { mode: "index", intersect: false },
  },
  scales: {
    x: {
      grid: { display: false },
      ticks: { maxTicksLimit: 6, font: { size: 10 }, color: "#6F7485" },
      border: { display: false },
    },
    y: {
      grid: { color: "rgba(0,0,0,0.04)" },
      ticks: { font: { size: 10 }, color: "#6F7485" },
      border: { display: false },
    },
  },
  animation: { duration: 300 },
};

// ─── 금융 뉴스 TOP3 ───────────────────────────────────────────────────────────
const financialNews = ref([]);
const newsLoading = ref(false);
const NEWS_COLORS = ["#DFFAF4", "#FFF8E6", "#F0EDFF"];

async function loadFinancialNews() {
  newsLoading.value = true;
  try {
    const res = await fetch("/api/news/stock/?q=금융경제&display=3");
    const data = await res.json();
    financialNews.value = (data.results || []).slice(0, 3);
  } catch {
    financialNews.value = [];
  } finally {
    newsLoading.value = false;
  }
}

function fmtPubDate(str) {
  if (!str) return "";
  const d = new Date(str);
  if (isNaN(d.getTime())) return str.slice(0, 10);
  return d.toLocaleDateString("ko-KR", { month: "long", day: "numeric" });
}

onMounted(() => {
  loadMovers();
  loadIndex();
  loadFinancialNews();
});
onUnmounted(() => {
  if (cycleTimer) clearInterval(cycleTimer);
});
</script>

<template>
  <div
    class="min-h-screen bg-white"
    style="font-family: 'Pretendard', 'Noto Sans KR', sans-serif"
  >
    <NavBar />

    <!-- ═══════════════════════ HERO ═══════════════════════ -->
    <section
      class="relative overflow-hidden"
      style="
        padding-top: 64px;
        min-height: 520px;
        background: linear-gradient(
          90deg,
          #fffdf9 0%,
          #ffffff 50%,
          #f2fffb 100%
        );
      "
    >
      <!-- 배경 glow blobs -->
      <div
        class="absolute pointer-events-none"
        style="
          right: 8%;
          top: 8%;
          width: 360px;
          height: 360px;
          background: rgba(87, 224, 195, 0.1);
          border-radius: 50%;
          filter: blur(70px);
        "
      ></div>
      <div
        class="absolute pointer-events-none"
        style="
          right: 3%;
          bottom: 10%;
          width: 220px;
          height: 220px;
          background: rgba(255, 215, 106, 0.13);
          border-radius: 50%;
          filter: blur(55px);
        "
      ></div>
      <div
        class="absolute pointer-events-none"
        style="
          left: 3%;
          top: 25%;
          width: 180px;
          height: 180px;
          background: rgba(87, 224, 195, 0.07);
          border-radius: 50%;
          filter: blur(45px);
        "
      ></div>
      <!-- 왼쪽 노란 glow -->
      <div
        class="absolute pointer-events-none"
        style="
          left: 0%;
          top: 5%;
          width: 240px;
          height: 240px;
          background: rgba(255, 167, 38, 0.1);
          border-radius: 50%;
          filter: blur(60px);
        "
      ></div>
      <div
        class="absolute pointer-events-none"
        style="
          left: 5%;
          bottom: 8%;
          width: 140px;
          height: 140px;
          background: rgba(255, 215, 106, 0.12);
          border-radius: 50%;
          filter: blur(40px);
        "
      ></div>

      <div
        class="max-w-[1400px] mx-auto px-6 flex items-center gap-8"
        style="min-height: 456px"
      >
        <!-- ── Left ── -->
        <div class="flex-1 min-w-0 py-14">
          <h1
            class="font-extrabold leading-[1.15] mb-6"
            style="
              font-size: clamp(2rem, 3.6vw, 3rem);
              color: #0f122b;
              font-weight: 800;
            "
          >
            금융상품 <span style="color: #57e0c3">비교</span>부터<br />
            <span style="color: #57e0c3">투자 정보</span>까지 한 번에
          </h1>

          <p
            class="mb-9 leading-relaxed"
            style="font-size: 1.05rem; color: #6f7485; max-width: 420px"
          >
            나에게 맞는 금융상품을 찾고,<br />
            투자 정보를 확인하며,<br />
            자산을 효율적으로 관리하세요.
          </p>

          <div class="flex items-center gap-3 flex-wrap">
            <RouterLink
              to="/app/products"
              class="inline-flex items-center gap-2 px-7 py-3.5 rounded-2xl font-bold text-white transition-all hover:opacity-90 active:scale-95"
              style="
                background: #0f122b;
                font-size: 0.95rem;
                box-shadow: 0 4px 20px rgba(15, 18, 43, 0.25);
              "
            >
              시작하기 →
            </RouterLink>
            <RouterLink
              to="/intro"
              class="inline-flex items-center gap-2 px-7 py-3.5 rounded-2xl font-semibold transition-all hover:bg-gray-50 active:scale-95"
              style="
                background: white;
                border: 1.5px solid #eef1f5;
                color: #0f122b;
                font-size: 0.95rem;
              "
            >
              서비스 둘러보기
            </RouterLink>
          </div>
        </div>

        <!-- ── Right: Hero image ── -->
        <div
          class="flex-1 hidden md:flex items-center justify-end relative self-stretch"
        >
          <img
            src="/hero2.png"
            alt="hero"
            class="h-full object-cover"
            style="
              width: 180%;
              max-width: 825px;
              pointer-events: none;
              user-select: none;
              mix-blend-mode: multiply;
            "
          />
        </div>
      </div>
    </section>

    <!-- ═══════════════════════ MAIN CONTENT ═══════════════════════ -->
    <div class="max-w-[1520px] mx-auto px-6 pb-12" style="margin-top: 32px">
      <!-- Row 1: 주요기능 + 실시간주식 -->
      <div class="flex flex-col lg:flex-row gap-4 mb-4">
        <!-- ── 주요 기능 ── -->
        <div
          class="lg:flex-[5] rounded-[24px] p-4 transition-all duration-300 hover:-translate-y-1 flex flex-col"
          style="
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(15, 18, 43, 0.05);
            box-shadow: 0 8px 32px rgba(15, 18, 43, 0.05),
              0 2px 8px rgba(15, 18, 43, 0.03);
          "
        >
          <h2
            class="font-bold text-sm mb-3 flex-shrink-0"
            style="color: #0f122b"
          >
            주요 기능
          </h2>
          <div class="grid grid-cols-2 gap-2 flex-1">
            <RouterLink
              v-for="feat in features"
              :key="feat.title"
              :to="feat.to"
              class="group flex items-center gap-3 p-4 rounded-2xl transition-all duration-300 hover:-translate-y-1 hover:shadow-sm"
              style="background: #fcfcfc; border: 1px solid #eef1f5"
            >
              <div
                class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-transform duration-300 group-hover:scale-110"
                :style="{ background: feat.bg }"
              >
                <component
                  :is="feat.icon"
                  class="w-5 h-5"
                  :style="{ color: feat.iconColor }"
                />
              </div>
              <div class="min-w-0">
                <p class="font-bold text-sm" style="color: #0f122b">
                  {{ feat.title }}
                </p>
                <p
                  class="mt-0.5 leading-tight"
                  style="color: #6f7485; font-size: 0.75rem"
                >
                  {{ feat.desc }}
                </p>
              </div>
            </RouterLink>
          </div>
        </div>

        <!-- ── 실시간 주식 ── -->
        <div
          class="lg:flex-[7] rounded-[24px] p-4 transition-all duration-300 hover:-translate-y-1"
          style="
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(15, 18, 43, 0.05);
            box-shadow: 0 8px 32px rgba(15, 18, 43, 0.05),
              0 2px 8px rgba(15, 18, 43, 0.03);
          "
        >
          <div class="flex items-center justify-between mb-3">
            <h2 class="font-bold text-sm" style="color: #0f122b">
              실시간 주식
            </h2>
            <RouterLink
              to="/app/stocks"
              class="text-xs font-semibold flex items-center gap-1 transition-opacity hover:opacity-60"
              style="color: #6f7485"
            >
              전체 보기 <ArrowRight class="w-3 h-3" />
            </RouterLink>
          </div>

          <!-- Loading -->
          <div
            v-if="moversLoading"
            class="flex items-center justify-center h-40"
          >
            <Loader2 class="w-5 h-5 animate-spin" style="color: #57e0c3" />
          </div>

          <div v-else-if="topStocks.length" class="flex gap-4 items-stretch">
            <!-- ── 왼쪽: 활성 카드 + 하단 4종목 ── -->
            <div
              class="flex-shrink-0 flex flex-col gap-3 justify-center"
              style="width: 42%"
            >
              <!-- 활성 카드 (자동 순환) -->
              <div
                class="rounded-2xl p-4 flex-shrink-0"
                style="
                  background: white;
                  box-shadow: 0 4px 20px rgba(15, 18, 43, 0.08);
                  border: 1px solid rgba(15, 18, 43, 0.04);
                "
              >
                <div class="flex items-center gap-3 mb-2">
                  <div class="w-9 h-9 rounded-xl overflow-hidden flex-shrink-0 flex items-center justify-center" style="background:#F8F9FF;border:1px solid #EEF1F5">
                    <img
                      :src="`https://static.toss.im/png-icons/securities/icn-sec-fill-${logoCode(activeStock?.symbol ?? '')}.png`"
                      :alt="activeStock?.name"
                      class="w-full h-full object-cover"
                      @error="e => { e.target.style.display='none'; e.target.nextElementSibling.style.display='flex' }"
                    />
                    <span class="font-black hidden items-center justify-center w-full h-full" style="font-size:0.65rem;color:#0F122B">
                      {{ activeStock?.name?.slice(0,2) }}
                    </span>
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="font-black truncate" style="font-size:0.95rem;color:#0F122B">{{ activeStock?.name }}</p>
                    <span class="inline-flex items-center px-2 py-0.5 rounded-full font-bold" style="background:#DFFAF4;color:#0D9B7A;font-size:0.62rem">시총 {{ activeIdx + 1 }}위</span>
                  </div>
                </div>
                <div class="flex items-baseline gap-2">
                  <span
                    class="font-black tabular-nums"
                    style="font-size: 1.3rem; color: #0f122b; line-height: 1"
                  >
                    {{
                      activeStock?.close != null
                        ? Math.round(activeStock.close).toLocaleString()
                        : "-"
                    }}
                  </span>
                  <span
                    class="font-bold tabular-nums"
                    style="font-size: 0.8rem"
                    :style="{
                      color:
                        (activeStock?.change_pct ?? 0) >= 0
                          ? '#E5323B'
                          : '#3B7FED',
                    }"
                  >
                    {{
                      activeStock?.change_pct != null
                        ? (activeStock.change_pct >= 0 ? "▲ " : "▼ ") +
                          Math.abs(activeStock.change_pct).toFixed(2) +
                          "%"
                        : ""
                    }}
                  </span>
                </div>
              </div>

              <!-- 하단 4슬롯 가로 (active 제외한 나머지) -->
              <div class="flex gap-2">
                <div
                  v-for="s in otherStocks"
                  :key="s.symbol"
                  class="flex-1 text-left px-2 py-2 rounded-xl min-w-0"
                  style="background: #f8f9ff"
                >
                  <div class="w-7 h-7 rounded-lg overflow-hidden mb-1 flex items-center justify-center" style="background:white;border:1px solid #EEF1F5">
                    <img
                      :src="`https://static.toss.im/png-icons/securities/icn-sec-fill-${logoCode(s.symbol)}.png`"
                      :alt="s.name"
                      class="w-full h-full object-cover"
                      @error="e => { e.target.style.display='none'; e.target.nextElementSibling.style.display='flex' }"
                    />
                    <span class="font-black hidden items-center justify-center w-full h-full" style="font-size:0.55rem;color:#0F122B">
                      {{ s.name?.slice(0,2) }}
                    </span>
                  </div>
                  <p class="font-black tabular-nums mb-0.5" style="font-size:0.62rem;color:#6f7485">{{ s.rank + 1 }}위</p>
                  <p class="font-bold truncate mb-1" style="font-size:0.75rem;color:#0f122b">{{ s.name }}</p>
                  <p class="font-bold tabular-nums mb-0.5" style="font-size:0.75rem;color:#0f122b">
                    {{ s.close != null ? Math.round(s.close).toLocaleString() : "-" }}
                  </p>
                  <p class="font-bold tabular-nums" style="font-size:0.72rem" :style="{ color: (s.change_pct ?? 0) >= 0 ? '#E5323B' : '#3B7FED' }">
                    {{ s.change_pct != null ? (s.change_pct >= 0 ? "▲" : "▼") + Math.abs(s.change_pct).toFixed(2) + "%" : "-" }}
                  </p>
                </div>
              </div>
            </div>

            <!-- ── 오른쪽: 코스피 차트 ── -->
            <div class="flex-1 flex flex-col gap-2">
              <div class="flex items-baseline gap-2 flex-wrap">
                <span
                  class="font-bold"
                  style="font-size: 0.75rem; color: #6f7485"
                  >코스피</span
                >
                <span
                  class="font-black tabular-nums"
                  style="font-size: 1.3rem; color: #0f122b; line-height: 1"
                >
                  {{
                    indexData?.kospi?.value != null
                      ? Number(indexData.kospi.value).toLocaleString("ko-KR", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })
                      : "—"
                  }}
                </span>
                <span
                  v-if="indexData?.kospi?.change_pct != null"
                  class="font-bold tabular-nums"
                  style="font-size: 0.8rem"
                  :style="{
                    color:
                      indexData.kospi.change_pct >= 0 ? '#E5323B' : '#3B7FED',
                  }"
                >
                  {{
                    (indexData.kospi.change_pct >= 0 ? "▲ " : "▼ ") +
                    Math.abs(indexData.kospi.change_pct).toFixed(2) +
                    "%"
                  }}
                </span>
              </div>
              <div class="flex items-center gap-1.5 flex-wrap">
                <button
                  v-for="p in KOSPI_PERIODS"
                  :key="p.value"
                  @click="kospiPeriod = p.value"
                  class="px-3 py-1 rounded-full font-bold transition-all"
                  style="font-size: 0.72rem"
                  :style="
                    kospiPeriod === p.value
                      ? 'background:#0F122B;color:white'
                      : 'background:#F8F9FF;color:#6F7485'
                  "
                >
                  {{ p.label }}
                </button>
              </div>
              <div class="relative flex-1" style="min-height: 200px">
                <div
                  v-if="kospiLoading"
                  class="absolute inset-0 flex items-center justify-center"
                >
                  <Loader2
                    class="w-4 h-4 animate-spin"
                    style="color: #57e0c3"
                  />
                </div>
                <Line
                  v-else-if="kospiHistory.length"
                  :data="kospiChartData"
                  :options="chartOpts"
                  style="height: 100%; width: 100%"
                />
                <div
                  v-else
                  class="absolute inset-0 flex items-center justify-center"
                  style="font-size: 0.75rem; color: #6f7485"
                >
                  차트 데이터 없음
                </div>
              </div>
            </div>
          </div>

          <div
            v-else
            class="flex items-center justify-center h-40"
            style="font-size: 0.8rem; color: #6f7485"
          >
            데이터를 불러오는 중...
          </div>
        </div>
      </div>

      <!-- Row 2: 금융 뉴스 TOP3 -->
      <div
        class="rounded-[24px] p-4 transition-all duration-300 hover:-translate-y-1"
        style="
          background: rgba(255, 255, 255, 0.9);
          backdrop-filter: blur(12px);
          border: 1px solid rgba(15, 18, 43, 0.05);
          box-shadow: 0 8px 32px rgba(15, 18, 43, 0.05),
            0 2px 8px rgba(15, 18, 43, 0.03);
        "
      >
        <div class="flex items-center justify-between mb-3">
          <h2 class="font-bold text-sm" style="color: #0f122b">
            금융 뉴스 TOP3
          </h2>
          <RouterLink
            to="/app/news"
            class="text-xs font-semibold flex items-center gap-1 transition-opacity hover:opacity-60"
            style="color: #6f7485"
          >
            더보기 <ArrowRight class="w-3 h-3" />
          </RouterLink>
        </div>

        <!-- Loading -->
        <div v-if="newsLoading" class="flex items-center justify-center h-28">
          <Loader2 class="w-5 h-5 animate-spin" style="color: #57e0c3" />
        </div>

        <!-- News cards -->
        <div
          v-else-if="financialNews.length"
          class="grid grid-cols-1 sm:grid-cols-3 gap-3"
        >
          <a
            v-for="(item, i) in financialNews"
            :key="i"
            :href="item.url"
            target="_blank"
            rel="noopener noreferrer"
            class="group flex gap-3 p-3 rounded-2xl overflow-hidden transition-all duration-300 cursor-pointer hover:-translate-y-0.5 hover:shadow-sm items-start"
            style="border: 1px solid #eef1f5"
          >
            <!-- 컬러 아이콘 박스 -->
            <div
              class="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
              :style="{ background: NEWS_COLORS[i] }"
            >
              <Newspaper class="w-5 h-5 opacity-40" style="color: #0f122b" />
            </div>
            <!-- Content -->
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-1.5 mb-1">
                <span
                  class="font-semibold"
                  style="color: #57e0c3; font-size: 0.65rem"
                  >금융뉴스</span
                >
                <span style="color: #eef1f5; font-size: 0.65rem">·</span>
                <span style="color: #6f7485; font-size: 0.65rem">{{
                  fmtPubDate(item.pub_date)
                }}</span>
              </div>
              <h3
                class="font-bold leading-snug line-clamp-2 group-hover:opacity-70 transition-opacity"
                style="color: #0f122b; font-size: 0.8rem"
              >
                {{ item.title }}
              </h3>
            </div>
          </a>
        </div>

        <!-- 뉴스 없음 -->
        <div
          v-else
          class="flex flex-col items-center justify-center py-8 gap-1.5"
        >
          <Newspaper class="w-6 h-6 opacity-20" style="color: #6f7485" />
          <p style="font-size: 0.8rem; color: #6f7485">
            금융 뉴스를 불러오는 중입니다.
          </p>
        </div>
      </div>
    </div>

    <AppFooter />
  </div>
</template>

<style scoped>
@keyframes heroFloat {
  0%,
  100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-18px) rotate(4deg);
  }
}
@keyframes heroFloatRev {
  0%,
  100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(14px);
  }
}

.hero-float {
  animation: heroFloat 7s ease-in-out infinite;
}
.hero-float-rev {
  animation: heroFloatRev 6s ease-in-out infinite;
}
</style>
