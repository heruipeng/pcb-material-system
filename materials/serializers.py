from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Material, MaterialCategory, MaterialHistory, MaterialAttachment


class MaterialCategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True, default=None)

    class Meta:
        model = MaterialCategory
        fields = ['id', 'name', 'code', 'parent', 'parent_name', 'description', 'sort_order', 'is_active']


class MaterialListSerializer(serializers.ModelSerializer):
    factory_name = serializers.CharField(source='factory.name', read_only=True, default='')
    category_name = serializers.CharField(source='category.name', read_only=True, default='')
    creator_name = serializers.CharField(source='creator.username', read_only=True, default='')
    maker_name = serializers.CharField(source='maker.username', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    process_type_display = serializers.CharField(source='get_process_type_display', read_only=True)

    class Meta:
        model = Material
        fields = [
            'id', 'serial_no', 'factory_name', 'factory_id', 'material_no', 'version_code',
            'process_type', 'process_type_display', 'category_name', 'category_id',
            'status', 'status_display', 'remark', 'created_at', 'updated_at',
            'file_path', 'maker_name', 'creator_name'
        ]
        read_only_fields = ['serial_no', 'created_at', 'updated_at']


class MaterialSerializer(serializers.ModelSerializer):
    factory_name = serializers.CharField(source='factory.name', read_only=True, default='')
    category_name = serializers.CharField(source='category.name', read_only=True, default='')
    creator_name = serializers.CharField(source='creator.username', read_only=True, default='')
    maker_name = serializers.CharField(source='maker.username', read_only=True, default='')
    approver_name = serializers.CharField(source='approver.username', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    process_type_display = serializers.CharField(source='get_process_type_display', read_only=True)

    class Meta:
        model = Material
        fields = [
            'id', 'serial_no', 'factory', 'factory_name', 'material_no',
            'version_code', 'process_type', 'process_type_display',
            'category', 'category_name', 'status', 'status_display',
            'remark', 'file_path', 'file_name', 'file_size',
            'creator', 'creator_name', 'maker', 'maker_name',
            'created_at', 'updated_at', 'completed_at',
            'approver', 'approver_name', 'approved_at', 'approve_remark'
        ]
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'serial_no': {'required': False, 'allow_blank': True},
        }

    def validate(self, data):
        """创建时检查料号+版本是否重复"""
        if self.instance is None:  # 仅创建时检查
            material_no = data.get('material_no')
            version_code = data.get('version_code')
            if material_no and version_code:
                existing = Material.objects.filter(
                    material_no=material_no,
                    version_code=version_code
                ).first()
                if existing:
                    raise serializers.ValidationError(
                        f'料号「{material_no}」版本「{version_code}」已存在（流水号：{existing.serial_no}），请勿重复创建'
                    )
        return data


class MaterialHistorySerializer(serializers.ModelSerializer):
    operator_name = serializers.CharField(source='operator.username', read_only=True, default='')
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = MaterialHistory
        fields = ['id', 'material', 'action', 'action_display', 'operator', 'operator_name', 'remark', 'created_at']


class MaterialAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True, default='')
    file_url = serializers.SerializerMethodField()
    
    ALLOWED_EXTENSIONS = ['.zip', '.rar', '.7z', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png', '.gif']
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    class Meta:
        model = MaterialAttachment
        fields = ['id', 'material', 'file', 'file_url', 'file_name', 'file_size',
                  'file_type', 'description', 'uploaded_by', 'uploaded_by_name', 'uploaded_at']
    
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
        return obj.file.url if obj.file else None
