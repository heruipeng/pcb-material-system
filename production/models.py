from django.db import models
from django.conf import settings


class ProductionJob(models.Model):
    """产线作业任务 - 产线过账后由脚本拉取处理的作业"""
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]

    TOOL_TYPE_CHOICES = [
        ('fly_probe', '飞针测试'),
        ('impedance', '阻抗测试'),
        ('aoi', 'AOI检测'),
        ('xray', 'X-Ray检测'),
        ('ict', 'ICT测试'),
        ('functional', '功能测试'),
        ('other', '其他'),
    ]

    # 产线过账数据
    job_no = models.CharField('作业编号', max_length=50, unique=True)
    serial_no = models.CharField('流水号', max_length=50)
    material_no = models.CharField('料号', max_length=50)
    version_code = models.CharField('版本编码', max_length=10)
    factory = models.ForeignKey('core.Factory', on_delete=models.CASCADE, verbose_name='工厂')
    tool_type = models.CharField('工具类型', max_length=20, choices=TOOL_TYPE_CHOICES)

    # 过账原始数据（产线传入的其他字段）
    post_data = models.JSONField('过账数据', default=dict, blank=True)

    # 状态
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')

    # 处理输出（脚本回传）
    output_path = models.CharField('输出路径', max_length=500, blank=True)
    output_files = models.JSONField('输出文件', default=list, blank=True)
    process_log = models.TextField('处理日志', blank=True)
    error_message = models.TextField('错误信息', blank=True)

    # 执行人/脚本标识
    processor = models.CharField('处理脚本', max_length=100, blank=True)

    # 时间轴
    posted_at = models.DateTimeField('过账时间')
    processing_at = models.DateTimeField('开始处理时间', null=True, blank=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)
    duration = models.IntegerField('处理时长(秒)', null=True, blank=True)

    # 重试
    retry_count = models.IntegerField('重试次数', default=0)
    max_retries = models.IntegerField('最大重试次数', default=3)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '产线作业'
        verbose_name_plural = '产线作业'
        ordering = ['-posted_at']
        indexes = [
            models.Index(fields=['status', 'tool_type']),
            models.Index(fields=['job_no']),
            models.Index(fields=['serial_no']),
            models.Index(fields=['posted_at']),
        ]

    def __str__(self):
        return f"{self.job_no} - {self.material_no} [{self.get_status_display()}]"
