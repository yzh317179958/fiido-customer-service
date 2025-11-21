#!/usr/bin/env python3
"""
简单的会话隔离测试 - 遵循正确的 Coze 实现方式
"""
import requests
import uuid

BASE_URL = "http://localhost:8000"

def generate_session():
    """模拟前端生成 session_id"""
    return f"session_{uuid.uuid4().hex[:16]}"

# 步骤1: 用户 A 打开页面 - 立即创建 conversation
session_a = generate_session()
print(f"\n👤 用户 A 打开页面 (session: {session_a})")
conv_resp = requests.post(f"{BASE_URL}/api/conversation/new",
    json={"session_id": session_a}, timeout=10)
conv_a = conv_resp.json().get("conversation_id")
print(f"   ✅ Conversation 已创建: {conv_a}")

# 步骤2: 用户 A 第一次对话
print("   发送: 我叫张三")
resp = requests.post(f"{BASE_URL}/api/chat",
    json={
        "message": "我叫张三",
        "user_id": session_a,
        "conversation_id": conv_a
    }, timeout=60)
print(f"   回复: {resp.json().get('message', '')[:80]}...")

# 步骤3: 用户 B 打开页面 - 立即创建 conversation
session_b = generate_session()
print(f"\n👤 用户 B 打开页面 (session: {session_b})")
conv_resp = requests.post(f"{BASE_URL}/api/conversation/new",
    json={"session_id": session_b}, timeout=10)
conv_b = conv_resp.json().get("conversation_id")
print(f"   ✅ Conversation 已创建: {conv_b}")

# 步骤4: 用户 B 第一次对话
print("   发送: 我叫李四")
resp = requests.post(f"{BASE_URL}/api/chat",
    json={
        "message": "我叫李四",
        "user_id": session_b,
        "conversation_id": conv_b
    }, timeout=60)
print(f"   回复: {resp.json().get('message', '')[:80]}...")

# 步骤5: 用户 A 第二轮 - 验证记忆
print(f"\n👤 用户 A 第二轮")
print("   发送: 我叫什么?")
resp = requests.post(f"{BASE_URL}/api/chat",
    json={
        "message": "我叫什么?",
        "user_id": session_a,
        "conversation_id": conv_a
    }, timeout=60)
reply = resp.json().get('message', '')
print(f"   回复: {reply[:80]}...")

# 验证
if "张三" in reply:
    print("\n✅ 测试通过 - 用户 A 能记住自己的名字(张三)")
elif "李四" in reply:
    print("\n❌ 测试失败 - 用户 A 错误地回忆起用户 B 的名字(李四)")
else:
    print("\n⚠️  无法判断 - 回复中既没有张三也没有李四")

print(f"\n📋 Conversation ID 验证:")
print(f"   Session A: {session_a}")
print(f"     → Conversation: {conv_a}")
print(f"   Session B: {session_b}")
print(f"     → Conversation: {conv_b}")
print(f"   ✅ ID 不同: {conv_a != conv_b}")
