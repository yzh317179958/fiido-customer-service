# Shopify 集成配置待办事项

> **状态**: ⚠️ 待完成
> **优先级**: P1
> **创建时间**: 2025-11-26

---

## 📋 必须获取的信息

### 1. Shopify 店铺配置 ⭐ **必需**

#### 1.1 店铺名称
- **当前占位符**: `fiido-store`
- **获取位置**: Shopify Admin 后台 URL
- **示例**: 如果您的 Shopify 后台地址是 `https://my-shop.myshopify.com/admin`，则店铺名称为 `my-shop`

#### 1.2 Admin API Access Token ⭐ **敏感信息**
- **当前占位符**: `shpat_example_token_replace_me_with_real_token`
- **获取步骤**:
  1. 登录 Shopify Admin: `https://你的店铺.myshopify.com/admin`
  2. 设置 > 应用和销售渠道 > 开发应用
  3. 点击"创建应用"，命名为 "Fiido客服系统"
  4. 配置 Admin API 访问范围:
     - ✅ `read_customers` - 读取客户信息
     - ✅ `read_orders` - 读取订单
     - ✅ `read_products` - 读取产品信息
  5. 点击"安装应用"
  6. 复制 **Admin API Access Token**（以 `shpat_` 开头的长字符串）

---

### 2. 业务规则配置 ⭐ **必需**

#### 2.1 VIP 标签格式
- **当前占位符**: `vip_gold`, `vip_silver`, `vip_bronze`
- **说明**: 检查您 Shopify 后台客户标签中实际使用的 VIP 等级标签格式
- **可能的格式**:
  - `vip_gold`, `vip_silver`, `vip_bronze`（小写+下划线）
  - `VIP-GOLD`, `VIP-SILVER`, `VIP-BRONZE`（大写+连字符）
  - `VIP Gold`, `VIP Silver`, `VIP Bronze`（空格分隔）
  - 其他自定义格式

#### 2.2 语言标签格式
- **当前占位符**: `lang_de`, `lang_fr`, `lang_en`, `lang_it`, `lang_es`
- **说明**: 检查您 Shopify 后台客户标签中实际使用的语言偏好标签格式
- **可能的格式**:
  - `lang_de`, `lang_fr`（小写+下划线）
  - `language:de`, `language:fr`（冒号分隔）
  - `Language-DE`, `Language-FR`（大写+连字符）

#### 2.3 来源渠道标签格式
- **当前占位符**: `shopify_campaign`, `amazon`, `dealer`
- **说明**: 检查您 Shopify 后台客户标签中实际使用的客户来源标签格式
- **可能的格式**:
  - `shopify_campaign`, `amazon`, `dealer`
  - `source:shopify`, `source:amazon`
  - `Source-Shopify`, `Source-Amazon`

---

## 🔧 修改步骤

### 步骤 1: 更新 .env 文件

打开 `/home/yzh/AI客服/鉴权/.env`，找到以下行并修改：

```bash
# ====================
# Shopify API 配置 (v3.3.0+)
# ====================

# ⚠️ 待更新：替换为真实的店铺名称
SHOPIFY_SHOP_NAME=fiido-store

# ⚠️ 待更新：替换为真实的 Access Token（敏感信息）
SHOPIFY_ACCESS_TOKEN=shpat_example_token_replace_me_with_real_token

# ⚠️ 待更新：确认实际使用的标签格式
# VIP 标签格式当前假设：vip_gold, vip_silver, vip_bronze
# 语言标签格式当前假设：lang_de, lang_fr, lang_en
# 来源标签格式当前假设：shopify_campaign, amazon, dealer

# API 版本（默认最新稳定版）
SHOPIFY_API_VERSION=2024-10

# 功能开关：true=使用真实Shopify数据，false=使用mock数据
SHOPIFY_ENABLED=false  # ⚠️ 获取真实 Token 后改为 true

# 缓存时间（秒）
SHOPIFY_CACHE_TTL=300
```

### 步骤 2: 检查标签格式

1. 登录 Shopify Admin
2. 进入 **客户 (Customers)** 页面
3. 随机打开几个客户详情页
4. 查看 **标签 (Tags)** 字段，记录实际使用的标签格式
5. 根据实际情况修改 `src/shopify_client.py` 中的标签解析函数：
   - `extract_vip_from_tags()`
   - `extract_language_from_tags()`
   - `extract_source_from_tags()`

### 步骤 3: 启用 Shopify 集成

修改 `.env` 中的 `SHOPIFY_ENABLED=true`，然后重启后端：

```bash
cd /home/yzh/AI客服/鉴权
python3 backend.py
```

### 步骤 4: 测试验证

```bash
# 1. 健康检查
curl http://localhost:8000/api/health

# 2. 测试客户画像（需要真实的 customer_id）
curl -H "Authorization: Bearer ${AGENT_TOKEN}" \
  http://localhost:8000/api/customers/123456789/profile

# 3. 测试订单历史
curl -H "Authorization: Bearer ${AGENT_TOKEN}" \
  http://localhost:8000/api/customers/123456789/orders
```

---

## 📝 验证清单

- [ ] 已获取 Shopify 店铺名称
- [ ] 已创建 Shopify Custom App
- [ ] 已配置 API 权限（read_customers, read_orders, read_products）
- [ ] 已复制 Admin API Access Token
- [ ] 已确认 VIP 标签格式
- [ ] 已确认语言标签格式
- [ ] 已确认来源标签格式
- [ ] 已更新 `.env` 文件
- [ ] 已修改标签解析函数（如果格式不同）
- [ ] 已启用 `SHOPIFY_ENABLED=true`
- [ ] 已重启后端服务
- [ ] 已测试 API 返回真实数据

---

## ⚠️ 注意事项

1. **敏感信息安全**:
   - Access Token 是敏感信息，不要提交到 Git
   - `.env` 文件已在 `.gitignore` 中

2. **速率限制**:
   - Shopify 标准计划：2 请求/秒
   - 代码已实现速率限制，每次请求间隔 500ms

3. **降级策略**:
   - 如果 Shopify API 失败，系统会自动返回 mock 数据
   - 不影响坐席工作台的正常使用

4. **测试环境**:
   - 建议先在测试环境验证 API 可用性
   - 确认无误后再启用生产环境

---

**文档维护者**: Claude Code
**最后更新**: 2025-11-26
**关联文档**: `docs/Shopify集成实施方案.md`
