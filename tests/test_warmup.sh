#!/bin/bash
# ============================================================
# Shopify 缓存预热功能测试脚本
# 版本: v4.2.0
# ============================================================

set -e

BASE_URL="${BASE_URL:-http://localhost:8000}"
PASSED=0
FAILED=0

echo "========================================"
echo "🔥 Shopify 缓存预热功能测试"
echo "========================================"
echo "Base URL: $BASE_URL"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试函数
test_api() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local expected_status="$4"
    local check_field="$5"

    echo -n "测试: $name... "

    if [ "$method" = "GET" ]; then
        RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    else
        RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$endpoint")
    fi

    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    if [ "$HTTP_CODE" = "$expected_status" ]; then
        if [ -n "$check_field" ]; then
            if echo "$BODY" | grep -q "$check_field"; then
                echo -e "${GREEN}✅ PASS${NC}"
                ((PASSED++))
            else
                echo -e "${RED}❌ FAIL${NC} - 响应缺少字段: $check_field"
                echo "   响应: $BODY"
                ((FAILED++))
            fi
        else
            echo -e "${GREEN}✅ PASS${NC}"
            ((PASSED++))
        fi
    else
        echo -e "${RED}❌ FAIL${NC} - 预期 $expected_status, 实际 $HTTP_CODE"
        echo "   响应: $BODY"
        ((FAILED++))
    fi
}

# ==================== 测试开始 ====================

echo ""
echo "--- 1. 预热状态 API 测试 ---"
test_api "GET /api/warmup/status" "GET" "/api/warmup/status" "200" "success"

echo ""
echo "--- 2. 预热历史 API 测试 ---"
test_api "GET /api/warmup/history" "GET" "/api/warmup/history" "200" "success"

echo ""
echo "--- 3. 手动触发预热 API 测试 ---"
test_api "POST /api/warmup/trigger (增量)" "POST" "/api/warmup/trigger?warmup_type=incremental" "200" "success"

# 等待2秒让任务启动
sleep 2

echo ""
echo "--- 4. 停止预热 API 测试 ---"
test_api "POST /api/warmup/stop" "POST" "/api/warmup/stop" "200" "success"

echo ""
echo "--- 5. 再次获取状态（验证历史记录） ---"
test_api "GET /api/warmup/status (验证)" "GET" "/api/warmup/status" "200" "last_warmup"

# ==================== 缓存 TTL 验证 ====================

echo ""
echo "--- 6. 缓存 TTL 配置验证 ---"
echo -n "验证缓存 TTL 配置... "

TTL_CHECK=$(python3 -c "
from src.shopify_uk_cache import ShopifyUKCache
cache = ShopifyUKCache.__new__(ShopifyUKCache)
ttl = cache.DEFAULT_TTL

# 验证 TTL 值
assert ttl['order_detail'] == 172800, f'order_detail TTL 错误: {ttl[\"order_detail\"]}'
assert ttl['order_search'] == 172800, f'order_search TTL 错误: {ttl[\"order_search\"]}'
assert ttl['tracking'] == 21600, f'tracking TTL 错误: {ttl[\"tracking\"]}'
print('OK')
" 2>&1)

if [ "$TTL_CHECK" = "OK" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}"
    echo "   错误: $TTL_CHECK"
    ((FAILED++))
fi

# ==================== 预热服务模块验证 ====================

echo ""
echo "--- 7. 预热服务模块验证 ---"
echo -n "验证预热服务模块... "

MODULE_CHECK=$(python3 -c "
from src.warmup_service import WarmupService, get_warmup_service
service = get_warmup_service()
status = service.get_status()

assert status['enabled'] == True, 'enabled should be True'
assert status['config']['order_days'] == 7, 'order_days should be 7'
assert status['config']['rate_limit'] == 0.5, 'rate_limit should be 0.5'
print('OK')
" 2>&1)

if [ "$MODULE_CHECK" = "OK" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}"
    echo "   错误: $MODULE_CHECK"
    ((FAILED++))
fi

# ==================== APScheduler 验证 ====================

echo ""
echo "--- 8. APScheduler 调度器验证 ---"
echo -n "验证调度器配置... "

SCHEDULER_CHECK=$(python3 -c "
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from src.warmup_service import get_warmup_service

warmup_service = get_warmup_service()
scheduler = AsyncIOScheduler()

# 添加测试任务
scheduler.add_job(
    warmup_service.full_warmup,
    CronTrigger(hour=2, minute=0),
    id='warmup_full',
    replace_existing=True
)

scheduler.add_job(
    warmup_service.incremental_warmup,
    CronTrigger(hour=8, minute=0),
    id='warmup_inc',
    replace_existing=True
)

jobs = scheduler.get_jobs()
assert len(jobs) == 2, f'Expected 2 jobs, got {len(jobs)}'
print('OK')
" 2>&1)

if [ "$SCHEDULER_CHECK" = "OK" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}"
    echo "   错误: $SCHEDULER_CHECK"
    ((FAILED++))
fi

# ==================== 测试结果汇总 ====================

echo ""
echo "========================================"
echo "📊 测试结果汇总"
echo "========================================"
echo -e "通过: ${GREEN}$PASSED${NC}"
echo -e "失败: ${RED}$FAILED${NC}"
TOTAL=$((PASSED + FAILED))
echo "总计: $TOTAL"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ 所有测试通过！${NC}"
    exit 0
else
    echo -e "${RED}❌ 存在失败的测试${NC}"
    exit 1
fi
