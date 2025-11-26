#!/bin/bash

# 工单系统功能测试脚本
# 测试工单CRUD、流转、评论等核心功能

BASE_URL="http://localhost:8000"

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试计数
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 测试结果函数
test_result() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $2"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}❌ FAIL${NC}: $2"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

echo "=========================================="
echo "🎫 工单系统功能测试"
echo "=========================================="

# 1. 获取管理员Token
echo ""
echo "=== 步骤1: 管理员登录获取Token ==="
ADMIN_LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/agent/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')

ADMIN_TOKEN=$(echo $ADMIN_LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('token', ''))" 2>/dev/null)

if [ -z "$ADMIN_TOKEN" ]; then
    echo -e "${RED}❌ 管理员登录失败${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 管理员登录成功${NC}"

# 2. 创建工单
echo ""
echo "=== 步骤2: 创建工单 ==="
CREATE_TICKET_RESPONSE=$(curl -s -X POST "$BASE_URL/api/tickets" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "title": "电池续航异常",
    "description": "客户反馈 C11 Pro 电池续航不足50公里，需要检查",
    "category": "technical",
    "priority": "high",
    "customer_id": "customer_001",
    "bike_model": "C11 Pro",
    "vin": "VIN123456789",
    "department": "technical"
  }')

echo "$CREATE_TICKET_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$CREATE_TICKET_RESPONSE"

TICKET_ID=$(echo $CREATE_TICKET_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('data', {}).get('ticket_id', ''))" 2>/dev/null)
TICKET_NUMBER=$(echo $CREATE_TICKET_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('data', {}).get('ticket_number', ''))" 2>/dev/null)

if [ -z "$TICKET_ID" ]; then
    test_result 1 "创建工单"
    echo "创建失败，后续测试跳过"
    exit 1
else
    test_result 0 "创建工单 (ID: $TICKET_ID, Number: $TICKET_NUMBER)"
fi

# 3. 获取工单详情
echo ""
echo "=== 步骤3: 获取工单详情 ==="
GET_TICKET_RESPONSE=$(curl -s -X GET "$BASE_URL/api/tickets/$TICKET_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

FETCHED_TITLE=$(echo $GET_TICKET_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('data', {}).get('title', ''))" 2>/dev/null)

if [ "$FETCHED_TITLE" = "电池续航异常" ]; then
    test_result 0 "获取工单详情"
else
    test_result 1 "获取工单详情"
fi

# 4. 查询工单列表
echo ""
echo "=== 步骤4: 查询工单列表 ==="
LIST_TICKETS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/tickets?status=pending&page=1&page_size=20" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

TOTAL=$(echo $LIST_TICKETS_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('data', {}).get('total', 0))" 2>/dev/null)

if [ "$TOTAL" -ge 1 ]; then
    test_result 0 "查询工单列表 (共 $TOTAL 条)"
else
    test_result 1 "查询工单列表"
fi

# 5. 指派工单
echo ""
echo "=== 步骤5: 指派工单 ==="
ASSIGN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/tickets/$TICKET_ID/assign" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "assignee_id": "agent_001",
    "assignee_name": "客服小王",
    "department": "technical"
  }')

ASSIGNEE=$(echo $ASSIGN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('data', {}).get('assignee_name', ''))" 2>/dev/null)

if [ "$ASSIGNEE" = "客服小王" ]; then
    test_result 0 "指派工单给客服小王"
else
    test_result 1 "指派工单"
fi

# 6. 更新工单状态
echo ""
echo "=== 步骤6: 更新工单状态为处理中 ==="
STATUS_RESPONSE=$(curl -s -X POST "$BASE_URL/api/tickets/$TICKET_ID/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "status": "in_progress",
    "comment": "开始处理，正在检查电池"
  }')

NEW_STATUS=$(echo $STATUS_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('data', {}).get('status', ''))" 2>/dev/null)

if [ "$NEW_STATUS" = "in_progress" ]; then
    test_result 0 "更新工单状态为 in_progress"
else
    test_result 1 "更新工单状态"
fi

# 7. 添加评论
echo ""
echo "=== 步骤7: 添加工单评论 ==="
COMMENT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/tickets/$TICKET_ID/comments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "content": "已联系客户确认问题，将更换电池",
    "mentions": [],
    "is_internal": false
  }')

COMMENTS_COUNT=$(echo $COMMENT_RESPONSE | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('data', {}).get('comments', [])))" 2>/dev/null)

if [ "$COMMENTS_COUNT" -ge 1 ]; then
    test_result 0 "添加工单评论"
else
    test_result 1 "添加工单评论"
fi

# 8. 更新工单信息
echo ""
echo "=== 步骤8: 更新工单标题和优先级 ==="
UPDATE_RESPONSE=$(curl -s -X PATCH "$BASE_URL/api/tickets/$TICKET_ID" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "title": "电池续航异常 - 需紧急更换",
    "priority": "urgent"
  }')

UPDATED_TITLE=$(echo $UPDATE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('data', {}).get('title', ''))" 2>/dev/null)

if [[ "$UPDATED_TITLE" == *"紧急更换"* ]]; then
    test_result 0 "更新工单标题和优先级"
else
    test_result 1 "更新工单信息"
fi

# 9. 状态流转 - 解决工单
echo ""
echo "=== 步骤9: 标记工单为已解决 ==="
RESOLVE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/tickets/$TICKET_ID/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "status": "resolved",
    "comment": "已更换电池，客户确认问题解决"
  }')

RESOLVED_STATUS=$(echo $RESOLVE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('data', {}).get('status', ''))" 2>/dev/null)

if [ "$RESOLVED_STATUS" = "resolved" ]; then
    test_result 0 "标记工单为已解决"
else
    test_result 1 "标记工单为已解决"
fi

# 10. 检查活动日志
echo ""
echo "=== 步骤10: 检查活动日志完整性 ==="
FINAL_TICKET=$(curl -s -X GET "$BASE_URL/api/tickets/$TICKET_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

ACTIVITY_COUNT=$(echo $FINAL_TICKET | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('data', {}).get('activity_log', [])))" 2>/dev/null)

if [ "$ACTIVITY_COUNT" -ge 5 ]; then
    test_result 0 "活动日志完整性检查 (共 $ACTIVITY_COUNT 条活动)"
else
    test_result 1 "活动日志完整性检查"
fi

# 输出测试总结
echo ""
echo "=========================================="
echo "📊 测试总结"
echo "=========================================="
echo -e "总测试数: $TOTAL_TESTS"
echo -e "${GREEN}通过: $PASSED_TESTS${NC}"
echo -e "${RED}失败: $FAILED_TESTS${NC}"
echo "=========================================="

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ 所有测试通过！${NC}"
    exit 0
else
    echo -e "${RED}❌ 部分测试失败${NC}"
    exit 1
fi
