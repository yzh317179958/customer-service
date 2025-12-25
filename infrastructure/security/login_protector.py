# -*- coding: utf-8 -*-
"""
安全防护组件 - 登录保护器

防止暴力破解攻击：
- 记录登录失败次数
- 达到阈值后锁定账户
- 支持自动解锁（TTL）
- 登录成功后重置计数
"""

import time
import math
from typing import Any, Optional

from .config import LoginProtectorConfig
from .metrics import security_metrics


class LoginProtector:
    """
    登录保护器

    防止暴力破解攻击，实现账户锁定机制：
    - 连续 N 次登录失败后锁定账户
    - 锁定时长可配置（默认 15 分钟）
    - 登录成功后自动重置失败计数

    Redis Key:
    - security:login_failures:{username} - 失败计数（带 TTL）
    - security:account_locked:{username} - 锁定标记（带 TTL）

    Usage:
        from infrastructure.bootstrap import get_redis_client

        redis = get_redis_client()
        protector = LoginProtector(redis)

        # 检查账户是否锁定
        if await protector.is_locked(username):
            raise HTTPException(423, "Account locked")

        # 验证密码...
        if password_valid:
            await protector.reset(username)
        else:
            failures = await protector.record_failure(username)
            if failures >= 5:
                # 账户将被自动锁定
                pass
    """

    # Redis Key 前缀
    FAILURES_PREFIX = "security:login_failures"
    LOCKED_PREFIX = "security:account_locked"

    def __init__(
        self,
        redis_client: Any,
        max_failures: int = 5,
        lockout_duration: int = 900,
        failure_ttl: Optional[int] = None
    ):
        """
        初始化登录保护器

        Args:
            redis_client: Redis 客户端实例（同步 redis.Redis）
            max_failures: 最大失败次数，超过后锁定
            lockout_duration: 锁定时长（秒），默认 15 分钟
            failure_ttl: 失败计数过期时间（秒），默认与锁定时长相同
        """
        self.redis = redis_client
        self.max_failures = max_failures
        self.lockout_duration = lockout_duration
        self.failure_ttl = failure_ttl or lockout_duration

    @classmethod
    def from_config(cls, redis_client: Any, config: LoginProtectorConfig) -> "LoginProtector":
        """
        从配置创建登录保护器

        Args:
            redis_client: Redis 客户端
            config: 登录保护配置

        Returns:
            LoginProtector 实例
        """
        return cls(
            redis_client=redis_client,
            max_failures=config.max_failures,
            lockout_duration=config.lockout_duration,
            failure_ttl=config.failure_ttl
        )

    async def is_locked(self, username: str) -> bool:
        """
        检查账户是否被锁定

        Args:
            username: 用户名

        Returns:
            True 表示被锁定，False 表示未锁定
        """
        if self.redis is None:
            return False

        try:
            key = f"{self.LOCKED_PREFIX}:{username}"
            # 同步调用
            result = self.redis.exists(key)
            return bool(result)
        except Exception as e:
            print(f"[Security] ⚠️ 检查账户锁定状态失败: {e}")
            return False

    async def record_failure(self, username: str) -> int:
        """
        记录登录失败

        每次调用增加失败计数，达到阈值后自动锁定账户

        Args:
            username: 用户名

        Returns:
            当前失败次数
        """
        if self.redis is None:
            print("[Security] ⚠️ Redis 未初始化，无法记录登录失败")
            return 0

        try:
            failures_key = f"{self.FAILURES_PREFIX}:{username}"

            # 增加失败计数（同步调用）
            failures = self.redis.incr(failures_key)

            # 设置/刷新 TTL
            self.redis.expire(failures_key, self.failure_ttl)

            print(f"[Security] ⚠️ 登录失败: {username} (第 {failures} 次)")
            try:
                security_metrics.login_failure(username)
            except Exception:
                pass

            # 检查是否需要锁定
            if failures >= self.max_failures:
                await self._lock_account(username)

            return failures

        except Exception as e:
            print(f"[Security] ⚠️ 记录登录失败异常: {e}")
            return 0

    async def _lock_account(self, username: str) -> None:
        """
        锁定账户

        Args:
            username: 用户名
        """
        try:
            locked_key = f"{self.LOCKED_PREFIX}:{username}"

            # 设置锁定标记（带 TTL，同步调用）
            self.redis.setex(locked_key, self.lockout_duration, "1")

            # 清除失败计数（已锁定，不需要继续计数）
            failures_key = f"{self.FAILURES_PREFIX}:{username}"
            self.redis.delete(failures_key)

            minutes = self.lockout_duration // 60
            print(f"[Security] 🔒 账户已锁定: {username} ({minutes} 分钟)")
            try:
                security_metrics.account_lockout(username)
            except Exception:
                pass

        except Exception as e:
            print(f"[Security] ⚠️ 锁定账户失败: {e}")

    async def reset(self, username: str) -> bool:
        """
        重置登录状态（登录成功后调用）

        清除失败计数和锁定状态

        Args:
            username: 用户名

        Returns:
            True 表示重置成功
        """
        if self.redis is None:
            return False

        try:
            failures_key = f"{self.FAILURES_PREFIX}:{username}"
            locked_key = f"{self.LOCKED_PREFIX}:{username}"

            # 删除失败计数和锁定标记（同步调用）
            self.redis.delete(failures_key, locked_key)

            print(f"[Security] ✅ 登录状态已重置: {username}")
            return True

        except Exception as e:
            print(f"[Security] ⚠️ 重置登录状态失败: {e}")
            return False

    async def get_failures(self, username: str) -> int:
        """
        获取当前失败次数

        Args:
            username: 用户名

        Returns:
            失败次数
        """
        if self.redis is None:
            return 0

        try:
            failures_key = f"{self.FAILURES_PREFIX}:{username}"
            # 同步调用
            failures = self.redis.get(failures_key)
            return int(failures) if failures else 0
        except Exception as e:
            print(f"[Security] ⚠️ 获取失败次数异常: {e}")
            return 0

    async def get_lockout_remaining(self, username: str) -> int:
        """
        获取剩余锁定时间（秒）

        Args:
            username: 用户名

        Returns:
            剩余锁定秒数，未锁定返回 0
        """
        if self.redis is None:
            return 0

        try:
            locked_key = f"{self.LOCKED_PREFIX}:{username}"
            # 优先使用毫秒级 TTL，避免 1 秒锁定时读到 0 的边界问题
            if hasattr(self.redis, "pttl"):
                pttl = self.redis.pttl(locked_key)
                if pttl and pttl > 0:
                    return int(math.ceil(pttl / 1000))

            ttl = self.redis.ttl(locked_key)
            return max(0, ttl) if ttl and ttl > 0 else 0
        except Exception as e:
            print(f"[Security] ⚠️ 获取锁定时间异常: {e}")
            return 0


# 全局单例
_protector_instance: Optional[LoginProtector] = None


def get_login_protector(redis_client: Any = None) -> LoginProtector:
    """
    获取登录保护器单例

    Args:
        redis_client: Redis 客户端，首次调用时必须提供

    Returns:
        LoginProtector 实例
    """
    global _protector_instance

    if _protector_instance is None:
        if redis_client is None:
            raise RuntimeError("LoginProtector not initialized. Provide redis_client on first call.")
        _protector_instance = LoginProtector(redis_client)

    return _protector_instance


def init_login_protector(
    redis_client: Any,
    config: Optional[LoginProtectorConfig] = None
) -> LoginProtector:
    """
    初始化登录保护器

    Args:
        redis_client: Redis 客户端
        config: 登录保护配置，默认从环境变量读取

    Returns:
        LoginProtector 实例
    """
    global _protector_instance

    if config is None:
        config = LoginProtectorConfig.from_env()

    _protector_instance = LoginProtector.from_config(redis_client, config)
    return _protector_instance
