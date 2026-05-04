from django.db import models
from django.conf import settings


class Factory(models.Model):
    """工厂/厂区"""
    name = models.CharField('工厂名称', max_length=100)
    code = models.CharField('工厂代码', max_length=20, unique=True)
    address = models.CharField('地址', max_length=200, blank=True)
    phone = models.CharField('电话', max_length=20, blank=True)
    contact = models.CharField('联系人', max_length=50, blank=True)
    
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '工厂'
        verbose_name_plural = '工厂'
        ordering = ['code']
        
    def __str__(self):
        return f"{self.code} - {self.name}"


class SystemConfig(models.Model):
    """系统配置"""
    key = models.CharField('配置键', max_length=100, unique=True)
    value = models.TextField('配置值')
    description = models.TextField('描述', blank=True)
    is_public = models.BooleanField('是否公开', default=False)
    
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '系统配置'
        verbose_name_plural = '系统配置'
        
    def __str__(self):
        return self.key


class OperationLog(models.Model):
    """操作日志"""
    ACTION_CHOICES = [
        ('create', '创建'),
        ('update', '更新'),
        ('delete', '删除'),
        ('view', '查看'),
        ('export', '导出'),
        ('import', '导入'),
        ('login', '登录'),
        ('logout', '登出'),
        ('other', '其他'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                            null=True, verbose_name='用户')
    action = models.CharField('操作类型', max_length=20, choices=ACTION_CHOICES)
    module = models.CharField('模块', max_length=50)
    object_type = models.CharField('对象类型', max_length=50)
    object_id = models.CharField('对象ID', max_length=50, blank=True)
    description = models.TextField('描述')
    ip_address = models.GenericIPAddressField('IP地址', null=True, blank=True)
    user_agent = models.TextField('User Agent', blank=True)
    
    created_at = models.DateTimeField('操作时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '操作日志'
        verbose_name_plural = '操作日志'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['module', '-created_at']),
        ]
        
    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.module}"


class Notification(models.Model):
    """通知消息"""
    TYPE_CHOICES = [
        ('info', '信息'),
        ('warning', '警告'),
        ('error', '错误'),
        ('success', '成功'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                            related_name='notifications', verbose_name='接收人')
    title = models.CharField('标题', max_length=200)
    content = models.TextField('内容')
    notification_type = models.CharField('类型', max_length=20, choices=TYPE_CHOICES, default='info')
    
    # 链接
    link = models.CharField('链接', max_length=500, blank=True)
    
    # 状态
    is_read = models.BooleanField('已读', default=False)
    read_at = models.DateTimeField('阅读时间', null=True, blank=True)
    
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '通知'
        verbose_name_plural = '通知'
        ordering = ['-created_at']
        
    def __str__(self):
        return self.title


class FileStorage(models.Model):
    """文件存储"""
    FILE_TYPE_CHOICES = [
        ('material', '资料文件'),
        ('tool_output', '工具输出'),
        ('report', '报表'),
        ('temp', '临时文件'),
        ('other', '其他'),
    ]
    
    file = models.FileField('文件', upload_to='uploads/%Y/%m/')
    file_name = models.CharField('文件名', max_length=200)
    file_size = models.BigIntegerField('文件大小', default=0)
    file_type = models.CharField('文件类型', max_length=20, choices=FILE_TYPE_CHOICES)
    mime_type = models.CharField('MIME类型', max_length=100, blank=True)
    
    # 关联信息
    related_type = models.CharField('关联对象类型', max_length=50, blank=True)
    related_id = models.CharField('关联对象ID', max_length=50, blank=True)
    
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                   null=True, verbose_name='上传人')
    uploaded_at = models.DateTimeField('上传时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '文件存储'
        verbose_name_plural = '文件存储'
        ordering = ['-uploaded_at']
        
    def __str__(self):
        return self.file_name
