from django.urls import path
from . import views

urlpatterns = [
    path('',                views.chat,            name='chatbot-chat'),
    path('investment-type/', views.investment_type, name='investment-type'),
]
