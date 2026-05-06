#!/usr/bin/env python3
"""
获取 DRF Auth Token
用法: python3 get_token.py [--save]

    --save   将 token 保存到 .env 文件，供其他脚本读取
"""
import requests
import sys
import os

BASE_URL = "http://127.0.0.1:8000"
USERNAME = "admin"
PASSWORD = "admin123"


def get_token():
    resp = requests.post(
        f"{BASE_URL}/api/auth/token/",
        json={"username": USERNAME, "password": PASSWORD},
    )
    if resp.status_code == 200:
        return resp.json()["token"]
    else:
        print(f"❌ 获取失败: {resp.status_code} {resp.text}")
        sys.exit(1)


if __name__ == "__main__":
    token = get_token()
    print(f"✅ Token: {token}")

    if "--save" in sys.argv:
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        env_lines = []
        if os.path.exists(env_path):
            with open(env_path) as f:
                env_lines = f.readlines()
        # 替换或追加
        found = False
        for i, line in enumerate(env_lines):
            if line.startswith("API_TOKEN="):
                env_lines[i] = f"API_TOKEN={token}\n"
                found = True
                break
        if not found:
            env_lines.append(f"API_TOKEN={token}\n")
        with open(env_path, "w") as f:
            f.writelines(env_lines)
        print(f"📁 已保存到 {env_path}")
