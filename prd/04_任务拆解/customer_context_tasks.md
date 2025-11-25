# 客户信息与业务上下文 - 任务拆解文档

> 文档版本: v1.0
> 创建时间: 2025-11-25
> 优先级: P1
> 依赖: codex.md 第1节, Shopify API, 设备管理系统

---

## 📋 模块概述

为坐席提供完整的客户画像和业务上下文信息，支持欧洲多语言、多币种、多站点的E-bike业务场景，帮助坐席快速了解客户背景并提供精准服务。

### 核心目标

1. **聚合客户画像**：姓名、邮箱、电话、国家/城市、语言偏好、支付货币、GDPR状态
2. **订单与设备信息**：Shopify订单同步、车型配置、物流轨迹、车辆VIN、电池/电机信息
3. **对话历史洞察**：AI/人工完整历史、知识库命中、用户情绪评分

---

## 🎯 功能需求（基于 codex.md 第1节）

### 1.1 客户画像 (Customer Profile)

**优先级**: P1
**预计工时**: 8小时

#### 功能描述

展示客户基本信息和合规状态，支持多语言和脱敏视图。

#### 数据字段

| 字段分类 | 字段名 | 类型 | 说明 | 数据源 |
|---------|-------|------|------|--------|
| **基本信息** | customer_id | string | 客户唯一ID | Shopify |
| | name | string | 客户姓名 | Shopify |
| | email | string | 邮箱（支持脱敏） | Shopify |
| | phone | string | 电话（支持脱敏） | Shopify |
| | country | string | 所在国家 | Shopify |
| | city | string | 所在城市 | Shopify |
| | language_preference | string | 语言偏好 (en/de/fr/it/es) | Shopify/Session |
| | payment_currency | string | 支付货币 (EUR/GBP) | Shopify |
| | source_channel | string | 来源渠道 | Shopify Tags |
| **合规状态** | gdpr_consent | boolean | GDPR同意状态 | Shopify |
| | marketing_subscribed | boolean | 营销订阅状态 | Shopify |
| | vip_status | string | VIP车友会状态 | CRM |
| **显示控制** | is_sensitive_hidden | boolean | 是否脱敏显示 | 前端控制 |

#### 来源渠道枚举

- `shopify_organic` - Shopify独立站自然流量
- `shopify_campaign` - 门户活动
- `amazon` - 亚马逊
- `dealer` - 经销商
- `other` - 其他

#### UI界面要求

**布局位置**: 会话详情右侧 Sidebar > "客户信息" Tab

**显示组件**:
```vue
<CustomerProfile>
  <!-- 基本信息卡片 -->
  <ProfileCard>
    <Avatar :src="customer.avatar_url" />
    <Name>{{ customer.name }}</Name>
    <Email :sensitive="true">{{ customer.email }}</Email>
    <Phone :sensitive="true">{{ customer.phone }}</Phone>
    <Location>
      <CountryFlag :code="customer.country" />
      {{ customer.city }}, {{ customer.country }}
    </Location>
    <Language>{{ getLanguageName(customer.language_preference) }}</Language>
    <Currency>{{ customer.payment_currency }}</Currency>
  </ProfileCard>

  <!-- 来源与状态 -->
  <StatusCard>
    <SourceChannel :channel="customer.source_channel" />
    <GDPRStatus :consented="customer.gdpr_consent" />
    <MarketingStatus :subscribed="customer.marketing_subscribed" />
    <VIPBadge v-if="customer.vip_status" :level="customer.vip_status" />
  </StatusCard>
</CustomerProfile>
```

#### API 接口设计

**获取客户画像**:
```http
GET /api/customers/{customer_id}/profile
Authorization: Bearer {agent_token}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "customer_id": "cust_12345",
    "name": "John Doe",
    "email": "j***@example.com",  // 脱敏
    "phone": "+49***1234",         // 脱敏
    "country": "DE",
    "city": "Berlin",
    "language_preference": "de",
    "payment_currency": "EUR",
    "source_channel": "shopify_organic",
    "gdpr_consent": true,
    "marketing_subscribed": false,
    "vip_status": "gold",
    "created_at": 1700000000
  }
}
```

#### 技术实现要点

1. **脱敏逻辑**:
   - 邮箱: 只显示首字母和域名 `j***@example.com`
   - 电话: 只显示区号和尾号 `+49***1234`
   - 可通过权限控制是否显示完整信息

2. **国家旗帜组件**:
   - 使用 `country-flag-icons` 或 emoji flag
   - 支持 ISO 3166-1 alpha-2 国家代码

3. **多语言支持**:
   - 界面文字使用 vue-i18n
   - 支持 en/de/fr/it/es 五种语言

#### 验收标准

- [ ] 客户画像卡片正确显示所有字段
- [ ] 脱敏功能正确工作（邮箱、电话）
- [ ] 国家旗帜正确显示
- [ ] VIP 状态正确显示徽章
- [ ] GDPR 状态正确标识
- [ ] 支持5种语言切换

---

### 1.2 订单与设备信息 (Orders & Devices)

**优先级**: P1
**预计工时**: 16小时

#### 功能描述

同步Shopify最近3个订单，展示订单详情、产品配置、物流轨迹、车辆VIN、电池/电机信息。

#### 订单数据模型

```typescript
interface Order {
  order_id: string           // Shopify订单号
  order_number: string       // 显示编号 (#1001)
  status: OrderStatus        // 订单状态
  created_at: number         // 下单时间
  total_amount: number       // 订单金额
  currency: string           // 币种
  vat_amount: number         // VAT金额
  discount_amount: number    // 折扣金额
  shipping_fee: number       // 运费
  customs_fee: number        // 关税
  payment_method: string     // 支付方式
  warehouse: string          // 发货仓
  items: OrderItem[]         // 订单商品
  shipping: ShippingInfo     // 物流信息
}

interface OrderItem {
  product_id: string         // 产品ID
  sku: string                // SKU
  product_name: string       // 产品名称 (C11 Pro)
  category: string           // 车型系列 (C/T/M/N)
  color: string              // 颜色
  quantity: number           // 数量
  price: number              // 单价
  configuration: BikeConfig  // 车辆配置
}

interface BikeConfig {
  motor_power: string        // 电机功率 (250W/500W)
  battery_capacity: string   // 电池容量 (48V 14.5Ah)
  battery_removable: boolean // 电池可拆卸
  max_load: string           // 最大承重 (120kg)
  brake_type: string         // 刹车类型 (液压碟刹)
  tire_size: string          // 轮胎规格 (700×40C)
  assist_modes: number       // 辅助模式数量
  firmware_version: string   // 固件版本
}

interface ShippingInfo {
  tracking_number: string    // 追踪号
  carrier: string            // 承运商
  status: ShippingStatus     // 物流状态
  estimated_delivery: number // 预计送达
  actual_delivery: number    // 实际送达
  insurance: boolean         // 是否保险
  customs_cleared: boolean   // 是否清关
  milestones: Milestone[]    // 物流节点
}

interface Milestone {
  timestamp: number          // 时间戳
  location: string           // 地点
  status: string             // 状态描述
  description: string        // 详细描述
}
```

#### 订单状态枚举

```typescript
enum OrderStatus {
  PENDING = 'pending',           // 待处理
  PAID = 'paid',                 // 已支付
  PROCESSING = 'processing',     // 处理中
  SHIPPED = 'shipped',           // 已发货
  IN_TRANSIT = 'in_transit',     // 运输中
  CUSTOMS = 'customs',           // 清关中
  OUT_FOR_DELIVERY = 'out_for_delivery',  // 配送中
  DELIVERED = 'delivered',       // 已送达
  CANCELLED = 'cancelled',       // 已取消
  REFUNDED = 'refunded'          // 已退款
}

enum ShippingStatus {
  PENDING = 'pending',           // 待发货
  SHIPPED = 'shipped',           // 已发货
  IN_TRANSIT = 'in_transit',     // 运输中
  CUSTOMS_HELD = 'customs_held', // 海关扣留
  CUSTOMS_CLEARED = 'customs_cleared', // 已清关
  OUT_FOR_DELIVERY = 'out_for_delivery', // 配送中
  DELIVERED = 'delivered',       // 已送达
  EXCEPTION = 'exception'        // 异常
}
```

#### 设备信息数据模型

```typescript
interface Device {
  vin: string                // 车辆识别码
  product_name: string       // 车型名称
  activation_date: number    // 激活时间
  battery: BatteryInfo       // 电池信息
  motor: MotorInfo           // 电机信息
  firmware: FirmwareInfo     // 固件信息
  warranty: WarrantyInfo     // 保修信息
}

interface BatteryInfo {
  model: string              // 电池型号
  serial_number: string      // 序列号
  capacity: string           // 容量 (48V 14.5Ah)
  removable: boolean         // 是否可拆卸
  cycles: number             // 充电循环次数
  health_percent: number     // 健康度百分比
  warranty_until: number     // 保修期至
}

interface MotorInfo {
  model: string              // 电机型号
  power: string              // 功率 (250W/500W)
  location: string           // 位置 (中置/后轮)
  torque: string             // 扭矩 (80Nm)
}

interface FirmwareInfo {
  version: string            // 版本号
  release_date: number       // 发布日期
  update_available: boolean  // 是否有更新
  latest_version: string     // 最新版本
}

interface WarrantyInfo {
  frame: string              // 车架保修 (2年)
  motor: string              // 电机保修 (2年)
  battery: string            // 电池保修 (1年)
  expires_at: number         // 保修到期
  registration_status: string // 注册状态
}
```

#### UI界面要求

**布局位置**: 会话详情右侧 Sidebar > "订单 & 物流" Tab

**订单列表组件**:
```vue
<OrderList>
  <OrderCard v-for="order in orders" :key="order.order_id">
    <!-- 订单头部 -->
    <OrderHeader>
      <OrderNumber>{{ order.order_number }}</OrderNumber>
      <StatusBadge :status="order.status" />
      <Amount>{{ formatCurrency(order.total_amount, order.currency) }}</Amount>
      <Date>{{ formatDate(order.created_at) }}</Date>
    </OrderHeader>

    <!-- 订单商品 -->
    <OrderItems>
      <ProductItem v-for="item in order.items">
        <ProductImage :src="item.image_url" />
        <ProductName>{{ item.product_name }}</ProductName>
        <SKU>{{ item.sku }}</SKU>
        <Color :color="item.color" />
        <BikeSpecs :config="item.configuration" />
      </ProductItem>
    </OrderItems>

    <!-- 物流追踪 -->
    <ShippingTracking v-if="order.shipping">
      <TrackingNumber>{{ order.shipping.tracking_number }}</TrackingNumber>
      <Carrier>{{ order.shipping.carrier }}</Carrier>
      <ShippingStatus :status="order.shipping.status" />
      <Timeline :milestones="order.shipping.milestones" />
    </ShippingTracking>

    <!-- 设备信息 -->
    <DeviceInfo v-if="item.device">
      <VIN>{{ item.device.vin }}</VIN>
      <BatteryHealth :percent="item.device.battery.health_percent" />
      <FirmwareVersion>{{ item.device.firmware.version }}</FirmwareVersion>
      <WarrantyStatus :info="item.device.warranty" />
    </DeviceInfo>
  </OrderCard>
</OrderList>
```

#### API 接口设计

**获取客户订单列表**:
```http
GET /api/customers/{customer_id}/orders?limit=3
Authorization: Bearer {agent_token}
```

**获取单个订单详情**:
```http
GET /api/orders/{order_id}
Authorization: Bearer {agent_token}
```

**获取设备信息**:
```http
GET /api/devices/{vin}
Authorization: Bearer {agent_token}
```

#### 技术实现要点

1. **Shopify API 集成**:
   - 使用 Shopify REST Admin API 或 GraphQL API
   - 需要 OAuth 认证和 API 密钥
   - 处理速率限制（2次/秒）

2. **物流追踪集成**:
   - 支持多个承运商 API (DHL, UPS, FedEx, etc.)
   - 统一物流状态枚举
   - 缓存追踪信息（避免频繁查询）

3. **设备数据同步**:
   - 从设备管理系统获取 VIN、电池、电机数据
   - 定期同步固件版本信息
   - 健康度计算算法

4. **性能优化**:
   - 订单数据缓存（Redis, 5分钟过期）
   - 懒加载物流追踪（点击展开时加载）
   - 图片 CDN 加速

#### 验收标准

- [ ] 显示最近3个订单
- [ ] 订单状态正确显示
- [ ] 产品配置信息完整
- [ ] 物流追踪时间线正确
- [ ] VAT/关税/运费正确显示
- [ ] 设备VIN正确显示
- [ ] 电池健康度正确计算
- [ ] 固件版本信息正确
- [ ] 保修状态正确显示

---

### 1.3 对话历史 (Conversation History)

**优先级**: P1
**预计工时**: 6小时

#### 功能描述

展示AI/人工的完整对话历史，标注知识库命中情况，分析用户情绪评分，支持按站点、渠道、产品搜索。

#### 对话历史数据模型

```typescript
interface ConversationHistory {
  session_id: string
  customer_id: string
  created_at: number
  updated_at: number
  status: SessionStatus
  channel: string           // 渠道 (web/mobile/whatsapp)
  site: string              // 站点 (EU/UK/US)
  product_context: string[] // 相关产品
  total_messages: number
  ai_messages: number
  human_messages: number
  avg_sentiment: number     // 平均情绪 (-1 to 1)
  knowledge_hits: KnowledgeHit[]
  messages: Message[]
}

interface KnowledgeHit {
  knowledge_id: string
  topic: string             // 主题
  category: string          // 分类
  confidence: number        // 置信度 (0-1)
  timestamp: number
}

interface Message {
  message_id: string
  type: 'user' | 'ai' | 'agent'
  sender_id: string
  sender_name: string
  content: string
  timestamp: number
  sentiment: number         // 情绪评分 (-1 to 1)
  language: string
  knowledge_referenced: string[] // 引用的知识库ID
}
```

#### UI界面要求

**布局位置**: 会话详情右侧 Sidebar > "对话历史" Tab

**对话历史组件**:
```vue
<ConversationHistory>
  <!-- 统计概览 -->
  <HistoryStats>
    <Stat label="总消息数">{{ history.total_messages }}</Stat>
    <Stat label="AI消息">{{ history.ai_messages }}</Stat>
    <Stat label="人工消息">{{ history.human_messages }}</Stat>
    <SentimentIndicator :score="history.avg_sentiment" />
  </HistoryStats>

  <!-- 搜索与筛选 -->
  <SearchFilters>
    <SearchInput v-model="searchKeyword" placeholder="搜索对话内容..." />
    <FilterSelect v-model="filterSite" :options="sites" />
    <FilterSelect v-model="filterProduct" :options="products" />
    <FilterSelect v-model="filterChannel" :options="channels" />
  </SearchFilters>

  <!-- 知识库命中 -->
  <KnowledgeHits v-if="history.knowledge_hits.length">
    <KnowledgeTag
      v-for="hit in history.knowledge_hits"
      :key="hit.knowledge_id"
      :topic="hit.topic"
      :confidence="hit.confidence"
    />
  </KnowledgeHits>

  <!-- 消息列表 -->
  <MessageList>
    <MessageBubble
      v-for="msg in filteredMessages"
      :key="msg.message_id"
      :type="msg.type"
      :content="msg.content"
      :timestamp="msg.timestamp"
      :sentiment="msg.sentiment"
      :knowledge="msg.knowledge_referenced"
    />
  </MessageList>
</ConversationHistory>
```

#### API 接口设计

**获取对话历史**:
```http
GET /api/conversations/history
  ?customer_id={customer_id}
  &site={site}
  &channel={channel}
  &product={product}
Authorization: Bearer {agent_token}
```

#### 技术实现要点

1. **情绪分析**:
   - 使用情感分析模型（如BERT-based）
   - 评分范围 -1（负面）到 1（正面）
   - 可视化情绪曲线

2. **知识库关联**:
   - 标记AI引用的知识库条目
   - 显示置信度评分
   - 支持点击查看原始知识

3. **搜索功能**:
   - 全文搜索消息内容
   - 支持多条件组合筛选
   - 高亮搜索关键词

#### 验收标准

- [ ] 完整显示对话历史
- [ ] AI/人工消息正确区分
- [ ] 知识库命中正确标注
- [ ] 情绪评分正确显示
- [ ] 搜索功能正常工作
- [ ] 筛选器正常工作
- [ ] 支持按时间倒序/正序排列

---

## 🔌 系统集成要求

### 外部系统对接

1. **Shopify API**
   - REST Admin API / GraphQL API
   - 权限范围: `read_orders`, `read_customers`, `read_products`
   - 速率限制: 2 requests/second

2. **物流追踪 API**
   - DHL API
   - UPS API
   - FedEx API
   - 通用物流追踪服务（如 AfterShip）

3. **设备管理系统**
   - 内部设备数据库
   - VIN 查询接口
   - 电池健康度 API
   - 固件版本查询 API

4. **CRM 系统**
   - Salesforce / HubSpot
   - VIP 状态查询
   - 客户标签同步

### 数据同步策略

| 数据类型 | 同步方式 | 频率 | 缓存时长 |
|---------|---------|------|---------|
| 客户画像 | 实时查询 | 按需 | 5分钟 |
| 订单信息 | Webhook + 轮询 | 5分钟 | 10分钟 |
| 物流追踪 | 按需查询 | 按需 | 30分钟 |
| 设备信息 | 实时查询 | 按需 | 1小时 |
| 对话历史 | 实时推送 | 实时 | 无缓存 |

---

## 📊 性能指标

| 指标 | 目标值 | 说明 |
|------|-------|------|
| 客户画像加载时间 | < 500ms | 从点击到显示 |
| 订单列表加载时间 | < 1s | 3个订单 |
| 物流追踪查询 | < 2s | 单次查询 |
| 对话历史加载 | < 500ms | 100条消息 |
| Sidebar 切换响应 | < 100ms | Tab 切换 |

---

## 🔒 安全与合规

### GDPR 合规要求

1. **数据脱敏**
   - 默认脱敏显示邮箱、电话
   - 需要权限才能查看完整信息
   - 记录查看日志

2. **数据访问控制**
   - 基于角色的权限控制
   - 审计日志记录所有访问
   - 支持数据删除请求（Right to be Forgotten）

3. **数据加密**
   - 传输加密（TLS 1.3）
   - 敏感字段存储加密
   - API Token 安全管理

### 权限矩阵

| 角色 | 客户画像 | 订单信息 | 设备VIN | 对话历史 |
|------|---------|---------|---------|---------|
| 坐席 | 脱敏查看 | 完整查看 | 完整查看 | 完整查看 |
| 组长 | 完整查看 | 完整查看 | 完整查看 | 完整查看 |
| 运营 | 完整查看 | 完整查看 | 脱敏查看 | 统计查看 |
| 技术 | 不可见 | 订单号 | 完整查看 | 不可见 |

---

## 📝 开发任务清单

### 后端任务

- [ ] Task 1.1: 设计数据模型（3h）
  - [ ] 定义 TypeScript/Python 类型
  - [ ] 设计数据库表结构
  - [ ] 编写 ORM 模型

- [ ] Task 1.2: Shopify API 集成（6h）
  - [ ] OAuth 认证配置
  - [ ] 客户信息查询接口
  - [ ] 订单列表查询接口
  - [ ] Webhook 接收配置

- [ ] Task 1.3: 物流追踪 API 集成（4h）
  - [ ] 多承运商 API 封装
  - [ ] 统一状态映射
  - [ ] 缓存策略实现

- [ ] Task 1.4: 设备信息 API（3h）
  - [ ] VIN 查询接口
  - [ ] 电池健康度计算
  - [ ] 固件版本查询

- [ ] Task 1.5: 对话历史 API（4h）
  - [ ] 历史查询接口
  - [ ] 知识库关联逻辑
  - [ ] 情绪分析集成
  - [ ] 搜索与筛选实现

- [ ] Task 1.6: 数据同步任务（3h）
  - [ ] Redis 缓存配置
  - [ ] 定时同步任务
  - [ ] Webhook 处理器

### 前端任务

- [ ] Task 2.1: 客户画像组件（4h）
  - [ ] CustomerProfile.vue
  - [ ] ProfileCard.vue
  - [ ] StatusCard.vue
  - [ ] 脱敏逻辑实现

- [ ] Task 2.2: 订单与设备组件（8h）
  - [ ] OrderList.vue
  - [ ] OrderCard.vue
  - [ ] ProductItem.vue
  - [ ] ShippingTracking.vue
  - [ ] DeviceInfo.vue
  - [ ] 物流时间线组件

- [ ] Task 2.3: 对话历史组件（5h）
  - [ ] ConversationHistory.vue
  - [ ] MessageList.vue
  - [ ] MessageBubble.vue
  - [ ] KnowledgeHits.vue
  - [ ] SearchFilters.vue

- [ ] Task 2.4: 集成到 Dashboard（2h）
  - [ ] 添加 Sidebar Tabs
  - [ ] 数据流集成
  - [ ] 状态管理（Pinia Store）

### 测试任务

- [ ] Task 3.1: 单元测试（3h）
  - [ ] API 测试
  - [ ] 组件测试
  - [ ] 工具函数测试

- [ ] Task 3.2: 集成测试（2h）
  - [ ] Shopify API Mock
  - [ ] 端到端测试

- [ ] Task 3.3: GDPR 合规测试（2h）
  - [ ] 脱敏功能测试
  - [ ] 权限控制测试
  - [ ] 审计日志验证

---

## 📚 相关文档

- 📘 [codex.md](../../codex.md) - 第1节：客户信息与业务上下文
- 📘 [CLAUDE.md](../../CLAUDE.md) - 开发流程规范
- 📘 [Shopify API 文档](https://shopify.dev/api/admin-rest)
- 📘 [GDPR 合规指南](https://gdpr.eu/)

---

**文档维护者**: Claude Code
**最后更新**: 2025-11-25
**预计总工时**: 30小时
