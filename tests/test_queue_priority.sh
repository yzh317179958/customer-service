#!/bin/bash
# 【L1-1-Part1-模块2】会话优先级与队列管理 - 自动化测试脚本
# 测试队列管理API、优先级计算、排序逻辑

BASE_URL="http://localhost:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================="
echo "【L1-1-Part1-模块2】队列管理功能测试"
echo "========================================="
echo ""

# 计数器
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 测试函数
test_api() {
    local test_name=$1
    local endpoint=$2
    local expected_field=$3
    local expected_condition=$4  # ">", ">=", "=", etc.
    local expected_value=$5

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "测试 $TOTAL_TESTS: $test_name ... "

    response=$(curl -s "$BASE_URL$endpoint")
    success=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)

    if [ "$success" = "True" ]; then
        if [ -n "$expected_field" ]; then
            actual=$(echo "$response" | python3 -c "
import sys, json
d = json.load(sys.stdin)
parts = '$expected_field'.split('.')
value = d
for part in parts:
    if isinstance(value, dict):
        value = value.get(part)
    else:
        value = None
        break
print(value if value is not None else 'NOT_FOUND')
" 2>/dev/null)

            # 检查条件
            if [ "$expected_condition" = "=" ]; then
                if [ "$actual" = "$expected_value" ]; then
                    echo -e "${GREEN}✓ 通过${NC} ($actual)"
                    PASSED_TESTS=$((PASSED_TESTS + 1))
                else
                    echo -e "${RED}✗ 失败${NC} (期望: $expected_value, 实际: $actual)"
                    FAILED_TESTS=$((FAILED_TESTS + 1))
                fi
            elif [ "$expected_condition" = ">=" ]; then
                # 使用Python进行浮点数比较
                result=$(python3 -c "print(1 if float('$actual') >= float('$expected_value') else 0)" 2>/dev/null)
                if [ "$result" = "1" ]; then
                    echo -e "${GREEN}✓ 通过${NC} ($actual >= $expected_value)"
                    PASSED_TESTS=$((PASSED_TESTS + 1))
                else
                    echo -e "${RED}✗ 失败${NC} (期望: >= $expected_value, 实际: $actual)"
                    FAILED_TESTS=$((FAILED_TESTS + 1))
                fi
            else
                echo -e "${GREEN}✓ 通过${NC} (字段存在: $actual)"
                PASSED_TESTS=$((PASSED_TESTS + 1))
            fi
        else
            echo -e "${GREEN}✓ 通过${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        fi
    else
        error=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('detail', 'Unknown error'))" 2>/dev/null)
        echo -e "${RED}✗ 失败${NC} ($error)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

# 测试队列API的优先级排序
test_queue_priority() {
    local test_name=$1

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "测试 $TOTAL_TESTS: $test_name ... "

    response=$(curl -s "$BASE_URL/api/sessions/queue")

    # 检查是否成功返回
    success=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)

    if [ "$success" = "True" ]; then
        # 验证队列按优先级排序（urgent > high > normal）
        priority_check=$(echo "$response" | python3 -c "
import sys, json
d = json.load(sys.stdin)
queue = d.get('data', {}).get('queue', [])

if len(queue) == 0:
    print('EMPTY_QUEUE')
    sys.exit(0)

# 检查优先级排序（urgent=3, high=2, normal=1）
priority_weights = {'urgent': 3, 'high': 2, 'normal': 1}
prev_weight = 4  # 初始值大于最高优先级
is_sorted = True

for item in queue:
    level = item.get('priority_level', 'normal')
    weight = priority_weights.get(level, 1)
    if weight > prev_weight:
        is_sorted = False
        break
    prev_weight = weight

print('SORTED' if is_sorted else 'UNSORTED')
" 2>/dev/null)

        if [ "$priority_check" = "SORTED" ]; then
            echo -e "${GREEN}✓ 通过${NC} (队列按优先级正确排序)"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        elif [ "$priority_check" = "EMPTY_QUEUE" ]; then
            echo -e "${YELLOW}⚠ 跳过${NC} (队列为空)"
            TOTAL_TESTS=$((TOTAL_TESTS - 1))
        else
            echo -e "${RED}✗ 失败${NC} (队列排序不正确)"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    else
        echo -e "${RED}✗ 失败${NC} (API调用失败)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

echo -e "${BLUE}=== 队列API基础测试 ===${NC}"
echo ""

# Test 1: 队列API可访问性
test_api "队列API基础调用" "/api/sessions/queue"

# Test 2: 响应数据结构
test_api "队列数据包含total_count" "/api/sessions/queue" "data.total_count" ">=" "0"
test_api "队列数据包含vip_count" "/api/sessions/queue" "data.vip_count" ">=" "0"
test_api "队列数据包含avg_wait_time" "/api/sessions/queue" "data.avg_wait_time" ">=" "0"

echo ""
echo -e "${BLUE}=== 优先级排序逻辑测试 ===${NC}"
echo ""

# Test 3: 队列按优先级排序
test_queue_priority "队列按优先级排序（urgent > high > normal）"

echo ""
echo -e "${BLUE}=== 优先级字段验证 ===${NC}"
echo ""

# Test 4: 检查队列项包含必要字段
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "测试 $TOTAL_TESTS: 队列项包含必要优先级字段 ... "

response=$(curl -s "$BASE_URL/api/sessions/queue")
field_check=$(echo "$response" | python3 -c "
import sys, json
d = json.load(sys.stdin)
queue = d.get('data', {}).get('queue', [])

if len(queue) == 0:
    print('EMPTY_QUEUE')
    sys.exit(0)

# 检查第一个队列项的字段
item = queue[0]
required_fields = ['session_name', 'position', 'priority_level', 'is_vip', 'wait_time_seconds']
missing = [f for f in required_fields if f not in item]

if len(missing) == 0:
    print('ALL_FIELDS_PRESENT')
else:
    print(f'MISSING_FIELDS:{missing}')
" 2>/dev/null)

if [ "$field_check" = "ALL_FIELDS_PRESENT" ]; then
    echo -e "${GREEN}✓ 通过${NC} (所有必要字段存在)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
elif [ "$field_check" = "EMPTY_QUEUE" ]; then
    echo -e "${YELLOW}⚠ 跳过${NC} (队列为空)"
    TOTAL_TESTS=$((TOTAL_TESTS - 1))
else
    echo -e "${RED}✗ 失败${NC} ($field_check)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""
echo -e "${BLUE}=== VIP客户优先级测试 ===${NC}"
echo ""

# Test 5: VIP客户应该在队列前面
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "测试 $TOTAL_TESTS: VIP客户优先级高于普通客户 ... "

response=$(curl -s "$BASE_URL/api/sessions/queue")
vip_priority_check=$(echo "$response" | python3 -c "
import sys, json
d = json.load(sys.stdin)
queue = d.get('data', {}).get('queue', [])

if len(queue) < 2:
    print('INSUFFICIENT_DATA')
    sys.exit(0)

# 查找VIP和非VIP客户
vip_positions = [item['position'] for item in queue if item.get('is_vip')]
non_vip_positions = [item['position'] for item in queue if not item.get('is_vip')]

if len(vip_positions) == 0 or len(non_vip_positions) == 0:
    print('NO_MIXED_QUEUE')
    sys.exit(0)

# VIP的最大位置应该 <= 非VIP的最小位置（位置越小越靠前）
if max(vip_positions) <= min(non_vip_positions):
    print('VIP_PRIORITIZED')
else:
    print('VIP_NOT_PRIORITIZED')
" 2>/dev/null)

if [ "$vip_priority_check" = "VIP_PRIORITIZED" ]; then
    echo -e "${GREEN}✓ 通过${NC} (VIP客户优先)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
elif [ "$vip_priority_check" = "NO_MIXED_QUEUE" ] || [ "$vip_priority_check" = "INSUFFICIENT_DATA" ]; then
    echo -e "${YELLOW}⚠ 跳过${NC} (队列数据不足)"
    TOTAL_TESTS=$((TOTAL_TESTS - 1))
else
    echo -e "${RED}✗ 失败${NC} (VIP客户未优先)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# 输出测试结果
echo ""
echo "========================================="
echo "测试结果总结"
echo "========================================="
echo -e "总测试数: $TOTAL_TESTS"
echo -e "${GREEN}通过: $PASSED_TESTS${NC}"
echo -e "${RED}失败: $FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ 所有测试通过！${NC}"
    exit 0
else
    echo -e "${RED}✗ 部分测试失败${NC}"
    exit 1
fi
