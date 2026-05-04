from django.db import models
from django.conf import settings


class ToolCategory(models.Model):
    """工具分类"""
    name = models.CharField('分类名称', max_length=50)
    code = models.CharField('分类代码', max_length=20, unique=True)
    description = models.TextField('描述', blank=True)
    icon = models.CharField('图标', max_length=50, blank=True)
    sort_order = models.IntegerField('排序', default=0)
    is_active = models.BooleanField('是否启用', default=True)
    
    class Meta:
        verbose_name = '工具分类'
        verbose_name_plural = '工具分类'
        ordering = ['sort_order', 'id']
        
    def __str__(self):
        return self.name


class Tool(models.Model):
    """工具模型"""
    TOOL_TYPE_CHOICES = [
        ('fly_probe', '飞针测试'),
        ('impedance', '阻抗测试'),
        ('aoi', 'AOI检测'),
        ('xray', 'X-Ray检测'),
        ('ict', 'ICT测试'),
        ('functional', '功能测试'),
        ('other', '其他'),
    ]
    
    name = models.CharField('工具名称', max_length=100)
    code = models.CharField('工具代码', max_length=20, unique=True)
    category = models.ForeignKey(ToolCategory, on_delete=models.SET_NULL, null=True, verbose_name='分类')
    tool_type = models.CharField('工具类型', max_length=20, choices=TOOL_TYPE_CHOICES)
    description = models.TextField('描述', blank=True)
    version = models.CharField('版本', max_length=20, default='1.0')
    sort_order = models.IntegerField(default=0, verbose_name='排序')

    # 配置信息
    config_template = models.JSONField('配置模板', default=dict, blank=True)
    default_params = models.JSONField('默认参数', default=dict, blank=True)
    
    # 状态
    is_active = models.BooleanField('是否启用', default=True)
    is_system = models.BooleanField('系统工具', default=False)
    
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '工具'
        verbose_name_plural = '工具'
        ordering = ['category', 'sort_order', 'id']
        
    def __str__(self):
        return f"{self.name} (v{self.version})"


class ToolExecution(models.Model):
    """工具执行记录"""
    STATUS_CHOICES = [
        ('pending', '等待中'),
        ('running', '执行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    ]
    
    tool = models.ForeignKey(Tool, on_delete=models.CASCADE, related_name='executions', verbose_name='工具')
    material = models.ForeignKey('materials.Material', on_delete=models.CASCADE, 
                                related_name='tool_executions', verbose_name='关联资料')
    
    # 执行信息
    params = models.JSONField('执行参数', default=dict)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # 输入输出
    input_files = models.JSONField('输入文件', default=list)
    output_files = models.JSONField('输出文件', default=list)
    output_data = models.JSONField('输出数据', default=dict, blank=True)
    
    # 执行信息
    executor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                null=True, verbose_name='执行人')
    started_at = models.DateTimeField('开始时间', null=True, blank=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)
    duration = models.IntegerField('执行时长(秒)', null=True, blank=True)
    
    # 日志
    log_output = models.TextField('执行日志', blank=True)
    error_message = models.TextField('错误信息', blank=True)
    
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '工具执行记录'
        verbose_name_plural = '工具执行记录'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.tool.name} - {self.material.serial_no}"


class ToolTemplate(models.Model):
    """工具模板"""
    tool = models.ForeignKey(Tool, on_delete=models.CASCADE, related_name='templates', verbose_name='工具')
    name = models.CharField('模板名称', max_length=100)
    description = models.TextField('描述', blank=True)
    params = models.JSONField('参数配置', default=dict)
    
    is_default = models.BooleanField('默认模板', default=False)
    is_system = models.BooleanField('系统模板', default=False)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                  null=True, verbose_name='创建人')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '工具模板'
        verbose_name_plural = '工具模板'
        ordering = ['-is_default', '-created_at']
        
    def __str__(self):
        return f"{self.tool.name} - {self.name}"


class ToolOutput(models.Model):
    """工具输出"""
    OUTPUT_TYPE_CHOICES = [
        ('file', '文件'),
        ('data', '数据'),
        ('report', '报表'),
        ('chart', '图表'),
    ]
    
    execution = models.ForeignKey(ToolExecution, on_delete=models.CASCADE, 
                                 related_name='outputs', verbose_name='执行记录')
    output_type = models.CharField('输出类型', max_length=20, choices=OUTPUT_TYPE_CHOICES)
    name = models.CharField('名称', max_length=200)
    file = models.FileField('文件', upload_to='tool_outputs/%Y/%m/', null=True, blank=True)
    data = models.JSONField('数据', default=dict, blank=True)
    description = models.TextField('描述', blank=True)
    
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '工具输出'
        verbose_name_plural = '工具输出'
        ordering = ['-created_at']
        
    def __str__(self):
        return self.name
