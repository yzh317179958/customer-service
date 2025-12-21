"""
AI 智能客服 - 聊天处理器

端点:
- POST /chat - 同步聊天
- POST /chat/stream - 流式聊天
- GET /bot/info - 机器人信息
"""

import os
import json
import time
import asyncio
import uuid
import hashlib
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import httpx

# 导入依赖
from products.ai_chatbot.dependencies import (
    get_coze_client,
    get_token_manager,
    get_session_store,
    get_regulator,
    get_workflow_id,
    get_app_id,
    refresh_coze_client_if_needed,
)

# 导入模型
from products.ai_chatbot.models import ChatRequest, ChatResponse

# 导入会话状态相关
from services.session.state import (
    SessionState,
    SessionStatus,
    Message,
    EscalationInfo
)

router = APIRouter()

# HTTP 超时配置
HTTP_TIMEOUT = httpx.Timeout(
    connect=float(os.getenv("HTTP_TIMEOUT_CONNECT", 10.0)),
    read=float(os.getenv("HTTP_TIMEOUT_READ", 30.0)),
    write=float(os.getenv("HTTP_TIMEOUT_WRITE", 30.0)),
    pool=float(os.getenv("HTTP_TIMEOUT_POOL", 10.0))
)

# 会话缓存（后续会迁移到 services/session）
conversation_cache: dict = {}  # {session_name: conversation_id}

# SSE 队列（后续会迁移到 services/session）
sse_queues: dict = {}  # type: dict[str, asyncio.Queue]


def generate_user_id(ip_address: str = None, user_agent: str = None) -> str:
    """生成唯一的用户 ID（备用方案）"""
    if not ip_address and not user_agent:
        return f"user_{uuid.uuid4().hex[:16]}"

    identifier = f"{ip_address}_{user_agent}"
    hash_object = hashlib.md5(identifier.encode())
    return f"user_{hash_object.hexdigest()[:16]}"


@router.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    同步聊天接口（使用 Coze Workflow Chat API）
    通过 session_name + conversation_id 实现完整的会话隔离

    实现原理(基于官方文档):
    1. JWT 中传入 session_name (用户唯一标识)
    2. 首次对话不传 conversation_id,系统自动生成
    3. 后端存储 session_name 与 conversation_id 的映射
    4. 后续对话传入相同的 conversation_id 以保持上下文
    """
    global conversation_cache

    # 获取依赖
    token_manager = get_token_manager()
    session_store = get_session_store()
    regulator = get_regulator()
    workflow_id = get_workflow_id()
    app_id = get_app_id()

    try:
        # 获取会话标识（session_id），如果没有则生成
        session_id = request.user_id or generate_user_id()

        # 【P0-3 前置处理】检查会话状态 - 如果正在人工接管，拒绝AI对话
        if session_store and regulator:
            try:
                # 获取或创建会话状态
                conversation_id_for_state = request.conversation_id or conversation_cache.get(session_id)
                session_state = await session_store.get_or_create(
                    session_name=session_id,
                    conversation_id=conversation_id_for_state
                )

                # 如果正在人工接管中(包括等待人工和人工服务中)，返回 409 状态码
                if session_state.status in [SessionStatus.PENDING_MANUAL, SessionStatus.MANUAL_LIVE]:
                    print(f"⚠️  会话 {session_id} 状态为 {session_state.status}，拒绝AI对话")
                    raise HTTPException(
                        status_code=409,
                        detail=f"SESSION_IN_MANUAL_MODE: {session_state.status}"
                    )

                print(f"📊 会话状态: {session_state.status}")
            except HTTPException:
                raise
            except Exception as state_error:
                print(f"⚠️  状态检查异常（不影响对话）: {str(state_error)}")

        # 【会话隔离核心1】将 session_id 作为 session_name 传入 JWT
        access_token = token_manager.get_access_token(session_name=session_id)
        print(f"🔐 会话隔离: session_name={session_id}")

        # 【会话隔离核心2】管理 conversation_id
        conversation_id = request.conversation_id

        if not conversation_id:
            conversation_id = conversation_cache.get(session_id)
            if conversation_id:
                print(f"♻️  使用缓存的 Conversation: {conversation_id}")
            else:
                print(f"🆕 首次对话,将自动生成 conversation_id")

        # 准备参数（Workflow Chat API 格式）
        api_base = os.getenv("COZE_API_BASE", "https://api.coze.com")
        url = f"{api_base}/v1/workflows/chat"

        # 构建请求体
        payload = {
            "workflow_id": workflow_id,
            "app_id": app_id,
            "session_name": session_id,
            "parameters": {
                "USER_INPUT": request.message,
            },
            "additional_messages": [
                {
                    "content": request.message,
                    "content_type": "text",
                    "role": "user",
                    "type": "question"
                }
            ]
        }

        if conversation_id:
            payload["conversation_id"] = conversation_id
            print(f"💬 使用 Conversation: {conversation_id}")

        if request.parameters:
            payload["parameters"].update(request.parameters)

        print(f"📤 发送请求到 Coze:")
        print(f"   URL: {url}")
        print(f"   Session: {session_id}")
        print(f"   完整 Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")

        # 发送请求
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        http_client = httpx.Client(timeout=HTTP_TIMEOUT, trust_env=False)

        with http_client.stream('POST', url, json=payload, headers=headers) as response:
            if response.status_code != 200:
                error_text = response.text
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Coze API 错误: {error_text}"
                )

            response_messages = []
            returned_conversation_id = None
            event_type = None

            for line in response.iter_lines():
                if not line:
                    continue

                line = line.strip()
                if line.startswith('event:'):
                    event_type = line[6:].strip()
                elif line.startswith('data:'):
                    try:
                        data_str = line[5:].strip()
                        data = json.loads(data_str)

                        if 'conversation_id' in data and not returned_conversation_id:
                            returned_conversation_id = data['conversation_id']

                        if event_type == 'conversation.message.delta':
                            if 'content' in data and data.get('role') == 'assistant':
                                content = data['content']
                                if content:
                                    response_messages.append(content)

                        elif event_type is None and data.get('type') == 'answer' and data.get('content'):
                            content = data['content']
                            response_messages.append(content)
                            print(f"📤 同步接口收到 answer 类型消息: {len(content)} 字符")

                    except json.JSONDecodeError:
                        pass

        # 保存自动生成的 conversation_id
        if not conversation_id and returned_conversation_id:
            conversation_cache[session_id] = returned_conversation_id
            print(f"✅ 保存新 conversation: {returned_conversation_id} (session: {session_id})")

        final_message = "".join(response_messages) if response_messages else ""

        # 【P0-3 后置处理】更新会话状态和触发监管检查
        if session_store and regulator and final_message:
            try:
                conversation_id_for_update = returned_conversation_id or conversation_id
                session_state = await session_store.get_or_create(
                    session_name=session_id,
                    conversation_id=conversation_id_for_update
                )

                user_message = Message(role="user", content=request.message)
                session_state.add_message(user_message)

                ai_message = Message(role="assistant", content=final_message)
                session_state.add_message(ai_message)

                regulator_result = regulator.evaluate(
                    session=session_state,
                    user_message=request.message,
                    ai_response=final_message
                )

                if regulator_result.should_escalate:
                    print(f"🚨 触发人工接管: {regulator_result.reason} - {regulator_result.details}")

                    session_state.escalation = EscalationInfo(
                        reason=regulator_result.reason,
                        details=regulator_result.details,
                        severity=regulator_result.severity
                    )

                    session_state.transition_status(new_status=SessionStatus.PENDING_MANUAL)

                    print(json.dumps({
                        "event": "escalation_triggered",
                        "session_name": session_id,
                        "reason": regulator_result.reason,
                        "severity": regulator_result.severity,
                        "timestamp": int(time.time())
                    }, ensure_ascii=False))

                await session_store.save(session_state)

            except Exception as regulator_error:
                print(f"⚠️  监管处理异常（不影响对话）: {str(regulator_error)}")
                import traceback
                traceback.print_exc()

        return ChatResponse(success=True, message=final_message)

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        print(f"❌ 聊天错误: {error_msg}")

        if "token" in error_msg.lower() or "auth" in error_msg.lower() or "401" in error_msg:
            if token_manager:
                try:
                    print("🔄 检测到认证错误，清除token缓存...")
                    session_id = request.user_id or generate_user_id()
                    token_manager.invalidate_token(session_name=session_id)
                    return await chat(request)
                except Exception as retry_error:
                    error_msg = f"Token 刷新后仍然失败: {str(retry_error)}"

        return ChatResponse(success=False, error=error_msg)


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    流式聊天接口 - 使用 Coze Workflow Chat API
    通过 session_name + conversation_id 实现完整的会话隔离
    """
    global conversation_cache, sse_queues

    # 获取依赖
    token_manager = get_token_manager()
    session_store = get_session_store()
    regulator = get_regulator()
    workflow_id = get_workflow_id()
    app_id = get_app_id()

    async def event_generator():
        """SSE 事件生成器"""
        try:
            session_id = request.user_id or generate_user_id()

            # 创建 SSE 消息队列
            if session_id not in sse_queues:
                sse_queues[session_id] = asyncio.Queue()
                print(f"✅ SSE 队列已创建: {session_id}")

            # 检查会话状态
            if session_store and regulator:
                try:
                    conversation_id_for_state = request.conversation_id or conversation_cache.get(session_id)
                    session_state = await session_store.get_or_create(
                        session_name=session_id,
                        conversation_id=conversation_id_for_state
                    )

                    if session_state.status in [SessionStatus.PENDING_MANUAL, SessionStatus.MANUAL_LIVE]:
                        print(f"⚠️  流式会话 {session_id} 状态为 {session_state.status}，拒绝AI对话")
                        error_data = {
                            "type": "error",
                            "content": f"SESSION_IN_MANUAL_MODE: {session_state.status}"
                        }
                        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                        return

                    print(f"📊 流式会话状态: {session_state.status}")
                except Exception as state_error:
                    print(f"⚠️  流式状态检查异常（不影响对话）: {str(state_error)}")

            access_token = token_manager.get_access_token(session_name=session_id)
            print(f"🔐 流式会话隔离: session_name={session_id}")

            conversation_id = request.conversation_id
            if not conversation_id:
                conversation_id = conversation_cache.get(session_id)
                if conversation_id:
                    print(f"♻️  流式接口使用缓存的 Conversation: {conversation_id}")
                else:
                    print(f"🆕 流式接口首次对话,将自动生成 conversation_id")

            api_base = os.getenv("COZE_API_BASE", "https://api.coze.com")
            url = f"{api_base}/v1/workflows/chat"

            payload = {
                "workflow_id": workflow_id,
                "app_id": app_id,
                "session_name": session_id,
                "parameters": {
                    "USER_INPUT": request.message,
                },
                "additional_messages": [
                    {
                        "content": request.message,
                        "content_type": "text",
                        "role": "user",
                        "type": "question"
                    }
                ]
            }

            if conversation_id:
                payload["conversation_id"] = conversation_id
                print(f"💬 流式接口使用 Conversation: {conversation_id}")

            if request.parameters:
                payload["parameters"].update(request.parameters)

            print(f"📤 流式请求 - Session: {session_id}")

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            http_client = httpx.Client(timeout=HTTP_TIMEOUT, trust_env=False)

            with http_client.stream('POST', url, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    error_text = response.text
                    error_data = {
                        "type": "error",
                        "content": f"Coze API 错误: {error_text}"
                    }
                    yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                    return

                event_type = None
                returned_conversation_id = None
                full_ai_response = []

                for line in response.iter_lines():
                    # 检查队列中的人工消息
                    try:
                        while not sse_queues[session_id].empty():
                            queued_msg = await sse_queues[session_id].get()
                            yield f"data: {json.dumps(queued_msg, ensure_ascii=False)}\n\n"
                            print(f"✅ SSE 推送队列消息: {queued_msg.get('type')}")
                    except Exception as queue_error:
                        print(f"⚠️  SSE 队列检查异常: {str(queue_error)}")

                    if not line:
                        continue

                    line = line.strip()
                    if line.startswith('event:'):
                        event_type = line[6:].strip()
                    elif line.startswith('data:'):
                        try:
                            data_str = line[5:].strip()
                            data = json.loads(data_str)

                            if 'conversation_id' in data and not returned_conversation_id:
                                returned_conversation_id = data['conversation_id']

                            if event_type == 'conversation.message.delta':
                                if 'content' in data and data.get('role') == 'assistant':
                                    content = data['content']
                                    if content:
                                        full_ai_response.append(content)
                                        sse_data = {
                                            "type": "message",
                                            "content": content
                                        }
                                        yield f"data: {json.dumps(sse_data, ensure_ascii=False)}\n\n"

                            elif event_type is None and data.get('type') == 'answer' and data.get('content'):
                                content = data['content']
                                full_ai_response.append(content)
                                sse_data = {
                                    "type": "message",
                                    "content": content
                                }
                                yield f"data: {json.dumps(sse_data, ensure_ascii=False)}\n\n"
                                print(f"📤 Workflow answer 类型消息: {len(content)} 字符")

                            elif event_type == 'conversation.chat.failed':
                                error_content = data.get('last_error', {}).get('msg', '未知错误')
                                error_data = {
                                    "type": "error",
                                    "content": error_content
                                }
                                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                                return

                        except json.JSONDecodeError:
                            pass

            # 保存 conversation_id
            if not conversation_id and returned_conversation_id:
                conversation_cache[session_id] = returned_conversation_id
                print(f"✅ 流式接口保存新 conversation: {returned_conversation_id} (session: {session_id})")

            # 后置处理
            final_ai_message = "".join(full_ai_response)
            if session_store and regulator and final_ai_message:
                try:
                    conversation_id_for_update = returned_conversation_id or conversation_id
                    session_state = await session_store.get_or_create(
                        session_name=session_id,
                        conversation_id=conversation_id_for_update
                    )

                    user_message = Message(role="user", content=request.message)
                    session_state.add_message(user_message)

                    ai_message = Message(role="assistant", content=final_ai_message)
                    session_state.add_message(ai_message)

                    regulator_result = regulator.evaluate(
                        session=session_state,
                        user_message=request.message,
                        ai_response=final_ai_message
                    )

                    if regulator_result.should_escalate:
                        print(f"🚨 流式接口触发人工接管: {regulator_result.reason} - {regulator_result.details}")

                        session_state.escalation = EscalationInfo(
                            reason=regulator_result.reason,
                            details=regulator_result.details,
                            severity=regulator_result.severity
                        )

                        session_state.transition_status(new_status=SessionStatus.PENDING_MANUAL)

                        print(json.dumps({
                            "event": "escalation_triggered",
                            "session_name": session_id,
                            "reason": regulator_result.reason,
                            "severity": regulator_result.severity,
                            "timestamp": int(time.time())
                        }, ensure_ascii=False))

                    await session_store.save(session_state)

                except Exception as regulator_error:
                    print(f"⚠️  流式监管处理异常（不影响对话）: {str(regulator_error)}")
                    import traceback
                    traceback.print_exc()

            yield f"data: {json.dumps({'type': 'done', 'content': ''}, ensure_ascii=False)}\n\n"

        except Exception as e:
            error_msg = str(e)
            print(f"❌ 流式聊天错误: {error_msg}")

            error_data = {
                "type": "error",
                "content": f"服务器错误: {error_msg}"
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/bot/info")
async def get_bot_info():
    """获取客服配置信息(头像、昵称等)"""
    try:
        workflow_id = get_workflow_id()

        bot_name = os.getenv("COZE_BOT_NAME", "Fiido 客服")
        bot_icon_url = os.getenv("COZE_BOT_ICON_URL", "http://localhost:8000/fiido2.png")
        bot_description = os.getenv("COZE_BOT_DESCRIPTION", "Fiido 智能客服助手")
        bot_welcome = os.getenv("COZE_BOT_WELCOME", "您好！我是Fiido智能客服助手,很高兴为您服务。请问有什么可以帮助您的？")

        bot_info = {
            "name": bot_name,
            "description": bot_description,
            "icon_url": bot_icon_url,
            "welcome": bot_welcome,
            "workflow_id": workflow_id
        }

        print(f"📋 返回客服配置: 名称={bot_name}, 头像={'有' if bot_icon_url else '无'}")

        return {
            "success": True,
            "bot": bot_info
        }

    except Exception as e:
        print(f"❌ 客服信息接口错误: {str(e)}")
        return {
            "success": True,
            "bot": {
                "name": "Fiido 客服",
                "description": "Fiido 智能客服助手",
                "icon_url": "http://localhost:8000/fiido2.png",
                "welcome": "您好！有什么可以帮助您的？"
            }
        }
