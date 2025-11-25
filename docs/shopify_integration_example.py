"""
Shopify API 集成示例
未来将替换 backend.py 中的模拟数据
"""

import os
import httpx
from typing import Optional, Dict, Any

class ShopifyClient:
    """Shopify API 客户端"""

    def __init__(self):
        self.shop_url = os.getenv("SHOPIFY_SHOP_URL")  # 例如: fiido.myshopify.com
        self.access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
        self.api_version = "2024-01"

    async def get_customer_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        通过邮箱查询客户信息

        Args:
            email: 客户邮箱

        Returns:
            客户信息字典
        """
        url = f"https://{self.shop_url}/admin/api/{self.api_version}/customers/search.json"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params={"query": f"email:{email}"},
                headers={
                    "X-Shopify-Access-Token": self.access_token,
                    "Content-Type": "application/json"
                },
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                customers = data.get("customers", [])
                return customers[0] if customers else None
            else:
                return None

    async def get_customer_orders(self, customer_id: str, limit: int = 3) -> list:
        """
        获取客户的最近订单

        Args:
            customer_id: Shopify 客户 ID
            limit: 返回订单数量

        Returns:
            订单列表
        """
        url = f"https://{self.shop_url}/admin/api/{self.api_version}/customers/{customer_id}/orders.json"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params={"limit": limit, "status": "any"},
                headers={
                    "X-Shopify-Access-Token": self.access_token
                },
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("orders", [])
            else:
                return []

    def transform_to_customer_profile(self, shopify_customer: Dict) -> Dict:
        """
        将 Shopify 客户数据转换为系统格式

        Args:
            shopify_customer: Shopify API 返回的原始数据

        Returns:
            标准化的客户画像数据
        """
        default_address = shopify_customer.get("default_address", {})

        # 从标签中提取来源渠道
        tags = shopify_customer.get("tags", "").split(",")
        source_channel = "shopify_organic"  # 默认
        for tag in tags:
            tag = tag.strip().lower()
            if "amazon" in tag:
                source_channel = "amazon"
            elif "campaign" in tag:
                source_channel = "shopify_campaign"
            elif "dealer" in tag:
                source_channel = "dealer"

        # 从标签中提取 VIP 状态
        vip_status = None
        for tag in tags:
            tag = tag.strip().lower()
            if "vip" in tag or "gold" in tag:
                vip_status = "gold"
            elif "silver" in tag:
                vip_status = "silver"

        return {
            "customer_id": str(shopify_customer["id"]),
            "name": f"{shopify_customer.get('first_name', '')} {shopify_customer.get('last_name', '')}".strip(),
            "email": shopify_customer.get("email", ""),
            "phone": shopify_customer.get("phone", "") or default_address.get("phone", ""),
            "country": default_address.get("country_code", ""),
            "city": default_address.get("city", ""),
            "language_preference": self._infer_language(default_address.get("country_code", "")),
            "payment_currency": shopify_customer.get("currency", "EUR"),
            "source_channel": source_channel,
            "gdpr_consent": shopify_customer.get("accepts_marketing", False),
            "marketing_subscribed": shopify_customer.get("marketing_opt_in_level") == "confirmed_opt_in",
            "vip_status": vip_status,
            "avatar_url": None,
            "created_at": int(self._parse_timestamp(shopify_customer.get("created_at", "")))
        }

    def _infer_language(self, country_code: str) -> str:
        """根据国家推断语言"""
        language_map = {
            "DE": "de",  # 德国 → 德语
            "FR": "fr",  # 法国 → 法语
            "IT": "it",  # 意大利 → 意大利语
            "ES": "es",  # 西班牙 → 西班牙语
            "GB": "en",  # 英国 → 英语
            "US": "en",  # 美国 → 英语
        }
        return language_map.get(country_code, "en")

    def _parse_timestamp(self, datetime_str: str) -> float:
        """解析 Shopify 时间戳"""
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
            return dt.timestamp()
        except:
            return 0


# ====================================
# 在 backend.py 中的使用示例
# ====================================

# 初始化 Shopify 客户端（在应用启动时）
shopify_client = ShopifyClient()

@app.get("/api/customers/{customer_id}/profile")
async def get_customer_profile(
    customer_id: str,
    agent: dict = Depends(require_agent)
):
    """
    获取客户画像信息（集成 Shopify 后的版本）

    Args:
        customer_id: 会话ID（包含用户邮箱信息）
        agent: 坐席信息
    """
    try:
        # 1. 从会话中获取用户邮箱
        session = await session_store.get(customer_id)
        if not session:
            raise HTTPException(404, "会话不存在")

        user_email = session.user_profile.get("email")
        if not user_email:
            # 没有邮箱信息，返回基础数据
            return {
                "success": True,
                "data": {
                    "customer_id": customer_id,
                    "name": session.user_profile.get("nickname", "访客"),
                    "email": None,
                    "phone": None,
                    # ... 其他默认值
                }
            }

        # 2. 从 Shopify 查询客户信息
        shopify_customer = await shopify_client.get_customer_by_email(user_email)

        if not shopify_customer:
            # Shopify 中没有此客户（可能是新访客）
            return {
                "success": True,
                "data": {
                    "customer_id": customer_id,
                    "name": session.user_profile.get("nickname", "新访客"),
                    "email": user_email,
                    # ... 其他默认值
                }
            }

        # 3. 转换为标准格式
        customer_profile = shopify_client.transform_to_customer_profile(shopify_customer)

        print(f"✅ 获取客户画像: {customer_profile['name']} ({user_email})")

        return {
            "success": True,
            "data": customer_profile
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取客户画像失败: {str(e)}")
        raise HTTPException(500, f"获取客户画像失败: {str(e)}")


# ====================================
# .env 配置示例
# ====================================
"""
# Shopify API 配置
SHOPIFY_SHOP_URL=fiido.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxx
SHOPIFY_API_VERSION=2024-01
"""
