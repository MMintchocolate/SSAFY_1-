<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ShieldCheck, Eye, EyeOff, Loader2, AlertCircle } from '@lucide/vue'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { login, googleLogin } = useAuth()

const GOOGLE_CLIENT_ID = '928012216108-cr35gr1rss0phgu13ka6r7tcg0qf3noc.apps.googleusercontent.com'

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
    router.push('/app/home')
  } catch (err) {
    errorMsg.value = err?.error || '로그인에 실패했습니다.'
  } finally {
    loading.value = false
  }
}

async function onGoogleSignIn(response) {
  errorMsg.value = ''
  try {
    await googleLogin(response.credential)
    router.push('/app/home')
  } catch (err) {
    errorMsg.value = err?.error || 'Google 로그인에 실패했습니다.'
  }
}

function initGoogle() {
  window.google.accounts.id.initialize({
    client_id: GOOGLE_CLIENT_ID,
    callback: onGoogleSignIn,
  })
  window.google.accounts.id.renderButton(
    document.getElementById('google-signin-btn'),
    { theme: 'outline', size: 'large', width: 360, locale: 'ko' },
  )
}

onMounted(() => {
  if (window.google) {
    initGoogle()
    return
  }
  const script = document.createElement('script')
  script.src   = 'https://accounts.google.com/gsi/client'
  script.async = true
  script.defer = true
  script.onload = initGoogle
  document.head.appendChild(script)
})
</script>

<template>
  <div class="min-h-screen flex items-center justify-center px-4" style="background:linear-gradient(135deg,#fffdf9 0%,#f2fffb 100%);font-family:'Pretendard','Noto Sans KR',sans-serif">
    <div class="w-full max-w-sm">

      <!-- 로고 -->
      <div class="text-center mb-8">
        <RouterLink to="/" class="inline-flex items-center gap-2.5 justify-center">
          <svg width="36" height="30" viewBox="0 0 46 38" fill="none">
            <circle cx="15" cy="9" r="6" fill="#FFA726"/>
            <circle cx="31" cy="9" r="6" fill="#4ECBA8"/>
            <path d="M7 20 Q23 36 39 20" stroke="#0F122B" stroke-width="6" stroke-linecap="round" fill="none"/>
          </svg>
          <span class="font-black text-2xl" style="color:#0F122B;letter-spacing:-0.5px">moni</span>
        </RouterLink>
        <p class="mt-3 text-sm" style="color:#6F7485">계정에 로그인하세요</p>
      </div>

      <!-- 카드 -->
      <div class="rounded-2xl p-8" style="background:white;border:1px solid #EEF1F5;box-shadow:0 4px 24px rgba(15,18,43,0.06)">
        <form @submit.prevent="submit" class="space-y-5">

          <!-- 에러 -->
          <div v-if="errorMsg" class="flex items-center gap-2 p-3 rounded-xl text-sm" style="background:#FFF5F5;border:1px solid #FFD0D0;color:#E5323B">
            <AlertCircle class="w-4 h-4 flex-shrink-0" />
            {{ errorMsg }}
          </div>

          <!-- 아이디 -->
          <div>
            <label class="block font-semibold mb-1.5" style="font-size:0.85rem;color:#0F122B">아이디</label>
            <input
              v-model="username"
              type="text"
              autocomplete="username"
              placeholder="아이디 입력"
              class="w-full px-4 py-2.5 rounded-xl text-sm focus:outline-none transition-all"
              style="border:1.5px solid #EEF1F5;color:#0F122B"
            />
          </div>

          <!-- 비밀번호 -->
          <div>
            <label class="block font-semibold mb-1.5" style="font-size:0.85rem;color:#0F122B">비밀번호</label>
            <div class="relative">
              <input
                v-model="password"
                :type="showPw ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder="비밀번호 입력"
                class="w-full px-4 py-2.5 pr-11 rounded-xl text-sm focus:outline-none transition-all"
                style="border:1.5px solid #EEF1F5;color:#0F122B"
              />
              <button type="button" @click="showPw = !showPw"
                class="absolute right-3 top-1/2 -translate-y-1/2 transition-colors"
                style="color:#6F7485"
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
            class="w-full py-3 rounded-xl font-bold text-white transition-all flex items-center justify-center gap-2 disabled:opacity-60"
            style="background:#0F122B"
          >
            <Loader2 v-if="loading" class="w-4 h-4 animate-spin" />
            {{ loading ? '로그인 중...' : '로그인' }}
          </button>
        </form>

        <!-- 구분선 -->
        <div class="flex items-center gap-3 my-5">
          <div class="flex-1 h-px" style="background:#EEF1F5"></div>
          <span class="font-medium" style="font-size:0.72rem;color:#6F7485">또는</span>
          <div class="flex-1 h-px" style="background:#EEF1F5"></div>
        </div>

        <!-- Google 로그인 버튼 -->
        <div id="google-signin-btn" class="flex justify-center"></div>
      </div>

      <!-- 회원가입 링크 -->
      <p class="text-center text-sm mt-5" style="color:#6F7485">
        계정이 없으신가요?
        <RouterLink to="/register" class="font-bold hover:underline" style="color:#0F122B">회원가입</RouterLink>
      </p>
    </div>
  </div>
</template>
