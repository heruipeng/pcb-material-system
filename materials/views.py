from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone

from .models import Material, MaterialCategory, MaterialHistory, MaterialAttachment
from core.models import Factory
from .serializers import (
    MaterialSerializer, MaterialListSerializer,
    MaterialCategorySerializer, MaterialHistorySerializer,
    MaterialAttachmentSerializer
)
from accounts.permissions import (
    PERM_MATERIAL_VIEW, PERM_MATERIAL_CREATE,
    PERM_MATERIAL_EDIT, PERM_MATERIAL_DELETE, PERM_MATERIAL_APPROVE
)
from core.utils import log_operation


@login_required(login_url='/login/')
def material_list_page(request):
    """资料总纲页面"""
    queryset = Material.objects.select_related('factory', 'maker', 'creator').all()
    
    # 权限过滤
    user = request.user
    if user.role == 'viewer':
        queryset = queryset.filter(status__in=['completed', 'audited', 'archived'])
    elif user.role == 'operator':
        queryset = queryset.filter(
            Q(creator=user) | Q(status__in=['completed', 'audited', 'archived'])
        )
    
    # 搜索
    keyword = request.GET.get('keyword', '')
    factory_id = request.GET.get('factory', '')
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if keyword:
        queryset = queryset.filter(
            Q(serial_no__icontains=keyword) |
            Q(material_no__icontains=keyword) |
            Q(remark__icontains=keyword)
        )
    if factory_id:
        queryset = queryset.filter(factory_id=factory_id)
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    process_type_filter = request.GET.get('process_type', '')
    if process_type_filter:
        queryset = queryset.filter(process_type=process_type_filter)
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)
    
    # 状态统计（使用权限过滤后的 queryset 统计）
    status_stats = queryset.aggregate(
        all_count=Count('id'),
        unmade_count=Count('id', filter=Q(status='unmade')),
        making_count=Count('id', filter=Q(status='making')),
        completed_count=Count('id', filter=Q(status='completed')),
        audited_count=Count('id', filter=Q(status='audited')),
        rejected_count=Count('id', filter=Q(status='rejected')),
        archived_count=Count('id', filter=Q(status='archived')),
    )
    status_counts = {
        'all': status_stats['all_count'],
        'unmade': status_stats['unmade_count'],
        'making': status_stats['making_count'],
        'completed': status_stats['completed_count'],
        'audited': status_stats['audited_count'],
        'rejected': status_stats['rejected_count'],
        'archived': status_stats['archived_count'],
    }
    
    # 分页
    page_size = int(request.GET.get('page_size', 20))
    page_number = int(request.GET.get('page', 1))
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page_number)
    
    # 添加 maker_name 到每个对象
    for item in page_obj:
        item.maker_name = item.maker.username if item.maker else '-'
        item.status_display = item.get_status_display()
        item.process_type_display = item.get_process_type_display()
    
    context = {
        'page_obj': page_obj,
        'status_counts': status_counts,
        'factories': Factory.objects.filter(is_active=True),
        'page_size': page_size,
    }
    return render(request, 'materials/material_list.html', context)


@login_required(login_url='/login/')
def dashboard_page(request):
    """仪表盘首页"""
    return render(request, 'dashboard.html', {})


def material_detail_page(request, id):
    """资料详情页面"""
    material = get_object_or_404(Material.objects.select_related('factory', 'maker', 'creator', 'category'), pk=id)
    histories = material.histories.all()[:20]
    attachments = material.attachments.all()
    context = {
        'material': material,
        'histories': histories,
        'attachments': attachments,
        'status_display': dict(Material.STATUS_CHOICES).get(material.status, material.status),
        'process_type_display': material.get_process_type_display(),
    }
    return render(request, 'materials/material_detail.html', context)


def tool_detail_page(request, id):
    """工具详情页面"""
    from tools.models import Tool
    tool = get_object_or_404(Tool.objects.select_related('category'), pk=id)
    context = {
        'tool': tool,
        'type_display': dict(Tool.TOOL_TYPE_CHOICES).get(tool.tool_type, tool.tool_type),
    }
    return render(request, 'tools/tool_detail.html', context)


def report_detail_page(request, id):
    """报表详情页面"""
    from reports.models import Report
    report = get_object_or_404(Report.objects.select_related('category', 'created_by'), pk=id)
    instances = report.instances.select_related('generated_by').all()[:20]
    context = {
        'report': report,
        'instances': instances,
        'type_display': dict(Report.REPORT_TYPE_CHOICES).get(report.report_type, report.report_type),
    }
    return render(request, 'reports/report_detail.html', context)


@login_required(login_url='/login/')
def tool_list_page(request):
    """工具管理页面"""
    from tools.models import Tool, ToolExecution
    from django.db.models import Count
    TYPE_ICONS = {
        'fly_probe': 'fa-bolt', 'impedance': 'fa-wave-square', 'aoi': 'fa-eye',
        'xray': 'fa-x-ray', 'ict': 'fa-microchip', 'functional': 'fa-cogs',
    }
    TYPE_COLORS = {
        'fly_probe': '#409EFF', 'impedance': '#67C23A', 'aoi': '#409EFF',
        'xray': '#E6A23C', 'ict': '#F56C6C', 'functional': '#909399',
    }
    tools = []
    for t in Tool.objects.filter(is_active=True):
        tools.append({
            'id': t.id,
            'name': t.name,
            'type': t.tool_type,
            'icon': 'fas ' + TYPE_ICONS.get(t.tool_type, 'fa-tools'),
            'color': TYPE_COLORS.get(t.tool_type, '#909399'),
            'desc': t.description or '',
            'count': ToolExecution.objects.filter(tool=t).count(),
        })
    return render(request, 'tools/tool_list.html', {'tools': tools})


@login_required(login_url='/login/')
def report_list_page(request):
    """报表管理页面"""
    return render(request, 'reports/report_list.html', {})


class MaterialCategoryViewSet(viewsets.ModelViewSet):
    """资料分类管理"""
    queryset = MaterialCategory.objects.filter(is_active=True)
    serializer_class = MaterialCategorySerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['sort_order', 'id']
    ordering = ['sort_order', 'id']


class MaterialViewSet(viewsets.ModelViewSet):
    """工程资料管理 - 完整 CRUD + 审批/生成/统计"""
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'factory', 'category', 'creator', 'process_type']
    search_fields = ['serial_no', 'material_no', 'remark', 'version_code']
    ordering_fields = ['created_at', 'updated_at', 'serial_no', 'status', 'id']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MaterialListSerializer
        return MaterialSerializer
    
    def get_queryset(self):
        queryset = Material.objects.select_related('factory', 'maker', 'creator', 'category').all()
        
        # 权限过滤
        user = self.request.user
        if user.role == 'viewer':
            queryset = queryset.filter(status__in=['completed', 'audited', 'archived'])
        elif user.role == 'operator':
            queryset = queryset.filter(
                Q(creator=user) | Q(status__in=['completed', 'audited', 'archived'])
            )
        
        # 搜索条件
        keyword = self.request.query_params.get('keyword')
        if keyword:
            queryset = queryset.filter(
                Q(serial_no__icontains=keyword) |
                Q(material_no__icontains=keyword) |
                Q(remark__icontains=keyword)
            )
        
        # 日期范围
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset.select_related('factory', 'category', 'creator', 'maker')
    
    def perform_create(self, serializer):
        """创建资料"""
        if not self.request.user.has_permission(PERM_MATERIAL_CREATE):
            raise PermissionDenied('没有创建资料的权限')
        
        material = serializer.save(creator=self.request.user)
        
        # 记录操作历史
        MaterialHistory.objects.create(
            material=material,
            action='create',
            operator=self.request.user,
            remark='创建资料'
        )
        
        # 记录操作日志
        log_operation(self.request, 'create', 'materials', 'Material', material.id, f'创建资料 {material.serial_no}')
    
    def perform_update(self, serializer):
        """更新资料"""
        if not self.request.user.has_permission(PERM_MATERIAL_EDIT):
            raise PermissionDenied('没有编辑资料的权限')
        
        material = serializer.save()
        
        # 记录操作历史
        MaterialHistory.objects.create(
            material=material,
            action='update',
            operator=self.request.user,
            remark='更新资料'
        )
        
        log_operation(self.request, 'update', 'materials', 'Material', material.id, f'更新资料 {material.serial_no}')
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """审批资料"""
        if not request.user.has_permission(PERM_MATERIAL_APPROVE):
            return Response({'error': '没有审批权限'}, status=status.HTTP_403_FORBIDDEN)
        
        material = self.get_object()
        remark = request.data.get('remark', '')
        
        material.status = 'audited'
        material.approver = request.user
        material.approved_at = timezone.now()
        material.approve_remark = remark
        material.save()
        
        # 记录历史
        MaterialHistory.objects.create(
            material=material,
            action='approve',
            operator=request.user,
            remark=f'审批通过: {remark}'
        )
        
        log_operation(request, 'approve', 'materials', 'Material', material.id, f'审批通过资料 {material.serial_no}')
        
        # 自动发送通知给创建者和相关人员
        _send_material_notification(material, 'approve', request.user)
        
        return Response({'status': 'audited'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """驳回资料"""
        if not request.user.has_permission(PERM_MATERIAL_APPROVE):
            return Response({'error': '没有审批权限'}, status=status.HTTP_403_FORBIDDEN)
        
        material = self.get_object()
        remark = request.data.get('remark', '')
        
        material.status = 'rejected'
        material.approver = request.user
        material.approved_at = timezone.now()
        material.approve_remark = remark
        material.save()
        
        MaterialHistory.objects.create(
            material=material,
            action='reject',
            operator=request.user,
            remark=f'审批驳回: {remark}'
        )
        
        log_operation(request, 'reject', 'materials', 'Material', material.id, f'审批驳回资料 {material.serial_no}')
        
        # 自动发送通知
        _send_material_notification(material, 'reject', request.user)
        
        return Response({'status': 'rejected'})
    
    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """生成资料 - 触发工具执行流程"""
        material = self.get_object()
        if material.status not in ['unmade', 'making']:
            return Response(
                {'error': f'当前状态「{material.get_status_display()}」不允许生成'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if material.status == 'unmade':
            material.status = 'making'
            material.maker = request.user
            material.save()

        MaterialHistory.objects.create(
            material=material,
            action='publish',
            operator=request.user,
            remark='生成资料'
        )
        log_operation(request, 'create', 'materials', 'Material', material.id,
                     f'触发生成资料 {material.serial_no}')
        return Response({'success': True, 'status': material.status})

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """发布资料"""
        material = self.get_object()
        material.status = 'completed'
        material.completed_at = timezone.now()
        material.save()
        
        MaterialHistory.objects.create(
            material=material,
            action='publish',
            operator=request.user,
            remark='发布资料'
        )
        
        # 自动发送通知
        _send_material_notification(material, 'publish', request.user)
        
        return Response({'status': 'completed'})
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """获取资料操作历史"""
        material = self.get_object()
        histories = material.histories.all()
        serializer = MaterialHistorySerializer(histories, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """资料统计"""
        from django.db.models import Count
        
        # 按状态统计
        status_stats = Material.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # 按工厂统计
        factory_stats = Material.objects.values('factory__name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # 本月新增
        from datetime import datetime, timedelta
        today = datetime.now()
        month_start = today.replace(day=1)
        month_count = Material.objects.filter(created_at__gte=month_start).count()
        
        return Response({
            'status_stats': list(status_stats),
            'factory_stats': list(factory_stats),
            'month_count': month_count,
            'total_count': Material.objects.count(),
        })


class MaterialAttachmentViewSet(viewsets.ModelViewSet):
    """资料附件管理"""
    queryset = MaterialAttachment.objects.select_related('uploaded_by').all()
    serializer_class = MaterialAttachmentSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['material']
    search_fields = ['file_name', 'description']
    ordering_fields = ['uploaded_at', 'file_size']
    ordering = ['-uploaded_at']
    
    def get_queryset(self):
        material_id = self.request.query_params.get('material')
        if material_id:
            return MaterialAttachment.objects.filter(material_id=material_id)
        return MaterialAttachment.objects.all()
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


# ===== 辅助函数 =====

def _send_material_notification(material, action, operator):
    """资料状态变更时自动创建通知"""
    from core.models import Notification
    
    action_labels = {
        'approve': '已审批',
        'reject': '已驳回',
        'publish': '已发布',
    }
    action_types = {
        'approve': 'success',
        'reject': 'error',
        'publish': 'success',
    }
    
    label = action_labels.get(action, action)
    notif_type = action_types.get(action, 'info')
    link = f'/materials/{material.id}/'
    title = f'资料 {material.serial_no} {label}'
    content = f'资料「{material.serial_no} - {material.material_no}」已被 {operator.username} {label}。'
    
    # 收集需要通知的用户
    recipients = set()
    if material.creator:
        recipients.add(material.creator)
    if material.maker and material.maker != material.creator:
        recipients.add(material.maker)
    
    for user in recipients:
        Notification.objects.create(
            user=user,
            title=title,
            content=content,
            notification_type=notif_type,
            link=link,
        )
