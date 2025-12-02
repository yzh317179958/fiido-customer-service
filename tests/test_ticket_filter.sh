#!/bin/bash
# 【L1-2-Part1】工单高级筛选 API 自动化测试脚本

set -e

BASE_URL="${BASE_URL:-http://localhost:8000}"
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo "========================================="
echo "🧮 工单高级筛选 API 自动化测试"
echo "========================================="

login_agent() {
  echo -n "获取坐席 Token ... "
  local response
  response=$(curl -s -X POST "$BASE_URL/api/agent/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"agent001","password":"agent123"}')

  AGENT_TOKEN=$(echo "$response" | python3 -c "import sys,json; data=json.load(sys.stdin); print(data.get('token','')) if data.get('success') else print('')" 2>/dev/null)
  AGENT_ID=$(echo "$response" | python3 -c "import sys,json; data=json.load(sys.stdin); agent=data.get('agent') or {}; print(agent.get('id') or agent.get('username',''))" 2>/dev/null)
  AGENT_NAME=$(echo "$response" | python3 -c "import sys,json; data=json.load(sys.stdin); agent=data.get('agent') or {}; print(agent.get('name',''))" 2>/dev/null)

  if [ -z "$AGENT_TOKEN" ] || [ -z "$AGENT_ID" ]; then
    echo -e "${RED}失败${NC}"
    echo "$response"
    exit 1
  fi
  echo -e "${GREEN}成功${NC}"
}

create_ticket() {
  local title=$1
  local tag=$2
  local payload
  payload=$(cat <<EOF
{
  "title": "${title}",
  "description": "工单筛选测试: ${title}",
  "ticket_type": "after_sale",
  "priority": "high",
  "customer": {
    "name": "筛选测试用户",
    "email": "filter_user_${LABEL}@example.com",
    "country": "CN"
  },
  "metadata": {
    "tags": ["${tag}", "${LABEL}"],
    "category": "battery"
  }
}
EOF
)

  local response
  response=$(curl -s -X POST "$BASE_URL/api/tickets/manual" \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$payload")

  local ticket_id
  ticket_id=$(echo "$response" | python3 -c "import sys,json; data=json.load(sys.stdin); print(data.get('data',{}).get('ticket_id','')) if data.get('success') else print('')" 2>/dev/null)

  if [ -z "$ticket_id" ]; then
    echo -e "${RED}创建工单失败${NC}"
    echo "$response"
    exit 1
  fi
  echo "$ticket_id"
}

update_ticket_status() {
  local ticket_id=$1
  local status=$2
  curl -s -X PATCH "$BASE_URL/api/tickets/$ticket_id" \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"status\":\"$status\"}" >/dev/null
}

assign_ticket_to_me() {
  local ticket_id=$1
  curl -s -X POST "$BASE_URL/api/tickets/$ticket_id/assign" \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"agent_id\":\"$AGENT_ID\",\"agent_name\":\"$AGENT_NAME\"}" >/dev/null
}

run_filter_test() {
  local test_name=$1
  local payload=$2
  local python_code=$3

  TOTAL_TESTS=$((TOTAL_TESTS + 1))
  echo -n "测试 $TOTAL_TESTS: $test_name ... "

  local response
  response=$(curl -s -X POST "$BASE_URL/api/tickets/filter" \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$payload")

  if RESPONSE="$response" python3 -c "$python_code" 2>/dev/null; then
    echo -e "${GREEN}✓ 通过${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
  else
    echo -e "${RED}✗ 失败${NC}"
    echo "$response"
    FAILED_TESTS=$((FAILED_TESTS + 1))
  fi
}

run_empty_test() {
  TOTAL_TESTS=$((TOTAL_TESTS + 1))
  echo -n "测试 $TOTAL_TESTS: 日期范围无结果 ... "
  local response
  response=$(curl -s -X POST "$BASE_URL/api/tickets/filter" \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"keyword\":\"$LABEL\",\"created_end\":1}")
  local count
  count=$(echo "$response" | python3 -c "import sys,json; data=json.load(sys.stdin); print(data.get('data',{}).get('total',-1))" 2>/dev/null)
  if [ "$count" = "0" ]; then
    echo -e "${GREEN}✓ 通过${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
  else
    echo -e "${RED}✗ 失败${NC}"
    echo "$response"
    FAILED_TESTS=$((FAILED_TESTS + 1))
  fi
}

login_agent
LABEL="filter-e2e-$(date +%s)"

echo "创建测试工单 ..."
TICKET_A_ID=$(create_ticket "Filter Case A $LABEL" "tag-${LABEL}-a")
TICKET_B_ID=$(create_ticket "Filter Case B $LABEL" "tag-${LABEL}-b")
update_ticket_status "$TICKET_B_ID" "in_progress"
assign_ticket_to_me "$TICKET_B_ID"

PY_PENDING=$(cat <<'PYCODE'
import json, os, sys
data = json.loads(os.environ["RESPONSE"])
tickets = data.get("data", {}).get("tickets", [])
expect = os.environ["EXPECT_A"]
if len(tickets) == 1 and tickets[0].get("ticket_id") == expect:
    sys.exit(0)
sys.exit(1)
PYCODE
)

PY_ASSIGNED=$(cat <<'PYCODE'
import json, os, sys
data = json.loads(os.environ["RESPONSE"])
tickets = data.get("data", {}).get("tickets", [])
expect = os.environ["EXPECT_B"]
if tickets and all(t.get("assigned_agent_id") for t in tickets) and any(t.get("ticket_id") == expect for t in tickets):
    sys.exit(0)
sys.exit(1)
PYCODE
)

PY_TAGS=$(cat <<'PYCODE'
import json, os, sys
data = json.loads(os.environ["RESPONSE"])
tickets = data.get("data", {}).get("tickets", [])
expect = os.environ["EXPECT_B"]
if len(tickets) == 1 and tickets[0].get("ticket_id") == expect:
    sys.exit(0)
sys.exit(1)
PYCODE
)

PAYLOAD_PENDING=$(cat <<EOF
{
  "statuses": ["pending"],
  "keyword": "$LABEL",
  "limit": 10
}
EOF
)

PAYLOAD_ASSIGNED=$(cat <<EOF
{
  "assigned": "mine",
  "keyword": "$LABEL",
  "limit": 10
}
EOF
)

PAYLOAD_TAGS=$(cat <<EOF
{
  "tags": ["tag-${LABEL}-b"],
  "limit": 10
}
EOF
)

EXPECT_A="$TICKET_A_ID" run_filter_test "按状态筛选 (pending)" "$PAYLOAD_PENDING" "$PY_PENDING"
EXPECT_B="$TICKET_B_ID" run_filter_test "按指派筛选 (mine)" "$PAYLOAD_ASSIGNED" "$PY_ASSIGNED"
EXPECT_B="$TICKET_B_ID" run_filter_test "按标签筛选" "$PAYLOAD_TAGS" "$PY_TAGS"
run_empty_test

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
