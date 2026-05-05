from rest_framework import serializers
from .models import ProductionJob


class ProductionJobListSerializer(serializers.ModelSerializer):
    """列表序列化器（精简）"""
    factory_name = serializers.CharField(source='factory.name', read_only=True)
    tool_type_display = serializers.CharField(source='get_tool_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ProductionJob
        fields = [
            'id', 'job_no', 'serial_no', 'material_no', 'version_code',
            'factory', 'factory_name', 'tool_type', 'tool_type_display',
            'status', 'status_display', 'posted_at', 'processing_at', 'completed_at',
            'output_path', 'output_files', 'retry_count', 'created_at',
        ]


class ProductionJobDetailSerializer(serializers.ModelSerializer):
    """详情序列化器（完整）"""
    factory_name = serializers.CharField(source='factory.name', read_only=True)
    tool_type_display = serializers.CharField(source='get_tool_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ProductionJob
        fields = '__all__'


class ProductionPostSerializer(serializers.ModelSerializer):
    """产线过账请求"""
    class Meta:
        model = ProductionJob
        fields = [
            'job_no', 'serial_no', 'material_no', 'version_code',
            'factory', 'tool_type', 'post_data', 'posted_at',
        ]

    def validate(self, data):
        # 检查作业编号唯一性
        if ProductionJob.objects.filter(job_no=data.get('job_no')).exists():
            raise serializers.ValidationError({'job_no': '作业编号已存在'})
        return data


class ProductionStartSerializer(serializers.Serializer):
    """开始处理请求"""
    processor = serializers.CharField(max_length=100, required=False, default='auto_script', help_text='处理脚本标识')


class ProductionCompleteSerializer(serializers.Serializer):
    """完成处理请求"""
    output_path = serializers.CharField(max_length=500, required=False, allow_blank=True)
    output_files = serializers.JSONField(required=False, default=list)
    process_log = serializers.CharField(required=False, allow_blank=True)
    completed_at = serializers.DateTimeField(required=False, help_text='完成时间，不传则使用当前时间')
    duration = serializers.IntegerField(required=False, help_text='处理时长(秒)')
    success = serializers.BooleanField(default=True, help_text='是否成功')
    error_message = serializers.CharField(max_length=1000, required=False, allow_blank=True)
