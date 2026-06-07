from django.urls import path
from . import views

urlpatterns = [
    path('classify/', views.classify),
    path('render/',   views.render_form),
]
