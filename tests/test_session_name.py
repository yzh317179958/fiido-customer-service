#!/usr/bin/env python3
"""
会话隔离测试脚本 - 基于 session_name 机制
测试逻辑: 每次访问前端界面时生成唯一的 session_id (模拟 sessionStorage)
后端将 session_id 作为 JWT 的 session_name 参数,实现会话隔离
"""

import requests
import json
import time
import uuid

# 服务器配置
BASE_URL = "http://localhost:8000"
CHAT_ENDPOINT = f"{BASE_URL}/api/chat"

def generate_session_id():
    """模拟前端生成唯一的 session_id (类似 sessionStorage)"""
    return f"session_{uuid.uuid4().hex[:16]}"

def print_separator(char="=", width=70):
    """打印分隔线"""
    print(f"\n{char * width}")

def print_sub_separator(char="─", width=70):
    """打印子分隔线"""
    print(f"\n{char * width}")

def test_session_isolation():
    """
    测试会话隔离功能

    测试场景:
    1. 模拟两个不同用户访问前端 (生成两个不同的 session_id)
    2. 每个用户进行多轮对话
    3. 验证两个用户的会话是否完全隔离
    4. 验证每个用户能否记住自己的上下文
    """

    print_separator()
    print("🧪 测试会话隔离功能 - 基于 session_name 机制")
    print_separator()

    print("\n📋 测试说明:")
    print("  • 模拟前端访问: 每次访问生成唯一的 session_id (存储在 sessionStorage)")
    print("  • 后端鉴权: 将 session_id 作为 JWT 的 session_name 参数")
    print("  • 预期结果: 不同 session_id 的对话完全隔离，各自保持上下文")

    # ===== 场景 1: 用户 A 访问前端 =====
    session_a = generate_session_id()
    print_sub_separator()
    print(f"👤 用户 A 访问前端")
    print(f"   生成 session_id: {session_a}")
    print_sub_separator()

    # 用户 A - 第一轮对话
    print(f"\n💬 用户 A - 第 1 轮对话")
    message_a1 = "你好,我的名字是张三,我今年25岁"
    print(f"   发送消息: {message_a1}")

    payload_a1 = {
        "message": message_a1,
        "user_id": session_a  # 使用 session_id 作为 user_id
    }

    print(f"\n📤 请求 payload:")
    print(f"   {json.dumps(payload_a1, ensure_ascii=False, indent=2)}")

    try:
        response_a1 = requests.post(CHAT_ENDPOINT, json=payload_a1, timeout=60)

        if response_a1.status_code == 200:
            data_a1 = response_a1.json()
            print(f"\n✅ 响应成功")
            print(f"   回复: {data_a1.get('message', '')[:150]}...")
        else:
            print(f"\n❌ 请求失败: {response_a1.status_code}")
            print(f"   {response_a1.text}")
            return
    except Exception as e:
        print(f"\n❌ 请求异常: {str(e)}")
        return

    time.sleep(2)

    # ===== 场景 2: 用户 B 访问前端 (新的浏览器窗口) =====
    session_b = generate_session_id()
    print_sub_separator()
    print(f"👤 用户 B 访问前端 (新的浏览器窗口)")
    print(f"   生成 session_id: {session_b}")
    print_sub_separator()

    # 用户 B - 第一轮对话
    print(f"\n💬 用户 B - 第 1 轮对话")
    message_b1 = "你好,我叫李四,我是一名程序员"
    print(f"   发送消息: {message_b1}")

    payload_b1 = {
        "message": message_b1,
        "user_id": session_b  # 使用不同的 session_id
    }

    print(f"\n📤 请求 payload:")
    print(f"   {json.dumps(payload_b1, ensure_ascii=False, indent=2)}")

    try:
        response_b1 = requests.post(CHAT_ENDPOINT, json=payload_b1, timeout=60)

        if response_b1.status_code == 200:
            data_b1 = response_b1.json()
            print(f"\n✅ 响应成功")
            print(f"   回复: {data_b1.get('message', '')[:150]}...")
        else:
            print(f"\n❌ 请求失败: {response_b1.status_code}")
            print(f"   {response_b1.text}")
            return
    except Exception as e:
        print(f"\n❌ 请求异常: {str(e)}")
        return

    time.sleep(2)

    # ===== 场景 3: 用户 A 继续对话 - 测试上下文记忆 =====
    print_sub_separator()
    print(f"👤 用户 A 继续对话 (测试上下文记忆)")
    print_sub_separator()

    print(f"\n💬 用户 A - 第 2 轮对话")
    message_a2 = "我叫什么名字?我多大了?"
    print(f"   发送消息: {message_a2}")
    print(f"   期望回复: 应该记得张三,25岁")

    payload_a2 = {
        "message": message_a2,
        "user_id": session_a  # 使用相同的 session_id
    }

    try:
        response_a2 = requests.post(CHAT_ENDPOINT, json=payload_a2, timeout=60)

        if response_a2.status_code == 200:
            data_a2 = response_a2.json()
            reply_a2 = data_a2.get('message', '')
            print(f"\n✅ 响应成功")
            print(f"   回复: {reply_a2[:200]}...")

            # 验证是否记住了上下文
            if "张三" in reply_a2 or "25" in reply_a2:
                print(f"\n   ✅ 上下文记忆正确 - 记得用户 A 的信息(张三, 25岁)")
            else:
                print(f"\n   ⚠️  可能未正确记忆上下文")
        else:
            print(f"\n❌ 请求失败: {response_a2.status_code}")
    except Exception as e:
        print(f"\n❌ 请求异常: {str(e)}")

    time.sleep(2)

    # ===== 场景 4: 用户 B 继续对话 - 测试上下文记忆 =====
    print_sub_separator()
    print(f"👤 用户 B 继续对话 (测试上下文记忆)")
    print_sub_separator()

    print(f"\n💬 用户 B - 第 2 轮对话")
    message_b2 = "我的名字是什么?我的职业是什么?"
    print(f"   发送消息: {message_b2}")
    print(f"   期望回复: 应该记得李四,程序员")

    payload_b2 = {
        "message": message_b2,
        "user_id": session_b  # 使用相同的 session_id
    }

    try:
        response_b2 = requests.post(CHAT_ENDPOINT, json=payload_b2, timeout=60)

        if response_b2.status_code == 200:
            data_b2 = response_b2.json()
            reply_b2 = data_b2.get('message', '')
            print(f"\n✅ 响应成功")
            print(f"   回复: {reply_b2[:200]}...")

            # 验证是否记住了上下文
            if "李四" in reply_b2 or "程序员" in reply_b2:
                print(f"\n   ✅ 上下文记忆正确 - 记得用户 B 的信息(李四, 程序员)")
            else:
                print(f"\n   ⚠️  可能未正确记忆上下文")
        else:
            print(f"\n❌ 请求失败: {response_b2.status_code}")
    except Exception as e:
        print(f"\n❌ 请求异常: {str(e)}")

    # ===== 场景 5: 关键验证 - 用户 A 不应该知道用户 B 的信息 =====
    time.sleep(2)
    print_sub_separator()
    print(f"🔍 关键验证 - 测试会话隔离")
    print_sub_separator()

    print(f"\n💬 用户 A - 第 3 轮对话 (交叉验证)")
    message_a3 = "你知道李四是谁吗?"
    print(f"   发送消息: {message_a3}")
    print(f"   期望回复: 不应该知道李四(因为李四是用户 B 的信息)")

    payload_a3 = {
        "message": message_a3,
        "user_id": session_a
    }

    try:
        response_a3 = requests.post(CHAT_ENDPOINT, json=payload_a3, timeout=60)

        if response_a3.status_code == 200:
            data_a3 = response_a3.json()
            reply_a3 = data_a3.get('message', '')
            print(f"\n✅ 响应成功")
            print(f"   回复: {reply_a3[:200]}...")

            # 验证会话隔离
            if "程序员" in reply_a3 and "李四" in reply_a3:
                print(f"\n   ❌ 会话隔离失败 - 用户 A 知道了用户 B 的信息!")
                isolation_success = False
            else:
                print(f"\n   ✅ 会话隔离成功 - 用户 A 不知道用户 B 的信息")
                isolation_success = True
        else:
            print(f"\n❌ 请求失败: {response_a3.status_code}")
            isolation_success = False
    except Exception as e:
        print(f"\n❌ 请求异常: {str(e)}")
        isolation_success = False

    # ===== 测试结果总结 =====
    print_separator()
    print("📊 测试结果总结")
    print_separator()

    print(f"\n🔐 会话隔离机制:")
    print(f"   • 用户 A session_id: {session_a}")
    print(f"   • 用户 B session_id: {session_b}")
    print(f"   • Session ID 是否不同: {'✅ 是' if session_a != session_b else '❌ 否'}")

    print(f"\n📝 JWT session_name 机制:")
    print(f"   • 前端生成: 每次访问时生成唯一 session_id (存储在 sessionStorage)")
    print(f"   • 后端鉴权: 将 session_id 作为 JWT 的 session_name 参数")
    print(f"   • 会话隔离: 不同 session_name 的 JWT 访问不同的会话空间")

    print(f"\n✅ 测试结论:")
    if isolation_success and session_a != session_b:
        print(f"   ✅ 会话隔离测试通过!")
        print(f"   ✅ 每个用户的对话完全独立，互不影响")
        print(f"   ✅ JWT session_name 机制工作正常")
    else:
        print(f"   ❌ 会话隔离测试失败!")
        print(f"   ❌ 不同用户的会话可能存在混淆")
        print(f"   ❌ 请检查 JWT session_name 的传递逻辑")

    print_separator()


if __name__ == "__main__":
    try:
        test_session_isolation()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试过程中出现错误:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
