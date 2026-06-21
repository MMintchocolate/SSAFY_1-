import re
import html
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.utils import parsedate_to_datetime

import requests
from bs4 import BeautifulSoup
from django.conf import settings

CRAWL_KEYWORDS = ['유출', '해킹']
_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    )
}


def _strip_html(text: str) -> str:
    text = html.unescape(text or '')
    return re.sub(r'<[^>]+>', '', text).strip()


def _fetch_news_api(keyword: str, display: int = 100) -> list:
    res = requests.get(
        'https://openapi.naver.com/v1/search/news.json',
        params={'query': keyword, 'display': display, 'sort': 'date'},
        headers={
            'X-Naver-Client-Id':     settings.NAVER_SEARCH_CLIENT_ID,
            'X-Naver-Client-Secret': settings.NAVER_SEARCH_CLIENT_SECRET,
        },
        timeout=10,
    )
    res.raise_for_status()
    return res.json().get('items', [])


def _scrape_naver_content(url: str) -> str | None:
    """네이버 뉴스 기사 본문 스크래핑."""
    try:
        res = requests.get(url, headers=_HEADERS, timeout=6)
        soup = BeautifulSoup(res.text, 'html.parser')
        body = (
            soup.select_one('#dic_area')
            or soup.select_one('#articleBodyContents')
            or soup.select_one('article')
        )
        if body:
            for tag in body.select('script, style, .img_desc, .caption'):
                tag.decompose()
            text = body.get_text(separator='\n').strip()
            text = re.sub(r'\n{3,}', '\n\n', text)
            return text if len(text) > 50 else None
    except Exception:
        pass
    return None


def crawl_news(keyword: str) -> int:
    """키워드로 네이버 뉴스 100개 크롤링 후 DB 저장. 저장된 건수 반환."""
    from .models import News

    items = _fetch_news_api(keyword, display=100)

    articles = []
    for item in items:
        url = item.get('link', '')
        title = _strip_html(item.get('title', ''))
        description = _strip_html(item.get('description', ''))
        try:
            pub_date = parsedate_to_datetime(item['pubDate'])
        except Exception:
            pub_date = None
        articles.append({
            'title': title,
            'url': url,
            'description': description,
            'pub_date': pub_date,
            'is_naver': 'n.news.naver.com' in url,
        })

    # 네이버 뉴스 링크 본문 병렬 스크래핑
    def _fetch(article):
        if article['is_naver']:
            content = _scrape_naver_content(article['url'])
            return content or article['description']
        return article['description']

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_article = {executor.submit(_fetch, a): a for a in articles}
        for future in as_completed(future_to_article):
            article = future_to_article[future]
            try:
                article['content'] = future.result()
            except Exception:
                article['content'] = article['description']

    saved = 0
    for article in articles:
        if not article['url'] or News.objects.filter(url=article['url']).exists():
            continue
        News.objects.create(
            keyword=keyword,
            title=article['title'],
            url=article['url'],
            content=article.get('content', article['description']),
            published_date=article['pub_date'],
        )
        saved += 1

    return saved
