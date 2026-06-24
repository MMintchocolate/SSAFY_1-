<script setup>
// @ts-nocheck
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { LogIn, X } from '@lucide/vue'
import ChatbotWidget from '@/components/ChatbotWidget.vue'

const route  = useRoute()
const router = useRouter()
const showLoginAlert = ref(false)

watch(() => route.query.loginRequired, (val) => {
  if (val) {
    showLoginAlert.value = true
    const q = { ...route.query }
    delete q.loginRequired
    router.replace({ query: q })
  }
})

function goLogin() {
  showLoginAlert.value = false
  router.push('/login')
}
</script>

<template>
  <RouterView />
  <ChatbotWidget />

  <!-- 로그인 필요 모달 -->
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="showLoginAlert"
        class="fixed inset-0 z-[200] flex items-center justify-center"
        @click.self="showLoginAlert = false"
      >
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm"></div>
        <div class="relative bg-white rounded-2xl shadow-2xl p-8 max-w-sm w-full mx-4 text-center">
          <button
            @click="showLoginAlert = false"
            class="absolute top-4 right-4 p-1 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X class="w-4 h-4" />
          </button>
          <div class="w-14 h-14 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <LogIn class="w-7 h-7 text-blue-600" />
          </div>
          <h2 class="text-lg font-black text-gray-900 mb-1">로그인이 필요합니다</h2>
          <p class="text-sm text-gray-500 mb-6">이 기능을 사용하려면 로그인해 주세요.</p>
          <div class="flex gap-3">
            <button
              @click="showLoginAlert = false"
              class="flex-1 py-2.5 border border-gray-200 text-gray-600 text-sm font-semibold rounded-xl hover:bg-gray-50 transition-colors"
            >
              취소
            </button>
            <button
              @click="goLogin"
              class="flex-1 py-2.5 bg-blue-700 text-white text-sm font-bold rounded-xl hover:bg-blue-800 transition-colors"
            >
              로그인하기
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
