# 工程资料管理系统 V2.0 — 维护文档

> 作者：何瑞鹏 | 版本：V2.0 | 更新时间：2026年5月5日

---

## 一、系统概览

### 技术栈
| 层级 | 技术 |
|------|------|
| 后端框架 | Django 4.2 + Django REST Framework |
| 数据库 | MySQL 8.0 |
| 前端 | HTML5 + Bootstrap 5.3 + jQuery |
| Python | 3.10+ |
| Excel | openpyxl |

### 项目结构
```
D:\ai_one\
├── pcb_system/          # 项目配置
│   ├── settings.py      # 数据库、中间件、权限配置
│   └── urls.py          # 路由表
├── accounts/            # 用户与权限模块
│   ├── models.py        # User / Permission / RolePermission
│   └── views.py         # 用户 API
├── core/                # 核心模块
│   ├── models.py        # Factory / SystemConfig / OperationLog
│   ├── views.py         # API + 页面视图（含登录、用户管理、系统设置）
│   └── utils.py         # 日志工具
├── materials/           # 工程资料模块
│   ├── models.py        # Material / MaterialCategory / MaterialHistory
│   └── views.py         # API + 列表/详情/工具/报表页面视图
├── tools/               # 工具模块
│   ├── models.py        # Tool / ToolExecution / ToolCategory
│   └── views.py         # 工具 API
├── reports/             # 报表模块
│   ├── models.py        # Report / ReportInstance / ReportCategory
│   └── views.py         # 报表 API
├── templates/           # 前端模板
│   ├── base.html        # 公共布局（侧边栏/页脚）
│   ├── login.html       # 登录页
│   ├── dashboard.html   # 首页仪表盘
│   ├── materials/       # 资料页面
│   │   ├── material_list.html
│   │   └── material_detail.html
│   ├── tools/           # 工具页面
│   │   ├── tool_list.html
│   │   └── tool_detail.html
│   ├── reports/         # 报表页面
│   │   ├── report_list.html
│   │   └── report_detail.html
│   └── core/            # 系统页面
│       ├── manage_users.html
│       └── system_settings.html
├── setup_all.py         # 一键初始化脚本
├── requirements.txt     # Python 依赖
└── manage.py            # Django 管理入口
```

### 路由表
| URL | 名称 | 说明 |
|-----|------|------|
| `/` | dashboard | 首页仪表盘 |
| `/login/` | login | 登录页 |
| `/logout/` | logout | 退出登录 |
| `/materials/` | material-list | 资料总纲列表 |
| `/materials/<id>/` | material-detail | 资料详情 |
| `/tools/` | tool-list | 工具输出列表 |
| `/tools/<id>/` | tool-detail | 工具详情 |
| `/reports/` | report-list | 报表管理列表 |
| `/reports/<id>/` | report-detail | 报表详情 |
| `/users/` | manage-users | 用户管理 |
| `/system/` | system-settings | 系统设置 |
| `/admin/` | django-admin | Django 后台（保留） |
| `/api/materials/` | - | 资料 REST API |
| `/api/tools/` | - | 工具 REST API |
| `/api/reports/` | - | 报表 REST API |
| `/api/core/` | - | 核心 API（统计/日志） |

---

## 二、数据库结构

### 2.1 accounts_user（用户表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| username | VARCHAR(150) | 用户名 |
| password | VARCHAR(128) | 密码（哈希） |
| role | VARCHAR(20) | 角色：admin/manager/engineer/operator/viewer |
| phone | VARCHAR(20) | 电话 |
| department | VARCHAR(50) | 部门 |
| factory_id | INT | 所属工厂 FK→core_factory |
| is_active | TINYINT | 是否启用 |
| is_staff | TINYINT | 后台权限 |
| is_superuser | TINYINT | 超级管理员 |
| date_joined | DATETIME | 注册时间 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 2.2 core_factory（工厂表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| code | VARCHAR(20) | 工厂代码（唯一） |
| name | VARCHAR(100) | 工厂名称 |
| address | VARCHAR(200) | 地址 |
| contact | VARCHAR(50) | 联系人 |
| contact_phone | VARCHAR(20) | 联系电话 |
| is_active | TINYINT | 是否启用 |
| created_at | DATETIME | 创建时间 |

### 2.3 materials_material（工程资料主表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| serial_no | VARCHAR(20) | 流水号（唯一） |
| factory_id | INT | 工厂 FK |
| material_no | VARCHAR(50) | 料号 |
| version_code | VARCHAR(10) | 版本编码 |
| process_type | VARCHAR(20) | 工具类型：fly_probe/impedance/aoi/xray/ict/functional/other |
| category_id | INT | 分类 FK→materials_materialcategory |
| status | VARCHAR(20) | 状态：unmade/making/completed/audited/rejected/archived |
| remark | TEXT | 备注 |
| file_path | VARCHAR(500) | 文件路径 |
| file_name | VARCHAR(200) | 文件名 |
| file_size | BIGINT | 文件大小 |
| creator_id | INT | 创建人 FK |
| maker_id | INT | 制作人 FK |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |
| completed_at | DATETIME | 完成时间 |
| approver_id | INT | 审批人 FK |
| approved_at | DATETIME | 审批时间 |
| approve_remark | TEXT | 审批备注 |

### 2.4 materials_materialcategory（资料分类表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| name | VARCHAR(50) | 分类名称 |
| code | VARCHAR(20) | 分类代码（唯一） |
| parent_id | INT | 上级分类 FK |
| description | TEXT | 描述 |
| sort_order | INT | 排序 |
| is_active | TINYINT | 是否启用 |

### 2.5 materials_materialhistory（操作历史表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| material_id | INT | 资料 FK |
| action | VARCHAR(20) | 操作：create/update/delete/approve/reject/publish/archive/download |
| operator_id | INT | 操作人 FK |
| remark | TEXT | 备注 |
| created_at | DATETIME | 操作时间 |

### 2.6 tools_tool（工具表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| name | VARCHAR(100) | 工具名称 |
| code | VARCHAR(20) | 工具代码（唯一） |
| category_id | INT | 分类 FK→tools_toolcategory |
| tool_type | VARCHAR(20) | 类型：fly_probe/impedance/aoi/xray/ict/functional/other |
| description | TEXT | 描述 |
| version | VARCHAR(20) | 版本 |
| sort_order | INT | 排序 |
| config_template | JSON | 配置模板 |
| default_params | JSON | 默认参数 |
| is_active | TINYINT | 是否启用 |
| is_system | TINYINT | 系统工具 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 2.7 tools_toolexecution（工具执行记录表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| tool_id | INT | 工具 FK |
| material_id | INT | 关联资料 FK |
| params | JSON | 执行参数 |
| status | VARCHAR(20) | 状态：pending/running/completed/failed/cancelled |
| input_files | JSON | 输入文件列表 |
| output_files | JSON | 输出文件列表 |
| output_data | JSON | 输出数据 |
| executor_id | INT | 执行人 FK |
| started_at | DATETIME | 开始时间 |
| completed_at | DATETIME | 完成时间 |
| duration | INT | 执行时长（秒） |
| log_output | TEXT | 执行日志 |
| error_message | TEXT | 错误信息 |
| failure_reason | VARCHAR(500) | 失败原因 |
| created_at | DATETIME | 创建时间 |

### 2.8 reports_report（报表定义表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| name | VARCHAR(100) | 报表名称 |
| code | VARCHAR(20) | 报表代码（唯一） |
| category_id | INT | 分类 FK |
| report_type | VARCHAR(20) | 类型：summary/detail/statistical/analysis/custom |
| description | TEXT | 描述 |
| sort_order | INT | 排序 |
| query_sql | TEXT | 查询SQL |
| query_params | JSON | 查询参数 |
| column_config | JSON | 列配置 |
| chart_config | JSON | 图表配置 |
| is_active | TINYINT | 是否启用 |
| is_system | TINYINT | 系统报表 |
| created_by_id | INT | 创建人 FK |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 2.9 reports_reportinstance（报表实例表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| report_id | INT | 报表 FK |
| name | VARCHAR(200) | 实例名称 |
| query_params | JSON | 查询参数 |
| date_from | DATE | 开始日期 |
| date_to | DATE | 结束日期 |
| status | VARCHAR(20) | 状态：pending/completed/failed |
| file | VARCHAR(100) | 报表文件路径 |
| file_format | VARCHAR(10) | 文件格式 |
| row_count | INT | 数据行数 |
| file_size | BIGINT | 文件大小 |
| generated_by_id | INT | 生成人 FK |
| generated_at | DATETIME | 生成时间 |
| completed_at | DATETIME | 完成时间 |

### 2.10 core_systemconfig（系统配置表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| key | VARCHAR(100) | 配置键（唯一） |
| value | TEXT | 配置值 |
| description | TEXT | 描述 |
| is_public | TINYINT | 是否公开 |

### 2.11 core_operationlog（操作日志表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| user_id | INT | 操作人 FK |
| action | VARCHAR(50) | 操作类型 |
| module | VARCHAR(50) | 模块名 |
| object_type | VARCHAR(50) | 对象类型 |
| object_id | INT | 对象 ID |
| remark | TEXT | 备注 |
| created_at | DATETIME | 操作时间 |

---

## 三、日常维护指南

### 3.1 添加新的工具类型

**场景：** 需要增加一种新的工具类型（如 "激光测试"）。

**步骤：**

**① 修改模型常量**

编辑 `materials/models.py`，在 `PROCESS_TYPE_CHOICES` 中添加：
```python
PROCESS_TYPE_CHOICES = [
    ('fly_probe', '飞针测试'),
    ('impedance', '阻抗测试'),
    ('aoi', 'AOI检测'),
    ('xray', 'X-Ray检测'),
    ('ict', 'ICT测试'),
    ('functional', '功能测试'),
    ('laser', '激光测试'),      # 新增
    ('other', '其他'),
]
```

编辑 `tools/models.py`，在 `TOOL_TYPE_CHOICES` 中同步添加：
```python
TOOL_TYPE_CHOICES = [
    ('fly_probe', '飞针测试'),
    # ... 其他已有类型 ...
    ('laser', '激光测试'),      # 新增
]
```

**② 更新前端筛选下拉框**

编辑 `templates/materials/material_list.html`，在工具类型筛选中加入：
```html
<option value="laser">激光测试</option>
```

编辑 `templates/tools/tool_list.html`，在类型筛选加入：
```html
<option value="laser">激光测试</option>
```

**③ 生成迁移并更新数据库**
```powershell
python manage.py makemigrations
python manage.py migrate
```

**④ 在系统中添加对应工具**

进入系统设置页面，或在 Django Admin 中：
1. 创建工具分类（如 `LASER`, "激光测试"）
2. 创建工具实例（如 `LASER-001`, "激光测试仪 A1", tool_type=`laser`）

**⑤ 更新种子数据**（可选）

编辑 `setup_all.py`，在工具列表中加入：
```python
('LASER-001','激光测试仪 A1','laser','LASER','1.0','激光精密测试设备'),
```

然后运行 `python setup_all.py` 重新生成测试数据。

---

### 3.2 添加新的资料状态

**场景：** 需要在"未制作→制作中→已完成→已审核"流程中加入"待确认"状态。

**步骤：**

① 编辑 `materials/models.py`：
```python
STATUS_CHOICES = [
    ('unmade', '未制作'),
    ('pending_confirm', '待确认'),   # 新增
    ('making', '制作中'),
    ('completed', '已完成'),
    ('audited', '已审核'),
    ('rejected', '已驳回'),
    ('archived', '已归档'),
]
```

② 更新前端模板 `templates/materials/material_list.html` 的状态筛选和标签栏。

③ 更新 `materials/views.py` 中 `material_list_page` 的 `status_counts`。

④ 更新 `pcb_system/settings.py` 中的权限逻辑（如有需要）。

⑤ 生成迁移：
```powershell
python manage.py makemigrations materials
python manage.py migrate
```

---

### 3.3 添加新的数据库字段

**场景：** 在资料表中增加一个 "紧急程度" 字段。

**步骤：**

① 编辑 `materials/models.py`，在 Material 类中添加：
```python
urgency = models.CharField('紧急程度', max_length=10, default='normal',
    choices=[('low','低'),('normal','普通'),('high','高'),('urgent','紧急')])
```

② 生成并应用迁移：
```powershell
python manage.py makemigrations materials
python manage.py migrate
```

③ 更新列表模板 `templates/materials/material_list.html`：
- 表头加 `<th>紧急程度</th>`
- 数据行加 `<td>{{ item.get_urgency_display }}</td>`
- 改 colspan 数量

④ 更新详情模板 `templates/materials/material_detail.html`。

⑤ 更新种子数据 `setup_all.py`，在 Material 创建时加上 `urgency`。

⑥ 更新筛选逻辑 `materials/views.py`。

---

### 3.4 添加新的页面/菜单

**场景：** 需要增加一个 "质量看板" 页面。

**步骤：**

① 创建视图（如 `core/views.py`）：
```python
@login_required(login_url='/login/')
def quality_board(request):
    return render(request, 'core/quality_board.html', {})
```

② 创建模板 `templates/core/quality_board.html`（复制 base.html 结构）。

③ 注册路由 `pcb_system/urls.py`：
```python
path('quality/', quality_board, name='quality-board'),
```

④ 在侧边栏 `templates/base.html` 添加菜单项：
```html
<a href="/quality/" class="menu-item">
    <i class="fas fa-clipboard-check"></i> 质量看板
</a>
```

---

### 3.5 修改登录页样式/版权

编辑 `templates/login.html`，修改对应的 HTML 和 CSS。

页脚版权信息在 `templates/base.html` 底部。

---

### 3.6 备份与恢复数据库

**备份 MySQL：**
```powershell
mysqldump -h 192.168.127.131 -u root -pMyPassword123!@# test > backup_20260505.sql
```

**恢复：**
```powershell
mysql -h 192.168.127.131 -u root -pMyPassword123!@# test < backup_20260505.sql
```

---

### 3.7 重新生成测试数据

```powershell
cd D:\ai_one
python setup_all.py
```

脚本会：
1. 修复 settings.py 配置
2. 检查模型代码
3. 重建 MySQL 数据库（DROP + CREATE）
4. 执行迁移
5. 生成 1000 条资料 + 6 个工具 + 150 条执行记录 + 6 个报表 + 18 条报表实例

---

### 3.8 切换数据库

① 编辑 `pcb_system/settings.py`，修改 DATABASES 配置：
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # 或 sqlite3
        'NAME': 'test',
        'USER': 'root',
        'PASSWORD': 'MyPassword123!@#',
        'HOST': '192.168.127.131',
        'PORT': '3306',
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}
```

② 如果用 SQLite，移除文件顶部的 `import pymysql`。

③ 运行 `python setup_all.py`。

---

### 3.9 生产环境部署建议

```powershell
# 安装依赖
pip install -r requirements.txt

# 关闭 DEBUG
# 编辑 settings.py: DEBUG = False

# 收集静态文件
python manage.py collectstatic

# 用 gunicorn 运行（Linux）
gunicorn pcb_system.wsgi:application -b 0.0.0.0:8080 -w 4

# Windows 用 IIS + wfastcgi 或直接 runserver（仅开发）
```

---

## 四、常见问题排查

| 问题 | 原因 | 解决 |
|------|------|------|
| 登录后跳转 404 | LOGIN_REDIRECT_URL 未设置 | settings.py 加 `LOGIN_REDIRECT_URL = '/'` |
| 页面 403 | REST Framework 权限配置 | 开发环境用 `AllowAny` |
| 数据库表不存在 | 未执行 migrate | `python manage.py migrate` |
| InconsistentMigrationHistory | 数据库迁移记录损坏 | 重建数据库 `python setup_all.py` |
| 工具卡片点击 404 | 工具列表未带 id | 查 `tool_list_page` 视图是否从数据库查询 |
| 登录提示"账号已停用" | is_active=False | 用户管理页面重新启用 |
| 页面中文乱码 | 文件编码问题 | 确保文件 UTF-8 编码 |

---

## 五、测试账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 系统管理员 |
| zhangsan | admin123 | 部门经理 |
| lisi | admin123 | 工程师 |
| wangwu | admin123 | 操作员 |
| zhaoliu | admin123 | 查看者 |

---

## 六、GitHub 仓库

- 地址：`https://github.com/heruipeng/pcb-material-system`
- 提交格式：中文描述
- 推送前确认：`git status` → `git add -A` → `git commit -m "..."` → `git push origin main`
