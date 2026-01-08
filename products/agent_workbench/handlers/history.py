# -*- coding: utf-8 -*-
"""
Agent Workbench - Chat History Handler

Endpoints:
- GET /history/sessions
- GET /history/sessions/{session_name}
- GET /history/sessions/search
- GET /history/sessions/{session_name}/meta
- PUT /history/sessions/{session_name}/meta
- GET /history/search
- GET /history/statistics
- GET /history/export (CSV)
- POST /history/export-jobs
- GET /history/export-jobs
- GET /history/export-jobs/{job_id}
- GET /history/export-jobs/{job_id}/download
- POST /history/translate (Coze; optional)
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from products.agent_workbench.dependencies import require_agent, get_message_store


router = APIRouter(prefix="/history", tags=["Chat History"])


def _require_message_store():
    store = get_message_store()
    if store is None:
        raise HTTPException(status_code=503, detail="MessageStoreService not initialized")
    return store


def _load_repo_dotenv() -> None:
    """
    Best-effort load of repo `.env` regardless of current working directory.

    On servers, the process may run with a different WorkingDirectory. If Coze config
    is stored in a repo `.env`, relying on `os.getcwd()` makes translation return 503.
    """
    try:
        from dotenv import load_dotenv

        here = Path(__file__).resolve()
        for parent in [here, *here.parents]:
            dotenv_path = parent / ".env"
            if dotenv_path.exists():
                load_dotenv(dotenv_path=str(dotenv_path), override=False)
                return
        load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"), override=False)
    except Exception:
        pass


@router.get("/sessions")
async def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    start_time: Optional[float] = Query(None),
    end_time: Optional[float] = Query(None),
    agent: Dict[str, Any] = Depends(require_agent),
):
    store = _require_message_store()
    return await store.get_sessions(page=page, page_size=page_size, start_time=start_time, end_time=end_time)


@router.get("/sessions/search")
async def search_sessions(
    q: str = Query(..., min_length=2, description="Full-text search query (multi-word supported)"),
    start_time: Optional[float] = Query(None),
    end_time: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    agent: Dict[str, Any] = Depends(require_agent),
):
    store = _require_message_store()
    try:
        return await store.search_sessions(q=q, start_time=start_time, end_time=end_time, page=page, page_size=page_size)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions/{session_name}")
async def get_session_detail(
    session_name: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    order: str = Query("asc", description="Sort order: asc/desc"),
    agent: Dict[str, Any] = Depends(require_agent),
):
    store = _require_message_store()
    return await store.get_messages_by_session(session_name, limit=limit, offset=offset, order=order)


class SessionMetaUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(default=None, max_length=200)
    note: Optional[str] = Field(default=None, max_length=2000)
    tags: Optional[Any] = Field(default=None, description="JSON value (array/object)")


@router.get("/sessions/{session_name}/meta")
async def get_session_meta(
    session_name: str,
    agent: Dict[str, Any] = Depends(require_agent),
):
    store = _require_message_store()
    try:
        return await store.get_session_meta(session_name)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.put("/sessions/{session_name}/meta")
async def update_session_meta(
    session_name: str,
    req: SessionMetaUpdateRequest,
    agent: Dict[str, Any] = Depends(require_agent),
):
    store = _require_message_store()
    username = agent.get("username") or agent.get("agent_id") or "agent"
    try:
        return await store.upsert_session_meta(
            session_name,
            display_name=req.display_name,
            note=req.note,
            tags=req.tags,
            updated_by=username,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/search")
async def search_messages(
    q: str = Query(..., min_length=2, description="Full-text search query (multi-word supported)"),
    start_time: Optional[float] = Query(None),
    end_time: Optional[float] = Query(None),
    role: Optional[str] = Query(None, description="Filter by role: user/assistant/agent"),
    session_name: Optional[str] = Query(None, description="Filter by session_name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    agent: Dict[str, Any] = Depends(require_agent),
):
    store = _require_message_store()
    try:
        return await store.search_messages(
            q=q,
            start_time=start_time,
            end_time=end_time,
            role=role,
            session_name=session_name,
            page=page,
            page_size=page_size,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/statistics")
async def get_statistics(
    start_time: Optional[float] = Query(None),
    end_time: Optional[float] = Query(None),
    agent: Dict[str, Any] = Depends(require_agent),
):
    store = _require_message_store()
    return await store.get_statistics(start_time=start_time, end_time=end_time)


@router.get("/export")
async def export_messages(
    session_name: str = Query(..., min_length=1),
    start_time: Optional[float] = Query(None),
    end_time: Optional[float] = Query(None),
    agent: Dict[str, Any] = Depends(require_agent),
):
    store = _require_message_store()
    data = await store.export_messages_csv(session_name=session_name, start_time=start_time, end_time=end_time)

    safe_session = session_name.replace("/", "_").replace("\\", "_")
    filename = f"chat_history_{safe_session}.csv"

    return StreamingResponse(
        iter([data]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


class ExportJobCreateRequest(BaseModel):
    start_time: float = Field(..., ge=0, description="Unix seconds")
    end_time: float = Field(..., ge=0, description="Unix seconds")
    q: Optional[str] = Field(default=None, description="Optional keyword query (FTS)")
    role: Optional[str] = Field(default=None, description="user/assistant/agent")
    session_name: Optional[str] = Field(default=None, description="Optional session_name filter")


@router.post("/export-jobs")
async def create_export_job(
    req: ExportJobCreateRequest,
    agent: Dict[str, Any] = Depends(require_agent),
):
    store = _require_message_store()
    username = agent.get("username") or agent.get("agent_id") or "agent"

    try:
        job = await store.create_export_job(
            created_by=username,
            request={
                "start_time": float(req.start_time),
                "end_time": float(req.end_time),
                "q": (req.q or "").strip() or None,
                "role": (req.role or "").strip().lower() or None,
                "session_name": (req.session_name or "").strip() or None,
            },
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # Fire-and-forget execution in-process (production can move to a real worker).
    async def _run():
        try:
            await store.run_export_job(job["job_id"])
        except Exception:
            pass

    asyncio.create_task(_run())
    return job


@router.get("/export-jobs")
async def list_export_jobs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    agent: Dict[str, Any] = Depends(require_agent),
):
    store = _require_message_store()
    username = agent.get("username") or agent.get("agent_id") or "agent"
    try:
        return await store.list_export_jobs(created_by=username, limit=limit, offset=offset)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/export-jobs/{job_id}")
async def get_export_job(
    job_id: str,
    agent: Dict[str, Any] = Depends(require_agent),
):
    store = _require_message_store()
    username = agent.get("username") or agent.get("agent_id") or "agent"
    try:
        job = await store.get_export_job(job_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="job not found")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    if job.get("created_by") and job["created_by"] != username:
        raise HTTPException(status_code=403, detail="forbidden")
    return job


@router.get("/export-jobs/{job_id}/download")
async def download_export_job(
    job_id: str,
    agent: Dict[str, Any] = Depends(require_agent),
):
    store = _require_message_store()
    username = agent.get("username") or agent.get("agent_id") or "agent"
    try:
        job = await store.get_export_job(job_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="job not found")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    if job.get("created_by") and job["created_by"] != username:
        raise HTTPException(status_code=403, detail="forbidden")

    if job.get("status") != "done" or not job.get("file_path"):
        raise HTTPException(status_code=409, detail="job not ready")

    file_path = job["file_path"]
    filename = os.path.basename(file_path) or f"chat_export_{job_id}.csv"

    if not os.path.exists(file_path):
        raise HTTPException(status_code=410, detail="file not found")

    def _iter_file(path: str, chunk_size: int = 1024 * 1024):
        with open(path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    return StreamingResponse(
        _iter_file(file_path),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)


class TranslateResponse(BaseModel):
    translated_text: str


def _get_translate_config() -> dict[str, str]:
    _load_repo_dotenv()

    workflow_id = (os.getenv("COZE_TRANSLATE_WORKFLOW_ID", "") or os.getenv("COZE_WORKFLOW_ID", "")).strip()
    app_id = (os.getenv("COZE_TRANSLATE_APP_ID", "") or os.getenv("COZE_APP_ID", "")).strip()
    api_base = os.getenv("COZE_API_BASE", "https://api.coze.com").strip()
    input_key = os.getenv("COZE_TRANSLATE_INPUT_KEY", "USER_INPUT").strip() or "USER_INPUT"

    if not workflow_id or not app_id:
        raise HTTPException(
            status_code=503,
            detail="Translation not configured (set COZE_TRANSLATE_WORKFLOW_ID/COZE_TRANSLATE_APP_ID or COZE_WORKFLOW_ID/COZE_APP_ID)",
        )

    return {"workflow_id": workflow_id, "app_id": app_id, "api_base": api_base, "input_key": input_key}


async def _coze_translate_to_zh(*, text: str, session_name: str) -> str:
    """
    Translate via Coze workflow chat API.

    This is best-effort and may fail due to missing config or network issues.
    """
    import httpx

    from services.coze.token_manager import OAuthTokenManager

    cfg = _get_translate_config()
    try:
        _load_repo_dotenv()
        token_manager = OAuthTokenManager.from_env()
        access_token = token_manager.get_access_token(session_name=session_name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Translation auth not configured: {e}")

    url = f"{cfg['api_base']}/v1/workflows/chat"

    payload = {
        "workflow_id": cfg["workflow_id"],
        "app_id": cfg["app_id"],
        "session_name": session_name,
        "parameters": {
            cfg["input_key"]: text,
        },
        "additional_messages": [
            {
                "content": text,
                "content_type": "text",
                "role": "user",
                "type": "question",
            }
        ],
    }

    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    timeout = httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=10.0)

    def _extract_text(data: dict) -> Optional[str]:
        content = data.get("content")
        if isinstance(content, str) and content.strip():
            content_str = content.strip()
            # Some workflows return JSON-stringified outputs like {"output":"..."}.
            if content_str.startswith("{") and "\"output\"" in content_str:
                try:
                    parsed = json.loads(content_str)
                    output = parsed.get("output") if isinstance(parsed, dict) else None
                    if isinstance(output, str) and output.strip():
                        return output.strip()
                except Exception:
                    pass
            return content_str
        message = data.get("message")
        if isinstance(message, dict):
            msg_content = message.get("content")
            if isinstance(msg_content, str) and msg_content.strip():
                return msg_content
        output = data.get("output")
        if isinstance(output, str) and output.strip():
            return output
        return None

    best_answer: Optional[str] = None
    event_type: Optional[str] = None

    async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
        async with client.stream("POST", url, json=payload, headers=headers) as response:
            if response.status_code != 200:
                body = await response.aread()
                raise HTTPException(status_code=502, detail=f"Coze translate failed: {body.decode(errors='ignore')}")

            async for line in response.aiter_lines():
                if not line:
                    continue
                line = line.strip()
                if line.startswith("event:"):
                    event_type = line[6:].strip()
                    continue
                if not line.startswith("data:"):
                    continue

                data_str = line[5:].strip()
                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                extracted = _extract_text(data)
                if not extracted:
                    continue

                if data.get("role") == "assistant" and data.get("type") == "answer":
                    best_answer = extracted

    return (best_answer or "").strip()


@router.post("/translate", response_model=TranslateResponse)
async def translate_message(
    req: TranslateRequest,
    agent: Dict[str, Any] = Depends(require_agent),
):
    """
    Translate arbitrary text to Chinese for UI assistance (display only; not persisted).
    """
    username = agent.get("username") or agent.get("agent_id") or "agent"
    session_name = f"workbench_translate_{username}_{int(time.time() * 1000)}"
    translated = await _coze_translate_to_zh(text=req.text, session_name=session_name)
    if not translated:
        raise HTTPException(status_code=502, detail="Coze translate returned empty result")
    return TranslateResponse(translated_text=translated)
