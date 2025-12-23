# -*- coding: utf-8 -*-
"""
AI 智能客服 - Manual Handler

人工升级和消息处理 API 端点（用户端）

Endpoints:
- POST /manual/escalate - 人工升级
- POST /manual/messages - 人工消息写入
"""

import json
import time
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException

from services.session.state import (
    SessionState, SessionStatus, Message, EscalationInfo
)
from services.session.shift_config import is_in_shift
from services.email.service import send_escalation_email
from products.ai_chatbot.dependencies import (
    get_session_store, get_regulator,
    get_smart_assignment_engine, get_customer_reply_auto_reopen
)
from infrastructure.bootstrap.sse import enqueue_sse_message
from products.ai_chatbot.handlers.chat import conversation_cache

router = APIRouter(prefix="/manual", tags=["Manual"])


async def handle_customer_reply_event(session_state: SessionState, source: str):
    """
    当会话产生客户回复时，触发自动恢复规则
    """
    customer_reply_auto_reopen = get_customer_reply_auto_reopen()
    if not customer_reply_auto_reopen or not session_state:
        return

    try:
        async def notify_callback(target: str, payload: dict):
            # 使用统一 SSE 接口（支持 Redis 跨进程）
            await enqueue_sse_message(target, payload)

        updated_tickets = await customer_reply_auto_reopen.handle_reply(
            session_state,
            notify_callback=notify_callback
        )
    except Exception as exc:
        print(f"⚠️ 客户回复自动恢复执行失败: {exc}")
        return

    if updated_tickets:
        for ticket in updated_tickets:
            print(f"🔄 客户回复自动恢复工单: {ticket.ticket_id} (source={source})")


@router.post("/escalate")
async def manual_escalate(request: dict):
    """
    人工升级接口
    用户点击"人工客服"或监管触发后调用

    Body: { "session_name": "session_123", "reason": "user_request" }
    """
    session_store = get_session_store()

    session_name = request.get("session_name")
    reason = request.get("reason", "user_request")

    if not session_name:
        raise HTTPException(status_code=400, detail="session_name is required")

    try:
        # 获取或创建会话状态
        session_state = await session_store.get_or_create(
            session_name=session_name,
            conversation_id=conversation_cache.get(session_name)
        )

        # 检查是否已在人工接管中
        if session_state.status == SessionStatus.MANUAL_LIVE:
            raise HTTPException(status_code=409, detail="MANUAL_IN_PROGRESS")

        # 更新升级信息
        # 将 user_request 映射到正确的枚举值 "manual"
        escalation_reason = "manual" if reason == "user_request" else reason

        # P1-邮件: 检查工作时间
        in_shift = is_in_shift()
        email_sent = False

        if not in_shift:
            # 非工作时间：只发邮件，不触发状态转换
            # 创建临时会话状态用于邮件内容
            session_state.escalation = EscalationInfo(
                reason=escalation_reason,
                details=f"用户主动请求人工服务" if reason == "user_request" else f"触发原因: {reason}",
                severity="high" if reason == "user_request" else "low"
            )

            try:
                email_result = send_escalation_email(session_state)
                email_sent = email_result.get('success', False)
                if email_sent:
                    print(f"📧 非工作时间，已发送邮件通知: {session_name}")
                else:
                    print(f"⚠️  邮件发送失败: {email_result.get('error')}")
            except Exception as email_error:
                print(f"⚠️  邮件发送异常: {str(email_error)}")

            # 记录日志
            print(json.dumps({
                "event": "after_hours_escalate",
                "session_name": session_name,
                "reason": reason,
                "email_sent": email_sent,
                "timestamp": int(time.time())
            }, ensure_ascii=False))

            # 返回但不改变状态，AI继续服务
            return {
                "success": True,
                "data": session_state.model_dump(),
                "email_sent": email_sent,
                "is_in_shift": False
            }

        # 工作时间：正常触发人工接管
        session_state.escalation = EscalationInfo(
            reason=escalation_reason,
            details=f"用户主动请求人工服务" if reason == "user_request" else f"触发原因: {reason}",
            severity="high" if reason == "user_request" else "low"
        )

        # 状态转换为 pending_manual
        session_state.transition_status(
            new_status=SessionStatus.PENDING_MANUAL
        )

        # 智能分配坐席
        auto_assignment = None
        smart_assignment_engine = get_smart_assignment_engine()
        if smart_assignment_engine and not session_state.assigned_agent:
            auto_assignment = await smart_assignment_engine.assign_session(session_state)
            if auto_assignment:
                session_state.assigned_agent = auto_assignment.agent
                print(f"🤖 智能分配坐席: {auto_assignment.agent.name} ({auto_assignment.agent.id})")

        # 保存会话状态
        await session_store.save(session_state)

        # 记录日志
        print(json.dumps({
            "event": "manual_escalate",
            "session_name": session_name,
            "reason": reason,
            "status": session_state.status,
            "timestamp": int(time.time())
        }, ensure_ascii=False))

        # P0-5: 推送状态变化事件到 SSE（支持 Redis 跨进程）
        await enqueue_sse_message(session_name, {
            "type": "status_change",
            "status": session_state.status,
            "reason": reason,
            "timestamp": int(time.time())
        })
        print(f"✅ SSE 推送状态变化: {session_state.status}")

        return {
            "success": True,
            "data": session_state.model_dump(),
            "email_sent": email_sent,
            "is_in_shift": is_in_shift(),
            "auto_assigned": bool(auto_assignment),
            "recommendation": {
                "agent_id": auto_assignment.agent.id if auto_assignment else None,
                "agent_name": auto_assignment.agent.name if auto_assignment else None,
                "matched_tags": auto_assignment.matched_tags if auto_assignment else [],
                "manual_sessions": auto_assignment.manual_sessions if auto_assignment else 0,
                "pending_sessions": auto_assignment.pending_sessions if auto_assignment else 0,
            } if auto_assignment else None
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 人工升级失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"升级失败: {str(e)}")


@router.post("/messages")
async def manual_message(request: dict):
    """
    人工阶段消息写入
    用于用户/坐席在人工接管期间的消息

    Body: {
        "session_name": "session_123",
        "role": "agent" | "user",
        "content": "我要人工"
    }
    """
    session_store = get_session_store()

    session_name = request.get("session_name")
    role = request.get("role")
    content = request.get("content")

    if not all([session_name, role, content]):
        raise HTTPException(status_code=400, detail="session_name, role, and content are required")

    if role not in ["agent", "user"]:
        raise HTTPException(status_code=400, detail="role must be 'agent' or 'user'")

    try:
        # 获取会话状态
        session_state = await session_store.get(session_name)

        if not session_state:
            raise HTTPException(status_code=404, detail="Session not found")

        # 如果是用户消息，必须在manual_live状态
        if role == "user" and session_state.status != SessionStatus.MANUAL_LIVE:
            raise HTTPException(status_code=409, detail="Session not in manual_live status")

        # 创建消息
        agent_info = request.get("agent_info", {})
        message = Message(
            role=role,
            content=content,
            agent_id=agent_info.get("agent_id") if agent_info else None,
            agent_name=agent_info.get("agent_name") if agent_info else None
        )

        # 添加到历史
        session_state.add_message(message)

        # 保存会话状态
        await session_store.save(session_state)

        # 记录日志
        print(json.dumps({
            "event": "manual_message",
            "session_name": session_name,
            "role": role,
            "timestamp": message.timestamp
        }, ensure_ascii=False))

        # P0-5: 通过 SSE 推送消息到客户端（支持 Redis 跨进程）
        await enqueue_sse_message(session_name, {
            "type": "manual_message",
            "role": role,
            "content": content,
            "timestamp": message.timestamp,
            "agent_id": message.agent_id,
            "agent_name": message.agent_name
        })
        print(f"✅ SSE 推送人工消息到队列: {session_name}, role={role}")

        if role == "user":
            await handle_customer_reply_event(session_state, source="manual_message")

        return {
            "success": True,
            "data": {
                "timestamp": message.timestamp
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 写入人工消息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"写入失败: {str(e)}")
