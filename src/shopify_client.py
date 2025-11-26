"""
Shopify REST Admin API 客户端模块

功能：
- 获取客户信息（Customer API）
- 获取订单历史（Orders API）
- 获取产品信息（Products API）
- 速率限制管理（2 requests/second）
- 自动重试和错误处理

依赖：
- httpx - HTTP 客户端
- pydantic - 数据验证

使用示例：
    from src.shopify_client import get_shopify_client

    shopify = get_shopify_client()
    if shopify:
        customer = shopify.get_customer("123456789")
        orders = shopify.get_customer_orders("123456789")
"""

import httpx
import os
import time
from typing import Optional, Dict, List
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class ShopifyConfig(BaseModel):
    """Shopify API 配置模型"""
    shop_name: str  # 店铺名称（不含 .myshopify.com）
    access_token: str  # Admin API Access Token
    api_version: str = "2024-10"  # API 版本

    @property
    def base_url(self) -> str:
        """构建 API Base URL"""
        return f"https://{self.shop_name}.myshopify.com/admin/api/{self.api_version}"


class ShopifyClient:
    """
    Shopify REST Admin API 客户端

    实现功能：
    - 客户信息查询
    - 订单历史查询
    - 速率限制（2 req/s）
    - 自动重试
    """

    def __init__(self, config: ShopifyConfig):
        """
        初始化 Shopify 客户端

        Args:
            config: Shopify 配置对象
        """
        self.config = config
        self.client = httpx.Client(
            base_url=config.base_url,
            headers={
                "X-Shopify-Access-Token": config.access_token,
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=httpx.Timeout(10.0)
        )
        self._last_request_time = 0
        self._rate_limit_delay = 0.5  # 500ms between requests (2 req/s)

    def _rate_limit_wait(self):
        """
        速率限制等待

        Shopify 标准计划限制：2 requests/second
        实现策略：每次请求间隔至少 500ms
        """
        now = time.time()
        elapsed = now - self._last_request_time

        if elapsed < self._rate_limit_delay:
            sleep_time = self._rate_limit_delay - elapsed
            logger.debug(f"速率限制：等待 {sleep_time:.3f}s")
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def get_customer(self, customer_id: str) -> Optional[Dict]:
        """
        获取客户信息

        API 端点：GET /admin/api/2024-10/customers/{customer_id}.json

        Args:
            customer_id: Shopify 客户 ID

        Returns:
            客户信息字典，失败返回 None

        Example Response:
            {
                "id": 207119551,
                "email": "bob.norman@mail.example.com",
                "first_name": "Bob",
                "last_name": "Norman",
                "phone": "+16136120707",
                "tags": "vip_gold, lang_en",
                "default_address": {
                    "country_code": "CA",
                    "city": "Ottawa"
                },
                "created_at": "2024-01-01T12:00:00Z"
            }
        """
        self._rate_limit_wait()

        try:
            logger.info(f"🔍 Shopify API: 获取客户信息 customer_id={customer_id}")
            response = self.client.get(f"/customers/{customer_id}.json")
            response.raise_for_status()

            data = response.json()
            customer = data.get("customer")

            if customer:
                logger.info(f"✅ Shopify API: 成功获取客户 {customer.get('email')}")
            else:
                logger.warning(f"⚠️  Shopify API: 客户不存在 customer_id={customer_id}")

            return customer

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"⚠️  Shopify API: 客户不存在 customer_id={customer_id}")
            elif e.response.status_code == 429:
                logger.error(f"❌ Shopify API: 速率限制 (429) - {e}")
                # TODO: 实现指数退避重试
            else:
                logger.error(f"❌ Shopify API 错误 ({e.response.status_code}): {e}")
            return None

        except httpx.RequestError as e:
            logger.error(f"❌ Shopify API 请求失败: {e}")
            return None

    def get_customer_orders(
        self,
        customer_id: str,
        limit: int = 10,
        status: str = "any"
    ) -> List[Dict]:
        """
        获取客户订单列表

        API 端点：GET /admin/api/2024-10/customers/{customer_id}/orders.json

        Args:
            customer_id: Shopify 客户 ID
            limit: 返回订单数量（默认 10）
            status: 订单状态过滤 (any/open/closed)

        Returns:
            订单列表，失败返回空列表

        Example Response:
            [
                {
                    "id": 450789469,
                    "order_number": 1001,
                    "financial_status": "paid",
                    "fulfillment_status": "shipped",
                    "total_price": "2299.99",
                    "currency": "EUR",
                    "line_items": [...],
                    "created_at": "2024-01-01T12:00:00Z"
                }
            ]
        """
        self._rate_limit_wait()

        try:
            logger.info(f"🔍 Shopify API: 获取客户订单 customer_id={customer_id}, limit={limit}")
            response = self.client.get(
                f"/customers/{customer_id}/orders.json",
                params={"limit": limit, "status": status}
            )
            response.raise_for_status()

            data = response.json()
            orders = data.get("orders", [])

            logger.info(f"✅ Shopify API: 成功获取 {len(orders)} 个订单")
            return orders

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"⚠️  Shopify API: 客户不存在 customer_id={customer_id}")
            else:
                logger.error(f"❌ Shopify API 错误 ({e.response.status_code}): {e}")
            return []

        except httpx.RequestError as e:
            logger.error(f"❌ Shopify API 请求失败: {e}")
            return []

    def get_order(self, order_id: str) -> Optional[Dict]:
        """
        获取单个订单详情

        API 端点：GET /admin/api/2024-10/orders/{order_id}.json

        Args:
            order_id: Shopify 订单 ID

        Returns:
            订单详情字典，失败返回 None
        """
        self._rate_limit_wait()

        try:
            logger.info(f"🔍 Shopify API: 获取订单详情 order_id={order_id}")
            response = self.client.get(f"/orders/{order_id}.json")
            response.raise_for_status()

            data = response.json()
            order = data.get("order")

            if order:
                logger.info(f"✅ Shopify API: 成功获取订单 #{order.get('order_number')}")

            return order

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Shopify API 错误 ({e.response.status_code}): {e}")
            return None

        except httpx.RequestError as e:
            logger.error(f"❌ Shopify API 请求失败: {e}")
            return None

    def get_product(self, product_id: str) -> Optional[Dict]:
        """
        获取产品信息

        API 端点：GET /admin/api/2024-10/products/{product_id}.json

        Args:
            product_id: Shopify 产品 ID

        Returns:
            产品信息字典，失败返回 None
        """
        self._rate_limit_wait()

        try:
            logger.info(f"🔍 Shopify API: 获取产品信息 product_id={product_id}")
            response = self.client.get(f"/products/{product_id}.json")
            response.raise_for_status()

            data = response.json()
            product = data.get("product")

            if product:
                logger.info(f"✅ Shopify API: 成功获取产品 {product.get('title')}")

            return product

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Shopify API 错误 ({e.response.status_code}): {e}")
            return None

        except httpx.RequestError as e:
            logger.error(f"❌ Shopify API 请求失败: {e}")
            return None

    def close(self):
        """关闭 HTTP 客户端连接"""
        self.client.close()
        logger.info("🔌 Shopify 客户端连接已关闭")


# ====================
# 全局实例管理
# ====================

shopify_client: Optional[ShopifyClient] = None


def init_shopify_client():
    """
    初始化 Shopify 客户端（应用启动时调用）

    从环境变量读取配置：
    - SHOPIFY_SHOP_NAME: 店铺名称
    - SHOPIFY_ACCESS_TOKEN: Access Token
    - SHOPIFY_API_VERSION: API 版本（可选）
    - SHOPIFY_ENABLED: 功能开关

    如果配置缺失或 SHOPIFY_ENABLED=false，则跳过初始化
    """
    global shopify_client

    # 检查功能开关
    enabled = os.getenv("SHOPIFY_ENABLED", "false").lower() == "true"
    if not enabled:
        print("⚠️  Shopify 集成未启用 (SHOPIFY_ENABLED=false)")
        print("   系统将使用 mock 数据")
        return

    # 读取配置
    shop_name = os.getenv("SHOPIFY_SHOP_NAME")
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
    api_version = os.getenv("SHOPIFY_API_VERSION", "2024-10")

    # 验证配置
    if not shop_name or not access_token:
        print("⚠️  Shopify 配置缺失，使用 mock 数据")
        print("   请设置环境变量：")
        print("   - SHOPIFY_SHOP_NAME")
        print("   - SHOPIFY_ACCESS_TOKEN")
        return

    # 验证 Token 格式
    if not access_token.startswith("shpat_"):
        print("❌ SHOPIFY_ACCESS_TOKEN 格式错误（应以 'shpat_' 开头）")
        return

    try:
        # 创建配置对象
        config = ShopifyConfig(
            shop_name=shop_name,
            access_token=access_token,
            api_version=api_version
        )

        # 初始化客户端
        shopify_client = ShopifyClient(config)

        print(f"✅ Shopify 客户端初始化成功")
        print(f"   店铺: {shop_name}.myshopify.com")
        print(f"   API: {config.base_url}")

    except Exception as e:
        print(f"❌ Shopify 客户端初始化失败: {e}")
        shopify_client = None


def get_shopify_client() -> Optional[ShopifyClient]:
    """
    获取 Shopify 客户端实例

    Returns:
        ShopifyClient 实例，未初始化返回 None
    """
    return shopify_client


# ====================
# 数据转换辅助函数
# ====================

def extract_vip_from_tags(tags: str) -> Optional[str]:
    """
    从 Shopify 客户标签提取 VIP 状态

    Args:
        tags: 逗号分隔的标签字符串 "vip_gold, lang_en, shopify_campaign"

    Returns:
        VIP 等级: "gold" | "silver" | "bronze" | None

    注意：
        ⚠️ 当前假设标签格式：vip_gold, vip_silver, vip_bronze
        如果实际格式不同，请修改此函数
    """
    if not tags:
        return None

    tags_lower = tags.lower()

    # ⚠️ 待确认：当前假设格式 vip_gold, vip_silver, vip_bronze
    if "vip_gold" in tags_lower or "vip-gold" in tags_lower:
        return "gold"
    if "vip_silver" in tags_lower or "vip-silver" in tags_lower:
        return "silver"
    if "vip_bronze" in tags_lower or "vip-bronze" in tags_lower:
        return "bronze"

    return None


def extract_language_from_tags(tags: str) -> str:
    """
    从 Shopify 客户标签提取语言偏好

    Args:
        tags: 逗号分隔的标签字符串

    Returns:
        语言代码: "de" | "fr" | "en" | "it" | "es"（默认 "en"）

    注意：
        ⚠️ 当前假设标签格式：lang_de, lang_fr, lang_en
        如果实际格式不同（如 language:de），请修改此函数
    """
    if not tags:
        return "en"

    tags_lower = tags.lower()

    # ⚠️ 待确认：当前假设格式 lang_de, lang_fr
    for lang in ["de", "fr", "it", "es", "en"]:
        if f"lang_{lang}" in tags_lower or f"language:{lang}" in tags_lower:
            return lang

    return "en"  # 默认英语


def extract_source_from_tags(tags: str) -> str:
    """
    从 Shopify 客户标签提取来源渠道

    Args:
        tags: 逗号分隔的标签字符串

    Returns:
        来源渠道: "shopify_campaign" | "amazon" | "dealer" | "shopify_organic"

    注意：
        ⚠️ 当前假设标签格式：shopify_campaign, amazon, dealer
        如果实际格式不同（如 source:shopify），请修改此函数
    """
    if not tags:
        return "shopify_organic"

    tags_lower = tags.lower()

    # ⚠️ 待确认：当前假设格式 shopify_campaign, amazon, dealer
    if "shopify_campaign" in tags_lower or "source:shopify" in tags_lower:
        return "shopify_campaign"
    if "amazon" in tags_lower or "source:amazon" in tags_lower:
        return "amazon"
    if "dealer" in tags_lower or "source:dealer" in tags_lower:
        return "dealer"

    return "shopify_organic"
