# -*- coding: utf-8 -*-
"""
AI 智能客服 - Sessions Handler

会话状态查询 API 端点（用户端）

Endpoints:
- GET /sessions/{session_name} - 获取会话状态（供前端轮询）
- GET /sessions/{session_name}/events - 会话 SSE 事件流
"""

import asyncio
import json
import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from products.ai_chatbot.dependencies import get_session_store
from infrastructure.bootstrap.sse import subscribe_sse_events

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("/{session_name}")
async def get_session_status(session_name: str):
    """
    获取会话状态（供前端轮询）

    返回会话的当前状态、坐席信息、历史消息等
    """
    session_store = get_session_store()

    try:
        session_state = await session_store.get(session_name)

        if not session_state:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "success": True,
            "data": {
                "session": session_state.model_dump()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取会话状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/{session_name}/events")
async def session_events(session_name: str):
    """
    会话级 SSE 事件流（用户端）

    用于实时接收坐席消息和状态变化，替代轮询

    事件类型:
    - manual_message: 人工消息（role=agent/system）
    - status_change: 会话状态变化
    - heartbeat: 心跳保活
    """
    session_store = get_session_store()

    # 验证会话存在
    session_state = await session_store.get(session_name)
    if not session_state:
        raise HTTPException(status_code=404, detail="Session not found")

    print(f"✅ 用户 SSE 连接: session={session_name}")

    async def event_generator():
        try:
            # 发送连接成功事件
            yield f"data: {json.dumps({'type': 'connected', 'session_name': session_name, 'timestamp': int(time.time())}, ensure_ascii=False)}\n\n"

            # 使用统一订阅接口（支持 Redis 跨进程）
            subscription = subscribe_sse_events(session_name)

            while True:
                try:
                    # 等待下一条消息，30秒超时发送心跳
                    payload = await asyncio.wait_for(subscription.__anext__(), timeout=30.0)
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    # 发送心跳保持连接
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': int(time.time())}, ensure_ascii=False)}\n\n"
                except StopAsyncIteration:
                    break
        except asyncio.CancelledError:
            print(f"⏹️  用户 SSE 断开: session={session_name}")
            raise
        except Exception as exc:
            print(f"❌ 用户 SSE 异常: session={session_name}, error={str(exc)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc), 'timestamp': int(time.time())}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
