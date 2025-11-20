# 静态会话 Default 下的用户隔离方案：conversation_id 自动生成机制详解

> 本文档基于 Coze 官方解答整理,适用于绑定静态会话 `default` 的应用对话流。

---

## 目录
- [核心结论](#核心结论)
- [静态会话与用户隔离的兼容性](#静态会话与用户隔离的兼容性)
- [实现流程详解](#实现流程详解)
- [代码实现](#代码实现)
- [隔离风险与规避](#隔离风险与规避)
- [常见问题](#常见问题)

---

## 核心结论

### 首次不传入 conversation_id 可自动生成

在绑定静态会话 `default` 的场景下,**首次调用不传入 conversation_id 让系统自动生成**是实现用户隔离的有效方式,但必须满足以下条件:

### 必要条件

1. **必须使用 OAuth JWT 鉴权**
   - 在 JWT payload 中传入 `session_name`(用户唯一标识,如业务侧 UID)

2. **后端必须存储映射关系**
   - 保存自动生成的 `conversation_id` 与 `session_name` 的绑定关系
   - 确保后续对话携带该 `conversation_id`

### 关键矛盾点说明

> 静态会话 `default` 是所有用户共用的 "容器",但扣子会通过 `session_name` 和 `conversation_id` 在该容器内实现用户级数据隔离(类似 "文件夹内按用户分文件")。

---

## 静态会话与用户隔离的兼容性

| 场景 | 是否支持用户隔离 | 原理 |
|------|----------------|------|
| 仅绑定 `default` 静态会话 | ❌ 不支持 | 所有用户共用同一静态会话,未启用 `session_name` 时上下文完全共享 |
| `default` + `session_name` | ✅ 支持 | 静态会话作为 "顶级容器",`session_name` 作为用户子目录,实现数据隔离 |
| `default` + `session_name` + `conversation_id` | ✅✅ 强隔离 | 最完整的隔离方案,每个用户有独立的 conversation |

### 原理示意图

```
静态会话 `default`
├─ 用户 A (session_name: "user_123")
│  └─ conversation_id: "conv_7568811304438710279" (自动生成)
│     ├─ 对话记录 1
│     ├─ 对话记录 2
│     └─ ...
├─ 用户 B (session_name: "user_456")
│  └─ conversation_id: "conv_7568811304438710280" (自动生成)
│     ├─ 对话记录 1
│     ├─ 对话记录 2
│     └─ ...
└─ 用户 C (session_name: "user_789")
   └─ conversation_id: "conv_7568811304438710281" (自动生成)
```

---

## 实现流程详解

### 步骤 1: 首次调用 - 自动生成 conversation_id 并关联 session_name

#### 1.1 配置 OAuth JWT 鉴权

**JWT Payload 中必须包含 `session_name`**:

```json
{
  "iss": "你的 OAuth 应用 ID",
  "aud": "api.coze.cn",
  "iat": 1516239022,
  "exp": 1516259022,
  "jti": "随机字符串",
  "session_name": "user_123"  // ← 关键: 业务侧用户 UID
}
```

参考文档: [OAuth JWT 授权](https://www.coze.cn/docs/developer_guides/oauth_jwt)

#### 1.2 API 调用示例(不传入 conversation_id)

**Python 示例**:

```python
import httpx

# 首次调用,不传入 conversation_id
response = httpx.post(
    "https://api.coze.cn/v1/workflows/chat",
    json={
        "workflow_id": "绑定 default 的对话流 ID",
        "app_id": "你的 app_id",
        "session_name": "user_123",  # ← JWT 和 API 中都要传
        "parameters": {
            "USER_INPUT": "你好,我是张三"
        },
        "additional_messages": [
            {
                "content": "你好,我是张三",
                "content_type": "text",
                "role": "user",
                "type": "question"
            }
        ]
        # ← 注意: 首次不传 conversation_id
    },
    headers={
        "Authorization": f"Bearer {access_token}",  # JWT 生成的 token
        "Content-Type": "application/json"
    }
)

# 从响应中提取自动生成的 conversation_id
data = response.json()
conversation_id = data.get("conversation_id")  # 如: "conv_7568811304438710279"

print(f"自动生成的 conversation_id: {conversation_id}")
```

**使用 Coze SDK 示例**:

```python
from cozepy import Coze, JWTAuth, JWTOAuthApp

# 初始化
jwt_oauth_app = JWTOAuthApp(...)
coze = Coze(auth=JWTAuth(oauth_app=jwt_oauth_app))

# 首次调用(不传 conversation_id)
response = coze.workflows.chat(
    workflow_id="绑定 default 的对话流 ID",
    app_id="你的 app_id",
    parameters={"USER_INPUT": "你好,我是张三"}
)

# 提取自动生成的会话 ID
conversation_id = response.data.conversation_id
print(f"自动生成的 conversation_id: {conversation_id}")
```

---

### 步骤 2: 后端存储 conversation_id 与用户的映射关系

#### 2.1 为什么要存储?

- **自动生成的 conversation_id 是一次性的**
- 用户下次对话时,必须传入相同的 `conversation_id` 才能访问历史记录
- 如果不存储,每次都会生成新的 conversation,导致上下文丢失

#### 2.2 存储方案

**方案 1: 内存缓存(简单,适合开发测试)**

```python
# 全局字典
conversation_cache = {}  # {session_name: conversation_id}

# 存储
conversation_cache["user_123"] = "conv_7568811304438710279"

# 读取
conversation_id = conversation_cache.get("user_123")
```

**方案 2: Redis(推荐生产环境)**

```python
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

# 存储(设置过期时间 24 小时)
redis_client.setex(
    f"conversation:{session_name}",
    86400,  # 24 小时过期
    conversation_id
)

# 读取
conversation_id = redis_client.get(f"conversation:{session_name}")
if conversation_id:
    conversation_id = conversation_id.decode('utf-8')
```

**方案 3: 数据库(适合需要持久化的场景)**

```sql
-- 创建表
CREATE TABLE user_conversations (
    session_name VARCHAR(255) PRIMARY KEY,
    conversation_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 存储
INSERT INTO user_conversations (session_name, conversation_id)
VALUES ('user_123', 'conv_7568811304438710279')
ON DUPLICATE KEY UPDATE
    conversation_id = VALUES(conversation_id),
    updated_at = CURRENT_TIMESTAMP;

-- 读取
SELECT conversation_id FROM user_conversations
WHERE session_name = 'user_123';
```

**Python + SQLite 示例**:

```python
import sqlite3

# 初始化数据库
conn = sqlite3.connect('conversations.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_conversations (
        session_name TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# 存储
def save_conversation(session_name, conversation_id):
    cursor.execute('''
        INSERT OR REPLACE INTO user_conversations (session_name, conversation_id)
        VALUES (?, ?)
    ''', (session_name, conversation_id))
    conn.commit()

# 读取
def get_conversation(session_name):
    cursor.execute('''
        SELECT conversation_id FROM user_conversations
        WHERE session_name = ?
    ''', (session_name,))
    result = cursor.fetchone()
    return result[0] if result else None
```

---

### 步骤 3: 后续调用 - 必须传入 conversation_id

#### 3.1 从存储中读取并传入

```python
# 获取用户的 conversation_id
conversation_id = conversation_cache.get(session_name)

if conversation_id:
    # 后续调用,传入 conversation_id
    response = httpx.post(
        "https://api.coze.cn/v1/workflows/chat",
        json={
            "workflow_id": "绑定 default 的对话流 ID",
            "app_id": "你的 app_id",
            "session_name": session_name,
            "conversation_id": conversation_id,  # ← 传入之前生成的 ID
            "parameters": {
                "USER_INPUT": "我上次问了什么?"
            },
            "additional_messages": [...]
        },
        headers={...}
    )
else:
    # 首次对话,不传 conversation_id
    # (会自动生成,然后存储)
    pass
```

#### 3.2 完整流程示意

```python
def chat_with_user(session_name, user_message):
    """
    与用户对话(自动管理 conversation_id)
    """
    # 1. 获取 Access Token
    access_token = get_access_token(session_name)

    # 2. 检查是否已有 conversation_id
    conversation_id = get_conversation(session_name)

    # 3. 构建 payload
    payload = {
        "workflow_id": WORKFLOW_ID,
        "app_id": APP_ID,
        "session_name": session_name,
        "parameters": {"USER_INPUT": user_message},
        "additional_messages": [...]
    }

    # 4. 如果有 conversation_id,添加到 payload
    if conversation_id:
        payload["conversation_id"] = conversation_id
        print(f"使用已有 conversation: {conversation_id}")
    else:
        print("首次对话,将自动生成 conversation_id")

    # 5. 调用 API
    response = httpx.post(
        "https://api.coze.cn/v1/workflows/chat",
        json=payload,
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # 6. 如果是首次对话,保存自动生成的 conversation_id
    if not conversation_id:
        data = response.json()
        new_conversation_id = data.get("conversation_id")
        if new_conversation_id:
            save_conversation(session_name, new_conversation_id)
            print(f"保存新 conversation: {new_conversation_id}")

    return response.json()
```

---

## 代码实现

### 完整的后端实现(FastAPI)

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import jwt
import time
import uuid
from datetime import datetime, timedelta

app = FastAPI()

# 配置
CLIENT_ID = "your_client_id"
PUBLIC_KEY_ID = "your_public_key_id"
PRIVATE_KEY = "your_private_key"
WORKFLOW_ID = "your_workflow_id"
APP_ID = "your_app_id"
API_BASE = "https://api.coze.cn"

# Conversation 存储(生产环境建议用 Redis 或数据库)
conversation_cache = {}  # {session_name: conversation_id}
token_cache = {}  # {session_name: {token, expires_at}}

class ChatRequest(BaseModel):
    message: str
    user_id: str  # session_name

def create_jwt_token(session_name):
    """创建 JWT Token"""
    now = int(time.time())
    payload = {
        "iss": CLIENT_ID,
        "aud": "api.coze.cn",
        "iat": now,
        "exp": now + 3600,
        "jti": str(uuid.uuid4()),
        "session_name": session_name  # ← 关键
    }
    headers = {
        "kid": PUBLIC_KEY_ID,
        "alg": "RS256",
        "typ": "JWT"
    }
    return jwt.encode(payload, PRIVATE_KEY, algorithm="RS256", headers=headers)

def get_access_token(session_name):
    """获取 Access Token(带缓存)"""
    # 检查缓存
    if session_name in token_cache:
        cached = token_cache[session_name]
        if cached['expires_at'] > datetime.now():
            return cached['token']

    # 生成新 Token
    jwt_token = create_jwt_token(session_name)

    response = httpx.post(
        f"{API_BASE}/api/permission/oauth2/token",
        json={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": jwt_token,
            "duration_seconds": 3600
        }
    )

    if response.status_code != 200:
        raise HTTPException(500, f"获取 Token 失败: {response.text}")

    access_token = response.json()["access_token"]

    # 缓存
    token_cache[session_name] = {
        'token': access_token,
        'expires_at': datetime.now() + timedelta(seconds=3300)
    }

    return access_token

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    聊天接口 - 自动管理 conversation_id
    """
    session_name = request.user_id

    # 1. 获取 Access Token
    access_token = get_access_token(session_name)

    # 2. 检查是否已有 conversation_id
    conversation_id = conversation_cache.get(session_name)

    # 3. 构建 payload
    payload = {
        "workflow_id": WORKFLOW_ID,
        "app_id": APP_ID,
        "session_name": session_name,  # ← 关键
        "parameters": {
            "USER_INPUT": request.message
        },
        "additional_messages": [
            {
                "content": request.message,
                "content_type": "text",
                "role": "user",
                "type": "question"
            }
        ]
    }

    # 4. 如果有 conversation_id,添加到 payload
    if conversation_id:
        payload["conversation_id"] = conversation_id
        print(f"♻️  使用已有 conversation: {conversation_id}")
    else:
        print(f"🆕 首次对话,将自动生成 conversation_id")

    # 5. 调用 API
    response = httpx.post(
        f"{API_BASE}/v1/workflows/chat",
        json=payload,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        timeout=30
    )

    if response.status_code != 200:
        raise HTTPException(500, f"API 调用失败: {response.text}")

    data = response.json()

    # 6. 如果是首次对话,保存自动生成的 conversation_id
    if not conversation_id:
        new_conversation_id = data.get("conversation_id")
        if new_conversation_id:
            conversation_cache[session_name] = new_conversation_id
            print(f"✅ 保存新 conversation: {new_conversation_id}")

    return data
```

---

## 隔离风险与规避

### 风险 1: 未配置 session_name

**问题**: 如果只绑定 `default` 静态会话,但未在 JWT 和 API 中传入 `session_name`,所有用户会共享同一个会话。

**规避**:
- ✅ JWT Payload 中必须包含 `session_name`
- ✅ API 请求中也必须包含 `session_name`
- ✅ 确保 `session_name` 对每个用户是唯一的

### 风险 2: conversation_id 未存储或丢失

**问题**: 如果后端没有存储 `conversation_id`,每次请求都会生成新的 conversation,导致用户无法访问历史对话。

**规避**:
- ✅ 使用持久化存储(Redis/数据库)
- ✅ 设置合理的过期时间
- ✅ 提供"新建对话"功能,允许用户主动清除历史

### 风险 3: 长期记忆节点未按会话隔离

**问题**: 即使正确传递了 `session_name` 和 `conversation_id`,如果工作流的长期记忆节点未启用隔离,仍可能共享数据。

**规避**:
- ✅ 在 Coze 平台编辑工作流
- ✅ 长期记忆节点: 启用"按会话隔离"
- ✅ 知识库节点: 配置 `session_name` 筛选

---

## 常见问题

### Q1: 为什么首次不传 conversation_id 会自动生成?

**A**: 这是 Coze 平台的默认行为。当检测到:
- 请求中没有 `conversation_id`
- 且使用了 `session_name`

系统会自动为该用户创建一个新的 conversation,并返回生成的 ID。

### Q2: conversation_id 的有效期是多久?

**A**: conversation_id 本身没有过期时间,但建议后端设置合理的缓存过期(如 24 小时),超时后自动创建新会话。

### Q3: 用户可以有多个 conversation 吗?

**A**: 可以。一个 `session_name` 可以对应多个 `conversation_id`,类似于"多个对话窗口"。但需要前端管理多个 conversation 的切换。

### Q4: 如何实现"新建对话"功能?

**A**: 清除缓存中的 `conversation_id`,下次请求时不传入,系统会自动生成新的。

```python
# 新建对话
del conversation_cache[session_name]
```

### Q5: Workflow 和 Bot 的 conversation 管理有什么区别?

**A**:
- **Bot**: 支持 `/v1/conversations` API 主动创建
- **Workflow**: 只能通过首次调用自动生成,不支持主动创建 API

---

## 参考资料

- [Coze OAuth JWT 文档](https://www.coze.cn/docs/developer_guides/oauth_jwt)
- [Workflow Chat API](https://www.coze.cn/docs/developer_guides/workflow_chat)
- [会话隔离官方说明](https://www.coze.cn/docs/developer_guides/session_isolation)

---

**文档版本**: v2.0
**最后更新**: 2025-11-19
**适用场景**: 绑定静态会话 `default` 的应用对话流
