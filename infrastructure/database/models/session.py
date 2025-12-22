# -*- coding: utf-8 -*-
"""
会话归档 ORM 模型

用于存储已关闭会话的完整对话记录。
"""

from sqlalchemy import (
    Column, String, Text, Integer, Float, Index
)
from sqlalchemy.dialects.postgresql import JSONB

from ..base import Base


class SessionArchiveModel(Base):
    """会话归档表"""
    __tablename__ = "session_archives"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    archive_id = Column(String(50), unique=True, nullable=False, index=True, comment="归档ID")

    # 会话信息
    session_id = Column(String(100), nullable=False, index=True, comment="原会话ID")
    session_name = Column(String(200), nullable=True, comment="会话名称/标题")

    # 客户信息
    customer_id = Column(String(100), nullable=True, index=True, comment="客户ID")
    customer_email = Column(String(200), nullable=True, index=True, comment="客户邮箱")
    customer_name = Column(String(100), nullable=True, comment="客户名称")

    # 坐席信息
    agent_id = Column(String(100), nullable=True, index=True, comment="处理坐席ID")
    agent_name = Column(String(100), nullable=True, comment="处理坐席名称")

    # 渠道
    channel = Column(String(50), nullable=True, index=True, comment="会话渠道: web/email/chat")

    # 会话内容 (JSONB 存储完整消息列表)
    messages = Column(JSONB, nullable=True, comment="消息列表")

    # 会话统计
    message_count = Column(Integer, nullable=True, default=0, comment="消息数量")
    duration_seconds = Column(Integer, nullable=True, comment="会话时长(秒)")

    # 关联工单
    ticket_id = Column(String(50), nullable=True, index=True, comment="关联工单ID")

    # 时间戳
    started_at = Column(Float, nullable=True, comment="会话开始时间")
    ended_at = Column(Float, nullable=True, comment="会话结束时间")
    archived_at = Column(Float, nullable=False, index=True, comment="归档时间")

    # 索引
    __table_args__ = (
        Index("ix_session_archives_customer_archived", "customer_id", "archived_at"),
        Index("ix_session_archives_agent_archived", "agent_id", "archived_at"),
        {"comment": "会话归档表"},
    )

    def __repr__(self):
        return f"<SessionArchive(archive_id='{self.archive_id}', session='{self.session_id}')>"
