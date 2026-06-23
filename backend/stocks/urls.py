from django.urls import path
from . import views, ml_views

urlpatterns = [
    path('search/',                   views.search_stocks),
    path('gold/',                     views.gold_price),
    path('ml/script/',               views.ml_download_script),
    path('ml/generate/',             views.ml_generate_dataset),
    path('ml/train/',                ml_views.ml_train),
    path('ml/predict/',              ml_views.ml_predict),
    path('ml/status/',               ml_views.ml_status),
    path('stock-name/',               views.receive_stock_name),
    path('watchlist/',                views.watchlist),
    path('watchlist/<str:symbol>/',   views.watchlist_delete),
    path('<str:symbol>/history/',     views.stock_history),
    path('<str:symbol>/indicators/',  views.stock_indicators),
    path('<str:symbol>/',             views.stock_detail),
]
