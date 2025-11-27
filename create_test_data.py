#!/usr/bin/env python3
"""
创建测试数据 - 包含带标签的会话
"""

import time
import redis
from src.session_state import SessionState, SessionStatus, UserProfile
from src.session_tags import SessionTagManager

# 简单的 SessionStore Mock
class MockSessionStore:
    def __init__(self, redis_client):
        self.redis = redis_client

def main():
    print("=" * 60)
    print("  创建测试数据（带标签的会话）")
    print("=" * 60)

    # 连接 Redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    session_store = MockSessionStore(redis_client)
    tag_manager = SessionTagManager(session_store)

    # 测试会话数据
    test_sessions = [
        {
            "session_name": "vip_customer_张三_001",
            "nickname": "张三 (VIP会员)",
            "vip": True,
            "status": "pending_manual",
            "tags": ["tag_vip"],
            "last_message": "你好，我的 D4S 电动车电池充不进电了",
        },
        {
            "session_name": "urgent_issue_李四_002",
            "nickname": "李四",
            "vip": False,
            "status": "pending_manual",
            "tags": ["tag_urgent", "tag_technical"],
            "last_message": "急！车子突然不能启动了，显示屏也不亮",
        },
        {
            "session_name": "refund_request_王五_003",
            "nickname": "王五",
            "vip": False,
            "status": "pending_manual",
            "tags": ["tag_refund", "tag_after_sales"],
            "last_message": "我要申请退款，收到的车子有划痕",
        },
        {
            "session_name": "normal_customer_赵六_004",
            "nickname": "赵六",
            "vip": False,
            "status": "pending_manual",
            "tags": ["tag_follow_up"],
            "last_message": "请问这款车的续航里程是多少？",
        },
        {
            "session_name": "battery_problem_钱七_005",
            "nickname": "钱七",
            "vip": True,
            "status": "manual_live",
            "tags": ["tag_vip", "tag_technical"],
            "last_message": "电池健康度显示只有60%了",
        },
    ]

    print(f"\n创建 {len(test_sessions)} 个测试会话...\n")

    for data in test_sessions:
        session_name = data["session_name"]

        # 1. 创建会话状态
        session_key = f"session:{session_name}"
        session_data = {
            "session_name": session_name,
            "conversation_id": f"conv_{int(time.time())}_{session_name}",
            "status": data["status"],
            "created_at": time.time(),
            "updated_at": time.time(),
            "user_profile": {
                "nickname": data["nickname"],
                "vip": data["vip"]
            },
            "history": [
                {
                    "id": f"msg_{int(time.time())}",
                    "role": "user",
                    "content": data["last_message"],
                    "timestamp": time.time()
                }
            ]
        }

        # 如果是 pending_manual，添加升级信息
        if data["status"] == "pending_manual":
            session_data["escalation"] = {
                "reason": "用户请求人工服务",
                "details": data["last_message"][:50],
                "severity": "medium",
                "trigger_at": time.time()
            }

        # 如果是 manual_live，添加坐席信息
        if data["status"] == "manual_live":
            session_data["assigned_agent"] = {
                "id": "agent_001",
                "name": "测试坐席"
            }

        import json
        redis_client.set(session_key, json.dumps(session_data))

        # 2. 添加标签
        for tag_id in data["tags"]:
            try:
                tag_manager.add_tag_to_session(session_name, tag_id, "admin")
                tag = tag_manager.get_tag(tag_id)
                print(f"✅ {session_name:30s}  [{tag.color}] {tag.name}")
            except Exception as e:
                print(f"⚠️  {session_name:30s}  标签 {tag_id} 添加失败")

    print(f"\n" + "=" * 60)
    print("✅ 测试数据创建完成！")
    print("=" * 60)

    # 显示统计
    print(f"\n📊 数据统计：")
    print(f"  - 总会话数: {len(test_sessions)}")
    print(f"  - pending_manual: {sum(1 for s in test_sessions if s['status'] == 'pending_manual')}")
    print(f"  - manual_live: {sum(1 for s in test_sessions if s['status'] == 'manual_live')}")
    print(f"  - VIP 客户: {sum(1 for s in test_sessions if s['vip'])}")

    # 按标签统计
    print(f"\n🏷️  标签分布：")
    tag_counts = {}
    for session in test_sessions:
        for tag_id in session["tags"]:
            tag = tag_manager.get_tag(tag_id)
            if tag:
                tag_counts[tag.name] = tag_counts.get(tag.name, 0) + 1

    for tag_name, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
        print(f"  - {tag_name}: {count} 个会话")

    print()

if __name__ == "__main__":
    main()
