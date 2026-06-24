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

SYSTEM_PROMPT = (
    '당신은 금융 보안 전문 AI 어시스턴트입니다. '
    '주식, 보안 뉴스, 금융 상품, 사기 예방 등에 대해 친절하고 정확하게 답변해 주세요. '
    '또 다른 질문이 있을 수도 있습니다. 다만, 욕설이나 비방 언어에 대해서는 답변할 수 없다고 하세요'
    '마크다운 없이 순수 텍스트로만 답변해 주세요.'
)


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
