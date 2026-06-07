<script setup>
import { ref } from 'vue'
import { Users, PencilLine, Eye, Heart, MessageCircle, ShieldAlert, CheckCircle, Star, Flame } from '@lucide/vue'

const tabs = ['전체', '피싱 제보', '금융 팁', '상품 리뷰', 'Q&A']
const activeTab = ref('전체')

// TODO: API 연결 - 커뮤니티 게시글 조회 (탭 필터 포함)
const posts = ref([])
/*  예상 구조:
    [
      {
        id: number,
        author: { initials: string, colorClass: string },
        category: string,        // '피싱 제보' | '금융 팁' | '상품 리뷰' | 'Q&A'
        title: string,
        preview: string,
        likeCount: number,
        viewCount: number,
        replyCount: number,
        isHot: boolean,
        isVerifiedPhishing: boolean,
        isExpertAnswered: boolean,
        rating: number | null,   // 별점 (상품 리뷰만)
        createdAt: string,       // '2시간 전', '어제' 등
      }
    ]
*/

// TODO: API 연결 - 탭 변경 시 재조회
function changeTab(tab) {
  activeTab.value = tab
  // fetchPosts(tab)
}

// TODO: API 연결 - 좋아요 토글
function toggleLike(post) {
  // API 호출 후 likeCount 업데이트
  console.log('좋아요:', post.id)
}
</script>

<template>
  <section id="community" class="py-24 bg-white">
    <div class="max-w-7xl mx-auto px-4 sm:px-6">

      <!-- 섹션 헤더 -->
      <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-6 mb-10">
        <div>
          <div class="inline-flex items-center gap-2 bg-blue-50 text-blue-700 text-xs font-bold px-3 py-1.5 rounded-full mb-3 uppercase tracking-widest border border-blue-100">
            <Users class="w-3 h-3" />커뮤니티
          </div>
          <h2 class="text-4xl font-extrabold text-gray-900 tracking-tight">보안 커뮤니티</h2>
          <p class="text-gray-400 mt-2 text-lg">피싱 제보, 금융 팁, 상품 리뷰를 공유하세요</p>
        </div>
        <!-- TODO: 글쓰기 기능 구현 (로그인 필요) -->
        <button class="inline-flex items-center gap-2 px-5 py-3 bg-gradient-to-r from-blue-900 to-blue-700 text-white font-bold rounded-xl shadow-md hover:shadow-lg hover:from-blue-950 transition-all text-sm whitespace-nowrap">
          <PencilLine class="w-4 h-4" />글쓰기
        </button>
      </div>

      <!-- 카테고리 탭 -->
      <div class="flex gap-2 mb-7 overflow-x-auto pb-1">
        <button
          v-for="tab in tabs"
          :key="tab"
          @click="changeTab(tab)"
          class="px-4 py-2 text-xs font-bold rounded-xl whitespace-nowrap transition-all"
          :class="activeTab === tab
            ? 'bg-blue-800 text-white'
            : 'bg-gray-100 text-gray-500 hover:bg-gray-200'"
        >
          {{ tab }}
        </button>
      </div>

      <!-- 게시글 목록 -->
      <!-- 데이터 없음 -->
      <div v-if="posts.length === 0" class="space-y-3">
        <!-- 스켈레톤 -->
        <div v-for="i in 5" :key="i" class="border border-gray-100 rounded-2xl p-5">
          <div class="flex items-start gap-4">
            <div class="w-10 h-10 bg-gray-200 rounded-xl animate-pulse flex-shrink-0"></div>
            <div class="flex-1 space-y-2">
              <div class="flex gap-2">
                <div class="w-16 h-4 bg-gray-200 rounded-full animate-pulse"></div>
                <div class="w-12 h-4 bg-gray-200 rounded animate-pulse"></div>
              </div>
              <div class="w-3/4 h-5 bg-gray-200 rounded animate-pulse"></div>
              <div class="w-full h-4 bg-gray-200 rounded animate-pulse"></div>
              <div class="flex gap-4 pt-1">
                <div class="w-12 h-4 bg-gray-200 rounded animate-pulse"></div>
                <div class="w-12 h-4 bg-gray-200 rounded animate-pulse"></div>
                <div class="w-16 h-4 bg-gray-200 rounded animate-pulse"></div>
              </div>
            </div>
          </div>
        </div>
        <p class="text-center text-sm text-gray-400 pt-4">API 연결 후 게시글이 표시됩니다</p>
      </div>

      <!-- 데이터 있을 때 렌더링 -->
      <div v-else class="space-y-3">
        <div
          v-for="post in posts"
          :key="post.id"
          class="border rounded-2xl p-5 cursor-pointer transition-all duration-200 hover:shadow-md"
          :class="post.isHot ? 'border-red-100 bg-red-50/20 hover:bg-red-50/40' : 'border-gray-100 hover:bg-blue-50/30'"
        >
          <div class="flex items-start gap-4">
            <!-- 아바타 -->
            <div class="w-10 h-10 rounded-xl flex items-center justify-center text-white text-sm font-extrabold flex-shrink-0" :class="post.author.colorClass">
              {{ post.author.initials }}
            </div>

            <div class="flex-1 min-w-0">
              <!-- 메타 -->
              <div class="flex flex-wrap items-center gap-2 mb-2">
                <span v-if="post.isHot" class="bg-red-100 text-red-600 text-xs font-extrabold px-2 py-0.5 rounded-full flex items-center gap-1">
                  <Flame class="w-2.5 h-2.5" />HOT
                </span>
                <span class="text-xs font-semibold px-2 py-0.5 rounded-full border"
                  :class="{
                    'bg-orange-50 text-orange-600 border-orange-200': post.category === '피싱 제보',
                    'bg-emerald-50 text-emerald-700 border-emerald-200': post.category === '금융 팁',
                    'bg-purple-50 text-purple-700 border-purple-200': post.category === '상품 리뷰',
                    'bg-teal-50 text-teal-700 border-teal-200': post.category === 'Q&A',
                  }"
                >
                  {{ post.category }}
                </span>
                <span class="text-xs text-gray-400">{{ post.createdAt }}</span>
              </div>

              <!-- 제목 -->
              <h4 class="font-bold text-gray-900 mb-1.5 leading-snug hover:text-blue-800 transition-colors">
                {{ post.title }}
              </h4>
              <p class="text-sm text-gray-500 line-clamp-2">{{ post.preview }}</p>

              <!-- 하단 통계 -->
              <div class="flex flex-wrap items-center gap-4 mt-3">
                <button @click.stop="toggleLike(post)" class="flex items-center gap-1.5 text-sm text-gray-400 hover:text-red-500 transition-colors">
                  <Heart class="w-4 h-4" />{{ post.likeCount }}
                </button>
                <span class="flex items-center gap-1.5 text-sm text-gray-400">
                  <Eye class="w-4 h-4" />{{ post.viewCount.toLocaleString() }}
                </span>
                <span class="flex items-center gap-1.5 text-sm text-gray-400">
                  <MessageCircle class="w-4 h-4" />{{ post.replyCount }}
                </span>

                <!-- 별점 (상품 리뷰) -->
                <div v-if="post.rating" class="ml-auto flex gap-0.5">
                  <Star v-for="n in 5" :key="n" class="w-3.5 h-3.5" :class="n <= post.rating ? 'text-yellow-400 fill-yellow-400' : 'text-gray-200 fill-gray-200'" />
                </div>
                <!-- 피싱 확인 배지 -->
                <span v-else-if="post.isVerifiedPhishing" class="ml-auto flex items-center gap-1 text-xs text-blue-600 font-bold">
                  <ShieldAlert class="w-3.5 h-3.5" />피싱 확인됨
                </span>
                <!-- 전문가 답변 배지 -->
                <span v-else-if="post.isExpertAnswered" class="ml-auto flex items-center gap-1 text-xs text-emerald-600 font-bold">
                  <CheckCircle class="w-3.5 h-3.5" />전문가 답변
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 더보기 -->
      <div class="mt-8 text-center">
        <!-- TODO: 페이지네이션 또는 무한스크롤 구현 -->
        <button class="px-7 py-3 border-2 border-gray-200 text-gray-500 font-semibold rounded-xl hover:border-blue-300 hover:text-blue-700 hover:bg-blue-50/50 transition-all text-sm">
          게시글 더보기
        </button>
      </div>
    </div>
  </section>
</template>
