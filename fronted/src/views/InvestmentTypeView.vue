<script setup>
import { ref, computed } from 'vue'
import NavBar from '@/components/NavBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import { ChevronLeft, ChevronRight, RotateCcw, TrendingUp } from '@lucide/vue'

const QUESTIONS = [
  {
    q: '드디어 기다리던 월급날! 여유 자금 100만 원이 생겼다면 나의 행동은?',
    options: [
      '무조건 안전한 예적금이나 파킹통장에 넣어둔다.',
      '이름만 대면 다 아는 대기업 주식을 사서 묻어둔다.',
      '요즘 가장 핫하고 트렌디한 산업(AI, 우주항공 등) 유망주에 투자한다.',
      '최근 거래량이 터지면서 상승 추세를 탄 종목을 차트로 분석해 매수한다.',
    ],
  },
  {
    q: '주식 투자를 할 때 내가 가장 중요하게 생각하는 지표나 기준은?',
    options: [
      '매달 혹은 매년 꼬박꼬박 들어오는 배당금(배당수익률)',
      '기업의 매출 규모와 시장 지배력, 그리고 안전성',
      '미래 세상을 바꿀 만한 혁신 기술과 기술의 성장성',
      '기업의 재무제표 수치(PER, PBR)나 거래량 등의 데이터',
    ],
  },
  {
    q: '내가 산 주식이 다음 날 아침 -10% 폭락했다는 알림을 본다면?',
    options: [
      '가슴이 쿵쾅거리고 하루 종일 일이 손에 안 잡힌다. 당장 팔아야 하나 고민한다.',
      '"싸게 살 기회다!" 하고 오히려 기업의 펀더멘털을 재점검하며 추가 매수를 고려한다.',
      '"주식 하다 보면 이럴 때도 있지" 하고 미래 가치를 믿으며 본업에 집중한다.',
      '미리 설정해 둔 손절선(예: -5%)을 넘었다면 기계적으로 손절매하고 다음 종목을 찾는다.',
    ],
  },
  {
    q: '유튜브나 뉴스 리포트를 볼 때, 가장 내 눈길을 끄는 제목은?',
    options: [
      '"월 100만 원 따박따박 들어오는 무지성 배당금 조합법"',
      '"워런 버핏도 평생 들고 간다는 미국 시장 지수(S&P500)의 비밀"',
      '"제2의 테슬라 발견! 10년 뒤 100배 성장할 미래 혁신 섹터 총정리"',
      '"재무제표와 퀀트 알고리즘으로 찾아낸 절대 잃지 않는 저평가 종목"',
    ],
  },
  {
    q: '내가 투자한 돈을 최소한 얼마 동안 묶어둘 수 있을까?',
    options: [
      '기간과 상관없이 원금 손실 위험이 있다면 언제든 빼고 싶다.',
      '3년~5년 이상, 장기 적립식으로 꾸준히 모아갈 수 있다.',
      '6개월~2년 정도, 해당 산업이 눈에 띄는 성과를 낼 때까지 기다릴 수 있다.',
      '수일에서 수주일 내로 시세 차익이 나면 빠르게 수익 실현하고 싶다.',
    ],
  },
  {
    q: '친구가 "이 주식 무조건 오르니까 일단 사봐!"라며 종목을 추천해 준다면?',
    options: [
      '아무리 친해도 위험해 보이므로 정중히 거절하고 예금이나 알아본다.',
      '그 기업이 정말 튼튼한 우량주(삼성전자, 애플 등)인지 먼저 검색해 본다.',
      '솔깃해서 어떤 혁신적인 재료나 호재 뉴스가 있는지 스토리를 찾아본다.',
      '친구 말은 배제하고, 해당 종목의 실적 데이터와 차트 추세를 직접 분석해 본다.',
    ],
  },
  {
    q: '투자를 통해 최종적으로 달성하고 싶은 목표 수익률은?',
    options: [
      '은행 이자보다 조금 더 높은 연 4~6% (마음 편한 게 최고)',
      '자본주의의 평균 성장률을 따르는 연 8~12% 시장 평균 수익률',
      '위험을 감수하더라도 시장을 뛰어넘는 연 20~30% 이상의 고수익',
      '철저한 통계적 우위를 바탕으로 시장 상황 불문 매년 안정적 플러스 수익률',
    ],
  },
]

const TYPE_META = {
  A: { color: '#57E0C3', bg: '#DFFAF4', emoji: '🐢' },
  B: { color: '#3B7FED', bg: '#EEF5FF', emoji: '🦁' },
  C: { color: '#FFD76A', bg: '#FFF8E6', emoji: '🦅' },
  D: { color: '#A78BFA', bg: '#F0EDFF', emoji: '🦉' },
}

const step      = ref('intro')   // intro | quiz | loading | result
const current   = ref(0)
const answers   = ref([])
const result    = ref(null)
const error     = ref(null)

const progress = computed(() => Math.round((answers.value.length / QUESTIONS.length) * 100))

function startQuiz() {
  answers.value = []
  current.value = 0
  step.value    = 'quiz'
}

function selectOption(idx) {
  answers.value[current.value] = idx + 1
  if (current.value < QUESTIONS.length - 1) {
    current.value++
  }
}

function goPrev() {
  if (current.value > 0) current.value--
}

async function submitAnswers() {
  if (answers.value.length < QUESTIONS.length || answers.value.some(a => !a)) return
  step.value = 'loading'
  error.value = null
  try {
    const res = await fetch('/api/chat/investment-type/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answers: answers.value }),
    })
    const data = await res.json()
    if (!res.ok || data.error) throw new Error(data.error ?? `HTTP ${res.status}`)
    result.value = data.result
    step.value   = 'result'
  } catch (e) {
    error.value = e.message
    step.value  = 'quiz'
  }
}

function restart() {
  result.value  = null
  answers.value = []
  current.value = 0
  step.value    = 'intro'
}

const meta = computed(() => result.value ? (TYPE_META[result.value.type_code] ?? TYPE_META.B) : null)

const isAnswered = computed(() => !!answers.value[current.value])
const allAnswered = computed(() => answers.value.length === QUESTIONS.length && answers.value.every(Boolean))
</script>

<template>
  <div class="min-h-screen bg-white" style="font-family:'Pretendard','Noto Sans KR',sans-serif">
    <NavBar />

    <main class="pt-16">
      <!-- 헤더 -->
      <div style="background:linear-gradient(90deg,#fffdf9 0%,#ffffff 50%,#f2fffb 100%);border-bottom:1px solid #EEF1F5">
        <div class="max-w-2xl mx-auto px-6 py-10">
          <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-bold mb-3" style="background:#DFFAF4;color:#0D9B7A;font-size:0.72rem">
            <TrendingUp class="w-3 h-3" />투자 성향 테스트
          </div>
          <h1 class="font-black mb-1" style="font-size:1.8rem;color:#0F122B">나의 투자 유형은?</h1>
          <p style="color:#6F7485;font-size:0.9rem">7가지 질문으로 알아보는 AI 투자 성향 분석</p>
        </div>
      </div>

      <div class="max-w-2xl mx-auto px-6 py-10">

        <!-- ── INTRO ── -->
        <div v-if="step === 'intro'" class="text-center py-8">
          <div class="text-7xl mb-6">📊</div>
          <h2 class="font-black mb-3" style="font-size:1.5rem;color:#0F122B">투자 성향 분석</h2>
          <p class="mb-2 leading-relaxed" style="color:#6F7485">7가지 질문에 솔직하게 답하면<br>AI가 나의 투자 유형을 분석해 드려요.</p>
          <p class="text-sm mb-8" style="color:#6F7485;opacity:0.6">소요 시간 약 2분 · 총 4가지 유형</p>
          <div class="grid grid-cols-2 gap-3 mb-8">
            <div v-for="(t, k) in TYPE_META" :key="k" class="rounded-2xl p-4 text-left" :style="`background:${t.bg};border:1px solid ${t.color}33`">
              <span class="text-2xl">{{ t.emoji }}</span>
              <p class="font-bold text-sm mt-1" :style="`color:${t.color}`">
                {{ k === 'A' ? '안정 제일형' : k === 'B' ? '시장 추종형' : k === 'C' ? '성장 트렌드형' : '데이터 퀀트형' }}
              </p>
            </div>
          </div>
          <button @click="startQuiz" class="px-10 py-3.5 rounded-2xl font-bold text-white transition-all hover:opacity-90" style="background:#0F122B;font-size:1rem">
            테스트 시작하기 →
          </button>
        </div>

        <!-- ── QUIZ ── -->
        <div v-else-if="step === 'quiz'">
          <!-- 진행바 -->
          <div class="mb-6">
            <div class="flex items-center justify-between mb-2">
              <span class="font-bold text-sm" style="color:#0F122B">{{ current + 1 }} / {{ QUESTIONS.length }}</span>
              <span class="text-sm" style="color:#6F7485">{{ progress }}% 완료</span>
            </div>
            <div class="w-full rounded-full h-2" style="background:#EEF1F5">
              <div class="h-2 rounded-full transition-all duration-500" style="background:#57E0C3" :style="`width:${progress}%`"></div>
            </div>
          </div>

          <!-- 질문 카드 -->
          <div class="rounded-2xl p-8 mb-6" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
            <p class="font-bold mb-6 leading-relaxed" style="font-size:1.05rem;color:#0F122B">
              Q{{ current + 1 }}. {{ QUESTIONS[current].q }}
            </p>
            <div class="space-y-3">
              <button
                v-for="(opt, i) in QUESTIONS[current].options"
                :key="i"
                @click="selectOption(i)"
                class="w-full text-left px-5 py-4 rounded-xl font-medium text-sm transition-all"
                :style="answers[current] === i + 1
                  ? 'background:#0F122B;color:white;border:1.5px solid #0F122B'
                  : 'background:white;color:#0F122B;border:1.5px solid #EEF1F5'"
              >
                <span class="font-black mr-3" :style="answers[current] === i + 1 ? 'color:#57E0C3' : 'color:#6F7485'">{{ i + 1 }}</span>
                {{ opt }}
              </button>
            </div>
          </div>

          <!-- 에러 -->
          <p v-if="error" class="text-sm mb-4 px-4 py-3 rounded-xl" style="background:#FFF5F5;color:#E5323B;border:1px solid #FFD0D0">{{ error }}</p>

          <!-- 네비게이션 -->
          <div class="flex items-center justify-between">
            <button @click="goPrev" :disabled="current === 0"
              class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm transition-all disabled:opacity-30"
              style="background:#F8F9FF;color:#0F122B;border:1.5px solid #EEF1F5">
              <ChevronLeft class="w-4 h-4" />이전
            </button>

            <!-- 마지막 문항에서 제출 -->
            <button v-if="current === QUESTIONS.length - 1"
              @click="submitAnswers"
              :disabled="!allAnswered"
              class="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl font-bold text-sm transition-all disabled:opacity-40"
              style="background:#57E0C3;color:#0F122B">
              결과 보기 →
            </button>
            <button v-else
              @click="current++"
              :disabled="!isAnswered"
              class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm transition-all disabled:opacity-40"
              style="background:#0F122B;color:white">
              다음 <ChevronRight class="w-4 h-4" />
            </button>
          </div>

          <!-- 답변 미리보기 점 -->
          <div class="flex justify-center gap-2 mt-6">
            <div v-for="(_, i) in QUESTIONS" :key="i"
              class="w-2 h-2 rounded-full transition-all"
              :style="i === current ? 'background:#0F122B;width:20px' : answers[i] ? 'background:#57E0C3' : 'background:#EEF1F5'"
            ></div>
          </div>
        </div>

        <!-- ── LOADING ── -->
        <div v-else-if="step === 'loading'" class="text-center py-20">
          <div class="text-5xl mb-6 animate-bounce">🤖</div>
          <p class="font-bold mb-2" style="font-size:1.1rem;color:#0F122B">AI가 분석 중이에요</p>
          <p style="color:#6F7485;font-size:0.9rem">답변을 바탕으로 투자 성향을 파악하고 있어요...</p>
          <div class="flex justify-center gap-1.5 mt-8">
            <div v-for="i in 3" :key="i" class="w-2 h-2 rounded-full animate-bounce" style="background:#57E0C3" :style="`animation-delay:${(i-1)*0.15}s`"></div>
          </div>
        </div>

        <!-- ── RESULT ── -->
        <div v-else-if="step === 'result' && result">

          <!-- 유형 카드 -->
          <div class="rounded-2xl p-8 mb-6 text-center" :style="`background:${meta.bg};border:2px solid ${meta.color}40`">
            <div class="text-6xl mb-4">{{ meta.emoji }}</div>
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full font-bold mb-3" :style="`background:${meta.color}20;color:${meta.color};font-size:0.75rem`">
              유형 {{ result.type_code }}
            </div>
            <h2 class="font-black mb-3" style="font-size:1.5rem;color:#0F122B">{{ result.type_name }}</h2>
            <p class="leading-relaxed" style="color:#6F7485;font-size:0.92rem;white-space:pre-line">{{ result.type_description }}</p>
            <div class="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-xl" :style="`background:white;border:1px solid ${meta.color}40`">
              <span style="font-size:1.1rem">{{ meta.emoji }}</span>
              <span class="font-bold text-sm" style="color:#0F122B">{{ result.animal_match }}</span>
            </div>
          </div>

          <!-- 추천 종목 -->
          <div class="rounded-2xl p-6 mb-6" style="background:white;border:1px solid #EEF1F5;box-shadow:0 2px 12px rgba(15,18,43,0.04)">
            <h3 class="font-black mb-4" style="font-size:1rem;color:#0F122B">📈 추천 투자 자산</h3>
            <div class="space-y-4">
              <div v-for="(rec, i) in result.recommendations" :key="i"
                class="flex gap-4 p-4 rounded-xl" :style="`background:${meta.bg};border:1px solid ${meta.color}30`">
                <div class="w-8 h-8 rounded-lg flex items-center justify-center font-black text-sm flex-shrink-0" :style="`background:${meta.color};color:${result.type_code === 'C' || result.type_code === 'A' ? '#0F122B' : 'white'}`">
                  {{ i + 1 }}
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 mb-1 flex-wrap">
                    <span class="font-black" style="color:#0F122B">{{ rec.asset_name }}</span>
                    <span class="px-2 py-0.5 rounded-full text-xs font-bold" :style="`background:${meta.color}20;color:${meta.color}`">{{ rec.asset_type }}</span>
                  </div>
                  <p class="text-sm leading-relaxed" style="color:#6F7485">{{ rec.reason }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- 투자 팁 -->
          <div class="rounded-2xl p-5 mb-8" style="background:#FFF8E6;border:1px solid #FFD76A">
            <p class="font-bold text-sm mb-2" style="color:#B8860B">💡 이런 점을 주의하세요</p>
            <p class="text-sm leading-relaxed" style="color:#B8860B;opacity:0.85">{{ result.investment_tip }}</p>
          </div>

          <!-- 다시하기 -->
          <div class="text-center">
            <button @click="restart" class="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-sm transition-all" style="background:#F8F9FF;color:#0F122B;border:1.5px solid #EEF1F5">
              <RotateCcw class="w-4 h-4" />다시 테스트하기
            </button>
          </div>
        </div>

      </div>
    </main>

    <AppFooter />
  </div>
</template>
