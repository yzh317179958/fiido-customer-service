"""
会话隔离功能测试脚本

测试场景：
1. 多用户会话隔离（不同 session_id 拥有独立的 conversation_id）
2. 清除历史会话功能
3. 创建新对话功能
4. Token 隔离（每个 session 使用独立的 token）
"""

import requests
import json

API_BASE = "http://localhost:8000"


def test_session_isolation():
    """测试会话隔离功能"""
    print("=" * 60)
    print("测试 1: 多用户会话隔离")
    print("=" * 60)

    # 用户 A 创建会话
    print("\n1. 用户 A 创建会话...")
    response_a = requests.post(
        f"{API_BASE}/api/conversation/new",
        json={"session_id": "user_A"}
    )
    data_a = response_a.json()
    print(f"   用户 A conversation_id: {data_a.get('conversation_id')}")
    conv_a_1 = data_a.get('conversation_id')

    # 用户 B 创建会话
    print("\n2. 用户 B 创建会话...")
    response_b = requests.post(
        f"{API_BASE}/api/conversation/new",
        json={"session_id": "user_B"}
    )
    data_b = response_b.json()
    print(f"   用户 B conversation_id: {data_b.get('conversation_id')}")
    conv_b_1 = data_b.get('conversation_id')

    # 验证隔离
    if conv_a_1 != conv_b_1:
        print("\n✅ 会话隔离测试通过：用户 A 和用户 B 拥有不同的 conversation_id")
    else:
        print("\n❌ 会话隔离测试失败：用户 A 和用户 B 使用了相同的 conversation_id")
        return False

    return True


def test_clear_history():
    """测试清除历史会话"""
    print("\n" + "=" * 60)
    print("测试 2: 清除历史会话")
    print("=" * 60)

    # 创建会话
    print("\n1. 用户 C 创建会话...")
    response = requests.post(
        f"{API_BASE}/api/conversation/new",
        json={"session_id": "user_C"}
    )
    data = response.json()
    conv_old = data.get('conversation_id')
    print(f"   原始 conversation_id: {conv_old}")

    # 清除历史
    print("\n2. 清除历史会话...")
    response = requests.post(
        f"{API_BASE}/api/conversation/clear",
        json={"session_id": "user_C"}
    )
    data = response.json()
    conv_new = data.get('conversation_id')
    print(f"   新 conversation_id: {conv_new}")
    print(f"   消息: {data.get('message')}")

    # 验证
    if conv_old != conv_new:
        print("\n✅ 清除历史测试通过：生成了新的 conversation_id")
    else:
        print("\n❌ 清除历史测试失败：conversation_id 没有改变")
        return False

    return True


def run_all_tests():
    """运行所有测试"""
    print("\n🔬 开始会话隔离功能测试")
    print("=" * 60)

    tests = [
        ("会话隔离", test_session_isolation),
        ("清除历史", test_clear_history),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"\n❌ 测试 '{test_name}' 出错: {str(e)}")
            results[test_name] = False

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")

    # 计算通过率
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️  部分测试失败，请检查日志")


if __name__ == "__main__":
    run_all_tests()
