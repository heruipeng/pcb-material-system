"""
URL configuration for pcb_system project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from materials.views import material_list_page, dashboard_page, tool_list_page, report_list_page, material_detail_page, tool_detail_page, report_detail_page
from core.views import manage_users, system_settings, CustomLoginView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/materials/', include('materials.urls')),
    path('api/tools/', include('tools.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/core/', include('core.urls')),
    
    # 页面路由
    path('', dashboard_page, name='dashboard'),
    path('materials/', material_list_page, name='material-list'),
    path('materials/<int:id>/', material_detail_page, name='material-detail'),
    path('tools/', tool_list_page, name='tool-list'),
    path('tools/<int:id>/', tool_detail_page, name='tool-detail'),
    path('reports/', report_list_page, name='report-list'),
    path('reports/<int:id>/', report_detail_page, name='report-detail'),
    path('users/', manage_users, name='manage-users'),
    path('system/', system_settings, name='system-settings'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
