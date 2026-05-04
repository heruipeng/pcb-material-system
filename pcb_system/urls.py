"""
URL configuration for pcb_system project.
"""
from django.contrib import admin
from django.urls import path, include
from core.views import user_login, user_logout, dashboard
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('', dashboard, name='dashboard'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/materials/', include('materials.urls')),
    path('api/tools/', include('tools.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/core/', include('core.urls')),
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
