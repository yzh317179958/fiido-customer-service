# Shopify API 集成实施方案

> 文档版本: v1.0
> 创建时间: 2025-11-26
> 优先级: P1
> 预计工时: 8-12小时

---

## 📋 背景与目标

### 当前问题

v3.2.0 实现了客户画像、订单、设备信息的UI展示，但数据来源为 **mock数据**：

```python
# backend.py - 当前实现
@app.get("/api/customers/{customer_id}/orders")
async def get_customer_orders(customer_id: str, agent: dict = Depends(require_agent)):
    # MVP 阶段：返回模拟数据
    mock_orders = [
        {
            "order_id": "order_001",
            "order_number": "#1001",
            # ... 硬编码数据
        }
    ]
    return {"success": True, "data": {"orders": mock_orders}}
```

**限制**：
- ❌ 无法显示真实客户订单
- ❌ 坐席看到的是假数据，无法提供真实客服
- ❌ 物流追踪信息不准确

### 集成目标

将 mock 数据替换为 **Shopify REST Admin API** 真实数据：

1. **客户画像** (`/api/customers/{id}/profile`)
   - 从 Shopify Customer API 获取姓名、邮箱、电话、地址
   - 从 Customer Tags 解析 VIP 状态、来源渠道

2. **订单历史** (`/api/customers/{id}/orders`)
   - 从 Shopify Orders API 获取订单列表
   - 解析订单商品、金额、物流信息

3. **物流追踪** (订单内嵌)
   - 从 Shopify Fulfillments API 获取物流单号
   - 可选：集成第三方物流追踪API（DHL、UPS）

---

## 🔌 Shopify API 基础知识

### API 类型选择

Shopify 提供两种 API：
- **REST Admin API** - 简单易用，适合CRUD操作 ✅ **推荐**
- **GraphQL Admin API** - 灵活强大，但学习曲线陡峭

**决策**：使用 **REST Admin API**，原因：
- Fiido需求简单（查询客户、订单）
- 开发速度快
- 官方文档完善

### 认证方式

Shopify 支持两种认证：
1. **Private App (已废弃)** - 简单但不安全
2. **Custom App + Access Token** - 官方推荐 ✅

**实施步骤**：
1. 登录 Shopify Admin: `https://fiido-store.myshopify.com/admin`
2. 设置 > 应用和销售渠道 > 开发应用
3. 创建自定义应用 "Fiido客服系统"
4. 配置 API 权限范围：
   - `read_customers` - 读取客户信息
   - `read_orders` - 读取订单
   - `read_products` - 读取产品信息
5. 安装应用，获取 **Admin API Access Token**

### API 端点

**Shopify REST API Base URL**:
```
https://{shop}.myshopify.com/admin/api/2024-10/
```

**常用端点**：
```http
# 1. 获取客户信息
GET /customers/{customer_id}.json

# 2. 获取客户订单列表
GET /customers/{customer_id}/orders.json

# 3. 获取单个订单详情
GET /orders/{order_id}.json

# 4. 获取产品信息
GET /products/{product_id}.json
```

### 速率限制

Shopify API 限制：
- **标准计划**: 2 requests/second
- **Plus 计划**: 4 requests/second

**应对策略**：
- 本地缓存客户数据（Redis TTL 5分钟）
- 批量请求合并
- 错误重试机制

---

## 🛠️ 技术实现方案

### 1. 创建 Shopify 客户端模块

**文件**: `src/shopify_client.py`

```python
import httpx
import os
from typing import Optional, Dict, List
from pydantic import BaseModel
import time

class ShopifyConfig(BaseModel):
    """Shopify API 配置"""
    shop_name: str  # fiido-store
    access_token: str
    api_version: str = "2024-10"

    @property
    def base_url(self) -> str:
        return f"https://{self.shop_name}.myshopify.com/admin/api/{self.api_version}"

class ShopifyClient:
    """Shopify REST Admin API 客户端"""

    def __init__(self, config: ShopifyConfig):
        self.config = config
        self.client = httpx.Client(
            base_url=config.base_url,
            headers={
                "X-Shopify-Access-Token": config.access_token,
                "Content-Type": "application/json"
            },
            timeout=httpx.Timeout(10.0)
        )
        self._last_request_time = 0
        self._rate_limit_delay = 0.5  # 500ms between requests

    def _rate_limit_wait(self):
        """速率限制等待"""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self._rate_limit_delay:
            time.sleep(self._rate_limit_delay - elapsed)
        self._last_request_time = time.time()

    def get_customer(self, customer_id: str) -> Optional[Dict]:
        """获取客户信息"""
        self._rate_limit_wait()
        try:
            response = self.client.get(f"/customers/{customer_id}.json")
            response.raise_for_status()
            return response.json().get("customer")
        except httpx.HTTPError as e:
            print(f"❌ Shopify API错误: {e}")
            return None

    def get_customer_orders(self, customer_id: str, limit: int = 10) -> List[Dict]:
        """获取客户订单列表"""
        self._rate_limit_wait()
        try:
            response = self.client.get(
                f"/customers/{customer_id}/orders.json",
                params={"limit": limit, "status": "any"}
            )
            response.raise_for_status()
            return response.json().get("orders", [])
        except httpx.HTTPError as e:
            print(f"❌ Shopify API错误: {e}")
            return []

    def get_order(self, order_id: str) -> Optional[Dict]:
        """获取订单详情"""
        self._rate_limit_wait()
        try:
            response = self.client.get(f"/orders/{order_id}.json")
            response.raise_for_status()
            return response.json().get("order")
        except httpx.HTTPError as e:
            print(f"❌ Shopify API错误: {e}")
            return None

# 全局实例
shopify_client: Optional[ShopifyClient] = None

def init_shopify_client():
    """初始化 Shopify 客户端"""
    global shopify_client

    shop_name = os.getenv("SHOPIFY_SHOP_NAME")  # fiido-store
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")

    if not shop_name or not access_token:
        print("⚠️  Shopify 配置缺失，使用 mock 数据")
        return

    config = ShopifyConfig(
        shop_name=shop_name,
        access_token=access_token
    )

    shopify_client = ShopifyClient(config)
    print(f"✅ Shopify 客户端初始化成功: {shop_name}")

def get_shopify_client() -> Optional[ShopifyClient]:
    """获取 Shopify 客户端实例"""
    return shopify_client
```

### 2. 修改后端 API（数据转换层）

**文件**: `backend.py`

```python
from src.shopify_client import get_shopify_client, init_shopify_client

# 启动时初始化
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... 现有初始化代码 ...

    # 初始化 Shopify 客户端
    init_shopify_client()

    yield

# 修改客户画像接口
@app.get("/api/customers/{customer_id}/profile")
async def get_customer_profile(customer_id: str, agent: dict = Depends(require_agent)):
    """获取客户画像"""
    try:
        shopify = get_shopify_client()

        # 如果 Shopify 未配置，返回 mock 数据
        if not shopify:
            return get_mock_customer_profile(customer_id)

        # 从 Shopify 获取真实数据
        customer = shopify.get_customer(customer_id)

        if not customer:
            raise HTTPException(404, "客户不存在")

        # 转换为系统数据格式
        profile = {
            "customer_id": str(customer["id"]),
            "name": f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip(),
            "email": customer.get("email"),
            "phone": customer.get("phone"),
            "country": customer.get("default_address", {}).get("country_code", ""),
            "city": customer.get("default_address", {}).get("city", ""),
            "language_preference": extract_language_from_tags(customer.get("tags", "")),
            "payment_currency": customer.get("currency", "EUR"),
            "source_channel": extract_source_from_tags(customer.get("tags", "")),
            "gdpr_consent": customer.get("accepts_marketing", False),
            "marketing_subscribed": customer.get("email_marketing_consent", {}).get("state") == "subscribed",
            "vip_status": extract_vip_from_tags(customer.get("tags", "")),
            "created_at": int(datetime.fromisoformat(customer["created_at"].replace("Z", "+00:00")).timestamp())
        }

        return {"success": True, "data": profile}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取客户画像失败: {e}")
        raise HTTPException(500, str(e))

# 辅助函数：从 Shopify Tags 提取信息
def extract_vip_from_tags(tags: str) -> Optional[str]:
    """从标签提取 VIP 状态 (gold/silver/bronze)"""
    tags_lower = tags.lower()
    if "vip_gold" in tags_lower:
        return "gold"
    if "vip_silver" in tags_lower:
        return "silver"
    if "vip_bronze" in tags_lower:
        return "bronze"
    return None

def extract_source_from_tags(tags: str) -> str:
    """从标签提取来源渠道"""
    tags_lower = tags.lower()
    if "shopify_campaign" in tags_lower:
        return "shopify_campaign"
    if "amazon" in tags_lower:
        return "amazon"
    if "dealer" in tags_lower:
        return "dealer"
    return "shopify_organic"

def extract_language_from_tags(tags: str) -> str:
    """从标签提取语言偏好"""
    tags_lower = tags.lower()
    for lang in ["de", "fr", "it", "es", "en"]:
        if f"lang_{lang}" in tags_lower:
            return lang
    return "en"  # 默认英语
```

### 3. 环境变量配置

**文件**: `.env`

```bash
# ====================
# Shopify API 配置 (v3.3.0+)
# ====================

# Shopify 店铺名称（不含 .myshopify.com）
SHOPIFY_SHOP_NAME=fiido-store

# Shopify Admin API Access Token
# 获取方式: Shopify Admin > 设置 > 应用和销售渠道 > 开发应用
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxxxxxx

# Shopify API 版本（默认使用最新稳定版）
SHOPIFY_API_VERSION=2024-10

# 功能开关：是否启用 Shopify 集成
# true: 使用真实 Shopify 数据
# false: 使用 mock 数据（开发/测试阶段）
SHOPIFY_ENABLED=true

# Shopify 数据缓存时间（秒）
# 建议: 300秒（5分钟），减少API调用
SHOPIFY_CACHE_TTL=300
```

---

## 📝 实施步骤

### 阶段 1: 基础集成（4小时）

**任务清单**：
1. [ ] 创建 `src/shopify_client.py`
2. [ ] 添加环境变量到 `.env`
3. [ ] 修改 `backend.py` - 集成 Shopify 客户端
4. [ ] 实现客户画像数据转换
5. [ ] 添加降级策略（Shopify 失败时返回 mock）

**验证**：
```bash
# 1. 配置环境变量
export SHOPIFY_SHOP_NAME=fiido-store
export SHOPIFY_ACCESS_TOKEN=shpat_xxx

# 2. 重启后端
python3 backend.py

# 3. 测试API
curl http://localhost:8000/api/customers/123456/profile \
  -H "Authorization: Bearer ${AGENT_TOKEN}"

# 期望: 返回 Shopify 真实客户数据
```

### 阶段 2: 订单集成（3小时）

**任务清单**：
1. [ ] 修改 `get_customer_orders` API
2. [ ] 实现 Shopify Orders 到系统 Order 的数据转换
3. [ ] 解析物流信息（fulfillments）
4. [ ] 处理多币种（EUR/GBP）

**数据映射**：
```python
# Shopify Order → 系统 Order
shopify_order = {
    "id": 123456,
    "order_number": "1001",
    "financial_status": "paid",  # → status: "paid"
    "fulfillment_status": "shipped",  # → status: "shipped"
    "total_price": "2299.99",
    "currency": "EUR",
    "line_items": [...]  # → items
}
```

### 阶段 3: 缓存优化（2小时）

**任务清单**：
1. [ ] 使用 Redis 缓存 Shopify 响应
2. [ ] 设置 TTL 5分钟
3. [ ] 实现缓存失效策略
4. [ ] 监控缓存命中率

**实现**：
```python
import hashlib
import json

async def get_customer_with_cache(customer_id: str):
    """带缓存的客户查询"""
    cache_key = f"shopify:customer:{customer_id}"

    # 尝试从缓存读取
    cached = await session_store.redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # 缓存未命中，调用 Shopify API
    shopify = get_shopify_client()
    customer = shopify.get_customer(customer_id)

    # 写入缓存（5分钟TTL）
    if customer:
        await session_store.redis_client.setex(
            cache_key,
            300,  # 5 minutes
            json.dumps(customer)
        )

    return customer
```

### 阶段 4: 错误处理（1小时）

**任务清单**：
1. [ ] 处理 Shopify API 速率限制（429错误）
2. [ ] 处理网络超时
3. [ ] 记录错误日志
4. [ ] 实现降级策略

**错误处理示例**：
```python
try:
    customer = shopify.get_customer(customer_id)
except httpx.HTTPStatusError as e:
    if e.response.status_code == 429:
        # 速率限制，等待后重试
        retry_after = int(e.response.headers.get("Retry-After", 2))
        time.sleep(retry_after)
        customer = shopify.get_customer(customer_id)
    else:
        raise
except httpx.TimeoutException:
    # 超时，返回缓存数据或 mock
    return get_mock_customer_profile(customer_id)
```

---

## ✅ 验收标准

### 功能验收

- [ ] 客户画像显示真实 Shopify 数据
- [ ] 邮箱和电话正确脱敏
- [ ] VIP 状态从 Tags 正确解析
- [ ] 订单历史显示真实订单（最近10个）
- [ ] 订单商品、金额、状态正确显示
- [ ] 物流追踪信息正确显示
- [ ] 多币种正确处理（EUR/GBP）

### 性能验收

- [ ] 首次请求响应时间 < 2s
- [ ] 缓存命中后响应时间 < 100ms
- [ ] 速率限制正确工作（每秒不超过2次请求）
- [ ] 并发10个坐席时系统稳定

### 安全验收

- [ ] Shopify Access Token 不暴露在日志中
- [ ] API 响应不包含敏感字段（如支付信息）
- [ ] 坐席权限正确控制（需要 JWT Token）

---

## ⚠️ 风险与应对

### 风险1: Shopify API 不可用

**影响**: 坐席无法查看客户信息

**应对**:
- ✅ 实现降级策略：API 失败时返回缓存或 mock 数据
- ✅ 监控 Shopify API 可用性
- ✅ 设置超时阈值（10秒）

### 风险2: 速率限制导致请求失败

**影响**: 高峰期部分请求被限流

**应对**:
- ✅ 本地缓存（5分钟TTL）
- ✅ 请求队列排队
- ✅ 重试机制（指数退避）

### 风险3: 数据格式不兼容

**影响**: Shopify 数据结构变化导致解析失败

**应对**:
- ✅ 使用 Pydantic 模型验证
- ✅ 容错处理（字段缺失时使用默认值）
- ✅ 版本化 API（固定使用 2024-10 版本）

---

## 📚 参考文档

- [Shopify REST Admin API](https://shopify.dev/docs/api/admin-rest)
- [Shopify Customers API](https://shopify.dev/docs/api/admin-rest/2024-10/resources/customer)
- [Shopify Orders API](https://shopify.dev/docs/api/admin-rest/2024-10/resources/order)
- [速率限制说明](https://shopify.dev/docs/api/usage/rate-limits)

---

**文档维护者**: Claude Code
**最后更新**: 2025-11-26
**预计完成时间**: 2025-11-27
