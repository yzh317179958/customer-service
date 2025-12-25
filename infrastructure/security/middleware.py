# -*- coding: utf-8 -*-
"""
安全防护组件 - FastAPI 安全中间件

提供统一的安全中间件：
- IP 黑名单检查
- 返回标准 403 响应（被封禁时）
"""

from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .blacklist import IPBlacklist
from .metrics import security_metrics


@dataclass
class SecurityMiddlewareConfig:
    """
    安全中间件配置

    Attributes:
        enable_blacklist: 是否启用 IP 黑名单检查
        blacklist_error_message: 被封禁时的错误消息
        excluded_paths: 不检查的路径列表（如健康检查）
        get_client_ip: 自定义获取客户端 IP 的函数
    """
    enable_blacklist: bool = True
    blacklist_error_message: str = "Access denied. Your IP has been blocked."
    excluded_paths: List[str] = field(default_factory=lambda: ["/health", "/metrics"])
    get_client_ip: Optional[Callable[[Request], str]] = None


def get_client_ip(request: Request) -> str:
    """
    获取客户端真实 IP 地址

    优先级：
    1. X-Forwarded-For 头（nginx 反向代理）
    2. X-Real-IP 头
    3. request.client.host

    Args:
        request: FastAPI 请求对象

    Returns:
        客户端 IP 地址
    """
    # X-Forwarded-For: client, proxy1, proxy2
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # 取第一个（真实客户端 IP）
        return forwarded_for.split(",")[0].strip()

    # X-Real-IP（nginx 配置）
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # 直连客户端
    if request.client:
        return request.client.host

    return "unknown"


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    FastAPI 安全中间件

    在请求进入路由处理前进行安全检查：
    1. IP 黑名单检查 - 被封禁返回 403

    Usage:
        from infrastructure.security import SecurityMiddleware, SecurityMiddlewareConfig
        from infrastructure.security.blacklist import init_ip_blacklist
        from infrastructure.bootstrap import get_redis_client

        # 初始化黑名单
        redis = get_redis_client()
        blacklist = init_ip_blacklist(redis)

        # 添加中间件
        config = SecurityMiddlewareConfig(enable_blacklist=True)
        app.add_middleware(SecurityMiddleware, blacklist=blacklist, config=config)
    """

    def __init__(
        self,
        app: Any,
        blacklist: Optional[IPBlacklist] = None,
        config: Optional[SecurityMiddlewareConfig] = None
    ):
        """
        初始化安全中间件

        Args:
            app: FastAPI 应用实例
            blacklist: IP 黑名单实例
            config: 中间件配置
        """
        super().__init__(app)
        self.blacklist = blacklist
        self.config = config or SecurityMiddlewareConfig()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求

        检查流程：
        1. 检查是否为排除路径
        2. 获取客户端 IP
        3. 检查 IP 黑名单
        4. 通过则继续处理请求

        Args:
            request: 请求对象
            call_next: 下一个处理器

        Returns:
            响应对象
        """
        # 检查是否为排除路径
        path = request.url.path
        for excluded in self.config.excluded_paths:
            if path.startswith(excluded):
                return await call_next(request)

        # 获取客户端 IP
        if self.config.get_client_ip:
            client_ip = self.config.get_client_ip(request)
        else:
            client_ip = get_client_ip(request)

        # 检查 IP 黑名单
        if self.config.enable_blacklist and self.blacklist:
            try:
                is_blocked = await self.blacklist.is_blocked(client_ip)
                if is_blocked:
                    print(f"[Security] 🚫 请求被拒绝: IP {client_ip} 在黑名单中")
                    try:
                        security_metrics.blocked_request(client_ip)
                    except Exception:
                        pass
                    return JSONResponse(
                        status_code=403,
                        content={
                            "success": False,
                            "error": self.config.blacklist_error_message,
                            "code": "IP_BLOCKED"
                        }
                    )
            except Exception as e:
                # 黑名单检查失败不阻塞请求，记录日志
                print(f"[Security] ⚠️ IP 黑名单检查失败: {e}")

        # 继续处理请求
        response = await call_next(request)
        return response
