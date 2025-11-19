# Coze Python SDK 使用指南

本文档基于 [Coze 官方 Python SDK](https://github.com/coze-dev/coze-py) 提供使用示例和最佳实践,重点介绍**应用对话流 (Workflow)** 的使用方法。

---

## 目录
- [SDK 简介](#sdk-简介)
- [安装](#安装)
- [认证方式](#认证方式)
- [Workflow 相关功能](#workflow-相关功能)
- [适用于本项目的功能](#适用于本项目的功能)
- [本项目实现方式](#本项目实现方式)
- [使用建议](#使用建议)

---

## SDK 简介

Coze Python SDK 是用于集成 Coze 开放 API 的官方 Python 库。

### 核心特性

- ✅ **完整 API 覆盖**: 支持所有 Coze 开放 API 和认证方法
- ✅ **同步/异步双接口**: 支持同步和异步 SDK 调用
- ✅ **流式优化**: 原生 Stream 和 AsyncStream 对象支持实时数据
- ✅ **分页简化**: 基于迭代器的 Page 对象,便于列表操作
- ✅ **开发者友好**: 直观的 API 设计,快速集成

### 系统要求

- Python 3.7+

---

## 安装

```bash
pip install cozepy
```

---

## 认证方式

Coze SDK 支持多种认证方式,以下是与**应用对话流**相关的认证方法:

### 1. OAuth JWT (服务应用认证) ⭐ 推荐

**适用场景**:
- 服务端应用
- 需要会话隔离的多用户系统
- **本项目使用的方式**

**官方示例** (`examples/auth_oauth_jwt.py`):

```python
import os
from cozepy import Coze, JWTAuth, JWTOAuthApp, COZE_CN_BASE_URL

# 配置
coze_api_base = os.getenv("COZE_API_BASE", "https://api.coze.com")
jwt_oauth_client_id = os.getenv("COZE_JWT_OAUTH_CLIENT_ID")
jwt_oauth_public_key_id = os.getenv("COZE_JWT_OAUTH_PUBLIC_KEY_ID")

# 读取私钥
with open("private_key.pem", "r") as f:
    jwt_oauth_private_key = f.read()

# 创建 JWTOAuthApp
jwt_oauth_app = JWTOAuthApp(
    client_id=jwt_oauth_client_id,
    private_key=jwt_oauth_private_key,
    public_key_id=jwt_oauth_public_key_id,
    base_url=coze_api_base,
)

# 获取 Access Token
# ttl 默认 900秒,最长 24小时
oauth_token = jwt_oauth_app.get_access_token(ttl=3600)

# 创建 Coze 客户端
coze = Coze(
    auth=JWTAuth(oauth_app=jwt_oauth_app),
    base_url=coze_api_base
)

# 使用客户端
workspaces = coze.workspaces.list()
print(workspaces.items)
```

**关键点**:
- ✅ JWT OAuth 不支持刷新 Token,过期后直接调用 `get_access_token()` 获取新 Token
- ✅ 支持在 JWT 中添加 `session_name` 实现会话隔离
- ✅ 适合服务端应用,安全性高

### 2. Personal Access Token (个人访问令牌)

**适用场景**:
- 个人开发测试
- 简单的单用户应用

**官方示例** (`examples/auth_pat.py`):

```python
from cozepy import Coze, TokenAuth

# 使用个人访问令牌
coze = Coze(
    auth=TokenAuth(token="your_personal_access_token"),
    base_url="https://api.coze.com"
)
```

**关键点**:
- ❌ 不支持会话隔离
- ❌ 不适合多用户系统
- ✅ 简单易用,适合测试

---

## Workflow 相关功能

Coze SDK 提供了两类 Workflow 功能:

### 1. Workflow Run (工作流运行)

**用途**: 执行工作流,获取结果数据

**功能对比**:

| 功能 | 适用场景 | 是否支持对话 |
|------|---------|-------------|
| `workflows.runs.create()` | 执行工作流,获取结构化数据 | ❌ 否 |
| `workflows.runs.stream()` | 流式执行工作流 | ❌ 否 |
| `workflows.chat()` | **对话流聊天** | ✅ 是 |
| `workflows.chat.stream()` | **流式对话聊天** | ✅ 是 |

**官方示例 - 非流式** (`examples/workflow_no_stream.py`):

```python
from cozepy import Coze, TokenAuth

coze = Coze(auth=TokenAuth(token=access_token), base_url="https://api.coze.com")

# 执行工作流 (非对话)
workflow = coze.workflows.runs.create(
    workflow_id="workflow_id",
)

print("workflow.data", workflow.data)
```

### 2. Workflow Chat (工作流对话) ⭐ 本项目适用

**用途**: 与对话流进行多轮对话,支持上下文记忆

#### 流式对话 (推荐)

**官方示例** (`examples/workflow_chat_stream.py`):

```python
from cozepy import Coze, TokenAuth, ChatEventType, Message

# 初始化客户端
coze = Coze(
    auth=TokenAuth(token=access_token),
    base_url="https://api.coze.com"
)

# 创建会话
conversation = coze.conversations.create()

# 流式聊天
for event in coze.workflows.chat.stream(
    workflow_id="your_workflow_id",
    bot_id="your_bot_id",  # 可选
    conversation_id=conversation.id,
    additional_messages=[
        Message.build_user_question_text("How are you?"),
    ],
):
    # 处理消息增量
    if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
        print(event.message.content, end="", flush=True)

    # 处理完成事件
    if event.event == ChatEventType.CONVERSATION_CHAT_COMPLETED:
        print()
        print("Token usage:", event.chat.usage.token_count)
```

**关键点**:
- ✅ 适用于**应用对话流**
- ✅ 支持流式响应,实时输出
- ✅ 支持多轮对话 (通过 `conversation_id`)
- ✅ 支持会话隔离 (通过 JWT session_name)

#### 非流式对话

```python
# 非流式聊天
chat_result = coze.workflows.chat(
    workflow_id="your_workflow_id",
    conversation_id=conversation.id,
    additional_messages=[
        Message.build_user_question_text("你好"),
    ],
)

print(chat_result.message.content)
```

---

## 适用于本项目的功能

本项目是**应用对话流 (Workflow Chat)** 系统,以下是官方 SDK 中适用的功能:

### ✅ 适用功能

| 功能模块 | 官方示例文件 | 用途 | 适用性 |
|---------|-------------|------|--------|
| **JWT OAuth 认证** | `auth_oauth_jwt.py` | 服务应用认证 | ✅ 核心功能 |
| **Workflow Chat Stream** | `workflow_chat_stream.py` | 流式对话 | ✅ 核心功能 |
| **Conversation 管理** | `conversation.py` | 创建和管理会话 | ✅ 辅助功能 |

### ❌ 不适用功能

| 功能模块 | 官方示例文件 | 原因 |
|---------|-------------|------|
| Bot Chat | `chat_stream.py` | 本项目使用 Workflow,不是 Bot |
| Workflow Run | `workflow_no_stream.py` | 仅执行工作流,不支持对话 |
| Device/Web/PKCE OAuth | `auth_oauth_*.py` | 适用于客户端应用 |
| WebSocket | `websockets_*.py` | 本项目使用 HTTP SSE |
| Audio/Voice | `audio*.py` | 本项目仅文本对话 |

---

## 本项目实现方式

本项目**没有直接使用** Coze 官方 SDK,而是手动实现了 JWT 签署和 API 调用。

### 为什么不用官方 SDK?

1. **更精确的会话隔离控制**
   - 需要在 **API payload 中**直接添加 `session_name` 字段
   - 官方 SDK 只在 JWT 中添加 session_name,API payload 需手动处理

2. **自定义 Token 管理**
   - 实现了按 `session_name` 缓存和刷新的机制
   - 官方 SDK 的 Token 缓存需要自己实现

3. **符合官方会话隔离要求**
   - 确保 JWT **和** API 两处都正确传递 session_name
   - 官方文档要求:必须在两处都添加 session_name

### 实现对比

#### 官方 SDK 方式

```python
from cozepy import Coze, JWTAuth, JWTOAuthApp, Message

# 1. 创建 OAuth App
jwt_oauth_app = JWTOAuthApp(
    client_id=client_id,
    private_key=private_key,
    public_key_id=public_key_id,
    base_url="https://api.coze.com",
)

# 2. 获取 Token (可以添加 session_name)
token = jwt_oauth_app.get_access_token(
    ttl=3600,
    session_name="user_123"  # ✅ JWT 中有 session_name
)

# 3. 创建客户端
coze = Coze(auth=JWTAuth(oauth_app=jwt_oauth_app))

# 4. 调用 API
for event in coze.workflows.chat.stream(
    workflow_id="xxx",
    conversation_id="xxx",
    additional_messages=[Message.build_user_question_text("你好")],
    # ⚠️ 问题: API payload 中缺少 session_name
):
    print(event.message.content)
```

**问题**:
- JWT 中有 session_name ✅
- 但 API payload 中缺少 session_name ❌
- 不符合官方会话隔离要求

#### 本项目实现方式

**1. JWT 签署** (`src/jwt_signer.py`):

```python
import jwt
import time
import uuid

class JWTSigner:
    def create_jwt(self, session_name=None):
        """创建 JWT Token"""
        now = int(time.time())

        payload = {
            "iss": self.client_id,
            "aud": self.audience,
            "iat": now,
            "exp": now + self.ttl,
            "jti": str(uuid.uuid4()),
        }

        # ✅ JWT 中添加 session_name
        if session_name:
            payload["session_name"] = session_name

        headers = {
            "kid": self.public_key_id,
            "alg": "RS256",
            "typ": "JWT"
        }

        return jwt.encode(payload, self.private_key, algorithm="RS256", headers=headers)
```

**2. Token 管理** (`src/oauth_token_manager.py`):

```python
class OAuthTokenManager:
    def get_access_token(self, session_name=None):
        """获取 Access Token (按 session_name 缓存)"""
        cache_key = session_name or "default"

        # 检查缓存
        if self._is_token_valid(cache_key):
            return self._token_cache[cache_key]["token"]

        # 生成新 token
        jwt_token = self.jwt_signer.create_jwt(session_name=session_name)

        # 请求 Access Token
        access_token = self._request_access_token_from_jwt(jwt_token)

        # 缓存
        self._token_cache[cache_key] = {
            "token": access_token,
            "expires_at": datetime.now() + timedelta(seconds=3300)
        }

        return access_token
```

**3. API 调用** (`backend.py`):

```python
import httpx

@app.post("/api/chat")
async def chat(request: ChatRequest):
    session_id = request.user_id or generate_user_id()

    # 获取带 session_name 的 token
    access_token = token_manager.get_access_token(session_name=session_id)

    # ✅ 构建 payload (API 中也添加 session_name)
    payload = {
        "workflow_id": WORKFLOW_ID,
        "app_id": APP_ID,
        "session_name": session_id,  # ← 关键: API payload 中添加
        "parameters": {"USER_INPUT": request.message},
        "additional_messages": [
            {
                "content": request.message,
                "content_type": "text",
                "role": "user",
                "type": "question"
            }
        ]
    }

    # 调用 Coze API
    headers = {"Authorization": f"Bearer {access_token}"}
    response = httpx.post(
        "https://api.coze.com/v1/workflows/chat",
        json=payload,
        headers=headers
    )
```

### 关键差异总结

| 项目 | 官方 SDK | 本项目实现 |
|------|---------|-----------|
| **JWT 签署** | ✅ 支持 session_name | ✅ 手动实现,完全控制 |
| **API payload session_name** | ⚠️ 需手动添加 | ✅ 直接在 payload 中添加 |
| **Token 缓存** | ❌ 需要自己实现 | ✅ 内置按 session 缓存 |
| **会话隔离** | ⚠️ 需要自己组装 | ✅ 完整实现并测试通过 |
| **代码复杂度** | 低 (使用 SDK) | 中 (手动实现) |
| **灵活性** | 中等 | 高 (完全控制) |

---

## 使用建议

### 方案 1: 使用官方 SDK (推荐新项目)

**适用场景**:
- 新项目开发
- 标准的聊天功能
- 不需要复杂的会话管理
- 快速原型开发

**示例代码**:

```python
from cozepy import Coze, JWTAuth, JWTOAuthApp, Message, ChatEventType

# 初始化
jwt_oauth_app = JWTOAuthApp(
    client_id="your_client_id",
    private_key=private_key_content,
    public_key_id="your_public_key_id",
    base_url="https://api.coze.com"
)

coze = Coze(auth=JWTAuth(oauth_app=jwt_oauth_app))

# 使用
conversation = coze.conversations.create()
for event in coze.workflows.chat.stream(
    workflow_id="your_workflow_id",
    conversation_id=conversation.id,
    additional_messages=[Message.build_user_question_text("你好")],
):
    if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
        print(event.message.content, end="", flush=True)
```

**优势**:
- ✅ 代码简洁
- ✅ 官方维护,稳定可靠
- ✅ 自动处理很多细节

**劣势**:
- ⚠️ API payload 中的 session_name 需要手动处理
- ⚠️ Token 缓存需要自己实现

### 方案 2: 手动实现 (本项目方式)

**适用场景**:
- 需要精确控制会话隔离
- 多用户系统
- 需要自定义 Token 管理策略
- 需要在 API payload 中传递额外字段

**优势**:
- ✅ 完全控制 JWT payload
- ✅ 自定义 Token 缓存策略
- ✅ 确保 session_name 在 JWT 和 API 两处都正确传递
- ✅ 灵活性高,可扩展

**劣势**:
- ⚠️ 代码量更多
- ⚠️ 需要自己处理更多细节
- ⚠️ 维护成本略高

### 方案 3: 混合方式 (推荐)

**使用官方 SDK 生成 Token + 手动调用 API**:

```python
from cozepy import JWTOAuthApp
import httpx

# 1. 使用官方 SDK 生成 Token
jwt_oauth_app = JWTOAuthApp(
    client_id="your_client_id",
    private_key=private_key_content,
    public_key_id="your_public_key_id",
    base_url="https://api.coze.com"
)

# 为特定用户生成 Token
token = jwt_oauth_app.get_access_token(
    ttl=3600,
    session_name="user_123"  # JWT 中添加 session_name
)

# 2. 手动调用 API (确保 payload 中也有 session_name)
payload = {
    "workflow_id": "your_workflow_id",
    "app_id": "your_app_id",
    "session_name": "user_123",  # API payload 中也添加
    "parameters": {"USER_INPUT": "你好"},
    "additional_messages": [...]
}

response = httpx.post(
    "https://api.coze.com/v1/workflows/chat",
    json=payload,
    headers={"Authorization": f"Bearer {token}"}
)
```

**优势**:
- ✅ 利用 SDK 简化 JWT 生成
- ✅ 手动控制 API 调用,确保 session_name 正确传递
- ✅ 平衡了简洁性和控制力

---

## 参考资料

- [Coze Python SDK GitHub](https://github.com/coze-dev/coze-py)
- [Coze 官方文档](https://www.coze.com/docs)
- [OAuth JWT 文档](https://www.coze.com/docs/developer_guides/oauth_jwt)
- [Workflow Chat API](https://www.coze.com/docs/developer_guides/chat_with_bot_stream)
- [会话隔离官方说明](https://www.coze.com/docs/developer_guides/session_isolation)

---

**文档更新时间**: 2025-11-19
**基于 SDK 版本**: coze-py latest (2025)
