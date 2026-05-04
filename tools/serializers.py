from rest_framework import serializers
from .models import Tool, ToolCategory, ToolExecution, ToolTemplate, ToolOutput


class ToolCategorySerializer(serializers.ModelSerializer):
    """工具分类序列化器"""
    class Meta:
        model = ToolCategory
        fields = ['id', 'name', 'code', 'description', 'icon', 'sort_order', 'is_active']


class ToolSerializer(serializers.ModelSerializer):
    """工具序列化器"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    tool_type_display = serializers.CharField(source='get_tool_type_display', read_only=True)
    
    class Meta:
        model = Tool
        fields = [
            'id', 'name', 'code', 'category', 'category_name', 'tool_type', 
            'tool_type_display', 'description', 'version', 'config_template',
            'default_params', 'is_active', 'is_system', 'created_at', 'updated_at'
        ]


class ToolExecutionSerializer(serializers.ModelSerializer):
    """工具执行记录序列化器"""
    tool_name = serializers.CharField(source='tool.name', read_only=True)
    executor_name = serializers.CharField(source='executor.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    material_serial_no = serializers.CharField(source='material.serial_no', read_only=True)
    
    class Meta:
        model = ToolExecution
        fields = [
            'id', 'tool', 'tool_name', 'material', 'material_serial_no',
            'params', 'status', 'status_display', 'input_files', 'output_files',
            'output_data', 'executor', 'executor_name', 'started_at', 
            'completed_at', 'duration', 'log_output', 'error_message', 'created_at'
        ]


class ToolTemplateSerializer(serializers.ModelSerializer):
    """工具模板序列化器"""
    tool_name = serializers.CharField(source='tool.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ToolTemplate
        fields = [
            'id', 'tool', 'tool_name', 'name', 'description', 'params',
            'is_default', 'is_system', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]


class ToolOutputSerializer(serializers.ModelSerializer):
    """工具输出序列化器"""
    output_type_display = serializers.CharField(source='get_output_type_display', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ToolOutput
        fields = ['id', 'execution', 'output_type', 'output_type_display', 
                 'name', 'file', 'file_url', 'data', 'description', 'created_at']
    
    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None
