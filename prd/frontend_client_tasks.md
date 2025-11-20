# 前端用户端改造任务

## ⚠️ 前端接口调用约束

**前端开发必须遵守以下接口约束，确保不破坏现有 AI 对话功能**：

### 🔴 核心接口约束（不可修改）

#### 1. 现有 AI 对话接口 - 保持不变
以下接口是核心功能，**前端调用方式不得修改**：

**接口 1: `/api/chat` (非流式)**
```typescript
// ✅ 必须保持的调用方式
interface ChatRequest {
  message: string;
  user_id?: string;        // 会话 ID（必需支持）
  conversation_id?: string; // 可选
  parameters?: any;        // 可选
}

interface ChatResponse {
  success: boolean;
  message?: string;
  error?: string;
}

// ✅ 正确调用
const response = await api.chat({
  message: userInput,
  user_id: sessionId,  // 必须传入
  conversation_id: conversationId
});
```

**接口 2: `/api/chat/stream` (SSE 流式)**
```typescript
// ✅ 必须保持的 SSE 事件解析
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);

  // ✅ 必须支持的事件类型
  switch (data.type) {
    case 'message':  // AI 消息
      appendMessage(data.content);
      break;
    case 'done':     // 对话结束
      finishMessage();
      break;
    // ✅ 允许：新增事件类型（不影响现有逻辑）
    case 'manual_message':  // 人工消息（新增）
      appendManualMessage(data);
      break;
    case 'status':   // 状态变更（新增）
      updateSessionStatus(data.status);
      break;
  }
};
```

**约束说明**：
- ✅ **必须保持**：请求参数中的 `user_id` 字段（用于会话隔离）
- ✅ **必须保持**：SSE 事件的解析方式（`type: 'message'` 和 `type: 'done'`）
- ✅ **允许扩展**：添加新的事件类型处理（如 `manual_message`, `status`）
- ❌ **禁止修改**：现有事件类型的处理逻辑
- ❌ **禁止替换**：不得用 WebSocket 替换 SSE（核心 AI 对话必须保持 SSE）

#### 2. 允许的扩展方式

**✅ 允许：基于状态切换接口调用**
```typescript
// ✅ 正确：根据会话状态决定调用哪个接口
async function sendMessage(content: string) {
  const sessionStatus = chatStore.sessionStatus;

  if (sessionStatus === 'bot_active') {
    // AI 模式：调用原有接口
    await api.chatStream({
      message: content,
      user_id: chatStore.sessionId,
      conversation_id: chatStore.conversationId
    });
  } else if (sessionStatus === 'manual_live') {
    // 人工模式：调用新接口
    await api.sendManualMessage({
      session_name: chatStore.sessionId,
      role: 'user',
      content: content
    });
  } else if (sessionStatus === 'pending_manual') {
    // 等待人工：禁用输入
    showToast('正在等待人工客服接入...');
  }
}
```

**✅ 允许：在 SSE 流中处理新事件类型**
```typescript
// ✅ 正确：扩展事件处理，不影响现有逻辑
function handleSSEEvent(data: any) {
  // ✅ 保持原有事件处理
  if (data.type === 'message') {
    chatStore.appendMessage({
      role: 'assistant',
      content: data.content
    });
  }

  // ✅ 新增事件类型处理
  if (data.type === 'manual_message') {
    chatStore.appendMessage({
      role: 'agent',
      content: data.content,
      agent_info: data.agent_info
    });
  }

  if (data.type === 'status') {
    chatStore.updateSessionStatus(data.status);
  }
}
```

#### 3. 前端开发注意事项

**状态管理扩展**：
- ✅ 允许在 `chatStore` 中添加新状态字段（如 `sessionStatus`, `escalationInfo`）
- ✅ 允许扩展 `Message` 接口（如添加 `agent_info` 字段）
- ❌ 禁止修改核心状态字段的含义（如 `sessionId`, `conversationId`）

**向后兼容测试**：
所有前端改动必须通过以下测试：
1. **AI 对话功能正常**：在 `bot_active` 状态下，AI 对话流程完整无误
2. **SSE 流式响应正常**：消息实时显示，`type: 'done'` 正确触发结束
3. **会话隔离有效**：不同浏览器窗口（不同 sessionId）的对话互不干扰

**参考文档**：
- 📘 [TECHNICAL_CONSTRAINTS.md](./TECHNICAL_CONSTRAINTS.md) - 第 9 节（前端扩展）
- 📘 [api_contract.md](./api_contract.md) - API 接口规范

---

## 环境范围
- `frontend/` Vue 版本 (`ChatPanel.vue`, `chatStore.ts`, `api/chat.ts`).

## 优先级
- **P0**：与后端 P0 同步上线，保证用户可感知状态并切换人工。
- **P1**：体验优化。

## 任务拆解
| Priority | 文件 / 模块 | 任务 | 说明 |
| --- | --- | --- | --- |
| P0 | `chatStore.ts` | 增加 `sessionStatus`, `escalationInfo`, `manualChannel` 状态 | 保存当前会话状态；扩展 `Message.role` 支持 `agent`，并管理历史同步 |
| P0 | `api/chat.ts` | 新增访问 `/api/manual/escalate`, `/api/sessions/{session}` 等方法 | 根据状态决定调用 AI 接口或人工接口；处理 409/状态跳转 |
| P0 | `ChatPanel.vue` | 顶部状态条组件 | 根据 store 状态显示“AI 服务中/等待人工/人工接入/非工作时间”提示，配合图标和颜色 |
| P0 | 消息流 | 复用 `/api/chat/stream` SSE，当收到 `type='manual_message'/'status'` 事件时更新消息和状态 | 不单独创建 WebSocket；实现统一的 SSE 解析器 |
| P0 | 输入框逻辑 | 根据状态确定发送接口 | manual 状态走 `/api/manual/messages`，AI 状态走 `/api/chat/stream`；`pending_manual` 时禁用输入 |
| P0 | 历史回填 | 进入面板/刷新时调用 `/api/sessions/{session}`，按 `role` 渲染消息 | `Message.role` 支持 `agent`，保留最多 50 条 |
| P1 | 非工作时间提示 | 在 `after_hours_email` 状态展示邮件说明，提供“留下联系方式”输入框 | 输入内容应写入 `SessionState.history`，并随邮件发送 |

## 交付件
1. Store/组件/接口代码改造，附带基本单元测试或至少手动验证步骤。  
2. 更新 `frontend/README_CN.md` 说明人工模式使用方式。  
3. 演示脚本：展示 AI->人工->AI 流程。
