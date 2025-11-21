"""
测试 P0 补充的 API
- takeover 坐席接入 (防抢单)
- sessions 会话列表
- sessions/stats 会话统计
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


def print_section(title: str):
    """打印分隔线"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def print_result(step: str, response: requests.Response):
    """打印请求结果"""
    status_icon = "✅" if response.status_code < 400 else "❌"
    print(f"{status_icon} {step}")
    print(f"   状态码: {response.status_code}")
    try:
        data = response.json()
        print(f"   响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
    except:
        print(f"   响应: {response.text[:200]}")
    print()


def test_takeover_api():
    """测试坐席接入 API"""
    print_section("测试 P0-2: 坐席接入 API (防抢单)")

    # 1. 先创建一个 pending_manual 会话
    print("📝 步骤1: 创建 pending_manual 会话")
    session_name = f"test_session_{int(time.time())}"

    # 触发人工升级
    resp = requests.post(
        f"{BASE_URL}/api/manual/escalate",
        json={
            "session_name": session_name,
            "reason": "user_request"
        }
    )
    print_result("创建 pending_manual 会话", resp)

    # 2. 坐席1 接入
    print("📝 步骤2: 坐席1 尝试接入")
    resp1 = requests.post(
        f"{BASE_URL}/api/sessions/{session_name}/takeover",
        json={
            "agent_id": "agent_001",
            "agent_name": "小王"
        }
    )
    print_result("坐席1 接入", resp1)

    # 3. 坐席2 尝试接入 (应该失败，返回 409)
    print("📝 步骤3: 坐席2 尝试接入 (预期失败)")
    resp2 = requests.post(
        f"{BASE_URL}/api/sessions/{session_name}/takeover",
        json={
            "agent_id": "agent_002",
            "agent_name": "小张"
        }
    )
    print_result("坐席2 接入 (应该失败)", resp2)

    # 验证结果
    if resp1.status_code == 200 and resp2.status_code == 409:
        print("✅ 防抢单测试通过！")
    else:
        print("❌ 防抢单测试失败！")

    # 4. 测试错误状态接入
    print("\n📝 步骤4: 测试在 bot_active 状态下接入 (预期失败)")
    wrong_session = f"bot_session_{int(time.time())}"

    # 创建一个 bot_active 会话 (通过正常对话)
    # 这里直接测试接入一个不存在的会话
    resp3 = requests.post(
        f"{BASE_URL}/api/sessions/{wrong_session}/takeover",
        json={
            "agent_id": "agent_003",
            "agent_name": "小李"
        }
    )
    print_result("在错误状态下接入 (应该失败)", resp3)

    return session_name  # 返回会话名用于后续测试


def test_sessions_list_api(test_session: str):
    """测试会话列表 API"""
    print_section("测试 P0-3: 会话列表 API")

    # 1. 查询 pending_manual 状态的会话
    print("📝 步骤1: 查询 pending_manual 状态的会话")
    resp = requests.get(
        f"{BASE_URL}/api/sessions",
        params={"status": "pending_manual", "limit": 10}
    )
    print_result("查询 pending_manual 会话", resp)

    # 2. 查询 manual_live 状态的会话
    print("📝 步骤2: 查询 manual_live 状态的会话")
    resp = requests.get(
        f"{BASE_URL}/api/sessions",
        params={"status": "manual_live", "limit": 10}
    )
    print_result("查询 manual_live 会话", resp)

    # 3. 查询所有会话
    print("📝 步骤3: 查询所有会话")
    resp = requests.get(
        f"{BASE_URL}/api/sessions",
        params={"limit": 20}
    )
    print_result("查询所有会话", resp)

    # 4. 测试分页
    print("📝 步骤4: 测试分页功能")
    resp = requests.get(
        f"{BASE_URL}/api/sessions",
        params={"limit": 5, "offset": 0}
    )
    print_result("分页查询 (第1页)", resp)

    # 5. 测试错误的状态参数
    print("📝 步骤5: 测试错误的状态参数 (预期失败)")
    resp = requests.get(
        f"{BASE_URL}/api/sessions",
        params={"status": "invalid_status"}
    )
    print_result("错误的状态参数 (应该失败)", resp)


def test_sessions_stats_api():
    """测试会话统计 API"""
    print_section("测试 P1-1: 会话统计 API")

    print("📝 获取会话统计信息")
    resp = requests.get(f"{BASE_URL}/api/sessions/stats")
    print_result("获取统计信息", resp)

    # 验证统计数据结构
    if resp.status_code == 200:
        data = resp.json()
        if data.get("success"):
            stats = data.get("data", {})
            print("📊 统计数据:")
            print(f"   总会话数: {stats.get('total_sessions')}")
            print(f"   活跃会话数: {stats.get('active_sessions')}")
            print(f"   平均等待时间: {stats.get('avg_waiting_time', 0):.2f}秒")
            print(f"   按状态分布: {stats.get('by_status')}")
            print("✅ 统计 API 测试通过！")
        else:
            print("❌ 统计 API 返回失败！")
    else:
        print("❌ 统计 API 请求失败！")


def test_complete_workflow():
    """测试完整工作流"""
    print_section("测试完整人工接管工作流")

    session_name = f"workflow_test_{int(time.time())}"

    # 1. 触发人工升级
    print("📝 步骤1: 用户触发人工升级")
    resp = requests.post(
        f"{BASE_URL}/api/manual/escalate",
        json={"session_name": session_name, "reason": "keyword"}
    )
    print_result("触发升级", resp)
    assert resp.status_code == 200, "触发升级失败"

    # 2. 查询会话状态
    print("📝 步骤2: 查询会话状态")
    resp = requests.get(f"{BASE_URL}/api/sessions/{session_name}")
    print_result("查询状态", resp)
    assert resp.status_code == 200, "查询状态失败"
    data = resp.json()
    assert data["data"]["session"]["status"] == "pending_manual", "状态不正确"

    # 3. 坐席接入
    print("📝 步骤3: 坐席接入会话")
    resp = requests.post(
        f"{BASE_URL}/api/sessions/{session_name}/takeover",
        json={"agent_id": "agent_workflow", "agent_name": "测试坐席"}
    )
    print_result("坐席接入", resp)
    assert resp.status_code == 200, "坐席接入失败"

    # 4. 验证状态变化
    print("📝 步骤4: 验证状态已变为 manual_live")
    resp = requests.get(f"{BASE_URL}/api/sessions/{session_name}")
    print_result("验证状态", resp)
    data = resp.json()
    assert data["data"]["session"]["status"] == "manual_live", "状态转换失败"
    assert data["data"]["session"]["assigned_agent"]["name"] == "测试坐席", "坐席信息不正确"

    # 5. 坐席发送消息
    print("📝 步骤5: 坐席发送消息")
    resp = requests.post(
        f"{BASE_URL}/api/manual/messages",
        json={
            "session_name": session_name,
            "role": "agent",
            "content": "您好，我是测试坐席",
            "agent_id": "agent_workflow",
            "agent_name": "测试坐席"
        }
    )
    print_result("发送人工消息", resp)
    assert resp.status_code == 200, "发送消息失败"

    # 6. 坐席释放会话
    print("📝 步骤6: 坐席释放会话")
    resp = requests.post(
        f"{BASE_URL}/api/sessions/{session_name}/release",
        json={"agent_id": "agent_workflow", "reason": "resolved"}
    )
    print_result("释放会话", resp)
    assert resp.status_code == 200, "释放会话失败"

    # 7. 验证状态恢复
    print("📝 步骤7: 验证状态已恢复为 bot_active")
    resp = requests.get(f"{BASE_URL}/api/sessions/{session_name}")
    print_result("验证状态恢复", resp)
    data = resp.json()
    assert data["data"]["session"]["status"] == "bot_active", "状态恢复失败"

    print("\n✅ 完整工作流测试通过！")


def main():
    """主测试函数"""
    print("""
╔════════════════════════════════════════════════════════════╗
║                 P0 补充 API 测试套件                        ║
║                                                            ║
║  测试内容:                                                  ║
║  1. P0-2: 坐席接入 API (防抢单)                            ║
║  2. P0-3: 会话列表 API                                     ║
║  3. P1-1: 会话统计 API                                     ║
║  4. 完整工作流测试                                          ║
╚════════════════════════════════════════════════════════════╝
    """)

    try:
        # 测试1: 坐席接入 API
        test_session = test_takeover_api()

        # 测试2: 会话列表 API
        test_sessions_list_api(test_session)

        # 测试3: 会话统计 API
        test_sessions_stats_api()

        # 测试4: 完整工作流
        test_complete_workflow()

        print_section("✅ 所有测试通过！")

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到后端服务，请确保服务已启动 (python3 backend.py)")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
