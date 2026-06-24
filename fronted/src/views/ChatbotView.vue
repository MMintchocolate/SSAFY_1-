<script setup>
// @ts-nocheck
import { ref, nextTick } from 'vue'
import NavBar from '@/components/NavBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import { Send, Loader2, Bot, User, Trash2 } from '@lucide/vue'

// 대화 기록: [{ role: 'user'|'model', text: '...' }]
const messages = ref([])
const input    = ref('')
const loading  = ref(false)
const error    = ref('')
const scrollEl = ref(null)

async function send() {
  const text = input.value.trim()
  if (!text || loading.value) return

  error.value = ''
  messages.value.push({ role: 'user', text })
  input.value = ''
  loading.value = true
  await scrollBottom()

  try {
    const res = await fetch('/api/chat/', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        message: text,
        history: messages.value.slice(0, -1),  // 방금 추가한 것 제외
      }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || `오류 (${res.status})`)
    messages.value.push({ role: 'model', text: data.reply })
  } catch (e) {
    error.value = e.message
    messages.value.pop()  // 실패한 유저 메시지 제거
    input.value = text    // 입력창 복원
  } finally {
    loading.value = false
    await scrollBottom()
  }
}

function clearChat() {
  messages.value = []
  error.value    = ''
}

async function scrollBottom() {
  await nextTick()
  scrollEl.value?.scrollTo({ top: scrollEl.value.scrollHeight, behavior: 'smooth' })
}
</script>

<template>
  <div class="min-h-screen bg-slate-50 flex flex-col">
    <NavBar />

    <main class="flex-1 flex flex-col max-w-2xl w-full mx-auto px-4 sm:px-6 pt-24 pb-6">

      <!-- 헤더 -->
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-blue-100 rounded-2xl flex items-center justify-center">
            <Bot class="w-5 h-5 text-blue-700" />
          </div>
          <div>
            <h1 class="text-lg font-extrabold text-gray-900">AI 챗봇</h1>
            <p class="text-xs text-gray-400">금융·보안 전문 어시스턴트</p>
          </div>
        </div>
        <button
          v-if="messages.length > 0"
          @click="clearChat"
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-xl border border-gray-200 transition-all"
        >
          <Trash2 class="w-3.5 h-3.5" />대화 초기화
        </button>
      </div>

      <!-- 메시지 영역 -->
      <div
        ref="scrollEl"
        class="flex-1 overflow-y-auto rounded-2xl bg-white border border-gray-100 shadow-sm p-4 space-y-4 min-h-0"
        style="max-height: calc(100vh - 260px)"
      >
        <!-- 빈 상태 -->
        <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full py-16 text-gray-300">
          <Bot class="w-14 h-14 mb-3" />
          <p class="text-sm font-semibold">무엇이든 질문해 보세요</p>
          <p class="text-xs mt-1">주식, 보안 뉴스, 금융 상품 등</p>
        </div>

        <!-- 메시지 버블 -->
        <div v-for="(msg, i) in messages" :key="i" class="flex gap-3" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
          <!-- 모델 아바타 -->
          <div v-if="msg.role === 'model'" class="w-7 h-7 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5">
            <Bot class="w-4 h-4 text-blue-700" />
          </div>

          <!-- 말풍선 -->
          <div
            class="max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap"
            :class="msg.role === 'user'
              ? 'bg-blue-700 text-white rounded-tr-sm'
              : 'bg-gray-100 text-gray-800 rounded-tl-sm'"
          >
            {{ msg.text }}
          </div>

          <!-- 유저 아바타 -->
          <div v-if="msg.role === 'user'" class="w-7 h-7 bg-blue-700 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5">
            <User class="w-4 h-4 text-white" />
          </div>
        </div>

        <!-- 로딩 버블 -->
        <div v-if="loading" class="flex gap-3 justify-start">
          <div class="w-7 h-7 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0">
            <Bot class="w-4 h-4 text-blue-700" />
          </div>
          <div class="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-1.5">
            <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay:0ms"></span>
            <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay:150ms"></span>
            <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay:300ms"></span>
          </div>
        </div>
      </div>

      <!-- 오류 -->
      <p v-if="error" class="text-xs text-red-500 mt-2 px-1">{{ error }}</p>

      <!-- 입력창 -->
      <div class="flex gap-2 mt-3">
        <input
          v-model="input"
          @keydown.enter.prevent="send"
          placeholder="메시지를 입력하세요..."
          :disabled="loading"
          class="flex-1 px-4 py-3 rounded-2xl border border-gray-200 bg-white text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 disabled:opacity-50 transition-all"
        />
        <button
          @click="send"
          :disabled="!input.trim() || loading"
          class="w-12 h-12 flex items-center justify-center rounded-2xl bg-blue-700 text-white hover:bg-blue-800 disabled:opacity-40 transition-all flex-shrink-0"
        >
          <Loader2 v-if="loading" class="w-4 h-4 animate-spin" />
          <Send v-else class="w-4 h-4" />
        </button>
      </div>

    </main>
    <AppFooter />
  </div>
</template>
