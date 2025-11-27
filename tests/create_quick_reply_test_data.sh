#!/bin/bash
# 快捷回复测试数据创建脚本
# 用途: 创建多个快捷回复测试数据，方便UI测试

echo "🚀 开始创建快捷回复测试数据..."

# 1. 登录获取 Token
echo "1️⃣ 登录获取Token..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/agent/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin).get('token', ''))")

if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
  echo "❌ 登录失败，无法获取Token"
  exit 1
fi

echo "✅ Token获取成功: ${TOKEN:0:20}..."

# 2. 创建问候分类快捷回复
echo ""
echo "2️⃣ 创建问候分类快捷回复..."

curl -s -X POST http://localhost:8000/api/quick-replies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "标准欢迎语",
    "content": "您好，我是Fiido官方客服，很高兴为您服务！请问有什么可以帮助您的？",
    "category": "greeting",
    "is_shared": true
  }' > /dev/null

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

curl -s -X POST http://localhost:8000/api/quick-replies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "请稍等",
    "content": "好的，请您稍等片刻，我正在为您查询相关信息。",
    "category": "greeting",
    "is_shared": true
  }' > /dev/null

echo "✅ 问候分类创建完成（3条）"

# 3. 创建售前分类快捷回复
echo ""
echo "3️⃣ 创建售前分类快捷回复..."

curl -s -X POST http://localhost:8000/api/quick-replies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "产品介绍",
    "content": "关于{product_name}，我来为您详细介绍一下：这款产品具有轻便、续航长、性能强等特点，非常适合城市通勤使用。",
    "category": "pre_sales",
    "shortcut_key": "2",
    "is_shared": true
  }' > /dev/null

curl -s -X POST http://localhost:8000/api/quick-replies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "价格咨询",
    "content": "目前这款产品的官方售价是XX元，现在下单还有限时优惠活动，具体优惠详情我帮您查询一下。",
    "category": "pre_sales",
    "is_shared": true
  }' > /dev/null

curl -s -X POST http://localhost:8000/api/quick-replies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "库存确认",
    "content": "我帮您查询了一下，{product_name}目前有现货，今天下单明天即可发货。",
    "category": "pre_sales",
    "is_shared": true
  }' > /dev/null

echo "✅ 售前分类创建完成（3条）"

# 4. 创建售后分类快捷回复
echo ""
echo "4️⃣ 创建售后分类快捷回复..."

curl -s -X POST http://localhost:8000/api/quick-replies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "退换货政策",
    "content": "您好，关于退换货：我们提供7天无理由退换货服务。请您提供订单号{order_id}，我帮您查询处理。",
    "category": "after_sales",
    "shortcut_key": "3",
    "is_shared": true
  }' > /dev/null

curl -s -X POST http://localhost:8000/api/quick-replies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "维修服务",
    "content": "我们提供全国联保服务，保修期内免费维修。您可以选择寄回总部或到当地授权服务点维修。",
    "category": "after_sales",
    "is_shared": true
  }' > /dev/null

curl -s -X POST http://localhost:8000/api/quick-replies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "质量问题处理",
    "content": "非常抱歉给您带来不便。请您描述一下具体问题，我会第一时间为您安排处理方案。",
    "category": "after_sales",
    "is_shared": true
  }' > /dev/null

echo "✅ 售后分类创建完成（3条）"

# 5. 创建物流分类快捷回复
echo ""
echo "5️⃣ 创建物流分类快捷回复..."

curl -s -X POST http://localhost:8000/api/quick-replies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "物流查询",
    "content": "您的订单{order_id}当前状态：{order_status}，物流单号：{tracking_number}。您可以通过物流公司官网查询最新进度。",
    "category": "logistics",
    "shortcut_key": "4",
    "is_shared": true
  }' > /dev/null

curl -s -X POST http://localhost:8000/api/quick-replies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "发货通知",
    "content": "您的订单已发货！物流单号：{tracking_number}，预计3-5个工作日送达，请您注意查收。",
    "category": "logistics",
    "is_shared": true
  }' > /dev/null

echo "✅ 物流分类创建完成（2条）"

# 6. 创建技术支持分类快捷回复
echo ""
echo "6️⃣ 创建技术支持分类快捷回复..."

curl -s -X POST http://localhost:8000/api/quick-replies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "故障排查",
    "content": "请您尝试以下步骤：1. 检查电源是否正常；2. 重启设备；3. 检查连接线路。如果问题仍未解决，请告知我详细情况。",
    "category": "technical",
    "shortcut_key": "5",
    "is_shared": true
  }' > /dev/null

curl -s -X POST http://localhost:8000/api/quick-replies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "使用说明",
    "content": "关于产品使用，建议您先查看说明书或观看我们的视频教程。如有不明白的地方，我可以为您详细讲解。",
    "category": "technical",
    "is_shared": true
  }' > /dev/null

echo "✅ 技术支持分类创建完成（2条）"

# 7. 创建结束语分类快捷回复
echo ""
echo "7️⃣ 创建结束语分类快捷回复..."

curl -s -X POST http://localhost:8000/api/quick-replies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "问题解决",
    "content": "很高兴能帮助到您！如果还有其他问题，随时联系我们。祝您生活愉快！",
    "category": "closing",
    "shortcut_key": "9",
    "is_shared": true
  }' > /dev/null

curl -s -X POST http://localhost:8000/api/quick-replies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "满意度调查",
    "content": "感谢您的咨询！如果您对本次服务满意，欢迎给我们一个好评。期待再次为您服务！",
    "category": "closing",
    "is_shared": true
  }' > /dev/null

curl -s -X POST http://localhost:8000/api/quick-replies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "后续跟进",
    "content": "好的，我已记录您的问题，稍后会有专人跟进处理。请保持电话畅通，谢谢！",
    "category": "closing",
    "is_shared": true
  }' > /dev/null

echo "✅ 结束语分类创建完成（3条）"

# 8. 统计结果
echo ""
echo "=========================================="
echo "✅ 测试数据创建完成！"
echo "=========================================="
echo "总计创建快捷回复："
echo "  - 问候: 3条"
echo "  - 售前: 3条"
echo "  - 售后: 3条"
echo "  - 物流: 2条"
echo "  - 技术: 2条"
echo "  - 结束: 3条"
echo "  【总计: 16条】"
echo ""
echo "📋 测试指南："
echo "   docs/快捷回复功能测试指南.md"
echo ""
echo "🌐 访问地址："
echo "   快捷回复管理: http://localhost:5174/quick-replies"
echo "   坐席工作台:   http://localhost:5174/dashboard"
echo ""
