#!/bin/bash

# 快捷回复API测试脚本
# 模块3: 快捷回复系统
# 版本: v3.7.0

echo "================================"
echo "快捷回复API测试 v3.7.0"
echo "================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 测试计数器
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 测试函数
test_case() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo "测试 $TOTAL_TESTS: $1"
}

pass() {
    PASSED_TESTS=$((PASSED_TESTS + 1))
    echo -e "${GREEN}✓ 通过${NC}"
    echo ""
}

fail() {
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo -e "${RED}✗ 失败: $1${NC}"
    echo ""
}

# ================================
# 准备工作：获取Token
# ================================

echo "🔐 准备工作：登录获取Token"
echo "--------------------------------"

# 管理员登录
ADMIN_LOGIN=$(curl -s -X POST http://localhost:8000/api/agent/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }')

ADMIN_TOKEN=$(echo $ADMIN_LOGIN | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])" 2>/dev/null)

if [ -z "$ADMIN_TOKEN" ]; then
    echo -e "${RED}❌ 管理员登录失败${NC}"
    exit 1
fi

echo "✓ 管理员登录成功"
echo "Token: ${ADMIN_TOKEN:0:30}..."
echo ""

# 普通坐席登录
AGENT_LOGIN=$(curl -s -X POST http://localhost:8000/api/agent/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "agent001",
    "password": "agent123"
  }')

AGENT_TOKEN=$(echo $AGENT_LOGIN | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])" 2>/dev/null)

if [ -z "$AGENT_TOKEN" ]; then
    echo -e "${RED}❌ 坐席登录失败${NC}"
    exit 1
fi

echo "✓ 坐席登录成功"
echo "Token: ${AGENT_TOKEN:0:30}..."
echo ""

# ================================
# 测试1: 获取分类列表
# ================================
test_case "获取快捷回复分类列表"

CATEGORIES=$(curl -s -X GET http://localhost:8000/api/quick-replies/categories \
  -H "Authorization: Bearer $ADMIN_TOKEN")

if echo "$CATEGORIES" | grep -q '"success":true'; then
    if echo "$CATEGORIES" | grep -q '"greeting"'; then
        pass
    else
        fail "分类列表缺少 greeting"
    fi
else
    fail "获取分类失败"
fi

# ================================
# 测试2: 创建快捷回复（管理员）
# ================================
test_case "创建快捷回复（欢迎语）"

CREATE_RESPONSE=$(curl -s -X POST http://localhost:8000/api/quick-replies \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "欢迎语模板",
    "content": "您好{customer_name}，我是{agent_name}，很高兴为您服务",
    "category": "greeting",
    "shortcut_key": "1",
    "is_shared": true
  }')

if echo "$CREATE_RESPONSE" | grep -q '"success":true'; then
    REPLY_ID_1=$(echo $CREATE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null)
    if [ ! -z "$REPLY_ID_1" ]; then
        echo "  创建的快捷回复ID: $REPLY_ID_1"
        pass
    else
        fail "未返回快捷回复ID"
    fi
else
    fail "创建失败"
fi

# ================================
# 测试3: 创建快捷回复（售后服务）
# ================================
test_case "创建快捷回复（售后服务）"

CREATE_RESPONSE_2=$(curl -s -X POST http://localhost:8000/api/quick-replies \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "查询订单",
    "content": "请您提供订单号{order_id}，我帮您查询物流信息",
    "category": "after_sales",
    "is_shared": false
  }')

if echo "$CREATE_RESPONSE_2" | grep -q '"success":true'; then
    REPLY_ID_2=$(echo $CREATE_RESPONSE_2 | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null)
    echo "  创建的快捷回复ID: $REPLY_ID_2"
    pass
else
    fail "创建失败"
fi

# ================================
# 测试4: 获取快捷回复详情
# ================================
test_case "获取快捷回复详情"

if [ ! -z "$REPLY_ID_1" ]; then
    DETAIL=$(curl -s -X GET "http://localhost:8000/api/quick-replies/$REPLY_ID_1" \
      -H "Authorization: Bearer $ADMIN_TOKEN")

    if echo "$DETAIL" | grep -q '"success":true'; then
        if echo "$DETAIL" | grep -q '"title":"欢迎语模板"'; then
            pass
        else
            fail "返回的标题不正确"
        fi
    else
        fail "获取详情失败"
    fi
else
    fail "缺少快捷回复ID"
fi

# ================================
# 测试5: 获取所有快捷回复列表
# ================================
test_case "获取所有快捷回复列表"

LIST=$(curl -s -X GET "http://localhost:8000/api/quick-replies?limit=10" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

if echo "$LIST" | grep -q '"success":true'; then
    TOTAL=$(echo $LIST | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['total'])" 2>/dev/null)
    if [ "$TOTAL" -ge 2 ]; then
        echo "  共 $TOTAL 个快捷回复"
        pass
    else
        fail "快捷回复数量不足"
    fi
else
    fail "获取列表失败"
fi

# ================================
# 测试6: 按分类筛选
# ================================
test_case "按分类筛选（greeting）"

FILTER=$(curl -s -X GET "http://localhost:8000/api/quick-replies?category=greeting" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

if echo "$FILTER" | grep -q '"success":true'; then
    if echo "$FILTER" | grep -q '"category":"greeting"'; then
        pass
    else
        fail "筛选结果不正确"
    fi
else
    fail "分类筛选失败"
fi

# ================================
# 测试7: 关键词搜索
# ================================
test_case "关键词搜索（欢迎语）"

SEARCH=$(curl -s -X GET "http://localhost:8000/api/quick-replies?keyword=%E6%AC%A2%E8%BF%8E" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

if echo "$SEARCH" | grep -q '"success":true'; then
    if echo "$SEARCH" | grep -q '"欢迎'; then
        pass
    else
        fail "搜索结果不包含欢迎相关内容"
    fi
else
    fail "关键词搜索失败"
fi

# ================================
# 测试8: 更新快捷回复
# ================================
test_case "更新快捷回复"

if [ ! -z "$REPLY_ID_1" ]; then
    UPDATE=$(curl -s -X PUT "http://localhost:8000/api/quick-replies/$REPLY_ID_1" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "title": "欢迎语模板（更新版）",
        "shortcut_key": "2"
      }')

    if echo "$UPDATE" | grep -q '"success":true'; then
        if echo "$UPDATE" | grep -q '"title":"欢迎语模板（更新版）"'; then
            pass
        else
            fail "更新后的标题不正确"
        fi
    else
        fail "更新失败"
    fi
else
    fail "缺少快捷回复ID"
fi

# ================================
# 测试9: 使用快捷回复（变量替换）
# ================================
test_case "使用快捷回复（变量替换）"

if [ ! -z "$REPLY_ID_1" ]; then
    USE=$(curl -s -X POST "http://localhost:8000/api/quick-replies/$REPLY_ID_1/use" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "session_data": {
          "user_profile": {
            "nickname": "张三"
          }
        },
        "agent_data": {
          "name": "李客服"
        }
      }')

    if echo "$USE" | grep -q '"success":true'; then
        if echo "$USE" | grep -q '您好张三'; then
            if echo "$USE" | grep -q '我是李客服'; then
                echo "  替换后内容: 您好张三，我是李客服，很高兴为您服务"
                pass
            else
                fail "变量 {agent_name} 替换失败"
            fi
        else
            fail "变量 {customer_name} 替换失败"
        fi
    else
        fail "使用快捷回复失败"
    fi
else
    fail "缺少快捷回复ID"
fi

# ================================
# 测试10: 获取使用统计（管理员权限）
# ================================
test_case "获取使用统计（管理员）"

STATS=$(curl -s -X GET "http://localhost:8000/api/quick-replies/stats" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

if echo "$STATS" | grep -q '"success":true'; then
    if echo "$STATS" | grep -q '"total_count"'; then
        pass
    else
        fail "统计数据缺少 total_count"
    fi
else
    fail "获取统计失败"
fi

# ================================
# 测试11: 普通坐席访问统计（应失败）
# ================================
test_case "普通坐席访问统计（应拒绝）"

STATS_AGENT=$(curl -s -X GET "http://localhost:8000/api/quick-replies/stats" \
  -H "Authorization: Bearer $AGENT_TOKEN")

if echo "$STATS_AGENT" | grep -q '"detail":"PERMISSION_DENIED'; then
    pass
else
    fail "应该拒绝普通坐席访问统计"
fi

# ================================
# 测试12: 删除快捷回复
# ================================
test_case "删除快捷回复"

if [ ! -z "$REPLY_ID_2" ]; then
    DELETE=$(curl -s -X DELETE "http://localhost:8000/api/quick-replies/$REPLY_ID_2" \
      -H "Authorization: Bearer $ADMIN_TOKEN")

    if echo "$DELETE" | grep -q '"success":true'; then
        # 验证已删除
        VERIFY=$(curl -s -X GET "http://localhost:8000/api/quick-replies/$REPLY_ID_2" \
          -H "Authorization: Bearer $ADMIN_TOKEN")

        if echo "$VERIFY" | grep -q '"detail":"QUICK_REPLY_NOT_FOUND'; then
            pass
        else
            fail "删除后仍能获取快捷回复"
        fi
    else
        fail "删除失败"
    fi
else
    fail "缺少快捷回复ID"
fi

# ================================
# 测试13: 验证变量提取
# ================================
test_case "验证变量提取功能"

CREATE_VAR=$(curl -s -X POST http://localhost:8000/api/quick-replies \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "物流通知",
    "content": "您的订单{order_id}已发货，物流单号{tracking_number}",
    "category": "logistics"
  }')

if echo "$CREATE_VAR" | grep -q '"success":true'; then
    if echo "$CREATE_VAR" | grep -q '"order_id"'; then
        if echo "$CREATE_VAR" | grep -q '"tracking_number"'; then
            echo "  提取的变量: order_id, tracking_number"
            pass
        else
            fail "未提取到 tracking_number 变量"
        fi
    else
        fail "未提取到 order_id 变量"
    fi
else
    fail "创建失败"
fi

# ================================
# 测试总结
# ================================
echo "================================"
echo "测试总结"
echo "================================"
echo "总测试数: $TOTAL_TESTS"
echo -e "通过: ${GREEN}$PASSED_TESTS${NC}"
echo -e "失败: ${RED}$FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ 所有测试通过！${NC}"
    exit 0
else
    echo -e "${RED}✗ 部分测试失败${NC}"
    exit 1
fi
