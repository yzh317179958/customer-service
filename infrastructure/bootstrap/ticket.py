# -*- coding: utf-8 -*-
"""
基础设施 - 工单系统初始化模块

提供工单存储、模板存储、审计日志等的统一初始化
"""

from typing import Optional, Any, Type


# ============================================================================
# 全局单例
# ============================================================================

_ticket_store = None
_ticket_template_store = None
_audit_log_store = None
_quick_reply_store = None
_initialized = False
_ticket_store_cls: Optional[Type[Any]] = None
_ticket_template_store_cls: Optional[Type[Any]] = None
_audit_log_store_cls: Optional[Type[Any]] = None
_quick_reply_store_cls: Optional[Type[Any]] = None


def register_ticket_store_impls(
    ticket_store_cls: Type[Any],
    ticket_template_store_cls: Type[Any],
    audit_log_store_cls: Type[Any],
    quick_reply_store_cls: Type[Any]
) -> None:
    """
    注册工单系统相关实现类
    """
    global _ticket_store_cls, _ticket_template_store_cls, _audit_log_store_cls, _quick_reply_store_cls
    _ticket_store_cls = ticket_store_cls
    _ticket_template_store_cls = ticket_template_store_cls
    _audit_log_store_cls = audit_log_store_cls
    _quick_reply_store_cls = quick_reply_store_cls


def init_ticket_system(redis_client: Optional[Any] = None) -> dict:
    """
    初始化工单系统（单例模式）

    Args:
        redis_client: Redis 客户端（可选，为 None 时使用内存存储）

    Returns:
        包含各存储实例的字典
    """
    global _ticket_store, _ticket_template_store, _audit_log_store, _quick_reply_store, _initialized

    if _initialized:
        return {
            "ticket_store": _ticket_store,
            "ticket_template_store": _ticket_template_store,
            "audit_log_store": _audit_log_store,
            "quick_reply_store": _quick_reply_store
        }

    if not all([
        _ticket_store_cls,
        _ticket_template_store_cls,
        _audit_log_store_cls,
        _quick_reply_store_cls
    ]):
        raise RuntimeError("Ticket system implementations not registered")

    use_redis = redis_client is not None

    # 工单存储
    try:
        if use_redis:
            _ticket_store = _ticket_store_cls(redis_client)
            print("[Bootstrap] ✅ 工单系统初始化成功 (Redis)")
        else:
            _ticket_store = _ticket_store_cls()
            print("[Bootstrap] ⚠️ 工单系统使用内存存储")
    except Exception as e:
        _ticket_store = TicketStore()
        print(f"[Bootstrap] ⚠️ 工单系统初始化失败，使用内存存储: {e}")

    # 工单模板存储
    try:
        if use_redis:
            _ticket_template_store = _ticket_template_store_cls(redis_client)
            print("[Bootstrap] ✅ 工单模板存储初始化成功 (Redis)")
        else:
            _ticket_template_store = _ticket_template_store_cls()
            print("[Bootstrap] ⚠️ 工单模板使用内存存储")
    except Exception as e:
        _ticket_template_store = TicketTemplateStore()
        print(f"[Bootstrap] ⚠️ 工单模板初始化失败: {e}")

    # 审计日志存储
    try:
        if use_redis:
            _audit_log_store = _audit_log_store_cls(redis_client)
            print("[Bootstrap] ✅ 协作日志存储初始化成功 (Redis)")
        else:
            _audit_log_store = _audit_log_store_cls()
            print("[Bootstrap] ⚠️ 协作日志使用内存存储")
    except Exception as e:
        _audit_log_store = AuditLogStore()
        print(f"[Bootstrap] ⚠️ 协作日志初始化失败: {e}")

    # 快捷回复存储
    try:
        if use_redis:
            _quick_reply_store = _quick_reply_store_cls(redis_client)
            print("[Bootstrap] ✅ 快捷回复系统初始化成功 (Redis)")
        else:
            _quick_reply_store = None
            print("[Bootstrap] ⚠️ 快捷回复系统：内存存储未实现")
    except Exception as e:
        _quick_reply_store = None
        print(f"[Bootstrap] ⚠️ 快捷回复系统初始化失败: {e}")

    _initialized = True

    return {
        "ticket_store": _ticket_store,
        "ticket_template_store": _ticket_template_store,
        "audit_log_store": _audit_log_store,
        "quick_reply_store": _quick_reply_store
    }


def get_ticket_store() -> Any:
    """获取工单存储"""
    if _ticket_store is None:
        raise RuntimeError("TicketStore not initialized. Call init_ticket_system() first.")
    return _ticket_store


def get_ticket_template_store() -> Any:
    """获取工单模板存储"""
    return _ticket_template_store


def get_audit_log_store() -> Any:
    """获取审计日志存储"""
    return _audit_log_store


def get_quick_reply_store() -> Optional[Any]:
    """获取快捷回复存储（可能为 None）"""
    return _quick_reply_store


def reset():
    """重置初始化状态（仅用于测试）"""
    global _ticket_store, _ticket_template_store, _audit_log_store, _quick_reply_store, _initialized
    _ticket_store = None
    _ticket_template_store = None
    _audit_log_store = None
    _quick_reply_store = None
    _initialized = False
