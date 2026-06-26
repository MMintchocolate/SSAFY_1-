<script setup>
// @ts-nocheck
import { ref, computed, watch, onMounted } from 'vue'
import {
  Users, PencilLine, Eye, MessageCircle,
  X, Send, Trash2, LogIn,
} from '@lucide/vue'
import NavBar from '@/components/NavBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import { useAuth } from '@/composables/useAuth'
import { useRouter, useRoute } from 'vue-router'

const API = '/api/community'
const { isLoggedIn, user, authFetch } = useAuth()
const router = useRouter()
const route  = useRoute()

// ── Board ──────────────────────────────────────────────────────────────────
const BOARDS = [
  { key: 'stock', label: '주식' },
  { key: 'free',  label: '자유게시판' },
]
const activeBoard = ref(
  ['stock', 'free'].includes(route.query.board) ? route.query.board : 'stock'
)

// 네비게이션 드롭다운에서 ?board= 파라미터로 진입 시 탭 동기화
watch(() => route.query.board, (val) => {
  if (val === 'stock' || val === 'free') activeBoard.value = val
})

// ── Post list ──────────────────────────────────────────────────────────────
const posts       = ref([])
const postsTotal  = ref(0)
const page        = ref(1)
const PAGE_SIZE   = 5
const listLoading = ref(false)

const totalPages = computed(() => Math.max(1, Math.ceil(postsTotal.value / PAGE_SIZE)))

const pageNumbers = computed(() => {
  const total = totalPages.value
  const cur   = page.value
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  // 현재 페이지 주변 ± 2, 첫·끝 페이지는 항상 표시
  const pages = new Set([1, total, cur - 2, cur - 1, cur, cur + 1, cur + 2])
  return [...pages].filter(p => p >= 1 && p <= total).sort((a, b) => a - b)
})

async function fetchPosts(resetPage = false) {
  if (resetPage) page.value = 1
  listLoading.value = true
  try {
    const res = await fetch(`${API}/posts/?board_type=${activeBoard.value}&page=${page.value}`)
    const data = await res.json()
    posts.value      = data.results
    postsTotal.value = data.count
  } finally {
    listLoading.value = false
  }
}

function goToPage(n) {
  if (n < 1 || n > totalPages.value || n === page.value) return
  page.value = n
  fetchPosts()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

watch(activeBoard, () => fetchPosts(true))
onMounted(() => fetchPosts(true))

// ── Post detail ────────────────────────────────────────────────────────────
const selectedPost   = ref(null)
const detailLoading  = ref(false)

async function openPost(id) {
  detailLoading.value = true
  selectedPost.value = null
  try {
    const res = await fetch(`${API}/posts/${id}/`)
    selectedPost.value = await res.json()
  } finally {
    detailLoading.value = false
  }
}

function closePost() {
  selectedPost.value = null
  commentInput.value = ''
  editingComment.value = null
}

// ── Write / Edit post ──────────────────────────────────────────────────────
const showWriteForm  = ref(false)
const editingPost    = ref(null)
const writeLoading   = ref(false)
const writeForm      = ref({ board_type: 'stock', title: '', content: '' })

function openWriteForm() {
  if (!isLoggedIn.value) {
    router.replace({ query: { ...route.query, loginRequired: '1' } })
    return
  }
  editingPost.value  = null
  writeForm.value    = { board_type: activeBoard.value, title: '', content: '' }
  showWriteForm.value = true
}

function openEditPostForm(post) {
  editingPost.value   = post
  writeForm.value     = { board_type: post.board_type, title: post.title, content: post.content }
  showWriteForm.value = true
}

async function submitPost() {
  if (!writeForm.value.title.trim() || !writeForm.value.content.trim()) return
  writeLoading.value = true
  try {
    if (editingPost.value) {
      await authFetch(`${API}/posts/${editingPost.value.id}/update/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(writeForm.value),
      })
    } else {
      await authFetch(`${API}/posts/create/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(writeForm.value),
      })
    }
    showWriteForm.value = false
    if (selectedPost.value && editingPost.value) {
      await openPost(selectedPost.value.id)
    }
    await fetchPosts(true)
  } finally {
    writeLoading.value = false
  }
}

async function deletePost(id) {
  if (!confirm('게시글을 삭제하시겠습니까?')) return
  await authFetch(`${API}/posts/${id}/delete/`, { method: 'DELETE' })
  closePost()
  await fetchPosts(true)
}

// ── Comments ───────────────────────────────────────────────────────────────
const commentInput    = ref('')
const commentLoading  = ref(false)
const editingComment  = ref(null)

async function submitComment() {
  if (!commentInput.value.trim() || !selectedPost.value) return
  commentLoading.value = true
  try {
    await authFetch(`${API}/posts/${selectedPost.value.id}/comments/create/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: commentInput.value }),
    })
    commentInput.value = ''
    await openPost(selectedPost.value.id)
  } finally {
    commentLoading.value = false
  }
}

async function deleteComment(postId, commentId) {
  if (!confirm('댓글을 삭제하시겠습니까?')) return
  await authFetch(`${API}/posts/${postId}/comments/${commentId}/delete/`, { method: 'DELETE' })
  await openPost(postId)
}

// ── Utils ──────────────────────────────────────────────────────────────────
function fmtDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = Math.floor((now - d) / 1000)
  if (diff < 60)   return '방금 전'
  if (diff < 3600) return Math.floor(diff / 60) + '분 전'
  if (diff < 86400) return Math.floor(diff / 3600) + '시간 전'
  if (diff < 604800) return Math.floor(diff / 86400) + '일 전'
  return d.toLocaleDateString('ko-KR')
}

function avatarColor(name) {
  const colors = [
    'bg-blue-600', 'bg-emerald-600', 'bg-violet-600',
    'bg-orange-500', 'bg-rose-500', 'bg-cyan-600',
  ]
  let hash = 0
  for (const c of (name || '?')) hash = (hash * 31 + c.charCodeAt(0)) & 0xffffff
  return colors[hash % colors.length]
}

function initials(name) {
  return (name || '?').slice(0, 2).toUpperCase()
}
</script>

<template>
  <div class="min-h-screen bg-white" style="font-family:'Pretendard','Noto Sans KR',sans-serif">
    <NavBar />

    <main class="pt-16">
      <!-- 헤더 -->
      <div style="background:linear-gradient(90deg,#fffdf9 0%,#ffffff 50%,#f2fffb 100%);border-bottom:1px solid #EEF1F5">
        <div class="max-w-4xl mx-auto px-4 sm:px-6 py-10">
          <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-bold mb-3" style="background:#DFFAF4;color:#0D9B7A;font-size:0.72rem">
            <Users class="w-3 h-3" />커뮤니티
          </div>
          <div class="flex items-end justify-between">
            <div>
              <h1 class="font-black mb-1" style="font-size:1.8rem;color:#0F122B">커뮤니티</h1>
              <p style="color:#6F7485;font-size:0.9rem">주식 토론과 자유로운 이야기를 나눠보세요</p>
            </div>
            <button @click="openWriteForm" class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm transition-all" style="background:#0F122B;color:white">
              <PencilLine class="w-4 h-4" />글쓰기
            </button>
          </div>
        </div>
      </div>

      <div class="max-w-4xl mx-auto px-4 sm:px-6 py-8">

        <!-- 게시판 탭 -->
        <div class="flex gap-2 mb-6">
          <button v-for="board in BOARDS" :key="board.key" @click="activeBoard = board.key"
            class="px-5 py-2 text-sm font-bold rounded-xl transition-all"
            :style="activeBoard === board.key ? 'background:#0F122B;color:white' : 'background:white;color:#6F7485;border:1.5px solid #EEF1F5'"
          >{{ board.label }}</button>
        </div>

        <!-- 게시글 목록 -->
        <div class="space-y-2">
          <template v-if="listLoading && posts.length === 0">
            <div v-for="i in 5" :key="i" class="rounded-2xl p-5 animate-pulse" style="background:white;border:1px solid #EEF1F5">
              <div class="flex items-center gap-3 mb-3">
                <div class="w-9 h-9 rounded-xl flex-shrink-0" style="background:#EEF1F5"></div>
                <div class="w-24 h-3.5 rounded" style="background:#EEF1F5"></div>
                <div class="w-16 h-3 rounded ml-auto" style="background:#EEF1F5"></div>
              </div>
              <div class="w-3/4 h-4 rounded mb-2" style="background:#EEF1F5"></div>
              <div class="flex gap-4 mt-3">
                <div class="w-10 h-3 rounded" style="background:#EEF1F5"></div>
                <div class="w-10 h-3 rounded" style="background:#EEF1F5"></div>
              </div>
            </div>
          </template>

          <div v-else-if="!listLoading && posts.length === 0" class="rounded-2xl py-20 text-center" style="background:white;border:1px solid #EEF1F5">
            <Users class="w-10 h-10 mx-auto mb-4" style="color:#EEF1F5" />
            <p class="font-bold mb-1" style="color:#6F7485">아직 게시글이 없습니다</p>
            <p class="text-sm" style="color:#6F7485;opacity:0.6">첫 번째 글을 작성해보세요!</p>
          </div>

          <div v-for="post in posts" :key="post.id" @click="openPost(post.id)"
            class="rounded-2xl p-5 cursor-pointer transition-all group hover:bg-[#F8F9FF]"
            style="background:white;border:1px solid #EEF1F5"
          >
            <div class="flex items-start gap-3">
              <div class="w-9 h-9 rounded-xl flex items-center justify-center font-extrabold flex-shrink-0" style="background:#0F122B;color:white;font-size:0.72rem">
                {{ initials(post.author_name) }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1.5">
                  <span class="text-sm font-semibold" style="color:#0F122B">{{ post.author_name }}</span>
                  <span style="font-size:0.72rem;color:#6F7485">{{ fmtDate(post.created_at) }}</span>
                </div>
                <p class="font-bold leading-snug line-clamp-2 transition-colors group-hover:underline" style="color:#0F122B">{{ post.title }}</p>
                <div class="flex items-center gap-4 mt-2">
                  <span class="flex items-center gap-1" style="font-size:0.72rem;color:#6F7485"><Eye class="w-3.5 h-3.5" />{{ post.view_count }}</span>
                  <span class="flex items-center gap-1" style="font-size:0.72rem;color:#6F7485"><MessageCircle class="w-3.5 h-3.5" />{{ post.comment_count }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 페이지네이션 -->
          <div v-if="totalPages > 1" class="flex items-center justify-center gap-1 pt-6">
            <!-- 이전 -->
            <button @click="goToPage(page - 1)" :disabled="page === 1"
              class="w-9 h-9 flex items-center justify-center rounded-xl font-bold text-sm transition-all disabled:opacity-30"
              style="border:1.5px solid #EEF1F5;color:#6F7485">‹</button>

            <template v-for="(n, i) in pageNumbers" :key="n">
              <!-- 생략 표시 (앞 페이지와 2 이상 차이) -->
              <span v-if="i > 0 && n - pageNumbers[i-1] > 1"
                class="w-9 h-9 flex items-center justify-center text-sm"
                style="color:#6F7485">…</span>
              <button @click="goToPage(n)"
                class="w-9 h-9 flex items-center justify-center rounded-xl font-bold text-sm transition-all"
                :style="n === page
                  ? 'background:#0F122B;color:white'
                  : 'border:1.5px solid #EEF1F5;color:#6F7485'"
              >{{ n }}</button>
            </template>

            <!-- 다음 -->
            <button @click="goToPage(page + 1)" :disabled="page === totalPages"
              class="w-9 h-9 flex items-center justify-center rounded-xl font-bold text-sm transition-all disabled:opacity-30"
              style="border:1.5px solid #EEF1F5;color:#6F7485">›</button>
          </div>
        </div>
      </div>
    </main>

    <AppFooter />

    <!-- 게시글 상세 모달 -->
    <Teleport to="body">
      <div v-if="selectedPost || detailLoading"
        class="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto py-8"
        style="background:rgba(15,18,43,0.5);backdrop-filter:blur(4px)"
        @click.self="closePost"
      >
        <div v-if="detailLoading" class="w-full max-w-2xl mx-4 rounded-2xl p-10 text-center" style="background:white">
          <p style="color:#6F7485">게시글 불러오는 중...</p>
        </div>

        <div v-else-if="selectedPost" class="w-full max-w-2xl mx-4 rounded-2xl overflow-hidden" style="background:white;box-shadow:0 24px 64px rgba(15,18,43,0.2)">
          <div class="flex items-center justify-between px-6 py-4" style="border-bottom:1px solid #EEF1F5">
            <span class="font-bold px-3 py-1 rounded-full" style="font-size:0.72rem"
              :style="selectedPost.board_type === 'stock' ? 'background:#DFFAF4;color:#0D9B7A;border:1px solid #57E0C3' : 'background:#FFF8E6;color:#B8860B;border:1px solid #FFD76A'"
            >{{ selectedPost.board_type === 'stock' ? '주식' : '자유게시판' }}</span>
            <div class="flex items-center gap-2">
              <template v-if="isLoggedIn && selectedPost.author_name === user?.username">
                <button @click="openEditPostForm(selectedPost)" class="font-semibold px-2 py-1 rounded-lg transition-colors" style="font-size:0.72rem;color:#6F7485">수정</button>
                <button @click="deletePost(selectedPost.id)" class="font-semibold px-2 py-1 rounded-lg transition-colors" style="font-size:0.72rem;color:#E5323B">삭제</button>
              </template>
              <button @click="closePost" class="p-1.5 rounded-lg transition-colors" style="color:#6F7485"><X class="w-4 h-4" /></button>
            </div>
          </div>

          <div class="px-6 py-5">
            <h2 class="font-extrabold mb-3 leading-snug" style="font-size:1.2rem;color:#0F122B">{{ selectedPost.title }}</h2>
            <div class="flex items-center gap-3 mb-5 pb-5" style="border-bottom:1px solid #EEF1F5">
              <div class="w-8 h-8 rounded-xl flex items-center justify-center font-extrabold flex-shrink-0" style="background:#0F122B;color:white;font-size:0.65rem">
                {{ initials(selectedPost.author_name) }}
              </div>
              <span class="text-sm font-semibold" style="color:#0F122B">{{ selectedPost.author_name }}</span>
              <span style="font-size:0.72rem;color:#6F7485">{{ fmtDate(selectedPost.created_at) }}</span>
              <span class="ml-auto flex items-center gap-1" style="font-size:0.72rem;color:#6F7485">
                <Eye class="w-3.5 h-3.5" />{{ selectedPost.view_count }}
              </span>
            </div>
            <div class="text-sm leading-relaxed whitespace-pre-wrap min-h-[80px]" style="color:#0F122B">{{ selectedPost.content }}</div>
          </div>

          <div class="px-6 py-5" style="border-top:1px solid #EEF1F5;background:#F8F9FF">
            <h3 class="text-sm font-bold mb-4 flex items-center gap-2" style="color:#0F122B">
              <MessageCircle class="w-4 h-4" style="color:#57E0C3" />댓글 {{ selectedPost.comments?.length ?? 0 }}
            </h3>
            <div class="space-y-3 mb-5">
              <div v-for="c in selectedPost.comments" :key="c.id" class="rounded-xl px-4 py-3" style="background:white;border:1px solid #EEF1F5">
                <div class="flex items-center gap-2 mb-1.5">
                  <div class="w-6 h-6 rounded-lg flex items-center justify-center font-extrabold flex-shrink-0" style="background:#0F122B;color:white;font-size:0.6rem">
                    {{ initials(c.author_name) }}
                  </div>
                  <span class="font-semibold" style="font-size:0.72rem;color:#0F122B">{{ c.author_name }}</span>
                  <span style="font-size:0.72rem;color:#6F7485">{{ fmtDate(c.created_at) }}</span>
                  <button v-if="isLoggedIn && c.author_name === user?.username"
                    @click="deleteComment(selectedPost.id, c.id)"
                    class="ml-auto p-1 rounded-lg transition-all" style="color:#6F7485"
                  ><Trash2 class="w-3.5 h-3.5" /></button>
                </div>
                <p class="text-sm leading-relaxed" style="color:#0F122B">{{ c.content }}</p>
              </div>
              <div v-if="selectedPost.comments?.length === 0" class="text-center py-4 text-sm" style="color:#6F7485">첫 댓글을 남겨보세요</div>
            </div>
            <div v-if="isLoggedIn" class="flex gap-2">
              <input v-model="commentInput" @keydown.enter.exact.prevent="submitComment"
                placeholder="댓글을 입력하세요 (Enter로 등록)"
                class="flex-1 px-4 py-2.5 text-sm rounded-xl outline-none transition-all"
                style="background:white;border:1.5px solid #EEF1F5;color:#0F122B"
                :disabled="commentLoading"
              />
              <button @click="submitComment" :disabled="!commentInput.trim() || commentLoading"
                class="px-4 py-2.5 rounded-xl transition-all disabled:opacity-40 flex items-center gap-1.5 text-sm font-bold"
                style="background:#57E0C3;color:#0F122B"
              ><Send class="w-3.5 h-3.5" />등록</button>
            </div>
            <div v-else class="flex items-center gap-3 rounded-xl px-4 py-3 text-sm" style="background:white;border:1px solid #EEF1F5;color:#6F7485">
              <LogIn class="w-4 h-4" style="color:#6F7485" />
              <span>댓글을 작성하려면</span>
              <RouterLink to="/login" class="font-bold hover:underline" style="color:#0F122B">로그인</RouterLink>
              <span>이 필요합니다</span>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 글쓰기 / 수정 모달 -->
    <Teleport to="body">
      <div v-if="showWriteForm"
        class="fixed inset-0 z-50 flex items-center justify-center px-4"
        style="background:rgba(15,18,43,0.5);backdrop-filter:blur(4px)"
        @click.self="showWriteForm = false"
      >
        <div class="w-full max-w-xl rounded-2xl overflow-hidden" style="background:white;box-shadow:0 24px 64px rgba(15,18,43,0.2)">
          <div class="flex items-center justify-between px-6 py-4" style="border-bottom:1px solid #EEF1F5">
            <h2 class="font-extrabold" style="color:#0F122B">{{ editingPost ? '게시글 수정' : '글쓰기' }}</h2>
            <button @click="showWriteForm = false" class="p-1.5 rounded-lg transition-colors" style="color:#6F7485"><X class="w-4 h-4" /></button>
          </div>
          <div class="px-6 py-5 space-y-4">
            <div class="flex gap-2">
              <button v-for="board in BOARDS" :key="board.key" @click="writeForm.board_type = board.key"
                class="px-4 py-1.5 text-xs font-bold rounded-xl transition-all"
                :style="writeForm.board_type === board.key ? 'background:#0F122B;color:white' : 'background:#F8F9FF;color:#6F7485'"
              >{{ board.label }}</button>
            </div>
            <input v-model="writeForm.title" placeholder="제목을 입력하세요" maxlength="200"
              class="w-full px-4 py-3 text-sm font-semibold rounded-xl outline-none transition-all"
              style="border:1.5px solid #EEF1F5;color:#0F122B"
            />
            <textarea v-model="writeForm.content" placeholder="내용을 입력하세요" rows="8"
              class="w-full px-4 py-3 text-sm rounded-xl outline-none transition-all resize-none"
              style="border:1.5px solid #EEF1F5;color:#0F122B"
            ></textarea>
          </div>
          <div class="flex justify-end gap-2 px-6 py-4" style="border-top:1px solid #EEF1F5;background:#F8F9FF">
            <button @click="showWriteForm = false"
              class="px-5 py-2 text-sm font-semibold rounded-xl transition-colors"
              style="background:white;border:1.5px solid #EEF1F5;color:#6F7485"
            >취소</button>
            <button @click="submitPost" :disabled="!writeForm.title.trim() || !writeForm.content.trim() || writeLoading"
              class="px-5 py-2 text-sm font-bold rounded-xl transition-all disabled:opacity-40"
              style="background:#0F122B;color:white"
            >{{ writeLoading ? '저장 중...' : (editingPost ? '수정 완료' : '등록') }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
