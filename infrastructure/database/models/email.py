# -*- coding: utf-8 -*-
"""
邮件发送记录 ORM 模型

记录系统发送的所有邮件。
"""

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, Index
)
from sqlalchemy.dialects.postgresql import JSONB

from ..base import Base


class EmailRecordModel(Base):
    """邮件发送记录表"""
    __tablename__ = "email_records"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String(50), unique=True, nullable=False, index=True, comment="记录ID")

    # 邮件基本信息
    subject = Column(String(500), nullable=False, comment="邮件主题")
    from_email = Column(String(200), nullable=False, comment="发件人邮箱")
    to_email = Column(String(200), nullable=False, index=True, comment="收件人邮箱")
    cc_emails = Column(String(1000), nullable=True, comment="抄送邮箱列表(逗号分隔)")
    bcc_emails = Column(String(1000), nullable=True, comment="密送邮箱列表(逗号分隔)")

    # 邮件内容
    body_text = Column(Text, nullable=True, comment="纯文本内容")
    body_html = Column(Text, nullable=True, comment="HTML内容")

    # 邮件类型
    email_type = Column(String(50), nullable=True, index=True, comment="邮件类型: notification/reply/system")
    template_id = Column(String(100), nullable=True, comment="使用的模板ID")

    # 关联
    session_id = Column(String(100), nullable=True, index=True, comment="关联会话ID")
    ticket_id = Column(String(50), nullable=True, index=True, comment="关联工单ID")
    customer_id = Column(String(100), nullable=True, index=True, comment="关联客户ID")

    # 发送状态
    status = Column(String(20), nullable=False, default="pending", index=True, comment="状态: pending/sent/failed")
    error_message = Column(Text, nullable=True, comment="错误信息")
    retry_count = Column(Integer, nullable=False, default=0, comment="重试次数")

    # 外部服务响应
    external_id = Column(String(200), nullable=True, comment="外部服务返回的ID(如 Message-ID)")
    external_response = Column(JSONB, nullable=True, comment="外部服务响应详情")

    # 时间戳
    created_at = Column(Float, nullable=False, index=True, comment="创建时间")
    sent_at = Column(Float, nullable=True, comment="发送时间")

    # 索引
    __table_args__ = (
        Index("ix_email_records_to_created", "to_email", "created_at"),
        Index("ix_email_records_status_created", "status", "created_at"),
        {"comment": "邮件发送记录表"},
    )

    def __repr__(self):
        return f"<EmailRecord(record_id='{self.record_id}', to='{self.to_email}', status='{self.status}')>"
