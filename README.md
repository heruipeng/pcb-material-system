# PCB工程资料管理系统

基于Django框架开发的PCB工程资料管理系统，支持资料总纲、工具输出、报表管理等多个模块，具备完善的权限管理功能。

## 功能模块

### 1. 资料总纲
- 工程资料的创建、编辑、审批、发布流程
- 支持多工厂、多版本管理
- 资料分类管理
- 文件附件管理
- 操作历史记录

### 2. 工具输出模块
- 飞针测试工具
- 阻抗测试工具
- AOI检测工具
- X-Ray检测工具
- ICT测试工具
- 功能测试工具
- 工具执行记录管理
- 工具模板配置

### 3. 报表管理模块
- 汇总报表
- 明细报表
- 统计报表
- 分析报表
- 自定义报表
- 仪表盘
- 定时报表

### 4. 权限管理
- 角色：系统管理员、部门经理、工程师、操作员、查看者
- 细粒度权限控制
- 操作日志记录

## 技术栈

- **后端**: Django 4.2 + Django REST Framework
- **前端**: Bootstrap 5 + jQuery + DataTables
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **缓存**: Redis
- **任务队列**: Celery
- **部署**: Gunicorn

## 安装部署

### 1. 环境要求
- Python 3.8+
- Redis (可选，用于缓存和Celery)

### 2. 安装依赖
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 数据库配置
```bash
# 生成迁移文件
python manage.py makemigrations

# 执行迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser
```

### 4. 启动服务
```bash
# 开发环境
python manage.py runserver 0.0.0.0:8000

# 生产环境
gunicorn pcb_system.wsgi:application -b 0.0.0.0:8000
```

### 5. 初始化数据
```bash
# 创建默认工厂
python manage.py shell -c "from core.models import Factory; Factory.objects.create(name='总部工厂', code='001')"

# 创建默认资料分类
python manage.py shell -c "from materials.models import MaterialCategory; MaterialCategory.objects.create(name='默认分类', code='default')"
```

## 系统架构

```
pcb_system/
├── accounts/          # 用户和权限管理
├── materials/         # 资料总纲模块
├── tools/            # 工具输出模块
├── reports/          # 报表管理模块
├── core/             # 核心功能（工厂、日志、通知等）
├── templates/        # HTML模板
├── static/           # 静态文件
├── media/            # 上传文件
└── manage.py         # Django管理脚本
```

## API接口

### 资料管理
- `GET /api/materials/` - 资料列表
- `POST /api/materials/` - 创建资料
- `GET /api/materials/{id}/` - 资料详情
- `PUT /api/materials/{id}/` - 更新资料
- `DELETE /api/materials/{id}/` - 删除资料
- `POST /api/materials/{id}/approve/` - 审批通过
- `POST /api/materials/{id}/reject/` - 审批驳回
- `GET /api/materials/{id}/history/` - 操作历史

### 工具管理
- `GET /api/tools/` - 工具列表
- `POST /api/tools/{id}/execute/` - 执行工具
- `GET /api/tools/executions/` - 执行记录

### 报表管理
- `GET /api/reports/` - 报表列表
- `POST /api/reports/{id}/generate/` - 生成报表
- `GET /api/reports/instances/` - 报表实例

## 权限说明

| 角色 | 资料管理 | 工具使用 | 报表查看 | 用户管理 | 系统配置 |
|------|---------|---------|---------|---------|---------|
| 系统管理员 | 全部权限 | 全部权限 | 全部权限 | 全部权限 | 全部权限 |
| 部门经理 | 审批权限 | 配置权限 | 全部权限 | - | - |
| 工程师 | 编辑权限 | 使用权限 | 查看/导出 | - | - |
| 操作员 | 创建权限 | 使用权限 | 查看 | - | - |
| 查看者 | 查看权限 | - | 查看 | - | - |

## 开发计划

- [x] 基础框架搭建
- [x] 数据库模型设计
- [x] 权限系统
- [x] 资料管理模块
- [ ] 工具输出模块（完善）
- [ ] 报表管理模块（完善）
- [ ] 前端界面优化
- [ ] 数据导入导出
- [ ] 消息通知系统
- [ ] 工作流引擎

## 联系方式

如有问题或建议，请联系系统管理员。
