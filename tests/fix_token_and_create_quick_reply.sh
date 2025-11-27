#!/bin/bash
# 快捷回复功能快速修复和测试脚本
# 用途: 解决 Token 过期问题，并创建测试数据

echo "======================================"
echo "  快捷回复功能 - 快速修复工具"
echo "======================================"
echo ""

# 1. 重新登录获取新 Token
echo "1️⃣ 重新登录获取新 Token..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/agent/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')

echo "登录响应: $LOGIN_RESPONSE"
echo ""

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
  echo "❌ 登录失败，无法获取Token"
  echo "请检查："
  echo "  1. 后端服务是否运行在 8000 端口？"
  echo "     lsof -i :8000"
  echo "  2. 账号密码是否正确？（admin/admin123）"
  exit 1
fi

echo "✅ Token 获取成功: ${TOKEN:0:30}..."
echo ""

# 2. 验证 Token 有效性
echo "2️⃣ 验证 Token 有效性..."
VERIFY_RESPONSE=$(curl -s -X GET http://localhost:8000/api/quick-replies \
  -H "Authorization: Bearer $TOKEN")

if echo "$VERIFY_RESPONSE" | grep -q '"success":true'; then
  echo "✅ Token 验证通过！"
else
  echo "❌ Token 验证失败"
  echo "响应: $VERIFY_RESPONSE"
  exit 1
fi
echo ""

# 3. 检查现有快捷回复数量
echo "3️⃣ 检查现有快捷回复..."
EXISTING_COUNT=$(echo "$VERIFY_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('data', {}).get('items', [])))" 2>/dev/null)
echo "当前快捷回复数量: $EXISTING_COUNT 条"
echo ""

# 4. 创建示例快捷回复（如果数量少于 5 条）
if [ "$EXISTING_COUNT" -lt 5 ]; then
  echo "4️⃣ 数量较少，创建示例快捷回复..."

  # 创建欢迎语
  echo "  创建: 欢迎语..."
  curl -s -X POST http://localhost:8000/api/quick-replies \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "title": "标准欢迎语",
      "content": "您好，我是Fiido官方客服，很高兴为您服务！请问有什么可以帮助您的？",
      "category": "greeting",
      "is_shared": true
    }' > /dev/null

  # 创建带变量的欢迎语
  echo "  创建: 个性化欢迎..."
  curl -s -X POST http://localhost:8000/api/quick-replies \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "title": "个性化欢迎",
      "content": "您好{customer_name}，我是{agent_name}，很高兴为您服务！",
      "category": "greeting",
      "shortcut_key": "1",
      "is_shared": true
    }' > /dev/null

  # 创建售后回复
  echo "  创建: 退换货政策..."
  curl -s -X POST http://localhost:8000/api/quick-replies \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "title": "退换货政策",
      "content": "您好，关于退换货：我们提供7天无理由退换货服务。请您提供订单号{order_id}，我帮您查询处理。",
      "category": "after_sales",
      "shortcut_key": "2",
      "is_shared": true
    }' > /dev/null

  echo "✅ 示例快捷回复创建完成！"
else
  echo "4️⃣ 已有足够的快捷回复，跳过创建。"
fi
echo ""

# 5. 最终统计
echo "5️⃣ 最终统计..."
FINAL_RESPONSE=$(curl -s -X GET http://localhost:8000/api/quick-replies?limit=100 \
  -H "Authorization: Bearer $TOKEN")

FINAL_COUNT=$(echo "$FINAL_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('data', {}).get('items', [])))" 2>/dev/null)

echo "======================================"
echo "  ✅ 修复完成！"
echo "======================================"
echo ""
echo "📊 统计信息："
echo "  - Token 状态: 有效"
echo "  - Token 值: ${TOKEN:0:40}..."
echo "  - 快捷回复总数: $FINAL_COUNT 条"
echo ""
echo "📋 下一步操作："
echo "  1. 浏览器访问: http://localhost:5174"
echo "  2. 如果已登录，请退出登录（右上角）"
echo "  3. 重新登录: admin / admin123"
echo "  4. 进入「快捷回复」管理页面"
echo "  5. 或者在工作台点击 📝 图标测试"
echo ""
echo "💡 提示："
echo "  - Token 有效期：1 小时"
echo "  - Token 过期后需要重新登录"
echo "  - 本脚本可重复运行以获取新 Token"
echo ""
