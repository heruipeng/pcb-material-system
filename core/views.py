
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from materials.models import Material, MaterialCategory
from tools.models import Tool, ToolCategory
from reports.models import Report, ReportCategory
from core.models import Factory


def user_login(request):
    """Custom login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(request.GET.get('next', 'dashboard'))
        else:
            messages.error(request, 'Username or password incorrect')
    return render(request, 'registration/login.html', {})


def user_logout(request):
    logout(request)
    return redirect('login')


@login_required(login_url='/login/')
def dashboard(request):
    """Main dashboard with materials, reports, and admin tabs"""
    return render(request, 'dashboard.html', {
        'total_materials': Material.objects.count(),
        'material_categories': MaterialCategory.objects.filter(is_active=True),
        'materials': Material.objects.select_related('factory', 'category', 'maker').order_by('-created_at')[:50],
        'total_tools': Tool.objects.filter(is_active=True).count(),
        'tool_categories': ToolCategory.objects.filter(is_active=True),
        'tools': Tool.objects.select_related('category').filter(is_active=True),
        'total_reports': Report.objects.filter(is_active=True).count(),
        'report_categories': ReportCategory.objects.filter(is_active=True),
        'reports': Report.objects.select_related('category').filter(is_active=True),
        'factories': Factory.objects.filter(is_active=True),
        'material_status_choices': Material.STATUS_CHOICES,
    })

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Factory, SystemConfig, OperationLog, Notification, FileStorage
from .serializers import (
    FactorySerializer, SystemConfigSerializer, OperationLogSerializer,
    NotificationSerializer, FileStorageSerializer
)


class FactoryViewSet(viewsets.ModelViewSet):
    """工厂管理"""
    queryset = Factory.objects.filter(is_active=True)
    serializer_class = FactorySerializer
    permission_classes = [IsAuthenticated]


class SystemConfigViewSet(viewsets.ModelViewSet):
    """系统配置"""
    queryset = SystemConfig.objects.all()
    serializer_class = SystemConfigSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def get_value(self, request):
        """获取配置值"""
        key = request.query_params.get('key')
        if not key:
            return Response({'error': '请提供配置键'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            config = SystemConfig.objects.get(key=key)
            return Response({'key': key, 'value': config.value})
        except SystemConfig.DoesNotExist:
            return Response({'error': '配置不存在'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def set_value(self, request):
        """设置配置值"""
        key = request.data.get('key')
        value = request.data.get('value')
        
        if not key or value is None:
            return Response({'error': '请提供配置键和值'}, status=status.HTTP_400_BAD_REQUEST)
        
        config, created = SystemConfig.objects.update_or_create(
            key=key,
            defaults={'value': value}
        )
        
        return Response({
            'success': True,
            'key': key,
            'value': value,
            'created': created
        })


class OperationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """操作日志"""
    queryset = OperationLog.objects.all()
    serializer_class = OperationLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['action', 'module', 'user']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return OperationLog.objects.all()
        return OperationLog.objects.filter(user=user)


class NotificationViewSet(viewsets.ModelViewSet):
    """通知管理"""
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """获取未读通知"""
        notifications = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """标记所有通知为已读"""
        self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({'success': True})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """标记通知为已读"""
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        return Response({'success': True})


class FileStorageViewSet(viewsets.ModelViewSet):
    """文件存储管理"""
    queryset = FileStorage.objects.all()
    serializer_class = FileStorageSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """仪表盘统计数据"""
    from materials.models import Material
    from tools.models import ToolExecution
    from reports.models import ReportInstance
    
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    
    # 资料统计
    material_stats = {
        'total': Material.objects.count(),
        'today': Material.objects.filter(created_at__date=today).count(),
        'week': Material.objects.filter(created_at__date__gte=week_start).count(),
        'month': Material.objects.filter(created_at__date__gte=month_start).count(),
        'pending': Material.objects.filter(status='pending').count(),
    }
    
    # 工具执行统计
    tool_stats = {
        'total': ToolExecution.objects.count(),
        'today': ToolExecution.objects.filter(created_at__date=today).count(),
        'week': ToolExecution.objects.filter(created_at__date__gte=week_start).count(),
        'success': ToolExecution.objects.filter(status='completed').count(),
        'failed': ToolExecution.objects.filter(status='failed').count(),
    }
    
    # 报表统计
    report_stats = {
        'total': ReportInstance.objects.count(),
        'today': ReportInstance.objects.filter(generated_at__date=today).count(),
        'week': ReportInstance.objects.filter(generated_at__date__gte=week_start).count(),
    }
    
    # 按状态统计资料
    status_stats = Material.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    return Response({
        'material_stats': material_stats,
        'tool_stats': tool_stats,
        'report_stats': report_stats,
        'status_stats': list(status_stats),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_info(request):
    """系统信息"""
    import django
    import sys
    
    return Response({
        'django_version': django.get_version(),
        'python_version': sys.version,
        'timezone': str(timezone.get_current_timezone()),
    })
