import base64
import json
import requests

from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from playwright.sync_api import sync_playwright

from receipts.models import ReceiptText

GMS_BASE = 'https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com/v1beta/models'

def _gms_url():
    return f'{GMS_BASE}/{settings.GMS_MODEL}:generateContent'

TEMPLATE_MAP = {
    'expense_report': 'docforms/expense_report.html',
}


def _parse_gemini_json(raw: str):
    if raw.startswith('```'):
        raw = raw.split('```')[1]
        if raw.startswith('json'):
            raw = raw[4:]
    return json.loads(raw.strip())


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def classify(request):
    """OCR 텍스트 → 양식 분류 + 구조화 JSON 반환"""
    receipt_id = request.data.get('receipt_id')
    if not receipt_id:
        return Response({'error': 'receipt_id가 필요합니다.'}, status=400)

    try:
        receipt = ReceiptText.objects.get(pk=receipt_id, user=request.user)
    except ReceiptText.DoesNotExist:
        return Response({'error': '영수증을 찾을 수 없습니다.'}, status=404)

    prompt = (
        '다음 영수증/문서 텍스트를 분석하여 JSON만 반환하세요.\n\n'
        '지원 양식:\n'
        '- expense_report: 지출결의서 (지출 내역, 품목, 금액이 포함된 경우)\n\n'
        '반환 형식:\n'
        '{\n'
        '  "template_type": "expense_report",\n'
        '  "data": {\n'
        '    "title": "지출결의서",\n'
        '    "department": "부서명",\n'
        '    "applicant": "신청자명",\n'
        '    "date": "YYYY-MM-DD",\n'
        '    "purpose": "지출 목적",\n'
        '    "items": [\n'
        '      {"no": 1, "name": "품목명", "quantity": 1, "unit_price": 0, "amount": 0, "note": ""}\n'
        '    ],\n'
        '    "total": 0\n'
        '  }\n'
        '}\n\n'
        '모르는 항목은 빈 문자열("") 또는 0으로 채우세요.\n'
        'JSON 외 다른 텍스트는 절대 포함하지 마세요.\n\n'
        f'문서 텍스트:\n{receipt.text}'
    )

    try:
        res = requests.post(
            _gms_url(),
            headers={'Content-Type': 'application/json', 'x-goog-api-key': settings.GMS_KEY},
            json={'contents': [{'parts': [{'text': prompt}]}]},
            timeout=30,
        )
        res.raise_for_status()
        raw = res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        result = _parse_gemini_json(raw)
    except Exception as e:
        return Response({'error': f'분류 실패: {str(e)}'}, status=502)

    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def render_form(request):
    """구조화 JSON → HTML 렌더링 → PDF 반환"""
    template_type = request.data.get('template_type')
    data          = request.data.get('data', {})
    receipt_id    = request.data.get('receipt_id')

    if not template_type:
        return Response({'error': 'template_type이 필요합니다.'}, status=400)

    template_name = TEMPLATE_MAP.get(template_type)
    if not template_name:
        return Response({'error': f'지원하지 않는 양식 종류: {template_type}'}, status=400)

    # 금액 재계산 (프론트에서 편집된 수량/단가 반영)
    items = data.get('items', [])
    for item in items:
        try:
            item['amount'] = int(item.get('quantity', 0)) * int(item.get('unit_price', 0))
        except (TypeError, ValueError):
            item['amount'] = 0
    data['total'] = sum(item['amount'] for item in items)

    # 영수증 이미지 base64 임베드
    receipt_image_b64 = None
    if receipt_id:
        try:
            receipt = ReceiptText.objects.get(pk=receipt_id, user=request.user)
            if receipt.image:
                with open(receipt.image.path, 'rb') as f:
                    receipt_image_b64 = base64.b64encode(f.read()).decode()
        except (ReceiptText.DoesNotExist, OSError):
            pass

    html_string = render_to_string(template_name, {
        'data': data,
        'receipt_image_b64': receipt_image_b64,
    })

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html_string, wait_until='networkidle')
            pdf_bytes = page.pdf(format='A4', print_background=True)
            browser.close()
    except Exception as e:
        return Response({'error': f'PDF 생성 실패: {str(e)}'}, status=500)

    date_str = data.get('date', 'date')
    title = data.get('title', '지출결의서')
    filename = f"{title}_{date_str}.pdf"

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
