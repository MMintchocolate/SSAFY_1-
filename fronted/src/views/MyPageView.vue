<script setup>
// @ts-nocheck
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  UserCircle2, LogOut, ChevronRight, Star, Upload,
  FileText, MessageCircle, PencilLine, Lock, Check,
  AlertCircle, Eye, EyeOff, Trash2, BarChart2,
} from '@lucide/vue'
import NavBar from '@/components/NavBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { user, authFetch, logout } = useAuth()

// ── 활성 섹션 ──────────────────────────────────────────────
const activeSection = ref(null) // 'profile' | 'password'

function toggleSection(key) {
  activeSection.value = activeSection.value === key ? null : key
}

// ── 프로필 수정 ────────────────────────────────────────────
const nicknameInput = ref(user.value?.nickname || '')
const profileLoading = ref(false)
const profileMsg = ref(null) // { type: 'success'|'error', text }

async function saveProfile() {
  if (!nicknameInput.value.trim()) return
  profileLoading.value = true
  profileMsg.value = null
  try {
    const res = await authFetch('/api/accounts/me/nickname/', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nickname: nicknameInput.value }),
    })
    const data = await res.json()
    if (!res.ok) throw data
    user.value = { ...user.value, nickname: data.nickname }
    localStorage.setItem('user', JSON.stringify(user.value))
    profileMsg.value = { type: 'success', text: '닉네임이 변경되었습니다.' }
  } catch (e) {
    profileMsg.value = { type: 'error', text: e?.nickname?.[0] || '변경에 실패했습니다.' }
  } finally {
    profileLoading.value = false
  }
}

// ── 비밀번호 변경 (이메일 재설정) ────────────────────────────
// step: 'input' → 'confirm' → 'sent'
const pwStep        = ref('input')
const pwCurrent     = ref('')
const pwShowCurrent = ref(false)
const pwLoading     = ref(false)
const pwError       = ref('')

function requestEmailReset() {
  pwError.value = ''
  if (!pwCurrent.value) {
    pwError.value = '현재 비밀번호를 입력해 주세요.'
    return
  }
  pwStep.value = 'confirm'
}

function cancelConfirm() {
  pwStep.value = 'input'
  pwError.value = ''
}

async function sendEmailReset() {
  pwLoading.value = true
  pwError.value   = ''
  try {
    const res = await authFetch('/api/accounts/me/google/password/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ current_password: pwCurrent.value }),
    })
    const data = await res.json()
    if (!res.ok) {
      pwStep.value  = 'input'
      pwError.value = data?.error || '요청에 실패했습니다.'
      return
    }
    pwStep.value   = 'sent'
    pwCurrent.value = ''
  } catch {
    pwStep.value  = 'input'
    pwError.value = '서버 오류가 발생했습니다.'
  } finally {
    pwLoading.value = false
  }
}

function resetPwSection() {
  pwStep.value    = 'input'
  pwCurrent.value = ''
  pwError.value   = ''
}

// ── 지출내역서 CSV ─────────────────────────────────────────
const csvFile = ref(null)
const csvFileInput = ref(null)
const csvLoading = ref(false)
const csvMsg = ref(null)
const csvUploaded = ref(false)

function pickCsv(e) {
  csvFile.value = e.target.files[0] || null
  csvMsg.value = null
}

async function uploadCsv() {
  if (!csvFile.value) return
  csvLoading.value = true
  csvMsg.value = null
  try {
    const form = new FormData()
    form.append('file', csvFile.value)
    const res = await authFetch('/api/spending/upload/', { method: 'POST', body: form })
    const data = await res.json()
    if (!res.ok) throw data
    csvUploaded.value = true
    csvFile.value = null
    csvMsg.value = { type: 'success', text: `${data.rows}행 업로드 완료. 지출분석 페이지에서 확인하세요.` }
  } catch (e) {
    csvMsg.value = { type: 'error', text: e?.error || '업로드 실패' }
  } finally {
    csvLoading.value = false
  }
}

// ── 관심 주식 ──────────────────────────────────────────────
const watchlist = ref([])
const watchlistLoading = ref(false)

async function fetchWatchlist() {
  watchlistLoading.value = true
  try {
    const res = await authFetch('/api/stocks/watchlist/')
    if (res.ok) watchlist.value = await res.json()
  } finally {
    watchlistLoading.value = false
  }
}

async function removeWatch(symbol) {
  await authFetch(`/api/stocks/watchlist/${symbol}/`, { method: 'DELETE' })
  watchlist.value = watchlist.value.filter(w => w.symbol !== symbol)
}

// ── 내가 쓴 글 ────────────────────────────────────────────
const myPosts = ref([])
const myPostsLoading = ref(false)

async function fetchMyPosts() {
  myPostsLoading.value = true
  try {
    const res = await authFetch('/api/community/my/posts/')
    if (res.ok) myPosts.value = await res.json()
  } finally {
    myPostsLoading.value = false
  }
}

// ── 내가 쓴 댓글 ──────────────────────────────────────────
const myComments = ref([])
const myCommentsLoading = ref(false)

async function fetchMyComments() {
  myCommentsLoading.value = true
  try {
    const res = await authFetch('/api/community/my/comments/')
    if (res.ok) myComments.value = await res.json()
  } finally {
    myCommentsLoading.value = false
  }
}

// ── 로그아웃 ───────────────────────────────────────────────
async function handleLogout() {
  await logout()
  router.push('/')
}

// ── 유틸 ──────────────────────────────────────────────────
function fmtDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = Math.floor((now - d) / 1000)
  if (diff < 60)    return '방금 전'
  if (diff < 3600)  return Math.floor(diff / 60) + '분 전'
  if (diff < 86400) return Math.floor(diff / 3600) + '시간 전'
  if (diff < 604800) return Math.floor(diff / 86400) + '일 전'
  return d.toLocaleDateString('ko-KR')
}

function boardLabel(key) {
  return key === 'stock' ? '주식' : '자유게시판'
}

function avatarColor(name) {
  const colors = ['bg-blue-600','bg-emerald-600','bg-violet-600','bg-orange-500','bg-rose-500','bg-cyan-600']
  let h = 0
  for (const c of (name || '?')) h = (h * 31 + c.charCodeAt(0)) & 0xffffff
  return colors[h % colors.length]
}

onMounted(() => {
  fetchWatchlist()
  fetchMyPosts()
  fetchMyComments()
})
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <NavBar />

    <main class="pt-24 pb-16 max-w-2xl mx-auto px-4 sm:px-6 space-y-5">

      <!-- ── 프로필 카드 ── -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 flex items-center gap-5">
        <div
          class="w-16 h-16 rounded-2xl flex items-center justify-center text-white text-xl font-extrabold flex-shrink-0"
          :class="avatarColor(user?.username)"
        >
          {{ (user?.username || '?').slice(0, 2).toUpperCase() }}
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-lg font-extrabold text-gray-900 truncate">
            {{ user?.nickname || user?.username || '–' }}
          </p>
          <p class="text-sm text-gray-500 truncate">{{ user?.email || '이메일 없음' }}</p>
          <p class="text-xs text-gray-400 mt-0.5">@{{ user?.username }}</p>
        </div>
        <span class="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full flex-shrink-0">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>인증 완료
        </span>
      </div>

      <!-- ── 계정 설정 버튼들 ── -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <p class="text-xs font-bold text-gray-400 uppercase tracking-wider px-5 pt-4 pb-2">계정 설정</p>

        <!-- 프로필 수정 토글 -->
        <button
          @click="toggleSection('profile')"
          class="w-full flex items-center gap-4 px-5 py-4 hover:bg-blue-50 transition-colors border-t border-gray-50"
        >
          <div class="w-9 h-9 bg-blue-50 rounded-xl flex items-center justify-center flex-shrink-0">
            <PencilLine class="w-4 h-4 text-blue-700" />
          </div>
          <div class="flex-1 text-left">
            <p class="text-sm font-semibold text-gray-900">프로필 수정</p>
            <p class="text-xs text-gray-400 mt-0.5">닉네임 변경</p>
          </div>
          <ChevronRight
            class="w-4 h-4 text-gray-300 flex-shrink-0 transition-transform duration-200"
            :class="activeSection === 'profile' ? 'rotate-90' : ''"
          />
        </button>

        <!-- 프로필 수정 인라인 폼 -->
        <div v-if="activeSection === 'profile'" class="px-5 pb-5 pt-1 border-t border-gray-50 bg-blue-50/30">
          <div class="flex gap-2 mt-3">
            <input
              v-model="nicknameInput"
              placeholder="새 닉네임 입력"
              maxlength="30"
              class="flex-1 px-4 py-2.5 text-sm border border-gray-200 rounded-xl outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 bg-white"
            />
            <button
              @click="saveProfile"
              :disabled="profileLoading || !nicknameInput.trim()"
              class="px-4 py-2.5 bg-blue-700 text-white text-sm font-bold rounded-xl hover:bg-blue-800 disabled:opacity-40 transition-colors"
            >
              {{ profileLoading ? '저장 중…' : '저장' }}
            </button>
          </div>
          <p v-if="profileMsg" class="mt-2 text-xs font-semibold flex items-center gap-1"
            :class="profileMsg.type === 'success' ? 'text-emerald-600' : 'text-red-500'"
          >
            <Check v-if="profileMsg.type === 'success'" class="w-3.5 h-3.5" />
            <AlertCircle v-else class="w-3.5 h-3.5" />
            {{ profileMsg.text }}
          </p>
        </div>

        <!-- 비밀번호 변경 토글 -->
        <button
          @click="toggleSection('password')"
          class="w-full flex items-center gap-4 px-5 py-4 hover:bg-blue-50 transition-colors border-t border-gray-50"
        >
          <div class="w-9 h-9 bg-blue-50 rounded-xl flex items-center justify-center flex-shrink-0">
            <Lock class="w-4 h-4 text-blue-700" />
          </div>
          <div class="flex-1 text-left">
            <p class="text-sm font-semibold text-gray-900">비밀번호 변경</p>
            <p class="text-xs text-gray-400 mt-0.5">주기적인 변경을 권장합니다</p>
          </div>
          <ChevronRight
            class="w-4 h-4 text-gray-300 flex-shrink-0 transition-transform duration-200"
            :class="activeSection === 'password' ? 'rotate-90' : ''"
          />
        </button>

        <!-- 비밀번호 변경 인라인 폼 -->
        <div v-if="activeSection === 'password'" class="px-5 pb-5 pt-3 border-t border-gray-50 bg-blue-50/30">

          <!-- ① 현재 비밀번호 입력 -->
          <template v-if="pwStep === 'input'">
            <p class="text-xs text-gray-500 mb-3">
              현재 비밀번호를 확인한 뒤 등록된 이메일로 재설정 링크를 보내드립니다.
            </p>
            <div class="relative">
              <input
                v-model="pwCurrent"
                :type="pwShowCurrent ? 'text' : 'password'"
                placeholder="현재 비밀번호"
                @keyup.enter="requestEmailReset"
                class="w-full px-4 py-2.5 pr-10 text-sm border border-gray-200 rounded-xl outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 bg-white"
              />
              <button @click="pwShowCurrent = !pwShowCurrent"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                <EyeOff v-if="pwShowCurrent" class="w-4 h-4" />
                <Eye v-else class="w-4 h-4" />
              </button>
            </div>
            <button
              @click="requestEmailReset"
              :disabled="!pwCurrent"
              class="mt-2 w-full py-2.5 bg-blue-700 text-white text-sm font-bold rounded-xl hover:bg-blue-800 disabled:opacity-40 transition-colors"
            >
              확인
            </button>
            <p v-if="pwError" class="mt-2 text-xs font-semibold text-red-500 flex items-center gap-1">
              <AlertCircle class="w-3.5 h-3.5 flex-shrink-0" />{{ pwError }}
            </p>
          </template>

          <!-- ② 이메일 발송 확인 모달 -->
          <template v-else-if="pwStep === 'confirm'">
            <div class="bg-white border border-blue-100 rounded-xl p-4 text-center space-y-3">
              <div class="w-10 h-10 bg-blue-50 rounded-full flex items-center justify-center mx-auto">
                <Lock class="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p class="text-sm font-bold text-gray-900">이메일로 재설정 링크를 발송할까요?</p>
                <p class="text-xs text-gray-500 mt-1">
                  아래 이메일로 비밀번호 재설정 링크를 보내드립니다.
                </p>
                <p class="text-sm font-semibold text-blue-700 mt-1 break-all">
                  {{ user?.email || '등록된 이메일 없음' }}
                </p>
              </div>
              <div class="flex gap-2">
                <button
                  @click="cancelConfirm"
                  class="flex-1 py-2.5 border border-gray-200 text-gray-600 text-sm font-bold rounded-xl hover:bg-gray-50 transition-colors"
                >
                  취소
                </button>
                <button
                  @click="sendEmailReset"
                  :disabled="pwLoading"
                  class="flex-1 py-2.5 bg-blue-700 text-white text-sm font-bold rounded-xl hover:bg-blue-800 disabled:opacity-40 transition-colors"
                >
                  {{ pwLoading ? '발송 중…' : '발송' }}
                </button>
              </div>
            </div>
          </template>

          <!-- ③ 발송 완료 -->
          <template v-else-if="pwStep === 'sent'">
            <div class="bg-emerald-50 border border-emerald-100 rounded-xl p-4 text-center space-y-2">
              <Check class="w-8 h-8 text-emerald-500 mx-auto" />
              <p class="text-sm font-bold text-emerald-800">이메일을 발송했습니다</p>
              <p class="text-xs text-emerald-600">
                {{ user?.email }} 으로 재설정 링크를 보냈습니다.<br/>
                이메일을 확인해 주세요. (링크 유효시간 1시간)
              </p>
              <button
                @click="resetPwSection"
                class="mt-1 text-xs font-semibold text-emerald-700 underline"
              >
                다시 요청하기
              </button>
            </div>
          </template>

        </div>
      </div>

      <!-- ── 지출내역서 파일 ── -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div class="flex items-center gap-3 px-5 pt-5 pb-3">
          <div class="w-9 h-9 bg-amber-50 rounded-xl flex items-center justify-center flex-shrink-0">
            <FileText class="w-4 h-4 text-amber-600" />
          </div>
          <div>
            <p class="text-sm font-bold text-gray-900">지출내역서 파일</p>
            <p class="text-xs text-gray-400">KB국민·신한·우리 등 CSV 파일 업로드</p>
          </div>
          <RouterLink to="/spending"
            class="ml-auto flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800 transition-colors"
          >
            분석 보기 <ChevronRight class="w-3.5 h-3.5" />
          </RouterLink>
        </div>

        <div class="px-5 pb-5 space-y-3">
          <div
            class="flex items-center gap-3 border-2 border-dashed rounded-xl px-4 py-3 cursor-pointer transition-colors"
            :class="csvFile ? 'border-blue-300 bg-blue-50' : 'border-gray-200 hover:border-blue-200 hover:bg-blue-50/30'"
            @click="csvFileInput?.click()"
          >
            <Upload class="w-4 h-4 text-gray-400 flex-shrink-0" />
            <span class="text-sm text-gray-500 flex-1 truncate">
              {{ csvFile ? csvFile.name : 'CSV 파일을 선택하세요' }}
            </span>
            <input ref="csvFileInput" type="file" accept=".csv" class="hidden" @change="pickCsv" />
          </div>

          <button
            @click="uploadCsv"
            :disabled="!csvFile || csvLoading"
            class="w-full py-2.5 bg-amber-500 text-white text-sm font-bold rounded-xl hover:bg-amber-600 disabled:opacity-40 transition-colors"
          >
            {{ csvLoading ? '업로드 중…' : '업로드' }}
          </button>

          <p v-if="csvMsg" class="text-xs font-semibold flex items-center gap-1"
            :class="csvMsg.type === 'success' ? 'text-emerald-600' : 'text-red-500'"
          >
            <Check v-if="csvMsg.type === 'success'" class="w-3.5 h-3.5" />
            <AlertCircle v-else class="w-3.5 h-3.5" />
            {{ csvMsg.text }}
          </p>
        </div>
      </div>

      <!-- ── 관심 주식 ── -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div class="flex items-center gap-3 px-5 pt-5 pb-3">
          <div class="w-9 h-9 bg-amber-50 rounded-xl flex items-center justify-center flex-shrink-0">
            <Star class="w-4 h-4 text-amber-500 fill-amber-400" />
          </div>
          <div>
            <p class="text-sm font-bold text-gray-900">관심 주식</p>
            <p class="text-xs text-gray-400">{{ watchlist.length }}개 종목 등록됨</p>
          </div>
          <RouterLink to="/stocks"
            class="ml-auto flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800 transition-colors"
          >
            주식 검색 <ChevronRight class="w-3.5 h-3.5" />
          </RouterLink>
        </div>

        <div v-if="watchlistLoading" class="px-5 pb-5 space-y-2">
          <div v-for="i in 3" :key="i" class="h-12 bg-gray-100 rounded-xl animate-pulse"></div>
        </div>

        <div v-else-if="watchlist.length === 0" class="px-5 pb-5 text-center py-6">
          <Star class="w-8 h-8 text-gray-200 fill-gray-200 mx-auto mb-2" />
          <p class="text-sm text-gray-400">관심 종목이 없습니다</p>
        </div>

        <div v-else class="px-5 pb-5 space-y-2">
          <div
            v-for="item in watchlist"
            :key="item.symbol"
            class="flex items-center gap-3 px-4 py-3 bg-gray-50 rounded-xl group"
          >
            <div class="w-9 h-9 bg-gradient-to-br from-blue-600 to-blue-900 rounded-xl flex items-center justify-center text-white text-xs font-black flex-shrink-0">
              {{ item.symbol.slice(0, 4) }}
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-bold text-gray-900 truncate">{{ item.name }}</p>
              <p class="text-xs text-gray-500">{{ item.symbol }}</p>
            </div>
            <RouterLink :to="`/stocks`"
              class="opacity-0 group-hover:opacity-100 text-xs text-blue-600 font-semibold transition-opacity mr-2"
            >
              보기
            </RouterLink>
            <button
              @click="removeWatch(item.symbol)"
              class="opacity-0 group-hover:opacity-100 text-gray-300 hover:text-red-400 transition-all p-1 rounded-lg hover:bg-red-50"
            >
              <Trash2 class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      <!-- ── 내가 쓴 글 ── -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div class="flex items-center gap-3 px-5 pt-5 pb-3">
          <div class="w-9 h-9 bg-blue-50 rounded-xl flex items-center justify-center flex-shrink-0">
            <PencilLine class="w-4 h-4 text-blue-600" />
          </div>
          <div>
            <p class="text-sm font-bold text-gray-900">내가 쓴 글</p>
            <p class="text-xs text-gray-400">{{ myPosts.length }}개</p>
          </div>
          <RouterLink to="/community"
            class="ml-auto flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800 transition-colors"
          >
            커뮤니티 <ChevronRight class="w-3.5 h-3.5" />
          </RouterLink>
        </div>

        <div v-if="myPostsLoading" class="px-5 pb-5 space-y-2">
          <div v-for="i in 3" :key="i" class="h-14 bg-gray-100 rounded-xl animate-pulse"></div>
        </div>

        <div v-else-if="myPosts.length === 0" class="px-5 pb-5 text-center py-6">
          <PencilLine class="w-8 h-8 text-gray-200 mx-auto mb-2" />
          <p class="text-sm text-gray-400">아직 작성한 글이 없습니다</p>
        </div>

        <div v-else class="px-5 pb-5 space-y-2">
          <RouterLink
            v-for="post in myPosts"
            :key="post.id"
            to="/community"
            class="flex items-start gap-3 px-4 py-3 bg-gray-50 rounded-xl hover:bg-blue-50 transition-colors block"
          >
            <span
              class="text-xs font-bold px-2 py-0.5 rounded-full flex-shrink-0 mt-0.5"
              :class="post.board_type === 'stock'
                ? 'bg-blue-50 text-blue-700 border border-blue-200'
                : 'bg-emerald-50 text-emerald-700 border border-emerald-200'"
            >
              {{ boardLabel(post.board_type) }}
            </span>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-semibold text-gray-900 truncate">{{ post.title }}</p>
              <div class="flex items-center gap-3 mt-0.5">
                <span class="text-xs text-gray-400">{{ fmtDate(post.created_at) }}</span>
                <span class="flex items-center gap-0.5 text-xs text-gray-400">
                  <Eye class="w-3 h-3" />{{ post.view_count }}
                </span>
                <span class="flex items-center gap-0.5 text-xs text-gray-400">
                  <MessageCircle class="w-3 h-3" />{{ post.comment_count }}
                </span>
              </div>
            </div>
          </RouterLink>
        </div>
      </div>

      <!-- ── 내가 쓴 댓글 ── -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div class="flex items-center gap-3 px-5 pt-5 pb-3">
          <div class="w-9 h-9 bg-blue-50 rounded-xl flex items-center justify-center flex-shrink-0">
            <MessageCircle class="w-4 h-4 text-blue-600" />
          </div>
          <div>
            <p class="text-sm font-bold text-gray-900">내가 쓴 댓글</p>
            <p class="text-xs text-gray-400">{{ myComments.length }}개</p>
          </div>
        </div>

        <div v-if="myCommentsLoading" class="px-5 pb-5 space-y-2">
          <div v-for="i in 3" :key="i" class="h-14 bg-gray-100 rounded-xl animate-pulse"></div>
        </div>

        <div v-else-if="myComments.length === 0" class="px-5 pb-5 text-center py-6">
          <MessageCircle class="w-8 h-8 text-gray-200 mx-auto mb-2" />
          <p class="text-sm text-gray-400">아직 작성한 댓글이 없습니다</p>
        </div>

        <div v-else class="px-5 pb-5 space-y-2">
          <RouterLink
            v-for="c in myComments"
            :key="c.id"
            to="/community"
            class="flex items-start gap-3 px-4 py-3 bg-gray-50 rounded-xl hover:bg-blue-50 transition-colors block"
          >
            <MessageCircle class="w-4 h-4 text-gray-300 flex-shrink-0 mt-0.5" />
            <div class="flex-1 min-w-0">
              <p class="text-xs text-gray-400 truncate mb-0.5">
                → {{ c.post_title }}
              </p>
              <p class="text-sm text-gray-700 line-clamp-2">{{ c.content }}</p>
              <p class="text-xs text-gray-400 mt-0.5">{{ fmtDate(c.created_at) }}</p>
            </div>
          </RouterLink>
        </div>
      </div>

      <!-- ── 로그아웃 ── -->
      <button
        @click="handleLogout"
        class="w-full flex items-center justify-center gap-2 px-5 py-3.5 rounded-2xl border border-red-100 text-red-500 text-sm font-bold hover:bg-red-50 transition-colors"
      >
        <LogOut class="w-4 h-4" />로그아웃
      </button>

    </main>
    <AppFooter />
  </div>
</template>
