"""
兼容层 - 重导出新架构模块
"""
from services.ticket.models import (
    Ticket,
    TicketPriority,
    TicketStatus,
    TicketType,
    TicketCustomerInfo,
    TicketCommentType,
    TicketAttachment,
    TicketComment,
    generate_ticket_id,
)

__all__ = [
    "Ticket",
    "TicketPriority",
    "TicketStatus",
    "TicketType",
    "TicketCustomerInfo",
    "TicketCommentType",
    "TicketAttachment",
    "TicketComment",
    "generate_ticket_id",
]
