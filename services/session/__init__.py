"""
会话服务模块

提供会话状态管理和存储功能
"""

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

from services.session.redis_store import RedisSessionStore
from services.session.regulator import Regulator, RegulatorConfig
from services.session.shift_config import get_shift_config, is_in_shift

__all__ = [
    # 核心模型
    "SessionState",
    "SessionStatus",
    "Message",
    "MessageRole",

    # 存储接口
    "SessionStateStore",
    "InMemorySessionStore",
    "RedisSessionStore",

    # 辅助模型
    "EscalationInfo",
    "EscalationReason",
    "EscalationSeverity",
    "UserProfile",
    "AgentInfo",
    "MailInfo",
    "PriorityInfo",
    "PriorityLevel",

    # 工厂函数
    "get_session_store",

    # 调度器
    "Regulator",
    "RegulatorConfig",

    # 排班
    "get_shift_config",
    "is_in_shift",
]
