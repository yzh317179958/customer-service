"""
物流轨迹查询 API

提供物流轨迹查询接口，供前端展示物流时间线。

端点:
- GET /api/tracking/{tracking_number} - 查询物流轨迹
"""

import logging
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.tracking import get_tracking_service, TrackingStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tracking", tags=["物流追踪"])


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
    refresh: bool = False,
):
    """
    查询物流轨迹

    Args:
        tracking_number: 运单号
        carrier: 承运商代码（可选）
        order_id: 订单 ID（可选，用于自动注册）
        refresh: 是否强制刷新缓存

    Returns:
        物流轨迹信息，如果正在追踪中则 is_pending=True
    """
    logger.info(f"查询物流轨迹: {tracking_number}, order_id={order_id}")

    try:
        service = get_tracking_service()

        # 使用自动注册方法获取物流信息
        info = await service.get_tracking_info_with_auto_register(
            tracking_number=tracking_number,
            carrier=carrier,
            order_id=order_id,
        )

        # 如果是 pending 状态，直接返回
        if info.is_pending:
            return TrackingResponse(
                tracking_number=info.tracking_number,
                current_status="NotFound",
                current_status_zh=info.status_zh or "追踪中",
                is_delivered=False,
                is_exception=False,
                is_pending=True,
                event_count=0,
                events=[],
                order_id=info.order_id,
            )

        # 构建完整响应
        carrier_resp = None
        if info.carrier:
            carrier_resp = CarrierResponse(
                code=info.carrier.code,
                name=info.carrier.name,
                url=info.carrier.url,
            )

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

        return TrackingResponse(
            tracking_number=info.tracking_number,
            carrier=carrier_resp,
            current_status=info.status.value if info.status else "unknown",
            current_status_zh=info.status_zh or "未知",
            is_delivered=info.is_delivered,
            is_exception=info.is_exception,
            is_pending=False,
            event_count=len(info.events),
            events=events_resp,
            last_updated=last_updated,
            order_id=info.order_id,
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
