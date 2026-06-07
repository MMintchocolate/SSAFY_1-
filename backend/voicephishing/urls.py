from django.urls import path
from . import views

urlpatterns = [
    path('analyze/', views.analyze, name='vp_analyze'),
    path('history/', views.history, name='vp_history'),
]
