from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/products/', include('products.urls')),
    path('api/receipts/', include('receipts.urls')),
    path('api/branches/', include('branches.urls')),
    path('api/voicephishing/', include('voicephishing.urls')),
    path('api/accounts/', include('accounts.urls')),
    path('api/forms/',    include('docforms.urls')),
    path('api/spending/', include('spending.urls')),
    path('api/news/',    include('news.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
