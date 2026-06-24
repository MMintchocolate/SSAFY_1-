<script setup>
// @ts-nocheck
import { ref, watch, onMounted } from 'vue'
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
const hasMore     = ref(false)
const page        = ref(1)
const listLoading = ref(false)

async function fetchPosts(reset = false) {
  if (reset) page.value = 1
  listLoading.value = true
  try {
    const res = await fetch(`${API}/posts/?board_type=${activeBoard.value}&page=${page.value}`)
    const data = await res.json()
    posts.value    = reset ? data.results : [...posts.value, ...data.results]
    postsTotal.value = data.count
    hasMore.value  = data.has_next
  } finally {
    listLoading.value = false
  }
}

function loadMore() {
  page.value++
  fetchPosts()
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
  if (!isLoggedIn.value) { router.push('/login'); return }
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
  <div class="min-h-screen bg-gray-50">
    <NavBar />

    <main class="pt-16">
      <!-- Page header -->
      <div class="bg-white border-b border-gray-100">
        <div class="max-w-4xl mx-auto px-4 sm:px-6 py-10">
          <div class="inline-flex items-center gap-2 bg-blue-50 text-blue-700 text-xs font-bold px-3 py-1.5 rounded-full mb-3 uppercase tracking-widest border border-blue-100">
            <Users class="w-3 h-3" />커뮤니티
          </div>
          <div class="flex items-end justify-between">
            <div>
              <h1 class="text-3xl font-extrabold text-gray-900 mb-1">커뮤니티</h1>
              <p class="text-gray-400">주식 토론과 자유로운 이야기를 나눠보세요</p>
            </div>
            <button
              @click="openWriteForm"
              class="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-900 to-blue-700 text-white font-bold rounded-xl shadow-md hover:shadow-lg hover:from-blue-950 transition-all text-sm"
            >
              <PencilLine class="w-4 h-4" />글쓰기
            </button>
          </div>
        </div>
      </div>

      <div class="max-w-4xl mx-auto px-4 sm:px-6 py-8">

        <!-- Board tabs -->
        <div class="flex gap-2 mb-6">
          <button
            v-for="board in BOARDS"
            :key="board.key"
            @click="activeBoard = board.key"
            class="px-5 py-2 text-sm font-bold rounded-xl transition-all"
            :class="activeBoard === board.key
              ? 'bg-blue-800 text-white shadow-sm'
              : 'bg-white text-gray-500 border border-gray-200 hover:border-blue-300 hover:text-blue-700'"
          >
            {{ board.label }}
          </button>
        </div>

        <!-- Post list -->
        <div class="space-y-2">

          <!-- Loading skeleton -->
          <template v-if="listLoading && posts.length === 0">
            <div v-for="i in 5" :key="i" class="bg-white rounded-2xl border border-gray-100 p-5 animate-pulse">
              <div class="flex items-center gap-3 mb-3">
                <div class="w-9 h-9 rounded-xl bg-gray-200 flex-shrink-0"></div>
                <div class="w-24 h-3.5 bg-gray-200 rounded"></div>
                <div class="w-16 h-3 bg-gray-100 rounded ml-auto"></div>
              </div>
              <div class="w-3/4 h-4 bg-gray-200 rounded mb-2"></div>
              <div class="flex gap-4 mt-3">
                <div class="w-10 h-3 bg-gray-100 rounded"></div>
                <div class="w-10 h-3 bg-gray-100 rounded"></div>
              </div>
            </div>
          </template>

          <!-- Empty -->
          <div v-else-if="!listLoading && posts.length === 0"
            class="bg-white rounded-2xl border border-gray-100 py-20 text-center"
          >
            <Users class="w-10 h-10 text-gray-200 mx-auto mb-4" />
            <p class="font-bold text-gray-400 mb-1">아직 게시글이 없습니다</p>
            <p class="text-sm text-gray-300">첫 번째 글을 작성해보세요!</p>
          </div>

          <!-- Post items -->
          <div
            v-for="post in posts"
            :key="post.id"
            @click="openPost(post.id)"
            class="bg-white rounded-2xl border border-gray-100 p-5 cursor-pointer hover:border-blue-200 hover:shadow-sm transition-all group"
          >
            <div class="flex items-start gap-3">
              <div
                class="w-9 h-9 rounded-xl flex items-center justify-center text-white text-xs font-extrabold flex-shrink-0"
                :class="avatarColor(post.author_name)"
              >
                {{ initials(post.author_name) }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1.5">
                  <span class="text-sm font-semibold text-gray-700">{{ post.author_name }}</span>
                  <span class="text-xs text-gray-400">{{ fmtDate(post.created_at) }}</span>
                </div>
                <p class="font-bold text-gray-900 group-hover:text-blue-800 transition-colors leading-snug line-clamp-2">
                  {{ post.title }}
                </p>
                <div class="flex items-center gap-4 mt-2">
                  <span class="flex items-center gap-1 text-xs text-gray-400">
                    <Eye class="w-3.5 h-3.5" />{{ post.view_count }}
                  </span>
                  <span class="flex items-center gap-1 text-xs text-gray-400">
                    <MessageCircle class="w-3.5 h-3.5" />{{ post.comment_count }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Load more -->
          <div v-if="hasMore" class="text-center pt-4">
            <button
              @click="loadMore"
              :disabled="listLoading"
              class="px-6 py-2.5 border-2 border-gray-200 text-gray-500 font-semibold rounded-xl hover:border-blue-300 hover:text-blue-700 hover:bg-blue-50 transition-all text-sm disabled:opacity-50"
            >
              {{ listLoading ? '불러오는 중...' : '더보기' }}
            </button>
          </div>
        </div>
      </div>
    </main>

    <AppFooter />

    <!-- ── Post detail modal ─────────────────────────────────────────────── -->
    <Teleport to="body">
      <div
        v-if="selectedPost || detailLoading"
        class="fixed inset-0 z-50 flex items-start justify-center bg-black/40 backdrop-blur-sm overflow-y-auto py-8"
        @click.self="closePost"
      >
        <!-- Loading -->
        <div v-if="detailLoading" class="w-full max-w-2xl mx-4 bg-white rounded-2xl p-10 text-center">
          <p class="text-gray-400">게시글 불러오는 중...</p>
        </div>

        <!-- Detail card -->
        <div v-else-if="selectedPost" class="w-full max-w-2xl mx-4 bg-white rounded-2xl shadow-2xl overflow-hidden">

          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
            <span class="text-xs font-bold px-3 py-1 rounded-full"
              :class="selectedPost.board_type === 'stock'
                ? 'bg-blue-50 text-blue-700 border border-blue-200'
                : 'bg-emerald-50 text-emerald-700 border border-emerald-200'"
            >
              {{ selectedPost.board_type === 'stock' ? '주식' : '자유게시판' }}
            </span>
            <div class="flex items-center gap-2">
              <!-- Author actions -->
              <template v-if="isLoggedIn && selectedPost.author_name === user?.username">
                <button @click="openEditPostForm(selectedPost)"
                  class="text-xs font-semibold text-gray-400 hover:text-blue-600 px-2 py-1 rounded-lg hover:bg-blue-50 transition-colors"
                >
                  수정
                </button>
                <button @click="deletePost(selectedPost.id)"
                  class="text-xs font-semibold text-gray-400 hover:text-red-500 px-2 py-1 rounded-lg hover:bg-red-50 transition-colors"
                >
                  삭제
                </button>
              </template>
              <button @click="closePost" class="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100 transition-colors">
                <X class="w-4 h-4" />
              </button>
            </div>
          </div>

          <!-- Body -->
          <div class="px-6 py-5">
            <h2 class="text-xl font-extrabold text-gray-900 mb-3 leading-snug">{{ selectedPost.title }}</h2>
            <div class="flex items-center gap-3 mb-5 pb-5 border-b border-gray-100">
              <div class="w-8 h-8 rounded-xl flex items-center justify-center text-white text-xs font-extrabold flex-shrink-0"
                :class="avatarColor(selectedPost.author_name)">
                {{ initials(selectedPost.author_name) }}
              </div>
              <span class="text-sm font-semibold text-gray-700">{{ selectedPost.author_name }}</span>
              <span class="text-xs text-gray-400">{{ fmtDate(selectedPost.created_at) }}</span>
              <span class="ml-auto flex items-center gap-1 text-xs text-gray-400">
                <Eye class="w-3.5 h-3.5" />{{ selectedPost.view_count }}
              </span>
            </div>
            <div class="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap min-h-[80px]">
              {{ selectedPost.content }}
            </div>
          </div>

          <!-- Comments -->
          <div class="border-t border-gray-100 bg-gray-50 px-6 py-5">
            <h3 class="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
              <MessageCircle class="w-4 h-4" />댓글 {{ selectedPost.comments?.length ?? 0 }}
            </h3>

            <!-- Comment list -->
            <div class="space-y-3 mb-5">
              <div
                v-for="c in selectedPost.comments"
                :key="c.id"
                class="bg-white rounded-xl px-4 py-3 border border-gray-100"
              >
                <div class="flex items-center gap-2 mb-1.5">
                  <div class="w-6 h-6 rounded-lg flex items-center justify-center text-white text-xs font-extrabold flex-shrink-0"
                    :class="avatarColor(c.author_name)">
                    {{ initials(c.author_name) }}
                  </div>
                  <span class="text-xs font-semibold text-gray-700">{{ c.author_name }}</span>
                  <span class="text-xs text-gray-400">{{ fmtDate(c.created_at) }}</span>
                  <button
                    v-if="isLoggedIn && c.author_name === user?.username"
                    @click="deleteComment(selectedPost.id, c.id)"
                    class="ml-auto text-gray-300 hover:text-red-400 transition-colors p-1 rounded-lg hover:bg-red-50"
                  >
                    <Trash2 class="w-3.5 h-3.5" />
                  </button>
                </div>
                <p class="text-sm text-gray-700 leading-relaxed">{{ c.content }}</p>
              </div>

              <div v-if="selectedPost.comments?.length === 0" class="text-center py-4 text-sm text-gray-400">
                첫 댓글을 남겨보세요
              </div>
            </div>

            <!-- Comment input -->
            <div v-if="isLoggedIn" class="flex gap-2">
              <input
                v-model="commentInput"
                @keydown.enter.exact.prevent="submitComment"
                placeholder="댓글을 입력하세요 (Enter로 등록)"
                class="flex-1 px-4 py-2.5 text-sm bg-white border border-gray-200 rounded-xl outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 transition-all"
                :disabled="commentLoading"
              />
              <button
                @click="submitComment"
                :disabled="!commentInput.trim() || commentLoading"
                class="px-4 py-2.5 bg-blue-700 text-white rounded-xl hover:bg-blue-800 transition-colors disabled:opacity-40 flex items-center gap-1.5 text-sm font-bold"
              >
                <Send class="w-3.5 h-3.5" />등록
              </button>
            </div>

            <!-- Login prompt -->
            <div v-else class="flex items-center gap-3 bg-white border border-gray-200 rounded-xl px-4 py-3 text-sm text-gray-500">
              <LogIn class="w-4 h-4 text-gray-400" />
              <span>댓글을 작성하려면</span>
              <RouterLink to="/login" class="font-bold text-blue-700 hover:underline">로그인</RouterLink>
              <span>이 필요합니다</span>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ── Write / Edit post modal ───────────────────────────────────────── -->
    <Teleport to="body">
      <div
        v-if="showWriteForm"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm px-4"
        @click.self="showWriteForm = false"
      >
        <div class="w-full max-w-xl bg-white rounded-2xl shadow-2xl overflow-hidden">
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
            <h2 class="font-extrabold text-gray-900">{{ editingPost ? '게시글 수정' : '글쓰기' }}</h2>
            <button @click="showWriteForm = false" class="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100">
              <X class="w-4 h-4" />
            </button>
          </div>

          <div class="px-6 py-5 space-y-4">
            <!-- Board select -->
            <div class="flex gap-2">
              <button
                v-for="board in BOARDS"
                :key="board.key"
                @click="writeForm.board_type = board.key"
                class="px-4 py-1.5 text-xs font-bold rounded-xl transition-all"
                :class="writeForm.board_type === board.key
                  ? 'bg-blue-700 text-white'
                  : 'bg-gray-100 text-gray-500 hover:bg-gray-200'"
              >
                {{ board.label }}
              </button>
            </div>

            <!-- Title -->
            <input
              v-model="writeForm.title"
              placeholder="제목을 입력하세요"
              maxlength="200"
              class="w-full px-4 py-3 text-sm font-semibold border border-gray-200 rounded-xl outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 transition-all"
            />

            <!-- Content -->
            <textarea
              v-model="writeForm.content"
              placeholder="내용을 입력하세요"
              rows="8"
              class="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 transition-all resize-none"
            ></textarea>
          </div>

          <div class="flex justify-end gap-2 px-6 py-4 border-t border-gray-100 bg-gray-50">
            <button
              @click="showWriteForm = false"
              class="px-5 py-2 text-sm font-semibold text-gray-500 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors"
            >
              취소
            </button>
            <button
              @click="submitPost"
              :disabled="!writeForm.title.trim() || !writeForm.content.trim() || writeLoading"
              class="px-5 py-2 text-sm font-bold text-white bg-blue-700 rounded-xl hover:bg-blue-800 transition-colors disabled:opacity-40"
            >
              {{ writeLoading ? '저장 중...' : (editingPost ? '수정 완료' : '등록') }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
