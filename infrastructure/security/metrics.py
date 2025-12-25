# -*- coding: utf-8 -*-
"""
安全防护组件 - Prometheus 监控指标

提供安全相关的监控指标采集和导出功能。

指标列表:
- security_rate_limit_hits_total: 限流触发次数
- security_blocked_requests_total: IP 黑名单拦截次数
- security_login_failures_total: 登录失败次数
- security_account_lockouts_total: 账户锁定次数
- security_active_blocked_ips: 当前被封禁的 IP 数量
"""

from typing import Optional, Callable

from fastapi import Request, Response
from starlette.responses import PlainTextResponse

try:
    from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
except Exception:  # pragma: no cover
    Counter = None  # type: ignore[assignment]
    Gauge = None  # type: ignore[assignment]
    generate_latest = None  # type: ignore[assignment]
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"


# ============================================================================
# 定义指标
# ============================================================================

# 限流触发次数
if Counter is not None:
    rate_limit_hits = Counter(
        "security_rate_limit_hits_total",
        "Total number of rate limit hits",
        ["endpoint", "method"],
    )
else:
    rate_limit_hits = None

# IP 黑名单拦截次数
if Counter is not None:
    blocked_requests = Counter(
        "security_blocked_requests_total",
        "Total number of blocked requests due to IP blacklist",
        ["ip"],
    )
else:
    blocked_requests = None

# 登录失败次数
if Counter is not None:
    login_failures = Counter(
        "security_login_failures_total",
        "Total number of login failures",
        ["username"],
    )
else:
    login_failures = None

# 账户锁定次数
if Counter is not None:
    account_lockouts = Counter(
        "security_account_lockouts_total",
        "Total number of account lockouts",
        ["username"],
    )
else:
    account_lockouts = None

# 当前被封禁的 IP 数量（Gauge，可增可减）
if Gauge is not None:
    active_blocked_ips = Gauge(
        "security_active_blocked_ips",
        "Current number of blocked IP addresses",
    )
else:
    active_blocked_ips = None


# ============================================================================
# 指标操作函数
# ============================================================================

def record_rate_limit_hit(endpoint: str, method: str = "POST") -> None:
    """
    记录限流触发

    Args:
        endpoint: API 端点路径
        method: HTTP 方法
    """
    if rate_limit_hits is None:
        return
    rate_limit_hits.labels(endpoint=endpoint, method=method).inc()


def record_blocked_request(ip: str) -> None:
    """
    记录 IP 黑名单拦截

    Args:
        ip: 被拦截的 IP 地址
    """
    if blocked_requests is None:
        return
    blocked_requests.labels(ip=ip).inc()


def record_login_failure(username: str) -> None:
    """
    记录登录失败

    Args:
        username: 用户名
    """
    if login_failures is None:
        return
    login_failures.labels(username=username).inc()


def record_account_lockout(username: str) -> None:
    """
    记录账户锁定

    Args:
        username: 用户名
    """
    if account_lockouts is None:
        return
    account_lockouts.labels(username=username).inc()


def set_active_blocked_ips(count: int) -> None:
    """
    设置当前被封禁的 IP 数量

    Args:
        count: IP 数量
    """
    if active_blocked_ips is None:
        return
    active_blocked_ips.set(count)


def increment_blocked_ips() -> None:
    """增加被封禁 IP 计数"""
    if active_blocked_ips is None:
        return
    active_blocked_ips.inc()


def decrement_blocked_ips() -> None:
    """减少被封禁 IP 计数"""
    if active_blocked_ips is None:
        return
    active_blocked_ips.dec()


# ============================================================================
# 指标导出
# ============================================================================

def get_metrics_response() -> Response:
    """
    生成 Prometheus 格式的指标响应

    Returns:
        FastAPI Response 对象
    """
    if generate_latest is None:
        return PlainTextResponse(
            "prometheus_client is not installed; metrics endpoint disabled.\n",
            status_code=503,
        )

    metrics_output = generate_latest()
    return Response(content=metrics_output, media_type=CONTENT_TYPE_LATEST)


def get_metrics_handler() -> Callable:
    """
    获取指标端点处理函数

    Returns:
        FastAPI 路由处理函数

    Usage:
        app.add_route("/metrics", get_metrics_handler())
    """
    async def metrics_endpoint(request: Request) -> Response:
        return get_metrics_response()

    return metrics_endpoint


# ============================================================================
# 便捷类封装
# ============================================================================

class SecurityMetrics:
    """
    安全指标便捷操作类

    Usage:
        from infrastructure.security.metrics import security_metrics

        # 记录限流
        security_metrics.rate_limit_hit("/api/chat", "POST")

        # 记录登录失败
        security_metrics.login_failure("admin")
    """

    @staticmethod
    def rate_limit_hit(endpoint: str, method: str = "POST") -> None:
        """记录限流触发"""
        record_rate_limit_hit(endpoint, method)

    @staticmethod
    def blocked_request(ip: str) -> None:
        """记录 IP 黑名单拦截"""
        record_blocked_request(ip)

    @staticmethod
    def login_failure(username: str) -> None:
        """记录登录失败"""
        record_login_failure(username)

    @staticmethod
    def account_lockout(username: str) -> None:
        """记录账户锁定"""
        record_account_lockout(username)

    @staticmethod
    def set_blocked_ips(count: int) -> None:
        """设置被封禁 IP 数量"""
        set_active_blocked_ips(count)

    @staticmethod
    def ip_blocked() -> None:
        """IP 被封禁"""
        increment_blocked_ips()

    @staticmethod
    def ip_unblocked() -> None:
        """IP 解封"""
        decrement_blocked_ips()


# 单例实例
security_metrics = SecurityMetrics()
