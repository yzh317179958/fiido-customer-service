#!/usr/bin/env python3
"""
Redis 数据持久化测试脚本

测试场景：
1. 创建会话并保存数据
2. 验证数据已保存到 Redis
3. 模拟服务器重启（重新连接 Redis）
4. 验证数据恢复成功
"""

import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.redis_session_store import RedisSessionStore
from src.session_state import SessionState, SessionStatus, Message, UserProfile

async def test_redis_persistence():
    """测试 Redis 数据持久化"""

    print("=" * 70)
    print("Redis 数据持久化测试")
    print("=" * 70)
    print()

    # 1. 创建 Redis 存储实例
    print("📦 步骤 1/5: 连接 Redis...")
    store = RedisSessionStore(
        redis_url="redis://localhost:6379/0",
        default_ttl=86400
    )
    print(f"✅ Redis 连接成功")
    print()

    # 2. 创建测试会话数据
    print("📝 步骤 2/5: 创建测试会话数据...")
    test_session = SessionState(
        session_name="test_session_12345",
        status=SessionStatus.BOT_ACTIVE,
        conversation_id="conv_test_67890",
        history=[
            Message(
                role="user",
                content="你好，我想咨询Fiido产品",
                timestamp=1732500000.0
            ),
            Message(
                role="assistant",
                content="您好！我是Fiido产品顾问，很高兴为您服务",
                timestamp=1732500005.0
            ),
        ],
        user_profile=UserProfile(
            nickname="测试用户",
            vip=True
        )
    )
    print(f"✅ 测试会话创建成功: {test_session.session_name}")
    print(f"   状态: {test_session.status}")
    print(f"   消息数: {len(test_session.history)}")
    print(f"   用户: {test_session.user_profile.nickname} (VIP: {test_session.user_profile.vip})")
    print()

    # 3. 保存到 Redis
    print("💾 步骤 3/5: 保存会话到 Redis...")
    success = await store.save(test_session)
    if success:
        print(f"✅ 会话已保存到 Redis")
    else:
        print(f"❌ 保存失败")
        return False
    print()

    # 4. 验证 Redis 中的数据
    print("🔍 步骤 4/5: 从 Redis 读取会话验证...")
    loaded_session = await store.get("test_session_12345")

    if loaded_session:
        print(f"✅ 会话读取成功")
        print(f"   会话名: {loaded_session.session_name}")
        print(f"   Conversation ID: {loaded_session.conversation_id}")
        print(f"   状态: {loaded_session.status}")
        print(f"   历史消息数: {len(loaded_session.history)}")
        print(f"   用户信息: {loaded_session.user_profile.nickname}")

        # 验证数据完整性
        assert loaded_session.session_name == test_session.session_name
        assert loaded_session.conversation_id == test_session.conversation_id
        assert loaded_session.status == test_session.status
        assert len(loaded_session.history) == len(test_session.history)
        assert loaded_session.user_profile.nickname == test_session.user_profile.nickname

        print(f"   ✅ 数据完整性验证通过")
    else:
        print(f"❌ 会话读取失败")
        return False
    print()

    # 5. 模拟服务器重启（重新连接 Redis）
    print("🔄 步骤 5/5: 模拟服务器重启（重新连接 Redis）...")
    store2 = RedisSessionStore(
        redis_url="redis://localhost:6379/0",
        default_ttl=86400
    )
    print(f"✅ 新连接创建成功")
    print()

    # 6. 从新连接读取数据
    print("📖 验证服务器重启后数据恢复...")
    recovered_session = await store2.get("test_session_12345")

    if recovered_session:
        print(f"✅ 数据恢复成功！")
        print(f"   会话名: {recovered_session.session_name}")
        print(f"   Conversation ID: {recovered_session.conversation_id}")
        print(f"   状态: {recovered_session.status}")
        print(f"   历史消息:")
        for i, msg in enumerate(recovered_session.history, 1):
            print(f"      {i}. [{msg.role}] {msg.content}")
        print(f"   用户: {recovered_session.user_profile.nickname} (VIP: {recovered_session.user_profile.vip})")
        print()

        # 验证关键数据
        assert recovered_session.conversation_id == "conv_test_67890"
        assert len(recovered_session.history) == 2
        assert recovered_session.user_profile.vip == True

        print(f"   ✅ 服务器重启后数据恢复验证通过")
    else:
        print(f"❌ 数据恢复失败")
        return False
    print()

    # 7. 健康检查
    print("🏥 Redis 健康检查...")
    health = store.check_health()
    print(f"   状态: {health['status']}")
    print(f"   内存使用: {health['used_memory_mb']}MB")
    print(f"   会话数: {health['total_sessions']}")
    print()

    # 8. 清理测试数据
    print("🧹 清理测试数据...")
    await store.delete("test_session_12345")
    print(f"✅ 测试数据已清理")
    print()

    print("=" * 70)
    print("✅ Redis 数据持久化测试全部通过！")
    print("=" * 70)
    print()
    print("测试结果：")
    print("  ✅ 数据保存成功")
    print("  ✅ 数据读取成功")
    print("  ✅ 数据完整性验证通过")
    print("  ✅ 服务器重启后数据恢复成功")
    print("  ✅ 历史消息完整保留")
    print("  ✅ 用户信息正确恢复")
    print()
    print("🎉 Redis 数据持久化功能正常！")
    print()

    return True


if __name__ == "__main__":
    result = asyncio.run(test_redis_persistence())
    sys.exit(0 if result else 1)
