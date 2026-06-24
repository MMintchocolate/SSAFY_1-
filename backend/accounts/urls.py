from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/',         views.register),
    path('login/',            views.login),
    path('logout/',           views.logout),
    path('me/',               views.me),
    path('me/nickname/',           views.update_nickname),
    path('me/cluster-settings/',  views.cluster_settings),
    path('me/password/',      views.change_password),
    path('me/google/password/',      views.change_google_password),
    path('password-reset/confirm/',  views.password_reset_confirm),
    path('token/refresh/',    TokenRefreshView.as_view()),
    
]
