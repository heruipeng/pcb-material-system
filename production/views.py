from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import ProductionJob
from .serializers import (
    ProductionJobListSerializer,
    ProductionJobDetailSerializer,
    ProductionPostSerializer,
    ProductionStartSerializer,
    ProductionCompleteSerializer,
)


@extend_schema_view(
    list=extend_schema(summary='产线作业列表', tags=['产线作业']),
    retrieve=extend_schema(summary='产线作业详情', tags=['产线作业']),
)
class ProductionJobViewSet(viewsets.ReadOnlyModelViewSet):
    """产线作业查询（只读）"""
    queryset = ProductionJob.objects.select_related('factory').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'tool_type', 'factory', 'job_no', 'serial_no']
    search_fields = ['job_no', 'serial_no', 'material_no']
    ordering_fields = ['posted_at', 'completed_at', 'duration', 'created_at']
    ordering = ['-posted_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductionJobListSerializer
        return ProductionJobDetailSerializer

    @extend_schema(
        summary='产线过账',
        description='产线系统过账时调用，创建产线作业记录',
        tags=['产线作业'],
        request=ProductionPostSerializer,
        responses={201: ProductionJobDetailSerializer},
    )
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def post(self, request):
        """产线过账 - 创建作业记录"""
        serializer = ProductionPostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = ProductionJob.objects.create(
            status='pending',
            **serializer.validated_data,
        )
        return Response(
            ProductionJobDetailSerializer(job).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary='开始处理',
        description='外部脚本拉取作业后标记开始处理',
        tags=['产线作业'],
        request=ProductionStartSerializer,
        responses={200: ProductionJobDetailSerializer},
    )
    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def start(self, request, pk=None):
        """脚本开始处理作业"""
        job = self.get_object()
        if job.status not in ['pending', 'failed']:
            return Response(
                {'error': f'作业状态 {job.status} 不允许开始处理'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ProductionStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        job.status = 'processing'
        job.processor = serializer.validated_data.get('processor', 'auto_script')
        job.processing_at = timezone.now()
        job.save()

        return Response(ProductionJobDetailSerializer(job).data)

    @extend_schema(
        summary='完成处理',
        description='外部脚本处理完成后上传状态、输出路径、文件等信息',
        tags=['产线作业'],
        request=ProductionCompleteSerializer,
        responses={200: ProductionJobDetailSerializer},
    )
    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def complete(self, request, pk=None):
        """脚本完成处理并上传结果"""
        job = self.get_object()
        if job.status != 'processing':
            return Response(
                {'error': f'作业状态 {job.status} 不允许完成操作'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ProductionCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if data.get('success', True):
            job.status = 'completed'
            job.output_path = data.get('output_path', '')
            job.output_files = data.get('output_files', [])
            job.process_log = data.get('process_log', '')
            job.completed_at = data.get('completed_at') or timezone.now()
            job.duration = data.get('duration')

            # 关联到 Material 表（如果存在）
            try:
                from materials.models import Material
                material = Material.objects.get(serial_no=job.serial_no)
                material.file_path = job.output_path
                material.status = 'completed'
                material.completed_at = job.completed_at
                material.save()
            except Exception:
                pass  # 忽略关联失败

        else:
            job.status = 'failed'
            job.error_message = data.get('error_message', '')
            job.retry_count += 1
            job.completed_at = timezone.now()

        job.save()

        return Response(ProductionJobDetailSerializer(job).data)
