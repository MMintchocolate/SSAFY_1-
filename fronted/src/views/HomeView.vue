<script setup>
import NavBar from '@/components/NavBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import HeroSection from '@/components/sections/HeroSection.vue'
import { TrendingUp, MapPin, Receipt, Users, ArrowRight, PhoneOff, ChartBarBig } from '@lucide/vue'

const quickLinks = [
  {
    to: '/products',
    icon: TrendingUp,
    title: '인기 금융상품',
    desc: '적금·예금 금리 Top 3 비교',
    color: 'bg-blue-50 text-blue-700',
    iconBg: 'bg-blue-100',
  },
  {
    to: '/branches',
    icon: MapPin,
    title: '지점 찾기',
    desc: '인근 안전 금융기관 검색',
    color: 'bg-emerald-50 text-emerald-700',
    iconBg: 'bg-emerald-100',
  },
  {
    to: '/receipts',
    icon: Receipt,
    title: '영수증 장부',
    desc: 'AI 자동 지출 분류·관리',
    color: 'bg-purple-50 text-purple-700',
    iconBg: 'bg-purple-100',
  },
  {
    to: '/voicephishing',
    icon: PhoneOff,
    title: '보이스피싱 탐지',
    desc: '녹음·스크립트 AI 위험 분석',
    color: 'bg-red-50 text-red-700',
    iconBg: 'bg-red-100',
  },
  {
    to: '/spending',
    icon: ChartBarBig,
    title: '지출 분석',
    desc: 'CSV로 소비 패턴 시각화',
    color: 'bg-violet-50 text-violet-700',
    iconBg: 'bg-violet-100',
  },
  {
    to: '/community',
    icon: Users,
    title: '보안 커뮤니티',
    desc: '피싱 제보·금융 팁 공유',
    color: 'bg-orange-50 text-orange-700',
    iconBg: 'bg-orange-100',
  },
]
</script>

<template>
  <div class="min-h-screen bg-white">
    <NavBar />
    <main>
      <HeroSection />

      <!-- 빠른 이동 -->
      <section class="py-16 bg-white">
        <div class="max-w-7xl mx-auto px-4 sm:px-6">
          <h2 class="text-2xl font-extrabold text-gray-900 mb-8 text-center">주요 서비스</h2>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-5">
            <RouterLink
              v-for="link in quickLinks"
              :key="link.to"
              :to="link.to"
              class="group flex items-start gap-4 p-5 rounded-2xl border border-gray-100 hover:border-blue-200 hover:shadow-md transition-all duration-200"
              :class="link.color"
            >
              <div class="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0" :class="link.iconBg">
                <component :is="link.icon" class="w-5 h-5" />
              </div>
              <div class="flex-1 min-w-0">
                <p class="font-bold text-gray-900 mb-0.5">{{ link.title }}</p>
                <p class="text-sm text-gray-500 leading-snug">{{ link.desc }}</p>
              </div>
              <ArrowRight class="w-4 h-4 text-gray-300 group-hover:text-current group-hover:translate-x-1 transition-all mt-1 flex-shrink-0" />
            </RouterLink>
          </div>
        </div>
      </section>
    </main>
    <AppFooter />
  </div>
</template>
