#!/bin/bash

# 管理员功能 API 测试脚本
# 测试所有管理员 API 的权限验证和功能

set -e  # 遇到错误立即退出

BASE_URL="http://localhost:8000"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "🔐 管理员功能 API 测试"
echo "========================================"
echo ""

# 测试计数器
PASSED=0
FAILED=0

# 测试辅助函数
test_api() {
    local test_name=$1
    local method=$2
    local endpoint=$3
    local auth_header=$4
    local data=$5
    local expected_code=$6

    echo -n "测试: $test_name... "

    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$endpoint" $auth_header)
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$endpoint" $auth_header \
            -H "Content-Type: application/json" \
            -d "$data")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "$expected_code" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (期望 HTTP $expected_code, 实际 $http_code)"
        echo "响应内容: $body"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

echo "步骤 1: 管理员登录获取 Token"
echo "----------------------------------------"

LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/agent/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin123"}')

ADMIN_TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$ADMIN_TOKEN" ]; then
    echo -e "${RED}❌ 管理员登录失败${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 管理员登录成功${NC}"
echo "Token: ${ADMIN_TOKEN:0:50}..."
echo ""

echo "步骤 2: 普通坐席登录获取 Token"
echo "----------------------------------------"

AGENT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/agent/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"agent001","password":"agent123"}')

AGENT_TOKEN=$(echo $AGENT_RESPONSE | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$AGENT_TOKEN" ]; then
    echo -e "${RED}❌ 坐席登录失败${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 坐席登录成功${NC}"
echo "Token: ${AGENT_TOKEN:0:50}..."
echo ""

echo "步骤 3: 权限验证测试"
echo "----------------------------------------"

# 测试 1: 无 Token 访问 (FastAPI HTTPBearer 返回 403 Not authenticated)
test_api "无 Token 访问管理员 API" \
    "GET" "/api/agents" "" "" "403"

# 测试 2: 普通坐席 Token 访问 (应该返回 403)
response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/agents" \
    -H "Authorization: Bearer $AGENT_TOKEN")
http_code=$(echo "$response" | tail -n1)
echo -n "测试: 普通坐席访问管理员 API... "
if [ "$http_code" = "403" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} (期望 HTTP 403, 实际 $http_code)"
    FAILED=$((FAILED + 1))
fi

# 测试 3: 管理员 Token 访问 (应该返回 200)
response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/agents?page=1&page_size=10" \
    -H "Authorization: Bearer $ADMIN_TOKEN")
http_code=$(echo "$response" | tail -n1)
echo -n "测试: 管理员访问 API - 列表查询... "
if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} (期望 HTTP 200, 实际 $http_code)"
    body=$(echo "$response" | sed '$d')
    echo "响应内容: $body"
    FAILED=$((FAILED + 1))
fi

echo ""
echo "步骤 4: 管理员功能测试"
echo "----------------------------------------"

# 测试 4: 创建坐席
NEW_AGENT_DATA='{
  "username": "test_agent_'$(date +%s)'",
  "password": "test123456",
  "name": "测试坐席",
  "role": "agent",
  "max_sessions": 5
}'

response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/agents" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$NEW_AGENT_DATA")
http_code=$(echo "$response" | tail -n1)
echo -n "测试: 创建坐席账号... "
if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} (期望 HTTP 200, 实际 $http_code)"
    body=$(echo "$response" | sed '$d')
    echo "响应内容: $body"
    FAILED=$((FAILED + 1))
fi

# 提取创建的用户名 (从响应中提取更可靠)
NEW_USERNAME=$(echo "$response" | sed '$d' | grep -o '"username": *"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"/\1/')
if [ -z "$NEW_USERNAME" ]; then
    # 备用方案:从请求数据提取
    NEW_USERNAME=$(echo "$NEW_AGENT_DATA" | grep -o '"username": *"[^"]*"' | sed 's/.*"\([^"]*\)"/\1/')
fi
echo "DEBUG: 提取到的用户名: $NEW_USERNAME"

# 测试 5: 修改坐席信息
UPDATE_DATA='{"name": "测试坐席(已修改)", "max_sessions": 10}'

response=$(curl -s -w "\n%{http_code}" -X PUT "$BASE_URL/api/agents/$NEW_USERNAME" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$UPDATE_DATA")
http_code=$(echo "$response" | tail -n1)
echo -n "测试: 修改坐席信息... "
if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} (期望 HTTP 200, 实际 $http_code)"
    body=$(echo "$response" | sed '$d')
    echo "响应内容: $body"
    FAILED=$((FAILED + 1))
fi

# 测试 6: 重置密码
RESET_PASSWORD_DATA='{"new_password": "new_password_123"}'

response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/agents/$NEW_USERNAME/reset-password" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$RESET_PASSWORD_DATA")
http_code=$(echo "$response" | tail -n1)
echo -n "测试: 重置坐席密码... "
if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} (期望 HTTP 200, 实际 $http_code)"
    body=$(echo "$response" | sed '$d')
    echo "响应内容: $body"
    FAILED=$((FAILED + 1))
fi

# 测试 7: 删除坐席
response=$(curl -s -w "\n%{http_code}" -X DELETE "$BASE_URL/api/agents/$NEW_USERNAME" \
    -H "Authorization: Bearer $ADMIN_TOKEN")
http_code=$(echo "$response" | tail -n1)
echo -n "测试: 删除坐席账号... "
if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} (期望 HTTP 200, 实际 $http_code)"
    body=$(echo "$response" | sed '$d')
    echo "响应内容: $body"
    FAILED=$((FAILED + 1))
fi

echo ""
echo "步骤 5: 边界条件测试"
echo "----------------------------------------"

# 测试 8: 创建重复用户名
DUPLICATE_DATA='{"username":"admin","password":"test123456","name":"重复用户","role":"agent","max_sessions":5}'

response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/agents" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$DUPLICATE_DATA")
http_code=$(echo "$response" | tail -n1)
echo -n "测试: 创建重复用户名 (应该失败)... "
if [ "$http_code" = "400" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} (期望 HTTP 400, 实际 $http_code)"
    body=$(echo "$response" | sed '$d')
    echo "响应内容: $body"
    FAILED=$((FAILED + 1))
fi

# 测试 9: 删除不存在的用户
response=$(curl -s -w "\n%{http_code}" -X DELETE "$BASE_URL/api/agents/nonexistent_user_99999" \
    -H "Authorization: Bearer $ADMIN_TOKEN")
http_code=$(echo "$response" | tail -n1)
echo -n "测试: 删除不存在的用户 (应该失败)... "
if [ "$http_code" = "404" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} (期望 HTTP 404, 实际 $http_code)"
    body=$(echo "$response" | sed '$d')
    echo "响应内容: $body"
    FAILED=$((FAILED + 1))
fi

# 测试 10: 弱密码验证
WEAK_PASSWORD_DATA='{"username":"weak_test","password":"123","name":"弱密码测试","role":"agent","max_sessions":5}'

response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/agents" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$WEAK_PASSWORD_DATA")
http_code=$(echo "$response" | tail -n1)
echo -n "测试: 创建弱密码账号 (应该失败)... "
# 接受 400 (业务验证) 或 422 (Pydantic 字段验证)
if [ "$http_code" = "400" ] || [ "$http_code" = "422" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} (期望 HTTP 400/422, 实际 $http_code)"
    body=$(echo "$response" | sed '$d')
    echo "响应内容: $body"
    FAILED=$((FAILED + 1))
fi

echo ""
echo "========================================"
echo "📊 测试结果统计"
echo "========================================"
echo -e "${GREEN}通过: $PASSED${NC}"
echo -e "${RED}失败: $FAILED${NC}"
echo "总计: $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ 所有测试通过！${NC}"
    exit 0
else
    echo -e "${RED}✗ 有 $FAILED 个测试失败${NC}"
    exit 1
fi
