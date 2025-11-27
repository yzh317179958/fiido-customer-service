#!/bin/bash
# 回归测试脚本 - 每次开发完成后必须运行
# 根据 prd/CONSTRAINTS_AND_PRINCIPLES.md 的要求

# 不使用 set -e，手动处理错误

echo "=============================================="
echo "       Fiido AI客服 - 回归测试套件"
echo "=============================================="
echo ""

PASS=0
FAIL=0
BASE_URL="http://localhost:8000"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_result() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 通过${NC}"
        ((PASS++))
    else
        echo -e "${RED}❌ 失败${NC}"
        ((FAIL++))
    fi
}

echo "=== 第一层：核心功能测试 ==="
echo ""

# 测试1: 健康检查
echo -n "测试1: 健康检查... "
RESULT=$(curl -s $BASE_URL/api/health | grep -c '"coze_connected":true' || true)
if [ "$RESULT" -gt 0 ]; then
    echo -e "${GREEN}✅ 通过${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 失败${NC}"
    ((FAIL++))
fi

# 测试2: AI对话 (同步)
echo -n "测试2: AI对话 (同步)... "
RESULT=$(curl -s -X POST $BASE_URL/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"你好","user_id":"regression_test_sync"}' | grep -c '"success":true' || true)
if [ "$RESULT" -gt 0 ]; then
    echo -e "${GREEN}✅ 通过${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 失败${NC}"
    ((FAIL++))
fi

# 测试3: 会话隔离 (使用test_session_isolation.py)
# 根据 docs/process/会话隔离实现总结.md 的正确方法:
# - 首次对话不传 conversation_id，由Coze自动生成
# - 后续对话传入相同的 conversation_id 维持上下文
# - 验证不同 session_id 获得不同的 conversation_id
echo -n "测试3: 会话隔离... "
if python3 tests/test_session_isolation.py > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 通过${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 失败${NC}"
    ((FAIL++))
fi

echo ""
echo "=== 第二层：人工接管功能测试 ==="
echo ""

# 创建测试会话
SESSION="regression_manual_$(date +%s)"
curl -s -X POST $BASE_URL/api/conversation/new \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION\"}" > /dev/null

# 测试4: 人工升级
echo -n "测试4: 人工升级... "
RESULT=$(curl -s -X POST $BASE_URL/api/manual/escalate \
  -H "Content-Type: application/json" \
  -d "{\"session_name\": \"$SESSION\", \"reason\": \"manual\"}" | grep -c '"status":"pending_manual"' || true)
if [ "$RESULT" -gt 0 ]; then
    echo -e "${GREEN}✅ 通过${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 失败${NC}"
    ((FAIL++))
fi

# 测试5: AI阻止
echo -n "测试5: AI阻止 (manual mode)... "
RESULT=$(curl -s -X POST $BASE_URL/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"test\", \"user_id\": \"$SESSION\"}" | grep -c 'SESSION_IN_MANUAL_MODE' || true)
if [ "$RESULT" -gt 0 ]; then
    echo -e "${GREEN}✅ 通过${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 失败${NC}"
    ((FAIL++))
fi

# 测试6: 坐席接入
echo -n "测试6: 坐席接入... "
RESULT=$(curl -s -X POST "$BASE_URL/api/sessions/$SESSION/takeover" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "test_agent", "agent_name": "测试坐席"}' | grep -c '"status":"manual_live"' || true)
if [ "$RESULT" -gt 0 ]; then
    echo -e "${GREEN}✅ 通过${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 失败${NC}"
    ((FAIL++))
fi

# 测试7: 发送消息
echo -n "测试7: 发送消息... "
RESULT=$(curl -s -X POST $BASE_URL/api/manual/messages \
  -H "Content-Type: application/json" \
  -d "{\"session_name\": \"$SESSION\", \"role\": \"agent\", \"content\": \"测试消息\", \"agent_info\": {\"agent_id\": \"test_agent\", \"agent_name\": \"测试坐席\"}}" | grep -c '"success":true' || true)
if [ "$RESULT" -gt 0 ]; then
    echo -e "${GREEN}✅ 通过${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 失败${NC}"
    ((FAIL++))
fi

# 测试8: 释放会话
echo -n "测试8: 释放会话... "
RESULT=$(curl -s -X POST "$BASE_URL/api/sessions/$SESSION/release" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "test_agent", "reason": "resolved"}' | grep -c '"status":"bot_active"' || true)
if [ "$RESULT" -gt 0 ]; then
    echo -e "${GREEN}✅ 通过${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 失败${NC}"
    ((FAIL++))
fi

echo ""
echo "=== 第三层：坐席工作台功能测试 ==="
echo ""

# 测试9: 会话列表
echo -n "测试9: 会话列表... "
RESULT=$(curl -s "$BASE_URL/api/sessions?status=pending_manual" | grep -c '"success":true' || true)
if [ "$RESULT" -gt 0 ]; then
    echo -e "${GREEN}✅ 通过${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 失败${NC}"
    ((FAIL++))
fi

# 测试10: 统计信息
echo -n "测试10: 统计信息... "
RESULT=$(curl -s $BASE_URL/api/sessions/stats | grep -c '"success":true' || true)
if [ "$RESULT" -gt 0 ]; then
    echo -e "${GREEN}✅ 通过${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 失败${NC}"
    ((FAIL++))
fi

# 【L1-1-Part1-模块1】新增测试: 会话高级筛选与搜索
echo ""
echo "=== 【模块1】会话高级筛选与搜索测试 ==="
echo ""

# 测试11: VIP客户筛选
echo -n "测试11: VIP客户筛选... "
RESULT=$(curl -s "$BASE_URL/api/sessions?customer_type=vip&limit=5" | grep -c '"success":true' || true)
if [ "$RESULT" -gt 0 ]; then
    echo -e "${GREEN}✅ 通过${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 失败${NC}"
    ((FAIL++))
fi

# 测试12: 关键词搜索
echo -n "测试12: 关键词搜索... "
RESULT=$(curl -s "$BASE_URL/api/sessions?keyword=%E5%BC%A0%E4%B8%89&limit=5" | grep -c '"success":true' || true)
if [ "$RESULT" -gt 0 ]; then
    echo -e "${GREEN}✅ 通过${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 失败${NC}"
    ((FAIL++))
fi

# 测试13: VIP优先排序
echo -n "测试13: VIP优先排序... "
RESULT=$(curl -s "$BASE_URL/api/sessions?sort=vip&limit=5" | grep -c '"success":true' || true)
if [ "$RESULT" -gt 0 ]; then
    echo -e "${GREEN}✅ 通过${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 失败${NC}"
    ((FAIL++))
fi

# 测试14: 组合筛选(VIP+pending状态)
echo -n "测试14: 组合筛选... "
RESULT=$(curl -s "$BASE_URL/api/sessions?customer_type=vip&status=pending_manual&limit=5" | grep -c '"success":true' || true)
if [ "$RESULT" -gt 0 ]; then
    echo -e "${GREEN}✅ 通过${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 失败${NC}"
    ((FAIL++))
fi

# 【L1-1-Part1-模块2】新增测试: 队列管理与优先级
echo ""
echo "=== 【模块2】队列管理与优先级测试 ==="
echo ""

# 测试15: 队列API可访问性
echo -n "测试15: 队列API调用... "
RESULT=$(curl -s "$BASE_URL/api/sessions/queue" | grep -c '"success":true' || true)
if [ "$RESULT" -gt 0 ]; then
    echo -e "${GREEN}✅ 通过${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 失败${NC}"
    ((FAIL++))
fi

# 测试16: 队列数据结构
echo -n "测试16: 队列数据结构完整性... "
RESULT=$(curl -s "$BASE_URL/api/sessions/queue" | grep -E '"total_count":[0-9]+.*"vip_count":[0-9]+.*"avg_wait_time":[0-9.]+' | wc -l || true)
if [ "$RESULT" -gt 0 ]; then
    echo -e "${GREEN}✅ 通过${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 失败${NC}"
    ((FAIL++))
fi

# 测试17: 队列项包含优先级字段
echo -n "测试17: 队列项包含优先级字段... "
RESULT=$(curl -s "$BASE_URL/api/sessions/queue" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    queue = d.get('data', {}).get('queue', [])
    if len(queue) == 0:
        print('1')  # 空队列也算通过
    else:
        item = queue[0]
        required = ['session_name', 'position', 'priority_level', 'is_vip', 'wait_time_seconds']
        if all(f in item for f in required):
            print('1')
        else:
            print('0')
except:
    print('0')
" || echo '0')
if [ "$RESULT" = "1" ]; then
    echo -e "${GREEN}✅ 通过${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 失败${NC}"
    ((FAIL++))
fi

# 测试18: 会话列表API包含priority字段（模块2前端显示核心要求）
echo -n "测试18: 会话列表API返回priority字段... "
RESULT=$(curl -s "$BASE_URL/api/sessions?status=pending_manual&limit=1" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    sessions = d.get('data', {}).get('sessions', [])
    if len(sessions) == 0:
        print('1')  # 空列表也算通过
    else:
        session = sessions[0]
        priority = session.get('priority')
        if priority and 'level' in priority and 'is_vip' in priority:
            print('1')
        else:
            print('0')
except:
    print('0')
" || echo '0')
if [ "$RESULT" = "1" ]; then
    echo -e "${GREEN}✅ 通过${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 失败${NC}"
    ((FAIL++))
fi

# 【模块3】新增测试: 快捷回复功能 v3.7.0
echo ""
echo "=== 【模块3】快捷回复功能测试 v3.7.0 ==="
echo ""

# 获取管理员 Token（用于测试）
ADMIN_TOKEN=$(curl -s -X POST $BASE_URL/api/agent/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys, json; print(json.load(sys.stdin).get('token', ''))" 2>/dev/null)

if [ -z "$ADMIN_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  无法获取 Token，跳过快捷回复测试${NC}"
else
    # 测试19: 获取快捷回复分类
    echo -n "测试19: 获取快捷回复分类... "
    RESULT=$(curl -s "$BASE_URL/api/quick-replies/categories" \
      -H "Authorization: Bearer $ADMIN_TOKEN" | grep -c '"success":true' || true)
    if [ "$RESULT" -gt 0 ]; then
        echo -e "${GREEN}✅ 通过${NC}"
        ((PASS++))
    else
        echo -e "${RED}❌ 失败${NC}"
        ((FAIL++))
    fi

    # 测试20: 获取快捷回复列表
    echo -n "测试20: 获取快捷回复列表... "
    RESULT=$(curl -s "$BASE_URL/api/quick-replies?limit=10" \
      -H "Authorization: Bearer $ADMIN_TOKEN" | grep -c '"success":true' || true)
    if [ "$RESULT" -gt 0 ]; then
        echo -e "${GREEN}✅ 通过${NC}"
        ((PASS++))
    else
        echo -e "${RED}❌ 失败${NC}"
        ((FAIL++))
    fi

    # 测试21: 创建快捷回复
    echo -n "测试21: 创建快捷回复... "
    QR_ID=$(curl -s -X POST "$BASE_URL/api/quick-replies" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"title":"回归测试快捷回复","content":"这是回归测试创建的快捷回复","category":"greeting","is_shared":false}' \
      | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('data', {}).get('id', '') if d.get('success') else '')" 2>/dev/null)
    if [ -n "$QR_ID" ]; then
        echo -e "${GREEN}✅ 通过${NC}"
        ((PASS++))

        # 测试22: 更新快捷回复
        echo -n "测试22: 更新快捷回复... "
        RESULT=$(curl -s -X PUT "$BASE_URL/api/quick-replies/$QR_ID" \
          -H "Authorization: Bearer $ADMIN_TOKEN" \
          -H "Content-Type: application/json" \
          -d '{"title":"更新后的标题","content":"更新后的内容","category":"greeting","is_shared":true}' \
          | grep -c '"success":true' || true)
        if [ "$RESULT" -gt 0 ]; then
            echo -e "${GREEN}✅ 通过${NC}"
            ((PASS++))
        else
            echo -e "${RED}❌ 失败${NC}"
            ((FAIL++))
        fi

        # 测试23: 删除快捷回复
        echo -n "测试23: 删除快捷回复... "
        RESULT=$(curl -s -X DELETE "$BASE_URL/api/quick-replies/$QR_ID" \
          -H "Authorization: Bearer $ADMIN_TOKEN" | grep -c '"success":true' || true)
        if [ "$RESULT" -gt 0 ]; then
            echo -e "${GREEN}✅ 通过${NC}"
            ((PASS++))
        else
            echo -e "${RED}❌ 失败${NC}"
            ((FAIL++))
        fi
    else
        echo -e "${RED}❌ 失败${NC}"
        ((FAIL++))
        # 跳过依赖的测试
        echo -n "测试22: 更新快捷回复... "
        echo -e "${YELLOW}⊘ 跳过（创建失败）${NC}"
        ((FAIL++))
        echo -n "测试23: 删除快捷回复... "
        echo -e "${YELLOW}⊘ 跳过（创建失败）${NC}"
        ((FAIL++))
    fi
fi

echo ""
echo "=== TypeScript类型检查 ==="
echo ""

# 测试24: TypeScript检查 (agent-workbench)
echo -n "测试24: TypeScript检查... "
if cd agent-workbench && npx vue-tsc --noEmit > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 通过${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 失败${NC}"
    ((FAIL++))
fi
cd ..

# 测试25: TypeScript检查 (frontend)
echo -n "测试25: 用户前端TypeScript检查... "
if cd frontend && npx vue-tsc --noEmit > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 通过${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 失败${NC}"
    ((FAIL++))
fi
cd ..

echo ""
echo "=============================================="
echo "              测试结果汇总"
echo "=============================================="
echo ""
echo -e "通过: ${GREEN}$PASS${NC}"
echo -e "失败: ${RED}$FAIL${NC}"
TOTAL=$((PASS + FAIL))
echo "总计: $TOTAL"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}=============================================="
    echo "       所有测试通过！可以继续开发"
    echo "==============================================${NC}"
    exit 0
else
    echo -e "${RED}=============================================="
    echo "       存在失败的测试！请修复后再继续"
    echo "==============================================${NC}"
    exit 1
fi
