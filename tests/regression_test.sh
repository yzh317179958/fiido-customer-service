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

# 测试11: TypeScript检查 (agent-workbench)
echo -n "测试11: TypeScript检查... "
if cd agent-workbench && npx vue-tsc --noEmit > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 通过${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 失败${NC}"
    ((FAIL++))
fi
cd ..

# 测试12: TypeScript检查 (frontend)
echo -n "测试12: 用户前端TypeScript检查... "
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
