from rest_framework import serializers
from .models import Report, ReportCategory, ReportInstance, Dashboard, ScheduledReport


class ReportCategorySerializer(serializers.ModelSerializer):
    """报表分类序列化器"""
    class Meta:
        model = ReportCategory
        fields = ['id', 'name', 'code', 'description', 'sort_order', 'is_active']


class ReportSerializer(serializers.ModelSerializer):
    """报表序列化器"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'name', 'code', 'category', 'category_name', 'report_type',
            'report_type_display', 'description', 'query_sql', 'query_params',
            'column_config', 'chart_config', 'is_active', 'is_system',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]


class ReportInstanceSerializer(serializers.ModelSerializer):
    """报表实例序列化器"""
    report_name = serializers.CharField(source='report.name', read_only=True)
    generated_by_name = serializers.CharField(source='generated_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ReportInstance
        fields = [
            'id', 'report', 'report_name', 'name', 'query_params',
            'date_from', 'date_to', 'status', 'status_display',
            'file', 'file_url', 'file_format', 'row_count', 'file_size',
            'generated_by', 'generated_by_name', 'generated_at', 'completed_at'
        ]
    
    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None


class DashboardSerializer(serializers.ModelSerializer):
    """仪表盘序列化器"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Dashboard
        fields = [
            'id', 'name', 'description', 'layout_config', 'widgets',
            'is_public', 'allowed_users', 'allowed_roles',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]


class ScheduledReportSerializer(serializers.ModelSerializer):
    """定时报表序列化器"""
    report_name = serializers.CharField(source='report.name', read_only=True)
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ScheduledReport
        fields = [
            'id', 'report', 'report_name', 'name', 'frequency',
            'frequency_display', 'execute_time', 'execute_day',
            'recipients', 'is_active', 'last_executed',
            'created_by', 'created_by_name', 'created_at'
        ]
