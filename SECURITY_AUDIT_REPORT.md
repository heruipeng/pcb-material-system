# 🔒 工程资料管理系统 (pcb_system) 安全审计报告

**审计日期**: 2026-05-06  
**审计范围**: 完整代码库（models, views, serializers, middleware, settings, URLs）  
**风险等级**: 🔴 高风险  🟡 中风险  🟢 低风险  ⚪ 信息

---

## 一、数据唯一性

### 🔴 R01 - Material 表缺少 material_no + version_code 唯一约束

**位置**: `materials/models.py` Material 模型  
**问题**: `serial_no` 虽设为 `unique=True`，但 `material_no` + `version_code` 组合无任何唯一性约束。相同料号+版本可以被反复创建（仅流水号不同）。

```python
# 当前：仅 serial_no 唯一
serial_no = models.CharField('流水号', max_length=20, unique=True)
material_no = models.CharField('料号', max_length=50)
version_code = models.CharField('版本编码', max_length=10)
```

**风险**: 同一料号的同一版本可能产生多条记录，导致数据重复、审批混乱、生产指示出错。

**修复建议**:
```python
class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=['material_no', 'version_code', 'factory'],
            name='unique_material_version_per_factory'
        )
    ]
```
或者至少对 `(material_no, version_code)` 加 `unique_together`。

---

### 🟡 R02 - ProductionJob 缺少 serial_no + material_no + version_code 去重约束

**位置**: `production/models.py` ProductionJob 模型  
**问题**: 产线过账的 `post` action 仅通过 `ProductionPostSerializer.validate()` 校验 `job_no` 唯一性，但同一产线数据可能以不同 `job_no` 重复过账。

**风险**: 同一产线数据被多次拉取处理，浪费计算资源，产生冗余结果。

**修复建议**:
```python
class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=['serial_no', 'material_no', 'version_code', 'tool_type'],
            condition=models.Q(status='pending'),
            name='unique_pending_job'
        )
    ]
```

---

### 🟡 R03 - ToolExecution 缺少 (tool, material) 的去重/幂等性保护

**位置**: `tools/models.py` ToolExecution 模型  
**问题**: 同一工具可对同一资料多次创建执行记录，没有约束防止重复提交。

**修复建议**: 在创建执行记录前检查是否已有 `pending` 或 `running` 状态的执行：
```python
existing = ToolExecution.objects.filter(
    tool=tool, material=material, status__in=['pending', 'running']
).exists()
```
或添加数据库层唯一约束 `UniqueConstraint(fields=['tool', 'material'], condition=Q(status__in=['pending', 'running']))`.

---

### 🟢 R04 - 其他模型唯一性（正常）

| 模型 | 约束 | 状态 |
|------|------|------|
| Tool.code | unique=True | ✅ |
| Report.code | unique=True | ✅ |
| Factory.code | unique=True | ✅ |
| SystemConfig.key | unique=True | ✅ |
| Permission.code | unique=True | ✅ |
| RolePermission | unique_together=['role', 'permission'] | ✅ |
| MaterialCategory.code | unique=True | ✅ |
| ToolCategory.code | unique=True | ✅ |
| ReportCategory.code | unique=True | ✅ |

---

## 二、SQL 注入风险

### 🟡 R05 - Report 模型存在 query_sql 字段但未使用

**位置**: `reports/models.py` Report 模型 `query_sql` 字段  
**问题**: 虽然当前代码中 Report 的 `generate` action 使用 Django ORM 查询而非此字段，但该字段的存在意味着未来可能被用于 `raw()` 执行原始 SQL。如果通过 API 传入未校验的 SQL 会被注入。

**修复建议**: 
1. 如果确定不用，删除 `query_sql` 字段
2. 如果保留，必须在序列化器中校验此字段仅允许 SELECT 且无危险关键字

---

### 🟢 R06 - 所有 views.py 均使用 Django ORM

**扫描结果**: 全部 5 个 `views.py` + `core/utils.py` 中，所有数据库操作均通过 Django ORM 的 `filter()`, `get()`, `create()`, `update()`, `save()` 等方法实现，未发现任何 `raw()`, `connection.cursor()`, `extra()` 或字符串拼接 SQL。✅

---

## 三、认证授权

### 🔴 R07 - DRF 默认权限为 AllowAny

**位置**: `pcb_system/settings.py` REST_FRAMEWORK 配置  
```python
'DEFAULT_PERMISSION_CLASSES': [
    'rest_framework.permissions.AllowAny',
],
```

**问题**: 全局默认允许所有 API 请求，权限控制完全依赖自定义 `PermissionMiddleware`。一旦中间件绕过或未覆盖某 ViewSet，该接口将完全开放。

**修复建议**:
```python
'DEFAULT_PERMISSION_CLASSES': [
    'rest_framework.permissions.IsAuthenticated',
],
```
然后在需要开放的接口（如 login）上显式设置 `permission_classes=[AllowAny]`。

---

### 🔴 R08 - 多个 ViewSet 未设置 permission_classes

以下 ViewSet 没有显式 `permission_classes`，完全依赖中间件的路径匹配：

| ViewSet | 风险 | 说明 |
|---------|------|------|
| `SystemConfigViewSet` | 🔴 严重 | 系统配置的增删改查应仅 admin 可访问 |
| `FactoryViewSet` | 🔴 严重 | 工厂 CRUD 应仅管理员 |
| `ReportViewSet` | 🟡 中 | 报表生成可能泄露数据 |
| `DashboardViewSet` | 🟡 中 | 仪表盘配置可能泄露 |
| `ToolViewSet` | 🟡 中 | 工具执行没有权限校验 |
| `MaterialCategoryViewSet` | 🟡 中 | 分类管理无权限限制 |
| `ReportCategoryViewSet` | 🟡 中 | 同上 |
| `ToolCategoryViewSet` | 🟡 中 | 同上 |
| `ToolTemplateViewSet` | 🟡 中 | 同上 |
| `ScheduledReportViewSet` | 🟡 中 | 同上 |
| `FileStorageViewSet` | 🟡 中 | 文件上传无限制 |

**修复建议**: 为每个 ViewSet 添加合适的 `permission_classes`：
```python
# admin only
class SystemConfigViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
# authenticated users
class MaterialViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
```

---

### 🟡 R09 - PermissionMiddleware 的豁免路径过于宽松

**位置**: `accounts/middleware.py`  
```python
exempt_paths = [
    '/admin/',
    '/api/auth/login/',
    '/api/auth/register/',
    '/api/auth/token/',
    '/api/production/',   # ⚠️ 整个 production 路径免认证
    '/static/',
    '/media/',
]
```

**问题**: `/api/production/` 整个路径（包括 GET 列表和 POST 操作）免认证，加上 `ProductionJobViewSet.post/start/complete` 本身设置了 `permission_classes=[AllowAny]`，意味着任何人都可以：
- 查看所有产线作业列表
- 伪造过账数据
- 标记作业完成

**修复建议**:
1. 从 exempt_paths 中移除 `/api/production/`
2. 产线过账接口使用 API Key / Secret 认证而非完全开放
3. 或者在 Nginx/网关层面做 IP 白名单

---

### 🟡 R10 - PermissionMiddleware 中的 Token 认证逻辑脆弱

**位置**: `accounts/middleware.py` `_authenticate_token` 方法  
```python
auth = request.META.get('HTTP_AUTHORIZATION', '')
if auth.startswith('Token '):
    try:
        token = Token.objects.select_related('user').get(key=auth[6:])
```

**问题**: 
1. 手动解析 Token header，而非复用 DRF 的认证后端
2. 未处理 `Bearer` 前缀（部分客户端发送 `Bearer xxx`）
3. Token 明文存储在数据库（DRF 默认行为）

**修复建议**: 如果可能，让 DRF 的 `TokenAuthentication` 先处理，中间件直接读 `request.user`。

---

### 🟢 R11 - 页面路由使用 @login_required

所有 HTML 页面视图（`material_list_page`, `dashboard_page`, `manage_users` 等）都正确使用了 `@login_required(login_url='/login/')` 装饰器。✅

---

## 四、数据校验

### 🟡 R12 - MaterialSerializer 缺少自定义 validate

**位置**: `materials/serializers.py` MaterialSerializer  
**问题**: 创建/更新资料时没有校验：
- `material_no` + `version_code` + `factory` 的组合唯一性（与 R01 关联）
- `file_path` 内容是否合法（如路径遍历字符）
- `serial_no` 格式验证

**修复建议**:
```python
def validate(self, data):
    material_no = data.get('material_no')
    version_code = data.get('version_code')
    factory = data.get('factory')
    if Material.objects.filter(
        material_no=material_no, 
        version_code=version_code, 
        factory=factory
    ).exists():
        raise serializers.ValidationError('相同料号+版本在该工厂已存在')
    return data
```

---

### 🟡 R13 - ProductionCompleteSerializer 的 success 字段默认值可被滥用

**位置**: `production/serializers.py` ProductionCompleteSerializer  
```python
success = serializers.BooleanField(default=True, help_text='是否成功')
```

**问题**: 默认值为 `True`，如果攻击者发送 `complete` 请求时不传 `success` 字段，作业会被标记为 `completed`。

**修复建议**: 将默认值改为 `False`，或者去掉默认值改为 `required=True`：
```python
success = serializers.BooleanField(required=True)
```

---

### 🟡 R14 - change_password 接口无 CSRF 保护

**位置**: `accounts/views.py` UserViewSet.change_password  
**问题**: 修改密码的 POST 接口通过 DRF ViewSet action 暴露。如果使用 SessionAuthentication，CSRF 中间件会保护。但如果客户端带 Token 访问（TokenAuthentication 不强制 CSRF），修改密码可能被 CSRF 攻击利用。

**修复建议**: 
1. 要求修改密码时必须提供旧密码（已实现 ✅）
2. 在修改密码的 endpoint 上添加 `authentication_classes=[SessionAuthentication]` 以强制 CSRF 检查

---

### 🟢 R15 - 文件上传校验（正常）

- `MaterialAttachmentSerializer.validate_file` ✅ 检查扩展名 + 文件大小
- `FileStorageSerializer.validate_file` ✅ 同上
- 文件大小限制 10MB ✅

### ⚪ I01 - ToolOutput 文件字段无校验

**位置**: `tools/serializers.py` ToolOutputSerializer  
**问题**: `file = models.FileField(...)` 在模型中，但序列化器未添加 `validate_file` 方法。不过 ToolOutputViewSet 是 `ReadOnlyModelViewSet`，用户无法直接通过 API 上传，所以实际风险低。

---

## 五、CSRF / Token 安全

### 🟢 R16 - CSRF 和 CORS 配置（正常）

- CSRF 中间件已启用 ✅: `django.middleware.csrf.CsrfViewMiddleware`
- `CSRF_TRUSTED_ORIGINS` 从环境变量读取 ✅
- `CORS_ALLOW_ALL_ORIGINS = False` ✅
- `CORS_ALLOWED_ORIGINS` 从环境变量配置 ✅

### 🟡 R17 - get_token.py 可能泄露 Token

**位置**: `/pcb_system/get_token.py`  
需检查其内容。如果此脚本用于生产环境获取 token，应确保它不被部署到 Web 可访问路径。

### ⚪ I02 - DRF Token 格式

Token 明文存储（DRF `rest_framework.authtoken` 默认行为）。生产环境建议使用 JWT (`djangorestframework-simplejwt`) 或 hashed tokens。

---

## 六、异常处理

### 🔴 R18 - 自定义登录视图存在用户名枚举漏洞

**位置**: `core/views.py` CustomLoginView.form_invalid  
```python
try:
    user = User.objects.get(username=username)
    if not user.is_active:
        form.add_error(None, '该账号已被停用，请联系管理员')  # ← 泄露存在该用户
    elif not user.check_password(...):
        form.add_error(None, '密码错误，请重新输入')          # ← 泄露密码错但用户存在
except User.DoesNotExist:
    form.add_error(None, '用户名不存在')                     # ← 泄露用户不存在
```

**问题**: 攻击者可以根据不同错误消息精确枚举系统中存在的用户名，这是 OWASP 认证类漏洞之一。

**修复建议**: 统一错误消息为 `'用户名或密码错误'`，不区分"用户不存在"和"密码错误"：
```python
def form_invalid(self, form):
    # 始终返回相同的错误消息
    form._errors.clear()
    form.add_error(None, '用户名或密码错误')
    return self.render_to_response(self.get_context_data(form=form))
```

---

### 🟡 R19 - log_operation 中的裸 except

**位置**: `core/utils.py` log_operation 函数  
```python
try:
    OperationLog.objects.create(...)
except Exception as e:
    print(f"记录操作日志失败: {e}")
```

**问题**: 
1. 使用 `print` 而非 `logging` 模块，日志无法被集中收集
2. 捕获范围过宽（`Exception`），会吞掉所有错误
3. 如果数据库不可用，静默失败可能掩盖更严重的问题

**修复建议**:
```python
import logging
logger = logging.getLogger('pcb_system')

try:
    OperationLog.objects.create(...)
except Exception:
    logger.exception('记录操作日志失败')
```

---

### 🟢 R20 - 其他异常处理（正常）

- `production/views.py` complete action 中明确捕获 `Material.DoesNotExist` ✅
- DRF 框架默认返回结构化错误 ✅
- settings.py DEBUG 模式默认 True（需生产环境关闭）⚠️

---

## 七、文件安全

### 🔴 R21 - Report.generate 中的文件名注入风险

**位置**: `reports/views.py` ReportViewSet.generate  
```python
filename = f"{report.code}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
filepath = os.path.join(report_dir, filename)
wb.save(filepath)
```

**问题**: `report.code` 来自数据库，如果攻击者通过 API 创建报表时将 `code` 设为 `../../etc/passwd`，文件名将包含路径遍历字符。虽然 `os.path.join` 会规范化路径，但实际写入仍可能在预期目录外：

```python
# 如果 report.code = "../../tmp/malicious"
# filename = "../../tmp/malicious_20260506_180000.xlsx"
# filepath = os.path.join("/media/reports", "../../tmp/malicious_20260506_180000.xlsx")
# 实际写入: /media/tmp/malicious_20260506_180000.xlsx
```

**修复建议**:
```python
import re
safe_code = re.sub(r'[^\w\-]', '_', report.code)
# 或使用 Django 的 slugify
from django.utils.text import slugify
safe_code = slugify(report.code)
filename = f"{safe_code}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
```

---

### 🟡 R22 - Material.file_path 字段无路径校验

**位置**: `materials/models.py` Material 模型  
```python
file_path = models.CharField('文件路径', max_length=500, blank=True)
```

**问题**: `file_path` 是纯文本字段，可被写入任意内容（如 `../../etc/shadow`），在 `production/views.py` complete action 中直接被赋值：`material.file_path = job.output_path`。如果后续有代码基于此路径读取文件，存在路径遍历风险。

**修复建议**: 在 `output_path` 写入前做路径规范化校验，或改用 `FileField`。

---

### 🟡 R23 - ReportSerializer 中 query_sql 无校验

**位置**: `reports/serializers.py` ReportSerializer  
```python
query_sql = models.TextField('查询SQL', blank=True)
```

序列化器的 `fields` 列表包含 `query_sql`，可通过 API 直接写入任意 SQL 文本。虽然当前未被执行，但存储恶意 SQL 也是一个风险。

**修复建议**: 从序列化器中移除 `query_sql` 字段，或添加 SQL 关键字校验。

---

### 🟢 R24 - Media 文件服务（正常）

- `MEDIA_URL = '/media/'` ，仅在 `DEBUG=True` 时通过 Django 服务 ✅
- `FileField` 使用日期目录 `upload_to='materials/%Y/%m/'` ✅
- 上传文件扩展名白名单校验 ✅

---

## 八、其他发现

### 🟡 R25 - DEBUG 模式默认开启

**位置**: `pcb_system/settings.py`  
```python
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
```

默认值 `'True'` 意味着如果忘记配置环境变量，生产环境将以 DEBUG 模式运行，暴露详细错误堆栈、配置信息、SQL 查询。**这是 Django 安全检查清单的 Top 1 项。**

**修复建议**: 将默认值改为 `'False'`：
```python
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

---

### 🟡 R26 - SECRET_KEY 自动生成可能泄露

**位置**: `pcb_system/settings.py` `_get_or_create_secret_key`  
```python
# 开发回退：写入 .env 避免每次重启重置 session
key = os.urandom(24).hex()
with open(env_file, 'a') as f:
    f.write(f'\nSECRET_KEY={key}\n')
```

**问题**: 如果忘记设置环境变量，程序会把生成的 SECRET_KEY 写入 `.env` 文件。如果代码被提交到版本控制，密钥会泄露。

**修复建议**: 不自动写入文件，改为抛出异常提醒部署者配置：
```python
if not key:
    raise ImproperlyConfigured('SECRET_KEY 未配置，请在 .env 文件中设置')
```

---

### ⚪ I03 - OperationLog 模型字段定义顺序

**位置**: `core/models.py` OperationLog 模型  
`ip_address` 和 `user_agent` 字段定义在 `save()` 方法**之后**，虽然 Python/Django 可以正确处理（metaclass 收集），但这是不良代码风格，容易导致维护混淆。

**修复建议**: 将字段定义移到 `save()` 方法之前。

---

### 🟡 R27 - 密码硬编码在管理命令中

**位置**: `materials/management/commands/init_test_data.py`  
```python
users_data = [
    ('admin', 'admin123', 'admin'),
    ('zhangsan', 'pass123', 'engineer'),
    ('lisi', 'pass123', 'operator'),
]
```

**问题**: 密码以明文形式硬编码在代码中。虽然这是测试命令，但如果被误部署到生产环境，这些弱密码会成为安全隐患。

**修复建议**: 添加环境检查，禁止在生产环境执行：
```python
from django.conf import settings
if not settings.DEBUG:
    raise CommandError('禁止在生产环境执行此命令')
```

---

### ⚪ I04 - 数据库密码硬编码

**位置**: `pcb_system/settings.py`  
```python
'PASSWORD': os.getenv('DB_PASSWORD', 'MyPassword123!@#'),
```

默认 fallback 包含明文密码。应去掉默认值或使用空字符串，强制通过环境变量配置。

---

## 九、风险评估汇总

| 编号 | 类别 | 级别 | 简述 |
|------|------|------|------|
| R01 | 数据唯一性 | 🔴 | Material 缺少 material_no+version_code 唯一约束 |
| R07 | 认证授权 | 🔴 | DRF 默认 AllowAny，依赖中间件 |
| R08 | 认证授权 | 🔴 | 10+ 个 ViewSet 无 permission_classes |
| R18 | 异常处理 | 🔴 | 登录页用户名枚举漏洞 |
| R21 | 文件安全 | 🔴 | Report.generate 文件名路径遍历 |
| R02 | 数据唯一性 | 🟡 | ProductionJob 缺少去重约束 |
| R03 | 数据唯一性 | 🟡 | ToolExecution 缺少幂等性保护 |
| R05 | SQL注入 | 🟡 | query_sql 字段存在（未使用但可被写入） |
| R09 | 认证授权 | 🟡 | /api/production/ 全路径免认证 |
| R10 | 认证授权 | 🟡 | Token 认证逻辑脆弱 |
| R12 | 数据校验 | 🟡 | MaterialSerializer 无自定义 validate |
| R13 | 数据校验 | 🟡 | ProductionCompleteSerializer success 默认值 True |
| R14 | 数据校验 | 🟡 | change_password Token 认证下无 CSRF 保护 |
| R17 | Token安全 | 🟡 | get_token.py 可能暴露 Token |
| R19 | 异常处理 | 🟡 | log_operation 裸 except + print |
| R22 | 文件安全 | 🟡 | Material.file_path 无路径校验 |
| R23 | 文件安全 | 🟡 | ReportSerializer 允许写入 query_sql |
| R25 | 部署安全 | 🟡 | DEBUG 默认 True |
| R26 | 密钥管理 | 🟡 | SECRET_KEY 自动写入 .env |
| R27 | 凭证安全 | 🟡 | 管理命令硬编码明文密码 |

---

## 十、优先修复建议

### 🚨 立即修复（P0）
1. **R25**: 将 DEBUG 默认值改为 `False`
2. **R18**: 修复登录页用户名枚举，统一错误提示
3. **R07**: 将 DRF DEFAULT_PERMISSION_CLASSES 改为 `IsAuthenticated`
4. **R08**: 为 SystemConfigViewSet、FactoryViewSet 等关键 ViewSet 添加权限

### ⚡ 尽快修复（P1）
5. **R01**: Material 表添加 (material_no, version_code, factory) 唯一约束
6. **R21**: Report.generate 中对 report.code 做路径字符过滤
7. **R09**: 限制 /api/production/ 的认证豁免范围
8. **R13**: ProductionCompleteSerializer success 改为 required=True

### 📋 计划修复（P2）
9. **R12**: MaterialSerializer 添加业务规则校验
10. **R19**: log_operation 改用 logging 模块
11. **R26**: 移除 SECRET_KEY 自动写入逻辑
12. **R22**: Material.file_path 添加路径遍历防护
13. **R27**: init_test_data 添加环境检查

---

*报告由自动化安全审计生成，建议结合人工 Code Review 和渗透测试进一步验证。*
