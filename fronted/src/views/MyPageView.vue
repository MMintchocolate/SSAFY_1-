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

// ── 포트폴리오 관리 ───────────────────────────────────────
const portfolio      = ref([])
const portfolioLoading = ref(false)
const showPortfolioForm = ref(false)
const editingItem    = ref(null)   // null = 신규, object = 수정 대상
const pForm = ref({ symbol: '', name: '', quantity: '', avg_price: '' })
const pFormError = ref('')
const pFormLoading = ref(false)

async function fetchPortfolio() {
  portfolioLoading.value = true
  try {
    const res = await authFetch('/api/portfolio/')
    if (res.ok) portfolio.value = await res.json()
  } finally {
    portfolioLoading.value = false
  }
}

function openAddPortfolio() {
  editingItem.value = null
  pForm.value = { symbol: '', name: '', quantity: '', avg_price: '' }
  pFormError.value = ''
  showPortfolioForm.value = true
}

function openEditPortfolio(item) {
  editingItem.value = item
  pForm.value = { symbol: item.symbol, name: item.name, quantity: String(item.quantity), avg_price: String(item.avg_price) }
  pFormError.value = ''
  showPortfolioForm.value = true
}

async function savePortfolio() {
  pFormError.value = ''
  const { symbol, name, quantity, avg_price } = pForm.value
  if (!symbol.trim() || !name.trim() || !quantity || !avg_price) {
    pFormError.value = '모든 항목을 입력해 주세요.'; return
  }
  pFormLoading.value = true
  try {
    const body = { symbol: symbol.trim().toUpperCase(), name: name.trim(), quantity: parseFloat(quantity), avg_price: parseFloat(avg_price) }
    let res
    if (editingItem.value) {
      res = await authFetch(`/api/portfolio/${editingItem.value.id}/`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    } else {
      res = await authFetch('/api/portfolio/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    }
    if (!res.ok) { const d = await res.json(); pFormError.value = d.error ?? '저장 실패'; return }
    await fetchPortfolio()
    showPortfolioForm.value = false
  } finally {
    pFormLoading.value = false
  }
}

async function deletePortfolio(item) {
  if (!confirm(`${item.name} 종목을 삭제할까요?`)) return
  await authFetch(`/api/portfolio/${item.id}/`, { method: 'DELETE' })
  portfolio.value = portfolio.value.filter(p => p.id !== item.id)
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
  fetchPortfolio()
  fetchWatchlist()
  fetchMyPosts()
  fetchMyComments()
})
</script>

<template>
  <div class="min-h-screen bg-white" style="font-family:'Pretendard','Noto Sans KR',sans-serif">
    <NavBar />

    <main class="pt-24 pb-16 max-w-2xl mx-auto px-4 sm:px-6 space-y-5">

      <!-- 프로필 카드 -->
      <div class="rounded-2xl p-6 flex items-center gap-5" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
        <div class="w-16 h-16 rounded-2xl flex items-center justify-center font-extrabold flex-shrink-0" style="background:#0F122B;color:white;font-size:1.1rem">
          {{ (user?.username || '?').slice(0, 2).toUpperCase() }}
        </div>
        <div class="flex-1 min-w-0">
          <p class="font-extrabold truncate" style="font-size:1.05rem;color:#0F122B">{{ user?.nickname || user?.username || '–' }}</p>
          <p class="text-sm truncate" style="color:#6F7485">{{ user?.email || '이메일 없음' }}</p>
          <p class="mt-0.5" style="font-size:0.72rem;color:#6F7485">@{{ user?.username }}</p>
        </div>
        <span class="inline-flex items-center gap-1 font-semibold px-2 py-0.5 rounded-full flex-shrink-0" style="font-size:0.72rem;background:#DFFAF4;color:#0D9B7A;border:1px solid #57E0C3">
          <span class="w-1.5 h-1.5 rounded-full" style="background:#57E0C3"></span>인증 완료
        </span>
      </div>

      <!-- 계정 설정 -->
      <div class="rounded-2xl overflow-hidden" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
        <p class="font-bold px-5 pt-4 pb-2" style="font-size:0.72rem;color:#6F7485;letter-spacing:0.08em">계정 설정</p>

        <!-- 프로필 수정 토글 -->
        <button @click="toggleSection('profile')" class="w-full flex items-center gap-4 px-5 py-4 transition-colors hover:bg-[#F8F9FF]" style="border-top:1px solid #EEF1F5">
          <div class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" style="background:#DFFAF4">
            <PencilLine class="w-4 h-4" style="color:#0D9B7A" />
          </div>
          <div class="flex-1 text-left">
            <p class="text-sm font-semibold" style="color:#0F122B">프로필 수정</p>
            <p class="mt-0.5" style="font-size:0.72rem;color:#6F7485">닉네임 변경</p>
          </div>
          <ChevronRight class="w-4 h-4 flex-shrink-0 transition-transform duration-200" style="color:#6F7485" :class="activeSection === 'profile' ? 'rotate-90' : ''" />
        </button>

        <div v-if="activeSection === 'profile'" class="px-5 pb-5 pt-1" style="border-top:1px solid #EEF1F5;background:#F8F9FF">
          <div class="flex gap-2 mt-3">
            <input v-model="nicknameInput" placeholder="새 닉네임 입력" maxlength="30"
              class="flex-1 px-4 py-2.5 text-sm rounded-xl outline-none transition-all"
              style="border:1.5px solid #EEF1F5;background:white;color:#0F122B"
            />
            <button @click="saveProfile" :disabled="profileLoading || !nicknameInput.trim()"
              class="px-4 py-2.5 text-sm font-bold rounded-xl transition-all disabled:opacity-40"
              style="background:#0F122B;color:white"
            >{{ profileLoading ? '저장 중…' : '저장' }}</button>
          </div>
          <p v-if="profileMsg" class="mt-2 font-semibold flex items-center gap-1" style="font-size:0.72rem"
            :style="profileMsg.type === 'success' ? 'color:#0D9B7A' : 'color:#E5323B'"
          >
            <Check v-if="profileMsg.type === 'success'" class="w-3.5 h-3.5" />
            <AlertCircle v-else class="w-3.5 h-3.5" />
            {{ profileMsg.text }}
          </p>
        </div>

        <!-- 비밀번호 변경 토글 -->
        <button @click="toggleSection('password')" class="w-full flex items-center gap-4 px-5 py-4 transition-colors hover:bg-[#F8F9FF]" style="border-top:1px solid #EEF1F5">
          <div class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" style="background:#F8F9FF;border:1px solid #EEF1F5">
            <Lock class="w-4 h-4" style="color:#0F122B" />
          </div>
          <div class="flex-1 text-left">
            <p class="text-sm font-semibold" style="color:#0F122B">비밀번호 변경</p>
            <p class="mt-0.5" style="font-size:0.72rem;color:#6F7485">주기적인 변경을 권장합니다</p>
          </div>
          <ChevronRight class="w-4 h-4 flex-shrink-0 transition-transform duration-200" style="color:#6F7485" :class="activeSection === 'password' ? 'rotate-90' : ''" />
        </button>

        <div v-if="activeSection === 'password'" class="px-5 pb-5 pt-3" style="border-top:1px solid #EEF1F5;background:#F8F9FF">
          <template v-if="pwStep === 'input'">
            <p class="mb-3" style="font-size:0.72rem;color:#6F7485">현재 비밀번호를 확인한 뒤 등록된 이메일로 재설정 링크를 보내드립니다.</p>
            <div class="relative">
              <input v-model="pwCurrent" :type="pwShowCurrent ? 'text' : 'password'" placeholder="현재 비밀번호" @keyup.enter="requestEmailReset"
                class="w-full px-4 py-2.5 pr-10 text-sm rounded-xl outline-none transition-all"
                style="border:1.5px solid #EEF1F5;background:white;color:#0F122B"
              />
              <button @click="pwShowCurrent = !pwShowCurrent" class="absolute right-3 top-1/2 -translate-y-1/2 transition-colors" style="color:#6F7485">
                <EyeOff v-if="pwShowCurrent" class="w-4 h-4" /><Eye v-else class="w-4 h-4" />
              </button>
            </div>
            <button @click="requestEmailReset" :disabled="!pwCurrent"
              class="mt-2 w-full py-2.5 text-sm font-bold rounded-xl transition-all disabled:opacity-40"
              style="background:#0F122B;color:white"
            >확인</button>
            <p v-if="pwError" class="mt-2 font-semibold flex items-center gap-1" style="font-size:0.72rem;color:#E5323B">
              <AlertCircle class="w-3.5 h-3.5 flex-shrink-0" />{{ pwError }}
            </p>
          </template>

          <template v-else-if="pwStep === 'confirm'">
            <div class="rounded-xl p-4 text-center space-y-3" style="background:white;border:1px solid #EEF1F5">
              <div class="w-10 h-10 rounded-full flex items-center justify-center mx-auto" style="background:#F8F9FF;border:1px solid #EEF1F5">
                <Lock class="w-5 h-5" style="color:#0F122B" />
              </div>
              <div>
                <p class="text-sm font-bold" style="color:#0F122B">이메일로 재설정 링크를 발송할까요?</p>
                <p class="mt-1" style="font-size:0.72rem;color:#6F7485">아래 이메일로 비밀번호 재설정 링크를 보내드립니다.</p>
                <p class="text-sm font-semibold mt-1 break-all" style="color:#57E0C3">{{ user?.email || '등록된 이메일 없음' }}</p>
              </div>
              <div class="flex gap-2">
                <button @click="cancelConfirm" class="flex-1 py-2.5 text-sm font-bold rounded-xl transition-all" style="border:1.5px solid #EEF1F5;color:#6F7485">취소</button>
                <button @click="sendEmailReset" :disabled="pwLoading" class="flex-1 py-2.5 text-sm font-bold rounded-xl transition-all disabled:opacity-40" style="background:#0F122B;color:white">
                  {{ pwLoading ? '발송 중…' : '발송' }}
                </button>
              </div>
            </div>
          </template>

          <template v-else-if="pwStep === 'sent'">
            <div class="rounded-xl p-4 text-center space-y-2" style="background:#DFFAF4;border:1px solid #57E0C3">
              <Check class="w-8 h-8 mx-auto" style="color:#57E0C3" />
              <p class="text-sm font-bold" style="color:#0F122B">이메일을 발송했습니다</p>
              <p style="font-size:0.72rem;color:#0D9B7A">{{ user?.email }} 으로 재설정 링크를 보냈습니다.<br/>이메일을 확인해 주세요. (링크 유효시간 1시간)</p>
              <button @click="resetPwSection" class="mt-1 font-semibold underline" style="font-size:0.72rem;color:#0D9B7A">다시 요청하기</button>
            </div>
          </template>
        </div>
      </div>

      <!-- 지출내역서 파일 -->
      <div class="rounded-2xl overflow-hidden" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
        <div class="flex items-center gap-3 px-5 pt-5 pb-3">
          <div class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" style="background:#FFF8E6">
            <FileText class="w-4 h-4" style="color:#B8860B" />
          </div>
          <div>
            <p class="text-sm font-bold" style="color:#0F122B">지출내역서 파일</p>
            <p style="font-size:0.72rem;color:#6F7485">KB국민·신한·우리 등 CSV 파일 업로드</p>
          </div>
          <RouterLink to="/spending" class="ml-auto flex items-center gap-1 font-semibold transition-colors" style="font-size:0.72rem;color:#111827">
            분석 보기 <ChevronRight class="w-3.5 h-3.5" />
          </RouterLink>
        </div>
        <div class="px-5 pb-5 space-y-3">
          <div class="flex items-center gap-3 border-2 border-dashed rounded-xl px-4 py-3 cursor-pointer transition-colors"
            :style="csvFile ? 'border-color:#57E0C3;background:#DFFAF4' : 'border-color:#EEF1F5'"
            @click="csvFileInput?.click()"
          >
            <Upload class="w-4 h-4 flex-shrink-0" style="color:#6F7485" />
            <span class="text-sm flex-1 truncate" style="color:#6F7485">{{ csvFile ? csvFile.name : 'CSV 파일을 선택하세요' }}</span>
            <input ref="csvFileInput" type="file" accept=".csv" class="hidden" @change="pickCsv" />
          </div>
          <button @click="uploadCsv" :disabled="!csvFile || csvLoading"
            class="w-full py-2.5 text-sm font-bold rounded-xl transition-all disabled:opacity-40"
            style="background:#FFD76A;color:#0F122B"
          >{{ csvLoading ? '업로드 중…' : '업로드' }}</button>
          <p v-if="csvMsg" class="font-semibold flex items-center gap-1" style="font-size:0.72rem"
            :style="csvMsg.type === 'success' ? 'color:#0D9B7A' : 'color:#E5323B'"
          >
            <Check v-if="csvMsg.type === 'success'" class="w-3.5 h-3.5" />
            <AlertCircle v-else class="w-3.5 h-3.5" />
            {{ csvMsg.text }}
          </p>
        </div>
      </div>

      <!-- 관심 주식 -->
      <div class="rounded-2xl overflow-hidden" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
        <div class="flex items-center gap-3 px-5 pt-5 pb-3">
          <div class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" style="background:#FFF8E6">
            <Star class="w-4 h-4 fill-amber-400 text-amber-400" />
          </div>
          <div>
            <p class="text-sm font-bold" style="color:#0F122B">관심 주식</p>
            <p style="font-size:0.72rem;color:#6F7485">{{ watchlist.length }}개 종목 등록됨</p>
          </div>
          <RouterLink to="/stocks" class="ml-auto flex items-center gap-1 font-semibold transition-colors" style="font-size:0.72rem;color:#111827">
            주식 검색 <ChevronRight class="w-3.5 h-3.5" />
          </RouterLink>
        </div>
        <div v-if="watchlistLoading" class="px-5 pb-5 space-y-2">
          <div v-for="i in 3" :key="i" class="h-12 rounded-xl animate-pulse" style="background:#EEF1F5"></div>
        </div>
        <div v-else-if="watchlist.length === 0" class="px-5 pb-5 text-center py-6">
          <Star class="w-8 h-8 mx-auto mb-2" style="color:#EEF1F5;fill:#EEF1F5" />
          <p class="text-sm" style="color:#6F7485">관심 종목이 없습니다</p>
        </div>
        <div v-else class="px-5 pb-5 space-y-2">
          <div v-for="item in watchlist" :key="item.symbol" class="flex items-center gap-3 px-4 py-3 rounded-xl group" style="background:#F8F9FF">
            <div class="w-9 h-9 rounded-xl flex items-center justify-center font-black flex-shrink-0" style="background:#0F122B;color:white;font-size:0.65rem">
              {{ item.symbol.slice(0, 4) }}
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-bold truncate" style="color:#0F122B">{{ item.name }}</p>
              <p style="font-size:0.72rem;color:#6F7485">{{ item.symbol }}</p>
            </div>
            <RouterLink to="/stocks" class="opacity-0 group-hover:opacity-100 font-semibold transition-opacity mr-2" style="font-size:0.72rem;color:#57E0C3">보기</RouterLink>
            <button @click="removeWatch(item.symbol)" class="opacity-0 group-hover:opacity-100 p-1 rounded-lg transition-all" style="color:#6F7485">
              <Trash2 class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      <!-- 내가 쓴 글 -->
      <div class="rounded-2xl overflow-hidden" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
        <div class="flex items-center gap-3 px-5 pt-5 pb-3">
          <div class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" style="background:#DFFAF4">
            <PencilLine class="w-4 h-4" style="color:#0D9B7A" />
          </div>
          <div>
            <p class="text-sm font-bold" style="color:#0F122B">내가 쓴 글</p>
            <p style="font-size:0.72rem;color:#6F7485">{{ myPosts.length }}개</p>
          </div>
          <RouterLink to="/community" class="ml-auto flex items-center gap-1 font-semibold transition-colors" style="font-size:0.72rem;color:#111827">
            커뮤니티 <ChevronRight class="w-3.5 h-3.5" />
          </RouterLink>
        </div>
        <div v-if="myPostsLoading" class="px-5 pb-5 space-y-2">
          <div v-for="i in 3" :key="i" class="h-14 rounded-xl animate-pulse" style="background:#EEF1F5"></div>
        </div>
        <div v-else-if="myPosts.length === 0" class="px-5 pb-5 text-center py-6">
          <PencilLine class="w-8 h-8 mx-auto mb-2" style="color:#EEF1F5" />
          <p class="text-sm" style="color:#6F7485">아직 작성한 글이 없습니다</p>
        </div>
        <div v-else class="px-5 pb-5 space-y-2">
          <RouterLink v-for="post in myPosts" :key="post.id" to="/community"
            class="flex items-start gap-3 px-4 py-3 rounded-xl transition-colors block hover:bg-[#F8F9FF]"
            style="background:#F8F9FF"
          >
            <span class="font-bold px-2 py-0.5 rounded-full flex-shrink-0 mt-0.5"
              style="font-size:0.72rem"
              :style="post.board_type === 'stock' ? 'background:#DFFAF4;color:#0D9B7A;border:1px solid #57E0C3' : 'background:#FFF8E6;color:#B8860B;border:1px solid #FFD76A'"
            >{{ boardLabel(post.board_type) }}</span>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-semibold truncate" style="color:#0F122B">{{ post.title }}</p>
              <div class="flex items-center gap-3 mt-0.5">
                <span style="font-size:0.72rem;color:#6F7485">{{ fmtDate(post.created_at) }}</span>
                <span class="flex items-center gap-0.5" style="font-size:0.72rem;color:#6F7485"><Eye class="w-3 h-3" />{{ post.view_count }}</span>
                <span class="flex items-center gap-0.5" style="font-size:0.72rem;color:#6F7485"><MessageCircle class="w-3 h-3" />{{ post.comment_count }}</span>
              </div>
            </div>
          </RouterLink>
        </div>
      </div>

      <!-- 내가 쓴 댓글 -->
      <div class="rounded-2xl overflow-hidden" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
        <div class="flex items-center gap-3 px-5 pt-5 pb-3">
          <div class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" style="background:#DFFAF4">
            <MessageCircle class="w-4 h-4" style="color:#0D9B7A" />
          </div>
          <div>
            <p class="text-sm font-bold" style="color:#0F122B">내가 쓴 댓글</p>
            <p style="font-size:0.72rem;color:#6F7485">{{ myComments.length }}개</p>
          </div>
        </div>
        <div v-if="myCommentsLoading" class="px-5 pb-5 space-y-2">
          <div v-for="i in 3" :key="i" class="h-14 rounded-xl animate-pulse" style="background:#EEF1F5"></div>
        </div>
        <div v-else-if="myComments.length === 0" class="px-5 pb-5 text-center py-6">
          <MessageCircle class="w-8 h-8 mx-auto mb-2" style="color:#EEF1F5" />
          <p class="text-sm" style="color:#6F7485">아직 작성한 댓글이 없습니다</p>
        </div>
        <div v-else class="px-5 pb-5 space-y-2">
          <RouterLink v-for="c in myComments" :key="c.id" to="/community"
            class="flex items-start gap-3 px-4 py-3 rounded-xl transition-colors block hover:bg-[#F8F9FF]"
            style="background:#F8F9FF"
          >
            <MessageCircle class="w-4 h-4 flex-shrink-0 mt-0.5" style="color:#EEF1F5" />
            <div class="flex-1 min-w-0">
              <p class="truncate mb-0.5" style="font-size:0.72rem;color:#6F7485">→ {{ c.post_title }}</p>
              <p class="text-sm line-clamp-2" style="color:#0F122B">{{ c.content }}</p>
              <p class="mt-0.5" style="font-size:0.72rem;color:#6F7485">{{ fmtDate(c.created_at) }}</p>
            </div>
          </RouterLink>
        </div>
      </div>

      <!-- ── 포트폴리오 설정 ── -->
      <div class="rounded-2xl overflow-hidden" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
        <div class="flex items-center justify-between px-5 py-4" style="border-bottom:1px solid #EEF1F5">
          <div>
            <p class="font-bold text-sm" style="color:#0F122B">포트폴리오 설정</p>
            <p style="font-size:0.72rem;color:#6F7485">{{ portfolio.length }}개 종목 등록됨</p>
          </div>
          <div class="flex items-center gap-2">
            <RouterLink to="/app/portfolio" class="text-xs font-bold px-3 py-1.5 rounded-lg transition-all" style="background:#DFFAF4;color:#0D9B7A">대시보드 보기</RouterLink>
            <button @click="openAddPortfolio" class="text-xs font-bold px-3 py-1.5 rounded-lg" style="background:#0F122B;color:white">+ 종목 추가</button>
          </div>
        </div>

        <div v-if="portfolioLoading" class="px-5 py-6 text-center text-sm" style="color:#6F7485">불러오는 중...</div>
        <div v-else-if="portfolio.length === 0" class="px-5 py-6 text-center text-sm" style="color:#6F7485">
          등록된 종목이 없습니다. + 종목 추가 버튼을 눌러 추가해 보세요.
        </div>
        <div v-else class="divide-y" style="--tw-divide-opacity:1;border-color:#EEF1F5">
          <div v-for="item in portfolio" :key="item.id" class="flex items-center gap-3 px-5 py-3.5">
            <div class="w-9 h-9 rounded-xl flex items-center justify-center font-black flex-shrink-0" style="background:#0F122B;color:white;font-size:0.65rem">
              {{ item.name.slice(0,2) }}
            </div>
            <div class="flex-1 min-w-0">
              <p class="font-bold text-sm truncate" style="color:#0F122B">{{ item.name }}</p>
              <p style="font-size:0.7rem;color:#6F7485">{{ item.quantity }}주 · 평균 {{ Math.round(item.avg_price).toLocaleString() }}원</p>
            </div>
            <div class="flex items-center gap-2">
              <button @click="openEditPortfolio(item)" class="text-xs font-semibold px-2.5 py-1 rounded-lg transition-all" style="background:#F8F9FF;color:#0F122B;border:1px solid #EEF1F5">수정</button>
              <button @click="deletePortfolio(item)" class="text-xs font-semibold px-2.5 py-1 rounded-lg transition-all" style="background:#FFF5F5;color:#E5323B;border:1px solid #FFD0D0">삭제</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 포트폴리오 추가/수정 모달 -->
      <Teleport to="body">
        <div v-if="showPortfolioForm" class="fixed inset-0 z-50 flex items-center justify-center px-4"
          style="background:rgba(15,18,43,0.5);backdrop-filter:blur(4px)"
          @click.self="showPortfolioForm = false">
          <div class="w-full max-w-sm rounded-2xl overflow-hidden" style="background:white;box-shadow:0 24px 64px rgba(15,18,43,0.2)">
            <div class="flex items-center justify-between px-6 py-4" style="border-bottom:1px solid #EEF1F5">
              <h3 class="font-bold" style="color:#0F122B">{{ editingItem ? '종목 수정' : '종목 추가' }}</h3>
              <button @click="showPortfolioForm = false" class="p-1" style="color:#6F7485">✕</button>
            </div>
            <div class="px-6 py-5 space-y-3">
              <div>
                <label class="block font-semibold mb-1" style="font-size:0.8rem;color:#0F122B">종목코드</label>
                <input v-model="pForm.symbol" placeholder="예: 005930.KS" :disabled="!!editingItem"
                  class="w-full px-4 py-2.5 text-sm rounded-xl outline-none" style="border:1.5px solid #EEF1F5;color:#0F122B" />
                <p style="font-size:0.68rem;color:#6F7485;margin-top:4px">국내: 005930.KS / 해외: AAPL</p>
              </div>
              <div>
                <label class="block font-semibold mb-1" style="font-size:0.8rem;color:#0F122B">종목명</label>
                <input v-model="pForm.name" placeholder="예: 삼성전자"
                  class="w-full px-4 py-2.5 text-sm rounded-xl outline-none" style="border:1.5px solid #EEF1F5;color:#0F122B" />
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block font-semibold mb-1" style="font-size:0.8rem;color:#0F122B">수량 (주)</label>
                  <input v-model="pForm.quantity" type="number" min="0" step="any" placeholder="10"
                    class="w-full px-4 py-2.5 text-sm rounded-xl outline-none" style="border:1.5px solid #EEF1F5;color:#0F122B" />
                </div>
                <div>
                  <label class="block font-semibold mb-1" style="font-size:0.8rem;color:#0F122B">평균단가 (원)</label>
                  <input v-model="pForm.avg_price" type="number" min="0" step="any" placeholder="75000"
                    class="w-full px-4 py-2.5 text-sm rounded-xl outline-none" style="border:1.5px solid #EEF1F5;color:#0F122B" />
                </div>
              </div>
              <p v-if="pFormError" class="text-xs px-3 py-2 rounded-lg" style="background:#FFF5F5;color:#E5323B">{{ pFormError }}</p>
            </div>
            <div class="flex justify-end gap-2 px-6 py-4" style="border-top:1px solid #EEF1F5;background:#F8F9FF">
              <button @click="showPortfolioForm = false" class="px-4 py-2 text-sm font-semibold rounded-xl" style="background:white;border:1.5px solid #EEF1F5;color:#6F7485">취소</button>
              <button @click="savePortfolio" :disabled="pFormLoading" class="px-5 py-2 text-sm font-bold rounded-xl disabled:opacity-50" style="background:#0F122B;color:white">
                {{ pFormLoading ? '저장 중...' : (editingItem ? '수정 완료' : '추가') }}
              </button>
            </div>
          </div>
        </div>
      </Teleport>

      <!-- 로그아웃 -->
      <button @click="handleLogout"
        class="w-full flex items-center justify-center gap-2 px-5 py-3.5 rounded-2xl text-sm font-bold transition-all"
        style="border:1.5px solid #FFD0D0;color:#E5323B"
      >
        <LogOut class="w-4 h-4" />로그아웃
      </button>

    </main>
    <AppFooter />
  </div>
</template>
