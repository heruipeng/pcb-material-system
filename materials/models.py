from django.db import models
from django.conf import settings


class MaterialCategory(models.Model):
    """资料分类"""
    name = models.CharField('分类名称', max_length=50)
    code = models.CharField('分类代码', max_length=20, unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, verbose_name='上级分类')
    description = models.TextField('描述', blank=True)
    sort_order = models.IntegerField('排序', default=0)
    is_active = models.BooleanField('是否启用', default=True)
    
    class Meta:
        verbose_name = '资料分类'
        verbose_name_plural = '资料分类'
        ordering = ['sort_order', 'id']
        
    def __str__(self):
        return self.name


class Material(models.Model):
    """工程资料主表"""
    STATUS_CHOICES = [
        ('unmade', '未制作'),
        ('making', '制作中'),
        ('completed', '已完成'),
        ('audited', '已审核'),
        ('rejected', '已驳回'),
        ('archived', '已归档'),
    ]
    
    PROCESS_TYPE_CHOICES = [
        ('fly_probe', '飞针测试'),
        ('impedance', '阻抗测试'),
        ('aoi', 'AOI检测'),
        ('xray', 'X-Ray检测'),
        ('ict', 'ICT测试'),
        ('functional', '功能测试'),
        ('other', '其他'),
    ]
    
    # 基本信息
    serial_no = models.CharField('流水号', max_length=20, unique=True)
    factory = models.ForeignKey('core.Factory', on_delete=models.CASCADE, verbose_name='工厂')
    material_no = models.CharField('料号', max_length=50)
    version_code = models.CharField('版本编码', max_length=10)
    process_type = models.CharField('工具类型', max_length=20, choices=PROCESS_TYPE_CHOICES, default='other')
    category = models.ForeignKey(MaterialCategory, on_delete=models.SET_NULL, null=True, verbose_name='分类')
    
    # 状态信息
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='unmade')
    remark = models.TextField('备注', blank=True)
    
    # 文件信息
    file_path = models.CharField('文件路径', max_length=500, blank=True)
    file_name = models.CharField('文件名', max_length=200, blank=True)
    file_size = models.BigIntegerField('文件大小', default=0)
    
    # 制作信息
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                null=True, related_name='created_materials', verbose_name='创建人')
    maker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                             null=True, related_name='made_materials', verbose_name='制作人')
    
    # 时间信息
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)
    
    # 审批信息
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                null=True, related_name='approved_materials', verbose_name='审批人')
    approved_at = models.DateTimeField('审批时间', null=True, blank=True)
    approve_remark = models.TextField('审批备注', blank=True)
    
    class Meta:
        verbose_name = '工程资料'
        verbose_name_plural = '工程资料'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['serial_no']),
            models.Index(fields=['material_no']),
            models.Index(fields=['status']),
            models.Index(fields=['factory', 'status']),
            models.Index(fields=['process_type']),
        ]
        
    def __str__(self):
        return f"{self.serial_no} - {self.material_no}"
    
    def get_status_display_color(self):
        """获取状态显示颜色"""
        color_map = {
            'unmade': 'gray',
            'making': 'orange',
            'completed': 'green',
            'audited': 'blue',
            'rejected': 'red',
            'archived': 'purple',
        }
        return color_map.get(self.status, 'gray')


class MaterialHistory(models.Model):
    """资料操作历史"""
    ACTION_CHOICES = [
        ('create', '创建'),
        ('update', '更新'),
        ('delete', '删除'),
        ('approve', '审批'),
        ('reject', '驳回'),
        ('publish', '发布'),
        ('archive', '归档'),
        ('download', '下载'),
    ]
    
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='histories', verbose_name='资料')
    action = models.CharField('操作类型', max_length=20, choices=ACTION_CHOICES)
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='操作人')
    remark = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('操作时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '资料操作历史'
        verbose_name_plural = '资料操作历史'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.material.serial_no} - {self.get_action_display()}"


class MaterialAttachment(models.Model):
    """资料附件"""
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='attachments', verbose_name='资料')
    file = models.FileField('文件', upload_to='materials/%Y/%m/')
    file_name = models.CharField('文件名', max_length=200)
    file_size = models.BigIntegerField('文件大小', default=0)
    file_type = models.CharField('文件类型', max_length=50, blank=True)
    description = models.TextField('描述', blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='上传人')
    uploaded_at = models.DateTimeField('上传时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '资料附件'
        verbose_name_plural = '资料附件'
        ordering = ['-uploaded_at']
        
    def __str__(self):
        return self.file_name
