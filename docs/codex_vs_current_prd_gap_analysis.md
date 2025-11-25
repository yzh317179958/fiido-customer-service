# Codex.md 与现有 PRD 功能差异分析报告

> **版本**: v1.0
> **创建时间**: 2025-11-25
> **分析者**: Claude Code
> **目的**: 识别 codex.md 中的新需求,并以现有文档约束为准进行整合

---

## 📋 分析原则

**重要**: 如果 codex.md 与现有文档约束有冲突,**以现有文档的约束为准**。

**现有约束文档优先级**:
1. `prd/02_约束与原则/CONSTRAINTS_AND_PRINCIPLES.md` - 最高优先级
2. `prd/02_约束与原则/TECHNICAL_CONSTRAINTS.md` - 技术约束
3. `prd/02_约束与原则/coze.md` - Coze API 约束
4. `CLAUDE.md` - 开发流程规范

---

## 🔍 功能对比总览

### Codex.md 特有的功能需求

| 功能模块 | Codex.md 描述 | 现有 PRD 状态 | 评估结论 |
|---------|--------------|--------------|----------|
| **1. Fiido E-bike 业务背景** | 欧洲独立站、10+车型、跨境电商 | ❌ 无 | 🟢 可添加为业务上下文 |
| **2. 客户画像增强** | GDPR、VIP会员、支付货币、国家/城市 | ⚠️  部分(VIP) | 🟢 可扩展用户画像 |
| **3. Shopify 订单集成** | 订单号、SKU、物流、VIN、电池序列号 | ❌ 无 | 🟡 需评估复杂度 |
| **4. 多语言翻译** | EN/DE/FR/IT/ES 实时翻译 | ❌ 无 | 🟡 需评估实现成本 |
| **5. 工单系统** | 完整工单流程、SLA、跨团队协作 | ❌ 无 | 🔴 大功能,需独立方案 |
| **6. E-bike 知识库** | FAQ 库、多语言、审批流程 | ❌ 无 | 🔴 大功能,需独立方案 |
| **7. AI 质量分析** | 命中率、响应时长、误判分析 | ❌ 无 | 🟢 可添加为统计功能 |
| **8. 坐席效率分析** | 接入率、等待时间、转接率 | ❌ 无 | 🟢 可添加为统计功能 |
| **9. 客户体验指标** | CSAT/NPS、退货率、合规投诉率 | ❌ 无 | 🟡 需外部系统集成 |
| **10. 外部系统集成** | Shopify、OMS、RMA、CRM、Slack | ❌ 无 | 🔴 需评估接口对接 |
| **11. 合规性要求** | GDPR、EU Battery Regulation、CE | ❌ 无 | 🟢 可添加为文档说明 |

**图例**:
- 🟢 低复杂度,可直接添加到现有文档
- 🟡 中等复杂度,需要评估实现成本
- 🔴 高复杂度,需要独立实施方案

---

## 📊 详细功能差异分析

### 1. 客户信息与业务上下文

#### Codex.md 需求

```markdown
### 1. 客户信息与业务上下文
- **1.1 客户画像**
  - 展示客户姓名、邮箱、电话、所在国家/城市、语言偏好、支付货币
  - 提示 GDPR 同意状态、营销订阅状态、是否加入 VIP 车友会

- **1.2 订单与设备**
  - 同步最近 3 个 Shopify 订单
  - 展示物流轨迹、车辆 VIN、电池型号/序列号

- **1.3 对话历史**
  - 展示 AI/人工的完整历史
  - 知识库命中记录
  - 用户情绪评分
```

#### 现有 PRD 状态

**PRD_COMPLETE_v3.0.md**:
- ✅ 已有基础会话管理(`SessionState`)
- ✅ 已有用户画像基础字段(`user_profile`: `nickname`, `vip`)
- ❌ 无 GDPR 状态、营销订阅
- ❌ 无订单集成、VIN、电池序列号
- ❌ 无知识库命中记录
- ❌ 无情绪评分

#### 冲突检查

**CONSTRAINTS_AND_PRINCIPLES.md**:
```
约束7: SessionState 扩展约束
- 允许添加新字段(如 GDPR 状态、订单信息)
- 不得修改核心状态机逻辑
```

✅ **无冲突** - 可以扩展 `user_profile` 字段

#### 集成建议

🟢 **低复杂度** - 扩展现有数据模型

**实施步骤**:
1. 扩展 `SessionState.user_profile` 字段:
   ```python
   class UserProfile:
       nickname: str
       vip: bool = False
       # ✅ 新增字段
       gdpr_consent: bool = False
       marketing_subscribed: bool = False
       country: str = ""
       city: str = ""
       language: str = "en"
       currency: str = "USD"
   ```

2. 添加订单信息(可选):
   ```python
   class OrderInfo:
       order_id: str
       product_sku: str
       vin: str = ""  # 车辆识别码
       battery_serial: str = ""
   ```

3. 更新文档:
   - `prd/03_技术方案/api_contract.md` - 更新数据模型
   - `prd/05_验收与记录/ACCEPTANCE_CRITERIA_v1.0.md` - 添加验收标准

---

### 2. 实时对话监控与干预

#### Codex.md 需求

```markdown
### 2. 实时对话监控与干预
- **2.1 队列与状态管理**
  - 列表支持按优先级、等待时长、国家、订单金额排序

- **2.2 干预触发规则**
  - 高价值订单(>€2000)
  - Shopify 大促、预售、缺货状态

- **2.4 聊天能力**
  - 支持多语言切换、翻译(英/德/法/意/西)
  - 一键插入订单信息、物流追踪链接
```

#### 现有 PRD 状态

**PRD_COMPLETE_v3.0.md**:
- ✅ 已有队列管理(`GET /api/sessions`)
- ✅ 已有触发规则(`regulator.py`: 关键词、AI 失败、VIP)
- ❌ 无订单金额触发
- ❌ 无多语言翻译
- ❌ 无订单信息快捷插入

**agent_workbench_tasks.md**:
- ✅ P2 任务: 快捷短语/模板(待开发)

#### 冲突检查

**CONSTRAINTS_AND_PRINCIPLES.md**:
```
约束9: 监管引擎扩展约束
- 允许添加新的触发规则
- 不得修改核心检测逻辑
```

✅ **无冲突** - 可以添加新的触发规则

#### 集成建议

🟢 **低复杂度** - 扩展触发规则

**实施步骤**:
1. 扩展 `Regulator.check()` 方法:
   ```python
   # 新增高价值订单触发
   if session_state.order_amount and session_state.order_amount > 2000:
       return EscalationDecision(
           should_escalate=True,
           reason="high_value_order",
           severity="high"
       )
   ```

2. 添加快捷短语配置:
   - 在 `.env` 或后端配置文件中添加多语言模板
   - 更新 `agent_workbench_tasks.md` P2 任务

🟡 **中等复杂度** - 多语言翻译

**评估结论**: 需要调用外部翻译 API(如 DeepL、Google Translate),建议作为 P2 功能

---

### 3. 工单与跨团队协作

#### Codex.md 需求

```markdown
### 3. 工单与跨团队协作
- **3.1 工单模型**
  - 工单字段: 工单号、关联会话、订单号、车型、问题分类、优先级、SLA

- **3.2 流程与流转**
  - 支持跨部门指派(售前、售后、配件仓、合规)
  - 工单状态: 待接单 → 处理中 → 待客户 → 已解决 → 已关闭

- **3.3 通知与协作**
  - @同事、评论、上传维修报告
  - 同步 Slack/企业微信通知
```

#### 现有 PRD 状态

**PRD_COMPLETE_v3.0.md**:
- ❌ 完全无工单系统相关内容

#### 冲突检查

**CLAUDE.md**:
```
阶段1: 开发前审查
- 全新功能必须先编写详细的实施方案文档
```

🔴 **需要独立实施方案**

#### 集成建议

🔴 **高复杂度** - 需要独立方案文档

**建议**:
1. 按照 CLAUDE.md 要求,先创建 `docs/工单系统实施方案详解.md`
2. 包含以下内容:
   - 为什么需要工单系统?(当前问题分析)
   - 工单系统技术原理
   - 数据模型设计
   - API 接口设计
   - 与会话系统的关联
   - 实施步骤和时间估算
3. 用户确认方案后再开发

**不建议在本次整合**: 工单系统是独立的大功能,应作为后续迭代内容

---

### 4. AI 表现与运营分析

#### Codex.md 需求

```markdown
### 4. AI 表现与运营分析
- **4.1 AI 质量**
  - 统计分国家/语言/车型的 AI 命中率、平均响应时长

- **4.2 坐席效率**
  - 接入率、平均等待时间、服务时长、转接率、一次解决率

- **4.3 客户体验**
  - 售前转化率、售后满意度(CSAT/NPS)、退货率
```

#### 现有 PRD 状态

**PRD_COMPLETE_v3.0.md**:
- ✅ 已有统计接口(`GET /api/sessions/stats`)
- ❌ 仅包含基础统计(会话数量、状态分布)

**api_contract.md**:
```python
GET /api/sessions/stats
Response:
{
  "total_sessions": 50,
  "by_status": {...},
  "active_agents": 2,
  "avg_waiting_time": 120
}
```

#### 冲突检查

✅ **无冲突** - 可以扩展统计字段

#### 集成建议

🟢 **低复杂度** - 扩展统计 API

**实施步骤**:
1. 扩展 `/api/sessions/stats` 返回字段:
   ```python
   {
     "ai_quality": {
       "avg_response_time_ms": 850,
       "success_rate": 0.85,
       "escalation_rate": 0.15
     },
     "agent_efficiency": {
       "avg_takeover_time_sec": 120,
       "avg_service_time_sec": 300,
       "resolution_rate": 0.92
     }
   }
   ```

2. 更新文档:
   - `prd/03_技术方案/api_contract.md` - 更新统计接口
   - `prd/05_验收与记录/TESTING_GUIDE.md` - 添加测试用例

---

### 5. 知识库与学习回路

#### Codex.md 需求

```markdown
### 5. 知识库与学习回路
- **5.1 E-bike 主题知识库**
  - 结构化整理 FAQ 主题(售前参数、合法性、退换货等)
  - 按车型(C 系列/T 系列)与市场(EU/UK)分类

- **5.2 回流机制**
  - 工单关闭时沉淀为知识
  - 知识管理员审批
  - AI 团队定期更新模型
```

#### 现有 PRD 状态

**PRD_COMPLETE_v3.0.md**:
- ❌ 完全无知识库相关内容

#### 冲突检查

**CLAUDE.md**:
```
阶段1: 开发前审查
- 全新功能必须先编写详细的实施方案文档
```

🔴 **需要独立实施方案**

#### 集成建议

🔴 **高复杂度** - 需要独立方案文档

**建议**:
1. 先创建 `docs/E-bike知识库系统实施方案详解.md`
2. 包含以下内容:
   - 知识库数据模型设计
   - 与 Coze Workflow 的集成方式(如何更新 Prompt)
   - 审批流程设计
   - 多语言支持方案
3. 用户确认方案后再开发

**不建议在本次整合**: 知识库系统是独立的大功能,应作为后续迭代内容

---

### 6. 安全、权限与合规

#### Codex.md 需求

```markdown
### 6. 安全、权限与合规
- **6.1 权限模型**
  - 角色: 坐席、组长、运营、技术、合规、仓储
  - 每个角色控制读写权限

- **6.2 数据与合规**
  - 全链路 TLS、加密存储敏感字段
  - 满足 GDPR、EU Battery Regulation、CE 合规
```

#### 现有 PRD 状态

**PRD_COMPLETE_v3.0.md**:
- ✅ 已有坐席认证系统(v2.3.7+)
- ✅ 已有 JWT Token 认证
- ❌ 无多角色权限控制

**CONSTRAINTS_AND_PRINCIPLES.md**:
```
约束17: 坐席认证安全性约束
- JWT Token 有效期 1 小时
- 密码 bcrypt 加密
```

#### 冲突检查

✅ **无冲突** - 可以扩展权限系统

#### 集成建议

🟡 **中等复杂度** - 扩展权限系统

**实施步骤**:
1. 扩展 JWT Token 的 `role` 字段:
   ```python
   class AgentRole(str, Enum):
       AGENT = "agent"          # 坐席
       SUPERVISOR = "supervisor"  # 组长
       ADMIN = "admin"          # 管理员
   ```

2. 添加权限中间件:
   ```python
   def require_role(allowed_roles: List[AgentRole]):
       # 检查 JWT Token 的 role 字段
       pass
   ```

3. 更新文档:
   - `prd/04_任务拆解/admin_management_tasks.md` - 添加角色管理任务

🟢 **低复杂度** - 合规性文档说明

**建议**: 添加 `docs/合规性说明.md` 文档,说明系统如何满足 GDPR、CE 等合规要求

---

## 📋 整合建议优先级

### P0 - 当前版本立即整合(低复杂度)

| 功能 | 工作量 | 文件修改 |
|------|--------|---------|
| 1. 扩展用户画像字段 | 2小时 | `src/session_state.py`, `api_contract.md` |
| 2. 扩展触发规则(订单金额) | 1小时 | `src/regulator.py` |
| 3. 扩展统计 API | 2小时 | `backend.py`, `api_contract.md` |
| 4. 添加合规性文档 | 1小时 | `docs/合规性说明.md` (新建) |

**总计**: 约 6 小时

### P1 - 下一版本(中等复杂度)

| 功能 | 工作量 | 备注 |
|------|--------|------|
| 1. 多语言翻译功能 | 8小时 | 需调用外部 API |
| 2. 快捷短语多语言 | 4小时 | 扩展现有 P2 任务 |
| 3. 多角色权限控制 | 12小时 | 扩展认证系统 |

**总计**: 约 24 小时

### P2 - 后续迭代(高复杂度)

| 功能 | 工作量 | 备注 |
|------|--------|------|
| 1. 工单系统 | 80小时 | 需独立实施方案 |
| 2. E-bike 知识库 | 60小时 | 需独立实施方案 |
| 3. Shopify 订单集成 | 40小时 | 需对接 Shopify API |
| 4. 外部系统集成(CRM/Slack) | 60小时 | 需对接多个外部系统 |

**总计**: 约 240 小时

---

## 🎯 本次整合范围建议

**建议仅整合 P0 功能**,理由:

1. **符合 CLAUDE.md 规范**: P1、P2 功能需要独立实施方案
2. **不破坏现有约束**: 所有 P0 功能均不涉及核心接口修改
3. **可快速交付**: P0 功能 6 小时即可完成

**不建议整合的内容**:
- ❌ 工单系统(需独立方案)
- ❌ 知识库系统(需独立方案)
- ❌ Shopify 订单集成(复杂度高)
- ❌ 多语言翻译(需外部 API)

---

## 📝 下一步行动

### Step 1: 用户确认整合范围

请用户确认:
1. 是否同意仅整合 P0 功能?
2. 是否需要对 P1、P2 功能编写独立实施方案?

### Step 2: 执行 P0 功能整合

如果用户同意,执行以下操作:

1. **扩展数据模型**:
   - 修改 `src/session_state.py`
   - 更新 `prd/03_技术方案/api_contract.md`

2. **扩展触发规则**:
   - 修改 `src/regulator.py`
   - 更新 `prd/02_约束与原则/CONSTRAINTS_AND_PRINCIPLES.md`

3. **扩展统计 API**:
   - 修改 `backend.py`
   - 更新 `prd/03_技术方案/api_contract.md`

4. **添加合规性文档**:
   - 创建 `docs/合规性说明.md`

5. **更新 PRD_COMPLETE_v3.0.md**:
   - 添加 Fiido E-bike 业务背景章节
   - 更新数据模型章节
   - 更新统计功能章节

### Step 3: 回归测试

```bash
cd /home/yzh/AI客服/鉴权
./tests/regression_test.sh
# 预期: 12/12 通过
```

---

## 📚 文档更新清单

### 需要更新的文档

- [ ] `prd/01_全局指导/PRD_COMPLETE_v3.0.md` - 添加 Fiido 业务背景
- [ ] `prd/02_约束与原则/CONSTRAINTS_AND_PRINCIPLES.md` - 更新约束说明
- [ ] `prd/03_技术方案/api_contract.md` - 更新数据模型和 API
- [ ] `prd/05_验收与记录/ACCEPTANCE_CRITERIA_v1.0.md` - 添加验收标准
- [ ] `prd/05_验收与记录/TESTING_GUIDE.md` - 添加测试用例

### 需要新建的文档

- [ ] `docs/合规性说明.md` - GDPR、CE 合规性说明

---

**最后更新**: 2025-11-25
**维护者**: Fiido AI 客服开发团队
**文档版本**: v1.0
