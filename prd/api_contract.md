# AI 监管/人工接管 API Contract (v2.2)

## ⚠️ Coze API 强制约束

**本文档中的所有 API 接口必须遵守以下 Coze 平台约束**：

### 🔴 核心约束声明

#### 1. 不可修改的核心接口（涉及 Coze API）

以下接口**直接调用 Coze API**，其核心逻辑**不可修改**，只能扩展：

| 接口 | Coze 依赖 | 约束级别 | 说明 |
|------|-----------|----------|------|
| `POST /api/chat` | ✅ 直接调用 | 🔴 **不可修改** | SSE 流式响应、session_name 隔离必须保持 |
| `POST /api/chat/stream` | ✅ 直接调用 | 🔴 **不可修改** | SSE 事件格式（`type:message/done`）不可变 |
| `POST /api/conversation/new` | ✅ 直接调用 | 🔴 **不可修改** | Conversation ID 生成逻辑必须由 Coze 控制 |

**强制要求**：
- ✅ **必须保持**：SSE 流式响应格式（`event:` 和 `data:` 行）
- ✅ **必须保持**：OAuth+JWT 鉴权流程和 `session_name` 参数
- ✅ **必须保持**：Coze API payload 的必需字段（`workflow_id`, `app_id`, `additional_messages`）
- ❌ **禁止修改**：Coze API 响应的解析逻辑（从顶层提取 `type` 和 `content` 字段）

**参考文档**：
- 📘 [TECHNICAL_CONSTRAINTS.md](./TECHNICAL_CONSTRAINTS.md) - 第 2-5 节（Coze 平台限制）
- 📘 [coze.md](./coze.md) - 第 12 节（Coze API 约束规范）

#### 2. 允许扩展的新接口（不涉及 Coze API）

以下接口是**新增功能**，不直接调用 Coze API，可以自由设计：

| 接口 | Coze 依赖 | 约束级别 | 说明 |
|------|-----------|----------|------|
| `POST /api/manual/escalate` | ❌ 无依赖 | ✅ **可自由设计** | 会话状态管理，不影响 Coze API |
| `GET /api/sessions/{session_name}` | ❌ 无依赖 | ✅ **可自由设计** | 本地状态查询 |
| `POST /api/manual/messages` | ❌ 无依赖 | ✅ **可自由设计** | 人工消息通道（通过 SSE 推送） |
| `POST /api/sessions/{session_name}/release` | ❌ 无依赖 | ✅ **可自由设计** | 状态转换逻辑 |

**扩展要求**：
- ⚠️ 新接口的异常不应导致核心 AI 对话功能失败
- ⚠️ 必须在响应格式中明确标注是否涉及 Coze API 调用
- ⚠️ 必须通过向后兼容性测试

#### 3. SSE 流扩展规范

**现有 SSE 事件格式（不可变）**：
```
data: {"type":"message","content":"AI回复内容"}\n\n
data: {"type":"done","content":""}\n\n
```

**允许的扩展（新增事件类型）**：
```
data: {"type":"manual_message","role":"agent","content":"人工回复","agent_info":{...}}\n\n
data: {"type":"status","status":"pending_manual","reason":"keyword"}\n\n
```

**约束**：
- ✅ 允许添加新的 `type` 值（如 `manual_message`, `status`）
- ❌ 禁止修改现有 `type: message` 和 `type: done` 的格式和含义
- ✅ 新事件类型必须向后兼容（不影响只识别 `message/done` 的客户端）

---

本文件在 `PRD_REVIEW.md` 建议的基础上，重新定义需要实现/扩展的接口，确保 MVP（P0）优先交付 4 个核心接口，再在 P1 引入更多能力。

## 通用约定
- **响应格式**：
  ```json
  { "success": true, "data": {...} }
  { "success": false, "error": "错误信息", "code": "ERROR_CODE" }
  ```
- **鉴权**：除用户侧的 `POST /api/manual/escalate`、`POST /api/manual/messages`(role=user) 外，其余接口均需 `Authorization: Bearer <JWT>`，且 JWT 中必须包含 `role` (`agent`/`admin`)。  
- **会话标识**：`session_name` 与前端的 `sessionId` 完全一致。  
- **时间戳**：统一使用 **UTC 秒级时间戳**（数字），前端负责格式化。  
- **History 限制**：仅返回最近 50 条消息，若更多可在后端归档。

## SessionState 数据结构
```json
{
  "session_name": "session_123",
  "status": "bot_active",
  "conversation_id": "conv_xxx",
  "user_profile": {
    "nickname": "访客A",
    "vip": false
  },
  "history": [
    { "id": "msg_1", "role": "user", "content": "你好", "timestamp": 1737000000 },
    { "id": "msg_2", "role": "assistant", "content": "您好！", "timestamp": 1737000001 }
  ],
  "escalation": {
    "reason": "keyword",
    "details": "命中关键词: 人工",
    "severity": "high",
    "trigger_at": 1737000300
  },
  "assigned_agent": { "id": "agent_01", "name": "Alice" },
  "mail": { "sent": false, "email_to": [] },
  "ai_fail_count": 0,
  "last_manual_end_at": null
}
```
> `audit_trail` 单独存储：`[{ "status_from": "...", "status_to": "...", "operator": "...", "timestamp": 1737000400 }]`

---

## P0 核心接口

### 1. `POST /api/manual/escalate`
- **用途**：用户点击“人工客服”或监管触发后调用。  
- **Body**：
  ```json
  { "session_name": "session_123", "reason": "user_request" }
  ```
- **响应**：`data` 返回最新 `SessionState`。  
- **错误**：`409 MANUAL_IN_PROGRESS`（已有人工会话）。

### 2. `GET /api/sessions/{session_name}`
- **用途**：前端刷新会话历史 & 状态。  
- **响应**：
  ```json
  {
    "success": true,
    "data": {
      "session": SessionState,
      "audit_trail": [...]
    }
  }
  ```
- **权限**：用户端/内部系统均可，无需角色鉴权（仅根据 session token）。

### 3. `POST /api/manual/messages`
- **用途**：人工阶段的消息写入（用户/坐席）。  
- **Body**：
  ```json
  {
    "session_name": "session_123",
    "role": "agent" | "user",
    "content": "我要人工"
  }
  ```
- **响应**：`{ "success": true, "data": { "message_id": "uuid", "timestamp": 1737000400 } }`  
- **行为**：写入 `history`，并通过 `/api/chat/stream` SSE 推送 `{"type":"manual_message",...}`。  
- **校验**：`role='user'` 时必须当前状态为 `manual_live`。

### 4. `POST /api/sessions/{session_name}/release`
- **用途**：结束人工，恢复 AI。  
- **Body**：`{ "agent_id": "agent_01", "reason": "resolved" }`  
- **行为**：状态 `manual_live -> bot_active`，追加系统消息“人工结束，AI 已接管”。  
- **响应**：返回最新 `SessionState`。

---

## P1 扩展接口

| 接口 | 描述 | 主要字段 |
| --- | --- | --- |
| `GET /api/sessions` | 工作台队列，支持 `status`, `keyword`, `page`, `page_size` | 返回 `{items:[SessionSummary], total}` |
| `POST /api/sessions/{session_name}/takeover` | 坐席接入 | Body `{agent_id, agent_name}`；CAS 更新 |
| `POST /api/sessions/{session_name}/email` | 非工作时间邮件转交 | Body `{force?:boolean}`，响应 `{mail_id}` |
| `GET /api/shift/config` | 工作时间配置 | 数据 `{start,end,timezone,weekends_disabled,holidays}` |

`SessionSummary` 推荐字段：`session_name`, `status`, `escalation`, `waiting_seconds`, `assigned_agent`, `last_message_preview`.

---

## 实时事件 (SSE MVP)
- 仍使用 `/api/chat/stream`。新增事件：
  ```json
  data: {"type":"status","status":"pending_manual"}
  data: {"type":"manual_message","role":"agent","content":"您好","timestamp":1737000500,"agent_info":{"agent_id":"agent_01","agent_name":"Alice"}}
  ```
- 前端解析器需区分 `type`：`message`（AI 默认）、`manual_message`、`status`、`error`。  
- WebSocket 版本作为 P2 目标，届时再追加 `/ws/client/{session_name}`、`/ws/agent/{agent_id}`。

---

如需新增字段/接口，请先更新此文件并同步相关前后端负责人，确保 Claude Code 等协作者对齐。
