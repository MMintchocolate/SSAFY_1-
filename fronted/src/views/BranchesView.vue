<script setup>
// @ts-nocheck
import { ref, onMounted, onUnmounted } from 'vue'
import NavBar from '@/components/NavBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import { MapPin, Crosshair, Search, Loader2, Building2, Navigation, Phone, Route } from '@lucide/vue'

const KAKAO_JS_KEY = import.meta.env.VITE_KAKAO_MAP_JS_KEY

// ── 검색 모드 ─────────────────────────────────────────────────────────────
const mode = ref('region')

// ── 공용 상태 ──────────────────────────────────────────────────────────────
const mapEl     = ref(null)
const branches  = ref([])
const errorMsg  = ref('')
const searching = ref(false)

// ── 기능 1: 지역명 검색 ────────────────────────────────────────────────────
const regionInput = ref('')
const bankInput   = ref('은행')

// ── 기능 2: 내 위치 ────────────────────────────────────────────────────────
const locating    = ref(false)
const currentArea = ref('')
const userPos     = ref(null)
const nearbyKw    = ref('은행')

// ── 카카오맵 인스턴스 ───────────────────────────────────────────────────────
let kakaoMap         = null
let userOverlay      = null
const branchMarkers  = []
const infoWindows    = []

// ══════════════════════════════════════════════════════════════════════════
// 카카오맵 SDK 초기화
// ══════════════════════════════════════════════════════════════════════════

function loadKakaoMapScript() {
  return new Promise((resolve, reject) => {
    if (window.kakao?.maps) { window.kakao.maps.load(resolve); return }
    const s = document.createElement('script')
    s.src = `//dapi.kakao.com/v2/maps/sdk.js?appkey=${KAKAO_JS_KEY}&autoload=false`
    s.onload  = () => window.kakao.maps.load(resolve)
    s.onerror = reject
    document.head.appendChild(s)
  })
}

function initMap(lat = 37.5665, lng = 126.9780, level = 7) {
  const center = new window.kakao.maps.LatLng(lat, lng)
  if (!kakaoMap) {
    kakaoMap = new window.kakao.maps.Map(mapEl.value, { center, level })
  } else {
    kakaoMap.setCenter(center)
    kakaoMap.setLevel(level)
  }
}

// ══════════════════════════════════════════════════════════════════════════
// 마커 관리
// ══════════════════════════════════════════════════════════════════════════

function setUserOverlay(lat, lng) {
  if (userOverlay) userOverlay.setMap(null)
  const dot = '<div style="width:18px;height:18px;border-radius:50%;margin:-9px 0 0 -9px;background:#2563eb;border:3px solid white;box-shadow:0 0 0 5px rgba(37,99,235,0.25)"></div>'
  userOverlay = new window.kakao.maps.CustomOverlay({
    position: new window.kakao.maps.LatLng(lat, lng),
    content: dot,
    map: kakaoMap,
    zIndex: 10,
  })
}

function addBranchMarker(branch, index) {
  if (!kakaoMap) return

  const pos    = new window.kakao.maps.LatLng(branch.lat, branch.lng)
  const color  = mode.value === 'region' ? '#1d4ed8' : '#059669'

  const labelOverlay = new window.kakao.maps.CustomOverlay({
    position: pos,
    content: `<div style="
      background:${color};color:white;font-size:11px;font-weight:700;
      padding:3px 8px;border-radius:12px;white-space:nowrap;cursor:pointer;
      box-shadow:0 2px 6px rgba(0,0,0,0.25)">${index + 1}</div>`,
    map: kakaoMap,
    zIndex: 5,
  })

  const phoneRow = branch.phone
    ? `<div style="color:#6b7280;font-size:11px;margin-top:3px">${branch.phone}</div>` : ''
  const distRow  = branch.distance
    ? `<div style="color:#9ca3af;font-size:10px;margin-top:2px">${Number(branch.distance).toLocaleString()}m</div>` : ''

  const infoWindow = new window.kakao.maps.InfoWindow({
    content: `
      <div style="padding:10px 14px;font-size:12px;min-width:160px;max-width:220px;
                  font-family:sans-serif;line-height:1.5;">
        <b style="color:#1e3a8a">${branch.title}</b>
        <div style="color:#6b7280;margin-top:3px;font-size:11px">${branch.address}</div>
        ${phoneRow}${distRow}
      </div>`,
    removable: true,
  })

  // 라벨 클릭 → 인포윈도우 토글 (CustomOverlay는 일반 DOM이므로 직접 이벤트)
  const node = labelOverlay.getContent?.()
  if (node) {
    const el = typeof node === 'string'
      ? (() => { const d = document.createElement('div'); d.innerHTML = node; return d.firstChild })()
      : node
    if (el?.addEventListener) {
      el.addEventListener('click', () => {
        infoWindows.forEach(iw => iw !== infoWindow && iw.close())
        if (infoWindow.getMap()) infoWindow.close()
        else {
          // InfoWindow는 Marker 기준이므로 임시 마커 없이 position으로 open
          infoWindow.open(kakaoMap, { getPosition: () => pos })
        }
      })
    }
  }

  branchMarkers.push(labelOverlay)
  infoWindows.push(infoWindow)
}

function clearBranchMarkers() {
  branchMarkers.forEach(m => m.setMap(null))
  branchMarkers.length = 0
  infoWindows.forEach(iw => iw.close())
  infoWindows.length = 0
}

function renderBranches(list) {
  clearBranchMarkers()
  branches.value = list
  list.forEach((b, i) => addBranchMarker(b, i))
  if (list.length) {
    kakaoMap.setCenter(new window.kakao.maps.LatLng(list[0].lat, list[0].lng))
    kakaoMap.setLevel(4)
  }
}

function focusBranch(branch) {
  kakaoMap?.setCenter(new window.kakao.maps.LatLng(branch.lat, branch.lng))
  kakaoMap?.setLevel(3)
}

// ══════════════════════════════════════════════════════════════════════════
// 기능 1: 지역명 + 은행명 검색
// ══════════════════════════════════════════════════════════════════════════

async function searchByRegion() {
  if (!regionInput.value.trim() && !bankInput.value.trim()) return
  searching.value = true
  errorMsg.value  = ''
  try {
    const params = new URLSearchParams({
      region:  regionInput.value.trim(),
      keyword: bankInput.value.trim() || '은행',
    })
    const res  = await fetch(`/api/branches/search/?${params}`)
    const json = await res.json()
    if (!res.ok) throw new Error(json.error ?? '검색 실패')
    renderBranches(json.branches ?? [])
    if (!json.branches?.length) errorMsg.value = '검색 결과가 없습니다.'
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    searching.value = false
  }
}

// ══════════════════════════════════════════════════════════════════════════
// 기능 2: 현재 위치 기반 검색
// ══════════════════════════════════════════════════════════════════════════

async function locateAndSearch() {
  locating.value  = true
  errorMsg.value  = ''
  currentArea.value = ''
  try {
    const pos = await new Promise((resolve, reject) =>
      navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 8000 })
    )
    const lat = pos.coords.latitude
    const lng = pos.coords.longitude
    userPos.value = { lat, lng }
    initMap(lat, lng, 5)
    setUserOverlay(lat, lng)
    await doLocationSearch(lat, lng)
  } catch (e) {
    errorMsg.value = e.code === 1
      ? '위치 권한이 거부되었습니다. 브라우저 설정에서 위치 권한을 허용해 주세요.'
      : '위치 정보를 가져올 수 없습니다.'
  } finally {
    locating.value = false
  }
}

async function doLocationSearch(lat, lng) {
  searching.value = true
  try {
    const params = new URLSearchParams({
      lat:     lat,
      lng:     lng,
      keyword: nearbyKw.value.trim() || '은행',
      radius:  3000,
    })
    const res  = await fetch(`/api/branches/search-by-location/?${params}`)
    const json = await res.json()
    if (!res.ok) throw new Error(json.error ?? '검색 실패')
    currentArea.value = json.area ?? ''
    renderBranches(json.branches ?? [])
    if (!json.branches?.length) errorMsg.value = '주변에 검색 결과가 없습니다.'
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    searching.value = false
  }
}

async function searchNearbyAgain() {
  if (!userPos.value) return
  errorMsg.value = ''
  await doLocationSearch(userPos.value.lat, userPos.value.lng)
}

// ══════════════════════════════════════════════════════════════════════════
// 라이프사이클
// ══════════════════════════════════════════════════════════════════════════

onMounted(async () => {
  try {
    await loadKakaoMapScript()
    initMap()
  } catch (e) {
    errorMsg.value = '카카오맵 로드에 실패했습니다. Kakao Developers 콘솔에서 https://localhost:5173 도메인이 등록되어 있는지 확인해 주세요.'
  }
})

onUnmounted(() => {
  clearBranchMarkers()
  userOverlay?.setMap(null)
})
</script>

<template>
  <div class="min-h-screen bg-white" style="font-family:'Pretendard','Noto Sans KR',sans-serif">
    <NavBar />
    <main class="pt-24 pb-16 max-w-3xl mx-auto px-4 sm:px-6">

      <!-- 헤더 -->
      <div class="mb-6">
        <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-bold mb-3" style="background:#DFFAF4;color:#0D9B7A;font-size:0.72rem">
          <MapPin class="w-3 h-3" />지점 찾기
        </div>
        <h1 class="font-black mb-1" style="font-size:1.8rem;color:#0F122B">은행 지점 검색</h1>
        <p style="color:#6F7485;font-size:0.9rem">지역명으로 검색하거나 내 위치 주변 지점을 찾아보세요</p>
      </div>

      <!-- 모드 탭 -->
      <div class="flex gap-1 p-1 rounded-xl w-fit mb-4" style="background:white;border:1px solid #EEF1F5">
        <button
          @click="mode = 'region'"
          class="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold transition-all"
          :style="mode === 'region' ? 'background:#0F122B;color:white' : 'color:#6F7485'"
        >
          <Building2 class="w-4 h-4" />지역 검색
        </button>
        <button
          @click="mode = 'location'"
          class="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold transition-all"
          :style="mode === 'location' ? 'background:#57E0C3;color:#0F122B' : 'color:#6F7485'"
        >
          <Navigation class="w-4 h-4" />내 위치
        </button>
      </div>

      <!-- 기능 1 -->
      <div v-if="mode === 'region'" class="rounded-2xl p-4 mb-4" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
        <p class="font-bold mb-3" style="font-size:0.72rem;color:#6F7485;letter-spacing:0.08em">지역 + 은행 검색</p>
        <div class="flex flex-col sm:flex-row gap-2">
          <input
            v-model="regionInput"
            @keyup.enter="searchByRegion"
            type="text"
            placeholder="지역명  예) 부산진구, 강남구"
            class="flex-1 px-4 py-2.5 rounded-xl text-sm focus:outline-none transition-all"
            style="border:1.5px solid #EEF1F5;color:#0F122B"
          />
          <input
            v-model="bankInput"
            @keyup.enter="searchByRegion"
            type="text"
            placeholder="은행명  예) 국민은행, ATM"
            class="flex-1 px-4 py-2.5 rounded-xl text-sm focus:outline-none transition-all"
            style="border:1.5px solid #EEF1F5;color:#0F122B"
          />
          <button
            @click="searchByRegion"
            :disabled="searching"
            class="flex items-center gap-1.5 px-5 py-2.5 rounded-xl text-sm font-bold transition-all disabled:opacity-50"
            style="background:#0F122B;color:white"
          >
            <Loader2 v-if="searching" class="w-4 h-4 animate-spin" />
            <Search v-else class="w-4 h-4" />검색
          </button>
        </div>
        <p class="mt-2" style="font-size:0.75rem;color:#6F7485">지역명만 입력해도 검색됩니다.</p>
      </div>

      <!-- 기능 2 -->
      <div v-else class="rounded-2xl p-4 mb-4" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
        <p class="font-bold mb-3" style="font-size:0.72rem;color:#6F7485;letter-spacing:0.08em">현재 위치 기반 검색 (반경 3km)</p>
        <div class="flex flex-col sm:flex-row gap-2">
          <input
            v-model="nearbyKw"
            @keyup.enter="searchNearbyAgain"
            type="text"
            placeholder="은행명  예) 국민은행, ATM"
            class="flex-1 px-4 py-2.5 rounded-xl text-sm focus:outline-none transition-all"
            style="border:1.5px solid #EEF1F5;color:#0F122B"
          />
          <button
            @click="userPos ? searchNearbyAgain() : locateAndSearch()"
            :disabled="locating || searching"
            class="flex items-center gap-1.5 px-5 py-2.5 rounded-xl text-sm font-bold transition-all disabled:opacity-50"
            style="background:#57E0C3;color:#0F122B"
          >
            <Loader2 v-if="locating || searching" class="w-4 h-4 animate-spin" />
            <Crosshair v-else class="w-4 h-4" />
            {{ locating ? '위치 확인 중...' : (userPos ? '재검색' : '내 위치로 검색') }}
          </button>
        </div>
        <div v-if="currentArea" class="mt-2 flex items-center gap-1.5 font-semibold" style="font-size:0.75rem;color:#0D9B7A">
          <MapPin class="w-3 h-3" />{{ currentArea }} 주변 검색 중
        </div>
        <p v-else class="mt-2" style="font-size:0.75rem;color:#6F7485">버튼을 누르면 브라우저 위치 권한을 요청합니다.</p>
      </div>

      <!-- 오류 -->
      <div v-if="errorMsg" class="mb-4 rounded-xl px-4 py-3 text-sm font-medium" style="background:#FFF5F5;border:1px solid #FFD0D0;color:#E5323B">
        {{ errorMsg }}
      </div>

      <!-- 지도 -->
      <div class="rounded-2xl overflow-hidden mb-4" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
        <div ref="mapEl" style="height: 360px; width: 100%;" />
      </div>

      <!-- 결과 목록 -->
      <div class="rounded-2xl p-5" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
        <p class="font-bold mb-4" style="font-size:0.72rem;color:#6F7485;letter-spacing:0.08em">
          검색 결과
          <span v-if="branches.length" class="ml-1 font-black" style="color:#57E0C3">{{ branches.length }}개</span>
        </p>

        <div v-if="searching" class="space-y-3">
          <div v-for="i in 5" :key="i" class="flex items-center gap-3 p-3 rounded-xl animate-pulse" style="border:1px solid #EEF1F5">
            <div class="w-10 h-10 rounded-xl flex-shrink-0" style="background:#EEF1F5" />
            <div class="flex-1 space-y-2">
              <div class="w-40 h-4 rounded" style="background:#EEF1F5" />
              <div class="w-56 h-3 rounded" style="background:#EEF1F5" />
            </div>
          </div>
        </div>

        <div v-else-if="!branches.length" class="text-center py-10 text-sm" style="color:#6F7485">
          <MapPin class="w-8 h-8 mx-auto mb-2 opacity-20" />
          검색어를 입력하고 검색 버튼을 눌러주세요.
        </div>

        <div v-else class="space-y-2">
          <div
            v-for="(branch, i) in branches"
            :key="i"
            @click="focusBranch(branch)"
            class="flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-colors hover:bg-[#F8F9FF]"
            style="border:1px solid #EEF1F5"
          >
            <div
              class="w-10 h-10 rounded-xl flex items-center justify-center font-black flex-shrink-0"
              :style="mode === 'region'
                ? 'background:#0F122B;color:white;font-size:0.75rem'
                : 'background:#57E0C3;color:#0F122B;font-size:0.75rem'"
            >{{ i + 1 }}</div>
            <div class="flex-1 min-w-0">
              <p class="font-bold text-sm truncate" style="color:#0F122B">{{ branch.title }}</p>
              <p class="text-xs truncate" style="color:#6F7485">{{ branch.address }}</p>
              <div class="flex items-center gap-2 mt-0.5">
                <span v-if="branch.phone" class="flex items-center gap-0.5" style="font-size:0.72rem;color:#6F7485">
                  <Phone class="w-3 h-3" />{{ branch.phone }}
                </span>
                <span v-if="branch.distance" class="font-semibold" style="font-size:0.72rem;color:#0D9B7A">
                  {{ Number(branch.distance).toLocaleString() }}m
                </span>
              </div>
            </div>
            <a
              :href="`https://map.kakao.com/link/to/${encodeURIComponent(branch.title)},${branch.lat},${branch.lng}`"
              target="_blank"
              rel="noopener noreferrer"
              @click.stop
              class="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold flex-shrink-0 transition-colors"
              style="background:#FFD76A;color:#0F122B"
            ><Route class="w-3 h-3" />길찾기</a>
          </div>
        </div>
      </div>

    </main>
    <AppFooter />
  </div>
</template>
