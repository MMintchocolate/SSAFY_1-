<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ShieldCheck, Menu, X, UserCircle2, LogIn, LogOut } from '@lucide/vue'
import { useAuth } from '@/composables/useAuth'

const router     = useRouter()
const { isLoggedIn, user, logout } = useAuth()
const mobileOpen = ref(false)

const navLinks = [
  { label: '금융상품',   to: '/products' },
  { label: '지점찾기',   to: '/branches' },
  { label: '영수증',     to: '/receipts' },
  { label: '지출분석',   to: '/spending' },
  { label: '주식',       to: '/stocks' },
  { label: '금시세',     to: '/gold' },
  { label: '매수신호',   to: '/indicators' },
  { label: 'ML데이터',   to: '/dataset' },
  { label: '보안뉴스',   to: '/news' },
  { label: '커뮤니티',   to: '/community' },
]

async function handleLogout() {
  mobileOpen.value = false
  await logout()
  router.push('/home')
}
</script>

<template>
  <nav class="fixed top-0 inset-x-0 z-50 bg-white/96 backdrop-blur-md border-b border-slate-100 shadow-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">

      <!-- 로고 -->
      <RouterLink to="/home" class="flex items-center gap-2.5 select-none">
        <div class="w-9 h-9 bg-gradient-to-br from-blue-900 to-blue-600 rounded-xl flex items-center justify-center shadow-md">
          <ShieldCheck class="w-5 h-5 text-white" />
        </div>
        <span class="text-xl font-black tracking-tight">
          <span class="text-blue-900">Safe</span><span class="text-blue-500">Finance</span>
        </span>
        <span class="hidden sm:flex items-center gap-1 text-xs font-bold text-emerald-600 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 blink"></span>안전
        </span>
      </RouterLink>

      <!-- 데스크탑 메뉴 -->
      <div class="hidden md:flex items-center gap-0.5">
        <RouterLink
          v-for="link in navLinks"
          :key="link.to"
          :to="link.to"
          class="px-2.5 py-1.5 text-xs font-semibold rounded-lg transition-all whitespace-nowrap"
          :class="$route.path === link.to
            ? 'text-blue-700 bg-blue-50'
            : 'text-gray-600 hover:text-blue-700 hover:bg-blue-50'"
        >
          {{ link.label }}
        </RouterLink>

        <div class="w-px h-5 bg-gray-200 mx-1"></div>

        <!-- 로그인 상태 -->
        <template v-if="isLoggedIn">
          <RouterLink to="/mypage"
            class="flex items-center gap-1.5 px-3 py-2 text-sm font-semibold text-gray-700 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-all"
          >
            <UserCircle2 class="w-4 h-4" />
            {{ user?.username }}
          </RouterLink>
          <button @click="handleLogout"
            class="flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-blue-900 to-blue-700 text-white text-sm font-bold rounded-lg hover:from-blue-950 hover:to-blue-800 transition-all shadow-sm"
          >
            <LogOut class="w-4 h-4" />로그아웃
          </button>
        </template>

        <!-- 비로그인 상태 -->
        <template v-else>
          <RouterLink to="/login"
            class="flex items-center gap-1.5 px-3 py-2 text-sm font-semibold text-gray-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-all"
          >
            <LogIn class="w-4 h-4" />로그인
          </RouterLink>
          <RouterLink to="/register"
            class="flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-blue-900 to-blue-700 text-white text-sm font-bold rounded-lg hover:from-blue-950 hover:to-blue-800 transition-all shadow-sm"
          >
            회원가입
          </RouterLink>
        </template>
      </div>

      <!-- 모바일 토글 -->
      <button @click="mobileOpen = !mobileOpen" class="md:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors">
        <X    v-if="mobileOpen" class="w-5 h-5 text-gray-600" />
        <Menu v-else             class="w-5 h-5 text-gray-600" />
      </button>
    </div>

    <!-- 모바일 드로어 -->
    <div v-show="mobileOpen" class="md:hidden border-t border-gray-100 bg-white px-4 py-3 space-y-1">
      <RouterLink
        v-for="link in navLinks"
        :key="link.to"
        :to="link.to"
        @click="mobileOpen = false"
        class="block px-3 py-2 text-sm font-medium rounded-lg"
        :class="$route.path === link.to
          ? 'text-blue-700 bg-blue-50 font-semibold'
          : 'text-gray-700 hover:bg-blue-50 hover:text-blue-700'"
      >
        {{ link.label }}
      </RouterLink>

      <div class="border-t border-gray-100 pt-2 mt-1 space-y-1">
        <template v-if="isLoggedIn">
          <RouterLink to="/mypage" @click="mobileOpen = false"
            class="block px-3 py-2 text-sm font-semibold text-blue-700 bg-blue-50 rounded-lg"
          >
            <UserCircle2 class="inline w-4 h-4 mr-1" />{{ user?.username }}
          </RouterLink>
          <button @click="handleLogout"
            class="w-full text-left px-3 py-2 text-sm font-semibold text-red-600 hover:bg-red-50 rounded-lg"
          >
            <LogOut class="inline w-4 h-4 mr-1" />로그아웃
          </button>
        </template>
        <template v-else>
          <RouterLink to="/login"   @click="mobileOpen = false" class="block px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-blue-50 rounded-lg">로그인</RouterLink>
          <RouterLink to="/register" @click="mobileOpen = false" class="block px-3 py-2 text-sm font-bold text-white bg-blue-700 rounded-lg text-center">회원가입</RouterLink>
        </template>
      </div>
    </div>
  </nav>
</template>
