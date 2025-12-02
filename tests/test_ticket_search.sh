#!/bin/bash
# 【L1-2-Part1】工单关键词搜索 API 自动化测试

set -e

BASE_URL="${BASE_URL:-http://localhost:8000}"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo "========================================="
echo "🔍 工单搜索 API 自动化测试"
echo "========================================="

login_agent() {
  echo -n "获取坐席 Token ... "
  local response
  response=$(curl -s -X POST "$BASE_URL/api/agent/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"agent001","password":"agent123"}')

  AGENT_TOKEN=$(echo "$response" | python3 -c "import sys,json; data=json.load(sys.stdin); print(data.get('token','')) if data.get('success') else print('')" 2>/dev/null)

  if [ -z "$AGENT_TOKEN" ]; then
    echo -e "${RED}失败${NC}"
    echo "$response"
    exit 1
  fi
  echo -e "${GREEN}成功${NC}"
}

create_test_ticket() {
  echo -n "创建测试工单 ... "
  local ts
  ts=$(date +%s)
  TEST_EMAIL="search_user_${ts}@example.com"
  TEST_ORDER_ID="ORD${ts}"
  local payload
  payload=$(cat <<EOF
{
  "title": "搜索测试工单 ${ts}",
  "description": "用于验证关键词搜索的工单，创建于 ${ts}",
  "ticket_type": "after_sale",
  "priority": "high",
  "customer": {
    "name": "搜索测试用户",
    "email": "${TEST_EMAIL}",
    "phone": "+8613800000000",
    "country": "CN"
  },
  "metadata": {
    "order_id": "${TEST_ORDER_ID}",
    "tags": ["search-test", "auto"]
  }
}
EOF
)

  local response
  response=$(curl -s -X POST "$BASE_URL/api/tickets/manual" \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$payload")

  TICKET_ID=$(echo "$response" | python3 -c "import sys,json; data=json.load(sys.stdin); print(data.get('data',{}).get('ticket_id','')) if data.get('success') else print('')" 2>/dev/null)

  if [ -z "$TICKET_ID" ]; then
    echo -e "${RED}失败${NC}"
    echo "$response"
    exit 1
  fi
  echo -e "${GREEN}成功${NC} (Ticket: $TICKET_ID)"
}

run_search_test() {
  local test_name=$1
  local query_value=$2
  local python_code=$3

  TOTAL_TESTS=$((TOTAL_TESTS + 1))
  echo -n "测试 $TOTAL_TESTS: $test_name ... "

  local response
  response=$(curl -s -G "$BASE_URL/api/tickets/search" \
    --data-urlencode "query=$query_value" \
    --data-urlencode "limit=20" \
    -H "Authorization: Bearer $AGENT_TOKEN")

  if RESPONSE="$response" python3 -c "$python_code" 2>/dev/null; then
    echo -e "${GREEN}✓ 通过${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
  else
    echo -e "${RED}✗ 失败${NC}"
    echo "$response"
    FAILED_TESTS=$((FAILED_TESTS + 1))
  fi
}

run_invalid_query_test() {
  TOTAL_TESTS=$((TOTAL_TESTS + 1))
  echo -n "测试 $TOTAL_TESTS: 空查询参数返回400 ... "

  local output
  output=$(curl -s -w "\n%{http_code}" -G "$BASE_URL/api/tickets/search" \
    --data-urlencode "query=" \
    -H "Authorization: Bearer $AGENT_TOKEN")

  local http_code
  http_code=$(echo "$output" | tail -n1)

  if [ "$http_code" = "400" ]; then
    echo -e "${GREEN}✓ 通过${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
  else
    echo -e "${RED}✗ 失败${NC} (HTTP $http_code)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
  fi
}

login_agent
create_test_ticket

PY_MATCH_TICKET=$(cat <<'PYCODE'
import json, os, sys
data = json.loads(os.environ["RESPONSE"])
ticket_id = os.environ["EXPECT_TICKET_ID"]
tickets = data.get("data", {}).get("tickets", [])
if data.get("success") and tickets and tickets[0].get("ticket_id") == ticket_id:
    sys.exit(0)
sys.exit(1)
PYCODE
)

PY_MATCH_EMAIL=$(cat <<'PYCODE'
import json, os, sys
target = os.environ["EXPECT_EMAIL"].lower()
data = json.loads(os.environ["RESPONSE"])
tickets = data.get("data", {}).get("tickets", [])
if not data.get("success"):
    sys.exit(1)
for ticket in tickets:
    customer = ticket.get("customer") or {}
    if (customer.get("email") or "").lower() == target:
        sys.exit(0)
sys.exit(1)
PYCODE
)

PY_MATCH_ORDER=$(cat <<'PYCODE'
import json, os, sys
target = os.environ["EXPECT_ORDER"].upper()
data = json.loads(os.environ["RESPONSE"])
tickets = data.get("data", {}).get("tickets", [])
if not data.get("success") or not tickets:
    sys.exit(1)
metadata = tickets[0].get("metadata") or {}
if str(metadata.get("order_id", "")).upper() == target:
    sys.exit(0)
sys.exit(1)
PYCODE
)

EXPECT_TICKET_ID="$TICKET_ID" run_search_test "工单号精确匹配" "$TICKET_ID" "$PY_MATCH_TICKET"
EXPECT_EMAIL="$TEST_EMAIL" run_search_test "客户邮箱关键字匹配" "${TEST_EMAIL%%@*}" "$PY_MATCH_EMAIL"
EXPECT_ORDER="$TEST_ORDER_ID" run_search_test "订单号精确匹配" "$TEST_ORDER_ID" "$PY_MATCH_ORDER"
run_invalid_query_test

echo ""
echo "========================================="
echo "测试结果: 通过 $PASSED_TESTS / $TOTAL_TESTS"
if [ $FAILED_TESTS -eq 0 ]; then
  echo -e "${GREEN}✓ 所有测试通过${NC}"
  exit 0
else
  echo -e "${RED}✗ 存在失败用例${NC}"
  exit 1
fi
