"""
兼容层 - 重导出新架构模块
"""
from services.email.service import EmailService, get_email_service, send_escalation_email

__all__ = ["EmailService", "get_email_service", "send_escalation_email"]
