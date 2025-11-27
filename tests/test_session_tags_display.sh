#!/bin/bash
# 会话标签系统显示功能自动化测试 v3.6.0

echo "🧪 会话标签系统显示功能自动化测试"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试计数器
PASSED=0
FAILED=0
TOTAL=0

# 测试函数
test_case() {
    TOTAL=$((TOTAL + 1))
    local test_name="$1"
    local test_cmd="$2"
    local expected="$3"

    echo -n "测试 $TOTAL: $test_name ... "

    result=$(eval "$test_cmd" 2>&1)

    if echo "$result" | grep -q "$expected"; then
        echo -e "${GREEN}✅ 通过${NC}"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ 失败${NC}"
        echo "  预期: $expected"
        echo "  实际: $result"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# 获取管理员token
echo "🔐 获取测试Token..."
ADMIN_TOKEN=$(cat /tmp/admin_token.txt 2>/dev/null || echo "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhZ2VudF9pZCI6ImFnZW50XzE3NjM5NzM2MDM2MzIiLCJ1c2VybmFtZSI6ImFkbWluIiwicm9sZSI6ImFkbWluIiwiaWF0IjoxNzY0MTMxMDgzLjczNjY5MjIsImV4cCI6MTc2NDEzNDY4My43MzY2OTIyfQ.UxRoX0BOw1NC8TlimLJCsOaLsMQU9A_7C-_7yruuR6Q")
AUTH_HEADER="Authorization: Bearer $ADMIN_TOKEN"
API_BASE="http://localhost:8000"

echo ""
echo "📊 测试1: 统计数据显示"
echo "========================"

test_case "获取会话统计" \
    "curl -s '$API_BASE/api/sessions/stats' -H '$AUTH_HEADER' | jq -r '.success'" \
    "true"

test_case "待接入数量统计" \
    "curl -s '$API_BASE/api/sessions/stats' -H '$AUTH_HEADER' | jq -r '.data.by_status.pending_manual'" \
    "4"

test_case "服务中数量统计" \
    "curl -s '$API_BASE/api/sessions/stats' -H '$AUTH_HEADER' | jq -r '.data.by_status.manual_live'" \
    "1"

echo ""
echo "🏷️  测试2: 标签显示数据"
echo "========================"

test_case "获取标签列表" \
    "curl -s '$API_BASE/api/tags' -H '$AUTH_HEADER' | jq -r '.success'" \
    "true"

test_case "系统标签数量" \
    "curl -s '$API_BASE/api/tags' -H '$AUTH_HEADER' | jq -r '.data.system_tags | length'" \
    "6"

test_case "VIP标签存在" \
    "curl -s '$API_BASE/api/tags' -H '$AUTH_HEADER' | jq -r '.data.system_tags[] | select(.id==\"tag_vip\") | .name'" \
    "VIP"

test_case "紧急标签存在" \
    "curl -s '$API_BASE/api/tags' -H '$AUTH_HEADER' | jq -r '.data.system_tags[] | select(.id==\"tag_urgent\") | .name'" \
    "紧急"

echo ""
echo "📋 测试3: 会话列表标签显示"
echo "============================"

test_case "获取所有会话" \
    "curl -s '$API_BASE/api/sessions?limit=50' -H '$AUTH_HEADER' | jq -r '.success'" \
    "true"

test_case "张三会话标签" \
    "curl -s '$API_BASE/api/sessions?limit=50' -H '$AUTH_HEADER' | jq -r '.data.sessions[] | select(.session_name==\"vip_customer_张三_001\") | .tags[0]'" \
    "tag_vip"

test_case "李四会话多标签" \
    "curl -s '$API_BASE/api/sessions?limit=50' -H '$AUTH_HEADER' | jq -r '.data.sessions[] | select(.session_name==\"urgent_issue_李四_002\") | .tags | length'" \
    "2"

test_case "王五会话标签" \
    "curl -s '$API_BASE/api/sessions?limit=50' -H '$AUTH_HEADER' | jq -r '.data.sessions[] | select(.session_name==\"refund_request_王五_003\") | .tags | contains([\"tag_refund\"])'" \
    "true"

test_case "钱七会话标签" \
    "curl -s '$API_BASE/api/sessions?limit=50' -H '$AUTH_HEADER' | jq -r '.data.sessions[] | select(.session_name==\"battery_problem_钱七_005\") | .tags | contains([\"tag_vip\", \"tag_technical\"])'" \
    "true"

echo ""
echo "🔍 测试4: 按状态筛选会话"
echo "=========================="

test_case "筛选待接入会话" \
    "curl -s '$API_BASE/api/sessions?status=pending_manual&limit=50' -H '$AUTH_HEADER' | jq -r '.data.sessions | length >= 4'" \
    "true"

test_case "筛选服务中会话" \
    "curl -s '$API_BASE/api/sessions?status=manual_live&limit=50' -H '$AUTH_HEADER' | jq -r '.data.sessions | length >= 1'" \
    "true"

echo ""
echo "🏷️  测试5: 按标签筛选会话"
echo "============================"

test_case "筛选VIP标签会话" \
    "curl -s '$API_BASE/api/sessions/by-tag/tag_vip?limit=10' -H '$AUTH_HEADER' | jq -r '.data.sessions | length >= 2'" \
    "true"

test_case "筛选技术标签会话" \
    "curl -s '$API_BASE/api/sessions/by-tag/tag_technical?limit=10' -H '$AUTH_HEADER' | jq -r '.data.sessions | length >= 2'" \
    "true"

test_case "筛选紧急标签会话" \
    "curl -s '$API_BASE/api/sessions/by-tag/tag_urgent?limit=10' -H '$AUTH_HEADER' | jq -r '.data.sessions | length >= 1'" \
    "true"

echo ""
echo "🎨 测试6: 标签颜色和图标"
echo "=========================="

test_case "VIP标签颜色" \
    "curl -s '$API_BASE/api/tags' -H '$AUTH_HEADER' | jq -r '.data.system_tags[] | select(.id==\"tag_vip\") | .color'" \
    "#F59E0B"

test_case "紧急标签图标" \
    "curl -s '$API_BASE/api/tags' -H '$AUTH_HEADER' | jq -r '.data.system_tags[] | select(.id==\"tag_urgent\") | .icon'" \
    "🔴"

test_case "技术标签图标" \
    "curl -s '$API_BASE/api/tags' -H '$AUTH_HEADER' | jq -r '.data.system_tags[] | select(.id==\"tag_technical\") | .icon'" \
    "🔵"

echo ""
echo "🔄 测试7: 标签管理操作"
echo "========================"

# 创建自定义标签
CUSTOM_TAG_RESPONSE=$(curl -s -X POST "$API_BASE/api/tags" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "测试标签",
        "color": "#10B981",
        "icon": "🧪",
        "description": "自动化测试标签"
    }')

CUSTOM_TAG_ID=$(echo "$CUSTOM_TAG_RESPONSE" | jq -r '.data.tag.id')

test_case "创建自定义标签" \
    "echo '$CUSTOM_TAG_RESPONSE' | jq -r '.success'" \
    "true"

test_case "自定义标签ID生成" \
    "echo '$CUSTOM_TAG_ID' | grep -q 'tag_custom_' && echo 'true'" \
    "true"

# 添加标签到会话
test_case "添加标签到会话" \
    "curl -s -X POST '$API_BASE/api/sessions/vip_customer_张三_001/tags' -H '$AUTH_HEADER' -H 'Content-Type: application/json' -d '{\"tag_id\":\"$CUSTOM_TAG_ID\"}' | jq -r '.success'" \
    "true"

# 验证标签已添加
test_case "验证标签已添加" \
    "curl -s '$API_BASE/api/sessions?limit=50' -H '$AUTH_HEADER' | jq -r '.data.sessions[] | select(.session_name==\"vip_customer_张三_001\") | .tags | contains([\"$CUSTOM_TAG_ID\"])'" \
    "true"

# 移除标签
test_case "移除会话标签" \
    "curl -s -X DELETE '$API_BASE/api/sessions/vip_customer_张三_001/tags/$CUSTOM_TAG_ID' -H '$AUTH_HEADER' | jq -r '.success'" \
    "true"

echo ""
echo "📊 测试8: Redis数据一致性"
echo "============================"

test_case "Redis状态索引-待接入" \
    "redis-cli SCARD 'status:pending_manual'" \
    "4"

test_case "Redis状态索引-服务中" \
    "redis-cli SCARD 'status:manual_live'" \
    "1"

test_case "会话数据包含标签字段" \
    "redis-cli GET 'session:vip_customer_张三_001' | jq -r '.tags | type'" \
    "array"

echo ""
echo "======================================"
echo "📊 测试结果汇总"
echo "======================================"
echo -e "总测试数: $TOTAL"
echo -e "${GREEN}通过: $PASSED${NC}"
echo -e "${RED}失败: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ 所有测试通过！${NC}"
    exit 0
else
    echo -e "${RED}❌ 有 $FAILED 个测试失败${NC}"
    exit 1
fi
