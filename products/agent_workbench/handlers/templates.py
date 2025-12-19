# -*- coding: utf-8 -*-
"""
Agent Workbench - Templates Handler

Endpoints:
- GET /templates - List templates
- POST /templates - Create template
- GET /templates/{template_id} - Get template
- PUT /templates/{template_id} - Update template
- DELETE /templates/{template_id} - Delete template
- POST /templates/{template_id}/render - Render template
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from services.ticket.models import TicketType, TicketPriority
from services.ticket.template import TicketTemplateStore

from products.agent_workbench.dependencies import require_agent


router = APIRouter(prefix="/templates", tags=["Templates"])


# ============================================================================
# Global State
# ============================================================================

_ticket_template_store: Optional[TicketTemplateStore] = None


def set_ticket_template_store(store: TicketTemplateStore) -> None:
    global _ticket_template_store
    _ticket_template_store = store


def get_ticket_template_store() -> Optional[TicketTemplateStore]:
    return _ticket_template_store


# ============================================================================
# Request Models
# ============================================================================

class TicketTemplateRequest(BaseModel):
    name: str = Field(..., max_length=100)
    ticket_type: TicketType = TicketType.AFTER_SALE
    category: str = Field(..., max_length=100)
    priority: TicketPriority = TicketPriority.MEDIUM
    title_template: str = Field(..., max_length=200)
    description_template: str = Field(..., max_length=5000)


class TicketTemplateRenderRequest(BaseModel):
    customer_name: Optional[str] = None


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("")
async def list_ticket_templates(agent: Dict[str, Any] = Depends(require_agent)):
    """List all ticket templates"""
    if not _ticket_template_store:
        raise HTTPException(status_code=503, detail="Template store not initialized")

    templates = _ticket_template_store.list()
    return {
        "success": True,
        "data": [template.dict() for template in templates]
    }


@router.post("")
async def create_ticket_template(
    request: TicketTemplateRequest,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Create new ticket template"""
    if not _ticket_template_store:
        raise HTTPException(status_code=503, detail="Template store not initialized")

    template = _ticket_template_store.create(
        name=request.name.strip(),
        ticket_type=request.ticket_type,
        category=request.category.strip(),
        priority=request.priority,
        title_template=request.title_template.strip(),
        description_template=request.description_template.strip(),
        created_by=agent.get("agent_id") or agent.get("username") or "system"
    )
    return {
        "success": True,
        "data": template.dict()
    }


@router.get("/{template_id}")
async def get_ticket_template(
    template_id: str,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Get ticket template by ID"""
    if not _ticket_template_store:
        raise HTTPException(status_code=503, detail="Template store not initialized")

    template = _ticket_template_store.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "success": True,
        "data": template.dict()
    }


@router.put("/{template_id}")
async def update_ticket_template(
    template_id: str,
    request: TicketTemplateRequest,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Update ticket template"""
    if not _ticket_template_store:
        raise HTTPException(status_code=503, detail="Template store not initialized")

    template = _ticket_template_store.update(
        template_id,
        name=request.name.strip(),
        ticket_type=request.ticket_type,
        category=request.category.strip(),
        priority=request.priority,
        title_template=request.title_template.strip(),
        description_template=request.description_template.strip()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "success": True,
        "data": template.dict()
    }


@router.delete("/{template_id}")
async def delete_ticket_template(
    template_id: str,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Delete ticket template"""
    if not _ticket_template_store:
        raise HTTPException(status_code=503, detail="Template store not initialized")

    deleted = _ticket_template_store.delete(template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Template not found")

    return {"success": True}


@router.post("/{template_id}/render")
async def render_ticket_template(
    template_id: str,
    request: TicketTemplateRenderRequest,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Render ticket template with variables"""
    if not _ticket_template_store:
        raise HTTPException(status_code=503, detail="Template store not initialized")

    template = _ticket_template_store.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    rendered = _ticket_template_store.render_template(
        template,
        {"customer_name": request.customer_name or ""}
    )
    return {
        "success": True,
        "data": rendered
    }
