<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
    <div class="w-full max-w-md bg-white rounded-2xl shadow-xl p-8 space-y-6">

      <!-- 헤더 -->
      <div class="text-center space-y-1">
        <div class="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
          <KeyRound class="w-6 h-6 text-blue-600" />
        </div>
        <h1 class="text-xl font-bold text-gray-900">비밀번호 재설정</h1>
        <p class="text-sm text-gray-500">이메일에서 받은 UID와 TOKEN을 입력하고<br/>새 비밀번호를 설정해 주세요.</p>
      </div>

      <!-- 완료 상태 -->
      <div v-if="step === 'done'" class="text-center space-y-4">
        <div class="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto">
          <Check class="w-8 h-8 text-emerald-600" />
        </div>
        <p class="font-bold text-gray-900">비밀번호가 변경되었습니다</p>
        <p class="text-sm text-gray-500">새 비밀번호로 로그인해 주세요.</p>
        <a href="/login"
          class="block w-full py-3 bg-blue-700 text-white text-sm font-bold rounded-xl hover:bg-blue-800 transition-colors text-center">
          로그인 하러 가기
        </a>
      </div>

      <!-- 입력 폼 -->
      <template v-else>
        <div class="space-y-3">
          <!-- UID -->
          <div>
            <label class="block text-xs font-semibold text-gray-600 mb-1">UID</label>
            <input
              v-model="form.uid"
              type="text"
              placeholder="이메일의 UID 값 붙여넣기"
              class="w-full px-4 py-2.5 text-sm border border-gray-200 rounded-xl outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
            />
          </div>

          <!-- TOKEN -->
          <div>
            <label class="block text-xs font-semibold text-gray-600 mb-1">TOKEN</label>
            <input
              v-model="form.token"
              type="text"
              placeholder="이메일의 TOKEN 값 붙여넣기"
              class="w-full px-4 py-2.5 text-sm border border-gray-200 rounded-xl outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
            />
          </div>

          <!-- 새 비밀번호 -->
          <div class="relative">
            <label class="block text-xs font-semibold text-gray-600 mb-1">새 비밀번호</label>
            <input
              v-model="form.password"
              :type="showPw ? 'text' : 'password'"
              placeholder="새 비밀번호"
              class="w-full px-4 py-2.5 pr-10 text-sm border border-gray-200 rounded-xl outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
            />
            <button @click="showPw = !showPw"
              class="absolute right-3 bottom-2.5 text-gray-400 hover:text-gray-600">
              <EyeOff v-if="showPw" class="w-4 h-4" />
              <Eye v-else class="w-4 h-4" />
            </button>
          </div>

          <!-- 비밀번호 확인 -->
          <div>
            <label class="block text-xs font-semibold text-gray-600 mb-1">새 비밀번호 확인</label>
            <input
              v-model="form.passwordConfirm"
              type="password"
              placeholder="새 비밀번호 다시 입력"
              @keyup.enter="submit"
              class="w-full px-4 py-2.5 text-sm border border-gray-200 rounded-xl outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
            />
          </div>
        </div>

        <!-- 에러 -->
        <p v-if="errorMsg" class="text-xs font-semibold text-red-500 flex items-start gap-1">
          <AlertCircle class="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
          <span>{{ errorMsg }}</span>
        </p>

        <!-- 제출 -->
        <button
          @click="submit"
          :disabled="loading || !form.uid || !form.token || !form.password || !form.passwordConfirm"
          class="w-full py-3 bg-blue-700 text-white text-sm font-bold rounded-xl hover:bg-blue-800 disabled:opacity-40 transition-colors"
        >
          {{ loading ? '변경 중…' : '비밀번호 변경' }}
        </button>

        <p class="text-center">
          <a href="/login" class="text-xs text-gray-400 hover:text-gray-600 underline">로그인으로 돌아가기</a>
        </p>
      </template>

    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { KeyRound, Eye, EyeOff, Check, AlertCircle } from '@lucide/vue'

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
