"""
物流状态翻译与承运商识别

提供物流状态的中英文翻译，以及承运商追踪链接生成。
"""

from typing import Optional, Dict


# ==================== 承运商追踪链接模板 ====================

CARRIER_TRACKING_URLS = {
    # UK 常见承运商
    "Royal Mail": "https://www.royalmail.com/track-your-item#/tracking-results/{tracking_number}",
    "DPD": "https://www.dpd.co.uk/tracking/trackingSearch.do?parcelNumber={tracking_number}",
    "DPD UK": "https://www.dpd.co.uk/tracking/trackingSearch.do?parcelNumber={tracking_number}",
    "Hermes": "https://www.evri.com/track-a-parcel/{tracking_number}",
    "Evri": "https://www.evri.com/track-a-parcel/{tracking_number}",
    "Yodel": "https://www.yodel.co.uk/tracking/{tracking_number}",
    "Parcelforce": "https://www.parcelforce.com/track-trace?trackNumber={tracking_number}",

    # DX (大件物流)
    "DX": "https://www.dxdelivery.com/track/?ref={tracking_number}",
    "DX Freight": "https://www.dxdelivery.com/track/?ref={tracking_number}",
    "DX FREIGHT": "https://www.dxdelivery.com/track/?ref={tracking_number}",
    "DX Delivery": "https://www.dxdelivery.com/track/?ref={tracking_number}",

    # 国际承运商
    "UPS": "https://www.ups.com/track?tracknum={tracking_number}",
    "DHL": "https://www.dhl.com/en/express/tracking.html?AWB={tracking_number}",
    "DHL Express": "https://www.dhl.com/en/express/tracking.html?AWB={tracking_number}",
    "FedEx": "https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
    "TNT": "https://www.tnt.com/express/en_gb/site/shipping-tools/tracking.html?searchType=con&cons={tracking_number}",

    # 中国承运商（跨境电商常用）
    "YunExpress": "https://www.yuntrack.com/Track/Result?TrackingNumber={tracking_number}",
    "YUNWAY": "https://www.yuntrack.com/Track/Result?TrackingNumber={tracking_number}",
    "Yanwen": "https://track.yw56.com.cn/en-US/Track?chnNumbers={tracking_number}",
    "4PX": "https://track.4px.com/?locale=en_US&track_no={tracking_number}",
    "CNE Express": "https://www.cne.com/track?tracking_number={tracking_number}",
    "SF Express": "https://www.sf-express.com/uk/en/dynamic_function/waybill/#search/bill-number/{tracking_number}",

    # 其他
    "PostNL": "https://postnl.post/tracktrace/?B={tracking_number}",
    "GLS": "https://gls-group.eu/track/{tracking_number}",
}

# 承运商名称标准化映射
CARRIER_ALIASES = {
    # Royal Mail
    "royalmail": "Royal Mail",
    "royal-mail": "Royal Mail",
    "royal_mail": "Royal Mail",

    # DPD
    "dpd": "DPD",
    "dpd uk": "DPD UK",
    "dpduk": "DPD UK",

    # Hermes/Evri
    "hermes": "Evri",
    "evri": "Evri",
    "myhermes": "Evri",

    # DX (大件物流)
    "dx": "DX",
    "dx freight": "DX FREIGHT",
    "dxfreight": "DX FREIGHT",
    "dx-freight": "DX FREIGHT",
    "dx_freight": "DX FREIGHT",
    "dx delivery": "DX Delivery",
    "dxdelivery": "DX Delivery",

    # DHL
    "dhl": "DHL",
    "dhl express": "DHL Express",
    "dhlexpress": "DHL Express",

    # UPS
    "ups": "UPS",
    "plupseu": "UPS",  # UPS 欧洲变体

    # FedEx
    "fedex": "FedEx",

    # Yodel
    "yodel": "Yodel",

    # SF Express
    "sf express": "SF Express",
    "sf-express": "SF Express",
    "sfexpress": "SF Express",
    "顺丰": "SF Express",

    # YUNWAY / YunExpress
    "yunway": "YUNWAY",
    "yunexpress": "YunExpress",
    "yun express": "YunExpress",
}


# ==================== 物流状态翻译 ====================

# Shopify 订单级发货状态 (order.fulfillment_status)
FULFILLMENT_STATUS_TRANSLATION = {
    # 订单发货状态
    None: {"en": "Processing", "zh": "处理中"},
    "null": {"en": "Processing", "zh": "处理中"},
    "unfulfilled": {"en": "Processing", "zh": "处理中"},
    "partial": {"en": "Partially Shipped", "zh": "部分发货"},
    "fulfilled": {"en": "Shipped", "zh": "已发货"},
}

# Shopify 发货记录状态和物流运输状态
# 注意区分两种状态：
#   - fulfillment.status: 发货操作状态（success=发货成功，不是送达成功）
#   - fulfillment.shipment_status: 物流运输状态（delivered=已送达，in_transit=运输中）
# 我们的 delivery_status 优先使用 shipment_status，其次是退款状态
FULFILLMENT_RECORD_STATUS_TRANSLATION = {
    # 物流运输状态 (shipment_status) - 真正的送达状态
    "delivered": {"en": "Received", "zh": "已收货"},  # 物流已送达
    "in_transit": {"en": "In Transit", "zh": "运输中"},  # 运输中
    "out_for_delivery": {"en": "Out for Delivery", "zh": "派送中"},  # 派送中
    "failure": {"en": "Delivery Failed", "zh": "投递失败"},  # 投递失败

    # 发货操作状态 (fulfillment.status) - 仅表示发货操作成功
    "pending": {"en": "Pending", "zh": "待处理"},
    "open": {"en": "Open", "zh": "已创建"},
    "success": {"en": "Received", "zh": "已收货"},  # 兼容旧逻辑：success → 已收货
    "cancelled": {"en": "Cancelled", "zh": "已取消"},
    "error": {"en": "Error", "zh": "错误"},

    # 服务类商品状态
    "active": {"en": "Active", "zh": "已生效"},
    "expired": {"en": "Expired", "zh": "已失效"},
    "service": {"en": "Active", "zh": "已生效"},

    # 退款相关状态
    "refunded": {"en": "Refunded", "zh": "已退款"},
    "returned": {"en": "Returned & Refunded", "zh": "已退货退款"},
}

# 物流追踪状态（通用，用于第三方物流API）
TRACKING_STATUS_TRANSLATION = {
    "pending": {"en": "Pending", "zh": "待揽收"},
    "label_created": {"en": "Label Created", "zh": "已创建标签"},
    "label_printed": {"en": "Label Printed", "zh": "标签已打印"},
    "attempted_delivery": {"en": "Attempted Delivery", "zh": "尝试投递"},
    "ready_for_pickup": {"en": "Ready for Pickup", "zh": "待取件"},
    "confirmed": {"en": "Confirmed", "zh": "已确认"},
    "in_transit": {"en": "In Transit", "zh": "运输中"},
    "out_for_delivery": {"en": "Out for Delivery", "zh": "派送中"},
    "delivered": {"en": "Received", "zh": "已收货"},
    "success": {"en": "Received", "zh": "已收货"},  # Shopify 用 success 表示已收货
    "failure": {"en": "Delivery Failed", "zh": "投递失败"},
    "active": {"en": "Active", "zh": "已生效"},  # 服务类商品已生效
    "expired": {"en": "Expired", "zh": "已失效"},  # 服务类商品已失效（随实物退款）
    "refunded": {"en": "Refunded", "zh": "已退款"},  # 仅退款
    "returned": {"en": "Returned & Refunded", "zh": "已退货退款"},  # 退货退款
    "cancelled": {"en": "Cancelled", "zh": "已取消"},  # 取消退款
}

# 支付状态翻译
FINANCIAL_STATUS_TRANSLATION = {
    "pending": {"en": "Pending", "zh": "待支付"},
    "authorized": {"en": "Authorized", "zh": "已授权"},
    "paid": {"en": "Paid", "zh": "已支付"},
    "partially_paid": {"en": "Partially Paid", "zh": "部分支付"},
    "partially_refunded": {"en": "Partially Refunded", "zh": "部分退款"},
    "refunded": {"en": "Refunded", "zh": "已退款"},
    "voided": {"en": "Voided", "zh": "已作废"},
}


# ==================== 工具函数 ====================

def normalize_carrier_name(carrier: str) -> str:
    """
    标准化承运商名称

    Args:
        carrier: 原始承运商名称

    Returns:
        标准化后的承运商名称
    """
    if not carrier:
        return "Unknown"

    # 转小写并去除空格
    normalized = carrier.lower().strip()

    # 查找别名映射
    if normalized in CARRIER_ALIASES:
        return CARRIER_ALIASES[normalized]

    # 返回原始名称（首字母大写）
    return carrier.title()


def get_tracking_url(carrier: str, tracking_number: str) -> Optional[str]:
    """
    生成物流追踪链接

    Args:
        carrier: 承运商名称
        tracking_number: 运单号

    Returns:
        追踪链接，如果没有运单号返回 None，否则至少返回 17track 通用链接
    """
    if not tracking_number:
        return None

    # 如果有承运商名称，尝试使用专用链接
    if carrier:
        # 标准化承运商名称
        normalized_carrier = normalize_carrier_name(carrier)

        # 查找追踪链接模板
        template = CARRIER_TRACKING_URLS.get(normalized_carrier)

        if template:
            return template.format(tracking_number=tracking_number)

    # 回退：使用 17track 通用追踪链接（支持全球 1000+ 快递公司）
    return f"https://t.17track.net/en#nums={tracking_number}"


def translate_fulfillment_status(status: Optional[str], lang: str = "en") -> str:
    """
    翻译订单发货状态 (order.fulfillment_status)

    Args:
        status: Shopify 订单发货状态 (fulfilled/partial/null)
        lang: 目标语言 (zh/en)

    Returns:
        翻译后的状态文本
    """
    if status is None:
        status = "null"

    status_lower = status.lower() if status else "null"
    translation = FULFILLMENT_STATUS_TRANSLATION.get(status_lower, {})

    return translation.get(lang, status or "Unknown")


def translate_fulfillment_record_status(status: str, lang: str = "en") -> str:
    """
    翻译发货记录状态 (fulfillment.status)

    Args:
        status: Shopify 发货记录状态 (success/pending/cancelled/error/failure)
        lang: 目标语言 (zh/en)

    Returns:
        翻译后的状态文本
    """
    if not status:
        return "Unknown" if lang == "en" else "未知"

    status_lower = status.lower()
    translation = FULFILLMENT_RECORD_STATUS_TRANSLATION.get(status_lower, {})

    return translation.get(lang, status)


def translate_tracking_status(status: str, lang: str = "en") -> str:
    """
    翻译物流追踪状态

    Args:
        status: 物流追踪状态
        lang: 目标语言 (zh/en)

    Returns:
        翻译后的状态文本
    """
    if not status:
        return "Unknown" if lang == "en" else "未知"

    status_lower = status.lower()
    translation = TRACKING_STATUS_TRANSLATION.get(status_lower, {})

    return translation.get(lang, status)


def translate_financial_status(status: str, lang: str = "en") -> str:
    """
    翻译支付状态

    Args:
        status: 支付状态
        lang: 目标语言 (zh/en)

    Returns:
        翻译后的状态文本
    """
    if not status:
        return "Unknown" if lang == "en" else "未知"

    status_lower = status.lower()
    translation = FINANCIAL_STATUS_TRANSLATION.get(status_lower, {})

    return translation.get(lang, status)


def generate_tracking_message(
    order_number: str,
    tracking_company: Optional[str],
    tracking_number: Optional[str],
    status: Optional[str],
    estimated_delivery: Optional[str] = None,
    lang: str = "zh"
) -> str:
    """
    生成客服话术模板

    Args:
        order_number: 订单号
        tracking_company: 承运商
        tracking_number: 运单号
        status: 物流状态
        estimated_delivery: 预计送达时间
        lang: 语言

    Returns:
        格式化的物流信息文本
    """
    if lang == "zh":
        if not tracking_company or not tracking_number:
            return f"您的订单 {order_number} 尚未发货，我们会尽快为您安排发货。"

        tracking_url = get_tracking_url(tracking_company, tracking_number)
        status_text = translate_tracking_status(status, "zh") if status else "运输中"

        message = f"""您的订单 {order_number} 物流信息：
承运商: {tracking_company}
运单号: {tracking_number}
当前状态: {status_text}"""

        if estimated_delivery:
            message += f"\n预计送达: {estimated_delivery}"

        if tracking_url:
            message += f"\n\n追踪链接: {tracking_url}"

        return message

    else:  # English
        if not tracking_company or not tracking_number:
            return f"Your order {order_number} has not been shipped yet. We will arrange shipment as soon as possible."

        tracking_url = get_tracking_url(tracking_company, tracking_number)
        status_text = translate_tracking_status(status, "en") if status else "In Transit"

        message = f"""Your order {order_number} tracking information:
Carrier: {tracking_company}
Tracking Number: {tracking_number}
Current Status: {status_text}"""

        if estimated_delivery:
            message += f"\nEstimated Delivery: {estimated_delivery}"

        if tracking_url:
            message += f"\n\nTracking Link: {tracking_url}"

        return message


def enrich_tracking_data(tracking_data: Dict) -> Dict:
    """
    丰富物流数据，添加翻译和追踪链接

    Args:
        tracking_data: 原始物流数据

    Returns:
        添加了翻译和链接的物流数据
    """
    enriched = tracking_data.copy()

    # 添加订单级发货状态翻译 (order.fulfillment_status)
    if "fulfillment_status" in enriched:
        enriched["fulfillment_status_zh"] = translate_fulfillment_status(
            enriched["fulfillment_status"], "zh"
        )
        enriched["fulfillment_status_en"] = translate_fulfillment_status(
            enriched["fulfillment_status"], "en"
        )

    # 为每个发货记录添加状态翻译
    if "fulfillments" in enriched:
        for f in enriched["fulfillments"]:
            if f.get("status"):
                f["status_zh"] = translate_fulfillment_record_status(f["status"], "zh")
                f["status_en"] = translate_fulfillment_record_status(f["status"], "en")

    # 处理主要物流信息
    if "primary_tracking" in enriched:
        primary = enriched["primary_tracking"]

        if primary.get("company"):
            # 标准化承运商名称
            primary["company_normalized"] = normalize_carrier_name(primary["company"])

            # 生成追踪链接（如果原始链接为空）
            if primary.get("number"):
                tracking_url = get_tracking_url(primary["company"], primary["number"])
                if tracking_url:
                    primary["tracking_url_generated"] = tracking_url
                    # 如果原始 url 为空，使用生成的链接
                    if not primary.get("url"):
                        primary["url"] = tracking_url

        # 为主物流信息添加状态翻译（使用发货记录状态翻译）
        if primary.get("status"):
            primary["status_zh"] = translate_fulfillment_record_status(primary["status"], "zh")
            primary["status_en"] = translate_fulfillment_record_status(primary["status"], "en")

    # 生成客服话术
    if "order_number" in enriched:
        primary = enriched.get("primary_tracking", {})
        enriched["message_template_zh"] = generate_tracking_message(
            enriched["order_number"],
            primary.get("company"),
            primary.get("number"),
            primary.get("status"),
            lang="zh"
        )
        enriched["message_template_en"] = generate_tracking_message(
            enriched["order_number"],
            primary.get("company"),
            primary.get("number"),
            primary.get("status"),
            lang="en"
        )

    return enriched
