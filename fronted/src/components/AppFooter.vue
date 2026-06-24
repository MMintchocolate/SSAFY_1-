<script setup>
import { ExternalLink, Share2, Camera, PlayCircle } from '@lucide/vue'

const services = ['금융상품 비교', '주식 정보', '금 시세', '지점찾기', '커뮤니티']
const support  = ['고객센터', '피싱 신고 (1332)', '문의하기', '접근성 안내']
const dataSources = [
  { label: '금융감독원 (FSS)',       url: 'https://www.fss.or.kr' },
  { label: '행정안전부',             url: 'https://www.mois.go.kr' },
  { label: '금융정보분석원 (KoFIU)', url: 'https://www.kofiu.go.kr' },
  { label: '한국은행 (BOK)',         url: 'https://www.bok.or.kr' },
]
</script>

<template>
  <footer style="background:#0F122B;font-family:'Pretendard','Noto Sans KR',sans-serif">
    <div class="max-w-7xl mx-auto px-6 pt-14 pb-8">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10 mb-10">

        <!-- 브랜드 -->
        <div>
          <div class="flex items-center gap-2.5 mb-4">
            <svg width="34" height="28" viewBox="0 0 46 38" fill="none">
              <circle cx="15" cy="9" r="6" fill="#FFA726"/>
              <circle cx="31" cy="9" r="6" fill="#4ECBA8"/>
              <path d="M7 20 Q23 36 39 20" stroke="#57E0C3" stroke-width="6" stroke-linecap="round" fill="none"/>
            </svg>
            <span class="font-black text-xl" style="color:white;letter-spacing:-0.5px">moni</span>
          </div>
          <p class="text-sm leading-relaxed mb-5" style="color:#6F7485">
            금융상품 비교부터 투자 정보까지<br>한 번에 관리하는 스마트 금융 플랫폼
          </p>
          <div class="flex gap-2">
            <button class="w-9 h-9 rounded-xl flex items-center justify-center transition-colors" style="background:rgba(255,255,255,0.06)"><Share2 class="w-4 h-4" style="color:#6F7485" /></button>
            <button class="w-9 h-9 rounded-xl flex items-center justify-center transition-colors" style="background:rgba(255,255,255,0.06)"><Camera class="w-4 h-4" style="color:#6F7485" /></button>
            <button class="w-9 h-9 rounded-xl flex items-center justify-center transition-colors" style="background:rgba(255,255,255,0.06)"><PlayCircle class="w-4 h-4" style="color:#6F7485" /></button>
          </div>
        </div>

        <!-- 서비스 -->
        <div>
          <h4 class="font-bold text-sm mb-4" style="color:#57E0C3;letter-spacing:0.08em">서비스</h4>
          <ul class="space-y-2.5">
            <li v-for="s in services" :key="s">
              <a href="#" class="text-sm transition-colors" style="color:#6F7485" onmouseover="this.style.color='white'" onmouseout="this.style.color='#6F7485'">{{ s }}</a>
            </li>
          </ul>
        </div>

        <!-- 고객지원 -->
        <div>
          <h4 class="font-bold text-sm mb-4" style="color:#57E0C3;letter-spacing:0.08em">고객지원</h4>
          <ul class="space-y-2.5">
            <li v-for="s in support" :key="s">
              <a href="#" class="text-sm transition-colors" style="color:#6F7485" onmouseover="this.style.color='white'" onmouseout="this.style.color='#6F7485'">{{ s }}</a>
            </li>
          </ul>
        </div>

        <!-- 공공데이터 출처 -->
        <div>
          <h4 class="font-bold text-sm mb-4" style="color:#57E0C3;letter-spacing:0.08em">공공데이터 출처</h4>
          <ul class="space-y-2.5">
            <li v-for="src in dataSources" :key="src.label" class="flex items-start gap-1.5">
              <ExternalLink class="w-3 h-3 mt-0.5 flex-shrink-0" style="color:#57E0C3;opacity:0.5" />
              <a :href="src.url" target="_blank" rel="noopener noreferrer"
                class="text-sm transition-colors" style="color:#6F7485"
                onmouseover="this.style.color='white'" onmouseout="this.style.color='#6F7485'"
              >{{ src.label }}</a>
            </li>
          </ul>
        </div>
      </div>

      <!-- 하단 -->
      <div class="pt-6" style="border-top:1px solid rgba(255,255,255,0.07)">
        <div class="flex flex-col sm:flex-row items-center justify-between gap-4 mb-3">
          <p class="text-xs" style="color:rgba(111,116,133,0.7)">© 2026 moni Corp. All rights reserved.</p>
          <div class="flex flex-wrap gap-4 justify-center">
            <a href="#" class="text-xs transition-colors" style="color:rgba(111,116,133,0.7)" onmouseover="this.style.color='#6F7485'" onmouseout="this.style.color='rgba(111,116,133,0.7)'">이용약관</a>
            <a href="#" class="text-xs transition-colors" style="color:rgba(111,116,133,0.7)" onmouseover="this.style.color='#6F7485'" onmouseout="this.style.color='rgba(111,116,133,0.7)'">개인정보처리방침</a>
            <a href="#" class="text-xs transition-colors" style="color:rgba(111,116,133,0.7)" onmouseover="this.style.color='#6F7485'" onmouseout="this.style.color='rgba(111,116,133,0.7)'">쿠키정책</a>
            <a href="#" class="text-xs transition-colors" style="color:rgba(111,116,133,0.7)" onmouseover="this.style.color='#6F7485'" onmouseout="this.style.color='rgba(111,116,133,0.7)'">공공데이터 출처</a>
          </div>
        </div>
        <p class="text-xs text-center" style="color:rgba(111,116,133,0.5)">
          본 플랫폼은 정보 제공 목적으로만 운영되며, 투자 조언을 제공하지 않습니다. 금융 결정은 반드시 전문 재무상담사와 상담 후 진행하시기 바랍니다.
        </p>
      </div>
    </div>
  </footer>
</template>
