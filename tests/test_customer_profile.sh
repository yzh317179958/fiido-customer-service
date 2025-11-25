#!/bin/bash

echo "=========================================="
echo "  客户画像功能测试演示"
echo "=========================================="
echo ""

# 1. 获取坐席 Token
echo "步骤1: 坐席登录获取 Token..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/agent/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }')

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ 登录失败"
  exit 1
fi

echo "✅ 登录成功，获得 Token: ${TOKEN:0:20}..."
echo ""

# 2. 调用客户画像 API
echo "步骤2: 获取客户画像信息..."
CUSTOMER_ID="session_test_123"

PROFILE_RESPONSE=$(curl -s -X GET \
  "http://localhost:8000/api/customers/${CUSTOMER_ID}/profile" \
  -H "Authorization: Bearer $TOKEN")

echo "API 响应:"
echo "$PROFILE_RESPONSE" | python3 -m json.tool
echo ""

# 3. 解析关键字段
echo "=========================================="
echo "  客户画像关键信息"
echo "=========================================="

NAME=$(echo $PROFILE_RESPONSE | grep -o '"name":"[^"]*"' | cut -d'"' -f4)
EMAIL=$(echo $PROFILE_RESPONSE | grep -o '"email":"[^"]*"' | cut -d'"' -f4)
COUNTRY=$(echo $PROFILE_RESPONSE | grep -o '"country":"[^"]*"' | cut -d'"' -f4)
VIP=$(echo $PROFILE_RESPONSE | grep -o '"vip_status":"[^"]*"' | cut -d'"' -f4)

echo "👤 姓名: $NAME"
echo "📧 邮箱: $EMAIL"
echo "🌍 国家: $COUNTRY"
echo "⭐ VIP: $VIP"
echo ""

echo "=========================================="
echo "  测试完成！"
echo "=========================================="
echo ""
echo "📝 说明："
echo "1. 当前返回的是模拟数据（MVP阶段）"
echo "2. 未来将集成 Shopify API 获取真实数据"
echo "3. 前端会自动脱敏显示邮箱和电话"
echo ""
