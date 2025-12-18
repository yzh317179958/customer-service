"""
兼容层 - 重导出新架构模块
"""
from infrastructure.security.agent_auth import (
    AgentManager,
    AgentTokenManager,
    initialize_super_admin,
    LoginRequest,
    LoginResponse,
    agent_to_dict,
    Agent,
    AgentStatus,
    AgentSkill,
    AgentRole,
    UpdateAgentSkillsRequest,
    CreateAgentRequest,
    UpdateAgentRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    UpdateProfileRequest,
    validate_password,
    PasswordHasher,
)

__all__ = [
    "AgentManager",
    "AgentTokenManager",
    "initialize_super_admin",
    "LoginRequest",
    "LoginResponse",
    "agent_to_dict",
    "Agent",
    "AgentStatus",
    "AgentSkill",
    "AgentRole",
    "UpdateAgentSkillsRequest",
    "CreateAgentRequest",
    "UpdateAgentRequest",
    "ResetPasswordRequest",
    "ChangePasswordRequest",
    "UpdateProfileRequest",
    "validate_password",
    "PasswordHasher",
]
