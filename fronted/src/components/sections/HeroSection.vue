<script setup>
import { ref } from "vue";
import {
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  PhoneOff,
  TrendingUp,
  Zap,
} from "@lucide/vue";

// TODO: API 연결 - 기기 보안 점수 조회
const securityScore = ref(null); // null이면 '--' 표시

// TODO: API 연결 - 보안 체크 항목 조회
const securityChecks = ref([]);
/*  예상 구조:
    [
      { label: '전화 스푸핑 차단', status: 'active' | 'warning' | 'inactive' },
      ...
    ]
*/

// TODO: API 연결 - 실시간 피싱 알림 목록
const alertMessages = ref(["실시간 보이스피싱 알림을 불러오는 중..."]);

// 게이지 dash offset 계산 (반지름 72, 원주 ≒ 452.4)
const CIRCUMFERENCE = 452.4;
const dashOffset = (score) => {
  if (!score) return CIRCUMFERENCE;
  return CIRCUMFERENCE - (CIRCUMFERENCE * score) / 100;
};
</script>

<template>
  <section
    class="pt-16"
    style="
      background: linear-gradient(
        135deg,
        #0f1f47 0%,
        #1e3a8a 45%,
        #1d4ed8 85%,
        #2563eb 100%
      );
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    "
  >
    <!-- 실시간 피싱 알림 티커 -->
    <div
      class="overflow-hidden border-b py-2.5"
      style="
        background: rgba(0, 0, 0, 0.2);
        border-color: rgba(255, 255, 255, 0.1);
      "
    >
      <div class="flex items-center gap-3 px-4">
        <span
          class="flex-shrink-0 text-xs font-black text-yellow-300 uppercase tracking-widest flex items-center gap-1"
        >
          ⚠ LIVE
        </span>
        <div class="overflow-hidden flex-1">
          <p
            class="ticker-text whitespace-nowrap text-sm"
            style="color: rgba(253, 224, 71, 0.9)"
          >
            <span v-for="(msg, i) in alertMessages" :key="i">
              {{ msg }} &ensp;·&ensp;
            </span>
          </p>
        </div>
      </div>
    </div>

    <!-- 히어로 본문 -->
    <div class="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 py-16 lg:py-24">
      <div class="grid lg:grid-cols-2 gap-14 items-center">
        <!-- 좌: 카피 -->
        <div class="text-white">
          <div
            class="inline-flex items-center gap-2 text-xs font-bold px-3 py-1.5 rounded-full mb-7 uppercase tracking-widest border"
            style="
              background: rgba(29, 78, 216, 0.4);
              color: #93c5fd;
              border-color: rgba(59, 130, 246, 0.4);
            "
          >
            <Zap class="w-3 h-3" />AI 금융보안 플랫폼
          </div>
          <h1
            class="text-5xl lg:text-6xl font-black leading-tight mb-6 tracking-tight"
          >
            내 자산을<br />
            <span style="color: #93c5fd">보이스피싱</span>으로부터<br />
            안전하게
          </h1>
          <p
            class="text-lg mb-9 max-w-md leading-relaxed"
            style="color: rgba(219, 234, 254, 0.8)"
          >
            실시간 AI 탐지로 금융사기를 차단합니다. 최적의 금융상품 비교, 안전한
            지점 찾기, 48,000명의 투자자 커뮤니티에 참여하세요.
          </p>
          <div class="flex flex-wrap gap-3 mb-12">
            <button
              class="flex items-center gap-2 px-6 py-3.5 bg-white font-bold rounded-xl text-sm shadow-lg hover:bg-blue-50 transition-all"
              style="color: #1e3a8a"
            >
              <ShieldCheck class="w-4 h-4" />보안 점수 확인
            </button>
            <button
              class="flex items-center gap-2 px-6 py-3.5 font-semibold rounded-xl border text-sm transition-all"
              style="
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border-color: rgba(255, 255, 255, 0.2);
              "
            >
              서비스 소개 보기
            </button>
          </div>

          <!-- 통계 (API 연결 전 -- 표시) -->
          <!-- TODO: API 연결 - 플랫폼 통계 조회 -->
          <div
            class="grid grid-cols-3 rounded-2xl overflow-hidden border"
            style="
              background: rgba(255, 255, 255, 0.05);
              border-color: rgba(255, 255, 255, 0.12);
            "
          >
            <div class="p-5">
              <p class="text-2xl font-extrabold">--</p>
              <p class="text-xs mt-0.5 font-medium" style="color: #93c5fd">
                보호된 사용자
              </p>
            </div>
            <div
              class="p-5 border-x"
              style="border-color: rgba(255, 255, 255, 0.1)"
            >
              <p class="text-2xl font-extrabold">--</p>
              <p class="text-xs mt-0.5 font-medium" style="color: #93c5fd">
                피해 예방액
              </p>
            </div>
            <div class="p-5">
              <p class="text-2xl font-extrabold">--</p>
              <p class="text-xs mt-0.5 font-medium" style="color: #93c5fd">
                탐지 정확도
              </p>
            </div>
          </div>
        </div>

        <!-- 우: 보안 점수 대시보드 카드 -->
        <div class="flex justify-center lg:justify-end">
          <div class="relative w-full max-w-md">
            <!-- 메인 카드 -->
            <div
              class="rounded-2xl p-6 shadow-2xl"
              style="
                background: rgba(255, 255, 255, 0.09);
                backdrop-filter: blur(16px);
                border: 1px solid rgba(255, 255, 255, 0.18);
              "
            >
              <div class="flex items-center justify-between mb-5">
                <h3 class="text-white font-bold">기기 보안 점수</h3>
                <span
                  class="text-xs font-bold px-2.5 py-1 rounded-full"
                  :style="
                    securityScore
                      ? 'background:rgba(16,185,129,0.2);color:#6ee7b7;border:1px solid rgba(52,211,153,0.3)'
                      : 'background:rgba(148,163,184,0.2);color:#94a3b8;border:1px solid rgba(148,163,184,0.3)'
                  "
                >
                  {{ securityScore ? "● 안전" : "● 확인중" }}
                </span>
              </div>

              <!-- SVG 원형 게이지 -->
              <div class="flex justify-center mb-5">
                <div class="relative">
                  <svg
                    width="176"
                    height="176"
                    viewBox="0 0 176 176"
                    style="transform: rotate(-90deg)"
                  >
                    <circle
                      cx="88"
                      cy="88"
                      r="72"
                      fill="none"
                      stroke="rgba(255,255,255,0.08)"
                      stroke-width="11"
                    />
                    <circle
                      cx="88"
                      cy="88"
                      r="72"
                      fill="none"
                      stroke="url(#gauge-grad)"
                      stroke-width="11"
                      stroke-linecap="round"
                      :stroke-dasharray="CIRCUMFERENCE"
                      :stroke-dashoffset="dashOffset(securityScore)"
                      style="transition: stroke-dashoffset 1s ease"
                    />
                    <defs>
                      <linearGradient
                        id="gauge-grad"
                        x1="0%"
                        y1="0%"
                        x2="100%"
                        y2="0%"
                      >
                        <stop offset="0%" stop-color="#10b981" />
                        <stop offset="100%" stop-color="#34d399" />
                      </linearGradient>
                    </defs>
                  </svg>
                  <div
                    class="absolute inset-0 flex flex-col items-center justify-center"
                  >
                    <span class="text-5xl font-black text-white leading-none">{{
                      securityScore ?? "--"
                    }}</span>
                    <span
                      class="text-sm font-semibold mt-0.5"
                      style="color: #6ee7b7"
                      >/ 100</span
                    >
                    <ShieldCheck
                      class="w-5 h-5 mt-1.5"
                      style="color: #34d399"
                    />
                  </div>
                </div>
              </div>

              <!-- 보안 체크 목록 -->
              <!-- TODO: API 연결 후 securityChecks 배열로 렌더링 -->
              <div v-if="securityChecks.length === 0" class="space-y-3">
                <div
                  v-for="i in 4"
                  :key="i"
                  class="flex items-center justify-between"
                >
                  <div
                    class="flex items-center gap-2"
                    style="color: rgba(219, 234, 254, 0.5)"
                  >
                    <AlertCircle class="w-4 h-4" />
                    <span class="text-sm">항목 로딩 중...</span>
                  </div>
                  <span
                    class="text-xs font-semibold"
                    style="color: rgba(148, 163, 184, 0.6)"
                    >대기</span
                  >
                </div>
              </div>
              <div v-else class="space-y-3">
                <div
                  v-for="check in securityChecks"
                  :key="check.label"
                  class="flex items-center justify-between text-sm"
                >
                  <span class="flex items-center gap-2" style="color: #dbeafe">
                    <CheckCircle2
                      v-if="check.status === 'active'"
                      class="w-4 h-4"
                      style="color: #34d399"
                    />
                    <AlertCircle
                      v-else
                      class="w-4 h-4"
                      style="color: #fbbf24"
                    />
                    {{ check.label }}
                  </span>
                  <span
                    :style="
                      check.status === 'active'
                        ? 'color: #34d399;'
                        : 'color: #fbbf24;'
                    "
                    class="text-xs font-semibold"
                  >
                    {{ check.status === "active" ? "활성" : "검토" }}
                  </span>
                </div>
              </div>
            </div>

            <!-- 플로팅 미니 카드 (차단 현황) -->
            <!-- TODO: API 연결 - 오늘 차단 건수 조회 -->
            <div
              class="absolute -top-5 -right-5 bg-white rounded-2xl shadow-xl px-3.5 py-2.5 flex items-center gap-2.5"
            >
              <div
                class="w-8 h-8 bg-red-100 rounded-xl flex items-center justify-center"
              >
                <PhoneOff class="w-4 h-4 text-red-500" />
              </div>
              <div>
                <p class="text-xs font-extrabold text-gray-900">-- 건 차단</p>
                <p class="text-xs text-gray-400">오늘</p>
              </div>
            </div>

            <!-- 플로팅 미니 카드 (보안 레벨) -->
            <!-- TODO: API 연결 - 보안 레벨 변화 조회 -->
            <div
              class="absolute -bottom-5 -left-5 bg-white rounded-2xl shadow-xl px-3.5 py-2.5 flex items-center gap-2.5"
            >
              <div
                class="w-8 h-8 bg-emerald-100 rounded-xl flex items-center justify-center"
              >
                <TrendingUp class="w-4 h-4 text-emerald-600" />
              </div>
              <div>
                <p class="text-xs font-extrabold text-gray-900">-- 오늘</p>
                <p class="text-xs text-gray-400">보안 레벨</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 웨이브 구분선 -->
    <svg
      viewBox="0 0 1440 72"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      class="w-full block"
    >
      <path
        d="M0,36 C360,72 720,0 1080,36 C1260,54 1380,24 1440,36 L1440,72 L0,72 Z"
        fill="white"
      />
    </svg>
  </section>
</template>
