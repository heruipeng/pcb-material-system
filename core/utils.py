from .models import OperationLog


def log_operation(request, action, module, object_type, object_id, description):
    """
    记录操作日志
    
    Args:
        request: HTTP请求对象
        action: 操作类型 (create/update/delete/view/export/import/login/logout/other)
        module: 模块名称
        object_type: 对象类型
        object_id: 对象ID
        description: 操作描述
    """
    try:
        OperationLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action=action,
            module=module,
            object_type=object_type,
            object_id=str(object_id),
            description=description,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    except Exception as e:
        # 日志记录失败不应影响主流程
        print(f"记录操作日志失败: {e}")


def get_client_ip(request):
    """
    获取客户端IP地址
    
    Args:
        request: HTTP请求对象
        
    Returns:
        str: IP地址
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
