# -*- coding: utf-8 -*-
"""
Chat session metadata ORM model.

This table stores business-friendly labels/tags/notes for `session_name` so the workbench
can display readable titles without relying on external customer systems.
"""

from sqlalchemy import Column, String, Float, Index
from sqlalchemy.dialects.postgresql import JSONB

from ..base import Base


class ChatSessionMetaModel(Base):
    """Chat session metadata table (one row per session_name)."""

    __tablename__ = "chat_session_meta"

    session_name = Column(String(200), primary_key=True, comment="会话标识(session_name)")

    display_name = Column(String(200), nullable=True, comment="业务友好展示名（可编辑）")
    note = Column(String(2000), nullable=True, comment="会话备注（可编辑）")
    tags = Column(JSONB, nullable=True, comment="会话标签（数组/对象）")

    updated_by = Column(String(100), nullable=True, comment="最后编辑人（坐席 username）")

    created_at = Column(Float, nullable=False, index=True, comment="创建时间(Unix时间戳)")
    updated_at = Column(Float, nullable=False, index=True, comment="更新时间(Unix时间戳)")

    __table_args__ = (
        Index("ix_chat_session_meta_updated_at", "updated_at"),
        {"comment": "聊天会话元信息（展示名/备注/标签）"},
    )

