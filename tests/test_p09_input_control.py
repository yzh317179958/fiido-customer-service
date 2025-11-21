#!/usr/bin/env python3
"""
P0-9 输入控制逻辑测试
测试根据会话状态切换发送接口的功能
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
TEST_SESSION = f"test_p09_{int(time.time())}"

def print_test(name, passed, details=""):
    status = "✅ 通过" if passed else "❌ 失败"
    print(f"\n{status}: {name}")
    if details:
        print(f"   详情: {details}")
    return passed

def test_1_bot_active_normal():
    """测试1: bot_active 状态下正常 AI 对话"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": "你好", "user_id": TEST_SESSION},
            timeout=10
        )
        data = response.json()
        passed = data.get("success") and data.get("message")
        return print_test(
            "bot_active 状态 - AI 对话功能",
            passed,
            f"返回消息: {data.get('message', '')[:50]}..."
        )
    except Exception as e:
        return print_test("bot_active 状态 - AI 对话功能", False, str(e))

def test_2_escalate_to_manual():
    """测试2: 触发人工升级"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/manual/escalate",
            json={"session_name": TEST_SESSION, "reason": "user_request"},
            timeout=10  # 增加超时时间
        )
        data = response.json()
        passed = (
            data.get("success") and
            data.get("data", {}).get("status") == "pending_manual"
        )
        return print_test(
            "转人工功能 - 状态变为 pending_manual",
            passed,
            f"当前状态: {data.get('data', {}).get('status')}"
        )
    except Exception as e:
        return print_test("转人工功能 - 状态变为 pending_manual", False, str(e))

def test_3_pending_manual_blocks_ai():
    """测试3: pending_manual 状态下阻止 AI 对话"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": "测试消息", "user_id": TEST_SESSION},
            timeout=5
        )
        # 应该返回 409 错误
        passed = response.status_code == 409
        return print_test(
            "pending_manual 状态 - 阻止 AI 对话",
            passed,
            f"HTTP 状态码: {response.status_code} (期望 409)"
        )
    except Exception as e:
        return print_test("pending_manual 状态 - 阻止 AI 对话", False, str(e))

def test_4_agent_takeover():
    """测试4: 坐席接入会话"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/sessions/{TEST_SESSION}/takeover",
            json={"agent_id": "agent_test", "agent_name": "测试坐席"},
            timeout=5
        )
        data = response.json()
        passed = (
            data.get("success") and
            data.get("data", {}).get("status") == "manual_live"
        )
        return print_test(
            "坐席接入 - 状态变为 manual_live",
            passed,
            f"当前状态: {data.get('data', {}).get('status')}"
        )
    except Exception as e:
        return print_test("坐席接入 - 状态变为 manual_live", False, str(e))

def test_5_manual_live_user_message():
    """测试5: manual_live 状态下发送用户消息"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/manual/messages",
            json={
                "session_name": TEST_SESSION,
                "role": "user",
                "content": "我是用户消息"
            },
            timeout=5
        )
        data = response.json()
        passed = data.get("success")
        return print_test(
            "manual_live 状态 - 用户消息发送",
            passed,
            "用户消息已写入"
        )
    except Exception as e:
        return print_test("manual_live 状态 - 用户消息发送", False, str(e))

def test_6_manual_live_agent_message():
    """测试6: manual_live 状态下发送坐席消息"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/manual/messages",
            json={
                "session_name": TEST_SESSION,
                "role": "agent",
                "content": "我是坐席回复",
                "agent_info": {
                    "agent_id": "agent_test",
                    "agent_name": "测试坐席"
                }
            },
            timeout=5
        )
        data = response.json()
        passed = data.get("success")
        return print_test(
            "manual_live 状态 - 坐席消息发送",
            passed,
            "坐席消息已写入"
        )
    except Exception as e:
        return print_test("manual_live 状态 - 坐席消息发送", False, str(e))

def test_7_release_session():
    """测试7: 释放会话"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/sessions/{TEST_SESSION}/release",
            json={"agent_id": "agent_test", "reason": "resolved"},
            timeout=5
        )
        data = response.json()
        passed = (
            data.get("success") and
            data.get("data", {}).get("status") == "bot_active"
        )
        return print_test(
            "释放会话 - 状态恢复为 bot_active",
            passed,
            f"当前状态: {data.get('data', {}).get('status')}"
        )
    except Exception as e:
        return print_test("释放会话 - 状态恢复为 bot_active", False, str(e))

def test_8_bot_active_after_release():
    """测试8: 释放后恢复 AI 对话"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": "现在能对话了吗", "user_id": TEST_SESSION},
            timeout=10
        )
        data = response.json()
        passed = data.get("success") and data.get("message")
        return print_test(
            "释放后 - AI 对话恢复正常",
            passed,
            f"返回消息: {data.get('message', '')[:50]}..."
        )
    except Exception as e:
        return print_test("释放后 - AI 对话恢复正常", False, str(e))

def main():
    print("=" * 60)
    print("P0-9 输入控制逻辑测试")
    print("=" * 60)
    print(f"测试会话: {TEST_SESSION}")

    results = []

    # 执行测试
    results.append(test_1_bot_active_normal())
    time.sleep(1)

    results.append(test_2_escalate_to_manual())
    time.sleep(1)

    results.append(test_3_pending_manual_blocks_ai())
    time.sleep(1)

    results.append(test_4_agent_takeover())
    time.sleep(1)

    results.append(test_5_manual_live_user_message())
    time.sleep(1)

    results.append(test_6_manual_live_agent_message())
    time.sleep(1)

    results.append(test_7_release_session())
    time.sleep(1)

    results.append(test_8_bot_active_after_release())

    # 统计结果
    passed_count = sum(1 for r in results if r)
    total_count = len(results)
    percentage = (passed_count / total_count * 100) if total_count > 0 else 0

    print("\n" + "=" * 60)
    print(f"测试结果: {passed_count}/{total_count} 通过 ({percentage:.1f}%)")
    print("=" * 60)

    if passed_count == total_count:
        print("\n✅ P0-9 所有功能测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} 个测试未通过")
        return 1

if __name__ == "__main__":
    exit(main())
