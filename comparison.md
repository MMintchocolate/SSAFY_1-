# 개발 방식 비교: Claude Code 활용 vs 초보 개발자 직접 구현

> **비교 대상:** 챗봇 기능 (`backend/chatbot/views.py`)
> **주제:** AI 코딩 도구(Claude Code)를 활용한 개발과 초보 개발자가 직접 구현한 결과물의 차이

---

## 코드 비교

### 초보 개발자가 직접 짠 코드

```python
from rest_framework.decorators import api_view
from rest_framework.response import Response

# 답변을 직접 다 적어놓음
RESPONSES = {
    '금융상품': '금융상품 비교 기능에서 정기예금과 적금을 비교할 수 있어요.',
    '예금':     '정기예금은 금융상품 비교 메뉴에서 확인하세요.',
    '적금':     '적금 상품은 금융상품 비교 메뉴에서 확인하세요.',
    '주식':     '실시간 주식 메뉴에서 국내 주식 시세를 확인할 수 있어요.',
    '매수':     '매수 신호 메뉴에서 기술적 지표를 확인하세요.',
    '예측':     'ML 데이터 메뉴에서 AI 주가 예측 기능을 사용할 수 있어요.',
    '지출':     '지출 분석 메뉴에서 소비 패턴을 확인할 수 있어요.',
    '영수증':   '영수증 장부 메뉴에서 영수증을 입력하고 PDF로 저장할 수 있어요.',
    '뉴스':     '금융 뉴스 메뉴에서 최신 뉴스를 확인하세요.',
    '안녕':     '안녕하세요! moni 챗봇입니다.',
}

@api_view(['POST'])
def chat(request):
    message = request.data.get('message', '')

    # 키워드 하나씩 비교
    reply = '죄송해요, 잘 모르겠어요.'
    for keyword in RESPONSES:
        if keyword in message:
            reply = RESPONSES[keyword]
            break

    return Response({'reply': reply})
```

---

### Claude Code로 개발한 코드

```python
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
- 금융상품 비교: 금융감독원 공시 기준 정기예금·적금을 최고금리 순으로 비교.
- 실시간 주식: 국내 주식 실시간 시세, 호가창, 체결 내역, 관심 종목 등록 및 차트 분석.
- 매수 신호: RSI, MACD, 볼린저밴드 등 기술적 지표를 AI가 종합해 매수·매도 신호 자동 산출.
- ML 데이터 (AI 예측): 종목 과거 데이터로 LightGBM 모델을 학습시키고 다음 날 주가 방향 예측.
- 지출 분석: 영수증·카드 데이터를 카테고리별로 자동 분류해 월별 소비 트렌드 시각화.
- 영수증 장부: 영수증을 입력하면 PDF 장부로 자동 생성.
- 금 시세: 국제 금 시세와 환율 실시간 추적.
- 금융 뉴스: 금융·경제 최신 뉴스 모아보기, AI 요약으로 핵심 내용 빠르게 파악.
- 커뮤니티: 주식 토론 게시판과 자유 게시판에서 다른 투자자들과 정보 교류.
- 지점 찾기: 내 주변 은행 지점·ATM 위치 검색.

[답변 지침]
- 가장 적합한 메뉴 이름을 언급하며 추천해 주세요. URL이나 경로는 절대 언급하지 마세요.
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

    if not settings.GMS_KEY:
        return Response({'error': 'GMS_KEY 환경변수가 설정되지 않았습니다.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    history = request.data.get('history', [])

    # 시스템 프롬프트 + 이전 대화 + 현재 메시지 조립
    contents = [
        {'role': 'user',  'parts': [{'text': SYSTEM_PROMPT}]},
        {'role': 'model', 'parts': [{'text': '알겠습니다. 도움이 필요하신 내용을 말씀해 주세요.'}]},
    ]
    for h in history:
        role = 'model' if h.get('role') == 'model' else 'user'
        contents.append({'role': role, 'parts': [{'text': h.get('text', '')}]})
    contents.append({'role': 'user', 'parts': [{'text': message}]})

    try:
        res = requests.post(
            _GMS_URL.format(model=settings.GMS_MODEL),
            headers={'Content-Type': 'application/json', 'x-goog-api-key': settings.GMS_KEY},
            json={'contents': contents},
            timeout=30,
        )
        res.raise_for_status()
        raw   = res.json()['candidates'][0]['content']['parts'][0]['text']
        reply = re.sub(r'\*\*|#+\s*', '', raw).strip()
    except Exception as e:
        return Response({'error': f'응답 생성 실패: {e}'}, status=status.HTTP_502_BAD_GATEWAY)

    return Response({'reply': reply})
```

---

## 항목별 비교

| 항목 | 초보 개발자 직접 구현 | Claude Code 활용 |
|---|---|---|
| **코드 줄 수** | 약 25줄 | 약 55줄 |
| **답변 방식** | 딕셔너리 키워드 매칭 | Gemini AI 자연어 생성 |
| **대화 맥락** | ❌ 없음 (매 요청 독립) | ✅ `history`로 이전 대화 유지 |
| **역할 부여** | ❌ 없음 | ✅ `SYSTEM_PROMPT`로 moni 어시스턴트 지정 |
| **오류 처리** | ❌ 없음 | ✅ API 키 미설정, 네트워크 오류 등 분기 처리 |
| **HTTP 상태코드** | 모든 응답 200 | ✅ 400 / 503 / 502 상황별 반환 |
| **욕설 처리** | ❌ 감지 불가 | ✅ SYSTEM_PROMPT 규칙으로 자동 거절 |
| **유지보수** | 키워드 추가 시 코드 수정 | 텍스트(SYSTEM_PROMPT)만 수정 |
| **확장성** | 키워드 수만큼만 대응 | 질문 형태 무제한 대응 |
| **응답 품질** | 고정 문장 1개 | 질문 맥락에 맞는 자연어 답변 |

---

## 같은 질문, 다른 답변

### Q. "적금 금리 높은 거 추천해줘"

| | 답변 |
|---|---|
| **초보 직접 구현** | `"적금 상품은 금융상품 비교 메뉴에서 확인하세요."` |
| **Claude Code 활용** | `"적금 금리 비교는 금융상품 비교 메뉴에서 확인하실 수 있어요. 저축 기간 필터로 원하는 기간의 최고금리 상품을 바로 찾을 수 있고, 우대조건도 함께 확인할 수 있습니다."` |

---

### Q. "요즘 테슬라 살만해?"

| | 답변 |
|---|---|
| **초보 직접 구현** | `"죄송해요, 잘 모르겠어요."` (`"테슬라"` 키워드 없음) |
| **Claude Code 활용** | `"테슬라 투자 판단에는 매수 신호 메뉴와 ML 데이터 메뉴를 활용해 보세요. 매수 신호에서 RSI·MACD·볼린저밴드 기반 시그널을, ML 데이터에서 LightGBM 모델의 다음날 방향 예측을 확인할 수 있습니다. 단, 투자 결정은 본인의 판단 하에 신중하게 하시길 권장드립니다."` |

---

### Q. (직전 대화에서 "적금 물어봤고) "그거 말고 주식도 알려줘"

| | 답변 |
|---|---|
| **초보 직접 구현** | `"실시간 주식 메뉴에서 국내 주식 시세를 확인할 수 있어요."` (앞 대화 모름) |
| **Claude Code 활용** | `"적금 외에 주식도 관심이 있으시군요. 실시간 주식 메뉴에서 시세와 차트를, 매수 신호 메뉴에서 AI 기반 매수·매도 타이밍 분석을 함께 확인하실 수 있어요."` (앞 대화 기억) |

---

## 개발 과정 비교

```
[ 초보 개발자 직접 구현 ]

기획 → 키워드 직접 수집 → 답변 문장 하나씩 작성 → 코드 작성
       (시간 소요 큼)      (업데이트 어려움)

예상 소요: 수 시간 ~ 하루


[ Claude Code 활용 ]

기획 → Claude Code에 요구사항 전달 → 코드 생성 → 검토 및 SYSTEM_PROMPT 수정
                                      (자동 생성)   (빠른 수정)

예상 소요: 수십 분
```

---

## 핵심 차이 요약

- **초보 직접 구현:** 개발자가 모든 답변을 미리 예상하고 하드코딩해야 함. 예상 못한 질문에는 무조건 실패.
- **Claude Code 활용:** 구조 설계와 SYSTEM_PROMPT 작성에 집중하면, 나머지 답변 품질은 Gemini가 담당. 개발자가 예상하지 못한 질문도 자연스럽게 처리.
