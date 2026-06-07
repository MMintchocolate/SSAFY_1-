import uuid
import time
import base64
import requests

from django.conf import settings
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import ReceiptText


def _serialize_receipt(receipt):
    return {
        'id': receipt.id,
        'original_filename': receipt.original_filename,
        'image_url': receipt.image.url if receipt.image else None,
        'text': receipt.text,
        'fields': receipt.fields,
        'created_at': receipt.created_at.isoformat(),
    }


# ── 영수증 ──────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def ocr_receipt(request):
    if not settings.CLOVA_OCR_INVOKE_URL or not settings.CLOVA_OCR_SECRET:
        return Response({'error': 'CLOVA OCR 환경변수를 설정해 주세요.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    image_file = request.FILES.get('image')
    if not image_file:
        return Response({'error': '이미지 파일이 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

    ext = image_file.name.rsplit('.', 1)[-1].lower()
    fmt = 'jpg' if ext in ('jpg', 'jpeg') else ext

    image_b64 = base64.b64encode(image_file.read()).decode('utf-8')

    payload = {
        'version':   'V2',
        'requestId': str(uuid.uuid4()),
        'timestamp': int(time.time() * 1000),
        'images': [{'format': fmt, 'name': 'receipt', 'data': image_b64}],
    }

    try:
        res = requests.post(
            settings.CLOVA_OCR_INVOKE_URL,
            json=payload,
            headers={
                'X-OCR-SECRET': settings.CLOVA_OCR_SECRET,
                'Content-Type': 'application/json',
            },
            timeout=15,
        )
        res.raise_for_status()
        result = res.json()
    except requests.RequestException as e:
        return Response({'error': f'CLOVA OCR 호출 실패: {str(e)}'}, status=status.HTTP_502_BAD_GATEWAY)

    fields = result.get('images', [{}])[0].get('fields', [])
    text   = '\n'.join(f['inferText'] for f in fields if f.get('inferText'))
    receipt = ReceiptText.objects.create(
        user=request.user,
        original_filename=image_file.name,
        image=image_file,
        text=text,
        fields=fields,
    )

    return Response({'receipt_id': receipt.id, 'text': text, 'fields': fields})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def receipt_first(request):
    receipt = ReceiptText.objects.filter(user=request.user).order_by('id').first()
    if receipt is None:
        return Response({'error': '저장된 영수증이 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(_serialize_receipt(receipt))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def receipt_list(request):
    receipts = ReceiptText.objects.filter(user=request.user)
    return Response([_serialize_receipt(r) for r in receipts])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def receipt_detail(request, pk):
    try:
        receipt = ReceiptText.objects.get(pk=pk, user=request.user)
    except ReceiptText.DoesNotExist:
        return Response({'error': '저장된 영수증 텍스트를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(_serialize_receipt(receipt))

