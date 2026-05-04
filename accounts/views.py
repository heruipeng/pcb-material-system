from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model

from .models import Permission, RolePermission
from .serializers import (
    UserSerializer, UserCreateSerializer, PermissionSerializer,
    RolePermissionSerializer, LoginSerializer, ChangePasswordSerializer
)
from .permissions import PERMISSIONS, PERMISSION_NAMES
from core.utils import log_operation

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """用户管理"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action in ['login', 'register']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return User.objects.all()
        elif user.role == 'manager':
            return User.objects.filter(department=user.department)
        return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """用户登录"""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            log_operation(request, 'login', 'accounts', 'User', user.id, '用户登录')
            return Response({
                'success': True,
                'user': UserSerializer(user).data
            })
        
        return Response({
            'success': False,
            'error': '用户名或密码错误'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """用户登出"""
        log_operation(request, 'logout', 'accounts', 'User', request.user.id, '用户登出')
        logout(request)
        return Response({'success': True})
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """获取当前用户信息"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """修改密码"""
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'error': '原密码错误'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'success': True})
    
    @action(detail=False, methods=['get'])
    def permissions(self, request):
        """获取当前用户权限"""
        user = request.user
        role_perms = PERMISSIONS.get(user.role, [])
        
        permissions = []
        for perm_code in role_perms:
            permissions.append({
                'code': perm_code,
                'name': PERMISSION_NAMES.get(perm_code, perm_code)
            })
        
        return Response({
            'role': user.role,
            'role_display': user.get_role_display(),
            'permissions': permissions
        })


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """权限管理"""
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]


class RolePermissionViewSet(viewsets.ModelViewSet):
    """角色权限配置"""
    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        role = self.request.query_params.get('role')
        if role:
            return RolePermission.objects.filter(role=role)
        return RolePermission.objects.all()
