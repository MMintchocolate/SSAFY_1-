<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ShieldCheck, Menu, X, UserCircle2, LogIn, LogOut, ChevronDown } from '@lucide/vue'
import { useAuth } from '@/composables/useAuth'

const router     = useRouter()
const route      = useRoute()
const { isLoggedIn, user, logout } = useAuth()
const mobileOpen           = ref(false)
const stockOpen            = ref(false)
const mobileStockOpen      = ref(false)
const communityOpen        = ref(false)
const mobileCommunityOpen  = ref(false)

const navLinks = [
  { label: '금융상품', to: '/products' },
  { label: '지점찾기', to: '/branches' },
  { label: '지출분석', to: '/spending' },
  { label: '보안뉴스', to: '/news' },
]

const stockSubLinks = [
  { label: '주식 검색', to: '/stocks' },
  { label: '매수신호',  to: '/indicators' },
  { label: 'ML 데이터', to: '/dataset' },
]

const communitySubLinks = [
  { label: '주식 게시판', to: '/community?board=stock' },
  { label: '자유게시판',  to: '/community?board=free'  },
]

const isStockActive = computed(() =>
  ['/stocks', '/indicators', '/dataset'].some(p => route.path.includes(p))
)

const isCommunityActive = computed(() => route.path.includes('/community'))

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
        <!-- 금융상품, 지점찾기 -->
        <RouterLink
          v-for="link in navLinks.slice(0, 2)"
          :key="link.to"
          :to="link.to"
          class="px-2.5 py-1.5 text-xs font-semibold rounded-lg transition-all whitespace-nowrap"
          :class="$route.path === link.to
            ? 'text-blue-700 bg-blue-50'
            : 'text-gray-600 hover:text-blue-700 hover:bg-blue-50'"
        >
          {{ link.label }}
        </RouterLink>

        <!-- 지출분석 -->
        <RouterLink
          :to="navLinks[2].to"
          class="px-2.5 py-1.5 text-xs font-semibold rounded-lg transition-all whitespace-nowrap"
          :class="$route.path === navLinks[2].to
            ? 'text-blue-700 bg-blue-50'
            : 'text-gray-600 hover:text-blue-700 hover:bg-blue-50'"
        >
          {{ navLinks[2].label }}
        </RouterLink>

        <!-- 주식 드롭다운 -->
        <div
          class="relative"
          @mouseenter="stockOpen = true"
          @mouseleave="stockOpen = false"
        >
          <button
            class="flex items-center gap-0.5 px-2.5 py-1.5 text-xs font-semibold rounded-lg transition-all whitespace-nowrap"
            :class="isStockActive
              ? 'text-blue-700 bg-blue-50'
              : 'text-gray-600 hover:text-blue-700 hover:bg-blue-50'"
          >
            주식
            <ChevronDown class="w-3 h-3 transition-transform duration-200" :class="stockOpen ? 'rotate-180' : ''" />
          </button>

          <div v-show="stockOpen" class="absolute top-full left-0 w-36 pt-1 z-50">
            <div class="bg-white rounded-xl border border-gray-200 shadow-lg py-1">
              <RouterLink
                v-for="sub in stockSubLinks"
                :key="sub.to"
                :to="sub.to"
                @click="stockOpen = false"
                class="block px-4 py-2 text-xs font-semibold transition-colors"
                :class="$route.path.includes(sub.to.replace('/', ''))
                  ? 'text-blue-700 bg-blue-50'
                  : 'text-gray-700 hover:bg-blue-50 hover:text-blue-700'"
              >
                {{ sub.label }}
              </RouterLink>
            </div>
          </div>
        </div>

        <!-- 보안뉴스 -->
        <RouterLink
          v-for="link in navLinks.slice(3)"
          :key="link.to"
          :to="link.to"
          class="px-2.5 py-1.5 text-xs font-semibold rounded-lg transition-all whitespace-nowrap"
          :class="$route.path === link.to
            ? 'text-blue-700 bg-blue-50'
            : 'text-gray-600 hover:text-blue-700 hover:bg-blue-50'"
        >
          {{ link.label }}
        </RouterLink>

        <!-- 커뮤니티 드롭다운 -->
        <div
          class="relative"
          @mouseenter="communityOpen = true"
          @mouseleave="communityOpen = false"
        >
          <button
            class="flex items-center gap-0.5 px-2.5 py-1.5 text-xs font-semibold rounded-lg transition-all whitespace-nowrap"
            :class="isCommunityActive
              ? 'text-blue-700 bg-blue-50'
              : 'text-gray-600 hover:text-blue-700 hover:bg-blue-50'"
          >
            커뮤니티
            <ChevronDown class="w-3 h-3 transition-transform duration-200" :class="communityOpen ? 'rotate-180' : ''" />
          </button>

          <div v-show="communityOpen" class="absolute top-full left-0 w-36 pt-1 z-50">
            <div class="bg-white rounded-xl border border-gray-200 shadow-lg py-1">
              <RouterLink
                v-for="sub in communitySubLinks"
                :key="sub.to"
                :to="sub.to"
                @click="communityOpen = false"
                class="block px-4 py-2 text-xs font-semibold transition-colors text-gray-700 hover:bg-blue-50 hover:text-blue-700"
              >
                {{ sub.label }}
              </RouterLink>
            </div>
          </div>
        </div>

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
      <!-- 금융상품, 지점찾기, 지출분석 -->
      <RouterLink
        v-for="link in navLinks.slice(0, 3)"
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

      <!-- 주식 (모바일 아코디언) -->
      <div>
        <button
          @click="mobileStockOpen = !mobileStockOpen"
          class="w-full flex items-center justify-between px-3 py-2 text-sm font-medium rounded-lg"
          :class="isStockActive
            ? 'text-blue-700 bg-blue-50 font-semibold'
            : 'text-gray-700 hover:bg-blue-50 hover:text-blue-700'"
        >
          주식
          <ChevronDown class="w-4 h-4 transition-transform duration-200" :class="mobileStockOpen ? 'rotate-180' : ''" />
        </button>
        <div v-show="mobileStockOpen" class="ml-3 mt-1 space-y-0.5 border-l-2 border-blue-100 pl-3">
          <RouterLink
            v-for="sub in stockSubLinks"
            :key="sub.to"
            :to="sub.to"
            @click="mobileOpen = false; mobileStockOpen = false"
            class="block px-3 py-2 text-sm font-medium rounded-lg"
            :class="$route.path.includes(sub.to.replace('/', ''))
              ? 'text-blue-700 bg-blue-50 font-semibold'
              : 'text-gray-600 hover:bg-blue-50 hover:text-blue-700'"
          >
            {{ sub.label }}
          </RouterLink>
        </div>
      </div>

      <!-- 보안뉴스 -->
      <RouterLink
        v-for="link in navLinks.slice(3)"
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

      <!-- 커뮤니티 (모바일 아코디언) -->
      <div>
        <button
          @click="mobileCommunityOpen = !mobileCommunityOpen"
          class="w-full flex items-center justify-between px-3 py-2 text-sm font-medium rounded-lg"
          :class="isCommunityActive
            ? 'text-blue-700 bg-blue-50 font-semibold'
            : 'text-gray-700 hover:bg-blue-50 hover:text-blue-700'"
        >
          커뮤니티
          <ChevronDown class="w-4 h-4 transition-transform duration-200" :class="mobileCommunityOpen ? 'rotate-180' : ''" />
        </button>
        <div v-show="mobileCommunityOpen" class="ml-3 mt-1 space-y-0.5 border-l-2 border-blue-100 pl-3">
          <RouterLink
            v-for="sub in communitySubLinks"
            :key="sub.to"
            :to="sub.to"
            @click="mobileOpen = false; mobileCommunityOpen = false"
            class="block px-3 py-2 text-sm font-medium rounded-lg text-gray-600 hover:bg-blue-50 hover:text-blue-700"
          >
            {{ sub.label }}
          </RouterLink>
        </div>
      </div>

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
