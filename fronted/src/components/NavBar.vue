<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Menu, X, UserCircle2, LogOut, ChevronDown } from '@lucide/vue'
import { useAuth } from '@/composables/useAuth'

const router    = useRouter()
const route     = useRoute()
const { isLoggedIn, user, logout } = useAuth()
const mobileOpen          = ref(false)
const stockOpen           = ref(false)
const mobileStockOpen     = ref(false)
const communityOpen       = ref(false)
const mobileCommunityOpen = ref(false)

const navLinks = [
  { label: '금융상품',      to: '/products' },
  { label: '지점찾기',      to: '/branches' },
  { label: '소비분석',      to: '/spending' },
  { label: '금 시세',       to: '/app/gold' },
  { label: '뉴스',          to: '/news' },
  { label: '내 포트폴리오', to: '/app/portfolio' },
]

const stockSubLinks = [
  { label: '주식 검색',   to: '/stocks' },
  { label: '매수신호',    to: '/indicators' },
  { label: 'ML 데이터',   to: '/dataset' },
  { label: '투자 성향 테스트', to: '/app/investment-type' },
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
  <nav
    class="fixed top-0 inset-x-0 z-50"
    style="background:white;border-bottom:1px solid #F0F0F2;font-family:'Pretendard','Noto Sans KR',sans-serif"
  >
    <div class="max-w-[1520px] mx-auto px-6 h-16 flex items-center justify-between">

      <!-- 로고 -->
      <RouterLink to="/home" class="flex items-center gap-2 select-none flex-shrink-0">
        <svg width="34" height="28" viewBox="0 0 46 38" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="15" cy="9" r="6" fill="#FFA726"/>
          <circle cx="31" cy="9" r="6" fill="#4ECBA8"/>
          <path d="M7 20 Q23 36 39 20" stroke="#0F122B" stroke-width="6" stroke-linecap="round" fill="none"/>
        </svg>
        <span class="font-black text-lg" style="color:#0F122B;letter-spacing:-0.5px">moni</span>
      </RouterLink>

      <!-- 데스크탑 메뉴 -->
      <div class="hidden md:flex items-center gap-1" style="margin-left:48px;margin-right:auto">

        <!-- 금융상품, 지점찾기, 지출분석 -->
        <RouterLink
          v-for="link in navLinks.slice(0, 3)"
          :key="link.to"
          :to="link.to"
          class="px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-150 whitespace-nowrap"
          :style="$route.path === link.to
            ? 'color:#0F122B;background:#F4F5F8'
            : 'color:#6F7485'"
          style="font-size:0.9rem"
        >
          {{ link.label }}
        </RouterLink>

        <!-- 주식 드롭다운 -->
        <div class="relative" @mouseenter="stockOpen = true" @mouseleave="stockOpen = false">
          <button
            class="flex items-center gap-0.5 px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-150 whitespace-nowrap"
            :style="isStockActive ? 'color:#0F122B;background:#F4F5F8' : 'color:#6F7485'"
            style="font-size:0.9rem"
          >
            주식
            <ChevronDown class="w-3.5 h-3.5 transition-transform duration-200" :class="stockOpen ? 'rotate-180' : ''" />
          </button>
          <div v-show="stockOpen" class="absolute top-full left-0 pt-1 z-50" style="min-width:140px">
            <div class="rounded-2xl py-1.5" style="background:white;border:1px solid #EEF1F5;box-shadow:0 8px 24px rgba(15,18,43,0.1)">
              <RouterLink
                v-for="sub in stockSubLinks"
                :key="sub.to"
                :to="sub.to"
                @click="stockOpen = false"
                class="block px-4 py-2 text-sm font-semibold transition-colors"
                :style="$route.path.includes(sub.to.replace('/',''))
                  ? 'color:#0F122B;background:#F4F5F8'
                  : 'color:#6F7485'"
              >{{ sub.label }}</RouterLink>
            </div>
          </div>
        </div>

        <!-- 금 시세, 뉴스 -->
        <RouterLink
          v-for="link in navLinks.slice(3)"
          :key="link.to"
          :to="link.to"
          class="px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-150 whitespace-nowrap"
          :style="$route.path === link.to
            ? 'color:#0F122B;background:#F4F5F8'
            : 'color:#6F7485'"
          style="font-size:0.9rem"
        >
          {{ link.label }}
        </RouterLink>

        <!-- 커뮤니티 드롭다운 -->
        <div class="relative" @mouseenter="communityOpen = true" @mouseleave="communityOpen = false">
          <button
            class="flex items-center gap-0.5 px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-150 whitespace-nowrap"
            :style="isCommunityActive ? 'color:#0F122B;background:#F4F5F8' : 'color:#6F7485'"
            style="font-size:0.9rem"
          >
            커뮤니티
            <ChevronDown class="w-3.5 h-3.5 transition-transform duration-200" :class="communityOpen ? 'rotate-180' : ''" />
          </button>
          <div v-show="communityOpen" class="absolute top-full left-0 pt-1 z-50" style="min-width:140px">
            <div class="rounded-2xl py-1.5" style="background:white;border:1px solid #EEF1F5;box-shadow:0 8px 24px rgba(15,18,43,0.1)">
              <RouterLink
                v-for="sub in communitySubLinks"
                :key="sub.to"
                :to="sub.to"
                @click="communityOpen = false"
                class="block px-4 py-2 text-sm font-semibold transition-colors"
                style="color:#6F7485"
              >{{ sub.label }}</RouterLink>
            </div>
          </div>
        </div>
      </div>

      <!-- 우측 버튼 -->
      <div class="hidden md:flex items-center gap-2">
        <template v-if="isLoggedIn">
          <RouterLink to="/mypage"
            class="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold transition-all"
            style="color:#6F7485"
          >
            <UserCircle2 class="w-4 h-4" />{{ user?.username }}
          </RouterLink>
          <button @click="handleLogout"
            class="flex items-center gap-1.5 px-5 py-2 rounded-xl text-sm font-bold transition-all"
            style="background:#0F122B;color:white"
          >
            <LogOut class="w-4 h-4" />로그아웃
          </button>
        </template>
        <template v-else>
          <RouterLink to="/login"
            class="px-5 py-2 rounded-xl text-sm font-semibold transition-all"
            style="color:#6F7485;border:1.5px solid #EEF1F5"
          >
            로그인
          </RouterLink>
          <RouterLink to="/register"
            class="px-5 py-2 rounded-xl text-sm font-bold transition-all"
            style="background:#0F122B;color:white"
          >
            회원가입
          </RouterLink>
        </template>
      </div>

      <!-- 모바일 토글 -->
      <button @click="mobileOpen = !mobileOpen" class="md:hidden p-2 rounded-xl transition-colors" style="color:#6F7485">
        <X    v-if="mobileOpen" class="w-5 h-5" />
        <Menu v-else             class="w-5 h-5" />
      </button>
    </div>

    <!-- 모바일 드로어 -->
    <div v-show="mobileOpen" class="md:hidden px-4 py-3 space-y-1" style="border-top:1px solid #F0F0F2;background:white">
      <RouterLink
        v-for="link in navLinks.slice(0, 3)"
        :key="link.to"
        :to="link.to"
        @click="mobileOpen = false"
        class="block px-3 py-2.5 text-sm font-semibold rounded-xl"
        :style="$route.path === link.to ? 'color:#0F122B;background:#F4F5F8' : 'color:#6F7485'"
      >{{ link.label }}</RouterLink>

      <div>
        <button
          @click="mobileStockOpen = !mobileStockOpen"
          class="w-full flex items-center justify-between px-3 py-2.5 text-sm font-semibold rounded-xl"
          :style="isStockActive ? 'color:#0F122B;background:#F4F5F8' : 'color:#6F7485'"
        >
          주식
          <ChevronDown class="w-4 h-4 transition-transform duration-200" :class="mobileStockOpen ? 'rotate-180' : ''" />
        </button>
        <div v-show="mobileStockOpen" class="ml-3 mt-1 space-y-0.5 border-l-2 pl-3" style="border-color:#EEF1F5">
          <RouterLink
            v-for="sub in stockSubLinks"
            :key="sub.to"
            :to="sub.to"
            @click="mobileOpen = false; mobileStockOpen = false"
            class="block px-3 py-2 text-sm font-semibold rounded-xl"
            style="color:#6F7485"
          >{{ sub.label }}</RouterLink>
        </div>
      </div>

      <RouterLink
        v-for="link in navLinks.slice(3)"
        :key="link.to"
        :to="link.to"
        @click="mobileOpen = false"
        class="block px-3 py-2.5 text-sm font-semibold rounded-xl"
        :style="$route.path === link.to ? 'color:#0F122B;background:#F4F5F8' : 'color:#6F7485'"
      >{{ link.label }}</RouterLink>

      <div>
        <button
          @click="mobileCommunityOpen = !mobileCommunityOpen"
          class="w-full flex items-center justify-between px-3 py-2.5 text-sm font-semibold rounded-xl"
          :style="isCommunityActive ? 'color:#0F122B;background:#F4F5F8' : 'color:#6F7485'"
        >
          커뮤니티
          <ChevronDown class="w-4 h-4 transition-transform duration-200" :class="mobileCommunityOpen ? 'rotate-180' : ''" />
        </button>
        <div v-show="mobileCommunityOpen" class="ml-3 mt-1 space-y-0.5 border-l-2 pl-3" style="border-color:#EEF1F5">
          <RouterLink
            v-for="sub in communitySubLinks"
            :key="sub.to"
            :to="sub.to"
            @click="mobileOpen = false; mobileCommunityOpen = false"
            class="block px-3 py-2 text-sm font-semibold rounded-xl"
            style="color:#6F7485"
          >{{ sub.label }}</RouterLink>
        </div>
      </div>

      <div class="pt-2 mt-1 space-y-1.5" style="border-top:1px solid #F0F0F2">
        <template v-if="isLoggedIn">
          <RouterLink to="/mypage" @click="mobileOpen = false"
            class="block px-3 py-2.5 text-sm font-semibold rounded-xl"
            style="color:#0F122B;background:#F4F5F8"
          ><UserCircle2 class="inline w-4 h-4 mr-1" />{{ user?.username }}</RouterLink>
          <button @click="handleLogout"
            class="w-full text-left px-3 py-2.5 text-sm font-semibold rounded-xl"
            style="color:white;background:#0F122B"
          ><LogOut class="inline w-4 h-4 mr-1" />로그아웃</button>
        </template>
        <template v-else>
          <RouterLink to="/login" @click="mobileOpen = false"
            class="block px-3 py-2.5 text-sm font-semibold rounded-xl text-center"
            style="color:#6F7485;border:1.5px solid #EEF1F5"
          >로그인</RouterLink>
          <RouterLink to="/register" @click="mobileOpen = false"
            class="block px-3 py-2.5 text-sm font-bold rounded-xl text-center"
            style="background:#0F122B;color:white"
          >회원가입</RouterLink>
        </template>
      </div>
    </div>
  </nav>
</template>
