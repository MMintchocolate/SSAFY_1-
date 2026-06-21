"""
뉴스 기사 DBSCAN 군집화 모듈.

파이프라인:
  1. 제목 + 본문 앞 500자를 합쳐 TF-IDF 벡터화 (한국어는 형태소 분석기 없이
     char n-gram 2~4으로 처리)
  2. TruncatedSVD 로 2D 축소 (희소 행렬 그대로 사용, 메모리 절약)
  3. DBSCAN(metric='cosine') 으로 군집 레이블 부여
  4. 군집별 기사 수 기준 Top-3 추출
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize

# 군집별 색상 (클라이언트에서 참조)
CLUSTER_COLORS = [
    '#3b82f6',  # blue
    '#10b981',  # emerald
    '#f59e0b',  # amber
    '#8b5cf6',  # violet
    '#ef4444',  # red
    '#06b6d4',  # cyan
    '#f97316',  # orange
    '#ec4899',  # pink
    '#84cc16',  # lime
    '#6366f1',  # indigo
]
NOISE_COLOR = '#94a3b8'  # slate


def _color_for(cluster_id: int) -> str:
    if cluster_id < 0:
        return NOISE_COLOR
    return CLUSTER_COLORS[cluster_id % len(CLUSTER_COLORS)]


def run_clustering(news_qs, eps: float = 0.45, min_samples: int = 2) -> dict:
    """
    QuerySet → 군집화 결과 dict 반환.

    Returns:
        {
          points: [{id, title, keyword, cluster, color, x, y}],
          clusters: [{id, size, color, articles:[{id,title,url,keyword,published_date}]}],   # top-3
          noise_count: int,
          total: int,
          n_clusters: int,
        }
    """
    articles = list(news_qs)
    n = len(articles)

    if n < 5:
        return {'error': f'군집화에 필요한 최소 기사 수(5)가 부족합니다. 현재 {n}건'}

    # ── 1. TF-IDF 벡터화 ────────────────────────────────────────────────────
    texts = [f"{a.title} {a.content[:500]}" for a in articles]

    vectorizer = TfidfVectorizer(
        analyzer='char_wb',   # 한국어: 음절 n-gram
        ngram_range=(2, 4),
        max_features=4000,
        min_df=2,
        sublinear_tf=True,
    )
    X = vectorizer.fit_transform(texts)           # sparse (n, vocab)
    X_norm = normalize(X, norm='l2')              # cosine 거리를 위해 L2 정규화

    # ── 2. DBSCAN 군집화 ────────────────────────────────────────────────────
    db = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine', n_jobs=-1)
    labels = db.fit_predict(X_norm)

    # ── 3. 2D 축소 (TruncatedSVD) ────────────────────────────────────────────
    n_components = min(2, n - 1)
    svd = TruncatedSVD(n_components=n_components, random_state=42)
    X_2d = svd.fit_transform(X_norm)             # dense (n, 2)

    if n_components == 1:
        X_2d = np.column_stack([X_2d, np.zeros(n)])

    # ── 4. points 목록 ──────────────────────────────────────────────────────
    points = []
    for i, article in enumerate(articles):
        cid = int(labels[i])
        points.append({
            'id':      article.id,
            'title':   article.title,
            'keyword': article.keyword,
            'cluster': cid,
            'color':   _color_for(cid),
            'x':       round(float(X_2d[i, 0]), 5),
            'y':       round(float(X_2d[i, 1]), 5),
        })

    # ── 5. Top-3 군집 (노이즈 제외, 크기 내림차순) ─────────────────────────
    unique_labels = sorted(set(labels) - {-1})
    cluster_sizes = {lbl: int(np.sum(labels == lbl)) for lbl in unique_labels}
    top3_labels   = sorted(cluster_sizes, key=lambda l: -cluster_sizes[l])[:3]

    clusters = []
    for rank, lbl in enumerate(top3_labels):
        indices = [i for i, l in enumerate(labels) if l == lbl]
        # 대표 기사: published_date 내림차순으로 최대 10개
        rep_articles = sorted(
            [articles[i] for i in indices],
            key=lambda a: a.published_date or __import__('datetime').datetime.min.replace(
                tzinfo=__import__('datetime').timezone.utc
            ),
            reverse=True,
        )[:10]

        clusters.append({
            'id':    int(lbl),
            'rank':  rank + 1,
            'size':  cluster_sizes[lbl],
            'color': _color_for(lbl),
            'articles': [
                {
                    'id':             a.id,
                    'title':          a.title,
                    'url':            a.url,
                    'keyword':        a.keyword,
                    'published_date': a.published_date.isoformat() if a.published_date else None,
                }
                for a in rep_articles
            ],
        })

    return {
        'points':      points,
        'clusters':    clusters,
        'noise_count': int(np.sum(labels == -1)),
        'n_clusters':  len(unique_labels),
        'total':       n,
        'params':      {'eps': eps, 'min_samples': min_samples},
    }
