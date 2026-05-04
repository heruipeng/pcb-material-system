from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ToolViewSet, ToolCategoryViewSet, ToolExecutionViewSet,
    ToolTemplateViewSet, ToolOutputViewSet
)

router = DefaultRouter()
router.register('categories', ToolCategoryViewSet, basename='tool-category')
router.register('executions', ToolExecutionViewSet, basename='tool-execution')
router.register('templates', ToolTemplateViewSet, basename='tool-template')
router.register('outputs', ToolOutputViewSet, basename='tool-output')
router.register('', ToolViewSet, basename='tool')

urlpatterns = [
    path('', include(router.urls)),
]
