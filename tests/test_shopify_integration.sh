#!/bin/bash
# Shopify API 集成测试脚本
# 用途: 验证客户画像和订单历史 API（Mock 模式）

echo "============================================"
echo "Shopify API 集成测试 - v3.3.0"
echo "模式: Mock 数据（SHOPIFY_ENABLED=false）"
echo "============================================"
echo ""

# 登录获取 Token
echo "步骤 1: 坐席登录..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/agent/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "❌ 登录失败"
    exit 1
fi

echo "✅ 登录成功"
echo "   Token: ${TOKEN:0:30}..."
echo ""

# 测试客户画像 API
echo "步骤 2: 测试客户画像 API..."
PROFILE_RESPONSE=$(curl -s http://localhost:8000/api/customers/test_customer_123/profile \
  -H "Authorization: Bearer $TOKEN")

echo "$PROFILE_RESPONSE" | python3 -m json.tool | head -20

PROFILE_SUCCESS=$(echo "$PROFILE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['success'])" 2>/dev/null)

if [ "$PROFILE_SUCCESS" = "True" ]; then
    echo ""
    echo "✅ 客户画像 API 测试通过"

    # 提取关键字段验证
    CUSTOMER_ID=$(echo "$PROFILE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['customer_id'])" 2>/dev/null)
    NAME=$(echo "$PROFILE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['name'])" 2>/dev/null)
    VIP_STATUS=$(echo "$PROFILE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['vip_status'])" 2>/dev/null)

    echo "   Customer ID: $CUSTOMER_ID"
    echo "   Name: $NAME"
    echo "   VIP Status: $VIP_STATUS"
else
    echo "❌ 客户画像 API 测试失败"
fi

echo ""
echo "============================================"

# 测试订单历史 API
echo "步骤 3: 测试订单历史 API..."
ORDERS_RESPONSE=$(curl -s http://localhost:8000/api/customers/test_customer_123/orders \
  -H "Authorization: Bearer $TOKEN")

echo "$ORDERS_RESPONSE" | python3 -m json.tool | head -30

ORDERS_SUCCESS=$(echo "$ORDERS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['success'])" 2>/dev/null)

if [ "$ORDERS_SUCCESS" = "True" ]; then
    echo ""
    echo "✅ 订单历史 API 测试通过"

    # 提取订单数量
    ORDER_COUNT=$(echo "$ORDERS_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['data']['orders']))" 2>/dev/null)

    echo "   订单数量: $ORDER_COUNT"

    # 提取第一个订单信息
    if [ "$ORDER_COUNT" -gt 0 ]; then
        ORDER_NUMBER=$(echo "$ORDERS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['orders'][0]['order_number'])" 2>/dev/null)
        ORDER_STATUS=$(echo "$ORDERS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['orders'][0]['status'])" 2>/dev/null)
        ORDER_TOTAL=$(echo "$ORDERS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['orders'][0]['total_amount'])" 2>/dev/null)

        echo "   第一个订单: $ORDER_NUMBER"
        echo "   订单状态: $ORDER_STATUS"
        echo "   订单金额: €$ORDER_TOTAL"
    fi
else
    echo "❌ 订单历史 API 测试失败"
fi

echo ""
echo "============================================"
echo "测试完成！"
echo ""
echo "📝 说明:"
echo "   当前使用 Mock 数据（SHOPIFY_ENABLED=false）"
echo "   获取真实 Shopify 凭证后："
echo "   1. 参考 docs/Shopify配置待办事项.md"
echo "   2. 更新 .env 配置"
echo "   3. 重启后端服务"
echo "   4. 再次运行此测试脚本"
echo "============================================"
