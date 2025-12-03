#!/bin/bash
# tests/test_sla_timer.sh
# SLA 计时器 API 测试脚本
# 增量3-1: v3.7.1

BASE_URL="${TEST_BASE_URL:-http://localhost:8000}"
PASSED=0
FAILED=0

echo "=========================================="
echo "SLA 计时器 API 测试"
echo "=========================================="

# 获取管理员Token
echo "获取管理员Token..."
LOGIN_RESP=$(curl -s -X POST "$BASE_URL/api/agent/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}')

TOKEN=$(echo "$LOGIN_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token',''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "❌ 获取Token失败，跳过测试"
    exit 1
fi
echo "✅ 获取Token成功"

# 测试1: 创建一个测试工单
echo ""
echo "测试1: 创建测试工单"
CREATE_RESP=$(curl -s -X POST "$BASE_URL/api/tickets/manual" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "SLA测试工单",
    "description": "用于测试SLA计时器功能的工单",
    "ticket_type": "after_sale",
    "priority": "high",
    "customer": {
      "name": "SLA测试客户",
      "email": "slatest@example.com"
    }
  }')

TICKET_ID=$(echo "$CREATE_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('ticket',{}).get('ticket_id',''))" 2>/dev/null)

if [ -n "$TICKET_ID" ]; then
    echo "✅ PASS - 工单创建成功: $TICKET_ID"
    ((PASSED++))
else
    echo "❌ FAIL - 工单创建失败"
    echo "响应: $CREATE_RESP"
    ((FAILED++))
    exit 1
fi

# 测试2: 获取单个工单SLA信息
echo ""
echo "测试2: 获取单个工单SLA信息 - GET /api/tickets/{ticket_id}/sla"
SLA_RESP=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/tickets/$TICKET_ID/sla" \
  -H "Authorization: Bearer $TOKEN")

HTTP_CODE=$(echo "$SLA_RESP" | tail -n1)
BODY=$(echo "$SLA_RESP" | head -n-1)

if [ "$HTTP_CODE" -eq 200 ]; then
    # 验证返回的字段
    HAS_FRT=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print('frt_target_seconds' in d.get('data',{}).get('sla',{}))" 2>/dev/null)
    HAS_RT=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print('rt_target_seconds' in d.get('data',{}).get('sla',{}))" 2>/dev/null)

    if [ "$HAS_FRT" = "True" ] && [ "$HAS_RT" = "True" ]; then
        echo "✅ PASS - SLA信息获取成功"
        echo "  - 首次响应目标(秒): $(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('sla',{}).get('frt_target_seconds','N/A'))" 2>/dev/null)"
        echo "  - 解决时效目标(秒): $(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('sla',{}).get('rt_target_seconds','N/A'))" 2>/dev/null)"
        echo "  - 首次响应状态: $(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('sla',{}).get('frt_status','N/A'))" 2>/dev/null)"
        echo "  - 解决时效状态: $(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('sla',{}).get('rt_status','N/A'))" 2>/dev/null)"
        ((PASSED++))
    else
        echo "❌ FAIL - SLA信息字段不完整"
        echo "响应: $BODY"
        ((FAILED++))
    fi
else
    echo "❌ FAIL - 状态码错误，预期200，实际$HTTP_CODE"
    echo "响应: $BODY"
    ((FAILED++))
fi

# 测试3: 获取SLA仪表盘数据
echo ""
echo "测试3: 获取SLA仪表盘数据 - GET /api/tickets/sla-dashboard"
DASHBOARD_RESP=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/tickets/sla-dashboard" \
  -H "Authorization: Bearer $TOKEN")

HTTP_CODE=$(echo "$DASHBOARD_RESP" | tail -n1)
BODY=$(echo "$DASHBOARD_RESP" | head -n-1)

if [ "$HTTP_CODE" -eq 200 ]; then
    # 验证返回的字段
    HAS_FRT_STATS=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print('frt_stats' in d.get('data',{}))" 2>/dev/null)
    HAS_RT_STATS=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print('rt_stats' in d.get('data',{}))" 2>/dev/null)
    HAS_ALERTS=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print('alerts' in d.get('data',{}))" 2>/dev/null)

    if [ "$HAS_FRT_STATS" = "True" ] && [ "$HAS_RT_STATS" = "True" ] && [ "$HAS_ALERTS" = "True" ]; then
        echo "✅ PASS - SLA仪表盘数据获取成功"
        echo "  - 未完成工单数: $(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('total_open_tickets',0))" 2>/dev/null)"
        echo "  - 告警数量: $(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('alerts_count',0))" 2>/dev/null)"
        ((PASSED++))
    else
        echo "❌ FAIL - 仪表盘数据字段不完整"
        echo "响应: $BODY"
        ((FAILED++))
    fi
else
    echo "❌ FAIL - 状态码错误，预期200，实际$HTTP_CODE"
    echo "响应: $BODY"
    ((FAILED++))
fi

# 测试4: 测试不存在的工单SLA
echo ""
echo "测试4: 获取不存在工单的SLA信息 - 预期404"
NOT_FOUND_RESP=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/tickets/NONEXISTENT123/sla" \
  -H "Authorization: Bearer $TOKEN")

HTTP_CODE=$(echo "$NOT_FOUND_RESP" | tail -n1)

if [ "$HTTP_CODE" -eq 404 ]; then
    echo "✅ PASS - 不存在的工单返回404"
    ((PASSED++))
else
    echo "❌ FAIL - 预期404，实际$HTTP_CODE"
    ((FAILED++))
fi

# 测试5: 验证SLA目标值（高优先级售后工单）
echo ""
echo "测试5: 验证SLA目标值设置"
FRT_TARGET=$(echo "$SLA_RESP" | head -n-1 | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('sla',{}).get('frt_target_seconds',0))" 2>/dev/null)
RT_TARGET=$(echo "$SLA_RESP" | head -n-1 | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('sla',{}).get('rt_target_seconds',0))" 2>/dev/null)

# 高优先级工单: FRT应为15分钟=900秒, RT应为8小时=28800秒
if [ "$FRT_TARGET" -eq 900 ] && [ "$RT_TARGET" -eq 28800 ]; then
    echo "✅ PASS - SLA目标值正确"
    echo "  - 高优先级首次响应目标: 15分钟 (900秒)"
    echo "  - 高优先级售后解决目标: 8小时 (28800秒)"
    ((PASSED++))
else
    echo "❌ FAIL - SLA目标值不正确"
    echo "  - 首次响应目标: $FRT_TARGET (预期900)"
    echo "  - 解决时效目标: $RT_TARGET (预期28800)"
    ((FAILED++))
fi

# 测试6: 验证未授权访问
echo ""
echo "测试6: 未授权访问测试 - 预期401"
UNAUTH_RESP=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/tickets/$TICKET_ID/sla")

HTTP_CODE=$(echo "$UNAUTH_RESP" | tail -n1)

if [ "$HTTP_CODE" -eq 401 ] || [ "$HTTP_CODE" -eq 403 ]; then
    echo "✅ PASS - 未授权访问被拒绝"
    ((PASSED++))
else
    echo "❌ FAIL - 预期401/403，实际$HTTP_CODE"
    ((FAILED++))
fi

# 清理：关闭测试工单
echo ""
echo "清理: 关闭测试工单"
curl -s -X PUT "$BASE_URL/api/tickets/$TICKET_ID" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"status": "resolved"}' > /dev/null

curl -s -X PUT "$BASE_URL/api/tickets/$TICKET_ID" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"status": "closed"}' > /dev/null

echo "=========================================="
echo "测试完成"
echo "=========================================="
echo "总测试: $((PASSED + FAILED))"
echo "通过: $PASSED"
echo "失败: $FAILED"

if [ $FAILED -eq 0 ]; then
    echo "✅ 所有测试通过"
    exit 0
else
    echo "❌ 有测试失败"
    exit 1
fi
