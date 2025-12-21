# -*- coding: utf-8 -*-
"""
坐席工作台 - 依赖注入模块

提供全局状态的 getter/setter 函数，用于依赖注入
"""
import asyncio
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# 类型导入
from infrastructure.security.agent_auth import AgentManager, AgentTokenManager
from services.session.state import SessionStateStore
from services.ticket.store import TicketStore
from services.session.quick_reply_store import QuickReplyStore
from services.ticket.audit import AuditLogStore


# ============================================================================
# 全局状态
# ============================================================================

_agent_manager: Optional[AgentManager] = None
_agent_token_manager: Optional[AgentTokenManager] = None
_session_store: Optional[SessionStateStore] = None
_ticket_store: Optional[TicketStore] = None
_quick_reply_store: Optional[QuickReplyStore] = None
_audit_log_store: Optional[AuditLogStore] = None
_sse_queues: Dict[str, asyncio.Queue] = {}


# ============================================================================
# Setter 函数 (由 backend.py 在 lifespan 中调用)
# ============================================================================

def set_agent_manager(manager: AgentManager) -> None:
    global _agent_manager
    _agent_manager = manager


def set_agent_token_manager(manager: AgentTokenManager) -> None:
    global _agent_token_manager
    _agent_token_manager = manager


def set_session_store(store: SessionStateStore) -> None:
    global _session_store
    _session_store = store


def set_ticket_store(store: TicketStore) -> None:
    global _ticket_store
    _ticket_store = store


def set_quick_reply_store(store: QuickReplyStore) -> None:
    global _quick_reply_store
    _quick_reply_store = store


def set_audit_log_store(store: AuditLogStore) -> None:
    global _audit_log_store
    _audit_log_store = store


def set_sse_queues(queues: Dict[str, asyncio.Queue]) -> None:
    global _sse_queues
    _sse_queues = queues


# ============================================================================
# Getter 函数 (供 handlers 使用)
# ============================================================================

def get_agent_manager() -> AgentManager:
    if _agent_manager is None:
        raise RuntimeError("AgentManager not initialized")
    return _agent_manager


def get_agent_token_manager() -> AgentTokenManager:
    if _agent_token_manager is None:
        raise RuntimeError("AgentTokenManager not initialized")
    return _agent_token_manager


def get_session_store() -> SessionStateStore:
    if _session_store is None:
        raise RuntimeError("SessionStore not initialized")
    return _session_store


def get_ticket_store() -> TicketStore:
    if _ticket_store is None:
        raise RuntimeError("TicketStore not initialized")
    return _ticket_store


def get_quick_reply_store() -> Optional[QuickReplyStore]:
    """快捷回复存储可能为 None（未配置 Redis 时）"""
    return _quick_reply_store


def get_audit_log_store() -> Optional[AuditLogStore]:
    """审计日志存储可能为 None"""
    return _audit_log_store


def get_sse_queues() -> Dict[str, asyncio.Queue]:
    return _sse_queues


def get_or_create_sse_queue(target: str) -> asyncio.Queue:
    """获取或创建 SSE 队列"""
    global _sse_queues
    if target not in _sse_queues:
        _sse_queues[target] = asyncio.Queue()
    return _sse_queues[target]


# ============================================================================
# 权限验证依赖
# ============================================================================

security = HTTPBearer()


async def verify_agent_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    验证 JWT Token

    Args:
        credentials: HTTP Bearer 凭证

    Returns:
        Dict: Token 载荷（包含 agent_id, username, role）

    Raises:
        HTTPException 401: Token 无效或已过期
    """
    if _agent_token_manager is None:
        raise HTTPException(
            status_code=503,
            detail="坐席认证系统未初始化"
        )

    token = credentials.credentials
    payload = _agent_token_manager.verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Token 无效或已过期"
        )

    return payload


async def require_admin(
    agent: Dict[str, Any] = Depends(verify_agent_token)
) -> Dict[str, Any]:
    """
    要求管理员权限

    Args:
        agent: 经过 verify_agent_token 验证的坐席信息

    Returns:
        Dict: Token 载荷

    Raises:
        HTTPException 403: 权限不足（非管理员）
    """
    if agent.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="需要管理员权限"
        )
    return agent


async def require_agent(
    agent: Dict[str, Any] = Depends(verify_agent_token)
) -> Dict[str, Any]:
    """
    要求坐席权限（包括管理员）

    Args:
        agent: 经过 verify_agent_token 验证的坐席信息

    Returns:
        Dict: Token 载荷

    说明:
        此函数用于保护坐席工作台 API
        管理员和普通坐席都可以访问
    """
    return agent
