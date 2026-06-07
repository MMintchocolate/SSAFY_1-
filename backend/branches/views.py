import requests
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


@api_view(['GET'])
def reverse_geocode(request):
    """
    NCP Reverse Geocoding 프록시
    ?coords=lng,lat  (경도,위도 순서 — NCP 규격)
    """
    coords = request.query_params.get('coords')
    if not coords:
        return Response({'error': 'coords 파라미터가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

    if not settings.NCP_MAP_CLIENT_ID or not settings.NCP_MAP_CLIENT_SECRET:
        return Response({'error': 'NCP_MAP_CLIENT_ID / NCP_MAP_CLIENT_SECRET 환경변수를 설정해 주세요.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    res = requests.get(
        'https://maps.apigw.ntruss.com/map-reversegeocode/v2/gc',
        params={'coords': coords, 'output': 'json', 'orders': 'roadaddr,addr'},
        headers={
            'X-NCP-APIGW-API-KEY-ID': settings.NCP_MAP_CLIENT_ID,
            'X-NCP-APIGW-API-KEY':    settings.NCP_MAP_CLIENT_SECRET,
        },
        timeout=5,
    )
    return Response(res.json(), status=res.status_code)


@api_view(['GET'])
def search_branches(request):
    """
    Naver 지역 검색 프록시
    ?query=은행명&display=5
    """
    query   = request.query_params.get('query', '은행')
    display = request.query_params.get('display', '10')

    if not settings.NAVER_SEARCH_CLIENT_ID or not settings.NAVER_SEARCH_CLIENT_SECRET:
        return Response({'error': 'NAVER_SEARCH_CLIENT_ID / NAVER_SEARCH_CLIENT_SECRET 환경변수를 설정해 주세요.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    res = requests.get(
        'https://openapi.naver.com/v1/search/local.json',
        params={'query': query, 'display': display, 'sort': 'random'},
        headers={
            'X-Naver-Client-Id':     settings.NAVER_SEARCH_CLIENT_ID,
            'X-Naver-Client-Secret': settings.NAVER_SEARCH_CLIENT_SECRET,
        },
        timeout=5,
    )
    return Response(res.json(), status=res.status_code)
