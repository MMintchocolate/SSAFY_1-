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
    router.push('/app/home')
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
  <div class="min-h-screen flex items-center justify-center px-4 py-10" style="background:linear-gradient(135deg,#fffdf9 0%,#f2fffb 100%);font-family:'Pretendard','Noto Sans KR',sans-serif">
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
        <p class="mt-3 text-sm" style="color:#6F7485">새 계정을 만드세요</p>
      </div>

      <div class="rounded-2xl p-8" style="background:white;border:1px solid #EEF1F5;box-shadow:0 4px 24px rgba(15,18,43,0.06)">
        <form @submit.prevent="submit" class="space-y-4">

          <!-- 에러 목록 -->
          <div v-if="Object.keys(errors).length" class="p-3 rounded-xl text-sm space-y-1" style="background:#FFF5F5;border:1px solid #FFD0D0;color:#E5323B">
            <div v-for="msg in flattenErrors(errors)" :key="msg" class="flex items-start gap-2">
              <AlertCircle class="w-4 h-4 flex-shrink-0 mt-0.5" />{{ msg }}
            </div>
          </div>

          <!-- 아이디 -->
          <div>
            <label class="block font-semibold mb-1.5" style="font-size:0.85rem;color:#0F122B">아이디</label>
            <input v-model="username" type="text" autocomplete="username" placeholder="영문·숫자 조합"
              class="w-full px-4 py-2.5 rounded-xl text-sm focus:outline-none transition-all"
              :style="errors.username ? 'border:1.5px solid #E5323B;color:#0F122B' : 'border:1.5px solid #EEF1F5;color:#0F122B'"
            />
          </div>

          <!-- 이메일 -->
          <div>
            <label class="block font-semibold mb-1.5" style="font-size:0.85rem;color:#0F122B">이메일</label>
            <input v-model="email" type="email" autocomplete="email" placeholder="example@email.com"
              class="w-full px-4 py-2.5 rounded-xl text-sm focus:outline-none transition-all"
              :style="errors.email ? 'border:1.5px solid #E5323B;color:#0F122B' : 'border:1.5px solid #EEF1F5;color:#0F122B'"
            />
          </div>

          <!-- 비밀번호 -->
          <div>
            <label class="block font-semibold mb-1.5" style="font-size:0.85rem;color:#0F122B">비밀번호</label>
            <div class="relative">
              <input v-model="password" :type="showPw ? 'text' : 'password'" autocomplete="new-password" placeholder="8자 이상"
                class="w-full px-4 py-2.5 pr-11 rounded-xl text-sm focus:outline-none transition-all"
                :style="errors.password ? 'border:1.5px solid #E5323B;color:#0F122B' : 'border:1.5px solid #EEF1F5;color:#0F122B'"
              />
              <button type="button" @click="showPw = !showPw" class="absolute right-3 top-1/2 -translate-y-1/2 transition-colors" style="color:#6F7485">
                <EyeOff v-if="showPw" class="w-4 h-4" /><Eye v-else class="w-4 h-4" />
              </button>
            </div>
            <!-- 비밀번호 강도 바 -->
            <div v-if="password" class="mt-2 flex gap-1">
              <div v-for="i in 4" :key="i" class="h-1 flex-1 rounded-full transition-colors"
                :style="pwStrength(password) >= i
                  ? ['background:#E5323B','background:#FFD76A','background:#57E0C3','background:#0D9B7A'][i-1]
                  : 'background:#EEF1F5'"
              />
            </div>
          </div>

          <!-- 비밀번호 확인 -->
          <div>
            <label class="block font-semibold mb-1.5" style="font-size:0.85rem;color:#0F122B">비밀번호 확인</label>
            <div class="relative">
              <input v-model="password2" :type="showPw ? 'text' : 'password'" autocomplete="new-password" placeholder="동일한 비밀번호"
                class="w-full px-4 py-2.5 pr-11 rounded-xl text-sm focus:outline-none transition-all"
                :style="errors.password ? 'border:1.5px solid #E5323B;color:#0F122B' : 'border:1.5px solid #EEF1F5;color:#0F122B'"
              />
              <CheckCircle v-if="password && password === password2" class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4" style="color:#57E0C3" />
            </div>
          </div>

          <button type="submit" :disabled="loading"
            class="w-full py-3 mt-1 rounded-xl font-bold text-white transition-all flex items-center justify-center gap-2 disabled:opacity-60"
            style="background:#0F122B"
          >
            <Loader2 v-if="loading" class="w-4 h-4 animate-spin" />
            {{ loading ? '가입 중...' : '회원가입' }}
          </button>
        </form>
      </div>

      <p class="text-center text-sm mt-5" style="color:#6F7485">
        이미 계정이 있으신가요?
        <RouterLink to="/login" class="font-bold hover:underline" style="color:#0F122B">로그인</RouterLink>
      </p>
    </div>
  </div>
</template>
