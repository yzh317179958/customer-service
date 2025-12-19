# -*- coding: utf-8 -*-
"""
Agent Workbench - Misc Handler

Endpoints:
- POST /admin/sessions/clear - Clear all sessions (admin)
- GET /customers/{customer_id}/profile - Get customer profile
- GET /transfer-requests/pending - Get pending transfer requests
- POST /transfer-requests/{request_id}/respond - Respond to transfer request
"""
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.session_state import SessionStatus, Message, AgentInfo

from products.agent_workbench.dependencies import (
    get_session_store, get_sse_queues,
    require_agent, require_admin
)


router = APIRouter(tags=["Misc"])


# ============================================================================
# Storage for transfer requests and history
# ============================================================================

pending_transfer_requests: Dict[str, List[Dict]] = {}
transfer_history_store: Dict[str, List[Dict]] = {}


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
