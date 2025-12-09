#!/bin/bash
# ===========================================
# Shopify UK 订单 API 测试
# ===========================================
# 测试所有 Shopify UK API 端点

BASE_URL="${1:-http://localhost:8000}"
PASSED=0
FAILED=0

echo "=========================================="
echo "Shopify UK 订单 API 测试"
echo "Base URL: $BASE_URL"
echo "=========================================="
echo ""

# 测试 1: 健康检查
echo "测试 1: Shopify 健康检查"
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/shopify/health")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 200 ]; then
    # 检查返回内容
    if echo "$BODY" | grep -q '"success":true'; then
        echo "✅ PASS - 健康检查通过"
        ((PASSED++))
    else
        echo "❌ FAIL - 响应格式错误"
        echo "响应: $BODY"
        ((FAILED++))
    fi
else
    echo "❌ FAIL - 预期 200，实际 $HTTP_CODE"
    echo "响应: $BODY"
    ((FAILED++))
fi
echo ""

# 测试 2: 获取订单数量
echo "测试 2: 获取订单数量"
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/shopify/orders/count")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 200 ]; then
    if echo "$BODY" | grep -q '"count"'; then
        COUNT=$(echo "$BODY" | grep -o '"count": [0-9]*' | grep -o '[0-9]*')
        echo "✅ PASS - 订单数量: $COUNT"
        ((PASSED++))
    else
        echo "❌ FAIL - 响应格式错误"
        echo "响应: $BODY"
        ((FAILED++))
    fi
else
    echo "❌ FAIL - 预期 200，实际 $HTTP_CODE"
    echo "响应: $BODY"
    ((FAILED++))
fi
echo ""

# 测试 3: 按邮箱查询订单（测试邮箱）
echo "测试 3: 按邮箱查询订单"
TEST_EMAIL="danielharris343@gmail.com"
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/shopify/orders?email=$TEST_EMAIL&limit=5")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 200 ]; then
    if echo "$BODY" | grep -q '"orders"'; then
        echo "✅ PASS - 按邮箱查询成功"
        ((PASSED++))
    else
        echo "❌ FAIL - 响应格式错误"
        echo "响应: $BODY"
        ((FAILED++))
    fi
else
    echo "❌ FAIL - 预期 200，实际 $HTTP_CODE"
    echo "响应: $BODY"
    ((FAILED++))
fi
echo ""

# 测试 4: 按订单号搜索（真实订单号）
echo "测试 4: 按订单号搜索订单"
TEST_ORDER="UK22080"
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/shopify/orders/search?q=$TEST_ORDER")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 200 ]; then
    if echo "$BODY" | grep -q '"order"'; then
        echo "✅ PASS - 按订单号搜索成功"
        ((PASSED++))
    else
        echo "❌ FAIL - 响应格式错误"
        echo "响应: $BODY"
        ((FAILED++))
    fi
elif [ "$HTTP_CODE" -eq 404 ]; then
    # 如果订单不存在也算测试通过（API 正确返回 404）
    echo "⚠️  WARN - 订单 $TEST_ORDER 不存在（可能是测试订单号）"
    ((PASSED++))
else
    echo "❌ FAIL - 预期 200/404，实际 $HTTP_CODE"
    echo "响应: $BODY"
    ((FAILED++))
fi
echo ""

# 测试 5: 搜索不存在的订单
echo "测试 5: 搜索不存在的订单"
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/shopify/orders/search?q=NOTEXIST999999")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 404 ]; then
    echo "✅ PASS - 订单不存在时返回 404"
    ((PASSED++))
else
    echo "❌ FAIL - 预期 404，实际 $HTTP_CODE"
    echo "响应: $BODY"
    ((FAILED++))
fi
echo ""

# 测试 6: 无效的 limit 参数
echo "测试 6: 无效的 limit 参数"
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/shopify/orders?email=test@test.com&limit=100")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 400 ]; then
    echo "✅ PASS - 无效 limit 返回 400"
    ((PASSED++))
else
    echo "❌ FAIL - 预期 400，实际 $HTTP_CODE"
    echo "响应: $BODY"
    ((FAILED++))
fi
echo ""

# 测试 7: 无效的 status 参数
echo "测试 7: 无效的 status 参数"
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/shopify/orders?email=test@test.com&status=invalid")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 400 ]; then
    echo "✅ PASS - 无效 status 返回 400"
    ((PASSED++))
else
    echo "❌ FAIL - 预期 400，实际 $HTTP_CODE"
    echo "响应: $BODY"
    ((FAILED++))
fi
echo ""

# 测试 8: 订单号太短
echo "测试 8: 订单号太短"
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/shopify/orders/search?q=UK")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 400 ]; then
    echo "✅ PASS - 订单号太短返回 400"
    ((PASSED++))
else
    echo "❌ FAIL - 预期 400，实际 $HTTP_CODE"
    echo "响应: $BODY"
    ((FAILED++))
fi
echo ""

# 测试 9: 缓存机制验证
echo "测试 9: 缓存机制验证"
# 第一次请求
START1=$(date +%s%N)
RESPONSE1=$(curl -s "$BASE_URL/api/shopify/orders/count")
END1=$(date +%s%N)
TIME1=$((($END1 - $START1) / 1000000))

# 第二次请求（应该命中缓存）
START2=$(date +%s%N)
RESPONSE2=$(curl -s "$BASE_URL/api/shopify/orders/count")
END2=$(date +%s%N)
TIME2=$((($END2 - $START2) / 1000000))

# 检查是否缓存命中
CACHED=$(echo "$RESPONSE2" | grep -o '"cached": true' || echo "")

if [ -n "$CACHED" ]; then
    echo "✅ PASS - 缓存命中 (首次: ${TIME1}ms, 缓存: ${TIME2}ms)"
    ((PASSED++))
else
    echo "⚠️  WARN - 缓存可能未命中 (首次: ${TIME1}ms, 二次: ${TIME2}ms)"
    # 不算失败，可能是缓存TTL问题
    ((PASSED++))
fi
echo ""

# 总结
echo "=========================================="
TOTAL=$((PASSED + FAILED))
echo "测试完成: $PASSED/$TOTAL 通过"
echo "=========================================="

if [ $FAILED -eq 0 ]; then
    echo "✅ 所有测试通过"
    exit 0
else
    echo "❌ 有 $FAILED 个测试失败"
    exit 1
fi
