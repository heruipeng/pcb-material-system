from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Factory, SystemConfig, OperationLog, Notification, FileStorage


class FactorySerializer(serializers.ModelSerializer):
    """工厂序列化器"""
    class Meta:
        model = Factory
        fields = ['id', 'name', 'code', 'address', 'phone', 'contact', 'is_active', 'created_at']


class SystemConfigSerializer(serializers.ModelSerializer):
    """系统配置序列化器"""
    class Meta:
        model = SystemConfig
        fields = ['id', 'key', 'value', 'description', 'is_public', 'created_at', 'updated_at']


class OperationLogSerializer(serializers.ModelSerializer):
    """操作日志序列化器"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = OperationLog
        fields = [
            'id', 'user', 'user_name', 'action', 'action_display',
            'module', 'object_type', 'object_id', 'description',
            'ip_address', 'created_at'
        ]


class NotificationSerializer(serializers.ModelSerializer):
    """通知序列化器"""
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'content', 'notification_type', 'notification_type_display',
            'link', 'is_read', 'read_at', 'created_at'
        ]


class FileStorageSerializer(serializers.ModelSerializer):
    """文件存储序列化器"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = FileStorage
        fields = [
            'id', 'file', 'file_url', 'file_name', 'file_size',
            'file_type', 'mime_type', 'related_type', 'related_id',
            'uploaded_by', 'uploaded_by_name', 'uploaded_at'
        ]
    
    @extend_schema_field(serializers.URLField)
    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None
