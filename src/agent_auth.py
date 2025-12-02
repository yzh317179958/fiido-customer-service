#!/usr/bin/env python3
"""
坐席认证系统

功能：
- JWT Token 生成和验证
- 密码加密和验证
- 坐席账号管理
- 权限控制

作者：Fiido AI 客服开发团队
创建时间：2025-11-24
"""

import jwt
import bcrypt
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum


# ====================
# 数据模型定义
# ====================

class AgentRole(str, Enum):
    """坐席角色"""
    AGENT = "agent"  # 普通坐席
    ADMIN = "admin"  # 管理员


class AgentStatus(str, Enum):
    """坐席状态"""
    ONLINE = "online"      # 在线
    BUSY = "busy"          # 忙碌
    BREAK = "break"        # 小休
    LUNCH = "lunch"        # 午休
    TRAINING = "training"  # 培训中
    OFFLINE = "offline"    # 离线


class AgentSkillLevel(str, Enum):
    """坐席技能熟练度"""
    JUNIOR = "junior"
    INTERMEDIATE = "intermediate"
    SENIOR = "senior"


class AgentSkill(BaseModel):
    """坐席技能标签"""
    category: str = Field(..., min_length=1, max_length=50, description="技能分类")
    level: AgentSkillLevel = AgentSkillLevel.JUNIOR
    tags: List[str] = Field(default_factory=list, description="技能关键词标签")

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("技能分类不能为空")
        return normalized

    @field_validator("tags", mode="before")
    @classmethod
    def ensure_list(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return value

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: List[str]) -> List[str]:
        normalized: List[str] = []
        seen = set()
        for tag in value:
            tag_str = str(tag).strip().lower()
            if not tag_str:
                continue
            if tag_str in seen:
                continue
            normalized.append(tag_str)
            seen.add(tag_str)
        return normalized


class Agent(BaseModel):
    """坐席账号模型"""
    id: str
    username: str
    password_hash: str  # 加密后的密码
    name: str  # 显示名称
    role: AgentRole = AgentRole.AGENT
    status: AgentStatus = AgentStatus.OFFLINE
    status_note: Optional[str] = Field(default=None, description="状态说明")
    status_updated_at: float = Field(default_factory=time.time)
    last_active_at: float = Field(default_factory=time.time)
    max_sessions: int = Field(default=5, description="最大同时服务会话数")
    created_at: float = Field(default_factory=time.time)
    last_login: Optional[float] = None
    avatar_url: Optional[str] = None
    skills: List[AgentSkill] = Field(default_factory=list, description="技能标签")


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应"""
    success: bool
    token: str
    refresh_token: str
    expires_in: int  # Token 有效期（秒）
    agent: Dict[str, Any]  # 坐席信息（不含密码）


class TokenPayload(BaseModel):
    """JWT Token 载荷"""
    agent_id: str
    username: str
    role: AgentRole
    exp: float  # 过期时间（Unix 时间戳）
    iat: float  # 签发时间


# ====================
# 密码加密工具
# ====================

class PasswordHasher:
    """密码加密和验证"""

    @staticmethod
    def hash_password(password: str) -> str:
        """加密密码"""
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        return password_hash.decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """验证密码"""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception:
            return False


# ====================
# JWT Token 管理器
# ====================

class AgentTokenManager:
    """坐席 JWT Token 管理器"""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 60,  # 访问Token 1小时
        refresh_token_expire_days: int = 7  # 刷新Token 7天
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire = timedelta(minutes=access_token_expire_minutes)
        self.refresh_token_expire = timedelta(days=refresh_token_expire_days)

    def create_access_token(self, agent: Agent) -> str:
        """
        生成访问 Token

        Args:
            agent: 坐席账号

        Returns:
            JWT Token 字符串
        """
        # 修复: 使用 time.time() 代替 datetime.utcnow().timestamp()
        # datetime.utcnow().timestamp() 会被解释为本地时间，导致时区问题
        now = time.time()
        expire = now + self.access_token_expire.total_seconds()

        payload = {
            "agent_id": agent.id,
            "username": agent.username,
            "role": agent.role.value,
            "iat": now,
            "exp": expire
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def create_refresh_token(self, agent: Agent) -> str:
        """
        生成刷新 Token

        Args:
            agent: 坐席账号

        Returns:
            JWT Token 字符串
        """
        # 修复: 使用 time.time() 代替 datetime.utcnow().timestamp()
        now = time.time()
        expire = now + self.refresh_token_expire.total_seconds()

        payload = {
            "agent_id": agent.id,
            "username": agent.username,
            "type": "refresh",
            "iat": now,
            "exp": expire
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证 Token

        Args:
            token: JWT Token 字符串

        Returns:
            Token 载荷（验证成功）或 None（验证失败）
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            # Token 已过期
            return None
        except jwt.InvalidTokenError:
            # Token 无效
            return None

    def decode_token(self, token: str) -> Optional[TokenPayload]:
        """
        解码 Token（不验证过期时间）

        Args:
            token: JWT Token 字符串

        Returns:
            Token 载荷或 None
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False}  # 不验证过期时间
            )
            return TokenPayload(**payload)
        except Exception:
            return None


# ====================
# 坐席账号管理器
# ====================

class AgentManager:
    """坐席账号管理器（基于 Redis 存储）"""

    def __init__(self, redis_store):
        """
        初始化坐席管理器

        Args:
            redis_store: Redis 存储实例
        """
        self.redis = redis_store.redis
        self.key_prefix = "agent:"
        self.id_index_prefix = "agent_id:"
        self.default_ttl = 86400 * 365  # 1年

    def _username_key(self, username: str) -> str:
        return f"{self.key_prefix}{username}"

    def _id_index_key(self, agent_id: str) -> str:
        return f"{self.id_index_prefix}{agent_id}"

    def _store_agent_record(self, agent: Agent):
        """将坐席信息写入Redis并刷新索引"""
        data = agent.json()
        self.redis.set(self._username_key(agent.username), data, ex=self.default_ttl)
        self.redis.set(self._id_index_key(agent.id), agent.username, ex=self.default_ttl)

    def create_agent(
        self,
        username: str,
        password: str,
        name: str,
        role: AgentRole = AgentRole.AGENT,
        max_sessions: int = 5
    ) -> Agent:
        """
        创建坐席账号

        Args:
            username: 用户名
            password: 密码（明文）
            name: 显示名称
            role: 角色
            max_sessions: 最大同时服务会话数

        Returns:
            创建的坐席账号
        """
        # 生成坐席 ID
        agent_id = f"agent_{int(time.time() * 1000)}"

        # 加密密码
        password_hash = PasswordHasher.hash_password(password)

        # 创建坐席对象
        agent = Agent(
            id=agent_id,
            username=username,
            password_hash=password_hash,
            name=name,
            role=role,
            max_sessions=max_sessions
        )

        # 保存到 Redis
        self._store_agent_record(agent)

        return agent

    def get_agent_by_username(self, username: str) -> Optional[Agent]:
        """
        根据用户名获取坐席账号

        Args:
            username: 用户名

        Returns:
            坐席账号或 None
        """
        key = self._username_key(username)
        data = self.redis.get(key)

        if data:
            return Agent.parse_raw(data)
        return None

    def get_agent_by_id(self, agent_id: str) -> Optional[Agent]:
        """
        根据坐席ID获取账号

        Args:
            agent_id: 坐席ID
        """
        username = self.redis.get(self._id_index_key(agent_id))
        if username:
            if isinstance(username, bytes):
                username = username.decode("utf-8")
            return self.get_agent_by_username(username)

        # 兼容旧数据：扫描所有坐席
        for key in self.redis.scan_iter(f"{self.key_prefix}*", count=100):
            data = self.redis.get(key)
            if not data:
                continue
            try:
                agent = Agent.parse_raw(data)
            except Exception:
                continue
            if agent.id == agent_id:
                self.redis.set(self._id_index_key(agent_id), agent.username, ex=self.default_ttl)
                return agent
        return None

    def update_agent(self, agent: Agent):
        """
        更新坐席账号

        Args:
            agent: 坐席账号
        """
        self._store_agent_record(agent)

    def authenticate(self, username: str, password: str) -> Optional[Agent]:
        """
        验证坐席登录

        Args:
            username: 用户名
            password: 密码（明文）

        Returns:
            坐席账号（验证成功）或 None（验证失败）
        """
        agent = self.get_agent_by_username(username)

        if not agent:
            return None

        # 验证密码
        if not PasswordHasher.verify_password(password, agent.password_hash):
            return None

        # 更新最后登录时间
        agent.last_login = time.time()
        agent.status = AgentStatus.ONLINE
        agent.status_note = None
        agent.status_updated_at = time.time()
        agent.last_active_at = time.time()
        self.update_agent(agent)

        return agent

    def update_status(
        self,
        username: str,
        status: AgentStatus,
        status_note: Optional[str] = None
    ) -> Optional[Agent]:
        """
        更新坐席状态

        Args:
            username: 用户名
            status: 新状态
        """
        agent = self.get_agent_by_username(username)
        if agent:
            agent.status = status
            if status_note is not None:
                note = status_note.strip()
                agent.status_note = note if note else None
            agent.status_updated_at = time.time()
            agent.last_active_at = time.time()
            self.update_agent(agent)
            return agent
        return None

    def update_last_active(self, username: str) -> Optional[float]:
        """
        更新坐席最近活跃时间

        Args:
            username: 用户名

        Returns:
            float: 更新时间戳或 None（坐席不存在）
        """
        agent = self.get_agent_by_username(username)
        if not agent:
            return None

        agent.last_active_at = time.time()
        self.update_agent(agent)
        return agent.last_active_at

    def get_all_agents(self) -> list:
        """
        获取所有坐席账号

        Returns:
            坐席列表
        """
        agents = []
        # 使用 SCAN 遍历所有坐席 key
        for key in self.redis.scan_iter(f"{self.key_prefix}*", count=100):
            data = self.redis.get(key)
            if data:
                try:
                    agent = Agent.parse_raw(data)
                    agents.append(agent)
                except Exception:
                    pass
        return agents

    def delete_agent(self, username: str) -> bool:
        """
        删除坐席账号

        Args:
            username: 用户名

        Returns:
            是否删除成功
        """
        key = self._username_key(username)
        agent = self.get_agent_by_username(username)
        result = self.redis.delete(key)
        if agent:
            self.redis.delete(self._id_index_key(agent.id))
        return result > 0

    def count_admins(self) -> int:
        """
        统计管理员数量

        Returns:
            管理员数量
        """
        agents = self.get_all_agents()
        return sum(1 for a in agents if a.role == AgentRole.ADMIN)


# ====================
# 初始化超级管理员账号
# ====================

def initialize_super_admin(
    agent_manager: AgentManager,
    admin_username: str = "admin",
    admin_password: str = "admin123"
):
    """
    初始化固定的超级管理员账号（系统根账号）

    该账号是系统唯一的预设管理员，用于：
    1. 首次登录系统
    2. 创建其他坐席账号
    3. 管理所有用户权限

    其他所有账号都必须通过该管理员在系统内创建。

    Args:
        agent_manager: 坐席管理器
        admin_username: 管理员用户名（默认 "admin"）
        admin_password: 管理员密码（默认 "admin123"，生产环境请从环境变量读取）
    """
    # 检查超级管理员是否已存在
    existing_admin = agent_manager.get_agent_by_username(admin_username)
    if existing_admin:
        print(f"  ⏭️  超级管理员账号 '{admin_username}' 已存在，跳过初始化")
        return existing_admin

    # 创建超级管理员账号
    admin = agent_manager.create_agent(
        username=admin_username,
        password=admin_password,
        name="系统管理员",
        role=AgentRole.ADMIN,
        max_sessions=20  # 管理员可同时管理更多会话
    )

    print(f"  ✅ 创建超级管理员账号: {admin.username}")
    print(f"  ⚠️  请在首次登录后立即修改密码！")

    return admin



# ====================
# 工具函数
# ====================

def agent_to_dict(agent: Agent) -> Dict[str, Any]:
    """
    将坐席对象转换为字典（隐藏密码）

    Args:
        agent: 坐席账号

    Returns:
        字典（不含 password_hash）
    """
    data = agent.dict()
    data.pop("password_hash", None)  # 移除密码哈希
    return data


# ====================
# JWT 权限中间件
# ====================

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# HTTP Bearer 安全方案
security = HTTPBearer()


def create_jwt_dependencies(agent_token_manager: 'AgentTokenManager', agent_manager: 'AgentManager'):
    """
    创建 JWT 权限依赖项

    Args:
        agent_token_manager: Token 管理器
        agent_manager: 坐席管理器

    Returns:
        tuple: (verify_agent_token, require_admin) 两个依赖项函数
    """

    async def verify_agent_token(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict[str, Any]:
        """
        验证 JWT Token 中间件

        验证请求中的 JWT Token，返回 Token 载荷。

        Returns:
            Token 载荷（包含 agent_id, username, role）

        Raises:
            HTTPException: 401 - Token 无效或已过期
        """
        token = credentials.credentials

        payload = agent_token_manager.verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=401,
                detail="Token 无效或已过期"
            )

        # 验证坐席是否存在
        agent = agent_manager.get_agent_by_username(payload.get("username"))
        if not agent:
            raise HTTPException(
                status_code=401,
                detail="坐席账号不存在"
            )

        return payload

    async def require_admin(
        payload: Dict[str, Any] = Depends(verify_agent_token)
    ) -> Dict[str, Any]:
        """
        要求管理员权限中间件

        验证当前用户是否为管理员。

        Returns:
            Token 载荷

        Raises:
            HTTPException: 403 - 需要管理员权限
        """
        if payload.get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="需要管理员权限"
            )
        return payload

    return verify_agent_token, require_admin


# ====================
# 请求/响应模型
# ====================

class CreateAgentRequest(BaseModel):
    """创建坐席请求"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=1, max_length=50)
    role: AgentRole = AgentRole.AGENT
    max_sessions: int = Field(default=5, ge=1, le=20)
    avatar_url: Optional[str] = None


class UpdateAgentRequest(BaseModel):
    """修改坐席请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    role: Optional[AgentRole] = None
    max_sessions: Optional[int] = Field(None, ge=1, le=20)
    status: Optional[AgentStatus] = None
    avatar_url: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    new_password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    """修改自己密码请求"""
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class UpdateProfileRequest(BaseModel):
    """修改个人资料请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    avatar_url: Optional[str] = None


class UpdateAgentSkillsRequest(BaseModel):
    """更新坐席技能请求"""
    skills: List[AgentSkill] = Field(default_factory=list, description="技能标签列表")

    @field_validator("skills")
    @classmethod
    def validate_total(cls, value: List[AgentSkill]) -> List[AgentSkill]:
        if len(value) > 20:
            raise ValueError("每个坐席最多配置20条技能记录")
        return value


def validate_password(password: str) -> bool:
    """
    验证密码强度

    要求：
    - 至少 8 个字符
    - 包含字母和数字

    Args:
        password: 密码

    Returns:
        是否符合要求
    """
    if len(password) < 8:
        return False

    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)

    return has_letter and has_digit
