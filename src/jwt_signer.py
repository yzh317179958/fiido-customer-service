"""
JWT 签名工具模块
用于生成和管理 Coze OAuth JWT 令牌
"""

import time
import uuid
from typing import Optional, Dict, Any
import jwt
import os


class JWTSigner:
    """JWT 签名器 - 用于生成 Coze OAuth JWT 令牌"""

    def __init__(
        self,
        client_id: str,
        private_key: str,
        public_key_id: str,
        audience: str = "api.coze.com",
        ttl: int = 3600
    ):
        """
        初始化 JWT 签名器

        Args:
            client_id: OAuth 应用的 Client ID
            private_key: RSA 私钥（PEM 格式字符串）
            public_key_id: 公钥指纹（kid）
            audience: JWT 受众，默认为 api.coze.com（国内版用 api.coze.cn）
            ttl: JWT 有效期（秒），默认 3600 秒（1小时）
        """
        self.client_id = client_id
        self.private_key = private_key
        self.public_key_id = public_key_id
        self.audience = audience
        self.ttl = ttl

    @classmethod
    def from_env(cls) -> "JWTSigner":
        """
        从环境变量创建 JWT 签名器

        需要的环境变量：
        - COZE_OAUTH_CLIENT_ID: OAuth 应用 Client ID
        - COZE_OAUTH_PRIVATE_KEY 或 COZE_OAUTH_PRIVATE_KEY_FILE: 私钥
        - COZE_OAUTH_PUBLIC_KEY_ID: 公钥指纹
        - COZE_API_BASE: API 基础 URL（可选）
        """
        client_id = os.getenv("COZE_OAUTH_CLIENT_ID")
        if not client_id:
            raise ValueError("环境变量 COZE_OAUTH_CLIENT_ID 未设置")

        # 尝试从文件或环境变量获取私钥
        private_key_file = os.getenv("COZE_OAUTH_PRIVATE_KEY_FILE")
        if private_key_file:
            with open(private_key_file, 'r') as f:
                private_key = f.read()
        else:
            private_key = os.getenv("COZE_OAUTH_PRIVATE_KEY")
            if not private_key:
                raise ValueError(
                    "环境变量 COZE_OAUTH_PRIVATE_KEY 或 "
                    "COZE_OAUTH_PRIVATE_KEY_FILE 未设置"
                )

        public_key_id = os.getenv("COZE_OAUTH_PUBLIC_KEY_ID")
        if not public_key_id:
            raise ValueError("环境变量 COZE_OAUTH_PUBLIC_KEY_ID 未设置")

        # 从 API Base URL 推断 audience
        api_base = os.getenv("COZE_API_BASE", "https://api.coze.com")
        audience = "api.coze.cn" if "coze.cn" in api_base else "api.coze.com"

        return cls(
            client_id=client_id,
            private_key=private_key,
            public_key_id=public_key_id,
            audience=audience
        )

    def create_jwt(
        self,
        session_name: Optional[str] = None,
        device_id: Optional[str] = None,
        custom_ttl: Optional[int] = None
    ) -> str:
        """
        创建 JWT 令牌

        Args:
            session_name: 用户会话名称（用户在业务侧的 UID）
            device_id: 设备唯一标识 ID（IoT 设备等）
            custom_ttl: 自定义有效期（秒），不超过 86400（24小时）

        Returns:
            签名后的 JWT 字符串
        """
        now = int(time.time())
        ttl = custom_ttl if custom_ttl is not None else self.ttl

        # 确保 TTL 不超过 24 小时
        if ttl > 86400:
            ttl = 86400

        # 构建 JWT payload
        payload: Dict[str, Any] = {
            "iss": self.client_id,      # 签发者：OAuth 应用的 Client ID
            "aud": self.audience,        # 受众：Coze API Endpoint
            "iat": now,                  # 签发时间
            "exp": now + ttl,            # 过期时间
            "jti": str(uuid.uuid4()),    # JWT ID：随机字符串，防止重放攻击
        }

        # 可选字段：会话信息
        if session_name:
            payload["session_name"] = session_name

        # 可选字段：设备信息
        if device_id:
            payload["session_context"] = {
                "device_info": {
                    "device_id": device_id
                }
            }

        # JWT 头部
        headers = {
            "kid": self.public_key_id,   # 公钥指纹
            "alg": "RS256",              # 签名算法
            "typ": "JWT"                 # 令牌类型
        }

        # 使用私钥签名
        encoded_jwt = jwt.encode(
            payload,
            self.private_key,
            algorithm="RS256",
            headers=headers
        )

        return encoded_jwt

    def verify_jwt(self, token: str) -> Dict[str, Any]:
        """
        验证 JWT 令牌（用于调试）

        Args:
            token: JWT 令牌字符串

        Returns:
            解码后的 payload
        """
        # 注意：这里不验证签名，仅用于调试查看内容
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded


def generate_jwt_from_env() -> str:
    """
    便捷函数：从环境变量生成 JWT 令牌

    Returns:
        签名后的 JWT 字符串
    """
    signer = JWTSigner.from_env()
    return signer.create_jwt()


if __name__ == "__main__":
    """命令行测试工具"""
    from dotenv import load_dotenv
    load_dotenv()  # 加载 .env 文件

    print("🔐 JWT 签名工具")
    print("=" * 50)

    try:
        # 从环境变量创建签名器
        signer = JWTSigner.from_env()

        # 生成 JWT
        jwt_token = signer.create_jwt(
            session_name="test_user_001",
            device_id="device_12345"
        )

        print(f"✅ JWT 生成成功！")
        print(f"\nJWT Token:")
        print(jwt_token)
        print(f"\n令牌长度: {len(jwt_token)} 字符")

        # 解码查看内容（调试用）
        decoded = signer.verify_jwt(jwt_token)
        print(f"\n📄 JWT Payload:")
        import json
        print(json.dumps(decoded, indent=2, ensure_ascii=False))

        # 计算剩余有效时间
        expires_in = decoded['exp'] - int(time.time())
        print(f"\n⏰ 令牌有效期: {expires_in} 秒 ({expires_in // 60} 分钟)")

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
