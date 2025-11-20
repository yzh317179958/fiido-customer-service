# Backend 状态存储与 API 拆解

## ⚠️ 强制性 Coze 平台约束

**在开始任何后端开发任务前，必须阅读并遵守以下约束**：

### 🔴 核心约束（不可绕过）

#### 1. Coze API 调用接口 - 不可修改
以下接口涉及 Coze API 调用，**禁止修改其核心逻辑**：
- `/api/chat` - 非流式 AI 对话
- `/api/chat/stream` - 流式 AI 对话（SSE）
- `/api/conversation/new` - 创建会话

**约束细节**：
- ✅ **必须保持**：SSE 流式响应格式（`event:` 和 `data:` 行）
- ✅ **必须保持**：OAuth+JWT 鉴权流程和 `session_name` 隔离机制
- ✅ **必须保持**：Coze API payload 的必需字段（`workflow_id`, `app_id`, `additional_messages`）
- ❌ **禁止修改**：Coze API 响应的解析逻辑（从顶层提取 `type` 和 `content` 字段）
- ❌ **禁止使用**：`.json()` 方法解析响应（必须用 `.stream()` 处理 SSE）

**参考文档**：
- 📘 [TECHNICAL_CONSTRAINTS.md](./TECHNICAL_CONSTRAINTS.md) - 第 2-5 节
- 📘 [coze.md](./coze.md) - 第 12 节

#### 2. 允许扩展的方式
- ✅ **允许**：在 `/api/chat/stream` SSE 流中注入新的事件类型（如 `type:'manual_message'`, `type:'status'`）
- ✅ **允许**：在现有接口**前置处理**中添加状态判断（如检查 `session_status`）
- ✅ **允许**：添加新的独立 API 接口（如 `/api/manual/*`, `/api/sessions/*`）
- ✅ **允许**：在响应返回前添加后处理逻辑（如日志、监控）

#### 3. 开发变更规则

**适用场景**：修改涉及 Coze API 调用的代码

**强制要求**：
1. 变更前必须使用 [TECHNICAL_CONSTRAINTS.md](./TECHNICAL_CONSTRAINTS.md) 中的审查清单
2. 不得修改 `session_name`、`conversation_id` 的传递逻辑
3. 不得移除错误处理和重试机制
4. 必须保留完整的日志输出（包括 session_id、conversation_id）
5. 必须通过向后兼容性测试（核心对话功能、会话隔离）

**示例 - Chat 接口改造**：
```python
# ✅ 正确方式：在不影响 Coze API 调用的基础上添加状态判断
@app.post("/api/chat")
async def chat_async(request: ChatRequest):
    session_id = request.user_id or generate_session_id()

    # ✅ 允许：新增状态判断（前置处理）
    session_state = session_store.get(session_id)
    if session_state and session_state.status == "manual_live":
        return {"success": False, "error": "MANUAL_IN_PROGRESS"}, 409

    # ✅ 必须保持：原有 Coze API 调用逻辑
    access_token = token_manager.get_access_token(session_name=session_id)
    payload = {
        "workflow_id": WORKFLOW_ID,
        "app_id": APP_ID,
        "additional_messages": [
            {
                "content": request.message,
                "content_type": "text",
                "role": "user"
            }
        ]
    }

    # ✅ 必须保持：使用 stream() 接收 SSE
    async with async_http_client.stream(...) as response:
        # 原有解析逻辑...

    # ✅ 允许：响应后处理（如触发监管）
    if session_state:
        regulator_result = regulator.check(message_content)
        if regulator_result.should_escalate:
            session_store.transition(session_id, "pending_manual")

    return ChatResponse(success=True, message=message_content)
```

```python
# ❌ 错误方式：修改 Coze API 调用逻辑
async def chat_async(request: ChatRequest):
    # ❌ 错误：移除了 session_name
    access_token = token_manager.get_access_token()

    # ❌ 错误：使用 .post() 替代 .stream()
    response = await async_http_client.post(...)
    data = response.json()  # 这会失败！
```

---

## 优先级说明
- **P0**：首个 AI 监管版本必须完成，影响端到端闭环。
- **P1**：首版可延后，但需紧随 P0 交付。
- **P2**：优化增强。

## 任务列表
| Priority | 模块 | 任务 | 说明 | 依赖 |
| --- | --- | --- | --- | --- |
| P0 | SessionStateStore | 设计 `SessionState` 数据模型，**仅实现内存版 + 周期性文件快照** | 字段遵循 PRD §8（history≤50、UTC timestamp、audit_trail 独立），提供 `get/save/append_history/transition` | 无 |
| P0 | 监管策略引擎 | 实现关键词/失败次数/VIP 检测函数，支持 `.env` 配置，返回统一 `EscalationResult` | 优先级：VIP > 关键词 > 失败；暂不实现情绪检测 | SessionStateStore |
| P0 | Chat 接口改造 | 在 `/api/chat` / `/api/chat/stream` 中接入状态判断与监管钩子 | `manual_live` 时直接 409；AI 回复结束后统计 `ai_fail_count` 并触发 `Regulator` | SessionStateStore |
| P0 | 核心 API | 实现 `/api/manual/escalate`, `/api/sessions/{session}`, `/api/manual/messages`, `/api/sessions/{session}/release` | 仅保留 4 个核心接口；其余接口延后到 P1 | SessionStateStore, JWT |
| P0 | SSE 增量推送 | 复用 `/api/chat/stream`，在人工阶段向同一 SSE 通道注入 `manual_message/status` 事件 | 无需 WebSocket；确保 Coze 流式事件与人工事件有序写入 | SessionStateStore |
| P0 | 日志规范 | 所有状态流转、人工操作写入 `backend.log` JSON 行 | 字段：`event`, `session_name`, `status_from`, `status_to`, `operator`, `timestamp` | SessionStateStore |
| P1 | ShiftConfig Provider | 解析 `.env`（班次/节假日）并提供 `is_in_shift()`、`/api/shift/config` | 供监管与前端使用 | 无 |
| P1 | 邮件触发器调用点 | 进入 `after_hours_email` 时触发邮件模块并更新 `SessionState.mail` | 参见 `email_and_monitoring_tasks.md` | ShiftConfig, Email 模块 |
| P1 | 坐席接口 | `/api/sessions`, `/api/sessions/{session}/takeover`, `/api/sessions/{session}/email` | 工作台依赖；实现抢接校验 | SessionStateStore |
| P2 | Metrics | 暴露 `/metrics`（Prometheus）记录人工接管、邮件等指标 | 后续可引入 Redis + WebSocket | SessionStateStore |

## 交付件
1. `session_state.py`（或同等模块）定义数据结构与存储实现。  
2. FastAPI 路由更新 + 新增路由单元测试。  
3. 文档：更新 `README.md`/`docs`，描述新接口和状态。
