import re
import requests
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import News
from .crawler import crawl_news, CRAWL_KEYWORDS
from .cluster import run_clustering

_GMS_URL = (
    'https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com'
    '/v1beta/models/{model}:generateContent'
)


@api_view(['POST'])
def crawl(request):
    """유출/해킹 키워드로 네이버 뉴스 100건씩 크롤링."""
    try:
        results = {}
        for keyword in CRAWL_KEYWORDS:
            results[keyword] = crawl_news(keyword)
        return Response({'success': True, 'saved': results})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def news_list(request):
    """저장된 뉴스 목록 반환. ?keyword=유출|해킹 으로 필터링."""
    keyword = request.query_params.get('keyword', '')
    qs = News.objects.all()
    if keyword:
        qs = qs.filter(keyword=keyword)

    data = [
        {
            'id':             n.id,
            'keyword':        n.keyword,
            'title':          n.title,
            'url':            n.url,
            'content':        n.content,
            'summary':        n.summary,
            'published_date': n.published_date.isoformat() if n.published_date else None,
            'created_at':     n.created_at.isoformat(),
        }
        for n in qs[:300]
    ]
    return Response(data)


@api_view(['GET'])
def cluster(request):
    """DBSCAN 군집화 결과 반환.
    ?keyword=유출|해킹  (없으면 전체)
    ?eps=0.45&min_samples=2  (DBSCAN 파라미터)
    """
    keyword     = request.query_params.get('keyword', '')
    eps         = float(request.query_params.get('eps', 0.45))
    min_samples = int(request.query_params.get('min_samples', 2))

    qs = News.objects.all()
    if keyword:
        qs = qs.filter(keyword=keyword)

    result = run_clustering(qs, eps=eps, min_samples=min_samples)
    if 'error' in result:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)
    return Response(result)


@api_view(['POST'])
def summarize(request, pk):
    """GMS(Gemini)로 기사 요약 생성 후 DB 저장."""
    news = get_object_or_404(News, pk=pk)

    # 이미 요약이 있으면 재사용
    if news.summary:
        return Response({'summary': news.summary, 'cached': True})

    if not settings.GMS_KEY:
        return Response({'error': 'GMS_KEY 환경변수가 설정되지 않았습니다.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    body = news.content.strip() or news.title
    # 토큰 절약: 본문 2000자 이내로 제한
    body_excerpt = body[:2000]

    prompt = f"""다음 보안 뉴스 기사를 한국어로 3~5문장으로 간결하게 요약해줘.
핵심 사건, 피해 규모(있으면), 원인, 대응 방안 순으로 정리해줘.
마크다운이나 제목 없이 순수 텍스트만 출력해.

제목: {news.title}

본문:
{body_excerpt}"""

    try:
        res = requests.post(
            _GMS_URL.format(model=settings.GMS_MODEL),
            headers={
                'Content-Type':  'application/json',
                'x-goog-api-key': settings.GMS_KEY,
            },
            json={'contents': [{'parts': [{'text': prompt}]}]},
            timeout=30,
        )
        res.raise_for_status()
        raw = res.json()['candidates'][0]['content']['parts'][0]['text']
        summary = re.sub(r'\*\*|#+\s*', '', raw).strip()
    except Exception as e:
        return Response({'error': f'요약 생성 실패: {e}'}, status=status.HTTP_502_BAD_GATEWAY)

    news.summary = summary
    news.save(update_fields=['summary'])

    return Response({'summary': summary, 'cached': False})


@api_view(['GET'])
def top3_news(request):
    """홈페이지용 키워드별 최신 뉴스 Top 3."""
    def _serialize(n):
        return {
            'id':             n.id,
            'keyword':        n.keyword,
            'title':          n.title,
            'url':            n.url,
            'summary':        n.summary,
            'published_date': n.published_date.isoformat() if n.published_date else None,
        }

    result = {}
    for kw in CRAWL_KEYWORDS:
        qs = News.objects.filter(keyword=kw).order_by('-published_date')[:3]
        result[kw] = [_serialize(n) for n in qs]

    return Response(result)


@api_view(['GET'])
def news_stats(request):
    """키워드별 저장 건수 반환."""
    stats = {}
    for kw in CRAWL_KEYWORDS:
        stats[kw] = News.objects.filter(keyword=kw).count()
    stats['total'] = News.objects.count()
    return Response(stats)
