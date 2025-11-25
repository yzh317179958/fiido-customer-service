# 工单与跨团队协作 - 任务拆解文档

> 文档版本: v1.0
> 创建时间: 2025-11-25
> 优先级: P1
> 依赖: codex.md 第3节, customer_context_tasks.md

---

## 📋 模块概述

实现E-bike业务场景下的工单全流程管理，支持跨部门协作（欧洲售前、深圳售后、配件仓、合规团队），与订单系统联动，形成可追溯的审计链路。

### 核心目标

1. **工单自动生成**：从会话自动创建工单，关联订单和车型
2. **流程流转**：支持跨部门指派和状态流转
3. **协作通知**：@同事、评论、附件上传、Slack/企业微信通知
4. **系统对接**：与配件库存、RMA 系统、物流系统联动

---

## 🎯 功能需求（基于 codex.md 第3节）

### 3.1 工单模型 (Ticket Model)

**优先级**: P1
**预计工时**: 8小时

#### 数据模型

```typescript
interface Ticket {
  // 基础信息
  ticket_id: string
  ticket_number: string        // 显示编号 (TK-2023001)
  title: string
  description: string

  // 关联信息
  session_id: string           // 关联会话
  customer_id: string
  order_id: string             // 关联订单
  bike_model: string           // 车型
  vin: string                  // 车辆VIN

  // 分类与优先级
  category: TicketCategory
  priority: TicketPriority
  tags: string[]

  // 状态与流转
  status: TicketStatus
  assignee_id: string          // 当前负责人
  department: Department       // 当前部门
  created_by: string
  created_at: number
  updated_at: number
  resolved_at: number
  closed_at: number

  // SLA
  sla_deadline: number
  sla_status: 'within' | 'warning' | 'breached'

  // AI 分析
  ai_summary: string           // AI 生成摘要
  customer_intent: string      // 客户诉求
  ai_conclusion: string        // AI 处理结论

  // 附件与评论
  attachments: Attachment[]
  comments: Comment[]
  activity_log: Activity[]
}

enum TicketCategory {
  PRE_SALES = 'pre_sales',           // 售前配置
  ORDER_MODIFY = 'order_modify',     // 订单修改
  SHIPPING = 'shipping',             // 物流异常
  AFTER_SALES = 'after_sales',       // 售后维修
  COMPLIANCE = 'compliance',         // 合规申诉
  TECHNICAL = 'technical',           // 技术故障
  RETURNS = 'returns',               // 退换货
  WARRANTY = 'warranty'              // 保修
}

enum TicketPriority {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  URGENT = 'urgent'
}

enum TicketStatus {
  PENDING = 'pending',              // 待接单
  IN_PROGRESS = 'in_progress',      // 处理中
  WAITING_CUSTOMER = 'waiting_customer',  // 待客户
  WAITING_PARTS = 'waiting_parts',  // 待配件
  RESOLVED = 'resolved',            // 已解决
  CLOSED = 'closed'                 // 已关闭
}

enum Department {
  SALES_EU = 'sales_eu',           // 欧洲售前
  SERVICE_CN = 'service_cn',       // 深圳售后
  WAREHOUSE = 'warehouse',         // 配件仓
  COMPLIANCE = 'compliance',       // 合规团队
  TECHNICAL = 'technical',         // 技术支持
  LOGISTICS = 'logistics'          // 物流团队
}
```

#### 核心功能

**3.1.1 自动创建工单**
- 从会话一键创建工单
- 自动拉取 AI 摘要、客户诉求、处理结论
- 自动关联订单、车型、VIN
- 坐席补充人工判断和分类

**3.1.2 工单流转**
- 支持跨部门指派
- 状态自动流转（pending → in_progress → resolved → closed）
- 记录完整时间线
- SLA 自动计算和预警

**3.1.3 协作功能**
- @同事功能
- 评论回复
- 附件上传（发票、关税凭证、照片、维修报告）
- 实时通知（Slack/企业微信）

---

### 3.2 UI 界面要求

**布局位置**:
1. 会话详情右侧 Sidebar > "工单" Tab
2. 独立工单管理页面

**工单面板组件**:
```vue
<TicketPanel>
  <!-- 快速创建 -->
  <QuickCreate v-if="!currentTicket">
    <Button @click="createTicket">从会话创建工单</Button>
  </QuickCreate>

  <!-- 工单详情 -->
  <TicketDetail v-if="currentTicket">
    <TicketHeader>
      <TicketNumber>{{ ticket.ticket_number }}</TicketNumber>
      <StatusBadge :status="ticket.status" />
      <PriorityBadge :priority="ticket.priority" />
    </TicketHeader>

    <TicketInfo>
      <CategoryTag :category="ticket.category" />
      <AssigneeSelect v-model="ticket.assignee_id" />
      <DepartmentSelect v-model="ticket.department" />
      <SLAIndicator :deadline="ticket.sla_deadline" :status="ticket.sla_status" />
    </TicketInfo>

    <RelatedInfo>
      <OrderLink :order_id="ticket.order_id" />
      <BikeModel>{{ ticket.bike_model }}</BikeModel>
      <VIN>{{ ticket.vin }}</VIN>
    </RelatedInfo>

    <AISummary>
      <Summary>{{ ticket.ai_summary }}</Summary>
      <Intent>{{ ticket.customer_intent }}</Intent>
      <Conclusion>{{ ticket.ai_conclusion }}</Conclusion>
    </AISummary>

    <TicketContent>
      <Title>{{ ticket.title }}</Title>
      <Description>{{ ticket.description }}</Description>
    </TicketContent>

    <Attachments>
      <AttachmentItem v-for="file in ticket.attachments" />
      <UploadButton @upload="handleUpload" />
    </Attachments>

    <Comments>
      <CommentItem v-for="comment in ticket.comments" />
      <CommentInput @submit="addComment" />
    </Comments>

    <ActivityLog>
      <TimelineItem v-for="activity in ticket.activity_log" />
    </ActivityLog>
  </TicketDetail>
</TicketPanel>
```

---

## 📝 API 接口设计

### 工单 CRUD

```http
# 创建工单
POST /api/tickets
Authorization: Bearer {agent_token}
Content-Type: application/json

{
  "session_id": "session_123",
  "title": "电池续航异常",
  "description": "客户反馈C11 Pro电池续航不足...",
  "category": "technical",
  "priority": "high",
  "order_id": "order_456",
  "bike_model": "C11 Pro",
  "vin": "VIN123456"
}

# 更新工单
PATCH /api/tickets/{ticket_id}

# 指派工单
POST /api/tickets/{ticket_id}/assign
{
  "assignee_id": "agent_789",
  "department": "service_cn"
}

# 更新状态
POST /api/tickets/{ticket_id}/status
{
  "status": "in_progress",
  "comment": "已开始处理"
}

# 添加评论
POST /api/tickets/{ticket_id}/comments
{
  "content": "已联系仓库调拨配件",
  "mentions": ["@user_123"]
}

# 上传附件
POST /api/tickets/{ticket_id}/attachments
Content-Type: multipart/form-data

# 获取工单列表
GET /api/tickets?status={status}&department={dept}&assignee={id}

# 获取工单详情
GET /api/tickets/{ticket_id}
```

---

## 🔌 系统集成

### 外部系统对接

| 系统 | 集成方式 | 数据同步 |
|------|---------|---------|
| **配件库存系统** | REST API | 实时查询库存 |
| **RMA 系统** | REST API | 创建退货单 |
| **物流系统** | Webhook | 同步物流单号 |
| **Slack** | Webhook | 工单通知 |
| **企业微信** | API | 工单通知 |

---

## 📊 SLA 配置

| 分类 | 优先级 | 响应时间 | 解决时间 |
|------|-------|---------|---------|
| 售前配置 | NORMAL | 2小时 | 24小时 |
| 订单修改 | HIGH | 30分钟 | 4小时 |
| 物流异常 | HIGH | 1小时 | 12小时 |
| 售后维修 | NORMAL | 4小时 | 48小时 |
| 技术故障 | URGENT | 15分钟 | 8小时 |
| 合规申诉 | HIGH | 2小时 | 24小时 |

---

## 📝 开发任务清单

### 后端任务 (20小时)

- [ ] Task 1: 工单数据模型设计 (3h)
- [ ] Task 2: 工单 CRUD API (5h)
- [ ] Task 3: 流转与指派逻辑 (4h)
- [ ] Task 4: SLA 计算引擎 (3h)
- [ ] Task 5: 通知集成（Slack/企业微信）(3h)
- [ ] Task 6: 附件上传与存储 (2h)

### 前端任务 (16小时)

- [ ] Task 7: 工单面板组件 (4h)
- [ ] Task 8: 工单详情页面 (4h)
- [ ] Task 9: 评论与@功能 (3h)
- [ ] Task 10: 附件上传组件 (2h)
- [ ] Task 11: 活动时间线组件 (2h)
- [ ] Task 12: 工单列表与搜索 (1h)

### 测试任务 (4h)

- [ ] Task 13: 单元测试 (2h)
- [ ] Task 14: 集成测试 (2h)

**预计总工时**: 40小时

---

## 📚 相关文档

- 📘 [codex.md](../../codex.md) - 第3节：工单与跨团队协作
- 📘 [customer_context_tasks.md](./customer_context_tasks.md) - 客户信息依赖
- 📘 [CLAUDE.md](../../CLAUDE.md) - 开发流程规范

---

**文档维护者**: Claude Code
**最后更新**: 2025-11-25
