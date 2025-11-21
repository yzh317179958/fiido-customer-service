#!/usr/bin/env python3
"""
P0 人工接管完整流程测试
演示如何使用P0 API实现人工接管
"""

import requests
import json
import time
from typing import Dict, Any

# 配置
API_BASE = "http://localhost:8000"
SESSION_NAME = f"test_session_{int(time.time())}"

class Color:
    """终端颜色"""
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_step(step: str, message: str):
    """打印步骤"""
    print(f"\n{Color.BOLD}{Color.BLUE}[步骤 {step}]{Color.END} {message}")

def print_success(message: str):
    """打印成功"""
    print(f"{Color.GREEN}✅ {message}{Color.END}")

def print_error(message: str):
    """打印错误"""
    print(f"{Color.RED}❌ {message}{Color.END}")

def print_info(message: str):
    """打印信息"""
    print(f"{Color.YELLOW}ℹ️  {message}{Color.END}")

def print_json(data: Dict[Any, Any]):
    """打印JSON"""
    print(json.dumps(data, ensure_ascii=False, indent=2))

def test_ai_chat():
    """测试1：正常AI对话"""
    print_step("1", "测试正常AI对话")

    response = requests.post(
        f"{API_BASE}/api/chat",
        json={
            "message": "你好",
            "user_id": SESSION_NAME
        }
    )

    if response.status_code == 200:
        data = response.json()
        print_success("AI对话成功")
        print_info(f"AI回复: {data.get('message', '')[:100]}...")
        return True
    else:
        print_error(f"AI对话失败: {response.status_code}")
        return False

def test_trigger_keyword():
    """测试2：触发关键词监管"""
    print_step("2", "发送包含关键词的消息触发监管")

    response = requests.post(
        f"{API_BASE}/api/chat",
        json={
            "message": "我要人工客服",
            "user_id": SESSION_NAME
        }
    )

    if response.status_code == 200:
        data = response.json()
        print_success("关键词触发成功")
        print_info(f"AI回复: {data.get('message', '')[:100]}...")
    else:
        print_error(f"请求失败: {response.status_code}")
        return False

    # 等待状态更新
    time.sleep(1)
    return True

def test_get_session_state():
    """测试3：获取会话状态"""
    print_step("3", "获取会话状态")

    response = requests.get(f"{API_BASE}/api/sessions/{SESSION_NAME}")

    if response.status_code == 200:
        data = response.json()
        session = data.get('data', {}).get('session', {})
        status = session.get('status')
        escalation = session.get('escalation')

        print_success(f"会话状态: {status}")

        if status == "pending_manual":
            print_success("✅ 会话已成功转为待人工状态！")

        if escalation:
            print_info("升级信息:")
            print_json(escalation)

        return status == "pending_manual"
    else:
        print_error(f"获取会话失败: {response.status_code}")
        return False

def test_manual_escalate():
    """测试4：手动触发人工升级"""
    print_step("4", "手动触发人工升级（如果未自动触发）")

    response = requests.post(
        f"{API_BASE}/api/manual/escalate",
        json={
            "session_name": SESSION_NAME,
            "reason": "user_request"
        }
    )

    if response.status_code == 200:
        data = response.json()
        print_success("人工升级成功")
        print_json(data.get('data', {}))
        return True
    elif response.status_code == 409:
        print_info("会话已在人工接管中")
        return True
    else:
        print_error(f"人工升级失败: {response.status_code} - {response.text}")
        return False

def test_ai_blocked():
    """测试5：验证AI对话被阻止"""
    print_step("5", "尝试AI对话（应该被拒绝）")

    response = requests.post(
        f"{API_BASE}/api/chat",
        json={
            "message": "现在能回答我吗？",
            "user_id": SESSION_NAME
        }
    )

    if response.status_code == 409:
        print_success("✅ AI对话被正确阻止（409 Conflict）")
        print_info("说明人工接管状态正常工作")
        return True
    else:
        print_error(f"AI对话未被阻止（状态码：{response.status_code}）")
        return False

def test_agent_message():
    """测试6：坐席发送消息"""
    print_step("6", "模拟坐席发送消息")

    response = requests.post(
        f"{API_BASE}/api/manual/messages",
        json={
            "session_name": SESSION_NAME,
            "role": "agent",
            "content": "您好！我是人工客服小王，很高兴为您服务。",
            "agent_info": {
                "agent_id": "agent_001",
                "agent_name": "小王"
            }
        }
    )

    if response.status_code == 200:
        data = response.json()
        print_success("坐席消息发送成功")
        print_json(data)
        return True
    else:
        print_error(f"坐席消息发送失败: {response.status_code} - {response.text}")
        return False

def test_user_message_in_manual():
    """测试7：用户在人工模式下发送消息"""
    print_step("7", "用户在人工接管期间发送消息")

    response = requests.post(
        f"{API_BASE}/api/manual/messages",
        json={
            "session_name": SESSION_NAME,
            "role": "user",
            "content": "好的，我想咨询一下产品问题。"
        }
    )

    if response.status_code == 200:
        data = response.json()
        print_success("用户消息发送成功")
        print_json(data)
        return True
    else:
        print_error(f"用户消息发送失败: {response.status_code} - {response.text}")
        return False

def test_check_history():
    """测试8：检查消息历史"""
    print_step("8", "查看完整消息历史")

    response = requests.get(f"{API_BASE}/api/sessions/{SESSION_NAME}")

    if response.status_code == 200:
        data = response.json()
        session = data.get('data', {}).get('session', {})
        history = session.get('history', [])

        print_success(f"历史消息数量: {len(history)}")

        print_info("\n消息历史:")
        for i, msg in enumerate(history, 1):
            role = msg.get('role')
            content = msg.get('content')[:50]
            agent_name = msg.get('agent_name', '')

            if role == 'agent':
                print(f"  {i}. [{role}] {agent_name}: {content}...")
            else:
                print(f"  {i}. [{role}]: {content}...")

        return True
    else:
        print_error(f"获取历史失败: {response.status_code}")
        return False

def test_release_session():
    """测试9：释放会话，恢复AI"""
    print_step("9", "坐席结束服务，释放会话")

    response = requests.post(
        f"{API_BASE}/api/sessions/{SESSION_NAME}/release",
        json={
            "agent_id": "agent_001",
            "reason": "resolved"
        }
    )

    if response.status_code == 200:
        data = response.json()
        session = data.get('data', {})
        status = session.get('status')

        print_success(f"会话已释放，状态: {status}")

        if status == "bot_active":
            print_success("✅ 会话成功恢复为AI模式！")

        return status == "bot_active"
    else:
        print_error(f"释放会话失败: {response.status_code} - {response.text}")
        return False

def test_ai_restored():
    """测试10：验证AI对话恢复"""
    print_step("10", "验证AI对话功能已恢复")

    response = requests.post(
        f"{API_BASE}/api/chat",
        json={
            "message": "现在AI能回答我了吗？",
            "user_id": SESSION_NAME
        }
    )

    if response.status_code == 200:
        data = response.json()
        print_success("✅ AI对话已恢复正常")
        print_info(f"AI回复: {data.get('message', '')[:100]}...")
        return True
    else:
        print_error(f"AI对话未恢复: {response.status_code}")
        return False

def main():
    """主测试流程"""
    print(f"\n{Color.BOLD}{'='*60}{Color.END}")
    print(f"{Color.BOLD}🧪 P0 人工接管完整流程测试{Color.END}")
    print(f"{Color.BOLD}{'='*60}{Color.END}")
    print(f"\n测试会话: {Color.YELLOW}{SESSION_NAME}{Color.END}\n")

    tests = [
        ("正常AI对话", test_ai_chat),
        ("触发关键词监管", test_trigger_keyword),
        ("获取会话状态", test_get_session_state),
        ("手动触发人工升级", test_manual_escalate),
        ("验证AI被阻止", test_ai_blocked),
        ("坐席发送消息", test_agent_message),
        ("用户消息（人工模式）", test_user_message_in_manual),
        ("查看消息历史", test_check_history),
        ("释放会话", test_release_session),
        ("验证AI恢复", test_ai_restored),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print_error(f"测试异常: {str(e)}")
            failed += 1

        # 测试间隔
        time.sleep(0.5)

    # 总结
    print(f"\n{Color.BOLD}{'='*60}{Color.END}")
    print(f"{Color.BOLD}📊 测试总结{Color.END}")
    print(f"{Color.BOLD}{'='*60}{Color.END}")
    print(f"{Color.GREEN}✅ 通过: {passed}{Color.END}")
    print(f"{Color.RED}❌ 失败: {failed}{Color.END}")
    print(f"{Color.BOLD}总计: {passed + failed}{Color.END}\n")

    if failed == 0:
        print(f"{Color.GREEN}{Color.BOLD}🎉 所有测试通过！P0后端功能正常工作！{Color.END}\n")
    else:
        print(f"{Color.RED}{Color.BOLD}⚠️  部分测试失败，请检查日志。{Color.END}\n")

if __name__ == "__main__":
    main()
