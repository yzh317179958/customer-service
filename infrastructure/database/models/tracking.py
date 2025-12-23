# -*- coding: utf-8 -*-
"""
物流追踪 ORM 模型

包含运单注册记录和通知发送记录。
"""

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, Index
)
from sqlalchemy.dialects.postgresql import JSONB

from ..base import Base


class TrackingRegistrationModel(Base):
    """运单注册记录表"""
    __tablename__ = "tracking_registrations"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 运单信息
    tracking_number = Column(
        String(100), unique=True, nullable=False, index=True,
        comment="运单号"
    )
    carrier_code = Column(
        Integer, nullable=True,
        comment="承运商代码(17track)"
    )
    carrier_name = Column(
        String(100), nullable=True,
        comment="承运商名称"
    )

    # 订单关联
    order_id = Column(
        String(50), nullable=True, index=True,
        comment="Shopify订单ID"
    )
    order_number = Column(
        String(50), nullable=True,
        comment="订单显示号(如#1234)"
    )
    site = Column(
        String(20), nullable=True, index=True,
        comment="站点(uk/de/us)"
    )

    # 状态
    status = Column(
        String(30), nullable=False, default="registered", index=True,
        comment="状态: registered/tracking/delivered/exception/stopped"
    )
    current_tracking_status = Column(
        String(30), nullable=True,
        comment="17track当前状态: NotFound/InTransit/Delivered等"
    )
    is_delivered = Column(
        Boolean, nullable=False, default=False,
        comment="是否已签收"
    )
    is_exception = Column(
        Boolean, nullable=False, default=False,
        comment="是否有异常"
    )

    # 17track 响应
    register_response = Column(
        JSONB, nullable=True,
        comment="注册API响应"
    )
    last_event = Column(
        JSONB, nullable=True,
        comment="最新物流事件"
    )

    # 时间戳
    created_at = Column(
        Float, nullable=False, index=True,
        comment="创建时间(Unix时间戳)"
    )
    updated_at = Column(
        Float, nullable=False,
        comment="更新时间(Unix时间戳)"
    )
    delivered_at = Column(
        Float, nullable=True,
        comment="签收时间(Unix时间戳)"
    )

    # 索引
    __table_args__ = (
        Index("ix_tracking_reg_order_site", "order_id", "site"),
        Index("ix_tracking_reg_status_created", "status", "created_at"),
        {"comment": "运单注册记录表"},
    )

    def __repr__(self):
        return f"<TrackingRegistration(tracking='{self.tracking_number}', order='{self.order_id}', status='{self.status}')>"


class NotificationRecordModel(Base):
    """通知发送记录表"""
    __tablename__ = "notification_records"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    notification_id = Column(
        String(50), unique=True, nullable=False, index=True,
        comment="通知ID"
    )

    # 关联信息
    tracking_number = Column(
        String(100), nullable=True, index=True,
        comment="关联运单号"
    )
    order_id = Column(
        String(50), nullable=True, index=True,
        comment="关联订单ID"
    )
    order_number = Column(
        String(50), nullable=True,
        comment="订单显示号"
    )
    site = Column(
        String(20), nullable=True,
        comment="站点"
    )

    # 通知类型
    notification_type = Column(
        String(30), nullable=False, index=True,
        comment="类型: split_package/presale/exception/delivery"
    )
    exception_type = Column(
        String(30), nullable=True,
        comment="异常类型: address_issue/customs/lost等"
    )

    # 收件人
    to_email = Column(
        String(200), nullable=False, index=True,
        comment="收件人邮箱"
    )
    customer_name = Column(
        String(200), nullable=True,
        comment="客户姓名"
    )

    # 邮件内容
    subject = Column(
        String(500), nullable=False,
        comment="邮件主题"
    )
    template_name = Column(
        String(100), nullable=True,
        comment="使用的模板名"
    )
    template_data = Column(
        JSONB, nullable=True,
        comment="模板渲染数据"
    )

    # 发送状态
    status = Column(
        String(20), nullable=False, default="pending", index=True,
        comment="状态: pending/sent/failed"
    )
    error_message = Column(
        Text, nullable=True,
        comment="错误信息"
    )
    retry_count = Column(
        Integer, nullable=False, default=0,
        comment="重试次数"
    )

    # 触发事件
    trigger_event = Column(
        String(50), nullable=True,
        comment="触发事件: fulfillment_create/tracking_update等"
    )
    trigger_data = Column(
        JSONB, nullable=True,
        comment="触发事件数据"
    )

    # 时间戳
    created_at = Column(
        Float, nullable=False, index=True,
        comment="创建时间"
    )
    sent_at = Column(
        Float, nullable=True,
        comment="发送时间"
    )

    # 索引
    __table_args__ = (
        Index("ix_notification_type_created", "notification_type", "created_at"),
        Index("ix_notification_order_type", "order_id", "notification_type"),
        {"comment": "物流通知发送记录表"},
    )

    def __repr__(self):
        return f"<NotificationRecord(id='{self.notification_id}', type='{self.notification_type}', status='{self.status}')>"
