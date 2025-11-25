"""
Redis 会话状态存储实现

本模块实现基于 Redis 的会话状态持久化存储，解决内存存储的三大问题：
1. 数据丢失 - 服务器重启后数据自动恢复
2. 无法扩展 - 支持多台服务器共享数据
3. 无历史数据 - 支持历史数据查询和导出

遵守约束16：生产环境安全性与稳定性要求
"""

import redis
import json
import logging
from typing import Optional, List
from datetime import datetime, timezone

from src.session_state import (
    SessionState,
    SessionStatus,
    SessionStateStore,
)

logger = logging.getLogger(__name__)


class RedisSessionStore(SessionStateStore):
    """
    Redis 会话状态存储实现

    设计原则：
    1. ✅ 资源限制 - 使用连接池，限制最大连接数
    2. ✅ 数据过期 - 所有会话数据设置 TTL（24小时）
    3. ✅ 错误处理 - 所有 Redis 操作都有异常处理
    4. ✅ 超时保护 - 设置连接和操作超时
    5. ✅ 监控友好 - 详细的日志记录
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        max_connections: int = 50,
        socket_timeout: float = 5.0,
        socket_connect_timeout: float = 5.0,
        default_ttl: int = 86400  # 24小时
    ):
        """
        初始化 Redis 连接

        Args:
            redis_url: Redis 连接地址
                - 本地开发: redis://localhost:6379/0
                - 生产环境: redis://:password@host:6379/0
            max_connections: 最大连接数（约束16.1.3 - 限制连接数）
            socket_timeout: Socket 超时时间（约束16.3.2 - 超时保护）
            socket_connect_timeout: 连接超时时间
            default_ttl: 默认过期时间（秒），约束16.1.1 - 必须设置 TTL
        """
        try:
            # 创建连接池（约束16.1.3 - 数据库连接池）
            pool = redis.ConnectionPool.from_url(
                redis_url,
                max_connections=max_connections,
                socket_timeout=socket_timeout,
                socket_connect_timeout=socket_connect_timeout,
                decode_responses=True  # 自动解码为字符串
            )

            self.redis = redis.Redis(connection_pool=pool)
            self.default_ttl = default_ttl

            # 验证连接
            self.redis.ping()
            logger.info(f"✅ Redis 连接成功: {redis_url} (连接池大小: {max_connections})")

        except Exception as e:
            logger.error(f"❌ Redis 连接失败: {e}")
            raise

    async def save(self, state: SessionState) -> bool:
        """
        保存会话到 Redis

        工作流程:
        1. 将 SessionState 对象序列化为 JSON
        2. 存储到 Redis: session:{session_name}
        3. 更新状态索引: status:{status}
        4. 设置 24 小时过期时间（约束16.1.1 - 必须设置 TTL）

        Args:
            state: 会话状态对象

        Returns:
            bool: 保存是否成功
        """
        try:
            # 1. 序列化（使用 Pydantic 的 model_dump_json）
            key = f"session:{state.session_name}"
            json_data = state.model_dump_json()

            # 2. 存储（带过期时间 - 约束16.1.1）
            self.redis.setex(key, self.default_ttl, json_data)

            # 3. 更新状态索引（用于按状态查询）
            status_key = f"status:{state.status}"
            self.redis.sadd(status_key, state.session_name)

            # 4. 清理旧状态索引（如果状态发生变化）
            for status in SessionStatus:
                if status != state.status:
                    old_status_key = f"status:{status}"
                    self.redis.srem(old_status_key, state.session_name)

            logger.debug(f"💾 会话已保存: {state.session_name} (状态: {state.status})")
            return True

        except Exception as e:
            logger.error(f"❌ 保存会话失败 {state.session_name}: {e}")
            return False

    async def get(self, session_name: str) -> Optional[SessionState]:
        """
        从 Redis 获取会话

        工作流程:
        1. 从 Redis 读取 JSON 数据
        2. 反序列化为 SessionState 对象

        Args:
            session_name: 会话名称

        Returns:
            SessionState 对象，如果不存在则返回 None
        """
        try:
            key = f"session:{session_name}"
            json_data = self.redis.get(key)

            if json_data:
                # 使用 Pydantic 的 model_validate_json 反序列化
                state = SessionState.model_validate_json(json_data)
                logger.debug(f"📖 会话已加载: {session_name}")
                return state
            else:
                logger.debug(f"🔍 会话不存在: {session_name}")
                return None

        except Exception as e:
            logger.error(f"❌ 读取会话失败 {session_name}: {e}")
            return None

    async def get_or_create(
        self,
        session_name: str,
        conversation_id: Optional[str] = None
    ) -> SessionState:
        """
        获取或创建会话状态

        工作流程:
        1. 尝试从 Redis 获取现有会话
        2. 如果不存在，创建新会话并保存
        3. 如果存在且提供了 conversation_id，更新它

        Args:
            session_name: 会话名称
            conversation_id: 可选的对话 ID

        Returns:
            SessionState: 会话状态对象
        """
        try:
            # 1. 尝试获取现有会话
            state = await self.get(session_name)

            if state:
                # 2. 如果存在且需要更新 conversation_id
                if conversation_id and state.conversation_id != conversation_id:
                    state.conversation_id = conversation_id
                    state.updated_at = datetime.now(timezone.utc).timestamp()
                    await self.save(state)
                    logger.debug(f"🔄 更新会话 conversation_id: {session_name}")
                return state
            else:
                # 3. 创建新会话
                state = SessionState(
                    session_name=session_name,
                    conversation_id=conversation_id,
                    status=SessionStatus.BOT_ACTIVE
                )
                await self.save(state)
                logger.info(f"✨ 创建新会话: {session_name}")
                return state

        except Exception as e:
            logger.error(f"❌ 获取或创建会话失败 {session_name}: {e}")
            # 返回一个默认的会话状态（降级处理）
            return SessionState(
                session_name=session_name,
                conversation_id=conversation_id,
                status=SessionStatus.BOT_ACTIVE
            )

    async def delete(self, session_name: str) -> bool:
        """
        删除会话

        Args:
            session_name: 会话名称

        Returns:
            bool: 删除是否成功
        """
        try:
            # 1. 先获取会话状态，用于清理索引
            state = await self.get(session_name)

            # 2. 删除主数据
            key = f"session:{session_name}"
            self.redis.delete(key)

            # 3. 清理状态索引
            if state:
                status_key = f"status:{state.status}"
                self.redis.srem(status_key, session_name)

            logger.debug(f"🗑️  会话已删除: {session_name}")
            return True

        except Exception as e:
            logger.error(f"❌ 删除会话失败 {session_name}: {e}")
            return False

    async def list_by_status(
        self,
        status: SessionStatus,
        limit: int = 50,
        offset: int = 0
    ) -> List[SessionState]:
        """
        按状态查询会话列表

        工作流程:
        1. 从状态索引获取会话名称列表
        2. 批量读取会话数据
        3. 排序和分页

        Args:
            status: 会话状态
            limit: 每页数量
            offset: 偏移量

        Returns:
            会话列表
        """
        try:
            status_key = f"status:{status}"
            session_names = self.redis.smembers(status_key)

            # 批量获取会话数据
            sessions = []
            for name in session_names:
                state = await self.get(name)
                if state:
                    sessions.append(state)

            # 排序（按更新时间倒序）
            sessions.sort(key=lambda x: x.updated_at, reverse=True)

            # 分页
            result = sessions[offset:offset + limit]

            logger.debug(f"📋 查询会话列表: 状态={status}, 总数={len(sessions)}, 返回={len(result)}")
            return result

        except Exception as e:
            logger.error(f"❌ 查询会话列表失败 (状态={status}): {e}")
            return []

    async def count_by_status(self, status: SessionStatus) -> int:
        """
        统计指定状态的会话数量

        Args:
            status: 会话状态

        Returns:
            int: 会话数量
        """
        try:
            status_key = f"status:{status}"
            count = self.redis.scard(status_key)
            return count
        except Exception as e:
            logger.error(f"❌ 统计会话数量失败 (状态={status}): {e}")
            return 0

    async def get_stats(self) -> dict:
        """
        获取会话统计信息

        返回各状态的会话数量统计

        Returns:
            dict: 包含各状态会话数量的字典
        """
        try:
            stats = {
                "total": 0,
                "by_status": {}
            }

            # 统计各状态的会话数量
            for status in SessionStatus:
                count = await self.count_by_status(status)
                stats["by_status"][status.value] = count
                stats["total"] += count

            logger.debug(f"📊 会话统计: 总数={stats['total']}")
            return stats

        except Exception as e:
            logger.error(f"❌ 获取会话统计失败: {e}")
            return {
                "total": 0,
                "by_status": {status.value: 0 for status in SessionStatus}
            }

    async def get_all_sessions(self) -> List[SessionState]:
        """
        获取所有会话（用于统计和管理）

        注意：生产环境谨慎使用，可能返回大量数据

        Returns:
            所有会话列表
        """
        try:
            sessions = []

            # 使用 SCAN 遍历所有会话 key（约束16.2.1 - 避免 KEYS 命令阻塞）
            for key in self.redis.scan_iter("session:*", count=100):
                session_name = key.replace("session:", "")
                state = await self.get(session_name)
                if state:
                    sessions.append(state)

            logger.debug(f"📊 获取所有会话: 总数={len(sessions)}")
            return sessions

        except Exception as e:
            logger.error(f"❌ 获取所有会话失败: {e}")
            return []

    def check_health(self) -> dict:
        """
        健康检查（约束16.5.2 - 健康检查端点）

        Returns:
            dict: 健康状态信息
        """
        try:
            # 1. 检查连接
            self.redis.ping()

            # 2. 获取内存使用情况（约束16.2.2 - 监控存储使用量）
            info = self.redis.info('memory')
            used_memory_mb = info['used_memory'] / 1024 / 1024
            max_memory_mb = info.get('maxmemory', 0) / 1024 / 1024 if info.get('maxmemory', 0) > 0 else None

            # 3. 统计会话数量
            total_sessions = len(list(self.redis.scan_iter("session:*", count=10)))

            health_info = {
                "status": "healthy",
                "used_memory_mb": round(used_memory_mb, 2),
                "max_memory_mb": round(max_memory_mb, 2) if max_memory_mb else "unlimited",
                "memory_usage_percent": round(used_memory_mb / max_memory_mb * 100, 2) if max_memory_mb else None,
                "total_sessions": total_sessions,
            }

            # 4. 告警检查（约束16.2.2 - 监控存储使用量）
            if max_memory_mb and used_memory_mb / max_memory_mb > 0.9:
                health_info["warning"] = f"内存使用率超过90%: {health_info['memory_usage_percent']}%"
                logger.warning(f"⚠️ Redis 内存使用率高: {health_info['memory_usage_percent']}%")

            return health_info

        except Exception as e:
            logger.error(f"❌ Redis 健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def cleanup_expired_sessions(self, days: int = 7) -> int:
        """
        清理超过指定天数未活跃的会话（约束16.2.1 - 定期清理过期数据）

        注意：Redis 已通过 TTL 自动清理，此方法用于额外的主动清理

        Args:
            days: 保留天数

        Returns:
            int: 清理的会话数量
        """
        try:
            threshold = datetime.now(timezone.utc).timestamp() - days * 24 * 3600
            cleaned_count = 0

            # 使用 SCAN 遍历（避免 KEYS 阻塞）
            for key in self.redis.scan_iter("session:*", count=100):
                session_name = key.replace("session:", "")
                state = await self.get(session_name)

                if state and state.updated_at < threshold:
                    await self.delete(session_name)
                    cleaned_count += 1

            if cleaned_count > 0:
                logger.info(f"🧹 清理过期会话: {cleaned_count} 个（超过 {days} 天未活跃）")

            return cleaned_count

        except Exception as e:
            logger.error(f"❌ 清理过期会话失败: {e}")
            return 0
