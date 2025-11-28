"""
Fiido智能客服后端服务
使用 FastAPI 提供 RESTful API，采用 OAuth+JWT 鉴权
支持基于 Workflow 的多轮对话

【会话隔离机制】
根据官方文档 b.md，会话隔离的核心是 session_name：
1. 前端打开页面时生成唯一的 session_id (存储在 sessionStorage)
2. 前端在每次请求中携带 session_id
3. 后端将 session_id 作为 session_name 传入 JWT，实现会话隔离
4. 工作流已恢复为静态会话 "default"，不再需要动态传入 CONVERSATION_NAME
"""

import os
import json
import time
import asyncio
from typing import Optional
from contextlib import asynccontextmanager
import uuid
import hashlib
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from typing import Dict, Any, List, Literal

from cozepy import Coze, TokenAuth, JWTAuth, JWTOAuthApp
import httpx

# 导入 OAuth Token 管理器
from src.oauth_token_manager import OAuthTokenManager

# 导入 SessionState 和 Regulator 模块（P0 任务）
from src.session_state import (
    SessionState,
    SessionStatus,
    InMemorySessionStore,
    Message,
    EscalationInfo
)
from src.redis_session_store import RedisSessionStore  # Redis 存储实现
from src.regulator import Regulator, RegulatorConfig
from src.shift_config import get_shift_config, is_in_shift
from src.email_service import get_email_service, send_escalation_email

# 导入坐席认证系统模块
from src.agent_auth import (
    AgentManager,
    AgentTokenManager,
    initialize_default_agents,
    LoginRequest,
    LoginResponse,
    agent_to_dict,
    Agent,
    AgentStatus
)

# 【模块3】导入快捷回复系统模块
from src.quick_reply import QuickReply, QuickReplyCategory, QUICK_REPLY_CATEGORIES, SUPPORTED_VARIABLES
from src.quick_reply_store import QuickReplyStore
from src.variable_replacer import VariableReplacer, build_variable_context

# 【模块5】导入协助请求模块
from src.assist_request import (
    AssistRequest,
    AssistStatus,
    CreateAssistRequestRequest,
    AnswerAssistRequestRequest,
    assist_request_store
)

# 加载环境变量
load_dotenv()

# 配置 HTTP 客户端超时
HTTP_TIMEOUT = httpx.Timeout(
    connect=float(os.getenv("HTTP_TIMEOUT_CONNECT", 10.0)),
    read=float(os.getenv("HTTP_TIMEOUT_READ", 30.0)),
    write=10.0,
    pool=10.0
)


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    parameters: Optional[dict] = {}
    user_id: Optional[str] = None  # 会话 ID（前端生成的唯一标识）
    conversation_id: Optional[str] = None  # Conversation ID（用于保留历史对话）


class ChatResponse(BaseModel):
    """聊天响应模型"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


class NewConversationRequest(BaseModel):
    """创建新对话请求模型"""
    user_id: str  # session_id


class ConversationResponse(BaseModel):
    """Conversation 响应模型"""
    success: bool
    conversation_id: Optional[str] = None
    error: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """刷新 Token 请求模型"""
    refresh_token: str


class UpdateAgentStatusRequest(BaseModel):
    """坐席状态更新请求"""
    status: AgentStatus
    status_note: Optional[str] = Field(
        default=None,
        max_length=120,
        description="状态说明（可选）"
    )


# 全局变量
coze_client: Optional[Coze] = None
token_manager: Optional[OAuthTokenManager] = None
jwt_oauth_app: Optional[JWTOAuthApp] = None  # 用于 Chat SDK 的 JWTOAuthApp
session_store: Optional[InMemorySessionStore] = None  # 会话状态存储（P0）
regulator: Optional[Regulator] = None  # 监管策略引擎（P0）
agent_manager: Optional[AgentManager] = None  # 坐席账号管理器
agent_token_manager: Optional[AgentTokenManager] = None  # 坐席 JWT Token 管理器
quick_reply_store: Optional['QuickReplyStore'] = None  # 快捷回复存储管理器（模块3）
variable_replacer: Optional['VariableReplacer'] = None  # 变量替换器（模块3）
WORKFLOW_ID: str = ""
APP_ID: str = ""  # AI 应用 ID（应用中嵌入对话流时必需）
AUTH_MODE: str = ""  # 鉴权模式：OAUTH_JWT 或 PAT

# Conversation 管理 - 存储每个 session_name 对应的 conversation_id
# 实现原理: 首次不传 conversation_id,Coze 会自动生成并返回
# 后续对话必须传入相同的 conversation_id 以保持上下文
conversation_cache: dict = {}  # {session_name: conversation_id}

# P0-5: SSE 消息队列 - 用于人工消息推送
# 结构: {session_name: asyncio.Queue()}
sse_queues: dict = {}  # type: dict[str, asyncio.Queue]

# 坐席状态相关配置
AGENT_AUTO_BUSY_SECONDS = int(os.getenv("AGENT_AUTO_BUSY_SECONDS", "300"))
AGENT_STATS_TTL = int(os.getenv("AGENT_STATS_TTL", "86400"))


def _agent_stats_key(agent_identifier: str) -> str:
    """构建坐席当日统计的 Redis Key"""
    date_key = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"agent_stats:{agent_identifier}:{date_key}"


def _update_agent_stat(agent_identifier: str, field: str, amount: float, *, as_int: bool = False):
    """更新坐席统计字段"""
    if not agent_manager or not hasattr(agent_manager, "redis"):
        return

    redis_client = getattr(agent_manager, "redis", None)
    if not redis_client:
        return

    key = _agent_stats_key(agent_identifier)
    try:
        if as_int:
            redis_client.hincrby(key, field, int(amount))
        else:
            redis_client.hincrbyfloat(key, field, float(amount))
        redis_client.expire(key, AGENT_STATS_TTL)
    except Exception as exc:
        print(f"⚠️ 更新坐席统计失败: {exc}")


def _parse_float(value: Optional[str]) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _parse_int(value: Optional[str]) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _record_agent_response_time(agent_identifier: str, seconds: float):
    """记录坐席响应时间"""
    if seconds is None or seconds < 0:
        return
    _update_agent_stat(agent_identifier, "total_response_time", seconds)
    _update_agent_stat(agent_identifier, "response_samples", 1, as_int=True)


def _record_agent_session_duration(agent_identifier: str, seconds: float):
    """记录坐席处理时长并增加完成数"""
    if seconds is None or seconds < 0:
        return
    _update_agent_stat(agent_identifier, "total_duration", seconds)
    _update_agent_stat(agent_identifier, "duration_samples", 1, as_int=True)
    _update_agent_stat(agent_identifier, "processed_count", 1, as_int=True)


def _load_agent_stats(agent_identifier: str) -> Dict[str, Any]:
    """读取坐席当日统计原始数据"""
    if not agent_manager or not hasattr(agent_manager, "redis"):
        return {}
    redis_client = getattr(agent_manager, "redis", None)
    if not redis_client:
        return {}
    key = _agent_stats_key(agent_identifier)
    try:
        return redis_client.hgetall(key) or {}
    except Exception as exc:
        print(f"⚠️ 读取坐席统计失败: {exc}")
        return {}


def _compose_today_stats(agent_identifier: str) -> Dict[str, Any]:
    """组装今日统计指标"""
    raw = _load_agent_stats(agent_identifier)
    total_response = _parse_float(raw.get("total_response_time"))
    response_samples = _parse_int(raw.get("response_samples"))
    total_duration = _parse_float(raw.get("total_duration"))
    duration_samples = _parse_int(raw.get("duration_samples"))
    satisfaction_total = _parse_float(raw.get("satisfaction_total"))
    satisfaction_samples = _parse_int(raw.get("satisfaction_samples"))
    processed = _parse_int(raw.get("processed_count"))

    avg_response = total_response / response_samples if response_samples else 0.0
    avg_duration = total_duration / duration_samples if duration_samples else 0.0
    satisfaction = satisfaction_total / satisfaction_samples if satisfaction_samples else 0.0

    return {
        "processed_count": processed,
        "avg_response_time": round(avg_response, 2),
        "avg_duration": round(avg_duration, 2),
        "satisfaction_score": round(satisfaction, 2)
    }


async def _count_agent_live_sessions(agent_identifier: str) -> int:
    """统计坐席当前处理中的会话数"""
    if not session_store:
        return 0
    try:
        live_sessions = await session_store.list_by_status(
            status=SessionStatus.MANUAL_LIVE,
            limit=500
        )
        return sum(
            1
            for session in live_sessions
            if session.assigned_agent and session.assigned_agent.id == agent_identifier
        )
    except Exception as exc:
        print(f"⚠️ 统计当前会话失败: {exc}")
        return 0


async def _build_agent_status_payload(agent_obj: Agent, agent_identifier: str) -> Dict[str, Any]:
    """构建返回给前端的状态信息"""
    today_stats = _compose_today_stats(agent_identifier)
    current_sessions = await _count_agent_live_sessions(agent_identifier)
    return {
        "status": agent_obj.status.value if isinstance(agent_obj.status, AgentStatus) else agent_obj.status,
        "status_note": agent_obj.status_note or "",
        "status_updated_at": agent_obj.status_updated_at,
        "last_active_at": agent_obj.last_active_at,
        "current_sessions": current_sessions,
        "max_sessions": agent_obj.max_sessions,
        "today_stats": today_stats
    }


def _auto_adjust_agent_status(agent_obj: Agent) -> Agent:
    """根据最近活跃时间自动切换状态"""
    if not agent_manager:
        return agent_obj

    last_active = agent_obj.last_active_at or 0
    now = time.time()
    if (
        agent_obj.status == AgentStatus.ONLINE
        and AGENT_AUTO_BUSY_SECONDS > 0
        and now - last_active > AGENT_AUTO_BUSY_SECONDS
    ):
        agent_obj.status = AgentStatus.BUSY
        if not agent_obj.status_note:
            agent_obj.status_note = "系统检测到超过5分钟无操作，已自动置为忙碌"
        agent_obj.status_updated_at = now
        try:
            agent_manager.update_agent(agent_obj)
        except Exception as exc:
            print(f"⚠️ 自动更新坐席状态失败: {exc}")
    return agent_obj


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global coze_client, token_manager, jwt_oauth_app, session_store, regulator, agent_manager, agent_token_manager, quick_reply_store, variable_replacer, WORKFLOW_ID, APP_ID, AUTH_MODE

    # 读取配置
    WORKFLOW_ID = os.getenv("COZE_WORKFLOW_ID", "")
    APP_ID = os.getenv("COZE_APP_ID", "")
    AUTH_MODE = os.getenv("COZE_AUTH_MODE", "OAUTH_JWT")
    api_base = os.getenv("COZE_API_BASE", "https://api.coze.com")

    if not WORKFLOW_ID:
        raise ValueError("COZE_WORKFLOW_ID 环境变量未设置")
    if not APP_ID:
        raise ValueError("COZE_APP_ID 环境变量未设置")

    print(f"\n{'=' * 60}")
    print(f"🚀 Fiido 智能客服后端服务初始化")
    print(f"{'=' * 60}")
    print(f"🔐 鉴权模式: {AUTH_MODE}")
    print(f"🌐 API Base: {api_base}")
    print(f"📱 App ID: {APP_ID}")
    print(f"🔄 Workflow ID: {WORKFLOW_ID}")
    print(f"💬 多轮对话: 已启用")

    # 初始化 SessionState 存储（P0 + Redis 数据持久化）
    # 约束16.3.1 - Redis 不可用时降级到内存存储
    try:
        # 读取 Redis 配置
        USE_REDIS = os.getenv("USE_REDIS", "true").lower() == "true"
        REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
        REDIS_TIMEOUT = float(os.getenv("REDIS_TIMEOUT", "5.0"))
        REDIS_SESSION_TTL = int(os.getenv("REDIS_SESSION_TTL", "86400"))  # 24小时

        if USE_REDIS:
            try:
                session_store = RedisSessionStore(
                    redis_url=REDIS_URL,
                    max_connections=REDIS_MAX_CONNECTIONS,
                    socket_timeout=REDIS_TIMEOUT,
                    socket_connect_timeout=REDIS_TIMEOUT,
                    default_ttl=REDIS_SESSION_TTL
                )
                print(f"✅ 使用 Redis 存储")
                print(f"   URL: {REDIS_URL}")
                print(f"   连接池: {REDIS_MAX_CONNECTIONS}")
                print(f"   TTL: {REDIS_SESSION_TTL}s ({REDIS_SESSION_TTL/3600}h)")

                # 健康检查
                health = session_store.check_health()
                if health.get("status") == "healthy":
                    print(f"   内存: {health['used_memory_mb']}MB / {health['max_memory_mb']}")
                    print(f"   会话数: {health['total_sessions']}")
                else:
                    print(f"   ⚠️ 健康检查异常: {health.get('error')}")

            except Exception as redis_error:
                print(f"❌ Redis 连接失败: {redis_error}")
                print(f"⚠️  降级到内存存储（生产环境不推荐）")
                session_store = InMemorySessionStore()
        else:
            session_store = InMemorySessionStore()
            print(f"⚠️ 使用内存存储（开发/测试环境）")

    except Exception as e:
        print(f"❌ SessionState 存储初始化失败: {str(e)}")
        print(f"⚠️  降级到内存存储")
        session_store = InMemorySessionStore()

    # 初始化 Regulator 监管引擎（P0）
    try:
        regulator_config = RegulatorConfig()
        regulator = Regulator(regulator_config)
        print(f"✅ Regulator 监管引擎初始化成功")
        print(f"   关键词: {len(regulator_config.keywords)}个")
        print(f"   失败阈值: {regulator_config.fail_threshold}")
    except Exception as e:
        print(f"⚠️  Regulator 初始化失败: {str(e)}")

    # OAuth+JWT 鉴权
    try:
        token_manager = OAuthTokenManager.from_env()
        # 获取初始 token
        access_token = token_manager.get_access_token()

        # 创建带超时配置的 HTTP 客户端（禁用环境代理以避免 SOCKS 协议问题）
        http_client = httpx.Client(
            timeout=HTTP_TIMEOUT,
            trust_env=False  # 不从环境变量读取代理配置，避免 SOCKS 协议不支持的问题
        )
        coze_client = Coze(
            auth=TokenAuth(token=access_token),
            base_url=api_base,
            http_client=http_client
        )
        print(f"✅ OAuth+JWT 鉴权初始化成功")
        print(f"   Token 预览: {access_token[:30]}...")
        print(f"   超时配置: 连接 10s, 读取 30s")

        # 创建 JWTOAuthApp (用于 Chat SDK token 生成)
        private_key_file = os.getenv("COZE_OAUTH_PRIVATE_KEY_FILE")
        if private_key_file and os.path.exists(private_key_file):
            with open(private_key_file, "r") as f:
                private_key = f.read()

            jwt_oauth_app = JWTOAuthApp(
                client_id=os.getenv("COZE_OAUTH_CLIENT_ID"),
                private_key=private_key,
                public_key_id=os.getenv("COZE_OAUTH_PUBLIC_KEY_ID"),
                base_url=api_base,
            )
            print(f"✅ JWTOAuthApp 初始化成功 (用于 Chat SDK)")
        else:
            print(f"⚠️  未找到私钥文件，Chat SDK token 生成将不可用")

    except Exception as e:
        raise ValueError(f"OAuth+JWT 初始化失败: {str(e)}")

    # 初始化坐席认证系统
    try:
        # JWT密钥（生产环境必须使用强随机密钥）
        JWT_SECRET = os.getenv("JWT_SECRET_KEY", "dev_secret_key_change_in_production_2025")

        # 初始化坐席 Token 管理器
        agent_token_manager = AgentTokenManager(
            secret_key=JWT_SECRET,
            algorithm="HS256",
            access_token_expire_minutes=int(os.getenv("AGENT_TOKEN_EXPIRE_MINUTES", "60")),
            refresh_token_expire_days=int(os.getenv("AGENT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        )

        # 初始化坐席账号管理器
        agent_manager = AgentManager(session_store)

        # 初始化默认坐席账号
        print(f"🔐 初始化坐席认证系统...")
        initialize_default_agents(agent_manager)

        print(f"✅ 坐席认证系统初始化成功")
        print(f"   Token过期时间: 60分钟")
        print(f"   刷新Token过期: 7天")

    except Exception as e:
        print(f"⚠️  坐席认证系统初始化失败: {str(e)}")
        print(f"   坐席登录功能将不可用")

    # 【模块3】初始化快捷回复系统
    try:
        # 使用session_store中的redis_client
        if USE_REDIS and hasattr(session_store, 'redis'):
            quick_reply_store = QuickReplyStore(session_store.redis)
            variable_replacer = VariableReplacer()
            print(f"✅ 快捷回复系统初始化成功")
            print(f"   存储: Redis")
        else:
            quick_reply_store = None
            variable_replacer = VariableReplacer()
            print(f"⚠️  快捷回复系统：内存存储未实现，功能受限")

    except Exception as e:
        print(f"⚠️  快捷回复系统初始化失败: {str(e)}")
        quick_reply_store = None
        variable_replacer = VariableReplacer()

    print(f"{'=' * 60}\n")

    yield

    # 关闭时清理
    print("👋 关闭 Coze 客户端")


# 创建 FastAPI 应用
app = FastAPI(
    title="Fiido智能客服API",
    description="基于 Coze Workflow 的智能客服后端服务，支持 OAuth+JWT 鉴权和多轮对话",
    version="2.1.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 获取当前文件所在目录（用于提供静态文件）
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 挂载静态文件目录（提供图片等资源）
# 访问方式：http://IP:8000/fiido2.png
try:
    app.mount("/static", StaticFiles(directory=CURRENT_DIR), name="static")
except Exception as e:
    print(f"⚠️  静态文件挂载失败: {e}")


# ====================
# JWT 权限中间件 (Agent Authorization Middleware)
# ====================

# 初始化 HTTPBearer 安全方案
security = HTTPBearer()


async def verify_agent_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    验证 JWT Token

    Args:
        credentials: HTTP Bearer 凭证

    Returns:
        Dict: Token 载荷（包含 agent_id, username, role）

    Raises:
        HTTPException 401: Token 无效或已过期
    """
    if not agent_token_manager:
        raise HTTPException(
            status_code=503,
            detail="坐席认证系统未初始化"
        )

    token = credentials.credentials

    # 验证 Token
    payload = agent_token_manager.verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Token 无效或已过期"
        )

    return payload


async def require_admin(
    agent: Dict[str, Any] = Depends(verify_agent_token)
) -> Dict[str, Any]:
    """
    要求管理员权限

    Args:
        agent: 经过 verify_agent_token 验证的坐席信息

    Returns:
        Dict: Token 载荷

    Raises:
        HTTPException 403: 权限不足（非管理员）
    """
    if agent.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="需要管理员权限"
        )

    return agent


async def require_agent(
    agent: Dict[str, Any] = Depends(verify_agent_token)
) -> Dict[str, Any]:
    """
    要求坐席权限（包括管理员）

    Args:
        agent: 经过 verify_agent_token 验证的坐席信息

    Returns:
        Dict: Token 载荷

    说明:
        此函数用于保护坐席工作台 API
        管理员和普通坐席都可以访问
    """
    return agent


def generate_user_id(ip_address: str = None, user_agent: str = None) -> str:
    """生成唯一的用户 ID（备用方案）"""
    # 如果没有提供信息,使用 UUID
    if not ip_address and not user_agent:
        return f"user_{uuid.uuid4().hex[:16]}"

    # 使用 IP 和 User-Agent 生成稳定的用户 ID
    identifier = f"{ip_address}_{user_agent}"
    hash_object = hashlib.md5(identifier.encode())
    return f"user_{hash_object.hexdigest()[:16]}"


def refresh_coze_client_if_needed():
    """在 OAuth+JWT 模式下，检查并刷新 token"""
    global coze_client, token_manager

    if token_manager:
        # 获取 token（自动处理缓存和刷新）
        access_token = token_manager.get_access_token()

        # 更新 Coze 客户端的 token（带超时配置，禁用环境代理）
        api_base = os.getenv("COZE_API_BASE", "https://api.coze.com")
        http_client = httpx.Client(timeout=HTTP_TIMEOUT, trust_env=False)
        coze_client = Coze(
            auth=TokenAuth(token=access_token),
            base_url=api_base,
            http_client=http_client
        )


@app.get("/")
async def root():
    """根路径 - 返回 API 信息"""
    return {
        "service": "Fiido智能客服API",
        "status": "running",
        "version": "2.2.0",
        "auth_mode": "OAUTH_JWT",
        "frontend": "Vue 3 前端（frontend/ 目录）",
        "frontend_url": "请访问 http://localhost:5173（需先启动 Vue 开发服务器）",
        "endpoints": {
            "chat": "/api/chat",
            "chat_stream": "/api/chat/stream",
            "health": "/api/health",
            "config": "/api/config",
            "bot_info": "/api/bot/info",
            "token_info": "/api/token/info",
            "conversation_new": "/api/conversation/new",
            "conversation_clear": "/api/conversation/clear"
        },
        "docs": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/index2.html")
async def serve_index():
    """提供前端页面（明确指定文件名）"""
    index_path = os.path.join(CURRENT_DIR, "index2.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        raise HTTPException(status_code=404, detail="前端文件未找到")


@app.get("/fiido2.png")
async def serve_icon():
    """提供客服头像图片"""
    icon_path = os.path.join(CURRENT_DIR, "fiido2.png")
    if os.path.exists(icon_path):
        return FileResponse(icon_path)
    else:
        raise HTTPException(status_code=404, detail="图片文件未找到")


@app.post("/api/conversation/create")
async def create_conversation(request: NewConversationRequest):
    """
    创建新的 Conversation (用于多轮对话)
    每次创建新对话时调用此接口,返回 conversation_id
    """
    if coze_client is None:
        raise HTTPException(status_code=503, detail="Coze 客户端未初始化")

    try:
        session_id = request.user_id

        # 获取带 session_name 的 token
        access_token = token_manager.get_access_token(session_name=session_id)

        # 刷新 coze_client (确保使用正确的 token，禁用环境代理)
        api_base = os.getenv("COZE_API_BASE", "https://api.coze.com")
        http_client = httpx.Client(timeout=HTTP_TIMEOUT, trust_env=False)
        temp_coze_client = Coze(
            auth=TokenAuth(token=access_token),
            base_url=api_base,
            http_client=http_client
        )

        # 使用 Coze SDK 创建 conversation
        conversation = temp_coze_client.conversations.create()

        print(f"✅ 创建新 Conversation: {conversation.id} (session: {session_id})")

        return ConversationResponse(
            success=True,
            conversation_id=conversation.id
        )

    except Exception as e:
        error_msg = str(e)
        print(f"❌ 创建 Conversation 失败: {error_msg}")
        return ConversationResponse(
            success=False,
            error=error_msg
        )


@app.post("/api/conversation/new")
async def create_new_conversation(request: dict):
    """
    创建新对话 (使用 Python SDK)
    保持 session_id 不变,但创建新的 conversation

    【Coze API 约束】
    - 严格遵守 PRD 12.1.1: 不手动生成 conversation_id，由 Coze 自动生成
    - 必须传入 session_name 实现会话隔离
    """
    global conversation_cache

    session_id = request.get("session_id")

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    if not jwt_oauth_app:
        raise HTTPException(status_code=503, detail="JWTOAuthApp 未初始化")

    try:
        # 使用 JWTOAuthApp 生成带 session_name 的 token
        token_response = jwt_oauth_app.get_access_token(
            ttl=3600,
            session_name=session_id  # 【Coze 约束】会话隔离关键
        )

        # 提取 access_token
        access_token = token_response.access_token if hasattr(token_response, 'access_token') else token_response

        # 使用 Python SDK 创建 Coze 客户端（配置超时和代理）
        api_base = os.getenv("COZE_API_BASE", "https://api.coze.com")
        http_client = httpx.Client(timeout=HTTP_TIMEOUT, trust_env=False)
        temp_coze = Coze(
            auth=TokenAuth(token=access_token),
            base_url=api_base,
            http_client=http_client
        )

        # 【Coze 约束】创建新 conversation（由 Coze 自动生成 ID）
        conversation = temp_coze.conversations.create()

        # 更新缓存：保存新的 conversation_id
        conversation_cache[session_id] = conversation.id

        print(f"✅ 新对话已创建: {conversation.id} (session: {session_id})")

        return {
            "success": True,
            "conversation_id": conversation.id
        }
    except Exception as e:
        print(f"❌ 创建对话失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/api/conversation/clear")
async def clear_conversation_history(request: dict):
    """
    清除历史会话
    实现方式：创建新的 conversation_id 并更新缓存

    【Coze API 约束】
    - 严格遵守 PRD 12.1.1: conversation_id 由 Coze 生成，不手动创建
    - 清除历史 = 创建新会话，废弃旧 conversation_id
    - 必须更新 session_name → conversation_id 映射关系
    """
    global conversation_cache

    session_id = request.get("session_id")

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    if not jwt_oauth_app:
        raise HTTPException(status_code=503, detail="JWTOAuthApp 未初始化")

    try:
        # 记录旧的 conversation_id（用于日志）
        old_conversation_id = conversation_cache.get(session_id, "无")

        # 使用 JWTOAuthApp 生成带 session_name 的 token
        token_response = jwt_oauth_app.get_access_token(
            ttl=3600,
            session_name=session_id  # 【Coze 约束】会话隔离
        )

        # 提取 access_token
        access_token = token_response.access_token if hasattr(token_response, 'access_token') else token_response

        # 使用 Python SDK 创建 Coze 客户端（配置超时和代理）
        api_base = os.getenv("COZE_API_BASE", "https://api.coze.com")
        http_client = httpx.Client(timeout=HTTP_TIMEOUT, trust_env=False)
        temp_coze = Coze(
            auth=TokenAuth(token=access_token),
            base_url=api_base,
            http_client=http_client
        )

        # 【Coze 约束】创建新的 conversation（自动生成新 ID）
        new_conversation = temp_coze.conversations.create()

        # 更新缓存：用新 conversation_id 替换旧的
        conversation_cache[session_id] = new_conversation.id

        print(f"✅ 历史会话已清除")
        print(f"   Session: {session_id}")
        print(f"   旧 Conversation: {old_conversation_id}")
        print(f"   新 Conversation: {new_conversation.id}")

        return {
            "success": True,
            "conversation_id": new_conversation.id,
            "message": "历史会话已清除，新对话已创建"
        }
    except Exception as e:
        print(f"❌ 清除历史失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    if coze_client is None:
        raise HTTPException(status_code=503, detail="Coze 客户端未初始化")

    health_info = {
        "status": "healthy",
        "coze_connected": True,
        "workflow_id": WORKFLOW_ID,
        "app_id": APP_ID,
        "auth_mode": "OAUTH_JWT",
        "session_isolation": True  # 会话隔离已启用
    }

    # OAuth+JWT 模式下添加 token 信息
    if token_manager:
        health_info["token_info"] = token_manager.get_token_info()

    return health_info


@app.get("/api/config")
async def get_config():
    """获取前端所需的配置信息（不包含敏感信息）"""
    return {
        "appId": APP_ID,
        "workflowId": WORKFLOW_ID,
        "authMode": "OAUTH_JWT",
        "sessionIsolation": True  # 会话隔离已启用
    }


@app.get("/api/shift/config")
async def get_shift_config_api():
    """获取工作时间配置"""
    try:
        config = get_shift_config()
        return {
            "success": True,
            "data": config.get_config()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/shift/status")
async def get_shift_status():
    """获取当前是否在工作时间"""
    try:
        in_shift = is_in_shift()
        config = get_shift_config()
        return {
            "success": True,
            "data": {
                "is_in_shift": in_shift,
                "message": "人工客服在线" if in_shift else "当前为非工作时间",
                "shift_hours": f"{config.shift_start.strftime('%H:%M')} - {config.shift_end.strftime('%H:%M')}"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/token/info")
async def get_token_info():
    """获取当前 token 信息"""
    if not token_manager:
        raise HTTPException(status_code=503, detail="Token 管理器未初始化")

    return token_manager.get_token_info()


@app.post("/api/token/refresh")
async def refresh_token():
    """手动刷新 token"""
    global coze_client, token_manager

    if not token_manager:
        raise HTTPException(status_code=503, detail="Token 管理器未初始化")

    try:
        # 强制刷新 token
        new_token = token_manager.refresh_token()

        # 更新 Coze 客户端（禁用环境代理）
        api_base = os.getenv("COZE_API_BASE", "https://api.coze.com")
        http_client = httpx.Client(timeout=HTTP_TIMEOUT, trust_env=False)
        coze_client = Coze(
            auth=TokenAuth(token=new_token),
            base_url=api_base,
            http_client=http_client
        )

        return {
            "success": True,
            "message": "Token 刷新成功",
            "token_info": token_manager.get_token_info()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token 刷新失败: {str(e)}")


@app.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    同步聊天接口（使用 Coze Workflow Chat API）
    通过 session_name + conversation_id 实现完整的会话隔离

    实现原理(基于官方文档):
    1. JWT 中传入 session_name (用户唯一标识)
    2. 首次对话不传 conversation_id,系统自动生成
    3. 后端存储 session_name 与 conversation_id 的映射
    4. 后续对话传入相同的 conversation_id 以保持上下文
    """
    global conversation_cache

    if coze_client is None:
        raise HTTPException(status_code=503, detail="Coze 客户端未初始化")

    try:
        # 获取会话标识（session_id），如果没有则生成
        session_id = request.user_id or generate_user_id()

        # 【P0-3 前置处理】检查会话状态 - 如果正在人工接管，拒绝AI对话
        if session_store and regulator:
            try:
                # 获取或创建会话状态
                conversation_id_for_state = request.conversation_id or conversation_cache.get(session_id)
                session_state = await session_store.get_or_create(
                    session_name=session_id,
                    conversation_id=conversation_id_for_state
                )

                # 🔴 P0-1: 如果正在人工接管中(包括等待人工和人工服务中)，返回 409 状态码
                if session_state.status in [SessionStatus.PENDING_MANUAL, SessionStatus.MANUAL_LIVE]:
                    print(f"⚠️  会话 {session_id} 状态为 {session_state.status}，拒绝AI对话")
                    raise HTTPException(
                        status_code=409,
                        detail=f"SESSION_IN_MANUAL_MODE: {session_state.status}"
                    )

                print(f"📊 会话状态: {session_state.status}")
            except HTTPException:
                raise
            except Exception as state_error:
                # ⚠️ 状态检查失败不应影响核心对话功能
                print(f"⚠️  状态检查异常（不影响对话）: {str(state_error)}")

        # 【会话隔离核心1】将 session_id 作为 session_name 传入 JWT
        access_token = token_manager.get_access_token(session_name=session_id)
        print(f"🔐 会话隔离: session_name={session_id}")

        # 【会话隔离核心2】管理 conversation_id
        # 检查是否已有该用户的 conversation_id
        conversation_id = request.conversation_id

        if not conversation_id:
            # 检查缓存
            conversation_id = conversation_cache.get(session_id)

            if conversation_id:
                print(f"♻️  使用缓存的 Conversation: {conversation_id}")
            else:
                print(f"🆕 首次对话,将自动生成 conversation_id")

        # 准备参数（Workflow Chat API 格式）
        api_base = os.getenv("COZE_API_BASE", "https://api.coze.com")
        url = f"{api_base}/v1/workflows/chat"

        # 构建请求体 - 添加 session_name 字段实现会话隔离
        payload = {
            "workflow_id": WORKFLOW_ID,
            "app_id": APP_ID,
            "session_name": session_id,  # 【关键1】session_name
            "parameters": {
                "USER_INPUT": request.message,
            },
            "additional_messages": [
                {
                    "content": request.message,
                    "content_type": "text",
                    "role": "user",
                    "type": "question"
                }
            ]
        }

        # 【关键2】如果有 conversation_id,添加到 payload
        if conversation_id:
            payload["conversation_id"] = conversation_id
            print(f"💬 使用 Conversation: {conversation_id}")

        # 如果有额外参数，合并到 parameters
        if request.parameters:
            payload["parameters"].update(request.parameters)

        # 【调试】打印完整请求
        print(f"📤 发送请求到 Coze:")
        print(f"   URL: {url}")
        print(f"   Session: {session_id}")
        print(f"   Payload session_name: {payload.get('session_name')}")
        print(f"   完整 Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")

        # 发送请求（使用流式接收）
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        http_client = httpx.Client(timeout=HTTP_TIMEOUT, trust_env=False)

        with http_client.stream('POST', url, json=payload, headers=headers) as response:
            if response.status_code != 200:
                error_text = response.text
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Coze API 错误: {error_text}"
                )

            # 收集所有消息内容和 conversation_id
            response_messages = []
            returned_conversation_id = None
            event_type = None

            for line in response.iter_lines():
                if not line:
                    continue

                line = line.strip()
                if line.startswith('event:'):
                    event_type = line[6:].strip()
                elif line.startswith('data:'):
                    try:
                        data_str = line[5:].strip()
                        data = json.loads(data_str)

                        # 提取 conversation_id (如果存在)
                        if 'conversation_id' in data and not returned_conversation_id:
                            returned_conversation_id = data['conversation_id']

                        # 处理消息增量事件
                        if event_type == 'conversation.message.delta':
                            if 'content' in data and data.get('role') == 'assistant':
                                content = data['content']
                                if content:
                                    response_messages.append(content)

                    except json.JSONDecodeError:
                        pass

        # 【关键3】如果是首次对话,保存自动生成的 conversation_id
        if not conversation_id and returned_conversation_id:
            conversation_cache[session_id] = returned_conversation_id
            print(f"✅ 保存新 conversation: {returned_conversation_id} (session: {session_id})")

        # 合并所有消息
        final_message = "".join(response_messages) if response_messages else ""

        # 【P0-3 后置处理】更新会话状态和触发监管检查
        if session_store and regulator and final_message:
            try:
                # 获取会话状态
                conversation_id_for_update = returned_conversation_id or conversation_id
                session_state = await session_store.get_or_create(
                    session_name=session_id,
                    conversation_id=conversation_id_for_update
                )

                # 添加用户消息到历史
                user_message = Message(
                    role="user",
                    content=request.message
                )
                session_state.add_message(user_message)

                # 添加AI响应到历史
                ai_message = Message(
                    role="assistant",
                    content=final_message
                )
                session_state.add_message(ai_message)

                # 触发监管引擎评估
                regulator_result = regulator.evaluate(
                    session=session_state,
                    user_message=request.message,
                    ai_response=final_message
                )

                # 如果需要升级到人工
                if regulator_result.should_escalate:
                    print(f"🚨 触发人工接管: {regulator_result.reason} - {regulator_result.details}")

                    # 更新升级信息
                    session_state.escalation = EscalationInfo(
                        reason=regulator_result.reason,
                        details=regulator_result.details,
                        severity=regulator_result.severity
                    )

                    # 状态转换为 pending_manual
                    session_state.transition_status(
                        new_status=SessionStatus.PENDING_MANUAL
                    )

                    # 记录日志
                    print(json.dumps({
                        "event": "escalation_triggered",
                        "session_name": session_id,
                        "reason": regulator_result.reason,
                        "severity": regulator_result.severity,
                        "timestamp": int(time.time())
                    }, ensure_ascii=False))

                # 保存会话状态
                await session_store.save(session_state)

            except Exception as regulator_error:
                # ⚠️ 监管逻辑失败不应影响核心对话功能
                print(f"⚠️  监管处理异常（不影响对话）: {str(regulator_error)}")
                import traceback
                traceback.print_exc()

        return ChatResponse(
            success=True,
            message=final_message
        )

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        print(f"❌ 聊天错误: {error_msg}")

        # 如果是 token 过期错误，尝试刷新
        if "token" in error_msg.lower() or "auth" in error_msg.lower() or "401" in error_msg:
            if token_manager:
                try:
                    print("🔄 检测到认证错误，清除token缓存...")
                    session_id = request.user_id or generate_user_id()
                    token_manager.invalidate_token(session_name=session_id)
                    # 递归重试一次
                    return await chat(request)
                except Exception as retry_error:
                    error_msg = f"Token 刷新后仍然失败: {str(retry_error)}"

        return ChatResponse(
            success=False,
            error=error_msg
        )


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    流式聊天接口 - 使用 Coze Workflow Chat API
    通过 session_name + conversation_id 实现完整的会话隔离

    实现原理(基于官方文档):
    1. JWT 中传入 session_name (用户唯一标识)
    2. 首次对话不传 conversation_id,系统自动生成
    3. 后端存储 session_name 与 conversation_id 的映射
    4. 后续对话传入相同的 conversation_id 以保持上下文
    """
    global conversation_cache

    if coze_client is None:
        raise HTTPException(status_code=503, detail="Coze 客户端未初始化")

    async def event_generator():
        """SSE 事件生成器"""
        try:
            # 获取会话标识（session_id），如果没有则生成
            session_id = request.user_id or generate_user_id()

            # 【P0-5】创建 SSE 消息队列（如果不存在）
            global sse_queues
            if session_id not in sse_queues:
                sse_queues[session_id] = asyncio.Queue()
                print(f"✅ SSE 队列已创建: {session_id}")

            # 【P0-3 前置处理】检查会话状态 - 如果正在人工接管，拒绝AI对话
            if session_store and regulator:
                try:
                    # 获取或创建会话状态
                    conversation_id_for_state = request.conversation_id or conversation_cache.get(session_id)
                    session_state = await session_store.get_or_create(
                        session_name=session_id,
                        conversation_id=conversation_id_for_state
                    )

                    # 🔴 P0-1: 如果正在人工接管中(包括等待人工和人工服务中)，发送错误事件
                    if session_state.status in [SessionStatus.PENDING_MANUAL, SessionStatus.MANUAL_LIVE]:
                        print(f"⚠️  流式会话 {session_id} 状态为 {session_state.status}，拒绝AI对话")
                        error_data = {
                            "type": "error",
                            "content": f"SESSION_IN_MANUAL_MODE: {session_state.status}"
                        }
                        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                        return

                    print(f"📊 流式会话状态: {session_state.status}")
                except Exception as state_error:
                    # ⚠️ 状态检查失败不应影响核心对话功能
                    print(f"⚠️  流式状态检查异常（不影响对话）: {str(state_error)}")

            # 【会话隔离核心1】将 session_id 作为 session_name 传入 JWT
            access_token = token_manager.get_access_token(session_name=session_id)
            print(f"🔐 流式会话隔离: session_name={session_id}")

            # 【会话隔离核心2】管理 conversation_id
            conversation_id = request.conversation_id

            if not conversation_id:
                # 检查缓存
                conversation_id = conversation_cache.get(session_id)

                if conversation_id:
                    print(f"♻️  流式接口使用缓存的 Conversation: {conversation_id}")
                else:
                    print(f"🆕 流式接口首次对话,将自动生成 conversation_id")

            # 准备参数（Workflow Chat API 格式）
            api_base = os.getenv("COZE_API_BASE", "https://api.coze.com")
            url = f"{api_base}/v1/workflows/chat"

            # 构建请求体
            payload = {
                "workflow_id": WORKFLOW_ID,
                "app_id": APP_ID,
                "session_name": session_id,  # 【关键1】session_name
                "parameters": {
                    "USER_INPUT": request.message,
                },
                "additional_messages": [
                    {
                        "content": request.message,
                        "content_type": "text",
                        "role": "user",
                        "type": "question"
                    }
                ]
            }

            # 【关键2】如果有 conversation_id,添加到 payload
            if conversation_id:
                payload["conversation_id"] = conversation_id
                print(f"💬 流式接口使用 Conversation: {conversation_id}")

            # 如果有额外参数，合并到 parameters
            if request.parameters:
                payload["parameters"].update(request.parameters)

            print(f"📤 流式请求 - Session: {session_id}")

            # 发送请求（使用流式接收）
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            http_client = httpx.Client(timeout=HTTP_TIMEOUT, trust_env=False)

            with http_client.stream('POST', url, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    error_text = response.text
                    error_data = {
                        "type": "error",
                        "content": f"Coze API 错误: {error_text}"
                    }
                    yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                    return

                # 处理 SSE 流
                event_type = None
                returned_conversation_id = None
                full_ai_response = []  # 【P0-3】收集完整AI响应用于监管检查

                for line in response.iter_lines():
                    # 【P0-5】检查队列中的人工消息，优先推送
                    try:
                        while not sse_queues[session_id].empty():
                            queued_msg = await sse_queues[session_id].get()
                            yield f"data: {json.dumps(queued_msg, ensure_ascii=False)}\n\n"
                            print(f"✅ SSE 推送队列消息: {queued_msg.get('type')}")
                    except Exception as queue_error:
                        print(f"⚠️  SSE 队列检查异常: {str(queue_error)}")

                    if not line:
                        continue

                    line = line.strip()
                    if line.startswith('event:'):
                        event_type = line[6:].strip()
                    elif line.startswith('data:'):
                        try:
                            data_str = line[5:].strip()
                            data = json.loads(data_str)

                            # 提取 conversation_id (如果存在)
                            if 'conversation_id' in data and not returned_conversation_id:
                                returned_conversation_id = data['conversation_id']

                            # 处理消息增量事件 - 实时推送
                            if event_type == 'conversation.message.delta':
                                if 'content' in data and data.get('role') == 'assistant':
                                    content = data['content']
                                    if content:
                                        full_ai_response.append(content)  # 【P0-3】收集内容
                                        sse_data = {
                                            "type": "message",
                                            "content": content
                                        }
                                        yield f"data: {json.dumps(sse_data, ensure_ascii=False)}\n\n"

                            # 处理错误事件
                            elif event_type == 'conversation.chat.failed':
                                error_content = data.get('last_error', {}).get('msg', '未知错误')
                                error_data = {
                                    "type": "error",
                                    "content": error_content
                                }
                                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                                return

                        except json.JSONDecodeError:
                            # 跳过非 JSON 数据
                            pass

            # 【关键3】如果是首次对话,保存自动生成的 conversation_id
            if not conversation_id and returned_conversation_id:
                conversation_cache[session_id] = returned_conversation_id
                print(f"✅ 流式接口保存新 conversation: {returned_conversation_id} (session: {session_id})")

            # 【P0-3 后置处理】更新会话状态和触发监管检查
            final_ai_message = "".join(full_ai_response)
            if session_store and regulator and final_ai_message:
                try:
                    # 获取会话状态
                    conversation_id_for_update = returned_conversation_id or conversation_id
                    session_state = await session_store.get_or_create(
                        session_name=session_id,
                        conversation_id=conversation_id_for_update
                    )

                    # 添加用户消息到历史
                    user_message = Message(
                        role="user",
                        content=request.message
                    )
                    session_state.add_message(user_message)

                    # 添加AI响应到历史
                    ai_message = Message(
                        role="assistant",
                        content=final_ai_message
                    )
                    session_state.add_message(ai_message)

                    # 触发监管引擎评估
                    regulator_result = regulator.evaluate(
                        session=session_state,
                        user_message=request.message,
                        ai_response=final_ai_message
                    )

                    # 如果需要升级到人工
                    if regulator_result.should_escalate:
                        print(f"🚨 流式接口触发人工接管: {regulator_result.reason} - {regulator_result.details}")

                        # 更新升级信息
                        session_state.escalation = EscalationInfo(
                            reason=regulator_result.reason,
                            details=regulator_result.details,
                            severity=regulator_result.severity
                        )

                        # 状态转换为 pending_manual
                        session_state.transition_status(
                            new_status=SessionStatus.PENDING_MANUAL
                        )

                        # 记录日志
                        print(json.dumps({
                            "event": "escalation_triggered",
                            "session_name": session_id,
                            "reason": regulator_result.reason,
                            "severity": regulator_result.severity,
                            "timestamp": int(time.time())
                        }, ensure_ascii=False))

                    # 保存会话状态
                    await session_store.save(session_state)

                except Exception as regulator_error:
                    # ⚠️ 监管逻辑失败不应影响核心对话功能
                    print(f"⚠️  流式监管处理异常（不影响对话）: {str(regulator_error)}")
                    import traceback
                    traceback.print_exc()

            # 发送完成事件
            yield f"data: {json.dumps({'type': 'done', 'content': ''}, ensure_ascii=False)}\n\n"

        except Exception as e:
            error_msg = str(e)
            print(f"❌ 流式聊天错误: {error_msg}")

            # 发送错误事件
            error_data = {
                "type": "error",
                "content": f"服务器错误: {error_msg}"
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/api/bot/info")
async def get_bot_info():
    """获取客服配置信息(头像、昵称等)"""
    try:
        # 从环境变量读取配置
        bot_name = os.getenv("COZE_BOT_NAME", "Fiido 客服")
        # 使用本地头像文件
        bot_icon_url = os.getenv("COZE_BOT_ICON_URL", "http://localhost:8000/fiido2.png")
        bot_description = os.getenv("COZE_BOT_DESCRIPTION", "Fiido 智能客服助手")
        bot_welcome = os.getenv("COZE_BOT_WELCOME", "您好！我是Fiido智能客服助手,很高兴为您服务。请问有什么可以帮助您的？")

        bot_info = {
            "name": bot_name,
            "description": bot_description,
            "icon_url": bot_icon_url,
            "welcome": bot_welcome,
            "workflow_id": WORKFLOW_ID
        }

        print(f"📋 返回客服配置: 名称={bot_name}, 头像={'有' if bot_icon_url else '无'}")

        return {
            "success": True,
            "bot": bot_info
        }

    except Exception as e:
        print(f"❌ 客服信息接口错误: {str(e)}")
        return {
            "success": True,
            "bot": {
                "name": "Fiido 客服",
                "description": "Fiido 智能客服助手",
                "icon_url": "http://localhost:8000/fiido2.png",
                "welcome": "您好！有什么可以帮助您的？"
            }
        }


@app.get("/fiido2.png")
async def get_fiido_icon():
    """返回 fiido2.png 头像文件"""
    from fastapi.responses import FileResponse
    icon_path = os.path.join(CURRENT_DIR, "fiido2.png")
    if os.path.exists(icon_path):
        return FileResponse(icon_path, media_type="image/png")
    else:
        raise HTTPException(status_code=404, detail="Icon not found")


# ==================== P0-4: 核心人工接管 API ====================

@app.post("/api/manual/escalate")
async def manual_escalate(request: dict):
    """
    人工升级接口
    用户点击"人工客服"或监管触发后调用

    Body: { "session_name": "session_123", "reason": "user_request" }
    """
    if not session_store or not regulator:
        raise HTTPException(status_code=503, detail="SessionStore or Regulator not initialized")

    session_name = request.get("session_name")
    reason = request.get("reason", "user_request")

    if not session_name:
        raise HTTPException(status_code=400, detail="session_name is required")

    try:
        # 获取或创建会话状态
        session_state = await session_store.get_or_create(
            session_name=session_name,
            conversation_id=conversation_cache.get(session_name)
        )

        # 检查是否已在人工接管中
        if session_state.status == SessionStatus.MANUAL_LIVE:
            raise HTTPException(status_code=409, detail="MANUAL_IN_PROGRESS")

        # 更新升级信息
        # 将 user_request 映射到正确的枚举值 "manual"
        escalation_reason = "manual" if reason == "user_request" else reason

        # P1-邮件: 检查工作时间
        in_shift = is_in_shift()
        email_sent = False

        if not in_shift:
            # 非工作时间：只发邮件，不触发状态转换
            # 创建临时会话状态用于邮件内容
            session_state.escalation = EscalationInfo(
                reason=escalation_reason,
                details=f"用户主动请求人工服务" if reason == "user_request" else f"触发原因: {reason}",
                severity="high" if reason == "user_request" else "low"
            )

            try:
                email_result = send_escalation_email(session_state)
                email_sent = email_result.get('success', False)
                if email_sent:
                    print(f"📧 非工作时间，已发送邮件通知: {session_name}")
                else:
                    print(f"⚠️  邮件发送失败: {email_result.get('error')}")
            except Exception as email_error:
                print(f"⚠️  邮件发送异常: {str(email_error)}")

            # 记录日志
            print(json.dumps({
                "event": "after_hours_escalate",
                "session_name": session_name,
                "reason": reason,
                "email_sent": email_sent,
                "timestamp": int(time.time())
            }, ensure_ascii=False))

            # 返回但不改变状态，AI继续服务
            return {
                "success": True,
                "data": session_state.model_dump(),
                "email_sent": email_sent,
                "is_in_shift": False
            }

        # 工作时间：正常触发人工接管
        session_state.escalation = EscalationInfo(
            reason=escalation_reason,
            details=f"用户主动请求人工服务" if reason == "user_request" else f"触发原因: {reason}",
            severity="high" if reason == "user_request" else "low"
        )

        # 状态转换为 pending_manual
        session_state.transition_status(
            new_status=SessionStatus.PENDING_MANUAL
        )

        # 保存会话状态
        await session_store.save(session_state)

        # 记录日志
        print(json.dumps({
            "event": "manual_escalate",
            "session_name": session_name,
            "reason": reason,
            "status": session_state.status,
            "timestamp": int(time.time())
        }, ensure_ascii=False))

        # P0-5: 推送状态变化事件到 SSE
        if session_name in sse_queues:
            await sse_queues[session_name].put({
                "type": "status_change",
                "status": session_state.status,
                "reason": reason,
                "timestamp": int(time.time())
            })
            print(f"✅ SSE 推送状态变化: {session_state.status}")

        return {
            "success": True,
            "data": session_state.model_dump(),
            "email_sent": email_sent,
            "is_in_shift": is_in_shift()
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 人工升级失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"升级失败: {str(e)}")


# ==================== v2.5 新增：统计指标计算辅助函数 ====================

async def _calculate_ai_quality_metrics() -> dict:
    """
    计算 AI 质量指标（v2.5 新增）

    Returns:
        dict: {
            "avg_response_time_ms": 平均响应时长（毫秒）,
            "success_rate": AI 成功处理率,
            "escalation_rate": 人工升级率,
            "avg_messages_before_escalation": 升级前平均对话轮次
        }
    """
    if not session_store:
        return {
            "avg_response_time_ms": 0,
            "success_rate": 0.0,
            "escalation_rate": 0.0,
            "avg_messages_before_escalation": 0.0
        }

    try:
        # 获取所有会话（限制 1000 条以避免性能问题）
        all_sessions = await session_store.list_all(limit=1000)

        if not all_sessions:
            return {
                "avg_response_time_ms": 0,
                "success_rate": 0.0,
                "escalation_rate": 0.0,
                "avg_messages_before_escalation": 0.0
            }

        total_sessions = len(all_sessions)
        escalated_sessions = [s for s in all_sessions if s.escalation]
        escalation_count = len(escalated_sessions)

        # 计算升级率
        escalation_rate = escalation_count / total_sessions if total_sessions > 0 else 0.0
        success_rate = 1.0 - escalation_rate

        # 计算升级前平均对话轮次
        if escalated_sessions:
            messages_before_escalation = []
            for session in escalated_sessions:
                if session.escalation:
                    # 统计升级前的消息数量
                    escalation_time = session.escalation.trigger_at
                    pre_escalation_msgs = [
                        msg for msg in session.history
                        if msg.timestamp < escalation_time
                    ]
                    messages_before_escalation.append(len(pre_escalation_msgs))

            avg_messages = sum(messages_before_escalation) / len(messages_before_escalation) if messages_before_escalation else 0.0
        else:
            avg_messages = 0.0

        # 计算 AI 平均响应时长（简化版：基于历史消息的时间间隔）
        response_times = []
        for session in all_sessions:
            for i in range(len(session.history) - 1):
                if session.history[i].role == "user" and session.history[i + 1].role == "assistant":
                    response_time_sec = session.history[i + 1].timestamp - session.history[i].timestamp
                    response_times.append(response_time_sec * 1000)  # 转为毫秒

        avg_response_time_ms = sum(response_times) / len(response_times) if response_times else 0.0

        return {
            "avg_response_time_ms": round(avg_response_time_ms, 2),
            "success_rate": round(success_rate, 3),
            "escalation_rate": round(escalation_rate, 3),
            "avg_messages_before_escalation": round(avg_messages, 2)
        }

    except Exception as e:
        print(f"⚠️  计算 AI 质量指标失败: {e}")
        return {
            "avg_response_time_ms": 0,
            "success_rate": 0.0,
            "escalation_rate": 0.0,
            "avg_messages_before_escalation": 0.0
        }


async def _calculate_agent_efficiency_metrics() -> dict:
    """
    计算坐席效率指标（v2.5 新增）

    Returns:
        dict: {
            "avg_takeover_time_sec": 平均接入时长（秒）,
            "avg_service_time_sec": 平均服务时长（秒）,
            "resolution_rate": 一次解决率,
            "avg_sessions_per_agent": 每个坐席平均会话数
        }
    """
    if not session_store:
        return {
            "avg_takeover_time_sec": 0,
            "avg_service_time_sec": 0,
            "resolution_rate": 0.0,
            "avg_sessions_per_agent": 0.0
        }

    try:
        # 获取所有人工服务中和已完成的会话
        live_sessions = await session_store.list_by_status(SessionStatus.MANUAL_LIVE, limit=1000)
        closed_sessions = await session_store.list_by_status(SessionStatus.CLOSED, limit=1000)

        all_manual_sessions = live_sessions + [
            s for s in closed_sessions
            if s.last_manual_end_at is not None  # 曾经经过人工服务
        ]

        if not all_manual_sessions:
            return {
                "avg_takeover_time_sec": 0,
                "avg_service_time_sec": 0,
                "resolution_rate": 0.0,
                "avg_sessions_per_agent": 0.0
            }

        # 计算平均接入时长（pending_manual → manual_live）
        takeover_times = []
        for session in all_manual_sessions:
            if session.escalation and session.assigned_agent:
                # 简化计算：假设接入时间 = 当前时间或结束时间 - 升级时间
                if session.status == SessionStatus.MANUAL_LIVE:
                    takeover_time = time.time() - session.escalation.trigger_at
                elif session.last_manual_end_at:
                    takeover_time = session.last_manual_end_at - session.escalation.trigger_at
                else:
                    continue

                # 接入时长应该是升级到坐席接入的时间，这里简化处理
                # 实际应该记录坐席接入时间戳
                takeover_times.append(min(takeover_time, 3600))  # 限制最大 1 小时

        avg_takeover_time = sum(takeover_times) / len(takeover_times) if takeover_times else 0.0

        # 计算平均服务时长
        service_times = []
        current_time = time.time()
        for session in live_sessions:
            if session.escalation:
                service_time = current_time - session.escalation.trigger_at
                service_times.append(service_time)

        for session in closed_sessions:
            if session.last_manual_end_at and session.escalation:
                service_time = session.last_manual_end_at - session.escalation.trigger_at
                service_times.append(service_time)

        avg_service_time = sum(service_times) / len(service_times) if service_times else 0.0

        # 计算一次解决率（简化版：未再次升级的比例）
        # 实际应该根据工单系统判断问题是否解决
        resolved_sessions = len([
            s for s in closed_sessions
            if s.last_manual_end_at and s.ai_fail_count == 0
        ])
        resolution_rate = resolved_sessions / len(all_manual_sessions) if all_manual_sessions else 0.0

        # 计算每个坐席平均会话数
        agent_session_counts = {}
        for session in all_manual_sessions:
            if session.assigned_agent:
                agent_id = session.assigned_agent.id
                agent_session_counts[agent_id] = agent_session_counts.get(agent_id, 0) + 1

        avg_sessions_per_agent = (
            sum(agent_session_counts.values()) / len(agent_session_counts)
            if agent_session_counts else 0.0
        )

        return {
            "avg_takeover_time_sec": round(avg_takeover_time, 2),
            "avg_service_time_sec": round(avg_service_time, 2),
            "resolution_rate": round(resolution_rate, 3),
            "avg_sessions_per_agent": round(avg_sessions_per_agent, 2)
        }

    except Exception as e:
        print(f"⚠️  计算坐席效率指标失败: {e}")
        return {
            "avg_takeover_time_sec": 0,
            "avg_service_time_sec": 0,
            "resolution_rate": 0.0,
            "avg_sessions_per_agent": 0.0
        }


@app.get("/api/sessions/stats")
async def get_sessions_stats():
    """获取会话统计信息（增强版）"""
    if not session_store:
        raise HTTPException(status_code=503, detail="SessionStore not initialized")

    try:
        stats = await session_store.get_stats()

        # 计算平均等待时间
        pending_sessions = await session_store.list_by_status(
            status=SessionStatus.PENDING_MANUAL,
            limit=100
        )

        current_time = time.time()

        if pending_sessions:
            waiting_times = [
                current_time - session.escalation.trigger_at
                for session in pending_sessions
                if session.escalation
            ]
            avg_waiting_time = sum(waiting_times) / len(waiting_times) if waiting_times else 0
            max_waiting_time = max(waiting_times) if waiting_times else 0
        else:
            avg_waiting_time = 0
            max_waiting_time = 0

        stats["avg_waiting_time"] = round(avg_waiting_time, 2)
        stats["max_waiting_time"] = round(max_waiting_time, 2)

        # 获取正在服务中的会话，计算服务时长
        live_sessions = await session_store.list_by_status(
            status=SessionStatus.MANUAL_LIVE,
            limit=100
        )

        if live_sessions:
            service_times = [
                current_time - (session.escalation.trigger_at if session.escalation else session.updated_at)
                for session in live_sessions
            ]
            avg_service_time = sum(service_times) / len(service_times) if service_times else 0
        else:
            avg_service_time = 0

        stats["avg_service_time"] = round(avg_service_time, 2)
        stats["active_agents"] = len(set(
            session.assigned_agent.id
            for session in live_sessions
            if session.assigned_agent
        ))

        # 按升级原因统计
        all_pending = await session_store.list_by_status(
            status=SessionStatus.PENDING_MANUAL,
            limit=1000
        )
        all_live = await session_store.list_by_status(
            status=SessionStatus.MANUAL_LIVE,
            limit=1000
        )

        escalation_reasons = {}
        for session in (all_pending + all_live):
            if session.escalation:
                reason = session.escalation.reason
                escalation_reasons[reason] = escalation_reasons.get(reason, 0) + 1

        stats["by_escalation_reason"] = escalation_reasons

        # 今日统计（简化版，实际应该从持久化存储获取）
        today_stats = {
            "total_escalations": len(all_pending) + len(all_live),
            "pending": len(all_pending),
            "serving": len(all_live)
        }
        stats["today"] = today_stats

        # ⭐ v2.5 新增: AI 质量指标
        ai_quality = await _calculate_ai_quality_metrics()
        stats["ai_quality"] = ai_quality

        # ⭐ v2.5 新增: 坐席效率指标
        agent_efficiency = await _calculate_agent_efficiency_metrics()
        stats["agent_efficiency"] = agent_efficiency

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        print(f"❌ 获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# ==================== 模块2: 队列管理 API ====================

@app.get("/api/sessions/queue")
async def get_sessions_queue():
    """
    获取等待队列信息（模块2）

    功能:
    - 获取所有 pending_manual 状态的会话
    - 按优先级排序（VIP > 等待时长 > 默认）
    - 返回队列统计信息

    Returns:
        queue: 队列中的会话列表（按优先级排序）
        total_count: 总队列数量
        vip_count: VIP客户数量
        avg_wait_time: 平均等待时长（秒）
    """
    if not session_store:
        raise HTTPException(status_code=503, detail="SessionStore not initialized")

    try:
        # 获取所有等待接入的会话
        pending_sessions = await session_store.list_by_status(
            status=SessionStatus.PENDING_MANUAL,
            limit=100  # 限制最多100个排队会话
        )

        if not pending_sessions:
            return {
                "success": True,
                "data": {
                    "queue": [],
                    "total_count": 0,
                    "vip_count": 0,
                    "avg_wait_time": 0,
                    "max_wait_time": 0
                }
            }

        # 紧急关键词列表（配置化）
        urgent_keywords = ["投诉", "退款", "质量问题", "差评", "赔偿"]

        # 更新每个会话的优先级信息
        current_time = time.time()
        for session in pending_sessions:
            session.update_priority(urgent_keywords=urgent_keywords)

        # 按优先级排序
        # 规则:
        # 1. VIP客户永远最优先（is_vip=True）
        # 2. 同级别内按等待时长降序
        # 3. urgent > high > normal
        def priority_sort_key(s):
            priority_weight = {
                "urgent": 3,
                "high": 2,
                "normal": 1
            }.get(s.priority.level, 1)

            # VIP客户排第一（vip_priority=1），非VIP=0
            vip_priority = 1 if s.priority.is_vip else 0

            # 返回: (VIP优先倒序, 优先级权重倒序, 等待时长倒序)
            return (-vip_priority, -priority_weight, -s.priority.wait_time_seconds)

        sorted_sessions = sorted(pending_sessions, key=priority_sort_key)

        # 构建队列数据
        queue_data = []
        vip_count = 0
        total_wait_time = 0

        for position, session in enumerate(sorted_sessions, start=1):
            is_vip = session.user_profile.vip if session.user_profile else False
            if is_vip:
                vip_count += 1

            wait_time = session.priority.wait_time_seconds
            total_wait_time += wait_time

            queue_data.append({
                "session_name": session.session_name,
                "position": position,
                "priority_level": session.priority.level,
                "is_vip": is_vip,
                "wait_time_seconds": round(wait_time, 1),
                "is_timeout": session.priority.is_timeout,
                "urgent_keywords": session.priority.urgent_keywords,
                "user_profile": {
                    "nickname": session.user_profile.nickname if session.user_profile else "访客",
                    "vip": is_vip
                },
                "last_message": session.history[-1].content[:50] if session.history else ""
            })

        avg_wait_time = total_wait_time / len(sorted_sessions) if sorted_sessions else 0
        max_wait_time = max([s.priority.wait_time_seconds for s in sorted_sessions]) if sorted_sessions else 0

        return {
            "success": True,
            "data": {
                "queue": queue_data,
                "total_count": len(sorted_sessions),
                "vip_count": vip_count,
                "avg_wait_time": round(avg_wait_time, 1),
                "max_wait_time": round(max_wait_time, 1)
            }
        }

    except Exception as e:
        print(f"❌ 获取队列信息失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取队列失败: {str(e)}")


@app.get("/api/sessions/{session_name}")
async def get_session_state(session_name: str):
    """
    获取会话状态
    前端刷新会话历史 & 状态
    """
    if not session_store:
        raise HTTPException(status_code=503, detail="SessionStore not initialized")

    try:
        # 获取会话状态
        session_state = await session_store.get(session_name)

        if not session_state:
            raise HTTPException(status_code=404, detail="Session not found")

        # 获取审计日志（如果实现了）
        audit_trail = []  # TODO: 从独立存储获取

        return {
            "success": True,
            "data": {
                "session": session_state.model_dump(),
                "audit_trail": audit_trail
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取会话状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@app.post("/api/manual/messages")
async def manual_message(request: dict):
    """
    人工阶段消息写入
    用于用户/坐席在人工接管期间的消息

    Body: {
        "session_name": "session_123",
        "role": "agent" | "user",
        "content": "我要人工"
    }
    """
    if not session_store:
        raise HTTPException(status_code=503, detail="SessionStore not initialized")

    session_name = request.get("session_name")
    role = request.get("role")
    content = request.get("content")

    if not all([session_name, role, content]):
        raise HTTPException(status_code=400, detail="session_name, role, and content are required")

    if role not in ["agent", "user"]:
        raise HTTPException(status_code=400, detail="role must be 'agent' or 'user'")

    try:
        # 获取会话状态
        session_state = await session_store.get(session_name)

        if not session_state:
            raise HTTPException(status_code=404, detail="Session not found")

        # 如果是用户消息，必须在manual_live状态
        if role == "user" and session_state.status != SessionStatus.MANUAL_LIVE:
            raise HTTPException(status_code=409, detail="Session not in manual_live status")

        # 创建消息
        agent_info = request.get("agent_info", {})
        message = Message(
            role=role,
            content=content,
            agent_id=agent_info.get("agent_id") if agent_info else None,
            agent_name=agent_info.get("agent_name") if agent_info else None
        )

        # 添加到历史
        session_state.add_message(message)

        # 保存会话状态
        await session_store.save(session_state)

        # 记录日志
        print(json.dumps({
            "event": "manual_message",
            "session_name": session_name,
            "role": role,
            "timestamp": message.timestamp
        }, ensure_ascii=False))

        # P0-5: 通过 SSE 推送消息到客户端
        if session_name in sse_queues:
            await sse_queues[session_name].put({
                "type": "manual_message",
                "role": role,
                "content": content,
                "timestamp": message.timestamp,
                "agent_id": message.agent_id,
                "agent_name": message.agent_name
            })
            print(f"✅ SSE 推送人工消息到队列: {session_name}, role={role}")

        return {
            "success": True,
            "data": {
                "timestamp": message.timestamp
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 写入人工消息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"写入失败: {str(e)}")


@app.post("/api/sessions/{session_name}/release")
async def release_session(session_name: str, request: dict):
    """
    结束人工接管，恢复AI

    Body: { "agent_id": "agent_01", "reason": "resolved" }
    """
    if not session_store:
        raise HTTPException(status_code=503, detail="SessionStore not initialized")

    agent_id = request.get("agent_id")
    reason = request.get("reason", "resolved")

    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required")

    try:
        # 获取会话状态
        session_state = await session_store.get(session_name)

        if not session_state:
            raise HTTPException(status_code=404, detail="Session not found")

        # 必须在manual_live状态才能释放
        if session_state.status != SessionStatus.MANUAL_LIVE:
            raise HTTPException(status_code=409, detail="Session not in manual_live status")

        manual_start_at = session_state.manual_start_at

        # 添加系统消息
        system_message = Message(
            role="system",
            content="人工服务已结束，AI 助手已接管对话"
        )
        session_state.add_message(system_message)

        # 记录结束时间
        session_state.last_manual_end_at = time.time()

        # 状态转换为 bot_active
        session_state.transition_status(
            new_status=SessionStatus.BOT_ACTIVE
        )

        # 清除坐席信息
        session_state.assigned_agent = None
        session_state.manual_start_at = None

        # 保存会话状态
        await session_store.save(session_state)

        # 记录日志
        print(json.dumps({
            "event": "session_released",
            "session_name": session_name,
            "agent_id": agent_id,
            "reason": reason,
            "timestamp": int(time.time())
        }, ensure_ascii=False))

        # P0-5: 推送状态变化和系统消息到 SSE
        if session_name in sse_queues:
            # 推送系统消息
            await sse_queues[session_name].put({
                "type": "manual_message",
                "role": "system",
                "content": "人工服务已结束，AI 助手已接管对话",
                "timestamp": system_message.timestamp
            })
            # 推送状态变化
            await sse_queues[session_name].put({
                "type": "status_change",
                "status": session_state.status,
                "reason": "released",
                "timestamp": int(time.time())
            })
            print(f"✅ SSE 推送会话释放事件: {session_name}")

        # 记录坐席工作统计
        if manual_start_at:
            service_duration = max(0.0, time.time() - manual_start_at)
            _record_agent_session_duration(agent_id, service_duration)

        if agent_manager:
            agent_manager.update_last_active(agent_id)

        return {
            "success": True,
            "data": session_state.model_dump()
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 释放会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"释放失败: {str(e)}")


@app.post("/api/sessions/{session_name}/takeover")
async def takeover_session(
    session_name: str,
    takeover_request: dict
):
    """
    坐席接入会话（防抢单）

    Body:
    {
        "agent_id": "agent_001",
        "agent_name": "小王"
    }
    """
    if not session_store:
        raise HTTPException(status_code=503, detail="SessionStore not initialized")

    agent_id = takeover_request.get("agent_id")
    agent_name = takeover_request.get("agent_name")

    if not all([agent_id, agent_name]):
        raise HTTPException(
            status_code=400,
            detail="agent_id and agent_name are required"
        )

    try:
        takeover_started_at = time.time()
        # 🔴 P0-2.1: 获取会话状态
        session_state = await session_store.get(session_name)

        if not session_state:
            raise HTTPException(status_code=404, detail="Session not found")

        # 🔴 P0-2.2: 检查状态是否为pending_manual
        if session_state.status != SessionStatus.PENDING_MANUAL:
            if session_state.status == SessionStatus.MANUAL_LIVE:
                # 已被其他坐席接入
                assigned_agent_name = session_state.assigned_agent.name if session_state.assigned_agent else "未知"
                raise HTTPException(
                    status_code=409,
                    detail=f"ALREADY_TAKEN: 会话已被坐席【{assigned_agent_name}】接入"
                )
            else:
                raise HTTPException(
                    status_code=409,
                    detail=f"INVALID_STATUS: 当前状态为{session_state.status}，无法接入"
                )

        # 🔴 P0-2.3: 分配坐席
        from src.session_state import AgentInfo
        session_state.assigned_agent = AgentInfo(
            id=agent_id,
            name=agent_name
        )

        # 🔴 P0-2.4: 状态转换为manual_live
        success = session_state.transition_status(
            new_status=SessionStatus.MANUAL_LIVE
        )

        if not success:
            raise HTTPException(
                status_code=500,
                detail="状态转换失败"
            )

        # 记录人工服务开始时间
        session_state.manual_start_at = takeover_started_at

        # 🔴 P0-2.5: 添加系统消息
        system_message = Message(
            role="system",
            content=f"客服【{agent_name}】已接入，正在为您服务"
        )
        session_state.add_message(system_message)

        # 🔴 P0-2.6: 保存会话状态
        await session_store.save(session_state)

        # 🔴 P0-2.7: 记录日志
        print(json.dumps({
            "event": "agent_takeover",
            "session_name": session_name,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "timestamp": int(time.time())
        }, ensure_ascii=False))

        # 🔴 P0-2.8: 推送SSE事件
        if session_name in sse_queues:
            # 推送状态变化
            await sse_queues[session_name].put({
                "type": "status_change",
                "status": "manual_live",
                "agent_info": {
                    "agent_id": agent_id,
                    "agent_name": agent_name
                },
                "timestamp": int(time.time())
            })

            # 推送系统消息
            await sse_queues[session_name].put({
                "type": "manual_message",
                "role": "system",
                "content": f"客服【{agent_name}】已接入，正在为您服务",
                "timestamp": system_message.timestamp
            })

            print(f"✅ SSE 推送坐席接入事件: {session_name}")

        # 更新坐席统计信息
        if session_state.escalation:
            response_time = max(0.0, takeover_started_at - session_state.escalation.trigger_at)
            _record_agent_response_time(agent_id, response_time)

        if agent_manager:
            agent_manager.update_last_active(agent_id)

        return {
            "success": True,
            "data": session_state.model_dump()
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 接入会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"接入失败: {str(e)}")


@app.post("/api/sessions/{session_name}/transfer")
async def transfer_session(
    session_name: str,
    transfer_request: dict
):
    """
    会话转接（坐席间转接）

    Body:
    {
        "from_agent_id": "agent_001",
        "to_agent_id": "agent_002",
        "to_agent_name": "小李",
        "reason": "专业问题需转接技术支持"
    }
    """
    if not session_store:
        raise HTTPException(status_code=503, detail="SessionStore not initialized")

    from_agent_id = transfer_request.get("from_agent_id")
    to_agent_id = transfer_request.get("to_agent_id")
    to_agent_name = transfer_request.get("to_agent_name")
    reason = transfer_request.get("reason", "坐席转接")
    note = transfer_request.get("note", "")  # ⭐ 新增：转接备注

    if not all([from_agent_id, to_agent_id, to_agent_name]):
        raise HTTPException(
            status_code=400,
            detail="from_agent_id, to_agent_id, and to_agent_name are required"
        )

    if not reason or reason.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="REASON_REQUIRED: 转接原因不能为空"
        )

    try:
        # 获取会话状态
        session_state = await session_store.get(session_name)

        if not session_state:
            raise HTTPException(status_code=404, detail="Session not found")

        # 必须在 manual_live 状态才能转接
        if session_state.status != SessionStatus.MANUAL_LIVE:
            raise HTTPException(
                status_code=409,
                detail=f"INVALID_STATUS: 当前状态为{session_state.status}，无法转接"
            )

        # 验证当前坐席是否匹配
        if session_state.assigned_agent and session_state.assigned_agent.id != from_agent_id:
            raise HTTPException(
                status_code=403,
                detail="只有当前服务的坐席才能转接会话"
            )

        from src.session_state import AgentInfo  # noqa: F401  # 保留以兼容后续处理
        old_agent_name = session_state.assigned_agent.name if session_state.assigned_agent else "未知"

        # 创建待确认的转接请求
        request_id = f"transfer_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        created_at = time.time()
        pending_request = {
            "id": request_id,
            "session_name": session_name,
            "from_agent_id": from_agent_id,
            "from_agent_name": old_agent_name,
            "to_agent_id": to_agent_id,
            "to_agent_name": to_agent_name,
            "reason": reason,
            "note": note,
            "status": "pending",
            "created_at": created_at
        }

        pending_transfer_requests.setdefault(to_agent_id, []).append(pending_request)

        # 记录日志
        print(json.dumps({
            "event": "transfer_requested",
            "session_name": session_name,
            "from_agent": from_agent_id,
            "to_agent": to_agent_id,
            "to_agent_name": to_agent_name,
            "reason": reason,
            "note": note,
            "timestamp": int(created_at)
        }, ensure_ascii=False))

        if agent_manager:
            agent_manager.update_last_active(from_agent_id)

        return {
            "success": True,
            "data": pending_request,
            "message": f"已向【{to_agent_name}】发送转接请求，等待对方确认"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 转接会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"转接失败: {str(e)}")


@app.get("/api/sessions")
async def get_sessions(
    status: Optional[str] = None,
    time_start: Optional[float] = None,  # Unix timestamp
    time_end: Optional[float] = None,    # Unix timestamp
    agent: Optional[str] = None,         # "all" / "mine" / "unassigned" / agent_id
    customer_type: Optional[str] = None, # "all" / "vip" / "old" / "new"
    keyword: Optional[str] = None,       # 搜索关键词
    sort: Optional[str] = "default",     # "default" / "newest" / "oldest" / "vip" / "waitTime"
    limit: int = 50,
    offset: int = 0
):
    """
    获取会话列表 (增强版 - 支持高级筛选和搜索)

    【模块1: 会话高级筛选与搜索】

    Query Parameters:
      - status: 会话状态过滤（pending_manual, manual_live等）
      - time_start: 开始时间（Unix时间戳）
      - time_end: 结束时间（Unix时间戳）
      - agent: 坐席筛选（all/mine/unassigned/agent_id）
      - customer_type: 客户类型（all/vip/old/new）
      - keyword: 搜索关键词（搜索昵称、会话ID、消息内容）
      - sort: 排序方式（default/newest/oldest/vip/waitTime）
      - limit: 每页数量（默认50）
      - offset: 偏移量（默认0）
    """
    if not session_store:
        raise HTTPException(status_code=503, detail="SessionStore not initialized")

    try:
        # 🔴 L1-1-Part1-F1: 获取所有会话或按状态筛选
        if status and status != 'all':
            try:
                status_enum = SessionStatus(status)
                sessions = await session_store.list_by_status(
                    status=status_enum,
                    limit=10000,  # 先获取所有，再内存筛选
                    offset=0
                )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status: {status}. Valid values: {[s.value for s in SessionStatus]}"
                )
        else:
            sessions = await session_store.list_all(limit=10000, offset=0)

        # 🔴 L1-1-Part1-F1-2: 时间范围筛选
        if time_start:
            sessions = [s for s in sessions if s.created_at >= time_start]
        if time_end:
            sessions = [s for s in sessions if s.created_at <= time_end]

        # 🔴 L1-1-Part1-F1-3: 坐席筛选
        if agent and agent != 'all':
            if agent == 'unassigned':
                # 显示 pending_manual 状态的会话
                sessions = [s for s in sessions if s.status == SessionStatus.PENDING_MANUAL]
            elif agent == 'mine':
                # TODO: 需要从JWT token中获取当前坐席ID
                # 暂时跳过，需要权限中间件支持
                pass
            else:
                # 指定坐席
                sessions = [s for s in sessions if s.assigned_agent and s.assigned_agent.get('id') == agent]

        # 🔴 L1-1-Part1-F1-4: 客户类型筛选
        if customer_type and customer_type != 'all':
            if customer_type == 'vip':
                sessions = [s for s in sessions if s.user_profile and s.user_profile.vip]
            elif customer_type == 'old':
                # 老客户：有订单历史（暂时用 metadata 中的 order_count 判断）
                sessions = [s for s in sessions if s.user_profile and s.user_profile.metadata.get('order_count', 0) > 0]
            elif customer_type == 'new':
                # 新客户：无订单历史
                sessions = [s for s in sessions if not s.user_profile or s.user_profile.metadata.get('order_count', 0) == 0]

        # 🔴 L1-1-Part1-F1-5: 关键词搜索
        if keyword:
            keyword_lower = keyword.lower().strip()
            filtered_sessions = []
            for session in sessions:
                # 搜索会话ID
                if keyword_lower in session.session_name.lower():
                    filtered_sessions.append(session)
                    continue
                # 搜索客户昵称
                if session.user_profile and session.user_profile.nickname:
                    if keyword_lower in session.user_profile.nickname.lower():
                        filtered_sessions.append(session)
                        continue
                # 搜索对话历史内容
                if session.history:
                    for msg in session.history:
                        if keyword_lower in msg.content.lower():
                            filtered_sessions.append(session)
                            break
                    else:
                        # 如果内层循环正常结束(没有break),继续外层循环
                        continue
                    # 如果内层循环被break,说明找到了匹配,继续外层下一个session
                    continue
                # 搜索坐席名称
                if session.assigned_agent and session.assigned_agent.name:
                    if keyword_lower in session.assigned_agent.name.lower():
                        filtered_sessions.append(session)
                        continue
            sessions = filtered_sessions

        # 🔴 L1-1-Part1-F1-7: 智能排序
        if sort == 'newest':
            # 最新优先
            sessions.sort(key=lambda s: s.updated_at, reverse=True)
        elif sort == 'oldest':
            # 最早优先
            sessions.sort(key=lambda s: s.updated_at, reverse=False)
        elif sort == 'vip':
            # VIP优先，同级按时间
            def vip_sort_key(s):
                is_vip = s.user_profile.vip if s.user_profile else False
                return (not is_vip, -s.updated_at)  # VIP在前，时间倒序
            sessions.sort(key=vip_sort_key)
        elif sort == 'waitTime':
            # 等待时长优先
            current_time = time.time()
            sessions.sort(key=lambda s: -(current_time - s.created_at))
        else:
            # 默认排序：优先级 > 更新时间
            def default_sort_key(s):
                is_vip = s.user_profile.vip if s.user_profile else False
                # 状态权重
                status_weight = {
                    SessionStatus.PENDING_MANUAL: 3,
                    SessionStatus.MANUAL_LIVE: 2,
                    SessionStatus.BOT_ACTIVE: 1,
                    SessionStatus.CLOSED: 0
                }.get(s.status, 1)
                return (not is_vip, -status_weight, -s.updated_at)
            sessions.sort(key=default_sort_key)

        # 🔴 分页处理
        total = len(sessions)
        paginated_sessions = sessions[offset:offset + limit]

        # 【模块2】更新优先级信息（在转换为摘要前）
        urgent_keywords = ["投诉", "退款", "质量问题", "差评", "赔偿"]
        for session in paginated_sessions:
            session.update_priority(urgent_keywords=urgent_keywords)

        # 🔴 转换为摘要格式
        sessions_summary = [session.to_summary() for session in paginated_sessions]

        return {
            "success": True,
            "data": {
                "sessions": sessions_summary,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + len(paginated_sessions)) < total
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取会话列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# ====================
# 坐席认证 API (Agent Authentication)
# ====================

@app.post("/api/agent/login")
async def agent_login(request: LoginRequest):
    """
    坐席登录接口

    功能:
    - 验证坐席用户名和密码
    - 生成访问 Token 和刷新 Token
    - 更新坐席登录状态

    Args:
        request: 登录请求（username, password）

    Returns:
        LoginResponse: 包含 token, refresh_token, expires_in, agent 信息

    Raises:
        401: 用户名或密码错误
        500: 服务器内部错误
    """
    try:
        if not agent_manager or not agent_token_manager:
            raise HTTPException(
                status_code=500,
                detail="坐席认证系统未初始化"
            )

        # 验证坐席账号
        agent = agent_manager.authenticate(
            username=request.username,
            password=request.password
        )

        if not agent:
            raise HTTPException(
                status_code=401,
                detail="用户名或密码错误"
            )

        # 生成 Token
        access_token = agent_token_manager.create_access_token(agent)
        refresh_token = agent_token_manager.create_refresh_token(agent)

        # 返回登录响应
        return LoginResponse(
            success=True,
            token=access_token,
            refresh_token=refresh_token,
            expires_in=3600,  # 1小时
            agent=agent_to_dict(agent)
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 坐席登录失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"登录失败: {str(e)}"
        )


@app.post("/api/agent/logout")
async def agent_logout(username: str):
    """
    坐席登出接口

    功能:
    - 更新坐席状态为离线

    Args:
        username: 坐席用户名

    Returns:
        success: bool
    """
    try:
        if not agent_manager:
            raise HTTPException(
                status_code=500,
                detail="坐席认证系统未初始化"
            )

        agent_manager.update_status(username, AgentStatus.OFFLINE)

        return {
            "success": True,
            "message": "登出成功"
        }

    except Exception as e:
        print(f"❌ 坐席登出失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"登出失败: {str(e)}"
        )


@app.get("/api/agent/profile")
async def get_agent_profile(username: str):
    """
    获取坐席信息接口

    功能:
    - 获取坐席的详细信息（不含密码）

    Args:
        username: 坐席用户名

    Returns:
        agent: 坐席信息字典

    Raises:
        404: 坐席不存在
        500: 服务器内部错误
    """
    try:
        if not agent_manager:
            raise HTTPException(
                status_code=500,
                detail="坐席认证系统未初始化"
            )

        agent = agent_manager.get_agent_by_username(username)

        if not agent:
            raise HTTPException(
                status_code=404,
                detail="坐席不存在"
            )

        return {
            "success": True,
            "agent": agent_to_dict(agent)
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取坐席信息失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取失败: {str(e)}"
        )


@app.get("/api/agent/status")
async def get_agent_status(agent: Dict[str, Any] = Depends(require_agent)):
    """获取坐席当前状态"""
    try:
        if not agent_manager:
            raise HTTPException(status_code=500, detail="坐席认证系统未初始化")

        username = agent.get("username")
        current_agent = agent_manager.get_agent_by_username(username)

        if not current_agent:
            raise HTTPException(status_code=404, detail="坐席不存在")

        current_agent = _auto_adjust_agent_status(current_agent)
        payload = await _build_agent_status_payload(current_agent, username)

        return {
            "success": True,
            "data": payload
        }
    except HTTPException:
        raise
    except Exception as exc:
        print(f"❌ 获取坐席状态失败: {exc}")
        raise HTTPException(status_code=500, detail="获取坐席状态失败")


@app.put("/api/agent/status")
async def update_agent_status_api(
    request: UpdateAgentStatusRequest,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """更新坐席状态"""
    try:
        if not agent_manager:
            raise HTTPException(status_code=500, detail="坐席认证系统未初始化")

        username = agent.get("username")
        updated_agent = agent_manager.update_status(
            username=username,
            status=request.status,
            status_note=request.status_note
        )

        if not updated_agent:
            raise HTTPException(status_code=404, detail="坐席不存在")

        payload = await _build_agent_status_payload(updated_agent, username)
        return {
            "success": True,
            "data": payload
        }
    except HTTPException:
        raise
    except Exception as exc:
        print(f"❌ 更新坐席状态失败: {exc}")
        raise HTTPException(status_code=500, detail="更新失败")


@app.post("/api/agent/status/heartbeat")
async def heartbeat_agent_status(agent: Dict[str, Any] = Depends(require_agent)):
    """更新坐席心跳，用于自动状态判断"""
    try:
        if not agent_manager:
            raise HTTPException(status_code=500, detail="坐席认证系统未初始化")

        username = agent.get("username")
        last_active = agent_manager.update_last_active(username)

        return {
            "success": True,
            "last_active_at": last_active
        }
    except HTTPException:
        raise
    except Exception as exc:
        print(f"❌ 坐席心跳上报失败: {exc}")
        raise HTTPException(status_code=500, detail="心跳上报失败")


@app.get("/api/agent/stats/today")
async def get_agent_today_stats(agent: Dict[str, Any] = Depends(require_agent)):
    """获取坐席今日统计"""
    try:
        if not agent_manager:
            raise HTTPException(status_code=500, detail="坐席认证系统未初始化")

        username = agent.get("username")
        today_stats = _compose_today_stats(username)
        current_sessions = await _count_agent_live_sessions(username)
        current_agent = agent_manager.get_agent_by_username(username)

        today_stats.update({
            "current_sessions": current_sessions,
            "max_sessions": current_agent.max_sessions if current_agent else 0
        })

        return {
            "success": True,
            "data": today_stats
        }
    except HTTPException:
        raise
    except Exception as exc:
        print(f"❌ 获取坐席统计失败: {exc}")
        raise HTTPException(status_code=500, detail="统计获取失败")


@app.post("/api/agent/refresh")
async def refresh_agent_token(request: RefreshTokenRequest):
    """
    刷新坐席 Token 接口

    功能:
    - 使用刷新 Token 生成新的访问 Token

    Args:
        request: 刷新 Token 请求

    Returns:
        token: 新的访问 Token
        expires_in: 过期时间（秒）

    Raises:
        401: 刷新 Token 无效或已过期
        500: 服务器内部错误
    """
    try:
        if not agent_manager or not agent_token_manager:
            raise HTTPException(
                status_code=500,
                detail="坐席认证系统未初始化"
            )

        # 验证刷新 Token
        payload = agent_token_manager.verify_token(request.refresh_token)

        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=401,
                detail="无效的刷新 Token"
            )

        # 获取坐席信息
        username = payload.get("username")
        agent = agent_manager.get_agent_by_username(username)

        if not agent:
            raise HTTPException(
                status_code=401,
                detail="坐席不存在"
            )

        # 生成新的访问 Token
        new_access_token = agent_token_manager.create_access_token(agent)

        return {
            "success": True,
            "token": new_access_token,
            "expires_in": 3600
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 刷新 Token 失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"刷新失败: {str(e)}"
        )


# ====================
# 管理员功能 API
# ====================

# 导入请求模型
from src.agent_auth import (
    CreateAgentRequest,
    UpdateAgentRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    UpdateProfileRequest,
    validate_password,
    PasswordHasher,
    AgentRole
)


@app.get("/api/agents")
async def get_agents_list(
    status: Optional[str] = None,
    role: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    admin: Dict[str, Any] = Depends(require_admin)  # ← 添加管理员权限验证
):
    """
    获取坐席列表 (需要管理员权限)

    Query Parameters:
        status: 过滤状态 (online/offline/busy)
        role: 过滤角色 (admin/agent)
        page: 页码，默认1
        page_size: 每页数量，默认20

    权限: 管理员

    Returns:
        items: 坐席列表
        total: 总数
        page: 当前页
        page_size: 每页数量
    """
    try:
        if not agent_manager:
            raise HTTPException(status_code=500, detail="坐席管理系统未初始化")

        # 获取所有坐席
        agents = agent_manager.get_all_agents()

        # 过滤
        if status:
            agents = [a for a in agents if a.status.value == status]
        if role:
            agents = [a for a in agents if a.role.value == role]

        # 排序（按创建时间倒序）
        agents.sort(key=lambda x: x.created_at, reverse=True)

        # 分页
        total = len(agents)
        start = (page - 1) * page_size
        end = start + page_size
        items = agents[start:end]

        # 转换为字典（隐藏密码）
        items_dict = []
        for agent in items:
            data = agent.dict()
            data.pop("password_hash", None)
            items_dict.append(data)

        return {
            "success": True,
            "data": {
                "items": items_dict,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取坐席列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取失败: {str(e)}"
        )


@app.get("/api/agents/available")
async def get_available_agents(
    agent: Dict[str, Any] = Depends(require_agent)
):
    """
    获取可转接的坐席列表 (需要坐席权限)

    用于会话转接功能，返回除当前登录坐席外的所有在线坐席

    Args:
        agent: 当前登录坐席信息

    Returns:
        items: 可转接的坐席列表（包含 id, name, status, current_sessions）
    """
    try:
        if not agent_manager:
            raise HTTPException(status_code=500, detail="坐席管理系统未初始化")

        # 获取所有坐席
        all_agents = agent_manager.get_all_agents()

        # 过滤：排除当前登录坐席，只返回在线状态的坐席
        current_agent_id = agent.get("agent_id")
        available = []

        for a in all_agents:
            # 只返回在线且非当前登录坐席
            if a.id != current_agent_id and a.status == AgentStatus.ONLINE:
                available.append({
                    "id": a.id,
                    "username": a.username,
                    "name": a.name,
                    "status": a.status.value,
                    "role": a.role.value,
                    "max_sessions": a.max_sessions
                })

        # 按状态排序：在线优先
        status_priority = {
            'online': 1,
            'busy': 2,
            'break': 3,
            'lunch': 4,
            'training': 5,
            'offline': 6
        }
        available.sort(key=lambda x: status_priority.get(x['status'], 99))

        return {
            "success": True,
            "data": {
                "items": available,
                "total": len(available)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取可转接坐席列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取失败: {str(e)}"
        )


@app.post("/api/agents")
async def create_agent(
    request: CreateAgentRequest,
    admin: Dict[str, Any] = Depends(require_admin)  # ← 添加管理员权限验证
):
    """
    创建坐席账号 (需要管理员权限)

    Args:
        request: 创建坐席请求

    权限: 管理员

    Returns:
        agent: 创建的坐席信息
    """
    try:
        if not agent_manager:
            raise HTTPException(status_code=500, detail="坐席管理系统未初始化")

        # 检查用户名是否已存在
        if agent_manager.get_agent_by_username(request.username):
            raise HTTPException(
                status_code=400,
                detail="USERNAME_EXISTS: 用户名已存在"
            )

        # 验证密码强度
        if not validate_password(request.password):
            raise HTTPException(
                status_code=400,
                detail="INVALID_PASSWORD: 密码必须至少8个字符，包含字母和数字"
            )

        # 创建坐席
        agent = agent_manager.create_agent(
            username=request.username,
            password=request.password,
            name=request.name,
            role=request.role,
            max_sessions=request.max_sessions
        )

        # 更新头像
        if request.avatar_url:
            agent.avatar_url = request.avatar_url
            agent_manager.update_agent(agent)

        # 返回结果（隐藏密码）
        agent_dict = agent.dict()
        agent_dict.pop("password_hash", None)

        print(f"✅ 创建坐席账号: {agent.username} (角色: {agent.role.value})")

        return {
            "success": True,
            "agent": agent_dict
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 创建坐席账号失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"创建失败: {str(e)}"
        )


@app.put("/api/agents/{username}")
async def update_agent(
    username: str,
    request: UpdateAgentRequest,
    admin: Dict[str, Any] = Depends(require_admin)  # ← 添加管理员权限验证
):
    """
    修改坐席信息 (需要管理员权限)

    Args:
        username: 坐席用户名
        request: 修改请求

    权限: 管理员

    Returns:
        agent: 修改后的坐席信息
    """
    try:
        if not agent_manager:
            raise HTTPException(status_code=500, detail="坐席管理系统未初始化")

        # 获取坐席
        agent = agent_manager.get_agent_by_username(username)
        if not agent:
            raise HTTPException(
                status_code=404,
                detail="AGENT_NOT_FOUND: 坐席不存在"
            )

        # 检查是否要降级最后一个管理员
        if request.role == AgentRole.AGENT and agent.role == AgentRole.ADMIN:
            if agent_manager.count_admins() <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="LAST_ADMIN: 不能降级最后一个管理员"
                )

        # 更新字段
        if request.name is not None:
            agent.name = request.name
        if request.role is not None:
            agent.role = request.role
        if request.max_sessions is not None:
            agent.max_sessions = request.max_sessions
        if request.status is not None:
            agent.status = request.status
        if request.avatar_url is not None:
            agent.avatar_url = request.avatar_url

        # 保存
        agent_manager.update_agent(agent)

        # 返回结果（隐藏密码）
        agent_dict = agent.dict()
        agent_dict.pop("password_hash", None)

        print(f"✅ 修改坐席信息: {username}")

        return {
            "success": True,
            "agent": agent_dict
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 修改坐席信息失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"修改失败: {str(e)}"
        )


@app.delete("/api/agents/{username}")
async def delete_agent(
    username: str,
    admin: Dict[str, Any] = Depends(require_admin)  # ← 添加管理员权限验证
):
    """
    删除坐席账号 (需要管理员权限)

    限制：
    - 不能删除最后一个管理员
    - 不能删除有活跃会话的坐席（暂不实现）

    Args:
        username: 坐席用户名

    权限: 管理员

    Returns:
        message: 删除结果
    """
    try:
        if not agent_manager:
            raise HTTPException(status_code=500, detail="坐席管理系统未初始化")

        # 获取坐席
        agent = agent_manager.get_agent_by_username(username)
        if not agent:
            raise HTTPException(
                status_code=404,
                detail="AGENT_NOT_FOUND: 坐席不存在"
            )

        # 检查是否是最后一个管理员
        if agent.role == AgentRole.ADMIN and agent_manager.count_admins() <= 1:
            raise HTTPException(
                status_code=400,
                detail="LAST_ADMIN: 不能删除最后一个管理员"
            )

        # 删除坐席
        result = agent_manager.delete_agent(username)
        if not result:
            raise HTTPException(
                status_code=500,
                detail="删除失败"
            )

        print(f"✅ 删除坐席账号: {username}")

        return {
            "success": True,
            "message": f"坐席 {username} 已删除"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 删除坐席账号失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"删除失败: {str(e)}"
        )


@app.post("/api/agents/{username}/reset-password")
async def reset_agent_password(
    username: str,
    request: ResetPasswordRequest,
    admin: Dict[str, Any] = Depends(require_admin)  # ← 添加管理员权限验证
):
    """
    重置坐席密码 (需要管理员权限)

    Args:
        username: 坐席用户名
        request: 重置密码请求

    权限: 管理员

    Returns:
        message: 重置结果
    """
    try:
        if not agent_manager:
            raise HTTPException(status_code=500, detail="坐席管理系统未初始化")

        # 获取坐席
        agent = agent_manager.get_agent_by_username(username)
        if not agent:
            raise HTTPException(
                status_code=404,
                detail="AGENT_NOT_FOUND: 坐席不存在"
            )

        # 验证密码强度
        if not validate_password(request.new_password):
            raise HTTPException(
                status_code=400,
                detail="INVALID_PASSWORD: 密码必须至少8个字符，包含字母和数字"
            )

        # 更新密码
        agent.password_hash = PasswordHasher.hash_password(request.new_password)
        agent_manager.update_agent(agent)

        print(f"✅ 重置坐席密码: {username}")

        return {
            "success": True,
            "message": "密码已重置"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 重置坐席密码失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"重置失败: {str(e)}"
        )


@app.post("/api/admin/sessions/clear")
async def clear_all_sessions(admin: Dict[str, Any] = Depends(require_admin)):
    """
    清空所有会话数据（管理员）
    """
    if not session_store:
        raise HTTPException(status_code=503, detail="Session store not initialized")

    cleared = await session_store.clear_all()
    print(f"🧹 管理员 {admin.get('username')} 清空会话 {cleared} 条")

    return {
        "success": True,
        "cleared": cleared
    }


@app.post("/api/agent/change-password")
async def change_password(
    request: ChangePasswordRequest,
    agent: Dict[str, Any] = Depends(require_agent)  # ← 任何登录用户都可以
):
    """
    修改自己的密码 (需要坐席权限)

    Args:
        request: 修改密码请求

    权限: 任何登录用户

    Returns:
        message: 修改结果
    """
    try:
        if not agent_manager:
            raise HTTPException(status_code=500, detail="坐席管理系统未初始化")

        # 获取当前登录的坐席
        username = agent.get("username")
        current_agent = agent_manager.get_agent_by_username(username)

        if not current_agent:
            raise HTTPException(
                status_code=404,
                detail="AGENT_NOT_FOUND: 坐席不存在"
            )

        # 验证旧密码
        if not PasswordHasher.verify_password(request.old_password, current_agent.password_hash):
            raise HTTPException(
                status_code=400,
                detail="OLD_PASSWORD_INCORRECT: 旧密码不正确"
            )

        # 验证新密码强度
        if not validate_password(request.new_password):
            raise HTTPException(
                status_code=400,
                detail="INVALID_PASSWORD: 密码必须至少8个字符，包含字母和数字"
            )

        # 验证新密码不能与旧密码相同
        if PasswordHasher.verify_password(request.new_password, current_agent.password_hash):
            raise HTTPException(
                status_code=400,
                detail="PASSWORD_SAME: 新密码不能与旧密码相同"
            )

        # 更新密码
        current_agent.password_hash = PasswordHasher.hash_password(request.new_password)
        agent_manager.update_agent(current_agent)

        print(f"✅ 坐席修改密码: {username}")

        return {
            "success": True,
            "message": "密码修改成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 坐席修改密码失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"修改失败: {str(e)}"
        )


@app.put("/api/agent/profile")
async def update_profile(
    request: UpdateProfileRequest,
    agent: Dict[str, Any] = Depends(require_agent)  # ← 任何登录用户都可以
):
    """
    修改个人资料 (需要坐席权限)

    Args:
        request: 修改资料请求

    权限: 任何登录用户

    Returns:
        agent: 修改后的坐席信息
    """
    try:
        if not agent_manager:
            raise HTTPException(status_code=500, detail="坐席管理系统未初始化")

        # 获取当前登录的坐席
        username = agent.get("username")
        current_agent = agent_manager.get_agent_by_username(username)

        if not current_agent:
            raise HTTPException(
                status_code=404,
                detail="AGENT_NOT_FOUND: 坐席不存在"
            )

        # 检查是否至少有一个字段需要修改
        if request.name is None and request.avatar_url is None:
            raise HTTPException(
                status_code=400,
                detail="NO_FIELDS_TO_UPDATE: 至少需要提供一个要修改的字段"
            )

        # 只修改允许的字段
        if request.name is not None:
            current_agent.name = request.name

        if request.avatar_url is not None:
            current_agent.avatar_url = request.avatar_url

        # 更新坐席信息
        agent_manager.update_agent(current_agent)

        # 返回结果（隐藏密码）
        agent_dict = current_agent.dict()
        agent_dict.pop("password_hash", None)

        print(f"✅ 坐席修改个人资料: {username}")

        return {
            "success": True,
            "agent": agent_dict
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 坐席修改个人资料失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"修改失败: {str(e)}"
        )


# ====================
# 客户信息与业务上下文 API (v3.2.0+)
# ====================

@app.get("/api/customers/{customer_id}/profile")
async def get_customer_profile(
    customer_id: str,
    agent: dict = Depends(require_agent)
):
    """
    获取客户画像信息

    Args:
        customer_id: 客户ID（当前为 session_id）
        agent: 坐席信息（来自 JWT）

    Returns:
        客户画像数据
    """
    try:
        if not session_store:
            raise HTTPException(status_code=503, detail="Session store not initialized")

        session_state = await session_store.get(customer_id)
        if not session_state:
            raise HTTPException(status_code=404, detail="CUSTOMER_NOT_FOUND: 会话不存在")

        profile = session_state.user_profile
        profile_dict = profile.model_dump()
        profile_dict["customer_id"] = customer_id

        print(f"✅ 获取客户画像: customer_id={customer_id}, agent={agent.get('username')}")

        return {
            "success": True,
            "data": profile_dict
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取客户画像失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取客户画像失败: {str(e)}"
        )


# ====================
# 【模块3】快捷回复系统 API (v3.7.0+)
# ====================

@app.get("/api/quick-replies/categories")
async def get_quick_reply_categories(
    agent: dict = Depends(require_agent)
):
    """
    获取快捷回复分类列表

    Args:
        agent: 当前登录坐席信息

    Returns:
        分类列表
    """
    try:
        return {
            "success": True,
            "data": {
                "categories": QUICK_REPLY_CATEGORIES,
                "supported_variables": SUPPORTED_VARIABLES
            }
        }

    except Exception as e:
        print(f"❌ 获取分类列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取失败: {str(e)}"
        )


@app.get("/api/quick-replies/stats")
async def get_quick_reply_stats(
    agent: dict = Depends(require_agent)
):
    """
    获取快捷回复使用统计

    权限: 管理员

    Args:
        agent: 当前登录坐席信息

    Returns:
        使用统计数据
    """
    try:
        # 权限检查：仅管理员可查看统计
        if agent.get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="PERMISSION_DENIED: 需要管理员权限"
            )

        if not quick_reply_store:
            raise HTTPException(status_code=503, detail="快捷回复系统未初始化")

        stats = quick_reply_store.get_stats()

        return {
            "success": True,
            "data": stats
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取快捷回复统计失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取统计失败: {str(e)}"
        )


@app.get("/api/quick-replies")
async def get_quick_replies(
    category: Optional[str] = None,
    agent_id: Optional[str] = None,
    include_shared: bool = True,
    keyword: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    agent: dict = Depends(require_agent)
):
    """
    获取快捷回复列表

    功能:
    - 按分类筛选
    - 按坐席筛选（获取自己创建的 + 团队共享的）
    - 关键词搜索
    - 分页

    Args:
        category: 分类筛选
        agent_id: 坐席ID筛选（默认为当前登录坐席）
        include_shared: 是否包含团队共享的快捷回复
        keyword: 搜索关键词
        limit: 每页数量
        offset: 偏移量
        agent: 当前登录坐席信息

    Returns:
        快捷回复列表
    """
    try:
        if not quick_reply_store:
            raise HTTPException(status_code=503, detail="快捷回复系统未初始化")

        # 如果未指定 agent_id，使用当前登录坐席
        if not agent_id:
            agent_id = agent.get("agent_id")

        # 关键词搜索
        if keyword:
            replies = quick_reply_store.search(
                keyword=keyword,
                agent_id=agent_id,
                category=category,
                limit=limit
            )
        # 按分类查询
        elif category:
            replies = quick_reply_store.list_by_category(
                category=category,
                limit=limit,
                offset=offset
            )
        # 按坐席查询
        elif agent_id:
            replies = quick_reply_store.list_by_agent(
                agent_id=agent_id,
                include_shared=include_shared,
                limit=limit,
                offset=offset
            )
        # 获取全部
        else:
            replies = quick_reply_store.list_all(limit=limit, offset=offset)

        return {
            "success": True,
            "data": {
                "items": [r.to_dict() for r in replies],
                "total": len(replies),
                "limit": limit,
                "offset": offset
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取快捷回复列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取失败: {str(e)}"
        )


@app.post("/api/quick-replies")
async def create_quick_reply(
    request: dict,
    agent: dict = Depends(require_agent)
):
    """
    创建快捷回复

    Body:
    {
        "title": "欢迎语",
        "content": "您好{customer_name}，我是{agent_name}",
        "category": "greeting",
        "shortcut_key": "1",
        "is_shared": false
    }

    Args:
        request: 创建请求
        agent: 当前登录坐席信息

    Returns:
        创建的快捷回复
    """
    try:
        if not quick_reply_store or not variable_replacer:
            raise HTTPException(status_code=503, detail="快捷回复系统未初始化")

        # 验证必填字段
        if not request.get("title") or not request.get("content"):
            raise HTTPException(
                status_code=400,
                detail="MISSING_FIELDS: title 和 content 为必填项"
            )

        # 验证分类
        category = request.get("category", "custom")
        if category not in QUICK_REPLY_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail=f"INVALID_CATEGORY: 无效的分类 {category}"
            )

        # 提取模板中使用的变量
        content = request.get("content")
        variables = variable_replacer.extract_variables(content)

        # 创建快捷回复对象
        quick_reply = QuickReply(
            id="",  # 由 store 自动生成
            title=request.get("title"),
            content=content,
            category=category,
            variables=variables,
            shortcut_key=request.get("shortcut_key"),
            is_shared=request.get("is_shared", False),
            created_by=agent.get("agent_id")
        )

        # 保存到存储
        created = quick_reply_store.create(quick_reply)

        print(f"✅ 创建快捷回复: {created.id} by {agent.get('username')}")

        return {
            "success": True,
            "data": created.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 创建快捷回复失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"创建失败: {str(e)}"
        )


@app.get("/api/quick-replies/{reply_id}")
async def get_quick_reply(
    reply_id: str,
    agent: dict = Depends(require_agent)
):
    """
    获取快捷回复详情

    Args:
        reply_id: 快捷回复ID
        agent: 当前登录坐席信息

    Returns:
        快捷回复详情
    """
    try:
        if not quick_reply_store:
            raise HTTPException(status_code=503, detail="快捷回复系统未初始化")

        reply = quick_reply_store.get(reply_id)

        if not reply:
            raise HTTPException(
                status_code=404,
                detail="QUICK_REPLY_NOT_FOUND: 快捷回复不存在"
            )

        return {
            "success": True,
            "data": reply.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取快捷回复详情失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取失败: {str(e)}"
        )


@app.put("/api/quick-replies/{reply_id}")
async def update_quick_reply(
    reply_id: str,
    request: dict,
    agent: dict = Depends(require_agent)
):
    """
    更新快捷回复

    Body:
    {
        "title": "新标题",
        "content": "新内容",
        "category": "pre_sales",
        "shortcut_key": "2",
        "is_shared": true
    }

    权限:
    - 创建者可以修改
    - 管理员可以修改所有快捷回复

    Args:
        reply_id: 快捷回复ID
        request: 更新请求
        agent: 当前登录坐席信息

    Returns:
        更新后的快捷回复
    """
    try:
        if not quick_reply_store or not variable_replacer:
            raise HTTPException(status_code=503, detail="快捷回复系统未初始化")

        # 获取原快捷回复
        reply = quick_reply_store.get(reply_id)

        if not reply:
            raise HTTPException(
                status_code=404,
                detail="QUICK_REPLY_NOT_FOUND: 快捷回复不存在"
            )

        # 权限检查：只有创建者或管理员可以修改
        if reply.created_by != agent.get("agent_id") and agent.get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="PERMISSION_DENIED: 只有创建者或管理员可以修改"
            )

        # 构建更新字典
        updates = {}

        if "title" in request:
            updates["title"] = request["title"]

        if "content" in request:
            updates["content"] = request["content"]
            # 重新提取变量
            updates["variables"] = variable_replacer.extract_variables(request["content"])

        if "category" in request:
            category = request["category"]
            if category not in QUICK_REPLY_CATEGORIES:
                raise HTTPException(
                    status_code=400,
                    detail=f"INVALID_CATEGORY: 无效的分类 {category}"
                )
            updates["category"] = category

        if "shortcut_key" in request:
            updates["shortcut_key"] = request["shortcut_key"]

        if "is_shared" in request:
            updates["is_shared"] = request["is_shared"]

        # 更新
        updated = quick_reply_store.update(reply_id, updates)

        if not updated:
            raise HTTPException(
                status_code=500,
                detail="更新失败"
            )

        print(f"✅ 更新快捷回复: {reply_id} by {agent.get('username')}")

        return {
            "success": True,
            "data": updated.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 更新快捷回复失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"更新失败: {str(e)}"
        )


@app.delete("/api/quick-replies/{reply_id}")
async def delete_quick_reply(
    reply_id: str,
    agent: dict = Depends(require_agent)
):
    """
    删除快捷回复

    权限:
    - 创建者可以删除
    - 管理员可以删除所有快捷回复

    Args:
        reply_id: 快捷回复ID
        agent: 当前登录坐席信息

    Returns:
        删除结果
    """
    try:
        if not quick_reply_store:
            raise HTTPException(status_code=503, detail="快捷回复系统未初始化")

        # 获取快捷回复
        reply = quick_reply_store.get(reply_id)

        if not reply:
            raise HTTPException(
                status_code=404,
                detail="QUICK_REPLY_NOT_FOUND: 快捷回复不存在"
            )

        # 权限检查：只有创建者或管理员可以删除
        if reply.created_by != agent.get("agent_id") and agent.get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="PERMISSION_DENIED: 只有创建者或管理员可以删除"
            )

        # 删除
        result = quick_reply_store.delete(reply_id)

        if not result:
            raise HTTPException(
                status_code=500,
                detail="删除失败"
            )

        print(f"✅ 删除快捷回复: {reply_id} by {agent.get('username')}")

        return {
            "success": True,
            "message": f"快捷回复 {reply_id} 已删除"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 删除快捷回复失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"删除失败: {str(e)}"
        )


@app.post("/api/quick-replies/{reply_id}/use")
async def use_quick_reply(
    reply_id: str,
    request: dict,
    agent: dict = Depends(require_agent)
):
    """
    使用快捷回复（执行变量替换并增加使用次数）

    Body:
    {
        "session_data": {...},  # 会话数据（包含 user_profile）
        "agent_data": {...},    # 坐席数据
        "shopify_data": {...}   # Shopify 数据（可选）
    }

    Args:
        reply_id: 快捷回复ID
        request: 使用请求
        agent: 当前登录坐席信息

    Returns:
        替换变量后的内容
    """
    try:
        if not quick_reply_store or not variable_replacer:
            raise HTTPException(status_code=503, detail="快捷回复系统未初始化")

        # 获取快捷回复
        reply = quick_reply_store.get(reply_id)

        if not reply:
            raise HTTPException(
                status_code=404,
                detail="QUICK_REPLY_NOT_FOUND: 快捷回复不存在"
            )

        # 构建变量上下文
        context = build_variable_context(
            session_data=request.get("session_data"),
            agent_data=request.get("agent_data"),
            shopify_data=request.get("shopify_data")
        )

        # 执行变量替换
        replaced_content = variable_replacer.replace(
            template=reply.content,
            context=context
        )

        # 增加使用次数
        quick_reply_store.increment_usage(reply_id)

        print(f"✅ 使用快捷回复: {reply_id} by {agent.get('username')}")

        return {
            "success": True,
            "data": {
                "id": reply.id,
                "title": reply.title,
                "original_content": reply.content,
                "replaced_content": replaced_content,
                "variables": reply.variables
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 使用快捷回复失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"使用失败: {str(e)}"
        )


# ==================== 【模块5】内部备注功能 ====================

# 内存存储（生产环境应使用 Redis）
internal_notes_store: Dict[str, List[Dict[str, Any]]] = {}


class InternalNoteRequest(BaseModel):
    """创建/更新内部备注请求"""
    content: str
    mentions: Optional[List[str]] = []  # @的坐席username列表


@app.post("/api/sessions/{session_name}/notes")
async def create_internal_note(
    session_name: str,
    request: InternalNoteRequest,
    agent: dict = Depends(require_agent)
):
    """
    添加内部备注（仅坐席可见）

    Args:
        session_name: 会话ID
        request: 备注内容和@提醒列表
        agent: 当前登录坐席信息

    Returns:
        创建的备注信息
    """
    try:
        # 验证会话是否存在
        if not session_store:
            raise HTTPException(status_code=503, detail="会话系统未初始化")

        session_state = await session_store.get(session_name)
        if not session_state:
            raise HTTPException(
                status_code=404,
                detail="SESSION_NOT_FOUND: 会话不存在"
            )

        # 创建备注
        note = {
            "id": f"note_{uuid.uuid4().hex[:16]}",
            "session_name": session_name,
            "content": request.content,
            "created_by": agent.get("username"),
            "created_by_name": agent.get("name", agent.get("username")),
            "created_at": time.time(),
            "updated_at": time.time(),
            "mentions": request.mentions or []
        }

        # 保存到存储
        if session_name not in internal_notes_store:
            internal_notes_store[session_name] = []
        internal_notes_store[session_name].append(note)

        print(f"✅ 创建内部备注: {note['id']} for session {session_name} by {agent.get('username')}")

        # TODO: 如果有@提醒，通过SSE推送通知给被@的坐席
        if request.mentions:
            print(f"📢 @提醒: {request.mentions}")

        return {
            "success": True,
            "data": note
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 创建内部备注失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"创建失败: {str(e)}"
        )


@app.get("/api/sessions/{session_name}/notes")
async def get_internal_notes(
    session_name: str,
    agent: dict = Depends(require_agent)
):
    """
    获取会话的所有内部备注

    Args:
        session_name: 会话ID
        agent: 当前登录坐席信息

    Returns:
        备注列表
    """
    try:
        # 获取备注列表
        notes = internal_notes_store.get(session_name, [])

        # 按创建时间倒序排序
        notes_sorted = sorted(notes, key=lambda x: x["created_at"], reverse=True)

        return {
            "success": True,
            "data": notes_sorted,
            "total": len(notes_sorted)
        }

    except Exception as e:
        print(f"❌ 获取内部备注失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取失败: {str(e)}"
        )


@app.put("/api/sessions/{session_name}/notes/{note_id}")
async def update_internal_note(
    session_name: str,
    note_id: str,
    request: InternalNoteRequest,
    agent: dict = Depends(require_agent)
):
    """
    编辑内部备注（仅创建者和管理员可编辑）

    Args:
        session_name: 会话ID
        note_id: 备注ID
        request: 新的备注内容
        agent: 当前登录坐席信息

    Returns:
        更新后的备注信息
    """
    try:
        # 查找备注
        notes = internal_notes_store.get(session_name, [])
        note = next((n for n in notes if n["id"] == note_id), None)

        if not note:
            raise HTTPException(
                status_code=404,
                detail="NOTE_NOT_FOUND: 备注不存在"
            )

        # 权限检查：仅创建者和管理员可编辑
        if note["created_by"] != agent.get("username") and agent.get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="PERMISSION_DENIED: 只有创建者和管理员可以编辑备注"
            )

        # 更新备注
        note["content"] = request.content
        note["mentions"] = request.mentions or []
        note["updated_at"] = time.time()

        print(f"✅ 更新内部备注: {note_id} by {agent.get('username')}")

        return {
            "success": True,
            "data": note
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 更新内部备注失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"更新失败: {str(e)}"
        )


@app.delete("/api/sessions/{session_name}/notes/{note_id}")
async def delete_internal_note(
    session_name: str,
    note_id: str,
    agent: dict = Depends(require_agent)
):
    """
    删除内部备注（仅创建者和管理员可删除）

    Args:
        session_name: 会话ID
        note_id: 备注ID
        agent: 当前登录坐席信息

    Returns:
        删除结果
    """
    try:
        # 查找备注
        notes = internal_notes_store.get(session_name, [])
        note = next((n for n in notes if n["id"] == note_id), None)

        if not note:
            raise HTTPException(
                status_code=404,
                detail="NOTE_NOT_FOUND: 备注不存在"
            )

        # 权限检查：仅创建者和管理员可删除
        if note["created_by"] != agent.get("username") and agent.get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="PERMISSION_DENIED: 只有创建者和管理员可以删除备注"
            )

        # 删除备注
        internal_notes_store[session_name] = [
            n for n in notes if n["id"] != note_id
        ]

        print(f"✅ 删除内部备注: {note_id} by {agent.get('username')}")

        return {
            "success": True,
            "message": f"备注 {note_id} 已删除"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 删除内部备注失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"删除失败: {str(e)}"
        )


# ==================== 【模块5】会话转接增强 ====================

class TransferRequestEnhanced(BaseModel):
    """增强的会话转接请求"""
    from_agent_id: str
    to_agent_id: str
    to_agent_name: str
    reason: str  # 转接原因
    note: Optional[str] = ""  # 转接备注（给接收坐席的说明）


# 转接历史存储
transfer_history_store: Dict[str, List[Dict[str, Any]]] = {}
pending_transfer_requests: Dict[str, List[Dict[str, Any]]] = {}


class TransferResponseRequest(BaseModel):
    """转接请求响应"""
    action: Literal['accept', 'decline']
    response_note: Optional[str] = ""


def find_pending_transfer_request(request_id: str):
    """
    辅助函数：定位待处理转接请求
    """
    for agent_id, requests in pending_transfer_requests.items():
        for index, request in enumerate(requests):
            if request.get("id") == request_id:
                return request, agent_id, index
    return None, None, None


@app.get("/api/sessions/{session_name}/transfer-history")
async def get_transfer_history(
    session_name: str,
    agent: dict = Depends(require_agent)
):
    """
    获取会话转接历史

    Args:
        session_name: 会话ID
        agent: 当前登录坐席信息

    Returns:
        转接历史列表
    """
    try:
        history = transfer_history_store.get(session_name, [])

        # 按时间倒序
        history_sorted = sorted(history, key=lambda x: x["transferred_at"], reverse=True)

        return {
            "success": True,
            "data": history_sorted,
            "total": len(history_sorted)
        }

    except Exception as e:
        print(f"❌ 获取转接历史失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取失败: {str(e)}"
        )


@app.get("/api/transfer-requests/pending")
async def get_pending_transfer_requests(agent: dict = Depends(require_agent)):
    """
    获取当前登录坐席待处理的转接请求
    """
    try:
        agent_id = agent.get("agent_id")
        if not agent_id:
            raise HTTPException(status_code=401, detail="UNAUTHORIZED")

        requests = pending_transfer_requests.get(agent_id, [])
        return {
            "success": True,
            "data": requests,
            "total": len(requests)
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取转接请求失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@app.post("/api/transfer-requests/{request_id}/respond")
async def respond_transfer_request(
    request_id: str,
    response: TransferResponseRequest,
    agent: dict = Depends(require_agent)
):
    """
    处理转接请求（接受/拒绝）
    """
    try:
        pending_request, owner_id, index = find_pending_transfer_request(request_id)
        if not pending_request:
            raise HTTPException(status_code=404, detail="REQUEST_NOT_FOUND: 转接请求不存在或已处理")

        current_agent_id = agent.get("agent_id")
        if owner_id != current_agent_id:
            raise HTTPException(status_code=403, detail="PERMISSION_DENIED: 只能处理指向自己的转接请求")

        # 移除待处理请求
        pending_transfer_requests[owner_id].pop(index)
        if not pending_transfer_requests[owner_id]:
            del pending_transfer_requests[owner_id]

        session_name = pending_request["session_name"]
        from_agent_id = pending_request["from_agent_id"]
        to_agent_id = pending_request["to_agent_id"]
        to_agent_name = pending_request["to_agent_name"]
        reason = pending_request["reason"]
        note = pending_request.get("note", "")

        # 统一记录历史
        def append_history(record: Dict[str, Any]):
            if session_name not in transfer_history_store:
                transfer_history_store[session_name] = []
            transfer_history_store[session_name].append(record)

        if response.action == 'decline':
            record = {
                "id": request_id,
                "session_name": session_name,
                "from_agent": from_agent_id,
                "from_agent_name": pending_request.get("from_agent_name"),
                "to_agent": to_agent_id,
                "to_agent_name": to_agent_name,
                "reason": reason,
                "note": note,
                "transferred_at": pending_request.get("created_at"),
                "accepted": False,
                "decision": "declined",
                "responded_at": time.time(),
                "response_note": response.response_note or ""
            }
            append_history(record)

            return {
                "success": True,
                "message": "已拒绝转接请求"
            }

        # 接受流程
        if not session_store:
            raise HTTPException(status_code=503, detail="SessionStore not initialized")

        session_state = await session_store.get(session_name)
        if not session_state:
            raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND: 会话不存在")

        if session_state.status != SessionStatus.MANUAL_LIVE:
            record = {
                "id": request_id,
                "session_name": session_name,
                "from_agent": from_agent_id,
                "from_agent_name": pending_request.get("from_agent_name"),
                "to_agent": to_agent_id,
                "to_agent_name": to_agent_name,
                "reason": reason,
                "note": note,
                "transferred_at": pending_request.get("created_at"),
                "accepted": False,
                "decision": "expired",
                "responded_at": time.time(),
                "response_note": "会话状态已改变"
            }
            append_history(record)
            raise HTTPException(status_code=409, detail="INVALID_STATUS: 会话状态已改变，无法接收转接")

        if session_state.assigned_agent and session_state.assigned_agent.id != from_agent_id:
            record = {
                "id": request_id,
                "session_name": session_name,
                "from_agent": from_agent_id,
                "from_agent_name": pending_request.get("from_agent_name"),
                "to_agent": to_agent_id,
                "to_agent_name": to_agent_name,
                "reason": reason,
                "note": note,
                "transferred_at": pending_request.get("created_at"),
                "accepted": False,
                "decision": "expired",
                "responded_at": time.time(),
                "response_note": "会话已被其他坐席接管"
            }
            append_history(record)
            raise HTTPException(status_code=409, detail="SESSION_ALREADY_TAKEN: 会话已经被其他坐席接管")

        from src.session_state import AgentInfo

        system_message = Message(
            role="system",
            content=f"会话已从【{pending_request.get('from_agent_name', '未知')}】转接至【{to_agent_name}】（原因：{reason}）"
        )
        session_state.add_message(system_message)
        session_state.assigned_agent = AgentInfo(id=to_agent_id, name=to_agent_name)
        session_state.manual_start_at = time.time()

        await session_store.save(session_state)

        record = {
            "id": request_id,
            "session_name": session_name,
            "from_agent": from_agent_id,
            "from_agent_name": pending_request.get("from_agent_name"),
            "to_agent": to_agent_id,
            "to_agent_name": to_agent_name,
            "reason": reason,
            "note": note,
            "transferred_at": pending_request.get("created_at"),
            "accepted": True,
            "decision": "accepted",
            "responded_at": time.time(),
            "response_note": response.response_note or ""
        }
        append_history(record)

        # 推送 SSE
        if session_name in sse_queues:
            await sse_queues[session_name].put({
                "type": "manual_message",
                "role": "system",
                "content": system_message.content,
                "timestamp": system_message.timestamp
            })
            await sse_queues[session_name].put({
                "type": "status_change",
                "status": "manual_live",
                "agent_info": {
                    "agent_id": to_agent_id,
                    "agent_name": to_agent_name
                },
                "reason": "transferred",
                "timestamp": int(time.time())
            })

        if agent_manager:
            agent_manager.update_last_active(from_agent_id)
            agent_manager.update_last_active(to_agent_id)

        return {
            "success": True,
            "data": session_state.model_dump(),
            "message": "已接受转接请求"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 处理转接请求失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


# ==================== 【模块5】协助请求功能 ====================

@app.post("/api/assist-requests")
async def create_assist_request(
    request: CreateAssistRequestRequest,
    agent: dict = Depends(require_agent)
):
    """
    创建协助请求

    允许坐席在不转接会话的情况下请求其他坐席协助。

    Args:
        request: 协助请求信息
        agent: 当前登录坐席信息

    Returns:
        创建的协助请求
    """
    try:
        # 验证协助者是否存在
        assistant_agent = agent_manager.get_agent_by_username(request.assistant)
        if not assistant_agent:
            raise HTTPException(
                status_code=404,
                detail="ASSISTANT_NOT_FOUND: 协助者不存在"
            )

        # 验证会话是否存在
        session_state = session_store.get(request.session_name)
        if not session_state:
            raise HTTPException(
                status_code=404,
                detail="SESSION_NOT_FOUND: 会话不存在"
            )

        # 创建协助请求
        assist_request = AssistRequest(
            id=f"assist_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}",
            session_name=request.session_name,
            requester=agent.get("username"),
            assistant=request.assistant,
            question=request.question,
            status=AssistStatus.PENDING,
            created_at=time.time()
        )

        # 保存到存储
        assist_request_store.create(assist_request)

        print(f"✅ 创建协助请求: {assist_request.id} ({agent.get('username')} → {request.assistant})")

        # 推送SSE通知给协助者
        if request.assistant in sse_queues:
            await sse_queues[request.assistant].put({
                "type": "assist_request",
                "data": {
                    "id": assist_request.id,
                    "session_name": assist_request.session_name,
                    "requester": assist_request.requester,
                    "question": assist_request.question,
                    "created_at": assist_request.created_at
                }
            })

        return {
            "success": True,
            "data": assist_request.model_dump()
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 创建协助请求失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"创建失败: {str(e)}"
        )


@app.get("/api/assist-requests")
async def get_assist_requests(
    status: Optional[str] = None,
    agent: dict = Depends(require_agent)
):
    """
    获取协助请求列表

    坐席可以查看：
    - 发送给自己的协助请求（作为协助者）
    - 自己发出的协助请求（作为请求者）

    Args:
        status: 可选的状态过滤（pending/answered）
        agent: 当前登录坐席信息

    Returns:
        协助请求列表（包含收到的和发出的）
    """
    try:
        username = agent.get("username")

        # 验证状态参数
        filter_status = None
        if status:
            try:
                filter_status = AssistStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"INVALID_STATUS: 无效的状态值，必须是 pending 或 answered"
                )

        # 获取收到的协助请求（我作为协助者）
        received_requests = assist_request_store.get_by_assistant(username, status=filter_status)

        # 获取发出的协助请求（我作为请求者）
        sent_requests = assist_request_store.get_by_requester(username, status=filter_status)

        return {
            "success": True,
            "data": {
                "received": [r.model_dump() for r in received_requests],
                "sent": [r.model_dump() for r in sent_requests]
            },
            "count": {
                "received": len(received_requests),
                "sent": len(sent_requests),
                "received_pending": assist_request_store.count_pending_by_assistant(username)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取协助请求失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取失败: {str(e)}"
        )


@app.post("/api/assist-requests/{request_id}/answer")
async def answer_assist_request(
    request_id: str,
    request: AnswerAssistRequestRequest,
    agent: dict = Depends(require_agent)
):
    """
    回复协助请求

    只有被请求协助的坐席可以回复。

    Args:
        request_id: 协助请求ID
        request: 回复内容
        agent: 当前登录坐席信息

    Returns:
        更新后的协助请求
    """
    try:
        # 获取协助请求
        assist_request = assist_request_store.get(request_id)
        if not assist_request:
            raise HTTPException(
                status_code=404,
                detail="REQUEST_NOT_FOUND: 协助请求不存在"
            )

        # 权限检查：只有协助者可以回复
        if assist_request.assistant != agent.get("username"):
            raise HTTPException(
                status_code=403,
                detail="PERMISSION_DENIED: 只有被请求的坐席可以回复"
            )

        # 检查是否已回复
        if assist_request.status == AssistStatus.ANSWERED:
            raise HTTPException(
                status_code=400,
                detail="ALREADY_ANSWERED: 该请求已被回复"
            )

        # 回复协助请求
        updated_request = assist_request_store.answer(request_id, request.answer)

        print(f"✅ 回复协助请求: {request_id} by {agent.get('username')}")

        # 推送SSE通知给请求者
        if updated_request.requester in sse_queues:
            await sse_queues[updated_request.requester].put({
                "type": "assist_answer",
                "data": {
                    "id": updated_request.id,
                    "session_name": updated_request.session_name,
                    "assistant": updated_request.assistant,
                    "answer": updated_request.answer,
                    "answered_at": updated_request.answered_at
                }
            })

        return {
            "success": True,
            "data": updated_request.model_dump()
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 回复协助请求失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"回复失败: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    print(f"""
    ==========================================
    🚀 Fiido智能客服后端服务启动中...
    ==========================================
    📍 地址: http://{host}:{port}
    📖 API文档: http://{host}:{port}/docs
    📊 交互式文档: http://{host}:{port}/redoc
    🔐 鉴权模式: {os.getenv("COZE_AUTH_MODE", "OAUTH_JWT")}
    💬 多轮对话: 已启用
    🔧 人工接管: 已启用
    ==========================================
    """)

    uvicorn.run(
        "backend:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
