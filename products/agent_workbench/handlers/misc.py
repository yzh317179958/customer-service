# -*- coding: utf-8 -*-
"""
Agent Workbench - Misc Handler

Endpoints:
- POST /admin/sessions/clear - Clear all sessions (admin)
- GET /customers/{customer_id}/profile - Get customer profile
- GET /transfer-requests/pending - Get pending transfer requests
- POST /transfer-requests/{request_id}/respond - Respond to transfer request
- POST /sessions/{session_name}/notes - Create internal note
- GET /sessions/{session_name}/notes - Get internal notes
- PUT /sessions/{session_name}/notes/{note_id} - Update internal note
- DELETE /sessions/{session_name}/notes/{note_id} - Delete internal note
- GET /sessions/{session_name}/transfer-history - Get transfer history
- GET /agent/events - Agent SSE event stream
"""
import asyncio
import json
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from services.session.state import SessionStatus, Message, AgentInfo

from products.agent_workbench.dependencies import (
    get_session_store, get_sse_queues, get_or_create_sse_queue,
    require_agent, require_admin
)


router = APIRouter(tags=["Misc"])


# ============================================================================
# Storage for transfer requests, history and internal notes
# ============================================================================

pending_transfer_requests: Dict[str, List[Dict]] = {}
transfer_history_store: Dict[str, List[Dict]] = {}
internal_notes_store: Dict[str, List[Dict[str, Any]]] = {}


def find_pending_transfer_request(request_id: str):
    """Find pending transfer request by ID"""
    for owner_id, requests in pending_transfer_requests.items():
        for index, req in enumerate(requests):
            if req.get("id") == request_id:
                return req, owner_id, index
    return None, None, None


# ============================================================================
# Request Models
# ============================================================================

class TransferResponseRequest(BaseModel):
    action: str = Field(..., description="accept or decline")
    response_note: Optional[str] = Field(default=None, max_length=200)


class InternalNoteRequest(BaseModel):
    """创建/更新内部备注请求"""
    content: str
    mentions: Optional[List[str]] = []  # @的坐席username列表


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/admin/sessions/clear")
async def clear_all_sessions(admin: Dict[str, Any] = Depends(require_admin)):
    """Clear all session data (admin only)"""
    session_store = get_session_store()

    cleared = await session_store.clear_all()
    print(f"Admin {admin.get('username')} cleared {cleared} sessions")

    return {"success": True, "cleared": cleared}


@router.get("/customers/{customer_id}/profile")
async def get_customer_profile(
    customer_id: str,
    agent: dict = Depends(require_agent)
):
    """Get customer profile by session ID"""
    session_store = get_session_store()

    session_state = await session_store.get(customer_id)
    if not session_state:
        raise HTTPException(
            status_code=404,
            detail="CUSTOMER_NOT_FOUND: Session not found"
        )

    profile = session_state.user_profile
    profile_dict = profile.model_dump()
    profile_dict["customer_id"] = customer_id

    print(f"Get customer profile: customer_id={customer_id}, agent={agent.get('username')}")

    return {"success": True, "data": profile_dict}


@router.get("/transfer-requests/pending")
async def get_pending_transfer_requests(agent: dict = Depends(require_agent)):
    """Get pending transfer requests for current agent"""
    agent_id = agent.get("agent_id")
    if not agent_id:
        raise HTTPException(status_code=401, detail="UNAUTHORIZED")

    requests = pending_transfer_requests.get(agent_id, [])
    return {
        "success": True,
        "data": requests,
        "total": len(requests)
    }


@router.post("/transfer-requests/{request_id}/respond")
async def respond_transfer_request(
    request_id: str,
    response: TransferResponseRequest,
    agent: dict = Depends(require_agent)
):
    """Respond to transfer request (accept/decline)"""
    pending_request, owner_id, index = find_pending_transfer_request(request_id)
    if not pending_request:
        raise HTTPException(
            status_code=404,
            detail="REQUEST_NOT_FOUND: Transfer request not found or already processed"
        )

    current_agent_id = agent.get("agent_id")
    if owner_id != current_agent_id:
        raise HTTPException(
            status_code=403,
            detail="PERMISSION_DENIED: Can only respond to requests assigned to you"
        )

    # Remove pending request
    pending_transfer_requests[owner_id].pop(index)
    if not pending_transfer_requests[owner_id]:
        del pending_transfer_requests[owner_id]

    session_name = pending_request["session_name"]
    from_agent_id = pending_request["from_agent_id"]
    to_agent_id = pending_request["to_agent_id"]
    to_agent_name = pending_request["to_agent_name"]
    reason = pending_request["reason"]
    note = pending_request.get("note", "")

    def append_history(record: Dict[str, Any]):
        if session_name not in transfer_history_store:
            transfer_history_store[session_name] = []
        transfer_history_store[session_name].append(record)

    if response.action == 'decline':
        record = {
            "id": request_id,
            "session_name": session_name,
            "from_agent": from_agent_id,
            "from_agent_name": pending_request.get("from_agent_name"),
            "to_agent": to_agent_id,
            "to_agent_name": to_agent_name,
            "reason": reason,
            "note": note,
            "transferred_at": pending_request.get("created_at"),
            "accepted": False,
            "decision": "declined",
            "responded_at": time.time(),
            "response_note": response.response_note or ""
        }
        append_history(record)
        return {"success": True, "message": "Transfer request declined"}

    # Accept flow
    session_store = get_session_store()

    session_state = await session_store.get(session_name)
    if not session_state:
        raise HTTPException(
            status_code=404,
            detail="SESSION_NOT_FOUND: Session not found"
        )

    if session_state.status != SessionStatus.MANUAL_LIVE:
        record = {
            "id": request_id,
            "session_name": session_name,
            "from_agent": from_agent_id,
            "from_agent_name": pending_request.get("from_agent_name"),
            "to_agent": to_agent_id,
            "to_agent_name": to_agent_name,
            "reason": reason,
            "note": note,
            "transferred_at": pending_request.get("created_at"),
            "accepted": False,
            "decision": "expired",
            "responded_at": time.time(),
            "response_note": "Session status changed"
        }
        append_history(record)
        raise HTTPException(
            status_code=409,
            detail="INVALID_STATUS: Session status changed, cannot accept transfer"
        )

    if session_state.assigned_agent and session_state.assigned_agent.id != from_agent_id:
        record = {
            "id": request_id,
            "session_name": session_name,
            "from_agent": from_agent_id,
            "from_agent_name": pending_request.get("from_agent_name"),
            "to_agent": to_agent_id,
            "to_agent_name": to_agent_name,
            "reason": reason,
            "note": note,
            "transferred_at": pending_request.get("created_at"),
            "accepted": False,
            "decision": "expired",
            "responded_at": time.time(),
            "response_note": "Session taken by other agent"
        }
        append_history(record)
        raise HTTPException(
            status_code=409,
            detail="SESSION_ALREADY_TAKEN: Session already taken by another agent"
        )

    system_message = Message(
        role="system",
        content=f"Session transferred from [{pending_request.get('from_agent_name', 'Unknown')}] to [{to_agent_name}] (reason: {reason})"
    )
    session_state.add_message(system_message)
    session_state.assigned_agent = AgentInfo(id=to_agent_id, name=to_agent_name)
    session_state.manual_start_at = time.time()

    await session_store.save(session_state)

    record = {
        "id": request_id,
        "session_name": session_name,
        "from_agent": from_agent_id,
        "from_agent_name": pending_request.get("from_agent_name"),
        "to_agent": to_agent_id,
        "to_agent_name": to_agent_name,
        "reason": reason,
        "note": note,
        "transferred_at": pending_request.get("created_at"),
        "accepted": True,
        "decision": "accepted",
        "responded_at": time.time(),
        "response_note": response.response_note or ""
    }
    append_history(record)

    # Push SSE notifications
    sse_queues = get_sse_queues()

    if session_name in sse_queues:
        await sse_queues[session_name].put({
            "type": "status_change",
            "status": "manual_live",
            "agent_info": {"agent_id": to_agent_id, "agent_name": to_agent_name},
            "reason": f"transfer_accepted_{reason}",
            "timestamp": int(time.time())
        })
        await sse_queues[session_name].put({
            "type": "manual_message",
            "role": "system",
            "content": system_message.content,
            "timestamp": system_message.timestamp
        })

    print(f"Transfer accepted: {session_name} from {from_agent_id} to {to_agent_id}")

    return {
        "success": True,
        "message": "Transfer accepted",
        "data": {
            "session": session_state.model_dump()
        }
    }


# ============================================================================
# Internal Notes Endpoints
# ============================================================================

@router.post("/sessions/{session_name}/notes")
async def create_internal_note(
    session_name: str,
    request: InternalNoteRequest,
    agent: dict = Depends(require_agent)
):
    """
    添加内部备注（仅坐席可见）

    Args:
        session_name: 会话ID
        request: 备注内容和@提醒列表
        agent: 当前登录坐席信息

    Returns:
        创建的备注信息
    """
    session_store = get_session_store()

    # 验证会话是否存在
    session_state = await session_store.get(session_name)
    if not session_state:
        raise HTTPException(
            status_code=404,
            detail="SESSION_NOT_FOUND: 会话不存在"
        )

    # 创建备注
    note = {
        "id": f"note_{uuid.uuid4().hex[:16]}",
        "session_name": session_name,
        "content": request.content,
        "created_by": agent.get("username"),
        "created_by_name": agent.get("name", agent.get("username")),
        "created_at": time.time(),
        "updated_at": time.time(),
        "mentions": request.mentions or []
    }

    # 保存到存储
    if session_name not in internal_notes_store:
        internal_notes_store[session_name] = []
    internal_notes_store[session_name].append(note)

    print(f"✅ 创建内部备注: {note['id']} for session {session_name} by {agent.get('username')}")

    # 如果有@提醒，通过SSE推送通知给被@的坐席
    if request.mentions:
        unique_mentions = set(request.mentions)
        sse_queues = get_sse_queues()
        for mention in unique_mentions:
            if mention in sse_queues:
                await sse_queues[mention].put({
                    "type": "mention",
                    "from_agent": agent.get("username"),
                    "from_agent_name": agent.get("name", agent.get("username")),
                    "session_name": session_name,
                    "note_id": note["id"],
                    "content_preview": request.content[:100] if len(request.content) > 100 else request.content,
                    "timestamp": note["created_at"]
                })
                print(f"📢 推送@提醒给: {mention}")

    return {
        "success": True,
        "data": note
    }


@router.get("/sessions/{session_name}/notes")
async def get_internal_notes(
    session_name: str,
    agent: dict = Depends(require_agent)
):
    """
    获取会话的所有内部备注

    Args:
        session_name: 会话ID
        agent: 当前登录坐席信息

    Returns:
        备注列表
    """
    # 获取备注列表
    notes = internal_notes_store.get(session_name, [])

    # 按创建时间倒序排序
    notes_sorted = sorted(notes, key=lambda x: x["created_at"], reverse=True)

    return {
        "success": True,
        "data": notes_sorted,
        "total": len(notes_sorted)
    }


@router.put("/sessions/{session_name}/notes/{note_id}")
async def update_internal_note(
    session_name: str,
    note_id: str,
    request: InternalNoteRequest,
    agent: dict = Depends(require_agent)
):
    """
    编辑内部备注（仅创建者和管理员可编辑）

    Args:
        session_name: 会话ID
        note_id: 备注ID
        request: 新的备注内容
        agent: 当前登录坐席信息

    Returns:
        更新后的备注信息
    """
    # 查找备注
    notes = internal_notes_store.get(session_name, [])
    note = next((n for n in notes if n["id"] == note_id), None)

    if not note:
        raise HTTPException(
            status_code=404,
            detail="NOTE_NOT_FOUND: 备注不存在"
        )

    # 权限检查：仅创建者和管理员可编辑
    if note["created_by"] != agent.get("username") and agent.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="PERMISSION_DENIED: 只有创建者和管理员可以编辑备注"
        )

    # 更新备注
    note["content"] = request.content
    note["mentions"] = request.mentions or []
    note["updated_at"] = time.time()

    print(f"✅ 更新内部备注: {note_id} by {agent.get('username')}")

    return {
        "success": True,
        "data": note
    }


@router.delete("/sessions/{session_name}/notes/{note_id}")
async def delete_internal_note(
    session_name: str,
    note_id: str,
    agent: dict = Depends(require_agent)
):
    """
    删除内部备注（仅创建者和管理员可删除）

    Args:
        session_name: 会话ID
        note_id: 备注ID
        agent: 当前登录坐席信息

    Returns:
        删除结果
    """
    # 查找备注
    notes = internal_notes_store.get(session_name, [])
    note = next((n for n in notes if n["id"] == note_id), None)

    if not note:
        raise HTTPException(
            status_code=404,
            detail="NOTE_NOT_FOUND: 备注不存在"
        )

    # 权限检查：仅创建者和管理员可删除
    if note["created_by"] != agent.get("username") and agent.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="PERMISSION_DENIED: 只有创建者和管理员可以删除备注"
        )

    # 删除备注
    internal_notes_store[session_name] = [
        n for n in notes if n["id"] != note_id
    ]

    print(f"✅ 删除内部备注: {note_id} by {agent.get('username')}")

    return {
        "success": True,
        "message": f"备注 {note_id} 已删除"
    }


# ============================================================================
# Transfer History Endpoint
# ============================================================================

@router.get("/sessions/{session_name}/transfer-history")
async def get_transfer_history(
    session_name: str,
    agent: dict = Depends(require_agent)
):
    """
    获取会话转接历史

    Args:
        session_name: 会话ID
        agent: 当前登录坐席信息

    Returns:
        转接历史列表
    """
    history = transfer_history_store.get(session_name, [])

    # 按时间倒序
    history_sorted = sorted(history, key=lambda x: x["transferred_at"], reverse=True)

    return {
        "success": True,
        "data": history_sorted,
        "total": len(history_sorted)
    }


# ============================================================================
# Agent SSE Event Stream
# ============================================================================

@router.get("/agent/events")
async def agent_events(agent: dict = Depends(require_agent)):
    """
    坐席事件 SSE 流
    用于接收 @提醒、协助请求等实时事件
    """
    username = agent.get("username")
    if not username:
        raise HTTPException(status_code=400, detail="INVALID_AGENT")

    # 获取或创建 SSE 队列
    queue = get_or_create_sse_queue(username)
    print(f"✅ 坐席事件SSE连接: {username}")

    async def event_generator():
        try:
            while True:
                payload = await queue.get()
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            print(f"⏹️  坐席事件 SSE 断开: {username}")
            raise
        except Exception as exc:
            print(f"❌ 坐席事件 SSE 异常: {str(exc)}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
