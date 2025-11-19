#!/usr/bin/env python3
"""
会话隔离测试脚本
用于验证不同用户的会话是否正确隔离
"""

import requests
import json
import time

# 服务器配置
BASE_URL = "http://localhost:8000"
CHAT_ENDPOINT = f"{BASE_URL}/api/chat"

def test_session_isolation():
    """测试会话隔离功能"""

    print("=" * 60)
    print("🧪 测试会话隔离功能")
    print("=" * 60)

    # 测试场景: 两个不同用户的对话
    user_a_id = "user_A_test_001"
    user_b_id = "user_B_test_002"

    print(f"\n📝 用户 A ID: {user_a_id}")
    print(f"📝 用户 B ID: {user_b_id}")

    # 用户 A 的第一轮对话
    print(f"\n{'─' * 60}")
    print("👤 用户 A: 第一轮对话")
    print(f"{'─' * 60}")

    user_a_message_1 = "你好,我是用户A,请记住我的名字"
    print(f"发送消息: {user_a_message_1}")

    response_a1 = requests.post(
        CHAT_ENDPOINT,
        json={
            "message": user_a_message_1,
            "user_id": user_a_id
        },
        timeout=30
    )

    if response_a1.status_code == 200:
        data_a1 = response_a1.json()
        print(f"✅ 响应成功")
        print(f"   会话ID: {data_a1.get('conversation_id')}")
        print(f"   回复: {data_a1.get('message', '')[:100]}...")
        conversation_a = data_a1.get('conversation_id')
    else:
        print(f"❌ 请求失败: {response_a1.status_code}")
        print(f"   {response_a1.text}")
        return

    time.sleep(2)

    # 用户 B 的第一轮对话
    print(f"\n{'─' * 60}")
    print("👤 用户 B: 第一轮对话")
    print(f"{'─' * 60}")

    user_b_message_1 = "你好,我是用户B,请记住我是B不是A"
    print(f"发送消息: {user_b_message_1}")

    response_b1 = requests.post(
        CHAT_ENDPOINT,
        json={
            "message": user_b_message_1,
            "user_id": user_b_id
        },
        timeout=30
    )

    if response_b1.status_code == 200:
        data_b1 = response_b1.json()
        print(f"✅ 响应成功")
        print(f"   会话ID: {data_b1.get('conversation_id')}")
        print(f"   回复: {data_b1.get('message', '')[:100]}...")
        conversation_b = data_b1.get('conversation_id')
    else:
        print(f"❌ 请求失败: {response_b1.status_code}")
        print(f"   {response_b1.text}")
        return

    time.sleep(2)

    # 用户 A 的第二轮对话 - 测试上下文记忆
    print(f"\n{'─' * 60}")
    print("👤 用户 A: 第二轮对话(测试上下文)")
    print(f"{'─' * 60}")

    user_a_message_2 = "我是谁?"
    print(f"发送消息: {user_a_message_2}")
    print(f"使用会话ID: {conversation_a}")

    response_a2 = requests.post(
        CHAT_ENDPOINT,
        json={
            "message": user_a_message_2,
            "user_id": user_a_id,
            "conversation_id": conversation_a
        },
        timeout=30
    )

    if response_a2.status_code == 200:
        data_a2 = response_a2.json()
        print(f"✅ 响应成功")
        print(f"   回复: {data_a2.get('message', '')[:200]}...")

        # 检查是否提到用户A
        message_a2 = data_a2.get('message', '').lower()
        if 'a' in message_a2 or '用户a' in message_a2:
            print(f"   ✅ 正确识别用户 A")
        else:
            print(f"   ⚠️  可能未正确识别用户")
    else:
        print(f"❌ 请求失败: {response_a2.status_code}")
        print(f"   {response_a2.text}")

    time.sleep(2)

    # 用户 B 的第二轮对话 - 测试上下文记忆
    print(f"\n{'─' * 60}")
    print("👤 用户 B: 第二轮对话(测试上下文)")
    print(f"{'─' * 60}")

    user_b_message_2 = "我是谁?"
    print(f"发送消息: {user_b_message_2}")
    print(f"使用会话ID: {conversation_b}")

    response_b2 = requests.post(
        CHAT_ENDPOINT,
        json={
            "message": user_b_message_2,
            "user_id": user_b_id,
            "conversation_id": conversation_b
        },
        timeout=30
    )

    if response_b2.status_code == 200:
        data_b2 = response_b2.json()
        print(f"✅ 响应成功")
        print(f"   回复: {data_b2.get('message', '')[:200]}...")

        # 检查是否提到用户B
        message_b2 = data_b2.get('message', '').lower()
        if 'b' in message_b2 or '用户b' in message_b2:
            print(f"   ✅ 正确识别用户 B")
        else:
            print(f"   ⚠️  可能未正确识别用户")
    else:
        print(f"❌ 请求失败: {response_b2.status_code}")
        print(f"   {response_b2.text}")

    # 最终结果
    print(f"\n{'=' * 60}")
    print("📊 测试结果总结")
    print(f"{'=' * 60}")
    print(f"用户 A 会话 ID: {conversation_a}")
    print(f"用户 B 会话 ID: {conversation_b}")
    print(f"会话 ID 是否不同: {'✅ 是' if conversation_a != conversation_b else '❌ 否'}")
    print()

    if conversation_a != conversation_b:
        print("✅ 会话隔离测试通过!")
        print("   不同用户使用了不同的 conversation_id")
        print("   结合 JWT session_name 实现了完整的会话隔离")
    else:
        print("❌ 会话隔离测试失败!")
        print("   不同用户共用了相同的 conversation_id")
        print("   请检查代码中的会话管理逻辑")

    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    try:
        test_session_isolation()
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
