import requests
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response

KAKAO_KEYWORD_URL  = 'https://dapi.kakao.com/v2/local/search/keyword.json'
KAKAO_COORD2ADDR   = 'https://dapi.kakao.com/v2/local/geo/coord2address.json'


def _kakao_headers():
    return {'Authorization': f'KakaoAK {settings.KAKAO_REST_API_KEY}'}


def _normalize_docs(docs: list) -> list:
    """카카오 장소 검색 documents → 프론트 표준 형식. 좌표는 이미 WGS84."""
    result = []
    for d in docs:
        try:
            lat = float(d['y'])
            lng = float(d['x'])
        except (KeyError, ValueError):
            continue
        result.append({
            'title':    d.get('place_name', ''),
            'address':  d.get('road_address_name') or d.get('address_name', ''),
            'category': d.get('category_name', ''),
            'phone':    d.get('phone', ''),
            'distance': d.get('distance', ''),
            'lat': lat,
            'lng': lng,
        })
    return result


def _kakao_search(query: str, x=None, y=None, radius=None,
                  sort='accuracy', pages=3) -> list:
    """
    카카오 키워드 검색 (size 최대 15/page).
    x, y, radius 제공 시 거리순 정렬.
    pages 만큼 페이지네이션해 합산 반환.
    """
    all_docs = []
    for page in range(1, pages + 1):
        params = {'query': query, 'size': 15, 'page': page, 'sort': sort}
        if x is not None and y is not None:
            params['x'] = x
            params['y'] = y
        if radius is not None:
            params['radius'] = radius

        try:
            r = requests.get(
                KAKAO_KEYWORD_URL,
                params=params,
                headers=_kakao_headers(),
                timeout=5,
            )
            if not r.ok:
                break
            data = r.json()
            all_docs.extend(data.get('documents', []))
            if data.get('meta', {}).get('is_end', True):
                break
        except Exception:
            break

    return all_docs


# ── 기능 1: 지역명 기반 은행 검색 ────────────────────────────────────────────

@api_view(['GET'])
def search_branches(request):
    """
    지역명 + 은행명 조합 검색 (geolocation 불필요).
    ?region=부산진구&keyword=국민은행

    - region : 시/구/동 단위 지역명 (없으면 keyword만으로 검색)
    - keyword: 은행 이름 (기본값: '은행')
    """
    region  = request.query_params.get('region', '').strip()
    keyword = request.query_params.get('keyword', '은행').strip()
    query   = f'{region} {keyword}'.strip() if region else keyword

    if not settings.KAKAO_REST_API_KEY:
        return Response({'error': 'KAKAO_REST_API_KEY 환경변수를 설정해 주세요.'}, status=503)

    docs     = _kakao_search(query, pages=3)   # 최대 45개
    branches = _normalize_docs(docs)
    return Response({'query': query, 'branches': branches})


# ── 기능 2: 현재 위치(위경도) 기반 은행 검색 ─────────────────────────────────

@api_view(['GET'])
def search_by_location(request):
    """
    위경도 + 반경으로 직접 장소 검색 (카카오 Local API 네이티브 지원).
    ?lat=35.16&lng=129.05&keyword=국민은행&radius=3000

    카카오 키워드 API의 x, y, radius 파라미터를 그대로 사용하므로
    리버스 지오코딩 없이 정확한 반경 검색이 가능.
    """
    try:
        lat = float(request.query_params['lat'])
        lng = float(request.query_params['lng'])
    except (KeyError, ValueError):
        return Response({'error': 'lat, lng 파라미터(숫자)가 필요합니다.'}, status=400)

    keyword = request.query_params.get('keyword', '은행').strip()
    radius  = int(request.query_params.get('radius', 3000))
    radius  = max(500, min(radius, 20000))   # 500m ~ 20km

    if not settings.KAKAO_REST_API_KEY:
        return Response({'error': 'KAKAO_REST_API_KEY 환경변수를 설정해 주세요.'}, status=503)

    docs     = _kakao_search(keyword, x=lng, y=lat, radius=radius, sort='distance', pages=2)
    branches = _normalize_docs(docs)

    # 주소 표시용 지역명 (카카오 좌표→주소 API)
    area = _coord_to_area(lat, lng)
    return Response({'area': area, 'branches': branches})


# ── 유틸: 좌표 → 지역명 (내 위치 라벨 표시용) ────────────────────────────────

def _coord_to_area(lat: float, lng: float) -> str:
    try:
        r = requests.get(
            KAKAO_COORD2ADDR,
            params={'x': lng, 'y': lat, 'input_coord': 'WGS84'},
            headers=_kakao_headers(),
            timeout=5,
        )
        docs = r.json().get('documents', [])
        if not docs:
            return ''
        addr = docs[0].get('road_address') or docs[0].get('address') or {}
        parts = [
            addr.get('region_1depth_name', ''),
            addr.get('region_2depth_name', ''),
            addr.get('region_3depth_name', ''),
        ]
        return ' '.join(p for p in parts if p).strip()
    except Exception:
        return ''


@api_view(['GET'])
def reverse_geocode(request):
    """
    ?lat=&lng=  → 카카오 좌표→주소 변환 프록시 (프론트 주소 표시용).
    """
    try:
        lat = float(request.query_params['lat'])
        lng = float(request.query_params['lng'])
    except (KeyError, ValueError):
        return Response({'error': 'lat, lng 파라미터가 필요합니다.'}, status=400)

    if not settings.KAKAO_REST_API_KEY:
        return Response({'error': 'KAKAO_REST_API_KEY 환경변수를 설정해 주세요.'}, status=503)

    try:
        r = requests.get(
            KAKAO_COORD2ADDR,
            params={'x': lng, 'y': lat, 'input_coord': 'WGS84'},
            headers=_kakao_headers(),
            timeout=5,
        )
        return Response(r.json(), status=r.status_code)
    except requests.RequestException as e:
        return Response({'error': str(e)}, status=502)
