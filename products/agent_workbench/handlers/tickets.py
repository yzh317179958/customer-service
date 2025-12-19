# -*- coding: utf-8 -*-
"""
Agent Workbench - Tickets Handler

Endpoints:
- POST /tickets - Create ticket
- POST /tickets/manual - Create manual ticket
- GET /tickets - List tickets
- GET /tickets/search - Search tickets
- POST /tickets/filter - Advanced filter
- POST /tickets/assign/recommend - Smart assignment
- POST /tickets/export - Export tickets
- GET /tickets/sla-dashboard - SLA dashboard
- GET /tickets/{ticket_id} - Get ticket detail
- PATCH /tickets/{ticket_id} - Update ticket
- POST /tickets/{ticket_id}/assign - Assign ticket
- POST /tickets/batch/assign - Batch assign
- POST /tickets/batch/close - Batch close
- POST /tickets/batch/priority - Batch priority
- POST /tickets/{ticket_id}/comments - Add comment
- GET /tickets/{ticket_id}/comments - List comments
- GET /tickets/{ticket_id}/attachments - List attachments
- POST /tickets/{ticket_id}/attachments - Upload attachment
- GET /tickets/{ticket_id}/attachments/{attachment_id} - Download
- GET /tickets/{ticket_id}/audit-logs - Audit logs
- DELETE /tickets/{ticket_id}/comments/{comment_id} - Delete comment
- POST /tickets/{ticket_id}/reopen - Reopen ticket
- POST /tickets/{ticket_id}/archive - Archive ticket
- POST /tickets/archive/auto - Auto archive
- GET /tickets/archived - List archived
- GET /tickets/sla-summary - SLA summary
- GET /tickets/sla-alerts - SLA alerts
- GET /tickets/{ticket_id}/sla - Ticket SLA info
"""
import csv
import io
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field, field_validator

from services.ticket.models import (
    Ticket, TicketStatus, TicketPriority, TicketType,
    TicketCustomerInfo, TicketCommentType
)
from services.ticket.store import TicketStore
from src.sla_timer import SLATimer, calculate_ticket_sla, SLAStatus
from src.session_state import SessionState, SessionStatus, MessageRole

from products.agent_workbench.dependencies import (
    get_ticket_store, get_audit_log_store, get_session_store,
    get_sse_queues, require_agent, require_admin
)


router = APIRouter(prefix="/tickets", tags=["Tickets"])


# ============================================================================
# Constants
# ============================================================================

MAX_TICKET_EXPORT_ROWS = 10000
ATTACHMENTS_DIR = Path(os.getenv("ATTACHMENTS_DIR", "attachments")).resolve()
ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)

ATTACHMENT_RULES = [
    {
        "name": "image",
        "max_size": 10 * 1024 * 1024,
        "content_types": {"image/jpeg", "image/png", "image/webp", "image/gif"},
        "extensions": {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    },
    {
        "name": "document",
        "max_size": 20 * 1024 * 1024,
        "content_types": {
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/plain"
        },
        "extensions": {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt"}
    },
    {
        "name": "video",
        "max_size": 50 * 1024 * 1024,
        "content_types": {"video/mp4"},
        "extensions": {".mp4"}
    }
]


# ============================================================================
# Request Models
# ============================================================================

class CreateTicketRequest(BaseModel):
    """Create ticket request"""
    session_name: Optional[str] = None
    title: str = Field(..., max_length=200)
    description: str = Field(..., max_length=5000)
    ticket_type: TicketType = TicketType.AFTER_SALE
    priority: TicketPriority = TicketPriority.MEDIUM
    customer: Optional[TicketCustomerInfo] = None
    assigned_agent_id: Optional[str] = None
    assigned_agent_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ManualTicketRequest(BaseModel):
    """Manual ticket request"""
    title: str = Field(..., max_length=200)
    description: str = Field(..., max_length=5000)
    ticket_type: TicketType = TicketType.AFTER_SALE
    priority: TicketPriority = TicketPriority.MEDIUM
    customer: TicketCustomerInfo
    assigned_agent_id: Optional[str] = None
    assigned_agent_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class UpdateTicketRequest(BaseModel):
    """Update ticket request"""
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assigned_agent_id: Optional[str] = None
    assigned_agent_name: Optional[str] = None
    note: Optional[str] = Field(default=None, max_length=500)
    metadata_updates: Optional[Dict[str, Any]] = None
    change_reason: Optional[str] = Field(default=None, max_length=200)


class SessionTicketRequest(BaseModel):
    """Session ticket request"""
    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=5000)
    ticket_type: TicketType = TicketType.AFTER_SALE
    priority: TicketPriority = TicketPriority.MEDIUM


class AssignTicketRequest(BaseModel):
    agent_id: str = Field(..., max_length=100)
    agent_name: Optional[str] = Field(default=None, max_length=100)
    note: Optional[str] = Field(default=None, max_length=500)


class TicketCommentRequest(BaseModel):
    content: str = Field(..., max_length=2000)
    comment_type: TicketCommentType = TicketCommentType.INTERNAL
    notify_agent_id: Optional[str] = Field(default=None, max_length=100)
    mentions: Optional[List[str]] = Field(default=None)


class ReopenTicketRequest(BaseModel):
    reason: str = Field(..., max_length=200)
    comment: Optional[str] = Field(default=None, max_length=500)


class ArchiveTicketRequest(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=200)


class AutoArchiveRequest(BaseModel):
    older_than_days: Optional[int] = Field(default=30, ge=1, le=365)


class TicketFilters(BaseModel):
    """Advanced ticket filters"""
    statuses: Optional[List[TicketStatus]] = None
    priorities: Optional[List[TicketPriority]] = None
    ticket_types: Optional[List[TicketType]] = None
    assigned: Optional[str] = None
    assigned_agent_ids: Optional[List[str]] = None
    keyword: Optional[str] = Field(default=None, max_length=200)
    tags: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    created_start: Optional[float] = Field(default=None, ge=0)
    created_end: Optional[float] = Field(default=None, ge=0)
    updated_start: Optional[float] = Field(default=None, ge=0)
    updated_end: Optional[float] = Field(default=None, ge=0)
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    sort_by: Optional[str] = Field(default="updated_at")
    sort_desc: bool = Field(default=True)


class TicketExportRequest(BaseModel):
    format: Literal['csv', 'xlsx', 'pdf'] = 'csv'
    filters: Optional[TicketFilters] = None


class SmartAssignRequest(BaseModel):
    """Smart assignment request"""
    ticket_type: TicketType = TicketType.AFTER_SALE
    priority: TicketPriority = TicketPriority.MEDIUM
    customer_email: Optional[str] = None
    customer_country: Optional[str] = None
    category: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class BatchAssignRequest(BaseModel):
    """Batch assign request"""
    ticket_ids: List[str]
    target_agent_id: str = Field(..., max_length=100)
    target_agent_name: Optional[str] = Field(default=None, max_length=100)
    note: Optional[str] = Field(default=None, max_length=200)

    @field_validator("ticket_ids")
    @classmethod
    def validate_ticket_ids(cls, value: List[str]) -> List[str]:
        cleaned = [tid.strip() for tid in value if tid and tid.strip()]
        unique = list(dict.fromkeys(cleaned))
        if not unique:
            raise ValueError("ticket_ids cannot be empty")
        if len(unique) > 50:
            raise ValueError("Max 50 tickets per batch")
        return unique


class BatchCloseRequest(BaseModel):
    ticket_ids: List[str]
    close_reason: Optional[str] = Field(default=None, max_length=200)
    comment: Optional[str] = Field(default=None, max_length=500)

    @field_validator("ticket_ids")
    @classmethod
    def validate_ticket_ids(cls, value: List[str]) -> List[str]:
        cleaned = [tid.strip() for tid in value if tid and tid.strip()]
        unique = list(dict.fromkeys(cleaned))
        if not unique:
            raise ValueError("ticket_ids cannot be empty")
        if len(unique) > 50:
            raise ValueError("Max 50 tickets per batch")
        return unique


class BatchPriorityRequest(BaseModel):
    ticket_ids: List[str]
    priority: TicketPriority
    reason: Optional[str] = Field(default=None, max_length=200)

    @field_validator("ticket_ids")
    @classmethod
    def validate_ticket_ids(cls, value: List[str]) -> List[str]:
        cleaned = [tid.strip() for tid in value if tid and tid.strip()]
        unique = list(dict.fromkeys(cleaned))
        if not unique:
            raise ValueError("ticket_ids cannot be empty")
        if len(unique) > 50:
            raise ValueError("Max 50 tickets per batch")
        return unique


# ============================================================================
# Helper Functions
# ============================================================================

def _format_timestamp(ts: Optional[float]) -> str:
    if not ts:
        return ""
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""


def _tickets_to_csv_bytes(tickets: List[Ticket]) -> bytes:
    headers = [
        "ticket_id", "title", "status", "priority", "ticket_type",
        "customer_name", "customer_email", "customer_phone",
        "assigned_agent_name", "assigned_agent_id", "session_name",
        "created_at", "updated_at", "first_response_at", "resolved_at",
        "closed_at", "reopened_count", "description", "tags", "metadata"
    ]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for ticket in tickets:
        data = ticket.to_dict()
        customer = data.get("customer") or {}
        metadata = data.get("metadata") or {}
        tags = metadata.get("tags")
        if isinstance(tags, list):
            tags_value = ", ".join(str(tag) for tag in tags)
        elif isinstance(tags, str):
            tags_value = tags
        else:
            tags_value = ""
        writer.writerow([
            ticket.ticket_id,
            ticket.title,
            ticket.status.value if isinstance(ticket.status, TicketStatus) else ticket.status,
            ticket.priority.value if isinstance(ticket.priority, TicketPriority) else ticket.priority,
            ticket.ticket_type.value if isinstance(ticket.ticket_type, TicketType) else ticket.ticket_type,
            customer.get("name") or "",
            customer.get("email") or "",
            customer.get("phone") or "",
            ticket.assigned_agent_name or "",
            ticket.assigned_agent_id or "",
            ticket.session_name or "",
            _format_timestamp(ticket.created_at),
            _format_timestamp(ticket.updated_at),
            _format_timestamp(ticket.first_response_at),
            _format_timestamp(ticket.resolved_at),
            _format_timestamp(ticket.closed_at),
            ticket.reopened_count,
            ticket.description,
            tags_value,
            json.dumps(metadata, ensure_ascii=False)
        ])
    return output.getvalue().encode("utf-8-sig")


def _resolve_attachment_rule(filename: str, content_type: Optional[str]):
    extension = Path(filename or "").suffix.lower()
    for rule in ATTACHMENT_RULES:
        if (content_type and content_type in rule["content_types"]) or (extension and extension in rule["extensions"]):
            return rule
    return None


async def _save_attachment_file(upload: UploadFile, dest: Path, max_size: int) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    size = 0
    try:
        with dest.open("wb") as buffer:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_size:
                    raise ValueError("FILE_TOO_LARGE")
                buffer.write(chunk)
    except Exception:
        if dest.exists():
            dest.unlink()
        raise
    finally:
        await upload.seek(0)
    return size


def _is_path_within(base: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def _attachment_response(ticket_id: str, attachment):
    data = attachment.dict()
    data["download_url"] = f"/api/tickets/{ticket_id}/attachments/{attachment.attachment_id}"
    return data


def log_ticket_event(
    event_type: str,
    ticket_id: str,
    operator: Optional[Dict[str, Any]],
    details: Optional[Dict[str, Any]] = None
):
    """Log ticket event to audit log store"""
    try:
        audit_log_store = get_audit_log_store()
    except RuntimeError:
        return

    if not audit_log_store:
        return

    operator_id = "system"
    operator_name = "system"
    if operator:
        operator_id = operator.get("agent_id") or operator.get("username") or "system"
        operator_name = operator.get("username") or operator_id

    try:
        audit_log_store.add_log(
            ticket_id=ticket_id,
            event_type=event_type,
            operator_id=operator_id,
            operator_name=operator_name,
            details=details or {}
        )
    except Exception as exc:
        print(f"Warning: Failed to log ticket event: {exc}")


async def enqueue_sse_message(target: str, payload: dict):
    """Enqueue SSE message to target"""
    sse_queues = get_sse_queues()
    if target not in sse_queues:
        return
    try:
        await sse_queues[target].put(payload)
    except Exception as e:
        print(f"Warning: Failed to enqueue SSE message: {e}")


def _parse_date(date_str: Optional[str]) -> Optional[float]:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str).timestamp()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format: {date_str}. Use ISO format YYYY-MM-DD"
        )


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("")
async def create_ticket_endpoint(
    request: CreateTicketRequest,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Create new ticket"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    try:
        created_by = agent.get("agent_id") or agent.get("username") or "system"
        ticket = ticket_store.create_from_payload(
            title=request.title.strip(),
            description=request.description.strip(),
            created_by=created_by,
            created_by_name=agent.get("username"),
            session_name=request.session_name,
            ticket_type=request.ticket_type,
            priority=request.priority,
            customer=request.customer.dict() if request.customer else None,
            assigned_agent_id=request.assigned_agent_id,
            assigned_agent_name=request.assigned_agent_name,
            metadata=request.metadata
        )

        log_ticket_event(
            "created",
            ticket.ticket_id,
            agent,
            {
                "title": ticket.title,
                "ticket_type": ticket.ticket_type,
                "priority": ticket.priority,
                "assigned_agent_id": ticket.assigned_agent_id,
                "assigned_agent_name": ticket.assigned_agent_name
            }
        )

        return {"success": True, "data": ticket.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error: Create ticket failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Create ticket failed")


@router.post("/manual")
async def create_manual_ticket_endpoint(
    request: ManualTicketRequest,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Create manual ticket without session"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    try:
        created_by = agent.get("agent_id") or agent.get("username") or "system"
        ticket = ticket_store.create_from_payload(
            title=request.title.strip(),
            description=request.description.strip(),
            created_by=created_by,
            created_by_name=agent.get("username"),
            session_name=None,
            ticket_type=request.ticket_type,
            priority=request.priority,
            customer=request.customer.dict(),
            assigned_agent_id=request.assigned_agent_id,
            assigned_agent_name=request.assigned_agent_name,
            metadata=request.metadata
        )

        log_ticket_event(
            "created",
            ticket.ticket_id,
            agent,
            {
                "title": ticket.title,
                "ticket_type": ticket.ticket_type,
                "priority": ticket.priority,
                "assigned_agent_id": ticket.assigned_agent_id,
                "assigned_agent_name": ticket.assigned_agent_name
            }
        )

        return {"success": True, "data": ticket.to_dict()}
    except Exception as e:
        print(f"Error: Create manual ticket failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Create ticket failed")


@router.get("")
async def list_tickets_endpoint(
    status: Optional[TicketStatus] = None,
    priority: Optional[TicketPriority] = None,
    assigned_agent_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """List tickets"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    try:
        total, tickets = ticket_store.list(
            status=status,
            priority=priority,
            assigned_agent_id=assigned_agent_id,
            limit=limit,
            offset=offset
        )
        return {
            "success": True,
            "data": {
                "tickets": [ticket.to_dict() for ticket in tickets],
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + len(tickets)) < total
            }
        }
    except Exception as e:
        print(f"Error: List tickets failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Query failed")


@router.get("/search")
async def search_tickets_endpoint(
    query: str,
    limit: int = 50,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Search tickets by keyword"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    keyword = (query or "").strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="Missing query keyword")

    limit = max(1, min(limit, 200))

    try:
        total, tickets = ticket_store.search(keyword, limit=limit)
        return {
            "success": True,
            "data": {
                "tickets": [ticket.to_dict() for ticket in tickets],
                "total": total,
                "limit": limit,
                "has_more": total > len(tickets)
            }
        }
    except Exception as e:
        print(f"Error: Search tickets failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.post("/filter")
async def filter_tickets_endpoint(
    filters: TicketFilters,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Advanced ticket filter"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    allowed_sort_fields = {
        "updated_at", "created_at", "priority", "status",
        "resolved_at", "first_response_at", "reopened_at"
    }
    sort_by = filters.sort_by or "updated_at"
    if sort_by not in allowed_sort_fields:
        raise HTTPException(status_code=400, detail=f"INVALID_SORT_FIELD: {sort_by}")

    try:
        total, tickets = ticket_store.filter_tickets(
            statuses=filters.statuses,
            priorities=filters.priorities,
            ticket_types=filters.ticket_types,
            assigned=filters.assigned,
            assigned_agent_ids=filters.assigned_agent_ids,
            keyword=filters.keyword,
            tags=filters.tags,
            categories=filters.categories,
            created_start=filters.created_start,
            created_end=filters.created_end,
            updated_start=filters.updated_start,
            updated_end=filters.updated_end,
            limit=filters.limit,
            offset=filters.offset,
            sort_by=sort_by,
            sort_desc=filters.sort_desc,
            current_agent_id=agent.get("agent_id") or agent.get("username")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "success": True,
        "data": {
            "tickets": [ticket.to_dict() for ticket in tickets],
            "total": total,
            "limit": filters.limit,
            "offset": filters.offset,
            "has_more": (filters.offset + len(tickets)) < total
        }
    }


@router.post("/assign/recommend")
async def recommend_ticket_assignment(
    request: SmartAssignRequest,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Get smart assignment recommendation"""
    # Note: smart_assignment_engine needs to be injected from dependencies
    # For now, return not available
    raise HTTPException(status_code=503, detail="Smart assignment not enabled")


@router.post("/export")
async def export_tickets_endpoint(
    request: TicketExportRequest,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Export tickets to CSV"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    export_format = request.format.lower()
    if export_format != 'csv':
        raise HTTPException(status_code=400, detail="Export format not supported yet")

    filters_payload = request.filters or TicketFilters()
    provided_fields = request.filters.model_fields_set if request.filters else set()

    allowed_sort_fields = {
        "updated_at", "created_at", "priority", "status",
        "resolved_at", "first_response_at", "reopened_at"
    }
    sort_by = filters_payload.sort_by or "updated_at"
    if sort_by not in allowed_sort_fields:
        raise HTTPException(status_code=400, detail=f"INVALID_SORT_FIELD: {sort_by}")

    limit = filters_payload.limit if "limit" in provided_fields else MAX_TICKET_EXPORT_ROWS
    limit = min(limit or MAX_TICKET_EXPORT_ROWS, MAX_TICKET_EXPORT_ROWS)
    offset = filters_payload.offset if "offset" in provided_fields else 0

    try:
        total, tickets = ticket_store.filter_tickets(
            statuses=filters_payload.statuses,
            priorities=filters_payload.priorities,
            ticket_types=filters_payload.ticket_types,
            assigned=filters_payload.assigned,
            assigned_agent_ids=filters_payload.assigned_agent_ids,
            keyword=filters_payload.keyword,
            tags=filters_payload.tags,
            categories=filters_payload.categories,
            created_start=filters_payload.created_start,
            created_end=filters_payload.created_end,
            updated_start=filters_payload.updated_start,
            updated_end=filters_payload.updated_end,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_desc=filters_payload.sort_desc,
            current_agent_id=agent.get("agent_id") or agent.get("username")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if "limit" not in provided_fields and total > MAX_TICKET_EXPORT_ROWS:
        raise HTTPException(
            status_code=400,
            detail=f"TOO_MANY_RECORDS: Max {MAX_TICKET_EXPORT_ROWS} records, narrow your filter"
        )

    csv_bytes = _tickets_to_csv_bytes(tickets)
    filename = f"tickets_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/sla-dashboard")
async def get_sla_dashboard(agent: Dict[str, Any] = Depends(require_agent)):
    """Get SLA dashboard data"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    _, tickets = ticket_store.filter_tickets(
        statuses=[
            TicketStatus.PENDING,
            TicketStatus.IN_PROGRESS,
            TicketStatus.WAITING_CUSTOMER,
            TicketStatus.WAITING_VENDOR,
        ],
        limit=200
    )

    frt_stats = {"normal": 0, "warning": 0, "urgent": 0, "violated": 0, "completed": 0}
    rt_stats = {"normal": 0, "warning": 0, "urgent": 0, "violated": 0, "completed": 0}
    alerts = []
    now = time.time()

    for ticket in tickets:
        timer = SLATimer(ticket)
        sla_info = timer.get_sla_info(now)

        frt_status = sla_info.frt_status.value
        if frt_status in frt_stats:
            frt_stats[frt_status] += 1

        rt_status = sla_info.rt_status.value
        if rt_status in rt_stats:
            rt_stats[rt_status] += 1

        should_alert = timer.should_alert(now)
        if should_alert["frt_alert"] or should_alert["rt_alert"]:
            alerts.append({
                "ticket_id": ticket.ticket_id,
                "title": ticket.title,
                "priority": ticket.priority.value,
                "status": ticket.status.value,
                "frt_alert": should_alert["frt_alert"],
                "frt_remaining_minutes": round(sla_info.frt_remaining_seconds / 60, 1),
                "frt_status": sla_info.frt_status.value,
                "rt_alert": should_alert["rt_alert"],
                "rt_remaining_hours": round(sla_info.rt_remaining_seconds / 3600, 2),
                "rt_status": sla_info.rt_status.value,
                "assigned_agent_name": ticket.assigned_agent_name,
            })

    priority_order = {"violated": 0, "urgent": 1, "warning": 2, "normal": 3, "completed": 4}
    alerts.sort(key=lambda x: (
        priority_order.get(x.get("rt_status", "normal"), 3),
        priority_order.get(x.get("frt_status", "normal"), 3),
        x.get("rt_remaining_hours", 999)
    ))

    summary = ticket_store.get_sla_summary()

    return {
        "success": True,
        "data": {
            "total_open_tickets": len(tickets),
            "frt_stats": frt_stats,
            "rt_stats": rt_stats,
            "alerts": alerts[:50],
            "alerts_count": len(alerts),
            "summary": summary
        }
    }


@router.get("/{ticket_id}")
async def get_ticket_detail(
    ticket_id: str,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Get ticket detail"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    ticket = ticket_store.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return {"success": True, "data": ticket.to_dict()}


@router.patch("/{ticket_id}")
async def update_ticket_endpoint(
    ticket_id: str,
    request: UpdateTicketRequest,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Update ticket"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    original_ticket = ticket_store.get(ticket_id)
    try:
        ticket = ticket_store.update_ticket(
            ticket_id,
            status=request.status,
            priority=request.priority,
            assigned_agent_id=request.assigned_agent_id,
            assigned_agent_name=request.assigned_agent_name,
            note=request.note,
            metadata_updates=request.metadata_updates,
            changed_by=agent.get("agent_id") or agent.get("username") or "system",
            change_reason=request.change_reason
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if original_ticket and request.status and ticket.status != original_ticket.status:
        log_ticket_event(
            "status_changed",
            ticket.ticket_id,
            agent,
            {
                "from_status": original_ticket.status,
                "to_status": ticket.status,
                "change_reason": request.change_reason
            }
        )
    if original_ticket and request.priority and ticket.priority != original_ticket.priority:
        log_ticket_event(
            "priority_changed",
            ticket.ticket_id,
            agent,
            {
                "from_priority": original_ticket.priority,
                "to_priority": ticket.priority,
                "change_reason": request.change_reason
            }
        )
    if original_ticket and (request.assigned_agent_id or request.assigned_agent_name):
        if ticket.assigned_agent_id != original_ticket.assigned_agent_id or ticket.assigned_agent_name != original_ticket.assigned_agent_name:
            log_ticket_event(
                "assigned",
                ticket.ticket_id,
                agent,
                {
                    "assigned_agent_id": ticket.assigned_agent_id,
                    "assigned_agent_name": ticket.assigned_agent_name,
                    "note": request.note
                }
            )

    return {"success": True, "data": ticket.to_dict()}


@router.post("/{ticket_id}/assign")
async def assign_ticket_endpoint(
    ticket_id: str,
    request: AssignTicketRequest,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Assign ticket"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    try:
        ticket = ticket_store.update_ticket(
            ticket_id,
            assigned_agent_id=request.agent_id,
            assigned_agent_name=request.agent_name,
            note=request.note,
            changed_by=agent.get("agent_id") or agent.get("username") or "system",
            change_reason="assign"
        )
    except ValueError as e:
        msg = str(e)
        if "ARCHIVED" in msg:
            raise HTTPException(status_code=400, detail=msg)
        raise HTTPException(status_code=400, detail=msg)

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return {"success": True, "data": ticket.to_dict()}


@router.post("/batch/assign")
async def batch_assign_tickets_endpoint(
    request: BatchAssignRequest,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Batch assign tickets"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    operator_id = agent.get("agent_id") or agent.get("username") or "system"

    try:
        result = ticket_store.batch_assign(
            request.ticket_ids,
            assigned_agent_id=request.target_agent_id.strip(),
            assigned_agent_name=request.target_agent_name.strip() if request.target_agent_name else None,
            changed_by=operator_id,
            note=request.note
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    updated_dicts = [ticket.to_dict() for ticket in result["tickets"]]
    for ticket in result["tickets"]:
        log_ticket_event(
            "assigned",
            ticket.ticket_id,
            agent,
            {
                "assigned_agent_id": ticket.assigned_agent_id,
                "assigned_agent_name": ticket.assigned_agent_name,
                "note": request.note,
                "batch": True
            }
        )

    return {
        "success": True,
        "data": {
            "succeeded": len(result["tickets"]),
            "failed": result["failed"],
            "tickets": updated_dicts
        }
    }


@router.post("/batch/close")
async def batch_close_tickets_endpoint(
    request: BatchCloseRequest,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Batch close tickets (resolved only)"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    operator = agent.get("agent_id") or agent.get("username") or "system"

    try:
        result = ticket_store.batch_close(
            request.ticket_ids,
            reason=request.close_reason,
            comment=request.comment,
            changed_by=operator
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    closed_tickets = [ticket.to_dict() for ticket in result["tickets"]]
    for ticket in result["tickets"]:
        log_ticket_event(
            "status_changed",
            ticket.ticket_id,
            agent,
            {
                "from_status": "resolved",
                "to_status": "closed",
                "reason": request.close_reason,
                "comment": request.comment,
                "batch": True
            }
        )

    return {
        "success": True,
        "data": {
            "succeeded": len(result["tickets"]),
            "failed": result["failed"],
            "tickets": closed_tickets
        }
    }


@router.post("/batch/priority")
async def batch_update_priority_endpoint(
    request: BatchPriorityRequest,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Batch update priority"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    operator = agent.get("agent_id") or agent.get("username") or "system"

    try:
        result = ticket_store.batch_update_priority(
            request.ticket_ids,
            priority=request.priority,
            reason=request.reason,
            changed_by=operator
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    updated_tickets = [ticket.to_dict() for ticket in result["tickets"]]
    for ticket in result["tickets"]:
        log_ticket_event(
            "priority_changed",
            ticket.ticket_id,
            agent,
            {
                "to_priority": ticket.priority,
                "reason": request.reason,
                "batch": True
            }
        )

    return {
        "success": True,
        "data": {
            "succeeded": len(result["tickets"]),
            "failed": result["failed"],
            "tickets": updated_tickets
        }
    }


@router.post("/{ticket_id}/comments")
async def add_ticket_comment(
    ticket_id: str,
    request: TicketCommentRequest,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Add ticket comment"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    try:
        comment = ticket_store.add_comment(
            ticket_id,
            content=request.content.strip(),
            author_id=agent.get("agent_id") or agent.get("username") or "system",
            author_name=agent.get("username"),
            comment_type=request.comment_type,
            mentions=request.mentions or []
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not comment:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if request.mentions:
        sender_name = agent.get("username") or agent.get("name") or "system"
        preview = comment.content[:120]
        for username in set(request.mentions):
            if not username:
                continue
            await enqueue_sse_message(username, {
                "type": "mention",
                "source": "ticket_comment",
                "ticket_id": ticket_id,
                "comment_id": comment.comment_id,
                "from_agent": sender_name,
                "content": preview,
                "created_at": comment.created_at
            })

    log_ticket_event(
        "commented",
        ticket_id,
        agent,
        {
            "comment_id": comment.comment_id,
            "comment_type": comment.comment_type,
            "mentions": request.mentions or []
        }
    )

    return {"success": True, "data": comment.dict()}


@router.get("/{ticket_id}/comments")
async def list_ticket_comments(
    ticket_id: str,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """List ticket comments"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    comments = ticket_store.list_comments(ticket_id)
    if comments is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return {"success": True, "data": [comment.dict() for comment in comments]}


@router.get("/{ticket_id}/attachments")
async def list_ticket_attachments(
    ticket_id: str,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """List ticket attachments"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    attachments = ticket_store.list_attachments(ticket_id)
    if attachments is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return {
        "success": True,
        "data": [_attachment_response(ticket_id, attachment) for attachment in attachments]
    }


@router.post("/{ticket_id}/attachments")
async def upload_ticket_attachment(
    ticket_id: str,
    comment_type: str = Form("internal"),
    file: UploadFile = File(...),
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Upload ticket attachment"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="MISSING_FILE: No file selected")

    try:
        comment_type_enum = TicketCommentType(comment_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="INVALID_COMMENT_TYPE")

    rule = _resolve_attachment_rule(file.filename, file.content_type)
    if not rule:
        raise HTTPException(status_code=400, detail="UNSUPPORTED_FILE_TYPE")

    stored_filename = f"{uuid.uuid4().hex}_{Path(file.filename).name}"
    stored_path = ATTACHMENTS_DIR / ticket_id / stored_filename

    try:
        saved_size = await _save_attachment_file(file, stored_path, rule["max_size"])
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"FILE_TOO_LARGE: File exceeds limit ({rule['max_size'] // (1024 * 1024)}MB)"
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"UPLOAD_FAILED: {str(exc)}")

    try:
        attachment = ticket_store.add_attachment(
            ticket_id,
            filename=file.filename,
            stored_path=str(stored_path),
            size=saved_size,
            content_type=file.content_type,
            comment_type=comment_type_enum,
            uploader_id=agent.get("agent_id") or agent.get("username") or "system",
            uploader_name=agent.get("username")
        )
        if not attachment:
            raise HTTPException(status_code=404, detail="Ticket not found")
    except Exception as exc:
        if stored_path.exists():
            stored_path.unlink()
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Save attachment failed: {str(exc)}")

    response_data = _attachment_response(ticket_id, attachment)
    log_ticket_event(
        "attachment_uploaded",
        ticket_id,
        agent,
        {
            "attachment_id": attachment.attachment_id,
            "filename": attachment.filename,
            "comment_type": attachment.comment_type,
            "size": attachment.size
        }
    )

    return {"success": True, "data": response_data}


@router.get("/{ticket_id}/attachments/{attachment_id}")
async def download_ticket_attachment(
    ticket_id: str,
    attachment_id: str,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Download ticket attachment"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    attachment = ticket_store.get_attachment(ticket_id, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    file_path = Path(attachment.stored_path)
    if not _is_path_within(ATTACHMENTS_DIR, file_path) or not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found or deleted")

    return FileResponse(
        file_path,
        media_type=attachment.content_type or "application/octet-stream",
        filename=attachment.filename
    )


@router.get("/{ticket_id}/audit-logs")
async def list_ticket_audit_logs(
    ticket_id: str,
    limit: int = 100,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """List ticket audit logs"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    try:
        audit_log_store = get_audit_log_store()
    except RuntimeError:
        return {"success": True, "data": []}

    if not audit_log_store:
        return {"success": True, "data": []}

    logs = audit_log_store.list_logs(ticket_id, limit=limit)
    return {"success": True, "data": [log.dict() for log in logs]}


@router.delete("/{ticket_id}/comments/{comment_id}")
async def delete_ticket_comment(
    ticket_id: str,
    comment_id: str,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Delete ticket comment"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    ticket = ticket_store.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if ticket.status == TicketStatus.ARCHIVED:
        raise HTTPException(status_code=400, detail="ARCHIVED_TICKET: Cannot delete comment on archived ticket")

    success = ticket_store.delete_comment(ticket_id, comment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Comment not found")

    return {"success": True}


@router.post("/{ticket_id}/reopen")
async def reopen_ticket_endpoint(
    ticket_id: str,
    request: ReopenTicketRequest,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Reopen closed ticket"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    try:
        ticket = ticket_store.reopen_ticket(
            ticket_id,
            agent_id=agent.get("agent_id") or agent.get("username") or "system",
            reason=request.reason,
            comment=request.comment
        )
        log_ticket_event(
            "status_changed",
            ticket.ticket_id,
            agent,
            {
                "from_status": TicketStatus.CLOSED,
                "to_status": ticket.status,
                "reason": request.reason,
                "comment": request.comment
            }
        )
        return {"success": True, "data": ticket.to_dict()}
    except ValueError as e:
        msg = str(e)
        if "NOT_FOUND" in msg:
            raise HTTPException(status_code=404, detail="Ticket not found")
        raise HTTPException(status_code=400, detail=msg)


@router.post("/{ticket_id}/archive")
async def archive_ticket_endpoint(
    ticket_id: str,
    request: ArchiveTicketRequest = ArchiveTicketRequest(),
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Archive closed ticket"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    try:
        ticket = ticket_store.archive_ticket(
            ticket_id,
            agent_id=agent.get("agent_id") or agent.get("username") or "system",
            reason=request.reason
        )
        log_ticket_event(
            "status_changed",
            ticket.ticket_id,
            agent,
            {
                "from_status": TicketStatus.CLOSED,
                "to_status": TicketStatus.ARCHIVED,
                "reason": request.reason or "archive"
            }
        )
        return {"success": True, "data": ticket.to_dict()}
    except ValueError as e:
        msg = str(e)
        if "NOT_FOUND" in msg:
            raise HTTPException(status_code=404, detail="Ticket not found")
        raise HTTPException(status_code=400, detail=msg)


@router.post("/archive/auto")
async def auto_archive_tickets(
    request: AutoArchiveRequest = AutoArchiveRequest(),
    admin: Dict[str, Any] = Depends(require_admin)
):
    """Trigger auto archive task"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    older_days = request.older_than_days or 30
    seconds = older_days * 86400
    result = ticket_store.auto_archive_closed(
        older_than_seconds=seconds,
        agent_id=admin.get("agent_id") or admin.get("username") or "system"
    )

    for ticket_id in result.get("ticket_ids", []):
        log_ticket_event(
            "status_changed",
            ticket_id,
            admin,
            {
                "from_status": TicketStatus.CLOSED,
                "to_status": TicketStatus.ARCHIVED,
                "reason": f"auto_archive_{older_days}d"
            }
        )

    return {
        "success": True,
        "data": {
            "archived_count": result["archived_count"],
            "ticket_ids": result["ticket_ids"],
            "older_than_days": older_days
        }
    }


@router.get("/archived")
async def get_archived_tickets(
    customer_email: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """List archived tickets"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    start_ts = _parse_date(start_date)
    end_ts = _parse_date(end_date)

    total, tickets = ticket_store.list_archived(
        email=customer_email,
        start_ts=start_ts,
        end_ts=end_ts,
        limit=limit,
        offset=offset
    )

    return {
        "success": True,
        "data": {
            "tickets": [ticket.to_dict() for ticket in tickets],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + len(tickets)) < total
        }
    }


@router.get("/sla-summary")
async def get_ticket_sla_summary(agent: Dict[str, Any] = Depends(require_agent)):
    """Get ticket SLA summary"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    summary = ticket_store.get_sla_summary()
    return {"success": True, "data": summary}


@router.get("/sla-alerts")
async def get_ticket_sla_alerts(agent: Dict[str, Any] = Depends(require_agent)):
    """Get SLA alerts"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    alerts = ticket_store.detect_sla_alerts()
    return {"success": True, "data": alerts}


@router.get("/{ticket_id}/sla")
async def get_ticket_sla_info(
    ticket_id: str,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Get ticket SLA info"""
    ticket_store = get_ticket_store()
    if not ticket_store:
        raise HTTPException(status_code=503, detail="Ticket system not initialized")

    ticket = ticket_store.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="TICKET_NOT_FOUND")

    sla_info = calculate_ticket_sla(ticket)
    return {
        "success": True,
        "data": {
            "ticket_id": ticket_id,
            "priority": ticket.priority.value,
            "ticket_type": ticket.ticket_type.value,
            "status": ticket.status.value,
            "sla": sla_info
        }
    }
