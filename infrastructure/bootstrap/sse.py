# -*- coding: utf-8 -*-
"""
基础设施 - SSE 消息队列管理模块

提供 Server-Sent Events 消息队列的统一管理
"""

import asyncio
from typing import Dict, Any


# ============================================================================
# 全局 SSE 队列
# ============================================================================

_sse_queues: Dict[str, asyncio.Queue] = {}


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

    Args:
        target: 目标标识
        payload: 消息内容

    注意:
        队列满时会丢弃最旧的消息
    """
    global _sse_queues
    if target not in _sse_queues:
        _sse_queues[target] = asyncio.Queue()
        print(f"[SSE] ✅ 创建全局队列: {target}")

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


def reset():
    """重置所有 SSE 队列（仅用于测试）"""
    global _sse_queues
    _sse_queues = {}
