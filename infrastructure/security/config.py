# -*- coding: utf-8 -*-
"""
安全防护组件 - 配置模型

提供安全组件的配置数据类：
- RateLimiterConfig: 限流器配置
- SecurityConfig: 统一安全配置
"""

import os
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional


@dataclass
class RateLimiterConfig:
    """
    限流器配置

    Attributes:
        default_limit: 默认限流规则，格式 "次数/时间单位"
                       支持: second, minute, hour, day
                       示例: "60/minute", "10/second", "1000/hour"
        burst_limit: 突发限流规则（秒级），防止并发攻击
                     示例: "5/second" 表示每秒最多 5 个请求
        storage_uri: Redis 连接 URI，None 则使用内存存储
                     格式: redis://localhost:6379/0
        key_func: 限流 Key 提取函数，默认使用 IP 地址
        endpoint_limits: 端点级别的限流规则覆盖
        error_message: 限流触发时的错误消息
        retry_after_header: 是否在响应中包含 Retry-After 头
    """
    default_limit: str = "60/minute"
    burst_limit: Optional[str] = "10/second"  # 秒级限流，防止并发攻击
    storage_uri: Optional[str] = None
    key_func: Optional[Callable] = None
    endpoint_limits: Dict[str, str] = field(default_factory=dict)
    error_message: str = "Too many requests. Please try again later."
    retry_after_header: bool = True

    @classmethod
    def from_env(cls) -> "RateLimiterConfig":
        """
        从环境变量创建配置

        环境变量:
            REDIS_URL: Redis 连接地址
            RATE_LIMIT_DEFAULT: 默认限流规则
            RATE_LIMIT_BURST: 突发限流规则（秒级）
            RATE_LIMIT_CHAT: /chat 端点限流规则
            RATE_LIMIT_LOGIN: /login 端点限流规则
        """
        endpoint_limits = {}

        # 读取端点级别限流配置
        chat_limit = os.getenv("RATE_LIMIT_CHAT")
        if chat_limit:
            endpoint_limits["/api/chat"] = chat_limit
            endpoint_limits["/api/chat/stream"] = chat_limit

        login_limit = os.getenv("RATE_LIMIT_LOGIN")
        if login_limit:
            endpoint_limits["/api/agent/login"] = login_limit

        return cls(
            default_limit=os.getenv("RATE_LIMIT_DEFAULT", "60/minute"),
            burst_limit=os.getenv("RATE_LIMIT_BURST", "10/second"),
            storage_uri=os.getenv("REDIS_URL"),
            endpoint_limits=endpoint_limits,
        )


@dataclass
class LoginProtectorConfig:
    """
    登录保护器配置

    Attributes:
        max_failures: 最大失败次数，超过后锁定账户
        lockout_duration: 锁定时长（秒）
        failure_ttl: 失败计数的过期时间（秒），与锁定时长相同
    """
    max_failures: int = 5
    lockout_duration: int = 900  # 15 分钟
    failure_ttl: int = 900

    @classmethod
    def from_env(cls) -> "LoginProtectorConfig":
        """从环境变量创建配置"""
        return cls(
            max_failures=int(os.getenv("LOGIN_MAX_FAILURES", "5")),
            lockout_duration=int(os.getenv("LOGIN_LOCKOUT_SECONDS", "900")),
            failure_ttl=int(os.getenv("LOGIN_LOCKOUT_SECONDS", "900")),
        )


@dataclass
class SecurityConfig:
    """
    统一安全配置

    聚合所有安全相关配置，便于一次性初始化
    """
    rate_limiter: RateLimiterConfig = field(default_factory=RateLimiterConfig)
    login_protector: LoginProtectorConfig = field(default_factory=LoginProtectorConfig)

    # IP 黑名单配置
    blacklist_default_duration: int = 3600  # 默认封禁 1 小时

    # 输入校验配置
    max_message_length: int = 2000  # 消息最大长度

    @classmethod
    def from_env(cls) -> "SecurityConfig":
        """从环境变量创建完整配置"""
        return cls(
            rate_limiter=RateLimiterConfig.from_env(),
            login_protector=LoginProtectorConfig.from_env(),
            blacklist_default_duration=int(os.getenv("BLACKLIST_DEFAULT_DURATION", "3600")),
            max_message_length=int(os.getenv("MAX_MESSAGE_LENGTH", "2000")),
        )
