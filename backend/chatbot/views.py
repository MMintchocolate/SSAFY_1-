import re
import requests
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

_GMS_URL = (
    'https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com'
    '/v1beta/models/{model}:generateContent'
)

SYSTEM_PROMPT = """당신은 moni의 AI 어시스턴트입니다.
moni는 금융상품 비교, 주식 분석, 지출 관리, 뉴스 요약 등을 제공하는 스마트 금융 플랫폼입니다.

[moni 서비스 메뉴]

- 금융상품 비교: 금융감독원 공시 기준 정기예금·적금을 최고금리 순으로 비교. 저축 기간 필터와 우대조건 확인 가능.
- 실시간 주식: 국내 주식 실시간 시세, 호가창, 체결 내역, 관심 종목 등록 및 차트 분석.
- 매수 신호: RSI, MACD, 볼린저밴드 등 기술적 지표를 AI가 종합해 매수·매도 신호 자동 산출.
- ML 데이터 (AI 예측): 종목 과거 데이터로 LightGBM 모델을 직접 학습시키고 다음 날 주가 방향 예측.
- 지출 분석: 영수증·카드 데이터를 카테고리별로 자동 분류해 월별 소비 트렌드와 과소비 항목 시각화.
- 영수증 장부: 영수증을 입력하면 PDF 장부로 자동 생성해 다운로드 및 공유 가능.
- 금 시세: 국제 금 시세와 환율 실시간 추적.
- 금융 뉴스: 금융·경제 최신 뉴스 모아보기, AI 요약으로 핵심 내용 빠르게 파악.
- 커뮤니티: 주식 토론 게시판과 자유 게시판에서 다른 투자자들과 정보 교류.
- 지점 찾기: 내 주변 은행 지점·ATM 위치 검색.

[답변 지침]
- 사용자가 궁금한 것이나 도움을 요청하면, 위 메뉴 중 가장 적합한 메뉴 이름을 언급하며 추천해 주세요. URL이나 경로는 절대 언급하지 마세요.
  예시: "적금 금리 비교는 금융상품 비교 메뉴에서 확인하실 수 있어요."
- 금융·투자·경제 관련 질문에는 친절하고 정확하게 답변하세요.
- 욕설이나 비방 언어가 포함된 질문에는 답변할 수 없다고 안내하세요.
- 마크다운 기호 없이 순수 텍스트로만 답변하세요.
"""


@api_view(['POST'])
@permission_classes([AllowAny])
def chat(request):
    message = request.data.get('message', '').strip()
    if not message:
        return Response({'error': '메시지를 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)
    # print("메세지는 받음", message)
    if not settings.GMS_KEY:
        return Response({'error': 'GMS_KEY 환경변수가 설정되지 않았습니다.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # 이전 대화 기록 (프론트에서 넘겨주는 배열: [{role, text}, ...])
    history = request.data.get('history', [])

    contents = [{'role': 'user', 'parts': [{'text': SYSTEM_PROMPT}]},
                {'role': 'model', 'parts': [{'text': '알겠습니다. 도움이 필요하신 내용을 말씀해 주세요.'}]}]

    for h in history:
        role = 'model' if h.get('role') == 'model' else 'user'
        contents.append({'role': role, 'parts': [{'text': h.get('text', '')}]})

    contents.append({'role': 'user', 'parts': [{'text': message}]})

    try:
        res = requests.post(
            _GMS_URL.format(model=settings.GMS_MODEL),
            headers={
                'Content-Type':   'application/json',
                'x-goog-api-key': settings.GMS_KEY,
            },
            json={'contents': contents},
            timeout=30,
        )
        res.raise_for_status()
        raw   = res.json()['candidates'][0]['content']['parts'][0]['text']
        reply = re.sub(r'\*\*|#+\s*', '', raw).strip()
    except Exception as e:
        return Response({'error': f'응답 생성 실패: {e}'}, status=status.HTTP_502_BAD_GATEWAY)

    return Response({'reply': reply})


INVESTMENT_PROMPT_TEMPLATE = """[Role]
You are a professional financial advisor and stock investment type analyzer. Your job is to analyze a user's answers to a 7-question investment propensity test, determine their investment type, and recommend appropriate stock investment sectors and specific assets (ETFs or Blue-chip stocks) current as of 2026.

[Test Questions & Context]
Each option (1 to 4) corresponds to a specific investment trait:
- Option 1: Conservative / Dividend-seeking (Type A)
- Option 2: Market-following / Blue-chip (Type B)
- Option 3: Growth-seeking / Tech & Innovation (Type C)
- Option 4: Data-driven / Quantitative & Momentum (Type D)

[Analysis Logic]
Count the frequency of each option (1 to 4). Determine the final type based on the majority.
- Majority 1s: Type A (안정 제일형 - 고배당 및 자산배분)
- Majority 2s: Type B (시장 추종형 - 우량주 및 지수 ETF)
- Majority 3s: Type C (성장 트렌드형 - 미래 혁신 및 테크 성장주)
- Majority 4s: Type D (데이터 퀀트형 - 계량 지표 및 모멘텀)
If there is a tie, use the answers to Q2 and Q7 as the tie-breaker to determine the final type.

[User Answers (Q1~Q7)]
{answers_json}

[Output Format]
You MUST respond ONLY with a valid JSON object. Do not include any conversational filler, markdown formatting (like ```json), or markdown tags. The JSON must follow this exact structure:

{{
  "result": {{
    "type_code": "A" | "B" | "C" | "D",
    "type_name": "유형 이름 (e.g., 미래의 테슬라를 찾는 성장/트렌드형)",
    "type_description": "이 유형의 투자 성향과 특징을 설명하는 친근하고 명확한 문장 (2~3줄)",
    "animal_match": "성향에 어울리는 투자 동물 캐릭터 이름 (e.g., 공격적인 사자, 느긋한 거북이, 꼼꼼한 부엉이 등)",
    "recommendations": [
      {{
        "asset_name": "추천 종목/ETF 명칭",
        "asset_type": "국내주식 / 해외주식 / ETF / 채권 중 택일",
        "reason": "이 유형의 사용자에게 이 자산을 추천하는 이유 (2줄 내외로 쉽고 친근하게 설명)"
      }},
      {{
        "asset_name": "...",
        "asset_type": "...",
        "reason": "..."
      }},
      {{
        "asset_name": "...",
        "asset_type": "...",
        "reason": "..."
      }}
    ],
    "investment_tip": "이 유형이 투자할 때 반드시 주의해야 할 점이나 리스크 관리 조언 (2줄)"
  }}
}}

[Constraints]
1. Language: Korean (한국어)
2. Tone: Friendly, professional, and engaging like an MBTI result.
3. Up-to-date: Financial asset recommendations must reflect the realistic market condition of 2026.
"""


@api_view(['POST'])
@permission_classes([AllowAny])
def investment_type(request):
    """7문항 답변을 받아 Gemini로 투자 성향 분석 결과 반환."""
    answers = request.data.get('answers', [])
    if len(answers) != 7 or not all(isinstance(a, int) and 1 <= a <= 4 for a in answers):
        return Response({'error': '1~4 사이 정수 7개를 answers 배열로 보내주세요.'}, status=status.HTTP_400_BAD_REQUEST)

    if not settings.GMS_KEY:
        return Response({'error': 'GMS_KEY 환경변수가 설정되지 않았습니다.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    import json as _json
    answers_json = _json.dumps({"answers": answers}, ensure_ascii=False)
    prompt = INVESTMENT_PROMPT_TEMPLATE.format(answers_json=answers_json)

    try:
        res = requests.post(
            _GMS_URL.format(model=settings.GMS_MODEL),
            headers={
                'Content-Type':   'application/json',
                'x-goog-api-key': settings.GMS_KEY,
            },
            json={'contents': [{'role': 'user', 'parts': [{'text': prompt}]}]},
            timeout=30,
        )
        res.raise_for_status()
        raw = res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        # 간혹 ```json ... ``` 감싸는 경우 제거
        raw = re.sub(r'^```json\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        result = _json.loads(raw)
    except _json.JSONDecodeError:
        return Response({'error': 'AI 응답을 파싱하지 못했습니다. 다시 시도해 주세요.'}, status=status.HTTP_502_BAD_GATEWAY)
    except Exception as e:
        return Response({'error': f'분석 실패: {e}'}, status=status.HTTP_502_BAD_GATEWAY)

    return Response(result)
