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

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

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
    Agent
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


# 全局变量
coze_client: Optional[Coze] = None
token_manager: Optional[OAuthTokenManager] = None
jwt_oauth_app: Optional[JWTOAuthApp] = None  # 用于 Chat SDK 的 JWTOAuthApp
session_store: Optional[InMemorySessionStore] = None  # 会话状态存储（P0）
regulator: Optional[Regulator] = None  # 监管策略引擎（P0）
agent_manager: Optional[AgentManager] = None  # 坐席账号管理器
agent_token_manager: Optional[AgentTokenManager] = None  # 坐席 JWT Token 管理器
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global coze_client, token_manager, jwt_oauth_app, session_store, regulator, agent_manager, agent_token_manager, WORKFLOW_ID, APP_ID, AUTH_MODE

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

        # 使用 Python SDK 创建 Coze 客户端
        temp_coze = Coze(
            auth=TokenAuth(token=access_token),
            base_url=os.getenv("COZE_API_BASE", "https://api.coze.com")
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

        # 使用 Python SDK 创建 Coze 客户端
        temp_coze = Coze(
            auth=TokenAuth(token=access_token),
            base_url=os.getenv("COZE_API_BASE", "https://api.coze.com")
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

    try:
        # 获取会话状态
        session_state = await session_store.get(session_name)

        if not session_state:
            raise HTTPException(status_code=404, detail="Session not found")

        # 必须在manual_live状态才能释放
        if session_state.status != SessionStatus.MANUAL_LIVE:
            raise HTTPException(status_code=409, detail="Session not in manual_live status")

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

    if not all([from_agent_id, to_agent_id, to_agent_name]):
        raise HTTPException(
            status_code=400,
            detail="from_agent_id, to_agent_id, and to_agent_name are required"
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

        # 更新坐席信息
        from src.session_state import AgentInfo
        old_agent_name = session_state.assigned_agent.name if session_state.assigned_agent else "未知"

        session_state.assigned_agent = AgentInfo(
            id=to_agent_id,
            name=to_agent_name
        )

        # 添加系统消息
        system_message = Message(
            role="system",
            content=f"会话已从【{old_agent_name}】转接至【{to_agent_name}】（原因：{reason}）"
        )
        session_state.add_message(system_message)

        # 保存会话状态
        await session_store.save(session_state)

        # 记录日志
        print(json.dumps({
            "event": "session_transferred",
            "session_name": session_name,
            "from_agent": from_agent_id,
            "to_agent": to_agent_id,
            "to_agent_name": to_agent_name,
            "reason": reason,
            "timestamp": int(time.time())
        }, ensure_ascii=False))

        # 推送 SSE 事件
        if session_name in sse_queues:
            # 推送系统消息
            await sse_queues[session_name].put({
                "type": "manual_message",
                "role": "system",
                "content": f"会话已从【{old_agent_name}】转接至【{to_agent_name}】",
                "timestamp": system_message.timestamp
            })
            # 推送状态变化（坐席变更）
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
            print(f"✅ SSE 推送转接事件: {session_name}")

        return {
            "success": True,
            "data": session_state.model_dump(),
            "message": f"会话已转接至【{to_agent_name}】"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 转接会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"转接失败: {str(e)}")


@app.get("/api/sessions")
async def get_sessions(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    获取会话列表

    Query Parameters:
      - status: 会话状态过滤（pending_manual, manual_live等）
      - limit: 每页数量（默认50）
      - offset: 偏移量（默认0）
    """
    if not session_store:
        raise HTTPException(status_code=503, detail="SessionStore not initialized")

    try:
        # 🔴 P0-3.1: 按状态查询
        if status:
            try:
                status_enum = SessionStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status: {status}. Valid values: {[s.value for s in SessionStatus]}"
                )

            sessions = await session_store.list_by_status(
                status=status_enum,
                limit=limit,
                offset=offset
            )
            total = await session_store.count_by_status(status_enum)
        else:
            # 🔴 P0-3.2: 获取所有会话
            sessions = await session_store.list_all(limit=limit, offset=offset)
            total = await session_store.count_all()

        # 🔴 P0-3.3: 转换为摘要格式
        sessions_summary = [session.to_summary() for session in sessions]

        return {
            "success": True,
            "data": {
                "sessions": sessions_summary,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + len(sessions)) < total
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取会话列表失败: {str(e)}")
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

        from src.agent_auth import AgentStatus
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
    create_jwt_dependencies,
    validate_password,
    PasswordHasher,
    AgentRole
)

# 创建 JWT 权限依赖项（延迟初始化）
verify_agent_token = None
require_admin = None


def init_jwt_dependencies():
    """初始化 JWT 权限依赖项"""
    global verify_agent_token, require_admin
    if agent_token_manager and agent_manager:
        verify_agent_token, require_admin = create_jwt_dependencies(
            agent_token_manager, agent_manager
        )


@app.get("/api/agents")
async def get_agents_list(
    status: Optional[str] = None,
    role: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    """
    获取坐席列表 (需要管理员权限)

    Query Parameters:
        status: 过滤状态 (online/offline/busy)
        role: 过滤角色 (admin/agent)
        page: 页码，默认1
        page_size: 每页数量，默认20

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


@app.post("/api/agents")
async def create_agent(request: CreateAgentRequest):
    """
    创建坐席账号 (需要管理员权限)

    Args:
        request: 创建坐席请求

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
async def update_agent(username: str, request: UpdateAgentRequest):
    """
    修改坐席信息 (需要管理员权限)

    Args:
        username: 坐席用户名
        request: 修改请求

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
async def delete_agent(username: str):
    """
    删除坐席账号 (需要管理员权限)

    限制：
    - 不能删除最后一个管理员
    - 不能删除有活跃会话的坐席（暂不实现）

    Args:
        username: 坐席用户名

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
async def reset_agent_password(username: str, request: ResetPasswordRequest):
    """
    重置坐席密码 (需要管理员权限)

    Args:
        username: 坐席用户名
        request: 重置密码请求

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
