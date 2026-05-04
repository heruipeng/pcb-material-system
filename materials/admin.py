from django.contrib import admin
from .models import Material, MaterialCategory, MaterialHistory, MaterialAttachment


@admin.register(MaterialCategory)
class MaterialCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'parent', 'sort_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['serial_no', 'factory', 'material_no', 'version_code', 'status', 'creator', 'created_at']
    list_filter = ['status', 'factory', 'category']
    search_fields = ['serial_no', 'material_no', 'remark']
    date_hierarchy = 'created_at'


@admin.register(MaterialHistory)
class MaterialHistoryAdmin(admin.ModelAdmin):
    list_display = ['material', 'action', 'operator', 'created_at']
    list_filter = ['action']
    date_hierarchy = 'created_at'


@admin.register(MaterialAttachment)
class MaterialAttachmentAdmin(admin.ModelAdmin):
    list_display = ['material', 'file_name', 'file_size', 'uploaded_by', 'uploaded_at']
    search_fields = ['file_name']
