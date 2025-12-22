# -*- coding: utf-8 -*-
"""
Pydantic ↔ ORM 模型转换器

提供 Pydantic 模型与 SQLAlchemy ORM 模型之间的双向转换。

使用示例:
    from infrastructure.database.converters import ticket_to_orm, ticket_from_orm

    # Pydantic -> ORM
    orm_model = ticket_to_orm(pydantic_ticket)

    # ORM -> Pydantic
    pydantic_ticket = ticket_from_orm(orm_model)
"""

import time
from typing import Optional, List, Dict, Any

# Pydantic 模型
from services.ticket.models import (
    Ticket, TicketComment, TicketAttachment,
    TicketStatusHistory, TicketAssignmentRecord,
    TicketCustomerInfo, TicketType, TicketStatus, TicketPriority,
    TicketCommentType
)
from infrastructure.security.agent_auth import Agent, AgentRole, AgentStatus, AgentSkill

# ORM 模型
from .models import (
    TicketModel, TicketCommentModel, TicketAttachmentModel,
    TicketStatusHistoryModel, TicketAssignmentModel,
    AgentModel,
    AuditLogModel,
)
from services.ticket.audit import AuditLog


# ============================================================================
# 工单转换器
# ============================================================================

def ticket_to_orm(ticket: Ticket) -> TicketModel:
    """
    将 Pydantic Ticket 转换为 ORM TicketModel

    注意：不包含关联对象（comments, attachments 等），
    需要单独转换并添加。
    """
    return TicketModel(
        ticket_id=ticket.ticket_id,
        title=ticket.title,
        description=ticket.description,
        session_name=ticket.session_name,
        ticket_type=ticket.ticket_type.value if isinstance(ticket.ticket_type, TicketType) else ticket.ticket_type,
        status=ticket.status.value if isinstance(ticket.status, TicketStatus) else ticket.status,
        priority=ticket.priority.value if isinstance(ticket.priority, TicketPriority) else ticket.priority,
        created_by=ticket.created_by,
        created_by_name=ticket.created_by_name,
        assigned_agent_id=ticket.assigned_agent_id,
        assigned_agent_name=ticket.assigned_agent_name,
        customer=ticket.customer.model_dump() if ticket.customer else None,
        extra_data=ticket.metadata,  # 注意：ORM 中是 extra_data
        closed_at=ticket.closed_at,
        archived_at=ticket.archived_at,
        first_response_at=ticket.first_response_at,
        resolved_at=ticket.resolved_at,
        reopened_at=ticket.reopened_at,
        reopened_count=ticket.reopened_count,
        reopened_by=ticket.reopened_by,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )


def ticket_from_orm(model: TicketModel) -> Ticket:
    """
    将 ORM TicketModel 转换为 Pydantic Ticket

    包含关联对象的转换。
    """
    # 转换客户信息
    customer = None
    if model.customer:
        customer = TicketCustomerInfo(**model.customer)

    # 转换历史记录
    history = [status_history_from_orm(h) for h in (model.status_history or [])]

    # 转换指派记录
    assignments = [assignment_from_orm(a) for a in (model.assignments or [])]

    # 转换评论
    comments = [comment_from_orm(c) for c in (model.comments or [])]

    # 转换附件
    attachments = [attachment_from_orm(a) for a in (model.attachments or [])]

    return Ticket(
        ticket_id=model.ticket_id,
        title=model.title,
        description=model.description,
        session_name=model.session_name,
        ticket_type=TicketType(model.ticket_type) if model.ticket_type else TicketType.AFTER_SALE,
        status=TicketStatus(model.status) if model.status else TicketStatus.PENDING,
        priority=TicketPriority(model.priority) if model.priority else TicketPriority.MEDIUM,
        created_by=model.created_by,
        created_by_name=model.created_by_name,
        assigned_agent_id=model.assigned_agent_id,
        assigned_agent_name=model.assigned_agent_name,
        customer=customer,
        metadata=model.extra_data or {},
        history=history,
        assignments=assignments,
        comments=comments,
        attachments=attachments,
        closed_at=model.closed_at,
        archived_at=model.archived_at,
        first_response_at=model.first_response_at,
        resolved_at=model.resolved_at,
        reopened_at=model.reopened_at,
        reopened_count=model.reopened_count or 0,
        reopened_by=model.reopened_by,
        created_at=model.created_at.timestamp() if hasattr(model.created_at, 'timestamp') else model.created_at,
        updated_at=model.updated_at.timestamp() if hasattr(model.updated_at, 'timestamp') else model.updated_at,
    )


def comment_to_orm(comment: TicketComment, ticket_id: str) -> TicketCommentModel:
    """将 Pydantic TicketComment 转换为 ORM TicketCommentModel"""
    return TicketCommentModel(
        comment_id=comment.comment_id,
        ticket_id=ticket_id,
        content=comment.content,
        author_id=comment.author_id,
        author_name=comment.author_name,
        comment_type=comment.comment_type.value if isinstance(comment.comment_type, TicketCommentType) else comment.comment_type,
        mentions=comment.mentions,
        created_at=comment.created_at,
        updated_at=comment.created_at,
    )


def comment_from_orm(model: TicketCommentModel) -> TicketComment:
    """将 ORM TicketCommentModel 转换为 Pydantic TicketComment"""
    return TicketComment(
        comment_id=model.comment_id,
        ticket_id=model.ticket_id,
        content=model.content,
        author_id=model.author_id,
        author_name=model.author_name,
        comment_type=TicketCommentType(model.comment_type) if model.comment_type else TicketCommentType.INTERNAL,
        mentions=model.mentions or [],
        created_at=model.created_at.timestamp() if hasattr(model.created_at, 'timestamp') else model.created_at,
    )


def attachment_to_orm(attachment: TicketAttachment, ticket_id: str) -> TicketAttachmentModel:
    """将 Pydantic TicketAttachment 转换为 ORM TicketAttachmentModel"""
    return TicketAttachmentModel(
        attachment_id=attachment.attachment_id,
        ticket_id=ticket_id,
        filename=attachment.filename,
        stored_path=attachment.stored_path,
        content_type=attachment.content_type,
        size=attachment.size,
        comment_type=attachment.comment_type.value if isinstance(attachment.comment_type, TicketCommentType) else attachment.comment_type,
        uploader_id=attachment.uploader_id,
        uploader_name=attachment.uploader_name,
        created_at=attachment.created_at,
        updated_at=attachment.created_at,
    )


def attachment_from_orm(model: TicketAttachmentModel) -> TicketAttachment:
    """将 ORM TicketAttachmentModel 转换为 Pydantic TicketAttachment"""
    return TicketAttachment(
        attachment_id=model.attachment_id,
        filename=model.filename,
        stored_path=model.stored_path,
        content_type=model.content_type,
        size=model.size,
        comment_type=TicketCommentType(model.comment_type) if model.comment_type else TicketCommentType.INTERNAL,
        uploader_id=model.uploader_id,
        uploader_name=model.uploader_name,
        created_at=model.created_at.timestamp() if hasattr(model.created_at, 'timestamp') else model.created_at,
    )


def status_history_to_orm(history: TicketStatusHistory, ticket_id: str) -> TicketStatusHistoryModel:
    """将 Pydantic TicketStatusHistory 转换为 ORM TicketStatusHistoryModel"""
    return TicketStatusHistoryModel(
        history_id=history.history_id,
        ticket_id=ticket_id,
        from_status=history.from_status.value if history.from_status else None,
        to_status=history.to_status.value if isinstance(history.to_status, TicketStatus) else history.to_status,
        changed_by=history.changed_by,
        change_reason=history.change_reason,
        comment=history.comment,
        changed_at=history.changed_at,
    )


def status_history_from_orm(model: TicketStatusHistoryModel) -> TicketStatusHistory:
    """将 ORM TicketStatusHistoryModel 转换为 Pydantic TicketStatusHistory"""
    return TicketStatusHistory(
        history_id=model.history_id,
        from_status=TicketStatus(model.from_status) if model.from_status else None,
        to_status=TicketStatus(model.to_status) if model.to_status else TicketStatus.PENDING,
        changed_by=model.changed_by,
        change_reason=model.change_reason,
        comment=model.comment,
        changed_at=model.changed_at,
    )


def assignment_to_orm(assignment: TicketAssignmentRecord, ticket_id: str) -> TicketAssignmentModel:
    """将 Pydantic TicketAssignmentRecord 转换为 ORM TicketAssignmentModel"""
    return TicketAssignmentModel(
        ticket_id=ticket_id,
        agent_id=assignment.agent_id,
        agent_name=assignment.agent_name,
        assigned_by=assignment.assigned_by,
        note=assignment.note,
        assigned_at=assignment.assigned_at,
    )


def assignment_from_orm(model: TicketAssignmentModel) -> TicketAssignmentRecord:
    """将 ORM TicketAssignmentModel 转换为 Pydantic TicketAssignmentRecord"""
    return TicketAssignmentRecord(
        agent_id=model.agent_id,
        agent_name=model.agent_name,
        assigned_by=model.assigned_by,
        note=model.note,
        assigned_at=model.assigned_at,
    )


# ============================================================================
# 坐席转换器
# ============================================================================

def agent_to_orm(agent: Agent) -> AgentModel:
    """将 Pydantic Agent 转换为 ORM AgentModel"""
    return AgentModel(
        agent_id=agent.id,
        username=agent.username,
        password_hash=agent.password_hash,
        name=agent.name,
        avatar_url=agent.avatar_url,
        role=agent.role.value if isinstance(agent.role, AgentRole) else agent.role,
        status=agent.status.value if isinstance(agent.status, AgentStatus) else agent.status,
        status_note=agent.status_note,
        status_updated_at=agent.status_updated_at,
        last_active_at=agent.last_active_at,
        last_login_at=agent.last_login,
        max_sessions=agent.max_sessions,
        skills=[s.model_dump() for s in agent.skills] if agent.skills else [],
        created_at=agent.created_at,
        updated_at=time.time(),
    )


def agent_from_orm(model: AgentModel) -> Agent:
    """将 ORM AgentModel 转换为 Pydantic Agent"""
    # 转换技能
    skills = []
    if model.skills:
        for skill_data in model.skills:
            try:
                skills.append(AgentSkill(**skill_data))
            except Exception:
                pass

    return Agent(
        id=model.agent_id,
        username=model.username,
        password_hash=model.password_hash,
        name=model.name,
        avatar_url=model.avatar_url,
        role=AgentRole(model.role) if model.role else AgentRole.AGENT,
        status=AgentStatus(model.status) if model.status else AgentStatus.OFFLINE,
        status_note=model.status_note,
        status_updated_at=model.status_updated_at or time.time(),
        last_active_at=model.last_active_at or time.time(),
        last_login=model.last_login_at,
        max_sessions=model.max_sessions or 5,
        skills=skills,
        created_at=model.created_at.timestamp() if hasattr(model.created_at, 'timestamp') else model.created_at,
    )


# ============================================================================
# 审计日志转换器
# ============================================================================

def audit_log_to_orm(log: AuditLog) -> AuditLogModel:
    """将 Pydantic AuditLog 转换为 ORM AuditLogModel"""
    return AuditLogModel(
        audit_id=log.id,
        ticket_id=log.ticket_id,
        event_type=log.event_type,
        operator_id=log.operator_id,
        operator_name=log.operator_name,
        details=log.details,
        created_at=log.created_at,
    )


def audit_log_from_orm(model: AuditLogModel) -> AuditLog:
    """将 ORM AuditLogModel 转换为 Pydantic AuditLog"""
    return AuditLog(
        id=model.audit_id,
        ticket_id=model.ticket_id,
        event_type=model.event_type,
        operator_id=model.operator_id,
        operator_name=model.operator_name,
        details=model.details or {},
        created_at=model.created_at,
    )
