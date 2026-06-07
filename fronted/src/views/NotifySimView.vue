<script setup>
import { ref, computed } from 'vue'
import { CreditCard, Bell, Check, Trash2 } from '@lucide/vue'
import { useAuth } from '@/composables/useAuth'

const { authFetch } = useAuth()

const CATEGORIES = [
  '카페', '식비', '편의점', '교통', '쇼핑',
  '의료', '문화', '구독', '통신', '현금출금', '이체', '기타',
]

const CAT_STYLE = {
  '카페':    { bg: 'bg-amber-100',  text: 'text-amber-700',  hover: 'hover:bg-amber-200'  },
  '식비':    { bg: 'bg-orange-100', text: 'text-orange-700', hover: 'hover:bg-orange-200' },
  '편의점':  { bg: 'bg-blue-100',   text: 'text-blue-700',   hover: 'hover:bg-blue-200'   },
  '교통':    { bg: 'bg-sky-100',    text: 'text-sky-700',    hover: 'hover:bg-sky-200'    },
  '쇼핑':    { bg: 'bg-pink-100',   text: 'text-pink-700',   hover: 'hover:bg-pink-200'   },
  '의료':    { bg: 'bg-red-100',    text: 'text-red-700',    hover: 'hover:bg-red-200'    },
  '문화':    { bg: 'bg-purple-100', text: 'text-purple-700', hover: 'hover:bg-purple-200' },
  '구독':    { bg: 'bg-violet-100', text: 'text-violet-700', hover: 'hover:bg-violet-200' },
  '통신':    { bg: 'bg-cyan-100',   text: 'text-cyan-700',   hover: 'hover:bg-cyan-200'   },
  '현금출금': { bg: 'bg-gray-100',   text: 'text-gray-700',   hover: 'hover:bg-gray-200'   },
  '이체':    { bg: 'bg-teal-100',   text: 'text-teal-700',   hover: 'hover:bg-teal-200'   },
  '기타':    { bg: 'bg-slate-100',  text: 'text-slate-600',  hover: 'hover:bg-slate-200'  },
}

function catClass(cat) {
  const s = CAT_STYLE[cat] ?? CAT_STYLE['기타']
  return `${s.bg} ${s.text} ${s.hover}`
}

const merchantInput = ref('')
const amountInput   = ref('')
const notification  = ref(null)   // { merchant, amount, time }
const history       = ref([])     // { merchant, amount, category, saved }
const savingIdx     = ref(null)

const totalByCategory = computed(() => {
  const map = {}
  for (const tx of history.value) {
    map[tx.category] = (map[tx.category] ?? 0) + tx.amount
  }
  return Object.entries(map).sort((a, b) => b[1] - a[1])
})

const totalAmount = computed(() => history.value.reduce((s, tx) => s + tx.amount, 0))

function fmt(n) {
  return Number(n).toLocaleString('ko-KR') + '원'
}

function simulate() {
  const name = merchantInput.value.trim()
  const amt  = parseInt(String(amountInput.value).replace(/,/g, ''), 10)
  if (!name || isNaN(amt) || amt <= 0) return
  notification.value = {
    merchant: name,
    amount:   amt,
    time:     new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }),
  }
  merchantInput.value = ''
  amountInput.value   = ''
}

async function classify(category) {
  if (!notification.value) return
  const tx = { ...notification.value, category, saved: false }
  notification.value = null
  history.value.unshift(tx)
  const idx = 0

  savingIdx.value = idx
  try {
    await authFetch('/api/spending/add-mapping/', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ merchant: tx.merchant, category }),
    })
    history.value[idx].saved = true
  } catch {
    // 저장 실패해도 로컬 기록은 유지
  } finally {
    savingIdx.value = null
  }
}

function removeItem(idx) {
  history.value.splice(idx, 1)
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 pt-4 pb-10 px-3 sm:px-6">
    <div class="max-w-2xl mx-auto space-y-4">

      <!-- Header -->
      <div class="pt-2">
        <h1 class="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Bell class="w-5 h-5 sm:w-6 sm:h-6 text-indigo-500" />
          결제 알림 시뮬레이터
        </h1>
        <p class="text-xs sm:text-sm text-gray-500 mt-1">
          가맹점명과 금액을 입력하면 알림 카드가 뜹니다. 카테고리를 탭하면 자동 저장됩니다.
        </p>
      </div>

      <!-- Input -->
      <div class="bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
        <div class="flex flex-col gap-2">
          <!-- 가맹점명: 항상 한 줄 전체 -->
          <input
            v-model="merchantInput"
            placeholder="가맹점명 (예: 스타벅스강남역점)"
            class="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            @keydown.enter="simulate"
          />
          <!-- 금액 -->
          <input
            v-model="amountInput"
            placeholder="금액 (원)"
            type="number"
            min="1"
            class="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            @keydown.enter="simulate"
          />
          <!-- 버튼: 항상 전체 너비 -->
          <button
            @click="simulate"
            class="w-full bg-indigo-500 hover:bg-indigo-600 active:bg-indigo-700 text-white py-3 rounded-xl text-sm font-semibold transition"
          >
            결제 발생
          </button>
        </div>
      </div>

      <!-- Notification card -->
      <Transition name="notif">
        <div
          v-if="notification"
          class="bg-gray-900 text-white rounded-2xl p-4 sm:p-5 shadow-2xl"
        >
          <!-- top bar -->
          <div class="flex items-center gap-2 mb-3">
            <div class="w-8 h-8 bg-indigo-500 rounded-xl flex items-center justify-center flex-shrink-0">
              <CreditCard class="w-4 h-4" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-[11px] text-gray-400">SafeFinance · {{ notification.time }}</p>
              <p class="text-xs text-gray-300 font-medium">카드 결제 알림</p>
            </div>
          </div>

          <!-- transaction -->
          <div class="bg-gray-800 rounded-xl px-4 py-3 mb-4">
            <p class="text-sm sm:text-base font-semibold truncate">{{ notification.merchant }}</p>
            <p class="text-indigo-300 text-lg sm:text-xl font-bold mt-0.5">{{ fmt(notification.amount) }}</p>
          </div>

          <!-- category buttons -->
          <p class="text-[11px] text-gray-400 mb-2">카테고리를 선택하세요</p>
          <div class="grid grid-cols-4 gap-1.5 sm:flex sm:flex-wrap sm:gap-2">
            <button
              v-for="cat in CATEGORIES"
              :key="cat"
              @click="classify(cat)"
              class="px-2 py-2 sm:px-3 sm:py-1.5 rounded-lg text-xs sm:text-sm font-medium transition cursor-pointer text-center"
              :class="catClass(cat)"
            >
              {{ cat }}
            </button>
          </div>
        </div>
      </Transition>

      <!-- History -->
      <div v-if="history.length" class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
          <h2 class="text-sm font-semibold text-gray-700">분류 내역</h2>
          <span class="text-sm font-bold text-indigo-600">총 {{ fmt(totalAmount) }}</span>
        </div>

        <ul class="divide-y divide-gray-50">
          <li
            v-for="(tx, idx) in history"
            :key="idx"
            class="px-4 py-3"
          >
            <!-- 상단: 카테고리 + 가맹점 + 삭제 -->
            <div class="flex items-center gap-2 mb-1">
              <span
                class="text-xs px-2 py-0.5 rounded-lg font-medium flex-shrink-0"
                :class="catClass(tx.category)"
              >{{ tx.category }}</span>
              <span class="flex-1 text-sm text-gray-800 truncate">{{ tx.merchant }}</span>
              <button
                @click="removeItem(idx)"
                class="text-gray-300 hover:text-red-400 transition flex-shrink-0 ml-1"
              >
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
            <!-- 하단: 금액 + 저장 상태 -->
            <div class="flex items-center gap-2 pl-0.5">
              <span class="text-sm font-semibold text-gray-700">{{ fmt(tx.amount) }}</span>
              <span v-if="tx.saved" class="text-[11px] text-green-500 flex items-center gap-0.5">
                <Check class="w-3 h-3" />저장됨
              </span>
              <span v-else-if="savingIdx === idx" class="text-[11px] text-gray-400">저장 중…</span>
            </div>
          </li>
        </ul>

        <!-- category totals -->
        <div class="px-4 py-3 bg-gray-50 border-t border-gray-100 flex flex-wrap gap-1.5">
          <span
            v-for="[cat, amt] in totalByCategory"
            :key="cat"
            class="text-xs px-2 py-1 rounded-lg font-medium"
            :class="catClass(cat)"
          >
            {{ cat }} {{ fmt(amt) }}
          </span>
        </div>
      </div>

      <!-- Empty state -->
      <div
        v-else-if="!notification"
        class="text-center py-14 text-gray-400"
      >
        <CreditCard class="w-10 h-10 mx-auto mb-3 opacity-30" />
        <p class="text-sm">가맹점명과 금액을 입력하고<br><strong>결제 발생</strong>을 눌러보세요.</p>
      </div>

    </div>
  </div>
</template>

<style scoped>
.notif-enter-active {
  animation: slide-down 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.notif-leave-active {
  animation: slide-down 0.15s ease-in reverse;
}
@keyframes slide-down {
  from { transform: translateY(-20px); opacity: 0; }
  to   { transform: translateY(0);     opacity: 1; }
}
</style>
