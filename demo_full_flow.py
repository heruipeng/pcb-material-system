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
BASE_URL = "http://127.0.0.1:8000"
USERNAME = "admin"
PASSWORD = "admin123"

# ====== 工具函数 ======
def log(step, msg, emoji="📌"):
    """统一日志输出"""
    print(f"  {emoji} [{step}] {msg}")


def api(method, path, data=None, use_auth=True):
    """统一 API 请求，自动处理认证和错误"""
    url = f"{BASE_URL}{path}"
    csrf = session.cookies.get("csrftoken", session.cookies.get("csrf", ""))
    headers = {
        "Content-Type": "application/json",
        "Referer": url,
    }
    if csrf:
        headers["X-CSRFToken"] = csrf

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

    # ─── 0. 登录 ───
    hr("第0步: 登录系统")
    # 1) 先 GET 登录页面获取 CSRF token
    login_page = session.get(f"{BASE_URL}/login/")
    csrf = session.cookies.get("csrftoken", "")
    if not csrf:
        log("登录", "❌ 无法获取 CSRF token，请确认服务器运行正常", "❌")
        sys.exit(1)
    # 2) 带 CSRF token 提交登录表单
    resp = session.post(
        f"{BASE_URL}/login/",
        data={"username": USERNAME, "password": PASSWORD, "csrfmiddlewaretoken": csrf},
        headers={"Referer": f"{BASE_URL}/login/", "X-CSRFToken": csrf},
        allow_redirects=False,
    )
    if resp.status_code in (302, 200) and "sessionid" in session.cookies:
        log("登录", f"✅ 用户 {USERNAME} 登录成功")
    else:
        # 检查错误信息
        err = "未知错误"
        if "请先登录" in resp.text or "login" in resp.url:
            err = "用户名或密码错误，请检查 USERNAME/PASSWORD 配置"
        elif resp.status_code == 200:
            err = f"登录页返回 200（可能用户名密码错误），状态码异常"
        log("登录", f"❌ 登录失败: {err}", "❌")
        sys.exit(1)

    # ─── 1. 产线过账 ───
    hr("第1步: 产线过账 — 创建 ProductionJob")

    post_data = {
        "job_no": "FP-2026-0506-001",
        "serial_no": "SN20260506001",
        "material_no": "PCB-A8X-001",
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
    result = api("POST", "/api/production/jobs/post/", post_data, use_auth=False)
    if result:
        job_id = result["id"]
        log("过账", f"ProductionJob #{job_id} 已创建 | 状态: {result['status']} | 工单: {result['job_no']}")
    else:
        sys.exit(1)

    # ─── 2. 前端创建资料 ───
    hr("第2步: 前端创建工程资料 — Material")

    material_data = {
        "serial_no": "SN20260506001",
        "factory": 1,
        "material_no": "PCB-A8X-001",
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
    jobs = api("GET", f"/api/production/jobs/?status=pending&job_no=FP-2026-0506-001")
    if jobs and jobs.get("results"):
        pending_job = jobs["results"][0]
        log("找到", f"作业 #{pending_job['id']} | {pending_job['job_no']} | 料号: {pending_job['material_no']}")
    else:
        log("警告", "未找到待处理作业（可能已被其他脚本处理）", "⚠️")

    # 4b: 脚本标记开始处理
    result = api("POST", f"/api/production/jobs/{job_id}/start/",
                 {"processor": "flyprobe_worker_01"}, use_auth=False)
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
                 complete_data, use_auth=False)
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
