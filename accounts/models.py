from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


class User(AbstractUser):
    """自定义用户模型"""
    ROLE_CHOICES = [
        ('admin', '系统管理员'),
        ('manager', '部门经理'),
        ('engineer', '工程师'),
        ('operator', '操作员'),
        ('viewer', '查看者'),
    ]
    
    role = models.CharField('角色', max_length=20, choices=ROLE_CHOICES, default='viewer')
    phone = models.CharField('电话', max_length=20, blank=True)
    department = models.CharField('部门', max_length=50, blank=True)
    factory = models.ForeignKey('core.Factory', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='所属工厂')
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'
        
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def has_permission(self, perm_code):
        """检查用户是否有特定权限"""
        from .permissions import PERMISSIONS
        role_perms = PERMISSIONS.get(self.role, [])
        return perm_code in role_perms


class Permission(models.Model):
    """权限模型"""
    code = models.CharField('权限代码', max_length=50, unique=True)
    name = models.CharField('权限名称', max_length=100)
    description = models.TextField('描述', blank=True)
    
    class Meta:
        verbose_name = '权限'
        verbose_name_plural = '权限'
        
    def __str__(self):
        return self.name


class RolePermission(models.Model):
    """角色权限关联"""
    role = models.CharField('角色', max_length=20, choices=User.ROLE_CHOICES)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, verbose_name='权限')
    
    class Meta:
        verbose_name = '角色权限'
        verbose_name_plural = '角色权限'
        unique_together = ['role', 'permission']


# ====== 信号：自动为用户创建 Token ======
@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
