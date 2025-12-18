"""
兼容层 - 重导出新架构模块

保持旧 import 路径可用，便于渐进式迁移
"""

# 从新位置重导出，保持向后兼容
from services.session.state import (
    SessionState,
    SessionStatus,
    SessionStateStore,
    InMemorySessionStore,
    Message,
    MessageRole,
    EscalationInfo,
    EscalationReason,
    EscalationSeverity,
    UserProfile,
    AgentInfo,
    MailInfo,
    PriorityInfo,
    PriorityLevel,
    get_session_store,
)

__all__ = [
    "SessionState",
    "SessionStatus",
    "SessionStateStore",
    "InMemorySessionStore",
    "Message",
    "MessageRole",
    "EscalationInfo",
    "EscalationReason",
    "EscalationSeverity",
    "UserProfile",
    "AgentInfo",
    "MailInfo",
    "PriorityInfo",
    "PriorityLevel",
    "get_session_store",
]
