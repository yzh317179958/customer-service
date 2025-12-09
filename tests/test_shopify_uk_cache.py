"""
Shopify UK 缓存层单元测试

测试 src/shopify_uk_cache.py 的功能：
- 缓存初始化
- 订单列表缓存
- 订单详情缓存
- 物流信息缓存
- 缓存失效
"""

import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.shopify_uk_cache import ShopifyUKCache, get_shopify_uk_cache


def test_cache_initialization():
    """测试 1: 缓存初始化"""
    print("测试 1: 缓存初始化")

    try:
        cache = ShopifyUKCache()

        # 验证 TTL 配置
        assert cache.ttl["order_list"] == 300, "订单列表 TTL 错误"
        assert cache.ttl["order_detail"] == 600, "订单详情 TTL 错误"
        assert cache.ttl["tracking"] == 1800, "物流信息 TTL 错误"
        assert cache.ttl["order_count"] == 3600, "订单数量 TTL 错误"

        print("✅ PASS - 缓存初始化成功")
        return True
    except Exception as e:
        print(f"❌ FAIL - {e}")
        return False


def test_singleton_pattern():
    """测试 2: 单例模式"""
    print("测试 2: 单例模式")

    try:
        cache1 = get_shopify_uk_cache()
        cache2 = get_shopify_uk_cache()

        assert cache1 is cache2, "单例模式失败"

        print("✅ PASS - 单例模式正常")
        return True
    except Exception as e:
        print(f"❌ FAIL - {e}")
        return False


async def test_order_list_cache():
    """测试 3: 订单列表缓存"""
    print("测试 3: 订单列表缓存")

    try:
        cache = get_shopify_uk_cache()
        test_email = "test_cache@example.com"
        test_orders = [
            {"order_id": "123", "order_number": "#UK001"},
            {"order_id": "124", "order_number": "#UK002"},
        ]

        # 先清理可能存在的测试数据
        cache.redis.delete(cache._order_list_key(test_email))

        # 测试缓存未命中
        result = await cache.get_order_list(test_email)
        assert result is None, "应该返回 None"

        # 写入缓存
        success = await cache.set_order_list(test_email, test_orders)
        assert success, "写入缓存失败"

        # 测试缓存命中
        result = await cache.get_order_list(test_email)
        assert result is not None, "应该返回缓存数据"
        assert len(result) == 2, "订单数量不对"
        assert result[0]["order_id"] == "123", "订单数据不对"

        # 清理测试数据
        cache.redis.delete(cache._order_list_key(test_email))

        print("✅ PASS - 订单列表缓存正常")
        return True
    except Exception as e:
        print(f"❌ FAIL - {e}")
        return False


async def test_order_detail_cache():
    """测试 4: 订单详情缓存"""
    print("测试 4: 订单详情缓存")

    try:
        cache = get_shopify_uk_cache()
        test_order_id = "test_order_999"
        test_order = {
            "order_id": test_order_id,
            "order_number": "#UK999",
            "total_price": "1234.56",
            "customer_name": "Test User",
        }

        # 先清理
        cache.redis.delete(cache._order_detail_key(test_order_id))

        # 测试缓存未命中
        result = await cache.get_order_detail(test_order_id)
        assert result is None, "应该返回 None"

        # 写入缓存
        success = await cache.set_order_detail(test_order_id, test_order)
        assert success, "写入缓存失败"

        # 测试缓存命中
        result = await cache.get_order_detail(test_order_id)
        assert result is not None, "应该返回缓存数据"
        assert result["order_number"] == "#UK999", "订单号不对"
        assert result["total_price"] == "1234.56", "金额不对"

        # 清理测试数据
        cache.redis.delete(cache._order_detail_key(test_order_id))

        print("✅ PASS - 订单详情缓存正常")
        return True
    except Exception as e:
        print(f"❌ FAIL - {e}")
        return False


async def test_order_search_cache():
    """测试 5: 订单号搜索缓存"""
    print("测试 5: 订单号搜索缓存")

    try:
        cache = get_shopify_uk_cache()
        test_order_number = "UK888"
        test_order = {
            "order_id": "888",
            "order_number": f"#{test_order_number}",
        }

        # 先清理
        cache.redis.delete(cache._order_search_key(test_order_number))

        # 测试缓存未命中
        result = await cache.get_order_by_number(test_order_number)
        assert result is None, "应该返回 None"

        # 写入缓存
        success = await cache.set_order_by_number(test_order_number, test_order)
        assert success, "写入缓存失败"

        # 测试缓存命中（带 # 前缀）
        result = await cache.get_order_by_number(f"#{test_order_number}")
        assert result is not None, "应该返回缓存数据"

        # 测试缓存命中（小写）
        result = await cache.get_order_by_number(test_order_number.lower())
        assert result is not None, "应该返回缓存数据（小写）"

        # 清理测试数据
        cache.redis.delete(cache._order_search_key(test_order_number))

        print("✅ PASS - 订单号搜索缓存正常")
        return True
    except Exception as e:
        print(f"❌ FAIL - {e}")
        return False


async def test_tracking_cache():
    """测试 6: 物流信息缓存"""
    print("测试 6: 物流信息缓存")

    try:
        cache = get_shopify_uk_cache()
        test_order_id = "test_tracking_777"
        test_tracking = {
            "tracking_company": "Royal Mail",
            "tracking_number": "AB123456789GB",
            "status": "in_transit",
        }

        # 先清理
        cache.redis.delete(cache._tracking_key(test_order_id))

        # 测试缓存未命中
        result = await cache.get_tracking(test_order_id)
        assert result is None, "应该返回 None"

        # 写入缓存
        success = await cache.set_tracking(test_order_id, test_tracking)
        assert success, "写入缓存失败"

        # 测试缓存命中
        result = await cache.get_tracking(test_order_id)
        assert result is not None, "应该返回缓存数据"
        assert result["tracking_company"] == "Royal Mail", "承运商不对"
        assert result["tracking_number"] == "AB123456789GB", "运单号不对"

        # 清理测试数据
        cache.redis.delete(cache._tracking_key(test_order_id))

        print("✅ PASS - 物流信息缓存正常")
        return True
    except Exception as e:
        print(f"❌ FAIL - {e}")
        return False


async def test_cache_invalidation():
    """测试 7: 缓存失效"""
    print("测试 7: 缓存失效")

    try:
        cache = get_shopify_uk_cache()
        test_order_id = "test_invalidate_666"
        test_order_number = "UK666"

        # 写入测试数据
        await cache.set_order_detail(test_order_id, {"order_id": test_order_id})
        await cache.set_tracking(test_order_id, {"status": "test"})
        await cache.set_order_by_number(test_order_number, {"order_id": test_order_id})

        # 验证数据存在
        assert await cache.get_order_detail(test_order_id) is not None, "订单详情应该存在"
        assert await cache.get_tracking(test_order_id) is not None, "物流信息应该存在"

        # 执行缓存失效
        deleted = await cache.invalidate_order(test_order_id, test_order_number)
        assert deleted >= 2, f"应该删除至少2个键，实际删除 {deleted} 个"

        # 验证数据已删除
        assert await cache.get_order_detail(test_order_id) is None, "订单详情应该已删除"
        assert await cache.get_tracking(test_order_id) is None, "物流信息应该已删除"

        print("✅ PASS - 缓存失效正常")
        return True
    except Exception as e:
        print(f"❌ FAIL - {e}")
        return False


async def test_cache_stats():
    """测试 8: 缓存统计"""
    print("测试 8: 缓存统计")

    try:
        cache = get_shopify_uk_cache()
        stats = cache.get_stats()

        assert "total" in stats, "缺少 total 字段"
        assert "order_list" in stats, "缺少 order_list 字段"
        assert "order_detail" in stats, "缺少 order_detail 字段"
        assert "tracking" in stats, "缺少 tracking 字段"

        print(f"✅ PASS - 缓存统计正常 (总缓存键: {stats['total']})")
        return True
    except Exception as e:
        print(f"❌ FAIL - {e}")
        return False


def run_tests():
    """运行所有测试"""
    print("=" * 50)
    print("Shopify UK 缓存层测试")
    print("=" * 50)
    print()

    passed = 0
    failed = 0

    # 同步测试
    tests_sync = [
        test_cache_initialization,
        test_singleton_pattern,
    ]

    for test in tests_sync:
        if test():
            passed += 1
        else:
            failed += 1
        print()

    # 异步测试
    tests_async = [
        test_order_list_cache,
        test_order_detail_cache,
        test_order_search_cache,
        test_tracking_cache,
        test_cache_invalidation,
        test_cache_stats,
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
