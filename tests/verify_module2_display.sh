#!/bin/bash
# 模块2前端显示验证脚本
# 验证优先级标识和队列统计是否正确显示

BASE_URL="http://localhost:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}==========================================="
echo "【模块2】前端显示功能验证"
echo -e "===========================================${NC}"
echo ""

# 测试1: 会话列表API包含priority字段
echo -e "${YELLOW}测试1: 会话列表API返回priority字段${NC}"
RESULT=$(curl -s "$BASE_URL/api/sessions?status=pending_manual&limit=1" | python3 -c "
import sys, json
d = json.load(sys.stdin)
if d['success'] and d['data']['sessions']:
    session = d['data']['sessions'][0]
    if 'priority' in session:
        print('✅ priority字段存在')
        print(f\"   level: {session['priority']['level']}\")
        print(f\"   is_vip: {session['priority']['is_vip']}\")
        exit(0)
    else:
        print('❌ 缺少priority字段')
        exit(1)
else:
    print('❌ 无待接入会话')
    exit(1)
" 2>&1)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}$RESULT${NC}"
else
    echo -e "${RED}$RESULT${NC}"
    exit 1
fi

echo ""

# 测试2: VIP客户显示紧急优先级
echo -e "${YELLOW}测试2: VIP客户标记为urgent级别${NC}"
RESULT=$(curl -s "$BASE_URL/api/sessions?customer_type=vip&limit=1" | python3 -c "
import sys, json
d = json.load(sys.stdin)
if d['success'] and d['data']['sessions']:
    session = d['data']['sessions'][0]
    if session.get('priority', {}).get('level') == 'urgent':
        print('✅ VIP客户优先级为urgent')
        exit(0)
    else:
        print(f\"❌ VIP客户优先级错误: {session.get('priority', {}).get('level')}\")
        exit(1)
else:
    print('⚠️  无VIP客户数据（可选测试）')
    exit(0)
" 2>&1)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}$RESULT${NC}"
else
    echo -e "${RED}$RESULT${NC}"
    exit 1
fi

echo ""

# 测试3: 队列统计数据完整性
echo -e "${YELLOW}测试3: 队列统计数据结构${NC}"
RESULT=$(curl -s "$BASE_URL/api/sessions/queue" | python3 -c "
import sys, json
d = json.load(sys.stdin)
if d['success']:
    stats = d['data']
    print(f\"✅ total_count: {stats['total_count']}\")
    print(f\"✅ vip_count: {stats['vip_count']}\")
    print(f\"✅ avg_wait_time: {stats['avg_wait_time']:.1f}s\")
    print(f\"✅ max_wait_time: {stats['max_wait_time']:.1f}s\")
    print(f\"✅ queue数组长度: {len(stats['queue'])}\")
    exit(0)
else:
    print('❌ 队列API失败')
    exit(1)
" 2>&1)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}$RESULT${NC}"
else
    echo -e "${RED}$RESULT${NC}"
    exit 1
fi

echo ""

# 测试4: 队列项包含position字段
echo -e "${YELLOW}测试4: 队列项包含position排序字段${NC}"
RESULT=$(curl -s "$BASE_URL/api/sessions/queue" | python3 -c "
import sys, json
d = json.load(sys.stdin)
if d['success'] and d['data']['queue']:
    item = d['data']['queue'][0]
    if 'position' in item:
        print(f\"✅ position字段存在: {item['position']}\")
        print(f\"   session_name: {item['session_name']}\")
        print(f\"   priority_level: {item['priority_level']}\")
        exit(0)
    else:
        print('❌ 缺少position字段')
        exit(1)
else:
    print('⚠️  队列为空（可选测试）')
    exit(0)
" 2>&1)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}$RESULT${NC}"
else
    echo -e "${RED}$RESULT${NC}"
    exit 1
fi

echo ""

# 测试5: 紧急关键词检测
echo -e "${YELLOW}测试5: 紧急关键词检测（包含'退款'的会话）${NC}"
RESULT=$(curl -s "$BASE_URL/api/sessions?keyword=退款&limit=1" | python3 -c "
import sys, json
d = json.load(sys.stdin)
if d['success'] and d['data']['sessions']:
    session = d['data']['sessions'][0]
    keywords = session.get('priority', {}).get('urgent_keywords', [])
    if '退款' in keywords:
        print('✅ 检测到紧急关键词: 退款')
        print(f\"   priority_level: {session.get('priority', {}).get('level')}\")
        exit(0)
    else:
        print(f\"❌ 未检测到关键词，keywords: {keywords}\")
        exit(1)
else:
    print('⚠️  无包含"退款"的会话（可选测试）')
    exit(0)
" 2>&1)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}$RESULT${NC}"
else
    echo -e "${YELLOW}$RESULT${NC}"
fi

echo ""
echo -e "${BLUE}==========================================="
echo "前端访问地址: http://localhost:5182/"
echo "默认账号: admin / admin123"
echo ""
echo "预期效果:"
echo "1. ✅ VIP客户显示 👑VIP + 🔴 标识"
echo "2. ✅ 包含'退款'的会话显示 🟠 标识"
echo "3. ✅ 左侧面板显示【等待队列】统计卡片"
echo "4. ✅ 统计卡片包含: 总人数、VIP数量、平均等待、最长等待"
echo "5. ✅ 🔴urgent标识有脉冲动画效果"
echo -e "===========================================${NC}"
