# -*- coding: utf-8 -*-
"""
工单相关 ORM 模型

包含：
- TicketModel: 工单主表
- TicketCommentModel: 工单评论表
- TicketAttachmentModel: 工单附件表
- TicketStatusHistoryModel: 工单状态历史表
- TicketAssignmentModel: 工单指派历史表
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean,
    ForeignKey, Index, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


# ============================================================================
# 枚举定义（与 Pydantic 模型保持一致）
# ============================================================================

class TicketTypeEnum(str):
    PRE_SALE = "pre_sale"
    AFTER_SALE = "after_sale"
    COMPLAINT = "complaint"


class TicketStatusEnum(str):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    WAITING_VENDOR = "waiting_vendor"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ARCHIVED = "archived"


class TicketPriorityEnum(str):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class CommentTypeEnum(str):
    INTERNAL = "internal"
    PUBLIC = "public"


# ============================================================================
# ORM 模型
# ============================================================================

class TicketModel(Base, TimestampMixin):
    """工单主表"""
    __tablename__ = "tickets"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String(50), unique=True, nullable=False, index=True, comment="工单号")

    # 基本信息
    title = Column(String(500), nullable=False, comment="工单标题")
    description = Column(Text, nullable=False, comment="工单描述")
    session_name = Column(String(100), nullable=True, index=True, comment="关联会话ID")

    # 分类与状态
    ticket_type = Column(String(20), nullable=False, default="after_sale", comment="工单类型")
    status = Column(String(30), nullable=False, default="pending", index=True, comment="工单状态")
    priority = Column(String(20), nullable=False, default="medium", index=True, comment="优先级")

    # 创建者
    created_by = Column(String(100), nullable=False, index=True, comment="创建者ID")
    created_by_name = Column(String(100), nullable=True, comment="创建者名称")

    # 指派
    assigned_agent_id = Column(String(100), nullable=True, index=True, comment="指派坐席ID")
    assigned_agent_name = Column(String(100), nullable=True, comment="指派坐席名称")

    # 客户信息 (JSONB)
    customer = Column(JSONB, nullable=True, comment="客户信息")

    # 扩展元数据 (JSONB) - 注意：不能用 metadata，是 SQLAlchemy 保留字
    extra_data = Column(JSONB, nullable=True, default=dict, comment="扩展元数据")

    # 时间戳 (使用 float 存储 Unix 时间戳，与 Pydantic 保持一致)
    closed_at = Column(Float, nullable=True, comment="关闭时间")
    archived_at = Column(Float, nullable=True, comment="归档时间")
    first_response_at = Column(Float, nullable=True, comment="首次响应时间")
    resolved_at = Column(Float, nullable=True, comment="解决时间")
    reopened_at = Column(Float, nullable=True, comment="重新打开时间")

    # 重新打开
    reopened_count = Column(Integer, nullable=False, default=0, comment="重新打开次数")
    reopened_by = Column(String(100), nullable=True, comment="重新打开者")

    # 关联关系
    comments = relationship("TicketCommentModel", back_populates="ticket", cascade="all, delete-orphan")
    attachments = relationship("TicketAttachmentModel", back_populates="ticket", cascade="all, delete-orphan")
    status_history = relationship("TicketStatusHistoryModel", back_populates="ticket", cascade="all, delete-orphan")
    assignments = relationship("TicketAssignmentModel", back_populates="ticket", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index("ix_tickets_status_priority", "status", "priority"),
        Index("ix_tickets_created_at", "created_at"),
        {"comment": "工单主表"},
    )

    def __repr__(self):
        return f"<Ticket(ticket_id='{self.ticket_id}', status='{self.status}')>"


class TicketCommentModel(Base, TimestampMixin):
    """工单评论表"""
    __tablename__ = "ticket_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_id = Column(String(50), unique=True, nullable=False, index=True, comment="评论ID")
    ticket_id = Column(String(50), ForeignKey("tickets.ticket_id", ondelete="CASCADE"), nullable=False, index=True)

    content = Column(Text, nullable=False, comment="评论内容")
    author_id = Column(String(100), nullable=False, index=True, comment="作者ID")
    author_name = Column(String(100), nullable=True, comment="作者名称")
    comment_type = Column(String(20), nullable=False, default="internal", comment="评论类型: internal/public")

    # @提及的用户列表 (JSONB)
    mentions = Column(JSONB, nullable=True, default=list, comment="提及的用户列表")

    # 关联
    ticket = relationship("TicketModel", back_populates="comments")

    __table_args__ = (
        Index("ix_ticket_comments_created_at", "created_at"),
        {"comment": "工单评论表"},
    )

    def __repr__(self):
        return f"<TicketComment(comment_id='{self.comment_id}', author='{self.author_id}')>"


class TicketAttachmentModel(Base, TimestampMixin):
    """工单附件表"""
    __tablename__ = "ticket_attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    attachment_id = Column(String(50), unique=True, nullable=False, index=True, comment="附件ID")
    ticket_id = Column(String(50), ForeignKey("tickets.ticket_id", ondelete="CASCADE"), nullable=False, index=True)

    filename = Column(String(500), nullable=False, comment="文件名")
    stored_path = Column(String(1000), nullable=False, comment="存储路径")
    content_type = Column(String(100), nullable=True, comment="MIME类型")
    size = Column(Integer, nullable=False, comment="文件大小(字节)")

    comment_type = Column(String(20), nullable=False, default="internal", comment="附件类型: internal/public")
    uploader_id = Column(String(100), nullable=False, comment="上传者ID")
    uploader_name = Column(String(100), nullable=True, comment="上传者名称")

    # 关联
    ticket = relationship("TicketModel", back_populates="attachments")

    __table_args__ = (
        {"comment": "工单附件表"},
    )

    def __repr__(self):
        return f"<TicketAttachment(attachment_id='{self.attachment_id}', filename='{self.filename}')>"


class TicketStatusHistoryModel(Base):
    """工单状态历史表"""
    __tablename__ = "ticket_status_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    history_id = Column(String(50), unique=True, nullable=False, index=True, comment="历史记录ID")
    ticket_id = Column(String(50), ForeignKey("tickets.ticket_id", ondelete="CASCADE"), nullable=False, index=True)

    from_status = Column(String(30), nullable=True, comment="原状态")
    to_status = Column(String(30), nullable=False, comment="新状态")
    changed_by = Column(String(100), nullable=False, comment="变更者")
    change_reason = Column(String(500), nullable=True, comment="变更原因")
    comment = Column(Text, nullable=True, comment="备注")

    # 使用 Float 存储时间戳
    changed_at = Column(Float, nullable=False, comment="变更时间")

    # 关联
    ticket = relationship("TicketModel", back_populates="status_history")

    __table_args__ = (
        Index("ix_ticket_status_history_changed_at", "changed_at"),
        {"comment": "工单状态历史表"},
    )

    def __repr__(self):
        return f"<TicketStatusHistory(history_id='{self.history_id}', {self.from_status} -> {self.to_status})>"


class TicketAssignmentModel(Base):
    """工单指派历史表"""
    __tablename__ = "ticket_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String(50), ForeignKey("tickets.ticket_id", ondelete="CASCADE"), nullable=False, index=True)

    agent_id = Column(String(100), nullable=True, index=True, comment="指派坐席ID")
    agent_name = Column(String(100), nullable=True, comment="指派坐席名称")
    assigned_by = Column(String(100), nullable=True, comment="指派者")
    note = Column(Text, nullable=True, comment="指派备注")

    # 使用 Float 存储时间戳
    assigned_at = Column(Float, nullable=False, comment="指派时间")

    # 关联
    ticket = relationship("TicketModel", back_populates="assignments")

    __table_args__ = (
        Index("ix_ticket_assignments_assigned_at", "assigned_at"),
        {"comment": "工单指派历史表"},
    )

    def __repr__(self):
        return f"<TicketAssignment(ticket_id='{self.ticket_id}', agent='{self.agent_id}')>"
