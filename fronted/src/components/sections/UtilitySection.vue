<script setup>
import { ref } from 'vue'
import { Receipt, UploadCloud, MapPin, Crosshair, Clock } from '@lucide/vue'

// --- 영수증 장부 ---
const isDragOver = ref(false)
const uploadedFile = ref(null)

function onDragOver(e) {
  e.preventDefault()
  isDragOver.value = true
}
function onDragLeave() {
  isDragOver.value = false
}
function onDrop(e) {
  e.preventDefault()
  isDragOver.value = false
  const file = e.dataTransfer.files[0]
  if (file) uploadedFile.value = file.name
  // TODO: 파일 업로드 후 OCR API 호출
}
function onFileChange(e) {
  const file = e.target.files[0]
  if (file) uploadedFile.value = file.name
  // TODO: 파일 업로드 후 OCR API 호출
}
function resetUpload() {
  uploadedFile.value = null
}

// TODO: API 연결 - 주간 지출 데이터 조회
// 예상 구조: [{ day: '월', amount: 50000 }, ...]
const weeklyExpenses = ref([])

// TODO: API 연결 - 이번주 지출 통계 조회
const expenseStats = ref(null)
/*  예상 구조:
    {
      thisWeek: number,   // 이번주 총 지출
      diff: number,       // 전주 대비 (음수면 감소)
      receiptCount: number
    }
*/

// --- 지점 찾기 ---
// TODO: API 연결 - 현재 위치 기반 인근 지점 조회 (카카오맵 API 또는 자체 API)
const nearbyBranches = ref([])
/*  예상 구조:
    [
      {
        bankCode: string,
        bankName: string,
        branchName: string,
        address: string,
        distance: string,  // 예: '320m'
        isOpen: boolean,
      }
    ]
*/

// 바 차트 최대값 계산
const maxAmount = (list) => Math.max(...list.map(d => d.amount), 1)
</script>

<template>
  <section id="utility" class="py-24 bg-slate-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6">

      <!-- 섹션 헤더 -->
      <div class="text-center mb-14">
        <div class="inline-flex items-center gap-2 bg-blue-50 text-blue-700 text-xs font-bold px-3 py-1.5 rounded-full mb-4 uppercase tracking-widest border border-blue-100">
          스마트 생활 도구
        </div>
        <h2 class="text-4xl font-extrabold text-gray-900 tracking-tight mb-3">관리 &amp; 탐색</h2>
        <p class="text-gray-400 text-lg">지출을 추적하고 인근 안전 지점을 찾아보세요</p>
      </div>

      <div class="grid lg:grid-cols-2 gap-8">

        <!-- ─── 영수증 장부 (좌) ─── -->
        <div class="bg-white rounded-3xl shadow-sm border border-gray-100 p-7">
          <div class="flex items-center justify-between mb-6">
            <div class="flex items-center gap-3">
              <div class="w-11 h-11 bg-blue-100 rounded-2xl flex items-center justify-center">
                <Receipt class="w-5 h-5 text-blue-700" />
              </div>
              <div>
                <h3 class="font-extrabold text-gray-900">영수증 장부</h3>
                <p class="text-xs text-gray-400">AI 자동 지출 분류</p>
              </div>
            </div>
            <button class="text-xs text-blue-600 font-semibold hover:underline">전체보기 →</button>
          </div>

          <!-- 드래그앤드롭 업로드 -->
          <label
            class="block border-2 border-dashed rounded-2xl p-8 text-center mb-7 cursor-pointer transition-all duration-200"
            :class="isDragOver ? 'border-blue-500 bg-blue-50' : 'border-blue-200 bg-blue-50/30 hover:bg-blue-50 hover:border-blue-400'"
            @dragover="onDragOver"
            @dragleave="onDragLeave"
            @drop="onDrop"
          >
            <input type="file" accept="image/*,.pdf" class="hidden" @change="onFileChange" />

            <div v-if="!uploadedFile" class="flex flex-col items-center gap-3">
              <div class="w-14 h-14 bg-blue-100 rounded-2xl flex items-center justify-center">
                <UploadCloud class="w-7 h-7 text-blue-500" />
              </div>
              <div>
                <p class="font-bold text-gray-700">영수증을 여기에 놓으세요</p>
                <p class="text-sm text-gray-400 mt-0.5">또는 <span class="text-blue-600">파일 선택</span></p>
              </div>
              <div class="flex gap-2">
                <span class="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded font-medium">JPG</span>
                <span class="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded font-medium">PNG</span>
                <span class="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded font-medium">PDF</span>
              </div>
            </div>

            <div v-else class="flex flex-col items-center gap-3" @click.prevent="">
              <div class="w-14 h-14 bg-emerald-100 rounded-2xl flex items-center justify-center">
                <svg class="w-7 h-7 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
              </div>
              <p class="font-bold text-emerald-700">{{ uploadedFile }} 업로드됨</p>
              <p class="text-sm text-gray-400">OCR 분석 중... (API 연결 필요)</p>
              <button @click.stop.prevent="resetUpload" class="text-xs text-red-500 underline">취소</button>
            </div>
          </label>

          <!-- 주간 지출 바 차트 -->
          <div>
            <div class="flex items-center justify-between mb-3">
              <span class="text-sm font-bold text-gray-800">주간 지출</span>
              <!-- TODO: 날짜 범위 동적으로 표시 -->
              <span class="text-xs text-gray-400 font-medium">이번 주</span>
            </div>

            <!-- 데이터 없음 -->
            <div v-if="weeklyExpenses.length === 0" class="flex items-end gap-2" style="height: 96px;">
              <div v-for="day in ['월','화','수','목','금','토','일']" :key="day" class="flex-1 flex flex-col items-center gap-1.5">
                <div class="w-full bg-gray-100 rounded-t-md animate-pulse" style="height: 60%;"></div>
                <span class="text-xs text-gray-300">{{ day }}</span>
              </div>
            </div>

            <!-- 데이터 있을 때 -->
            <div v-else class="flex items-end gap-2" style="height: 96px;">
              <div v-for="(item, i) in weeklyExpenses" :key="i" class="flex-1 flex flex-col items-center gap-1.5">
                <div
                  class="w-full bg-blue-500 rounded-t-md transition-all duration-500"
                  :style="`height: ${(item.amount / maxAmount(weeklyExpenses)) * 100}%`"
                ></div>
                <span class="text-xs text-gray-400">{{ item.day }}</span>
              </div>
            </div>

            <!-- 통계 카드 -->
            <div class="mt-5 grid grid-cols-3 gap-3">
              <div class="bg-blue-50 rounded-2xl p-3.5">
                <p class="text-xs text-gray-400 mb-0.5">이번 주</p>
                <p class="font-extrabold text-gray-900 text-sm">{{ expenseStats?.thisWeek ? `₩${expenseStats.thisWeek.toLocaleString()}` : '--' }}</p>
              </div>
              <div class="bg-emerald-50 rounded-2xl p-3.5">
                <p class="text-xs text-gray-400 mb-0.5">전주 대비</p>
                <p class="font-extrabold text-sm" :class="expenseStats?.diff < 0 ? 'text-emerald-600' : 'text-red-500'">
                  {{ expenseStats?.diff != null ? (expenseStats.diff < 0 ? `−₩${Math.abs(expenseStats.diff).toLocaleString()}` : `+₩${expenseStats.diff.toLocaleString()}`) : '--' }}
                </p>
              </div>
              <div class="bg-purple-50 rounded-2xl p-3.5">
                <p class="text-xs text-gray-400 mb-0.5">스캔 영수증</p>
                <p class="font-extrabold text-gray-900 text-sm">{{ expenseStats?.receiptCount != null ? `${expenseStats.receiptCount}장` : '--' }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- ─── 지점 찾기 / 지도 (우) ─── -->
        <div class="bg-white rounded-3xl shadow-sm border border-gray-100 p-7">
          <div class="flex items-center justify-between mb-5">
            <div class="flex items-center gap-3">
              <div class="w-11 h-11 bg-emerald-100 rounded-2xl flex items-center justify-center">
                <MapPin class="w-5 h-5 text-emerald-700" />
              </div>
              <div>
                <h3 class="font-extrabold text-gray-900">인근 안전 지점 찾기</h3>
                <p class="text-xs text-gray-400">현재 위치 기반</p>
              </div>
            </div>
            <button class="flex items-center gap-1 text-xs text-blue-600 font-semibold hover:underline">
              <Crosshair class="w-3 h-3" />내 위치
            </button>
          </div>

          <!-- 지도 플레이스홀더 -->
          <!-- TODO: 카카오맵 API 또는 네이버지도 API 연동 -->
          <div class="relative rounded-2xl overflow-hidden mb-5 bg-slate-100" style="height: 200px;">
            <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" class="absolute inset-0">
              <defs>
                <pattern id="mapgrid" width="32" height="32" patternUnits="userSpaceOnUse">
                  <path d="M32 0 L0 0 0 32" fill="none" stroke="rgba(148,163,184,0.2)" stroke-width="0.6"/>
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="#e2e8f0"/>
              <rect width="100%" height="100%" fill="url(#mapgrid)"/>
              <!-- 도로 -->
              <line x1="0"   y1="105" x2="100%" y2="105" stroke="white" stroke-width="10" opacity="0.9"/>
              <line x1="0"   y1="148" x2="100%" y2="145" stroke="white" stroke-width="6"  opacity="0.8"/>
              <line x1="155" y1="0"   x2="155" y2="100%" stroke="white" stroke-width="10" opacity="0.9"/>
              <line x1="310" y1="0"   x2="308" y2="100%" stroke="white" stroke-width="6"  opacity="0.7"/>
              <!-- 블록 -->
              <rect x="18"  y="18"  width="65" height="44" fill="rgba(148,163,184,0.3)" rx="3"/>
              <rect x="172" y="18"  width="85" height="52" fill="rgba(148,163,184,0.25)" rx="3"/>
              <rect x="325" y="16"  width="75" height="38" fill="rgba(148,163,184,0.2)"  rx="3"/>
              <rect x="18"  y="115" width="80" height="55" fill="rgba(148,163,184,0.25)" rx="3"/>
              <rect x="172" y="115" width="65" height="48" fill="rgba(148,163,184,0.3)"  rx="3"/>
            </svg>

            <!-- 현재 위치 -->
            <div class="absolute" style="top: 86px; left: 170px;">
              <div class="relative flex items-center justify-center w-5 h-5">
                <div class="loc-ping absolute w-5 h-5 rounded-full bg-blue-400/40"></div>
                <div class="w-4 h-4 rounded-full bg-white border-4 border-blue-600 shadow-md"></div>
              </div>
            </div>

            <!-- 지도 안내 텍스트 -->
            <div class="absolute inset-0 flex items-center justify-center">
              <div class="bg-white/80 backdrop-blur-sm rounded-xl px-4 py-2 text-center">
                <p class="text-xs font-bold text-gray-600">지도 API 연결 필요</p>
                <p class="text-xs text-gray-400">카카오맵 / 네이버지도</p>
              </div>
            </div>

            <div class="absolute bottom-2 right-3 text-xs text-slate-400">© SafeFinance</div>
          </div>

          <!-- 지점 목록 -->
          <div v-if="nearbyBranches.length === 0" class="space-y-2.5">
            <div v-for="i in 3" :key="i" class="flex items-center gap-3 p-3 rounded-2xl border border-gray-100">
              <div class="w-10 h-10 bg-gray-200 rounded-xl animate-pulse flex-shrink-0"></div>
              <div class="flex-1 space-y-1.5">
                <div class="w-40 h-4 bg-gray-200 rounded animate-pulse"></div>
                <div class="w-56 h-3 bg-gray-200 rounded animate-pulse"></div>
              </div>
              <div class="text-right space-y-1">
                <div class="w-10 h-4 bg-gray-200 rounded animate-pulse"></div>
                <div class="w-10 h-3 bg-gray-200 rounded animate-pulse"></div>
              </div>
            </div>
            <p class="text-center text-sm text-gray-400 pt-2">위치 정보 연동 후 지점이 표시됩니다</p>
          </div>

          <div v-else class="space-y-2.5">
            <div
              v-for="branch in nearbyBranches"
              :key="branch.branchName"
              class="flex items-center gap-3 p-3 rounded-2xl hover:bg-slate-50 transition-colors cursor-pointer border border-gray-100"
            >
              <div class="w-10 h-10 bg-blue-700 rounded-xl flex items-center justify-center text-white text-xs font-black flex-shrink-0">
                {{ branch.bankCode }}
              </div>
              <div class="flex-1 min-w-0">
                <p class="font-bold text-gray-900 text-sm">{{ branch.bankName }} {{ branch.branchName }}점</p>
                <p class="text-xs text-gray-400 truncate">{{ branch.address }}</p>
              </div>
              <div class="text-right flex-shrink-0">
                <p class="text-xs font-extrabold text-blue-600">{{ branch.distance }}</p>
                <p class="flex items-center gap-0.5 text-xs font-medium justify-end" :class="branch.isOpen ? 'text-emerald-600' : 'text-red-400'">
                  <Clock class="w-2.5 h-2.5" />{{ branch.isOpen ? '영업중' : '마감' }}
                </p>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </section>
</template>
