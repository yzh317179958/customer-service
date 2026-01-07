# -*- coding: utf-8 -*-
"""
基础设施 - 坐席认证系统初始化模块

提供坐席账号管理和 JWT Token 管理的统一初始化
"""

import os
from dataclasses import dataclass
from typing import Optional, Any
from fnmatch import fnmatch


@dataclass
class AgentAuthConfig:
    """坐席认证配置"""
    jwt_secret: str = "dev_secret_key_change_in_production_2025"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    super_admin_username: str = "admin"
    super_admin_password: str = "admin123"

    @classmethod
    def from_env(cls) -> "AgentAuthConfig":
        """从环境变量加载配置"""
        return cls(
            jwt_secret=os.getenv("JWT_SECRET_KEY", "dev_secret_key_change_in_production_2025"),
            algorithm="HS256",
            access_token_expire_minutes=int(os.getenv("AGENT_TOKEN_EXPIRE_MINUTES", "60")),
            refresh_token_expire_days=int(os.getenv("AGENT_REFRESH_TOKEN_EXPIRE_DAYS", "7")),
            super_admin_username=os.getenv("SUPER_ADMIN_USERNAME", "admin"),
            super_admin_password=os.getenv("SUPER_ADMIN_PASSWORD", "admin123")
        )


# ============================================================================
# 全局单例
# ============================================================================

_agent_manager = None
_agent_token_manager = None
_initialized = False


class _InMemoryRedis:
    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:  # noqa: ARG002
        self._data[str(key)] = str(value)
        return True

    def get(self, key: str) -> Optional[str]:
        return self._data.get(str(key))

    def delete(self, key: str) -> int:
        k = str(key)
        existed = 1 if k in self._data else 0
        self._data.pop(k, None)
        return existed

    def scan_iter(self, pattern: str, count: int = 100):  # noqa: ARG002
        pat = str(pattern)
        for k in list(self._data.keys()):
            if fnmatch(k, pat):
                yield k


class _InMemoryRedisStore:
    def __init__(self) -> None:
        self.redis = _InMemoryRedis()


def init_agent_auth(session_store: Any, config: Optional[AgentAuthConfig] = None) -> tuple:
    """
    初始化坐席认证系统（单例模式）

    Args:
        session_store: Session Store 实例（用于 AgentManager）
        config: 认证配置，默认从环境变量读取

    Returns:
        (AgentManager, AgentTokenManager) 元组

    注意:
        必须先调用 init_redis() 获取 session_store
    """
    global _agent_manager, _agent_token_manager, _initialized

    if _initialized and _agent_manager is not None:
        return _agent_manager, _agent_token_manager

    config = config or AgentAuthConfig.from_env()

    try:
        from infrastructure.security.agent_auth import (
            AgentManager,
            AgentTokenManager,
            initialize_super_admin
        )

        # 初始化 Token 管理器
        _agent_token_manager = AgentTokenManager(
            secret_key=config.jwt_secret,
            algorithm=config.algorithm,
            access_token_expire_minutes=config.access_token_expire_minutes,
            refresh_token_expire_days=config.refresh_token_expire_days
        )

        # 初始化坐席账号管理器
        if not hasattr(session_store, "redis") or getattr(session_store, "redis", None) is None:
            print("[Bootstrap] ⚠️ Redis 不可用，坐席认证降级为内存存储（仅开发/本地验收）")
            _agent_manager = AgentManager(_InMemoryRedisStore())
        else:
            _agent_manager = AgentManager(session_store)

        # 初始化超级管理员账号
        print(f"[Bootstrap] 🔐 初始化坐席认证系统...")
        initialize_super_admin(
            _agent_manager,
            config.super_admin_username,
            config.super_admin_password
        )

        print(f"[Bootstrap] ✅ 坐席认证系统初始化成功")
        print(f"   Token过期时间: {config.access_token_expire_minutes}分钟")
        print(f"   刷新Token过期: {config.refresh_token_expire_days}天")
        print(f"   超级管理员: {config.super_admin_username}")

        _initialized = True
        return _agent_manager, _agent_token_manager

    except Exception as e:
        print(f"[Bootstrap] ⚠️ 坐席认证系统初始化失败: {str(e)}")
        print(f"[Bootstrap]    坐席登录功能将不可用")
        raise


def get_agent_manager() -> Any:
    """
    获取坐席账号管理器

    Returns:
        AgentManager 实例

    Raises:
        RuntimeError: 未初始化时抛出
    """
    if _agent_manager is None:
        raise RuntimeError("AgentManager not initialized. Call init_agent_auth() first.")
    return _agent_manager


def get_agent_token_manager() -> Any:
    """
    获取坐席 Token 管理器

    Returns:
        AgentTokenManager 实例

    Raises:
        RuntimeError: 未初始化时抛出
    """
    if _agent_token_manager is None:
        raise RuntimeError("AgentTokenManager not initialized. Call init_agent_auth() first.")
    return _agent_token_manager


def reset():
    """重置初始化状态（仅用于测试）"""
    global _agent_manager, _agent_token_manager, _initialized
    _agent_manager = None
    _agent_token_manager = None
    _initialized = False
