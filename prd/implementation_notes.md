# Implementation Notes for AI 监管/人工接管

面向即将编写代码的同学，以下是落地时需注意的关键点与建议顺序。

## 1. 推荐开发顺序
1. **SessionStateStore MVP**：先在内存实现，接口包含 `get/ save / append_history / transition`，并定期写入 JSON 快照。之后才抽象 Redis 版本。
2. **监管逻辑嵌入**：在 `/api/chat` 与 `/api/chat/stream` 单一入口调用 `Regulator`，通过 `ensure_session_state(session_name)` 自动创建会话。
3. **核心 API**：先实现 `manual/escalate`、`sessions/{session}`、`manual/messages`、`release`，并打通 SSE 推送；`takeover`/`sessions list` 等放在 P1。
4. **工作时间/邮件（P1）**：待 MVP 稳定后加入 `ShiftConfig`、邮件模块，把 `after_hours_email` 流转串起来。
5. **工作台（P1）**：在后端接口稳定后再搭建独立 Vue 子项目，后续再考虑 WebSocket。

## 2. Regulator 设计建议
```python
class EscalationResult(BaseModel):
    should_escalate: bool
    reason: Literal['keyword', 'fail_loop', 'vip', 'manual']
    severity: Literal['low','high']
    details: str
```
- Keywords 列表可在 `.env` 设置 `REGULATOR_KEYWORDS="人工,真人,投诉"`，启动时解析为 set。
- 连续失败统计：在 `SessionState` 中维护 `ai_fail_count`; 每次 AI 回复 fallback 时 +1，否则归零。
- 情绪检测延后到 P2，避免 MVP 复杂化。
- VIP：前端将 `parameters.vip` 传给 `/api/chat`，后端写入 `SessionState.user_profile.vip`。

## 3. SessionState 持久化
- MVP 可使用 `dict[str, SessionState]`；提供线程锁或 `asyncio.Lock` 保障并发，并定期序列化到 `session_state_snapshot.json`。
- 请封装 `SessionRepository` 接口，方便后续替换成 Redis。
- `history` 仅保留最近 50 条消息，超出部分写入归档或磁盘文件。

## 4. 日志规范
- 每次状态切换调用 `log_state_transition(session_name, from_, to_, operator)`。
- 邮件/接管等关键动作写 JSON 行到 `backend.log`，字段 `event`, `session_name`, `operator`, `meta`。
- 方便后续 ELK/CloudWatch 检索。

## 5. 前端集成要点
- Pinia store 增加 `sessionStatus`, `escalationInfo`, `manualChannelReady` 等字段。
- 建议定义枚举 `enum SessionStatus { BOT = 'bot_active', PENDING = 'pending_manual', MANUAL = 'manual_live', AFTER_HOURS = 'after_hours_email' }`。
- 所有组件仅引用 store 状态，便于单测/调试。

## 6. 工作台架构建议（P1）
- 建议新建 `frontend-agent/` 工程，避免与用户端耦合。可共用公共 UI 库，但业务逻辑隔离。
- API 层独立：在 `frontend-agent/src/api` 内封装 `fetchSessions`, `takeover`, `sendManualMessage`, `release` 等。
- 状态管理仍使用 Pinia，state 包含 `queues`, `activeSession`, `agentProfile`, `filters`。
- MVP 阶段仍以轮询/SSE 获取数据；WebSocket 工具留待 P2。

## 7. 邮件模块实现提示（P1）
- 配置：`SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS`。
- 推荐封装 `EmailClient` 类，暴露 `send_manual_alert(session_state: SessionState) -> str` 返回 message_id。
- 错误处理：捕获 `smtplib.SMTPException`，记录日志并在 `SessionState.mail` 标记 `sent=False, error=...`。

## 8. 测试建议
- 单元测试：`tests/test_regulator.py`, `tests/test_session_store.py`, `tests/test_manual_messages_api.py`。
- 集成测试：使用 FastAPI TestClient 模拟 `POST /api/chat`（触发关键词）→ `POST /api/manual/messages` (agent) → `POST /api/manual/messages` (user) → `POST /release`，确保状态切换和 SSE 事件顺序正确。
- 待 P1 实现后，再补 `test_shift_config.py`、邮件/工作台相关测试。

## 9. 常见坑
- **token 刷新**：人工阶段仍需沿用当前 `session_name`，不要重新生成。`session_id` 必须与 Pinia store 同步。
- **并发**：可能多位坐席抢接同一会话，务必在服务端实现 CAS 并返回明确错误码。
- **历史顺序**：人工消息和 AI 消息时间线需按 `timestamp` 排序；前端渲染时根据 `role` 赋样式。
- **邮件重复**：避免短时间内重复发送，可在 `SessionState.mail.sent` 为 true 时跳过。

---
如需补充更多范例或图示，可在 `prd/` 目录继续添加文件。
