# PRD 文档目录

本目录包含 Fiido AI客服系统的所有需求和设计文档。

---

## 📖 阅读顺序

### 1️⃣ **必读**：技术约束文档
📘 **[TECHNICAL_CONSTRAINTS.md](./TECHNICAL_CONSTRAINTS.md)** 🔴🔴🔴

**在开发任何功能之前必须阅读此文档！这是最高优先级！**

该文档定义了：
- 🔴 **Coze 平台的不可绕过限制**（SSE流式响应、JWT认证等）
- 🔴 **核心 API 接口的不可变约束**（`/api/chat`, `/api/chat/stream` 等）
- 🔴 **OAuth+JWT 鉴权的强制要求**
- ✅ **允许的功能扩展方向**
- 🧪 **强制性测试标准**

**为什么必须先读？**
1. 避免开发不符合 Coze 平台规范的功能（会导致集成失败）
2. 明确哪些接口不可修改（保护核心功能）
3. 了解正确的扩展方式（在不破坏现有功能的基础上开发）
4. 理解测试要求（确保向后兼容）

**重要性**：⭐⭐⭐⭐⭐ （最高优先级，强制阅读）

**补充参考**：
📘 **[coze.md](./coze.md)** - Coze 平台会话隔离与历史管理的详细说明（第 12 节包含完整的 API 约束规范）

---

### 2️⃣ 产品需求文档
📄 **[prd.md](./prd.md)**

完整的产品需求说明，包括：
- 功能范围和阶段划分（P0/P1/P2）
- AI 监管与人工接管逻辑
- 前后端接口设计
- 数据模型定义

**重要性**：⭐⭐⭐⭐

---

### 3️⃣ API 契约文档
📄 **[api_contract.md](./api_contract.md)**

详细的 API 接口规范，包括：
- 请求/响应格式
- 错误码定义
- 使用示例

**重要性**：⭐⭐⭐⭐

---

### 4️⃣ 任务分解文档

#### 后端任务
📄 **[backend_tasks.md](./backend_tasks.md)**
- 会话状态管理
- 监管引擎
- 人工接管接口

#### 前端任务
📄 **[frontend_client_tasks.md](./frontend_client_tasks.md)**
- 用户界面改造
- 状态展示
- 消息渲染

#### 坐席工作台任务
📄 **[agent_workbench_tasks.md](./agent_workbench_tasks.md)**
- 坐席端功能
- 会话管理
- 快捷操作

#### 邮件与监控任务
📄 **[email_and_monitoring_tasks.md](./email_and_monitoring_tasks.md)**
- 邮件通知
- 工作时间判断
- 监控与告警

---

### 5️⃣ 补充文档

📄 **[implementation_notes.md](./implementation_notes.md)**
- 实施细节和技术选型说明

📄 **[PRD_REVIEW.md](./PRD_REVIEW.md)**
- PRD 评审记录和改进建议

---

## 🚨 开发流程

### Step 1: 阅读约束（强制）
```
✅ 阅读 TECHNICAL_CONSTRAINTS.md（必读！）
✅ 阅读 coze.md 第 12 节（Coze API 约束规范）
✅ 理解 Coze API 限制和不可绕过的技术约束
✅ 理解核心接口的不可变性
```

### Step 2: 理解需求
```
阅读 prd.md（了解产品功能和阶段划分）
阅读对应的任务文档（backend/frontend/agent/email）
查看 api_contract.md（了解接口规范和 Coze 依赖标注）
```

### Step 3: 开发前检查（强制）
```
✅ 是否涉及 Coze API 调用？
   ├─ 是 → 🔴 必须严格遵守 TECHNICAL_CONSTRAINTS.md
   │        - 不得修改核心接口逻辑
   │        - 必须保持 SSE 流式响应
   │        - 必须保持 session_name 隔离
   │        - 必须使用审查清单
   └─ 否 → ✅ 可自由设计，但需保证：
            - 向后兼容现有功能
            - 异常不影响核心对话
            - 通过测试验证

✅ 是否修改了核心接口（/api/chat, /api/chat/stream）？
   ├─ 是 → 🔴 禁止！必须回到 Step 1 重新理解约束
   └─ 否 → ✅ 继续

✅ 是否通过了强制性测试？
   ├─ 否 → 继续开发和测试
   └─ 是 → ✅ 可以提交代码
```

### Step 4: 代码审查（强制）
```
✅ 使用 TECHNICAL_CONSTRAINTS.md 中的检查清单
✅ 验证所有测试用例通过：
   - 基础 AI 对话测试
   - 流式对话测试
   - 会话隔离测试
✅ 确认向后兼容性
✅ 确认 Coze API 调用未被破坏
```

---

## 🔗 相关文档

### 项目文档
- [项目结构说明](../PROJECT_STRUCTURE.md)
- [SDK 使用示例](../docs/guides/SDK使用示例.md)
- [配置指南](../docs/guides/配置指南.md)

### Coze 官方文档
- [Workflow Chat API](https://www.coze.com/docs/developer_guides/workflow_chat)
- [OAuth JWT 认证](https://www.coze.com/docs/developer_guides/oauth_jwt)
- [会话隔离](https://www.coze.com/docs/developer_guides/session_isolation)

---

## ❓ 常见问题

### Q1: 我想修改 `/api/chat` 接口的逻辑，可以吗？
**A**: 🔴 **不可以**。该接口是核心接口，直接调用 Coze API，**必须保持其调用方式不变**。

**你可以做的**：
- ✅ 在接口**前置处理**中添加状态判断（如检查 `session_status`）
- ✅ 在接口**后处理**中添加监管逻辑（如触发人工接管）
- ✅ 添加新的可选参数（不影响现有逻辑）

**你不能做的**：
- ❌ 修改 Coze API 的调用方式（必须使用 `.stream()` 处理 SSE）
- ❌ 修改 SSE 流解析方式（必须从顶层提取 `type` 和 `content`）
- ❌ 修改返回格式（`ChatResponse` 结构不可变）
- ❌ 移除 `session_name` 支持

**参考**：
- [TECHNICAL_CONSTRAINTS.md](./TECHNICAL_CONSTRAINTS.md) 第 4 节 - 核心接口 1: `/api/chat`
- [backend_tasks.md](./backend_tasks.md) - Chat 接口改造示例

### Q2: 我想添加一个新功能，需要怎么做？
**A**: 首先判断是否涉及 Coze API 调用：

**情况 1：涉及 Coze API**（如修改对话流程）
1. 🔴 **强制**：阅读 [TECHNICAL_CONSTRAINTS.md](./TECHNICAL_CONSTRAINTS.md)
2. 🔴 **强制**：使用文档中的审查清单
3. 🔴 **强制**：不能修改核心接口，只能扩展
4. 🔴 **强制**：通过向后兼容性测试

**情况 2：不涉及 Coze API**（如添加邮件通知、工作台等）
1. ✅ 可自由设计数据模型和业务逻辑
2. ⚠️ 但需确保：
   - 不影响现有核心功能
   - 异常不导致核心对话失败
   - 通过向后兼容性测试
3. ✅ 在 [api_contract.md](./api_contract.md) 中标注"无 Coze 依赖"

**示例**：
- ✅ 添加会话状态管理（SessionState）- 无 Coze 依赖，可自由设计
- ✅ 添加监管引擎（Regulator）- 无 Coze 依赖，可自由设计
- ✅ 添加人工接管接口 - 无 Coze 依赖，可自由设计
- 🔴 修改 AI 对话流程 - 有 Coze 依赖，必须遵守约束

### Q3: Coze API 返回的数据格式变了怎么办？
**A**: 🚨 **立即停止开发**，按以下步骤处理：

1. **停止所有开发工作**
2. **更新约束文档**：修改 [TECHNICAL_CONSTRAINTS.md](./TECHNICAL_CONSTRAINTS.md) 中的 Coze API 数据结构说明
3. **修改核心接口**：调整 `/api/chat` 和 `/api/chat/stream` 的解析逻辑
4. **运行完整测试**：执行所有向后兼容性测试和回归测试
5. **更新所有文档**：同步更新 PRD、API Contract 等文档
6. **通知团队**：确保所有开发人员了解变更

**参考**：
- [TECHNICAL_CONSTRAINTS.md](./TECHNICAL_CONSTRAINTS.md) 第 2.2 节 - SSE 事件数据结构

### Q4: 我可以用 WebSocket 替代 SSE 吗？
**A**: 分情况：

**核心 AI 对话功能**：❌ **不可以**
- `/api/chat/stream` 必须保持 SSE 流式响应
- 这是 Coze API 的强制要求，不可绕过
- 参考：[TECHNICAL_CONSTRAINTS.md](./TECHNICAL_CONSTRAINTS.md) 第 2.1 节

**新增功能**（如坐席工作台）：✅ **可以**
- 工作台的实时通信可以使用 WebSocket
- 邮件通知可以使用任何通信方式
- 前提：不影响核心 AI 对话功能

**MVP 建议**：
- P0 阶段：所有功能复用 `/api/chat/stream` SSE 流（简化架构）
- P1 阶段：为工作台添加独立的 WebSocket 通道
- 参考：[prd.md](./prd.md) 第 5.2 节 - 实时推送策略

### Q5: 如何确保我的代码不会破坏现有功能？
**A**: 执行以下强制性测试：

**测试 1：基础 AI 对话测试**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"你好","user_id":"test_001"}'
```
预期：✅ `success: true`，收到有效 AI 回复

**测试 2：流式对话测试**
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message":"你好","user_id":"test_002"}' \
  --no-buffer
```
预期：✅ 实时返回 SSE 事件流，包含 `type:message` 和 `type:done`

**测试 3：会话隔离测试**
```bash
# 两个不同用户发送消息
curl -X POST http://localhost:8000/api/chat \
  -d '{"message":"记住我叫张三","user_id":"user_001"}'

curl -X POST http://localhost:8000/api/chat \
  -d '{"message":"我叫什么？","user_id":"user_002"}'
```
预期：✅ user_002 不应知道 "张三"（会话隔离有效）

**参考**：
- [TECHNICAL_CONSTRAINTS.md](./TECHNICAL_CONSTRAINTS.md) 第 10 节 - 强制性测试要求

---

## 📝 文档维护

### 更新原则
1. **技术约束文档** (`TECHNICAL_CONSTRAINTS.md`) 变更需经过技术负责人审核
2. **PRD 文档** 变更需产品经理和技术负责人共同审核
3. **API 契约** 变更必须向后兼容
4. 所有变更需更新文档版本号和变更记录

### 文档版本
- 主版本号：重大架构变更
- 次版本号：功能新增或修改
- 修订版本号：文档修正和补充

---

**最后更新**: 2025-11-19
**维护者**: 开发团队
