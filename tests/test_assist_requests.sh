#!/bin/bash
# 协助请求功能测试脚本
# 功能需求: prd/04_任务拆解/L1-1-Part3_协作与工作台优化.md F5.5

BASE_URL="http://localhost:8000"
PASSED=0
FAILED=0

echo "========================================"
echo "   【模块5】协助请求功能测试 v3.10.0"
echo "========================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 清理函数
cleanup() {
    rm -f /tmp/admin_token.txt /tmp/agent_token.txt /tmp/test_session.txt /tmp/request_id.txt
}

# 错误处理
trap cleanup EXIT

# ==================== 步骤1: 获取管理员Token ====================
echo "步骤1: 登录管理员账号..."
ADMIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/agent/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }')

ADMIN_TOKEN=$(echo "$ADMIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('token', ''))")

if [ -z "$ADMIN_TOKEN" ]; then
    echo -e "${RED}❌ 管理员登录失败${NC}"
    echo "$ADMIN_RESPONSE"
    exit 1
fi

echo "$ADMIN_TOKEN" > /tmp/admin_token.txt
echo -e "${GREEN}✅ 管理员登录成功${NC}"
echo ""

# ==================== 步骤2: 获取普通坐席Token ====================
echo "步骤2: 登录坐席账号 agent001..."
AGENT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/agent/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "agent001",
    "password": "agent123"
  }')

AGENT_TOKEN=$(echo "$AGENT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('token', ''))")

if [ -z "$AGENT_TOKEN" ]; then
    echo -e "${RED}❌ 坐席登录失败${NC}"
    echo "$AGENT_RESPONSE"
    exit 1
fi

echo "$AGENT_TOKEN" > /tmp/agent_token.txt
echo -e "${GREEN}✅ 坐席登录成功${NC}"
echo ""

# ==================== 步骤3: 创建测试会话 ====================
echo "步骤3: 创建测试会话..."
SESSION_NAME="test_assist_$(date +%s)"

# 触发会话创建（通过发送消息）
CHAT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"测试协助请求功能\",
    \"user_id\": \"$SESSION_NAME\"
  }")

echo "$SESSION_NAME" > /tmp/test_session.txt
echo -e "${GREEN}✅ 测试会话已创建: $SESSION_NAME${NC}"
echo ""

# 等待会话创建
sleep 1

# ==================== 测试1: 创建协助请求 - 正常场景 ====================
echo "测试1: 创建协助请求 - 正常场景"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/assist-requests" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AGENT_TOKEN" \
  -d "{
    \"session_name\": \"$SESSION_NAME\",
    \"assistant\": \"admin\",
    \"question\": \"客户询问电池保修期，我查不到政策，能否帮忙？\"
  }")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 200 ]; then
    # 验证返回数据
    SUCCESS=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))")
    REQUEST_ID=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('data', {}).get('id', ''))")

    if [ "$SUCCESS" == "True" ] && [ -n "$REQUEST_ID" ]; then
        echo -e "${GREEN}✅ PASS - 创建成功，请求ID: $REQUEST_ID${NC}"
        echo "$REQUEST_ID" > /tmp/request_id.txt
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL - 返回数据格式错误${NC}"
        echo "$BODY"
        ((FAILED++))
    fi
else
    echo -e "${RED}❌ FAIL - 预期200，实际$HTTP_CODE${NC}"
    echo "$BODY"
    ((FAILED++))
fi
echo ""

# 等待SSE推送
sleep 1

# ==================== 测试2: 获取协助请求列表 - 协助者视角 ====================
echo "测试2: 获取协助请求列表 - 协助者视角 (admin)"
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/assist-requests?status=pending" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 200 ]; then
    # 验证返回数据
    RECEIVED_COUNT=$(echo "$BODY" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('data', {}).get('received', [])))")
    PENDING_COUNT=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('count', {}).get('received_pending', 0))")

    if [ "$RECEIVED_COUNT" -ge 1 ] && [ "$PENDING_COUNT" -ge 1 ]; then
        echo -e "${GREEN}✅ PASS - 协助者收到 $RECEIVED_COUNT 个请求，待处理 $PENDING_COUNT 个${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL - 未收到协助请求${NC}"
        echo "$BODY"
        ((FAILED++))
    fi
else
    echo -e "${RED}❌ FAIL - 预期200，实际$HTTP_CODE${NC}"
    echo "$BODY"
    ((FAILED++))
fi
echo ""

# ==================== 测试3: 获取协助请求列表 - 请求者视角 ====================
echo "测试3: 获取协助请求列表 - 请求者视角 (agent001)"
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/assist-requests" \
  -H "Authorization: Bearer $AGENT_TOKEN")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 200 ]; then
    # 验证返回数据
    SENT_COUNT=$(echo "$BODY" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('data', {}).get('sent', [])))")

    if [ "$SENT_COUNT" -ge 1 ]; then
        echo -e "${GREEN}✅ PASS - 请求者发出了 $SENT_COUNT 个请求${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL - 未找到发出的请求${NC}"
        echo "$BODY"
        ((FAILED++))
    fi
else
    echo -e "${RED}❌ FAIL - 预期200，实际$HTTP_CODE${NC}"
    echo "$BODY"
    ((FAILED++))
fi
echo ""

# ==================== 测试4: 回复协助请求 - 正常场景 ====================
echo "测试4: 回复协助请求 - 正常场景"
REQUEST_ID=$(cat /tmp/request_id.txt)

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/assist-requests/$REQUEST_ID/answer" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "answer": "电池保修期是1年，可以在系统后台-产品管理-保修政策中查询。"
  }')

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 200 ]; then
    # 验证返回数据
    STATUS=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('data', {}).get('status', ''))")
    ANSWER=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('data', {}).get('answer', ''))")

    if [ "$STATUS" == "answered" ] && [ -n "$ANSWER" ]; then
        echo -e "${GREEN}✅ PASS - 回复成功，状态已更新为 answered${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL - 状态或答案错误${NC}"
        echo "$BODY"
        ((FAILED++))
    fi
else
    echo -e "${RED}❌ FAIL - 预期200，实际$HTTP_CODE${NC}"
    echo "$BODY"
    ((FAILED++))
fi
echo ""

# 等待SSE推送
sleep 1

# ==================== 测试5: 重复回复 - 应该失败 ====================
echo "测试5: 重复回复协助请求 - 应该失败（400）"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/assist-requests/$REQUEST_ID/answer" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "answer": "这是重复回复"
  }')

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 400 ]; then
    DETAIL=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('detail', ''))")

    if [[ "$DETAIL" == *"ALREADY_ANSWERED"* ]]; then
        echo -e "${GREEN}✅ PASS - 正确拒绝重复回复${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL - 错误消息不正确${NC}"
        echo "$BODY"
        ((FAILED++))
    fi
else
    echo -e "${RED}❌ FAIL - 预期400，实际$HTTP_CODE${NC}"
    echo "$BODY"
    ((FAILED++))
fi
echo ""

# ==================== 测试6: 权限检查 - 非协助者回复 ====================
echo "测试6: 权限检查 - 非协助者尝试回复 - 应该失败（403）"

# 先创建一个新请求（admin → agent001）
NEW_REQUEST=$(curl -s -X POST "$BASE_URL/api/assist-requests" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d "{
    \"session_name\": \"$SESSION_NAME\",
    \"assistant\": \"agent001\",
    \"question\": \"测试权限检查\"
  }")

NEW_REQUEST_ID=$(echo "$NEW_REQUEST" | python3 -c "import sys, json; print(json.load(sys.stdin).get('data', {}).get('id', ''))")

# 尝试用 admin 回复（但 admin 不是协助者）
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/assist-requests/$NEW_REQUEST_ID/answer" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "answer": "尝试非法回复"
  }')

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 403 ]; then
    DETAIL=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('detail', ''))")

    if [[ "$DETAIL" == *"PERMISSION_DENIED"* ]]; then
        echo -e "${GREEN}✅ PASS - 正确拒绝非协助者回复${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL - 错误消息不正确${NC}"
        echo "$BODY"
        ((FAILED++))
    fi
else
    echo -e "${RED}❌ FAIL - 预期403，实际$HTTP_CODE${NC}"
    echo "$BODY"
    ((FAILED++))
fi
echo ""

# ==================== 测试7: 不存在的协助者 ====================
echo "测试7: 创建协助请求 - 协助者不存在 - 应该失败（404）"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/assist-requests" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AGENT_TOKEN" \
  -d "{
    \"session_name\": \"$SESSION_NAME\",
    \"assistant\": \"nonexistent_agent\",
    \"question\": \"测试不存在的协助者\"
  }")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 404 ]; then
    DETAIL=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('detail', ''))")

    if [[ "$DETAIL" == *"ASSISTANT_NOT_FOUND"* ]]; then
        echo -e "${GREEN}✅ PASS - 正确拒绝不存在的协助者${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL - 错误消息不正确${NC}"
        echo "$BODY"
        ((FAILED++))
    fi
else
    echo -e "${RED}❌ FAIL - 预期404，实际$HTTP_CODE${NC}"
    echo "$BODY"
    ((FAILED++))
fi
echo ""

# ==================== 测试8: 状态筛选 ====================
echo "测试8: 获取已回复的协助请求（status=answered）"
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/assist-requests?status=answered" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 200 ]; then
    # 验证返回数据
    RECEIVED_COUNT=$(echo "$BODY" | python3 -c "import sys, json; data = json.load(sys.stdin).get('data', {}); print(len(data.get('received', [])))")

    # 检查是否所有返回的请求都是 answered 状态
    ALL_ANSWERED=$(echo "$BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin).get('data', {})
received = data.get('received', [])
print(all(r['status'] == 'answered' for r in received))
    ")

    if [ "$ALL_ANSWERED" == "True" ]; then
        echo -e "${GREEN}✅ PASS - 状态筛选正确，返回 $RECEIVED_COUNT 个已回复请求${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL - 状态筛选错误，包含非 answered 请求${NC}"
        echo "$BODY"
        ((FAILED++))
    fi
else
    echo -e "${RED}❌ FAIL - 预期200，实际$HTTP_CODE${NC}"
    echo "$BODY"
    ((FAILED++))
fi
echo ""

# ==================== 测试总结 ====================
echo "========================================"
echo "总测试: $((PASSED + FAILED))"
echo -e "${GREEN}通过: $PASSED${NC}"
echo -e "${RED}失败: $FAILED${NC}"
echo "========================================"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ 所有协助请求功能测试通过！${NC}"
    exit 0
else
    echo -e "${RED}❌ 存在失败的测试${NC}"
    exit 1
fi
