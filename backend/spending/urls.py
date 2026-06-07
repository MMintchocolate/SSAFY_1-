from django.urls import path
from . import views

urlpatterns = [
    path('stats/',        views.stats),
    path('upload/',       views.upload_csv),
    path('classify-misc/', views.classify_misc),
    path('map-status/',   views.map_status),
    path('add-mapping/',  views.add_mapping),
]
