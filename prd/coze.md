# Coze 会话隔离与历史管理 PRD

## 1. 背景

- 现有 Coze Workflow Chat 集成中，前端所有用户共享静态 `conversation_id`，导致多用户上下文混淆。
- 业务侧希望通过 `session_name` 区分不同访客，配合 OAuth + JWT 分配独立访问令牌，实现真正的对话隔离。
- UI 新增扩展按钮，需要与 Python SDK 协同完成会话清理与新建，同时保持前端即时反馈、后端异步处理。
- 所有扩展需严格遵守 Coze 平台 API 规则，避免破坏既有功能或越权调用。

### 1.1 Coze Conversation ID 核心机制

**根据 Coze Python SDK (conversation.py) 的官方实现及实际测试验证：**

1. **动态生成特性**：通过 `conversations.create()` API 显式创建会话，由 Coze 自动生成唯一会话 ID
2. **用户隔离**：结合 `user_id` (在本系统中对应 `session_name`) 可实现严格的用户隔离
3. **静态会话影响**：即使对话流绑定了静态会话（如 "default"），也仅影响会话的"逻辑归属"，不改变 `conversation_id` 的动态生成特性
4. **上下文维持规则**：
   - **首次对话（不传 conversation_id）**：Coze 会自动生成新的 `conversation_id` 并在响应中返回
   - **后续对话（传入 conversation_id）**：Coze 继续使用该会话 ID，维持多轮上下文

### 1.2 ⚠️ 重要发现：会话隔离的正确实现方式（亲测有效）

**问题现象**：
在实际测试中发现，即使在 JWT Payload 和 API 请求中都正确传入了不同的 `session_name`，如果依赖首次对话时 Coze 自动生成 `conversation_id`，Coze API **仍然可能返回相同的 `conversation_id`**，导致不同用户共享对话上下文。

**根本原因**：
Coze API 在首次对话自动生成 `conversation_id` 时，可能基于内部逻辑复用已存在的 conversation 资源，即使 `session_name` 不同。

**✅ 正确的实现方式**（已验证）：

**必须在用户打开页面时，立即调用 `conversations.create()` API 预先创建 conversation**，而不是依赖首次对话时的自动生成。

**实现步骤**：
1. 前端页面加载时，立即生成唯一的 `session_id`
2. **立即调用后端 `/api/conversation/new` 接口**
3. 后端使用带 `session_name` 的 token 调用 `conversations.create()`
4. Coze 返回唯一的 `conversation_id`（每个 session 都不同）
5. 前端保存 `conversation_id` 到内存
6. 后续所有对话携带这个预先创建的 `conversation_id`

**为什么这样有效**：
- 显式调用 `conversations.create()` + 带 `session_name` 的 token
- Coze 会为每个 session 创建独立的 conversation 资源
- 返回完全不同的 `conversation_id`
- 后续对话使用这个预创建的 ID，确保完全隔离

**实测对比**：

❌ **错误方式**（依赖首次对话自动生成）：
```
Session A: session_xxx_111 → Conversation: 7572584214371631109
Session B: session_xxx_222 → Conversation: 7572584214371631109  ← 相同！
Session C: session_xxx_333 → Conversation: 7572584214371631109  ← 相同！
```

✅ **正确方式**（预先调用 create）：
```
Session A: session_xxx_111 → Conversation: 7574615036068397061
Session B: session_xxx_222 → Conversation: 7574617557825863685  ← 不同！
Session C: session_xxx_333 → Conversation: 7574616000908738565  ← 不同！
```

**实现要求**：
- ✅ 用户**打开页面时立即调用会话创建接口**，预先生成 `conversation_id`
- ✅ 后端使用 `conversations.create()` API 而非依赖自动生成
- ✅ 后端存储映射关系：`session_name` → `conversation_id`
- ✅ 后续调用时传入预先创建的 `conversation_id` 以维持上下文
- ✅ 清除历史或创建新对话时，重新调用 `create()` 生成新的 `conversation_id`

**参考文档**：
详见 `Coze会话隔离最终解决方案.md`（亲测有效）

## 2. 目标

1. 为每个 `session_name` 生成并绑定独立 JWT，任何请求都在 token 维度隔离。
2. 新访客进入时**首次必须调用会话创建接口**，生成动态 `conversation_id`，支撑 Coze 多轮上下文。
3. 严格遵守 Coze API 约束，确保所有开发符合平台规范。
4. 使用 Python SDK 管理 conversation 历史，支持保留、清除与新建，避免内存泄漏。
5. UI 扩展按钮提供「清除历史会话」「创建新对话」操作，交互无明显延迟。
6. 功能扩展覆盖后端、前端、认证、日志，且不突破 Coze 平台接口约束。

## 3. 范围

- **包含**：OAuth 授权、JWT 签发、会话生命周期管理、Python SDK 封装、前端交互与状态同步、监控与回滚方案。
- **不包含**：Coze 平台能力以外的 Bot 改造、复杂权限系统、长期用户身份管理（仅依赖前端临时 `session_name`）。

## 4. 角色与用户旅程


| 角色                            | 触发场景                  | 期望体验                                                      |
| ------------------------------- | ------------------------- | ------------------------------------------------------------- |
| 新访客（自动生成 session_name） | 打开前端页面              | 页面立即可输入，对话历史为空，后台已生成 token + conversation |
| 活跃访客                        | 连续发起多轮对话          | 历史上下文持续存在，刷新页面被视为全新访客                    |
| 访客触发扩展按钮                | 清除历史会话 / 创建新对话 | UI 即刻响应（下划线/清屏），后台调用对应接口                  |
| 运维/开发                       | 监控与调试                | 可通过日志追踪 session、token、conversation 关联关系          |

## 5. 需求明细


| 编号 | 描述                   | 细节                                                                                                                 |
| ---- | ---------------------- | -------------------------------------------------------------------------------------------------------------------- |
| FR1  | `session_name` 唯一化  | 前端加载时生成 UUID（或业务规则），关闭页面重开即新`session_name`；随请求传至后端                                    |
| FR2  | OAuth + JWT 隔离       | 后端基于`session_name` 获取/刷新 OAuth token，签发携带 `session_name` 的 JWT（过期时间、签名算法参照现有安全策略）   |
| FR3  | 动态 conversation 创建 | 每个新`session_name` 先调用 Coze 创建 conversation，存储在后端会话缓存/DB，并随 JWT 반환                             |
| FR4  | Python SDK 历史保留    | SDK 调用 workflow/chat 时带上对应`conversation_id`；使用上下文存储池（LRU/弱引用）避免长时间常驻内存                 |
| FR5  | 清除历史会话           | 前端触发后立即在 UI 插入一条下划线，后端调用 SDK 清空 conversation 历史（或重新创建）；完成后状态同步                |
| FR6  | 创建新对话             | 前端清空所有聊天记录并展示 loading，占位即可；后端创建新 conversation（同一个`session_name` 下）并更新 token payload |
| FR7  | Coze 约束              | 所有 API 参数遵循官方限制，不复用未授权接口；新增功能不得修改 Coze 平台默认规则，除非与 Coze 无关                    |
| NFR1 | 性能                   | 前端操作瞬时响应；后端异步处理不超过 2s；异常时 UI 展示 toast                                                        |
| NFR2 | 安全                   | JWT 在 HTTPS + HttpOnly 环境传输；token 与 conversation 映射需审计日志                                               |
| NFR3 | 稳定性                 | SDK 调用失败需重试 / fallback（例如重建 conversation）；避免内存泄漏                                                 |

## 6. 业务流程

1. **前端初始化**
   - 生成 `session_name`，展示空对话 UI。
   - 调用 `/auth/token`（示例）换取 JWT；后台完成 OAuth、token 缓存、conversation 创建，返回 `conversation_id`。
2. **普通聊天**
   - 前端发送消息携带 JWT、`session_name`、`conversation_id`。
   - 后端验证 JWT，调度 Python SDK `workflows.chat.stream`，带 `conversation_id` 保持上下文。
3. **清除历史会话**
   - 前端立即插入下划线分隔，并调用 `/conversation/clear`。
   - 后端调用 SDK 清除缓存或强制重启 conversation（保留同 ID 或生成新 ID，视 Coze 能力决定），写日志。
4. **创建新对话**
   - 前端清空面板，展示“新对话已创建”提示。
   - 后端创建全新 `conversation_id`，与当前 `session_name` 绑定并返回。
5. **页面关闭/刷新**
   - 浏览器事件导致旧 `session_name` 废弃；重新加载即走步骤 1，老 conversation 由后端回收策略处理。

## 7. API 设计（示例）


| 接口                      | 方法 | 主要入参                                            | 返回                                   | 说明                                      |
| ------------------------- | ---- | --------------------------------------------------- | -------------------------------------- | ----------------------------------------- |
| `/api/auth/token`         | POST | `session_name`, 浏览器指纹                          | `jwt`, `conversation_id`, `expires_in` | 完成 OAuth + JWT 签发 + conversation 创建 |
| `/api/chat/stream`        | POST | `message`, `session_name`, `conversation_id`, `jwt` | 流式回复                               | 需校验 JWT 与 session                     |
| `/api/conversation/clear` | POST | `session_name`, `conversation_id`                   | `status`, `conversation_id`            | 清除历史记录，可能返回同 ID 或新的 ID     |
| `/api/conversation/new`   | POST | `session_name`                                      | `conversation_id`                      | 创建全新对话，供前端刷新状态              |

> **注意**：所有接口调用 Coze SDK 时必须遵循官方速率限制、参数校验和鉴权方式，禁止私自修改 Coze 规则。

## 8. 数据与状态管理

- `session_name`：来源于前端临时生成，只在客户端生命周期内有效。
- `jwt`：payload 包含 `session_name`、`conversation_id`、token 颁发时间；存储在 HttpOnly Cookie 或安全存储。
- `conversation_id`：后端持久或缓存保存，确保同 session 多次请求复用；清除/新建时及时更新。
- `token ↔ conversation` 映射：建议使用 Redis / 内存缓存 + 定期清理，避免内存泄漏。

## 9. UI/UX 细节

- 扩展按钮展开两项：
  1. **清除历史会话**：点击后当前对话框内立即插入一条横向下划线，表示上下文断点，不阻塞输入框；后端异步处理异常时提示“清除失败，可重试”。
  2. **创建新的对话**：点击后立即清空聊天区域并显示“正在创建新对话...”；收到后台成功响应后更新隐藏状态中的 `conversation_id`。
- 所有操作需要无感延迟（<100ms UI 响应），后台处理可异步。

## 10. 监控与风险

- **监控**：JWT 签发次数、conversation 创建/清理耗时、Coze API 错误率、内存使用。
- **风险**：
  - Coze API 限流：需缓存 token、实现指数退避重试。
  - 内存泄漏：Python SDK 的 conversation 缓存需定期释放，可使用 weakref/LRU。
  - 前端 session 丢失：需检测 localStorage/内存状态，若缺失则重新走初始化流程。

## 11. 交付验收标准

- 能在本地/测试环境中模拟多浏览器窗口，互不干扰。
- 清除历史/新建对话前端动作即时可见，后端日志可查。
- JWT 与 conversation 关联可追踪，超时策略符合安全要求。
- 不触发 Coze 平台违规或异常报警。

---

## 12. Coze API 约束规范（强制遵守）

### 12.1 核心约束

**所有涉及 Coze API 调用的开发必须严格遵守以下规范：**

#### 1. Conversation ID 管理规范

**必须遵守：**
```python
# ✅ 正确：首次对话不传 conversation_id，让 Coze 自动生成
payload = {
    "workflow_id": WORKFLOW_ID,
    "app_id": APP_ID,
    "session_name": session_id,
    "parameters": {"USER_INPUT": message},
    # 注意：首次对话不包含 conversation_id 字段
}

# ✅ 正确：后续对话传入 conversation_id 维持上下文
payload = {
    "workflow_id": WORKFLOW_ID,
    "app_id": APP_ID,
    "session_name": session_id,
    "conversation_id": "7568xxx",  # 从首次响应中获取
    "parameters": {"USER_INPUT": message},
}
```

**禁止操作：**
```python
# ❌ 错误：手动生成 conversation_id（必须由 Coze 生成）
conversation_id = f"conv_{uuid.uuid4()}"

# ❌ 错误：跨用户共享 conversation_id
# 每个 session_name 必须有独立的 conversation_id
```

#### 2. Session Name 规范

**必须遵守：**
- `session_name` 必须在 JWT token 和 API 请求中保持一致
- 每个用户会话（浏览器窗口）生成唯一的 `session_name`
- `session_name` 格式建议：`session_{timestamp}_{random}`

**禁止操作：**
- 多个用户共享同一个 `session_name`
- 修改 Coze 返回的 `session_name` 字段

#### 3. Token 管理规范

**必须遵守：**
```python
# ✅ 正确：使用 JWTOAuthApp 生成带 session_name 的 token
token = jwt_oauth_app.get_access_token(
    ttl=3600,
    session_name=session_id  # 会话隔离关键
)
```

**禁止操作：**
- 跨 `session_name` 复用 token
- 修改 token 过期时间超过 Coze 限制（最大 86400 秒）
- 绕过 OAuth 流程直接使用 PAT token（除非明确配置为 PAT 模式）

#### 4. Workflow Chat API 参数规范

**必须包含的字段：**
```json
{
  "workflow_id": "必需",
  "app_id": "必需（应用中嵌入对话流时）",
  "session_name": "必需（会话隔离）",
  "parameters": {
    "USER_INPUT": "必需（用户输入）"
  },
  "additional_messages": [
    {
      "content": "必需（消息内容）",
      "content_type": "text",
      "role": "user",
      "type": "question"
    }
  ],
  "conversation_id": "可选（首次不传，后续必传）"
}
```

**禁止操作：**
- 省略 `session_name` 字段
- 在 `parameters` 中注入未定义的变量
- 修改 `additional_messages` 的标准格式

#### 5. 响应处理规范

**必须处理的字段：**
```python
# ✅ 正确：提取 conversation_id 并保存
if 'conversation_id' in data and not returned_conversation_id:
    returned_conversation_id = data['conversation_id']
    # 保存映射关系
    conversation_cache[session_id] = returned_conversation_id
```

**禁止操作：**
- 忽略 Coze 返回的 `conversation_id`
- 不保存 `conversation_id` 导致上下文丢失

### 12.2 开发变更规则

#### 规则 1：Coze API 调用代码变更

**适用场景：** 修改涉及 Coze API 调用的代码（如 `/api/chat`、`/api/conversation/*`）

**强制要求：**
1. 变更前必须审查是否符合上述约束规范
2. 不得修改 `session_name`、`conversation_id` 的传递逻辑
3. 不得移除错误处理和重试机制
4. 必须保留完整的日志输出（包括 session_id、conversation_id）

**示例：**
```python
# ✅ 允许：在不影响核心逻辑的基础上扩展功能
# 例如：添加消息历史记录功能
payload = {
    "workflow_id": WORKFLOW_ID,
    "app_id": APP_ID,
    "session_name": session_id,  # 保持不变
    "conversation_id": conversation_id,  # 保持不变
    "parameters": {
        "USER_INPUT": request.message,
        "CONTEXT": get_message_history(session_id)  # 新增功能
    },
}

# ❌ 禁止：移除 session_name
payload = {
    "workflow_id": WORKFLOW_ID,
    "app_id": APP_ID,
    # "session_name": session_id,  # ❌ 移除了必需字段
    "parameters": {"USER_INPUT": request.message},
}
```

#### 规则 2：功能扩展（无冲突）

**适用场景：** 新增功能不涉及 Coze API 调用逻辑

**无需遵守：** 可以自由开发，无需严格遵守 Coze 约束

**示例：**
- 添加消息缓存机制
- 实现用户偏好设置
- 开发管理后台
- 集成第三方分析工具

### 12.3 常见错误案例

#### ❌ 错误 1：手动管理 conversation_id
```python
# 错误示例
conversation_id = f"conv_{session_id}"  # 不应手动生成
```

**正确做法：**
```python
# 首次对话：不传 conversation_id
# Coze 会在响应中返回自动生成的 conversation_id
```

#### ❌ 错误 2：省略 session_name
```python
# 错误示例
token = jwt_oauth_app.get_access_token(ttl=3600)  # 缺少 session_name
```

**正确做法：**
```python
token = jwt_oauth_app.get_access_token(
    ttl=3600,
    session_name=session_id  # 必须传入
)
```

#### ❌ 错误 3：不保存 conversation_id
```python
# 错误示例：处理响应但不保存
for line in response.iter_lines():
    data = json.loads(line)
    # 忽略了 conversation_id
```

**正确做法：**
```python
for line in response.iter_lines():
    data = json.loads(line)
    if 'conversation_id' in data:
        conversation_cache[session_id] = data['conversation_id']
```

### 12.4 审查清单

**在修改 Coze 相关代码前，请确认：**

- [ ] 是否保留了 `session_name` 字段？
- [ ] 是否正确处理 `conversation_id`（首次不传，后续传入）？
- [ ] 是否保存了 Coze 返回的 `conversation_id`？
- [ ] 是否在 token 生成时传入了 `session_name`？
- [ ] 是否保留了完整的错误处理和日志？
- [ ] 是否符合 Coze API 参数规范？
- [ ] 是否测试了多用户隔离场景？

### 12.5 紧急回滚预案

如果发现 Coze API 调用异常：

1. **立即检查**：是否修改了 `session_name` 或 `conversation_id` 逻辑
2. **查看日志**：确认 API 请求参数是否完整
3. **回滚代码**：恢复到上一个稳定版本
4. **重新测试**：验证会话隔离功能是否正常

---

## 13. 实施优先级

1. **P0（必须）**：Conversation ID 动态管理（首次不传，后续传入）
2. **P0（必须）**：Session Name 隔离（token 和 API 请求一致）
3. **P1（重要）**：清除历史会话 API 实现
4. **P1（重要）**：前端交互优化（按钮和反馈）
5. **P2（建议）**：监控和日志完善
