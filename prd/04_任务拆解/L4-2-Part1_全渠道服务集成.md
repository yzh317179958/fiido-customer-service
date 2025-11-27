# L4-2-Part1: 全渠道服务集成

> **文档编号**: L4-2-Part1
> **文档版本**: v1.0
> **优先级**: P1（跨境增强层 - 重要）
> **状态**: ❌ 待开发
> **创建时间**: 2025-01-27

---

## 📑 文档导航

- **上级文档**: [ENTERPRISE_EBIKE_SUPPORT_TASKS.md](./ENTERPRISE_EBIKE_SUPPORT_TASKS.md)
- **同级文档**:
  - 上一篇: L4-1 多语言实时翻译系统
  - 当前: L4-2-Part1 全渠道服务集成
  - 下一篇: L4-2-Part2 智能推荐与主动服务
- **依赖关系**: 依赖 L1-1 会话管理、L2-2 客户画像

---

## 🎯 Part 1 概述

### 涵盖模块

| 模块编号 | 模块名称 | 核心功能 |
|---------|---------|---------|
| **模块1** | 社交媒体集成 | Instagram/Facebook/WhatsApp集成 |
| **模块2** | 统一收件箱管理 | 全渠道消息聚合、统一查看 |
| **模块3** | 跨渠道客户识别 | 自动关联、身份合并 |

### 业务价值

**实现后收益**：
- 📈 渠道覆盖率提升 **200%**（网站+社交媒体）
- 📈 客户触达率提升 **150%**（客户在哪里，服务到哪里）
- 📈 坐席效率提升 **80%**（统一处理，无需切换）
- 📊 年轻客户获取提升 **120%**（Instagram/TikTok）

---

## 📋 模块1: 社交媒体集成

### 1.1 Instagram Direct Message集成

**功能需求**：
- 接收Instagram DM到坐席工作台
- 显示客户Instagram资料（头像、用户名、粉丝数）
- 直接回复DM，无需打开Instagram
- 支持图片、视频消息

**业务逻辑**：
```
1. 用户在Instagram发送DM给@fiido_official
2. Instagram Webhook推送消息到系统
3. 系统创建会话（channel='instagram', session_name=instagram_user_id）
4. 坐席工作台显示消息
5. 坐席回复，系统通过Instagram API发送
6. 保存完整对话记录
```

**API集成**：
- Instagram Graph API
- Webhook订阅：`messages`, `messaging_postback`

**约束**：
- Instagram API有24小时响应窗口限制
- 超过24小时需要使用消息模板

### 1.2 Facebook Messenger集成

**功能需求**：
- 接收Facebook Page消息
- 支持Messenger机器人自动回复
- 富媒体消息（按钮、卡片、快捷回复）

**业务逻辑**：
```
1. 客户在Facebook Page发送消息
2. Messenger Webhook推送到系统
3. 系统判断：
   IF 常见问题: AI自动回复
   ELSE: 转人工，坐席接入
4. 支持富媒体回复（产品卡片、快捷按钮）
```

### 1.3 WhatsApp Business集成

**功能需求**：
- 接收WhatsApp Business消息
- 发送订单通知（物流更新）
- 支持文件传输（PDF说明书）
- 消息模板管理

**业务逻辑**：
```
1. 客户通过WhatsApp联系Fiido
2. WhatsApp Business API接收消息
3. 坐席工作台统一查看和回复
4. 支持主动发送：订单确认、发货通知（需使用预审批模板）
```

**约束**：
- WhatsApp Business API需要Meta审批
- 主动消息必须使用模板
- 24小时响应窗口

---

## 📋 模块2: 统一收件箱管理

### 2.1 全渠道消息聚合

**统一数据模型**：
```typescript
interface UnifiedMessage {
  message_id: string
  channel: 'website' | 'instagram' | 'facebook' | 'whatsapp' | 'email'
  customer_id: string              // 跨渠道统一客户ID
  session_name: string             // 会话ID
  sender_type: 'customer' | 'agent' | 'system'
  content: {
    text?: string
    media?: MediaAttachment[]      // 图片、视频、文件
    rich_content?: RichMessage     // 富媒体（卡片、按钮）
  }
  timestamp: Date
  status: 'sent' | 'delivered' | 'read' | 'failed'
}
```

### 2.2 坐席端统一收件箱

**UI设计**：
```
┌─────────────────────────────────────┐
│ 全渠道收件箱        [筛选: 全部▼]   │
├─────────────────────────────────────┤
│                                      │
│ 📱 Instagram | @john_doe_nyc        │
│    "How much is the D11?"            │
│    5分钟前                           │
│                                      │
│ 💬 网站聊天 | Sarah M                │
│    "Shipping to Canada?"             │
│    12分钟前                          │
│                                      │
│ 🟢 WhatsApp | +1-234-567-8900       │
│    [图片] Battery issue              │
│    1小时前                           │
│                                      │
│ 📘 Facebook | Lisa Chen              │
│    "D11 vs X model?"                 │
│    昨天                              │
│                                      │
└─────────────────────────────────────┘
```

### 2.3 渠道切换与回复

**智能回复路由**：
```
业务逻辑：
1. 坐席选择会话
2. 系统自动识别来源渠道
3. 回复时自动通过相应渠道发送
4. 支持手动切换渠道（如：邀请Instagram客户到网站聊天）
```

---

## 📋 模块3: 跨渠道客户识别

### 3.1 客户身份自动关联

**关联规则**：
```
业务逻辑：
1. 客户在Instagram咨询后，又在网站聊天
2. 系统匹配规则：
   - 邮箱匹配（优先）
   - 手机号匹配
   - 姓名 + 地址匹配
   - AI相似度匹配（> 80%）
3. 自动合并客户档案
4. 显示完整跨渠道互动历史
```

### 3.2 客户统一视图

**坐席端显示**：
```
┌─────────────────────────────────────┐
│ 客户: John Doe                       │
│ 首次联系: 2025-01-15 (Instagram)     │
├─────────────────────────────────────┤
│                                      │
│ 📊 跨渠道互动历史                    │
│                                      │
│ 📱 Instagram (3次)                   │
│ • 2025-01-15: 首次咨询产品           │
│ • 2025-01-20: 询问配送               │
│ • 2025-01-27: 当前会话               │
│                                      │
│ 💬 网站聊天 (2次)                    │
│ • 2025-01-18: 下单前咨询             │
│ • 2025-01-22: 物流查询               │
│                                      │
│ 🛒 Shopify订单 (1次)                 │
│ • 2025-01-19: #FD20250119001 $1,099 │
│                                      │
│ 💡 建议: 客户已购买，本次可能售后问题│
└─────────────────────────────────────┘
```

---

## 📊 开发优先级

### 第一阶段（P0）
- [ ] Instagram DM集成
- [ ] 统一收件箱基础功能
- [ ] 跨渠道客户识别（邮箱匹配）

### 第二阶段（P1）
- [ ] Facebook Messenger集成
- [ ] WhatsApp Business集成
- [ ] 富媒体消息支持

### 第三阶段（P2）
- [ ] SMS集成
- [ ] TikTok DM集成
- [ ] AI自动身份匹配

---

**文档维护者**: Claude Code
**最后更新**: 2025-01-27
