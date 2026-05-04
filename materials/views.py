from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
from django.utils import timezone

from .models import Material, MaterialCategory, MaterialHistory, MaterialAttachment
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


class MaterialCategoryViewSet(viewsets.ModelViewSet):
    """资料分类管理"""
    queryset = MaterialCategory.objects.filter(is_active=True)
    serializer_class = MaterialCategorySerializer
    
    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        return [IsAuthenticated()]


class MaterialViewSet(viewsets.ModelViewSet):
    """工程资料管理"""
    queryset = Material.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'factory', 'category', 'creator']
    search_fields = ['serial_no', 'material_no', 'remark']
    ordering_fields = ['created_at', 'updated_at', 'serial_no']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MaterialListSerializer
        return MaterialSerializer
    
    def get_queryset(self):
        queryset = Material.objects.all()
        
        # 权限过滤
        user = self.request.user
        if user.role == 'viewer':
            queryset = queryset.filter(status__in=['published', 'archived'])
        elif user.role == 'operator':
            queryset = queryset.filter(
                Q(creator=user) | Q(status__in=['published', 'archived'])
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
            raise PermissionError('没有创建资料的权限')
        
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
            raise PermissionError('没有编辑资料的权限')
        
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
        
        material.status = 'approved'
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
        
        return Response({'status': 'approved'})
    
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
        
        return Response({'status': 'rejected'})
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """发布资料"""
        material = self.get_object()
        material.status = 'published'
        material.save()
        
        MaterialHistory.objects.create(
            material=material,
            action='publish',
            operator=request.user,
            remark='发布资料'
        )
        
        return Response({'status': 'published'})
    
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
    queryset = MaterialAttachment.objects.all()
    serializer_class = MaterialAttachmentSerializer
    
    def get_queryset(self):
        material_id = self.request.query_params.get('material')
        if material_id:
            return MaterialAttachment.objects.filter(material_id=material_id)
        return MaterialAttachment.objects.all()
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
