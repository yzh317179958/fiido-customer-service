# Fiido 智能客服系统 - Claude 开发指令

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

**强制要求**：每个新会话必须预先调用 `/api/conversation/new` 创建独立的 `conversation_id`

```python
# ❌ 错误 - 直接发送消息会导致会话隔离失败
POST /api/chat {"message": "你好", "user_id": "session_a"}

# ✅ 正确 - 预先创建 conversation
POST /api/conversation/new {"session_id": "session_a"}
# 响应: {"conversation_id": "xxx"}

POST /api/chat {
  "message": "你好",
  "user_id": "session_a",
  "conversation_id": "xxx"
}
```

### 铁律 5: 状态机约束

```
bot_active → pending_manual → manual_live → bot_active
```

- 状态转换必须按顺序，不可跳跃
- 人工接管期间**必须阻止 AI 对话**（返回 409）
- `conversation_id` 由 Coze 自动生成，**禁止手动创建**

---

## 📋 开发流程规范

### 阶段1: 开发前审查

**在开始任何新功能开发之前，必须完成**：

#### 1.1 全新功能方案文档要求 ⭐ **强制执行**

**触发条件**：开发全新的模块功能时（不包括小改动或对原有功能的改善）

**强制要求**：
- ✅ **必须先编写详细的实施方案文档**，包含以下内容：
  1. **为什么需要这个功能？** - 当前问题分析，用实际场景演示
  2. **技术原理是什么？** - 清晰解释工作原理和核心概念
  3. **需要什么工具和配置？** - 详细的安装步骤和配置说明
  4. **如何实现？** - 完整的实施步骤，包含代码示例
  5. **最终效果是什么？** - Before/After 对比，验证标准
  6. **实施时间估算** - 各阶段耗时预估
  7. **常见问题 FAQ** - 预见性问题解答

**文档存放位置**：`docs/{功能名称}_实施方案详解.md`

**开发流程**：
1. 用户提出全新功能需求
2. Claude 编写详细方案文档（不开始开发）
3. 用户阅读并确认理解
4. 用户明确确认后，Claude 开始实施

**示例**：Redis 数据持久化 → 先创建 `docs/Redis数据持久化实施方案详解.md`

**例外情况**：
- 用户明确说"不用写方案文档"时可跳过
- 对原有功能的小改动、bug 修复不需要
- 用户明确说"立即开始开发"可跳过

---

#### 1.2 约束文档审查清单
- [ ] 阅读 `prd/02_约束与原则/CONSTRAINTS_AND_PRINCIPLES.md`
- [ ] 阅读 `prd/03_技术方案/TECHNICAL_SOLUTION_v1.0.md`
- [ ] 确认新功能是否涉及 Coze API 调用
- [ ] 确认新功能是否会修改现有接口
- [ ] 检查是否引入新的外部依赖

#### 1.3 基线验证
```bash
# 在开始开发前，运行基线测试确保当前系统正常
./tests/regression_test.sh
# 预期: 12/12 通过，否则不得开始新功能开发
```

#### 1.4 设计审查
- [ ] 新功能是否遵循"前置检查 + 后置处理"模式？
- [ ] 新功能失败时是否会影响核心 AI 对话？（必须是"否"）
- [ ] 是否需要添加新的约束条款？

### 阶段2: 开发中约束

#### 2.1 代码实现检查清单
- [ ] 新增代码是否遵循现有代码风格？
- [ ] 是否添加了充足的错误处理？
- [ ] 新功能失败时是否会阻塞核心功能？（不应阻塞）
- [ ] 是否添加了结构化日志记录？
- [ ] 敏感信息是否已脱敏？

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

### 阶段3: 开发后验证

```bash
# 必须运行回归测试
cd /home/yzh/AI客服/鉴权
./tests/regression_test.sh
# 预期: 12/12 通过
```

**验证要求**：
1. 核心对话功能不受影响
2. 会话隔离机制完整
3. 错误隔离：新功能异常不导致核心功能失败

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

```bash
# 启动后端
python3 backend.py

# 启动用户端
cd frontend && npm run dev

# 启动坐席工作台
cd agent-workbench && npm run dev

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

---

## ❌ 禁止事项

1. **不要修改** `.env` 中的 Coze 凭证
2. **不要删除** 任何现有的 API 端点
3. **不要修改** Coze API 的调用方式和返回解析
4. **不要绕过** token_manager 直接生成 Token
5. **不要使用** WebSocket 替换 SSE 流式响应
6. **不要跳过** 回归测试就提交代码
7. **不要在** 人工接管期间允许 AI 对话

---

## 📚 文档索引

完整文档结构见 `prd/INDEX.md`

```
prd/
├── 01_全局指导/     # 系统需求和指导
├── 02_约束与原则/   # 技术约束（最重要）
├── 03_技术方案/     # 架构和API
├── 04_任务拆解/     # 开发任务
└── 05_验收与记录/   # 测试和验收
```
