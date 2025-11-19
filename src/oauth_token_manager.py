"""
OAuth Token 管理器
负责使用 JWT 获取和管理 Coze Access Token
"""

import time
import requests
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import os

from src.jwt_signer import JWTSigner


class OAuthTokenManager:
    """OAuth 令牌管理器 - 使用 JWT 获取和刷新 Access Token"""

    def __init__(
        self,
        jwt_signer: JWTSigner,
        api_base: str = "https://api.coze.com",
        token_ttl: int = 86399  # 令牌有效期，默认 24 小时 - 1 秒
    ):
        """
        初始化令牌管理器

        Args:
            jwt_signer: JWT 签名器实例
            api_base: Coze API 基础 URL
            token_ttl: Access Token 请求的有效期（秒），最大 86400
        """
        self.jwt_signer = jwt_signer
        self.api_base = api_base.rstrip('/')
        self.token_ttl = min(token_ttl, 86400)  # 最大 24 小时

        # Token 缓存（按 session_name 分别缓存）
        self._token_cache: Dict[str, Dict[str, Any]] = {}  # {session_name: {token, expires_at}}

    @classmethod
    def from_env(cls) -> "OAuthTokenManager":
        """从环境变量创建令牌管理器"""
        jwt_signer = JWTSigner.from_env()
        api_base = os.getenv("COZE_API_BASE", "https://api.coze.com")
        return cls(jwt_signer=jwt_signer, api_base=api_base)

    def _request_access_token(
        self,
        session_name: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        使用 JWT 向 Coze API 请求 Access Token

        Args:
            session_name: 用户会话名称
            device_id: 设备 ID

        Returns:
            包含 access_token 和 expires_in 的字典

        Raises:
            Exception: 请求失败时抛出异常
        """
        # 1. 生成 JWT
        jwt_token = self.jwt_signer.create_jwt(
            session_name=session_name,
            device_id=device_id
        )

        # 2. 请求 Access Token
        url = f"{self.api_base}/api/permission/oauth2/token"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {jwt_token}"
        }
        payload = {
            "duration_seconds": self.token_ttl,
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer"
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            # 验证响应
            if "access_token" not in data:
                raise Exception(f"响应中缺少 access_token: {data}")

            return data

        except requests.exceptions.RequestException as e:
            raise Exception(f"请求 Access Token 失败: {str(e)}")

    def get_access_token(
        self,
        session_name: Optional[str] = None,
        device_id: Optional[str] = None,
        force_refresh: bool = False
    ) -> str:
        """
        获取有效的 Access Token（带缓存，按 session_name 隔离）

        Args:
            session_name: 用户会话名称（用于会话隔离）
            device_id: 设备 ID
            force_refresh: 是否强制刷新令牌

        Returns:
            有效的 Access Token 字符串
        """
        # 使用 session_name 作为缓存 key，如果没有则使用 "default"
        cache_key = session_name or "default"

        # 检查缓存的令牌是否仍然有效
        if not force_refresh and self._is_token_valid(cache_key):
            print(f"♻️  使用缓存的 Token (session: {cache_key})")
            return self._token_cache[cache_key]["token"]

        # 请求新令牌
        print(f"🔄 为 session '{cache_key}' 获取新的 Access Token...")
        token_data = self._request_access_token(
            session_name=session_name,
            device_id=device_id
        )

        # 更新缓存
        access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", self.token_ttl)

        # 计算过期时间（提前 5 分钟刷新，避免边界情况）
        expires_at = datetime.now() + timedelta(seconds=expires_in - 300)

        self._token_cache[cache_key] = {
            "token": access_token,
            "expires_at": expires_at,
            "session_name": session_name
        }

        print(f"✅ Access Token 获取成功 (session: {cache_key})，有效期至: {expires_at}")

        return access_token

    def _is_token_valid(self, cache_key: str) -> bool:
        """检查指定 session 的缓存令牌是否仍然有效"""
        if cache_key not in self._token_cache:
            return False

        token_info = self._token_cache[cache_key]
        expires_at = token_info.get("expires_at")

        if expires_at is None:
            return False

        # 检查是否过期（提前 1 分钟判定为过期）
        return datetime.now() < (expires_at - timedelta(minutes=1))

    def refresh_token(
        self,
        session_name: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> str:
        """
        强制刷新 Access Token

        Args:
            session_name: 用户会话名称
            device_id: 设备 ID

        Returns:
            新的 Access Token
        """
        return self.get_access_token(
            session_name=session_name,
            device_id=device_id,
            force_refresh=True
        )

    def invalidate_token(self, session_name: Optional[str] = None):
        """
        使令牌失效（清除缓存）

        Args:
            session_name: 指定要清除的 session，如果为 None 则清除所有缓存
        """
        if session_name:
            cache_key = session_name
            if cache_key in self._token_cache:
                del self._token_cache[cache_key]
                print(f"🗑️  令牌缓存已清除 (session: {cache_key})")
        else:
            self._token_cache.clear()
            print("🗑️  所有令牌缓存已清除")

    def get_token_info(self, session_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取令牌信息（调试用）

        Args:
            session_name: 指定查询的 session，如果为 None 则返回所有 session 的信息
        """
        if session_name:
            cache_key = session_name
            if cache_key in self._token_cache:
                token_info = self._token_cache[cache_key]
                return {
                    "session_name": cache_key,
                    "has_token": True,
                    "is_valid": self._is_token_valid(cache_key),
                    "expires_at": token_info["expires_at"].isoformat(),
                    "token_preview": f"{token_info['token'][:20]}..."
                }
            else:
                return {
                    "session_name": cache_key,
                    "has_token": False
                }
        else:
            # 返回所有 session 的信息
            return {
                "total_sessions": len(self._token_cache),
                "sessions": {
                    key: {
                        "is_valid": self._is_token_valid(key),
                        "expires_at": info["expires_at"].isoformat(),
                        "token_preview": f"{info['token'][:20]}..."
                    }
                    for key, info in self._token_cache.items()
                }
            }


if __name__ == "__main__":
    """命令行测试工具"""
    from dotenv import load_dotenv
    load_dotenv()  # 加载 .env 文件

    print("🎫 OAuth Token 管理器测试")
    print("=" * 50)

    try:
        # 从环境变量创建管理器
        manager = OAuthTokenManager.from_env()

        # 获取 Access Token
        print("\n📝 正在获取 Access Token...")
        access_token = manager.get_access_token(
            session_name="test_user_001",
            device_id="test_device_001"
        )

        print(f"\n✅ Access Token: {access_token[:30]}...")
        print(f"   完整长度: {len(access_token)} 字符")

        # 显示令牌信息
        token_info = manager.get_token_info()
        print(f"\n📊 令牌信息:")
        import json
        print(json.dumps(token_info, indent=2, ensure_ascii=False))

        # 测试缓存
        print("\n🔄 测试令牌缓存...")
        cached_token = manager.get_access_token()
        print(f"缓存命中: {cached_token == access_token}")

        # 测试强制刷新
        print("\n♻️  测试强制刷新...")
        new_token = manager.refresh_token()
        print(f"新令牌获取成功: {new_token[:30]}...")

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
