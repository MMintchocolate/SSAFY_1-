from django.urls import path
from . import views

urlpatterns = [
    path('reverse-geocode/', views.reverse_geocode),
    path('search/',           views.search_branches),
]
