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

# 聊天消息
from .chat_message import ChatMessageModel
from .chat_session_meta import ChatSessionMetaModel
from .chat_export_job import ChatExportJobModel

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
    # 聊天消息
    "ChatMessageModel",
    "ChatSessionMetaModel",
    "ChatExportJobModel",
    # 邮件记录
    "EmailRecordModel",
    # 物流追踪
    "TrackingRegistrationModel",
    "NotificationRecordModel",
]
