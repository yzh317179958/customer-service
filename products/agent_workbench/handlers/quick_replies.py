# -*- coding: utf-8 -*-
"""
Agent Workbench - Quick Replies Handler

Endpoints:
- GET /quick-replies/categories - Get categories
- GET /quick-replies/stats - Get usage stats (admin)
- GET /quick-replies - List quick replies
- POST /quick-replies - Create quick reply
- GET /quick-replies/{reply_id} - Get quick reply
- PUT /quick-replies/{reply_id} - Update quick reply
- DELETE /quick-replies/{reply_id} - Delete quick reply
- POST /quick-replies/{reply_id}/use - Use quick reply
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from src.quick_reply import QuickReply, QUICK_REPLY_CATEGORIES, SUPPORTED_VARIABLES
from src.quick_reply_store import QuickReplyStore
from src.variable_replacer import VariableReplacer, build_variable_context

from products.agent_workbench.dependencies import (
    get_quick_reply_store, require_agent
)


router = APIRouter(prefix="/quick-replies", tags=["Quick Replies"])


# ============================================================================
# Global State
# ============================================================================

_variable_replacer: Optional[VariableReplacer] = None


def set_variable_replacer(replacer: VariableReplacer) -> None:
    global _variable_replacer
    _variable_replacer = replacer


def get_variable_replacer() -> Optional[VariableReplacer]:
    return _variable_replacer


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/categories")
async def get_quick_reply_categories(agent: dict = Depends(require_agent)):
    """Get quick reply categories"""
    return {
        "success": True,
        "data": {
            "categories": QUICK_REPLY_CATEGORIES,
            "supported_variables": SUPPORTED_VARIABLES
        }
    }


@router.get("/stats")
async def get_quick_reply_stats(agent: dict = Depends(require_agent)):
    """Get quick reply usage stats (admin only)"""
    if agent.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="PERMISSION_DENIED: Admin permission required"
        )

    quick_reply_store = get_quick_reply_store()
    if not quick_reply_store:
        raise HTTPException(status_code=503, detail="Quick reply system not initialized")

    stats = quick_reply_store.get_stats()
    return {"success": True, "data": stats}


@router.get("")
async def get_quick_replies(
    category: Optional[str] = None,
    agent_id: Optional[str] = None,
    include_shared: bool = True,
    keyword: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    agent: dict = Depends(require_agent)
):
    """List quick replies"""
    quick_reply_store = get_quick_reply_store()
    if not quick_reply_store:
        raise HTTPException(status_code=503, detail="Quick reply system not initialized")

    if not agent_id:
        agent_id = agent.get("agent_id")

    try:
        if keyword:
            replies = quick_reply_store.search(
                keyword=keyword,
                agent_id=agent_id,
                category=category,
                limit=limit
            )
        elif category:
            replies = quick_reply_store.list_by_category(
                category=category,
                limit=limit,
                offset=offset
            )
        elif agent_id:
            replies = quick_reply_store.list_by_agent(
                agent_id=agent_id,
                include_shared=include_shared,
                limit=limit,
                offset=offset
            )
        else:
            replies = quick_reply_store.list_all(limit=limit, offset=offset)

        return {
            "success": True,
            "data": {
                "items": [r.to_dict() for r in replies],
                "total": len(replies),
                "limit": limit,
                "offset": offset
            }
        }
    except Exception as e:
        print(f"Error: Get quick replies failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Get failed: {str(e)}")


@router.post("")
async def create_quick_reply(
    request: dict,
    agent: dict = Depends(require_agent)
):
    """Create quick reply"""
    quick_reply_store = get_quick_reply_store()
    if not quick_reply_store or not _variable_replacer:
        raise HTTPException(status_code=503, detail="Quick reply system not initialized")

    if not request.get("title") or not request.get("content"):
        raise HTTPException(
            status_code=400,
            detail="MISSING_FIELDS: title and content are required"
        )

    category = request.get("category", "custom")
    if category not in QUICK_REPLY_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"INVALID_CATEGORY: Invalid category {category}"
        )

    content = request.get("content")
    variables = _variable_replacer.extract_variables(content)

    quick_reply = QuickReply(
        id="",
        title=request.get("title"),
        content=content,
        category=category,
        variables=variables,
        shortcut_key=request.get("shortcut_key"),
        is_shared=request.get("is_shared", False),
        created_by=agent.get("agent_id")
    )

    created = quick_reply_store.create(quick_reply)
    print(f"Created quick reply: {created.id} by {agent.get('username')}")

    return {"success": True, "data": created.to_dict()}


@router.get("/{reply_id}")
async def get_quick_reply(
    reply_id: str,
    agent: dict = Depends(require_agent)
):
    """Get quick reply by ID"""
    quick_reply_store = get_quick_reply_store()
    if not quick_reply_store:
        raise HTTPException(status_code=503, detail="Quick reply system not initialized")

    reply = quick_reply_store.get(reply_id)
    if not reply:
        raise HTTPException(
            status_code=404,
            detail="QUICK_REPLY_NOT_FOUND: Quick reply not found"
        )

    return {"success": True, "data": reply.to_dict()}


@router.put("/{reply_id}")
async def update_quick_reply(
    reply_id: str,
    request: dict,
    agent: dict = Depends(require_agent)
):
    """Update quick reply"""
    quick_reply_store = get_quick_reply_store()
    if not quick_reply_store or not _variable_replacer:
        raise HTTPException(status_code=503, detail="Quick reply system not initialized")

    reply = quick_reply_store.get(reply_id)
    if not reply:
        raise HTTPException(
            status_code=404,
            detail="QUICK_REPLY_NOT_FOUND: Quick reply not found"
        )

    # Permission check
    if reply.created_by != agent.get("agent_id") and agent.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="PERMISSION_DENIED: Only creator or admin can modify"
        )

    updates = {}

    if "title" in request:
        updates["title"] = request["title"]

    if "content" in request:
        updates["content"] = request["content"]
        updates["variables"] = _variable_replacer.extract_variables(request["content"])

    if "category" in request:
        category = request["category"]
        if category not in QUICK_REPLY_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail=f"INVALID_CATEGORY: Invalid category {category}"
            )
        updates["category"] = category

    if "shortcut_key" in request:
        updates["shortcut_key"] = request["shortcut_key"]

    if "is_shared" in request:
        updates["is_shared"] = request["is_shared"]

    updated = quick_reply_store.update(reply_id, updates)
    if not updated:
        raise HTTPException(status_code=500, detail="Update failed")

    print(f"Updated quick reply: {reply_id} by {agent.get('username')}")
    return {"success": True, "data": updated.to_dict()}


@router.delete("/{reply_id}")
async def delete_quick_reply(
    reply_id: str,
    agent: dict = Depends(require_agent)
):
    """Delete quick reply"""
    quick_reply_store = get_quick_reply_store()
    if not quick_reply_store:
        raise HTTPException(status_code=503, detail="Quick reply system not initialized")

    reply = quick_reply_store.get(reply_id)
    if not reply:
        raise HTTPException(
            status_code=404,
            detail="QUICK_REPLY_NOT_FOUND: Quick reply not found"
        )

    # Permission check
    if reply.created_by != agent.get("agent_id") and agent.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="PERMISSION_DENIED: Only creator or admin can delete"
        )

    result = quick_reply_store.delete(reply_id)
    if not result:
        raise HTTPException(status_code=500, detail="Delete failed")

    print(f"Deleted quick reply: {reply_id} by {agent.get('username')}")
    return {"success": True, "message": f"Quick reply {reply_id} deleted"}


@router.post("/{reply_id}/use")
async def use_quick_reply(
    reply_id: str,
    request: dict,
    agent: dict = Depends(require_agent)
):
    """Use quick reply (replace variables and increment usage count)"""
    quick_reply_store = get_quick_reply_store()
    if not quick_reply_store or not _variable_replacer:
        raise HTTPException(status_code=503, detail="Quick reply system not initialized")

    reply = quick_reply_store.get(reply_id)
    if not reply:
        raise HTTPException(
            status_code=404,
            detail="QUICK_REPLY_NOT_FOUND: Quick reply not found"
        )

    context = build_variable_context(
        session_data=request.get("session_data"),
        agent_data=request.get("agent_data"),
        shopify_data=request.get("shopify_data")
    )

    replaced_content = _variable_replacer.replace(
        template=reply.content,
        context=context
    )

    quick_reply_store.increment_usage(reply_id)
    print(f"Used quick reply: {reply_id} by {agent.get('username')}")

    return {
        "success": True,
        "data": {
            "id": reply.id,
            "title": reply.title,
            "original_content": reply.content,
            "replaced_content": replaced_content,
            "variables": reply.variables
        }
    }
