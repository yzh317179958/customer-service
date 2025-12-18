"""
兼容层 - 重导出新架构模块
"""
from services.ticket.audit import AuditLogStore, AuditLog, AuditEventType

__all__ = ["AuditLogStore", "AuditLog", "AuditEventType"]
