# 客服工作台开发任务

## ⚠️ 技术约束声明

**工作台功能与核心 Coze API 解耦，可自由设计**：

### ✅ 无 Coze 依赖 - 允许自由开发

工作台所有功能**不直接调用 Coze API**，属于独立业务模块：

**约束级别**：✅ **可自由设计**

**说明**：
- ✅ 工作台接口调用的是本地会话管理 API（`/api/sessions`, `/api/manual/*`）
- ✅ 这些接口不涉及 Coze API 调用，可以自由设计数据模型和业务逻辑
- ⚠️ 但需确保：工作台功能异常不影响核心 AI 对话功能

**注意事项**：
1. 工作台通过 `/api/chat/stream` 的 SSE 流接收消息（复用现有机制）
2. 工作台发送人工消息时调用 `/api/manual/messages`（新增接口）
3. 必须遵守 JWT 鉴权要求（`role=agent`）

**参考文档**：
- 📘 [TECHNICAL_CONSTRAINTS.md](./TECHNICAL_CONSTRAINTS.md) - 第 9 节（允许的扩展方向）
- 📘 [api_contract.md](./api_contract.md) - 新增接口规范

---

## 目标
为坐席提供独立的 Vue 工作台（推荐新建 `frontend-agent/` 子项目，方便鉴权/部署），支持队列、历史、实时聊天。根据评审结论，工作台整体定为 **P1**，在核心 MVP 成熟后再实现。

## 优先级
- **P1**：完成最小可用的坐席接管能力。
- **P2**：体验增强，如快捷短语、搜索、质检。

## 任务
| Priority | 功能块 | 任务 | 说明 | 主要依赖 |
| --- | --- | --- | --- | --- |
| P1 | 项目骨架 | 新建 `frontend-agent/`（或在现有项目中独立路由）并集成 OAuth/JWT 登录 | 必须校验 `role=agent`，只允许坐席访问 | 后端 JWT 自定义 claims |
| P1 | 会话队列 | `SessionList` 组件展示 `pending_manual`、`manual_live`、`after_hours_email` | 先使用轮询或 SSE；WebSocket 放在 P2 | `/api/sessions` |
| P1 | 接管操作 | 在会话详情中调用 `/api/sessions/{session}/takeover`，处理抢接冲突 | 接入成功后写入 `assigned_agent` | Backend API |
| P1 | 聊天面板 | 渲染 `history` 并通过 `/api/manual/messages` 发送人工回复 | MVP 阶段复用 SSE/轮询获取用户消息 | Backend API |
| P1 | 结束操作 | `release` 按钮调用 `/api/sessions/{session}/release`，刷新队列 | 完成后提示“AI 已接管” | Backend API |
| P2 | 快捷短语/模板 | 配置 5+ 常用回复，支持插入和搜索 | 数据来源 `.env` 或后端接口 | 无 |
| P2 | 状态日志 | 在详情页展示 `audit_trail` | 可用于质检回溯 | Backend logging |
| P2 | 搜索/过滤 | 按 session/user 信息过滤队列 | 支持关键字 + 状态筛选 | `/api/sessions` |
| P2 | 邮件补回 | 在 `after_hours_email` 列表中提供“补回”操作 | 点击后触发 `takeover` 并重置状态 | Email 模块 + Backend API |

## 交付件
1. 前端页面/组件 + 样式。  
2. 与后端联调脚本，演示坐席接入流程。  
3. 用户手册更新，包含坐席使用说明。
