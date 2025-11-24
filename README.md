# Fiido 智能客服系统

## 项目概述

一套完整的企业级智能客服解决方案，支持 **AI 自动应答 + 人工接管** 双模式。适用于电商独立站、SaaS 平台等需要客服支持的场景。

### 核心能力

- **AI 智能对话** - 基于 Coze Workflow，支持多轮对话和上下文理解
- **人工无缝接管** - AI 无法解决时自动/手动转人工，支持会话转接
- **实时消息推送** - SSE 长连接，坐席消息即时送达
- **完整状态管理** - 5 种会话状态，支持服务闭环
- **坐席工作台** - 独立的坐席管理系统，支持多坐席协作

### 技术栈

| 模块 | 技术 |
|------|------|
| 后端 | FastAPI + Python 3.10+ |
| 前端 | Vue 3 + TypeScript + Pinia |
| AI 引擎 | Coze Workflow API |
| 鉴权 | OAuth 2.0 + JWT |
| 实时通信 | Server-Sent Events (SSE) |

### 系统架构

```
用户浏览器 ←→ Vue前端 ←→ FastAPI后端 ←→ Coze AI
                              ↓
                        坐席工作台 (Vue)
```

### 会话状态流转

```
bot_active → pending_manual → manual_live → bot_active
   (AI服务)    (等待人工)      (人工服务)    (恢复AI)
```

### 适用场景

- 电商独立站客服
- SaaS 产品技术支持
- 在线咨询服务
- 售前/售后服务中心

---

## 当前版本: v2.3.6

**发布日期**: 2025-11-24

**功能完成度**: 95% (P0+P1+部分P3 已完成)

**系统状态**: 🎯 **生产可用 (Production Ready)** - 数据持久化已实现

**PRD 文档**: 见 `prd/INDEX.md` (20个需求文档，按6个分类组织)

**最新更新**:
- ✅ Redis 数据持久化实现
- ✅ 约束16：生产环境安全性与稳定性要求
- ✅ 会话数据自动恢复（服务器重启不丢失）
- ✅ 支持水平扩展（多台服务器共享数据）

**下一步**: 坐席认证系统 → 企业级部署

---

基于 Coze 对话流的智能客服系统，支持 OAuth+JWT 鉴权、完美的会话隔离和 Vue 3 前端。

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com)
[![Vue](https://img.shields.io/badge/Vue-3.5-brightgreen.svg)](https://vuejs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-blue.svg)](https://www.typescriptlang.org)
[![Coze](https://img.shields.io/badge/Coze-Workflow-orange.svg)](https://www.coze.com)

---

## 🎯 重要文档（必读）

### 会话隔离解决方案

⚠️ **如果您在实现多用户会话隔离时遇到问题，必读此文档：**

📖 **[Coze会话隔离最终解决方案.md](./Coze会话隔离最终解决方案.md)** （亲测有效）

**核心要点**：
- ✅ 必须在用户打开页面时立即调用 `conversations.create()` API
- ❌ 不能依赖首次对话时 Coze 自动生成 conversation_id
- ✅ 这是基于 Coze 开发的正确实践，已实际验证通过

**问题示例**：
```
窗口 1: "我是子豪"
窗口 2: "我是谁？"
AI 回答: "你是子豪" ← 这是错误的！应该不知道
```

**解决方案见**: [完整文档](./Coze会话隔离最终解决方案.md)

---

## ✨ 特性

### 后端特性
- ✅ **OAuth+JWT 鉴权** - 安全的访问密钥管理
- ✅ **会话隔离** - 基于 `session_name` 的多用户会话隔离
- ✅ **对话历史管理** - 基于 `conversation_id` 的历史保留
- ✅ **流式/同步双接口** - 支持实时响应和批量响应
- ✅ **Token 自动管理** - 按会话缓存和刷新 JWT Token
- ✅ **Chat SDK 支持** - 提供前端 SDK token 生成接口

### 前端特性
- ✅ **Vue 3 框架版本** - 现代化的前端架构
- ✅ **Fiido 官网设计** - 完全复刻 fiido.com 界面风格
- ✅ **流式响应** - 逐字显示AI回复
- ✅ **Markdown 渲染** - 支持富文本消息
- ✅ **气泡菜单** - 优雅的浮动操作菜单
- ✅ **对话/会话管理** - 清除对话、新建会话功能
- ✅ **历史分隔线** - 清晰区分对话历史
- ✅ **产品咨询** - 快捷产品咨询入口
- ✅ **响应式设计** - 支持移动端和PC端
- ✅ **局域网访问** - 支持同一网络下多设备访问

---

## 🚀 快速开始

### 后端启动

#### 1. 环境要求

- Python 3.10+
- pip 或 pip3

#### 2. 安装依赖

```bash
pip3 install -r requirements.txt
```

#### 3. 配置环境变量

创建 `.env` 文件:

```bash
# Coze API 配置
COZE_API_BASE=https://api.coze.com
COZE_AUTH_MODE=OAUTH_JWT
COZE_WORKFLOW_ID=你的工作流ID
COZE_APP_ID=你的应用ID

# OAuth 配置
COZE_OAUTH_CLIENT_ID=你的ClientID
COZE_OAUTH_PUBLIC_KEY_ID=你的公钥指纹
COZE_OAUTH_PRIVATE_KEY_FILE=./private_key.pem

# 服务器配置
HOST=0.0.0.0
PORT=8000
```

详细配置说明见 [配置指南](docs/配置指南.md)

#### 4. 启动服务

```bash
python3 backend.py
```

服务将在 `http://localhost:8000` 启动

---

### 前端启动

本项目使用 **Vue 3 + TypeScript** 现代化前端框架。

#### 环境要求
- Node.js 16+
- npm 或 yarn

#### 启动方式

**方式 A: 手动启动**
```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

**方式 B: 使用启动脚本**
```bash
./启动-Vue前端.sh
# 访问 http://localhost:5173
```

**局域网访问**:
```
http://<你的IP>:5173
```

#### 前端特性
- ✅ Vue 3 + TypeScript + Pinia
- ✅ 组件化架构，易于维护
- ✅ 完全复刻 Fiido.com 设计
- ✅ 热重载开发体验
- ✅ 类型安全
- ✅ 支持局域网访问

---

## 📁 项目结构

```
fiido-customer-service/
├── README.md                       # 项目说明
├── requirements.txt                # Python 依赖
├── .env                            # 环境变量配置
├── private_key.pem                 # OAuth 私钥
│
├── backend.py                      # FastAPI 后端主程序
├── fiido2.png                      # 客服头像
├── 启动-Vue前端.sh                  # Vue 启动脚本
│
├── frontend/                       # Vue 3 前端
│   ├── src/
│   │   ├── main.ts                 # 应用入口
│   │   ├── App.vue                 # 根组件
│   │   ├── components/             # Vue 组件 (8个)
│   │   │   ├── AppHeader.vue       # 导航栏
│   │   │   ├── HeroSection.vue     # Hero区域
│   │   │   ├── ProductsSection.vue # 产品展示
│   │   │   ├── AppFooter.vue       # 页脚
│   │   │   ├── ChatFloatButton.vue # 浮动按钮
│   │   │   ├── ChatPanel.vue       # 聊天面板
│   │   │   ├── ChatMessage.vue     # 消息组件
│   │   │   └── WelcomeScreen.vue   # 欢迎屏幕
│   │   ├── stores/
│   │   │   └── chatStore.ts        # Pinia 状态管理
│   │   ├── api/
│   │   │   └── chat.ts             # API 接口
│   │   ├── types/
│   │   │   └── index.ts            # TypeScript 类型
│   │   └── assets/
│   │       └── main.css            # 全局样式
│   ├── public/
│   │   └── fiido2.png              # 客服头像
│   ├── index.html                  # HTML 入口
│   ├── vite.config.ts              # Vite 配置
│   ├── package.json                # 依赖配置
│   └── .env                        # 环境变量
│
├── src/                            # 后端源代码
│   ├── __init__.py
│   ├── jwt_signer.py               # JWT 签名工具
│   └── oauth_token_manager.py      # OAuth Token 管理器
│
├── tests/                          # 测试脚本
│   ├── test_simple.py              # 简单会话隔离测试
│   └── test_session_name.py        # 完整会话隔离测试
│
├── docs/                           # 文档
│   ├── 配置指南.md                  # 配置说明
│   └── 会话隔离实现历程.md          # 实现过程记录
│
├── prd/                            # 需求文档
│   └── coze.md                     # Coze 集成需求文档
│
├── Coze会话隔离最终解决方案.md       # 会话隔离完整方案（亲测有效）
├── 文档清单.md                      # 文档索引
└── 文档整理完成总结.md              # 文档整理总结
```

---

## 🔌 API 接口

### 1. 聊天接口 (同步)

**请求**:
```bash
POST /api/chat
Content-Type: application/json

{
  "message": "你好",
  "user_id": "session_abc123",  # 可选,不提供则自动生成
  "conversation_id": "conv_123"  # 可选,用于保留历史
}
```

**响应**:
```json
{
  "success": true,
  "message": "您好！有什么可以帮助您的？"
}
```

### 2. 聊天接口 (流式)

**请求**:
```bash
POST /api/chat/stream
Content-Type: application/json

{
  "message": "你好",
  "user_id": "session_abc123",
  "conversation_id": "conv_123"  # 可选
}
```

**响应** (Server-Sent Events):
```
data: {"type": "message", "content": "您"}
data: {"type": "message", "content": "好"}
data: {"type": "message", "content": "！"}
data: {"type": "done", "content": ""}
```

### 3. 创建新对话

**请求**:
```bash
POST /api/conversation/new
Content-Type: application/json

{
  "user_id": "session_abc123"
}
```

**响应**:
```json
{
  "success": true,
  "conversation_id": "conv_7433558367123783713"
}
```

### 4. 生成 Chat SDK Token ⭐ 新增

**请求**:
```bash
POST /api/chat/token
Content-Type: application/json

{
  "user_id": "session_abc123"
}
```

**响应**:
```json
{
  "success": true,
  "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600
}
```

### 5. 获取 Bot 信息 ⭐ 新增

**请求**:
```bash
GET /api/bot/info
```

**响应**:
```json
{
  "success": true,
  "bot": {
    "name": "Fiido 客服",
    "description": "Fiido 智能客服助手",
    "icon_url": "https://..."
  }
}
```

### 6. 健康检查

```bash
GET /api/health
```

---

## 🤖 人工接管 API (P0-4)

以下API用于实现AI与人工客服的无缝切换。

### 7. 人工升级接口

触发人工接管流程，将会话从AI模式切换到待人工模式。

**请求**:
```bash
POST /api/manual/escalate
Content-Type: application/json

{
  "session_name": "session_abc123",
  "reason": "user_request"  # 或其他原因
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "session_name": "session_abc123",
    "status": "pending_manual",
    "escalation": {
      "reason": "manual",
      "details": "用户主动请求人工服务",
      "severity": "high"
    }
  }
}
```

**状态码**:
- `200`: 升级成功
- `409`: 已在人工接管中 (`MANUAL_IN_PROGRESS`)
- `400`: 缺少必需参数

### 8. 获取会话状态

获取会话的完整状态，包括历史消息和当前状态。

**请求**:
```bash
GET /api/sessions/{session_name}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "session": {
      "session_name": "session_abc123",
      "status": "pending_manual",
      "history": [...],
      "escalation": {...},
      "assigned_agent": null
    },
    "audit_trail": []
  }
}
```

### 9. 人工消息写入

在人工接管期间，坐席或用户发送的消息。

**请求**:
```bash
POST /api/manual/messages
Content-Type: application/json

{
  "session_name": "session_abc123",
  "role": "agent",  # 或 "user"
  "content": "您好，我是人工客服小王",
  "agent_info": {
    "agent_id": "agent_01",
    "agent_name": "小王"
  }
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "timestamp": 1763605000
  }
}
```

**说明**:
- `role` 必须是 `"agent"` 或 `"user"`
- 用户消息必须在 `manual_live` 状态下发送
- 坐席消息会通过SSE推送给前端

### 10. 坐席接入会话 (防抢单) ✨ **新增**

坐席接入待处理的会话，支持防抢单逻辑。

**请求**:
```bash
POST /api/sessions/{session_name}/takeover
Content-Type: application/json

{
  "agent_id": "agent_001",
  "agent_name": "小王"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "session_name": "session_abc123",
    "status": "manual_live",
    "assigned_agent": {
      "id": "agent_001",
      "name": "小王"
    }
  }
}
```

**状态码**:
- `200`: 接入成功
- `404`: 会话不存在
- `409`: 会话已被其他坐席接入 (`ALREADY_TAKEN`)
- `409`: 当前状态不允许接入 (`INVALID_STATUS`)
- `400`: 缺少必需参数

**防抢单逻辑**:
- 只允许在 `pending_manual` 状态下接入
- 同一会话只能被一个坐席接入
- 已接入的会话会返回 409 错误

### 11. 查询会话列表 ✨ **新增**

获取会话列表，支持按状态筛选和分页。

**请求**:
```bash
# 查询 pending_manual 状态的会话
GET /api/sessions?status=pending_manual&limit=10&offset=0

# 查询所有会话
GET /api/sessions?limit=20&offset=0
```

**Query Parameters**:
- `status` (可选): 会话状态筛选 (`pending_manual`, `manual_live`, `bot_active` 等)
- `limit` (可选): 每页数量，默认 50
- `offset` (可选): 偏移量，默认 0

**响应**:
```json
{
  "success": true,
  "data": {
    "sessions": [
      {
        "session_name": "session_123",
        "status": "pending_manual",
        "user_profile": {
          "nickname": "访客A",
          "vip": true
        },
        "updated_at": 1763695256.744,
        "last_message_preview": {
          "role": "user",
          "content": "我要人工",
          "timestamp": 1763695256.743
        },
        "escalation": {
          "reason": "keyword",
          "trigger_at": 1763695256.743,
          "waiting_seconds": 120.5
        },
        "assigned_agent": null
      }
    ],
    "total": 5,
    "limit": 10,
    "offset": 0,
    "has_more": false
  }
}
```

**说明**:
- 返回摘要格式，包含最后一条消息预览
- 自动计算等待时间 (`waiting_seconds`)
- 按更新时间倒序排列

### 12. 会话统计 ✨ **新增**

获取会话统计信息。

**请求**:
```bash
GET /api/sessions/stats
```

**响应**:
```json
{
  "success": true,
  "data": {
    "total_sessions": 50,
    "by_status": {
      "bot_active": 35,
      "pending_manual": 3,
      "manual_live": 2,
      "closed": 10
    },
    "active_sessions": 40,
    "avg_waiting_time": 45.67
  }
}
```

**说明**:
- `total_sessions`: 总会话数
- `by_status`: 各状态会话数量
- `active_sessions`: 活跃会话数（非 closed 状态）
- `avg_waiting_time`: 平均等待时间（秒）

### 13. 释放会话

结束人工接管，将会话恢复为AI模式。

**请求**:
```bash
POST /api/sessions/{session_name}/release
Content-Type: application/json

{
  "agent_id": "agent_01",
  "reason": "resolved"  # 或 "transferred", "timeout" 等
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "session_name": "session_abc123",
    "status": "bot_active",
    "last_manual_end_at": 1763605100
  }
}
```

---

## 🔄 SSE 实时推送 (P0-5)

系统支持通过 Server-Sent Events (SSE) 向前端实时推送人工接管相关事件。

### 工作原理

1. 前端建立 `/api/chat/stream` 长连接
2. 后端在以下情况推送事件：
   - 人工升级时 → 推送 `status_change`
   - 坐席发送消息时 → 推送 `manual_message`
   - 会话释放时 → 推送系统消息 + `status_change`

### SSE 事件格式

**状态变化事件**:
```
data: {
  "type": "status_change",
  "status": "pending_manual",
  "reason": "user_request",
  "timestamp": 1763605000
}
```

**人工消息事件**:
```
data: {
  "type": "manual_message",
  "role": "agent",
  "content": "您好，我是人工客服",
  "timestamp": 1763605000,
  "agent_id": "agent_01",
  "agent_name": "小王"
}
```

**系统消息事件**:
```
data: {
  "type": "manual_message",
  "role": "system",
  "content": "人工服务已结束，AI 助手已接管对话",
  "timestamp": 1763605100
}
```

### 前端接收示例

```javascript
const eventSource = new EventSource('/api/chat/stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'status_change') {
    console.log('状态变化:', data.status);
    // 更新UI显示状态
  }

  if (data.type === 'manual_message') {
    console.log('收到消息:', data.content);
    // 显示消息到聊天界面
  }
};
```

---

## 会话隔离机制

本系统实现了基于 `session_name` 的多用户会话隔离:

### 工作原理

```
前端访问 → 生成 session_id
    ↓
后端接收 user_id (session_id)
    ↓
┌─────────────────────────────┐
│ 1. JWT 签署时添加           │
│    jwt_payload["session_name"] = user_id
│                             │
│ 2. API 请求时添加           │
│    api_payload["session_name"] = user_id
└─────────────────────────────┘
    ↓
扣子平台根据 session_name 隔离会话
```

### 关键实现

**JWT 签署** (`src/jwt_signer.py:117-118`):
```python
if session_name:
    payload["session_name"] = session_name
```

**API 请求** (`backend.py:324`):
```python
payload = {
    "workflow_id": WORKFLOW_ID,
    "app_id": APP_ID,
    "session_name": session_id,  # ← 关键字段
    "parameters": {"USER_INPUT": message}
}
```

详细实现过程见 [会话隔离实现历程](docs/会话隔离实现历程.md)

---

## 测试

### 简单测试 (推荐)

```bash
python3 tests/test_simple.py
```

**测试内容**:
- 用户 A: "我叫张三"
- 用户 B: "我叫李四"
- 用户 A 第二轮: "我叫什么?" → 期望回答 "张三"

### 完整测试

```bash
python3 tests/test_session_name.py
```

---

## 常见问题

### Q: 会话隔离不生效怎么办?

**A**: 检查以下几点:
1. 确认 `backend.py:324` 添加了 `"session_name": session_id`
2. 确认流式接口 `backend.py:449` 也添加了 session_name
3. 运行测试验证: `python3 tests/test_simple.py`

### Q: 提示 "COZE_WORKFLOW_ID 环境变量未设置"?

**A**:
1. 确认 `.env` 文件存在
2. 检查文件内容是否正确
3. 重启后端服务

更多问题见 [配置指南](docs/配置指南.md#常见问题)

---

## 技术栈

- **后端框架**: FastAPI
- **HTTP 客户端**: httpx
- **JWT 处理**: PyJWT
- **AI 平台**: Coze Workflow
- **鉴权方式**: OAuth 2.0 + JWT

---

## 📚 文档

- [CHANGELOG.md](CHANGELOG.md) - 详细更新日志 ⭐ 新增
- [完整总结.md](完整总结.md) - 三个前端版本完整对比 ⭐ 新增
- [使用说明-最终版.md](使用说明-最终版.md) - index2.html 使用指南 ⭐ 新增
- [frontend/README_CN.md](frontend/README_CN.md) - Vue 3 版本文档 ⭐ 新增
- [配置指南](docs/配置指南.md) - 环境配置和 Coze 平台设置
- [会话隔离实现历程](docs/会话隔离实现历程.md) - 从问题到解决的完整过程

---

## 🧪 测试

### 健康检查
```bash
curl http://localhost:8000/api/health
```

### 简单测试 (推荐)

```bash
python3 tests/test_simple.py
```

**测试内容**:
- 用户 A: "我叫张三"
- 用户 B: "我叫李四"
- 用户 A 第二轮: "我叫什么?" → 期望回答 "张三"

### 完整会话隔离测试 ⭐ 已修复

```bash
python3 tests/test_session_name.py
```

**测试步骤** (遵循正确的会话隔离实现):
1. 用户A打开页面 → 立即调用 `/api/conversation/new` 创建 conversation_A
2. 用户B打开页面 → 立即调用 `/api/conversation/new` 创建 conversation_B
3. 验证 conversation_A ≠ conversation_B
4. 用户A说 "我叫张三，我今年25岁"
5. 用户B说 "我叫李四，我是一名程序员"
6. 用户A问 "我叫什么？我多大了？" → 期望回答 "张三、25岁"
7. 用户B问 "我的名字和职业是什么？" → 期望回答 "李四、程序员"
8. **关键验证**: 用户A问 "你知道李四是谁吗？" → 期望**不知道**（证明会话隔离成功）

**注意**: 此测试脚本已修复，严格遵循《Coze会话隔离最终解决方案.md》的实现方式

---
## 📊 版本历史

### v2.3.6 (2025-11-24) - Redis 数据持久化实现 💾

**功能完成度**: 95% (核心功能完成，生产环境就绪)

**主要更新**:

**🔴 Redis 数据持久化** (100%) - 解决三大问题
- ✅ **问题1 解决**：服务器重启后数据自动恢复（不再丢失）
- ✅ **问题2 解决**：支持水平扩展（多台服务器共享 Redis 数据）
- ✅ **问题3 解决**：支持历史数据查询和导出
- ✅ 创建 `src/redis_session_store.py` (406行)
  - 完整实现 SessionStateStore 接口
  - 连接池管理（max_connections=50）
  - TTL 过期策略（24小时自动清理）
  - 健康检查和监控功能
  - 定期清理策略
- ✅ 修改 `backend.py` 集成 Redis
  - 实现降级策略（Redis 失败时降级到内存存储）
  - 启动时显示 Redis 健康状态
  - 支持环境变量配置
- ✅ 更新 `.env` 配置
  - 新增 6 个 Redis 配置项
  - 详细的注释和生产环境注意事项

**🔒 约束16：生产环境安全性与稳定性** (100%)
- ✅ 新增约束文档 `prd/02_约束与原则/CONSTRAINTS_AND_PRINCIPLES.md`
- ✅ 资源管理与限制（16.1）
  - 存储限制：maxmemory, TTL
  - 日志管理：日志轮转
  - 连接池限制
- ✅ 数据清理策略（16.2）
  - 定期清理过期数据
  - 监控存储使用量
- ✅ 错误处理与降级（16.3）
  - Redis 不可用时自动降级
  - 超时保护（5秒）
- ✅ 安全性要求（16.4）
  - 敏感信息保护
  - 环境变量隔离
  - 输入验证
- ✅ 监控与告警（16.5）
  - 关键指标监控
  - 健康检查端点
- ✅ 生产环境检查清单（16.6）

**🧪 测试验证** (100%)
- ✅ 创建 `tests/test_redis_persistence.py`
- ✅ 所有测试通过：
  - 数据保存成功
  - 数据读取成功
  - 数据完整性验证
  - 服务器重启后数据恢复
  - 历史消息完整保留
  - 用户信息正确恢复

**当前系统功能**:
- ✅ AI 智能对话 - 基于 Coze Workflow
- ✅ 人工接管流程 - 5 种状态管理
- ✅ 坐席工作台 - 完整工作台实现
- ✅ 实时消息推送 - SSE 长连接
- ✅ 会话隔离 - 基于 session_name
- ✅ 历史回填 - 刷新保持上下文
- ✅ 品牌设计 - Fiido 官方风格
- ✅ 局域网访问 - 支持多设备访问
- ✅ **Redis 数据持久化** - 服务器重启不丢失数据 ⭐ 新增
- ✅ **水平扩展支持** - 多台服务器共享数据 ⭐ 新增

**生产环境就绪**:
- ✅ 数据持久化机制
- ✅ 降级策略
- ✅ 资源限制
- ✅ 监控告警
- ✅ 安全性保障

**下一步**: 坐席认证系统（JWT） → HTTPS 部署

**GitHub**:
- Commit: `2054341`
- Tag: `v2.3.6`
- Files: 9 files changed

---

### v2.3.5 (2025-11-24) - 开发流程规范完善

**主要更新**:
- 新增"全新功能方案文档"强制要求（CLAUDE.md）
- 创建 Redis 数据持久化方案文档

**GitHub**: Commit `85a8c80`, Tag `v2.3.5`

---

### v2.3.4 (2025-11-24) - 文档结构优化
- 重组 prd/ 和 docs/ 目录结构
- 创建文档索引和导航
- **GitHub**: Commit `b4b90d2`, Tag `v2.3.4`

---

### v2.3.3 (2025-11-24) - UI 美化与品牌升级
- 坐席工作台 Fiido 品牌设计
- 用户端人工接管 UI 完善
- 网络访问配置优化
- **GitHub**: Commit `ab42735`, Tag `v2.3.3`

---

### v2.3.2 (2025-11-23) - 坐席工作台完善
- P0-12 至 P0-15: 坐席工作台核心功能
- P1-1: 会话统计 API
- P1-2: 历史回填功能
- 回归测试框架（12项自动化测试）
- **GitHub**: Tag `v2.3.2`

---

### v2.3.1 (2025-11-22) - Coze Workflow ID 更新
- 更新 Workflow ID 至最新版本
- 修复前端客服头像加载问题
- **GitHub**: Tag `v2.3.1`

---

### v2.3.0 (2025-11-21) - P0人工接管功能完成
- P0-4: 核心API实现（人工升级、会话状态、消息写入、释放）
- P0-5: SSE实时推送
- P0-6: JSON日志规范
- **GitHub**: Tag `v2.3.0`

---

### v2.2.1 (2025-11-20) - UI菜单交互修复
- 修复气泡菜单交互问题
- **GitHub**: Tag `v2.2.1`

---

### v2.2.0 (2025-11-20) - 会话隔离重大突破
- 彻底解决会话隔离问题
- 前端UI优化（气泡菜单、清除对话、新建会话）
- **GitHub**: Tag `v2.2.0`

---

### v2.1.0 (2025-11-19) - 三前端版本发布
- 后端新增多个API接口
- 三个前端版本：Vue 3、Chat SDK、增强版HTML
- 完全复刻 Fiido.com 设计
- **GitHub**: Tag `v2.1.0`

---

📖 **详细版本历史**: 见 [CHANGELOG_DETAIL.md](./CHANGELOG_DETAIL.md)

---

## v2.0.0 之前的版本

### v2.0.0 (2025-11-18) - 会话隔离实现
- 实现基于 session_name 的会话隔离
- 双重添加 session_name (JWT + API payload)
- 完整的测试验证

---

**最后更新**: 2025-11-24
**当前版本**: v2.3.6

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## 📄 许可证

MIT License

---

Made with ❤️ by Claude Code
