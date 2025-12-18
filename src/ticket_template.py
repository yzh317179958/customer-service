"""
兼容层 - 重导出新架构模块
"""
from services.ticket.template import TicketTemplateStore, TicketTemplate

__all__ = ["TicketTemplateStore", "TicketTemplate"]
