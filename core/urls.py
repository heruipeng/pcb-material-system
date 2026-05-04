from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FactoryViewSet, SystemConfigViewSet, OperationLogViewSet,
    NotificationViewSet, FileStorageViewSet, dashboard_stats, system_info, api_root
)

router = DefaultRouter()
router.register('factories', FactoryViewSet, basename='factory')
router.register('configs', SystemConfigViewSet, basename='config')
router.register('logs', OperationLogViewSet, basename='log')
router.register('notifications', NotificationViewSet, basename='notification')
router.register('files', FileStorageViewSet, basename='file')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard-stats/', dashboard_stats, name='dashboard-stats'),
    path('system-info/', system_info, name='system-info'),
    path('', api_root, name='api-root'),
]
