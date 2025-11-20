# 邮件通知与监控任务

## ⚠️ 技术约束声明

**邮件和监控功能与核心 Coze API 完全解耦**：

### ✅ 无 Coze 依赖 - 允许自由开发

邮件通知和监控模块**不涉及 Coze API 调用**，属于独立业务功能：

**约束级别**：✅ **可自由设计**

**说明**：
- ✅ 邮件触发基于本地会话状态判断（`after_hours_email` 状态）
- ✅ 监控指标来源于本地业务逻辑（状态转换、接管次数等）
- ✅ ShiftConfig 是纯配置管理，与 Coze 平台无关
- ⚠️ 确保：邮件发送失败不应影响核心 AI 对话功能

**注意事项**：
1. 邮件内容包含会话历史时，需从本地 SessionState 获取，不直接调用 Coze API
2. 监控指标应记录核心接口（`/api/chat`）的调用情况，但不修改其逻辑
3. 告警触发不应干扰正常对话流程

**参考文档**：
- 📘 [TECHNICAL_CONSTRAINTS.md](./TECHNICAL_CONSTRAINTS.md) - 第 9 节（允许的扩展方向）
- 📘 [prd.md](./prd.md) - 第 10 节（非功能需求）

---

## 范围
- 工作时间外邮件转交
- ShiftConfig 配置
- 指标、告警

## 优先级
- **P1**：完成工作时间判断 + 邮件转交（工作台上线前准备）
- **P2**：监控与可观测增强

## 任务列表
| Priority | 模块 | 任务 | 说明 |
| --- | --- | --- | --- |
| P1 | ShiftConfig | 解析 `.env`（`HUMAN_SHIFT_START/END`, `TIMEZONE`, `WEEKENDS_DISABLED`, `HOLIDAYS`）并提供 `is_in_shift()` | 暴露 `GET /api/shift/config` 供前端/工作台使用 |
| P1 | 邮件模板 | 设计邮件内容（用户信息、最近 10 条消息、触发原因、期望响应时间） | Markdown/HTML 模板，支持多收件人 |
| P1 | 邮件发送器 | 支持 SMTP 或企业邮 API，封装 `send_manual_escalation_email(session_state)` | 需重试 3 次 + 失败日志 |
| P1 | 会话标记 | 邮件发送成功后更新 `SessionState.mail` 字段，并写入系统消息 | 与 Backend 状态机联动 |
| P2 | 邮件重试/队列 | 失败时入队，后台重试 & 可手动补发 | 记录 `mail_retry_count` |
| P2 | 监控指标 | 暴露 `manual_escalation_total`, `after_hours_email_total`, `mail_failure_total` | `/metrics` 或日志采集 |
| P2 | 告警渠道 | 邮件/Slack/钉钉 通知队列积压 > SLA | 与 `pending_manual` 等状态联动 |

## 交付
1. `shift_config.py` + 测试。  
2. `email_service.py` + SMTP 配置示例。  
3. 运维文档：如何配置邮箱、如何验证监控。
