# -*- coding: utf-8 -*-
"""
安全防护组件 - IP 黑名单管理

提供 IP 封禁功能：
- 支持临时封禁（自动过期）
- 支持永久封禁
- 存储封禁原因和时间
"""

import json
import time
from typing import Any, Dict, List, Optional


class IPBlacklist:
    """
    IP 黑名单管理类

    使用 Redis 存储封禁信息：
    - security:blacklist:ip:{ip} - 封禁标记（带 TTL）
    - security:blacklist:ip - Hash 存储封禁详情

    Usage:
        from infrastructure.bootstrap import get_redis_client

        redis = get_redis_client()
        blacklist = IPBlacklist(redis)

        # 封禁 IP 1 小时
        await blacklist.add("192.168.1.100", duration=3600, reason="Too many requests")

        # 检查是否被封禁
        if await blacklist.is_blocked("192.168.1.100"):
            return 403

        # 解封
        await blacklist.remove("192.168.1.100")
    """

    # Redis Key 前缀
    KEY_PREFIX = "security:blacklist:ip"
    HASH_KEY = "security:blacklist:ip"

    def __init__(self, redis_client: Any):
        """
        初始化黑名单管理器

        Args:
            redis_client: Redis 客户端实例（同步 redis.Redis）
        """
        self.redis = redis_client

    async def is_blocked(self, ip: str) -> bool:
        """
        检查 IP 是否被封禁

        Args:
            ip: IP 地址

        Returns:
            True 表示被封禁，False 表示未封禁
        """
        if self.redis is None:
            return False

        try:
            key = f"{self.KEY_PREFIX}:{ip}"
            # 同步调用，不使用 await
            result = self.redis.exists(key)
            return bool(result)
        except Exception as e:
            print(f"[Security] ⚠️ 检查 IP 黑名单失败: {e}")
            return False

    async def add(
        self,
        ip: str,
        duration: Optional[int] = None,
        reason: str = "manual_ban"
    ) -> bool:
        """
        添加 IP 到黑名单

        Args:
            ip: IP 地址
            duration: 封禁时长（秒），None 表示永久封禁
            reason: 封禁原因

        Returns:
            True 表示添加成功
        """
        if self.redis is None:
            print("[Security] ⚠️ Redis 未初始化，无法添加黑名单")
            return False

        try:
            key = f"{self.KEY_PREFIX}:{ip}"
            now = int(time.time())

            # 封禁详情
            ban_info = {
                "ip": ip,
                "reason": reason,
                "created_at": now,
                "expires_at": now + duration if duration else None,
                "permanent": duration is None
            }

            # 设置封禁标记（同步调用）
            if duration:
                # 临时封禁，带 TTL
                self.redis.setex(key, duration, "1")
            else:
                # 永久封禁
                self.redis.set(key, "1")

            # 存储封禁详情到 Hash
            self.redis.hset(
                self.HASH_KEY,
                ip,
                json.dumps(ban_info, ensure_ascii=False)
            )

            duration_str = f"{duration}秒" if duration else "永久"
            print(f"[Security] 🚫 IP 已封禁: {ip} ({duration_str}) - {reason}")
            return True

        except Exception as e:
            print(f"[Security] ⚠️ 添加 IP 黑名单失败: {e}")
            return False

    async def remove(self, ip: str) -> bool:
        """
        从黑名单移除 IP

        Args:
            ip: IP 地址

        Returns:
            True 表示移除成功
        """
        if self.redis is None:
            return False

        try:
            key = f"{self.KEY_PREFIX}:{ip}"

            # 删除封禁标记（同步调用）
            self.redis.delete(key)

            # 删除封禁详情
            self.redis.hdel(self.HASH_KEY, ip)

            print(f"[Security] ✅ IP 已解封: {ip}")
            return True

        except Exception as e:
            print(f"[Security] ⚠️ 移除 IP 黑名单失败: {e}")
            return False

    async def get_info(self, ip: str) -> Optional[Dict]:
        """
        获取 IP 封禁详情

        Args:
            ip: IP 地址

        Returns:
            封禁详情字典，未封禁返回 None
        """
        if self.redis is None:
            return None

        try:
            # 先检查是否仍被封禁
            if not await self.is_blocked(ip):
                # 如果封禁已过期，清理详情
                self.redis.hdel(self.HASH_KEY, ip)
                return None

            # 获取详情（同步调用）
            info_str = self.redis.hget(self.HASH_KEY, ip)
            if info_str:
                return json.loads(info_str)
            return None

        except Exception as e:
            print(f"[Security] ⚠️ 获取 IP 封禁详情失败: {e}")
            return None

    async def list_all(self) -> List[Dict]:
        """
        列出所有被封禁的 IP

        Returns:
            封禁详情列表
        """
        if self.redis is None:
            return []

        try:
            result = []
            # 同步调用
            all_info = self.redis.hgetall(self.HASH_KEY)

            if not all_info:
                return []

            for ip, info_str in all_info.items():
                # 处理 bytes 类型的 key
                if isinstance(ip, bytes):
                    ip = ip.decode('utf-8')
                if isinstance(info_str, bytes):
                    info_str = info_str.decode('utf-8')

                # 检查是否仍被封禁
                if await self.is_blocked(ip):
                    try:
                        info = json.loads(info_str)
                        result.append(info)
                    except json.JSONDecodeError:
                        pass
                else:
                    # 封禁已过期，清理
                    self.redis.hdel(self.HASH_KEY, ip)

            return result

        except Exception as e:
            print(f"[Security] ⚠️ 列出黑名单失败: {e}")
            return []

    async def count(self) -> int:
        """
        获取当前封禁 IP 数量

        Returns:
            封禁 IP 数量
        """
        blocked_list = await self.list_all()
        return len(blocked_list)


# 全局单例
_blacklist_instance: Optional[IPBlacklist] = None


def get_ip_blacklist(redis_client: Any = None) -> IPBlacklist:
    """
    获取 IP 黑名单单例

    Args:
        redis_client: Redis 客户端，首次调用时必须提供

    Returns:
        IPBlacklist 实例
    """
    global _blacklist_instance

    if _blacklist_instance is None:
        if redis_client is None:
            raise RuntimeError("IPBlacklist not initialized. Provide redis_client on first call.")
        _blacklist_instance = IPBlacklist(redis_client)

    return _blacklist_instance


def init_ip_blacklist(redis_client: Any) -> IPBlacklist:
    """
    初始化 IP 黑名单

    Args:
        redis_client: Redis 客户端

    Returns:
        IPBlacklist 实例
    """
    global _blacklist_instance
    _blacklist_instance = IPBlacklist(redis_client)
    return _blacklist_instance
