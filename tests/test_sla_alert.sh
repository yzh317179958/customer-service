#!/bin/bash
# ==================================================
# 【增量3-4】SLA 预警通知系统测试脚本
# ==================================================

BASE_URL="http://localhost:8000"
PASSED=0
FAILED=0

# 获取管理员Token
echo "=========================================="
echo "SLA 预警系统测试"
echo "=========================================="
echo "获取管理员Token..."

LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}')

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "❌ 登录失败，无法获取Token"
    echo "响应: $LOGIN_RESPONSE"
    exit 1
fi
echo "✅ 登录成功"
echo ""

# ------------------------------------------
# 测试 1: 获取 SLA 预警列表 API
# ------------------------------------------
echo "测试 1: 获取 SLA 预警列表"
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/tickets/sla-alerts" \
  -H "Authorization: Bearer $TOKEN")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 200 ]; then
    # 检查返回格式
    SUCCESS=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)
    if [ "$SUCCESS" = "True" ]; then
        echo "✅ PASS - SLA预警API返回成功"
        ((PASSED++))
    else
        echo "❌ FAIL - 返回格式错误"
        echo "响应: $BODY"
        ((FAILED++))
    fi
else
    echo "❌ FAIL - 预期200，实际$HTTP_CODE"
    ((FAILED++))
fi
echo ""

# ------------------------------------------
# 测试 2: 创建测试工单（低优先级，较短SLA）
# ------------------------------------------
echo "测试 2: 创建测试工单用于SLA检测"
TICKET_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/tickets" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "SLA测试工单",
    "description": "用于测试SLA预警功能的工单",
    "ticket_type": "after_sale",
    "priority": "urgent",
    "created_by": "admin",
    "created_by_name": "管理员"
  }')

HTTP_CODE=$(echo "$TICKET_RESPONSE" | tail -n1)
BODY=$(echo "$TICKET_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 200 ]; then
    TICKET_ID=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('ticket_id','') or d.get('ticket_id',''))" 2>/dev/null)
    if [ -n "$TICKET_ID" ]; then
        echo "✅ PASS - 创建工单成功: $TICKET_ID"
        ((PASSED++))
    else
        echo "❌ FAIL - 无法获取工单ID"
        echo "响应: $BODY"
        ((FAILED++))
        TICKET_ID=""
    fi
else
    echo "❌ FAIL - 创建工单失败，HTTP $HTTP_CODE"
    ((FAILED++))
    TICKET_ID=""
fi
echo ""

# ------------------------------------------
# 测试 3: 获取工单SLA信息
# ------------------------------------------
if [ -n "$TICKET_ID" ]; then
    echo "测试 3: 获取工单SLA信息"
    SLA_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/tickets/$TICKET_ID/sla" \
      -H "Authorization: Bearer $TOKEN")

    HTTP_CODE=$(echo "$SLA_RESPONSE" | tail -n1)
    BODY=$(echo "$SLA_RESPONSE" | head -n-1)

    if [ "$HTTP_CODE" -eq 200 ]; then
        # 检查必要字段
        FRT_STATUS=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('frt_status',''))" 2>/dev/null)
        RT_STATUS=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('rt_status',''))" 2>/dev/null)
        if [ -n "$FRT_STATUS" ] && [ -n "$RT_STATUS" ]; then
            echo "✅ PASS - SLA信息获取成功 (FRT: $FRT_STATUS, RT: $RT_STATUS)"
            ((PASSED++))
        else
            echo "❌ FAIL - SLA信息格式不完整"
            echo "响应: $BODY"
            ((FAILED++))
        fi
    else
        echo "❌ FAIL - 获取SLA信息失败，HTTP $HTTP_CODE"
        ((FAILED++))
    fi
    echo ""
fi

# ------------------------------------------
# 测试 4: 检查预警检测返回格式
# ------------------------------------------
echo "测试 4: 验证SLA预警返回格式"
ALERTS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/tickets/sla-alerts" \
  -H "Authorization: Bearer $TOKEN")

# 检查 summary 字段存在
SUMMARY=$(echo "$ALERTS_RESPONSE" | python3 -c "
import sys,json
d=json.load(sys.stdin)
data = d.get('data', {})
summary = data.get('summary', {})
print('OK' if 'total' in summary and 'by_status' in summary and 'by_type' in summary else 'FAIL')
" 2>/dev/null)

if [ "$SUMMARY" = "OK" ]; then
    echo "✅ PASS - 预警返回格式正确（包含 summary.total/by_status/by_type）"
    ((PASSED++))
else
    echo "❌ FAIL - 预警返回格式缺少必要字段"
    echo "响应: $ALERTS_RESPONSE"
    ((FAILED++))
fi
echo ""

# ------------------------------------------
# 测试 5: 检查后台任务配置
# ------------------------------------------
echo "测试 5: 验证后端健康状态"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/health")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" -eq 200 ]; then
    echo "✅ PASS - 后端服务运行正常"
    ((PASSED++))
else
    echo "❌ FAIL - 后端服务异常"
    ((FAILED++))
fi
echo ""

# ------------------------------------------
# 清理测试数据：关闭测试工单
# ------------------------------------------
if [ -n "$TICKET_ID" ]; then
    echo "清理: 关闭测试工单..."
    # 先解决工单
    curl -s -X PATCH "$BASE_URL/api/tickets/$TICKET_ID" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"status": "resolved", "changed_by": "admin"}' > /dev/null 2>&1

    # 再关闭工单
    curl -s -X PATCH "$BASE_URL/api/tickets/$TICKET_ID" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"status": "closed", "changed_by": "admin"}' > /dev/null 2>&1
    echo "✅ 测试工单已清理"
fi

# ------------------------------------------
# 输出总结
# ------------------------------------------
echo ""
echo "=========================================="
echo "测试总结"
echo "=========================================="
echo "总测试: $((PASSED + FAILED))"
echo "通过: $PASSED"
echo "失败: $FAILED"
echo "=========================================="

if [ $FAILED -eq 0 ]; then
    echo "✅ 所有测试通过!"
    exit 0
else
    echo "❌ 存在失败的测试"
    exit 1
fi
