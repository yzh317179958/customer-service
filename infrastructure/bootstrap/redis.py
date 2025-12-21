# -*- coding: utf-8 -*-
"""
基础设施 - Redis/Session Store 初始化模块

提供 Redis 连接和 Session Store 的统一初始化，支持：
- 单例模式：避免重复初始化
- 降级策略：Redis 不可用时降级到内存存储
- 配置外部化：通过环境变量或配置对象
"""

import os
from dataclasses import dataclass
from typing import Optional, Any, Type


@dataclass
class RedisConfig:
    """Redis 配置"""
    enabled: bool = True
    url: str = "redis://localhost:6379/0"
    max_connections: int = 50
    timeout: float = 5.0
    session_ttl: int = 86400  # 24小时

    @classmethod
    def from_env(cls) -> "RedisConfig":
        """从环境变量加载配置"""
        return cls(
            enabled=os.getenv("USE_REDIS", "true").lower() == "true",
            url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "50")),
            timeout=float(os.getenv("REDIS_TIMEOUT", "5.0")),
            session_ttl=int(os.getenv("REDIS_SESSION_TTL", "86400"))
        )


# ============================================================================
# 全局单例
# ============================================================================

_session_store = None
_redis_client = None
_initialized = False
_redis_session_store_cls: Optional[Type[Any]] = None
_memory_session_store_cls: Optional[Type[Any]] = None


def register_session_store_impls(
    redis_store_cls: Type[Any],
    memory_store_cls: Type[Any]
) -> None:
    """
    注册会话存储实现

    Args:
        redis_store_cls: Redis 会话存储类
        memory_store_cls: 内存会话存储类
    """
    global _redis_session_store_cls, _memory_session_store_cls
    _redis_session_store_cls = redis_store_cls
    _memory_session_store_cls = memory_store_cls


def init_redis(config: Optional[RedisConfig] = None) -> Any:
    """
    初始化 Redis/Session Store（单例模式）

    Args:
        config: Redis 配置，默认从环境变量读取

    Returns:
        Session Store 实例

    注意:
        - 重复调用会返回已初始化的实例
        - Redis 不可用时自动降级到内存存储
    """
    global _session_store, _redis_client, _initialized

    if _initialized and _session_store is not None:
        return _session_store

    config = config or RedisConfig.from_env()

    if config.enabled:
        try:
            if _redis_session_store_cls is None:
                raise RuntimeError("Redis session store implementation not registered")

            _session_store = _redis_session_store_cls(
                redis_url=config.url,
                max_connections=config.max_connections,
                socket_timeout=config.timeout,
                socket_connect_timeout=config.timeout,
                default_ttl=config.session_ttl
            )
            _redis_client = getattr(_session_store, "redis", None)
            _initialized = True

            print(f"[Bootstrap] ✅ Redis 初始化成功")
            print(f"   URL: {config.url}")
            print(f"   连接池: {config.max_connections}")
            print(f"   TTL: {config.session_ttl}s ({config.session_ttl/3600:.1f}h)")

            # 健康检查
            try:
                health = _session_store.check_health()
                if health.get("status") == "healthy":
                    print(f"   内存: {health.get('used_memory_mb', 'N/A')}MB")
                    print(f"   会话数: {health.get('total_sessions', 0)}")
            except Exception as health_err:
                print(f"   ⚠️ 健康检查异常: {health_err}")

        except Exception as redis_error:
            print(f"[Bootstrap] ❌ Redis 连接失败: {redis_error}")
            print(f"[Bootstrap] ⚠️ 降级到内存存储")
            _fallback_to_memory()
    else:
        print(f"[Bootstrap] ⚠️ Redis 已禁用，使用内存存储")
        _fallback_to_memory()

    return _session_store


def _fallback_to_memory():
    """降级到内存存储"""
    global _session_store, _redis_client, _initialized
    if _memory_session_store_cls is None:
        raise RuntimeError("Memory session store implementation not registered")
    _session_store = _memory_session_store_cls()
    _redis_client = None
    _initialized = True


def get_session_store() -> Any:
    """
    获取 Session Store 实例

    Returns:
        Session Store 实例

    Raises:
        RuntimeError: 未初始化时抛出
    """
    if _session_store is None:
        raise RuntimeError("Session store not initialized. Call init_redis() first.")
    return _session_store


def get_redis_client() -> Optional[Any]:
    """
    获取 Redis 客户端（可能为 None）

    Returns:
        Redis 客户端，内存模式下返回 None
    """
    return _redis_client


def is_redis_enabled() -> bool:
    """检查是否使用 Redis 存储"""
    return _redis_client is not None


def reset():
    """
    重置初始化状态（仅用于测试）
    """
    global _session_store, _redis_client, _initialized
    _session_store = None
    _redis_client = None
    _initialized = False
