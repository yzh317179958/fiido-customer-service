# Fiido 智能客服系统

基于 Coze 对话流的智能客服后端服务，支持 OAuth+JWT 鉴权和多用户会话隔离。

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com)
[![Coze](https://img.shields.io/badge/Coze-Workflow-orange.svg)](https://www.coze.com)

---

## 特性

- ✅ **OAuth+JWT 鉴权** - 安全的访问密钥管理
- ✅ **会话隔离** - 基于 `session_name` 的多用户会话隔离
- ✅ **流式/同步双接口** - 支持实时响应和批量响应
- ✅ **Token 自动管理** - 按会话缓存和刷新 JWT Token
- ✅ **完整测试** - 提供会话隔离验证测试

---

## 快速开始

### 1. 环境要求

- Python 3.10+
- pip 或 pip3

### 2. 安装依赖

```bash
pip3 install -r requirements.txt
```

### 3. 配置环境变量

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

### 4. 启动服务

```bash
python3 backend.py
```

服务将在 `http://localhost:8000` 启动

### 5. 测试

#### 健康检查
```bash
curl http://localhost:8000/api/health
```

#### 测试会话隔离
```bash
python3 tests/test_simple.py
```

---

## 项目结构

```
fiido-customer-service/
├── README.md                   # 项目说明
├── requirements.txt            # Python 依赖
├── .env                        # 环境变量配置
├── private_key.pem             # OAuth 私钥
│
├── backend.py                  # FastAPI 后端主程序
├── index2.html                 # 前端页面
├── fiido2.png                  # 客服头像
│
├── src/                        # 源代码模块
│   ├── __init__.py
│   ├── jwt_signer.py           # JWT 签名工具
│   └── oauth_token_manager.py  # OAuth Token 管理器
│
├── tests/                      # 测试脚本
│   ├── test_simple.py          # 简单会话隔离测试
│   ├── test_session_name.py    # 完整会话隔离测试
│   └── test_session_isolation.py # 旧版测试(已废弃)
│
├── docs/                       # 文档
│   ├── 配置指南.md              # 配置说明
│   └── 会话隔离实现历程.md      # 实现过程记录
│
└── archive/                    # 归档文件
    ├── backend_backup_*.py     # 代码备份
    ├── *.log                   # 日志文件
    └── *.html                  # 测试页面
```

---

## API 接口

### 1. 聊天接口 (同步)

**请求**:
```bash
POST /api/chat
Content-Type: application/json

{
  "message": "你好",
  "user_id": "session_abc123"  # 可选,不提供则自动生成
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
  "user_id": "session_abc123"
}
```

**响应** (Server-Sent Events):
```
data: {"type": "message", "content": "您"}
data: {"type": "message", "content": "好"}
data: {"type": "message", "content": "！"}
data: {"type": "done", "content": ""}
```

### 3. 健康检查

```bash
GET /api/health
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

## 文档

- [配置指南](docs/配置指南.md) - 环境配置和 Coze 平台设置
- [会话隔离实现历程](docs/会话隔离实现历程.md) - 从问题到解决的完整过程

---

## 版本历史

### v2.1.0 (2025-11-19)
- ✅ 实现基于 session_name 的会话隔离
- ✅ 双重添加 session_name (JWT + API payload)
- ✅ 完整的测试验证
- ✅ 文档整理和规范化

---

**最后更新**: 2025-11-19
