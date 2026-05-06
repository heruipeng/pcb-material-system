from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Count
from datetime import datetime, timedelta

from drf_spectacular.utils import extend_schema
from .models import Factory, SystemConfig, OperationLog, Notification, FileStorage
from .serializers import (
    FactorySerializer, SystemConfigSerializer, OperationLogSerializer,
    NotificationSerializer, FileStorageSerializer,
    DashboardStatsSerializer, SystemInfoSerializer, ApiRootSerializer,
)


class FactoryViewSet(viewsets.ModelViewSet):
    """工厂管理 - 完整 CRUD"""
    queryset = Factory.objects.filter(is_active=True)
    serializer_class = FactorySerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'code', 'address', 'contact']
    ordering_fields = ['created_at', 'id', 'name']
    ordering = ['-created_at']


class SystemConfigViewSet(viewsets.ModelViewSet):
    """系统配置管理"""
    queryset = SystemConfig.objects.all()
    serializer_class = SystemConfigSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['key', 'value', 'description']
    ordering_fields = ['key', 'updated_at']

    @action(detail=False, methods=['get'])
    def get_value(self, request):
        """获取单个配置值"""
        key = request.query_params.get('key')
        if not key:
            return Response({'error': '请提供 key 参数'}, status=400)
        try:
            config = SystemConfig.objects.get(key=key)
            return Response({'key': key, 'value': config.value, 'description': config.description})
        except SystemConfig.DoesNotExist:
            return Response({'key': key, 'value': None, 'message': '配置不存在'})

    @action(detail=False, methods=['post'])
    def set_value(self, request):
        """批量设置配置值"""
        configs = request.data.get('configs', {})
        if not configs:
            return Response({'error': '请提供 configs'}, status=400)
        updated = []
        for key, value in configs.items():
            config, created = SystemConfig.objects.update_or_create(key=key, defaults={'value': str(value)})
            updated.append({'key': key, 'value': value, 'created': created})
        return Response({'success': True, 'updated': updated})


class OperationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """操作日志 - 只读"""
    queryset = OperationLog.objects.select_related('user').all()
    serializer_class = OperationLogSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['action', 'module', 'user']
    search_fields = ['description', 'object_type']
    ordering_fields = ['created_at', 'id']
    ordering = ['-created_at']


class NotificationViewSet(viewsets.ModelViewSet):
    """通知管理"""
    serializer_class = NotificationSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['is_read', 'user']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Notification.objects.filter(user=self.request.user)
        return Notification.objects.none()

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """未读通知"""
        qs = self.get_queryset().filter(is_read=False)
        return Response(NotificationSerializer(qs, many=True).data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """全部标为已读"""
        self.get_queryset().filter(is_read=False).update(is_read=True, read_at=timezone.now())
        return Response({'success': True})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """标记单条已读"""
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        return Response({'success': True})


class FileStorageViewSet(viewsets.ModelViewSet):
    """文件存储管理"""
    queryset = FileStorage.objects.all()
    serializer_class = FileStorageSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['file_type']
    search_fields = ['file_name']
    ordering_fields = ['created_at', 'file_size']

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user if self.request.user.is_authenticated else None)


# ===== 统计与系统信息 API =====

@extend_schema(
    summary='仪表盘统计数据',
    tags=['统计'],
    responses={200: DashboardStatsSerializer},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """首页仪表盘统计数据"""
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
        'completed': ToolExecution.objects.filter(status='completed').count(),
        'failed': ToolExecution.objects.filter(status='failed').count(),
        'running': ToolExecution.objects.filter(status='running').count(),
        'pending': ToolExecution.objects.filter(status='pending').count(),
    }

    # 报表统计
    report_stats = {
        'total': ReportInstance.objects.count(),
        'today': ReportInstance.objects.filter(generated_at__date=today).count(),
        'week': ReportInstance.objects.filter(generated_at__date__gte=week_start).count(),
    }

    # 按状态统计
    status_stats = list(Material.objects.values('status').annotate(count=Count('id')).order_by('status'))

    return Response({
        'material_stats': material_stats,
        'tool_stats': tool_stats,
        'report_stats': report_stats,
        'status_stats': status_stats,
    })


@extend_schema(
    summary='系统信息',
    tags=['系统'],
    responses={200: SystemInfoSerializer},
)
@api_view(['GET'])
def system_info(request):
    """系统信息"""
    import django, sys, platform

    return Response({
        'django_version': django.get_version(),
        'python_version': sys.version.split()[0],
        'os': platform.platform(),
        'timezone': str(timezone.get_current_timezone()),
    })


@extend_schema(
    summary='API接口总览',
    tags=['系统'],
    responses={200: ApiRootSerializer},
)
@api_view(['GET'])
def api_root(request):
    """API 接口总览"""
    return Response({
        'name': '工程资料管理系统 V2.0 API',
        'version': '2.0',
        'endpoints': {
            # 认证
            'auth': {
                'login': 'POST /api/auth/users/login/',
                'logout': 'POST /api/auth/users/logout/',
                'me': 'GET /api/auth/users/me/',
                'change_password': 'POST /api/auth/users/change_password/',
                'permissions': 'GET /api/auth/users/permissions/',
                'users': 'GET/POST /api/auth/users/',
            },
            # 资料
            'materials': {
                'material_list': 'GET/POST /api/materials/',
                'material_detail': 'GET/PUT/PATCH/DELETE /api/materials/{id}/',
                'material_generate': 'POST /api/materials/{id}/generate/',
                'material_approve': 'POST /api/materials/{id}/approve/',
                'material_reject': 'POST /api/materials/{id}/reject/',
                'material_publish': 'POST /api/materials/{id}/publish/',
                'material_history': 'GET /api/materials/{id}/history/',
                'material_statistics': 'GET /api/materials/statistics/',
                'categories': 'GET/POST /api/materials/categories/',
                'attachments': 'GET/POST /api/materials/attachments/',
            },
            # 工具
            'tools': {
                'tool_list': 'GET/POST /api/tools/',
                'tool_detail': 'GET/PUT/PATCH/DELETE /api/tools/{id}/',
                'tool_execute': 'POST /api/tools/{id}/execute/',
                'tool_templates': 'GET /api/tools/{id}/templates/',
                'executions': 'GET /api/tools/executions/',
                'execution_cancel': 'POST /api/tools/executions/{id}/cancel/',
                'execution_outputs': 'GET /api/tools/executions/{id}/outputs/',
                'categories': 'GET/POST /api/tools/categories/',
                'templates': 'GET/POST /api/tools/templates/',
                'outputs': 'GET /api/tools/outputs/',
            },
            # 报表
            'reports': {
                'report_list': 'GET/POST /api/reports/',
                'report_detail': 'GET/PUT/PATCH/DELETE /api/reports/{id}/',
                'report_generate': 'POST /api/reports/{id}/generate/',
                'report_statistics': 'GET /api/reports/statistics/',
                'instances': 'GET /api/reports/instances/',
                'categories': 'GET/POST /api/reports/categories/',
                'dashboards': 'GET/POST /api/reports/dashboards/',
                'scheduled': 'GET/POST /api/reports/scheduled/',
            },
            # 核心
            'core': {
                'factories': 'GET/POST /api/core/factories/',
                'configs': 'GET/POST /api/core/configs/',
                'config_get': 'GET /api/core/configs/get_value/?key=site_name',
                'config_set': 'POST /api/core/configs/set_value/',
                'logs': 'GET /api/core/logs/',
                'notifications': 'GET/POST /api/core/notifications/',
                'files': 'GET/POST /api/core/files/',
                'dashboard_stats': 'GET /api/core/dashboard-stats/',
                'system_info': 'GET /api/core/system-info/',
            },
        },
        'filter_params': {
            'materials': '?status=completed&process_type=fly_probe&factory=1&search=keyword&ordering=-created_at',
            'tools': '?tool_type=fly_probe&category=1&search=keyword&ordering=name',
            'executions': '?status=failed&tool__tool_type=fly_probe&search=serial&ordering=-duration',
            'reports': '?report_type=summary&search=keyword&ordering=name',
            'logs': '?action=create&module=materials&ordering=-created_at',
        },
    })

# ===== 自定义登录视图 =====
from django.contrib.auth import authenticate, login as auth_login, get_user_model
from django.contrib.auth.views import LoginView

User = get_user_model()


class CustomLoginView(LoginView):
    """自定义登录视图 - 区分停用和密码错误"""
    template_name = 'login.html'

    def form_invalid(self, form):
        username = form.data.get('username', '')
        if username:
            try:
                user = User.objects.get(username=username)
                if not user.is_active:
                    form.add_error(None, '用户名或密码错误，请重新输入')
                    return self.render_to_response(self.get_context_data(form=form))
            except User.DoesNotExist:
                pass
        form.add_error(None, '用户名或密码错误，请重新输入')
        return self.render_to_response(self.get_context_data(form=form))


@login_required(login_url='/login/')
def manage_users(request):
    """用户管理页面"""
    from accounts.models import User as AUser
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

            if AUser.objects.filter(username=username).exists():
                messages.error(request, f'用户名 {username} 已存在')
            else:
                user = AUser.objects.create(
                    username=username, role=role,
                    department=department, factory_id=factory_id,
                    is_staff=is_staff
                )
                user.set_password(password)
                user.save()
                messages.success(request, f'用户 {username} 创建成功')

        elif action == 'edit':
            user_id = request.POST.get('user_id')
            user = get_object_or_404(AUser, pk=user_id)
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
            user = get_object_or_404(AUser, pk=user_id)
            if user.username == 'admin':
                messages.error(request, '不能删除超级管理员')
            else:
                uname = user.username
                user.delete()
                messages.success(request, f'用户 {uname} 已删除')

        elif action == 'toggle_active':
            user_id = request.POST.get('user_id')
            user = get_object_or_404(AUser, pk=user_id)
            user.is_active = not user.is_active
            user.save()
            st = '启用' if user.is_active else '停用'
            messages.success(request, f'用户 {user.username} 已{st}')

        return redirect('manage-users')

    users = AUser.objects.select_related('factory').all().order_by('-created_at')
    return render(request, 'core/manage_users.html', {
        'users': users,
        'factories': factories,
        'role_choices': AUser.ROLE_CHOICES,
    })


@login_required(login_url='/login/')
def system_settings(request):
    """系统设置页面"""
    from core.models import SystemConfig as SConfig, OperationLog as OLog

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'save_config':
            key = request.POST.get('key', '').strip()
            value = request.POST.get('value', '')
            desc = request.POST.get('description', '')
            SConfig.objects.update_or_create(key=key, defaults={'value': value, 'description': desc})
            messages.success(request, f'配置 {key} 已保存')
        elif action == 'delete_config':
            key = request.POST.get('key', '')
            SConfig.objects.filter(key=key).delete()
            messages.success(request, f'配置 {key} 已删除')
        return redirect('system-settings')

    configs = SConfig.objects.all().order_by('key')
    logs = OLog.objects.select_related('user').all().order_by('-created_at')[:50]

    today = timezone.now().date()
    log_stats = {
        'total': OLog.objects.count(),
        'today': OLog.objects.filter(created_at__date=today).count(),
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
