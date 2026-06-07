<script setup>
import NavBar from '@/components/NavBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import CommunitySection from '@/components/sections/CommunitySection.vue'
</script>

<template>
  <div class="min-h-screen bg-white">
    <NavBar />
    <main class="pt-16">
      <div class="bg-white border-b border-gray-100">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 py-10">
          <h1 class="text-3xl font-extrabold text-gray-900 mb-1">보안 커뮤니티</h1>
          <p class="text-gray-400">피싱 제보, 금융 팁, 상품 리뷰를 공유하는 공간</p>
        </div>
      </div>
      <CommunitySection />
    </main>
    <AppFooter />
  </div>
</template>
