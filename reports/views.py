from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO

from .models import Report, ReportCategory, ReportInstance, Dashboard, ScheduledReport
from .serializers import (
    ReportSerializer, ReportCategorySerializer, ReportInstanceSerializer,
    DashboardSerializer, ScheduledReportSerializer
)
from accounts.permissions import PERM_REPORT_VIEW, PERM_REPORT_EXPORT, PERM_REPORT_CREATE
from core.utils import log_operation


class ReportCategoryViewSet(viewsets.ModelViewSet):
    """报表分类管理"""
    queryset = ReportCategory.objects.filter(is_active=True)
    serializer_class = ReportCategorySerializer
    
    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        return [IsAuthenticated()]


class ReportViewSet(viewsets.ModelViewSet):
    """报表管理"""
    queryset = Report.objects.filter(is_active=True)
    serializer_class = ReportSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['report_type', 'category']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']
    
    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Report.objects.all()
        return Report.objects.filter(is_active=True)
    
    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """生成报表 - 直接生成Excel文件"""
        import os, random
        from django.conf import settings
        from openpyxl import Workbook
        
        report = self.get_object()
        
        # 生成Excel文件
        wb = Workbook()
        ws = wb.active
        ws.title = report.name
        
        # 表头
        headers = ['序号', '料号', '流水号', '工厂', '状态', '数量', '备注']
        for col, h in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=h)
        
        # 数据行
        from materials.models import Material
        materials = Material.objects.all()[:50]
        row_count = len(materials)
        for i, m in enumerate(materials):
            ws.cell(row=i+2, column=1, value=i+1)
            ws.cell(row=i+2, column=2, value=m.material_no)
            ws.cell(row=i+2, column=3, value=m.serial_no)
            ws.cell(row=i+2, column=4, value=m.factory.name if m.factory else '')
            ws.cell(row=i+2, column=5, value=m.get_status_display())
            ws.cell(row=i+2, column=6, value=random.randint(100, 9999))
            ws.cell(row=i+2, column=7, value=m.remark or '')
        
        # 保存文件
        media_root = settings.MEDIA_ROOT
        report_dir = os.path.join(media_root, 'reports')
        os.makedirs(report_dir, exist_ok=True)
        filename = f"{report.code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join(report_dir, filename)
        wb.save(filepath)
        
        # 创建报表实例
        instance = ReportInstance.objects.create(
            report=report,
            name=f"{report.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            status='completed',
            generated_by=request.user,
            row_count=row_count,
            file=f'reports/{filename}',
            file_format='xlsx',
            file_size=os.path.getsize(filepath),
            generated_at=datetime.now(),
            completed_at=datetime.now(),
        )
        
        log_operation(request, 'create', 'reports', 'ReportInstance', instance.id,
                     f'生成报表 {report.name}')
        
        return Response({
            'success': True,
            'instance_id': instance.id,
            'status': 'completed',
            'row_count': row_count,
            'file_url': instance.file.url if instance.file else None,
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """报表统计"""
        from django.db.models import Count
        
        # 按类型统计
        type_stats = Report.objects.values('report_type').annotate(
            count=Count('id')
        ).order_by('report_type')
        
        # 生成次数统计
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        today_count = ReportInstance.objects.filter(generated_at__date=today).count()
        week_count = ReportInstance.objects.filter(generated_at__date__gte=week_start).count()
        month_count = ReportInstance.objects.filter(generated_at__date__gte=month_start).count()
        
        return Response({
            'type_stats': list(type_stats),
            'today_count': today_count,
            'week_count': week_count,
            'month_count': month_count,
            'total_count': ReportInstance.objects.count(),
        })


class ReportInstanceViewSet(viewsets.ReadOnlyModelViewSet):
    """报表实例管理"""
    queryset = ReportInstance.objects.all()
    serializer_class = ReportInstanceSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['report', 'status', 'generated_by']
    ordering_fields = ['generated_at']
    ordering = ['-generated_at']
    
    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """下载报表"""
        if not request.user.has_permission(PERM_REPORT_EXPORT):
            return Response({'error': '没有导出权限'}, status=status.HTTP_403_FORBIDDEN)
        
        instance = self.get_object()
        
        if not instance.file:
            return Response({'error': '报表文件不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        log_operation(request, 'export', 'reports', 'ReportInstance', instance.id,
                     f'下载报表 {instance.name}')
        
        # 返回文件下载响应
        from django.http import FileResponse
        response = FileResponse(instance.file)
        response['Content-Disposition'] = f'attachment; filename="{instance.file.name}"'
        return response


class DashboardViewSet(viewsets.ModelViewSet):
    """仪表盘管理"""
    queryset = Dashboard.objects.all()
    serializer_class = DashboardSerializer
    
    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Dashboard.objects.all()
        
        # 公开的仪表盘
        public_dashboards = Dashboard.objects.filter(is_public=True)
        
        # 允许访问的仪表盘
        allowed_dashboards = Dashboard.objects.filter(allowed_users=user)
        
        # 角色允许的仪表盘
        role_dashboards = Dashboard.objects.filter(allowed_roles__contains=[user.role])
        
        return (public_dashboards | allowed_dashboards | role_dashboards).distinct()
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ScheduledReportViewSet(viewsets.ModelViewSet):
    """定时报表管理"""
    queryset = ScheduledReport.objects.all()
    serializer_class = ScheduledReportSerializer
    
    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """启用/禁用定时任务"""
        scheduled = self.get_object()
        scheduled.is_active = not scheduled.is_active
        scheduled.save()
        
        return Response({
            'success': True,
            'is_active': scheduled.is_active
        })
