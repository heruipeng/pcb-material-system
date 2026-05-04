from django.db import models
from django.conf import settings


class ReportCategory(models.Model):
    """报表分类"""
    name = models.CharField('分类名称', max_length=50)
    code = models.CharField('分类代码', max_length=20, unique=True)
    description = models.TextField('描述', blank=True)
    sort_order = models.IntegerField('排序', default=0)
    is_active = models.BooleanField('是否启用', default=True)
    
    class Meta:
        verbose_name = '报表分类'
        verbose_name_plural = '报表分类'
        ordering = ['sort_order', 'id']
        
    def __str__(self):
        return self.name


class Report(models.Model):
    """报表定义"""
    REPORT_TYPE_CHOICES = [
        ('summary', '汇总报表'),
        ('detail', '明细报表'),
        ('statistical', '统计报表'),
        ('analysis', '分析报表'),
        ('custom', '自定义报表'),
    ]
    
    name = models.CharField('报表名称', max_length=100)
    code = models.CharField('报表代码', max_length=20, unique=True)
    category = models.ForeignKey(ReportCategory, on_delete=models.SET_NULL, null=True, verbose_name='分类')
    report_type = models.CharField('报表类型', max_length=20, choices=REPORT_TYPE_CHOICES)
    description = models.TextField('描述', blank=True)
    
    # 报表配置
    query_sql = models.TextField('查询SQL', blank=True)
    query_params = models.JSONField('查询参数', default=dict, blank=True)
    column_config = models.JSONField('列配置', default=dict, blank=True)
    chart_config = models.JSONField('图表配置', default=dict, blank=True)
    
    # 状态
    is_active = models.BooleanField('是否启用', default=True)
    is_system = models.BooleanField('系统报表', default=False)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                  null=True, verbose_name='创建人')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '报表'
        verbose_name_plural = '报表'
        ordering = ['category', 'sort_order', 'id']
        
    def __str__(self):
        return self.name


class ReportInstance(models.Model):
    """报表实例"""
    STATUS_CHOICES = [
        ('pending', '生成中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]
    
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='instances', verbose_name='报表')
    name = models.CharField('实例名称', max_length=200)
    
    # 查询条件
    query_params = models.JSONField('查询参数', default=dict)
    date_from = models.DateField('开始日期', null=True, blank=True)
    date_to = models.DateField('结束日期', null=True, blank=True)
    
    # 状态
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # 文件
    file = models.FileField('报表文件', upload_to='reports/%Y/%m/', null=True, blank=True)
    file_format = models.CharField('文件格式', max_length=10, default='xlsx')
    
    # 统计信息
    row_count = models.IntegerField('数据行数', default=0)
    file_size = models.BigIntegerField('文件大小', default=0)
    
    # 生成信息
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, verbose_name='生成人')
    generated_at = models.DateTimeField('生成时间', auto_now_add=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)
    
    class Meta:
        verbose_name = '报表实例'
        verbose_name_plural = '报表实例'
        ordering = ['-generated_at']
        
    def __str__(self):
        return f"{self.report.name} - {self.name}"


class Dashboard(models.Model):
    """仪表盘"""
    name = models.CharField('名称', max_length=100)
    description = models.TextField('描述', blank=True)
    
    # 布局配置
    layout_config = models.JSONField('布局配置', default=dict)
    widgets = models.JSONField('组件配置', default=list)
    
    # 权限
    is_public = models.BooleanField('公开', default=False)
    allowed_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, 
                                          related_name='allowed_dashboards', verbose_name='允许访问的用户')
    allowed_roles = models.JSONField('允许访问的角色', default=list, blank=True)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                  null=True, related_name='created_dashboards', verbose_name='创建人')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '仪表盘'
        verbose_name_plural = '仪表盘'
        ordering = ['-created_at']
        
    def __str__(self):
        return self.name


class ScheduledReport(models.Model):
    """定时报表"""
    FREQUENCY_CHOICES = [
        ('daily', '每天'),
        ('weekly', '每周'),
        ('monthly', '每月'),
        ('quarterly', '每季度'),
    ]
    
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='schedules', verbose_name='报表')
    name = models.CharField('任务名称', max_length=100)
    frequency = models.CharField('频率', max_length=20, choices=FREQUENCY_CHOICES)
    
    # 执行时间
    execute_time = models.TimeField('执行时间', default='08:00')
    execute_day = models.IntegerField('执行日', default=1, help_text='周几或几号')
    
    # 接收人
    recipients = models.JSONField('接收人邮箱', default=list)
    
    # 状态
    is_active = models.BooleanField('是否启用', default=True)
    last_executed = models.DateTimeField('上次执行', null=True, blank=True)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                  null=True, verbose_name='创建人')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '定时报表'
        verbose_name_plural = '定时报表'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.report.name} - {self.get_frequency_display()}"
