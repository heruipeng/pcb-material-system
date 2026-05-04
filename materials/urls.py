from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MaterialViewSet, MaterialCategoryViewSet, MaterialAttachmentViewSet

router = DefaultRouter()
router.register('categories', MaterialCategoryViewSet, basename='material-category')
router.register('', MaterialViewSet, basename='material')
router.register('attachments', MaterialAttachmentViewSet, basename='material-attachment')

urlpatterns = [
    path('', include(router.urls)),
]
