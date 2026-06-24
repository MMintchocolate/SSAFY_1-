from django.urls import path
from . import views

urlpatterns = [
    path('',      views.portfolio_list,   name='portfolio-list'),
    path('<int:pk>/', views.portfolio_detail, name='portfolio-detail'),
]
