from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
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
        'unmade': Material.objects.filter(status='unmade').count(),
        'making': Material.objects.filter(status='making').count(),
        'completed': Material.objects.filter(status='completed').count(),
        'audited': Material.objects.filter(status='audited').count(),
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


# ===== 用户管理页面 =====
@login_required(login_url='/login/')
def manage_users(request):
    """用户管理 - V2.0 风格页面"""
    from accounts.models import User, Permission, RolePermission
    from core.models import Factory

    factories = Factory.objects.filter(is_active=True)

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'create':
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')
            role = request.POST.get('role', 'viewer')
            department = request.POST.get('department', '')
            factory_id = request.POST.get('factory', '') or None
            is_staff = request.POST.get('is_staff') == 'on'

            if User.objects.filter(username=username).exists():
                messages.error(request, f'用户名 {username} 已存在')
            else:
                user = User.objects.create(
                    username=username, role=role,
                    department=department, factory_id=factory_id,
                    is_staff=is_staff
                )
                user.set_password(password)
                user.save()
                messages.success(request, f'用户 {username} 创建成功')

        elif action == 'edit':
            user_id = request.POST.get('user_id')
            user = get_object_or_404(User, pk=user_id)
            user.role = request.POST.get('role', user.role)
            user.department = request.POST.get('department', user.department)
            user.factory_id = request.POST.get('factory') or None
            user.is_staff = request.POST.get('is_staff') == 'on'
            user.is_active = request.POST.get('is_active') == 'on'
            new_pw = request.POST.get('password', '')
            if new_pw:
                user.set_password(new_pw)
            user.save()
            messages.success(request, f'用户 {user.username} 已更新')

        elif action == 'delete':
            user_id = request.POST.get('user_id')
            user = get_object_or_404(User, pk=user_id)
            if user.username == 'admin':
                messages.error(request, '不能删除超级管理员')
            else:
                uname = user.username
                user.delete()
                messages.success(request, f'用户 {uname} 已删除')

        elif action == 'toggle_active':
            user_id = request.POST.get('user_id')
            user = get_object_or_404(User, pk=user_id)
            user.is_active = not user.is_active
            user.save()
            st = '启用' if user.is_active else '停用'
            messages.success(request, f'用户 {user.username} 已{st}')

        return redirect('manage-users')

    users = User.objects.select_related('factory').all().order_by('-created_at')
    return render(request, 'core/manage_users.html', {
        'users': users,
        'factories': factories,
        'role_choices': User.ROLE_CHOICES,
    })


# ===== 系统设置页面 =====
@login_required(login_url='/login/')
def system_settings(request):
    """系统设置 - V2.0 风格页面"""
    from core.models import SystemConfig, OperationLog
    from django.db.models import Count

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'save_config':
            key = request.POST.get('key', '').strip()
            value = request.POST.get('value', '')
            desc = request.POST.get('description', '')
            SystemConfig.objects.update_or_create(
                key=key,
                defaults={'value': value, 'description': desc}
            )
            messages.success(request, f'配置 {key} 已保存')
        elif action == 'delete_config':
            key = request.POST.get('key', '')
            SystemConfig.objects.filter(key=key).delete()
            messages.success(request, f'配置 {key} 已删除')

        return redirect('system-settings')

    configs = SystemConfig.objects.all().order_by('key')

    # 最近 50 条操作日志
    logs = OperationLog.objects.select_related('user').all().order_by('-created_at')[:50]

    # 日志统计
    today = timezone.now().date()
    log_stats = {
        'total': OperationLog.objects.count(),
        'today': OperationLog.objects.filter(created_at__date=today).count(),
        'by_module': list(OperationLog.objects.values('module').annotate(c=Count('id')).order_by('-c')[:10]),
    }

    import django, sys, platform
    system_info = {
        'django': django.get_version(),
        'python': sys.version.split()[0],
        'os': platform.platform(),
        'db': 'MySQL (192.168.127.131)',
    }

    return render(request, 'core/system_settings.html', {
        'configs': configs,
        'logs': logs,
        'log_stats': log_stats,
        'system_info': system_info,
    })
