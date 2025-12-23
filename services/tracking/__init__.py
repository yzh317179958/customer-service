"""
物流追踪服务 (services/tracking)

封装 17track API，提供物流追踪能力。

主要功能：
- 运单注册：将运单号注册到 17track 进行追踪
- 轨迹查询：获取完整物流轨迹事件
- Webhook 解析：解析 17track 推送的状态变更数据
- 运单→订单映射：通过运单号查找关联订单

使用示例：
    from services.tracking import Track17Client, get_track17_client

    client = get_track17_client()

    # 注册运单
    result = await client.register_tracking("AB123456789GB", "royalmail")

    # 查询轨迹
    info = await client.get_tracking_info("AB123456789GB")
"""

# Step 1.2: 客户端
from .client import Track17Client, Track17Error, get_track17_client

# Step 1.3: 数据模型和 Webhook 解析
from .models import (
    TrackingStatus,
    TrackingSubStatus,
    TrackingEvent,
    CarrierInfo,
    TrackingInfo,
    WebhookEvent,
)
from .webhook import (
    parse_17track_push,
    parse_17track_batch_push,
    verify_webhook_signature,
    is_delivery_event,
    is_exception_event,
    get_exception_type,
)

# Step 1.4: 服务层
from .service import TrackingService, get_tracking_service

__all__ = [
    # 客户端
    "Track17Client",
    "Track17Error",
    "get_track17_client",
    # 数据模型
    "TrackingStatus",
    "TrackingSubStatus",
    "TrackingEvent",
    "CarrierInfo",
    "TrackingInfo",
    "WebhookEvent",
    # Webhook 解析
    "parse_17track_push",
    "parse_17track_batch_push",
    "verify_webhook_signature",
    "is_delivery_event",
    "is_exception_event",
    "get_exception_type",
    # 服务层
    "TrackingService",
    "get_tracking_service",
]
