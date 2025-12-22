# -*- coding: utf-8 -*-
"""
基础设施 - Redis Pub/Sub SSE 管理器

使用 redis.asyncio 实现跨进程 SSE 消息传递，支持：
- 异步发布消息到 Redis 频道
- 异步订阅 Redis 频道接收消息
- 自动重连和错误处理
"""

import json
import asyncio
import os
from typing import AsyncGenerator, Optional, Any

import redis.asyncio as aioredis


class RedisSseManager:
    """
    Redis Pub/Sub SSE 管理器

    用于跨进程的 SSE 消息传递，支持微服务架构下的实时通信。

    使用示例：
        manager = RedisSseManager()
        await manager.connect()

        # 发布消息
        await manager.publish("sse:session:user_123", {"type": "status_change", ...})

        # 订阅消息
        async for message in manager.subscribe("sse:session:user_123"):
            print(message)
    """

    def __init__(self, redis_url: str = None):
        """
        初始化 Redis SSE 管理器

        Args:
            redis_url: Redis 连接 URL，默认从环境变量 REDIS_URL 读取
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis: Optional[aioredis.Redis] = None
        self._connected = False

    async def connect(self) -> bool:
        """
        连接 Redis

        Returns:
            是否连接成功
        """
        if self._redis is not None and self._connected:
            return True

        try:
            self._redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0
            )
            # 测试连接
            await self._redis.ping()
            self._connected = True
            print(f"[RedisSse] ✅ 连接成功: {self._mask_url(self.redis_url)}")
            return True

        except Exception as e:
            self._connected = False
            print(f"[RedisSse] ❌ 连接失败: {e}")
            raise

    def _mask_url(self, url: str) -> str:
        """隐藏 URL 中的密码"""
        if "@" in url:
            # redis://:password@host:port/db -> redis://***@host:port/db
            parts = url.split("@")
            return f"{parts[0].split(':')[0]}://***@{parts[1]}"
        return url

    async def publish(self, channel: str, message: dict) -> int:
        """
        发布消息到 Redis 频道

        Args:
            channel: 频道名（如 sse:session:xxx）
            message: 消息内容 dict

        Returns:
            接收到消息的订阅者数量

        Raises:
            RuntimeError: 未连接时抛出
        """
        if self._redis is None or not self._connected:
            await self.connect()

        payload = json.dumps(message, ensure_ascii=False)
        result = await self._redis.publish(channel, payload)

        if result > 0:
            print(f"[RedisSse] 📤 发布到 {channel}，订阅者: {result}")

        return result

    async def subscribe(self, channel: str) -> AsyncGenerator[dict, None]:
        """
        订阅 Redis 频道，返回异步生成器

        Args:
            channel: 频道名

        Yields:
            解析后的消息 dict

        注意:
            - 此方法会阻塞直到收到消息或连接断开
            - 调用方需要在 try/finally 中处理取消
        """
        if self._redis is None or not self._connected:
            await self.connect()

        pubsub = self._redis.pubsub()
        await pubsub.subscribe(channel)
        print(f"[RedisSse] 📡 订阅频道: {channel}")

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        yield data
                    except json.JSONDecodeError as e:
                        print(f"[RedisSse] ⚠️ JSON 解析失败: {message['data'][:100]}... 错误: {e}")
                elif message["type"] == "subscribe":
                    # 订阅确认消息，忽略
                    pass

        except asyncio.CancelledError:
            print(f"[RedisSse] ⏹️ 订阅取消: {channel}")
            raise

        except Exception as e:
            print(f"[RedisSse] ❌ 订阅异常: {channel}, 错误: {e}")
            raise

        finally:
            try:
                await pubsub.unsubscribe(channel)
                await pubsub.close()
                print(f"[RedisSse] 🔌 取消订阅: {channel}")
            except Exception as e:
                print(f"[RedisSse] ⚠️ 清理订阅失败: {e}")

    async def close(self):
        """关闭 Redis 连接"""
        if self._redis:
            try:
                await self._redis.close()
                self._redis = None
                self._connected = False
                print("[RedisSse] 🔌 连接关闭")
            except Exception as e:
                print(f"[RedisSse] ⚠️ 关闭连接失败: {e}")

    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected and self._redis is not None

    async def health_check(self) -> dict:
        """
        健康检查

        Returns:
            健康状态信息
        """
        try:
            if self._redis is None or not self._connected:
                return {"status": "disconnected", "error": "Not connected"}

            await self._redis.ping()
            info = await self._redis.info("server")
            return {
                "status": "healthy",
                "redis_version": info.get("redis_version", "unknown"),
                "connected_clients": info.get("connected_clients", "unknown")
            }

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# ============================================================================
# 全局单例管理
# ============================================================================

_redis_sse_manager: Optional[RedisSseManager] = None
_init_lock = asyncio.Lock() if hasattr(asyncio, 'Lock') else None


def init_redis_sse(redis_url: str = None) -> RedisSseManager:
    """
    初始化 Redis SSE 管理器（单例模式）

    Args:
        redis_url: Redis 连接 URL，默认从环境变量读取

    Returns:
        RedisSseManager 实例

    注意:
        此函数只创建实例，不建立连接。连接在首次 publish/subscribe 时自动建立。
    """
    global _redis_sse_manager

    if _redis_sse_manager is not None:
        return _redis_sse_manager

    url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
    _redis_sse_manager = RedisSseManager(redis_url=url)
    print(f"[RedisSse] ✅ 管理器初始化完成")

    return _redis_sse_manager


def get_redis_sse_manager() -> Optional[RedisSseManager]:
    """
    获取 Redis SSE 管理器实例

    Returns:
        RedisSseManager 实例，未初始化时返回 None
    """
    return _redis_sse_manager


async def shutdown_redis_sse():
    """
    关闭 Redis SSE 管理器

    用于应用关闭时清理资源。
    """
    global _redis_sse_manager

    if _redis_sse_manager:
        await _redis_sse_manager.close()
        _redis_sse_manager = None
        print("[RedisSse] ✅ 管理器已关闭")


def reset_redis_sse():
    """
    重置 Redis SSE 管理器（仅用于测试）
    """
    global _redis_sse_manager
    _redis_sse_manager = None
