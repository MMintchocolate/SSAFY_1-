from django.urls import path
from . import views

urlpatterns = [
    path('search/',           views.search_branches),    # 기능 1: 지역명 기반
    path('search-by-location/', views.search_by_location), # 기능 2: 위경도 기반
    path('reverse-geocode/',  views.reverse_geocode),    # 주소 표시용 프록시
]
