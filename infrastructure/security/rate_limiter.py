# -*- coding: utf-8 -*-
"""
安全防护组件 - 通用限流器

基于 slowapi 封装的限流器工厂，支持：
- Redis 存储（分布式限流）
- 内存存储（单机降级）
- 双重限流（秒级防并发 + 分钟级防刷）
- 自定义限流规则
- 标准化错误响应
"""

import os
from typing import Callable, List, Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .config import RateLimiterConfig
from .metrics import security_metrics


def create_rate_limiter(config: Optional[RateLimiterConfig] = None) -> Limiter:
    """
    创建限流器实例

    Args:
        config: 限流配置，默认从环境变量读取

    Returns:
        配置好的 Limiter 实例

    Usage:
        # 使用默认配置
        limiter = create_rate_limiter()

        # 使用自定义配置
        config = RateLimiterConfig(
            default_limit="60/minute",
            burst_limit="10/second",  # 秒级限流防并发
            storage_uri="redis://localhost:6379/0"
        )
        limiter = create_rate_limiter(config)

        # 在路由中使用
        @app.get("/api/data")
        @limiter.limit("10/minute")
        async def get_data(request: Request):
            return {"data": "value"}
    """
    if config is None:
        config = RateLimiterConfig.from_env()

    # 确定 key 提取函数
    # 默认使用本模块的 get_client_ip，确保在反向代理下按真实客户端 IP 限流
    key_func = config.key_func or get_client_ip

    # 确定存储后端
    # 注意：若显式传入 config，则尊重 config.storage_uri（即便为 None）
    # RateLimiterConfig.from_env() 已经会读取 REDIS_URL，无需在这里再次兜底读取环境变量
    storage_uri = config.storage_uri

    # 预检查 Redis 可用性，避免启动时因连接超时卡住
    if storage_uri and isinstance(storage_uri, str) and storage_uri.startswith(("redis://", "rediss://")):
        try:
            import redis  # 本项目已依赖 redis>=5.0.0
            client = redis.Redis.from_url(
                storage_uri,
                socket_connect_timeout=0.2,
                socket_timeout=0.2,
                retry_on_timeout=False,
            )
            client.ping()
        except Exception as e:
            print(f"[Security] ⚠️ Redis 不可用，降级到内存存储: {e}")
            storage_uri = None

    # 构建默认限流规则列表（双重限流）
    default_limits: List[str] = []

    # 秒级限流（防止并发攻击）
    if config.burst_limit:
        default_limits.append(config.burst_limit)

    # 分钟级限流（正常限流）
    if config.default_limit:
        default_limits.append(config.default_limit)

    # 创建限流器
    if storage_uri:
        # 使用 Redis 存储（支持分布式）
        try:
            limiter = Limiter(
                key_func=key_func,
                default_limits=default_limits,
                storage_uri=storage_uri,
            )
            limits_str = " + ".join(default_limits)
            print(f"[Security] ✅ 限流器初始化成功 (Redis: {storage_uri[:30]}..., 规则: {limits_str})")
        except Exception as e:
            # Redis 连接失败，降级到内存存储
            print(f"[Security] ⚠️ Redis 连接失败，降级到内存存储: {e}")
            limiter = Limiter(
                key_func=key_func,
                default_limits=default_limits,
            )
            limits_str = " + ".join(default_limits)
            print(f"[Security] ✅ 限流器初始化成功 (内存存储, 规则: {limits_str})")
    else:
        # 无 Redis 配置，使用内存存储
        limiter = Limiter(
            key_func=key_func,
            default_limits=default_limits,
        )
        limits_str = " + ".join(default_limits)
        print(f"[Security] ✅ 限流器初始化成功 (内存存储, 规则: {limits_str})")

    return limiter


def get_rate_limit_handler(
    error_message: Optional[str] = None,
    include_retry_after: bool = True
) -> Callable:
    """
    获取限流异常处理器

    Args:
        error_message: 自定义错误消息
        include_retry_after: 是否在响应中包含重试时间

    Returns:
        FastAPI 异常处理函数

    Usage:
        from slowapi.errors import RateLimitExceeded

        app.add_exception_handler(
            RateLimitExceeded,
            get_rate_limit_handler()
        )
    """
    default_message = error_message or "Too many requests. Please try again later."

    async def rate_limit_exceeded_handler(
        request: Request,
        exc: RateLimitExceeded
    ) -> JSONResponse:
        """处理限流异常，返回标准化 JSON 响应"""
        # 解析重试时间
        retry_after = None
        if include_retry_after:
            try:
                headers = getattr(exc, "headers", None) or {}
                if isinstance(headers, dict) and headers.get("Retry-After"):
                    retry_after = int(headers["Retry-After"])
            except Exception:
                retry_after = None

        if hasattr(exc, 'detail') and exc.detail:
            # slowapi 的 detail 格式: "Rate limit exceeded: X per Y"
            try:
                # 尝试从限制规则中提取时间
                detail = str(exc.detail)
                if 'second' in detail.lower():
                    retry_after = 1
                elif 'minute' in detail.lower():
                    retry_after = 60
                elif 'hour' in detail.lower():
                    retry_after = 3600
                elif 'day' in detail.lower():
                    retry_after = 86400
            except Exception:
                retry_after = 60  # 默认 60 秒

        # 构建响应
        response_data = {
            "success": False,
            "error": default_message,
        }

        if include_retry_after and retry_after:
            response_data["retry_after"] = retry_after

        # 构建响应头
        headers = {}
        if include_retry_after and retry_after:
            headers["Retry-After"] = str(retry_after)

        # 记录日志
        client_ip = get_client_ip(request)
        print(f"[Security] 🚫 限流触发: IP={client_ip}, Path={request.url.path}")
        try:
            security_metrics.rate_limit_hit(request.url.path, request.method)
        except Exception:
            pass

        return JSONResponse(
            status_code=429,
            content=response_data,
            headers=headers
        )

    return rate_limit_exceeded_handler


def get_client_ip(request: Request) -> str:
    """
    获取客户端真实 IP

    优先从 X-Forwarded-For 或 X-Real-IP 头获取，
    适用于 nginx 反向代理场景

    安全说明:
    - 仅在受信任的反向代理后面使用
    - 生产环境通过 TRUST_PROXY=true 启用代理头解析
    - 不启用时直接使用直连 IP，防止伪造

    Args:
        request: FastAPI 请求对象

    Returns:
        客户端 IP 地址
    """
    import os

    # 检查是否信任代理头（生产环境应明确配置）
    trust_proxy = os.getenv("TRUST_PROXY", "true").lower() in ("true", "1", "yes")

    if trust_proxy:
        # 优先检查 X-Forwarded-For
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # 取第一个 IP（最原始的客户端 IP）
            return forwarded_for.split(",")[0].strip()

        # 其次检查 X-Real-IP
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

    # 最后使用直连 IP
    if request.client:
        return request.client.host

    return "unknown"
