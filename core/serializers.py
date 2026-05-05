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
    
    ALLOWED_EXTENSIONS = ['.zip', '.rar', '.7z', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png', '.gif']
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    class Meta:
        model = FileStorage
        fields = [
            'id', 'file', 'file_url', 'file_name', 'file_size',
            'file_type', 'mime_type', 'related_type', 'related_id',
            'uploaded_by', 'uploaded_by_name', 'uploaded_at'
        ]
    
    def validate_file(self, value):
        import os
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(f'不支持的文件类型：{ext}。允许的类型：{", ".join(self.ALLOWED_EXTENSIONS)}')
        if value.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError(f'文件大小超过限制，最大允许 10MB')
        return value
    
    @extend_schema_field(serializers.URLField)
    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None


# ===== 响应序列化器（用于 swagger 文档） =====

class MaterialStatsSerializer(serializers.Serializer):
    """资料统计"""
    total = serializers.IntegerField()
    today = serializers.IntegerField()
    week = serializers.IntegerField()
    month = serializers.IntegerField()
    unmade = serializers.IntegerField()
    making = serializers.IntegerField()
    completed = serializers.IntegerField()
    audited = serializers.IntegerField()


class ToolStatsSerializer(serializers.Serializer):
    """工具执行统计"""
    total = serializers.IntegerField()
    today = serializers.IntegerField()
    week = serializers.IntegerField()
    completed = serializers.IntegerField()
    failed = serializers.IntegerField()
    running = serializers.IntegerField()
    pending = serializers.IntegerField()


class ReportStatsSerializer(serializers.Serializer):
    """报表统计"""
    total = serializers.IntegerField()
    today = serializers.IntegerField()
    week = serializers.IntegerField()


class StatusCountSerializer(serializers.Serializer):
    """按状态统计"""
    status = serializers.CharField()
    count = serializers.IntegerField()


class DashboardStatsSerializer(serializers.Serializer):
    """仪表盘统计数据响应"""
    material_stats = MaterialStatsSerializer()
    tool_stats = ToolStatsSerializer()
    report_stats = ReportStatsSerializer()
    status_stats = StatusCountSerializer(many=True)


class SystemInfoSerializer(serializers.Serializer):
    """系统信息响应"""
    django_version = serializers.CharField()
    python_version = serializers.CharField()
    os = serializers.CharField()
    timezone = serializers.CharField()


class ApiRootSerializer(serializers.Serializer):
    """API接口总览响应"""
    name = serializers.CharField()
    version = serializers.CharField()
    endpoints = serializers.DictField()
