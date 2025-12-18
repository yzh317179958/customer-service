"""
兼容层 - 重导出新架构模块
"""
from services.ticket.store import TicketStore

__all__ = ["TicketStore"]
