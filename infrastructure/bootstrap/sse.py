# -*- coding: utf-8 -*-
"""
基础设施 - SSE 消息队列管理模块

提供 Server-Sent Events 消息队列的统一管理，支持：
- Redis Pub/Sub 模式（跨进程）
- 内存队列模式（单进程降级）
"""

import asyncio
import os
from typing import Dict, Any, Optional, AsyncGenerator


# ============================================================================
# 配置
# ============================================================================

USE_REDIS_SSE = os.getenv("USE_REDIS_SSE", "true").lower() == "true"


# ============================================================================
# 全局 SSE 队列（内存模式）
# ============================================================================

_sse_queues: Dict[str, asyncio.Queue] = {}


# ============================================================================
# Redis SSE 管理器（延迟加载）
# ============================================================================

_redis_sse_manager: Optional[Any] = None
_redis_sse_logged = False  # 只记录一次日志


def _get_redis_sse_manager():
    """
    获取 Redis SSE 管理器（延迟加载）

    每次调用都检查管理器是否可用，确保在初始化后能正确获取
    """
    global _redis_sse_manager, _redis_sse_logged

    if not USE_REDIS_SSE:
        return None

    # 每次都尝试获取最新的管理器（可能在后续被初始化）
    try:
        from infrastructure.bootstrap.redis_sse import get_redis_sse_manager
        manager = get_redis_sse_manager()
        if manager:
            if not _redis_sse_logged:
                print("[SSE] ✅ 使用 Redis Pub/Sub 模式")
                _redis_sse_logged = True
            _redis_sse_manager = manager
            return manager
        else:
            if not _redis_sse_logged:
                print("[SSE] ⚠️ Redis SSE 管理器未初始化，使用内存队列")
            return None
    except Exception as e:
        if not _redis_sse_logged:
            print(f"[SSE] ⚠️ Redis SSE 不可用: {e}，使用内存队列")
        return None


def get_sse_queues() -> Dict[str, asyncio.Queue]:
    """获取 SSE 队列字典"""
    return _sse_queues


def get_or_create_sse_queue(target: str) -> asyncio.Queue:
    """
    获取或创建指定目标的 SSE 队列

    Args:
        target: 目标标识（如 session_name 或 agent_username）

    Returns:
        asyncio.Queue 实例
    """
    global _sse_queues
    if target not in _sse_queues:
        _sse_queues[target] = asyncio.Queue()
        print(f"[SSE] ✅ 创建队列: {target}")
    return _sse_queues[target]


async def enqueue_sse_message(target: str, payload: dict):
    """
    将消息放入指定目标的 SSE 队列

    优先使用 Redis Pub/Sub 发布消息（跨进程），
    Redis 不可用时降级到内存队列（仅单进程有效）。

    Args:
        target: 目标标识（session_name 或 agent_id）
        payload: 消息内容

    注意:
        - Redis 模式：发布到 sse:session:{target} 频道
        - 内存模式：队列满时会丢弃最旧的消息
    """
    # 尝试使用 Redis
    manager = _get_redis_sse_manager()
    if manager:
        try:
            channel = f"sse:session:{target}"
            await manager.publish(channel, payload)
            return
        except Exception as e:
            print(f"[SSE] ⚠️ Redis 发布失败，降级到内存队列: {e}")

    # 降级到内存队列
    await _enqueue_to_memory(target, payload)


async def _enqueue_to_memory(target: str, payload: dict):
    """将消息放入内存队列（降级模式）"""
    global _sse_queues

    if target not in _sse_queues:
        _sse_queues[target] = asyncio.Queue()
        print(f"[SSE] ✅ 创建内存队列: {target}")

    queue = _sse_queues[target]
    try:
        queue.put_nowait(payload)
    except asyncio.QueueFull:
        # 队列满时丢弃最旧的消息
        try:
            queue.get_nowait()
        except asyncio.QueueEmpty:
            pass
        queue.put_nowait(payload)


def remove_sse_queue(target: str):
    """移除指定目标的 SSE 队列"""
    global _sse_queues
    if target in _sse_queues:
        del _sse_queues[target]
        print(f"[SSE] 🗑️ 移除队列: {target}")


# ============================================================================
# SSE 订阅接口
# ============================================================================

async def subscribe_sse_events(target: str) -> AsyncGenerator[dict, None]:
    """
    订阅 SSE 事件流

    优先使用 Redis Pub/Sub 订阅消息（跨进程），
    Redis 不可用时降级到内存队列（仅单进程有效）。

    Args:
        target: 目标标识（session_name 或 agent_id）

    Yields:
        消息 dict

    注意:
        - Redis 模式：订阅 sse:session:{target} 频道
        - 内存模式：从内存队列读取
        - 调用方需要在 try/finally 中处理取消
    """
    manager = _get_redis_sse_manager()
    if manager:
        try:
            channel = f"sse:session:{target}"
            print(f"[SSE] 📡 Redis 订阅: {channel}")
            async for message in manager.subscribe(channel):
                yield message
        except Exception as e:
            print(f"[SSE] ⚠️ Redis 订阅失败，降级到内存队列: {e}")
            # 降级到内存队列
            async for message in _subscribe_from_memory(target):
                yield message
    else:
        # 使用内存队列
        async for message in _subscribe_from_memory(target):
            yield message


async def _subscribe_from_memory(target: str) -> AsyncGenerator[dict, None]:
    """
    从内存队列订阅消息（降级模式）

    Args:
        target: 目标标识

    Yields:
        消息 dict
    """
    queue = get_or_create_sse_queue(target)
    print(f"[SSE] 📡 内存队列订阅: {target}")

    try:
        while True:
            message = await queue.get()
            yield message
    except asyncio.CancelledError:
        print(f"[SSE] ⏹️ 内存队列订阅取消: {target}")
        raise


def reset():
    """重置所有 SSE 队列（仅用于测试）"""
    global _sse_queues
    _sse_queues = {}
