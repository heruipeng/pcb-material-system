from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from .permissions import PERMISSIONS


class PermissionMiddleware(MiddlewareMixin):
    """权限中间件 - 检查用户是否有权限访问特定功能"""

    def _authenticate_token(self, request):
        """尝试用 DRF Token 认证用户（API 调用用）"""
        auth = request.META.get('HTTP_AUTHORIZATION', '')
        if auth.startswith('Token '):
            try:
                token = Token.objects.select_related('user').get(key=auth[6:])
                request.user = token.user
                request._token_auth = True
            except Token.DoesNotExist:
                pass

    def process_request(self, request):
        # 跳过不需要权限检查的URL
        exempt_paths = [
            '/admin/',
            '/api/auth/login/',
            '/api/auth/register/',
            '/api/auth/token/',
            '/api/production/',
            '/static/',
            '/media/',
        ]
        
        path = request.path
        for exempt in exempt_paths:
            if path.startswith(exempt):
                return None
        
        # 对 API 请求，先尝试用 Token 认证
        if path.startswith('/api/'):
            self._authenticate_token(request)

        # 检查用户是否已认证
        if not request.user.is_authenticated:
            if path.startswith('/api/'):
                return JsonResponse({'error': '未登录'}, status=401)
            return None
        
        # 检查API权限
        if path.startswith('/api/'):
            # 资料管理权限检查
            if '/materials/' in path:
                if not self._check_material_permission(request):
                    return JsonResponse({'error': '没有权限访问资料管理'}, status=403)
            
            # 工具管理权限检查
            elif '/tools/' in path:
                if not self._check_tool_permission(request):
                    return JsonResponse({'error': '没有权限访问工具管理'}, status=403)
            
            # 报表管理权限检查
            elif '/reports/' in path:
                if not self._check_report_permission(request):
                    return JsonResponse({'error': '没有权限访问报表管理'}, status=403)
        
        return None
    
    def _check_material_permission(self, request):
        """检查资料管理权限"""
        user = request.user
        if user.role == 'admin':
            return True
        
        method = request.method
        if method in ['GET', 'HEAD', 'OPTIONS']:
            return 'material.view' in PERMISSIONS.get(user.role, [])
        elif method == 'POST':
            return 'material.create' in PERMISSIONS.get(user.role, [])
        elif method in ['PUT', 'PATCH']:
            return 'material.edit' in PERMISSIONS.get(user.role, [])
        elif method == 'DELETE':
            return 'material.delete' in PERMISSIONS.get(user.role, [])
        
        return False
    
    def _check_tool_permission(self, request):
        """检查工具管理权限"""
        user = request.user
        if user.role == 'admin':
            return True
        
        return 'tool.use' in PERMISSIONS.get(user.role, [])
    
    def _check_report_permission(self, request):
        """检查报表管理权限"""
        user = request.user
        if user.role == 'admin':
            return True
        
        return 'report.view' in PERMISSIONS.get(user.role, [])
