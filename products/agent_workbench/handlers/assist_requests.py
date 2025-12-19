# -*- coding: utf-8 -*-
"""
Agent Workbench - Assist Requests Handler

Endpoints:
- POST /assist-requests - Create assist request
- GET /assist-requests - List assist requests
- POST /assist-requests/{request_id}/answer - Answer assist request
"""
import time
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException

from src.assist_request import (
    AssistRequest, AssistStatus,
    CreateAssistRequestRequest, AnswerAssistRequestRequest,
    AssistRequestStore
)

from products.agent_workbench.dependencies import (
    get_agent_manager, get_session_store, get_sse_queues,
    require_agent
)


router = APIRouter(prefix="/assist-requests", tags=["Assist Requests"])


# ============================================================================
# Global State
# ============================================================================

_assist_request_store: Optional[AssistRequestStore] = None


def set_assist_request_store(store: AssistRequestStore) -> None:
    global _assist_request_store
    _assist_request_store = store


def get_assist_request_store() -> Optional[AssistRequestStore]:
    return _assist_request_store


async def enqueue_sse_message(target: str, payload: dict):
    """Enqueue SSE message to target"""
    sse_queues = get_sse_queues()
    if target not in sse_queues:
        return
    try:
        await sse_queues[target].put(payload)
    except Exception as e:
        print(f"Warning: Failed to enqueue SSE message: {e}")


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("")
async def create_assist_request(
    request: CreateAssistRequestRequest,
    agent: dict = Depends(require_agent)
):
    """Create assist request"""
    if not _assist_request_store:
        raise HTTPException(status_code=503, detail="Assist request system not initialized")

    try:
        agent_manager = get_agent_manager()
        session_store = get_session_store()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # Verify assistant exists
    assistant_agent = agent_manager.get_agent_by_username(request.assistant)
    if not assistant_agent:
        raise HTTPException(
            status_code=404,
            detail="ASSISTANT_NOT_FOUND: Assistant not found"
        )

    # Verify session exists
    session_state = await session_store.get(request.session_name)
    if not session_state:
        raise HTTPException(
            status_code=404,
            detail="SESSION_NOT_FOUND: Session not found"
        )

    # Create assist request
    assist_request = AssistRequest(
        id=f"assist_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}",
        session_name=request.session_name,
        requester=agent.get("username"),
        assistant=request.assistant,
        question=request.question,
        status=AssistStatus.PENDING,
        created_at=time.time()
    )

    _assist_request_store.create(assist_request)
    print(f"Created assist request: {assist_request.id} ({agent.get('username')} -> {request.assistant})")

    # Push SSE notification to assistant
    await enqueue_sse_message(request.assistant, {
        "type": "assist_request",
        "data": {
            "id": assist_request.id,
            "session_name": assist_request.session_name,
            "requester": assist_request.requester,
            "question": assist_request.question,
            "created_at": assist_request.created_at
        }
    })

    return {"success": True, "data": assist_request.model_dump()}


@router.get("")
async def get_assist_requests(
    status: Optional[str] = None,
    agent: dict = Depends(require_agent)
):
    """List assist requests"""
    if not _assist_request_store:
        raise HTTPException(status_code=503, detail="Assist request system not initialized")

    username = agent.get("username")

    filter_status = None
    if status:
        try:
            filter_status = AssistStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="INVALID_STATUS: Status must be pending or answered"
            )

    received_requests = _assist_request_store.get_by_assistant(username, status=filter_status)
    sent_requests = _assist_request_store.get_by_requester(username, status=filter_status)

    return {
        "success": True,
        "data": {
            "received": [r.model_dump() for r in received_requests],
            "sent": [r.model_dump() for r in sent_requests]
        },
        "count": {
            "received": len(received_requests),
            "sent": len(sent_requests),
            "received_pending": _assist_request_store.count_pending_by_assistant(username)
        }
    }


@router.post("/{request_id}/answer")
async def answer_assist_request(
    request_id: str,
    request: AnswerAssistRequestRequest,
    agent: dict = Depends(require_agent)
):
    """Answer assist request"""
    if not _assist_request_store:
        raise HTTPException(status_code=503, detail="Assist request system not initialized")

    assist_request = _assist_request_store.get(request_id)
    if not assist_request:
        raise HTTPException(
            status_code=404,
            detail="REQUEST_NOT_FOUND: Assist request not found"
        )

    # Permission check
    if assist_request.assistant != agent.get("username"):
        raise HTTPException(
            status_code=403,
            detail="PERMISSION_DENIED: Only the assigned assistant can answer"
        )

    if assist_request.status == AssistStatus.ANSWERED:
        raise HTTPException(
            status_code=400,
            detail="ALREADY_ANSWERED: Request already answered"
        )

    updated_request = _assist_request_store.answer(request_id, request.answer)
    print(f"Answered assist request: {request_id} by {agent.get('username')}")

    # Push SSE notification to requester
    await enqueue_sse_message(updated_request.requester, {
        "type": "assist_answer",
        "data": {
            "id": updated_request.id,
            "session_name": updated_request.session_name,
            "assistant": updated_request.assistant,
            "answer": updated_request.answer,
            "answered_at": updated_request.answered_at
        }
    })

    return {"success": True, "data": updated_request.model_dump()}
