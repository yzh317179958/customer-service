"""
物流状态翻译模块测试

测试 src/shopify_tracking.py 的功能：
- 承运商名称标准化
- 追踪链接生成
- 状态翻译
- 话术生成
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.shopify_tracking import (
    normalize_carrier_name,
    get_tracking_url,
    translate_fulfillment_status,
    translate_tracking_status,
    translate_financial_status,
    generate_tracking_message,
    enrich_tracking_data,
)


def test_normalize_carrier_name():
    """测试 1: 承运商名称标准化"""
    print("测试 1: 承运商名称标准化")

    try:
        # 测试常见承运商
        assert normalize_carrier_name("royalmail") == "Royal Mail", "Royal Mail 标准化失败"
        assert normalize_carrier_name("dpd") == "DPD", "DPD 标准化失败"
        assert normalize_carrier_name("hermes") == "Evri", "Hermes->Evri 标准化失败"
        assert normalize_carrier_name("dhl express") == "DHL Express", "DHL Express 标准化失败"
        assert normalize_carrier_name("ups") == "UPS", "UPS 标准化失败"
        assert normalize_carrier_name("sf express") == "SF Express", "SF Express 标准化失败"

        # 测试空值
        assert normalize_carrier_name("") == "Unknown", "空值处理失败"
        assert normalize_carrier_name(None) == "Unknown", "None 处理失败"

        # 测试未知承运商
        assert normalize_carrier_name("Some New Carrier") == "Some New Carrier", "未知承运商处理失败"

        print("✅ PASS - 承运商名称标准化正常")
        return True
    except Exception as e:
        print(f"❌ FAIL - {e}")
        return False


def test_get_tracking_url():
    """测试 2: 追踪链接生成"""
    print("测试 2: 追踪链接生成")

    try:
        # 测试 Royal Mail
        url = get_tracking_url("Royal Mail", "AB123456789GB")
        assert url is not None, "Royal Mail 链接生成失败"
        assert "AB123456789GB" in url, "链接中没有运单号"

        # 测试 DPD
        url = get_tracking_url("dpd", "12345678")
        assert url is not None, "DPD 链接生成失败"

        # 测试 UPS
        url = get_tracking_url("UPS", "1Z999AA10123456784")
        assert url is not None, "UPS 链接生成失败"

        # 测试未知承运商
        url = get_tracking_url("Unknown Carrier", "12345")
        assert url is None, "未知承运商应该返回 None"

        # 测试空值
        url = get_tracking_url("", "12345")
        assert url is None, "空承运商应该返回 None"
        url = get_tracking_url("Royal Mail", "")
        assert url is None, "空运单号应该返回 None"

        print("✅ PASS - 追踪链接生成正常")
        return True
    except Exception as e:
        print(f"❌ FAIL - {e}")
        return False


def test_translate_fulfillment_status():
    """测试 3: 发货状态翻译"""
    print("测试 3: 发货状态翻译")

    try:
        # 测试中文翻译
        assert translate_fulfillment_status(None, "zh") == "未发货", "None 翻译失败"
        assert translate_fulfillment_status("fulfilled", "zh") == "已发货", "fulfilled 翻译失败"
        assert translate_fulfillment_status("partial", "zh") == "部分发货", "partial 翻译失败"

        # 测试英文翻译
        assert translate_fulfillment_status(None, "en") == "Unfulfilled", "None 英文翻译失败"
        assert translate_fulfillment_status("fulfilled", "en") == "Fulfilled", "fulfilled 英文翻译失败"

        print("✅ PASS - 发货状态翻译正常")
        return True
    except Exception as e:
        print(f"❌ FAIL - {e}")
        return False


def test_translate_tracking_status():
    """测试 4: 物流追踪状态翻译"""
    print("测试 4: 物流追踪状态翻译")

    try:
        # 测试中文
        assert translate_tracking_status("in_transit", "zh") == "运输中", "in_transit 翻译失败"
        assert translate_tracking_status("delivered", "zh") == "已送达", "delivered 翻译失败"
        assert translate_tracking_status("out_for_delivery", "zh") == "派送中", "out_for_delivery 翻译失败"

        # 测试英文
        assert translate_tracking_status("in_transit", "en") == "In Transit", "in_transit 英文翻译失败"
        assert translate_tracking_status("delivered", "en") == "Delivered", "delivered 英文翻译失败"

        print("✅ PASS - 物流追踪状态翻译正常")
        return True
    except Exception as e:
        print(f"❌ FAIL - {e}")
        return False


def test_translate_financial_status():
    """测试 5: 支付状态翻译"""
    print("测试 5: 支付状态翻译")

    try:
        assert translate_financial_status("paid", "zh") == "已支付", "paid 翻译失败"
        assert translate_financial_status("refunded", "zh") == "已退款", "refunded 翻译失败"
        assert translate_financial_status("pending", "en") == "Pending", "pending 英文翻译失败"

        print("✅ PASS - 支付状态翻译正常")
        return True
    except Exception as e:
        print(f"❌ FAIL - {e}")
        return False


def test_generate_tracking_message():
    """测试 6: 客服话术生成"""
    print("测试 6: 客服话术生成")

    try:
        # 测试有物流信息的情况（中文）
        msg = generate_tracking_message(
            order_number="#UK22080",
            tracking_company="Royal Mail",
            tracking_number="AB123456789GB",
            status="in_transit",
            lang="zh"
        )
        assert "#UK22080" in msg, "订单号缺失"
        assert "Royal Mail" in msg, "承运商缺失"
        assert "AB123456789GB" in msg, "运单号缺失"
        assert "运输中" in msg, "状态缺失"
        assert "追踪链接" in msg, "追踪链接缺失"

        # 测试无物流信息的情况
        msg = generate_tracking_message(
            order_number="#UK22080",
            tracking_company=None,
            tracking_number=None,
            status=None,
            lang="zh"
        )
        assert "尚未发货" in msg, "未发货提示缺失"

        # 测试英文
        msg = generate_tracking_message(
            order_number="#UK22080",
            tracking_company="Royal Mail",
            tracking_number="AB123456789GB",
            status="delivered",
            lang="en"
        )
        assert "Delivered" in msg, "英文状态缺失"
        assert "Tracking Link" in msg, "英文追踪链接缺失"

        print("✅ PASS - 客服话术生成正常")
        return True
    except Exception as e:
        print(f"❌ FAIL - {e}")
        return False


def test_enrich_tracking_data():
    """测试 7: 物流数据丰富"""
    print("测试 7: 物流数据丰富")

    try:
        # 测试数据
        tracking_data = {
            "order_number": "#UK22080",
            "fulfillment_status": "fulfilled",
            "primary_tracking": {
                "company": "Royal Mail",
                "number": "AB123456789GB",
                "status": "in_transit"
            }
        }

        enriched = enrich_tracking_data(tracking_data)

        # 检查添加的字段
        assert "fulfillment_status_zh" in enriched, "缺少中文发货状态"
        assert "fulfillment_status_en" in enriched, "缺少英文发货状态"
        assert enriched["fulfillment_status_zh"] == "已发货", "发货状态翻译错误"

        # 检查物流信息丰富
        primary = enriched["primary_tracking"]
        assert "company_normalized" in primary, "缺少标准化承运商名称"
        assert "status_zh" in primary, "缺少中文物流状态"
        assert "tracking_url_generated" in primary, "缺少生成的追踪链接"

        # 检查客服话术
        assert "message_template_zh" in enriched, "缺少中文话术"
        assert "message_template_en" in enriched, "缺少英文话术"

        print("✅ PASS - 物流数据丰富正常")
        return True
    except Exception as e:
        print(f"❌ FAIL - {e}")
        return False


def run_tests():
    """运行所有测试"""
    print("=" * 50)
    print("物流状态翻译模块测试")
    print("=" * 50)
    print()

    passed = 0
    failed = 0

    tests = [
        test_normalize_carrier_name,
        test_get_tracking_url,
        test_translate_fulfillment_status,
        test_translate_tracking_status,
        test_translate_financial_status,
        test_generate_tracking_message,
        test_enrich_tracking_data,
    ]

    for test in tests:
        if test():
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
