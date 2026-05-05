"""
Celery Worker 配置
启动命令：celery -A pcb_system worker -l info
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pcb_system.settings')

app = Celery('pcb_system')

# 从 Django settings 加载配置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现任务
app.autodiscover_tasks()

# 定时任务（示例，可按需取消注释）
app.conf.beat_schedule = {
    # 每小时执行一次报表统计
    'report-statistics-hourly': {
        'task': 'reports.tasks.send_report_statistics',
        'schedule': crontab(minute=0),
    },
    # 每天清理过期临时文件
    'cleanup-temp-files-daily': {
        'task': 'core.tasks.cleanup_temp_files',
        'schedule': crontab(hour=3, minute=0),
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """调试任务"""
    print(f'Request: {self.request!r}')
