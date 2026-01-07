# -*- coding: utf-8 -*-
"""
聊天消息 ORM 模型

用于持久化存储聊天记录（用户 / AI / 坐席）。
"""

from sqlalchemy import Column, String, Text, Integer, Float, Index
from sqlalchemy.dialects.postgresql import TSVECTOR

from ..base import Base


class ChatMessageModel(Base):
    """聊天消息表"""

    __tablename__ = "chat_messages"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 幂等键（用于安全重试，避免重复写入）
    message_id = Column(String(36), unique=True, nullable=False, index=True, comment="消息ID(UUID)")

    # 会话标识
    session_name = Column(String(200), nullable=False, index=True, comment="会话标识(session_name)")
    conversation_id = Column(String(100), nullable=True, index=True, comment="Coze conversation_id")

    # 消息内容
    role = Column(String(20), nullable=False, index=True, comment="角色: user/assistant/agent")
    content = Column(Text, nullable=False, comment="消息内容")

    # 坐席信息（仅 role=agent 时）
    agent_id = Column(String(100), nullable=True, comment="坐席ID")
    agent_name = Column(String(100), nullable=True, comment="坐席名称")

    # AI 响应耗时（仅 role=assistant 时）
    response_time_ms = Column(Integer, nullable=True, comment="AI响应耗时(毫秒)")

    # 时间戳
    created_at = Column(Float, nullable=False, index=True, comment="创建时间(Unix时间戳)")

    # 全文检索字段（由数据库触发器维护）
    content_tsv = Column(TSVECTOR, nullable=False, comment="全文检索向量(to_tsvector)")

    __table_args__ = (
        Index("ix_chat_messages_time_session", "created_at", "session_name"),
        {"comment": "聊天消息表"},
    )

