# -*- coding: utf-8 -*-
"""
Infrastructure - Database Models

ORM 模型导出模块。
"""

# 工单相关模型
from .ticket import (
    TicketModel,
    TicketCommentModel,
    TicketAttachmentModel,
    TicketStatusHistoryModel,
    TicketAssignmentModel,
)

# 坐席相关模型
from .agent import AgentModel

# 审计日志
from .audit import AuditLogModel

# 会话归档
from .session import SessionArchiveModel

# 邮件记录
from .email import EmailRecordModel

# 物流追踪
from .tracking import TrackingRegistrationModel, NotificationRecordModel

__all__ = [
    # 工单
    "TicketModel",
    "TicketCommentModel",
    "TicketAttachmentModel",
    "TicketStatusHistoryModel",
    "TicketAssignmentModel",
    # 坐席
    "AgentModel",
    # 审计日志
    "AuditLogModel",
    # 会话归档
    "SessionArchiveModel",
    # 邮件记录
    "EmailRecordModel",
    # 物流追踪
    "TrackingRegistrationModel",
    "NotificationRecordModel",
]
