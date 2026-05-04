from rest_framework import serializers
from .models import Material, MaterialCategory, MaterialHistory, MaterialAttachment


class MaterialCategorySerializer(serializers.ModelSerializer):
    """资料分类序列化器"""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    
    class Meta:
        model = MaterialCategory
        fields = ['id', 'name', 'code', 'parent', 'parent_name', 'description', 'sort_order', 'is_active']


class MaterialListSerializer(serializers.ModelSerializer):
    """资料列表序列化器"""
    factory_name = serializers.CharField(source='factory.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    creator_name = serializers.CharField(source='creator.username', read_only=True)
    maker_name = serializers.CharField(source='maker.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    status_color = serializers.CharField(source='get_status_display_color', read_only=True)
    
    class Meta:
        model = Material
        fields = [
            'id', 'serial_no', 'factory_name', 'material_no', 'version_code',
            'category_name', 'status', 'status_display', 'status_color',
            'remark', 'created_at', 'file_path', 'maker_name', 'creator_name'
        ]


class MaterialSerializer(serializers.ModelSerializer):
    """资料详情序列化器"""
    factory_name = serializers.CharField(source='factory.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    creator_name = serializers.CharField(source='creator.username', read_only=True)
    maker_name = serializers.CharField(source='maker.username', read_only=True)
    approver_name = serializers.CharField(source='approver.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Material
        fields = [
            'id', 'serial_no', 'factory', 'factory_name', 'material_no', 
            'version_code', 'category', 'category_name', 'status', 'status_display',
            'remark', 'file_path', 'file_name', 'file_size',
            'creator', 'creator_name', 'maker', 'maker_name',
            'created_at', 'updated_at', 'completed_at',
            'approver', 'approver_name', 'approved_at', 'approve_remark'
        ]
        read_only_fields = ['serial_no', 'created_at', 'updated_at']


class MaterialHistorySerializer(serializers.ModelSerializer):
    """资料操作历史序列化器"""
    operator_name = serializers.CharField(source='operator.username', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = MaterialHistory
        fields = ['id', 'action', 'action_display', 'operator', 'operator_name', 'remark', 'created_at']


class MaterialAttachmentSerializer(serializers.ModelSerializer):
    """资料附件序列化器"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MaterialAttachment
        fields = ['id', 'material', 'file', 'file_url', 'file_name', 'file_size', 
                 'file_type', 'description', 'uploaded_by', 'uploaded_by_name', 'uploaded_at']
    
    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None
