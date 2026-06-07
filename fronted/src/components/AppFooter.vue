<script setup>
import { ShieldCheck, ExternalLink, Share2, Camera, PlayCircle } from '@lucide/vue'

const services = ['금융상품', '보이스피싱 탐지', '영수증 장부', '지점찾기', '보안 커뮤니티']
const support  = ['고객센터', '피싱 신고 (1332)', '문의하기', '접근성 안내']
const dataSources = [
  '금융감독원 (FSS)',
  '행정안전부',
  '금융정보분석원 (KoFIU)',
  '한국은행 (BOK)',
]
</script>

<template>
  <footer class="bg-gray-950 text-gray-400">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 pt-14 pb-8">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10 mb-10">

        <!-- 브랜드 -->
        <div>
          <div class="flex items-center gap-2.5 mb-4">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-700 to-blue-500 flex items-center justify-center">
              <ShieldCheck class="w-5 h-5 text-white" />
            </div>
            <span class="text-lg font-black text-white">Safe<span class="text-blue-400">Finance</span></span>
          </div>
          <p class="text-sm text-gray-500 leading-relaxed mb-5">
            AI 기반 금융보안 플랫폼.<br>보이스피싱과 금융사기로부터 고객을 보호합니다.
          </p>
          <div class="flex gap-2">
            <button class="w-9 h-9 bg-gray-800 hover:bg-gray-700 rounded-xl flex items-center justify-center transition-colors"><Share2 class="w-4 h-4" /></button>
            <button class="w-9 h-9 bg-gray-800 hover:bg-gray-700 rounded-xl flex items-center justify-center transition-colors"><Camera class="w-4 h-4" /></button>
            <button class="w-9 h-9 bg-gray-800 hover:bg-gray-700 rounded-xl flex items-center justify-center transition-colors"><PlayCircle class="w-4 h-4" /></button>
          </div>
        </div>

        <!-- 서비스 -->
        <div>
          <h4 class="text-white font-bold text-sm mb-4 uppercase tracking-widest">서비스</h4>
          <ul class="space-y-2.5">
            <li v-for="s in services" :key="s">
              <a href="#" class="text-sm text-gray-500 hover:text-white transition-colors">{{ s }}</a>
            </li>
          </ul>
        </div>

        <!-- 고객지원 -->
        <div>
          <h4 class="text-white font-bold text-sm mb-4 uppercase tracking-widest">고객지원</h4>
          <ul class="space-y-2.5">
            <li v-for="s in support" :key="s">
              <a href="#" class="text-sm text-gray-500 hover:text-white transition-colors">{{ s }}</a>
            </li>
          </ul>
        </div>

        <!-- 공공데이터 출처 -->
        <div>
          <h4 class="text-white font-bold text-sm mb-4 uppercase tracking-widest">공공데이터 출처</h4>
          <ul class="space-y-2.5">
            <li v-for="src in dataSources" :key="src" class="flex items-start gap-1.5">
              <ExternalLink class="w-3 h-3 mt-0.5 flex-shrink-0 text-gray-600" />
              <a href="#" class="text-sm text-gray-500 hover:text-white transition-colors">{{ src }}</a>
            </li>
          </ul>
        </div>
      </div>

      <div class="border-t border-gray-800 pt-6">
        <div class="flex flex-col sm:flex-row items-center justify-between gap-4 mb-3">
          <p class="text-xs text-gray-600">© 2026 SafeFinance Corp. All rights reserved.</p>
          <div class="flex flex-wrap gap-4 justify-center">
            <a href="#" class="text-xs text-gray-600 hover:text-gray-300 transition-colors">이용약관</a>
            <a href="#" class="text-xs text-gray-600 hover:text-gray-300 transition-colors">개인정보처리방침</a>
            <a href="#" class="text-xs text-gray-600 hover:text-gray-300 transition-colors">쿠키정책</a>
            <a href="#" class="text-xs text-gray-600 hover:text-gray-300 transition-colors">공공데이터 출처</a>
          </div>
        </div>
        <p class="text-xs text-gray-700 text-center">
          본 플랫폼은 정보 제공 목적으로만 운영되며, 투자 조언을 제공하지 않습니다. 금융 결정은 반드시 전문 재무상담사와 상담 후 진행하시기 바랍니다.
        </p>
      </div>
    </div>
  </footer>
</template>
