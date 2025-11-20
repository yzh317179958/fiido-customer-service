# PRD 技术评审报告

## 评审信息
- **评审时间**: 2025-01-19
- **评审人**: Claude Code
- **PRD 版本**: v2.1
- **当前系统版本**: v3.0.0

---

## 一、整体评价

### ✅ 优势
1. **需求清晰**: PRD 对人工接管功能的描述完整,包含用户端、工作台、后端各层面
2. **架构兼容**: 充分考虑了现有 `backend.py`、`frontend/` 的结构,扩展性设计合理
3. **文档完整**: API 契约、实现建议、任务拆解都很详尽
4. **优先级明确**: P0/P1/P2 划分清晰,便于分阶段实施

### ⚠️ 需要调整的地方
1. **技术栈适配**: 部分设计需要根据现有技术栈调整
2. **实现复杂度**: 某些功能可以简化,降低初期实现难度
3. **状态管理**: 需要更明确的状态机设计
4. **安全性**: JWT 角色校验需要补充实现细节

---

## 二、技术适配性评审

### 2.1 后端架构 (FastAPI)

#### ✅ 完全适配
- **现有基础**: `backend.py` 已有完善的 FastAPI 框架
- **OAuth/JWT**: `OAuthTokenManager` 和 `JWTOAuthApp` 已实现
- **会话机制**: `session_name` 机制已验证可用
- **流式接口**: `/api/chat/stream` SSE 实现完善

#### ⚠️ 需要调整
1. **WebSocket 实现**
   - **PRD 建议**: 使用 WebSocket 实现实时通道
   - **调整建议**:
     - 阶段1: 先用 SSE 长轮询实现 (复用现有技术)
     - 阶段2: 再升级到 WebSocket (需要前端配合改造)
   - **理由**: 当前前端已完善 SSE 处理,WebSocket 需要额外开发和测试

2. **持久化存储**
   - **PRD 建议**: Redis 或内存字典
   - **调整建议**:
     - MVP 阶段: 使用内存字典 + 文件持久化备份
     - 生产阶段: 升级到 Redis
   - **理由**: 避免引入新的基础设施依赖,降低部署复杂度

3. **JWT 角色校验**
   - **PRD 要求**: JWT 中需要包含 `role` 字段
   - **现状**: 当前 JWT 只包含 `session_name`
   - **调整建议**: 扩展 `JWTSigner` 支持自定义 claims,添加 `role` 字段
   - **实现**: 修改 `src/jwt_signer.py` 和 `OAuthTokenManager`

### 2.2 前端架构 (Vue 3 + TypeScript)

#### ✅ 完全适配
- **状态管理**: Pinia `chatStore` 已有完善的状态管理
- **消息类型**: `Message` 类型扩展 `role: 'agent'` 简单直接
- **API 层**: `api/chat.ts` 结构清晰,易于扩展

#### ⚠️ 需要调整
1. **工作台实现**
   - **PRD 建议**: 在 `frontend/` 中新增工作台路由
   - **调整建议**:
     - 阶段1: 创建独立的 `frontend-agent/` 项目 (代码隔离)
     - 阶段2: 根据需要合并到主项目
   - **理由**: 用户端和工作台的权限、功能差异大,独立项目便于开发和部署

2. **实时通道切换**
   - **PRD 建议**: 人工阶段改用 `/ws/client/{session_name}`
   - **调整建议**: 复用 `/api/chat/stream`,通过 `role` 区分消息来源
   - **理由**: 减少前端改造,保持接口一致性

### 2.3 监管策略引擎

#### ✅ 设计合理
- 关键词检测、连续失败、VIP 判断都符合实际需求
- 可配置化设计便于后续调整

#### ⚠️ 需要优化
1. **情绪检测**
   - **PRD 建议**: 情绪模型或 Coze 角色
   - **调整建议**: MVP 阶段暂不实现,使用关键词 + 失败次数已足够
   - **理由**: 情绪检测准确性要求高,需要大量调试,非核心功能

2. **触发策略优先级**
   - **新增建议**: 明确多个策略同时触发时的优先级
   - **建议顺序**: VIP > 关键词 > 连续失败 > 情绪

---

## 三、数据结构优化建议

### 3.1 SessionState 简化

**PRD 设计**:
```python
{
  "session_name": "string",
  "status": "bot_active | pending_manual | manual_live | after_hours_email | closed",
  "conversation_id": "string",
  "user_profile": {...},
  "history": [...],
  "escalation": {...},
  "assigned_agent": {...},
  "mail": {...},
  "last_manual_end_at": "ISO"
}
```

**优化建议**:
1. **history 限制**: 最多保留最近 50 条消息,超过部分归档
2. **user_profile 简化**: MVP 阶段只保留 `nickname` 和 `vip`,其他字段后续扩展
3. **audit_trail 分离**: 状态变更日志单独存储,不放在 SessionState 中
4. **时间戳统一**: 使用 UTC 时间戳 (int),前端展示时转换为本地时区

### 3.2 Message 扩展

**现有结构**:
```typescript
interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: number;
  sender?: string;
}
```

**扩展建议**:
```typescript
interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system' | 'agent';  // 新增 agent
  timestamp: number;
  sender?: string;
  agent_info?: {  // 新增:人工客服信息
    agent_id: string;
    agent_name: string;
  };
}
```

---

## 四、API 设计调整

### 4.1 保持现有接口不变

| 接口 | 说明 | 调整 |
|------|------|------|
| `POST /api/chat` | 同步聊天 | 增加状态判断,`manual_live` 时返回 409 |
| `POST /api/chat/stream` | 流式聊天 | 增加监管逻辑,自动触发人工 |
| `POST /api/conversation/new` | 创建对话 | 保持不变 |
| `GET /api/bot/info` | Bot 信息 | 保持不变 |
| `GET /api/health` | 健康检查 | 新增状态统计信息 |

### 4.2 新增接口简化

**PRD 中的 9 个新接口** → **简化为 6 个核心接口**

#### P0 (必须实现)
1. `POST /api/manual/escalate` - 用户/系统触发人工
2. `GET /api/sessions/{session_name}` - 获取会话详情
3. `POST /api/manual/messages` - 人工阶段发送消息
4. `POST /api/sessions/{session_name}/release` - 结束人工

#### P1 (后续实现)
5. `GET /api/sessions` - 工作台会话列表 (需要工作台时再实现)
6. `POST /api/sessions/{session_name}/takeover` - 坐席接入 (需要工作台时再实现)

#### 暂缓实现
- `POST /api/sessions/{session_name}/email` - 邮件功能 (P1)
- `GET /api/shift/config` - 工作时间配置 (P1)

### 4.3 响应格式统一

**建议采用更简洁的格式**:
```python
# 成功
{
  "success": true,
  "data": {...}
}

# 失败
{
  "success": false,
  "error": "错误信息",
  "code": "ERROR_CODE"  // 可选
}
```

**理由**: 与现有 `ChatResponse` 格式保持一致

---

## 五、实施建议

### 5.1 MVP 开发顺序 (推荐)

#### 第一阶段: 核心状态存储 (1-2天)
- [ ] 实现 `SessionStateStore` (内存版本)
- [ ] 实现 `SessionState` 数据模型
- [ ] 实现基础 CRUD 接口
- [ ] 单元测试

#### 第二阶段: 监管引擎 (1天)
- [ ] 实现 `Regulator` 关键词检测
- [ ] 实现连续失败检测
- [ ] 实现 VIP 判断
- [ ] 配置文件支持

#### 第三阶段: Chat 接口改造 (1天)
- [ ] `/api/chat` 集成监管逻辑
- [ ] `/api/chat/stream` 集成监管逻辑
- [ ] 状态判断和流程控制
- [ ] 集成测试

#### 第四阶段: 人工接口实现 (1-2天)
- [ ] `POST /api/manual/escalate`
- [ ] `GET /api/sessions/{session_name}`
- [ ] `POST /api/manual/messages`
- [ ] `POST /api/sessions/{session_name}/release`
- [ ] 端到端测试

#### 第五阶段: 前端适配 (2-3天)
- [ ] `chatStore` 扩展
- [ ] 状态展示组件
- [ ] 消息渲染适配
- [ ] 接口调用切换

### 5.2 后续扩展 (P1)
- 工作时间判断模块
- 邮件通知功能
- 工作台独立应用
- WebSocket 升级
- Redis 持久化

---

## 六、风险与建议

### 6.1 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 状态一致性 | 高 | 使用锁机制,实现 CAS 更新 |
| 消息丢失 | 中 | 定期持久化到文件,重启后恢复 |
| 并发冲突 | 中 | 限制单个 session 同时只能一个坐席 |
| JWT 兼容性 | 低 | 扩展现有 JWT,保持向后兼容 |

### 6.2 架构建议

1. **渐进式实现**: 不要一次性实现所有功能,先 MVP 再迭代
2. **接口隔离**: 用户端和工作台接口分开,便于权限控制
3. **日志先行**: 所有状态变更必须记录日志,便于排查问题
4. **测试覆盖**: 每个模块至少有基础单元测试

### 6.3 开发建议

1. **使用现有 backend_async.py**: 性能更好,支持高并发
2. **复用现有 OAuth 机制**: 不要重新实现鉴权
3. **保持接口一致性**: 新接口与现有接口风格保持一致
4. **文档同步更新**: 每个功能完成后更新 README

---

## 七、调整后的优先级

### P0 - 核心人工接管 (MVP)
1. SessionStateStore (内存版)
2. Regulator 监管引擎 (关键词 + 失败检测)
3. Chat 接口改造
4. 4 个核心 API (escalate, get, messages, release)
5. 前端状态展示和消息渲染

**目标**: 用户能触发人工,系统能记录状态,模拟坐席能回复 (通过 API)

### P1 - 工作台和完善
1. ShiftConfig 工作时间判断
2. 邮件通知模块
3. 工作台前端应用
4. 坐席接入/释放接口
5. 会话列表和搜索

**目标**: 真正的坐席可以通过工作台接管会话

### P2 - 优化增强
1. WebSocket 实时通道
2. Redis 持久化
3. Prometheus 监控
4. 情绪检测
5. 审计日志查询接口

---

## 八、总结

### ✅ PRD 整体质量高
- 需求描述清晰完整
- 技术方案合理可行
- 接口设计规范

### 📝 主要调整建议
1. **简化实现路径**: MVP 先用内存存储 + SSE,避免引入过多依赖
2. **分阶段交付**: P0 专注核心功能,P1/P2 渐进增强
3. **技术栈适配**: WebSocket、Redis 等后续引入,降低初期复杂度
4. **接口精简**: 从 9 个新接口简化为 6 个,优先实现 4 个核心接口

### 🎯 下一步行动
**建议从 P0 第一阶段开始**: 实现 SessionStateStore 和 SessionState 数据模型

这是整个功能的基础,完成后可以快速迭代其他模块。

---

**评审结论**: PRD 设计合理,经过适当调整后完全适配当前技术栈,建议按照上述优先级分阶段实施。
