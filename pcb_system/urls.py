"""
URL configuration for pcb_system project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from materials.views import material_list_page, dashboard_page, tool_list_page, report_list_page

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
    path('tools/', tool_list_page, name='tool-list'),
    path('reports/', report_list_page, name='report-list'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
