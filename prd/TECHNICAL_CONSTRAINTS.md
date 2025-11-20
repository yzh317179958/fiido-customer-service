# Fiido AI客服系统 - 技术约束与开发原则

> **文档版本**: v1.0
> **最后更新**: 2025-11-19
> **文档性质**: 🔴 **强制性技术约束** - 所有后续开发必须遵守

---

## 📜 文档目的

本文档定义了 Fiido AI客服系统的**不可变技术约束**，确保：
1. 系统始终符合 Coze 平台的 API 调用规则
2. 核心 AI 对话功能永不被破坏
3. 所有新功能必须在现有架构基础上扩展，而非替换

---

## 🚨 核心原则（铁律）

### 原则 1: 核心功能不可变
**所有涉及 Coze API 调用的功能，禁止修改其核心逻辑，只允许扩展**

- ✅ 允许：在现有接口基础上**增加**新功能
- ❌ 禁止：修改现有 Coze API 调用方式
- ❌ 禁止：更改现有接口的响应格式
- ❌ 禁止：移除现有的鉴权机制

### 原则 2: Coze 平台限制优先级最高
**任何设计决策必须以 Coze 平台限制为准**

- Coze API 的响应格式是什么样，我们就必须按什么样处理
- 无法绕过的限制，不得强行尝试

### 原则 3: 新功能向后兼容
**所有新增功能不得影响现有功能的正常运行**

- 新增 API 接口不得占用现有路由
- 新增模块不得修改现有模块的行为
- 测试必须验证现有功能仍然正常工作

---

## 🔒 Coze 平台限制（不可绕过）

### 1. API 调用限制

#### 1.1 Workflow Chat API 强制 SSE 流式响应

**平台限制**：
```
端点: POST /v1/workflows/chat
响应格式: Server-Sent Events (SSE) 流
```

**约束说明**：
- ❌ **禁止**：期望 JSON 格式响应
- ❌ **禁止**：使用 `response.json()` 解析响应
- ✅ **必须**：使用 `stream()` 方法接收 SSE 流
- ✅ **必须**：逐行解析 `event:` 和 `data:` 格式

**代码实现要求**：
```python
# ✅ 正确方式
async with async_http_client.stream(
    "POST",
    f"{api_base}/v1/workflows/chat",
    headers=headers,
    json=payload
) as response:
    async for chunk in response.aiter_bytes():
        # 解析 SSE 流
        ...

# ❌ 错误方式 - 禁止使用
response = await async_http_client.post(...)
data = response.json()  # 这会失败！
```

#### 1.2 SSE 事件数据结构

**平台返回格式**：
```
event: conversation.chat.created
data: {"id": "xxx", "status": "created", ...}

event: conversation.chat.in_progress
data: {"id": "xxx", "status": "in_progress", ...}

data: {"id": "xxx", "type": "answer", "content": "消息内容", ...}

data: {"id": "xxx", "status": "completed", ...}
```

**约束说明**：
- ✅ **必须**：从顶层提取 `type` 和 `content` 字段
- ❌ **禁止**：假设存在 `message.content` 嵌套结构
- ✅ **必须**：检查 `type == "answer"` 来识别 AI 回复
- ✅ **必须**：检查 `status == "completed"` 来判断对话结束

**代码实现要求**：
```python
# ✅ 正确解析
event_data = json.loads(data_content)
if event_data.get("type") == "answer" and event_data.get("content"):
    message_content += event_data["content"]

# ❌ 错误解析 - 禁止使用
if "message" in event_data:  # Coze 不返回这种结构！
    content = event_data["message"]["content"]
```

#### 1.3 必需的请求参数

**平台要求**：
```json
{
  "workflow_id": "必需",
  "app_id": "必需",
  "additional_messages": [
    {
      "content": "用户消息",
      "content_type": "text",
      "role": "user"
    }
  ]
}
```

**约束说明**：
- ✅ **必须**：提供 `workflow_id` 和 `app_id`
- ✅ **必须**：`additional_messages` 格式严格按上述结构
- ⚠️ **注意**：`app_id` 对应应用对话流，不是 `bot_id`（智能体）
- ✅ **可选**：`conversation_id`（用于多轮对话）
- ✅ **可选**：`parameters`（传递自定义参数）

---

### 2. OAuth + JWT 鉴权限制

#### 2.1 JWT Token 生成

**平台限制**：
- Token 通过 RSA 私钥签名生成
- Token 有效期最长 24 小时（推荐 1 小时）
- Token 过期后无法刷新，必须重新生成

**约束说明**：
- ✅ **必须**：使用 JWTOAuthApp 或手动实现 JWT 签名
- ✅ **必须**：支持 `session_name` 实现会话隔离
- ❌ **禁止**：尝试实现 Token 刷新机制（平台不支持）
- ✅ **必须**：Token 过期前主动重新生成

**代码实现要求**：
```python
# ✅ 正确方式 - 使用 JWTOAuthApp
jwt_oauth_app = JWTOAuthApp(
    client_id=client_id,
    private_key=private_key,
    public_key_id=public_key_id,
    base_url=api_base
)
token = jwt_oauth_app.get_access_token(
    ttl=3600,
    session_name=session_id  # 会话隔离
)

# ❌ 错误方式 - 禁止
# 没有 refresh_token 机制！
```

#### 2.2 会话隔离实现

**平台要求**：
- JWT payload 中必须包含 `session_name`
- API 请求 payload 中建议也包含 `session_name`

**约束说明**：
- ✅ **必须**：每个用户生成独立的 session_name
- ✅ **推荐**：session_name 使用 UUID 或唯一标识
- ✅ **必须**：同一 session 的对话使用相同 session_name

---

## 🛡️ 不可变核心接口

以下接口是系统的基石，**禁止修改其核心逻辑**，只允许扩展。

### 核心接口 1: `/api/chat` (非流式对话)

**功能**: 接收用户消息，返回完整 AI 回复

**技术约束**：
```python
# 必须遵守的实现方式
async def chat_async(request: ChatRequest):
    # 1. 获取 Token（必须支持 session_name）
    access_token = token_manager.get_access_token(session_name=session_id)

    # 2. 构建 payload（格式不可变）
    payload = {
        "workflow_id": WORKFLOW_ID,
        "app_id": APP_ID,
        "additional_messages": [
            {
                "content": request.message,
                "content_type": "text",
                "role": "user"
            }
        ]
    }

    # 3. 必须使用 stream() 接收 SSE 流
    async with async_http_client.stream(...) as response:
        # 4. 必须逐行解析 SSE
        buffer = ""
        async for chunk in response.aiter_bytes():
            buffer += chunk.decode('utf-8')
            # 解析逻辑...

    # 5. 返回格式不可变
    return ChatResponse(success=True, message=message_content)
```

**禁止的修改**：
- ❌ 修改 payload 的必需字段格式
- ❌ 使用 `.post()` 替代 `.stream()`
- ❌ 修改返回的 `ChatResponse` 结构
- ❌ 移除 session_name 支持

**允许的扩展**：
- ✅ 添加额外的可选参数（不影响现有逻辑）
- ✅ 在返回前添加后处理逻辑（如日志、监控）
- ✅ 添加错误处理和重试机制

---

### 核心接口 2: `/api/chat/stream` (流式对话)

**功能**: 接收用户消息，实时流式返回 AI 回复

**技术约束**：
```python
async def chat_stream_async(request: ChatRequest):
    async def generate_stream():
        # 1. 获取 Token（必须）
        access_token = token_manager.get_access_token(session_name=session_id)

        # 2. 构建 payload（格式不可变）
        payload = {
            "workflow_id": WORKFLOW_ID,
            "app_id": APP_ID,
            "additional_messages": [...]
        }

        # 3. 必须使用 stream() 接收
        async with async_http_client.stream(...) as response:
            buffer = ""
            async for chunk in response.aiter_bytes():
                # 4. 必须解析并实时转发
                if event_data.get("type") == "answer":
                    yield f"data: {json.dumps({'type': 'message', 'content': content})}\n\n"

                if event_data.get("status") == "completed":
                    yield f"data: {json.dumps({'type': 'done', 'content': ''})}\n\n"

    # 5. 返回格式不可变
    return StreamingResponse(generate_stream(), media_type="text/event-stream")
```

**禁止的修改**：
- ❌ 修改 SSE 事件格式 `data: {...}\n\n`
- ❌ 修改事件类型定义 (`type: message`, `type: done`)
- ❌ 移除实时转发机制
- ❌ 改为批量返回

**允许的扩展**：
- ✅ 添加额外的事件类型（如进度提示）
- ✅ 添加中间件处理流式数据
- ✅ 添加流式数据的监控和日志

---

### 核心接口 3: `/api/conversation/new` (创建会话)

**功能**: 为用户创建新的 Conversation

**技术约束**：
```python
async def create_new_conversation_async(request: NewConversationRequest):
    # 1. 必须使用 JWTOAuthApp 生成 Token
    token_response = jwt_oauth_app.get_access_token(
        ttl=3600,
        session_name=session_id  # 必须包含
    )

    # 2. 必须调用 Coze Conversation API
    response = await async_http_client.post(
        f"{api_base}/v1/conversations/create",
        headers={"Authorization": f"Bearer {access_token}"},
        json={}
    )

    # 3. 返回格式不可变
    return {
        "success": True,
        "conversation_id": conversation_id
    }
```

**禁止的修改**：
- ❌ 移除 session_name 机制
- ❌ 修改返回的数据结构
- ❌ 绕过 Coze API 自行生成 conversation_id

---

## 📋 核心数据模型（不可变）

### ChatRequest (请求模型)

```python
class ChatRequest(BaseModel):
    message: str                           # 必需
    parameters: Optional[dict] = {}        # 可选
    user_id: Optional[str] = None          # 会话 ID（必需支持）
    conversation_id: Optional[str] = None  # Conversation ID（可选）
```

**约束**：
- ❌ 禁止移除 `user_id` 字段（用于 session 隔离）
- ✅ 可以添加新的可选字段

### ChatResponse (响应模型)

```python
class ChatResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
```

**约束**：
- ❌ 禁止修改这三个字段的类型和含义
- ✅ 可以添加新的可选字段

---

## 🔧 核心模块（不可变）

### 1. OAuth Token 管理器 (`src/oauth_token_manager.py`)

**功能**: 管理 Coze OAuth Token 的生成、缓存、过期处理

**不可变接口**：
```python
class OAuthTokenManager:
    def get_access_token(self, session_name: str = None) -> str:
        """
        获取 Access Token

        必须支持:
        - session_name 参数（会话隔离）
        - Token 缓存机制
        - 自动过期检测和重新生成
        """
```

**约束**：
- ❌ 禁止移除 `session_name` 参数
- ❌ 禁止移除 Token 缓存机制
- ✅ 可以优化缓存策略（如使用 Redis）

### 2. JWT 签名器 (`src/jwt_signer.py`)

**功能**: 生成符合 Coze 要求的 JWT Token

**不可变接口**：
```python
class JWTSigner:
    def create_jwt(self, session_name: str = None) -> str:
        """
        生成 JWT Token

        必须包含:
        - iss (client_id)
        - aud (Coze audience)
        - iat, exp (时间戳)
        - jti (唯一 ID)
        - session_name (如果提供)
        """
```

**约束**：
- ❌ 禁止修改 JWT payload 的必需字段
- ❌ 禁止使用非 RSA 算法
- ✅ 可以添加自定义 claims（不影响 Coze 验证）

---

## ✅ 允许的扩展方向

以下功能开发**不涉及 Coze API 调用**，可以自由设计，但仍需遵守向后兼容原则。

### 1. 会话状态管理 (`src/session_state.py`)

**性质**: 本地状态管理，不依赖 Coze API

**允许的操作**：
- ✅ 自由设计数据模型（SessionState, Message, etc.）
- ✅ 添加新的状态字段
- ✅ 实现 Redis 存储替代内存存储
- ✅ 添加状态转换逻辑

**约束**：
- ⚠️ 不得影响核心 `/api/chat` 接口的响应速度
- ⚠️ 状态管理失败不应导致聊天功能失败

### 2. 监管策略引擎 (`src/regulator.py`)

**性质**: 本地规则引擎，不依赖 Coze API

**允许的操作**：
- ✅ 自由设计监管规则（关键词、失败检测、VIP 等）
- ✅ 添加新的触发条件
- ✅ 修改规则配置方式

**约束**：
- ⚠️ 不得阻塞或延迟 AI 回复的返回
- ⚠️ 监管逻辑应异步处理

### 3. 人工接管功能

**性质**: 独立业务逻辑，不修改 AI 对话流程

**允许的操作**：
- ✅ 设计人工接管的触发机制
- ✅ 实现坐席工作台 API
- ✅ 添加邮件通知、排队逻辑等

**约束**：
- ⚠️ 人工接管时，AI 对话接口仍需可用（可返回特定提示）
- ⚠️ 不得修改 `/api/chat` 和 `/api/chat/stream` 的核心逻辑

### 4. 前端扩展

**性质**: 纯前端功能，不影响后端 API

**允许的操作**：
- ✅ 添加 UI 组件
- ✅ 优化用户体验
- ✅ 添加客户端状态管理

**约束**：
- ⚠️ 必须保持与现有 API 接口的兼容性
- ⚠️ 不得修改现有接口的调用方式

---

## 🧪 强制性测试要求

所有涉及 Coze API 的功能修改或扩展，必须通过以下测试：

### 测试 1: 基础 AI 对话测试

```bash
# 测试非流式接口
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"你好","user_id":"test_001"}'

# 预期结果
{"success":true,"message":"...AI回复内容...","error":null}
```

**通过标准**：
- ✅ success 为 true
- ✅ message 包含有效的 AI 回复
- ✅ 响应时间 < 30 秒

### 测试 2: 流式对话测试

```bash
# 测试流式接口
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message":"你好","user_id":"test_002"}' \
  --no-buffer
```

**通过标准**：
- ✅ 实时返回 SSE 事件流
- ✅ 事件格式为 `data: {"type":"message","content":"..."}\n\n`
- ✅ 最后返回 `data: {"type":"done","content":""}\n\n`

### 测试 3: 会话隔离测试

```bash
# 两个不同用户发送相同消息
curl -X POST http://localhost:8000/api/chat \
  -d '{"message":"记住我叫张三","user_id":"user_001"}'

curl -X POST http://localhost:8000/api/chat \
  -d '{"message":"我叫什么？","user_id":"user_002"}'
```

**通过标准**：
- ✅ user_002 的回复不应包含"张三"
- ✅ 每个用户的对话上下文独立

---

## 📐 架构设计约束

### 1. 分层架构原则

```
┌─────────────────────────────────────┐
│   前端 (index2.html)                │
│   可自由修改，保持 API 兼容         │
└─────────────────────────────────────┘
              ↓ HTTP
┌─────────────────────────────────────┐
│   API 层 (backend_async.py)         │
│   🔴 核心接口不可变                 │
│   ✅ 可添加新接口                   │
└─────────────────────────────────────┘
              ↓
┌──────────────┬──────────────────────┐
│ Coze API 调用│  本地业务逻辑        │
│ 🔴 严格遵守  │  ✅ 可自由设计       │
│ 平台限制     │  (session, regulator)│
└──────────────┴──────────────────────┘
```

**约束**：
- 🔴 **Coze API 调用层**：严格按本文档约束实现
- ✅ **本地业务逻辑层**：可自由设计，保证不影响 API 层
- ✅ **API 层**：可添加新接口，但不得修改核心接口

### 2. 模块依赖原则

```
核心模块（不可破坏）:
- oauth_token_manager.py
- jwt_signer.py
- backend_async.py (核心接口部分)

可扩展模块（自由设计）:
- session_state.py
- regulator.py
- 新增的任何模块
```

**约束**：
- ❌ 可扩展模块不得修改核心模块的行为
- ✅ 可扩展模块可以依赖核心模块
- ✅ 核心模块可以可选地调用扩展模块

---

## 🔄 代码审查检查清单

所有涉及 Coze API 的 Pull Request 必须通过以下检查：

### Checklist 1: API 调用检查

- [ ] 是否使用 `stream()` 方法调用 Coze API？
- [ ] 是否正确解析 SSE 流格式？
- [ ] payload 是否包含必需的 `workflow_id` 和 `app_id`？
- [ ] 是否支持 `session_name` 参数？
- [ ] Token 是否通过 `OAuthTokenManager` 获取？

### Checklist 2: 数据结构检查

- [ ] 是否从顶层提取 `type` 和 `content` 字段？
- [ ] 是否检查 `type == "answer"` 来识别 AI 回复？
- [ ] 是否检查 `status == "completed"` 来判断结束？
- [ ] 返回的 `ChatResponse` 格式是否保持一致？

### Checklist 3: 向后兼容性检查

- [ ] 现有的 `/api/chat` 接口是否仍然正常工作？
- [ ] 现有的 `/api/chat/stream` 接口是否仍然正常工作？
- [ ] 是否通过了基础 AI 对话测试？
- [ ] 是否通过了流式对话测试？
- [ ] 是否通过了会话隔离测试？

### Checklist 4: 扩展功能检查

- [ ] 新增功能是否独立于核心功能？
- [ ] 新增功能失败是否会导致核心功能失败？
- [ ] 是否添加了对应的测试用例？

---

## 📚 参考文档

### Coze 官方文档
- [Workflow Chat API](https://www.coze.com/docs/developer_guides/workflow_chat)
- [OAuth JWT 认证](https://www.coze.com/docs/developer_guides/oauth_jwt)
- [会话隔离](https://www.coze.com/docs/developer_guides/session_isolation)

### 项目内部文档
- [SDK 使用示例](../docs/guides/SDK使用示例.md)
- [项目结构说明](../PROJECT_STRUCTURE.md)
- [PRD 需求文档](./prd.md)
- [API 契约](./api_contract.md)

---

## 🔔 违规处理

如发现违反本文档约束的代码：

1. **轻度违规**（可修复）：
   - 代码审查阶段拒绝合并
   - 要求重构后重新提交

2. **重度违规**（破坏核心功能）：
   - 立即回滚
   - 重新评估设计方案
   - 参考本文档重新实现

---

## 📝 文档变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2025-11-19 | 初始版本，定义核心技术约束 | Claude Code |

---

**最后更新时间**: 2025-11-19
**文档维护者**: 开发团队
**审核状态**: ✅ 已审核通过
