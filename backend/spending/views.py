import json
import re
import requests
from pathlib import Path

from django.conf import settings
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .parser import load_csv, parse_csv, aggregate_data, CATEGORY_MAP

GMS_BASE     = 'https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com/v1beta/models'
SAMPLE_CSV   = Path(__file__).parent / 'data' / 'sample_expenses.csv'
MERCHANT_MAP = Path(__file__).parent / 'data' / 'merchant_map.json'

_df_cache = None


# ── merchant_map.json 헬퍼 ──────────────────────────────────────────────────

def _load_map() -> dict:
    if MERCHANT_MAP.exists():
        return json.loads(MERCHANT_MAP.read_text(encoding='utf-8'))
    return {}


def _save_map(new_entries: dict):
    existing = _load_map()
    existing.update(new_entries)
    MERCHANT_MAP.parent.mkdir(parents=True, exist_ok=True)
    MERCHANT_MAP.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding='utf-8')


def _apply_map(df, mapping: dict) -> dict:
    """저장된 맵을 df의 기타 행에 적용. 변경된 {merchant: category} 반환."""
    changed = {}
    category_list = list(CATEGORY_MAP.keys())
    for merchant, category in mapping.items():
        if category not in category_list:
            continue
        mask = (df['merchant'] == merchant) & (df['category'] == '기타')
        if mask.any():
            df.loc[mask, 'category'] = category
            changed[merchant] = category
    return changed


# ── df 캐시 ──────────────────────────────────────────────────────────────────

def _get_df(uploaded_content: str | None = None):
    global _df_cache
    if uploaded_content:
        _df_cache = parse_csv(uploaded_content)
    elif _df_cache is None:
        _df_cache = load_csv(SAMPLE_CSV)
    else:
        return _df_cache
    # 새 df 로드 시 저장된 분류 자동 적용
    saved = _load_map()
    if saved:
        _apply_map(_df_cache, saved)
    return _df_cache


# ── 뷰 ────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stats(request):
    period    = request.query_params.get('period', 'this_month')
    start     = request.query_params.get('start')
    end       = request.query_params.get('end')
    direction = request.query_params.get('direction', 'out')
    try:
        df     = _get_df()
        result = aggregate_data(df, period, start, end, direction)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def upload_csv(request):
    csv_file = request.FILES.get('file')
    if not csv_file:
        return Response({'error': 'CSV 파일이 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

    for enc in ('utf-8-sig', 'utf-8', 'euc-kr', 'cp949'):
        try:
            content = csv_file.read().decode(enc)
            break
        except (UnicodeDecodeError, LookupError):
            csv_file.seek(0)
    else:
        return Response({'error': 'CSV 인코딩을 읽을 수 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        df      = _get_df(content)
        saved   = _load_map()
        return Response({'success': True, 'rows': len(df), 'saved_map_size': len(saved)})
    except Exception as e:
        return Response({'error': f'CSV 파싱 실패: {e}'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def classify_misc(request):
    """기타 카테고리 분류.
    only_saved=true  → 저장된 맵만 적용 (API 호출 없음)
    only_saved=false → 미분류 가맹점만 Gemini 호출 후 저장+적용
    """
    global _df_cache
    only_saved = str(request.data.get('only_saved', 'false')).lower() == 'true'

    df   = _get_df()
    saved = _load_map()

    # 1) 저장된 맵 먼저 적용
    from_saved = _apply_map(_df_cache, saved)

    if only_saved:
        return Response({
            'source':  'saved',
            'count':   len(from_saved),
            'classified': from_saved,
            'saved_map_size': len(saved),
        })

    # 2) 적용 후에도 기타로 남은 가맹점 추출 (이미 맵에 있는 것 제외)
    remaining = (
        _df_cache[_df_cache['category'] == '기타']
        .groupby('merchant')['amount']
        .sum()
        .sort_values(ascending=False)
        .head(50)
        .index.tolist()
    )
    # 저장된 맵에 이미 있는 가맹점 제외 (API 낭비 방지)
    to_ask = [m for m in remaining if m not in saved]

    if not to_ask:
        return Response({
            'source':   'saved_only',
            'count':    len(from_saved),
            'classified': from_saved,
            'saved_map_size': len(saved),
            'message':  '새로 분류할 가맹점이 없습니다. 저장된 분류만 적용했습니다.',
        })

    category_list  = list(CATEGORY_MAP.keys())
    merchant_lines = '\n'.join(f'- {m}' for m in to_ask)

    prompt = f"""다음은 한국 은행 거래 내역에서 카테고리가 분류되지 않은 가맹점 목록입니다.
각 가맹점을 아래 카테고리 중 하나로 분류해 주세요.

카테고리: {', '.join(category_list)}, 기타

가맹점 목록:
{merchant_lines}

규칙:
- 가맹점명이 사람 이름처럼 보이면 "기타"
- 명확히 분류되지 않으면 "기타"
- 반드시 JSON 형식으로만 응답 (설명 없이): {{"가맹점명": "카테고리", ...}}"""

    try:
        res = requests.post(
            f'{GMS_BASE}/{settings.GMS_MODEL}:generateContent',
            headers={'Content-Type': 'application/json', 'x-goog-api-key': settings.GMS_KEY},
            json={'contents': [{'parts': [{'text': prompt}]}]},
            timeout=30,
        )
        res.raise_for_status()
        raw = res.json()['candidates'][0]['content']['parts'][0]['text']
        raw = re.sub(r'^```(?:json)?\s*', '', raw.strip(), flags=re.MULTILINE)
        raw = re.sub(r'```\s*$', '', raw.strip(), flags=re.MULTILINE)
        mapping: dict = json.loads(raw.strip())
    except Exception as e:
        return Response({'error': f'Gemini 호출 실패: {e}'}, status=status.HTTP_502_BAD_GATEWAY)

    # 3) 영구 저장 (기타가 아닌 것만)
    to_save = {m: c for m, c in mapping.items() if c in category_list and c != '기타'}
    _save_map(to_save)

    # 4) 캐시 df에 적용
    from_ai = _apply_map(_df_cache, to_save)

    return Response({
        'source':         'ai',
        'count':          len(from_saved) + len(from_ai),
        'from_saved':     len(from_saved),
        'from_ai':        len(from_ai),
        'classified':     {**from_saved, **from_ai},
        'saved_map_size': len(_load_map()),
        'asked_gemini':   len(to_ask),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_mapping(request):
    """수동 분류 저장: {merchant, category} → merchant_map.json + 캐시 즉시 적용."""
    global _df_cache
    merchant_name = str(request.data.get('merchant', '')).strip()
    category      = str(request.data.get('category', '')).strip()
    category_list = list(CATEGORY_MAP.keys())

    if not merchant_name:
        return Response({'error': 'merchant가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
    if category not in category_list:
        return Response({'error': f'유효하지 않은 카테고리: {category}'}, status=status.HTTP_400_BAD_REQUEST)

    _save_map({merchant_name: category})
    if _df_cache is not None:
        _apply_map(_df_cache, {merchant_name: category})
    return Response({'success': True, 'merchant': merchant_name, 'category': category,
                     'saved_map_size': len(_load_map())})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def map_status(request):
    """저장된 merchant_map 현황 조회."""
    saved = _load_map()
    return Response({'saved_map_size': len(saved), 'entries': saved})
