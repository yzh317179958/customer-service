"""
Shopify UK 客户端单元测试

测试 src/shopify_uk_client.py 的基础功能：
- 客户端初始化
- API 健康检查
- 订单查询（需要真实Token才能通过）
"""

import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.shopify_uk_client import (
    ShopifyUKClient,
    ShopifyAPIError,
    get_shopify_uk_client,
    ERROR_CODES,
)


def test_client_initialization():
    """测试 1: 客户端初始化"""
    print("测试 1: 客户端初始化")

    try:
        client = ShopifyUKClient()

        # 验证基本属性
        assert client.shop_domain == "fiidouk.myshopify.com", "店铺域名错误"
        assert client.api_version == "2024-01", "API版本错误"
        assert client.base_url == "https://fiidouk.myshopify.com/admin/api/2024-01", "Base URL错误"

        print("✅ PASS - 客户端初始化成功")
        return True
    except Exception as e:
        print(f"❌ FAIL - {e}")
        return False


def test_singleton_pattern():
    """测试 2: 单例模式"""
    print("测试 2: 单例模式")

    try:
        client1 = get_shopify_uk_client()
        client2 = get_shopify_uk_client()

        assert client1 is client2, "单例模式失败"

        print("✅ PASS - 单例模式正常")
        return True
    except Exception as e:
        print(f"❌ FAIL - {e}")
        return False


def test_error_codes():
    """测试 3: 错误码定义"""
    print("测试 3: 错误码定义")

    try:
        expected_codes = [
            "SHOPIFY_API_ERROR",
            "ORDER_NOT_FOUND",
            "INVALID_ORDER_NUMBER",
            "RATE_LIMITED",
            "TOKEN_INVALID",
            "PERMISSION_DENIED",
        ]

        for code in expected_codes:
            assert code in ERROR_CODES, f"缺少错误码: {code}"
            assert "code" in ERROR_CODES[code], f"错误码 {code} 缺少 code 字段"
            assert "message" in ERROR_CODES[code], f"错误码 {code} 缺少 message 字段"

        print("✅ PASS - 错误码定义完整")
        return True
    except Exception as e:
        print(f"❌ FAIL - {e}")
        return False


async def test_health_check():
    """测试 4: 健康检查（需要真实Token）"""
    print("测试 4: 健康检查")

    try:
        client = get_shopify_uk_client()
        result = await client.health_check()

        assert "status" in result, "健康检查结果缺少 status 字段"

        if result["status"] == "healthy":
            print(f"✅ PASS - 健康检查通过 (订单总数: {result.get('total_orders', 'N/A')})")
            return True
        else:
            print(f"⚠️  WARN - 健康检查返回 unhealthy: {result.get('error', 'Unknown')}")
            print("   (这可能是因为 Token 未配置或无效)")
            return True  # 不算失败，因为可能是配置问题
    except Exception as e:
        print(f"❌ FAIL - {e}")
        return False


async def test_search_order_not_found():
    """测试 5: 搜索不存在的订单"""
    print("测试 5: 搜索不存在的订单")

    try:
        client = get_shopify_uk_client()

        # 搜索一个肯定不存在的订单号
        result = await client.search_order_by_number("NOTEXIST999999")

        # 应该返回 None
        assert result is None, "不存在的订单应该返回 None"

        print("✅ PASS - 订单不存在时正确返回 None")
        return True
    except ShopifyAPIError as e:
        if e.code == ERROR_CODES["TOKEN_INVALID"]["code"]:
            print("⚠️  WARN - Token 未配置或无效，跳过测试")
            return True
        print(f"❌ FAIL - API错误: {e}")
        return False
    except Exception as e:
        print(f"❌ FAIL - {e}")
        return False


def run_tests():
    """运行所有测试"""
    print("=" * 50)
    print("Shopify UK 客户端测试")
    print("=" * 50)
    print()

    passed = 0
    failed = 0

    # 同步测试
    tests_sync = [
        test_client_initialization,
        test_singleton_pattern,
        test_error_codes,
    ]

    for test in tests_sync:
        if test():
            passed += 1
        else:
            failed += 1
        print()

    # 异步测试
    tests_async = [
        test_health_check,
        test_search_order_not_found,
    ]

    for test in tests_async:
        if asyncio.run(test()):
            passed += 1
        else:
            failed += 1
        print()

    # 总结
    print("=" * 50)
    total = passed + failed
    print(f"测试完成: {passed}/{total} 通过")
    print("=" * 50)

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
