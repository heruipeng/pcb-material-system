"""
初始化测试数据命令
用法: python manage.py init_test_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
import random

User = get_user_model()

SAMPLE_DATA = [
    {
        'serial_no': '19095613', 'factory_code': '228', 'material_no': '100379441X1499C',
        'version_code': '02', 'remark': 'None',
        'created_at': '2026-05-03 15:19:12', 'maker': '张工',
        'file_path': '', 'status': 'unmade',
    },
    {
        'serial_no': '19095328', 'factory_code': '168', 'material_no': '100516862X0499A',
        'version_code': '01', 'remark': 'None',
        'created_at': '2026-05-03 14:28:38', 'maker': '李工',
        'file_path': '', 'status': 'unmade',
    },
    {
        'serial_no': '19095223', 'factory_code': '168', 'material_no': '100504099X0299B',
        'version_code': '01', 'remark': '工程资料已于20260328 02:26:07 输出2',
        'created_at': '2026-05-03 13:58:13', 'maker': '王工',
        'file_path': r'\\zhfile01\Product\08-ENG\WorkingFiles\LDI\外层抗氧化金LDI\504099X\0299\B\01\\',
        'status': 'unmade',
    },
    {
        'serial_no': '19094778', 'factory_code': '168', 'material_no': '100528821J0499B',
        'version_code': '01', 'remark': '工程资料已于20260325 03:34:14 输出1',
        'created_at': '2026-05-03 09:58:54', 'maker': '赵工',
        'file_path': r'\\zhfile01\Product\08-ENG\WorkingFiles\FPT\528821J\0499\B\01\\',
        'status': 'completed',
    },
    {
        'serial_no': '19094647', 'factory_code': '168', 'material_no': '100528818V0199A',
        'version_code': '01', 'remark': '工程资料已于20260325 02:36:38 输出1',
        'created_at': '2026-05-03 09:33:30', 'maker': '孙工',
        'file_path': r'\\zhfile01\Product\08-ENG\WorkingFiles\FPT\528818V\0199\A\01\\',
        'status': 'completed',
    },
    {
        'serial_no': '19094410', 'factory_code': '228', 'material_no': '100425066X0299B',
        'version_code': '01', 'remark': '工程资料已于20260324 17:04:35 输出2',
        'created_at': '2026-05-03 08:03:34', 'maker': '周工',
        'file_path': r'\\zhfile01\Product\08-ENG\WorkingFiles\FPT\425066X\0299\B\01\\',
        'status': 'completed',
    },
    {
        'serial_no': '19093961', 'factory_code': '228', 'material_no': '100447563X0298C',
        'version_code': '01', 'remark': 'None',
        'created_at': '2026-05-02 21:43:17', 'maker': '吴工',
        'file_path': '', 'status': 'making',
    },
    {
        'serial_no': '19093959', 'factory_code': '168', 'material_no': '100411149X0299A',
        'version_code': '01', 'remark': 'None',
        'created_at': '2026-05-02 21:42:49', 'maker': '郑工',
        'file_path': '', 'status': 'making',
    },
    {
        'serial_no': '19093940', 'factory_code': '228', 'material_no': '100433375X0299A',
        'version_code': '02', 'remark': 'None',
        'created_at': '2026-05-02 21:05:49', 'maker': '钱工',
        'file_path': '', 'status': 'unmade',
    },
    {
        'serial_no': '19093939', 'factory_code': '168', 'material_no': '100483407X0299B',
        'version_code': '02', 'remark': 'None',
        'created_at': '2026-05-02 21:05:49', 'maker': '冯工',
        'file_path': '', 'status': 'audited',
    },
    {
        'serial_no': '19093938', 'factory_code': '168', 'material_no': '100522968X0499A',
        'version_code': '01', 'remark': 'None',
        'created_at': '2026-05-02 21:05:49', 'maker': '陈工',
        'file_path': '', 'status': 'audited',
    },
    {
        'serial_no': '19093937', 'factory_code': '228', 'material_no': '100533794X0299B',
        'version_code': '01', 'remark': 'None',
        'created_at': '2026-05-02 21:05:49', 'maker': '刘工',
        'file_path': '', 'status': 'rejected',
    },
    {
        'serial_no': '19093936', 'factory_code': '228', 'material_no': '100413955X0499A',
        'version_code': '02', 'remark': 'None',
        'created_at': '2026-05-02 21:05:49', 'maker': '黄工',
        'file_path': '', 'status': 'completed',
    },
]


class Command(BaseCommand):
    help = '初始化飞针测试资料管理系统测试数据'

    def handle(self, *args, **options):
        from core.models import Factory
        from materials.models import Material, MaterialCategory

        self.stdout.write('开始初始化测试数据...')

        # 创建工厂
        factories = {}
        for code in ['168', '228', '336', '440']:
            f, created = Factory.objects.get_or_create(
                code=code,
                defaults={
                    'name': f'厂区{code}',
                    'address': f'广东省深圳市厂区{code}',
                    'contact': f'联系人{code}',
                }
            )
            factories[code] = f
            if created:
                self.stdout.write(f'  创建工厂: {f.name}')

        # 创建分类
        cat, _ = MaterialCategory.objects.get_or_create(
            code='fpt',
            defaults={'name': '飞针测试资料', 'sort_order': 1}
        )

        # 创建测试用户
        users_data = [
            ('admin', 'admin123', 'admin'),
            ('zhangsan', 'pass123', 'engineer'),
            ('lisi', 'pass123', 'operator'),
        ]
        for uname, pwd, role in users_data:
            if not User.objects.filter(username=uname).exists():
                User.objects.create_user(
                    username=uname, password=pwd, role=role,
                    is_staff=(role == 'admin'), is_superuser=(role == 'admin')
                )
                self.stdout.write(f'  创建用户: {uname} ({role}) 密码: {pwd}')

        # 创建资料数据
        created_count = 0
        for item in SAMPLE_DATA:
            serial = item['serial_no']
            if Material.objects.filter(serial_no=serial).exists():
                continue

            Material.objects.create(
                serial_no=serial,
                factory=factories.get(item['factory_code'], factories['168']),
                material_no=item['material_no'],
                version_code=item['version_code'],
                category=cat,
                status=item['status'],
                remark=item['remark'],
                file_path=item['file_path'],
                created_at=datetime.strptime(item['created_at'], '%Y-%m-%d %H:%M:%S'),
            )
            created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ 初始化完成！共 {created_count} 条测试资料'
        ))
        self.stdout.write(f'\n登录账号: admin / admin123')
        self.stdout.write(f'工程师账号: zhangsan / pass123')
        self.stdout.write(f'操作员账号: lisi / pass123')
