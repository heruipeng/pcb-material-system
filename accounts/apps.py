from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = '用户管理'

    def ready(self):
        import accounts.models  # noqa: 注册信号
