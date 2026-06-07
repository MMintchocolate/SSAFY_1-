import urllib.request
import urllib.parse
import json

from django.conf import settings
from django.core.cache import cache
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .constants import resolve_product_url


CACHE_TIMEOUT = 60 * 60  # 1시간


def _fetch_fss(endpoint: str, top_fin_grp_no: str = '020000', page_no: int = 1):
    cache_key = f'fss_{endpoint}_{top_fin_grp_no}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    params = urllib.parse.urlencode({
        'auth': settings.FSS_API_KEY,
        'topFinGrpNo': top_fin_grp_no,
        'pageNo': page_no,
    })
    url = f'{settings.FSS_BASE_URL}/{endpoint}?{params}'

    with urllib.request.urlopen(url, timeout=20) as res:
        data = json.loads(res.read().decode())

    result = data.get('result', {})
    if result.get('err_cd') != '000':
        raise ValueError(result.get('err_msg', '알 수 없는 오류'))

    base_list   = result.get('baseList',   [])
    option_list = result.get('optionList', [])

    products = [
        {
            'baseinfo': {
                **base,
                'product_url': resolve_product_url(base.get('kor_co_nm', ''), base.get('fin_prdt_nm', '')),
            },
            'options': [o for o in option_list if o['fin_prdt_cd'] == base['fin_prdt_cd']],
        }
        for base in base_list
    ]

    cache.set(cache_key, products, timeout=CACHE_TIMEOUT)
    return products


@api_view(['GET'])
def deposit_list(request):
    if not settings.FSS_API_KEY:
        return Response({'error': 'FSS_API_KEY 환경변수를 설정해 주세요.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    try:
        products = _fetch_fss('depositProductsSearch.json')
        return Response(products)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)
    except Exception as e:
        return Response({'error': f'FSS API 호출에 실패했습니다: {e}'}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(['GET'])
def savings_list(request):
    if not settings.FSS_API_KEY:
        return Response({'error': 'FSS_API_KEY 환경변수를 설정해 주세요.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    try:
        products = _fetch_fss('savingProductsSearch.json')
        return Response(products)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)
    except Exception as e:
        return Response({'error': f'FSS API 호출에 실패했습니다: {e}'}, status=status.HTTP_502_BAD_GATEWAY)
