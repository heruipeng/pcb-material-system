from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import UserViewSet, PermissionViewSet, RolePermissionViewSet

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('permissions', PermissionViewSet, basename='permission')
router.register('role-permissions', RolePermissionViewSet, basename='role-permission')

urlpatterns = [
    path('', include(router.urls)),
    path('token/', obtain_auth_token, name='api-token'),
]
