<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ShieldCheck, Eye, EyeOff, Loader2, AlertCircle } from '@lucide/vue'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { login } = useAuth()

const username  = ref('')
const password  = ref('')
const showPw    = ref(false)
const loading   = ref(false)
const errorMsg  = ref('')

async function submit() {
  errorMsg.value = ''
  if (!username.value.trim() || !password.value) {
    errorMsg.value = '아이디와 비밀번호를 입력해 주세요.'
    return
  }
  loading.value = true
  try {
    await login(username.value.trim(), password.value)
    router.push('/')
  } catch (err) {
    errorMsg.value = err?.error || '로그인에 실패했습니다.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-slate-50 flex items-center justify-center px-4">
    <div class="w-full max-w-sm">

      <!-- 로고 -->
      <div class="text-center mb-8">
        <RouterLink to="/" class="inline-flex items-center gap-2.5">
          <div class="w-10 h-10 bg-gradient-to-br from-blue-900 to-blue-600 rounded-xl flex items-center justify-center shadow-md">
            <ShieldCheck class="w-5 h-5 text-white" />
          </div>
          <span class="text-2xl font-black">
            <span class="text-blue-900">Safe</span><span class="text-blue-500">Finance</span>
          </span>
        </RouterLink>
        <p class="mt-3 text-sm text-gray-500">계정에 로그인하세요</p>
      </div>

      <!-- 카드 -->
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <form @submit.prevent="submit" class="space-y-5">

          <!-- 에러 -->
          <div v-if="errorMsg" class="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
            <AlertCircle class="w-4 h-4 flex-shrink-0" />
            {{ errorMsg }}
          </div>

          <!-- 아이디 -->
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">아이디</label>
            <input
              v-model="username"
              type="text"
              autocomplete="username"
              placeholder="아이디 입력"
              class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>

          <!-- 비밀번호 -->
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">비밀번호</label>
            <div class="relative">
              <input
                v-model="password"
                :type="showPw ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder="비밀번호 입력"
                class="w-full px-4 py-2.5 pr-11 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
              <button type="button" @click="showPw = !showPw"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <EyeOff v-if="showPw" class="w-4 h-4" />
                <Eye    v-else        class="w-4 h-4" />
              </button>
            </div>
          </div>

          <!-- 로그인 버튼 -->
          <button
            type="submit"
            :disabled="loading"
            class="w-full py-3 rounded-xl font-bold text-white bg-gradient-to-r from-blue-900 to-blue-700 hover:from-blue-950 hover:to-blue-800 transition-all flex items-center justify-center gap-2 disabled:opacity-60"
          >
            <Loader2 v-if="loading" class="w-4 h-4 animate-spin" />
            {{ loading ? '로그인 중...' : '로그인' }}
          </button>
        </form>
      </div>

      <!-- 회원가입 링크 -->
      <p class="text-center text-sm text-gray-500 mt-5">
        계정이 없으신가요?
        <RouterLink to="/register" class="font-bold text-blue-700 hover:underline">회원가입</RouterLink>
      </p>
    </div>
  </div>
</template>
