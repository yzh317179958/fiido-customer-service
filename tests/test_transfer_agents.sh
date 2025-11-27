#!/bin/bash
# tests/test_transfer_agents.sh
# 测试会话转接坐席列表获取功能

BASE_URL="http://localhost:8000"
PASSED=0
FAILED=0
TOTAL=0

echo "========================================"
echo "🧪 测试会话转接坐席列表功能"
echo "========================================"
echo ""

# 1. 获取 admin token
echo "步骤1: 获取 admin token"
ADMIN_LOGIN=$(curl -s -X POST "$BASE_URL/api/agent/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')

ADMIN_TOKEN=$(echo "$ADMIN_LOGIN" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$ADMIN_TOKEN" ]; then
  echo "❌ FAIL - 无法获取 admin token"
  exit 1
fi

echo "✅ admin token 获取成功"
echo ""

# 2. 获取 agent001 token
echo "步骤2: 获取 agent001 token"
AGENT_LOGIN=$(curl -s -X POST "$BASE_URL/api/agent/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"agent001","password":"agent123"}')

AGENT_TOKEN=$(echo "$AGENT_LOGIN" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$AGENT_TOKEN" ]; then
  echo "❌ FAIL - 无法获取 agent001 token"
  exit 1
fi

echo "✅ agent001 token 获取成功"
echo ""

# 测试1: 普通坐席获取可转接坐席列表
echo "测试1: 普通坐席获取可转接坐席列表"
((TOTAL++))

RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/agents/available" \
  -H "Authorization: Bearer $AGENT_TOKEN")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 200 ]; then
  echo "✅ PASS - 状态码200"
  ((PASSED++))

  # 验证返回数据格式
  if echo "$BODY" | grep -q '"success":true'; then
    echo "✅ PASS - 返回 success:true"
    ((PASSED++))
    ((TOTAL++))
  else
    echo "❌ FAIL - 缺少 success 字段"
    ((FAILED++))
    ((TOTAL++))
  fi

  # 验证是否包含坐席列表
  if echo "$BODY" | grep -q '"items"'; then
    echo "✅ PASS - 返回包含 items 字段"
    ((PASSED++))
    ((TOTAL++))

    # 显示坐席数量
    AGENT_COUNT=$(echo "$BODY" | grep -o '"total":[0-9]*' | cut -d':' -f2)
    echo "📊 可转接坐席数量: $AGENT_COUNT"
  else
    echo "❌ FAIL - 缺少 items 字段"
    ((FAILED++))
    ((TOTAL++))
  fi

  # 验证是否排除了当前坐席（agent001）
  if echo "$BODY" | grep -q '"username":"agent001"'; then
    echo "❌ FAIL - 列表中不应包含当前坐席 agent001"
    ((FAILED++))
    ((TOTAL++))
  else
    echo "✅ PASS - 正确排除当前坐席"
    ((PASSED++))
    ((TOTAL++))
  fi

  # 验证返回字段完整性（id, username, name, status, role, max_sessions）
  if echo "$BODY" | grep -q '"id"' && \
     echo "$BODY" | grep -q '"username"' && \
     echo "$BODY" | grep -q '"name"' && \
     echo "$BODY" | grep -q '"status"' && \
     echo "$BODY" | grep -q '"role"' && \
     echo "$BODY" | grep -q '"max_sessions"'; then
    echo "✅ PASS - 坐席信息字段完整"
    ((PASSED++))
    ((TOTAL++))
  else
    echo "❌ FAIL - 坐席信息字段不完整"
    echo "返回数据: $BODY"
    ((FAILED++))
    ((TOTAL++))
  fi
else
  echo "❌ FAIL - 状态码 $HTTP_CODE，预期 200"
  echo "返回内容: $BODY"
  ((FAILED++))
fi
echo ""

# 测试2: 管理员获取可转接坐席列表
echo "测试2: 管理员获取可转接坐席列表"
((TOTAL++))

RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/agents/available" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 200 ]; then
  echo "✅ PASS - 管理员可以访问"
  ((PASSED++))

  # 验证不包含 admin 本身
  if echo "$BODY" | grep -q '"username":"admin"'; then
    echo "❌ FAIL - 列表中不应包含当前坐席 admin"
    ((FAILED++))
    ((TOTAL++))
  else
    echo "✅ PASS - 正确排除当前坐席"
    ((PASSED++))
    ((TOTAL++))
  fi
else
  echo "❌ FAIL - 状态码 $HTTP_CODE"
  ((FAILED++))
fi
echo ""

# 测试3: 无 Token 访问（应该失败）
echo "测试3: 无 Token 访问"
((TOTAL++))

RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/agents/available")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" -eq 401 ] || [ "$HTTP_CODE" -eq 403 ]; then
  echo "✅ PASS - 正确拒绝无权限访问（状态码 $HTTP_CODE）"
  ((PASSED++))
else
  echo "❌ FAIL - 应该返回 401/403，实际返回 $HTTP_CODE"
  ((FAILED++))
fi
echo ""

# 输出总结
echo "========================================"
echo "测试总结"
echo "========================================"
echo "总测试数: $TOTAL"
echo "通过: $PASSED (绿色)"
echo "失败: $FAILED (红色)"
echo ""

if [ $FAILED -eq 0 ]; then
  echo "🎉 所有测试通过！"
  exit 0
else
  echo "❌ 有测试失败"
  exit 1
fi
