#!/usr/bin/env python
"""Initialize test data for PCB Engineering System"""
import os, sys, django

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pcb_system.settings')
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    django.setup()

    from accounts.models import User, Permission, RolePermission
    from core.models import Factory, SystemConfig
    from materials.models import MaterialCategory, Material
    from reports.models import ReportCategory, Report
    from tools.models import ToolCategory, Tool

    print('=' * 60)

    # 1. Factories
    factories = [
        {'code': 'SZ01', 'name': 'Shenzhen Plant 1', 'address': 'No.100 XX Rd, Baoan, Shenzhen', 'contact': 'Mr. Zhang'},
        {'code': 'SZ02', 'name': 'Shenzhen Plant 2', 'address': 'No.200 XX Rd, Longgang, Shenzhen', 'contact': 'Mr. Li'},
        {'code': 'DG01', 'name': 'Dongguan Plant', 'address': 'No.88 XX Rd, Changan, Dongguan', 'contact': 'Mr. Wang'},
    ]
    for f_data in factories:
        Factory.objects.get_or_create(code=f_data['code'], defaults=f_data)
    print('[OK] Factories x3 created')

    # 2. Users
    factories_map = {f.code: f for f in Factory.objects.all()}
    users_data = [
        {'username': 'admin', 'role': 'admin', 'department': 'IT', 'factory': 'SZ01'},
        {'username': 'zhangsan', 'role': 'manager', 'department': 'Engineering', 'factory': 'SZ01'},
        {'username': 'lisi', 'role': 'engineer', 'department': 'Quality', 'factory': 'SZ02'},
        {'username': 'wangwu', 'role': 'operator', 'department': 'Production', 'factory': 'DG01'},
        {'username': 'zhaoliu', 'role': 'viewer', 'department': 'R&D', 'factory': 'SZ01'},
    ]
    for u_data in users_data:
        user, created = User.objects.get_or_create(
            username=u_data['username'],
            defaults={
                'role': u_data['role'],
                'department': u_data['department'],
                'factory': factories_map.get(u_data['factory']),
                'is_staff': u_data['role'] in ('admin', 'manager'),
                'is_superuser': u_data['role'] == 'admin',
            }
        )
        if created:
            user.set_password('admin123')
            user.save()
        mark = '[NEW]' if created else '[OK]'
        print(f'  {mark} {u_data["username"]} ({u_data["role"]}) - pwd: admin123')
    print('[OK] Users x5 ready')

    # 3. Material Categories
    materials_cats = [
        {'code': 'PCB_DSN', 'name': 'PCB Design Files', 'sort_order': 1},
        {'code': 'GERBER', 'name': 'Gerber Files', 'sort_order': 2},
        {'code': 'BOM', 'name': 'BOM', 'sort_order': 3},
        {'code': 'SPEC', 'name': 'Specifications', 'sort_order': 4},
        {'code': 'TEST_RPT', 'name': 'Test Reports', 'sort_order': 5},
        {'code': 'QC_REC', 'name': 'Quality Records', 'sort_order': 6},
    ]
    mcat_objs = {}
    for cat in materials_cats:
        obj, _ = MaterialCategory.objects.get_or_create(code=cat['code'], defaults=cat)
        mcat_objs[cat['code']] = obj
    print('[OK] Material categories x6')

    # 4. Materials
    admin = User.objects.get(username='admin')
    zhangsan = User.objects.get(username='zhangsan')
    statuses = ['draft','pending','pending','approved','approved','published',
                'published','published','approved','approved','published',
                'archived','draft','approved','published','published',
                'approved','published','approved','draft']
    cat_keys = list(mcat_objs.keys())
    for i, s in enumerate(statuses, start=1):
        Material.objects.get_or_create(
            serial_no=f'PCB-{i:04d}',
            defaults={
                'factory': factories_map['SZ01' if i % 3 != 0 else ('SZ02' if i % 3 == 1 else 'DG01')],
                'material_no': f'PN-{6000+i}',
                'version_code': f'V{1+(i%3)}.{i%5}',
                'category': mcat_objs[cat_keys[i % len(cat_keys)]],
                'status': s,
                'creator': admin,
                'maker': zhangsan,
            }
        )
    print('[OK] Materials x20 created')

    # 5. Tool Categories
    tool_cats = [
        {'code': 'FLY_PROBE', 'name': 'Flying Probe', 'sort_order': 1},
        {'code': 'IMPEDANCE', 'name': 'Impedance Test', 'sort_order': 2},
        {'code': 'AOI', 'name': 'AOI Inspection', 'sort_order': 3},
        {'code': 'XRAY', 'name': 'X-Ray Inspection', 'sort_order': 4},
    ]
    tcat_objs = {}
    for tc in tool_cats:
        obj, _ = ToolCategory.objects.get_or_create(code=tc['code'], defaults=tc)
        tcat_objs[tc['code']] = obj
    print('[OK] Tool categories x4')

    # 6. Tools
    tools_data = [
        {'code': 'FP-001', 'name': 'Flying Probe Tester A1', 'tool_type': 'fly_probe', 'category': 'FLY_PROBE', 'version': '2.1'},
        {'code': 'FP-002', 'name': 'Flying Probe Tester A2', 'tool_type': 'fly_probe', 'category': 'FLY_PROBE', 'version': '2.0'},
        {'code': 'IMP-001', 'name': 'Impedance Analyzer B1', 'tool_type': 'impedance', 'category': 'IMPEDANCE', 'version': '1.5'},
        {'code': 'AOI-001', 'name': 'AOI Inspector C1', 'tool_type': 'aoi', 'category': 'AOI', 'version': '3.0'},
        {'code': 'AOI-002', 'name': 'AOI Inspector C2', 'tool_type': 'aoi', 'category': 'AOI', 'version': '3.1'},
        {'code': 'XR-001', 'name': 'X-Ray Inspector D1', 'tool_type': 'xray', 'category': 'XRAY', 'version': '1.0'},
    ]
    for td in tools_data:
        Tool.objects.get_or_create(code=td['code'], defaults={
            'name': td['name'], 'category': tcat_objs[td['category']],
            'tool_type': td['tool_type'], 'version': td['version'],
            'description': f'{td["name"]} v{td["version"]}',
        })
    print('[OK] Tools x6 created')

    # 7. Report Categories
    report_cats = [
        {'code': 'QUALITY', 'name': 'Quality Reports', 'sort_order': 1},
        {'code': 'PRODUCTION', 'name': 'Production Reports', 'sort_order': 2},
        {'code': 'YIELD', 'name': 'Yield Reports', 'sort_order': 3},
        {'code': 'COST', 'name': 'Cost Reports', 'sort_order': 4},
    ]
    rcat_objs = {}
    for rc in report_cats:
        obj, _ = ReportCategory.objects.get_or_create(code=rc['code'], defaults=rc)
        rcat_objs[rc['code']] = obj
    print('[OK] Report categories x4')

    # 8. Reports
    reports_data = [
        {'code': 'RPT_Q001', 'name': 'Daily Quality Inspection', 'report_type': 'summary', 'category': 'QUALITY'},
        {'code': 'RPT_Q002', 'name': 'Incoming Inspection Detail', 'report_type': 'detail', 'category': 'QUALITY'},
        {'code': 'RPT_P001', 'name': 'Daily Output Summary', 'report_type': 'summary', 'category': 'PRODUCTION'},
        {'code': 'RPT_P002', 'name': 'Process Efficiency Analysis', 'report_type': 'analysis', 'category': 'PRODUCTION'},
        {'code': 'RPT_Y001', 'name': 'Overall Yield Statistics', 'report_type': 'statistical', 'category': 'YIELD'},
        {'code': 'RPT_C001', 'name': 'Material Cost Accounting', 'report_type': 'analysis', 'category': 'COST'},
    ]
    for rd in reports_data:
        Report.objects.get_or_create(code=rd['code'], defaults={
            'name': rd['name'], 'category': rcat_objs[rd['category']],
            'report_type': rd['report_type'], 'description': f'{rd["name"]} Report',
        })
    print('[OK] Reports x6 created')

    # 9. Permissions
    perms = {
        'material.view': 'View Materials', 'material.create': 'Create Materials',
        'material.edit': 'Edit Materials', 'material.delete': 'Delete Materials',
        'material.approve': 'Approve Materials', 'material.export': 'Export Materials',
        'report.view': 'View Reports', 'report.create': 'Create Reports',
        'report.export': 'Export Reports', 'tool.view': 'View Tools',
        'tool.execute': 'Execute Tools', 'tool.config': 'Configure Tools',
        'user.manage': 'Manage Users', 'system.config': 'System Config',
    }
    perm_objs = {}
    for code, name in perms.items():
        obj, _ = Permission.objects.get_or_create(code=code, defaults={'name': name})
        perm_objs[code] = obj

    role_perms = {
        'admin': list(perms.keys()),
        'manager': ['material.view','material.create','material.edit','material.approve',
                    'material.export','report.view','report.create','report.export',
                    'tool.view','tool.execute'],
        'engineer': ['material.view','material.create','material.edit','material.export',
                     'report.view','report.create','tool.view','tool.execute'],
        'operator': ['material.view','tool.view','tool.execute','report.view'],
        'viewer': ['material.view','report.view','tool.view'],
    }
    for role, perm_codes in role_perms.items():
        for pc in perm_codes:
            RolePermission.objects.get_or_create(role=role, permission=perm_objs[pc])
    print('[OK] Permissions x{} + role assignments done'.format(len(perms)))

    # 10. System Configs
    configs = [
        {'key': 'site_name', 'value': 'PCB Engineering System', 'description': 'Site name'},
        {'key': 'auto_approve', 'value': 'false', 'description': 'Auto approve'},
        {'key': 'max_upload_size', 'value': '52428800', 'description': 'Max upload size (bytes)'},
    ]
    for cfg in configs:
        SystemConfig.objects.get_or_create(key=cfg['key'], defaults=cfg)
    print('[OK] System configs x{}'.format(len(configs)))

    print('=' * 60)
    print('[DONE] All test data initialized!')
    print()
    print('  Login accounts (password: admin123):')
    print('  admin     - Administrator (superuser)')
    print('  zhangsan  - Manager')
    print('  lisi      - Engineer')
    print('  wangwu    - Operator')
    print('  zhaoliu   - Viewer')
    print()
    print('  Run: python manage.py runserver')
    print('  URL: http://127.0.0.1:8000/')
    print('=' * 60)
