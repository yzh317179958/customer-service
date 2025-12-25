"""
Security infrastructure module

提供安全防护功能：
- JWT 认证和坐席管理
- API 限流（防 CC 攻击）
- IP 黑名单（封禁恶意 IP）
- 登录保护（防暴力破解）
- 输入校验（XSS 防护）
- 安全中间件（统一入口检查）
"""

# ==============================================================================
# 现有功能 - JWT 认证和坐席管理
# ==============================================================================
from infrastructure.security.jwt_signer import JWTSigner
from infrastructure.security.agent_auth import (
    AgentManager,
    AgentTokenManager,
    initialize_super_admin,
    LoginRequest,
    LoginResponse,
    agent_to_dict,
    Agent,
    AgentStatus,
    UpdateAgentSkillsRequest,
)

# ==============================================================================
# 新增功能 - 安全防护组件 (Step 1-6)
# ==============================================================================

# Step 1: 配置模型
from infrastructure.security.config import (
    RateLimiterConfig,
    LoginProtectorConfig,
    SecurityConfig,
)

# Step 2: 限流器
from infrastructure.security.rate_limiter import (
    create_rate_limiter,
    get_rate_limit_handler,
    get_client_ip,
)

# Step 3: IP 黑名单
from infrastructure.security.blacklist import (
    IPBlacklist,
    get_ip_blacklist,
    init_ip_blacklist,
)

# Step 4: 登录保护
from infrastructure.security.login_protector import (
    LoginProtector,
    get_login_protector,
    init_login_protector,
)

# Step 5: 输入校验
from infrastructure.security.validators import (
    validate_message_length,
    sanitize_input,
    validate_order_number,
    validate_tracking_number,
    validate_email,
    validate_username,
)

# Step 6: 安全中间件
from infrastructure.security.middleware import (
    SecurityMiddleware,
    SecurityMiddlewareConfig,
)

# Step 11: Prometheus 监控指标
from infrastructure.security.metrics import (
    security_metrics,
    get_metrics_handler,
    get_metrics_response,
    record_rate_limit_hit,
    record_blocked_request,
    record_login_failure,
    record_account_lockout,
)

# ==============================================================================
# 导出清单
# ==============================================================================
__all__ = [
    # --- 现有功能 ---
    "JWTSigner",
    "AgentManager",
    "AgentTokenManager",
    "initialize_super_admin",
    "LoginRequest",
    "LoginResponse",
    "agent_to_dict",
    "Agent",
    "AgentStatus",
    "UpdateAgentSkillsRequest",

    # --- 配置模型 ---
    "RateLimiterConfig",
    "LoginProtectorConfig",
    "SecurityConfig",

    # --- 限流器 ---
    "create_rate_limiter",
    "get_rate_limit_handler",
    "get_client_ip",

    # --- IP 黑名单 ---
    "IPBlacklist",
    "get_ip_blacklist",
    "init_ip_blacklist",

    # --- 登录保护 ---
    "LoginProtector",
    "get_login_protector",
    "init_login_protector",

    # --- 输入校验 ---
    "validate_message_length",
    "sanitize_input",
    "validate_order_number",
    "validate_tracking_number",
    "validate_email",
    "validate_username",

    # --- 安全中间件 ---
    "SecurityMiddleware",
    "SecurityMiddlewareConfig",

    # --- 监控指标 ---
    "security_metrics",
    "get_metrics_handler",
    "get_metrics_response",
    "record_rate_limit_hit",
    "record_blocked_request",
    "record_login_failure",
    "record_account_lockout",
]
