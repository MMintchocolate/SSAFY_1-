<template>
  <div class="min-h-screen flex items-center justify-center p-4" style="background:linear-gradient(135deg,#fffdf9 0%,#f2fffb 100%);font-family:'Pretendard','Noto Sans KR',sans-serif">
    <div class="w-full max-w-md rounded-2xl p-8 space-y-6" style="background:white;border:1px solid #EEF1F5;box-shadow:0 4px 24px rgba(15,18,43,0.06)">

      <div class="text-center space-y-1">
        <div class="w-12 h-12 rounded-full flex items-center justify-center mx-auto" style="background:#DFFAF4">
          <KeyRound class="w-6 h-6" style="color:#57E0C3" />
        </div>
        <h1 class="text-xl font-bold" style="color:#0F122B">비밀번호 재설정</h1>
        <p class="text-sm" style="color:#6F7485">이메일에서 받은 UID와 TOKEN을 입력하고<br/>새 비밀번호를 설정해 주세요.</p>
      </div>

      <div v-if="step === 'done'" class="text-center space-y-4">
        <div class="w-16 h-16 rounded-full flex items-center justify-center mx-auto" style="background:#DFFAF4">
          <Check class="w-8 h-8" style="color:#57E0C3" />
        </div>
        <p class="font-bold" style="color:#0F122B">비밀번호가 변경되었습니다</p>
        <p class="text-sm" style="color:#6F7485">새 비밀번호로 로그인해 주세요.</p>
        <a href="/login" class="block w-full py-3 text-sm font-bold rounded-xl transition-all text-center" style="background:#0F122B;color:white">로그인 하러 가기</a>
      </div>

      <template v-else>
        <div class="space-y-3">
          <!-- 링크로 직접 들어오지 않은 경우에만 수동 입력 표시 -->
          <template v-if="!route.query.uid || !route.query.token">
            <div>
              <label class="block font-semibold mb-1" style="font-size:0.72rem;color:#0F122B">UID</label>
              <input v-model="form.uid" type="text" placeholder="이메일의 UID 값 붙여넣기"
                class="w-full px-4 py-2.5 text-sm rounded-xl outline-none transition-all"
                style="border:1.5px solid #EEF1F5;color:#0F122B"
              />
            </div>
            <div>
              <label class="block font-semibold mb-1" style="font-size:0.72rem;color:#0F122B">TOKEN</label>
              <input v-model="form.token" type="text" placeholder="이메일의 TOKEN 값 붙여넣기"
                class="w-full px-4 py-2.5 text-sm rounded-xl outline-none transition-all"
                style="border:1.5px solid #EEF1F5;color:#0F122B"
              />
            </div>
          </template>
          <!-- 링크로 들어온 경우 안내 메시지 -->
          <div v-else class="flex items-center gap-2 px-4 py-3 rounded-xl" style="background:#DFFAF4">
            <Check class="w-4 h-4 flex-shrink-0" style="color:#0D9B7A" />
            <p class="text-sm font-semibold" style="color:#0D9B7A">이메일 링크로 인증되었습니다. 새 비밀번호만 입력하세요.</p>
          </div>
          <div class="relative">
            <label class="block font-semibold mb-1" style="font-size:0.72rem;color:#0F122B">새 비밀번호</label>
            <input v-model="form.password" :type="showPw ? 'text' : 'password'" placeholder="새 비밀번호"
              class="w-full px-4 py-2.5 pr-10 text-sm rounded-xl outline-none transition-all"
              style="border:1.5px solid #EEF1F5;color:#0F122B"
            />
            <button @click="showPw = !showPw" class="absolute right-3 bottom-2.5 transition-colors" style="color:#6F7485">
              <EyeOff v-if="showPw" class="w-4 h-4" /><Eye v-else class="w-4 h-4" />
            </button>
          </div>
          <div>
            <label class="block font-semibold mb-1" style="font-size:0.72rem;color:#0F122B">새 비밀번호 확인</label>
            <input v-model="form.passwordConfirm" type="password" placeholder="새 비밀번호 다시 입력" @keyup.enter="submit"
              class="w-full px-4 py-2.5 text-sm rounded-xl outline-none transition-all"
              style="border:1.5px solid #EEF1F5;color:#0F122B"
            />
          </div>
        </div>

        <p v-if="errorMsg" class="font-semibold flex items-start gap-1" style="font-size:0.72rem;color:#E5323B">
          <AlertCircle class="w-3.5 h-3.5 flex-shrink-0 mt-0.5" /><span>{{ errorMsg }}</span>
        </p>

        <button @click="submit" :disabled="loading || !form.uid || !form.token || !form.password || !form.passwordConfirm"
          class="w-full py-3 text-sm font-bold rounded-xl transition-all disabled:opacity-40"
          style="background:#0F122B;color:white"
        >{{ loading ? '변경 중…' : '비밀번호 변경' }}</button>

        <p class="text-center">
          <a href="/login" class="underline" style="font-size:0.72rem;color:#6F7485">로그인으로 돌아가기</a>
        </p>
      </template>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { KeyRound, Eye, EyeOff, Check, AlertCircle } from '@lucide/vue'

const route  = useRoute()
const step   = ref('form')
const showPw = ref(false)
const loading = ref(false)
const errorMsg = ref('')

const form = ref({
  uid:             '',
  token:           '',
  password:        '',
  passwordConfirm: '',
})

onMounted(() => {
  if (route.query.uid)   form.value.uid   = route.query.uid
  if (route.query.token) form.value.token = route.query.token
})

async function submit() {
  errorMsg.value = ''

  if (form.value.password !== form.value.passwordConfirm) {
    errorMsg.value = '비밀번호가 일치하지 않습니다.'
    return
  }

  loading.value = true
  try {
    const res = await fetch('/api/accounts/password-reset/confirm/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        uid:          form.value.uid.trim(),
        token:        form.value.token.trim(),
        new_password: form.value.password,
      }),
    })
    const data = await res.json()
    if (!res.ok) {
      errorMsg.value = Array.isArray(data?.error) ? data.error[0] : (data?.error || '변경에 실패했습니다.')
      return
    }
    step.value = 'done'
  } catch {
    errorMsg.value = '서버 오류가 발생했습니다.'
  } finally {
    loading.value = false
  }
}
</script>
