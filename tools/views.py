from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from drf_spectacular.utils import extend_schema

from .models import Tool, ToolCategory, ToolExecution, ToolTemplate, ToolOutput
from .serializers import (
    ToolSerializer, ToolCategorySerializer, ToolExecutionSerializer,
    ToolTemplateSerializer, ToolOutputSerializer
)
from core.utils import log_operation


class ToolCategoryViewSet(viewsets.ModelViewSet):
    """工具分类管理"""
    queryset = ToolCategory.objects.filter(is_active=True)
    serializer_class = ToolCategorySerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['sort_order', 'id']
    ordering = ['sort_order', 'id']


class ToolViewSet(viewsets.ModelViewSet):
    """工具管理 - 完整 CRUD + 执行/模板"""
    queryset = Tool.objects.select_related('category').filter(is_active=True)
    serializer_class = ToolSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['tool_type', 'category', 'is_active']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['created_at', 'name', 'sort_order', 'started_at', 'completed_at']
    ordering = ['sort_order', 'id']

    def get_queryset(self):
        qs = super().get_queryset()
        control = self.request.query_params.get('control', '')
        if control == 'idle':
            qs = qs.filter(started_at__isnull=True, completed_at__isnull=True)
        elif control == 'making':
            qs = qs.filter(started_at__isnull=False, completed_at__isnull=True)
        elif control == 'done':
            qs = qs.filter(completed_at__isnull=False)
        return qs

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """执行工具"""
        tool = self.get_object()
        material_id = request.data.get('material_id')
        params = request.data.get('params', {})
        
        # 参数校验
        if not material_id:
            return Response({'error': '缺少 material_id 参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from materials.models import Material
            material = Material.objects.get(pk=material_id)
        except Material.DoesNotExist:
            return Response({'error': f'资料 ID={material_id} 不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        execution = ToolExecution.objects.create(
            tool=tool,
            material=material,
            params={**tool.default_params, **params},
            status='pending',
            executor=request.user
        )
        
        # 关联资料自动设置状态为制作中
        if material.status == 'unmade':
            material.status = 'making'
            material.maker = request.user
            material.save()

        log_operation(request, 'create', 'tools', 'ToolExecution', execution.id,
                     f'执行工具 {tool.name} 于资料 {material.serial_no}')

        return Response({
            'success': True,
            'execution_id': execution.id,
            'status': execution.status,
            'material_status': material.status,
        })

    @extend_schema(operation_id='tool_instance_templates', summary='获取工具的模板列表')
    @action(detail=True, methods=['get'])
    def templates(self, request, pk=None):
        """获取工具模板"""
        tool = self.get_object()
        templates = tool.templates.all()
        serializer = ToolTemplateSerializer(templates, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """开始制作 - 记录制作时间"""
        tool = self.get_object()
        if tool.started_at:
            return Response({'error': '工具已开始制作', 'started_at': tool.started_at},
                          status=status.HTTP_400_BAD_REQUEST)
        tool.started_at = timezone.now()
        tool.save()
        log_operation(request, 'update', 'tools', 'Tool', tool.id,
                     f'开始制作工具 {tool.name}')
        return Response({'success': True, 'started_at': tool.started_at})

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """完成制作 - 记录完成时间"""
        tool = self.get_object()
        if not tool.started_at:
            return Response({'error': '工具尚未开始制作，请先开始'},
                          status=status.HTTP_400_BAD_REQUEST)
        if tool.completed_at:
            return Response({'error': '工具已完成制作', 'completed_at': tool.completed_at},
                          status=status.HTTP_400_BAD_REQUEST)
        tool.completed_at = timezone.now()
        tool.save()
        log_operation(request, 'update', 'tools', 'Tool', tool.id,
                     f'完成制作工具 {tool.name}')
        return Response({'success': True, 'completed_at': tool.completed_at})


class ToolExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """工具执行记录 - 只读 + 取消/输出"""
    queryset = ToolExecution.objects.select_related('tool', 'material', 'executor').all()
    serializer_class = ToolExecutionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['tool', 'tool__tool_type', 'status', 'executor']
    search_fields = ['material__serial_no', 'failure_reason']
    ordering_fields = ['created_at', 'started_at', 'completed_at', 'duration', 'status']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消执行"""
        execution = self.get_object()
        if execution.status in ['completed', 'failed', 'cancelled']:
            return Response({'error': '当前状态不能取消'}, status=status.HTTP_400_BAD_REQUEST)
        execution.status = 'cancelled'
        execution.save()
        return Response({'status': 'cancelled'})

    @action(detail=True, methods=['get'])
    def outputs(self, request, pk=None):
        """获取执行输出"""
        execution = self.get_object()
        outputs = execution.outputs.all()
        serializer = ToolOutputSerializer(outputs, many=True)
        return Response(serializer.data)


class ToolTemplateViewSet(viewsets.ModelViewSet):
    """工具模板管理"""
    queryset = ToolTemplate.objects.select_related('tool').all()
    serializer_class = ToolTemplateSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['tool', 'is_default']
    search_fields = ['name', 'description']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ToolOutputViewSet(viewsets.ReadOnlyModelViewSet):
    """工具输出管理"""
    queryset = ToolOutput.objects.select_related('execution').all()
    serializer_class = ToolOutputSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['execution']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
