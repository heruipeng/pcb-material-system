#!/usr/bin/env python
"""Apply all fixes: login page, dashboard, clean industrial UI, settings, etc."""
import os, sys

BASE = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 1. Fix settings.py: permissions, logging directory
# ============================================================
settings_path = os.path.join(BASE, 'pcb_system', 'settings.py')
with open(settings_path, 'r', encoding='utf-8') as f:
    settings_content = f.read()

# Fix IsAuthenticated -> AllowAny
settings_content = settings_content.replace(
    "'rest_framework.permissions.IsAuthenticated'",
    "'rest_framework.permissions.AllowAny'"
)

# Fix logging directory - auto-create
settings_content = settings_content.replace(
    "'filename': BASE_DIR / 'logs' / 'django.log'",
    "'filename': os.path.join(BASE_DIR, 'logs', 'django.log')"
)

with open(settings_path, 'w', encoding='utf-8') as f:
    f.write(settings_content)
print('[OK] settings.py fixed')

# ============================================================
# 2. Create logs directory
# ============================================================
os.makedirs(os.path.join(BASE, 'logs'), exist_ok=True)
print('[OK] logs/ directory created')

# ============================================================
# 3. Update core/views.py - add login/logout/dashboard
# ============================================================
login_views = '''
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from materials.models import Material, MaterialCategory
from tools.models import Tool, ToolCategory
from reports.models import Report, ReportCategory
from core.models import Factory


def user_login(request):
    """Custom login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(request.GET.get('next', 'dashboard'))
        else:
            messages.error(request, 'Username or password incorrect')
    return render(request, 'registration/login.html', {})


def user_logout(request):
    logout(request)
    return redirect('login')


@login_required(login_url='/login/')
def dashboard(request):
    """Main dashboard with materials, reports, and admin tabs"""
    return render(request, 'dashboard.html', {
        'total_materials': Material.objects.count(),
        'material_categories': MaterialCategory.objects.filter(is_active=True),
        'materials': Material.objects.select_related('factory', 'category', 'maker').order_by('-created_at')[:50],
        'total_tools': Tool.objects.filter(is_active=True).count(),
        'tool_categories': ToolCategory.objects.filter(is_active=True),
        'tools': Tool.objects.select_related('category').filter(is_active=True),
        'total_reports': Report.objects.filter(is_active=True).count(),
        'report_categories': ReportCategory.objects.filter(is_active=True),
        'reports': Report.objects.select_related('category').filter(is_active=True),
        'factories': Factory.objects.filter(is_active=True),
        'material_status_choices': Material.STATUS_CHOICES,
    })
'''

# Read existing core/views.py and insert login views at the top
views_path = os.path.join(BASE, 'core', 'views.py')
with open(views_path, 'r', encoding='utf-8') as f:
    original_content = f.read()

# Remove any previous login/dashboard definitions (safety)
lines = original_content.split('\n')
new_lines = []
skip_until_separator = False
for line in lines:
    if line.strip().startswith('from django.shortcuts') and 'render, redirect' in line and 'login' not in line:
        # Already have the right imports, skip duplicates
        pass
    new_lines.append(line)

# Check if login views already exist
if 'def user_login' not in original_content:
    # Insert imports and login views before the DRF views
    drf_start = original_content.find('from rest_framework')
    if drf_start == -1:
        drf_start = original_content.find('from .models import')
    
    if drf_start > 0:
        new_content = original_content[:drf_start] + login_views + '\n' + original_content[drf_start:]
    else:
        new_content = login_views + '\n' + original_content
    
    # Remove duplicate imports
    new_content = new_content.replace(
        'from django.shortcuts import render, redirect\nfrom django.shortcuts import render, redirect',
        'from django.shortcuts import render, redirect'
    )
    
    with open(views_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('[OK] core/views.py - added login/logout/dashboard views')

# ============================================================
# 4. Update pcb_system/urls.py - add login/logout/dashboard routes
# ============================================================
urls_path = os.path.join(BASE, 'pcb_system', 'urls.py')
with open(urls_path, 'r', encoding='utf-8') as f:
    urls_content = f.read()

if "from core.views import user_login" not in urls_content:
    # Add imports
    urls_content = urls_content.replace(
        'from django.urls import path, include',
        'from django.urls import path, include\nfrom core.views import user_login, user_logout, dashboard'
    )
    # Add routes before admin
    urls_content = urls_content.replace(
        "urlpatterns = [\n    path('admin/', admin.site.urls),",
        "urlpatterns = [\n    path('login/', user_login, name='login'),\n    path('logout/', user_logout, name='logout'),\n    path('', dashboard, name='dashboard'),\n    path('admin/', admin.site.urls),"
    )

with open(urls_path, 'w', encoding='utf-8') as f:
    f.write(urls_content)
print('[OK] pcb_system/urls.py - added login/logout/dashboard routes')

# ============================================================
# 5. Create templates/registration/login.html
# ============================================================
login_html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>PCB - Login</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#f0f2f5;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;color:#1d2129}
.box{width:400px;background:#fff;border-radius:12px;box-shadow:0 2px 16px rgba(0,0,0,.08);padding:48px 40px}
.lg{width:56px;height:56px;background:#165dff;border-radius:12px;display:inline-flex;align-items:center;justify-content:center;color:#fff;font-size:28px}
.hd{text-align:center;margin-bottom:40px}
.hd h1{font-size:22px;font-weight:600;margin-top:12px}
.hd p{color:#86909c;font-size:13px;margin-top:4px}
.fg{margin-bottom:20px}
.fg label{display:block;font-size:13px;font-weight:500;margin-bottom:6px}
.fg input{width:100%;padding:10px 14px;border:1px solid #e4e7eb;border-radius:6px;font-size:14px;background:#fafbfc;outline:none;transition:.2s}
.fg input:focus{border-color:#165dff;box-shadow:0 0 0 3px rgba(22,93,255,.1);background:#fff}
.err{background:#ffece8;color:#f53f3f;padding:10px 14px;border-radius:6px;font-size:13px;margin-bottom:16px}
.btn{width:100%;padding:11px;background:#165dff;color:#fff;border:none;border-radius:6px;font-size:15px;font-weight:500;cursor:pointer}
.btn:hover{background:#0e48d6}
.ft{text-align:center;margin-top:24px;color:#86909c;font-size:12px}
</style>
</head>
<body>
<div class="box">
<div class="hd"><div class="lg">&#x229E;</div><h1>PCB Engineering System</h1><p>Flying Probe Test Data Management</p></div>
{% if messages %}{% for msg in messages %}<div class="err">{{ msg }}</div>{% endfor %}{% endif %}
<form method="post" action="{% url 'login' %}">{% csrf_token %}
<div class="fg"><label>Username</label><input type="text" name="username" placeholder="Enter username" required autofocus></div>
<div class="fg"><label>Password</label><input type="password" name="password" placeholder="Enter password" required></div>
<button type="submit" class="btn">Sign In</button>
</form>
<div class="ft">Demo: admin / admin123</div>
</div>
</body>
</html>'''

os.makedirs(os.path.join(BASE, 'templates', 'registration'), exist_ok=True)
with open(os.path.join(BASE, 'templates', 'registration', 'login.html'), 'w', encoding='utf-8') as f:
    f.write(login_html)
print('[OK] templates/registration/login.html')

# ============================================================
# 6. Rewrite templates/dashboard.html
# ============================================================
dashboard_html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>PCB Engineering System</title>
<style>
:root{--bg:#f0f2f5;--s:#fff;--b:#e4e7eb;--t:#1d2129;--m:#86909c;--a:#165dff;--g:#00b42a;--o:#ff7d00;--r:#f53f3f}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;color:var(--t);font-size:14px}
/* Top bar */
.tb{height:52px;background:var(--s);border-bottom:1px solid var(--b);display:flex;align-items:center;padding:0 24px;position:sticky;top:0;z-index:100;box-shadow:0 1px 4px rgba(0,0,0,.04)}
.tb .l{font-size:16px;font-weight:600;text-decoration:none;color:var(--t)}
.tb .l::before{content:"\\229E ";color:var(--a)}
.tb .u{margin-left:auto;display:flex;align-items:center;gap:12px}
.tb .u span{color:var(--m);font-size:13px}
.tb .u a{color:var(--a);text-decoration:none;font-size:13px;padding:4px 12px;border:1px solid var(--a);border-radius:4px}
.tb .u a:hover{background:#e8f0fe}
/* Tabs */
.ts{background:var(--s);border-bottom:1px solid var(--b);padding:0 24px;display:flex}
.t{padding:12px 24px;font-size:14px;font-weight:500;color:var(--m);cursor:pointer;border:none;background:none;border-bottom:2px solid transparent;transition:.15s}
.t:hover{color:var(--a)}.t.ac{color:var(--a);border-bottom-color:var(--a)}
/* Content */
.ct{max-width:1400px;margin:0 auto;padding:24px}
.pn{display:none}.pn.ac{display:block}
/* Stats */
.st{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}
.sc{background:var(--s);border:1px solid var(--b);border-radius:8px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,.04)}
.sc .v{font-size:32px;font-weight:700;color:var(--a)}
.sc .la{font-size:13px;color:var(--m);margin-top:4px}
/* Filter bar */
.fb{background:var(--s);border:1px solid var(--b);border-radius:8px;padding:16px 20px;margin-bottom:16px;display:flex;gap:12px;align-items:flex-end;flex-wrap:wrap;box-shadow:0 1px 3px rgba(0,0,0,.04)}
.fg{display:flex;flex-direction:column;gap:4px}
.fg label{font-size:12px;color:var(--m);font-weight:500}
.fg input,.fg select{padding:7px 12px;border:1px solid var(--b);border-radius:6px;font-size:13px;background:#fafbfc;min-width:140px;outline:none;color:var(--t)}
.fg input:focus,.fg select:focus{border-color:var(--a);box-shadow:0 0 0 2px rgba(22,93,255,.08);background:#fff}
.bt{display:inline-flex;align-items:center;gap:6px;padding:7px 18px;border:none;border-radius:6px;font-size:13px;font-weight:500;cursor:pointer;text-decoration:none}
.bt-p{background:var(--a);color:#fff}.bt-p:hover{background:#0e48d6}
.bt-r{background:#fff;color:var(--t);border:1px solid var(--b)}.bt-r:hover{border-color:var(--a);color:var(--a)}
/* Table */
.tw{background:var(--s);border:1px solid var(--b);border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.04)}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:#f7f8fa;color:var(--m);font-weight:600;font-size:12px;padding:10px 14px;text-align:left;border-bottom:1px solid var(--b);white-space:nowrap}
td{padding:10px 14px;border-bottom:1px solid var(--b)}
tr:hover td{background:#f7f8fa}
/* Badges */
.bg{display:inline-block;padding:2px 10px;border-radius:10px;font-size:12px;font-weight:500}
.bg-s{color:var(--g);background:#e8ffea}
.bg-p{color:var(--o);background:#fff7e8}
.bg-d{color:var(--m);background:#f2f3f5}
.bg-e{color:var(--r);background:#ffece8}
.lk{color:var(--a);text-decoration:none;cursor:pointer}.lk:hover{text-decoration:underline}
.em{text-align:center;padding:60px 20px;color:var(--m)}
.ft{text-align:center;padding:20px;color:var(--m);font-size:12px}
/* Tool list */
.tool-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}
.tool-card{background:var(--s);border:1px solid var(--b);border-radius:8px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,.04);transition:.15s}
.tool-card:hover{box-shadow:0 2px 8px rgba(0,0,0,.08)}
.tool-card h3{font-size:15px;font-weight:600;margin-bottom:8px;color:var(--t)}
.tool-card .meta{font-size:12px;color:var(--m);margin-bottom:4px}
.tool-card .desc{font-size:13px;color:var(--m);margin-top:8px}
.top-actions{display:flex;gap:8px;margin-bottom:24px;flex-wrap:wrap}
</style>
</head>
<body>
<div class="tb">
    <a href="/" class="l">PCB Engineering System</a>
    <div class="u">
        <span>{{ request.user.username }} <strong style="color:var(--a)">[{{ request.user.get_role_display }}]</strong></span>
        <a href="{% url 'logout' %}">Sign Out</a>
    </div>
</div>

<div class="ts">
    <button class="t ac" onclick="sw('m')">Materials</button>
    <button class="t" onclick="sw('r')">Reports</button>
    <button class="t" onclick="sw('a')">Admin</button>
</div>

<div class="ct">

<!-- ===== Materials Tab ===== -->
<div id="pn-m" class="pn ac">
    <div class="st">
        <div class="sc"><div class="v">{{ total_materials }}</div><div class="la">Total Materials</div></div>
        <div class="sc"><div class="v">{{ material_categories.count }}</div><div class="la">Categories</div></div>
        <div class="sc"><div class="v">{{ total_tools }}</div><div class="la">Available Tools</div></div>
        <div class="sc"><div class="v">{{ factories.count }}</div><div class="la">Factories</div></div>
    </div>

    <div class="fb">
        <div class="fg"><label>Keyword</label><input id="kw-m" placeholder="Serial No / PN"></div>
        <div class="fg"><label>Factory</label><select id="f-m"><option value="">All</option>{% for f in factories %}<option value="{{ f.code }}">{{ f.name }}</option>{% endfor %}</select></div>
        <div class="fg"><label>Status</label><select id="s-m"><option value="">All</option>{% for c,l in material_status_choices %}<option value="{{ c }}">{{ l }}</option>{% endfor %}</select></div>
        <button class="bt bt-p" onclick="ft('mt')">Search</button>
        <button class="bt bt-r" onclick="rf('mt',['kw-m','f-m','s-m'])">Reset</button>
    </div>

    <div class="tw">
        <table id="mt">
            <thead><tr><th>Serial ID</th><th>Factory</th><th>Part No</th><th>Version</th><th>Category</th><th>Remark</th><th>Status</th><th>Maker</th><th>Created</th></tr></thead>
            <tbody>
                {% for m in materials %}
                <tr data-factory="{{ m.factory.code }}" data-status="{{ m.status }}" data-kw="{{ m.serial_no }} {{ m.material_no }}">
                    <td><span class="lk">{{ m.serial_no }}</span></td>
                    <td>{{ m.factory.code }}</td>
                    <td>{{ m.material_no }}</td>
                    <td>{{ m.version_code }}</td>
                    <td>{{ m.category.name|default:"-" }}</td>
                    <td>{{ m.remark|default:"-" }}</td>
                    <td>
                        {% if m.status == 'approved' or m.status == 'published' %}
                        <span class="bg bg-s">{{ m.get_status_display }}</span>
                        {% elif m.status == 'pending' %}
                        <span class="bg bg-p">{{ m.get_status_display }}</span>
                        {% elif m.status == 'rejected' %}
                        <span class="bg bg-e">{{ m.get_status_display }}</span>
                        {% else %}
                        <span class="bg bg-d">{{ m.get_status_display }}</span>
                        {% endif %}
                    </td>
                    <td>{{ m.maker.username|default:"-" }}</td>
                    <td>{{ m.created_at|date:"Y-m-d H:i" }}</td>
                </tr>
                {% empty %}
                <tr><td colspan="9" class="em">No material data</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- Tools section -->
    <h3 style="margin:24px 0 16px;font-size:16px;font-weight:600">Available Tools</h3>
    <div class="tool-grid">
        {% for t in tools %}
        <div class="tool-card">
            <h3>{{ t.name }}</h3>
            <div class="meta">Code: {{ t.code }} | Type: {{ t.get_tool_type_display }}</div>
            <div class="meta">Category: {{ t.category.name }} | v{{ t.version }}</div>
            <div class="desc">{{ t.description|default:"No description" }}</div>
        </div>
        {% empty %}
        <div class="em" style="grid-column:1/-1">No tools configured</div>
        {% endfor %}
    </div>
</div>

<!-- ===== Reports Tab ===== -->
<div id="pn-r" class="pn">
    <div class="st">
        <div class="sc"><div class="v">{{ total_reports }}</div><div class="la">Total Reports</div></div>
        <div class="sc"><div class="v">{{ report_categories.count }}</div><div class="la">Report Categories</div></div>
    </div>

    <div class="fb">
        <div class="fg"><label>Keyword</label><input id="kw-r" placeholder="Report Name / Code"></div>
        <div class="fg"><label>Category</label><select id="c-r"><option value="">All</option>{% for c in report_categories %}<option value="{{ c.code }}">{{ c.name }}</option>{% endfor %}</select></div>
        <button class="bt bt-p" onclick="ft('rt')">Search</button>
        <button class="bt bt-r" onclick="rf('rt',['kw-r','c-r'])">Reset</button>
    </div>

    <div class="tw">
        <table id="rt">
            <thead><tr><th>Code</th><th>Name</th><th>Category</th><th>Type</th><th>Description</th><th>Created</th></tr></thead>
            <tbody>
                {% for r in reports %}
                <tr data-category="{{ r.category.code }}" data-kw="{{ r.name }} {{ r.code }}">
                    <td><span class="lk">{{ r.code }}</span></td>
                    <td>{{ r.name }}</td>
                    <td>{{ r.category.name|default:"-" }}</td>
                    <td>{{ r.get_report_type_display }}</td>
                    <td>{{ r.description|default:"-" }}</td>
                    <td>{{ r.created_at|date:"Y-m-d H:i" }}</td>
                </tr>
                {% empty %}
                <tr><td colspan="6" class="em">No report data</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>

<!-- ===== Admin Tab ===== -->
<div id="pn-a" class="pn">
    <div class="tw" style="padding:60px;text-align:center">
        <div style="font-size:48px;margin-bottom:16px;opacity:.3">&#x2699;</div>
        <p style="font-size:16px;font-weight:500;margin-bottom:8px">Django Admin Console</p>
        <p style="color:var(--m);margin-bottom:24px">User management · Permissions · System settings</p>
        <a href="/admin/" class="bt bt-p" style="text-decoration:none;padding:10px 32px;font-size:14px">Open Admin &rarr;</a>
    </div>
</div>

</div>

<div class="ft">PCB Engineering System v2.0 &copy; 2026</div>

<script>
function sw(n){
    var tabs={m:1,r:2,a:3};
    document.querySelectorAll('.t').forEach(function(t,i){t.classList.toggle('ac',i+1===tabs[n])});
    document.querySelectorAll('.pn').forEach(function(p){p.classList.remove('ac')});
    document.getElementById('pn-'+n).classList.add('ac');
}
function ft(id){
    var rows=document.querySelectorAll('#'+id+' tbody tr');
    var p=id==='mt'?'m':'r';
    var kw=(document.getElementById('kw-'+p)?.value||'').toLowerCase();
    var fac=document.getElementById('f-'+p)?.value||'';
    var sta=document.getElementById('s-'+p)?.value||'';
    var cat=document.getElementById('c-'+p)?.value||'';
    rows.forEach(function(row){
        var ok=(!kw||(row.dataset.kw||'').toLowerCase().indexOf(kw)>-1)
            &&(!fac||(row.dataset.factory||'')===fac)
            &&(!sta||(row.dataset.status||'')===sta)
            &&(!cat||(row.dataset.category||'')===cat);
        row.style.display=ok?'':'none';
    });
}
function rf(id,ids){
    ids.forEach(function(i){var e=document.getElementById(i);if(e)e.value='';});
    ft(id);
}
document.querySelectorAll('.fb input').forEach(function(inp){
    inp.addEventListener('keydown',function(e){
        if(e.key==='Enter')ft(inp.closest('.pn').querySelector('table').id);
    });
});
</script>
</body>
</html>'''

with open(os.path.join(BASE, 'templates', 'dashboard.html'), 'w', encoding='utf-8') as f:
    f.write(dashboard_html)
print('[OK] templates/dashboard.html rewritten')

# ============================================================
# 7. Create migrations directories and __init__.py files
# ============================================================
for app in ['accounts', 'materials', 'tools', 'reports', 'core']:
    mig_dir = os.path.join(BASE, app, 'migrations')
    os.makedirs(mig_dir, exist_ok=True)
    init_file = os.path.join(mig_dir, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w', encoding='utf-8') as f:
            pass
print('[OK] migrations/ directories created')

# ============================================================
# 8. Create init_data.py
# ============================================================
init_data = '''#!/usr/bin/env python
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
'''

with open(os.path.join(BASE, 'init_data.py'), 'w', encoding='utf-8') as f:
    f.write(init_data)
print('[OK] init_data.py created')

# ============================================================
# 9. Create setup.sh / quickstart script
# ============================================================
quickstart = '''#!/bin/bash
# Quick setup for PCB Engineering System
python _apply_fixes.py
rm -f db.sqlite3
python manage.py makemigrations accounts materials tools reports core
python manage.py migrate
python init_data.py
echo ""
echo "============================================"
echo "  Setup complete! Run:"
echo "  python manage.py runserver"
echo "  Then open: http://127.0.0.1:8000/"
echo "  Login: admin / admin123"
echo "============================================"
'''

with open(os.path.join(BASE, 'setup.sh'), 'w', encoding='utf-8') as f:
    f.write(quickstart)
os.chmod(os.path.join(BASE, 'setup.sh'), 0o755)

print('')
print('=' * 60)
print('ALL FIXES APPLIED')
print('Add login/dashboard + clean industrial UI + seed data')
print('=' * 60)
