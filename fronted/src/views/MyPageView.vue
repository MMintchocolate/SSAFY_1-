<script setup>
import { useRouter } from 'vue-router'
import NavBar from '@/components/NavBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import { UserCircle2, Bell, Shield, CreditCard, LogOut, ChevronRight } from '@lucide/vue'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { user, logout } = useAuth()

const menuSections = [
  {
    title: '계정 설정',
    items: [
      { icon: UserCircle2, label: '프로필 수정',    desc: '이름·연락처 변경' },
      { icon: CreditCard,  label: '연결 계좌 관리', desc: '등록된 금융 계좌 확인' },
    ],
  },
  {
    title: '보안',
    items: [
      { icon: Shield, label: '비밀번호 변경', desc: '주기적인 변경을 권장합니다' },
      { icon: Bell,   label: '알림 설정',    desc: '보안 알림·마케팅 수신 관리' },
    ],
  },
]

async function handleLogout() {
  await logout()
  router.push('/')
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <NavBar />
    <main class="pt-24 pb-16 max-w-2xl mx-auto px-4 sm:px-6">

      <!-- 프로필 카드 -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 flex items-center gap-5 mb-6">
        <div class="w-16 h-16 bg-gradient-to-br from-blue-900 to-blue-600 rounded-2xl flex items-center justify-center flex-shrink-0">
          <UserCircle2 class="w-8 h-8 text-white" />
        </div>
        <div>
          <p class="text-lg font-extrabold text-gray-900">{{ user?.username ?? '–' }}</p>
          <p class="text-sm text-gray-500 mt-0.5">{{ user?.email ?? '이메일 없음' }}</p>
          <span class="inline-flex items-center gap-1 mt-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>인증 완료
          </span>
        </div>
      </div>

      <!-- 메뉴 섹션 -->
      <div v-for="section in menuSections" :key="section.title" class="mb-4">
        <p class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 px-1">{{ section.title }}</p>
        <div class="bg-white rounded-2xl border border-gray-100 shadow-sm divide-y divide-gray-50">
          <button
            v-for="item in section.items"
            :key="item.label"
            class="w-full flex items-center gap-4 px-5 py-4 hover:bg-blue-50 transition-colors first:rounded-t-2xl last:rounded-b-2xl"
          >
            <div class="w-9 h-9 bg-blue-50 rounded-xl flex items-center justify-center flex-shrink-0">
              <component :is="item.icon" class="w-4.5 h-4.5 text-blue-700" />
            </div>
            <div class="flex-1 text-left">
              <p class="text-sm font-semibold text-gray-900">{{ item.label }}</p>
              <p class="text-xs text-gray-400 mt-0.5">{{ item.desc }}</p>
            </div>
            <ChevronRight class="w-4 h-4 text-gray-300 flex-shrink-0" />
          </button>
        </div>
      </div>

      <!-- 로그아웃 -->
      <button @click="handleLogout"
        class="w-full flex items-center justify-center gap-2 mt-2 px-5 py-3.5 rounded-2xl border border-red-100 text-red-500 text-sm font-bold hover:bg-red-50 transition-colors"
      >
        <LogOut class="w-4 h-4" />
        로그아웃
      </button>

    </main>
    <AppFooter />
  </div>
</template>
