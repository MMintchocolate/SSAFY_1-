<script setup>
import { ref, onMounted } from 'vue'
import NavBar from '@/components/NavBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import {
  ShieldCheck, TrendingUp, MapPin, Receipt, PhoneOff,
  ChartBarBig, Users, ArrowRight, Newspaper, ExternalLink,
  Zap, AlertTriangle, Loader2,
} from '@lucide/vue'

// ─── 서비스 메뉴 ──────────────────────────────────────────────────────────────
const services = [
  { to: '/products',     icon: TrendingUp,  label: '금융상품',    desc: '예·적금 금리 비교',      color: 'bg-blue-50',    iconColor: 'text-blue-600',    border: 'border-blue-100' },
  { to: '/branches',     icon: MapPin,       label: '지점찾기',    desc: '인근 금융기관 검색',      color: 'bg-emerald-50', iconColor: 'text-emerald-600', border: 'border-emerald-100' },
  { to: '/receipts',     icon: Receipt,      label: '영수증 장부', desc: 'AI 자동 지출 분류',      color: 'bg-purple-50',  iconColor: 'text-purple-600',  border: 'border-purple-100' },
  { to: '/voicephishing',icon: PhoneOff,     label: '피싱탐지',    desc: '보이스피싱 AI 분석',      color: 'bg-red-50',     iconColor: 'text-red-600',     border: 'border-red-100' },
  { to: '/spending',     icon: ChartBarBig,  label: '지출분석',    desc: 'CSV 소비 시각화',        color: 'bg-violet-50',  iconColor: 'text-violet-600',  border: 'border-violet-100' },
  { to: '/community',    icon: Users,        label: '커뮤니티',    desc: '피싱 제보·금융 팁',       color: 'bg-orange-50',  iconColor: 'text-orange-600',  border: 'border-orange-100' },
]

// ─── Top3 뉴스 ────────────────────────────────────────────────────────────────
// { 유출: [...], 해킹: [...] }
const top3        = ref({ 유출: [], 해킹: [] })
const top3Loading = ref(true)
const top3Error   = ref(false)

const KEYWORDS = [
  { key: '유출', label: '유출 뉴스', barColor: 'bg-orange-500', badgeClass: 'bg-orange-100 text-orange-700' },
  { key: '해킹', label: '해킹 뉴스', barColor: 'bg-red-500',    badgeClass: 'bg-red-100 text-red-700' },
]

async function loadTop3() {
  top3Loading.value = true
  top3Error.value   = false
  try {
    const res = await fetch('/api/news/top3/')
    if (!res.ok) throw new Error()
    top3.value = await res.json()
  } catch {
    top3Error.value = true
  } finally {
    top3Loading.value = false
  }
}

const hasAnyNews = () => KEYWORDS.some(k => (top3.value[k.key] || []).length > 0)

function fmtDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('ko-KR', { month: 'long', day: 'numeric' })
}

const RANK_ICONS = ['🥇', '🥈', '🥉']

onMounted(loadTop3)
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <NavBar />

    <!-- ─── 히어로 ────────────────────────────────────────────────────────── -->
    <section
      class="pt-16 min-h-[52vh] flex flex-col justify-center"
      style="background: linear-gradient(135deg, #0f1f47 0%, #1e3a8a 50%, #2563eb 100%)"
    >
      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-16 text-white text-center">
        <div class="inline-flex items-center gap-2 text-xs font-bold px-3 py-1.5 rounded-full mb-6 uppercase tracking-widest border"
          style="background:rgba(29,78,216,0.4);color:#93c5fd;border-color:rgba(59,130,246,0.4)"
        >
          <Zap class="w-3 h-3" />AI 금융보안 플랫폼
        </div>
        <h1 class="text-4xl sm:text-5xl lg:text-6xl font-black leading-tight mb-5 tracking-tight">
          내 자산을<br />
          <span style="color:#93c5fd">보이스피싱</span>으로부터<br />
          안전하게
        </h1>
        <p class="text-base sm:text-lg max-w-xl mx-auto mb-8 leading-relaxed" style="color:rgba(219,234,254,0.8)">
          실시간 AI 탐지로 금융사기를 차단하고, 최신 보안 이슈를 한눈에 확인하세요.
        </p>
        <div class="flex flex-wrap justify-center gap-3">
          <RouterLink to="/voicephishing"
            class="flex items-center gap-2 px-6 py-3 bg-white font-bold rounded-xl text-sm shadow-lg hover:bg-blue-50 transition-all"
            style="color:#1e3a8a"
          >
            <ShieldCheck class="w-4 h-4" />피싱 탐지 시작
          </RouterLink>
          <RouterLink to="/news"
            class="flex items-center gap-2 px-6 py-3 font-semibold rounded-xl border text-sm transition-all"
            style="background:rgba(255,255,255,0.1);color:white;border-color:rgba(255,255,255,0.25)"
          >
            <Newspaper class="w-4 h-4" />보안 뉴스 보기
          </RouterLink>
        </div>
      </div>

      <!-- 웨이브 -->
      <svg viewBox="0 0 1440 56" fill="none" class="w-full block -mb-px">
        <path d="M0,28 C360,56 720,0 1080,28 C1260,42 1380,14 1440,28 L1440,56 L0,56 Z" fill="#f8fafc"/>
      </svg>
    </section>

    <!-- ─── 이슈 뉴스 Top 3 ────────────────────────────────────────────────── -->
    <section class="py-14 bg-slate-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6">

        <div class="flex items-end justify-between mb-7">
          <div>
            <div class="flex items-center gap-2 mb-1">
              <Newspaper class="w-5 h-5 text-blue-600" />
              <h2 class="text-xl font-black text-gray-900">최신 이슈 뉴스 Top 3</h2>
            </div>
            <p class="text-sm text-gray-500">유출·해킹 키워드 최신 보안 이슈 각 3건</p>
          </div>
          <RouterLink to="/news"
            class="flex items-center gap-1 text-sm font-semibold text-blue-600 hover:text-blue-800 transition-colors"
          >
            전체 보기 <ArrowRight class="w-4 h-4" />
          </RouterLink>
        </div>

        <!-- 로딩 -->
        <div v-if="top3Loading" class="flex justify-center py-16">
          <Loader2 class="w-7 h-7 animate-spin text-blue-400" />
        </div>

        <!-- 오류 / 뉴스 없음 -->
        <div v-else-if="top3Error || !hasAnyNews()"
          class="flex flex-col items-center justify-center py-14 gap-3 bg-white rounded-2xl border border-dashed border-gray-200"
        >
          <Newspaper class="w-10 h-10 text-gray-300" />
          <p class="text-sm text-gray-400">
            {{ top3Error ? '뉴스를 불러올 수 없습니다.' : '아직 수집된 뉴스가 없습니다.' }}
          </p>
          <RouterLink to="/news" class="text-xs font-semibold text-blue-600 hover:underline">
            보안뉴스 페이지에서 크롤링 시작하기 →
          </RouterLink>
        </div>

        <!-- 키워드별 2열 -->
        <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div v-for="kw in KEYWORDS" :key="kw.key">
            <!-- 키워드 헤더 -->
            <div class="flex items-center gap-2 mb-4">
              <span class="w-3 h-3 rounded-full flex-shrink-0" :class="kw.barColor"></span>
              <h3 class="font-bold text-gray-800">{{ kw.label }}</h3>
              <span class="text-xs text-gray-400 ml-auto">최신순</span>
            </div>

            <!-- 빈 키워드 -->
            <div v-if="!(top3[kw.key] || []).length"
              class="flex items-center justify-center h-32 bg-white rounded-xl border border-dashed border-gray-200 text-sm text-gray-400"
            >
              수집된 뉴스가 없습니다
            </div>

            <!-- 기사 카드 목록 -->
            <div v-else class="space-y-3">
              <a
                v-for="(article, idx) in top3[kw.key]" :key="article.id"
                :href="article.url" target="_blank" rel="noopener noreferrer"
                class="group flex items-start gap-3 p-4 bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
              >
                <!-- 순위 -->
                <span class="text-base font-black flex-shrink-0 mt-0.5">{{ RANK_ICONS[idx] }}</span>

                <div class="flex-1 min-w-0">
                  <h4 class="text-sm font-semibold text-gray-900 leading-snug line-clamp-2 group-hover:text-blue-700 transition-colors mb-1.5">
                    {{ article.title }}
                  </h4>
                  <!-- 요약 (있으면) -->
                  <p v-if="article.summary"
                    class="text-xs text-gray-500 leading-relaxed line-clamp-2 mb-1.5"
                  >{{ article.summary }}</p>
                  <span class="text-xs text-gray-400">{{ fmtDate(article.published_date) }}</span>
                </div>

                <ExternalLink class="w-3.5 h-3.5 flex-shrink-0 text-gray-300 group-hover:text-blue-500 transition-colors mt-1" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ─── 주요 서비스 ──────────────────────────────────────────────────────── -->
    <section class="py-14 bg-white border-t border-gray-100">
      <div class="max-w-7xl mx-auto px-4 sm:px-6">
        <h2 class="text-xl font-black text-gray-900 mb-7 flex items-center gap-2">
          <Zap class="w-5 h-5 text-blue-600" />주요 서비스
        </h2>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          <RouterLink
            v-for="svc in services" :key="svc.to"
            :to="svc.to"
            class="group flex flex-col items-center text-center gap-3 p-5 rounded-2xl border hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
            :class="[svc.color, svc.border]"
          >
            <div class="w-12 h-12 rounded-xl bg-white shadow-sm flex items-center justify-center">
              <component :is="svc.icon" class="w-5 h-5" :class="svc.iconColor" />
            </div>
            <div>
              <p class="text-sm font-bold text-gray-900">{{ svc.label }}</p>
              <p class="text-xs text-gray-500 mt-0.5 leading-snug">{{ svc.desc }}</p>
            </div>
            <ArrowRight class="w-3.5 h-3.5 text-gray-300 group-hover:text-current group-hover:translate-x-0.5 transition-all" />
          </RouterLink>
        </div>
      </div>
    </section>

    <!-- ─── 보안 팁 배너 ──────────────────────────────────────────────────────── -->
    <section class="py-10 bg-slate-50 border-t border-gray-100">
      <div class="max-w-7xl mx-auto px-4 sm:px-6">
        <div class="rounded-2xl p-6 sm:p-8 flex flex-col sm:flex-row items-start sm:items-center gap-5"
          style="background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%)"
        >
          <div class="flex-shrink-0 w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
            <AlertTriangle class="w-6 h-6 text-yellow-300" />
          </div>
          <div class="flex-1 text-white">
            <p class="font-bold text-base mb-1">금융사기 의심될 땐 즉시 신고</p>
            <p class="text-sm" style="color:rgba(219,234,254,0.8)">
              금융감독원 1332 · 경찰청 182 · 한국인터넷진흥원 118
            </p>
          </div>
          <RouterLink to="/voicephishing"
            class="flex-shrink-0 flex items-center gap-2 px-5 py-2.5 bg-white font-bold text-sm rounded-xl hover:bg-blue-50 transition-all"
            style="color:#1e3a8a"
          >
            <PhoneOff class="w-4 h-4" />지금 분석하기
          </RouterLink>
        </div>
      </div>
    </section>

    <AppFooter />
  </div>
</template>
