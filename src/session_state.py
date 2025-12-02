"""
会话状态存储模块
负责管理用户会话的状态、历史消息、人工接管信息等

【设计说明】
1. SessionState: 会话状态数据模型
2. SessionStateStore: 状态存储接口(支持内存/Redis)
3. InMemorySessionStore: 内存实现(MVP版本)
4. 线程安全: 使用 asyncio.Lock 保护并发访问
"""

import asyncio
import json
import os
from typing import Optional, Dict, List, Any, Literal
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from enum import Enum


# ==================== 枚举定义 ====================

class SessionStatus(str, Enum):
    """会话状态枚举"""
    BOT_ACTIVE = "bot_active"  # AI 服务中
    PENDING_MANUAL = "pending_manual"  # 等待人工接入
    MANUAL_LIVE = "manual_live"  # 人工服务中
    AFTER_HOURS_EMAIL = "after_hours_email"  # 非工作时间,已发邮件
    CLOSED = "closed"  # 已关闭


class MessageRole(str, Enum):
    """消息角色枚举"""
    USER = "user"  # 用户消息
    ASSISTANT = "assistant"  # AI 助手消息
    AGENT = "agent"  # 人工客服消息
    SYSTEM = "system"  # 系统消息


class EscalationReason(str, Enum):
    """人工接管触发原因"""
    KEYWORD = "keyword"  # 关键词匹配
    FAIL_LOOP = "fail_loop"  # AI 连续失败
    SENTIMENT = "sentiment"  # 情绪检测
    VIP = "vip"  # VIP 用户
    MANUAL = "manual"  # 手动触发


class EscalationSeverity(str, Enum):
    """问题严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PriorityLevel(str, Enum):
    """优先级等级 (模块2)"""
    URGENT = "urgent"  # 紧急（VIP客户、等待超时）
    HIGH = "high"      # 重要（关键词触发、二次转接）
    NORMAL = "normal"  # 普通


# ==================== 数据模型 ====================

class Message(BaseModel):
    """消息模型"""
    role: MessageRole
    content: str
    timestamp: float = Field(default_factory=lambda: round(datetime.now(timezone.utc).timestamp(), 3))
    agent_id: Optional[str] = None  # 人工客服 ID (role=agent 时有效)
    agent_name: Optional[str] = None  # 人工客服名称


class UserProfile(BaseModel):
    """用户信息（v2.5 扩展）"""
    # 基础信息
    nickname: str = "访客"
    email: Optional[str] = None
    vip: bool = False

    # ⭐ v2.5 新增: GDPR 合规字段
    gdpr_consent: bool = False  # GDPR 同意状态
    marketing_subscribed: bool = False  # 营销通讯订阅

    # ⭐ v2.5 新增: 地理位置与语言
    country: str = ""  # 国家代码 (ISO 3166-1, 如 "DE")
    city: str = ""  # 城市名称
    language: str = "en"  # 语言代码 (ISO 639-1, 如 "de")
    currency: str = "USD"  # 货币代码 (ISO 4217, 如 "EUR")

    # 扩展元数据
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EscalationInfo(BaseModel):
    """人工接管信息"""
    reason: EscalationReason
    details: str  # 详细描述,如"命中关键词: 人工"
    severity: EscalationSeverity = EscalationSeverity.LOW
    trigger_at: float = Field(default_factory=lambda: round(datetime.now(timezone.utc).timestamp(), 3))


class AgentInfo(BaseModel):
    """坐席信息"""
    id: str
    name: str


class MailInfo(BaseModel):
    """邮件信息"""
    sent: bool = False
    email_to: List[str] = Field(default_factory=list)
    message_id: Optional[str] = None
    error: Optional[str] = None


class PriorityInfo(BaseModel):
    """会话优先级信息 (模块2)"""
    level: PriorityLevel = PriorityLevel.NORMAL  # 优先级等级
    is_vip: bool = False  # 是否VIP客户
    wait_time_seconds: float = 0  # 等待时长（秒）
    is_timeout: bool = False  # 是否等待超时（>5分钟）
    is_repeat: bool = False  # 是否二次转接
    urgent_keywords: List[str] = Field(default_factory=list)  # 触发的紧急关键词

    def calculate_priority(self) -> PriorityLevel:
        """
        计算优先级等级

        规则：
        1. VIP客户 → urgent
        2. 等待超时（>5分钟）→ urgent
        3. 关键词触发 → high
        4. 二次转接 → high
        5. 默认 → normal
        """
        if self.is_vip or self.is_timeout:
            return PriorityLevel.URGENT
        elif self.urgent_keywords or self.is_repeat:
            return PriorityLevel.HIGH
        else:
            return PriorityLevel.NORMAL


class SessionState(BaseModel):
    """会话状态完整模型"""
    session_name: str  # 会话唯一标识 (即 user_id/sessionId)
    status: SessionStatus = SessionStatus.BOT_ACTIVE
    conversation_id: Optional[str] = None  # Coze Conversation ID

    # 用户信息
    user_profile: UserProfile = Field(default_factory=UserProfile)

    # 消息历史 (最多保留 50 条)
    history: List[Message] = Field(default_factory=list)

    # 人工接管信息
    escalation: Optional[EscalationInfo] = None
    assigned_agent: Optional[AgentInfo] = None

    # 邮件信息
    mail: Optional[MailInfo] = None

    # ⭐ 模块2新增：优先级信息
    priority: PriorityInfo = Field(default_factory=PriorityInfo)

    # 时间戳
    created_at: float = Field(default_factory=lambda: round(datetime.now(timezone.utc).timestamp(), 3))
    updated_at: float = Field(default_factory=lambda: round(datetime.now(timezone.utc).timestamp(), 3))
    manual_start_at: Optional[float] = None  # 最近一次人工服务开始时间
    last_manual_end_at: Optional[float] = None

    # AI 失败计数器 (用于检测连续失败)
    ai_fail_count: int = 0

    # 工单关联
    tickets: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True

    def add_message(self, message: Message, max_history: int = 50):
        """添加消息到历史记录"""
        self.history.append(message)
        # 限制历史消息数量
        if len(self.history) > max_history:
            self.history = self.history[-max_history:]
        self.updated_at = round(datetime.now(timezone.utc).timestamp(), 3)

    def update_priority(self, urgent_keywords: List[str] = None):
        """
        更新优先级信息 (模块2)

        Args:
            urgent_keywords: 紧急关键词列表 ["投诉", "退款", "质量问题"]
        """
        current_time = round(datetime.now(timezone.utc).timestamp(), 3)

        # 更新 VIP 状态
        self.priority.is_vip = self.user_profile.vip

        # 计算等待时长
        if self.escalation and self.status == SessionStatus.PENDING_MANUAL:
            self.priority.wait_time_seconds = current_time - self.escalation.trigger_at
            # 判断是否等待超时（>5分钟 = 300秒）
            self.priority.is_timeout = self.priority.wait_time_seconds > 300
        else:
            self.priority.wait_time_seconds = 0
            self.priority.is_timeout = False

        # 检查紧急关键词
        if urgent_keywords:
            found_keywords = []
            for msg in self.history:
                if msg.role == MessageRole.USER:
                    for keyword in urgent_keywords:
                        if keyword in msg.content:
                            found_keywords.append(keyword)
            self.priority.urgent_keywords = list(set(found_keywords))

        # 重新计算优先级等级
        self.priority.level = self.priority.calculate_priority()

    def transition_status(self, new_status: SessionStatus) -> bool:
        """
        状态转换

        Returns:
            bool: 转换是否成功
        """
        # 定义合法的状态转换
        valid_transitions = {
            SessionStatus.BOT_ACTIVE: {
                SessionStatus.PENDING_MANUAL,
                SessionStatus.AFTER_HOURS_EMAIL,
                SessionStatus.MANUAL_LIVE  # 允许直接接管
            },
            SessionStatus.PENDING_MANUAL: {
                SessionStatus.MANUAL_LIVE,
                SessionStatus.BOT_ACTIVE,  # 取消接管
                SessionStatus.AFTER_HOURS_EMAIL
            },
            SessionStatus.MANUAL_LIVE: {
                SessionStatus.BOT_ACTIVE,
                SessionStatus.CLOSED
            },
            SessionStatus.AFTER_HOURS_EMAIL: {
                SessionStatus.MANUAL_LIVE,  # 补回
                SessionStatus.BOT_ACTIVE,  # 忽略
                SessionStatus.CLOSED
            },
            SessionStatus.CLOSED: {
                SessionStatus.BOT_ACTIVE  # 重新激活
            }
        }

        if new_status in valid_transitions.get(self.status, set()):
            old_status = self.status
            self.status = new_status
            self.updated_at = round(datetime.now(timezone.utc).timestamp(), 3)

            # 状态转换时的特殊处理
            if new_status == SessionStatus.BOT_ACTIVE and old_status == SessionStatus.MANUAL_LIVE:
                self.last_manual_end_at = self.updated_at
                self.assigned_agent = None
                self.manual_start_at = None
            elif new_status == SessionStatus.CLOSED and old_status == SessionStatus.MANUAL_LIVE:
                self.manual_start_at = None

            return True
        return False

    def to_summary(self) -> Dict[str, Any]:
        """转换为摘要格式 (用于列表展示)"""
        summary = {
            "session_name": self.session_name,
            "status": self.status,
            "user_profile": {
                "nickname": self.user_profile.nickname,
                "vip": self.user_profile.vip
            },
            "updated_at": self.updated_at
        }

        # 添加最后一条消息预览
        if self.history:
            last_msg = self.history[-1]
            summary["last_message_preview"] = {
                "role": last_msg.role,
                "content": last_msg.content[:50] + "..." if len(last_msg.content) > 50 else last_msg.content,
                "timestamp": last_msg.timestamp
            }

        # 添加人工接管信息
        if self.escalation:
            summary["escalation"] = {
                "reason": self.escalation.reason,
                "trigger_at": self.escalation.trigger_at,
                "waiting_seconds": round(datetime.now(timezone.utc).timestamp(), 3) - self.escalation.trigger_at
            }

        if self.assigned_agent:
            summary["assigned_agent"] = {
                "id": self.assigned_agent.id,
                "name": self.assigned_agent.name
            }

        # 【模块2】添加优先级信息
        if self.priority:
            summary["priority"] = {
                "level": self.priority.level,
                "is_vip": self.priority.is_vip,
                "wait_time_seconds": self.priority.wait_time_seconds,
                "is_timeout": self.priority.is_timeout,
                "urgent_keywords": self.priority.urgent_keywords
            }

        if self.tickets:
            summary["tickets"] = self.tickets

        return summary

    def add_ticket_reference(self, ticket_id: str):
        """关联工单 ID"""
        if ticket_id not in self.tickets:
            self.tickets.append(ticket_id)
            self.updated_at = round(datetime.now(timezone.utc).timestamp(), 3)


# ==================== 状态存储接口 ====================

class SessionStateStore:
    """会话状态存储抽象接口"""

    async def get(self, session_name: str) -> Optional[SessionState]:
        """获取会话状态"""
        raise NotImplementedError

    async def save(self, state: SessionState) -> bool:
        """保存会话状态"""
        raise NotImplementedError

    async def delete(self, session_name: str) -> bool:
        """删除会话"""
        raise NotImplementedError

    async def list_by_status(
        self,
        status: SessionStatus,
        limit: int = 50,
        offset: int = 0
    ) -> List[SessionState]:
        """按状态查询会话列表"""
        raise NotImplementedError

    async def count_by_status(self, status: SessionStatus) -> int:
        """统计指定状态的会话数量"""
        raise NotImplementedError

    async def clear_all(self) -> int:
        """清空所有会话，返回清理数量"""
        raise NotImplementedError


# ==================== 内存存储实现 ====================

class InMemorySessionStore(SessionStateStore):
    """
    内存会话状态存储 (MVP 版本)

    特性:
    1. 使用字典存储,快速访问
    2. asyncio.Lock 保证线程安全
    3. 支持持久化到文件 (可选)
    """

    def __init__(self, backup_file: Optional[str] = None):
        """
        初始化内存存储

        Args:
            backup_file: 备份文件路径 (可选),用于持久化
        """
        self._store: Dict[str, SessionState] = {}
        self._lock = asyncio.Lock()
        self.backup_file = backup_file

        # 如果指定了备份文件,尝试加载
        if backup_file:
            self._load_from_file()

    async def get(self, session_name: str) -> Optional[SessionState]:
        """获取会话状态 (线程安全)"""
        async with self._lock:
            return self._store.get(session_name)

    async def save(self, state: SessionState) -> bool:
        """保存会话状态 (线程安全)"""
        async with self._lock:
            state.updated_at = round(datetime.now(timezone.utc).timestamp(), 3)
            self._store[state.session_name] = state

            # 异步备份到文件 (如果配置了)
            if self.backup_file:
                self._save_to_file_sync()

            return True

    async def delete(self, session_name: str) -> bool:
        """删除会话"""
        async with self._lock:
            if session_name in self._store:
                del self._store[session_name]
                if self.backup_file:
                    self._save_to_file_sync()
                return True
            return False

    async def list_by_status(
        self,
        status: SessionStatus,
        limit: int = 50,
        offset: int = 0
    ) -> List[SessionState]:
        """按状态查询会话列表"""
        async with self._lock:
            # 过滤指定状态的会话
            filtered = [
                state for state in self._store.values()
                if state.status == status
            ]
            # 按更新时间倒序排序
            filtered.sort(key=lambda x: x.updated_at, reverse=True)
            # 分页
            return filtered[offset:offset + limit]

    async def count_by_status(self, status: SessionStatus) -> int:
        """统计指定状态的会话数量"""
        async with self._lock:
            return sum(1 for state in self._store.values() if state.status == status)

    async def list_all(self, limit: int = 50, offset: int = 0) -> List[SessionState]:
        """获取所有会话列表"""
        async with self._lock:
            # 获取所有会话
            all_sessions = list(self._store.values())
            # 按更新时间倒序排序
            all_sessions.sort(key=lambda x: x.updated_at, reverse=True)
            # 分页
            return all_sessions[offset:offset + limit]

    async def count_all(self) -> int:
        """统计所有会话数量"""
        async with self._lock:
            return len(self._store)

    async def get_or_create(self, session_name: str, conversation_id: Optional[str] = None) -> SessionState:
        """
        获取或创建会话状态

        Args:
            session_name: 会话名称
            conversation_id: Coze Conversation ID (可选)

        Returns:
            SessionState: 会话状态
        """
        state = await self.get(session_name)
        if state is None:
            state = SessionState(
                session_name=session_name,
                conversation_id=conversation_id
            )
            await self.save(state)
        return state

    def _load_from_file(self):
        """从文件加载备份 (同步)"""
        try:
            if self.backup_file:
                import os
                if os.path.exists(self.backup_file):
                    with open(self.backup_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for session_name, state_dict in data.items():
                            self._store[session_name] = SessionState(**state_dict)
                    print(f"✅ 从备份文件加载了 {len(self._store)} 个会话")
        except Exception as e:
            print(f"⚠️  备份文件加载失败: {e}")

    def _save_to_file_sync(self):
        """同步保存到文件"""
        try:
            if self.backup_file:
                with open(self.backup_file, 'w', encoding='utf-8') as f:
                    data = {
                        session_name: state.dict()
                        for session_name, state in self._store.items()
                    }
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  备份文件保存失败: {e}")

    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        async with self._lock:
            total = len(self._store)
            by_status = {}
            for status in SessionStatus:
                count = sum(1 for state in self._store.values() if state.status == status)
                if count > 0:
                    by_status[status.value] = count

            return {
                "total_sessions": total,
                "by_status": by_status,
                "active_sessions": sum(
                    1 for state in self._store.values()
                    if state.status != SessionStatus.CLOSED
                )
            }

    async def clear_all(self) -> int:
        """清空所有会话"""
        async with self._lock:
            count = len(self._store)
            self._store.clear()
            if self.backup_file and os.path.exists(self.backup_file):
                try:
                    os.remove(self.backup_file)
                except OSError:
                    pass
            return count


# ==================== 全局单例 ====================

_global_store: Optional[InMemorySessionStore] = None


def get_session_store(backup_file: Optional[str] = None) -> InMemorySessionStore:
    """
    获取全局会话存储实例 (单例模式)

    Args:
        backup_file: 备份文件路径 (首次调用时设置)

    Returns:
        InMemorySessionStore: 全局存储实例
    """
    global _global_store
    if _global_store is None:
        _global_store = InMemorySessionStore(backup_file=backup_file)
    return _global_store
