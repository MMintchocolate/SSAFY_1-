from django.urls import path
from . import views

urlpatterns = [
    path('search/',                   views.search_stocks),
    path('watchlist/',                views.watchlist),
    path('watchlist/<str:symbol>/',   views.watchlist_delete),
    path('<str:symbol>/history/',     views.stock_history),
    path('<str:symbol>/indicators/',  views.stock_indicators),
    path('<str:symbol>/',             views.stock_detail),
]
