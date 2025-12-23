"""
17track Webhook 解析模块

解析 17track 推送的物流状态变更数据。

参考文档：https://help.17track.net/hc/en-us/articles/6089896188569-Webhook-push
"""

import hmac
import hashlib
import json
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

from .models import (
    TrackingStatus,
    TrackingEvent,
    WebhookEvent,
)


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: Optional[str] = None,
) -> bool:
    """
    验证 17track Webhook 签名

    17track 使用 HMAC-SHA256 签名验证推送请求的真实性。
    签名位于请求头 X-17track-Signature 中。

    Args:
        payload: 请求体原始字节
        signature: 请求头中的签名值
        secret: Webhook 密钥（从 .env 读取）

    Returns:
        bool: 签名是否有效
    """
    if not secret:
        secret = os.getenv("TRACK17_WEBHOOK_SECRET", "")

    if not secret:
        # 未配置密钥时，跳过验证（开发环境）
        return True

    # 计算 HMAC-SHA256
    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    # 安全比较，防止时序攻击
    return hmac.compare_digest(expected, signature)


def parse_17track_push(data: Dict[str, Any]) -> Optional[WebhookEvent]:
    """
    解析 17track Webhook 推送数据

    17track 推送格式示例：
    {
        "event": "TRACKING_UPDATED",
        "data": {
            "number": "AB123456789GB",
            "carrier": 21051,
            "tag": "order_12345",
            "track": {
                "e": 20,           # 状态码
                "f": "InTransit_PickedUp",  # 子状态
                "z0": {            # 最新事件
                    "a": "2024-12-22 10:30:00",
                    "b": 20,
                    "c": "Package in transit",
                    "d": "London, UK"
                }
            }
        }
    }

    Args:
        data: Webhook 推送的 JSON 数据

    Returns:
        WebhookEvent: 解析后的事件对象，解析失败返回 None
    """
    try:
        event_type = data.get("event", "")
        event_data = data.get("data", {})

        if not event_data:
            return None

        # 基础信息
        tracking_number = event_data.get("number", "")
        carrier_code = event_data.get("carrier")
        tag = event_data.get("tag")  # 注册时设置的自定义标签

        # 状态信息
        track = event_data.get("track", {})
        status_code = track.get("e")
        sub_status = track.get("f")

        new_status = None
        if status_code is not None:
            new_status = TrackingStatus.from_code(status_code)

        # 最新事件
        last_event_data = track.get("z0", {})
        last_event = None
        if last_event_data:
            last_event = TrackingEvent.from_17track_event(last_event_data)

        # 推送时间
        push_time = datetime.now()

        # 从 tag 中提取订单 ID（如果格式为 "order_xxxxx"）
        order_id = None
        if tag and tag.startswith("order_"):
            order_id = tag[6:]  # 去掉 "order_" 前缀

        return WebhookEvent(
            event_type=event_type,
            tracking_number=tracking_number,
            carrier_code=carrier_code,
            new_status=new_status,
            sub_status=sub_status,
            last_event=last_event,
            push_time=push_time,
            tag=tag,
            order_id=order_id,
            raw_data=data,
        )

    except Exception as e:
        # 解析失败，记录日志
        print(f"[Webhook] 解析 17track 推送失败: {e}")
        return None


def parse_17track_batch_push(data: Dict[str, Any]) -> List[WebhookEvent]:
    """
    解析 17track 批量推送数据

    17track 可能一次推送多个运单的更新。

    Args:
        data: Webhook 推送的 JSON 数据

    Returns:
        List[WebhookEvent]: 解析后的事件列表
    """
    events = []

    # 检查是否为批量推送
    items = data.get("data", [])
    if isinstance(items, list):
        for item in items:
            single_data = {
                "event": data.get("event", "TRACKING_UPDATED"),
                "data": item,
            }
            event = parse_17track_push(single_data)
            if event:
                events.append(event)
    else:
        # 单条推送
        event = parse_17track_push(data)
        if event:
            events.append(event)

    return events


def is_delivery_event(event: WebhookEvent) -> bool:
    """
    判断是否为签收事件

    Args:
        event: Webhook 事件

    Returns:
        bool: 是否为签收事件
    """
    if not event.new_status:
        return False
    return event.new_status == TrackingStatus.DELIVERED


def is_exception_event(event: WebhookEvent) -> bool:
    """
    判断是否为异常事件

    异常包括：Alert、Undelivered、Expired

    Args:
        event: Webhook 事件

    Returns:
        bool: 是否为异常事件
    """
    if not event.new_status:
        return False
    return event.new_status.is_exception


def get_exception_type(event: WebhookEvent) -> Optional[str]:
    """
    获取异常类型

    根据子状态判断具体异常原因：
    - Alert_AddressIssue: 地址问题
    - Alert_CustomsIssue: 海关问题
    - Alert_Damaged: 包裹损坏
    - Alert_Lost: 包裹丢失
    - Alert_Returned: 已退回
    - Undelivered_*: 投递失败

    Args:
        event: Webhook 事件

    Returns:
        str: 异常类型标识，无异常返回 None
    """
    if not is_exception_event(event):
        return None

    sub_status = event.sub_status or ""

    if "AddressIssue" in sub_status:
        return "address_issue"
    elif "CustomsIssue" in sub_status:
        return "customs_issue"
    elif "Damaged" in sub_status:
        return "damaged"
    elif "Lost" in sub_status:
        return "lost"
    elif "Returned" in sub_status:
        return "returned"
    elif "NoOneHome" in sub_status:
        return "no_one_home"
    elif "Refused" in sub_status:
        return "refused"
    elif event.new_status == TrackingStatus.EXPIRED:
        return "expired"
    else:
        return "other"
