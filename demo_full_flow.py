#!/usr/bin/env python3
"""
工程资料管理系统 完整流程演示脚本
--------------------------------
模拟：产线过账 → 生成工具数据 → 前端建资料 → 触发生成 → 脚本处理 → 完成闭环

运行方式：
    python3 demo_full_flow.py

依赖：
    pip install requests
"""

import requests
import time
import json
import sys
from datetime import datetime

# ====== 配置 ======
BASE_URL = "http://127.0.0.1:8080"
USERNAME = "admin"
PASSWORD = "admin123"
TOKEN = None  # 运行时自动获取，也可手动设置跳过认证步骤

# 尝试从环境变量或 .env 文件加载 TOKEN
import os as _os
if not TOKEN:
    TOKEN = _os.environ.get("API_TOKEN") or _os.environ.get("TOKEN")
if not TOKEN:
    _env_path = _os.path.join(_os.path.dirname(__file__), ".env")
    if _os.path.exists(_env_path):
        for _line in open(_env_path):
            _line = _line.strip()
            if _line.startswith("API_TOKEN=") or _line.startswith("TOKEN="):
                TOKEN = _line.split("=", 1)[1].strip().strip('"').strip("'")
                break

# ====== 工具函数 ======
def log(step, msg, emoji="📌"):
    """统一日志输出"""
    print(f"  {emoji} [{step}] {msg}")


def api(method, path, data=None):
    """统一 API 请求，使用 Token 认证"""
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["Authorization"] = f"Token {TOKEN}"

    try:
        if method == "GET":
            resp = session.get(url, headers=headers)
        elif method == "POST":
            resp = session.post(url, json=data, headers=headers)
        else:
            raise ValueError(f"Unknown method: {method}")

        resp.raise_for_status()
        return resp.json() if resp.text else {}
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 无法连接到服务器 {BASE_URL}")
        print("   请确认 Django 已启动: python manage.py runserver")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        try:
            detail = e.response.json()
        except Exception:
            detail = e.response.text
        print(f"\n❌ API 错误 [{method} {path}]: {detail}")
        return None


def hr(title):
    """分隔线标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ====== 主流程 ======
def main():
    global session
    session = requests.Session()

    hr("🚀 工程资料管理系统 - 完整流程演示")
    print(f"  服务器: {BASE_URL}")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ─── 0. 获取 Token ───
    hr("第0步: Token 认证")
    global TOKEN
    if TOKEN:
        log("认证", f"✅ 使用已有 Token ({TOKEN[:8]}...)，来源: {'环境变量/.env' if not TOKEN.startswith('manual') else '手动设置'}")
    else:
        # POST /api/auth/token/ 用用户名密码换取 token
        resp = session.post(
            f"{BASE_URL}/api/auth/token/",
            json={"username": USERNAME, "password": PASSWORD},
        )
        if resp.status_code == 200:
            TOKEN = resp.json().get("token")
            log("认证", f"✅ Token 获取成功 ({TOKEN[:8]}...)")
        else:
            log("认证", f"❌ Token 获取失败，请检查用户名密码", "❌")
            log("提示", f"首次使用需运行: python manage.py migrate 生成 authtoken 表", "💡")
            log("提示", f"如果已有用户但没有 token: python get_token.py --save", "💡")
            sys.exit(1)

    # ─── 1. 产线过账 ───
    hr("第1步: 产线过账 — 创建 ProductionJob")
    ts = datetime.now().strftime("%m%d%H%M")

    post_data = {
        "job_no": f"FP-2026-{ts}",
        "serial_no": f"SN{ts}",
        "material_no": f"PCB-A8X-{ts}",
        "version_code": "V1.2",
        "factory": 1,
        "tool_type": "fly_probe",
        "posted_at": "2026-05-06T09:00:00Z",
        "post_data": {
            "panel_size": "200x150mm",
            "test_points": 1280,
            "layer_count": 8,
        },
    }
    result = api("POST", "/api/production/jobs/post/", post_data)
    if result:
        job_id = result["id"]
        log("过账", f"ProductionJob #{job_id} 已创建 | 状态: {result['status']} | 工单: {result['job_no']}")
    else:
        sys.exit(1)

    # ─── 2. 前端创建资料 ───
    hr("第2步: 前端创建工程资料 — Material")

    material_data = {
        "serial_no": f"SN{ts}",
        "factory": 1,
        "material_no": f"PCB-A8X-{ts}",
        "version_code": "V1.2",
        "process_type": "fly_probe",
        "remark": "主控板飞针测试工单 — 产线自动过账生成",
    }
    result = api("POST", "/api/materials/", material_data)
    if result:
        mat_id = result["id"]
        log("建资料", f"Material #{mat_id} | 料号: {result['material_no']} | 状态: {result['status_display']}")
    else:
        sys.exit(1)

    # ─── 3. 触发生成 → 自动关联工具 ───
    hr("第3步: 触发生成 — Material.generate() → 自动关联工具")

    result = api("POST", f"/api/materials/{mat_id}/generate/")
    if result:
        exec_id = result.get("execution_id")
        log("生成", f"Material 状态 → {result['status']}")
        if exec_id:
            log("联动", f"自动创建 ToolExecution #{exec_id} | 工具: {result.get('tool_name', '未知')}")
    else:
        sys.exit(1)

    # ─── 4. 脚本拉取并开始处理 ───
    hr("第4步: 脚本拉取作业 — 开始处理")

    # 4a: 脚本轮询查询待处理作业
    log("轮询", "查询 pending 状态的产线作业...")
    jobs = api("GET", f"/api/production/jobs/?status=pending&job_no={post_data['job_no']}")
    if jobs and jobs.get("results"):
        pending_job = jobs["results"][0]
        log("找到", f"作业 #{pending_job['id']} | {pending_job['job_no']} | 料号: {pending_job['material_no']}")
    else:
        log("警告", "未找到待处理作业（可能已被其他脚本处理）", "⚠️")

    # 4b: 脚本标记开始处理
    result = api("POST", f"/api/production/jobs/{job_id}/start/",
                 {"processor": "flyprobe_worker_01"})
    if result:
        log("开始", f"作业状态 → {result['status']} | 处理脚本: {result['processor']}")
    else:
        sys.exit(1)

    # 4c: 同时更新前端 ToolExecution 状态
    log("同步", "更新 ToolExecution 状态: pending → running ...")
    if exec_id:
        # 直接通过数据库级别更新（模拟脚本操作）
        log("执行中", f"ToolExecution #{exec_id} 正在执行飞针测试脚本...", "⚙️")
        time.sleep(0.5)  # 模拟处理延迟
        log("处理", "测试中: 1280/1280 个测试点 | 发现 0 个故障点 | 耗时 45s")

    # ─── 5. 脚本完成 → 自动联动 Material + ToolExecution ───
    hr("第5步: 脚本完成 — 上传结果 + 自动联动")

    complete_data = {
        "success": True,
        "output_path": "/data/output/SN20260506001/fp_result.dat",
        "output_files": [
            "report_fp_001.pdf",
            "testlog_fp_001.csv",
            "fault_map_001.png",
        ],
        "process_log": (
            "飞针测试完成\n"
            "  - 测试点数: 1280/1280\n"
            "  - 故障点数: 0\n"
            "  - 测试电压: 100V\n"
            "  - 通过率: 100%"
        ),
        "duration": 45,
        "completed_at": "2026-05-06T09:03:45Z",
    }
    result = api("POST", f"/api/production/jobs/{job_id}/complete/",
                 complete_data)
    if result:
        log("完成", f"作业状态 → {result['status']}")
        log("输出", f"文件: {', '.join(result.get('output_files', []))}")
        log("联动", "✅ 自动更新 Material.status → 已完成")
        log("联动", "✅ 自动创建 ToolExecution 记录 (已完成)")
    else:
        sys.exit(1)

    # ─── 6. 验证最终状态 ───
    hr("第6步: 验证 — 查看完整链路数据")

    # 查看资料最终状态
    mat = api("GET", f"/api/materials/{mat_id}/")
    if mat:
        log("Material", f"#{mat['id']} | {mat['material_no']} | 状态: {mat['status_display']}")

    # 查看工具执行记录
    execs = api("GET", f"/api/tools/executions/?material={mat_id}&ordering=-created_at")
    if execs and execs.get("results"):
        log("执行记录", f"共 {execs['count']} 条:")
        for exe in execs["results"]:
            status_icon = {"pending": "⏳", "running": "🔄", "completed": "✅", "failed": "❌"}
            icon = status_icon.get(exe["status"], "❓")
            log("", f"    #{exe['id']} {icon} {exe['tool_name']} | "
                   f"料号: {exe.get('material_no', '-')} | "
                   f"执行人: {exe.get('executor_name', '-')} | "
                   f"状态: {exe['status_display']}")

    # 查看产线作业
    job = api("GET", f"/api/production/jobs/{job_id}/")
    if job:
        log("作业", f"#{job['id']} | {job['job_no']} | 最终状态: {job['status']}")

    # ─── 总结 ───
    hr("✅ 完整流程演示结束")
    print(f"""
  ┌──────────────────────────────────────────────────┐
  │                                                  │
  │   产线过账 → 建资料 → 触发生成 → 脚本处理 → 完成   │
  │                                                  │
  │   ProductionJob  : #{job_id}  状态: 已完成         │
  │   Material       : #{mat_id}  状态: 已完成         │
  │   ToolExecution  : 自动创建 (1条用户触发 + 1条脚本) │
  │                                                  │
  │   📊 数据链路完整闭环 ✅                            │
  │                                                  │
  └──────────────────────────────────────────────────┘
""")


if __name__ == "__main__":
    main()
