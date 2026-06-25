<script setup>
// @ts-nocheck
import { ref, nextTick } from 'vue'
import { Bot, X, Send, Loader2, User, Trash2 } from '@lucide/vue'

const open     = ref(false)
const messages = ref([])
const input    = ref('')
const loading  = ref(false)
const error    = ref('')
const scrollEl = ref(null)

function toggle() { open.value = !open.value }

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
        history: messages.value.slice(0, -1),
      }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || `오류 (${res.status})`)
    messages.value.push({ role: 'model', text: data.reply })
  } catch (e) {
    error.value = e.message
    messages.value.pop()
    input.value = text
  } finally {
    loading.value = false
    await scrollBottom()
  }
}

function clearChat() { messages.value = []; error.value = '' }

async function scrollBottom() {
  await nextTick()
  scrollEl.value?.scrollTo({ top: scrollEl.value.scrollHeight, behavior: 'smooth' })
}
</script>

<template>
  <div class="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">

    <!-- 채팅 패널 -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 translate-y-4 scale-95"
      enter-to-class="opacity-100 translate-y-0 scale-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 translate-y-0 scale-100"
      leave-to-class="opacity-0 translate-y-4 scale-95"
    >
      <div
        v-if="open"
        class="w-80 sm:w-96 bg-white rounded-2xl shadow-2xl border border-gray-100 flex flex-col overflow-hidden"
        style="height: 480px; transform-origin: bottom right;"
      >
        <!-- 헤더 -->
        <div class="flex items-center gap-3 px-4 py-3 bg-[#3CD2B6] flex-shrink-0">
          <div class="w-7 h-7 bg-black/10 rounded-xl flex items-center justify-center">
            <Bot class="w-4 h-4 text-gray-900" />
          </div>
          <div class="flex-1">
            <p class="text-sm font-bold text-gray-900">AI 챗봇</p>
            <p class="text-xs text-gray-900/70">금융·보안 어시스턴트</p>
          </div>
          <button
            v-if="messages.length > 0"
            @click="clearChat"
            class="p-1.5 text-gray-900/70 hover:text-gray-900 hover:bg-black/10 rounded-lg transition-colors"
            title="대화 초기화"
          >
            <Trash2 class="w-3.5 h-3.5" />
          </button>
          <button
            @click="toggle"
            class="p-1.5 text-gray-900/70 hover:text-gray-900 hover:bg-black/10 rounded-lg transition-colors"
          >
            <X class="w-4 h-4" />
          </button>
        </div>

        <!-- 메시지 영역 -->
        <div ref="scrollEl" class="flex-1 overflow-y-auto p-3 space-y-3">
          <!-- 빈 상태 -->
          <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full text-gray-300 py-8">
            <Bot class="w-10 h-10 mb-2" />
            <p class="text-xs font-semibold">무엇이든 질문해 보세요</p>
          </div>

          <!-- 말풍선 -->
          <div
            v-for="(msg, i) in messages" :key="i"
            class="flex gap-2"
            :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
          >
            <div v-if="msg.role === 'model'"
              class="w-6 h-6 bg-[#DFFAF4] rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
              <Bot class="w-3.5 h-3.5 text-[#0D9B7A]" />
            </div>

            <div
              class="max-w-[75%] px-3 py-2 rounded-2xl text-xs leading-relaxed whitespace-pre-wrap"
              :class="msg.role === 'user'
                ? 'bg-[#FFE49C] text-gray-900 rounded-tr-sm'
                : 'bg-gray-100 text-gray-800 rounded-tl-sm'"
            >{{ msg.text }}</div>

            <div v-if="msg.role === 'user'"
              class="w-6 h-6 bg-[#FFE49C] rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
              <User class="w-3.5 h-3.5 text-gray-900" />
            </div>
          </div>

          <!-- 로딩 dots -->
          <div v-if="loading" class="flex gap-2 justify-start">
            <div class="w-6 h-6 bg-[#DFFAF4] rounded-lg flex items-center justify-center flex-shrink-0">
              <Bot class="w-3.5 h-3.5 text-[#0D9B7A]" />
            </div>
            <div class="bg-gray-100 rounded-2xl rounded-tl-sm px-3 py-2.5 flex items-center gap-1">
              <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay:0ms"></span>
              <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay:150ms"></span>
              <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay:300ms"></span>
            </div>
          </div>
        </div>

        <!-- 오류 -->
        <p v-if="error" class="px-3 pb-1 text-xs text-red-500 flex-shrink-0">{{ error }}</p>

        <!-- 입력 영역 -->
        <div class="flex gap-2 px-3 py-3 border-t border-gray-100 flex-shrink-0">
          <input
            v-model="input"
            @keydown.enter.prevent="send"
            placeholder="메시지 입력..."
            :disabled="loading"
            class="flex-1 px-3 py-2 rounded-xl border border-gray-200 bg-gray-50 text-xs outline-none focus:border-[#57E0C3] focus:ring-2 focus:ring-[#57E0C3]/30 focus:bg-white disabled:opacity-50 transition-all"
          />
          <button
            @click="send"
            :disabled="!input.trim() || loading"
            class="w-9 h-9 flex items-center justify-center rounded-xl bg-[#57E0C3] text-gray-900 hover:bg-[#3FD4B5] disabled:opacity-40 transition-all flex-shrink-0"
          >
            <Loader2 v-if="loading" class="w-3.5 h-3.5 animate-spin" />
            <Send v-else class="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </Transition>

    <!-- 플로팅 토글 버튼 -->
    <button
      @click="toggle"
      class="w-14 h-14 rounded-2xl shadow-lg flex items-center justify-center transition-all duration-200"
      :class="open ? 'bg-gray-700 hover:bg-gray-800' : 'bg-[#57E0C3] hover:bg-[#3FD4B5]'"
    >
      <Transition
        enter-active-class="transition duration-150" enter-from-class="opacity-0 rotate-90" enter-to-class="opacity-100 rotate-0"
        leave-active-class="transition duration-150" leave-from-class="opacity-100 rotate-0" leave-to-class="opacity-0 rotate-90"
        mode="out-in"
      >
        <X   v-if="open"  class="w-6 h-6 text-white" />
        <Bot v-else        class="w-6 h-6 text-gray-900" />
      </Transition>
    </button>

  </div>
</template>
