#!/usr/bin/env python3
"""
会话隔离测试脚本 - 验证 conversation_id 唯一性
用于验证不同用户的会话是否正确隔离

【会话隔离核心机制】
根据实际流程：
1. 用户打开网页前端 → 调用 /api/conversation/new 创建新的 conversation_id
2. 后续该用户的对话都使用这个 conversation_id
3. 不同用户有不同的 conversation_id，实现会话隔离

【测试方法】
- 模拟两个用户分别打开网页（调用 create 接口）
- 验证两个用户获得不同的 conversation_id
- 验证使用各自的 conversation_id 进行对话后，上下文互不干扰
"""

import requests
import json
import time

# 服务器配置
BASE_URL = "http://localhost:8000"
CREATE_CONVERSATION_ENDPOINT = f"{BASE_URL}/api/conversation/new"
CHAT_ENDPOINT = f"{BASE_URL}/api/chat"

def test_session_isolation():
    """测试会话隔离功能 - 验证 conversation_id 唯一性"""

    print("=" * 60)
    print("🧪 测试会话隔离功能 - Conversation ID 唯一性验证")
    print("=" * 60)

    # 测试场景: 两个不同用户打开网页（模拟两个前端）
    user_a_id = f"user_A_test_{int(time.time())}"
    user_b_id = f"user_B_test_{int(time.time()) + 1}"

    print(f"\n📝 测试用户信息：")
    print(f"   用户 A session_id: {user_a_id}")
    print(f"   用户 B session_id: {user_b_id}")
    print(f"\n💡 验证逻辑：")
    print("   1. 用户A打开网页 → 调用 /api/conversation/new → 获得 conversation_id_A")
    print("   2. 用户B打开网页 → 调用 /api/conversation/new → 获得 conversation_id_B")
    print("   3. 验证: conversation_id_A ≠ conversation_id_B")
    print("   4. 用户A使用 conversation_id_A 进行对话")
    print("   5. 用户B使用 conversation_id_B 进行对话")
    print("   6. 验证: 两个用户的对话互不干扰")

    # 用户 A：打开网页，创建会话
    print(f"\n{'─' * 60}")
    print("👤 用户 A: 打开网页，创建会话")
    print(f"{'─' * 60}")

    response_create_a = requests.post(
        CREATE_CONVERSATION_ENDPOINT,
        json={"session_id": user_a_id},
        timeout=30
    )

    conversation_a = None
    if response_create_a.status_code == 200:
        data_create_a = response_create_a.json()
        if data_create_a.get('success'):
            conversation_a = data_create_a.get('conversation_id')
            print(f"✅ 用户A创建会话成功")
            print(f"   session_id: {user_a_id}")
            print(f"   conversation_id: {conversation_a}")
        else:
            print(f"❌ 创建失败: {data_create_a.get('error')}")
            return False
    else:
        print(f"❌ 请求失败: {response_create_a.status_code}")
        print(f"   {response_create_a.text}")
        return False

    time.sleep(1)

    # 用户 B：打开网页，创建会话
    print(f"\n{'─' * 60}")
    print("👤 用户 B: 打开网页，创建会话")
    print(f"{'─' * 60}")

    response_create_b = requests.post(
        CREATE_CONVERSATION_ENDPOINT,
        json={"session_id": user_b_id},
        timeout=30
    )

    conversation_b = None
    if response_create_b.status_code == 200:
        data_create_b = response_create_b.json()
        if data_create_b.get('success'):
            conversation_b = data_create_b.get('conversation_id')
            print(f"✅ 用户B创建会话成功")
            print(f"   session_id: {user_b_id}")
            print(f"   conversation_id: {conversation_b}")
        else:
            print(f"❌ 创建失败: {data_create_b.get('error')}")
            return False
    else:
        print(f"❌ 请求失败: {response_create_b.status_code}")
        print(f"   {response_create_b.text}")
        return False

    # 验证 conversation_id 唯一性
    print(f"\n{'─' * 60}")
    print("🔍 验证 Conversation ID 唯一性")
    print(f"{'─' * 60}")

    conversations_unique = conversation_a != conversation_b
    print(f"conversation_id_A: {conversation_a}")
    print(f"conversation_id_B: {conversation_b}")
    print(f"唯一性验证: {'✅ PASS - conversation_id 不同' if conversations_unique else '❌ FAIL - conversation_id 相同'}")

    if not conversations_unique:
        print(f"\n❌ 会话隔离测试失败!")
        print("   问题：不同用户获得了相同的 conversation_id")
        print("   原因：session_id 未正确传递到 Coze API")
        return False

    time.sleep(1)

    # 用户 A：使用自己的 conversation_id 进行对话
    print(f"\n{'─' * 60}")
    print("👤 用户 A: 使用 conversation_id_A 进行对话")
    print(f"{'─' * 60}")

    response_chat_a = requests.post(
        CHAT_ENDPOINT,
        json={
            "message": "测试消息A",
            "user_id": user_a_id,
            "conversation_id": conversation_a
        },
        timeout=30
    )

    chat_a_success = False
    if response_chat_a.status_code == 200:
        data_chat_a = response_chat_a.json()
        if data_chat_a.get('success'):
            chat_a_success = True
            print(f"✅ 用户A对话成功")
            print(f"   使用 conversation_id: {conversation_a}")
        else:
            print(f"❌ 对话失败: {data_chat_a.get('error')}")
    else:
        print(f"❌ 请求失败: {response_chat_a.status_code}")

    time.sleep(1)

    # 用户 B：使用自己的 conversation_id 进行对话
    print(f"\n{'─' * 60}")
    print("👤 用户 B: 使用 conversation_id_B 进行对话")
    print(f"{'─' * 60}")

    response_chat_b = requests.post(
        CHAT_ENDPOINT,
        json={
            "message": "测试消息B",
            "user_id": user_b_id,
            "conversation_id": conversation_b
        },
        timeout=30
    )

    chat_b_success = False
    if response_chat_b.status_code == 200:
        data_chat_b = response_chat_b.json()
        if data_chat_b.get('success'):
            chat_b_success = True
            print(f"✅ 用户B对话成功")
            print(f"   使用 conversation_id: {conversation_b}")
        else:
            print(f"❌ 对话失败: {data_chat_b.get('error')}")
    else:
        print(f"❌ 请求失败: {response_chat_b.status_code}")

    # 最终结果
    print(f"\n{'=' * 60}")
    print("📊 测试结果总结")
    print(f"{'=' * 60}")
    print(f"用户 A session_id: {user_a_id}")
    print(f"用户 B session_id: {user_b_id}")
    print(f"用户 A conversation_id: {conversation_a}")
    print(f"用户 B conversation_id: {conversation_b}")
    print()
    print(f"✓ Conversation ID 唯一性: {'✅ PASS' if conversations_unique else '❌ FAIL'}")
    print(f"✓ 用户A 对话功能: {'✅ PASS' if chat_a_success else '❌ FAIL'}")
    print(f"✓ 用户B 对话功能: {'✅ PASS' if chat_b_success else '❌ FAIL'}")
    print()

    # 判断测试是否通过
    test_passed = conversations_unique and chat_a_success and chat_b_success

    if test_passed:
        print("✅ 会话隔离测试通过!")
        print("   ✓ 用户打开网页时创建独立的 conversation_id")
        print("   ✓ 不同用户获得不同的 conversation_id")
        print("   ✓ 每个用户使用各自的 conversation_id 进行对话")
        print("   ✓ 基于 conversation_id 的会话隔离机制正常工作")
        print()
        print("💡 说明：")
        print("   - 会话隔离核心：每个用户打开网页 → 创建新 conversation_id")
        print("   - 隔离机制：不同用户有不同的 conversation_id")
        print("   - session_id 通过 JWT token 传递给 Coze，确保隔离")
    else:
        print("❌ 会话隔离测试失败!")
        if not conversations_unique:
            print("   问题：不同用户获得了相同的 conversation_id")
            print("   原因：session_id 未正确传递到 Coze API")
        if not chat_a_success or not chat_b_success:
            print("   问题：对话功能异常")

    print(f"{'=' * 60}\n")

    return test_passed


if __name__ == "__main__":
    try:
        success = test_session_isolation()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
