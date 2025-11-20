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


# 全局变量
coze_client: Optional[Coze] = None
token_manager: Optional[OAuthTokenManager] = None
jwt_oauth_app: Optional[JWTOAuthApp] = None  # 用于 Chat SDK 的 JWTOAuthApp
WORKFLOW_ID: str = ""
APP_ID: str = ""  # AI 应用 ID（应用中嵌入对话流时必需）
AUTH_MODE: str = ""  # 鉴权模式：OAUTH_JWT 或 PAT

# Conversation 管理 - 存储每个 session_name 对应的 conversation_id
# 实现原理: 首次不传 conversation_id,Coze 会自动生成并返回
# 后续对话必须传入相同的 conversation_id 以保持上下文
conversation_cache: dict = {}  # {session_name: conversation_id}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global coze_client, token_manager, jwt_oauth_app, WORKFLOW_ID, APP_ID, AUTH_MODE

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

    # OAuth+JWT 鉴权
    try:
        token_manager = OAuthTokenManager.from_env()
        # 获取初始 token
        access_token = token_manager.get_access_token()

        # 创建带超时配置的 HTTP 客户端
        http_client = httpx.Client(timeout=HTTP_TIMEOUT)
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

        # 更新 Coze 客户端的 token（带超时配置）
        api_base = os.getenv("COZE_API_BASE", "https://api.coze.com")
        http_client = httpx.Client(timeout=HTTP_TIMEOUT)
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

        # 刷新 coze_client (确保使用正确的 token)
        api_base = os.getenv("COZE_API_BASE", "https://api.coze.com")
        http_client = httpx.Client(timeout=HTTP_TIMEOUT)
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

        # 更新 Coze 客户端
        api_base = os.getenv("COZE_API_BASE", "https://api.coze.com")
        http_client = httpx.Client(timeout=HTTP_TIMEOUT)
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

        http_client = httpx.Client(timeout=HTTP_TIMEOUT)

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

            http_client = httpx.Client(timeout=HTTP_TIMEOUT)

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

                            # 处理消息增量事件 - 实时推送
                            if event_type == 'conversation.message.delta':
                                if 'content' in data and data.get('role') == 'assistant':
                                    content = data['content']
                                    if content:
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
    ==========================================
    """)

    uvicorn.run(
        "backend:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
