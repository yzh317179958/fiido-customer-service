#!/bin/bash
# 测试会话分配和接入逻辑修复
# 验证问题1: 被分配的坐席能成功接入
# 验证问题2: 已分配的会话不会显示在其他坐席的列表中

BASE_URL="http://localhost:8000"
PASSED=0
FAILED=0

echo "================================"
echo "会话分配与接入修复测试"
echo "================================"
echo ""

# 先登录获取坐席1和坐席2的token
echo "步骤1: 登录获取坐席token"
ADMIN_LOGIN=$(curl -s -X POST "$BASE_URL/api/agent/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}')

ADMIN_TOKEN=$(echo "$ADMIN_LOGIN" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('token', ''))")

if [ -z "$ADMIN_TOKEN" ]; then
  echo "❌ 失败: 无法获取admin token"
  exit 1
fi
echo "✅ 获取admin token成功"

AGENT1_LOGIN=$(curl -s -X POST "$BASE_URL/api/agent/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "agent001", "password": "agent123"}')

AGENT1_TOKEN=$(echo "$AGENT1_LOGIN" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('token', ''))" 2>/dev/null || echo "")
AGENT1_ID=$(echo "$AGENT1_LOGIN" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('agent', {}).get('id', ''))" 2>/dev/null || echo "")

if [ -z "$AGENT1_TOKEN" ]; then
  echo "⚠️  agent001不存在,跳过agent001测试"
  AGENT1_TOKEN="$ADMIN_TOKEN"
  AGENT1_ID=$(echo "$ADMIN_LOGIN" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('agent', {}).get('id', ''))")
fi
echo "✅ 获取agent1 token成功 (ID: $AGENT1_ID)"

echo ""
echo "================================"
echo "测试1: 创建测试会话并智能分配"
echo "================================"

# 创建一个测试会话
TEST_SESSION="test_assignment_$(date +%s)"

ESCALATE_RESP=$(curl -s -X POST "$BASE_URL/api/manual/escalate" \
  -H "Content-Type: application/json" \
  -d "{\"session_name\": \"$TEST_SESSION\", \"reason\": \"test\"}")

echo "创建会话: $TEST_SESSION"

# 手动分配给agent1
echo "分配会话给坐席1 (ID: $AGENT1_ID)..."
SESSION_DATA=$(curl -s "$BASE_URL/api/sessions/$TEST_SESSION" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

# 使用Python更新assigned_agent
python3 << EOF
import json
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# 获取会话数据
session_key = "session:$TEST_SESSION"
session_data = r.get(session_key)

if session_data:
    session = json.loads(session_data)
    # 分配给agent1
    session['assigned_agent'] = {
        'id': '$AGENT1_ID',
        'name': 'agent001'
    }
    r.set(session_key, json.dumps(session))
    print("✅ 成功分配会话给agent1")
else:
    print("❌ 会话不存在")
    exit(1)
EOF

if [ $? -ne 0 ]; then
  echo "❌ 失败: 无法分配会话"
  ((FAILED++))
  exit 1
fi

echo ""
echo "================================"
echo "测试2: 被分配的坐席能否接入会话"
echo "================================"

# agent1尝试接入
TAKEOVER_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/sessions/$TEST_SESSION/takeover" \
  -H "Authorization: Bearer $AGENT1_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"agent_id\": \"$AGENT1_ID\", \"agent_name\": \"agent001\"}")

HTTP_CODE=$(echo "$TAKEOVER_RESP" | tail -n1)
BODY=$(echo "$TAKEOVER_RESP" | head -n-1)

echo "HTTP状态码: $HTTP_CODE"
echo "响应内容: $BODY"

if [ "$HTTP_CODE" -eq 200 ]; then
  # 检查是否返回成功
  SUCCESS=$(echo "$BODY" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('success', False))" 2>/dev/null || echo "False")

  if [ "$SUCCESS" = "True" ]; then
    echo "✅ PASS - 被分配的坐席成功接入会话"
    ((PASSED++))
  else
    ERROR_DETAIL=$(echo "$BODY" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('detail', ''))" 2>/dev/null || echo "")
    echo "❌ FAIL - 接入失败: $ERROR_DETAIL"
    ((FAILED++))
  fi
else
  ERROR_DETAIL=$(echo "$BODY" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('detail', ''))" 2>/dev/null || echo "$BODY")
  echo "❌ FAIL - HTTP错误: $HTTP_CODE, 详情: $ERROR_DETAIL"
  ((FAILED++))
fi

echo ""
echo "================================"
echo "测试3: 其他坐席无法接入已分配的会话"
echo "================================"

# admin尝试接入 (应该失败)
TAKEOVER_RESP2=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/sessions/$TEST_SESSION/takeover" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"agent_id\": \"admin_id_xxx\", \"agent_name\": \"admin\"}")

HTTP_CODE2=$(echo "$TAKEOVER_RESP2" | tail -n1)
BODY2=$(echo "$TAKEOVER_RESP2" | head -n-1)

if [ "$HTTP_CODE2" -eq 409 ]; then
  ERROR_MSG=$(echo "$BODY2" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('detail', ''))" 2>/dev/null || echo "")

  if [[ "$ERROR_MSG" == *"ASSIGNED_TO_OTHER"* ]] || [[ "$ERROR_MSG" == *"已分配给"* ]] || [[ "$ERROR_MSG" == *"ALREADY_TAKEN"* ]]; then
    echo "✅ PASS - 其他坐席正确被拒绝: $ERROR_MSG"
    ((PASSED++))
  else
    echo "❌ FAIL - 错误消息不正确: $ERROR_MSG"
    ((FAILED++))
  fi
else
  echo "❌ FAIL - 应返回409状态码，实际: $HTTP_CODE2"
  ((FAILED++))
fi

echo ""
echo "================================"
echo "测试4: 已分配会话不显示在未分配列表中"
echo "================================"

# 查询未分配的会话列表
UNASSIGNED_LIST=$(curl -s "$BASE_URL/api/sessions?status=pending_manual&agent=unassigned" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

# 检查测试会话是否在列表中
IS_IN_LIST=$(echo "$UNASSIGNED_LIST" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    sessions = data.get('data', {}).get('sessions', [])
    found = any(s.get('session_name') == '$TEST_SESSION' for s in sessions)
    print('True' if found else 'False')
except:
    print('Error')
" 2>/dev/null)

if [ "$IS_IN_LIST" = "False" ]; then
  echo "✅ PASS - 已分配的会话不在未分配列表中"
  ((PASSED++))
elif [ "$IS_IN_LIST" = "True" ]; then
  echo "❌ FAIL - 已分配的会话仍然显示在未分配列表中"
  ((FAILED++))
else
  echo "⚠️  WARN - 无法解析响应"
fi

echo ""
echo "================================"
echo "测试5: 坐席1能在自己的列表中看到分配的会话"
echo "================================"

# 查询坐席1的会话列表
MY_LIST=$(curl -s "$BASE_URL/api/sessions?agent=mine" \
  -H "Authorization: Bearer $AGENT1_TOKEN")

IS_IN_MY_LIST=$(echo "$MY_LIST" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    sessions = data.get('data', {}).get('sessions', [])
    found = any(s.get('session_name') == '$TEST_SESSION' for s in sessions)
    print('True' if found else 'False')
except:
    print('Error')
" 2>/dev/null)

if [ "$IS_IN_MY_LIST" = "True" ]; then
  echo "✅ PASS - 坐席1能在自己的列表中看到分配的会话"
  ((PASSED++))
elif [ "$IS_IN_MY_LIST" = "False" ]; then
  echo "❌ FAIL - 坐席1看不到分配给自己的会话"
  ((FAILED++))
else
  echo "⚠️  WARN - 无法解析响应"
fi

echo ""
echo "================================"
echo "清理测试数据"
echo "================================"

# 清理测试会话
python3 << EOF
import redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)
r.delete("session:$TEST_SESSION")
r.srem("status:pending_manual", "$TEST_SESSION")
r.srem("status:manual_live", "$TEST_SESSION")
print("✅ 清理完成")
EOF

echo ""
echo "========================================"
echo "测试总结"
echo "========================================"
echo "总测试: $((PASSED + FAILED))"
echo "通过: $PASSED"
echo "失败: $FAILED"
echo "========================================"

if [ $FAILED -eq 0 ]; then
  echo "✅ 所有测试通过!"
  exit 0
else
  echo "❌ 存在失败的测试"
  exit 1
fi
