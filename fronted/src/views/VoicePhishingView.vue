<script setup>
import { ref, computed } from 'vue'
import NavBar from '@/components/NavBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import {
  PhoneOff, Upload, FileText, Mic, AlertTriangle,
  CheckCircle, XCircle, Loader2, RotateCcw, Clock
} from '@lucide/vue'

// ─── 상태 ──────────────────────────────────────────────────────────────────
const dragOver   = ref(false)
const file       = ref(null)
const loading    = ref(false)
const result     = ref(null)   // { probability, label, transcript, file_type, filename }
const errorMsg   = ref('')

// ─── 허용 확장자 ────────────────────────────────────────────────────────────
const ALLOWED_AUDIO = ['.wav', '.mp3', '.m4a', '.ogg', '.flac']
const ALLOWED_TEXT  = ['.txt']
const ALLOWED_ALL   = [...ALLOWED_AUDIO, ...ALLOWED_TEXT]

// ─── 파일 검증 ──────────────────────────────────────────────────────────────
function validateFile(f) {
  const ext = '.' + f.name.split('.').pop().toLowerCase()
  if (!ALLOWED_ALL.includes(ext)) {
    return `지원하지 않는 형식입니다. 지원 형식: ${ALLOWED_ALL.join(', ')}`
  }
  if (f.size > 50 * 1024 * 1024) {
    return '파일 크기는 50MB 이하여야 합니다.'
  }
  return null
}

function isAudio(f) {
  const ext = '.' + f.name.split('.').pop().toLowerCase()
  return ALLOWED_AUDIO.includes(ext)
}

// ─── 드래그 앤 드롭 / 파일 선택 ────────────────────────────────────────────
function onDrop(e) {
  dragOver.value = false
  const dropped = e.dataTransfer.files[0]
  if (dropped) selectFile(dropped)
}

function onFileInput(e) {
  const picked = e.target.files[0]
  if (picked) selectFile(picked)
  e.target.value = ''
}

function selectFile(f) {
  errorMsg.value = ''
  result.value   = null
  const err = validateFile(f)
  if (err) { errorMsg.value = err; return }
  file.value = f
}

// ─── 분석 요청 ──────────────────────────────────────────────────────────────
async function analyze() {
  if (!file.value || loading.value) return
  loading.value  = true
  errorMsg.value = ''
  result.value   = null

  const formData = new FormData()
  formData.append('file', file.value)

  try {
    const res = await fetch('/api/voicephishing/analyze/', {
      method: 'POST',
      body: formData,
    })
    const data = await res.json()
    if (!res.ok) {
      errorMsg.value = data.error || '분석 중 오류가 발생했습니다.'
    } else {
      result.value = data
    }
  } catch {
    errorMsg.value = '서버와 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.'
  } finally {
    loading.value = false
  }
}

// ─── 초기화 ─────────────────────────────────────────────────────────────────
function reset() {
  file.value     = null
  result.value   = null
  errorMsg.value = ''
}

// ─── 확률 관련 계산 ─────────────────────────────────────────────────────────
const riskLevel = computed(() => {
  if (!result.value) return null
  const p = result.value.probability
  if (p >= 0.7) return { key: 'danger', label: '위험', color: 'red' }
  if (p >= 0.4) return { key: 'warn',   label: '의심', color: 'amber' }
  return              { key: 'safe',   label: '안전', color: 'emerald' }
})

const pct = computed(() =>
  result.value ? Math.round(result.value.probability * 100) : 0
)

const gaugeColor = computed(() => {
  if (!result.value) return '#e2e8f0'
  const p = result.value.probability
  if (p >= 0.7) return '#ef4444'
  if (p >= 0.4) return '#f59e0b'
  return '#10b981'
})

// SVG arc gauge (반원)
const RADIUS = 70
const CIRC   = Math.PI * RADIUS

const arcOffset = computed(() => {
  const fraction = result.value ? result.value.probability : 0
  return CIRC * (1 - fraction)
})

// 파일 크기 포맷
function fmtSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 ** 2).toFixed(1)} MB`
}
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <NavBar />

    <main class="max-w-3xl mx-auto px-4 sm:px-6 pt-24 pb-20">

      <!-- 헤더 -->
      <div class="text-center mb-10">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-red-100 mb-4">
          <PhoneOff class="w-8 h-8 text-red-600" />
        </div>
        <h1 class="text-3xl font-black text-gray-900 mb-2">보이스피싱 탐지</h1>
        <p class="text-gray-500 text-sm leading-relaxed">
          통화 녹음 파일(.wav .mp3 .m4a) 또는 통화 스크립트(.txt)를 업로드하면<br>
          AI 모델이 보이스피싱 확률을 분석합니다.
        </p>
      </div>

      <!-- 업로드 영역 -->
      <div v-if="!result"
        class="rounded-2xl border-2 border-dashed transition-all duration-200 mb-6 cursor-pointer"
        :class="dragOver
          ? 'border-red-400 bg-red-50'
          : 'border-gray-200 bg-white hover:border-red-300 hover:bg-red-50/30'"
        @dragover.prevent="dragOver = true"
        @dragleave.prevent="dragOver = false"
        @drop.prevent="onDrop"
        @click="$refs.fileInput.click()"
      >
        <input ref="fileInput" type="file"
          :accept="ALLOWED_ALL.join(',')"
          class="hidden"
          @change="onFileInput"
        />

        <div class="py-14 flex flex-col items-center gap-3 select-none">
          <div class="w-14 h-14 rounded-xl flex items-center justify-center"
            :class="dragOver ? 'bg-red-200' : 'bg-gray-100'"
          >
            <Upload class="w-7 h-7" :class="dragOver ? 'text-red-600' : 'text-gray-400'" />
          </div>
          <div class="text-center">
            <p class="font-semibold text-gray-700">파일을 드래그하거나 클릭하여 업로드</p>
            <p class="text-sm text-gray-400 mt-1">
              오디오: .wav .mp3 .m4a &nbsp;|&nbsp; 텍스트: .txt &nbsp;|&nbsp; 최대 50MB
            </p>
          </div>
        </div>
      </div>

      <!-- 선택된 파일 카드 -->
      <div v-if="file && !result"
        class="flex items-center gap-4 p-4 bg-white border border-gray-200 rounded-xl mb-4"
      >
        <div class="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
          :class="isAudio(file) ? 'bg-blue-50' : 'bg-purple-50'"
        >
          <Mic v-if="isAudio(file)" class="w-5 h-5 text-blue-500" />
          <FileText v-else class="w-5 h-5 text-purple-500" />
        </div>
        <div class="flex-1 min-w-0">
          <p class="font-medium text-gray-800 truncate">{{ file.name }}</p>
          <p class="text-xs text-gray-400">{{ fmtSize(file.size) }} &nbsp;·&nbsp; {{ isAudio(file) ? '오디오' : '텍스트' }}</p>
        </div>
        <button @click.stop="reset"
          class="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <XCircle class="w-4 h-4" />
        </button>
      </div>

      <!-- 오류 메시지 -->
      <div v-if="errorMsg"
        class="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-xl mb-4 text-red-700 text-sm"
      >
        <AlertTriangle class="w-5 h-5 flex-shrink-0" />
        {{ errorMsg }}
      </div>

      <!-- 분석 버튼 -->
      <button v-if="!result"
        :disabled="!file || loading"
        @click="analyze"
        class="w-full py-3.5 rounded-xl font-bold text-white transition-all duration-200 flex items-center justify-center gap-2"
        :class="file && !loading
          ? 'bg-gradient-to-r from-red-600 to-rose-500 hover:from-red-700 hover:to-rose-600 shadow-md'
          : 'bg-gray-200 text-gray-400 cursor-not-allowed'"
      >
        <Loader2 v-if="loading" class="w-5 h-5 animate-spin" />
        <PhoneOff v-else class="w-5 h-5" />
        {{ loading ? '분석 중...' : '보이스피싱 분석 시작' }}
      </button>

      <!-- ─── 결과 ─────────────────────────────────────────────────────────── -->
      <div v-if="result" class="space-y-5">

        <!-- 게이지 카드 -->
        <div class="bg-white rounded-2xl border shadow-sm p-8 flex flex-col items-center"
          :class="{
            'border-red-200':    riskLevel.color === 'red',
            'border-amber-200':  riskLevel.color === 'amber',
            'border-emerald-200':riskLevel.color === 'emerald',
          }"
        >
          <!-- 반원 게이지 SVG -->
          <svg width="200" height="110" viewBox="-10 -10 220 120" class="mb-2">
            <!-- 배경 트랙 -->
            <path
              d="M 10 100 A 90 90 0 0 1 190 100"
              fill="none" stroke="#e2e8f0" stroke-width="14"
              stroke-linecap="round"
            />
            <!-- 진행 호 -->
            <path
              d="M 10 100 A 90 90 0 0 1 190 100"
              fill="none"
              :stroke="gaugeColor"
              stroke-width="14"
              stroke-linecap="round"
              stroke-dasharray="282.7"
              :stroke-dashoffset="282.7 * (1 - result.probability)"
              style="transition: stroke-dashoffset 0.8s ease, stroke 0.4s ease"
            />
            <!-- 중앙 퍼센트 텍스트 -->
            <text x="100" y="88" text-anchor="middle" font-size="28" font-weight="800"
              :fill="gaugeColor" style="font-family: system-ui, sans-serif;"
            >{{ pct }}%</text>
            <text x="100" y="108" text-anchor="middle" font-size="12" fill="#94a3b8"
              style="font-family: system-ui, sans-serif;"
            >보이스피싱 확률</text>
          </svg>

          <!-- 레이블 배지 -->
          <div class="inline-flex items-center gap-2 px-5 py-2 rounded-full font-bold text-lg mt-1"
            :class="{
              'bg-red-100 text-red-700':       riskLevel.color === 'red',
              'bg-amber-100 text-amber-700':   riskLevel.color === 'amber',
              'bg-emerald-100 text-emerald-700': riskLevel.color === 'emerald',
            }"
          >
            <XCircle       v-if="riskLevel.key === 'danger'" class="w-5 h-5" />
            <AlertTriangle v-else-if="riskLevel.key === 'warn'" class="w-5 h-5" />
            <CheckCircle   v-else class="w-5 h-5" />
            {{ riskLevel.label }}
          </div>

          <!-- 파일 정보 -->
          <p class="mt-3 text-xs text-gray-400">
            {{ result.filename }} &nbsp;·&nbsp;
            {{ result.file_type === 'audio' ? '오디오' : '텍스트' }}
          </p>
        </div>

        <!-- 위험도 안내 -->
        <div class="rounded-xl p-4 text-sm leading-relaxed"
          :class="{
            'bg-red-50 border border-red-200 text-red-800':        riskLevel.color === 'red',
            'bg-amber-50 border border-amber-200 text-amber-800':  riskLevel.color === 'amber',
            'bg-emerald-50 border border-emerald-200 text-emerald-800': riskLevel.color === 'emerald',
          }"
        >
          <p v-if="riskLevel.key === 'danger'" class="font-semibold mb-1">⚠️ 보이스피싱 가능성이 높습니다</p>
          <p v-if="riskLevel.key === 'danger'">즉시 통화를 종료하고, 피해가 발생했다면 금융감독원(1332) 또는 경찰청(182)에 신고하세요.</p>

          <p v-if="riskLevel.key === 'warn'" class="font-semibold mb-1">주의가 필요합니다</p>
          <p v-if="riskLevel.key === 'warn'">보이스피싱 의심 패턴이 감지되었습니다. 개인정보나 금융정보를 절대 제공하지 마세요.</p>

          <p v-if="riskLevel.key === 'safe'" class="font-semibold mb-1">안전한 통화로 판단됩니다</p>
          <p v-if="riskLevel.key === 'safe'">보이스피싱 패턴이 낮게 감지되었습니다. 그래도 개인정보 제공에는 항상 주의하세요.</p>
        </div>

        <!-- 스크립트 (오디오 변환 결과 또는 txt 내용) -->
        <div v-if="result.transcript" class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
            <FileText class="w-4 h-4 text-gray-400" />
            {{ result.file_type === 'audio' ? '음성 변환 텍스트' : '업로드된 스크립트' }}
          </h3>
          <p class="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap max-h-52 overflow-y-auto">{{ result.transcript }}</p>
        </div>

        <!-- 다시 분석 버튼 -->
        <button @click="reset"
          class="w-full py-3 rounded-xl border-2 border-gray-200 font-bold text-gray-600 hover:border-gray-300 hover:bg-gray-50 transition-all flex items-center justify-center gap-2"
        >
          <RotateCcw class="w-4 h-4" />
          다른 파일 분석하기
        </button>
      </div>

      <!-- 사용 안내 -->
      <div v-if="!result" class="mt-10 grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div v-for="tip in [
          { icon: Mic,       title: '오디오 업로드',    desc: '통화 녹음 파일(.wav/.mp3)을 바로 업로드하세요.' },
          { icon: FileText,  title: '텍스트 업로드',    desc: '통화 내용을 txt 파일로 저장 후 업로드하세요.' },
          { icon: Clock,     title: '즉시 결과 확인',   desc: '서버에서 AI 모델이 분석 후 확률을 반환합니다.' },
        ]" :key="tip.title"
          class="p-4 bg-white rounded-xl border border-gray-100 text-center"
        >
          <div class="inline-flex items-center justify-center w-10 h-10 bg-gray-50 rounded-lg mb-3">
            <component :is="tip.icon" class="w-5 h-5 text-gray-500" />
          </div>
          <p class="text-sm font-bold text-gray-800 mb-1">{{ tip.title }}</p>
          <p class="text-xs text-gray-500 leading-snug">{{ tip.desc }}</p>
        </div>
      </div>

    </main>
    <AppFooter />
  </div>
</template>
