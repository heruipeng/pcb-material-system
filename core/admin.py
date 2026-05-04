from django.contrib import admin
from .models import Factory, SystemConfig, OperationLog, Notification, FileStorage


@admin.register(Factory)
class FactoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'address', 'is_active', 'created_at']
    search_fields = ['name', 'code']


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'is_public', 'updated_at']
    search_fields = ['key']


@admin.register(OperationLog)
class OperationLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'module', 'object_type', 'created_at']
    list_filter = ['action', 'module']
    date_hierarchy = 'created_at'
    readonly_fields = ['user', 'action', 'module', 'object_type', 'object_id', 'description', 'ip_address', 'user_agent', 'created_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']


@admin.register(FileStorage)
class FileStorageAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'file_type', 'file_size', 'uploaded_by', 'uploaded_at']
    list_filter = ['file_type']
