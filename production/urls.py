from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductionJobViewSet

router = DefaultRouter()
router.register('jobs', ProductionJobViewSet, basename='production-job')

urlpatterns = [
    path('', include(router.urls)),
]
