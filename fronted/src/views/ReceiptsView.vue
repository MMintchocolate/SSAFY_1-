<script setup>
import { ref, computed, onMounted } from 'vue'
import NavBar from '@/components/NavBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import {
  UploadCloud, ScanText, X, FileText, FileDown,
  CheckCircle, ChevronLeft, ChevronRight, Clock, Plus, Trash2,
} from '@lucide/vue'
import { useAuth } from '@/composables/useAuth'

const { authFetch } = useAuth()

// ════════════════════════════════════════════════════════════
// 날짜 유틸
// ════════════════════════════════════════════════════════════
const DAY_LABELS = ['일', '월', '화', '수', '목', '금', '토']

function toDateKey(date) {
  return `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`
}
function fmtTime(iso) {
  return new Date(iso).toTimeString().slice(0, 5)
}
function fmtMonthTitle(date) {
  return `${date.getFullYear()}년 ${date.getMonth() + 1}월`
}
function fmtDayTitle(date) {
  return `${date.getMonth() + 1}월 ${date.getDate()}일`
}
function isSameDay(a, b) {
  return a && b &&
    a.getFullYear() === b.getFullYear() &&
    a.getMonth()    === b.getMonth()    &&
    a.getDate()     === b.getDate()
}

// ════════════════════════════════════════════════════════════
// 영수증 목록 & 달력
// ════════════════════════════════════════════════════════════
const receiptHistory = ref([])
const historyLoading = ref(false)
const calMonth       = ref(new Date())
const selectedDay    = ref(null)

async function fetchReceiptList() {
  historyLoading.value = true
  try {
    const res  = await authFetch('/api/receipts/')
    const json = await res.json()
    if (res.ok) receiptHistory.value = json
  } catch (_) {}
  finally { historyLoading.value = false }
}

const datesWithReceipts = computed(() => {
  const s = new Set()
  for (const r of receiptHistory.value) s.add(toDateKey(new Date(r.created_at)))
  return s
})

const dayReceipts = computed(() => {
  if (!selectedDay.value) return []
  const key = toDateKey(selectedDay.value)
  return receiptHistory.value.filter(r => toDateKey(new Date(r.created_at)) === key)
})

const calendarGrid = computed(() => {
  const y   = calMonth.value.getFullYear()
  const m   = calMonth.value.getMonth()
  const first = new Date(y, m, 1)
  const last  = new Date(y, m + 1, 0)
  const cells = []

  for (let i = 0; i < first.getDay(); i++)
    cells.push({ date: new Date(y, m, i - first.getDay() + 1), cur: false })

  for (let d = 1; d <= last.getDate(); d++)
    cells.push({ date: new Date(y, m, d), cur: true })

  let next = 1
  while (cells.length < 42)
    cells.push({ date: new Date(y, m + 1, next++), cur: false })

  return cells
})

function prevMonth() { calMonth.value = new Date(calMonth.value.getFullYear(), calMonth.value.getMonth() - 1, 1) }
function nextMonth() { calMonth.value = new Date(calMonth.value.getFullYear(), calMonth.value.getMonth() + 1, 1) }

function selectDay(cell) {
  if (!cell.cur) return
  selectedDay.value = isSameDay(selectedDay.value, cell.date) ? null : cell.date
}

function loadReceipt(r) {
  resultText.value    = r.text
  lastReceiptId.value = r.id
  dbImageUrl.value    = r.image_url ? `http://localhost:8000${r.image_url}` : null
  error.value         = null
  formData.value      = null
  classifyError.value = null
  setTimeout(() => document.getElementById('ocr-result')?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50)
}

// ════════════════════════════════════════════════════════════
// OCR 섹션
// ════════════════════════════════════════════════════════════
const isDragOver    = ref(false)
const file          = ref(null)
const preview       = ref(null)
const loading       = ref(false)
const error         = ref(null)
const resultText    = ref(null)
const dbImageUrl    = ref(null)
const lastReceiptId = ref(null)

function onDragOver(e)   { e.preventDefault(); isDragOver.value = true }
function onDragLeave()   { isDragOver.value = false }
function onDrop(e)       { e.preventDefault(); isDragOver.value = false; setFile(e.dataTransfer.files[0]) }
function onFileChange(e) { setFile(e.target.files[0]) }
function setFile(f) {
  if (!f) return
  file.value = f; resultText.value = null; error.value = null
  preview.value = f.type.startsWith('image/') ? URL.createObjectURL(f) : null
}
function reset() {
  file.value = preview.value = resultText.value = error.value = null
  lastReceiptId.value = null
  formData.value = null
  classifyError.value = null
}

async function runOcr() {
  if (!file.value) return
  loading.value = true; error.value = null; resultText.value = null
  const form = new FormData()
  form.append('image', file.value)
  try {
    const res  = await authFetch('/api/receipts/ocr/', { method: 'POST', body: form })
    const json = await res.json()
    if (!res.ok) throw new Error(json.error ?? `HTTP ${res.status}`)
    resultText.value    = json.text
    lastReceiptId.value = json.receipt_id
    dbImageUrl.value    = null
    formData.value      = null
    await fetchReceiptList()
    calMonth.value    = new Date()
    selectedDay.value = new Date()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

// ════════════════════════════════════════════════════════════
// AI 양식 분류 & PDF 생성 섹션
// ════════════════════════════════════════════════════════════
const classifyLoading = ref(false)
const classifyError   = ref(null)
const templateType    = ref(null)
const formData        = ref(null)
const pdfLoading      = ref(false)
const pdfError        = ref(null)

const computedTotal = computed(() => {
  if (!formData.value?.items) return 0
  return formData.value.items.reduce((s, it) => {
    return s + (parseInt(it.quantity) || 0) * (parseInt(it.unit_price) || 0)
  }, 0)
})

function addItem() {
  if (!formData.value) return
  const no = formData.value.items.length + 1
  formData.value.items.push({ no, name: '', quantity: 1, unit_price: 0, amount: 0, note: '' })
}

function removeItem(idx) {
  formData.value.items.splice(idx, 1)
  formData.value.items.forEach((it, i) => { it.no = i + 1 })
}

async function classifyReceipt() {
  if (!lastReceiptId.value) return
  classifyLoading.value = true
  classifyError.value   = null
  formData.value        = null
  try {
    const res  = await authFetch('/api/forms/classify/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ receipt_id: lastReceiptId.value }),
    })
    const json = await res.json()
    if (!res.ok) throw new Error(json.error ?? `HTTP ${res.status}`)
    templateType.value = json.template_type
    formData.value     = json.data
    setTimeout(() => document.getElementById('form-editor')?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50)
  } catch (e) {
    classifyError.value = e.message
  } finally {
    classifyLoading.value = false
  }
}

async function downloadPdf() {
  if (!formData.value) return
  pdfLoading.value = true
  pdfError.value   = null
  try {
    const res = await authFetch('/api/forms/render/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ template_type: templateType.value, data: formData.value, receipt_id: lastReceiptId.value }),
    })
    if (!res.ok) {
      const j = await res.json()
      throw new Error(j.error ?? `HTTP ${res.status}`)
    }
    const blob = await res.blob()
    const url  = URL.createObjectURL(blob)
    const date = formData.value.date || new Date().toISOString().slice(0, 10)
    const a    = Object.assign(document.createElement('a'), {
      href: url,
      download: `지출결의서_${date}.pdf`,
    })
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    pdfError.value = e.message
  } finally {
    pdfLoading.value = false
  }
}

onMounted(() => { fetchReceiptList() })
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <NavBar />
    <main class="pt-24 pb-16 max-w-2xl mx-auto px-4 sm:px-6">

      <!-- 헤더 -->
      <div class="mb-8">
        <div class="inline-flex items-center gap-2 bg-purple-50 text-purple-700 text-xs font-bold px-3 py-1.5 rounded-full mb-3 border border-purple-100">
          <ScanText class="w-3 h-3" />CLOVA OCR
        </div>
        <h1 class="text-3xl font-extrabold text-gray-900 mb-1">영수증 장부</h1>
        <p class="text-gray-400">영수증 이미지를 올리면 텍스트를 추출합니다</p>
      </div>

      <!-- ── 1. 업로드 & OCR ── -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-4">
        <label
          v-if="!file"
          class="flex flex-col items-center gap-4 border-2 border-dashed rounded-2xl p-10 cursor-pointer transition-all"
          :class="isDragOver ? 'border-purple-500 bg-purple-50' : 'border-gray-200 hover:border-purple-300 hover:bg-purple-50/30'"
          @dragover="onDragOver" @dragleave="onDragLeave" @drop="onDrop"
        >
          <input type="file" accept="image/*" class="hidden" @change="onFileChange" />
          <div class="w-14 h-14 bg-purple-100 rounded-2xl flex items-center justify-center">
            <UploadCloud class="w-7 h-7 text-purple-500" />
          </div>
          <div class="text-center">
            <p class="font-bold text-gray-700">영수증을 여기에 놓으세요</p>
            <p class="text-sm text-gray-400 mt-0.5">또는 <span class="text-purple-600">파일 선택</span></p>
          </div>
          <div class="flex gap-2">
            <span class="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded font-medium">JPG</span>
            <span class="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded font-medium">PNG</span>
          </div>
        </label>

        <div v-else>
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
                <FileText class="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p class="text-sm font-semibold text-gray-900 truncate max-w-xs">{{ file.name }}</p>
                <p class="text-xs text-gray-400">{{ (file.size / 1024).toFixed(1) }} KB</p>
              </div>
            </div>
            <button @click="reset" class="p-1.5 rounded-lg hover:bg-gray-100 transition-colors">
              <X class="w-4 h-4 text-gray-400" />
            </button>
          </div>
          <img v-if="preview" :src="preview" alt="미리보기" class="w-full max-h-64 object-contain rounded-xl border border-gray-100 mb-4" />
          <button @click="runOcr" :disabled="loading"
            class="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-purple-700 text-white font-bold text-sm hover:bg-purple-800 transition-colors disabled:opacity-50"
          >
            <ScanText class="w-4 h-4" />{{ loading ? '분석 중...' : '텍스트 추출' }}
          </button>
        </div>
      </div>

      <!-- 에러 / OCR 결과 -->
      <div v-if="error" class="bg-red-50 border border-red-200 rounded-2xl p-4 mb-4 text-sm text-red-600 font-medium">{{ error }}</div>

      <div v-if="resultText !== null" id="ocr-result" class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs font-bold text-gray-400 uppercase tracking-wider">인식 결과</p>
          <span v-if="lastReceiptId" class="text-xs text-emerald-600 font-semibold bg-emerald-50 px-2 py-0.5 rounded-full">ID #{{ lastReceiptId }}</span>
        </div>
        <img v-if="dbImageUrl" :src="dbImageUrl" class="w-full max-h-64 object-contain rounded-xl border border-gray-100 mb-4" />
        <pre class="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed font-mono bg-gray-50 rounded-xl p-4 max-h-96 overflow-y-auto">{{ resultText || '인식된 텍스트가 없습니다.' }}</pre>
      </div>

      <!-- ── 2. 달력 ── -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-4">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 bg-purple-100 rounded-xl flex items-center justify-center">
              <Clock class="w-4 h-4 text-purple-600" />
            </div>
            <p class="text-sm font-bold text-gray-800">내 영수증 달력</p>
          </div>
          <div class="flex items-center gap-1">
            <button @click="prevMonth" class="p-1.5 rounded-lg hover:bg-gray-100 transition-colors">
              <ChevronLeft class="w-4 h-4 text-gray-500" />
            </button>
            <span class="text-sm font-bold text-gray-700 w-28 text-center">{{ fmtMonthTitle(calMonth) }}</span>
            <button @click="nextMonth" class="p-1.5 rounded-lg hover:bg-gray-100 transition-colors">
              <ChevronRight class="w-4 h-4 text-gray-500" />
            </button>
          </div>
        </div>

        <div class="grid grid-cols-7 mb-1">
          <div v-for="d in DAY_LABELS" :key="d"
            class="text-center text-xs font-bold py-1"
            :class="d === '일' ? 'text-red-400' : d === '토' ? 'text-blue-400' : 'text-gray-400'"
          >{{ d }}</div>
        </div>

        <div class="grid grid-cols-7 gap-y-1">
          <div
            v-for="(cell, i) in calendarGrid" :key="i"
            @click="selectDay(cell)"
            class="relative flex flex-col items-center py-1.5 rounded-xl transition-all"
            :class="[
              cell.cur ? 'cursor-pointer' : 'cursor-default opacity-30 pointer-events-none',
              isSameDay(cell.date, selectedDay)
                ? 'bg-purple-600'
                : cell.cur ? 'hover:bg-purple-50' : '',
            ]"
          >
            <span
              class="text-sm font-semibold leading-none"
              :class="[
                isSameDay(cell.date, selectedDay) ? 'text-white' :
                isSameDay(cell.date, new Date())  ? 'text-purple-600 font-black' :
                cell.date.getDay() === 0 ? 'text-red-400' :
                cell.date.getDay() === 6 ? 'text-blue-400' : 'text-gray-700'
              ]"
            >{{ cell.date.getDate() }}</span>

            <span v-if="isSameDay(cell.date, new Date()) && !isSameDay(cell.date, selectedDay)"
              class="absolute bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-purple-500"
            />

            <span v-if="datesWithReceipts.has(toDateKey(cell.date))"
              class="mt-0.5 w-1.5 h-1.5 rounded-full"
              :class="isSameDay(cell.date, selectedDay) ? 'bg-white/80' : 'bg-purple-400'"
            />
          </div>
        </div>

        <div v-if="selectedDay" class="mt-4 pt-4 border-t border-gray-100">
          <p class="text-xs font-bold text-gray-500 mb-3">
            {{ fmtDayTitle(selectedDay) }} 영수증
            <span class="ml-1 text-purple-600">{{ dayReceipts.length }}건</span>
          </p>

          <div v-if="dayReceipts.length === 0" class="text-sm text-gray-400 text-center py-4">
            이 날 업로드된 영수증이 없습니다
          </div>

          <div v-else class="space-y-2">
            <div
              v-for="r in dayReceipts" :key="r.id"
              class="flex items-center gap-3 p-3 rounded-xl border transition-colors"
              :class="lastReceiptId === r.id ? 'border-purple-300 bg-purple-50' : 'border-gray-100 hover:border-purple-200 hover:bg-gray-50'"
            >
              <div class="w-10 h-10 rounded-lg overflow-hidden flex-shrink-0 border border-gray-100 bg-gray-50 flex items-center justify-center">
                <img v-if="r.image_url" :src="`http://localhost:8000${r.image_url}`" class="w-full h-full object-cover" alt="" />
                <FileText v-else class="w-5 h-5 text-gray-300" />
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-semibold text-gray-800 truncate">{{ r.original_filename || '영수증' }}</p>
                <p class="text-xs text-gray-400 flex items-center gap-1 mt-0.5">
                  <Clock class="w-3 h-3" />{{ fmtTime(r.created_at) }}
                  <span v-if="lastReceiptId === r.id" class="text-purple-600 font-bold">· 선택됨</span>
                </p>
              </div>
              <button
                @click="loadReceipt(r)"
                class="flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-bold transition-colors"
                :class="lastReceiptId === r.id
                  ? 'bg-purple-100 text-purple-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-purple-100 hover:text-purple-700'"
              >{{ lastReceiptId === r.id ? '선택됨' : '불러오기' }}</button>
            </div>
          </div>
        </div>

        <div class="mt-4 pt-3 border-t border-gray-100 flex items-center gap-4 text-xs text-gray-400">
          <span class="flex items-center gap-1.5"><span class="w-1.5 h-1.5 rounded-full bg-purple-400 inline-block"></span>영수증 있는 날</span>
          <span class="flex items-center gap-1.5"><span class="w-1 h-1 rounded-full bg-purple-500 inline-block"></span>오늘</span>
          <span class="flex items-center gap-1.5"><span class="w-4 h-4 rounded bg-purple-600 inline-block"></span>선택된 날</span>
        </div>
      </div>

      <!-- ── 3. AI 양식 분류 & PDF 생성 ── -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-4">
        <div class="flex items-center gap-2 mb-4">
          <div class="w-8 h-8 bg-emerald-100 rounded-xl flex items-center justify-center">
            <FileDown class="w-4 h-4 text-emerald-600" />
          </div>
          <div>
            <p class="text-sm font-bold text-gray-800">지출결의서 자동 생성</p>
            <p class="text-xs text-gray-400">영수증을 AI로 분석하여 지출결의서 PDF를 생성합니다</p>
          </div>
        </div>

        <!-- 영수증 상태 표시 -->
        <div class="flex items-center gap-1.5 mb-4 text-xs">
          <span class="w-1.5 h-1.5 rounded-full" :class="lastReceiptId ? 'bg-emerald-500' : 'bg-gray-300'"></span>
          <span :class="lastReceiptId ? 'text-emerald-600 font-semibold' : 'text-gray-400'">
            {{ lastReceiptId ? `영수증 #${lastReceiptId} 선택됨` : '위에서 영수증을 선택하거나 업로드하세요' }}
          </span>
        </div>

        <!-- 분류 버튼 -->
        <button
          @click="classifyReceipt"
          :disabled="classifyLoading || !lastReceiptId"
          class="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-emerald-600 text-white font-bold text-sm hover:bg-emerald-700 transition-colors disabled:opacity-40 mb-3"
        >
          <ScanText class="w-4 h-4" />
          {{ classifyLoading ? 'AI 분석 중...' : '영수증 분석 및 양식 생성' }}
        </button>
        <p v-if="classifyError" class="mb-3 text-xs text-red-500 font-medium">{{ classifyError }}</p>

        <!-- 편집 폼 -->
        <div v-if="formData" id="form-editor" class="border border-gray-200 rounded-xl overflow-hidden">
          <div class="bg-emerald-50 px-4 py-2.5 flex items-center gap-2 border-b border-gray-200">
            <CheckCircle class="w-4 h-4 text-emerald-600" />
            <p class="text-sm font-bold text-emerald-700">지출결의서 내용 확인 및 수정</p>
          </div>

          <div class="p-4 space-y-3">
            <!-- 기본 정보 -->
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-gray-500 mb-1">문서 제목</label>
                <input v-model="formData.title" type="text"
                  class="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-300"
                />
              </div>
              <div>
                <label class="block text-xs font-bold text-gray-500 mb-1">일자</label>
                <input v-model="formData.date" type="date"
                  class="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-300"
                />
              </div>
              <div>
                <label class="block text-xs font-bold text-gray-500 mb-1">부서</label>
                <input v-model="formData.department" type="text"
                  class="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-300"
                />
              </div>
              <div>
                <label class="block text-xs font-bold text-gray-500 mb-1">신청자</label>
                <input v-model="formData.applicant" type="text"
                  class="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-300"
                />
              </div>
            </div>
            <div>
              <label class="block text-xs font-bold text-gray-500 mb-1">지출 목적</label>
              <input v-model="formData.purpose" type="text"
                class="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-300"
              />
            </div>

            <!-- 품목 테이블 -->
            <div>
              <div class="flex items-center justify-between mb-2">
                <label class="text-xs font-bold text-gray-500">품목 내역</label>
                <button @click="addItem"
                  class="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-100 text-emerald-700 text-xs font-bold hover:bg-emerald-200 transition-colors"
                >
                  <Plus class="w-3 h-3" />행 추가
                </button>
              </div>

              <div class="overflow-x-auto rounded-xl border border-gray-200">
                <table class="w-full text-xs">
                  <thead>
                    <tr class="bg-gray-50 border-b border-gray-200">
                      <th class="px-2 py-2 text-gray-600 font-bold text-center w-8">No</th>
                      <th class="px-2 py-2 text-gray-600 font-bold text-left">품목명</th>
                      <th class="px-2 py-2 text-gray-600 font-bold text-center w-16">수량</th>
                      <th class="px-2 py-2 text-gray-600 font-bold text-right w-24">단가 (원)</th>
                      <th class="px-2 py-2 text-gray-600 font-bold text-right w-24">금액 (원)</th>
                      <th class="px-2 py-2 text-gray-600 font-bold text-left">비고</th>
                      <th class="px-2 py-2 w-8"></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, idx) in formData.items" :key="idx" class="border-b border-gray-100 last:border-none">
                      <td class="px-2 py-1.5 text-center text-gray-400">{{ idx + 1 }}</td>
                      <td class="px-2 py-1.5">
                        <input v-model="item.name" type="text" placeholder="품목명"
                          class="w-full px-2 py-1 rounded border border-gray-200 text-xs focus:outline-none focus:ring-1 focus:ring-emerald-300"
                        />
                      </td>
                      <td class="px-2 py-1.5">
                        <input v-model.number="item.quantity" type="number" min="1"
                          class="w-full px-2 py-1 rounded border border-gray-200 text-xs text-center focus:outline-none focus:ring-1 focus:ring-emerald-300"
                        />
                      </td>
                      <td class="px-2 py-1.5">
                        <input v-model.number="item.unit_price" type="number" min="0"
                          class="w-full px-2 py-1 rounded border border-gray-200 text-xs text-right focus:outline-none focus:ring-1 focus:ring-emerald-300"
                        />
                      </td>
                      <td class="px-2 py-1.5 text-right font-semibold text-gray-700 tabular-nums">
                        {{ ((item.quantity || 0) * (item.unit_price || 0)).toLocaleString() }}
                      </td>
                      <td class="px-2 py-1.5">
                        <input v-model="item.note" type="text" placeholder="비고"
                          class="w-full px-2 py-1 rounded border border-gray-200 text-xs focus:outline-none focus:ring-1 focus:ring-emerald-300"
                        />
                      </td>
                      <td class="px-2 py-1.5 text-center">
                        <button @click="removeItem(idx)" class="p-1 rounded text-gray-300 hover:text-red-500 hover:bg-red-50 transition-colors">
                          <Trash2 class="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  </tbody>
                  <tfoot>
                    <tr class="bg-gray-50 border-t border-gray-200 font-bold">
                      <td colspan="4" class="px-2 py-2 text-right text-gray-600 text-xs">합계</td>
                      <td class="px-2 py-2 text-right text-emerald-700 tabular-nums">{{ computedTotal.toLocaleString() }}</td>
                      <td colspan="2"></td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
          </div>

          <!-- PDF 다운로드 버튼 -->
          <div class="px-4 pb-4">
            <button @click="downloadPdf" :disabled="pdfLoading"
              class="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-emerald-700 text-white font-bold text-sm hover:bg-emerald-800 transition-colors disabled:opacity-40"
            >
              <FileDown class="w-4 h-4" />
              {{ pdfLoading ? 'PDF 생성 중...' : '지출결의서 PDF 다운로드' }}
            </button>
            <p v-if="pdfError" class="mt-2 text-xs text-red-500 font-medium">{{ pdfError }}</p>
          </div>
        </div>
      </div>

    </main>
    <AppFooter />
  </div>
</template>
