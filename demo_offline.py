#!/usr/bin/env python3
"""
工程资料管理系统 - 离线流程模拟（不依赖服务器）
----------------------------------------------
纯 Python 演示完整业务逻辑：每个步骤对应实际代码操作

运行：python3 demo_offline.py
"""

from datetime import datetime, timedelta


# ====== 模拟数据模型（与实际 Django Model 字段一致）======
class MockDB:
    """模拟数据库"""
    def __init__(self):
        self.materials = []
        self.tools = []
        self.tool_executions = []
        self.production_jobs = []
        self._next_id = 1

    def next_id(self):
        rid = self._next_id
        self._next_id += 1
        return rid


db = MockDB()


# ====== 工具函数 ======
def log(step, msg, emoji="📌"):
    print(f"  {emoji} [{step}] {msg}")


def hr(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")


# ====== 模拟数据初始化 ======
def init_system():
    """初始化系统数据（工具定义、工厂等）"""
    # 创建工厂
    db.factory = {"id": 1, "name": "深圳一厂", "code": "SZ01"}
    
    # 创建工具定义
    tools_def = [
        {"id": 1, "name": "飞针测试", "code": "FLY001", "tool_type": "fly_probe",
         "version": "1.0", "is_active": True, "category": "测试类"},
        {"id": 2, "name": "AOI检测", "code": "AOI001", "tool_type": "aoi",
         "version": "1.0", "is_active": True, "category": "检测类"},
        {"id": 3, "name": "阻抗测试", "code": "IMP001", "tool_type": "impedance",
         "version": "1.0", "is_active": True, "category": "测试类"},
    ]
    db.tools = tools_def
    log("初始化", f"加载 {len(tools_def)} 个工具定义 | 工厂: {db.factory['name']}")


# ====== 业务步骤 ======

def step1_production_post():
    """
    第1步：产线过账
    对应代码：production/views.py → ProductionJobViewSet.post()
    产线系统通过 API 传入工单信息
    """
    hr("第1步: 产线过账 → ProductionJob")

    job = {
        "id": db.next_id(),
        "job_no": "FP-2026-0506-001",
        "serial_no": "SN20260506001",
        "material_no": "PCB-A8X-001",
        "version_code": "V1.2",
        "factory_id": 1,
        "tool_type": "fly_probe",
        "post_data": {
            "panel_size": "200x150mm",
            "test_points": 1280,
            "layer_count": 8,
            "source": "MES产线系统",
        },
        "status": "pending",        # 待处理
        "output_path": "",
        "output_files": [],
        "process_log": "",
        "error_message": "",
        "retry_count": 0,
        "posted_at": datetime(2026, 5, 6, 9, 0, 0),
        "created_at": datetime(2026, 5, 6, 9, 0, 0),
    }
    db.production_jobs.append(job)

    log("过账", f"ProductionJob #{job['id']} | 工单: {job['job_no']}")
    log("数据", f"料号: {job['material_no']} | 类型: {job['tool_type']} | 测试点: {job['post_data']['test_points']}")
    log("状态", f"→ {job['status']}（等待脚本拉取处理）")
    return job


def step2_create_material(job):
    """
    第2步：前端创建工程资料
    对应代码：materials/views.py → MaterialViewSet.perform_create()
    员工在「资料总纲」页面新建资料记录
    """
    hr("第2步: 前端创建资料 → Material")

    material = {
        "id": db.next_id(),
        "serial_no": job["serial_no"],
        "factory_id": job["factory_id"],
        "material_no": job["material_no"],
        "version_code": job["version_code"],
        "process_type": job["tool_type"],
        "status": "unmade",          # 未制作
        "remark": "主控板飞针测试工单 — 产线自动过账生成",
        "file_path": "",
        "creator_name": "admin",
        "maker_name": None,
        "created_at": datetime(2026, 5, 6, 9, 1, 0),
        "completed_at": None,
    }
    db.materials.append(material)

    log("建资料", f"Material #{material['id']} | 料号: {material['material_no']} | 版本: {material['version_code']}")
    log("状态", f"→ {material['status']}（未制作）")
    log("关联", f"process_type={material['process_type']} — 将用于后续自动匹配工具")
    return material


def step3_generate(material):
    """
    第3步：触发生成 → 自动关联工具
    对应代码：materials/views.py → MaterialViewSet.generate()
    
    核心逻辑：
    1. Material.status: unmade → making
    2. 按 process_type 自动查找匹配的 Tool
    3. 创建 ToolExecution 记录
    """
    hr("第3步: 触发生成 → Material.generate()")

    # 检查状态
    if material["status"] not in ("unmade", "making"):
        log("错误", f"状态 {material['status']} 不允许生成", "❌")
        return None

    # 更新资料状态
    if material["status"] == "unmade":
        material["status"] = "making"
        material["maker_name"] = "admin"
        log("状态", f"Material {material['status']} | 制作人: {material['maker_name']}")

    # 自动匹配工具（按 tool_type = process_type）
    matched_tool = None
    for t in db.tools:
        if t["tool_type"] == material["process_type"] and t["is_active"]:
            matched_tool = t
            break

    if not matched_tool:
        log("警告", f"未找到 process_type={material['process_type']} 的活跃工具", "⚠️")
        return None

    log("匹配", f"自动关联工具: {matched_tool['name']} (id={matched_tool['id']})")

    # 创建工具执行记录
    execution = {
        "id": db.next_id(),
        "tool_id": matched_tool["id"],
        "tool_name": matched_tool["name"],
        "material_id": material["id"],
        "material_serial_no": material["serial_no"],
        "material_no": material["material_no"],
        "material_version": material["version_code"],
        "params": {"source": "manual_generate"},
        "status": "pending",          # 等待执行
        "executor_name": "admin",
        "started_at": None,
        "completed_at": None,
        "duration": None,
        "output_files": [],
        "created_at": datetime(2026, 5, 6, 9, 2, 0),
        "updated_at": None,
        "updated_by_name": None,
    }
    db.tool_executions.append(execution)

    log("联动", f"✅ 自动创建 ToolExecution #{execution['id']}")
    log("详情", f"工具: {execution['tool_name']} | 关联资料: #{material['id']} | 状态: {execution['status']}")
    return execution


def step4_script_process(job):
    """
    第4步：外部脚本拉取并处理
    对应代码：production/views.py → ProductionJobViewSet.start()
    
    脚本流程：
    1. 轮询 ProductionJob(status=pending)
    2. 标记 start → status=processing
    3. 实际执行工具（飞针测试）
    """
    hr("第4步: 脚本拉取 → 开始处理 → 执行工具")

    # 4a: 脚本轮询
    pending_jobs = [j for j in db.production_jobs if j["status"] == "pending"]
    log("轮询", f"找到 {len(pending_jobs)} 个待处理作业")
    log("锁定", f"脚本 flyprobe_worker_01 锁定作业 #{job['id']}")

    # 4b: 标记开始
    job["status"] = "processing"
    job["processor"] = "flyprobe_worker_01"
    job["processing_at"] = datetime(2026, 5, 6, 9, 3, 0)
    log("开始", f"作业状态 → {job['status']} | 脚本: {job['processor']}")

    # 4c: 更新前端 ToolExecution 状态
    for exe in db.tool_executions:
        if exe["material_id"] == db.materials[0]["id"] and exe["status"] == "pending":
            exe["status"] = "running"
            exe["started_at"] = datetime(2026, 5, 6, 9, 3, 0)
            log("同步", f"ToolExecution #{exe['id']} 状态 → {exe['status']}")
            break

    # 4d: 模拟实际执行
    log("执行", "⚙️ 飞针测试运行中... (1280个测试点)", "⚙️")
    log("进度", "  [████████████████████] 100%  | 故障点: 0 | 通过率: 100%")
    log("耗时", "45 秒")

    return True


def step5_complete(job):
    """
    第5步：脚本完成 → 自动联动
    对应代码：production/views.py → ProductionJobViewSet.complete()
    
    自动联动：
    1. ProductionJob.status → completed
    2. Material.status → completed
    3. 创建 ToolExecution（已完成）
    """
    hr("第5步: 脚本完成 → 自动联动 Material + ToolExecution")

    # 5a: 更新作业
    job["status"] = "completed"
    job["output_path"] = "/data/output/SN20260506001/fp_result.dat"
    job["output_files"] = [
        "report_fp_001.pdf",
        "testlog_fp_001.csv", 
        "fault_map_001.png",
    ]
    job["process_log"] = (
        "飞针测试完成\n"
        "  - 测试点数: 1280/1280\n"
        "  - 故障点: 0\n"
        "  - 通过率: 100%"
    )
    job["duration"] = 45
    job["completed_at"] = datetime(2026, 5, 6, 9, 3, 45)
    log("完成", f"作业状态 → {job['status']}")
    log("输出", f"文件: {', '.join(job['output_files'])}")

    # 5b: 自动关联 Material
    material = db.materials[0]
    material["status"] = "completed"
    material["file_path"] = job["output_path"]
    material["completed_at"] = job["completed_at"]
    log("联动 Material", f"状态 → {material['status']} | completed_at: {material['completed_at'].strftime('%H:%M:%S')}")

    # 5c: 自动创建 ToolExecution（已完成）
    matched_tool = db.tools[0]
    execution = {
        "id": db.next_id(),
        "tool_id": matched_tool["id"],
        "tool_name": matched_tool["name"],
        "material_id": material["id"],
        "material_no": material["material_no"],
        "material_version": material["version_code"],
        "params": job["post_data"],
        "status": "completed",
        "executor_name": job["processor"],
        "started_at": job["processing_at"],
        "completed_at": job["completed_at"],
        "duration": job["duration"],
        "output_files": job["output_files"],
        "created_at": datetime(2026, 5, 6, 9, 3, 45),
        "updated_at": None,
        "updated_by_name": None,
    }
    db.tool_executions.append(execution)
    log("联动 Tool", f"✅ 自动创建 ToolExecution #{execution['id']} | 状态: {execution['status']}")
    log("详情", f"执行人: {execution['executor_name']} | 耗时: {execution['duration']}s")


def step6_verify():
    """第6步：验证最终数据"""
    hr("第6步: 验证 — 完整链路数据")

    # 产线作业
    for j in db.production_jobs:
        log("作业", f"#{j['id']} {j['job_no']} | {j['material_no']} | {j['status']}")

    # 资料
    for m in db.materials:
        log("资料", f"#{m['id']} {m['serial_no']} | {m['material_no']} | {m['status']}")

    # 工具执行
    for e in db.tool_executions:
        icon = {"pending": "⏳", "running": "🔄", "completed": "✅"}.get(e["status"], "❓")
        log("执行", f"#{e['id']} {icon} {e['tool_name']} | {e['material_no']} | "
                   f"v{e['material_version']} | {e['executor_name']} | {e['status']} | {e['duration']}s")


# ====== 运行 ======
if __name__ == "__main__":
    hr("🚀 工程资料管理系统 V2.0 — 离线流程演示")
    print(f"  模拟时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  说明: 纯 Python 模拟 Django ORM 操作，无需启动服务器\n")

    # 初始化
    init_system()

    # 执行业务流程
    job = step1_production_post()           # 产线过账
    material = step2_create_material(job)   # 建资料
    execution = step3_generate(material)    # 触发生成 + 自动关联
    step4_script_process(job)               # 脚本拉取处理
    step5_complete(job)                     # 完成联动
    step6_verify()                          # 验证

    # 总结
    hr("✅ 完整闭环验证通过")

    # 数据链路图
    print(f"""
  ┌─────────────────────────────────────────────────────┐
  │                                                     │
  │  产线过账 ──→ 建资料 ──→ 触发生成 ──→ 脚本处理 ──→ 完成 │
  │                                                     │
  │  ProductionJob #{db.production_jobs[0]['id']}  : completed                      │
  │  Material      #{db.materials[0]['id']}  : completed (unmade→making→completed)  │
  │  ToolExecution : {len(db.tool_executions)} 条记录                                │
  │                                                     │
  │  📊 全部数据链路: {len(db.production_jobs) + len(db.materials) + len(db.tool_executions)} 条记录                  │
  │  🎯 自动化率: 产线脚本自动处理 Material 联动完成        │
  │                                                     │
  └─────────────────────────────────────────────────────┘
""")

    # 代码映射表
    print(f"  📁 代码对照表：")
    print(f"  {'步骤':<20} {'文件':<35} {'函数/类'}")
    print(f"  {'─'*20} {'─'*35} {'─'*25}")
    print(f"  {'产线过账':<20} {'production/views.py':<35} ProductionJobViewSet.post()")
    print(f"  {'建资料':<20} {'materials/views.py':<35} MaterialViewSet.perform_create()")
    print(f"  {'触发生成':<20} {'materials/views.py':<35} MaterialViewSet.generate()")
    print(f"  {'脚本开始':<20} {'production/views.py':<35} ProductionJobViewSet.start()")
    print(f"  {'脚本完成':<20} {'production/views.py':<35} ProductionJobViewSet.complete()")
    print(f"  {'前端列表':<20} {'templates/tools/tool_list.html':<35} loadExecutions()")
    print()
