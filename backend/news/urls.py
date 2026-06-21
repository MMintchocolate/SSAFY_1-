from django.urls import path
from . import views

urlpatterns = [
    path('crawl/',              views.crawl,      name='news-crawl'),
    path('cluster/',            views.cluster,    name='news-cluster'),
    path('stats/',              views.news_stats, name='news-stats'),
    path('top3/',               views.top3_news,  name='news-top3'),
    path('<int:pk>/summarize/', views.summarize,  name='news-summarize'),
    path('',                    views.news_list,  name='news-list'),
]
