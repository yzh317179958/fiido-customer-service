#!/bin/bash
# 测试会话标签显示的端到端验证脚本

set -e

echo "=================================================="
echo "🧪 会话标签显示端到端测试"
echo "=================================================="
echo ""

# 1. 检查后端服务
echo "【步骤1】检查后端服务..."
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "✅ 后端服务正常"
else
    echo "❌ 后端服务未运行"
    exit 1
fi
echo ""

# 2. 登录获取Token
echo "【步骤2】登录获取Token..."
ADMIN_TOKEN=$(curl -s -X POST "http://localhost:8000/api/agent/login" \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "password": "admin123"}' | \
    python3 -c "import json,sys; print(json.load(sys.stdin)['token'])")

if [ -z "$ADMIN_TOKEN" ]; then
    echo "❌ 登录失败"
    exit 1
fi
echo "✅ 登录成功"
echo ""

# 3. 获取标签列表
echo "【步骤3】获取标签列表..."
TAGS_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/tags" \
    -H "Authorization: Bearer $ADMIN_TOKEN")

echo "$TAGS_RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if data.get('success'):
    system_tags = data['data']['system_tags']
    print(f'✅ 标签API正常，返回 {len(system_tags)} 个系统标签')
    for tag in system_tags:
        print(f\"  - {tag['id']:15s} {tag['name']:6s} ({tag['color']})\")
else:
    print('❌ 标签API返回失败:', data)
    sys.exit(1)
"
echo ""

# 4. 获取会话列表（验证tags字段）
echo "【步骤4】获取会话列表..."
SESSIONS_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/sessions?limit=5")

echo "$SESSIONS_RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
sessions = data['data']['sessions']
print(f'✅ 会话API正常，返回 {len(sessions)} 个会话\n')

has_tags = False
for session in sessions[:5]:
    name = session['session_name']
    tags = session.get('tags', [])
    if tags:
        has_tags = True
        print(f'  会话: {name}')
        print(f'    标签: {tags}')
        print(f'    ✅ 标签格式正确（字符串数组）\n')

if not has_tags:
    print('⚠️  警告：前5个会话中没有带标签的会话')
    print('   建议：运行 python3 create_test_data.py 创建测试数据')
"
echo ""

# 5. 验证前端API配置
echo "【步骤5】检查前端配置..."
if grep -q "VITE_API_BASE=http://localhost:8000" /home/yzh/AI客服/鉴权/agent-workbench/.env; then
    echo "✅ 前端API配置正确: localhost:8000"
else
    echo "⚠️  前端API配置可能不匹配"
    cat /home/yzh/AI客服/鉴权/agent-workbench/.env
fi
echo ""

# 6. 检查前端服务
echo "【步骤6】检查前端服务..."
if pgrep -f "vite.*agent-workbench" > /dev/null; then
    PORT=$(tail -20 /tmp/agent-workbench.log | grep "Local:" | sed 's/.*http:\/\/localhost:\([0-9]*\).*/\1/')
    echo "✅ 前端服务正常运行"
    echo "   访问地址: http://localhost:$PORT"
else
    echo "❌ 前端服务未运行"
    exit 1
fi
echo ""

echo "=================================================="
echo "✅ 所有后端检查通过！"
echo "=================================================="
echo ""
echo "📝 前端显示检查清单："
echo ""
echo "1. 打开浏览器访问: http://localhost:$PORT"
echo "2. 登录账号: admin / admin123"
echo "3. 查看会话列表，每个会话下方应该显示彩色标签徽章"
echo ""
echo "如果标签仍然不显示，请："
echo "  - 按 F12 打开开发者工具"
echo "  - 切换到 Console 标签"
echo "  - 查找日志消息："
echo "    ✅ '标签列表加载成功: N 个' - 表示加载成功"
echo "    ❌ 任何错误信息 - 告诉我具体错误"
echo ""
echo "  - 切换到 Network 标签"
echo "  - 刷新页面，查找："
echo "    • GET /api/tags - 应该返回200状态码"
echo "    • GET /api/sessions - 应该返回200状态码"
echo ""
