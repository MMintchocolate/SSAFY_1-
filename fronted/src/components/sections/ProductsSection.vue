<script setup>
import { ref } from 'vue'
import { PiggyBank, Landmark, RefreshCw, LayoutGrid, ArrowRight } from '@lucide/vue'

// TODO: API 연결 - 적금 상품 Top 3 조회 (FSS 금융상품통합비교공시 API)
const savingsProducts = ref([])

// TODO: API 연결 - 예금 상품 Top 3 조회 (FSS 금융상품통합비교공시 API)
const depositProducts = ref([])

/*  예상 데이터 구조:
    {
      bankName: string,       // 은행명
      productName: string,    // 상품명
      baseRate: number,       // 기본금리 (%)
      maxRate: number,        // 최고금리 (%)
      term: string,           // 기간 (예: '12개월')
      tags: string[],         // 태그 (예: ['모바일', '온라인'])
      rank: number,           // 순위
    }
*/
</script>

<template>
  <section id="products" class="py-24 bg-white">
    <div class="max-w-7xl mx-auto px-4 sm:px-6">

      <!-- 섹션 헤더 -->
      <div class="text-center mb-14">
        <div class="inline-flex items-center gap-2 bg-blue-50 text-blue-700 text-xs font-bold px-3 py-1.5 rounded-full mb-4 uppercase tracking-widest border border-blue-100">
          <RefreshCw class="w-3 h-3" />매일 업데이트 · 금감원 인증
        </div>
        <h2 class="text-4xl font-extrabold text-gray-900 tracking-tight mb-3">인기 금융상품</h2>
        <p class="text-gray-400 text-lg">금융감독원 공시 기준, 금리 높은 순 상위 상품</p>
      </div>

      <div class="grid lg:grid-cols-2 gap-10">

        <!-- 적금 컬럼 -->
        <div>
          <div class="flex items-center gap-3 mb-6">
            <div class="w-11 h-11 bg-blue-100 rounded-2xl flex items-center justify-center">
              <PiggyBank class="w-5 h-5 text-blue-700" />
            </div>
            <div>
              <h3 class="font-extrabold text-gray-900 text-lg">적금 Top 3</h3>
              <p class="text-sm text-gray-400">최고금리 기준 상위 적금 상품</p>
            </div>
          </div>

          <!-- 데이터 없음 (API 연결 전) -->
          <div v-if="savingsProducts.length === 0" class="space-y-4">
            <div v-for="i in 3" :key="i" class="border border-gray-100 rounded-2xl p-5 bg-slate-50">
              <div class="flex items-start justify-between mb-4">
                <div class="flex items-center gap-3">
                  <div class="w-11 h-11 rounded-xl bg-gray-200 animate-pulse"></div>
                  <div class="space-y-1.5">
                    <div class="w-20 h-3 bg-gray-200 rounded animate-pulse"></div>
                    <div class="w-36 h-4 bg-gray-200 rounded animate-pulse"></div>
                  </div>
                </div>
                <div class="w-8 h-5 bg-gray-200 rounded-full animate-pulse"></div>
              </div>
              <div class="w-32 h-8 bg-gray-200 rounded animate-pulse mb-2"></div>
              <div class="w-48 h-4 bg-gray-200 rounded animate-pulse mb-3"></div>
              <div class="flex gap-1.5">
                <div class="w-14 h-5 bg-gray-200 rounded-full animate-pulse"></div>
                <div class="w-14 h-5 bg-gray-200 rounded-full animate-pulse"></div>
              </div>
            </div>
            <p class="text-center text-sm text-gray-400 pt-2">API 연결 후 상품 정보가 표시됩니다</p>
          </div>

          <!-- 데이터 있을 때 렌더링 -->
          <div v-else class="space-y-4">
            <div
              v-for="product in savingsProducts"
              :key="product.productName"
              class="border border-gray-100 hover:border-blue-200 rounded-2xl p-5 shadow-sm cursor-pointer group transition-all duration-250 hover:-translate-y-1 hover:shadow-lg"
            >
              <div class="flex items-start justify-between mb-4">
                <div class="flex items-center gap-3">
                  <div class="w-11 h-11 rounded-xl bg-gradient-to-br from-blue-700 to-blue-900 flex items-center justify-center text-white text-xs font-black shadow">
                    {{ product.bankCode }}
                  </div>
                  <div>
                    <p class="text-xs text-gray-400 font-medium">{{ product.bankName }}</p>
                    <p class="font-bold text-gray-900 group-hover:text-blue-800 transition-colors">{{ product.productName }}</p>
                  </div>
                </div>
                <span class="bg-amber-50 text-amber-600 text-xs font-extrabold px-2.5 py-0.5 rounded-full border border-amber-200">
                  #{{ product.rank }}
                </span>
              </div>
              <div class="flex items-end gap-2 mb-1">
                <span class="text-xs text-gray-400">최고금리</span>
                <span class="text-4xl font-black text-blue-700 leading-none">{{ product.maxRate }}%</span>
                <span class="text-sm text-gray-400 mb-1">/ 연</span>
              </div>
              <p class="text-sm text-gray-400 mb-3">
                기본금리 <span class="font-semibold text-gray-600">{{ product.baseRate }}%</span> · {{ product.term }}
              </p>
              <div class="flex flex-wrap gap-1.5">
                <span
                  v-for="tag in product.tags"
                  :key="tag"
                  class="bg-blue-50 text-blue-700 text-xs font-semibold px-2.5 py-0.5 rounded-full"
                >
                  #{{ tag }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- 예금 컬럼 -->
        <div>
          <div class="flex items-center gap-3 mb-6">
            <div class="w-11 h-11 bg-indigo-100 rounded-2xl flex items-center justify-center">
              <Landmark class="w-5 h-5 text-indigo-700" />
            </div>
            <div>
              <h3 class="font-extrabold text-gray-900 text-lg">예금 Top 3</h3>
              <p class="text-sm text-gray-400">최고금리 기준 상위 정기예금 상품</p>
            </div>
          </div>

          <!-- 데이터 없음 (API 연결 전) -->
          <div v-if="depositProducts.length === 0" class="space-y-4">
            <div v-for="i in 3" :key="i" class="border border-gray-100 rounded-2xl p-5 bg-slate-50">
              <div class="flex items-start justify-between mb-4">
                <div class="flex items-center gap-3">
                  <div class="w-11 h-11 rounded-xl bg-gray-200 animate-pulse"></div>
                  <div class="space-y-1.5">
                    <div class="w-20 h-3 bg-gray-200 rounded animate-pulse"></div>
                    <div class="w-36 h-4 bg-gray-200 rounded animate-pulse"></div>
                  </div>
                </div>
                <div class="w-8 h-5 bg-gray-200 rounded-full animate-pulse"></div>
              </div>
              <div class="w-32 h-8 bg-gray-200 rounded animate-pulse mb-2"></div>
              <div class="w-48 h-4 bg-gray-200 rounded animate-pulse mb-3"></div>
              <div class="flex gap-1.5">
                <div class="w-14 h-5 bg-gray-200 rounded-full animate-pulse"></div>
                <div class="w-14 h-5 bg-gray-200 rounded-full animate-pulse"></div>
              </div>
            </div>
            <p class="text-center text-sm text-gray-400 pt-2">API 연결 후 상품 정보가 표시됩니다</p>
          </div>

          <!-- 데이터 있을 때 렌더링 -->
          <div v-else class="space-y-4">
            <div
              v-for="product in depositProducts"
              :key="product.productName"
              class="border border-gray-100 hover:border-indigo-200 rounded-2xl p-5 shadow-sm cursor-pointer group transition-all duration-250 hover:-translate-y-1 hover:shadow-lg"
            >
              <div class="flex items-start justify-between mb-4">
                <div class="flex items-center gap-3">
                  <div class="w-11 h-11 rounded-xl bg-gradient-to-br from-indigo-600 to-purple-800 flex items-center justify-center text-white text-xs font-black shadow">
                    {{ product.bankCode }}
                  </div>
                  <div>
                    <p class="text-xs text-gray-400 font-medium">{{ product.bankName }}</p>
                    <p class="font-bold text-gray-900 group-hover:text-indigo-800 transition-colors">{{ product.productName }}</p>
                  </div>
                </div>
                <span class="bg-amber-50 text-amber-600 text-xs font-extrabold px-2.5 py-0.5 rounded-full border border-amber-200">
                  #{{ product.rank }}
                </span>
              </div>
              <div class="flex items-end gap-2 mb-1">
                <span class="text-xs text-gray-400">최고금리</span>
                <span class="text-4xl font-black text-indigo-700 leading-none">{{ product.maxRate }}%</span>
                <span class="text-sm text-gray-400 mb-1">/ 연</span>
              </div>
              <p class="text-sm text-gray-400 mb-3">
                기본금리 <span class="font-semibold text-gray-600">{{ product.baseRate }}%</span> · {{ product.term }}
              </p>
              <div class="flex flex-wrap gap-1.5">
                <span
                  v-for="tag in product.tags"
                  :key="tag"
                  class="bg-indigo-50 text-indigo-700 text-xs font-semibold px-2.5 py-0.5 rounded-full"
                >
                  #{{ tag }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 더보기 CTA -->
      <div class="mt-12 text-center">
        <button class="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-blue-900 to-blue-700 text-white font-bold rounded-xl shadow-lg hover:shadow-xl hover:from-blue-950 transition-all text-sm">
          <LayoutGrid class="w-4 h-4" />전체 금융상품 보기
          <ArrowRight class="w-4 h-4" />
        </button>
        <p class="text-xs text-gray-400 mt-3">
          금리 데이터 출처: <span class="font-medium text-gray-500">금융감독원 (FSS)</span> · 매일 오전 09:00 KST 업데이트
        </p>
      </div>
    </div>
  </section>
</template>
