# Fiido AI 客服系统 - Claude 开发全局指导准则

> **文档版本**: v1.0
> **创建日期**: 2025-11-20
> **文档性质**: 🔴 **全局开发准则** - 所有开发工作必须遵守
> **适用对象**: Claude Code AI 开发助手

---

## 📜 文档目的

本文档汇总了 Fiido AI 客服系统开发过程中必须遵守的所有约束、规则、限制、要求和标准，作为后续所有开发工作的全局性参考和指导准则。

**核心原则**：
1. 保证 Coze 平台 API 调用的基本功能可用（会话隔离、动态 conversation_id 等）
2. 不破坏现有功能，只允许安全扩展
3. 严格遵守技术约束，避免引入风险

---

## 🎯 第一优先级：Coze API 核心功能必须可用

### 🔴 会话隔离机制（最高优先级）

**关键文档**: `Coze会话隔离最终解决方案.md`、`prd/coze.md` 第 1.1 节

#### 核心要求

**✅ 必须实现**：
1. **用户打开页面时立即创建会话**：
   ```python
   # 前端加载时或后端首次接触新 session 时，立即调用
   conversation = coze_client.conversations.create()
   conversation_cache[session_id] = conversation.id
   ```

2. **禁止依赖首次对话时自动生成**：
   ```python
   # ❌ 错误方式 - 会导致多用户共享同一 conversation_id
   if not conversation_id:
       # 依赖 Coze 在对话响应中返回 conversation_id
       pass

   # ✅ 正确方式 - 提前创建
   if not conversation_id:
       conversation = coze_client.conversations.create()
       conversation_cache[session_id] = conversation.id
   ```

3. **session_name 必须在两处传递**：
   - JWT Token payload 中：`jwt_oauth_app.get_access_token(session_name=session_id)`
   - API 请求 payload 中：`{"session_name": session_id}`（如果 API 支持）

#### 验证标准

打开两个浏览器窗口测试：
```bash
# 窗口 1
用户输入: "我是子豪"
AI 回复: "你好，子豪！"

# 窗口 2
用户输入: "我是谁？"
AI 回复: "我不知道你是谁，请告诉我" ← 必须是这个结果！

# ❌ 错误结果
AI 回复: "你是子豪" ← 如果出现这个，说明会话隔离失败
```

---

### 🔴 Conversation ID 动态管理

**关键文档**: `prd/coze.md` 第 1.1 节

#### 核心机制

**Coze SDK 特性**：
- 每次调用 `conversations.create()` 会生成唯一的 conversation_id
- 结合 `session_name` 可实现严格的用户隔离
- 静态会话（如 "default"）仅影响逻辑归属，不改变动态生成特性

#### 实现要求

```python
# ✅ 正确流程
# 1. 用户首次进线时创建会话
token = jwt_oauth_app.get_access_token(
    ttl=3600,
    session_name=session_id  # 会话隔离关键
)
temp_coze = Coze(auth=JWTAuth(token=token), base_url=api_base)
conversation = temp_coze.conversations.create()

# 2. 存储映射关系
conversation_cache[session_id] = conversation.id

# 3. 后续对话传入 conversation_id
payload = {
    "workflow_id": WORKFLOW_ID,
    "app_id": APP_ID,
    "conversation_id": conversation_id,  # 维持上下文
    "additional_messages": [...]
}
```

#### 禁止操作

```python
# ❌ 禁止：手动生成 conversation_id
conversation_id = f"conv_{uuid.uuid4()}"

# ❌ 禁止：跨用户共享 conversation_id
# 每个 session_name 必须有独立的 conversation_id

# ❌ 禁止：修改 Coze 返回的 conversation_id
```

---

## 🛡️ Coze API 技术约束（不可绕过）

**关键文档**: `prd/TECHNICAL_CONSTRAINTS.md`、`prd/coze.md` 第 12 节

### 1. SSE 流式响应（强制）

#### 平台限制

```
端点: POST /v1/workflows/chat
响应格式: Server-Sent Events (SSE) 流
```

#### 代码约束

```python
# ✅ 正确方式
async with async_http_client.stream(
    "POST",
    f"{api_base}/v1/workflows/chat",
    headers=headers,
    json=payload
) as response:
    async for chunk in response.aiter_bytes():
        buffer += chunk.decode('utf-8')
        # 解析 SSE 流...

# ❌ 错误方式 - 禁止使用
response = await async_http_client.post(...)
data = response.json()  # 这会失败！
```

#### SSE 事件解析

```python
# ✅ 正确解析
event_data = json.loads(data_content)
if event_data.get("type") == "answer" and event_data.get("content"):
    message_content += event_data["content"]

# ❌ 错误解析 - Coze 不返回这种结构
if "message" in event_data:
    content = event_data["message"]["content"]
```

---

### 2. OAuth + JWT 鉴权

#### Token 生成

```python
# ✅ 正确方式
jwt_oauth_app = JWTOAuthApp(
    client_id=client_id,
    private_key=private_key,
    public_key_id=public_key_id,
    base_url=api_base
)
token = jwt_oauth_app.get_access_token(
    ttl=3600,
    session_name=session_id  # 必须传入
)

# ❌ 禁止：省略 session_name
token = jwt_oauth_app.get_access_token(ttl=3600)

# ❌ 禁止：跨 session 复用 token
# 每个 session 必须生成独立 token
```

---

### 3. API 请求 Payload 格式

#### 必需字段

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
  ],
  "conversation_id": "可选但强烈推荐",
  "parameters": "可选"
}
```

#### 约束

- ✅ **必须**：提供 `workflow_id` 和 `app_id`
- ✅ **必须**：`additional_messages` 格式严格按上述结构
- ❌ **禁止**：省略 `session_name`（在 Token 中）
- ❌ **禁止**：在 `parameters` 中注入未定义的变量

---

## 🚫 不可修改的核心接口

**关键文档**: `prd/TECHNICAL_CONSTRAINTS.md` 第 4-5 节

### 核心接口清单

以下接口的 **Coze API 调用逻辑** 不可修改：

1. **`/api/chat`** - 非流式 AI 对话
2. **`/api/chat/stream`** - 流式 AI 对话（SSE）
3. **`/api/conversation/new`** - 创建会话

### 允许的扩展方式

```python
# ✅ 允许：前置处理（状态判断）
@app.post("/api/chat")
async def chat_async(request: ChatRequest):
    session_id = request.user_id or generate_session_id()

    # ✅ 允许：新增状态判断
    session_state = session_store.get(session_id)
    if session_state and session_state.status == "manual_live":
        return {"success": False, "error": "MANUAL_IN_PROGRESS"}, 409

    # ✅ 必须保持：原有 Coze API 调用逻辑（不可修改）
    access_token = token_manager.get_access_token(session_name=session_id)
    # ... Coze API 调用代码 ...

    # ✅ 允许：后置处理（监管、日志）
    if session_state:
        regulator_result = regulator.evaluate(...)
        if regulator_result.should_escalate:
            session_store.transition(session_id, "pending_manual")

    return ChatResponse(...)
```

### 禁止的修改

```python
# ❌ 禁止：移除 session_name
access_token = token_manager.get_access_token()

# ❌ 禁止：使用 .post() 替代 .stream()
response = await async_http_client.post(...)

# ❌ 禁止：修改 SSE 解析方式
data = response.json()

# ❌ 禁止：修改返回格式
return {"msg": message_content}  # 必须使用 ChatResponse
```

---

## ✅ 允许自由设计的模块

**关键文档**: `prd/TECHNICAL_CONSTRAINTS.md` 第 9 节、`prd/backend_tasks.md` 第 26-30 行

### 无 Coze 依赖的模块

以下模块**不涉及 Coze API 调用**，可以自由设计：

| 模块 | 文件 | 用途 | 约束级别 |
|------|------|------|---------|
| 会话状态管理 | `src/session_state.py` | SessionState 数据模型和存储 | ✅ 自由设计 |
| 监管策略引擎 | `src/regulator.py` | 关键词/失败/VIP 检测 | ✅ 自由设计 |
| 人工接管 API | 新增接口 | `/api/manual/*`, `/api/sessions/*` | ✅ 自由设计 |
| 邮件通知 | P1 功能 | ShiftConfig、邮件发送 | ✅ 自由设计 |
| 工作台 | P1 功能 | 坐席端界面和 API | ✅ 自由设计 |

### 设计原则

虽然可以自由设计，但仍需遵守：
- ⚠️ 异常不应导致核心 AI 对话功能失败
- ⚠️ 必须通过向后兼容性测试
- ⚠️ 不得占用现有路由
- ⚠️ 不得修改现有模块的行为

---

## 📋 数据模型规范

**关键文档**: `prd/prd.md` 第 8 节

### SessionState 数据模型

```python
{
  "session_name": str,              # 会话唯一标识（即 user_id/sessionId）
  "status": SessionStatus,          # bot_active | pending_manual | manual_live | after_hours_email | closed
  "conversation_id": Optional[str], # Coze Conversation ID

  "user_profile": {
    "nickname": str,
    "vip": bool
  },

  "history": List[Message],         # 最多保留 50 条

  "escalation": Optional[{          # 人工接管信息
    "reason": str,                  # keyword | fail_loop | vip | manual
    "details": str,
    "severity": str,                # low | high
    "trigger_at": float             # UTC timestamp
  }],

  "assigned_agent": Optional[{      # 坐席信息
    "id": str,
    "name": str
  }],

  "mail": Optional[{                # 邮件信息
    "sent": bool,
    "email_to": List[str]
  }],

  "ai_fail_count": int,             # AI 失败计数器
  "created_at": float,              # UTC timestamp
  "updated_at": float,
  "last_manual_end_at": Optional[float]
}
```

### 约束

- ✅ `history` 最多保留 50 条
- ✅ 所有时间字段使用 UTC timestamp（秒）
- ✅ `audit_trail` 另建列表存储，不污染主结构

---

### Message 数据模型

```python
{
  "id": str,
  "role": str,      # user | assistant | system | agent
  "content": str,
  "timestamp": float,  # UTC
  "agent_info": Optional[{  # role='agent' 时有效
    "agent_id": str,
    "agent_name": str
  }]
}
```

---

## 🔧 开发流程与检查清单

**关键文档**: `prd/README.md` 第 4 节

### Step 1: 阅读约束（强制）

```
✅ 阅读 prd/TECHNICAL_CONSTRAINTS.md
✅ 阅读 prd/coze.md 第 12 节
✅ 阅读本文档 (claude.md)
✅ 理解 Coze API 限制
```

### Step 2: 理解需求

```
✅ 阅读 prd/prd.md（整体需求）
✅ 阅读对应的任务文档（backend/frontend/agent/email）
✅ 查看 prd/api_contract.md（接口规范）
```

### Step 3: 开发前检查（强制）

```
✅ 是否涉及 Coze API 调用？
   ├─ 是 → 🔴 必须严格遵守 TECHNICAL_CONSTRAINTS.md
   │        - 不得修改核心接口逻辑
   │        - 必须保持 SSE 流式响应
   │        - 必须保持 session_name 隔离
   │        - 必须使用审查清单
   └─ 否 → ✅ 可自由设计，但需保证：
            - 向后兼容现有功能
            - 异常不影响核心对话
            - 通过测试验证

✅ 是否修改了核心接口（/api/chat, /api/chat/stream）？
   ├─ 是 → 🔴 禁止！必须回到 Step 1 重新理解约束
   └─ 否 → ✅ 继续

✅ 是否通过了强制性测试？
   ├─ 否 → 继续开发和测试
   └─ 是 → ✅ 可以提交代码
```

### Step 4: 代码审查（强制）

使用以下检查清单：

**Coze API 调用检查**：
- [ ] 是否使用 `stream()` 方法调用 Coze API？
- [ ] 是否正确解析 SSE 流格式？
- [ ] payload 是否包含必需的 `workflow_id` 和 `app_id`？
- [ ] 是否支持 `session_name` 参数？
- [ ] Token 是否通过 `OAuthTokenManager` 获取？
- [ ] 是否在用户打开页面时创建 conversation？

**数据结构检查**：
- [ ] 是否从顶层提取 `type` 和 `content` 字段？
- [ ] 是否检查 `type == "answer"` 来识别 AI 回复？
- [ ] 是否检查 `status == "completed"` 来判断结束？
- [ ] 返回的 `ChatResponse` 格式是否保持一致？

**向后兼容性检查**：
- [ ] 现有的 `/api/chat` 接口是否仍然正常工作？
- [ ] 现有的 `/api/chat/stream` 接口是否仍然正常工作？
- [ ] 是否通过了会话隔离测试？

---

## 🧪 强制性测试标准

**关键文档**: `prd/TECHNICAL_CONSTRAINTS.md` 第 10 节

### 测试 1：基础 AI 对话测试

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"你好","user_id":"test_001"}'
```

**通过标准**：
- ✅ `success: true`
- ✅ `message` 包含有效的 AI 回复
- ✅ 响应时间 < 30 秒

---

### 测试 2：流式对话测试

```bash
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

---

### 测试 3：会话隔离测试（最重要）

```bash
# 窗口 1
curl -X POST http://localhost:8000/api/chat \
  -d '{"message":"记住我叫张三","user_id":"user_001"}'

# 窗口 2
curl -X POST http://localhost:8000/api/chat \
  -d '{"message":"我叫什么？","user_id":"user_002"}'
```

**通过标准**：
- ✅ user_002 的回复**不应包含**"张三"
- ✅ 每个用户的对话上下文独立
- ✅ 后端日志显示不同的 conversation_id

---

## 📦 项目结构约定

```
/home/yzh/AI客服/鉴权/
├── backend.py                    # 🔴 核心文件 - 包含 Coze API 调用
├── src/
│   ├── session_state.py          # ✅ 可自由修改 - 无 Coze 依赖
│   ├── regulator.py              # ✅ 可自由修改 - 无 Coze 依赖
│   ├── oauth_token_manager.py    # 🔴 核心模块 - 不可修改
│   └── jwt_signer.py             # 🔴 核心模块 - 不可修改
├── prd/                          # 📘 需求文档（必读）
│   ├── TECHNICAL_CONSTRAINTS.md  # 🔴 最高优先级
│   ├── coze.md                   # 🔴 Coze 约束规范
│   ├── backend_tasks.md          # 📋 后端任务
│   └── api_contract.md           # 📋 API 规范
├── docs/                         # 📚 技术文档
│   ├── Coze会话隔离最终解决方案.md  # 🔴 必读
│   └── 会话隔离实现总结.md
└── .env                          # ⚙️ 环境配置
```

---

## ⚙️ 环境配置规范

### 核心配置（.env）

```bash
# Coze API（不可变）
COZE_API_BASE=https://api.coze.com
COZE_AUTH_MODE=OAUTH_JWT
COZE_WORKFLOW_ID=7568811304438710279
COZE_APP_ID=7568402281331949575

# OAuth（不可变）
COZE_OAUTH_CLIENT_ID=1147548140378
COZE_OAUTH_PUBLIC_KEY_ID=lunGzVer4yes0LLkUW2M4rhMIZJJyvMTKZbnTsjySJs
COZE_OAUTH_PRIVATE_KEY_FILE=./private_key.pem

# 监管引擎（可自由配置）
REGULATOR_KEYWORDS=人工,真人,客服,投诉,无法解决,转人工,接人工
REGULATOR_AI_FAIL_KEYWORDS=抱歉,很抱歉,无法,不清楚,不太清楚,无法回答,不能确定
REGULATOR_FAIL_THRESHOLD=3
REGULATOR_VIP_AUTO_ESCALATE=true

# 会话存储（可自由配置）
SESSION_STATE_BACKUP_FILE=./data/sessions_backup.json
SESSION_MAX_HISTORY=50
```

---

## 🎯 P0 任务优先级

**关键文档**: `prd/backend_tasks.md` 第 100-112 行

### P0（必须完成）

| 优先级 | 模块 | 状态 | 说明 |
|-------|------|------|------|
| P0-1 | SessionStateStore | ✅ 已完成 | session_state.py 已开发 |
| P0-2 | 监管策略引擎 | ✅ 已完成 | regulator.py 已开发 |
| P0-3 | Chat 接口改造 | ⏳ 待开发 | 在 backend.py 中集成状态判断和监管 |
| P0-4 | 核心 API | ⏳ 待开发 | 4 个人工接管接口 |
| P0-5 | SSE 增量推送 | ⏳ 待开发 | 注入 manual_message/status 事件 |
| P0-6 | 日志规范 | ⏳ 待开发 | JSON 格式日志 |

---

## 📝 代码风格与日志规范

### 日志格式

```python
# ✅ 正确的日志格式（JSON 行）
import json
import logging

# 状态转换日志
logging.info(json.dumps({
    "event": "status_transition",
    "session_name": session_id,
    "status_from": old_status,
    "status_to": new_status,
    "operator": operator_id,
    "timestamp": int(time.time())
}, ensure_ascii=False))

# 会话隔离日志
print(f"🔐 会话隔离: session_name={session_id}")
print(f"💬 Conversation ID: {conversation_id}")
```

### 错误处理

```python
# ✅ 正确的错误处理
try:
    conversation = coze_client.conversations.create()
    conversation_cache[session_id] = conversation.id
except Exception as e:
    logging.error(json.dumps({
        "event": "conversation_create_failed",
        "session_name": session_id,
        "error": str(e),
        "timestamp": int(time.time())
    }))
    # ⚠️ 不能让异常影响核心功能
    raise HTTPException(status_code=500, detail="创建会话失败")
```

---

## 🚨 紧急回滚预案

**关键文档**: `prd/coze.md` 第 12.5 节

### 如果发现 Coze API 调用异常

1. **立即检查**：是否修改了 `session_name` 或 `conversation_id` 逻辑
2. **查看日志**：确认 API 请求参数是否完整
3. **回滚代码**：恢复到上一个稳定版本（使用 git）
4. **重新测试**：验证会话隔离功能是否正常

### 回滚命令

```bash
# 查看最近的提交
git log --oneline -5

# 回滚到上一个版本
git reset --hard HEAD~1

# 或回滚到特定提交
git reset --hard <commit-hash>

# 重启服务
python3 backend.py
```

---

## 📚 关键文档索引

### 必读文档（按优先级）

1. **🔴 本文档 (claude.md)** - 全局指导准则
2. **🔴 prd/TECHNICAL_CONSTRAINTS.md** - 技术约束（不可绕过）
3. **🔴 Coze会话隔离最终解决方案.md** - 会话隔离核心方案
4. **🔴 prd/coze.md 第 12 节** - Coze API 约束规范
5. **📘 prd/backend_tasks.md** - 后端任务拆解
6. **📘 prd/api_contract.md** - API 接口规范
7. **📘 prd/prd.md** - 产品需求文档

### 参考文档

- docs/会话隔离实现总结.md - 实现历程
- docs/官方会话隔离实现指南.md - Coze 官方说明
- docs/配置指南.md - 环境配置
- docs/MODULE_REVIEW_REPORT.md - 模块审查报告

---

## 🎓 开发最佳实践

### 1. 开发新功能前

```bash
# 1. 阅读本文档
cat claude.md

# 2. 确认是否涉及 Coze API
# 如涉及，必须阅读：
cat prd/TECHNICAL_CONSTRAINTS.md
cat prd/coze.md

# 3. 查看对应任务文档
cat prd/backend_tasks.md  # 或其他对应文档
```

### 2. 代码提交前

```bash
# 1. 运行强制性测试
# 测试 1: 基础对话
curl -X POST http://localhost:8000/api/chat \
  -d '{"message":"你好","user_id":"test_001"}'

# 测试 2: 流式对话
curl -X POST http://localhost:8000/api/chat/stream \
  -d '{"message":"你好","user_id":"test_002"}' \
  --no-buffer

# 测试 3: 会话隔离（最重要）
# 在两个终端窗口中分别运行：
curl -X POST http://localhost:8000/api/chat \
  -d '{"message":"记住我叫张三","user_id":"user_001"}'

curl -X POST http://localhost:8000/api/chat \
  -d '{"message":"我叫什么？","user_id":"user_002"}'

# 2. 使用审查清单（见本文档 Step 4）

# 3. 提交代码
git add .
git commit -m "功能描述"
```

### 3. 遇到问题时

```bash
# 1. 检查日志
tail -f backend.log

# 2. 查看会话隔离是否正常
grep "🔐 会话隔离" backend.log
grep "conversation_id" backend.log

# 3. 参考解决方案文档
cat Coze会话隔离最终解决方案.md

# 4. 如无法解决，回滚代码
git reset --hard HEAD~1
```

---

## 🔗 相关资源

### Coze 官方文档

- [Workflow Chat API](https://www.coze.com/docs/developer_guides/workflow_chat)
- [OAuth JWT 认证](https://www.coze.com/docs/developer_guides/oauth_jwt)
- [会话隔离](https://www.coze.com/docs/developer_guides/session_isolation)

### 项目仓库

- GitHub: (待填写)
- 文档中心: `/home/yzh/AI客服/鉴权/prd/`

---

**最后更新**: 2025-11-20
**维护者**: 开发团队
**联系方式**: (待填写)

---

## 📌 快速参考卡片

```
┌─────────────────────────────────────────────────────────────┐
│  🔴 最高优先级：Coze API 核心功能必须可用                   │
├─────────────────────────────────────────────────────────────┤
│  ✅ 用户打开页面时立即创建会话（conversations.create()）    │
│  ✅ 禁止依赖首次对话时自动生成 conversation_id              │
│  ✅ session_name 必须在 JWT 和 API 请求中传递               │
│  ✅ 会话隔离测试必须通过                                    │
├─────────────────────────────────────────────────────────────┤
│  🔴 不可修改的核心接口                                      │
├─────────────────────────────────────────────────────────────┤
│  /api/chat                  - 非流式 AI 对话                │
│  /api/chat/stream           - 流式 AI 对话（SSE）           │
│  /api/conversation/new      - 创建会话                      │
├─────────────────────────────────────────────────────────────┤
│  ✅ 允许自由设计的模块                                      │
├─────────────────────────────────────────────────────────────┤
│  src/session_state.py       - 会话状态管理                  │
│  src/regulator.py           - 监管策略引擎                  │
│  /api/manual/*              - 人工接管接口（新增）          │
│  /api/sessions/*            - 会话管理接口（新增）          │
└─────────────────────────────────────────────────────────────┘
```

