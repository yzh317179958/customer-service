"""
Email service module

Provides SMTP email sending functionality
"""

from services.email.service import (
    EmailService,
    get_email_service,
    send_escalation_email,
)

__all__ = [
    "EmailService",
    "get_email_service",
    "send_escalation_email",
]
