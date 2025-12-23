"""
物流追踪数据模型

定义物流状态、事件、信息等数据结构。

基于 17track API V2.4 数据格式设计。
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class TrackingStatus(str, Enum):
    """
    17track 物流主状态（9 种）

    参考：https://help.17track.net/hc/en-us/articles/37471096573337
    """

    NOT_FOUND = "NotFound"              # 未找到 - 运单号无信息
    INFO_RECEIVED = "InfoReceived"      # 已揽收 - 已创建运单，等待揽收
    IN_TRANSIT = "InTransit"            # 运输中 - 包裹正在运输途中
    PICK_UP = "PickUp"                  # 待取件 - 包裹到达待取
    OUT_FOR_DELIVERY = "OutForDelivery" # 派送中 - 正在派送途中
    UNDELIVERED = "Undelivered"         # 未送达 - 尝试派送但失败
    DELIVERED = "Delivered"             # 已签收 - 成功签收
    ALERT = "Alert"                     # 异常 - 发生异常（退件/海关/丢失等）
    EXPIRED = "Expired"                 # 过期 - 长时间无更新

    @classmethod
    def from_code(cls, code: int) -> "TrackingStatus":
        """
        从状态码转换为状态枚举

        17track 状态码映射：
        0 - NotFound
        10 - InfoReceived
        20 - InTransit
        30 - PickUp
        35 - OutForDelivery
        40 - Undelivered
        50 - Delivered
        60 - Alert
        70 - Expired
        """
        code_map = {
            0: cls.NOT_FOUND,
            10: cls.INFO_RECEIVED,
            20: cls.IN_TRANSIT,
            30: cls.PICK_UP,
            35: cls.OUT_FOR_DELIVERY,
            40: cls.UNDELIVERED,
            50: cls.DELIVERED,
            60: cls.ALERT,
            70: cls.EXPIRED,
        }
        return code_map.get(code, cls.NOT_FOUND)

    @property
    def code(self) -> int:
        """获取状态码"""
        code_map = {
            self.NOT_FOUND: 0,
            self.INFO_RECEIVED: 10,
            self.IN_TRANSIT: 20,
            self.PICK_UP: 30,
            self.OUT_FOR_DELIVERY: 35,
            self.UNDELIVERED: 40,
            self.DELIVERED: 50,
            self.ALERT: 60,
            self.EXPIRED: 70,
        }
        return code_map.get(self, 0)

    @property
    def zh(self) -> str:
        """中文名称"""
        zh_map = {
            self.NOT_FOUND: "未找到",
            self.INFO_RECEIVED: "已揽收",
            self.IN_TRANSIT: "运输中",
            self.PICK_UP: "待取件",
            self.OUT_FOR_DELIVERY: "派送中",
            self.UNDELIVERED: "未送达",
            self.DELIVERED: "已签收",
            self.ALERT: "异常",
            self.EXPIRED: "过期",
        }
        return zh_map.get(self, "未知")

    @property
    def is_final(self) -> bool:
        """是否为终态"""
        return self in (self.DELIVERED, self.ALERT, self.EXPIRED)

    @property
    def is_exception(self) -> bool:
        """是否为异常状态"""
        return self in (self.ALERT, self.UNDELIVERED, self.EXPIRED)


class TrackingSubStatus(str, Enum):
    """
    17track 物流子状态（常用）

    参考：https://help.17track.net/hc/en-us/articles/6089914889881
    """

    # InTransit 子状态
    IN_TRANSIT_PICKED_UP = "InTransit_PickedUp"           # 已揽收
    IN_TRANSIT_DEPARTED = "InTransit_Departed"             # 已离开
    IN_TRANSIT_ARRIVED = "InTransit_Arrived"               # 已到达
    IN_TRANSIT_CUSTOMS = "InTransit_Customs"               # 清关中
    IN_TRANSIT_OTHER = "InTransit_Other"                   # 运输中（其他）

    # Delivered 子状态
    DELIVERED_SIGNED = "Delivered_Signed"                  # 本人签收
    DELIVERED_FRONT_DOOR = "Delivered_FrontDoor"           # 门口签收
    DELIVERED_NEIGHBOR = "Delivered_Neighbor"              # 邻居代收
    DELIVERED_LOCKER = "Delivered_Locker"                  # 快递柜
    DELIVERED_OTHER = "Delivered_Other"                    # 其他签收

    # Alert 子状态
    ALERT_ADDRESS_ISSUE = "Alert_AddressIssue"             # 地址问题
    ALERT_CUSTOMS_ISSUE = "Alert_CustomsIssue"             # 海关问题
    ALERT_DAMAGED = "Alert_Damaged"                        # 包裹损坏
    ALERT_LOST = "Alert_Lost"                              # 包裹丢失
    ALERT_RETURNED = "Alert_Returned"                      # 已退回
    ALERT_OTHER = "Alert_Other"                            # 其他异常

    # Undelivered 子状态
    UNDELIVERED_NO_ONE_HOME = "Undelivered_NoOneHome"      # 无人在家
    UNDELIVERED_REFUSED = "Undelivered_Refused"            # 拒收
    UNDELIVERED_OTHER = "Undelivered_Other"                # 其他原因

    @property
    def zh(self) -> str:
        """中文名称"""
        zh_map = {
            # InTransit
            self.IN_TRANSIT_PICKED_UP: "已揽收",
            self.IN_TRANSIT_DEPARTED: "已离开",
            self.IN_TRANSIT_ARRIVED: "已到达",
            self.IN_TRANSIT_CUSTOMS: "清关中",
            self.IN_TRANSIT_OTHER: "运输中",
            # Delivered
            self.DELIVERED_SIGNED: "本人签收",
            self.DELIVERED_FRONT_DOOR: "门口签收",
            self.DELIVERED_NEIGHBOR: "邻居代收",
            self.DELIVERED_LOCKER: "快递柜签收",
            self.DELIVERED_OTHER: "已签收",
            # Alert
            self.ALERT_ADDRESS_ISSUE: "地址问题",
            self.ALERT_CUSTOMS_ISSUE: "海关问题",
            self.ALERT_DAMAGED: "包裹损坏",
            self.ALERT_LOST: "包裹丢失",
            self.ALERT_RETURNED: "已退回",
            self.ALERT_OTHER: "异常",
            # Undelivered
            self.UNDELIVERED_NO_ONE_HOME: "无人在家",
            self.UNDELIVERED_REFUSED: "拒收",
            self.UNDELIVERED_OTHER: "投递失败",
        }
        return zh_map.get(self, "未知")


class TrackingEvent(BaseModel):
    """
    物流事件

    表示物流轨迹中的一个节点。
    """

    timestamp: Optional[datetime] = Field(None, description="事件时间")
    timestamp_str: Optional[str] = Field(None, description="事件时间（原始字符串）")
    status: Optional[str] = Field(None, description="状态描述（英文）")
    status_zh: Optional[str] = Field(None, description="状态描述（中文）")
    location: Optional[str] = Field(None, description="事件地点")
    description: Optional[str] = Field(None, description="事件详情（英文）")
    description_zh: Optional[str] = Field(None, description="事件详情（中文）")
    status_code: Optional[int] = Field(None, description="状态码")

    @classmethod
    def from_17track_event(cls, event: Dict[str, Any]) -> "TrackingEvent":
        """
        从 17track API 返回的事件数据创建

        17track 事件格式:
        {
            "a": "2024-12-22 10:30:00",  # 时间
            "b": 20,                      # 状态码
            "c": "Package in transit",    # 状态描述
            "d": "London, UK",            # 地点
            "z": "..."                    # 其他信息
        }
        """
        timestamp = None
        timestamp_str = event.get("a")
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace(" ", "T"))
            except ValueError:
                pass

        return cls(
            timestamp=timestamp,
            timestamp_str=timestamp_str,
            status=event.get("c"),
            location=event.get("d"),
            description=event.get("c"),
            status_code=event.get("b"),
        )

    def with_translation(self, status_zh: str = None, description_zh: str = None) -> "TrackingEvent":
        """添加中文翻译"""
        return TrackingEvent(
            timestamp=self.timestamp,
            timestamp_str=self.timestamp_str,
            status=self.status,
            status_zh=status_zh or self.status_zh,
            location=self.location,
            description=self.description,
            description_zh=description_zh or self.description_zh,
            status_code=self.status_code,
        )


class CarrierInfo(BaseModel):
    """承运商信息"""

    code: Optional[int] = Field(None, description="承运商代码")
    name: Optional[str] = Field(None, description="承运商名称")
    phone: Optional[str] = Field(None, description="承运商电话")
    url: Optional[str] = Field(None, description="承运商官网")


class TrackingInfo(BaseModel):
    """
    完整物流信息

    包含运单状态、轨迹事件、承运商信息等。
    """

    tracking_number: str = Field(..., description="运单号")
    carrier: Optional[CarrierInfo] = Field(None, description="承运商信息")

    # 状态
    status: Optional[TrackingStatus] = Field(None, description="当前主状态")
    sub_status: Optional[str] = Field(None, description="子状态")
    status_zh: Optional[str] = Field(None, description="状态中文")

    # 轨迹
    events: List[TrackingEvent] = Field(default_factory=list, description="物流事件列表")
    last_event: Optional[TrackingEvent] = Field(None, description="最新事件")

    # 时间
    registered_at: Optional[datetime] = Field(None, description="注册时间")
    updated_at: Optional[datetime] = Field(None, description="最后更新时间")
    delivered_at: Optional[datetime] = Field(None, description="签收时间")

    # 关联信息
    order_id: Optional[str] = Field(None, description="关联订单 ID")
    order_number: Optional[str] = Field(None, description="关联订单号")

    # 原始数据
    raw_data: Optional[Dict[str, Any]] = Field(None, description="原始 API 响应")

    @classmethod
    def from_17track_response(
        cls,
        tracking_number: str,
        response: Dict[str, Any],
        order_id: Optional[str] = None,
        order_number: Optional[str] = None,
    ) -> "TrackingInfo":
        """
        从 17track API 响应创建

        Args:
            tracking_number: 运单号
            response: 17track gettrackinfo API 响应
            order_id: 关联订单 ID（可选）
            order_number: 关联订单号（可选）
        """
        track = response.get("track", {})

        # 解析状态
        status_code = track.get("e")
        status = TrackingStatus.from_code(status_code) if status_code is not None else None

        # 解析承运商
        carrier_data = response.get("carrier", {})
        carrier = CarrierInfo(
            code=carrier_data.get("key"),
            name=carrier_data.get("name"),
            url=carrier_data.get("url"),
        ) if carrier_data else None

        # 解析事件列表
        raw_events = track.get("z1", [])
        events = [TrackingEvent.from_17track_event(e) for e in raw_events]

        # 最新事件
        last_event_data = track.get("z0", {})
        last_event = TrackingEvent.from_17track_event(last_event_data) if last_event_data else None

        return cls(
            tracking_number=tracking_number,
            carrier=carrier,
            status=status,
            sub_status=track.get("f"),
            status_zh=status.zh if status else None,
            events=events,
            last_event=last_event,
            order_id=order_id,
            order_number=order_number,
            raw_data=response,
        )

    @property
    def is_delivered(self) -> bool:
        """是否已签收"""
        return self.status == TrackingStatus.DELIVERED

    @property
    def is_exception(self) -> bool:
        """是否有异常"""
        return self.status.is_exception if self.status else False

    @property
    def event_count(self) -> int:
        """事件数量"""
        return len(self.events)


class WebhookEvent(BaseModel):
    """
    17track Webhook 推送事件

    当运单状态变更时，17track 会推送此事件到配置的 Webhook URL。
    """

    event_type: str = Field(..., description="事件类型: TRACKING_UPDATED")
    tracking_number: str = Field(..., description="运单号")
    carrier_code: Optional[int] = Field(None, description="承运商代码")

    # 状态信息
    old_status: Optional[TrackingStatus] = Field(None, description="旧状态")
    new_status: Optional[TrackingStatus] = Field(None, description="新状态")
    sub_status: Optional[str] = Field(None, description="子状态")

    # 最新事件
    last_event: Optional[TrackingEvent] = Field(None, description="最新事件")

    # 时间
    event_time: Optional[datetime] = Field(None, description="事件发生时间")
    push_time: Optional[datetime] = Field(None, description="推送时间")

    # 自定义数据
    tag: Optional[str] = Field(None, description="自定义标签")
    order_id: Optional[str] = Field(None, description="关联订单号（注册时设置）")

    # 原始数据
    raw_data: Optional[Dict[str, Any]] = Field(None, description="原始推送数据")
