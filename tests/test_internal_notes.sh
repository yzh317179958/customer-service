#!/bin/bash

# ======================================================
# 内部备注功能测试脚本 v3.8.0
# ======================================================

BASE_URL="http://localhost:8000"
PASSED=0
FAILED=0

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================================"
echo "        内部备注功能测试 (模块5-P0)"
echo "======================================================"

# 检查后端健康状态
echo ""
echo "🔍 检查后端服务..."
HEALTH_CHECK=$(curl -s "$BASE_URL/api/health")
if echo "$HEALTH_CHECK" | grep -q '"status":"healthy"'; then
    echo -e "${GREEN}✅ 后端服务正常${NC}"
else
    echo -e "${RED}❌ 后端服务异常${NC}"
    exit 1
fi

# ===== 准备测试环境 =====
echo ""
echo "📋 准备测试环境..."

# 登录获取 Token
echo "  → 登录管理员账号..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/agent/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }')

ADMIN_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])" 2>/dev/null)

if [ -z "$ADMIN_TOKEN" ]; then
    echo -e "${RED}❌ 登录失败${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 登录成功${NC}"

# 创建测试会话
echo "  → 创建测试会话..."
TEST_SESSION="session_note_test_$(date +%s)"

# 使用 /api/manual/escalate 创建会话
ESCALATE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/manual/escalate" \
  -H "Content-Type: application/json" \
  -d "{
    \"session_name\": \"$TEST_SESSION\",
    \"reason\": \"manual\",
    \"details\": \"测试内部备注功能\",
    \"user_nickname\": \"测试用户\"
  }")

if echo "$ESCALATE_RESPONSE" | grep -q '"success":true'; then
    echo -e "${GREEN}✅ 测试会话已创建: $TEST_SESSION${NC}"
else
    echo -e "${RED}❌ 创建会话失败${NC}"
    echo "$ESCALATE_RESPONSE"
    exit 1
fi

# ===== 测试 1: 添加内部备注 =====
echo ""
echo "测试 1: 添加内部备注"
CREATE_NOTE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
  "$BASE_URL/api/sessions/$TEST_SESSION/notes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "content": "客户反馈电池续航问题，初步判断需要更换电池",
    "mentions": []
  }')

HTTP_CODE=$(echo "$CREATE_NOTE_RESPONSE" | tail -n1)
BODY=$(echo "$CREATE_NOTE_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 200 ]; then
    NOTE_ID=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null)
    if [ -n "$NOTE_ID" ]; then
        echo -e "${GREEN}✅ PASS - 添加备注成功，ID: $NOTE_ID${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL - 响应缺少备注ID${NC}"
        ((FAILED++))
    fi
else
    echo -e "${RED}❌ FAIL - HTTP $HTTP_CODE${NC}"
    echo "$BODY"
    ((FAILED++))
fi
((TOTAL=$PASSED+$FAILED))

# ===== 测试 2: 获取内部备注列表 =====
echo ""
echo "测试 2: 获取内部备注列表"
GET_NOTES_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET \
  "$BASE_URL/api/sessions/$TEST_SESSION/notes" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

HTTP_CODE=$(echo "$GET_NOTES_RESPONSE" | tail -n1)
BODY=$(echo "$GET_NOTES_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 200 ]; then
    NOTE_COUNT=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['total'])" 2>/dev/null)
    if [ "$NOTE_COUNT" -ge 1 ]; then
        echo -e "${GREEN}✅ PASS - 成功获取备注列表，共 $NOTE_COUNT 条${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL - 备注数量不正确${NC}"
        ((FAILED++))
    fi
else
    echo -e "${RED}❌ FAIL - HTTP $HTTP_CODE${NC}"
    ((FAILED++))
fi
((TOTAL=$PASSED+$FAILED))

# ===== 测试 3: 编辑内部备注 =====
echo ""
echo "测试 3: 编辑内部备注"
if [ -n "$NOTE_ID" ]; then
    UPDATE_NOTE_RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT \
      "$BASE_URL/api/sessions/$TEST_SESSION/notes/$NOTE_ID" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -d '{
        "content": "已指导客户检查电池连接，问题依旧。建议寄回检测",
        "mentions": []
      }')

    HTTP_CODE=$(echo "$UPDATE_NOTE_RESPONSE" | tail -n1)
    BODY=$(echo "$UPDATE_NOTE_RESPONSE" | head -n-1)

    if [ "$HTTP_CODE" -eq 200 ]; then
        UPDATED_CONTENT=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['content'])" 2>/dev/null)
        if echo "$UPDATED_CONTENT" | grep -q "寄回检测"; then
            echo -e "${GREEN}✅ PASS - 备注更新成功${NC}"
            ((PASSED++))
        else
            echo -e "${RED}❌ FAIL - 备注内容未更新${NC}"
            ((FAILED++))
        fi
    else
        echo -e "${RED}❌ FAIL - HTTP $HTTP_CODE${NC}"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}⊘ SKIP - 缺少备注ID${NC}"
fi
((TOTAL=$PASSED+$FAILED))

# ===== 测试 4: 权限验证（普通坐席只能编辑自己的备注）=====
echo ""
echo "测试 4: 权限验证"

# 登录另一个坐席
LOGIN_AGENT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/agent/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "agent001",
    "password": "agent123"
  }')

AGENT_TOKEN=$(echo "$LOGIN_AGENT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])" 2>/dev/null)

if [ -n "$AGENT_TOKEN" ] && [ -n "$NOTE_ID" ]; then
    # 尝试编辑其他坐席的备注（应该失败）
    UNAUTHORIZED_RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT \
      "$BASE_URL/api/sessions/$TEST_SESSION/notes/$NOTE_ID" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $AGENT_TOKEN" \
      -d '{
        "content": "尝试修改其他人的备注",
        "mentions": []
      }')

    HTTP_CODE=$(echo "$UNAUTHORIZED_RESPONSE" | tail -n1)

    if [ "$HTTP_CODE" -eq 403 ]; then
        echo -e "${GREEN}✅ PASS - 权限验证正确（禁止修改他人备注）${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL - 权限验证失败（HTTP $HTTP_CODE）${NC}"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}⊘ SKIP - 缺少坐席Token或备注ID${NC}"
fi
((TOTAL=$PASSED+$FAILED))

# ===== 测试 5: 删除内部备注 =====
echo ""
echo "测试 5: 删除内部备注"
if [ -n "$NOTE_ID" ]; then
    DELETE_NOTE_RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE \
      "$BASE_URL/api/sessions/$TEST_SESSION/notes/$NOTE_ID" \
      -H "Authorization: Bearer $ADMIN_TOKEN")

    HTTP_CODE=$(echo "$DELETE_NOTE_RESPONSE" | tail -n1)

    if [ "$HTTP_CODE" -eq 200 ]; then
        echo -e "${GREEN}✅ PASS - 备注删除成功${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL - HTTP $HTTP_CODE${NC}"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}⊘ SKIP - 缺少备注ID${NC}"
fi
((TOTAL=$PASSED+$FAILED))

# ===== 测试 6: 验证删除后列表为空 =====
echo ""
echo "测试 6: 验证删除后列表"
GET_NOTES_AFTER_DELETE=$(curl -s -w "\n%{http_code}" -X GET \
  "$BASE_URL/api/sessions/$TEST_SESSION/notes" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

HTTP_CODE=$(echo "$GET_NOTES_AFTER_DELETE" | tail -n1)
BODY=$(echo "$GET_NOTES_AFTER_DELETE" | head -n-1)

if [ "$HTTP_CODE" -eq 200 ]; then
    NOTE_COUNT=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['total'])" 2>/dev/null)
    if [ "$NOTE_COUNT" -eq 0 ]; then
        echo -e "${GREEN}✅ PASS - 备注列表为空${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL - 备注未被删除${NC}"
        ((FAILED++))
    fi
else
    echo -e "${RED}❌ FAIL - HTTP $HTTP_CODE${NC}"
    ((FAILED++))
fi
((TOTAL=$PASSED+$FAILED))

# ===== 测试总结 =====
echo ""
echo "======================================================"
echo "                  测试结果汇总"
echo "======================================================"
echo ""
echo "总测试数: $TOTAL"
echo -e "通过: ${GREEN}$PASSED${NC}"
echo -e "失败: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}======================================================"
    echo "        ✅ 所有测试通过！"
    echo -e "======================================================${NC}"
    exit 0
else
    echo -e "${RED}======================================================"
    echo "        ❌ 部分测试失败"
    echo -e "======================================================${NC}"
    exit 1
fi
