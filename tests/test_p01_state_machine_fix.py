"""
测试 P0-1: 状态机修复
验证 pending_manual 状态下 AI 对话被正确阻止
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_p01_pending_manual_blocks_ai():
    """测试: pending_manual 状态下 AI 对话被阻止"""
    print("\n" + "="*60)
    print("测试 P0-1: pending_manual 状态下 AI 对话被阻止")
    print("="*60)

    session_name = f"test_p01_{int(time.time())}"

    # 步骤1: 正常AI对话(应该成功)
    print(f"\n1️⃣  步骤1: 正常AI对话 (session: {session_name})")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": "你好",
            "user_id": session_name
        },
        timeout=30
    )

    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ AI对话成功")
        data = response.json()
        print(f"   回复: {data.get('message', '')[:50]}...")
    else:
        print(f"   ❌ AI对话失败: {response.text}")
        return False

    # 步骤2: 触发人工升级
    print(f"\n2️⃣  步骤2: 触发人工升级 (转为 pending_manual)")
    response = requests.post(
        f"{BASE_URL}/api/manual/escalate",
        json={
            "session_name": session_name,
            "reason": "user_request"
        },
        timeout=10
    )

    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ 升级成功")
        print(f"   状态: {data.get('data', {}).get('session', {}).get('status')}")
    else:
        print(f"   ❌ 升级失败: {response.text}")
        return False

    # 步骤3: 尝试AI对话(应该被阻止,返回409)
    print(f"\n3️⃣  步骤3: 尝试AI对话 (应该返回 409)")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": "再次对话",
            "user_id": session_name
        },
        timeout=10
    )

    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.text}")

    if response.status_code == 409:
        data = response.json()
        detail = data.get('detail', '')
        if 'SESSION_IN_MANUAL_MODE' in detail and 'pending_manual' in detail:
            print(f"   ✅ AI对话被正确阻止")
            print(f"   错误信息: {detail}")
            return True
        else:
            print(f"   ⚠️  返回409但错误信息不正确")
            print(f"   期望: SESSION_IN_MANUAL_MODE: pending_manual")
            print(f"   实际: {detail}")
            return False
    else:
        print(f"   ❌ 测试失败: 期望返回 409, 实际返回 {response.status_code}")
        return False


def test_p01_manual_live_blocks_ai():
    """测试: manual_live 状态下 AI 对话被阻止"""
    print("\n" + "="*60)
    print("测试 P0-1: manual_live 状态下 AI 对话被阻止")
    print("="*60)

    session_name = f"test_p01_live_{int(time.time())}"

    # 步骤1: 触发人工升级
    print(f"\n1️⃣  步骤1: 触发人工升级 (session: {session_name})")
    response = requests.post(
        f"{BASE_URL}/api/manual/escalate",
        json={
            "session_name": session_name,
            "reason": "user_request"
        },
        timeout=10
    )

    if response.status_code != 200:
        print(f"   ❌ 升级失败: {response.text}")
        return False

    print(f"   ✅ 升级成功,状态: pending_manual")

    # 步骤2: 坐席接入(转为 manual_live)
    print(f"\n2️⃣  步骤2: 坐席接入 (转为 manual_live)")
    response = requests.post(
        f"{BASE_URL}/api/sessions/{session_name}/takeover",
        json={
            "agent_id": "test_agent_001",
            "agent_name": "测试客服"
        },
        timeout=10
    )

    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        status = data.get('data', {}).get('status')
        print(f"   ✅ 接入成功,状态: {status}")
    else:
        print(f"   ❌ 接入失败: {response.text}")
        return False

    # 步骤3: 尝试AI对话(应该被阻止,返回409)
    print(f"\n3️⃣  步骤3: 尝试AI对话 (应该返回 409)")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": "尝试AI对话",
            "user_id": session_name
        },
        timeout=10
    )

    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.text}")

    if response.status_code == 409:
        data = response.json()
        detail = data.get('detail', '')
        if 'SESSION_IN_MANUAL_MODE' in detail and 'manual_live' in detail:
            print(f"   ✅ AI对话被正确阻止")
            print(f"   错误信息: {detail}")
            return True
        else:
            print(f"   ⚠️  返回409但错误信息不正确")
            return False
    else:
        print(f"   ❌ 测试失败: 期望返回 409, 实际返回 {response.status_code}")
        return False


def test_p01_stream_blocked():
    """测试: 流式接口在 pending_manual 状态下被阻止"""
    print("\n" + "="*60)
    print("测试 P0-1: 流式接口在 pending_manual 状态下被阻止")
    print("="*60)

    session_name = f"test_p01_stream_{int(time.time())}"

    # 步骤1: 触发人工升级
    print(f"\n1️⃣  步骤1: 触发人工升级 (session: {session_name})")
    response = requests.post(
        f"{BASE_URL}/api/manual/escalate",
        json={
            "session_name": session_name,
            "reason": "user_request"
        },
        timeout=10
    )

    if response.status_code != 200:
        print(f"   ❌ 升级失败: {response.text}")
        return False

    print(f"   ✅ 升级成功,状态: pending_manual")

    # 步骤2: 尝试流式AI对话(应该返回错误事件)
    print(f"\n2️⃣  步骤2: 尝试流式AI对话")
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json={
                "message": "流式对话",
                "user_id": session_name
            },
            stream=True,
            timeout=10
        )

        print(f"   状态码: {response.status_code}")

        # 读取SSE流
        lines = []
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                lines.append(line_text)
                print(f"   收到: {line_text}")

        # 检查是否有错误事件
        for line in lines:
            if line.startswith('data: '):
                try:
                    data = json.loads(line[6:])
                    if data.get('type') == 'error':
                        content = data.get('content', '')
                        if 'SESSION_IN_MANUAL_MODE' in content and 'pending_manual' in content:
                            print(f"   ✅ 流式AI对话被正确阻止")
                            print(f"   错误信息: {content}")
                            return True
                except json.JSONDecodeError:
                    pass

        print(f"   ❌ 未收到期望的错误事件")
        return False

    except Exception as e:
        print(f"   ❌ 请求异常: {str(e)}")
        return False


if __name__ == "__main__":
    print("\n" + "🔧 P0-1 状态机修复测试" + "\n")

    results = []

    # 测试1: pending_manual 阻止AI
    result1 = test_p01_pending_manual_blocks_ai()
    results.append(("pending_manual阻止AI", result1))

    time.sleep(1)

    # 测试2: manual_live 阻止AI
    result2 = test_p01_manual_live_blocks_ai()
    results.append(("manual_live阻止AI", result2))

    time.sleep(1)

    # 测试3: 流式接口被阻止
    result3 = test_p01_stream_blocked()
    results.append(("流式接口被阻止", result3))

    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)

    passed = 0
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
        if result:
            passed += 1

    print(f"\n总计: {passed}/{len(results)} 测试通过")

    if passed == len(results):
        print("\n🎉 所有测试通过! P0-1 修复成功!")
        exit(0)
    else:
        print("\n⚠️  部分测试失败,需要修复")
        exit(1)
