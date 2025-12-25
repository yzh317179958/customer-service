"""
物流轨迹查询 API

提供物流轨迹查询接口，供前端展示物流时间线。

端点:
- GET /api/tracking/{tracking_number} - 查询物流轨迹
"""

import os
import logging
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.tracking import get_tracking_service, TrackingStatus
from services.shopify.sites import get_all_configured_sites
from services.shopify import get_shopify_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tracking", tags=["物流追踪"])

# ============ 承运商配置 ============

# 小众承运商列表（通常不支持或更新慢）
MINOR_CARRIERS = {"yunway", "yunexpress", "yun express", "cne express", "cneexpress", "4px", "yanwen"}

# 承运商官网追踪链接模板
CARRIER_TRACKING_URL_TEMPLATES = {
    "fedex": "https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
    "ups": "https://www.ups.com/track?tracknum={tracking_number}",
    "dhl": "https://www.dhl.com/en/express/tracking.html?AWB={tracking_number}",
    "dhl express": "https://www.dhl.com/en/express/tracking.html?AWB={tracking_number}",
    "royal mail": "https://www.royalmail.com/track-your-item#{tracking_number}",
    "royalmail": "https://www.royalmail.com/track-your-item#{tracking_number}",
    "dpd": "https://www.dpd.co.uk/tracking?parcel={tracking_number}",
    "dpd uk": "https://www.dpd.co.uk/tracking?parcel={tracking_number}",
    "evri": "https://www.evri.com/track/parcel/{tracking_number}",
    "hermes": "https://www.evri.com/track/parcel/{tracking_number}",
    "dx": "https://my.dxdelivery.com/",
    "dx freight": "https://my.dxdelivery.com/",
    "gls": "https://gls-group.eu/track/{tracking_number}",
    "yodel": "https://www.yodel.co.uk/tracking/{tracking_number}",
    "parcelforce": "https://www.parcelforce.com/track-trace?trackNumber={tracking_number}",
    "usps": "https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}",
    "tnt": "https://www.tnt.com/express/en_gb/site/shipping-tools/track.html?searchType=con&cons={tracking_number}",
}


def _get_carrier_tracking_url(tracking_number: str, carrier: Optional[str]) -> str:
    """
    获取承运商官网追踪链接

    Args:
        tracking_number: 运单号
        carrier: 承运商名称

    Returns:
        承运商官网追踪链接，未找到时返回 17track 链接
    """
    if carrier:
        carrier_lower = carrier.lower().strip()
        # 精确匹配
        if carrier_lower in CARRIER_TRACKING_URL_TEMPLATES:
            return CARRIER_TRACKING_URL_TEMPLATES[carrier_lower].format(tracking_number=tracking_number)
        # 模糊匹配
        for key, template in CARRIER_TRACKING_URL_TEMPLATES.items():
            if key in carrier_lower or carrier_lower in key:
                return template.format(tracking_number=tracking_number)

    # 默认返回 17track 查询页面
    return f"https://t.17track.net/en#nums={tracking_number}"


def _is_minor_carrier(carrier: Optional[str]) -> bool:
    """判断是否为小众承运商"""
    if not carrier:
        return False
    return carrier.lower().strip() in MINOR_CARRIERS


def _generate_friendly_message(
    info,
    carrier: Optional[str] = None,
    is_pending: bool = False,
) -> tuple:
    """
    生成友好提示信息

    根据不同的物流状态生成对应的友好英文提示，帮助用户理解当前情况。

    Args:
        info: 物流信息对象
        carrier: 承运商名称
        is_pending: 是否正在追踪中

    Returns:
        (message, tracking_url) 元组
    """
    tracking_url = _get_carrier_tracking_url(info.tracking_number, carrier)

    # 场景 1: 正在后台注册追踪中
    if is_pending:
        return (
            "Fetching tracking info, please refresh in 1-2 minutes.",
            tracking_url
        )

    # 场景 2: 运单过期
    if info.status == TrackingStatus.EXPIRED:
        return (
            "This tracking record has expired (over 90 days).",
            tracking_url
        )

    # 场景 3: 异常状态 - 根据子状态细分
    if info.status == TrackingStatus.ALERT:
        sub_status = getattr(info, 'sub_status', None) or ''
        alert_messages = {
            "Alert_AddressIssue": "Address issue detected. Please verify your address and contact seller.",
            "Alert_CustomsIssue": "Package held at customs. Additional documents may be required.",
            "Alert_Damaged": "Package damaged in transit. Please contact seller.",
            "Alert_Lost": "Package may be lost. Please contact seller or carrier for claim.",
            "Alert_Returned": "Package returned to sender. Please contact seller.",
        }
        message = alert_messages.get(sub_status, "Shipping exception occurred. Please contact seller or carrier.")
        return (message, tracking_url)

    # 场景 4: 未送达状态
    if info.status == TrackingStatus.UNDELIVERED:
        sub_status = getattr(info, 'sub_status', None) or ''
        undelivered_messages = {
            "Undelivered_NoOneHome": "No one home during delivery. Carrier will retry or leave a notice.",
            "Undelivered_Refused": "Delivery refused. Package will be returned. Please contact seller.",
        }
        message = undelivered_messages.get(sub_status, "Delivery unsuccessful. Carrier will reschedule.")
        return (message, tracking_url)

    # 场景 5: 待取件
    if info.status == TrackingStatus.PICK_UP:
        return (
            "Package ready for pickup at collection point.",
            tracking_url
        )

    # 场景 6: 派送中
    if info.status == TrackingStatus.OUT_FOR_DELIVERY:
        return (
            "Package out for delivery. Expected to arrive today.",
            tracking_url
        )

    # 场景 7: 已签收但无轨迹详情
    if info.status == TrackingStatus.DELIVERED and len(info.events) == 0:
        return (
            "Package delivered, but detailed tracking is not available.",
            tracking_url
        )

    # 场景 8: NotFound - 区分新运单和不支持的承运商
    if info.status == TrackingStatus.NOT_FOUND:
        if _is_minor_carrier(carrier):
            return (
                "This carrier doesn't support online tracking. Click 'Track' to check carrier website.",
                tracking_url
            )
        else:
            return (
                "Tracking info syncing. New shipments usually take 24-48 hours to update.",
                tracking_url
            )

    # 其他情况：有轨迹数据，无需特殊提示
    return ("", tracking_url)

def _status_text_en(status: Optional[TrackingStatus], *, is_pending: bool = False) -> str:
    if is_pending:
        return "Tracking"
    if not status:
        return "Unknown"
    mapping = {
        TrackingStatus.NOT_FOUND: "No tracking info",
        TrackingStatus.INFO_RECEIVED: "Info received",
        TrackingStatus.IN_TRANSIT: "In transit",
        TrackingStatus.PICK_UP: "Ready for pickup",
        TrackingStatus.OUT_FOR_DELIVERY: "Out for delivery",
        TrackingStatus.UNDELIVERED: "Undelivered",
        TrackingStatus.DELIVERED: "Delivered",
        TrackingStatus.ALERT: "Exception",
        TrackingStatus.EXPIRED: "Expired",
    }
    return mapping.get(status, "Unknown")


# ============ 响应模型 ============

class TrackingEventResponse(BaseModel):
    """物流事件响应"""
    timestamp: Optional[str] = Field(None, description="事件时间 ISO 格式")
    status: Optional[str] = Field(None, description="状态描述")
    status_zh: Optional[str] = Field(None, description="状态描述（中文）")
    location: Optional[str] = Field(None, description="事件地点")
    description: Optional[str] = Field(None, description="事件详情")


class CarrierResponse(BaseModel):
    """承运商响应"""
    code: Optional[int] = Field(None, description="承运商代码")
    name: Optional[str] = Field(None, description="承运商名称")
    url: Optional[str] = Field(None, description="承运商官网")


class TrackingResponse(BaseModel):
    """物流轨迹响应"""
    tracking_number: str = Field(..., description="运单号")
    carrier: Optional[CarrierResponse] = Field(None, description="承运商信息")
    current_status: Optional[str] = Field(None, description="当前状态")
    current_status_zh: Optional[str] = Field(None, description="当前状态（中文）")
    is_delivered: bool = Field(False, description="是否已签收")
    is_exception: bool = Field(False, description="是否有异常")
    is_pending: bool = Field(False, description="是否正在追踪中（后台注册中）")
    event_count: int = Field(0, description="事件数量")
    events: List[TrackingEventResponse] = Field(
        default_factory=list, description="物流事件列表"
    )
    last_updated: Optional[str] = Field(None, description="最后更新时间")
    order_id: Optional[str] = Field(None, description="关联订单 ID")
    message: Optional[str] = Field(None, description="提示信息（轨迹不可用时显示）")
    message_zh: Optional[str] = Field(None, description="提示信息（中文）")
    tracking_url: Optional[str] = Field(None, description="承运商官方追踪链接")
    debug: Optional[dict] = Field(None, description="调试信息（仅 debug=1 时返回）")


# ============ API 端点 ============

@router.get(
    "/{tracking_number}",
    response_model=TrackingResponse,
    summary="查询物流轨迹",
    description="根据运单号查询物流轨迹信息，支持自动注册未注册的运单",
)
async def get_tracking(
    tracking_number: str,
    carrier: Optional[str] = None,
    order_id: Optional[str] = None,
    order_number: Optional[str] = None,
    postal_code: Optional[str] = None,
    refresh: bool = False,
    debug: Optional[str] = Query(
        None,
        description="调试开关：true/1/on/yes 时返回 debug 字段",
    ),
):
    """
    查询物流轨迹

    Args:
        tracking_number: 运单号
        carrier: 承运商代码（可选）
        order_id: 订单 ID（可选，用于自动注册）
        order_number: 订单号（可选，用于从 Shopify 获取邮编）
        postal_code: 目的地邮编（可选，某些承运商如 DX FREIGHT 需要）
        refresh: 是否强制刷新缓存

    Returns:
        物流轨迹信息，如果正在追踪中则 is_pending=True
    """
    logger.info(f"查询物流轨迹: {tracking_number}, order_id={order_id}, order_number={order_number}, postal_code={postal_code}")

    try:
        service = get_tracking_service()

        postal_code_source = "query" if postal_code else None
        # 如果有订单号但没有邮编，尝试从 Shopify 获取
        if order_number and not postal_code:
            postal_code = await _get_postal_code_from_order(order_number)
            if postal_code:
                postal_code_source = "shopify"
                logger.info(f"从订单 {order_number} 获取到邮编: {postal_code}")

        if refresh:
            await service.clear_cache(tracking_number)

        # 使用自动注册方法获取物流信息
        info = await service.get_tracking_info_with_auto_register(
            tracking_number=tracking_number,
            carrier=carrier,
            order_id=order_id,
            order_number=order_number,
            destination_postal_code=postal_code,
            refresh=refresh,
        )

        debug_enabled = str(debug).lower() in {"1", "true", "on", "yes"}

        debug_info = None
        if debug_enabled:
            has_track17_api_key = bool(os.getenv("TRACK17_API_KEY"))
            configured_shopify_sites = sorted(get_all_configured_sites().keys())
            carrier_lower = (carrier or "").lower()
            carrier_maybe_dx = "dx" in carrier_lower
            pending_reason_guess = None
            if not has_track17_api_key:
                pending_reason_guess = "TRACK17_API_KEY 未配置，无法查询/注册到 17track"
            elif carrier_maybe_dx and not postal_code:
                pending_reason_guess = "DX 承运商通常需要目的地邮编；当前请求未拿到 postal_code"
            elif not order_number:
                pending_reason_guess = "未传 order_number，后端无法从订单自动获取邮编（DX 场景会一直 pending）"

            debug_info = {
                "tracking_number": tracking_number,
                "carrier": carrier,
                "order_id": order_id,
                "order_number": order_number,
                "postal_code": postal_code,
                "postal_code_source": postal_code_source,
                "refresh": refresh,
                "has_track17_api_key": has_track17_api_key,
                "configured_shopify_sites": configured_shopify_sites,
                "info_is_pending": bool(getattr(info, "is_pending", False)),
                "info_status": getattr(getattr(info, "status", None), "value", None),
                "info_events_count": len(getattr(info, "events", []) or []),
                "pending_reason_guess": pending_reason_guess,
                "tips": [
                    "如果一直 pending：先确认后端环境变量 TRACK17_API_KEY 已配置",
                    "DX 承运商：需要订单收货邮编；确保请求带上 order_number 或 postal_code",
                    "pending 是异步注册机制：首次点击可能 pending，稍后携带 refresh=1 再点一次"
                ]
            }

            # debug 模式：如果仍 pending，尝试同步触发一次注册并立即重查，拿到 17track 的拒绝原因
            if getattr(info, "is_pending", False):
                register_result = None
                register_error = None
                refetch_error = None
                try:
                    register_result = await service.client.register_tracking(
                        tracking_number=tracking_number,
                        carrier_code=carrier,
                        order_id=order_id,
                        tag=None,
                        destination_postal_code=postal_code,
                    )
                except Exception as exc:
                    register_error = str(exc)

                try:
                    refetched = await service.get_tracking_info(
                        tracking_number=tracking_number,
                        carrier=carrier,
                        use_cache=False,
                    )
                    if refetched and (
                        refetched.events
                        or (refetched.status and refetched.status != TrackingStatus.NOT_FOUND)
                    ):
                        info = refetched
                        debug_info["info_is_pending"] = False
                        debug_info["info_status"] = getattr(getattr(info, "status", None), "value", None)
                        debug_info["info_events_count"] = len(getattr(info, "events", []) or [])
                except Exception as exc:
                    refetch_error = str(exc)

                debug_info["debug_register"] = {
                    "attempted": True,
                    "register_result": register_result,
                    "register_error": register_error,
                    "refetch_error": refetch_error,
                }

            try:
                debug_info["code_location"] = {
                    "handler_file": __file__,
                    "handler_mtime": os.path.getmtime(__file__),
                    "tracking_service_file": getattr(service.__class__, "__module__", None),
                }
            except Exception:
                pass

        # 如果是 pending 状态，直接返回
        if info.is_pending:
            pending_message, pending_tracking_url = _generate_friendly_message(
                info,
                carrier=carrier,
                is_pending=True,
            )
            return TrackingResponse(
                tracking_number=info.tracking_number,
                current_status="NotFound",
                current_status_zh=_status_text_en(info.status, is_pending=True),
                is_delivered=False,
                is_exception=False,
                is_pending=True,
                event_count=0,
                events=[],
                order_id=info.order_id,
                message=pending_message,
                tracking_url=pending_tracking_url,
                debug=debug_info,
            )

        # 构建完整响应
        carrier_resp = None
        carrier_name = None
        carrier_url = None
        if info.carrier:
            carrier_resp = CarrierResponse(
                code=info.carrier.code,
                name=info.carrier.name,
                url=info.carrier.url,
            )
            carrier_name = info.carrier.name
            carrier_url = info.carrier.url

        # 如果 17track 没有返回承运商名称，使用请求参数中的 carrier
        if not carrier_name and carrier:
            carrier_name = carrier.upper()
            # 常见承运商官网映射
            carrier_urls = {
                "DX": "https://my.dxdelivery.com/",
                "DX FREIGHT": "https://my.dxdelivery.com/",
                "UPS": "https://www.ups.com/track",
                "FEDEX": "https://www.fedex.com/fedextrack/",
                "DHL": "https://www.dhl.com/global-en/home/tracking.html",
                "YUNWAY": "https://www.yuntrack.com/",
                "ROYAL MAIL": "https://www.royalmail.com/track-your-item",
                "DPD": "https://www.dpd.co.uk/tracking",
                "EVRI": "https://www.evri.com/track-a-parcel",
                "HERMES": "https://www.evri.com/track-a-parcel",
            }
            carrier_url = carrier_urls.get(carrier_name, carrier_urls.get(carrier.upper()))

        events_resp = [
            TrackingEventResponse(
                timestamp=e.timestamp.isoformat() if e.timestamp else e.timestamp_str,
                status=e.status,
                status_zh=e.status_zh,
                location=e.location,
                description=e.description or e.status,
            )
            for e in info.events
        ]

        # 最后更新时间
        last_updated = None
        if info.last_event and info.last_event.timestamp:
            last_updated = info.last_event.timestamp.isoformat()
        elif info.events and info.events[0].timestamp:
            last_updated = info.events[0].timestamp.isoformat()

        # 生成友好提示信息
        message, tracking_url = _generate_friendly_message(
            info,
            carrier=carrier_name or carrier,
            is_pending=False,
        )

        return TrackingResponse(
            tracking_number=info.tracking_number,
            carrier=carrier_resp,
            current_status=info.status.value if info.status else "unknown",
            current_status_zh=_status_text_en(info.status),
            is_delivered=info.is_delivered,
            is_exception=info.is_exception,
            is_pending=False,
            event_count=len(info.events),
            events=events_resp,
            last_updated=last_updated,
            order_id=info.order_id,
            message=message if message else None,
            tracking_url=tracking_url if tracking_url else None,
            debug=debug_info,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询物流轨迹失败: {tracking_number}, 错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"查询物流轨迹失败: {str(e)}",
        )


@router.get(
    "/{tracking_number}/status",
    summary="查询物流状态",
    description="仅查询运单当前状态（轻量接口）",
)
async def get_tracking_status(
    tracking_number: str,
    carrier: Optional[str] = None,
):
    """
    查询物流状态（轻量接口）

    Args:
        tracking_number: 运单号
        carrier: 承运商代码（可选）

    Returns:
        状态信息
    """
    try:
        service = get_tracking_service()
        status = await service.get_status(tracking_number, carrier)

        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"未找到运单 {tracking_number} 的状态信息",
            )

        return {
            "tracking_number": tracking_number,
            "status": status.value,
            "status_zh": status.zh,
            "is_delivered": status == TrackingStatus.DELIVERED,
            "is_exception": status.is_exception,
            "is_final": status.is_final,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询物流状态失败: {tracking_number}, 错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"查询物流状态失败: {str(e)}",
        )


# ============ 辅助函数 ============

async def _get_postal_code_from_order(order_number: str) -> Optional[str]:
    """
    从 Shopify 订单中获取收货地址邮编

    Args:
        order_number: 订单号（如 UK22080）

    Returns:
        邮编字符串，如果获取失败返回 None
    """
    try:
        # 从订单号判断站点
        site = "uk" if order_number.upper().startswith("UK") else "de"
        shopify = get_shopify_service(site)

        # 查询订单
        result = await shopify.search_order_by_number(order_number)
        if not result or not result.get("order"):
            logger.warning(f"订单 {order_number} 未找到")
            return None

        order = result["order"]

        # 获取收货地址邮编
        shipping_address = order.get("shipping_address", {})
        postal_code = shipping_address.get("zip") or shipping_address.get("postal_code")

        if postal_code:
            return postal_code.strip()

        logger.warning(f"订单 {order_number} 没有收货地址邮编")
        return None

    except Exception as e:
        logger.error(f"从订单获取邮编失败: {order_number}, 错误: {e}")
        return None
