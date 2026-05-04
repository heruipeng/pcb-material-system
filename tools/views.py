from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone

from .models import Tool, ToolCategory, ToolExecution, ToolTemplate, ToolOutput
from .serializers import (
    ToolSerializer, ToolCategorySerializer, ToolExecutionSerializer,
    ToolTemplateSerializer, ToolOutputSerializer
)
from accounts.permissions import PERM_TOOL_USE, PERM_TOOL_CONFIG
from core.utils import log_operation


class ToolCategoryViewSet(viewsets.ModelViewSet):
    """工具分类管理"""
    queryset = ToolCategory.objects.filter(is_active=True)
    serializer_class = ToolCategorySerializer
    
    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        return [IsAuthenticated()]


class ToolViewSet(viewsets.ModelViewSet):
    """工具管理"""
    queryset = Tool.objects.filter(is_active=True)
    serializer_class = ToolSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['tool_type', 'category']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']
    
    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """执行工具"""
        if not request.user.has_permission(PERM_TOOL_USE):
            return Response({'error': '没有使用工具的权限'}, status=status.HTTP_403_FORBIDDEN)
        
        tool = self.get_object()
        material_id = request.data.get('material_id')
        params = request.data.get('params', {})
        
        # 创建执行记录
        execution = ToolExecution.objects.create(
            tool=tool,
            material_id=material_id,
            params={**tool.default_params, **params},
            status='pending',
            executor=request.user
        )
        
        # 异步执行工具（实际项目中使用Celery）
        # execute_tool.delay(execution.id)
        
        log_operation(request, 'create', 'tools', 'ToolExecution', execution.id, 
                     f'执行工具 {tool.name}')
        
        return Response({
            'success': True,
            'execution_id': execution.id,
            'status': execution.status
        })
    
    @action(detail=True, methods=['get'])
    def templates(self, request, pk=None):
        """获取工具模板"""
        tool = self.get_object()
        templates = tool.templates.filter(is_active=True)
        serializer = ToolTemplateSerializer(templates, many=True)
        return Response(serializer.data)


class ToolExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """工具执行记录"""
    queryset = ToolExecution.objects.all()
    serializer_class = ToolExecutionSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['tool', 'status', 'executor']
    ordering_fields = ['created_at', 'started_at', 'completed_at']
    ordering = ['-created_at']
    
    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return ToolExecution.objects.all()
        return ToolExecution.objects.filter(executor=user)
    
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
    queryset = ToolTemplate.objects.all()
    serializer_class = ToolTemplateSerializer
    
    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ToolOutputViewSet(viewsets.ReadOnlyModelViewSet):
    """工具输出管理"""
    queryset = ToolOutput.objects.all()
    serializer_class = ToolOutputSerializer
    
    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        return [IsAuthenticated()]
