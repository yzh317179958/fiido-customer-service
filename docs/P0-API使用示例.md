# P0 人工接管 API 使用示例

本文档提供 P0 人工接管功能的完整使用示例，包括 curl 命令和前端代码示例。

---

## 目录

1. [完整工作流程](#完整工作流程)
2. [API 调用示例](#api-调用示例)
3. [前端集成示例](#前端集成示例)
4. [错误处理](#错误处理)
5. [最佳实践](#最佳实践)

---

## 完整工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                     人工接管完整流程                         │
└─────────────────────────────────────────────────────────────┘

1. 用户与AI对话 (bot_active)
   │
   ├─ 触发条件：
   │  • 用户主动点击"人工客服"
   │  • Regulator 检测到需要升级
   │  • AI 多次回答失败
   │
   ↓
2. 触发人工升级 (POST /api/manual/escalate)
   │
   ↓ 状态: bot_active → pending_manual
   │ SSE 推送: status_change 事件
   │
3. 坐席系统接收通知
   │
   ├─ 坐席分配
   │
   ↓
4. 坐席接手会话
   │
   ↓ 状态: pending_manual → manual_live
   │ SSE 推送: status_change 事件
   │
5. 人工对话阶段
   │
   ├─ 坐席发送消息 (POST /api/manual/messages)
   │  SSE 推送: manual_message 事件
   │
   ├─ 用户发送消息 (POST /api/manual/messages)
   │  SSE 推送: manual_message 事件
   │
6. 坐席结束服务 (POST /api/sessions/{session}/release)
   │
   ↓ 状态: manual_live → bot_active
   │ SSE 推送: system 消息 + status_change 事件
   │
7. 恢复 AI 对话 (bot_active)
```

---

## API 调用示例

### 1. 人工升级

**场景**: 用户点击"转人工"按钮

```bash
curl -X POST http://localhost:8000/api/manual/escalate \
  -H "Content-Type: application/json" \
  -d '{
    "session_name": "session_user123",
    "reason": "user_request"
  }'
```

**响应**:
```json
{
  "success": true,
  "data": {
    "session_name": "session_user123",
    "status": "pending_manual",
    "escalation": {
      "reason": "manual",
      "details": "用户主动请求人工服务",
      "severity": "high",
      "timestamp": 1763605000
    },
    "conversation_id": "7574621136676667397",
    "history": [
      {
        "role": "user",
        "content": "我要人工客服",
        "timestamp": 1763604995
      }
    ]
  }
}
```

**错误示例** (已在人工接管中):
```json
{
  "detail": "MANUAL_IN_PROGRESS"
}
```
HTTP 状态码: `409 Conflict`

---

### 2. 获取会话状态

**场景**: 坐席系统拉取待处理会话

```bash
curl -X GET http://localhost:8000/api/sessions/session_user123
```

**响应**:
```json
{
  "success": true,
  "data": {
    "session": {
      "session_name": "session_user123",
      "conversation_id": "7574621136676667397",
      "status": "pending_manual",
      "history": [
        {
          "role": "user",
          "content": "你好",
          "timestamp": 1763604900
        },
        {
          "role": "assistant",
          "content": "您好！请问有什么可以帮您？",
          "timestamp": 1763604901
        },
        {
          "role": "user",
          "content": "我要人工客服",
          "timestamp": 1763604995
        }
      ],
      "escalation": {
        "reason": "manual",
        "details": "用户主动请求人工服务",
        "severity": "high",
        "timestamp": 1763605000
      },
      "assigned_agent": null,
      "created_at": 1763604900,
      "updated_at": 1763605000
    },
    "audit_trail": []
  }
}
```

---

### 3. 发送坐席消息

**场景**: 坐席回复用户

```bash
curl -X POST http://localhost:8000/api/manual/messages \
  -H "Content-Type: application/json" \
  -d '{
    "session_name": "session_user123",
    "role": "agent",
    "content": "您好，我是人工客服小王，请问有什么可以帮您？",
    "agent_info": {
      "agent_id": "agent_001",
      "agent_name": "小王"
    }
  }'
```

**响应**:
```json
{
  "success": true,
  "data": {
    "timestamp": 1763605010
  }
}
```

**同时，前端通过 SSE 接收到**:
```json
{
  "type": "manual_message",
  "role": "agent",
  "content": "您好，我是人工客服小王，请问有什么可以帮您？",
  "timestamp": 1763605010,
  "agent_id": "agent_001",
  "agent_name": "小王"
}
```

---

### 4. 用户回复坐席

**场景**: 用户在人工对话中回复

```bash
curl -X POST http://localhost:8000/api/manual/messages \
  -H "Content-Type: application/json" \
  -d '{
    "session_name": "session_user123",
    "role": "user",
    "content": "我想咨询一下产品价格"
  }'
```

**响应**:
```json
{
  "success": true,
  "data": {
    "timestamp": 1763605020
  }
}
```

---

### 5. 释放会话

**场景**: 坐席解决问题后结束服务

```bash
curl -X POST http://localhost:8000/api/sessions/session_user123/release \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_001",
    "reason": "resolved"
  }'
```

**响应**:
```json
{
  "success": true,
  "data": {
    "session_name": "session_user123",
    "status": "bot_active",
    "last_manual_end_at": 1763605100,
    "assigned_agent": null
  }
}
```

**同时，前端通过 SSE 接收到两个事件**:

1. 系统消息:
```json
{
  "type": "manual_message",
  "role": "system",
  "content": "人工服务已结束，AI 助手已接管对话",
  "timestamp": 1763605100
}
```

2. 状态变化:
```json
{
  "type": "status_change",
  "status": "bot_active",
  "reason": "released",
  "timestamp": 1763605100
}
```

---

## 前端集成示例

### Vue 3 示例

```vue
<template>
  <div class="chat-container">
    <!-- 状态指示器 -->
    <div class="status-indicator" :class="sessionStatus">
      <span v-if="sessionStatus === 'bot_active'">🤖 AI 助手</span>
      <span v-else-if="sessionStatus === 'pending_manual'">⏳ 等待人工...</span>
      <span v-else-if="sessionStatus === 'manual_live'">👤 人工客服</span>
    </div>

    <!-- 消息列表 -->
    <div class="messages">
      <div v-for="msg in messages" :key="msg.timestamp" :class="['message', msg.role]">
        <div class="content">{{ msg.content }}</div>
      </div>
    </div>

    <!-- 输入框 -->
    <div class="input-area">
      <button @click="requestManual" :disabled="sessionStatus !== 'bot_active'">
        转人工
      </button>
      <input v-model="userInput" @keyup.enter="sendMessage" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const sessionName = ref(`session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
const sessionStatus = ref('bot_active');
const messages = ref([]);
const userInput = ref('');
let eventSource = null;

// 建立 SSE 连接
function connectSSE() {
  // 发送一个消息来建立 SSE 连接
  fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: '',  // 空消息仅用于建立连接
      user_id: sessionName.value
    })
  }).then(response => {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    function read() {
      reader.read().then(({ done, value }) => {
        if (done) return;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6));
              handleSSEMessage(data);
            } catch (e) {
              console.error('解析 SSE 消息失败:', e);
            }
          }
        }

        read();
      });
    }

    read();
  });
}

// 处理 SSE 消息
function handleSSEMessage(data) {
  if (data.type === 'status_change') {
    sessionStatus.value = data.status;
    console.log('状态变化:', data);
  } else if (data.type === 'manual_message') {
    messages.value.push({
      role: data.role,
      content: data.content,
      timestamp: data.timestamp
    });
  }
}

// 请求人工客服
async function requestManual() {
  try {
    const response = await fetch('/api/manual/escalate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_name: sessionName.value,
        reason: 'user_request'
      })
    });

    const result = await response.json();
    if (result.success) {
      sessionStatus.value = result.data.status;
      messages.value.push({
        role: 'system',
        content: '正在为您转接人工客服...',
        timestamp: Date.now()
      });
    }
  } catch (error) {
    console.error('请求人工失败:', error);
  }
}

// 发送消息
async function sendMessage() {
  if (!userInput.value.trim()) return;

  const message = userInput.value;
  userInput.value = '';

  // 添加到消息列表
  messages.value.push({
    role: 'user',
    content: message,
    timestamp: Date.now()
  });

  // 根据状态选择不同的接口
  if (sessionStatus.value === 'manual_live') {
    // 人工对话中，使用 manual_messages API
    await fetch('/api/manual/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_name: sessionName.value,
        role: 'user',
        content: message
      })
    });
  } else {
    // AI 对话中，使用 chat/stream API
    // ... (常规 AI 对话逻辑)
  }
}

onMounted(() => {
  connectSSE();
});
</script>
```

---

### React 示例

```jsx
import { useState, useEffect, useRef } from 'react';

function ChatApp() {
  const [sessionName] = useState(() =>
    `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  );
  const [sessionStatus, setSessionStatus] = useState('bot_active');
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState('');

  useEffect(() => {
    connectSSE();
  }, []);

  function connectSSE() {
    fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: '',
        user_id: sessionName
      })
    }).then(response => {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      function read() {
        reader.read().then(({ done, value }) => {
          if (done) return;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.substring(6));
                handleSSEMessage(data);
              } catch (e) {
                console.error('解析失败:', e);
              }
            }
          }

          read();
        });
      }

      read();
    });
  }

  function handleSSEMessage(data) {
    if (data.type === 'status_change') {
      setSessionStatus(data.status);
    } else if (data.type === 'manual_message') {
      setMessages(prev => [...prev, {
        role: data.role,
        content: data.content,
        timestamp: data.timestamp
      }]);
    }
  }

  async function requestManual() {
    const response = await fetch('/api/manual/escalate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_name: sessionName,
        reason: 'user_request'
      })
    });

    const result = await response.json();
    if (result.success) {
      setSessionStatus(result.data.status);
      setMessages(prev => [...prev, {
        role: 'system',
        content: '正在为您转接人工客服...',
        timestamp: Date.now()
      }]);
    }
  }

  async function sendMessage() {
    if (!userInput.trim()) return;

    const message = userInput;
    setUserInput('');

    setMessages(prev => [...prev, {
      role: 'user',
      content: message,
      timestamp: Date.now()
    }]);

    if (sessionStatus === 'manual_live') {
      await fetch('/api/manual/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_name: sessionName,
          role: 'user',
          content: message
        })
      });
    } else {
      // AI 对话逻辑
    }
  }

  return (
    <div className="chat-container">
      {/* 状态指示器 */}
      <div className={`status-indicator ${sessionStatus}`}>
        {sessionStatus === 'bot_active' && '🤖 AI 助手'}
        {sessionStatus === 'pending_manual' && '⏳ 等待人工...'}
        {sessionStatus === 'manual_live' && '👤 人工客服'}
      </div>

      {/* 消息列表 */}
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
      </div>

      {/* 输入框 */}
      <div className="input-area">
        <button
          onClick={requestManual}
          disabled={sessionStatus !== 'bot_active'}
        >
          转人工
        </button>
        <input
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          onKeyUp={(e) => e.key === 'Enter' && sendMessage()}
        />
      </div>
    </div>
  );
}
```

---

## 错误处理

### 常见错误

1. **409 Conflict - MANUAL_IN_PROGRESS**
   - 含义: 会话已在人工接管中
   - 处理: 提示用户已在人工对话中

2. **404 Not Found - Session not found**
   - 含义: 会话不存在
   - 处理: 重新创建会话

3. **409 Conflict - Session not in manual_live status**
   - 含义: 状态不对，无法执行操作
   - 处理: 检查会话状态，引导用户正确操作

4. **400 Bad Request - Missing parameters**
   - 含义: 缺少必需参数
   - 处理: 检查请求参数

### 错误处理示例

```javascript
async function requestManual() {
  try {
    const response = await fetch('/api/manual/escalate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_name: sessionName,
        reason: 'user_request'
      })
    });

    if (response.status === 409) {
      const error = await response.json();
      if (error.detail === 'MANUAL_IN_PROGRESS') {
        alert('您已在人工客服对话中');
        return;
      }
    }

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const result = await response.json();
    // 处理成功响应
  } catch (error) {
    console.error('请求人工失败:', error);
    alert('转接人工失败，请稍后重试');
  }
}
```

---

## 最佳实践

### 1. SSE 连接管理

```javascript
class SSEManager {
  constructor(sessionName) {
    this.sessionName = sessionName;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect() {
    fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: '',
        user_id: this.sessionName
      })
    }).then(response => {
      this.reconnectAttempts = 0;  // 重置重连计数
      this.handleStream(response);
    }).catch(error => {
      console.error('SSE 连接失败:', error);
      this.reconnect();
    });
  }

  reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('SSE 重连次数超限');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    console.log(`${delay}ms 后重连...`);

    setTimeout(() => this.connect(), delay);
  }

  handleStream(response) {
    // 处理流式响应
  }
}
```

### 2. 状态同步

```javascript
// 定期同步会话状态
setInterval(async () => {
  const response = await fetch(`/api/sessions/${sessionName}`);
  const result = await response.json();

  if (result.success) {
    const serverStatus = result.data.session.status;
    if (serverStatus !== localStatus) {
      console.warn('状态不同步，更新本地状态');
      localStatus = serverStatus;
    }
  }
}, 30000);  // 每 30 秒同步一次
```

### 3. 消息去重

```javascript
const messageIdSet = new Set();

function addMessage(message) {
  const messageId = `${message.timestamp}_${message.role}_${message.content.substring(0, 20)}`;

  if (messageIdSet.has(messageId)) {
    console.log('消息已存在，跳过');
    return;
  }

  messageIdSet.add(messageId);
  messages.push(message);
}
```

---

## 附录: 完整 Python 测试脚本

见 `tests/test_p04_apis.py` 和 `tests/test_p05_sse.py`

---

**文档版本**: v1.0
**最后更新**: 2025-11-20
