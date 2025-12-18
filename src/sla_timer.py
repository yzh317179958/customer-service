"""
兼容层 - 重导出新架构模块
"""
from services.ticket.sla import (
    SLATimer,
    calculate_ticket_sla,
    SLAStatus,
    check_sla_alerts,
    SLAAlert,
    SLA_PAUSE_STATUSES,
)

__all__ = [
    "SLATimer",
    "calculate_ticket_sla",
    "SLAStatus",
    "check_sla_alerts",
    "SLAAlert",
    "SLA_PAUSE_STATUSES",
]
