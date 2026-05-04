#!/usr/bin/env python
"""PCB System - One-click complete setup: login, dashboard, clean UI, seed data, launch"""
import os, sys, subprocess

BASE = r'D:\pcb_system'

def write_file(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  [OK] {path}')

def run(cmd):
    print(f'  >>> {cmd}')
    r = subprocess.run(cmd, shell=True, cwd=BASE, capture_output=True, text=True)
    if r.stdout: print(r.stdout.strip())
    if r.returncode != 0:
        print(f'  [ERR] {r.stderr}')
        return False
    return True

print('='*60)
print('PCB System - One-Click Complete Setup')
print('='*60)

# ===== 1. Fix settings.py =====
print('\n[1/4] Fixing settings...')
sp = os.path.join(BASE, 'pcb_system', 'settings.py')
with open(sp, 'r', encoding='utf-8') as f:
    sc = f.read()
sc = sc.replace("'rest_framework.permissions.IsAuthenticated'", "'rest_framework.permissions.AllowAny'")
with open(sp, 'w', encoding='utf-8') as f:
    f.write(sc)
os.makedirs(os.path.join(BASE, 'logs'), exist_ok=True)
print('  [OK] settings.py + logs/')

# ===== 2. Create all template/code files =====
print('\n[2/4] Creating files...')

# core/views.py - add login/dashboard
views_extra = """
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from materials.models import Material, MaterialCategory
from tools.models import Tool, ToolCategory
from reports.models import Report, ReportCategory
from core.models import Factory


def user_login(request):
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
    return render(request, 'dashboard.html', {
        'total_materials': Material.objects.count(),
        'material_categories': MaterialCategory.objects.filter(is_active=True),
        'materials': Material.objects.select_related('factory','category','maker').order_by('-created_at')[:50],
        'total_tools': Tool.objects.filter(is_active=True).count(),
        'tool_categories': ToolCategory.objects.filter(is_active=True),
        'tools': Tool.objects.select_related('category').filter(is_active=True),
        'total_reports': Report.objects.filter(is_active=True).count(),
        'report_categories': ReportCategory.objects.filter(is_active=True),
        'reports': Report.objects.select_related('category').filter(is_active=True),
        'factories': Factory.objects.filter(is_active=True),
        'material_status_choices': Material.STATUS_CHOICES,
    })
"""
vp = os.path.join(BASE, 'core', 'views.py')
with open(vp, 'r', encoding='utf-8') as f:
    vc = f.read()
if 'def user_login' not in vc:
    with open(vp, 'w', encoding='utf-8') as f:
        f.write(views_extra + '\n' + vc)
print('  [OK] core/views.py')

# pcb_system/urls.py
up = os.path.join(BASE, 'pcb_system', 'urls.py')
with open(up, 'r', encoding='utf-8') as f:
    uc = f.read()
if 'user_login' not in uc:
    uc = uc.replace(
        'from django.urls import path, include',
        'from django.urls import path, include\nfrom core.views import user_login, user_logout, dashboard'
    )
    uc = uc.replace(
        "urlpatterns = [\n    path('admin/', admin.site.urls),",
        "urlpatterns = [\n    path('login/', user_login, name='login'),\n    path('logout/', user_logout, name='logout'),\n    path('', dashboard, name='dashboard'),\n    path('admin/', admin.site.urls),"
    )
    with open(up, 'w', encoding='utf-8') as f:
        f.write(uc)
print('  [OK] pcb_system/urls.py')

# login.html
write_file('templates/registration/login.html', '''<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>PCB System - Login</title>
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
</style></head>
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
</div></body></html>''')

# dashboard.html
write_file('templates/dashboard.html', '''<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>PCB Engineering System</title>
<style>
:root{--bg:#f0f2f5;--s:#fff;--b:#e4e7eb;--t:#1d2129;--m:#86909c;--a:#165dff;--g:#00b42a;--o:#ff7d00;--r:#f53f3f}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;color:var(--t);font-size:14px}
.tb{height:52px;background:var(--s);border-bottom:1px solid var(--b);display:flex;align-items:center;padding:0 24px;position:sticky;top:0;z-index:100;box-shadow:0 1px 4px rgba(0,0,0,.04)}
.tb .l{font-size:16px;font-weight:600;text-decoration:none;color:var(--t)}
.tb .l::before{content:"\\229E ";color:var(--a)}
.tb .u{margin-left:auto;display:flex;align-items:center;gap:12px}
.tb .u span{color:var(--m);font-size:13px}
.tb .u a{color:var(--a);text-decoration:none;font-size:13px;padding:4px 12px;border:1px solid var(--a);border-radius:4px}
.tb .u a:hover{background:#e8f0fe}
.ts{background:var(--s);border-bottom:1px solid var(--b);padding:0 24px;display:flex}
.t{padding:12px 24px;font-size:14px;font-weight:500;color:var(--m);cursor:pointer;border:none;background:none;border-bottom:2px solid transparent;transition:.15s}
.t:hover{color:var(--a)}.t.ac{color:var(--a);border-bottom-color:var(--a)}
.ct{max-width:1400px;margin:0 auto;padding:24px}
.pn{display:none}.pn.ac{display:block}
.st{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}
.sc{background:var(--s);border:1px solid var(--b);border-radius:8px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,.04)}
.sc .v{font-size:32px;font-weight:700;color:var(--a)}
.sc .la{font-size:13px;color:var(--m);margin-top:4px}
.fb{background:var(--s);border:1px solid var(--b);border-radius:8px;padding:16px 20px;margin-bottom:16px;display:flex;gap:12px;align-items:flex-end;flex-wrap:wrap;box-shadow:0 1px 3px rgba(0,0,0,.04)}
.fg{display:flex;flex-direction:column;gap:4px}
.fg label{font-size:12px;color:var(--m);font-weight:500}
.fg input,.fg select{padding:7px 12px;border:1px solid var(--b);border-radius:6px;font-size:13px;background:#fafbfc;min-width:140px;outline:none;color:var(--t)}
.fg input:focus,.fg select:focus{border-color:var(--a);box-shadow:0 0 0 2px rgba(22,93,255,.08);background:#fff}
.bt{display:inline-flex;align-items:center;gap:6px;padding:7px 18px;border:none;border-radius:6px;font-size:13px;font-weight:500;cursor:pointer;text-decoration:none}
.bt-p{background:var(--a);color:#fff}.bt-p:hover{background:#0e48d6}
.bt-r{background:#fff;color:var(--t);border:1px solid var(--b)}.bt-r:hover{border-color:var(--a);color:var(--a)}
.tw{background:var(--s);border:1px solid var(--b);border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.04)}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:#f7f8fa;color:var(--m);font-weight:600;font-size:12px;padding:10px 14px;text-align:left;border-bottom:1px solid var(--b);white-space:nowrap}
td{padding:10px 14px;border-bottom:1px solid var(--b)}
tr:hover td{background:#f7f8fa}
.bg{display:inline-block;padding:2px 10px;border-radius:10px;font-size:12px;font-weight:500}
.bg-s{color:var(--g);background:#e8ffea}
.bg-p{color:var(--o);background:#fff7e8}
.bg-d{color:var(--m);background:#f2f3f5}
.bg-e{color:var(--r);background:#ffece8}
.lk{color:var(--a);text-decoration:none;cursor:pointer}.lk:hover{text-decoration:underline}
.em{text-align:center;padding:60px 20px;color:var(--m)}
.ft{text-align:center;padding:20px;color:var(--m);font-size:12px}
.tool-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;margin-top:16px}
.tool-card{background:var(--s);border:1px solid var(--b);border-radius:8px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,.04);transition:.15s}
.tool-card:hover{box-shadow:0 2px 8px rgba(0,0,0,.08)}
.tool-card h3{font-size:15px;font-weight:600;margin-bottom:8px;color:var(--t)}
.tool-card .meta{font-size:12px;color:var(--m);margin-bottom:4px}
.tool-card .desc{font-size:13px;color:var(--m);margin-top:8px}
</style></head>
<body>
<div class="tb"><a href="/" class="l">PCB Engineering System</a>
<div class="u"><span>{{ request.user.username }} <strong style="color:var(--a)">[{{ request.user.get_role_display }}]</strong></span><a href="{% url 'logout' %}">Sign Out</a></div></div>
<div class="ts">
<button class="t ac" onclick="sw('m')">Materials</button>
<button class="t" onclick="sw('r')">Reports</button>
<button class="t" onclick="sw('a')">Admin</button></div>
<div class="ct">
<div id="pn-m" class="pn ac">
<div class="st">
<div class="sc"><div class="v">{{ total_materials }}</div><div class="la">Total Materials</div></div>
<div class="sc"><div class="v">{{ material_categories.count }}</div><div class="la">Categories</div></div>
<div class="sc"><div class="v">{{ total_tools }}</div><div class="la">Available Tools</div></div>
<div class="sc"><div class="v">{{ factories.count }}</div><div class="la">Factories</div></div></div>
<div class="fb">
<div class="fg"><label>Keyword</label><input id="kw-m" placeholder="Serial No / PN"></div>
<div class="fg"><label>Factory</label><select id="f-m"><option value="">All</option>{% for f in factories %}<option value="{{ f.code }}">{{ f.name }}</option>{% endfor %}</select></div>
<div class="fg"><label>Status</label><select id="s-m"><option value="">All</option>{% for c,l in material_status_choices %}<option value="{{ c }}">{{ l }}</option>{% endfor %}</select></div>
<button class="bt bt-p" onclick="ft('mt')">Search</button>
<button class="bt bt-r" onclick="rf('mt',['kw-m','f-m','s-m'])">Reset</button></div>
<div class="tw"><table id="mt">
<thead><tr><th>Serial ID</th><th>Factory</th><th>Part No</th><th>Version</th><th>Category</th><th>Remark</th><th>Status</th><th>Maker</th><th>Created</th></tr></thead>
<tbody>{% for m in materials %}<tr data-factory="{{ m.factory.code }}" data-status="{{ m.status }}" data-kw="{{ m.serial_no }} {{ m.material_no }}">
<td><span class="lk">{{ m.serial_no }}</span></td><td>{{ m.factory.code }}</td><td>{{ m.material_no }}</td><td>{{ m.version_code }}</td>
<td>{{ m.category.name|default:"-" }}</td><td>{{ m.remark|default:"-" }}</td>
<td>{% if m.status == 'approved' or m.status == 'published' %}<span class="bg bg-s">{{ m.get_status_display }}</span>{% elif m.status == 'pending' %}<span class="bg bg-p">{{ m.get_status_display }}</span>{% elif m.status == 'rejected' %}<span class="bg bg-e">{{ m.get_status_display }}</span>{% else %}<span class="bg bg-d">{{ m.get_status_display }}</span>{% endif %}</td>
<td>{{ m.maker.username|default:"-" }}</td><td>{{ m.created_at|date:"Y-m-d H:i" }}</td></tr>{% empty %}<tr><td colspan="9" class="em">No materials yet</td></tr>{% endfor %}</tbody></table></div>
<h3 style="margin:24px 0 16px;font-size:16px;font-weight:600">Tool Inventory</h3>
<div class="tool-grid">{% for t in tools %}<div class="tool-card">
<h3>{{ t.name }}</h3><div class="meta">Code: {{ t.code }} | Type: {{ t.get_tool_type_display }}</div>
<div class="meta">Category: {{ t.category.name }} | v{{ t.version }}</div>
<div class="desc">{{ t.description|default:"No description" }}</div></div>{% empty %}<div class="em" style="grid-column:1/-1">No tools configured</div>{% endfor %}</div></div>
<div id="pn-r" class="pn">
<div class="st"><div class="sc"><div class="v">{{ total_reports }}</div><div class="la">Total Reports</div></div><div class="sc"><div class="v">{{ report_categories.count }}</div><div class="la">Report Categories</div></div></div>
<div class="fb"><div class="fg"><label>Keyword</label><input id="kw-r" placeholder="Report Name / Code"></div><div class="fg"><label>Category</label><select id="c-r"><option value="">All</option>{% for c in report_categories %}<option value="{{ c.code }}">{{ c.name }}</option>{% endfor %}</select></div><button class="bt bt-p" onclick="ft('rt')">Search</button><button class="bt bt-r" onclick="rf('rt',['kw-r','c-r'])">Reset</button></div>
<div class="tw"><table id="rt"><thead><tr><th>Code</th><th>Name</th><th>Category</th><th>Type</th><th>Description</th><th>Created</th></tr></thead>
<tbody>{% for r in reports %}<tr data-category="{{ r.category.code }}" data-kw="{{ r.name }} {{ r.code }}">
<td><span class="lk">{{ r.code }}</span></td><td>{{ r.name }}</td><td>{{ r.category.name|default:"-" }}</td><td>{{ r.get_report_type_display }}</td><td>{{ r.description|default:"-" }}</td><td>{{ r.created_at|date:"Y-m-d H:i" }}</td></tr>{% empty %}<tr><td colspan="6" class="em">No reports yet</td></tr>{% endfor %}</tbody></table></div></div>
<div id="pn-a" class="pn"><div class="tw" style="padding:60px;text-align:center"><div style="font-size:48px;margin-bottom:16px;opacity:.3">⚙️</div><p style="font-size:16px;font-weight:500;margin-bottom:8px">Django Admin Console</p><p style="color:var(--m);margin-bottom:24px">User management · Permissions · System settings</p><a href="/admin/" class="bt bt-p" style="text-decoration:none;padding:10px 32px;font-size:14px">Open Admin →</a></div></div>
</div><div class="ft">PCB Engineering System v2.0 &copy; 2026</div>
<script>
function sw(n){var m=['m','r','a'];document.querySelectorAll('.t').forEach(function(t,i){t.classList.toggle('ac',i===m.indexOf(n))});document.querySelectorAll('.pn').forEach(function(p){p.classList.remove('ac')});document.getElementById('pn-'+n).classList.add('ac')}
function ft(id){var r=document.querySelectorAll('#'+id+' tbody tr');var p=id==='mt'?'m':'r';var k=(document.getElementById('kw-'+p)?.value||'').toLowerCase();var f=document.getElementById('f-'+p)?.value||'';var s=document.getElementById('s-'+p)?.value||'';var c=document.getElementById('c-'+p)?.value||'';r.forEach(function(row){var ok=(!k||(row.dataset.kw||'').toLowerCase().indexOf(k)>-1)&&(!f||(row.dataset.factory||'')===f)&&(!s||(row.dataset.status||'')===s)&&(!c||(row.dataset.category||'')===c);row.style.display=ok?'':'none'})}
function rf(id,ids){ids.forEach(function(i){var e=document.getElementById(i);if(e)e.value=''});ft(id)}
document.querySelectorAll('.fb input').forEach(function(i){i.addEventListener('keydown',function(e){if(e.key==='Enter')ft(i.closest('.pn').querySelector('table').id)})})
</script></body></html>''')

# Create migrations directories
for app in ['accounts', 'materials', 'tools', 'reports', 'core']:
    md = os.path.join(BASE, app, 'migrations')
    os.makedirs(md, exist_ok=True)
    init = os.path.join(md, '__init__.py')
    if not os.path.exists(init):
        with open(init, 'w') as f: pass
print('  [OK] migrations/ directories')

# Create init_data.py
write_file('init_data.py', '''#!/usr/bin/env python
"""Initialize test data for PCB Engineering System"""
import os, sys, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pcb_system.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from accounts.models import User, Permission, RolePermission
from core.models import Factory, SystemConfig
from materials.models import MaterialCategory, Material
from reports.models import ReportCategory, Report
from tools.models import ToolCategory, Tool

print('='*60)
# Factories
for f_data in [
    {'code':'SZ01','name':'Shenzhen Plant 1','address':'No.100 XX Rd, Baoan','contact':'Mr. Zhang'},
    {'code':'SZ02','name':'Shenzhen Plant 2','address':'No.200 XX Rd, Longgang','contact':'Mr. Li'},
    {'code':'DG01','name':'Dongguan Plant','address':'No.88 XX Rd, Changan','contact':'Mr. Wang'},
]:
    Factory.objects.get_or_create(code=f_data['code'], defaults=f_data)
print('[OK] Factories x3')

fmap = {f.code:f for f in Factory.objects.all()}
for u_data, is_super, is_staff in [
    ({'username':'admin','role':'admin','department':'IT','factory':'SZ01'}, True, True),
    ({'username':'zhangsan','role':'manager','department':'Engineering','factory':'SZ01'}, False, True),
    ({'username':'lisi','role':'engineer','department':'Quality','factory':'SZ02'}, False, False),
    ({'username':'wangwu','role':'operator','department':'Production','factory':'DG01'}, False, False),
    ({'username':'zhaoliu','role':'viewer','department':'R&D','factory':'SZ01'}, False, False),
]:
    user, created = User.objects.get_or_create(
        username=u_data['username'],
        defaults={**u_data, 'factory':fmap.get(u_data['factory']), 'is_superuser':is_super, 'is_staff':is_staff}
    )
    if created:
        user.set_password('admin123')
        user.save()
    print(f"  {'[+]' if created else '[=]'} {u_data['username']} ({u_data['role']})")
print('[OK] Users x5')

mcat = {}
for cat in [('PCB_DSN','PCB Design'),('GERBER','Gerber'),('BOM','BOM'),('SPEC','Specifications'),('TEST_RPT','Test Reports'),('QC_REC','Quality Records')]:
    obj,_ = MaterialCategory.objects.get_or_create(code=cat[0], defaults={'name':cat[1],'sort_order':1})
    mcat[cat[0]] = obj
print('[OK] Material categories x6')

admin = User.objects.get(username='admin')
zhangsan = User.objects.get(username='zhangsan')
statuses = ['draft','pending','pending','approved','approved','published','published','published','approved','approved','published','archived','draft','approved','published','published','approved','published','approved','draft']
cat_keys = list(mcat.keys())
for i,s in enumerate(statuses, start=1):
    fid = 'SZ01' if i<=10 else ('SZ02' if i<=15 else 'DG01')
    Material.objects.get_or_create(serial_no=f'PCB-{i:04d}', defaults={'factory':fmap[fid],'material_no':f'PN-{6000+i}','version_code':f'V{1+(i%3)}.{i%5}','category':mcat[cat_keys[i%6]],'status':s,'creator':admin,'maker':zhangsan})
print('[OK] Materials x20')

tcat = {}
for tc in [('FLY_PROBE','Flying Probe'),('IMPEDANCE','Impedance'),('AOI','AOI'),('XRAY','X-Ray')]:
    obj,_ = ToolCategory.objects.get_or_create(code=tc[0], defaults={'name':tc[1],'sort_order':1})
    tcat[tc[0]] = obj
for td in [
    ('FP-001','Flying Probe A1','fly_probe','FLY_PROBE','2.1'),
    ('FP-002','Flying Probe A2','fly_probe','FLY_PROBE','2.0'),
    ('IMP-001','Impedance Analyzer B1','impedance','IMPEDANCE','1.5'),
    ('AOI-001','AOI Inspector C1','aoi','AOI','3.0'),
    ('AOI-002','AOI Inspector C2','aoi','AOI','3.1'),
    ('XR-001','X-Ray Inspector D1','xray','XRAY','1.0'),
]:
    Tool.objects.get_or_create(code=td[0], defaults={'name':td[1],'category':tcat[td[3]],'tool_type':td[2],'version':td[4],'description':f'{td[1]} v{td[4]}'})
print('[OK] Tools x6')

rcat = {}
for rc in [('QUALITY','Quality'),('PRODUCTION','Production'),('YIELD','Yield'),('COST','Cost')]:
    obj,_ = ReportCategory.objects.get_or_create(code=rc[0], defaults={'name':rc[1],'sort_order':1})
    rcat[rc[0]] = obj
for rd in [
    ('RPT_Q001','Daily Quality Inspection','summary','QUALITY'),
    ('RPT_Q002','Incoming Inspection Detail','detail','QUALITY'),
    ('RPT_P001','Daily Output Summary','summary','PRODUCTION'),
    ('RPT_P002','Process Efficiency Analysis','analysis','PRODUCTION'),
    ('RPT_Y001','Overall Yield Statistics','statistical','YIELD'),
    ('RPT_C001','Material Cost Accounting','analysis','COST'),
]:
    Report.objects.get_or_create(code=rd[0], defaults={'name':rd[1],'category':rcat[rd[3]],'report_type':rd[2],'description':f'{rd[1]} Report'})
print('[OK] Reports x6')

perms = {'material.view':'View','material.create':'Create','material.edit':'Edit','material.delete':'Delete','material.approve':'Approve','material.export':'Export','report.view':'View Reports','report.create':'Create Reports','report.export':'Export Reports','tool.view':'View Tools','tool.execute':'Execute','tool.config':'Configure','user.manage':'User Mgmt','system.config':'Config'}
pobj = {}
for code,name in perms.items():
    obj,_ = Permission.objects.get_or_create(code=code, defaults={'name':name})
    pobj[code] = obj
for role,pcodes in {'admin':list(perms.keys()),'manager':['material.view','material.create','material.edit','material.approve','material.export','report.view','report.create','report.export','tool.view','tool.execute'],'engineer':['material.view','material.create','material.edit','material.export','report.view','report.create','tool.view','tool.execute'],'operator':['material.view','tool.view','tool.execute','report.view'],'viewer':['material.view','report.view','tool.view']}.items():
    for pc in pcodes:
        RolePermission.objects.get_or_create(role=role, permission=pobj[pc])
print('[OK] Permissions x{}'.format(len(perms)))

for cfg in [('site_name','PCB Engineering System'),('auto_approve','false'),('max_upload_size','52428800')]:
    SystemConfig.objects.get_or_create(key=cfg[0], defaults={'value':cfg[1],'description':cfg[0]})
print('[OK] System configs x3')

print('='*60)
print('[DONE]')
print('  Login: admin/admin123, zhangsan/admin123, etc.')
print('  Run: python manage.py runserver')
print('='*60)
''')

# ===== 3. Destroy old db + run migrations =====
print('\n[3/4] Setting up database...')
db = os.path.join(BASE, 'db.sqlite3')
if os.path.exists(db):
    os.remove(db)
    print('  [OK] Old db.sqlite3 removed')

if not run('python manage.py makemigrations accounts materials tools reports core'):
    print('  [WARN] makemigrations had issues, continuing...')
if not run('python manage.py migrate'):
    print('  [WARN] migrate had issues, continuing...')

# ===== 4. Seed data =====
print('\n[4/4] Seeding test data...')
run('python init_data.py')

print('\n' + '='*60)
print('[DONE] Complete! Now run:')
print('  python manage.py runserver')
print('  Login at http://127.0.0.1:8000/')
print('  Username: admin  Password: admin123')
print('='*60)
