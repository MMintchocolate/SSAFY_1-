<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ShieldCheck, Eye, EyeOff, Loader2, AlertCircle, CheckCircle } from '@lucide/vue'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { register } = useAuth()

const username   = ref('')
const email      = ref('')
const password   = ref('')
const password2  = ref('')
const showPw     = ref(false)
const loading    = ref(false)
const errors     = ref({})

function flattenErrors(errObj) {
  const msgs = []
  for (const v of Object.values(errObj)) {
    if (Array.isArray(v)) msgs.push(...v)
    else if (typeof v === 'string') msgs.push(v)
  }
  return msgs
}

async function submit() {
  errors.value = {}
  loading.value = true
  try {
    await register(username.value.trim(), email.value.trim(), password.value, password2.value)
    router.push('/')
  } catch (err) {
    errors.value = err
  } finally {
    loading.value = false
  }
}

const pwStrength = (pw) => {
  if (!pw) return 0
  let s = 0
  if (pw.length >= 8)             s++
  if (/[A-Z]/.test(pw))           s++
  if (/[0-9]/.test(pw))           s++
  if (/[^A-Za-z0-9]/.test(pw))    s++
  return s
}
</script>

<template>
  <div class="min-h-screen bg-slate-50 flex items-center justify-center px-4 py-10">
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
        <p class="mt-3 text-sm text-gray-500">새 계정을 만드세요</p>
      </div>

      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <form @submit.prevent="submit" class="space-y-4">

          <!-- 에러 목록 -->
          <div v-if="Object.keys(errors).length" class="p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm space-y-1">
            <div v-for="msg in flattenErrors(errors)" :key="msg" class="flex items-start gap-2">
              <AlertCircle class="w-4 h-4 flex-shrink-0 mt-0.5" />{{ msg }}
            </div>
          </div>

          <!-- 아이디 -->
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">아이디</label>
            <input v-model="username" type="text" autocomplete="username" placeholder="영문·숫자 조합"
              class="w-full px-4 py-2.5 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
              :class="errors.username ? 'border-red-300' : 'border-gray-200'"
            />
          </div>

          <!-- 이메일 -->
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">이메일</label>
            <input v-model="email" type="email" autocomplete="email" placeholder="example@email.com"
              class="w-full px-4 py-2.5 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
              :class="errors.email ? 'border-red-300' : 'border-gray-200'"
            />
          </div>

          <!-- 비밀번호 -->
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">비밀번호</label>
            <div class="relative">
              <input v-model="password" :type="showPw ? 'text' : 'password'" autocomplete="new-password" placeholder="8자 이상"
                class="w-full px-4 py-2.5 pr-11 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                :class="errors.password ? 'border-red-300' : 'border-gray-200'"
              />
              <button type="button" @click="showPw = !showPw" class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
                <EyeOff v-if="showPw" class="w-4 h-4" /><Eye v-else class="w-4 h-4" />
              </button>
            </div>
            <!-- 비밀번호 강도 바 -->
            <div v-if="password" class="mt-2 flex gap-1">
              <div v-for="i in 4" :key="i" class="h-1 flex-1 rounded-full transition-colors"
                :class="pwStrength(password) >= i
                  ? ['bg-red-400','bg-amber-400','bg-emerald-400','bg-emerald-500'][i-1]
                  : 'bg-gray-100'"
              />
            </div>
          </div>

          <!-- 비밀번호 확인 -->
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">비밀번호 확인</label>
            <div class="relative">
              <input v-model="password2" :type="showPw ? 'text' : 'password'" autocomplete="new-password" placeholder="동일한 비밀번호"
                class="w-full px-4 py-2.5 pr-11 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                :class="errors.password ? 'border-red-300' : 'border-gray-200'"
              />
              <CheckCircle v-if="password && password === password2" class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-emerald-500" />
            </div>
          </div>

          <button type="submit" :disabled="loading"
            class="w-full py-3 mt-1 rounded-xl font-bold text-white bg-gradient-to-r from-blue-900 to-blue-700 hover:from-blue-950 hover:to-blue-800 transition-all flex items-center justify-center gap-2 disabled:opacity-60"
          >
            <Loader2 v-if="loading" class="w-4 h-4 animate-spin" />
            {{ loading ? '가입 중...' : '회원가입' }}
          </button>
        </form>
      </div>

      <p class="text-center text-sm text-gray-500 mt-5">
        이미 계정이 있으신가요?
        <RouterLink to="/login" class="font-bold text-blue-700 hover:underline">로그인</RouterLink>
      </p>
    </div>
  </div>
</template>
