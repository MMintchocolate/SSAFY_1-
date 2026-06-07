from django.urls import path
from . import views

urlpatterns = [
    path('deposit/', views.deposit_list),
    path('savings/', views.savings_list),
]
