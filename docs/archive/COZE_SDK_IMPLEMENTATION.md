# Coze SDK 集成方案 - 前端 Chat SDK + 后端 Python SDK

## 架构设计

```
前端: Coze Chat SDK (官方界面渲染)
    ↓
自定义按钮 (新对话 / 新会话)
    ↓
后端 API (FastAPI)
    ↓
Coze Python SDK (conversation 管理)
```

## 优势

✅ **使用官方 Chat SDK** - 界面美观、功能完整、维护方便
✅ **使用 Python SDK** - 后端操作标准化、类型安全
✅ **最少代码** - 不需要自己实现聊天界面
✅ **易于扩展** - 基于官方 SDK,升级方便

---

## 实现方案

### 1. 前端实现 (使用 Coze Chat SDK)

#### HTML 页面

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fiido 智能客服</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .container {
            text-align: center;
            color: white;
        }

        h1 {
            font-size: 48px;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        p {
            font-size: 20px;
            margin-bottom: 40px;
            opacity: 0.9;
        }

        .action-buttons {
            display: flex;
            gap: 20px;
            justify-content: center;
            flex-wrap: wrap;
        }

        .btn {
            padding: 15px 30px;
            font-size: 16px;
            font-weight: 600;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }

        .btn-primary {
            background: white;
            color: #667eea;
        }

        .btn-secondary {
            background: rgba(255,255,255,0.2);
            color: white;
            border: 2px solid white;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(0,0,0,0.3);
        }

        /* 自定义 Chat SDK 悬浮按钮位置 */
        #coze-chat-container {
            position: fixed;
            right: 20px;
            bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚴 Fiido 智能客服</h1>
        <p>您好！欢迎来到 Fiido 电动车在线客服系统</p>

        <div class="action-buttons">
            <button class="btn btn-primary" onclick="openChat()">
                💬 开始对话
            </button>
            <button class="btn btn-secondary" onclick="newConversation()">
                🆕 新对话
            </button>
            <button class="btn btn-secondary" onclick="newSession()">
                🔄 新会话
            </button>
        </div>
    </div>

    <!-- Coze Chat SDK -->
    <script src="https://lf-cdn.coze.cn/obj/unpkg/flow-platform/chat-app-sdk/1.2.0-beta.15/libs/cn/index.js"></script>

    <script>
        // 配置
        const API_BASE = 'http://localhost:8000';

        // 初始化 Session ID
        let sessionId = sessionStorage.getItem('fiido_session_id');
        if (!sessionId) {
            sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            sessionStorage.setItem('fiido_session_id', sessionId);
        }

        // 初始化 Coze Chat SDK
        const chatClient = new CozeWebSDK.WebChatClient({
            config: {
                // Workflow ID (应用对话流)
                workflow_id: 'YOUR_WORKFLOW_ID',  // 替换为您的 Workflow ID
                // 无需 bot_id (因为是应用对话流,不是智能体)
            },
            componentProps: {
                title: 'Fiido 智能客服',
                icon: 'https://your-domain.com/fiido2.png',  // 可选
            },
            auth: {
                type: 'token',
                token: async () => {
                    // 从后端获取 access_token
                    const response = await fetch(`${API_BASE}/api/token/sdk`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ session_id: sessionId })
                    });
                    const data = await response.json();
                    return data.token;
                },
                onRefreshToken: async () => {
                    // Token 刷新逻辑 (同上)
                    const response = await fetch(`${API_BASE}/api/token/sdk`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ session_id: sessionId })
                    });
                    const data = await response.json();
                    return data.token;
                }
            }
        });

        // 打开聊天窗口
        function openChat() {
            chatClient.open();
        }

        // 新对话 (清空历史,创建新 conversation)
        async function newConversation() {
            try {
                const response = await fetch(`${API_BASE}/api/conversation/new`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: sessionId })
                });

                const data = await response.json();
                if (data.success) {
                    alert('✅ 新对话已创建！');
                    // 刷新聊天界面
                    chatClient.close();
                    setTimeout(() => chatClient.open(), 300);
                } else {
                    alert('❌ 创建失败: ' + data.error);
                }
            } catch (error) {
                alert('❌ 请求失败: ' + error.message);
            }
        }

        // 新会话 (全新的 session)
        function newSession() {
            if (confirm('确定要开始新会话吗？这将清空当前所有对话记录。')) {
                sessionStorage.clear();
                window.location.reload();
            }
        }

        // 自动打开聊天窗口 (可选)
        // setTimeout(() => chatClient.open(), 1000);
    </script>
</body>
</html>
```

### 2. 后端实现 (使用 Python SDK)

#### 修改 backend.py

```python
from cozepy import Coze, JWTAuth, JWTOAuthApp

# 在全局变量部分添加
jwt_oauth_app: Optional[JWTOAuthApp] = None

# 在 lifespan 函数中初始化
@asynccontextmanager
async def lifespan(app: FastAPI):
    global jwt_oauth_app, token_manager

    # ... 现有代码 ...

    # 创建 JWTOAuthApp (用于生成 SDK token)
    jwt_oauth_app = JWTOAuthApp(
        client_id=os.getenv("COZE_OAUTH_CLIENT_ID"),
        private_key=open(os.getenv("COZE_OAUTH_PRIVATE_KEY_FILE"), "r").read(),
        public_key_id=os.getenv("COZE_OAUTH_PUBLIC_KEY_ID"),
        base_url=api_base,
    )

    yield


# 新增 API: 为 Chat SDK 生成 token
@app.post("/api/token/sdk")
async def get_sdk_token(request: dict):
    """
    为 Coze Chat SDK 生成 access_token
    带 session_name 实现会话隔离
    """
    session_id = request.get("session_id")

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    try:
        # 使用 Python SDK 生成带 session_name 的 token
        token = jwt_oauth_app.get_access_token(
            ttl=3600,
            session_name=session_id  # ← 会话隔离
        )

        return {
            "success": True,
            "token": token
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# 新增 API: 创建新对话 (新 conversation)
@app.post("/api/conversation/new")
async def create_new_conversation(request: dict):
    """
    创建新对话 (使用 Python SDK)
    保持 session_id 不变,但创建新的 conversation
    """
    session_id = request.get("session_id")

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    try:
        # 获取带 session_name 的 token
        token = jwt_oauth_app.get_access_token(
            ttl=3600,
            session_name=session_id
        )

        # 使用 Python SDK 创建 Coze 客户端
        temp_coze = Coze(
            auth=JWTAuth(oauth_app=jwt_oauth_app),
            base_url=os.getenv("COZE_API_BASE", "https://api.coze.com")
        )

        # 创建新 conversation
        conversation = temp_coze.conversations.create()

        print(f"✅ 新对话已创建: {conversation.id} (session: {session_id})")

        return {
            "success": True,
            "conversation_id": conversation.id
        }
    except Exception as e:
        print(f"❌ 创建对话失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
```

---

## 关键点说明

### 1. Workflow Chat vs Bot Chat

| 项目 | Workflow Chat | Bot Chat |
|------|---------------|----------|
| **配置参数** | `workflow_id` | `bot_id` |
| **适用场景** | 应用对话流 | 智能体 |
| **本项目使用** | ✅ 是 | ❌ 否 |

### 2. 会话隔离实现

```
前端生成 session_id → 存储在 sessionStorage
    ↓
请求后端时携带 session_id
    ↓
后端使用 Python SDK 生成带 session_name 的 token
    ↓
前端 Chat SDK 使用该 token
    ↓
不同用户的对话自动隔离 ✅
```

### 3. 历史对话保留

Coze Chat SDK 自动管理 conversation_id,无需手动处理！

只需要通过 Python SDK 的 `conversations.create()` 创建新对话。

---

## 部署步骤

### 1. 安装依赖

```bash
cd /home/yzh/AI客服/鉴权
pip install cozepy
```

### 2. 配置环境变量

确保 `.env` 文件包含:

```bash
COZE_OAUTH_CLIENT_ID=your_client_id
COZE_OAUTH_PUBLIC_KEY_ID=your_public_key_id
COZE_OAUTH_PRIVATE_KEY_FILE=./private_key.pem
COZE_WORKFLOW_ID=your_workflow_id
COZE_APP_ID=your_app_id
```

### 3. 修改 HTML

将上面的 HTML 代码中的 `YOUR_WORKFLOW_ID` 替换为您的实际 Workflow ID。

### 4. 启动服务

```bash
python3 backend.py
```

### 5. 访问

打开浏览器访问: http://localhost:8000

---

## 测试计划

### 测试 1: 会话隔离

```
1. 打开页面 A (自动生成 session_A)
2. 对话: "我叫张三"
3. 打开新标签页 B (生成 session_B)
4. 对话: "我叫李四"
5. 回到页面 A
6. 对话: "我叫什么?" → 应该回答 "张三" ✅
```

### 测试 2: 新对话

```
1. 对话: "我叫张三"
2. 点击 "新对话" 按钮
3. 对话: "我叫什么?" → 应该回答 "您还没告诉我" ✅
```

### 测试 3: 新会话

```
1. 对话: "我叫张三"
2. 点击 "新会话" 按钮 (页面刷新)
3. 对话: "我叫什么?" → 应该回答 "您还没告诉我" ✅
```

---

## 下一步

1. 修改 `backend.py` 添加新的 API 接口
2. 创建新的 HTML 文件使用 Coze Chat SDK
3. 测试完整功能

是否需要我帮您完成这些修改？
