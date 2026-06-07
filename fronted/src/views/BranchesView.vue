<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import NavBar from '@/components/NavBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import { MapPin, Crosshair, Search, Loader } from '@lucide/vue'

const NCP_CLIENT_ID = import.meta.env.VITE_NCP_MAP_CLIENT_ID

// ── 상태 ──────────────────────────────────────────────────
const mapEl          = ref(null)
const currentAddress = ref('')
const userPos        = ref(null)   // { lat, lng }
const branches       = ref([])
const searchQuery    = ref('은행')
const loadingLoc     = ref(false)
const loadingSearch  = ref(false)
const errorMsg       = ref('')

let naverMap   = null
let userMarker = null
const branchMarkers = []

// ── 네이버 지도 SDK 동적 로드 ──────────────────────────────
function loadNaverMapScript() {
  return new Promise((resolve, reject) => {
    if (window.naver?.maps) { resolve(); return }
    const script = document.createElement('script')
    script.src = `https://oapi.map.naver.com/openapi/v3/maps.js?ncpKeyId=${NCP_CLIENT_ID}`
    script.onload  = resolve
    script.onerror = reject
    document.head.appendChild(script)
  })
}

// ── 지도 초기화 ───────────────────────────────────────────
function initMap(lat, lng) {
  const center = new window.naver.maps.LatLng(lat, lng)
  naverMap = new window.naver.maps.Map(mapEl.value, {
    center,
    zoom: 15,
    zoomControl: true,
    zoomControlOptions: { position: window.naver.maps.Position.TOP_RIGHT },
  })
  setUserMarker(lat, lng)
}

function setUserMarker(lat, lng) {
  if (userMarker) userMarker.setMap(null)
  userMarker = new window.naver.maps.Marker({
    position: new window.naver.maps.LatLng(lat, lng),
    map: naverMap,
    icon: {
      content: `<div style="width:16px;height:16px;border-radius:50%;background:#2563eb;border:3px solid white;box-shadow:0 0 0 3px rgba(37,99,235,0.3)"></div>`,
      anchor: new window.naver.maps.Point(8, 8),
    },
  })
  naverMap.setCenter(new window.naver.maps.LatLng(lat, lng))
}

// ── 현재 위치 가져오기 ─────────────────────────────────────
async function locateMe() {
  loadingLoc.value = true
  errorMsg.value   = ''
  try {
    const pos = await new Promise((resolve, reject) =>
      navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 8000 })
    )
    const lat = pos.coords.latitude
    const lng = pos.coords.longitude
    userPos.value = { lat, lng }

    if (!naverMap) initMap(lat, lng)
    else setUserMarker(lat, lng)

    await fetchReverseGeocode(lng, lat)
    await searchNearby()
  } catch (e) {
    errorMsg.value = '위치 정보를 가져올 수 없습니다. 브라우저 위치 권한을 확인해 주세요.'
  } finally {
    loadingLoc.value = false
  }
}

// ── Reverse Geocoding (주소 표시) ─────────────────────────
async function fetchReverseGeocode(lng, lat) {
  try {
    const res  = await fetch(`/api/branches/reverse-geocode/?coords=${lng},${lat}`)
    const json = await res.json()
    const results = json.results ?? []
    if (results.length) {
      const r    = results[0]
      const area = r.region
      currentAddress.value = [
        area?.area1?.name,
        area?.area2?.name,
        area?.area3?.name,
        r.land?.name,
        r.land?.number1,
      ].filter(Boolean).join(' ')
    }
  } catch (_) {}
}

// ── 주변 지점 검색 ─────────────────────────────────────────
async function searchNearby() {
  if (!userPos.value) return
  loadingSearch.value = true
  errorMsg.value      = ''
  clearBranchMarkers()
  try {
    // 현재 위치 행정구역(시/구/동)을 앞에 붙여 근거리 결과 유도
    const areaHint = currentAddress.value.split(' ').slice(0, 3).join(' ')
    const query    = areaHint ? `${areaHint} ${searchQuery.value}` : searchQuery.value
    const res  = await fetch(`/api/branches/search/?query=${encodeURIComponent(query)}&display=10`)
    const json = await res.json()
    const items = json.items ?? []

    branches.value = items.map(item => {
      // Naver 검색 API 좌표는 카텍 좌표계(KATECH) — 변환 없이 mapx/mapy 사용 (단위: 1e-7 degree)
      const lat = item.mapy / 1e7
      const lng = item.mapx / 1e7
      const dist = calcDistance(userPos.value.lat, userPos.value.lng, lat, lng)
      return {
        title:    item.title.replace(/<[^>]+>/g, ''),
        address:  item.roadAddress || item.address,
        category: item.category,
        lat, lng, dist,
      }
    }).sort((a, b) => a.dist - b.dist)

    branches.value.forEach((b, i) => addBranchMarker(b, i))
  } catch (e) {
    errorMsg.value = '지점 검색에 실패했습니다.'
  } finally {
    loadingSearch.value = false
  }
}

// ── 마커 관리 ─────────────────────────────────────────────
function addBranchMarker(branch, index) {
  if (!naverMap) return
  const marker = new window.naver.maps.Marker({
    position: new window.naver.maps.LatLng(branch.lat, branch.lng),
    map: naverMap,
    icon: {
      content: `<div style="background:#1d4ed8;color:white;font-size:11px;font-weight:bold;padding:3px 7px;border-radius:12px;white-space:nowrap;box-shadow:0 2px 6px rgba(0,0,0,0.25)">${index + 1}</div>`,
      anchor: new window.naver.maps.Point(14, 12),
    },
  })
  const infoWindow = new window.naver.maps.InfoWindow({
    content: `<div style="padding:8px 12px;font-size:12px;min-width:140px"><b>${branch.title}</b><br><span style="color:#6b7280">${branch.address}</span></div>`,
    borderWidth: 0,
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 10px rgba(0,0,0,0.15)',
  })
  window.naver.maps.Event.addListener(marker, 'click', () => {
    if (infoWindow.getMap()) infoWindow.close()
    else infoWindow.open(naverMap, marker)
  })
  branchMarkers.push(marker)
}

function clearBranchMarkers() {
  branchMarkers.forEach(m => m.setMap(null))
  branchMarkers.length = 0
}

function focusBranch(branch) {
  naverMap?.setCenter(new window.naver.maps.LatLng(branch.lat, branch.lng))
  naverMap?.setZoom(17)
}

// ── 거리 계산 (Haversine) ─────────────────────────────────
function calcDistance(lat1, lng1, lat2, lng2) {
  const R  = 6371000
  const dL = (lat2 - lat1) * Math.PI / 180
  const dG = (lng2 - lng1) * Math.PI / 180
  const a  = Math.sin(dL / 2) ** 2 + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dG / 2) ** 2
  return Math.round(R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)))
}

function formatDist(m) {
  return m >= 1000 ? `${(m / 1000).toFixed(1)}km` : `${m}m`
}

onMounted(async () => {
  await loadNaverMapScript()
  // 키 없이도 지도 틀 자체는 표시
  if (NCP_CLIENT_ID) {
    naverMap = new window.naver.maps.Map(mapEl.value, {
      center: new window.naver.maps.LatLng(37.5665, 126.9780),
      zoom: 13,
    })
  }
})

onUnmounted(() => {
  clearBranchMarkers()
  if (userMarker) userMarker.setMap(null)
})
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <NavBar />
    <main class="pt-24 pb-16 max-w-3xl mx-auto px-4 sm:px-6">

      <!-- 헤더 -->
      <div class="mb-6 flex items-center justify-between">
        <div>
          <div class="inline-flex items-center gap-2 bg-emerald-50 text-emerald-700 text-xs font-bold px-3 py-1.5 rounded-full mb-3 border border-emerald-100">
            <MapPin class="w-3 h-3" />위치 기반
          </div>
          <h1 class="text-3xl font-extrabold text-gray-900 mb-1">지점 찾기</h1>
          <p class="text-gray-400 text-sm">
            {{ currentAddress || '인근 금융기관을 검색합니다' }}
          </p>
        </div>
        <button
          @click="locateMe"
          :disabled="loadingLoc"
          class="flex items-center gap-1.5 px-4 py-2 bg-white border border-gray-200 rounded-xl text-sm font-semibold text-blue-600 hover:border-blue-300 transition-colors shadow-sm disabled:opacity-50"
        >
          <Loader v-if="loadingLoc" class="w-4 h-4 animate-spin" />
          <Crosshair v-else class="w-4 h-4" />
          내 위치
        </button>
      </div>

      <!-- 에러 -->
      <div v-if="errorMsg" class="mb-4 bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-600 font-medium">
        {{ errorMsg }}
      </div>

      <!-- 지도 -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden mb-4">
        <div ref="mapEl" style="height: 320px; width: 100%;" />
      </div>

      <!-- 검색 바 -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 mb-4">
        <div class="flex gap-2">
          <input
            v-model="searchQuery"
            @keyup.enter="searchNearby"
            type="text"
            placeholder="예: 국민은행, 우리은행, ATM"
            class="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-300"
          />
          <button
            @click="searchNearby"
            :disabled="loadingSearch || !userPos"
            class="flex items-center gap-1.5 px-4 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-bold hover:bg-emerald-700 transition-colors disabled:opacity-40"
          >
            <Loader v-if="loadingSearch" class="w-4 h-4 animate-spin" />
            <Search v-else class="w-4 h-4" />
            검색
          </button>
        </div>
        <p v-if="!userPos" class="text-xs text-gray-400 mt-2 text-center">
          먼저 '내 위치' 버튼을 눌러 현재 위치를 설정해 주세요
        </p>
      </div>

      <!-- 지점 목록 -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
        <p class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">
          인근 지점
          <span v-if="branches.length" class="ml-1 text-emerald-600">{{ branches.length }}개</span>
        </p>

        <!-- 스켈레톤 -->
        <div v-if="loadingSearch" class="space-y-3">
          <div v-for="i in 4" :key="i" class="flex items-center gap-3 p-3 rounded-xl border border-gray-100 animate-pulse">
            <div class="w-10 h-10 bg-gray-200 rounded-xl flex-shrink-0" />
            <div class="flex-1 space-y-1.5">
              <div class="w-40 h-4 bg-gray-200 rounded" />
              <div class="w-56 h-3 bg-gray-200 rounded" />
            </div>
            <div class="w-10 h-4 bg-gray-200 rounded" />
          </div>
        </div>

        <!-- 빈 상태 -->
        <div v-else-if="branches.length === 0" class="text-center py-8 text-sm text-gray-400">
          {{ userPos ? '검색 결과가 없습니다.' : '위치를 설정하면 인근 지점이 표시됩니다.' }}
        </div>

        <!-- 지점 리스트 -->
        <div v-else class="space-y-2">
          <div
            v-for="(branch, i) in branches"
            :key="i"
            @click="focusBranch(branch)"
            class="flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 transition-colors cursor-pointer border border-gray-100"
          >
            <div class="w-10 h-10 bg-blue-700 rounded-xl flex items-center justify-center text-white text-xs font-black flex-shrink-0">
              {{ i + 1 }}
            </div>
            <div class="flex-1 min-w-0">
              <p class="font-bold text-gray-900 text-sm truncate">{{ branch.title }}</p>
              <p class="text-xs text-gray-400 truncate">{{ branch.address }}</p>
            </div>
            <div class="text-right flex-shrink-0">
              <p class="text-xs font-extrabold text-blue-600">{{ formatDist(branch.dist) }}</p>
            </div>
          </div>
        </div>
      </div>

    </main>
    <AppFooter />
  </div>
</template>
