#!/bin/bash
# 测试转接列表只显示在线坐席

BASE_URL="http://localhost:8000"
PASSED=0
FAILED=0

echo "========================================"
echo "测试：转接列表在线状态过滤"
echo "========================================"

# 登录 admin 获取 token
echo "步骤1: 登录 admin"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/agent/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}')

ADMIN_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('token', ''))")

if [ -z "$ADMIN_TOKEN" ]; then
  echo "❌ FAIL - 无法获取 admin token"
  exit 1
fi

echo "✅ PASS - Admin 登录成功"
((PASSED++))

# 测试2: 获取可转接坐席列表（应该只有真正在线的）
echo ""
echo "测试2: 获取可转接坐席列表"
AGENTS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/agents/available" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

echo "$AGENTS_RESPONSE" | python3 -m json.tool

AGENT_COUNT=$(echo "$AGENTS_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('data', {}).get('items', [])))")

echo "可转接坐席数量: $AGENT_COUNT"

# 检查所有返回的坐席状态是否都是 online
ALL_ONLINE=$(echo "$AGENTS_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data.get('data', {}).get('items', [])
all_online = all(agent['status'] == 'online' for agent in items)
print('true' if all_online else 'false')
")

if [ "$ALL_ONLINE" == "true" ]; then
  echo "✅ PASS - 所有返回的坐席状态都是 online"
  ((PASSED++))
else
  echo "❌ FAIL - 存在非 online 状态的坐席"
  ((FAILED++))
fi

echo ""
echo "========================================"
echo "总测试: $((PASSED + FAILED))"
echo "通过: $PASSED"
echo "失败: $FAILED"
echo "========================================"

if [ $FAILED -eq 0 ]; then
  exit 0
else
  exit 1
fi
