# -*- coding: utf-8 -*-
"""
Chat export jobs ORM model.

Used for production-style async/batch CSV exports (operations/QA).
"""

from sqlalchemy import Column, String, Integer, Float, Index, Text
from sqlalchemy.dialects.postgresql import JSONB

from ..base import Base


class ChatExportJobModel(Base):
    """Chat export job table."""

    __tablename__ = "chat_export_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    job_id = Column(String(36), unique=True, nullable=False, index=True, comment="导出任务ID(UUID)")
    created_by = Column(String(100), nullable=False, index=True, comment="创建人（坐席 username）")

    status = Column(String(20), nullable=False, index=True, comment="状态: pending/running/done/failed")

    request = Column(JSONB, nullable=False, comment="导出参数（JSON）")

    row_count = Column(Integer, nullable=True, comment="导出行数（消息条数）")
    file_path = Column(String(500), nullable=True, comment="CSV 文件路径（本地/挂载卷）")
    error = Column(Text, nullable=True, comment="失败原因")

    created_at = Column(Float, nullable=False, index=True, comment="创建时间(Unix时间戳)")
    updated_at = Column(Float, nullable=False, index=True, comment="更新时间(Unix时间戳)")
    finished_at = Column(Float, nullable=True, comment="完成时间(Unix时间戳)")

    __table_args__ = (
        Index("ix_chat_export_jobs_created_by_time", "created_by", "created_at"),
        {"comment": "聊天记录导出任务"},
    )

