#!/usr/bin/env python3
"""
简单的会话隔离测试
"""
import requests
import uuid

BASE_URL = "http://localhost:8000"

def generate_session():
    """模拟前端生成 session_id"""
    return f"session_{uuid.uuid4().hex[:16]}"

# 用户 A
session_a = generate_session()
print(f"\n👤 用户 A (session: {session_a})")
print("发送: 我叫张三")
resp = requests.post(f"{BASE_URL}/api/chat",
    json={"message": "我叫张三", "user_id": session_a}, timeout=60)
print(f"回复: {resp.json().get('message', '')[:80]}...")

# 用户 B
session_b = generate_session()
print(f"\n👤 用户 B (session: {session_b})")
print("发送: 我叫李四")
resp = requests.post(f"{BASE_URL}/api/chat",
    json={"message": "我叫李四", "user_id": session_b}, timeout=60)
print(f"回复: {resp.json().get('message', '')[:80]}...")

# 用户 A 第二轮
print(f"\n👤 用户 A 第二轮")
print("发送: 我叫什么?")
resp = requests.post(f"{BASE_URL}/api/chat",
    json={"message": "我叫什么?", "user_id": session_a}, timeout=60)
reply = resp.json().get('message', '')
print(f"回复: {reply[:80]}...")

# 验证
if "张三" in reply:
    print("✅ 测试通过 - 用户 A 能记住自己的名字(张三)")
elif "李四" in reply:
    print("❌ 测试失败 - 用户 A 错误地回忆起用户 B 的名字(李四)")
else:
    print("⚠️  无法判断 - 回复中既没有张三也没有李四")
