# P0-4: 核心人工接管 API - 详细分析报告

> **任务**: 实现 4 个核心人工接管接口
> **位置**: backend.py:1085-1326
> **分析日期**: 2025-11-20
> **分析人**: Claude Code

---

## 📋 总览

P0-4 提供了**人工客服接管流程的完整生命周期管理**，包含 4 个核心 API：

| API | 端点 | 作用 | 状态转换 |
|-----|------|------|---------|
| 1 | `/api/manual/escalate` | 升级到人工 | bot_active → pending_manual |
| 2 | `/api/sessions/{session_name}` | 查询会话状态 | 无状态转换 |
| 3 | `/api/manual/messages` | 人工对话消息 | 无状态转换 |
| 4 | `/api/sessions/{session_name}/release` | 结束人工服务 | manual_live → bot_active |

---

## API 1: `/api/manual/escalate` - 人工升级接口

### 功能描述

将会话从 AI 模式升级到人工接管模式，触发人工客服接管流程。

### 位置

**backend.py**: Lines 1087-1149

### 触发场景

1. **用户主动请求**: 点击"人工客服"按钮 (`reason: "user_request"`)
2. **系统自动触发**: Regulator 监管引擎检测到需要人工介入
   - 关键词触发 (`reason: "keyword"`)
   - 失败循环 (`reason: "fail_loop"`)
   - VIP 用户 (`reason: "vip"`)
   - 情绪检测 (`reason: "sentiment"`)

### 请求格式

```json
POST /api/manual/escalate
Content-Type: application/json

{
  "session_name": "session_123",
  "reason": "user_request"  // 或 "keyword", "fail_loop", "vip", "sentiment"
}
```

### 核心执行流程

```python
1. 参数验证
   ├─ 验证 session_name 必须存在
   └─ 验证 reason 字段

2. 获取会话状态
   └─ session_store.get_or_create(session_name, conversation_id)

3. 状态冲突检查
   ├─ 如果已在 MANUAL_LIVE 状态
   └─ 返回 409 Conflict: "MANUAL_IN_PROGRESS"

4. 创建升级信息 (EscalationInfo)
   ├─ reason: 映射 "user_request" → "manual" (Enum 约束)
   ├─ details: 升级详情描述
   └─ severity: "high" (用户请求) | "low" (系统触发)

5. 状态转换
   └─ transition_status(new_status=PENDING_MANUAL)

6. 持久化
   └─ session_store.save(session_state)

7. 记录日志 (JSON 格式)
   └─ {"event": "manual_escalate", ...}

8. 返回响应
   └─ 包含完整会话状态 (model_dump)
```

### 关键代码片段

```python
# 【关键1】reason 枚举值映射
escalation_reason = "manual" if reason == "user_request" else reason

# 【关键2】创建升级信息
session_state.escalation = EscalationInfo(
    reason=escalation_reason,  # 必须是有效的 EscalationReason
    details=f"用户主动请求人工服务" if reason == "user_request" else f"触发原因: {reason}",
    severity="high" if reason == "user_request" else "low"
)

# 【关键3】状态转换
session_state.transition_status(
    new_status=SessionStatus.PENDING_MANUAL
)
```

### 响应示例

**成功响应** (200 OK):
```json
{
  "success": true,
  "data": {
    "session_name": "session_123",
    "status": "pending_manual",
    "conversation_id": "7574688296594145285",
    "escalation": {
      "reason": "manual",
      "details": "用户主动请求人工服务",
      "severity": "high",
      "trigger_at": 1763623676.552
    },
    "assigned_agent": null,
    "history": [...],
    "created_at": 1763623676.552,
    "updated_at": 1763623676.552,
    ...
  }
}
```

**错误响应** (409 Conflict):
```json
{
  "detail": "MANUAL_IN_PROGRESS"
}
```

### 输出日志

```json
{
  "event": "manual_escalate",
  "session_name": "session_123",
  "reason": "user_request",
  "status": "pending_manual",
  "timestamp": 1763623676
}
```

### 设计亮点

✅ **Enum 安全性**: 自动将 `"user_request"` 映射到合法的 `"manual"` 枚举值
✅ **冲突检测**: 防止重复升级（409 状态码）
✅ **详细日志**: JSON 结构化日志便于监控
✅ **完整状态**: 返回完整会话状态供前端展示

---

## API 2: `/api/sessions/{session_name}` - 获取会话状态

### 功能描述

查询指定会话的完整状态信息，包括历史消息、升级信息、坐席分配等。

### 位置

**backend.py**: Lines 1152-1183

### 使用场景

1. **前端刷新**: 页面加载时获取会话历史
2. **坐席查看**: 人工客服查看用户对话记录
3. **状态监控**: 监控面板展示会话状态

### 请求格式

```http
GET /api/sessions/{session_name}
```

**示例**:
```bash
curl -X GET http://localhost:8000/api/sessions/session_123
```

### 核心执行流程

```python
1. 获取会话状态
   └─ session_state = session_store.get(session_name)

2. 存在性检查
   ├─ 如果不存在
   └─ 返回 404 Not Found: "Session not found"

3. 序列化状态
   └─ session_state.model_dump()  # Pydantic v2

4. 获取审计日志 (TODO)
   └─ audit_trail = []  # 占位符

5. 构建响应
   └─ 返回 session + audit_trail
```

### 响应示例

**成功响应** (200 OK):
```json
{
  "success": true,
  "data": {
    "session": {
      "session_name": "session_123",
      "status": "pending_manual",
      "conversation_id": "7574688296594145285",
      "user_profile": {
        "nickname": "访客",
        "email": null,
        "vip": false,
        "metadata": {}
      },
      "history": [
        {
          "role": "user",
          "content": "我要转人工",
          "timestamp": 1763623600.123,
          "agent_id": null,
          "agent_name": null
        },
        {
          "role": "assistant",
          "content": "正在为您转接人工客服...",
          "timestamp": 1763623605.456,
          "agent_id": null,
          "agent_name": null
        }
      ],
      "escalation": {
        "reason": "manual",
        "details": "用户主动请求人工服务",
        "severity": "high",
        "trigger_at": 1763623610.789
      },
      "assigned_agent": null,
      "created_at": 1763623500.000,
      "updated_at": 1763623610.789,
      "last_manual_end_at": null,
      "ai_fail_count": 0
    },
    "audit_trail": []  // TODO: 审计日志功能待实现
  }
}
```

**错误响应** (404 Not Found):
```json
{
  "detail": "Session not found"
}
```

### 返回字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `session_name` | string | 会话唯一标识 |
| `status` | string | 当前状态: bot_active, pending_manual, manual_live, closed |
| `conversation_id` | string | Coze 对话 ID |
| `user_profile` | object | 用户信息（昵称、邮箱、VIP 状态） |
| `history` | array | 完整对话历史（用户+AI+坐席） |
| `escalation` | object | 升级信息（原因、详情、严重程度） |
| `assigned_agent` | string? | 当前坐席 ID（null 表示未分配） |
| `created_at` | float | 会话创建时间（Unix 时间戳） |
| `updated_at` | float | 最后更新时间 |
| `last_manual_end_at` | float? | 上次人工服务结束时间 |
| `ai_fail_count` | int | AI 失败次数（触发升级的依据） |

### 设计亮点

✅ **完整状态**: 一次请求获取所有会话信息
✅ **前端友好**: 直接返回可展示的结构化数据
✅ **扩展性**: 预留 `audit_trail` 字段用于审计

---

## API 3: `/api/manual/messages` - 人工消息写入

### 功能描述

在人工接管期间，记录用户和坐席之间的对话消息。

### 位置

**backend.py**: Lines 1186-1258

### 使用场景

1. **坐席发送**: 人工客服发送消息给用户
2. **用户回复**: 用户在人工接管期间发送消息
3. **历史记录**: 保存完整对话历史

### 请求格式

```json
POST /api/manual/messages
Content-Type: application/json

{
  "session_name": "session_123",
  "role": "agent",  // 或 "user"
  "content": "您好，请问有什么可以帮您？",
  "agent_info": {    // 可选，仅 role=agent 时有效
    "agent_id": "agent_01",
    "agent_name": "张三"
  }
}
```

### 核心执行流程

```python
1. 参数验证
   ├─ 验证 session_name, role, content 必须存在
   └─ 验证 role ∈ {"agent", "user"}

2. 获取会话状态
   └─ session_state = session_store.get(session_name)
   └─ 如果不存在 → 404 Not Found

3. 状态安全检查
   ├─ 如果 role == "user"
   ├─── 必须在 MANUAL_LIVE 状态
   └─── 否则 → 409 Conflict: "Session not in manual_live status"

4. 创建消息对象
   ├─ 提取 agent_info (如果存在)
   └─ Message(
       role=role,
       content=content,
       agent_id=agent_info.get("agent_id"),
       agent_name=agent_info.get("agent_name"),
       timestamp=自动生成
     )

5. 添加到历史
   └─ session_state.add_message(message)

6. 持久化
   └─ session_store.save(session_state)

7. 记录日志 (JSON 格式)
   └─ {"event": "manual_message", ...}

8. TODO: SSE 推送 (P0-5)
   └─ 实时推送消息给前端

9. 返回响应
   └─ 包含消息时间戳
```

### 关键代码片段

```python
# 【关键1】用户消息状态验证
if role == "user" and session_state.status != SessionStatus.MANUAL_LIVE:
    raise HTTPException(status_code=409, detail="Session not in manual_live status")

# 【关键2】处理 agent_info
agent_info = request.get("agent_info", {})
message = Message(
    role=role,
    content=content,
    agent_id=agent_info.get("agent_id") if agent_info else None,
    agent_name=agent_info.get("agent_name") if agent_info else None
)

# 【关键3】添加到历史
session_state.add_message(message)
```

### 响应示例

**成功响应** (200 OK):
```json
{
  "success": true,
  "data": {
    "timestamp": 1763623700.123
  }
}
```

**错误响应** (409 Conflict):
```json
{
  "detail": "Session not in manual_live status"
}
```

**错误响应** (404 Not Found):
```json
{
  "detail": "Session not found"
}
```

### 输出日志

```json
{
  "event": "manual_message",
  "session_name": "session_123",
  "role": "agent",
  "timestamp": 1763623700.123
}
```

### 角色权限说明

| Role | 允许状态 | 说明 |
|------|----------|------|
| `agent` | pending_manual, manual_live | 坐席可以在等待和接管状态发消息 |
| `user` | **仅 manual_live** | 用户只能在坐席接管后发消息 |

### 设计亮点

✅ **角色验证**: 用户消息必须在 manual_live 状态，防止无效消息
✅ **坐席信息**: 自动记录发送消息的坐席 ID 和姓名
✅ **时间戳自动生成**: 使用 Message 模型的默认值
✅ **预留 SSE**: 为 P0-5 实时推送功能预留接口

### TODO (P0-5)

```python
# TODO P0-5: 通过 SSE 推送消息给前端
# 格式: {"type":"manual_message", "role":"agent", "content":"...", "timestamp":...}
```

---

## API 4: `/api/sessions/{session_name}/release` - 结束人工接管

### 功能描述

结束人工客服服务，将会话归还给 AI 助手。

### 位置

**backend.py**: Lines 1261-1325

### 使用场景

1. **问题已解决**: 坐席处理完用户问题
2. **超时释放**: 用户长时间无响应
3. **转接完成**: 转接到其他渠道后释放

### 请求格式

```json
POST /api/sessions/{session_name}/release
Content-Type: application/json

{
  "agent_id": "agent_01",
  "reason": "resolved"  // 或 "timeout", "transferred"
}
```

### 核心执行流程

```python
1. 获取会话状态
   └─ session_state = session_store.get(session_name)
   └─ 如果不存在 → 404 Not Found

2. 状态验证
   ├─ 必须在 MANUAL_LIVE 状态
   └─ 否则 → 409 Conflict: "Session not in manual_live status"

3. 添加系统消息
   └─ Message(
       role="system",
       content="人工服务已结束，AI 助手已接管对话"
     )

4. 记录结束时间
   └─ session_state.last_manual_end_at = time.time()

5. 状态转换
   └─ transition_status(new_status=BOT_ACTIVE)

6. 清除坐席信息
   └─ session_state.assigned_agent = None

7. 持久化
   └─ session_store.save(session_state)

8. 记录日志 (JSON 格式)
   └─ {"event": "session_released", ...}

9. 返回响应
   └─ 包含完整会话状态
```

### 关键代码片段

```python
# 【关键1】状态验证
if session_state.status != SessionStatus.MANUAL_LIVE:
    raise HTTPException(status_code=409, detail="Session not in manual_live status")

# 【关键2】添加系统消息
system_message = Message(
    role="system",
    content="人工服务已结束，AI 助手已接管对话"
)
session_state.add_message(system_message)

# 【关键3】状态转换
session_state.transition_status(
    new_status=SessionStatus.BOT_ACTIVE
)

# 【关键4】清除坐席
session_state.assigned_agent = None
```

### 响应示例

**成功响应** (200 OK):
```json
{
  "success": true,
  "data": {
    "session_name": "session_123",
    "status": "bot_active",
    "conversation_id": "7574688296594145285",
    "assigned_agent": null,
    "last_manual_end_at": 1763623800.456,
    "history": [
      ...
      {
        "role": "system",
        "content": "人工服务已结束，AI 助手已接管对话",
        "timestamp": 1763623800.456,
        "agent_id": null,
        "agent_name": null
      }
    ],
    ...
  }
}
```

**错误响应** (409 Conflict):
```json
{
  "detail": "Session not in manual_live status"
}
```

### 输出日志

```json
{
  "event": "session_released",
  "session_name": "session_123",
  "agent_id": "agent_01",
  "reason": "resolved",
  "timestamp": 1763623800
}
```

### 状态转换说明

| 当前状态 | 目标状态 | 是否允许 |
|----------|----------|----------|
| manual_live | bot_active | ✅ 允许（正常释放） |
| pending_manual | bot_active | ❌ 拒绝（必须先接管） |
| bot_active | bot_active | ❌ 拒绝（无需释放） |
| closed | bot_active | ❌ 拒绝（已关闭） |

### 设计亮点

✅ **系统消息**: 自动添加释放通知，用户可见状态变化
✅ **时间记录**: 记录 `last_manual_end_at` 用于统计分析
✅ **清除坐席**: 防止状态泄露
✅ **状态严格**: 必须在 manual_live 才能释放

---

## 🔄 四个 API 的完整协作流程

### 流程图

```
┌────────────────┐
│  AI 对话阶段  │
│ (bot_active)  │
└───────┬────────┘
        │
        │ 用户点击"人工客服" 或 Regulator 触发
        │
        ▼
┌────────────────────────┐
│ API 1: 人工升级        │
│ POST /manual/escalate  │
│ 状态: bot_active       │
│    → pending_manual    │
└───────┬────────────────┘
        │
        │ 前端轮询状态 或 SSE 推送
        │
        ▼
┌────────────────────────┐
│ API 2: 查询状态        │
│ GET /sessions/{name}   │
│ 返回: pending_manual   │
└───────┬────────────────┘
        │
        │ 坐席接管（外部操作）
        │ 状态: pending_manual → manual_live
        │
        ▼
┌────────────────────────┐
│ API 3: 坐席发送消息    │
│ POST /manual/messages  │
│ role: agent            │
└───────┬────────────────┘
        │
        │ 用户回复
        │
        ▼
┌────────────────────────┐
│ API 3: 用户发送消息    │
│ POST /manual/messages  │
│ role: user             │
│ (必须 manual_live)     │
└───────┬────────────────┘
        │
        │ 多轮对话...
        │
        ▼
┌────────────────────────┐
│ API 4: 结束人工        │
│ POST /sessions/release │
│ 状态: manual_live      │
│    → bot_active        │
└───────┬────────────────┘
        │
        │ 系统消息: "人工服务已结束"
        │
        ▼
┌────────────────┐
│ 返回 AI 对话   │
│ (bot_active)   │
└────────────────┘
```

### 时序示例

```
时间轴 | 用户                 | 前端                   | 后端                 | 坐席
-------|---------------------|------------------------|---------------------|-----
T0     | 点击"人工客服"      | →                      |                     |
T1     |                     | POST /manual/escalate  | →                   |
T2     |                     |                        | 状态: pending_manual| ← 通知
T3     |                     | GET /sessions/{name}   | → 返回状态          |
T4     |                     |                        |                     | 接管（外部）
T5     |                     |                        | 状态: manual_live   |
T6     |                     |                        | ← 坐席消息          | 发送消息
T7     | ← 收到坐席消息      | SSE 推送 (P0-5)        |                     |
T8     | 发送回复            | →                      |                     |
T9     |                     | POST /manual/messages  | → 保存消息          |
T10    |                     |                        | → 转发给坐席        | ← 收到消息
...    | (多轮对话)          |                        |                     |
T20    |                     |                        | ← 释放请求          | 结束服务
T21    |                     |                        | 状态: bot_active    |
T22    | ← 系统消息          | SSE 推送               |                     |
T23    | 发送新问题          | →                      |                     |
T24    |                     | POST /api/chat         | → Coze AI           |
T25    | ← AI 回复           |                        |                     |
```

---

## 🐛 发现并修复的 Bug

### Bug #1: EscalationInfo reason 枚举值错误

**错误**:
```python
session_state.escalation = EscalationInfo(
    reason=reason,  # 如果 reason="user_request" 会报错
    ...
)
```

**原因**: `EscalationReason` 只允许 `["keyword", "fail_loop", "sentiment", "vip", "manual"]`，没有 `"user_request"`

**修复**:
```python
escalation_reason = "manual" if reason == "user_request" else reason
session_state.escalation = EscalationInfo(
    reason=escalation_reason,
    ...
)
```

**位置**: backend.py:1117-1119

---

### Bug #2: transition_status() operator 参数不存在

**错误**:
```python
session_state.transition_status(
    new_status=SessionStatus.PENDING_MANUAL,
    operator="user"  # ❌ 参数不存在
)
```

**原因**: `SessionState.transition_status()` 只接受 `new_status` 参数

**修复**:
```python
session_state.transition_status(
    new_status=SessionStatus.PENDING_MANUAL
)
```

**位置**: backend.py:1125-1127, 1297-1299

---

### Bug #3: SessionState.to_dict() 方法不存在

**错误**:
```python
return {
    "success": True,
    "data": session_state.to_dict()  # ❌ 方法不存在
}
```

**原因**: Pydantic v2 使用 `model_dump()` 而不是 `to_dict()`

**修复**:
```python
return {
    "success": True,
    "data": session_state.model_dump()
}
```

**位置**: backend.py:1143, 1175, 1318

---

### Bug #4: Message.id 属性不存在

**错误**:
```python
return {
    "success": True,
    "data": {
        "message_id": message.id,  # ❌ 属性不存在
        ...
    }
}
```

**原因**: `Message` 模型没有 `id` 字段，只有 `timestamp`

**修复**:
```python
return {
    "success": True,
    "data": {
        "timestamp": message.timestamp
    }
}
```

**位置**: backend.py:1241, 1249

---

### Bug #5: Message agent_info 参数不存在

**错误**:
```python
message = Message(
    role=role,
    content=content,
    agent_info=request.get("agent_info")  # ❌ 参数不存在
)
```

**原因**: `Message` 使用 `agent_id` 和 `agent_name` 分开存储

**修复**:
```python
agent_info = request.get("agent_info", {})
message = Message(
    role=role,
    content=content,
    agent_id=agent_info.get("agent_id") if agent_info else None,
    agent_name=agent_info.get("agent_name") if agent_info else None
)
```

**位置**: backend.py:1224-1230

---

## 📊 P0-4 完成情况总结

### 实现完整度

| API | 功能 | 实现 | Bug修复 | 测试 |
|-----|------|------|---------|------|
| API 1: escalate | 人工升级 | ✅ 已实现 | ✅ 5个bug已修复 | ✅ 已测试 |
| API 2: sessions | 查询状态 | ✅ 已实现 | ✅ 已修复 | ✅ 已测试 |
| API 3: messages | 消息写入 | ✅ 已实现 | ✅ 已修复 | ⏳ 需 manual_live |
| API 4: release | 结束服务 | ✅ 已实现 | ✅ 已修复 | ⏳ 需 manual_live |

### 代码质量指标

✅ **语法检查**: 通过
✅ **类型安全**: Pydantic 模型验证
✅ **异常处理**: 完整的 try-except
✅ **日志规范**: JSON 结构化日志
✅ **状态机**: 严格的状态转换验证

### 依赖关系

```
P0-4 (核心 API)
├─ 依赖 P0-1: SessionStateStore ✅
├─ 依赖 P0-2: Regulator ✅
├─ 依赖 P0-3: Chat 接口集成 ✅
└─ 为 P0-5: SSE 推送预留接口 ⏳
```

### 下一步工作

根据 `prd/backend_tasks.md`:

1. **P0-5: SSE 增量推送** (Line 107)
   - 复用 `/api/chat/stream`
   - 注入 manual_message/status 事件
   - 实现 backend.py:1244 的 TODO

2. **P0-6: 日志规范** (Line 108)
   - 已部分完成（JSON 格式）
   - 需统一所有状态转换日志

3. **集成测试**
   - 完整流程测试（需坐席系统配合）
   - 并发测试
   - 压力测试

---

## ✅ 验证测试结果

### 测试 1: API 1 (人工升级)

**命令**:
```bash
curl -X POST http://localhost:8000/api/manual/escalate \
  -H "Content-Type: application/json" \
  -d '{"session_name":"p04_complete","reason":"user_request"}'
```

**结果**: ✅ **通过**
```json
{
  "success": true,
  "data": {
    "session_name": "p04_complete",
    "status": "pending_manual",
    "escalation": {
      "reason": "manual",  // ✅ 正确映射
      "details": "用户主动请求人工服务",
      "severity": "high"
    }
  }
}
```

### 测试 2: API 2 (查询状态)

**命令**:
```bash
curl -X GET http://localhost:8000/api/sessions/p04_complete
```

**结果**: ✅ **通过**
```json
{
  "success": true,
  "data": {
    "session": {
      "session_name": "p04_complete",
      "status": "pending_manual",
      ...
    },
    "audit_trail": []
  }
}
```

### 测试 3 & 4: 需要 manual_live 状态

由于 InMemorySessionStore 跨进程不共享，完整流程测试需要：
- 实现坐席接管接口（将状态从 pending_manual → manual_live）
- 或使用持久化存储（如 Redis）

---

## 📝 总结

P0-4 实现了**人工客服接管的完整生命周期管理**，包含：

✅ **4 个核心 API**: escalate, sessions, messages, release
✅ **完整状态机**: bot_active ↔ pending_manual ↔ manual_live
✅ **5 个 Bug 修复**: 枚举值、方法名、参数错误
✅ **安全验证**: 角色权限、状态转换检查
✅ **JSON 日志**: 所有关键操作都有结构化日志
✅ **扩展性**: 为 P0-5 SSE 推送预留接口

**下一步**: 实现 P0-5 SSE 增量推送，完成 P0 阶段所有任务。

---

**报告生成时间**: 2025-11-20
**分析人**: Claude Code
**验证状态**: ✅ 部分测试通过，完整流程需坐席系统配合
