"""
Ticket service module

Provides ticket CRUD, assignment, and SLA management
"""

from services.ticket.models import (
    Ticket,
    TicketPriority,
    TicketStatus,
    TicketType,
    TicketCustomerInfo,
    TicketCommentType,
    TicketAttachment,
    generate_ticket_id,
)
from services.ticket.store import TicketStore
from services.ticket.assignment import SmartAssignmentEngine
from services.ticket.template import TicketTemplateStore, TicketTemplate
from services.ticket.sla import check_sla_alerts, SLAAlert, SLA_PAUSE_STATUSES
from services.ticket.audit import AuditLogStore

__all__ = [
    "Ticket",
    "TicketPriority",
    "TicketStatus",
    "TicketType",
    "TicketCustomerInfo",
    "TicketCommentType",
    "TicketAttachment",
    "generate_ticket_id",
    "TicketStore",
    "AuditLogStore",
    "SmartAssignmentEngine",
    "TicketTemplateStore",
    "TicketTemplate",
    "check_sla_alerts",
    "SLAAlert",
    "SLA_PAUSE_STATUSES",
]
