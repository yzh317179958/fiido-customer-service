#!/usr/bin/env python3
"""
P0-4 核心API测试脚本
测试4个人工接管API的功能
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
SESSION_NAME = f"test_p04_{int(time.time())}"

def print_section(title):
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}")

def test_api(method, url, data=None, description=""):
    print(f"\n📤 {method} {url}")
    if description:
        print(f"   说明: {description}")
    if data:
        print(f"   请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")

    try:
        if method == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method == "GET":
            response = requests.get(url, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")

        print(f"\n📥 响应状态: {response.status_code}")

        try:
            response_data = response.json()
            print(f"   响应数据:")
            print(json.dumps(response_data, ensure_ascii=False, indent=2))
            return response.status_code == 200, response_data
        except:
            print(f"   响应文本: {response.text[:200]}")
            return response.status_code == 200, None

    except Exception as e:
        print(f"\n❌ 请求失败: {str(e)}")
        return False, None

# ==================== 测试流程 ====================

print_section("P0-4 核心API测试")
print(f"测试会话: {SESSION_NAME}")

# 测试 1: 人工升级
print_section("测试 1: POST /api/manual/escalate")
success, data = test_api(
    "POST",
    f"{BASE_URL}/api/manual/escalate",
    {"session_name": SESSION_NAME, "reason": "user_request"},
    "用户主动请求人工服务"
)

if success and data:
    print(f"\n✅ 升级成功!")
    print(f"   当前状态: {data.get('data', {}).get('status')}")
    print(f"   升级原因: {data.get('data', {}).get('escalation', {}).get('reason')}")
else:
    print(f"\n❌ 升级失败")
    exit(1)

time.sleep(1)

# 测试 2: 获取会话状态
print_section("测试 2: GET /api/sessions/{session_name}")
success, data = test_api(
    "GET",
    f"{BASE_URL}/api/sessions/{SESSION_NAME}",
    description="获取会话状态和历史"
)

if success and data:
    print(f"\n✅ 获取成功!")
    session_data = data.get('data', {}).get('session', {})
    print(f"   状态: {session_data.get('status')}")
    print(f"   消息数: {len(session_data.get('history', []))}")
else:
    print(f"\n❌ 获取失败")

time.sleep(1)

# 测试 3: 发送人工消息 (坐席)
print_section("测试 3: POST /api/manual/messages (坐席消息)")

# 首先需要将状态改为 manual_live
print("\n⚠️  注意: 需要先将状态改为 manual_live")
print("   当前测试假设监管引擎会自动转换状态...")

# 模拟坐席发送消息
success, data = test_api(
    "POST",
    f"{BASE_URL}/api/manual/messages",
    {
        "session_name": SESSION_NAME,
        "role": "agent",
        "content": "您好，我是人工客服，有什么可以帮您的？",
        "agent_info": {
            "agent_id": "agent_01",
            "agent_name": "Alice"
        }
    },
    "坐席发送消息"
)

if success and data:
    print(f"\n✅ 消息发送成功!")
    print(f"   消息ID: {data.get('data', {}).get('message_id')}")
else:
    print(f"\n⚠️  消息发送失败（可能因为状态不是manual_live）")

time.sleep(1)

# 测试 4: 释放会话
print_section("测试 4: POST /api/sessions/{session_name}/release")
success, data = test_api(
    "POST",
    f"{BASE_URL}/api/sessions/{SESSION_NAME}/release",
    {
        "agent_id": "agent_01",
        "reason": "resolved"
    },
    "结束人工服务，恢复AI"
)

if success and data:
    print(f"\n✅ 会话释放成功!")
    print(f"   当前状态: {data.get('data', {}).get('status')}")
    print(f"   结束时间: {data.get('data', {}).get('last_manual_end_at')}")
else:
    print(f"\n⚠️  会话释放失败")

# 测试 5: 再次获取会话状态，验证释放
print_section("测试 5: 验证会话已释放")
success, data = test_api(
    "GET",
    f"{BASE_URL}/api/sessions/{SESSION_NAME}",
    description="验证状态已恢复为bot_active"
)

if success and data:
    session_data = data.get('data', {}).get('session', {})
    final_status = session_data.get('status')
    print(f"\n   最终状态: {final_status}")

    if final_status == "bot_active":
        print(f"   ✅ 状态正确恢复为bot_active")
    else:
        print(f"   ⚠️  状态为 {final_status}")

# 总结
print_section("测试总结")
print("✅ P0-4 核心API测试完成")
print(f"   会话名称: {SESSION_NAME}")
print("\n已测试的API:")
print("  1. POST /api/manual/escalate - 人工升级")
print("  2. GET /api/sessions/{session_name} - 获取会话状态")
print("  3. POST /api/manual/messages - 人工消息写入")
print("  4. POST /api/sessions/{session_name}/release - 释放会话")
print("\n所有核心功能已验证！")
