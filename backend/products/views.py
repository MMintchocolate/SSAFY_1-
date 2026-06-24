import urllib.request
import urllib.parse
import json

from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .constants import resolve_product_url
from .models import FinancialProductCache


def _fetch_fss_from_api(endpoint: str):
    """FSS API 직접 호출 — DB 저장용"""
    params = urllib.parse.urlencode({
        'auth': settings.FSS_API_KEY,
        'topFinGrpNo': '020000',
        'pageNo': 1,
    })
    url = f'{settings.FSS_BASE_URL}/{endpoint}?{params}'

    with urllib.request.urlopen(url, timeout=20) as res:
        data = json.loads(res.read().decode())

    result = data.get('result', {})
    if result.get('err_cd') != '000':
        raise ValueError(result.get('err_msg', '알 수 없는 오류'))

    base_list   = result.get('baseList',   [])
    option_list = result.get('optionList', [])

    return [
        {
            'baseinfo': {
                **base,
                'product_url': resolve_product_url(base.get('kor_co_nm', ''), base.get('fin_prdt_nm', '')),
            },
            'options': [o for o in option_list if o['fin_prdt_cd'] == base['fin_prdt_cd']],
        }
        for base in base_list
    ]


def _read_from_db(product_type: str):
    try:
        obj = FinancialProductCache.objects.get(product_type=product_type)
        return obj.data, obj.updated_at
    except FinancialProductCache.DoesNotExist:
        return None, None


@api_view(['GET'])
def deposit_list(request):
    data, updated_at = _read_from_db(FinancialProductCache.DEPOSIT)
    if data is None:
        return Response({'error': 'no_data'}, status=status.HTTP_404_NOT_FOUND)
    return Response({'products': data, 'updated_at': updated_at.isoformat()})


@api_view(['GET'])
def savings_list(request):
    data, updated_at = _read_from_db(FinancialProductCache.SAVINGS)
    if data is None:
        return Response({'error': 'no_data'}, status=status.HTTP_404_NOT_FOUND)
    return Response({'products': data, 'updated_at': updated_at.isoformat()})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_products(request):
    """FSS API 호출 후 DB 갱신. 로그인 필요."""
    if not settings.FSS_API_KEY:
        return Response({'error': 'FSS_API_KEY 환경변수를 설정해 주세요.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    product_type = request.data.get('type', 'all')
    results = {}

    try:
        if product_type in ('deposit', 'all'):
            data = _fetch_fss_from_api('depositProductsSearch.json')
            obj, _ = FinancialProductCache.objects.update_or_create(
                product_type=FinancialProductCache.DEPOSIT,
                defaults={'data': data},
            )
            results['deposit'] = {'count': len(data), 'updated_at': obj.updated_at.isoformat()}

        if product_type in ('savings', 'all'):
            data = _fetch_fss_from_api('savingProductsSearch.json')
            obj, _ = FinancialProductCache.objects.update_or_create(
                product_type=FinancialProductCache.SAVINGS,
                defaults={'data': data},
            )
            results['savings'] = {'count': len(data), 'updated_at': obj.updated_at.isoformat()}

    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)
    except Exception as e:
        return Response({'error': f'FSS API 호출에 실패했습니다: {e}'}, status=status.HTTP_502_BAD_GATEWAY)

    return Response({'ok': True, 'results': results})
