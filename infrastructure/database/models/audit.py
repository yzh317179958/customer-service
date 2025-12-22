# -*- coding: utf-8 -*-
"""
审计日志 ORM 模型

记录工单系统中的所有操作日志。
"""

from sqlalchemy import (
    Column, String, Text, Integer, Float, Index
)
from sqlalchemy.dialects.postgresql import JSONB

from ..base import Base


class AuditLogModel(Base):
    """审计日志表"""
    __tablename__ = "audit_logs"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    audit_id = Column(String(50), unique=True, nullable=False, index=True, comment="审计日志ID")

    # 关联
    ticket_id = Column(String(50), nullable=False, index=True, comment="关联工单ID")

    # 事件信息
    event_type = Column(String(50), nullable=False, index=True, comment="事件类型: created/status_changed/assigned/commented/etc")

    # 操作者
    operator_id = Column(String(100), nullable=False, index=True, comment="操作者ID")
    operator_name = Column(String(100), nullable=True, comment="操作者名称")

    # 详情 (JSONB)
    details = Column(JSONB, nullable=True, default=dict, comment="事件详情")

    # 时间戳
    created_at = Column(Float, nullable=False, index=True, comment="创建时间")

    # 索引
    __table_args__ = (
        Index("ix_audit_logs_ticket_created", "ticket_id", "created_at"),
        Index("ix_audit_logs_operator_created", "operator_id", "created_at"),
        {"comment": "审计日志表"},
    )

    def __repr__(self):
        return f"<AuditLog(audit_id='{self.audit_id}', event='{self.event_type}', ticket='{self.ticket_id}')>"
