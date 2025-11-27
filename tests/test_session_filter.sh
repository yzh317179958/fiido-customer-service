#!/bin/bash
# 【L1-1-Part1-模块1】会话高级筛选与搜索 - 自动化测试脚本
# 测试新增的筛选、搜索、排序功能

BASE_URL="http://localhost:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "【L1-1-Part1-模块1】会话筛选功能测试"
echo "========================================="
echo ""

# 计数器
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 测试函数
test_api() {
    local test_name=$1
    local endpoint=$2
    local expected_field=$3
    local expected_value=$4

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "测试 $TOTAL_TESTS: $test_name ... "

    response=$(curl -s "$BASE_URL$endpoint")
    success=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)

    if [ "$success" = "True" ]; then
        if [ -n "$expected_field" ]; then
            actual=$(echo "$response" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['data'].get('$expected_field', 'NOT_FOUND'))" 2>/dev/null)
            if [ "$actual" = "$expected_value" ]; then
                echo -e "${GREEN}✓ 通过${NC}"
                PASSED_TESTS=$((PASSED_TESTS + 1))
            else
                echo -e "${RED}✗ 失败${NC} (期望: $expected_value, 实际: $actual)"
                FAILED_TESTS=$((FAILED_TESTS + 1))
            fi
        else
            echo -e "${GREEN}✓ 通过${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        fi
    else
        error=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('detail', 'Unknown error'))" 2>/dev/null)
        echo -e "${RED}✗ 失败${NC} ($error)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

echo "=== 基础筛选测试 ==="
echo ""

# Test 1: 基础查询
test_api "基础会话列表查询" "/api/sessions?limit=5"

# Test 2: 状态筛选
test_api "按状态筛选(all)" "/api/sessions?status=all&limit=5"
test_api "按状态筛选(pending_manual)" "/api/sessions?status=pending_manual&limit=5"

# Test 3: VIP客户筛选
echo ""
echo "=== VIP客户筛选测试 ==="
echo ""
test_api "筛选VIP客户" "/api/sessions?customer_type=vip&limit=5"

# Test 4: 关键词搜索
echo ""
echo "=== 关键词搜索测试 ==="
echo ""

# URL编码：张三=%E5%BC%A0%E4%B8%89
test_api "搜索客户昵称(张三)" "/api/sessions?keyword=%E5%BC%A0%E4%B8%89&limit=5"

# Test 5: 排序功能
echo ""
echo "=== 排序功能测试 ==="
echo ""
test_api "VIP优先排序" "/api/sessions?sort=vip&limit=5"
test_api "最新优先排序" "/api/sessions?sort=newest&limit=5"
test_api "最早优先排序" "/api/sessions?sort=oldest&limit=5"
test_api "等待时长排序" "/api/sessions?sort=waitTime&limit=5"

# Test 6: 组合筛选
echo ""
echo "=== 组合筛选测试 ==="
echo ""
test_api "VIP+pending状态" "/api/sessions?customer_type=vip&status=pending_manual&limit=5"

echo ""
echo "========================================="
echo "测试结果汇总"
echo "========================================="
echo -e "总测试数: $TOTAL_TESTS"
echo -e "${GREEN}通过: $PASSED_TESTS${NC}"
echo -e "${RED}失败: $FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ 所有测试通过！${NC}"
    exit 0
else
    echo -e "${RED}✗ 部分测试失败${NC}"
    exit 1
fi
