# -*- coding: utf-8 -*-
"""
Agent Workbench - Sessions Handler

Endpoints:
- GET /sessions/stats - Session statistics
- GET /sessions/queue - Queue info
- GET /sessions/{session_name} - Session details
- POST /sessions/{session_name}/release - Release session
- POST /sessions/{session_name}/takeover - Takeover session
- POST /sessions/{session_name}/transfer - Transfer session
- GET /sessions - Session list
- POST /sessions/{session_name}/notes - Add notes
- POST /sessions/{session_name}/ticket - Create ticket from session
"""
import json
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from services.session.state import (
    SessionState,
    SessionStatus,
    Message,
    AgentInfo,
    MessageRole,
)
from services.ticket.models import TicketType, TicketPriority, TicketCustomerInfo
from services.ticket.store import TicketStore
from products.agent_workbench.dependencies import (
    get_session_store, get_agent_manager, get_ticket_store,
    get_sse_queues, get_or_create_sse_queue,
    require_agent
)

router = APIRouter(prefix="/sessions", tags=["Sessions"])

# Pending transfer requests storage
pending_transfer_requests: Dict[str, List[Dict]] = {}


# ============================================================================
# Request Models
# ============================================================================

class SessionTicketRequest(BaseModel):
    """Request model for creating ticket from session"""
    title: Optional[str] = None
    description: Optional[str] = None
    ticket_type: TicketType = TicketType.AFTER_SALE
    priority: TicketPriority = TicketPriority.MEDIUM


# ============================================================================
# Helper Functions
# ============================================================================

async def enqueue_sse_message(target: str, message: dict):
    """Enqueue SSE message to target"""
    sse_queues = get_sse_queues()
    if target not in sse_queues:
        return
    try:
        await sse_queues[target].put(message)
    except Exception as e:
        print(f"Warning: Failed to enqueue SSE message: {e}")


def _record_agent_response_time(agent_identifier: str, seconds: float):
    """Record agent response time (placeholder - uses backend.py impl)"""
    pass  # Will be called from backend.py's global


def _record_agent_session_duration(agent_identifier: str, seconds: float):
    """Record agent session duration (placeholder)"""
    pass


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/stats")
async def get_sessions_stats():
    """Get session statistics"""
    session_store = get_session_store()

    try:
        stats = await session_store.get_stats()

        # Calculate average waiting time
        pending_sessions = await session_store.list_by_status(
            status=SessionStatus.PENDING_MANUAL,
            limit=100
        )

        current_time = time.time()

        if pending_sessions:
            waiting_times = [
                current_time - session.escalation.trigger_at
                for session in pending_sessions
                if session.escalation
            ]
            avg_waiting_time = sum(waiting_times) / len(waiting_times) if waiting_times else 0
            max_waiting_time = max(waiting_times) if waiting_times else 0
        else:
            avg_waiting_time = 0
            max_waiting_time = 0

        stats["avg_waiting_time"] = round(avg_waiting_time, 2)
        stats["max_waiting_time"] = round(max_waiting_time, 2)

        # Get live sessions for service time
        live_sessions = await session_store.list_by_status(
            status=SessionStatus.MANUAL_LIVE,
            limit=100
        )

        if live_sessions:
            service_times = [
                current_time - (session.escalation.trigger_at if session.escalation else session.updated_at)
                for session in live_sessions
            ]
            avg_service_time = sum(service_times) / len(service_times) if service_times else 0
        else:
            avg_service_time = 0

        stats["avg_service_time"] = round(avg_service_time, 2)
        stats["active_agents"] = len(set(
            session.assigned_agent.id
            for session in live_sessions
            if session.assigned_agent
        ))

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        print(f"Error: Get stats failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/queue")
async def get_sessions_queue():
    """Get queue information"""
    session_store = get_session_store()

    try:
        pending_sessions = await session_store.list_by_status(
            status=SessionStatus.PENDING_MANUAL,
            limit=100
        )

        if not pending_sessions:
            return {
                "success": True,
                "data": {
                    "queue": [],
                    "total_count": 0,
                    "vip_count": 0,
                    "avg_wait_time": 0,
                    "max_wait_time": 0
                }
            }

        urgent_keywords = ["投诉", "退款", "质量问题", "差评", "赔偿"]
        current_time = time.time()

        for session in pending_sessions:
            session.update_priority(urgent_keywords=urgent_keywords)

        def priority_sort_key(s):
            priority_weight = {
                "urgent": 3,
                "high": 2,
                "normal": 1
            }.get(s.priority.level, 1)
            vip_priority = 1 if s.priority.is_vip else 0
            return (-vip_priority, -priority_weight, -s.priority.wait_time_seconds)

        sorted_sessions = sorted(pending_sessions, key=priority_sort_key)

        queue_data = []
        vip_count = 0
        total_wait_time = 0

        for position, session in enumerate(sorted_sessions, start=1):
            is_vip = session.user_profile.vip if session.user_profile else False
            if is_vip:
                vip_count += 1

            wait_time = session.priority.wait_time_seconds
            total_wait_time += wait_time

            queue_data.append({
                "session_name": session.session_name,
                "position": position,
                "priority_level": session.priority.level,
                "is_vip": is_vip,
                "wait_time_seconds": round(wait_time, 1),
                "is_timeout": session.priority.is_timeout,
                "urgent_keywords": session.priority.urgent_keywords,
                "user_profile": {
                    "nickname": session.user_profile.nickname if session.user_profile else "Guest",
                    "vip": is_vip
                },
                "last_message": session.history[-1].content[:50] if session.history else ""
            })

        avg_wait_time = total_wait_time / len(sorted_sessions) if sorted_sessions else 0
        max_wait_time = max([s.priority.wait_time_seconds for s in sorted_sessions]) if sorted_sessions else 0

        return {
            "success": True,
            "data": {
                "queue": queue_data,
                "total_count": len(sorted_sessions),
                "vip_count": vip_count,
                "avg_wait_time": round(avg_wait_time, 1),
                "max_wait_time": round(max_wait_time, 1)
            }
        }

    except Exception as e:
        print(f"Error: Get queue failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Get queue failed: {str(e)}")


@router.get("/{session_name}")
async def get_session_state(session_name: str):
    """Get session state"""
    session_store = get_session_store()

    try:
        session_state = await session_store.get(session_name)

        if not session_state:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "success": True,
            "data": {
                "session": session_state.model_dump(),
                "audit_trail": []
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: Get session failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Get failed: {str(e)}")


@router.post("/{session_name}/release")
async def release_session(session_name: str, request: dict):
    """Release session back to AI"""
    session_store = get_session_store()
    sse_queues = get_sse_queues()

    agent_id = request.get("agent_id")
    reason = request.get("reason", "resolved")

    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required")

    try:
        session_state = await session_store.get(session_name)

        if not session_state:
            raise HTTPException(status_code=404, detail="Session not found")

        if session_state.status != SessionStatus.MANUAL_LIVE:
            raise HTTPException(status_code=409, detail="Session not in manual_live status")

        manual_start_at = session_state.manual_start_at

        system_message = Message(
            role="system",
            content="Human service ended, AI assistant has taken over"
        )
        session_state.add_message(system_message)
        session_state.last_manual_end_at = time.time()
        session_state.transition_status(new_status=SessionStatus.BOT_ACTIVE)
        session_state.assigned_agent = None
        session_state.manual_start_at = None

        await session_store.save(session_state)

        print(json.dumps({
            "event": "session_released",
            "session_name": session_name,
            "agent_id": agent_id,
            "reason": reason,
            "timestamp": int(time.time())
        }, ensure_ascii=False))

        if session_name in sse_queues:
            await sse_queues[session_name].put({
                "type": "manual_message",
                "role": "system",
                "content": "Human service ended, AI assistant has taken over",
                "timestamp": system_message.timestamp
            })
            await sse_queues[session_name].put({
                "type": "status_change",
                "status": session_state.status,
                "reason": "released",
                "timestamp": int(time.time())
            })

        try:
            agent_manager = get_agent_manager()
            agent_manager.update_last_active(agent_id)
        except RuntimeError:
            pass

        return {
            "success": True,
            "data": session_state.model_dump()
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: Release session failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Release failed: {str(e)}")


@router.post("/{session_name}/takeover")
async def takeover_session(session_name: str, takeover_request: dict):
    """Agent takeover session"""
    session_store = get_session_store()
    sse_queues = get_sse_queues()

    agent_id = takeover_request.get("agent_id")
    agent_name = takeover_request.get("agent_name")

    if not all([agent_id, agent_name]):
        raise HTTPException(
            status_code=400,
            detail="agent_id and agent_name are required"
        )

    try:
        takeover_started_at = time.time()
        session_state = await session_store.get(session_name)

        if not session_state:
            raise HTTPException(status_code=404, detail="Session not found")

        if session_state.status != SessionStatus.PENDING_MANUAL:
            if session_state.status == SessionStatus.MANUAL_LIVE:
                assigned_agent_name = session_state.assigned_agent.name if session_state.assigned_agent else "Unknown"
                raise HTTPException(
                    status_code=409,
                    detail=f"ALREADY_TAKEN: Session already taken by agent [{assigned_agent_name}]"
                )
            else:
                raise HTTPException(
                    status_code=409,
                    detail=f"INVALID_STATUS: Current status is {session_state.status}, cannot takeover"
                )

        if session_state.assigned_agent:
            if session_state.assigned_agent.id != agent_id:
                raise HTTPException(
                    status_code=409,
                    detail=f"ASSIGNED_TO_OTHER: Session assigned to agent [{session_state.assigned_agent.name}]"
                )
        else:
            session_state.assigned_agent = AgentInfo(id=agent_id, name=agent_name)

        success = session_state.transition_status(new_status=SessionStatus.MANUAL_LIVE)

        if not success:
            raise HTTPException(status_code=500, detail="Status transition failed")

        session_state.manual_start_at = takeover_started_at

        system_message = Message(
            role="system",
            content=f"Agent [{agent_name}] has joined, serving you now"
        )
        session_state.add_message(system_message)

        await session_store.save(session_state)

        print(json.dumps({
            "event": "agent_takeover",
            "session_name": session_name,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "timestamp": int(time.time())
        }, ensure_ascii=False))

        if session_name in sse_queues:
            await sse_queues[session_name].put({
                "type": "status_change",
                "status": "manual_live",
                "agent_info": {"agent_id": agent_id, "agent_name": agent_name},
                "timestamp": int(time.time())
            })
            await sse_queues[session_name].put({
                "type": "manual_message",
                "role": "system",
                "content": f"Agent [{agent_name}] has joined, serving you now",
                "timestamp": system_message.timestamp
            })

        try:
            agent_manager = get_agent_manager()
            agent_manager.update_last_active(agent_id)
        except RuntimeError:
            pass

        return {
            "success": True,
            "data": session_state.model_dump()
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: Takeover session failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Takeover failed: {str(e)}")


@router.post("/{session_name}/transfer")
async def transfer_session(session_name: str, transfer_request: dict):
    """Transfer session to another agent"""
    session_store = get_session_store()

    from_agent_id = transfer_request.get("from_agent_id")
    to_agent_id = transfer_request.get("to_agent_id")
    to_agent_name = transfer_request.get("to_agent_name")
    reason = transfer_request.get("reason", "Agent transfer")
    note = transfer_request.get("note", "")

    if not all([from_agent_id, to_agent_id, to_agent_name]):
        raise HTTPException(
            status_code=400,
            detail="from_agent_id, to_agent_id, and to_agent_name are required"
        )

    if not reason or reason.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="REASON_REQUIRED: Transfer reason cannot be empty"
        )

    try:
        session_state = await session_store.get(session_name)

        if not session_state:
            raise HTTPException(status_code=404, detail="Session not found")

        if session_state.status != SessionStatus.MANUAL_LIVE:
            raise HTTPException(
                status_code=409,
                detail=f"INVALID_STATUS: Current status is {session_state.status}, cannot transfer"
            )

        if session_state.assigned_agent and session_state.assigned_agent.id != from_agent_id:
            raise HTTPException(
                status_code=403,
                detail="Only current serving agent can transfer session"
            )

        old_agent_name = session_state.assigned_agent.name if session_state.assigned_agent else "Unknown"

        request_id = f"transfer_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        created_at = time.time()
        pending_request = {
            "id": request_id,
            "session_name": session_name,
            "from_agent_id": from_agent_id,
            "from_agent_name": old_agent_name,
            "to_agent_id": to_agent_id,
            "to_agent_name": to_agent_name,
            "reason": reason,
            "note": note,
            "status": "pending",
            "created_at": created_at
        }

        pending_transfer_requests.setdefault(to_agent_id, []).append(pending_request)

        print(json.dumps({
            "event": "transfer_requested",
            "session_name": session_name,
            "from_agent": from_agent_id,
            "to_agent": to_agent_id,
            "reason": reason,
            "timestamp": int(created_at)
        }, ensure_ascii=False))

        return {
            "success": True,
            "data": {
                "request_id": request_id,
                "status": "pending",
                "message": f"Transfer request sent to agent [{to_agent_name}]"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: Transfer session failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transfer failed: {str(e)}")


@router.get("")
async def get_sessions_list(
    status: Optional[str] = None,
    agent_id: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100)
):
    """Get sessions list with filters"""
    session_store = get_session_store()

    try:
        if status:
            try:
                session_status = SessionStatus(status)
                sessions = await session_store.list_by_status(
                    status=session_status,
                    limit=page_size * page
                )
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        else:
            # Get all sessions
            pending = await session_store.list_by_status(SessionStatus.PENDING_MANUAL, limit=500)
            live = await session_store.list_by_status(SessionStatus.MANUAL_LIVE, limit=500)
            sessions = pending + live

        # Filter by agent_id if provided
        if agent_id:
            sessions = [
                s for s in sessions
                if s.assigned_agent and s.assigned_agent.id == agent_id
            ]

        # Pagination
        total = len(sessions)
        start = (page - 1) * page_size
        end = start + page_size
        items = sessions[start:end]

        return {
            "success": True,
            "data": {
                "items": [s.model_dump() for s in items],
                "total": total,
                "page": page,
                "page_size": page_size
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: Get sessions list failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.post("/{session_name}/notes")
async def add_session_notes(
    session_name: str,
    request: dict,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Add notes to session"""
    session_store = get_session_store()

    content = request.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Note content is required")

    try:
        session_state = await session_store.get(session_name)

        if not session_state:
            raise HTTPException(status_code=404, detail="Session not found")

        note = {
            "id": f"note_{int(time.time() * 1000)}",
            "content": content,
            "agent_id": agent.get("agent_id"),
            "agent_name": agent.get("username"),
            "created_at": time.time()
        }

        if not hasattr(session_state, "notes") or session_state.notes is None:
            session_state.notes = []
        session_state.notes.append(note)

        await session_store.save(session_state)

        return {
            "success": True,
            "data": note
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: Add notes failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Add notes failed: {str(e)}")


@router.post("/{session_name}/ticket")
async def create_ticket_from_session(
    session_name: str,
    request: SessionTicketRequest = SessionTicketRequest(),
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Create ticket from session"""
    session_store = get_session_store()
    ticket_store = get_ticket_store()

    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    try:
        session_state = await session_store.get(session_name)
        if not session_state:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get last user message as default description
        last_user_message = next(
            (msg for msg in reversed(session_state.history) if msg.role == MessageRole.USER),
            None
        )
        default_description = last_user_message.content if last_user_message else "Session to ticket"

        # Get assigned agent info
        assigned_agent_id = session_state.assigned_agent.id if session_state.assigned_agent else agent.get("agent_id")
        assigned_agent_name = session_state.assigned_agent.name if session_state.assigned_agent else agent.get("username")

        # Build customer info
        customer_info = TicketCustomerInfo(
            name=session_state.user_profile.nickname,
            email=session_state.user_profile.email,
            country=session_state.user_profile.country
        )

        # Create ticket
        ticket = ticket_store.create_from_payload(
            title=request.title or f"{session_state.user_profile.nickname}'s ticket",
            description=request.description or default_description,
            created_by=agent.get("agent_id") or agent.get("username") or "system",
            created_by_name=agent.get("username"),
            session_name=session_state.session_name,
            ticket_type=request.ticket_type,
            priority=request.priority,
            customer=customer_info.dict(),
            assigned_agent_id=assigned_agent_id,
            assigned_agent_name=assigned_agent_name,
            metadata={
                "session_name": session_state.session_name,
                "conversation_id": session_state.conversation_id
            }
        )

        # Link ticket to session
        session_state.add_ticket_reference(ticket.ticket_id)
        await session_store.save(session_state)

        return {
            "success": True,
            "data": {
                "ticket": ticket.to_dict(),
                "session": session_state.to_summary()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: Create ticket from session failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Create failed: {str(e)}")
