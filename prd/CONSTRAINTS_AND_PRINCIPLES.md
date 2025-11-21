# 人工接管功能开发 - 技术约束与开发原则

## 📋 文档信息

- **文档版本**: v1.0
- **创建时间**: 2025-11-21
- **依赖文档**: TECHNICAL_CONSTRAINTS.md
- **文档性质**: 🔴 **强制性开发约束** - 所有开发必须遵守

---

## 🎯 文档目的

本文档基于 `TECHNICAL_CONSTRAINTS.md` 中定义的核心技术约束,明确**人工接管功能开发**的边界和原则,确保:

1. ✅ 人工接管功能不破坏现有AI对话能力
2. ✅ 严格遵守 Coze 平台 API 调用规范
3. ✅ 所有新功能向后兼容
4. ✅ 扩展而非替换核心功能

---

## 🚨 核心铁律(必须遵守)

### 铁律 1: 不可修改的核心接口

以下接口是系统基石,**严禁修改其核心逻辑**:

```
🔴 不可修改:
- POST /api/chat              (同步AI对话)
- POST /api/chat/stream       (流式AI对话)
- POST /api/conversation/new  (创建会话)
```

**允许的操作**:
- ✅ 在调用前添加前置检查(如状态检查)
- ✅ 在返回后添加后置处理(如日志记录)
- ❌ **禁止**修改 Coze API 调用方式
- ❌ **禁止**修改返回的数据结构

**示例 - P0-1任务中的正确做法**:

```python
# ✅ 正确 - 在现有逻辑前添加状态检查
@app.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    # 【新增】人工接管状态检查 - 前置检查
    if session_store and regulator:
        session_state = await session_store.get_or_create(...)

        # 如果在人工接管中,拒绝AI对话
        if session_state.status in [SessionStatus.PENDING_MANUAL, SessionStatus.MANUAL_LIVE]:
            raise HTTPException(
                status_code=409,
                detail=f"SESSION_IN_MANUAL_MODE: {session_state.status}"
            )

    # ... 以下是原有的 Coze API 调用逻辑,完全不动 ...
    access_token = token_manager.get_access_token(session_name=session_id)

    payload = {
        "workflow_id": WORKFLOW_ID,
        "app_id": APP_ID,
        "additional_messages": [...]
    }

    async with async_http_client.stream(...) as response:
        # ... 原有SSE解析逻辑 ...
```

```python
# ❌ 错误 - 修改了核心逻辑
@app.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    # ❌ 错误:改变了Coze API调用方式
    if is_manual_mode:
        # 调用人工API而非Coze API
        return call_manual_agent(request)

    # ❌ 错误:修改了payload结构
    payload = {
        "workflow_id": WORKFLOW_ID,
        "manual_mode": True  # 新增字段会导致Coze API报错
    }
```

---

### 铁律 2: Coze API 调用规范(不可违反)

#### 2.1 必须使用 SSE 流式响应

```python
# ✅ 正确 - 使用 stream() 方法
async with async_http_client.stream(
    "POST",
    f"{api_base}/v1/workflows/chat",
    headers=headers,
    json=payload
) as response:
    async for chunk in response.aiter_bytes():
        # 解析SSE流
        ...

# ❌ 错误 - 使用 post() 方法会失败
response = await async_http_client.post(...)
data = response.json()  # Coze返回的是SSE流,不是JSON!
```

#### 2.2 SSE 事件解析规范

```python
# ✅ 正确 - 从顶层提取字段
event_data = json.loads(data_content)
if event_data.get("type") == "answer" and event_data.get("content"):
    message_content += event_data["content"]

# ❌ 错误 - Coze不返回嵌套结构
if "message" in event_data:
    content = event_data["message"]["content"]  # 这个字段不存在!
```

#### 2.3 必需的请求参数

```python
# ✅ 正确 - 包含所有必需字段
payload = {
    "workflow_id": WORKFLOW_ID,      # 必需
    "app_id": APP_ID,                # 必需
    "additional_messages": [         # 必需
        {
            "content": user_message,
            "content_type": "text",
            "role": "user"
        }
    ],
    "conversation_id": conv_id,      # 可选(多轮对话需要)
    "parameters": custom_params      # 可选
}

# ❌ 错误 - 缺少必需字段
payload = {
    "workflow_id": WORKFLOW_ID,
    # 缺少 app_id 会导致API调用失败!
    "messages": [...]  # 字段名错误,应为 additional_messages
}
```

---

### 铁律 3: OAuth + JWT 鉴权机制(不可绕过)

#### 3.1 Token 获取方式

```python
# ✅ 正确 - 使用 token_manager
access_token = token_manager.get_access_token(
    session_name=session_id  # 必须包含session_name实现隔离
)

# ❌ 错误 - 硬编码Token
access_token = "hardcoded_token"  # Token会过期!

# ❌ 错误 - 绕过token_manager
access_token = jwt.encode(...)  # 缺少缓存和过期管理!
```

#### 3.2 会话隔离机制

```python
# ✅ 正确 - 每个用户独立session_name
session_id = request.user_id or str(uuid.uuid4())
access_token = token_manager.get_access_token(session_name=session_id)

# ❌ 错误 - 所有用户共用一个Token
access_token = token_manager.get_access_token()  # 会导致对话混乱!
```

---

## 📐 人工接管功能开发边界

### ✅ 允许的扩展(不涉及Coze API)

以下功能**完全自由设计**,不受Coze平台限制:

#### 1. 会话状态管理 (`src/session_state.py`)

```python
# ✅ 允许自由设计
class SessionState(BaseModel):
    session_name: str
    status: SessionStatus           # ✅ 可自由定义状态
    escalation: Optional[EscalationInfo]  # ✅ 可添加任意字段
    assigned_agent: Optional[AgentInfo]   # ✅ 可自定义数据模型
    history: List[Message]          # ✅ 可自定义消息格式
```

**约束**:
- ⚠️ 状态管理失败不应影响AI对话功能
- ⚠️ 建议异步保存状态,避免阻塞API响应

#### 2. 监管引擎 (`src/regulator.py`)

```python
# ✅ 允许自由设计
class Regulator:
    def evaluate(self, session, user_message, ai_response):
        # ✅ 可自由实现监管规则
        # ✅ 可添加关键词检测、失败检测、VIP检测等
        # ✅ 可自定义触发条件和优先级
```

**约束**:
- ⚠️ 监管逻辑应异步处理,不阻塞AI回复
- ⚠️ 触发监管后可以拒绝AI请求,但需返回明确错误

#### 3. 人工接管API (新增接口)

```python
# ✅ 允许自由设计新接口
@app.post("/api/manual/escalate")        # ✅ 新增接口
@app.post("/api/manual/messages")        # ✅ 新增接口
@app.post("/api/sessions/{id}/takeover") # ✅ 新增接口
@app.post("/api/sessions/{id}/release")  # ✅ 新增接口
@app.get("/api/sessions")                # ✅ 新增接口
```

**约束**:
- ✅ 可以自由设计接口路径和参数
- ✅ 可以自由设计返回格式
- ⚠️ 不得占用现有路由 (`/api/chat`, `/api/chat/stream`, etc.)

#### 4. SSE 队列管理 (消息推送)

```python
# ✅ 允许扩展SSE事件类型
sse_queues: dict[str, asyncio.Queue] = {}  # ✅ 可自由实现

async def push_sse_event(session_id: str, event: dict):
    # ✅ 可自定义事件类型
    event = {
        "type": "manual_message",   # ✅ 新事件类型
        "role": "agent",            # ✅ 自定义字段
        "content": "...",
        "agent_info": {...}         # ✅ 自定义字段
    }
```

**约束**:
- ✅ 可以添加新的SSE事件类型
- ⚠️ 不得修改现有事件类型格式 (`type: message`, `type: done`)

---

### ❌ 禁止的操作

#### 1. 禁止修改AI对话核心流程

```python
# ❌ 禁止 - 在人工模式下改变AI对话逻辑
@app.post("/api/chat/stream")
async def chat_stream_async(request: ChatRequest):
    if is_manual_mode:
        # ❌ 错误:直接返回人工消息
        return StreamingResponse(manual_stream(), ...)

    # 原有逻辑...
```

**正确做法**:

```python
# ✅ 正确 - 在前置检查中拒绝请求
@app.post("/api/chat/stream")
async def chat_stream_async(request: ChatRequest):
    # 前置检查
    if session_state.status in [PENDING_MANUAL, MANUAL_LIVE]:
        # 返回错误,不继续执行
        async def error_stream():
            yield f"data: {json.dumps({'type': 'error', 'content': 'MANUAL_IN_PROGRESS'})}\n\n"
        return StreamingResponse(error_stream(), ...)

    # ... 原有Coze API调用逻辑完全不动 ...
```

#### 2. 禁止修改SSE流格式

```python
# ❌ 禁止 - 修改Coze返回的事件格式
async def generate_stream():
    # ❌ 错误:改变事件格式
    yield f"{json.dumps({'message': content})}\n\n"  # 缺少 "data: " 前缀!

    # ❌ 错误:改变type字段含义
    yield f"data: {json.dumps({'type': 'ai_message', ...})}\n\n"  # type应为'message'

# ✅ 正确 - 保持格式一致
async def generate_stream():
    # AI消息
    yield f"data: {json.dumps({'type': 'message', 'content': ai_content})}\n\n"

    # 完成标记
    yield f"data: {json.dumps({'type': 'done', 'content': ''})}\n\n"

    # 可以添加新的事件类型(不影响现有)
    yield f"data: {json.dumps({'type': 'manual_message', 'role': 'agent', ...})}\n\n"
```

#### 3. 禁止绕过Token机制

```python
# ❌ 禁止 - 绕过OAuth认证
async with async_http_client.stream(
    "POST",
    f"{api_base}/v1/workflows/chat",
    headers={"Authorization": "Bearer hardcoded_token"},  # ❌ 错误!
    ...
)

# ✅ 正确 - 始终使用token_manager
access_token = token_manager.get_access_token(session_name=session_id)
async with async_http_client.stream(
    "POST",
    f"{api_base}/v1/workflows/chat",
    headers={"Authorization": f"Bearer {access_token}"},  # ✅ 正确
    ...
)
```

---

## 🔧 开发实施指导

### P0-1: 修复状态机逻辑

**任务**: 在 `pending_manual` 状态下阻止AI对话

**技术约束检查**:
- ✅ 不修改 `/api/chat` 核心逻辑
- ✅ 只添加前置状态检查
- ✅ Coze API调用部分完全不动

**实施代码**:

```python
# backend.py line 532-580
@app.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    # ... 现有的session_id提取逻辑 ...

    # 【新增】前置状态检查 - 不影响原有逻辑
    if session_store and regulator:
        session_state = await session_store.get_or_create(
            session_name=session_id,
            conversation_id=conversation_id_for_state
        )

        # 如果正在人工接管中,直接拒绝
        if session_state.status in [SessionStatus.PENDING_MANUAL, SessionStatus.MANUAL_LIVE]:
            raise HTTPException(
                status_code=409,
                detail=f"SESSION_IN_MANUAL_MODE: {session_state.status}"
            )

    # ===== 以下是原有逻辑,完全不动 =====

    # 获取Token (原有逻辑)
    access_token = token_manager.get_access_token(session_name=session_id)

    # 构建payload (原有逻辑)
    payload = {
        "workflow_id": WORKFLOW_ID,
        "app_id": APP_ID,
        "additional_messages": [...]
    }

    # 调用Coze API (原有逻辑)
    async with async_http_client.stream(...) as response:
        # ... 原有SSE解析逻辑 ...

    return ChatResponse(success=True, message=message_content)
```

**验证**:
- ✅ 现有AI对话功能不受影响
- ✅ Coze API调用方式未改变
- ✅ 返回格式保持一致

---

### P0-2: 实现坐席接入API

**任务**: 实现 `POST /api/sessions/{session_name}/takeover`

**技术约束检查**:
- ✅ 这是新增接口,不涉及Coze API
- ✅ 可以自由设计参数和返回格式
- ✅ 不影响现有接口

**实施代码**:

```python
# backend.py (新增接口)
@app.post("/api/sessions/{session_name}/takeover")
async def takeover_session(session_name: str, request: dict):
    """
    坐席接入会话 - 完全新增的业务逻辑
    不涉及Coze API调用,可以自由设计
    """
    if not session_store:
        raise HTTPException(status_code=503, detail="SessionStore not initialized")

    # ✅ 自由设计:获取参数
    agent_id = request.get("agent_id")
    agent_name = request.get("agent_name")

    # ✅ 自由设计:业务逻辑
    session_state = await session_store.get(session_name)

    # 防抢单检查
    if session_state.status == SessionStatus.MANUAL_LIVE:
        raise HTTPException(
            status_code=409,
            detail=f"ALREADY_TAKEN: 已被{session_state.assigned_agent.name}接入"
        )

    # 分配坐席
    session_state.assigned_agent = AgentInfo(id=agent_id, name=agent_name)
    session_state.transition_status(SessionStatus.MANUAL_LIVE)

    await session_store.save(session_state)

    # ✅ 自由设计:返回格式
    return {"success": True, "data": session_state.model_dump()}
```

**验证**:
- ✅ 未修改任何现有接口
- ✅ 不涉及Coze API调用
- ✅ 完全独立的业务逻辑

---

### P0-8: 扩展SSE事件处理

**任务**: 在流式接口中添加人工消息推送

**技术约束检查**:
- ✅ 可以添加新的事件类型
- ❌ 不得修改现有事件格式
- ✅ 保持向后兼容

**实施代码**:

```python
# backend.py line 805-950
@app.post("/api/chat/stream")
async def chat_stream_async(request: ChatRequest):
    async def generate_stream():
        # ... 省略前置逻辑 ...

        # ===== Coze AI响应处理 (原有逻辑,不动) =====
        async with async_http_client.stream(...) as response:
            buffer = ""
            async for chunk in response.aiter_bytes():
                # ... 原有SSE解析逻辑 ...

                # AI消息 (原有格式,不动)
                if event_data.get("type") == "answer":
                    yield f"data: {json.dumps({'type': 'message', 'content': content})}\n\n"

                # 完成标记 (原有格式,不动)
                if event_data.get("status") == "completed":
                    yield f"data: {json.dumps({'type': 'done', 'content': ''})}\n\n"

        # ===== 【新增】人工消息推送 (不影响原有) =====

        # 检查SSE队列中是否有人工消息
        if session_id in sse_queues:
            queue = sse_queues[session_id]

            # 非阻塞检查队列
            while not queue.empty():
                try:
                    manual_event = await asyncio.wait_for(queue.get(), timeout=0.1)

                    # ✅ 新增事件类型 - 不影响前端对现有事件的处理
                    if manual_event.get("type") == "manual_message":
                        yield f"data: {json.dumps(manual_event)}\n\n"

                    elif manual_event.get("type") == "status_change":
                        yield f"data: {json.dumps(manual_event)}\n\n"

                except asyncio.TimeoutError:
                    break

    return StreamingResponse(generate_stream(), media_type="text/event-stream")
```

**验证**:
- ✅ 原有事件格式未改变
- ✅ 新增事件类型独立添加
- ✅ 前端对现有事件的处理不受影响

---

## 📋 开发检查清单

在提交代码前,必须通过以下检查:

### Checklist 1: Coze API约束检查

- [ ] 是否使用 `stream()` 方法调用Coze API? (不使用 `post()`)
- [ ] 是否从顶层提取 `type` 和 `content` 字段? (不假设嵌套结构)
- [ ] payload是否包含 `workflow_id` 和 `app_id`?
- [ ] 是否通过 `token_manager.get_access_token()` 获取Token?
- [ ] 是否支持 `session_name` 参数实现会话隔离?

### Checklist 2: 核心接口兼容性检查

- [ ] `/api/chat` 接口是否仍正常工作?
- [ ] `/api/chat/stream` 接口是否仍正常工作?
- [ ] ChatRequest 和 ChatResponse 数据结构是否未改变?
- [ ] SSE 事件格式是否保持一致?

### Checklist 3: 新功能独立性检查

- [ ] 新增功能是否独立于核心功能?
- [ ] 新增功能失败是否会导致AI对话失败?
- [ ] 是否添加了新增接口的测试用例?
- [ ] 状态管理失败是否会阻塞AI响应?

### Checklist 4: 功能测试

```bash
# 测试1: AI对话功能正常
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"你好","user_id":"test_001"}'
# 预期: {"success":true,"message":"...AI回复..."}

# 测试2: 流式对话功能正常
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"你好","user_id":"test_002"}' \
  --no-buffer
# 预期: 实时SSE流 data: {"type":"message","content":"..."}\n\n

# 测试3: 会话隔离正常
curl -X POST http://localhost:8000/api/chat \
  -d '{"message":"记住我叫张三","user_id":"user_001"}'
curl -X POST http://localhost:8000/api/chat \
  -d '{"message":"我叫什么？","user_id":"user_002"}'
# 预期: user_002的回复不应包含"张三"

# 测试4: 人工接管状态下AI被阻止 (新增)
curl -X POST http://localhost:8000/api/manual/escalate \
  -d '{"session_name":"test_003","reason":"user_request"}'
curl -X POST http://localhost:8000/api/chat \
  -d '{"message":"你好","user_id":"test_003"}'
# 预期: HTTP 409, detail包含"SESSION_IN_MANUAL_MODE"
```

---

## 🎯 总结

### 核心原则

1. **Coze API调用部分 = 不可变区域**
   - 使用 `stream()` 方法
   - 解析顶层 `type` 和 `content`
   - 包含必需参数 `workflow_id`, `app_id`
   - 通过 `token_manager` 获取Token
   - 支持 `session_name` 隔离

2. **本地业务逻辑 = 自由设计区域**
   - SessionState 状态管理
   - Regulator 监管引擎
   - 人工接管API
   - SSE队列推送

3. **扩展策略 = 前置检查 + 后置处理**
   - ✅ 在现有接口前添加状态检查
   - ✅ 在现有流程后添加额外逻辑
   - ❌ 不修改核心Coze API调用
   - ❌ 不改变现有数据结构

### 违规后果

- **轻度违规**: 代码审查拒绝,要求重构
- **重度违规**: 立即回滚,重新设计

---

## 🧪 验证状态 (2025-11-21)

基于 `docs/核心功能全面验证报告.md` 的测试结果:

### 约束遵守验证结果

| 约束项 | 验证状态 | 测试结果 |
|--------|---------|----------|
| **铁律1: 不可修改核心接口** | ✅ 完全遵守 | Coze API 调用逻辑未改变，同步/流式接口均正常 |
| **铁律2: Coze API 调用规范** | ✅ 完全遵守 | SSE 流式响应、事件解析格式完全符合规范 |
| **铁律3: OAuth+JWT 鉴权** | ✅ 完全遵守 | 会话隔离机制正常，session_name 正确传递 |
| **P0-1: AI对话阻止逻辑** | ✅ 验证通过 | pending_manual 和 manual_live 状态正确返回 HTTP 409 |
| **P0-2: 坐席接入API** | ✅ 验证通过 | 防抢单逻辑正常，状态转换正确 |
| **P0-3: 会话列表API** | ✅ 验证通过 | 查询、过滤、分页功能正常 |

**总体通过率**: 15/15 测试通过 (100%)

**系统状态**: 🎉 生产可用 (Production Ready)

---

## 📝 开发过程中的新发现约束

### 约束4: EscalationReason 枚举值强制验证

**发现日期**: 2025-11-21
**问题**: 测试中发现 `POST /api/manual/escalate` 使用非枚举值 `reason: "test"` 会导致 HTTP 500 错误

**强制约束**:
```python
# ✅ 正确 - 必须使用枚举值
class EscalationReason(str, Enum):
    KEYWORD = "keyword"       # 关键词触发
    FAIL_LOOP = "fail_loop"   # AI连续失败
    SENTIMENT = "sentiment"   # 情绪检测
    VIP = "vip"               # VIP用户
    MANUAL = "manual"         # 手动请求

# ❌ 错误 - 使用自定义字符串
{"reason": "test"}           # 会导致验证失败
{"reason": "user_request"}   # 会导致验证失败
```

**正确用法**:
```bash
# 用户主动请求人工
curl -X POST /api/manual/escalate \
  -d '{"session_name":"session_123","reason":"manual"}'

# 关键词触发
curl -X POST /api/manual/escalate \
  -d '{"session_name":"session_123","reason":"keyword"}'
```

**验证代码位置**: `tests/test_核心功能验证.py:305`

---

### 约束5: 会话隔离的正确实现方式 ⭐

**发现日期**: 2025-11-21
**问题**: 初始测试显示会话隔离失败，Session B 知道了 Session A 的信息

**根本原因**: 未遵循 Coze 平台的正确实现方式 - **必须在打开页面时立即调用 `/api/conversation/new`**

**强制约束**:

```python
# ❌ 错误 - 直接发送消息（依赖 Coze 自动生成 conversation_id）
POST /api/chat
{
  "message": "记住，我是张三",
  "user_id": "session_a"
  # 缺少 conversation_id，会导致 Coze 可能复用其他 conversation
}

# ✅ 正确 - 预先创建独立的 conversation_id
# 步骤1: 打开页面时立即创建 conversation
POST /api/conversation/new
{"session_id": "session_a"}
# 响应: {"conversation_id": "7574681165306363909"}

# 步骤2: 携带 conversation_id 发送消息
POST /api/chat
{
  "message": "记住，我是张三",
  "user_id": "session_a",
  "conversation_id": "7574681165306363909"  # 关键！
}
```

**实际验证结果**:
```
Session A conversation_id: 7574681165306363909
Session B conversation_id: 7574686112397737989
✅ 两个 conversation_id 不同，隔离生效

Session A 记得: "你是张三啊，记住了哈..."
Session B 不知道: "你是那个在找fiido骑行乐趣的杨子豪呗..."
✅ 会话完全隔离
```

**前端实现要求**:

```typescript
// Vue 3 前端实现示例
export const useChatStore = defineStore('chat', () => {
  const conversationId = ref<string>('')

  // 初始化时立即创建 conversation
  async function initConversation() {
    const response = await fetch('/api/conversation/new', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId.value })
    })
    const data = await response.json()
    conversationId.value = data.conversation_id
  }

  // 组件挂载时调用
  onMounted(async () => {
    await initConversation()
  })

  return { conversationId, initConversation }
})
```

**参考文档**:
- `Coze会话隔离最终解决方案.md`
- `docs/核心功能全面验证报告.md` 第2节

**验证代码位置**: `tests/test_核心功能验证.py:143-276`

---

### 约束6: API 路由顺序要求

**发现日期**: 2025-11-21
**问题**: `GET /api/sessions/stats` 返回 404，被 `/api/sessions/{session_name}` 路由捕获

**强制约束**:

```python
# ❌ 错误 - stats 在后面会被 {session_name} 捕获
@app.get("/api/sessions/{session_name}")
async def get_session(session_name: str):
    ...

@app.get("/api/sessions/stats")  # "stats" 被当作 session_name!
async def get_stats():
    ...

# ✅ 正确 - 具体路由必须在参数化路由之前
@app.get("/api/sessions/stats")
async def get_stats():
    ...

@app.get("/api/sessions/{session_name}")
async def get_session(session_name: str):
    ...
```

**规则**: 所有包含路径参数的路由必须放在最后定义

**验证代码位置**: `backend.py:1183-1218` (stats路由已移至正确位置)

---

## 🔐 生产环境安全约束

### 约束7: 敏感信息处理

**强制要求**:
```python
# ❌ 禁止 - 在日志中暴露敏感信息
logger.info(f"User token: {access_token}")
logger.info(f"User ID: {user_id}, Password: {password}")

# ✅ 正确 - 脱敏处理
logger.info(f"User token: {access_token[:10]}...")
logger.info(f"User login: {user_id}")
```

### 约束8: 错误信息处理

**强制要求**:
```python
# ❌ 禁止 - 暴露内部实现细节
raise HTTPException(
    status_code=500,
    detail=f"Database error: {str(db_exception)}"
)

# ✅ 正确 - 返回通用错误信息
raise HTTPException(
    status_code=500,
    detail="Internal server error"
)
# 详细错误记录到日志
logger.error(f"DB error: {str(db_exception)}")
```

---

## 🎨 前端开发约束 (P0-4 至 P0-6 新增)

### 约束9: 前端状态变更规范 ⭐ **P0-6 新增**

**发现日期**: 2025-11-21
**问题**: P0-6 转人工按钮依赖 `canEscalate` 计算属性，该属性依赖 `sessionStatus` 和 `isEscalating` 状态

**强制约束**:
```typescript
// ❌ 错误 - 直接修改状态
sessionStatus.value = 'manual_live'  // 不会触发审计日志，破坏状态机

// ✅ 正确 - 使用状态更新方法
updateSessionStatus('manual_live')  // 触发日志，维护状态机一致性
```

**规则**:
1. **任何修改 `sessionStatus` 必须使用 `updateSessionStatus()` 方法**
2. **不能直接修改 `sessionStatus.value`**
3. **确保 `canEscalate` 计算属性能正确响应**
4. **状态变更必须记录到控制台日志**

**验证代码位置**:
- `frontend/src/stores/chatStore.ts:201-205` (updateSessionStatus 方法)
- `frontend/src/stores/chatStore.ts:94-96` (canEscalate 计算属性)

**依赖关系**:
- `canEscalate` 依赖 `sessionStatus` 和 `isEscalating`
- 转人工按钮依赖 `canEscalate`
- 任何破坏状态一致性的修改会导致按钮禁用逻辑失效

---

### 约束10: 系统消息格式规范 ⭐ **P0-6 新增**

**发现日期**: 2025-11-21
**问题**: P0-6 转人工功能添加系统消息，需要统一格式以保持一致性

**强制约束**:
```typescript
// ❌ 错误 - 格式不一致
chatStore.addMessage({
  id: Date.now().toString(),  // 普通ID
  role: 'system',
  content: '转人工成功',
  timestamp: new Date()
  // 缺少 sender
})

// ✅ 正确 - 标准系统消息格式
chatStore.addMessage({
  id: `system-${Date.now()}`,  // 以 'system-' 开头
  role: 'system',
  content: '正在为您转接人工客服，请稍候...',
  timestamp: new Date(),
  sender: 'System'  // 必须为 'System'
})
```

**规则**:
1. **`role` 必须为 `'system'`**
2. **`id` 必须以 `'system-'` 开头**
3. **`sender` 必须为 `'System'`**
4. **`timestamp` 使用 `new Date()` 对象**
5. **`content` 使用用户友好的中文提示**

**验证代码位置**:
- `frontend/src/components/ChatPanel.vue:150-156` (转人工系统消息)
- `frontend/src/components/ChatPanel.vue:90-97` (分隔线系统消息)

**适用场景**:
- 转人工提示
- 会话分隔线
- 人工接入通知
- 人工结束通知
- 错误提示

---

### 约束11: 用户交互确认规范 ⭐ **P0-6 新增**

**发现日期**: 2025-11-21
**问题**: P0-6 转人工需要用户确认，避免误操作

**强制约束**:
```typescript
// ❌ 错误 - 重要操作无确认
const handleEscalateToManual = async () => {
  // 直接执行，用户可能误点击
  await chatStore.escalateToManual('manual')
}

// ✅ 正确 - 添加用户确认
const handleEscalateToManual = async () => {
  if (!confirm('确定要转接人工客服吗？')) {
    return  // 用户取消
  }
  await chatStore.escalateToManual('manual')
}
```

**规则**:
1. **重要操作（转人工、清空对话、删除数据）必须有用户确认**
2. **使用 `confirm()` 对话框**
3. **用户取消时立即返回，不执行操作**
4. **确认文案清晰明确，告知操作后果**

**验证代码位置**:
- `frontend/src/components/ChatPanel.vue:137-139` (转人工确认)
- `frontend/src/components/ChatPanel.vue:56-58` (新对话确认)

**需要确认的操作**:
- ✅ 转人工 (不可撤销)
- ✅ 新建对话 (清空界面)
- ❌ 清除对话分隔线 (不清空数据，无需确认)
- ❌ 发送消息 (常规操作，无需确认)

---

### 约束12: 计算属性依赖管理 ⭐ **P0-4 新增**

**发现日期**: 2025-11-21
**问题**: 前端引入多个计算属性，相互依赖关系需要明确管理

**强制约束**:
```typescript
// ❌ 错误 - 计算属性循环依赖
const canSendMessage = computed(() => {
  return canEscalate.value && !isLoading.value
})

const canEscalate = computed(() => {
  return canSendMessage.value && sessionStatus.value === 'bot_active'
})

// ✅ 正确 - 依赖基础状态，不相互依赖
const canSendMessage = computed(() => {
  return !isLoading.value &&
         sessionStatus.value !== 'pending_manual' &&
         sessionStatus.value !== 'closed'
})

const canEscalate = computed(() => {
  return sessionStatus.value === 'bot_active' && !isEscalating.value
})
```

**规则**:
1. **计算属性只依赖 ref 状态，不依赖其他计算属性**
2. **避免循环依赖**
3. **保持计算逻辑简单明确**
4. **必要时添加注释说明依赖关系**

**当前依赖图** (P0-4/P0-5/P0-6):
```
基础状态:
├─ sessionStatus (ref)
├─ isEscalating (ref)
├─ isLoading (ref)
├─ agentInfo (ref)
└─ escalationInfo (ref)

计算属性:
├─ isManualMode → sessionStatus
├─ canSendMessage → isLoading, sessionStatus
├─ canEscalate → sessionStatus, isEscalating
├─ statusText → sessionStatus, agentInfo
└─ statusColorClass → sessionStatus
```

**验证代码位置**: `frontend/src/stores/chatStore.ts:72-138`

---

---

## 🧪 会话隔离测试规范

### 约束13: 会话隔离的测试标准 ⭐ **必须遵守**

**核心原则**: 会话隔离以**打开新的前端网页**为判定依据，每个新打开的前端界面代表一个独立用户。

**测试场景定义**:

```
场景定义:
├─ 用户A: 浏览器窗口/标签页 #1
├─ 用户B: 浏览器窗口/标签页 #2
└─ 用户C: 浏览器窗口/标签页 #3 (可选)

判定标准:
- ✅ 每个新窗口/标签页 = 一个新的 session_id
- ✅ 每个 session_id 对应独立的 conversation_id
- ✅ 不同 session_id 之间的上下文完全隔离
```

**标准测试流程**:

```python
# 步骤1: 打开用户A的窗口
# 操作: 在浏览器中打开 http://localhost:5173
# 验证: 控制台显示 "✅ 会话初始化成功, Conversation ID: conv_A"

# 步骤2: 打开用户B的窗口
# 操作: 在新标签页/窗口打开 http://localhost:5173
# 验证: 控制台显示 "✅ 会话初始化成功, Conversation ID: conv_B"
# 验证: conv_B ≠ conv_A

# 步骤3: 用户A发送消息
# 操作: 在窗口A中输入 "我叫张三，今年25岁"
# 验证: AI 回复记住了用户A的信息

# 步骤4: 用户B发送消息
# 操作: 在窗口B中输入 "我叫李四，我是程序员"
# 验证: AI 回复记住了用户B的信息

# 步骤5: 验证用户A的隔离
# 操作: 在窗口A中输入 "我叫什么？我多大了？"
# 期望: AI 回答 "张三、25岁"
# 验证: ✅ 能正确回忆用户A的信息

# 步骤6: 验证用户B的隔离
# 操作: 在窗口B中输入 "我的名字和职业是什么？"
# 期望: AI 回答 "李四、程序员"
# 验证: ✅ 能正确回忆用户B的信息

# 步骤7: 关键验证 - 跨会话隔离
# 操作: 在窗口A中输入 "你知道李四是谁吗？"
# 期望: AI 回答 "不知道" 或 "没有相关信息"
# 验证: ✅ 用户A不应该知道用户B的信息（会话完全隔离）

# 步骤8: 关键验证 - 双向隔离
# 操作: 在窗口B中输入 "你知道张三吗？他多大了？"
# 期望: AI 回答 "不知道" 或 "没有相关信息"
# 验证: ✅ 用户B不应该知道用户A的信息（会话完全隔离）
```

**自动化测试实现** (参考 `tests/test_session_name.py`):

```python
def test_session_isolation():
    """测试会话隔离 - 遵循正确的Coze实现方式"""

    # 1. 模拟用户A打开页面 - 立即创建conversation
    response_A = requests.post(
        f"{BASE_URL}/api/conversation/new",
        json={"session_id": "session_A"}
    )
    conv_A = response_A.json()["conversation_id"]

    # 2. 模拟用户B打开页面 - 立即创建conversation
    response_B = requests.post(
        f"{BASE_URL}/api/conversation/new",
        json={"session_id": "session_B"}
    )
    conv_B = response_B.json()["conversation_id"]

    # 3. 验证 conversation_id 不同
    assert conv_A != conv_B, "Conversation ID 应该不同"

    # 4. 用户A发送信息
    requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": "我叫张三，今年25岁",
            "user_id": "session_A",
            "conversation_id": conv_A
        }
    )

    # 5. 用户B发送信息
    requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": "我叫李四，我是程序员",
            "user_id": "session_B",
            "conversation_id": conv_B
        }
    )

    # 6. 验证用户A记住自己的信息
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": "我叫什么？我多大了？",
            "user_id": "session_A",
            "conversation_id": conv_A
        }
    )
    assert "张三" in response.json()["message"]
    assert "25" in response.json()["message"]

    # 7. 关键验证 - 用户A不知道用户B的信息
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": "你知道李四是谁吗？",
            "user_id": "session_A",
            "conversation_id": conv_A
        }
    )
    # 应该不包含李四的信息
    assert "程序员" not in response.json()["message"]
```

**测试脚本位置**:
- `tests/test_session_name.py` - 完整的会话隔离测试
- `tests/test_simple.py` - 简化版测试

**验证要点**:
1. ✅ **前置条件**: 用户打开页面时立即调用 `/api/conversation/new`
2. ✅ **隔离验证**: 不同窗口的 conversation_id 必须不同
3. ✅ **上下文隔离**: 用户A不应该知道用户B的对话内容
4. ✅ **双向验证**: 用户B也不应该知道用户A的对话内容

**重要说明**:
- 🔴 **禁止**在首次对话时依赖 Coze 自动生成 conversation_id
- ✅ **必须**在页面加载时立即调用 `conversations.create()` API
- ✅ **必须**将返回的 conversation_id 保存并用于后续对话
- 📖 详细方案见: `Coze会话隔离最终解决方案.md`

**测试命令**:

```bash
# 运行会话隔离测试
cd /home/yzh/AI客服/鉴权
python3 tests/test_session_name.py

# 运行简化测试
python3 tests/test_simple.py
```

**测试位置**: `prd/CONSTRAINTS_AND_PRINCIPLES.md:975-1100`

---

**文档维护者**: Claude Code
**最后更新**: 2025-11-21
**文档版本**: v1.3 ⭐ 新增会话隔离测试规范 (约束13)
**审核状态**: ✅ 已完成
**验证状态**: ✅ 生产可用 (15/15 测试通过)
