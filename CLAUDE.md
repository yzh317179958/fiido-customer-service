# Fiido 智能客服系统 - Claude 开发指令

---

## ⚠️ 🔴 ⭐ 必读警告 - 渐进式增量化开发

```
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   🚨 强制要求：渐进式增量化开发（铁律0 - 最高优先级）              ║
║                                                                      ║
║   ❌ 禁止一次性开发多个功能                                         ║
║   ❌ 禁止一次提交修改 > 5个文件（后端）或 > 3个组件（前端）         ║
║   ❌ 禁止一次提交 > 300行代码变更                                   ║
║   ❌ 禁止开发超过2小时不提交                                        ║
║   ❌ 禁止跳过测试直接提交                                           ║
║                                                                      ║
║   ✅ 必须将需求拆解为小增量（每个 < 2小时）                         ║
║   ✅ 必须每个增量独立开发、测试、提交                               ║
║   ✅ 必须每次提交打版本tag                                          ║
║   ✅ 必须每个增量通过回归测试                                       ║
║   ✅ 必须前端UI功能经过自测和用户测试                               ║
║                                                                      ║
║   违规后果：严重违规（修改>10文件，>500行）→ 立即回滚              ║
║                                                                      ║
║   详细说明见下方 "铁律 0: 渐进式增量化开发"                         ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```

**开发前必须阅读**：
1. ⭐ 铁律 0: 渐进式增量化开发（本文档第56行）← **最重要！**
2. 🔴 必读文档清单（本文档第9行）
3. 🚨 核心铁律 1-5（本文档第359行起）

---

## 项目概述

这是一个基于 Coze API 的智能客服系统，包含用户端、坐席工作台和后端服务。

---

## 🔴 必读文档（开发前必须全部阅读）

**开发任何功能前，必须阅读以下所有文档，一个都不能落下：**

### 1. 约束与原则（最高优先级，必须首先阅读）

- `prd/02_约束与原则/CONSTRAINTS_AND_PRINCIPLES.md` - 核心约束与开发原则
- `prd/02_约束与原则/TECHNICAL_CONSTRAINTS.md` - 技术约束详细说明
- `prd/02_约束与原则/coze.md` - Coze API 使用约束和规范

### 2. 全局指导

- `prd/01_全局指导/prd.md` - 主PRD文档，系统需求定义和开发流程规范
- `prd/01_全局指导/PRD_COMPLETE_v3.0.md` - 完整版PRD，详细功能规格
- `prd/01_全局指导/README.md` - 项目概述和快速入门

### 3. 技术方案

- `prd/03_技术方案/TECHNICAL_SOLUTION_v1.0.md` - 技术架构方案
- `prd/03_技术方案/api_contract.md` - API 接口契约文档

### 4. 任务拆解

- `prd/04_任务拆解/IMPLEMENTATION_TASKS_v1.0.md` - 总体任务拆解
- `prd/04_任务拆解/backend_tasks.md` - 后端开发任务
- `prd/04_任务拆解/frontend_client_tasks.md` - 用户端前端任务
- `prd/04_任务拆解/agent_workbench_tasks.md` - 坐席工作台任务
- `prd/04_任务拆解/admin_management_tasks.md` - 管理员功能任务拆解 ⭐ 新增
- `prd/04_任务拆解/email_and_monitoring_tasks.md` - 邮件和监控任务

### 5. 验收与记录

- `prd/05_验收与记录/ACCEPTANCE_CRITERIA_v1.0.md` - 详细验收标准
- `prd/05_验收与记录/TESTING_GUIDE.md` - 测试流程规范
- `prd/05_验收与记录/implementation_notes.md` - 实施过程笔记
- `prd/05_验收与记录/PRD_REVIEW.md` - PRD 评审记录
- `prd/05_验收与记录/DOCUMENTATION_SUMMARY.md` - 文档总结

### 6. 企业部署

- `prd/06_企业部署/ENTERPRISE_DEPLOYMENT_PRD.md` - 企业级部署需求（独立站部署）
- `prd/06_企业部署/DEPLOYMENT_TASKS.md` - 部署开发任务拆解

**⚠️ 重要：开发前必须使用 Read 工具阅读上述所有文档，确保完全理解项目约束和规范后再开始编码。**

---

## 🚨 核心铁律（必须遵守，不可违反）

---

### ⭐ 铁律 0: 渐进式增量化开发 🔴 **最高优先级 - 必须严格遵守**

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                                                  ┃
┃  ⚠️  警告：这是最重要的开发原则，违反将导致代码回滚！          ┃
┃                                                                  ┃
┃  所有开发工作必须严格遵守渐进式增量化开发方式                   ┃
┃  禁止一次性大规模修改                                            ┃
┃                                                                  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

**强制要求**：所有开发工作必须严格遵守渐进式增量化开发方式，禁止一次性大规模修改。

#### 核心原则

**1. 小步快跑，频繁验证**

```
❌ 错误示例 - 一次性开发多个功能：
- 同时开发：内部备注 + 转接增强 + 协助请求 + 快捷键
- 一次性修改 10+ 个文件
- 开发完成后才测试
- 结果：出现问题难以定位，回滚代价高

✅ 正确示例 - 渐进式增量开发：
Step 1: 内部备注（后端API）
  - 开发 → 测试 → 提交 → 打tag v3.8.1
Step 2: 内部备注（前端UI）
  - 开发 → 自测 → 用户测试 → 提交 → 打tag v3.8.2
Step 3: 转接增强（后端）
  - 开发 → 测试 → 提交 → 打tag v3.8.3
Step 4: 转接增强（前端）
  - 开发 → 自测 → 用户测试 → 提交 → 打tag v3.8.4
```

**2. 每个增量必须是完整可验证的**

```
增量定义：
- ✅ 一个完整的后端API（包含测试）
- ✅ 一个完整的前端功能模块（包含自测）
- ✅ 一个Bug修复（包含验证）
- ❌ 半成品功能（缺少测试）
- ❌ 跨多个模块的大规模改动
```

**3. 每个增量独立提交和版本标记**

```bash
# ✅ 正确 - 每个增量独立提交
git commit -m "feat: 内部备注后端API v3.8.1"
git tag v3.8.1

git commit -m "feat: 内部备注前端UI v3.8.2"
git tag v3.8.2

# ❌ 错误 - 批量提交多个功能
git commit -m "feat: 内部备注+转接+协助请求 v3.8.5"
# 问题：无法单独回滚某个功能
```

#### 增量粒度标准

**后端开发**：

| 增量类型           | 最大修改范围         | 提交周期     |
| ------------------ | -------------------- | ------------ |
| 单个API端点        | 1个文件，< 100行代码 | 立即提交     |
| 数据模型变更       | 1-2个文件            | 立即提交     |
| 业务逻辑模块       | 1个模块文件          | 立即提交     |
| Bug修复            | 最小改动             | 立即提交     |
| ❌ 禁止大规模重构 | 修改 > 5个文件       | 必须拆分增量 |

**前端开发**：

| 增量类型         | 最大修改范围         | 提交周期         |
| ---------------- | -------------------- | ---------------- |
| 单个组件         | 1个.vue文件          | 自测后立即提交   |
| 样式调整         | 1个组件的CSS         | 立即提交         |
| 交互逻辑         | 1个composable        | 立即提交         |
| UI测试验证       | 用户确认后           | 用户确认后提交   |
| ❌ 禁止批量修改 | 修改 > 3个组件       | 必须拆分为多次   |

**文档更新**：

| 增量类型       | 最大修改范围         | 提交周期     |
| -------------- | -------------------- | ------------ |
| 单个功能文档   | 1个.md文件           | 立即提交     |
| 进度更新       | 任务拆解文档状态更新 | 功能完成后   |
| ❌ 禁止批量更新 | 修改 > 3个文档      | 必须拆分增量 |

#### 开发流程强制要求

**阶段1: 需求拆解**（开发前）

```
1. 将大需求拆解为独立的小增量
2. 每个增量必须：
   - 可独立开发
   - 可独立测试
   - 可独立部署
   - 有明确的验收标准

示例：
大需求："实现坐席协作功能"
拆解为增量：
  增量1: 内部备注API（后端）
  增量2: 内部备注UI（前端）
  增量3: 转接增强API（后端）
  增量4: 转接增强UI（前端）
  增量5: 协助请求API（后端）
  增量6: 协助请求UI（前端）
```

**阶段2: 增量开发**（开发中）

```
对于每个增量：
1. 开发（最多1小时）
2. 自测（立即）
3. 编写测试（后端必须，前端可选）
4. 运行回归测试（必须）
5. 提交代码（立即）
6. 打版本标签（立即）
7. 用户测试（前端UI功能）
8. 修复问题（如有）→ 新增量

⚠️ 禁止：
- 开发超过2小时不提交
- 跳过测试直接提交
- 批量提交多个功能
```

**阶段3: 集成验证**（开发后）

```
1. 回归测试（所有增量集成后）
2. 性能测试（如需要）
3. 用户验收（完整功能）
4. 文档更新（同步更新进度）
```

#### 违规后果与强制措施

**违规行为识别**：

```
🔴 严重违规（立即回滚）：
- 一次提交修改 > 10个文件
- 一次提交 > 500行代码变更
- 开发超过4小时不提交
- 跳过测试直接提交
- 提交时回归测试未通过

🟡 轻度违规（警告并要求拆分）：
- 一次提交修改 5-10个文件
- 一次提交 300-500行代码变更
- 开发超过2小时不提交
```

**强制措施**：

```
1. 代码回滚要求
   - 检测到严重违规 → 立即回滚到上一个稳定版本
   - 重新拆分增量 → 逐个实现

2. 提交前自检
   git diff --stat  # 检查修改文件数
   git diff | wc -l  # 检查代码行数

   如果超标 → 拆分为多次提交

3. 版本标签强制
   每次提交必须打tag → 方便回滚
```

#### 增量开发检查清单

**开发前**：
- [ ] 需求已拆解为独立增量（每个 < 2小时开发量）
- [ ] 每个增量有明确的验收标准
- [ ] 增量之间依赖关系明确

**开发中**（每个增量）：
- [ ] 开发时间 < 2小时
- [ ] 修改文件数 < 5个
- [ ] 代码变更 < 300行
- [ ] 已完成自测
- [ ] 已编写或更新测试脚本（后端必须）
- [ ] 回归测试通过

**提交前**：
- [ ] 代码已review
- [ ] 测试全部通过
- [ ] 文档已同步更新
- [ ] commit message清晰
- [ ] 已打版本tag

**提交后**：
- [ ] 前端UI功能已通知用户测试（如适用）
- [ ] 用户测试通过（前端UI功能）
- [ ] 已集成到回归测试套件

#### 典型场景示例

**场景1: 新增一个复杂功能**

```
需求：实现快捷键系统

❌ 错误做法：
- 一次性实现全部15个快捷键
- 一次性修改 Dashboard.vue、useKeyboardShortcuts.ts、
  KeyboardShortcutsHelp.vue 等5个文件
- 开发6小时后一次性提交
- 结果：出现多个Bug，难以定位

✅ 正确做法：
增量1 (v3.9.0): 快捷键基础框架
  - 创建 useKeyboardShortcuts.ts
  - 实现核心监听逻辑
  - 测试 → 提交 → 打tag

增量2 (v3.9.1): 基础快捷键（3个）
  - 实现 Ctrl+Shift+f (搜索)
  - 实现 Ctrl+ArrowUp/Down (切换会话)
  - 实现 Escape (关闭面板)
  - 测试 → 提交 → 打tag

增量3 (v3.9.2): 操作类快捷键（2个）
  - 实现 Ctrl+Shift+t (转接)
  - 实现 Ctrl+Shift+r (释放)
  - 测试 → 提交 → 打tag

增量4 (v3.9.3): 快捷键帮助面板
  - 创建 KeyboardShortcutsHelp.vue
  - 自测 → 用户测试 → 提交 → 打tag

每个增量独立可用，问题容易定位
```

**场景2: Bug修复**

```
Bug: 发送按钮被遮挡

❌ 错误做法：
- 同时修复发送按钮遮挡 + 优化浮动菜单 + 调整输入框样式
- 一次性修改多处CSS
- 结果：不确定哪个改动解决了问题

✅ 正确做法：
增量1 (v3.9.1): 修复发送按钮遮挡
  - 仅修改 .chat-send 的 z-index 和 flex-shrink
  - 测试确认问题解决
  - 提交 → 打tag

增量2 (v3.9.2): 优化浮动菜单（可选）
  - 调整 .sub-bubbles 的 z-index
  - 测试 → 提交 → 打tag

问题修复明确，容易验证
```

**场景3: 文档更新**

```
需求：更新快捷键文档

❌ 错误做法：
- 同时更新 L1-1-Part3 + CLAUDE.md + README.md
- 一次性大量修改
- 结果：难以review

✅ 正确做法：
增量1 (v3.9.1): 更新快捷键描述
  - 仅修改 L1-1-Part3 的快捷键表格
  - 提交 → 打tag

增量2 (v3.9.2): 更新开发指南（如需要）
  - 修改 CLAUDE.md 添加快捷键开发规范
  - 提交 → 打tag

每个文档独立提交，便于review
```

#### 监控与度量

**开发效率指标**：

| 指标             | 目标值       | 警戒值       |
| ---------------- | ------------ | ------------ |
| 单次提交文件数   | < 3个        | > 5个        |
| 单次提交代码行数 | < 200行      | > 500行      |
| 提交频率         | 每2小时至少1次 | > 4小时无提交 |
| 回归测试通过率   | 100%         | < 100%       |
| Bug回滚率        | < 5%         | > 10%        |

**质量指标**：

| 指标             | 目标值       |
| ---------------- | ------------ |
| 测试覆盖率       | > 80%        |
| 代码review通过率 | 100%         |
| 用户测试通过率   | > 95%        |
| 回归测试通过率   | 100%         |

---

**🔴 重要提醒**：
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                                            ┃
┃  开始开发前，请再次确认你已理解并遵守铁律0的所有要求：     ┃
┃                                                            ┃
┃  ✅ 需求已拆解为小增量（每个 < 2小时）                     ┃
┃  ✅ 每个增量独立开发、测试、提交、打tag                    ┃
┃  ✅ 修改文件数 < 5个（后端）或 < 3个组件（前端）           ┃
┃  ✅ 代码变更 < 300行                                       ┃
┃  ✅ 回归测试必须通过                                       ┃
┃                                                            ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

### 铁律 1: 不可修改的核心接口

以下接口是系统基石，**严禁修改其核心逻辑**：

```
🔴 不可修改:
- POST /api/chat              (同步AI对话)
- POST /api/chat/stream       (流式AI对话)
- POST /api/conversation/new  (创建会话)
```

**允许的操作**:

- ✅ 在调用前添加前置检查（如状态检查）
- ✅ 在返回后添加后置处理（如日志记录）
- ❌ **禁止**修改 Coze API 调用方式
- ❌ **禁止**修改返回的数据结构
- ❌ **禁止**修改 payload 的必需字段格式

### 铁律 2: Coze API 调用规范

#### 必须使用 SSE 流式响应

```python
# ✅ 正确 - 使用 stream() 方法
with http_client.stream('POST', url, json=payload, headers=headers) as response:
    for line in response.iter_lines():
        # 解析SSE流

# ❌ 错误 - Coze返回的是SSE流,不是JSON!
response = http_client.post(...)
data = response.json()
```

#### 必须从顶层提取字段

```python
# ✅ 正确
event_data = json.loads(data_content)
if event_data.get("type") == "answer":
    content = event_data["content"]

# ❌ 错误 - Coze不返回嵌套结构
content = event_data["message"]["content"]
```

#### 必需的请求参数

```python
payload = {
    "workflow_id": WORKFLOW_ID,      # 必需
    "app_id": APP_ID,                # 必需
    "session_name": session_id,      # 必需 - 会话隔离
    "additional_messages": [...],    # 必需
    "conversation_id": conv_id,      # 可选(多轮对话需要)
}
```

### 铁律 3: OAuth + JWT 鉴权机制

```python
# ✅ 正确 - 使用 token_manager
access_token = token_manager.get_access_token(
    session_name=session_id  # 必须包含session_name实现隔离
)

# ❌ 错误 - 硬编码Token
access_token = "hardcoded_token"

# ❌ 错误 - 所有用户共用一个Token
access_token = token_manager.get_access_token()  # 缺少session_name!
```

### 铁律 4: 会话隔离机制

**强制要求**：基于 `session_name` 实现会话隔离，conversation_id 由 Coze 自动管理

**核心原理** (详见 `docs/process/会话隔离实现总结.md`):

1. ✅ **首次对话不传 conversation_id**，由 Coze 自动生成
2. ✅ **后续对话传入相同的 conversation_id** 维持上下文
3. ✅ **验证标准**: 不同 session_name 获得不同的 conversation_id

```python
# ✅ 正确方式 - Coze 自动管理 conversation_id
@app.post("/api/chat")
async def chat(request: ChatRequest):
    session_id = request.user_id or generate_user_id()

    # 获取带 session_name 的 JWT Token
    access_token = token_manager.get_access_token(session_name=session_id)

    # 从缓存获取 conversation_id（如果有）
    conversation_id = conversation_cache.get(session_id)

    # 构建 API payload
    payload = {
        "workflow_id": WORKFLOW_ID,
        "app_id": APP_ID,
        "session_name": session_id,  # ← 关键！会话隔离核心
        "parameters": {"USER_INPUT": request.message}
    }

    # 首次对话不传 conversation_id，后续对话才传
    if conversation_id:
        payload["conversation_id"] = conversation_id

    # 调用 Coze API
    response = httpx.post(url, json=payload, headers=headers)

    # 保存 Coze 返回的 conversation_id
    if not conversation_id and returned_conversation_id:
        conversation_cache[session_id] = returned_conversation_id

# ❌ 错误方式 - 手动生成 conversation_id
conversation_id = f"conv_{uuid.uuid4()}"  # 禁止！

# ❌ 错误方式 - 依赖首次对话自动生成但不保存
# 问题：会导致每次对话都生成新 conversation_id，无法维持上下文
```

**测试验证** (使用 `tests/test_session_isolation.py`):

```bash
# 正确的会话隔离测试流程
# 1. 用户 A 首次对话（不传 conversation_id）
POST /api/chat {"message": "我是用户A", "user_id": "session_a"}
# 响应: {"conversation_id": "7576537373...", "message": "..."}

# 2. 用户 B 首次对话（不传 conversation_id）
POST /api/chat {"message": "我是用户B", "user_id": "session_b"}
# 响应: {"conversation_id": "7576539408...", "message": "..."}  ← 不同！

# 3. 用户 A 第二轮（传入 conversation_id）
POST /api/chat {"message": "我是谁?", "user_id": "session_a", "conversation_id": "7576537373..."}
# 响应: 应该回答"你是用户A"，证明上下文维持成功

# 验证: conversation_id 不同 ✅
```

**关键约束**:

- ❌ 禁止手动生成 conversation_id
- ❌ 禁止修改 conversation_id 管理逻辑
- ✅ 必须保存 Coze 返回的 conversation_id
- ✅ 必须在 JWT 和 API payload 中都传入 session_name

### 铁律 5: 状态机约束

```
bot_active → pending_manual → manual_live → bot_active
```

- 状态转换必须按顺序，不可跳跃
- 人工接管期间**必须阻止 AI 对话**（返回 409）
- `conversation_id` 由 Coze 自动生成，**禁止手动创建**

---

## 📋 开发流程规范

---

**⭐ 快速参考：渐进式增量化开发流程**

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                                               ┃
┃  每个增量的标准流程（严格按顺序执行）：                       ┃
┃                                                               ┃
┃  1️⃣ 需求拆解 → 确保单个增量 < 2小时开发量                    ┃
┃  2️⃣ 开发实现 → 修改文件 < 5个，代码 < 300行                  ┃
┃  3️⃣ 自测验证 → 功能正常工作                                  ┃
┃  4️⃣ 编写测试 → 后端必须，前端可选                            ┃
┃  5️⃣ 回归测试 → 必须100%通过                                  ┃
┃  6️⃣ Git提交  → 立即提交并打tag（如v3.9.3）                   ┃
┃  7️⃣ 用户测试 → 前端UI功能必须                                ┃
┃  8️⃣ 集成测试 → 添加到regression_test.sh                      ┃
┃                                                               ┃
┃  ⚠️  每个步骤都不能跳过！                                     ┃
┃                                                               ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

### 阶段1: 开发前审查

**在开始任何新功能开发之前，必须完成**：

#### 1.1 开发进度管理要求 ⭐ **强制执行**

**触发条件**：任何模块开发（新功能、优化、Bug修复）

**强制要求**：

1. **进度查询规范**

   - 查询开发进度时，**优先从 `prd/04_任务拆解/` 文件夹下搜索**
   - 每个模块对应一个独立的 `.md` 文件
   - 文件命名格式：`{模块名称}_tasks.md`
2. **任务拆解文件结构要求**

每个任务拆解文件必须包含以下章节：

```markdown
# {模块名称}功能需求文档与任务拆解

> 文档版本: v{版本号}
> 状态: ✅ P0 已完成 / ⚠️ P0 开发中 / ❌ P0 待开发
> 更新时间: YYYY-MM-DD

## 1. 功能列表

| 功能ID | 功能名称 | 优先级 | 状态 | 完成时间 |
|--------|---------|--------|------|---------|
| {模块}-01 | 功能名称 | P0 | ✅ 已完成 | 2025-11-25 |
| {模块}-02 | 功能名称 | P1 | ⚠️ 开发中 | - |
| {模块}-03 | 功能名称 | P2 | ❌ 待开发 | - |

## 2. 当前模块开发进度

**总体进度**: 60% (P0: 100%, P1: 50%, P2: 0%)

**当前阶段**: P1 开发中

**最近更新**:
- 2025-11-25: 完成 P0 功能，开始 P1 开发
- 2025-11-24: 创建模块，完成技术方案设计

## 3. 技术方案（同步到 prd/03_技术方案/）

## 4. 约束与原则（同步到 prd/02_约束与原则/）

## 5. API 接口（同步到 prd/03_技术方案/api_contract.md）

## 6. 验收标准
```

3. **同步更新要求**

开发过程中，必须同步更新以下文件：


| 更新内容   | 同步位置                                                                       |
| ---------- | ------------------------------------------------------------------------------ |
| 技术方案   | `prd/03_技术方案/{模块名称}_solution.md` 或集成到 `TECHNICAL_SOLUTION_v1.0.md` |
| 约束与原则 | `prd/02_约束与原则/CONSTRAINTS_AND_PRINCIPLES.md` (添加新约束)                 |
| API 接口   | `prd/03_技术方案/api_contract.md` (添加新接口)                                 |
| 任务进度   | `prd/04_任务拆解/{模块名称}_tasks.md` (更新状态和进度)                         |

4. **开发完成后强制更新**

每次完成开发后，**必须更新开发进度**：

```bash
# 必须执行的更新
1. 更新 prd/04_任务拆解/{模块名称}_tasks.md
   - 修改功能状态（待开发 → 开发中 → 已完成）
   - 更新完成时间
   - 更新总体进度百分比

2. 如有新增约束，更新 prd/02_约束与原则/CONSTRAINTS_AND_PRINCIPLES.md

3. 如有新增API，更新 prd/03_技术方案/api_contract.md

4. 提交并推送到 GitHub 仓库，包含进度更新
```

**示例**：

```markdown
# 管理员功能开发完成 v3.1.3

更新内容：
- ✅ P0 功能全部完成（坐席CRUD、权限控制）
- ✅ P1 功能全部完成（修改密码、修改资料）
- 📄 更新 admin_management_tasks.md 进度为 100%
- 📄 添加约束19-21到 CONSTRAINTS_AND_PRINCIPLES.md
- 📄 添加7个新API到 api_contract.md
```

5. **检查清单**

开发完成后，执行以下检查：

- [ ]  `prd/04_任务拆解/{模块名称}_tasks.md` 状态已更新
- [ ]  新增约束已写入 `prd/02_约束与原则/`
- [ ]  新增API已写入 `prd/03_技术方案/api_contract.md`
- [ ]  **新功能测试脚本已创建并验证通过** ⭐ 新增
- [ ]  **测试已集成到 `tests/regression_test.sh`** ⭐ 新增
- [ ]  **回归测试全部通过（包括新增测试）** ⭐ 更新
- [ ]  Git commit 完成并已推送到远程仓库，commit message 包含进度信息
- [ ]  提交并更新仓库的main分支，并且打上tag标签发布一个小版本

#### 1.2 版本号规范 ⭐ **强制遵守**

**版本号格式**: `v主版本.次版本.补丁版本`（如 v3.8.1）

**版本号更新规则**：

1. **补丁版本（第三位）** - 日常功能开发和Bug修复
   - **触发条件**: 常规功能开发、Bug修复、小优化
   - **更新方式**: 只更新第三位数字（如 v3.8.1 → v3.8.2）
   - **示例**:
     - v3.8.1 → v3.8.2 (新增快捷键功能)
     - v3.8.2 → v3.8.3 (修复转接Bug)

2. **次版本（第二位）** - 用户明确要求的大版本更新
   - **触发条件**: 用户明确说"更新一个大版本"
   - **更新方式**: 更新第二位数字，第三位归零（如 v3.8.3 → v3.9.0）
   - **示例**:
     - v3.8.3 → v3.9.0 (用户要求大版本更新)

3. **主版本（第一位）** - 重大架构变更（极少使用）
   - **触发条件**: 系统架构重大变更、不兼容更新
   - **更新方式**: 更新第一位数字，后两位归零（如 v3.9.0 → v4.0.0）

**⚠️ 重要约束**：
- ❌ **禁止**自行决定更新次版本（第二位）
- ✅ **默认**每次开发完成后更新补丁版本（第三位）
- ✅ **仅当用户明确要求**时才更新次版本（第二位）

**示例流程**：
```bash
# 当前版本: v3.8.1

# 场景1: 常规功能开发（默认）
# 开发快捷键系统 → 打 tag v3.8.2
git tag v3.8.2 -m "feat: 快捷键系统"

# 场景2: Bug修复
# 修复转接功能Bug → 打 tag v3.8.3
git tag v3.8.3 -m "fix: 修复会话转接Bug"

# 场景3: 用户明确要求大版本更新
# 用户: "更新一个大版本"
# → 打 tag v3.9.0（第二位+1，第三位归零）
git tag v3.9.0 -m "release: v3.9.0 大版本更新"
```

---

#### 1.3 约束文档审查清单

- [ ]  阅读 `prd/02_约束与原则/CONSTRAINTS_AND_PRINCIPLES.md`
- [ ]  阅读 `prd/03_技术方案/TECHNICAL_SOLUTION_v1.0.md`
- [ ]  确认新功能是否涉及 Coze API 调用
- [ ]  确认新功能是否会修改现有接口
- [ ]  检查是否引入新的外部依赖

#### 1.3 基线验证

```bash
# 在开始开发前，运行基线测试确保当前系统正常
./tests/regression_test.sh
# 预期: 12/12 通过，否则不得开始新功能开发
```

#### 1.4 设计审查

- [ ]  新功能是否遵循"前置检查 + 后置处理"模式？
- [ ]  新功能失败时是否会影响核心 AI 对话？（必须是"否"）
- [ ]  是否需要添加新的约束条款？

### 阶段2: 开发中约束

#### 2.1 代码实现检查清单

- [ ]  新增代码是否遵循现有代码风格？
- [ ]  是否添加了充足的错误处理？
- [ ]  新功能失败时是否会阻塞核心功能？（不应阻塞）
- [ ]  是否添加了结构化日志记录？
- [ ]  敏感信息是否已脱敏？

#### 2.2 正确的扩展模式

```python
# ✅ 正确 - 前置检查，不修改核心逻辑
@app.post("/api/chat")
async def chat(request: ChatRequest):
    # 【新增】前置检查
    if session_state.status in [PENDING_MANUAL, MANUAL_LIVE]:
        raise HTTPException(status_code=409, detail="MANUAL_IN_PROGRESS")

    # 原有 Coze API 调用逻辑（完全不动）
    access_token = token_manager.get_access_token(session_name=session_id)
    # ...
```

#### 2.3 编写自动化测试 ⭐ **强制执行**

**在完成功能开发后，立即编写自动化测试**：

1. **创建测试脚本**
   ```bash
   # 命名规范: tests/test_{功能名称}.sh 或 tests/test_{功能名称}.py

   # 示例：
   tests/test_admin_apis.sh           # 管理员功能测试
   tests/test_customer_profile.sh     # 客户画像测试
   tests/test_session_tags.sh         # 会话标签测试
   ```

2. **测试脚本要求**
   - ✅ 覆盖新功能的所有核心API
   - ✅ 包含正常场景测试（Happy Path）
   - ✅ 包含异常场景测试（错误处理、边界条件）
   - ✅ 验证返回数据格式、字段完整性和状态码
   - ✅ 测试权限控制（如适用）
   - ✅ 输出清晰的测试结果（✅ PASS / ❌ FAIL）
   - ✅ 每个测试用例有明确的描述

3. **测试示例模板**
   ```bash
   #!/bin/bash
   # tests/test_example_feature.sh

   BASE_URL="http://localhost:8000"
   PASSED=0
   FAILED=0

   # 测试1: 正常场景
   echo "测试1: 创建资源 - 正常场景"
   RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/resource" \
     -H "Content-Type: application/json" \
     -d '{"name": "test"}')

   HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
   BODY=$(echo "$RESPONSE" | head -n-1)

   if [ "$HTTP_CODE" -eq 200 ]; then
       echo "✅ PASS - 状态码正确"
       ((PASSED++))
   else
       echo "❌ FAIL - 预期200，实际$HTTP_CODE"
       ((FAILED++))
   fi

   # 测试2: 异常场景
   echo "测试2: 创建资源 - 缺少必需字段"
   # ... 测试逻辑

   # 输出总结
   echo "========================================"
   echo "总测试: $((PASSED + FAILED))"
   echo "通过: $PASSED"
   echo "失败: $FAILED"

   if [ $FAILED -eq 0 ]; then
       exit 0
   else
       exit 1
   fi
   ```

4. **独立验证测试**
   ```bash
   # 运行新功能测试脚本
   chmod +x tests/test_{功能名称}.sh
   ./tests/test_{功能名称}.sh
   # 预期: 所有测试通过
   ```

5. **自测环节 ⭐ 强制执行**

   **强制要求**：在通知用户进行 UI 测试之前，开发者（Claude）必须先进行自测

   **自测流程**：
   - ✅ 检查代码是否编译通过（TypeScript 类型检查）
   - ✅ 检查前端服务是否能正常启动（npm run dev）
   - ✅ 检查浏览器控制台是否有错误
   - ✅ 测试核心功能是否可用（如快捷键是否响应）
   - ✅ 确认没有明显的 UI 渲染问题

   **自测命令示例**：
   ```bash
   # 1. TypeScript 类型检查
   cd agent-workbench
   npx vue-tsc --noEmit
   # 预期: 无类型错误

   # 2. 启动前端服务
   npm run dev
   # 预期: 服务正常启动在 http://localhost:5174

   # 3. 浏览器自测（手动）
   # - 打开 http://localhost:5174
   # - 登录系统
   # - 测试新功能基本可用
   # - 检查浏览器控制台无错误
   ```

   **自测通过标准**：
   - ✅ 无编译错误
   - ✅ 无类型错误
   - ✅ 前端服务正常运行
   - ✅ 核心功能可用
   - ✅ 无控制台错误

   **自测失败处理**：
   - ❌ 如发现错误，立即修复，重新自测
   - ❌ 不得将有明显错误的代码提交给用户测试

6. **UI 手动测试 ⭐ 关键步骤**

   **强制要求**：对于涉及前端UI的功能，在集成到回归测试之前，必须先经过自测，然后通知用户进行 UI 手动测试

   **流程**：
   - ✅ 自测通过后，提交代码到Git，标记为"待UI验证"
   - ✅ 通知用户进行UI手动测试
   - ✅ 等待用户确认UI功能正常
   - ✅ 用户确认后，才能集成到回归测试

   **示例**：
   ```bash
   # 1. 自测通过
   npx vue-tsc --noEmit  # ✅ 无类型错误
   npm run dev           # ✅ 服务正常启动
   # 浏览器测试：快捷键响应正常，无控制台错误

   # 2. 提交代码（不集成回归测试）
   git add agent-workbench/src/composables/useKeyboardShortcuts.ts
   git add agent-workbench/src/components/KeyboardShortcutsHelp.vue
   git add agent-workbench/src/views/Dashboard.vue
   git commit -m "feat: 快捷键系统 (待UI验证)"
   git push origin main

   # 3. 通知用户：
   # "已完成快捷键系统功能，自测已通过（类型检查、服务启动、基本功能验证）。
   #  请测试以下快捷键：
   #  - Ctrl+F: 搜索框聚焦
   #  - Alt+↑/↓: 切换会话
   #  - Ctrl+T: 转接对话框
   #  - ?: 显示快捷键帮助
   #  确认无误后告知，我将集成到回归测试套件。"

   # 4. 等待用户确认...
   # 用户: "UI测试通过，可以集成了"

   # 5. 集成到回归测试
   # (添加测试到 regression_test.sh)
   ```

   **适用场景**：
   - 前端界面改动（如新增组件、修改布局）
   - 用户交互流程变更（如对话框、表单）
   - 视觉效果优化（如加载状态、错误提示）

   **不适用场景**（直接集成回归测试）：
   - 纯后端API功能（无前端变化）
   - Bug修复（已有功能的修正）
   - 性能优化（无UI变化）

7. **集成到回归测试 ⭐ 关键步骤**

   **强制要求**：
   - 纯后端功能：API测试通过后，直接集成到 `tests/regression_test.sh`
   - 前端功能：**必须经过自测和用户UI测试确认后**，才能集成到回归测试

   ```bash
   # 编辑 tests/regression_test.sh
   # 在适当位置添加新功能测试

   # 示例：
   echo "测试 15: 客户画像功能"
   bash tests/test_customer_profile.sh
   if [ $? -eq 0 ]; then
       echo "✅ 客户画像功能测试通过"
       ((passed++))
   else
       echo "❌ 客户画像功能测试失败"
       ((failed++))
   fi
   ((total++))
   ```

8. **更新测试计数**
   ```bash
   # 更新回归测试脚本中的预期测试总数
   # 例如：从 12/12 更新为 13/13
   ```

### 阶段3: 开发后验证

#### 3.1 新功能测试 ⭐ **强制执行**

**验证在阶段2编写的测试脚本是否完整且通过**：

1. **独立运行新功能测试**
   ```bash
   # 运行新功能测试脚本
   chmod +x tests/test_{功能名称}.sh
   ./tests/test_{功能名称}.sh
   # 预期: 所有测试通过
   ```

2. **检查测试覆盖率**
   - ✅ 是否覆盖了所有新增的API端点？
   - ✅ 是否包含正常场景和异常场景？
   - ✅ 是否测试了权限控制（如适用）？
   - ✅ 是否验证了返回数据格式？

3. **集成到回归测试 ⭐ 关键步骤**

   **强制要求**：测试通过后，必须将新功能测试集成到 `tests/regression_test.sh`

   ```bash
   # 编辑 tests/regression_test.sh
   # 在适当位置添加新功能测试

   # 示例：
   echo "测试 15: 客户画像功能"
   bash tests/test_customer_profile.sh
   if [ $? -eq 0 ]; then
       echo "✅ 客户画像功能测试通过"
       ((passed++))
   else
       echo "❌ 客户画像功能测试失败"
       ((failed++))
   fi
   ((total++))
   ```

4. **更新测试计数**
   ```bash
   # 更新回归测试脚本中的预期测试总数
   # 例如：从 12/12 更新为 13/13
   ```

#### 3.2 回归测试验证

```bash
# 必须运行完整回归测试
cd /home/yzh/AI客服/鉴权
./tests/regression_test.sh
# 预期: 所有测试通过（包括新增的功能测试）
```

**验证要求**：

1. 核心对话功能不受影响
2. 会话隔离机制完整
3. 错误隔离：新功能异常不导致核心功能失败
4. **新功能测试已集成到回归测试中** ⭐ 关键要求

#### 3.3 文档与代码提交检查

- [ ] 新功能测试脚本已创建并验证通过（在阶段2完成）
- [ ] 测试脚本已集成到 `tests/regression_test.sh`
- [ ] 回归测试总数已更新
- [ ] 回归测试全部通过
- [ ] 测试结果已记录到 `prd/05_验收与记录/implementation_notes.md`
- [ ] `prd/04_任务拆解/{模块名称}_tasks.md` 状态已更新
- [ ] 新增约束已写入 `prd/02_约束与原则/`
- [ ] 新增API已写入 `prd/03_技术方案/api_contract.md`
- [ ] Git commit 完成并已推送到远程仓库，commit message 包含进度信息
- [ ] 提交并更新仓库的main分支，并且打上tag标签发布一个小版本

---

## ✅ 允许的扩展方向

以下功能**完全自由设计**，不受 Coze 平台限制：

### 1. 会话状态管理 (`src/session_state.py`)

- 可自由定义状态枚举
- 可添加任意字段
- 可自定义数据模型

### 2. 监管引擎 (`src/regulator.py`)

- 关键词检测规则
- AI 失败计数逻辑
- 自动升级触发条件

### 3. 新增 API 接口

- 人工接管相关接口
- 统计查询接口
- 坐席管理接口

### 4. SSE 事件扩展

- 可添加新的事件类型（如 `type:'manual_message'`）
- 不得替换核心 AI 对话的 SSE 流

---

## 项目结构

```
/home/yzh/AI客服/鉴权/
├── backend.py              # 后端主服务
├── src/                    # 后端模块
│   ├── session_state.py    # 会话状态机
│   ├── regulator.py        # 监管引擎
│   ├── shift_config.py     # 工作时间配置
│   ├── email_service.py    # 邮件服务
│   └── oauth_token_manager.py  # Token管理
├── frontend/               # 用户端 Vue 项目
├── agent-workbench/        # 坐席工作台 Vue 项目
├── prd/                    # PRD 文档
│   └── INDEX.md            # 文档索引
└── tests/                  # 测试脚本
    └── regression_test.sh  # 回归测试
```

---

## 常用命令

### 启动服务

```bash
# 启动后端
python3 backend.py
# 访问: http://localhost:8000
# API文档: http://localhost:8000/docs

# 启动用户端
cd frontend && npm run dev
# 访问: http://localhost:5173 (本地)
# 访问: http://192.168.x.x:5173 (局域网)

# 启动坐席工作台
cd agent-workbench && npm run dev
# 访问: http://localhost:5174 (本地，必须是5174端口)
# 访问: http://192.168.x.x:5174 (局域网)
# 默认账号: admin/admin123, agent001/agent123
```

### 端口管理规范 ⭐ **强制遵守**

**标准端口配置**（不得随意更改）：

| 服务 | 端口 | 说明 |
|------|------|------|
| 后端 API | 8000 | FastAPI 后端服务 |
| 用户端 | 5173 | 客户聊天界面 |
| 坐席工作台 | 5174 | 坐席管理系统（必须） |

**启动前检查**：

```bash
# 检查端口占用情况
lsof -i :5174

# 如果端口被占用，清除旧进程
pkill -f "agent-workbench.*vite"

# 等待进程退出
sleep 2

# 确认端口已释放
lsof -i :5174 || echo "✅ 端口 5174 已释放"

# 重新启动前端
cd agent-workbench && npm run dev
```

**强制要求**：
- ✅ 坐席工作台必须运行在 5174 端口
- ✅ 如果端口被占用，必须先清除旧进程
- ❌ 禁止让 Vite 自动切换到其他端口（5175、5176等）
- ❌ 禁止修改 claude.md 中的标准端口配置

### 完整服务访问地址


| 服务       | 本地地址                   | 局域网地址                   | 说明         |
| ---------- | -------------------------- | ---------------------------- | ------------ |
| 后端API    | http://localhost:8000      | http://192.168.x.x:8000      | FastAPI后端  |
| API文档    | http://localhost:8000/docs | http://192.168.x.x:8000/docs | Swagger UI   |
| 用户端     | http://localhost:5173      | http://192.168.x.x:5173      | Vue前端      |
| 坐席工作台 | http://localhost:5174      | http://192.168.x.x:5174      | 坐席管理系统 |

### ⭐ 前端 API 地址配置规范（强制遵守）

**所有前端项目中的 API 调用必须使用环境变量配置，禁止硬编码地址！**

#### 正确做法 ✅

```javascript
// 在组件顶部声明 API_BASE（紧随 import 之后）
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

// 使用 API_BASE 调用接口
const response = await fetch(`${API_BASE}/api/quick-replies`, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
```

#### 错误做法 ❌

```javascript
// ❌ 错误 - 硬编码地址
const response = await fetch('http://localhost:8000/api/quick-replies', ...)

// ❌ 错误 - 直接使用 localhost
const response = await fetch(`http://localhost:8000/api/${endpoint}`, ...)
```

#### 环境变量配置

在前端项目的 `.env` 文件中配置：

```bash
# agent-workbench/.env
VITE_API_BASE=http://localhost:8000

# frontend/.env
VITE_API_BASE=http://localhost:8000
```

**注意**：
- 使用 Vite 的环境变量必须以 `VITE_` 开头
- 所有 API 调用必须使用 `${API_BASE}` 拼接路径
- 禁止在任何地方硬编码 `http://localhost:8000`
- 参考 `Dashboard.vue` 的实现模式

### 测试命令

```bash
# 回归测试
./tests/regression_test.sh

# 健康检查
curl http://localhost:8000/api/health

# 会话统计
curl http://localhost:8000/api/sessions/stats
```

---

## 环境变量 (.env)

关键配置：

- `COZE_WORKFLOW_ID` - 工作流ID
- `COZE_APP_ID` - 应用ID
- `COZE_OAUTH_CLIENT_ID` - OAuth客户端ID
- `REGULATOR_KEYWORDS` - 人工接管触发关键词
- `REGULATOR_FAIL_THRESHOLD` - AI连续失败阈值
- `JWT_SECRET_KEY` - JWT密钥（生产环境必须使用强随机密钥） ⭐ v3.1+

---

## 🔐 坐席认证与权限约束 ⭐ **强制遵守** (v3.1+)

### 核心约束

#### 约束19: 字段级访问控制 ⭐ **新增 v3.1.3**

**强制要求**：

1. **坐席只能修改自己的 name 和 avatar_url**

```python
# ✅ 正确 - 只允许修改非敏感字段
@app.put("/api/agent/profile")
async def update_profile(
    request: UpdateProfileRequest,  # 只包含 name 和 avatar_url
    agent: Dict = Depends(require_agent)
):
    # 只更新允许的字段
    if request.name is not None:
        current_agent.name = request.name
    if request.avatar_url is not None:
        current_agent.avatar_url = request.avatar_url

# ❌ 错误 - 允许修改敏感字段
request_data = request.dict()
for key, value in request_data.items():
    setattr(current_agent, key, value)  # 可能修改 role, max_sessions 等
```

**禁止修改的字段**：

- `role` - 角色（admin/agent）
- `username` - 用户名
- `max_sessions` - 最大会话数
- `status` - 坐席状态
- `created_at` - 创建时间
- `last_login` - 最后登录时间
- `password_hash` - 密码哈希

**生产环境基准值**：

- 允许修改：`name` (1-50字符), `avatar_url` (URL字符串)
- 至少需要提供一个字段
- 返回 400 如果请求体为空

#### 约束20: 密码修改安全性 ⭐ **新增 v3.1.2**

**强制要求**：

1. **三重验证机制**

```python
# ✅ 正确 - 完整的密码修改流程
@app.post("/api/agent/change-password")
async def change_password(request: ChangePasswordRequest, agent: Dict = Depends(require_agent)):
    # 验证1: 旧密码正确性
    if not PasswordHasher.verify_password(request.old_password, current_agent.password_hash):
        raise HTTPException(400, "OLD_PASSWORD_INCORRECT: 旧密码不正确")

    # 验证2: 新密码强度（至少8字符，包含字母和数字）
    if not validate_password(request.new_password):
        raise HTTPException(400, "INVALID_PASSWORD: 密码必须至少8个字符，包含字母和数字")

    # 验证3: 新旧密码不能相同
    if PasswordHasher.verify_password(request.new_password, current_agent.password_hash):
        raise HTTPException(400, "PASSWORD_SAME: 新密码不能与旧密码相同")

# ❌ 错误 - 缺少验证
current_agent.password_hash = PasswordHasher.hash_password(request.new_password)  # 不验证旧密码！
```

**生产环境基准值**：

- 最小密码长度：8 字符
- 必须包含：字母 + 数字
- 禁止：新旧密码相同
- Token有效性：修改密码后旧Token仍有效（直到过期）

#### 约束21: JWT 权限分级

**强制要求**：

1. **三级权限模型**

```python
# ✅ 正确 - 使用权限中间件
@app.get("/api/agents")  # 管理员功能
async def get_agents(admin: Dict = Depends(require_admin)):
    pass

@app.post("/api/agent/change-password")  # 任何登录用户
async def change_password(agent: Dict = Depends(require_agent)):
    pass

# 用户端 API 无需认证
@app.post("/api/chat")
async def chat(request: ChatRequest):
    pass

# ❌ 错误 - 混用权限
@app.get("/api/agents")
async def get_agents(agent: Dict = Depends(require_agent)):  # 应该用 require_admin!
    pass
```

**权限级别**：


| 权限              | 适用对象     | 典型API                             |
| ----------------- | ------------ | ----------------------------------- |
| `无需认证`        | 用户端前端   | `/api/chat`, `/api/manual/escalate` |
| `require_agent()` | 任何登录坐席 | 修改密码、修改资料、会话查询        |
| `require_admin()` | 管理员       | 坐席CRUD、密码重置、权限管理        |

**生产环境基准值**：

- Token过期时间：1小时（Access Token）
- Refresh Token：7天
- 401 错误：Token无效或过期
- 403 错误：权限不足（如普通坐席访问管理员API）

---

## ❌ 禁止事项

1. **不要修改** `.env` 中的 Coze 凭证
2. **不要删除** 任何现有的 API 端点
3. **不要修改** Coze API 的调用方式和返回解析
4. **不要绕过** token_manager 直接生成 Token
5. **不要使用** WebSocket 替换 SSE 流式响应
6. **不要跳过** 回归测试就提交代码
7. **不要在** 人工接管期间允许 AI 对话
8. **不要允许** 坐席修改自己的 role、username、max_sessions 等敏感字段 ⭐ v3.1.3
9. **不要跳过** 旧密码验证直接修改密码 ⭐ v3.1.2
10. **不要混用** JWT 权限级别（如用 require_agent 保护管理员 API）⭐ v3.1

---

## 📚 文档索引

完整文档结构见 `prd/INDEX.md`

```
prd/
├── 01_全局指导/     # 系统需求和指导
├── 02_约束与原则/   # 技术约束（最重要)
├── 03_技术方案/     # 架构和API
├── 04_任务拆解/     # 开发任务
└── 05_验收与记录/   # 测试和验收
```

---

## 🏢 企业生产环境要求 ⭐ **强制遵守**

### 核心原则

在所有后续开发中，**必须充分考虑企业实际使用和生产环境下的合理并发性和实时性**。

---

### 1. 并发性要求 (Concurrency)

#### 1.1 连接池管理

**强制要求**：

```python
# ✅ 正确 - 使用连接池限制并发连接数
redis_pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    max_connections=50,          # 最大连接数
    socket_timeout=5.0,          # 超时设置
    socket_connect_timeout=5.0,
    socket_keepalive=True
)

# ❌ 错误 - 无限制创建连接
for i in range(1000):
    redis_client = redis.Redis(host='localhost')  # 可能耗尽连接数
```

**生产环境基准值**：

- Redis 连接池：50 连接（支持 100+ 并发用户）
- HTTP 客户端连接池：100 连接
- 数据库连接池：20-50 连接

#### 1.2 请求速率限制

**强制要求**：

```python
# ✅ 正确 - 实现速率限制
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@app.post("/api/chat")
@limiter.limit("20/minute")  # 每分钟最多20次请求
async def chat(request: ChatRequest):
    pass

# ❌ 错误 - 无速率限制，可能被恶意攻击
@app.post("/api/chat")
async def chat(request: ChatRequest):
    pass  # 任意频率调用
```

**生产环境基准值**：

- 普通用户：20 请求/分钟
- VIP 用户：100 请求/分钟
- 坐席账号：无限制（内部使用）

#### 1.3 并发 SSE 连接管理

**强制要求**：

```python
# ✅ 正确 - 限制每个用户的 SSE 连接数
MAX_SSE_PER_USER = 3  # 每个用户最多3个并发 SSE 连接

sse_connections: dict[str, int] = {}  # {session_id: connection_count}

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    session_id = request.user_id

    # 检查并发连接数
    if sse_connections.get(session_id, 0) >= MAX_SSE_PER_USER:
        raise HTTPException(429, "Too many concurrent connections")

    sse_connections[session_id] = sse_connections.get(session_id, 0) + 1
    try:
        # SSE 流式响应
        yield ...
    finally:
        sse_connections[session_id] -= 1

# ❌ 错误 - 无限制 SSE 连接，可能导致资源耗尽
```

**生产环境基准值**：

- 每个用户最多 3 个并发 SSE 连接
- 全局最大 SSE 连接数：1000（根据服务器资源调整）
- 超时自动断开：5 分钟无活动

#### 1.4 消息队列长度限制

**强制要求**：

```python
# ✅ 正确 - 限制队列长度
if session_id not in sse_queues:
    sse_queues[session_id] = asyncio.Queue(maxsize=100)  # 最多100条消息

try:
    sse_queues[session_id].put_nowait(message)
except asyncio.QueueFull:
    logger.warning(f"SSE 队列已满: {session_id}")
    # 丢弃最旧的消息
    sse_queues[session_id].get_nowait()
    sse_queues[session_id].put_nowait(message)

# ❌ 错误 - 无限制队列，可能导致内存溢出
sse_queues[session_id] = asyncio.Queue()  # 无限大小
```

---

### 2. 实时性要求 (Real-Time Performance)

#### 2.1 SSE 优于轮询

**强制要求**：所有实时更新必须使用 SSE，禁止使用短轮询

```typescript
// ✅ 正确 - 使用 SSE 实时推送
const eventSource = new EventSource(`/api/chat/stream`)
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data)
  // 实时更新 UI
}

// ❌ 错误 - 使用轮询，延迟高、资源浪费
setInterval(async () => {
  const response = await fetch('/api/sessions/stats')
  // 每5秒查询一次
}, 5000)
```

**性能对比**：

- SSE 推送延迟：< 100ms
- 5秒轮询延迟：平均 2.5秒
- 资源消耗：SSE 节省 80% 网络请求

#### 2.2 消息推送延迟要求

**强制要求**：

```python
# ✅ 正确 - 立即推送消息，不缓冲
@app.post("/api/manual/messages")
async def manual_message(request: dict):
    session_name = request.get("session_name")

    # 保存消息到存储
    await session_store.save(session_state)

    # 【关键】立即推送到 SSE 队列，不等待批处理
    if session_name in sse_queues:
        await sse_queues[session_name].put({
            "type": "manual_message",
            "content": request.get("content"),
            "timestamp": time.time()
        })
        # 目标延迟: < 50ms

# ❌ 错误 - 批量推送，延迟高
messages_buffer = []
async def flush_messages():
    while True:
        await asyncio.sleep(1)  # 每秒批量推送一次
        for msg in messages_buffer:
            await push_sse(msg)
```

**生产环境基准值**：

- 人工消息推送延迟：< 100ms（从发送到用户收到）
- 状态变化通知延迟：< 50ms
- AI 响应流式推送：实时逐字显示，< 50ms 首字延迟

#### 2.3 前端响应性能

**强制要求**：

```typescript
// ✅ 正确 - 使用虚拟滚动处理大量消息
import { VirtualList } from 'vue-virtual-scroller'

// 超过100条消息时启用虚拟滚动
<VirtualList
  :items="messages"
  :item-height="80"
  v-if="messages.length > 100"
>
  <template v-slot="{ item }">
    <ChatMessage :message="item" />
  </template>
</VirtualList>

// ❌ 错误 - 直接渲染所有消息，卡顿
<div v-for="msg in messages" :key="msg.id">
  <ChatMessage :message="msg" />
</div>  <!-- 1000条消息会导致严重卡顿 -->
```

**性能目标**：

- 消息列表滚动帧率：60 FPS
- 新消息追加延迟：< 16ms（一帧）
- 支持消息数：10,000+ 条不卡顿

#### 2.4 Coze API 超时设置

**强制要求**：

```python
# ✅ 正确 - 设置合理的超时
HTTP_TIMEOUT = httpx.Timeout(
    connect=5.0,   # 连接超时 5秒
    read=30.0,     # 读取超时 30秒（Coze AI 响应可能较慢）
    write=10.0,    # 写入超时 10秒
    pool=10.0      # 连接池超时 10秒
)

http_client = httpx.Client(timeout=HTTP_TIMEOUT)

# ❌ 错误 - 无超时限制，可能永久阻塞
http_client = httpx.Client()  # 默认无超时
```

**生产环境基准值**：

- Coze API 连接超时：5秒
- Coze API 读取超时：30秒（AI 生成需要时间）
- 内部 API 超时：10秒
- SSE 保活间隔：30秒发送心跳

---

### 3. 资源限制与监控

#### 3.1 内存限制

**强制要求**：

```python
# ✅ 正确 - Redis 内存限制
# redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru  # 内存满时删除最少使用的 key

# ✅ 正确 - 会话数据 TTL
REDIS_SESSION_TTL = 86400  # 24 小时自动过期

# ❌ 错误 - 无限制存储
redis.set(key, value)  # 永久保留，最终耗尽内存
```

#### 3.2 性能监控

**强制要求**：

```python
# ✅ 正确 - 记录慢请求
@app.middleware("http")
async def log_slow_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    if duration > 1.0:  # 超过1秒告警
        logger.warning(
            f"慢请求: {request.method} {request.url.path} "
            f"耗时 {duration:.2f}s"
        )

    return response
```

**监控指标**：

- API 响应时间：P50 < 200ms, P99 < 1s
- SSE 连接数：实时监控
- Redis 内存使用率：< 80%
- CPU 使用率：< 70%（留有余量）

---

### 4. 生产环境检查清单

**每次部署前必须验证**：

#### 4.1 并发性检查

- [ ]  Redis 连接池大小是否配置？（建议 50）
- [ ]  HTTP 客户端是否使用连接池？
- [ ]  SSE 连接数是否有限制？（建议每用户 3 个）
- [ ]  消息队列是否有长度限制？（建议 100）
- [ ]  是否实现了速率限制？

#### 4.2 实时性检查

- [ ]  是否使用 SSE 替代轮询？
- [ ]  消息推送是否立即执行（不批处理）？
- [ ]  超时配置是否合理？（连接 5s，读取 30s）
- [ ]  前端是否使用虚拟滚动？（> 100 条消息）
- [ ]  是否有性能监控？

#### 4.3 压力测试

```bash
# 1. 并发用户测试 - 100 个并发用户
ab -n 1000 -c 100 http://localhost:8000/api/health

# 2. SSE 连接测试 - 50 个并发 SSE 连接
for i in {1..50}; do
  curl -N http://localhost:8000/api/chat/stream &
done

# 3. 监控资源使用
watch -n 1 'redis-cli INFO memory | grep used_memory_human'
```

**通过标准**：

- 100 并发用户：平均响应时间 < 500ms
- 50 并发 SSE：无连接拒绝
- Redis 内存：< 80% 使用率
- 无错误日志

---

### 5. 典型场景性能要求


| 场景             | 并发要求               | 实时性要求           |
| ---------------- | ---------------------- | -------------------- |
| **用户发送消息** | 支持 100+ 并发         | AI 响应延迟 < 2s     |
| **坐席接入会话** | 支持 10 个坐席同时操作 | 状态变化通知 < 50ms  |
| **人工消息推送** | 支持 50+ 并发会话      | 消息推送延迟 < 100ms |
| **会话列表刷新** | 支持 10 个坐席同时查询 | 使用 SSE 自动更新    |
| **历史消息加载** | 支持 1000+ 条消息      | 首屏渲染 < 500ms     |

---

### 6. 违规后果

**不遵守并发性和实时性要求将导致**：

🔴 **并发性问题**：

- 连接池耗尽 → 服务不可用
- 无速率限制 → 被 DDoS 攻击
- 内存溢出 → 系统崩溃

🔴 **实时性问题**：

- 使用轮询 → 延迟高、资源浪费
- 无超时设置 → 请求永久阻塞
- 消息批处理 → 用户体验差

---

**文档维护者**: Claude Code
**最后更新**: 2025-11-27
**文档版本**: v1.4 ⭐ 将自动化测试纳入开发流程（阶段2），强制要求测试集成到回归测试
