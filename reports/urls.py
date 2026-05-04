from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ReportViewSet, ReportCategoryViewSet, ReportInstanceViewSet,
    DashboardViewSet, ScheduledReportViewSet
)

router = DefaultRouter()
router.register('categories', ReportCategoryViewSet, basename='report-category')
router.register('instances', ReportInstanceViewSet, basename='report-instance')
router.register('dashboards', DashboardViewSet, basename='dashboard')
router.register('scheduled', ScheduledReportViewSet, basename='scheduled-report')
router.register('', ReportViewSet, basename='report')

urlpatterns = [
    path('', include(router.urls)),
]
