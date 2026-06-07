from django.urls import path
from . import views

urlpatterns = [
    path('', views.receipt_list),
    path('ocr/', views.ocr_receipt),
    path('first/', views.receipt_first),
    path('<int:pk>/', views.receipt_detail),
]
