# -*- coding: utf-8 -*-
"""
Message store service (PostgreSQL).

This service is a shared dependency used by products to persist and query chat messages.

Design goals:
- Best-effort, non-blocking writes via an in-process async queue + background worker(s)
- Sync SQLAlchemy sessions executed in a thread to avoid blocking the event loop
- Strong search via PostgreSQL full-text search (tsvector + GIN index)
"""

from __future__ import annotations

import asyncio
import csv
import io
import os
import pathlib
import time
import uuid
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy import and_
from sqlalchemy.exc import ProgrammingError


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


@dataclass(frozen=True)
class _SaveMessageRequest:
    message_id: str
    session_name: str
    role: str
    content: str
    created_at: float
    conversation_id: Optional[str]
    agent_id: Optional[str]
    agent_name: Optional[str]
    response_time_ms: Optional[int]


class MessageStoreService:
    """
    Chat message persistence + query service.

    Notes:
    - Writes are best-effort: enqueue failures will be dropped to protect request latency.
    - Call `start()` once at product startup to initialize worker(s).
    - Call `shutdown()` on product shutdown for graceful stop.
    """

    def __init__(
        self,
        *,
        enabled: Optional[bool] = None,
        queue_maxsize: Optional[int] = None,
        workers: Optional[int] = None,
    ) -> None:
        self._enabled = _env_bool("CHAT_HISTORY_ENABLED", True) if enabled is None else enabled
        self._queue_maxsize = _env_int("CHAT_HISTORY_QUEUE_MAXSIZE", 2000) if queue_maxsize is None else queue_maxsize
        self._workers = _env_int("CHAT_HISTORY_WORKERS", 1) if workers is None else workers

        self._queue: Optional[asyncio.Queue[_SaveMessageRequest]] = None
        self._worker_tasks: list[asyncio.Task[None]] = []
        self._started = False
        self._stopping = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def start(self) -> None:
        if self._started:
            return
        if not self._enabled:
            self._started = True
            return

        self._queue = asyncio.Queue(maxsize=max(self._queue_maxsize, 1))
        self._stopping = False

        worker_count = max(int(self._workers), 1)
        self._worker_tasks = [
            asyncio.create_task(self._worker_loop(), name=f"message-store-worker-{i}")
            for i in range(worker_count)
        ]
        self._started = True

    async def shutdown(self) -> None:
        if not self._started:
            return
        self._stopping = True

        if self._worker_tasks:
            for task in self._worker_tasks:
                task.cancel()
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks = []
        self._queue = None
        self._started = False

    async def flush(self, timeout_s: float = 2.0) -> None:
        """
        Wait until queued writes are processed (best-effort).
        Intended for tests only.
        """
        if not self._queue:
            return
        await asyncio.wait_for(self._queue.join(), timeout=timeout_s)

    def enqueue_save_message(
        self,
        *,
        session_name: str,
        role: str,
        content: str,
        conversation_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        response_time_ms: Optional[int] = None,
        created_at: Optional[float] = None,
        message_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Enqueue a message write (non-blocking).

        Returns:
            message_id if accepted; otherwise None.
        """
        if not self._enabled or not self._started or not self._queue:
            return None

        if not session_name or not role or content is None:
            return None

        role = role.strip().lower()
        if role not in {"user", "assistant", "agent"}:
            return None

        msg_id = message_id or str(uuid.uuid4())
        req = _SaveMessageRequest(
            message_id=msg_id,
            session_name=session_name,
            role=role,
            content=content,
            created_at=created_at if created_at is not None else time.time(),
            conversation_id=conversation_id,
            agent_id=agent_id,
            agent_name=agent_name,
            response_time_ms=response_time_ms,
        )

        try:
            self._queue.put_nowait(req)
            return msg_id
        except asyncio.QueueFull:
            return None

    async def _worker_loop(self) -> None:
        assert self._queue is not None
        while True:
            req = await self._queue.get()
            try:
                try:
                    await asyncio.to_thread(self._insert_message, req)
                except Exception:
                    # Best-effort semantics: drop the message on any DB error.
                    # Do not crash the worker; keep draining the queue.
                    pass
            finally:
                self._queue.task_done()

    @staticmethod
    def _insert_message(req: _SaveMessageRequest) -> None:
        from infrastructure.database import init_database, get_db_session
        from infrastructure.database.models import ChatMessageModel

        init_database()
        with get_db_session() as session:
            row = ChatMessageModel(
                message_id=req.message_id,
                session_name=req.session_name,
                conversation_id=req.conversation_id,
                role=req.role,
                content=req.content,
                agent_id=req.agent_id,
                agent_name=req.agent_name,
                response_time_ms=req.response_time_ms,
                created_at=req.created_at,
                # content_tsv is maintained by DB trigger
            )
            session.add(row)
            session.flush()

    async def get_sessions(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> dict[str, Any]:
        """
        List sessions aggregated by `session_name` (optionally including metadata).
        """

        def _query() -> dict[str, Any]:
            from infrastructure.database import init_database, get_db_session
            from infrastructure.database.models import ChatMessageModel, ChatSessionMetaModel

            init_database()

            with get_db_session() as session:
                base = session.query(ChatMessageModel)
                if start_time is not None:
                    base = base.filter(ChatMessageModel.created_at >= float(start_time))
                if end_time is not None:
                    base = base.filter(ChatMessageModel.created_at <= float(end_time))

                # Aggregate per session_name
                agg = (
                    base.with_entities(
                        ChatMessageModel.session_name.label("session_name"),
                        func.count(ChatMessageModel.id).label("message_count"),
                        func.min(ChatMessageModel.created_at).label("first_message_at"),
                        func.max(ChatMessageModel.created_at).label("last_message_at"),
                        func.count(func.distinct(ChatMessageModel.conversation_id)).label("conversation_count"),
                    )
                    .group_by(ChatMessageModel.session_name)
                )

                total = session.query(func.count()).select_from(agg.subquery()).scalar() or 0

                offset = max(page - 1, 0) * max(page_size, 1)

                rows = (
                    agg.order_by(func.max(ChatMessageModel.created_at).desc())
                    .offset(offset)
                    .limit(page_size)
                    .all()
                )

                # Join last message preview + session meta (page_size bounded)
                session_names = [r.session_name for r in rows]
                previews: dict[str, str] = {}
                if session_names:
                    last_created_at_sq = (
                        session.query(
                            ChatMessageModel.session_name.label("session_name"),
                            func.max(ChatMessageModel.created_at).label("last_created_at"),
                        )
                        .filter(ChatMessageModel.session_name.in_(session_names))
                        .group_by(ChatMessageModel.session_name)
                        .subquery()
                    )
                    msg_rows = (
                        session.query(ChatMessageModel.session_name, ChatMessageModel.content)
                        .join(
                            last_created_at_sq,
                            and_(
                                ChatMessageModel.session_name == last_created_at_sq.c.session_name,
                                ChatMessageModel.created_at == last_created_at_sq.c.last_created_at,
                            ),
                        )
                        .all()
                    )
                    for sn, content in msg_rows:
                        previews[sn] = (content or "")[:160]

                meta_by_session: dict[str, Any] = {}
                if session_names:
                    try:
                        meta_rows = (
                            session.query(ChatSessionMetaModel)
                            .filter(ChatSessionMetaModel.session_name.in_(session_names))
                            .all()
                        )
                        for m in meta_rows:
                            meta_by_session[m.session_name] = {
                                "display_name": m.display_name,
                                "note": m.note,
                                "tags": m.tags,
                                "updated_by": m.updated_by,
                                "updated_at": m.updated_at,
                            }
                    except ProgrammingError:
                        meta_by_session = {}

                items = [
                    {
                        "session_name": r.session_name,
                        "meta": meta_by_session.get(r.session_name),
                        "last_message_preview": previews.get(r.session_name, ""),
                        "message_count": int(r.message_count or 0),
                        "first_message_at": float(r.first_message_at or 0.0),
                        "last_message_at": float(r.last_message_at or 0.0),
                        "conversation_count": int(r.conversation_count or 0),
                    }
                    for r in rows
                ]

                return {
                    "items": items,
                    "total": int(total),
                    "page": int(page),
                    "page_size": int(page_size),
                }

        return await asyncio.to_thread(_query)

    async def get_messages_by_session(
        self,
        session_name: str,
        *,
        limit: int = 100,
        offset: int = 0,
        order: str = "asc",
    ) -> dict[str, Any]:
        def _query() -> dict[str, Any]:
            from infrastructure.database import init_database, get_db_session
            from infrastructure.database.models import ChatMessageModel

            init_database()

            with get_db_session() as session:
                q = session.query(ChatMessageModel).filter(ChatMessageModel.session_name == session_name)
                total = q.count()
                order_key = (order or "asc").strip().lower()
                if order_key not in {"asc", "desc"}:
                    order_key = "asc"

                ordered = q.order_by(ChatMessageModel.created_at.desc() if order_key == "desc" else ChatMessageModel.created_at.asc())

                rows = (
                    ordered.offset(max(offset, 0))
                    .limit(min(max(limit, 1), 1000))
                    .all()
                )
                items = [
                    {
                        "id": r.id,
                        "message_id": r.message_id,
                        "session_name": r.session_name,
                        "conversation_id": r.conversation_id,
                        "role": r.role,
                        "content": r.content,
                        "agent_id": r.agent_id,
                        "agent_name": r.agent_name,
                        "response_time_ms": r.response_time_ms,
                        "created_at": r.created_at,
                    }
                    for r in rows
                ]
                return {"session_name": session_name, "total": int(total), "items": items, "order": order_key}

        return await asyncio.to_thread(_query)

    async def search_sessions(
        self,
        *,
        q: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """
        Search sessions by message full-text match and return aggregated session list.
        """
        query_text = (q or "").strip()
        if len(query_text) < 2:
            raise ValueError("query too short")

        def _query() -> dict[str, Any]:
            from infrastructure.database import init_database, get_db_session
            from infrastructure.database.models import ChatMessageModel, ChatSessionMetaModel

            init_database()
            ts_query = func.websearch_to_tsquery("simple", query_text)

            with get_db_session() as session:
                base = session.query(ChatMessageModel).filter(ChatMessageModel.content_tsv.op("@@")(ts_query))
                if start_time is not None:
                    base = base.filter(ChatMessageModel.created_at >= float(start_time))
                if end_time is not None:
                    base = base.filter(ChatMessageModel.created_at <= float(end_time))

                agg = (
                    base.with_entities(
                        ChatMessageModel.session_name.label("session_name"),
                        func.count(ChatMessageModel.id).label("match_count"),
                        func.max(ChatMessageModel.created_at).label("last_match_at"),
                    )
                    .group_by(ChatMessageModel.session_name)
                )

                total = session.query(func.count()).select_from(agg.subquery()).scalar() or 0
                offset = max(page - 1, 0) * max(page_size, 1)
                rows = (
                    agg.order_by(func.max(ChatMessageModel.created_at).desc())
                    .offset(offset)
                    .limit(page_size)
                    .all()
                )

                session_names = [r.session_name for r in rows]
                previews: dict[str, str] = {}
                if session_names:
                    last_match_sq = (
                        base.with_entities(
                            ChatMessageModel.session_name.label("session_name"),
                            func.max(ChatMessageModel.created_at).label("last_match_at"),
                        )
                        .filter(ChatMessageModel.session_name.in_(session_names))
                        .group_by(ChatMessageModel.session_name)
                        .subquery()
                    )
                    msg_rows = (
                        session.query(ChatMessageModel.session_name, ChatMessageModel.content)
                        .join(
                            last_match_sq,
                            and_(
                                ChatMessageModel.session_name == last_match_sq.c.session_name,
                                ChatMessageModel.created_at == last_match_sq.c.last_match_at,
                            ),
                        )
                        .all()
                    )
                    for sn, content in msg_rows:
                        previews[sn] = (content or "")[:160]

                meta_by_session: dict[str, Any] = {}
                if session_names:
                    try:
                        meta_rows = (
                            session.query(ChatSessionMetaModel)
                            .filter(ChatSessionMetaModel.session_name.in_(session_names))
                            .all()
                        )
                        for m in meta_rows:
                            meta_by_session[m.session_name] = {
                                "display_name": m.display_name,
                                "note": m.note,
                                "tags": m.tags,
                                "updated_by": m.updated_by,
                                "updated_at": m.updated_at,
                            }
                    except ProgrammingError:
                        meta_by_session = {}

                items = [
                    {
                        "session_name": r.session_name,
                        "meta": meta_by_session.get(r.session_name),
                        "match_count": int(r.match_count or 0),
                        "last_match_at": float(r.last_match_at or 0.0),
                        "last_match_preview": previews.get(r.session_name, ""),
                    }
                    for r in rows
                ]

                return {"items": items, "total": int(total), "page": int(page), "page_size": int(page_size)}

        return await asyncio.to_thread(_query)

    async def get_session_meta(self, session_name: str) -> dict[str, Any]:
        def _query() -> dict[str, Any]:
            from infrastructure.database import init_database, get_db_session
            from infrastructure.database.models import ChatSessionMetaModel

            init_database()
            with get_db_session() as session:
                try:
                    row = session.query(ChatSessionMetaModel).filter(ChatSessionMetaModel.session_name == session_name).first()
                except ProgrammingError:
                    return {"session_name": session_name, "meta": None}
                if not row:
                    return {"session_name": session_name, "meta": None}
                return {
                    "session_name": session_name,
                    "meta": {
                        "display_name": row.display_name,
                        "note": row.note,
                        "tags": row.tags,
                        "updated_by": row.updated_by,
                        "created_at": row.created_at,
                        "updated_at": row.updated_at,
                    },
                }

        return await asyncio.to_thread(_query)

    async def upsert_session_meta(
        self,
        session_name: str,
        *,
        display_name: Optional[str],
        note: Optional[str],
        tags: Any,
        updated_by: Optional[str],
    ) -> dict[str, Any]:
        def _write() -> dict[str, Any]:
            from infrastructure.database import init_database, get_db_session
            from infrastructure.database.models import ChatSessionMetaModel

            init_database()
            now = time.time()
            with get_db_session() as session:
                try:
                    row = session.query(ChatSessionMetaModel).filter(ChatSessionMetaModel.session_name == session_name).first()
                except ProgrammingError as e:
                    raise RuntimeError(f"chat_session_meta unavailable: {e}")
                if not row:
                    row = ChatSessionMetaModel(
                        session_name=session_name,
                        display_name=display_name.strip() if isinstance(display_name, str) and display_name.strip() else None,
                        note=note.strip() if isinstance(note, str) and note.strip() else None,
                        tags=tags,
                        updated_by=updated_by,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(row)
                else:
                    row.display_name = display_name.strip() if isinstance(display_name, str) and display_name.strip() else None
                    row.note = note.strip() if isinstance(note, str) and note.strip() else None
                    row.tags = tags
                    row.updated_by = updated_by
                    row.updated_at = now
                session.flush()

                return {
                    "session_name": session_name,
                    "meta": {
                        "display_name": row.display_name,
                        "note": row.note,
                        "tags": row.tags,
                        "updated_by": row.updated_by,
                        "created_at": row.created_at,
                        "updated_at": row.updated_at,
                    },
                }

        return await asyncio.to_thread(_write)

    async def create_export_job(
        self,
        *,
        created_by: str,
        request: dict[str, Any],
    ) -> dict[str, Any]:
        def _write() -> dict[str, Any]:
            from infrastructure.database import init_database, get_db_session
            from infrastructure.database.models import ChatExportJobModel

            init_database()
            now = time.time()
            job_id = str(uuid.uuid4())
            row = ChatExportJobModel(
                job_id=job_id,
                created_by=created_by,
                status="pending",
                request=request,
                created_at=now,
                updated_at=now,
            )
            with get_db_session() as session:
                try:
                    session.add(row)
                    session.flush()
                except ProgrammingError as e:
                    raise RuntimeError(f"chat_export_jobs unavailable: {e}")
            return {"job_id": job_id, "status": "pending", "created_by": created_by}

        return await asyncio.to_thread(_write)

    async def list_export_jobs(
        self,
        *,
        created_by: str,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        def _query() -> dict[str, Any]:
            from infrastructure.database import init_database, get_db_session
            from infrastructure.database.models import ChatExportJobModel

            init_database()
            with get_db_session() as session:
                try:
                    q = session.query(ChatExportJobModel).filter(ChatExportJobModel.created_by == created_by)
                except ProgrammingError as e:
                    raise RuntimeError(f"chat_export_jobs unavailable: {e}")
                total = q.count()
                rows = (
                    q.order_by(ChatExportJobModel.created_at.desc())
                    .offset(max(offset, 0))
                    .limit(min(max(limit, 1), 200))
                    .all()
                )
                items = []
                for r in rows:
                    items.append(
                        {
                            "job_id": r.job_id,
                            "created_by": r.created_by,
                            "status": r.status,
                            "request": r.request,
                            "row_count": r.row_count,
                            "file_path": r.file_path,
                            "error": r.error,
                            "created_at": r.created_at,
                            "updated_at": r.updated_at,
                            "finished_at": r.finished_at,
                        }
                    )
                return {"items": items, "total": int(total), "limit": int(limit), "offset": int(offset)}

        return await asyncio.to_thread(_query)

    async def get_export_job(self, job_id: str) -> dict[str, Any]:
        def _query() -> dict[str, Any]:
            from infrastructure.database import init_database, get_db_session
            from infrastructure.database.models import ChatExportJobModel

            init_database()
            with get_db_session() as session:
                try:
                    r = session.query(ChatExportJobModel).filter(ChatExportJobModel.job_id == job_id).first()
                except ProgrammingError as e:
                    raise RuntimeError(f"chat_export_jobs unavailable: {e}")
                if not r:
                    raise ValueError("job not found")
                return {
                    "job_id": r.job_id,
                    "created_by": r.created_by,
                    "status": r.status,
                    "request": r.request,
                    "row_count": r.row_count,
                    "file_path": r.file_path,
                    "error": r.error,
                    "created_at": r.created_at,
                    "updated_at": r.updated_at,
                    "finished_at": r.finished_at,
                }

        return await asyncio.to_thread(_query)

    @staticmethod
    def _export_dir() -> pathlib.Path:
        root = pathlib.Path(os.getenv("CHAT_HISTORY_EXPORT_DIR", "data/exports"))
        return root

    async def run_export_job(self, job_id: str) -> None:
        """
        Execute an export job (best-effort) and write CSV to disk.
        """

        def _run() -> None:
            from infrastructure.database import init_database, get_db_session
            from infrastructure.database.models import ChatExportJobModel, ChatMessageModel, ChatSessionMetaModel

            init_database()
            now = time.time()
            export_dir = self._export_dir()
            export_dir.mkdir(parents=True, exist_ok=True)

            with get_db_session() as session:
                try:
                    job = session.query(ChatExportJobModel).filter(ChatExportJobModel.job_id == job_id).first()
                except ProgrammingError:
                    return
                if not job:
                    return
                job.status = "running"
                job.updated_at = now
                job.error = None
                request = job.request if isinstance(job.request, dict) else {}
                request_snapshot = dict(request)
                session.flush()

            def _fail(err: str) -> None:
                with get_db_session() as session2:
                    job2 = session2.query(ChatExportJobModel).filter(ChatExportJobModel.job_id == job_id).first()
                    if not job2:
                        return
                    job2.status = "failed"
                    job2.error = err[:5000]
                    job2.updated_at = time.time()
                    job2.finished_at = time.time()
                    session2.flush()

            try:
                start_time = request_snapshot.get("start_time")
                end_time = request_snapshot.get("end_time")
                q_text = (request_snapshot.get("q") or "").strip()
                role = (request_snapshot.get("role") or "").strip().lower() or None
                session_name = (request_snapshot.get("session_name") or "").strip() or None

                # Guardrails
                if not start_time or not end_time:
                    _fail("start_time and end_time are required")
                    return
                start_time = float(start_time)
                end_time = float(end_time)
                if end_time < start_time:
                    _fail("end_time must be >= start_time")
                    return
                max_range_s = float(os.getenv("CHAT_HISTORY_EXPORT_MAX_RANGE_SECONDS", str(7 * 86400)))
                if end_time - start_time > max_range_s:
                    _fail("time range too large")
                    return

                max_rows = int(os.getenv("CHAT_HISTORY_EXPORT_MAX_ROWS", "200000"))

                file_path = export_dir / f"chat_export_{job_id}.csv"
                row_count = 0

                with get_db_session() as session3:
                    base = session3.query(ChatMessageModel).filter(
                        ChatMessageModel.created_at >= start_time,
                        ChatMessageModel.created_at <= end_time,
                    )
                    if role:
                        base = base.filter(ChatMessageModel.role == role)
                    if session_name:
                        base = base.filter(ChatMessageModel.session_name == session_name)
                    if q_text:
                        ts_query = func.websearch_to_tsquery("simple", q_text)
                        base = base.filter(ChatMessageModel.content_tsv.op("@@")(ts_query))

                    meta_rows = (
                        session3.query(ChatSessionMetaModel.session_name, ChatSessionMetaModel.display_name)
                        .all()
                    )
                    display_name_map = {sn: dn for sn, dn in meta_rows}

                    with file_path.open("w", encoding="utf-8", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow(
                            [
                                "created_at",
                                "session_name",
                                "session_display_name",
                                "role",
                                "content",
                                "conversation_id",
                                "agent_id",
                                "agent_name",
                                "response_time_ms",
                            ]
                        )

                        for msg in base.order_by(ChatMessageModel.created_at.asc()).yield_per(1000):
                            writer.writerow(
                                [
                                    msg.created_at,
                                    msg.session_name,
                                    display_name_map.get(msg.session_name) or "",
                                    msg.role,
                                    msg.content,
                                    msg.conversation_id or "",
                                    msg.agent_id or "",
                                    msg.agent_name or "",
                                    msg.response_time_ms or "",
                                ]
                            )
                            row_count += 1
                            if row_count >= max_rows:
                                break

                with get_db_session() as session4:
                    job4 = session4.query(ChatExportJobModel).filter(ChatExportJobModel.job_id == job_id).first()
                    if not job4:
                        return
                    job4.status = "done"
                    job4.row_count = row_count
                    job4.file_path = str(file_path)
                    job4.updated_at = time.time()
                    job4.finished_at = time.time()
                    session4.flush()

            except Exception as e:
                _fail(str(e))

        await asyncio.to_thread(_run)

    async def search_messages(
        self,
        *,
        q: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        role: Optional[str] = None,
        session_name: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        query_text = (q or "").strip()
        if len(query_text) < 2:
            raise ValueError("query too short")

        role_filter = role.strip().lower() if role else None
        if role_filter and role_filter not in {"user", "assistant", "agent"}:
            raise ValueError("invalid role")

        def _query() -> dict[str, Any]:
            from infrastructure.database import init_database, get_db_session
            from infrastructure.database.models import ChatMessageModel

            init_database()

            ts_query = func.websearch_to_tsquery("simple", query_text)
            rank = func.ts_rank(ChatMessageModel.content_tsv, ts_query)

            with get_db_session() as session:
                base = session.query(ChatMessageModel).filter(ChatMessageModel.content_tsv.op("@@")(ts_query))
                if start_time is not None:
                    base = base.filter(ChatMessageModel.created_at >= float(start_time))
                if end_time is not None:
                    base = base.filter(ChatMessageModel.created_at <= float(end_time))
                if role_filter:
                    base = base.filter(ChatMessageModel.role == role_filter)
                if session_name:
                    base = base.filter(ChatMessageModel.session_name == session_name)

                total = base.count()
                offset = max(page - 1, 0) * max(page_size, 1)

                rows = (
                    base.add_columns(rank.label("rank"))
                    .order_by(rank.desc(), ChatMessageModel.created_at.desc())
                    .offset(offset)
                    .limit(page_size)
                    .all()
                )

                items = []
                for msg, msg_rank in rows:
                    items.append(
                        {
                            "id": msg.id,
                            "message_id": msg.message_id,
                            "session_name": msg.session_name,
                            "conversation_id": msg.conversation_id,
                            "role": msg.role,
                            "content": msg.content,
                            "agent_id": msg.agent_id,
                            "agent_name": msg.agent_name,
                            "response_time_ms": msg.response_time_ms,
                            "created_at": msg.created_at,
                            "rank": float(msg_rank or 0.0),
                        }
                    )

                return {"items": items, "total": int(total), "page": int(page), "page_size": int(page_size)}

        return await asyncio.to_thread(_query)

    async def get_statistics(
        self,
        *,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> dict[str, Any]:
        def _query() -> dict[str, Any]:
            from infrastructure.database import init_database, get_db_session
            from infrastructure.database.models import ChatMessageModel

            init_database()

            with get_db_session() as session:
                base = session.query(ChatMessageModel)
                if start_time is not None:
                    base = base.filter(ChatMessageModel.created_at >= float(start_time))
                if end_time is not None:
                    base = base.filter(ChatMessageModel.created_at <= float(end_time))

                total_messages = base.count()
                total_sessions = (
                    base.with_entities(ChatMessageModel.session_name).distinct().count()
                )
                by_role_rows = (
                    base.with_entities(ChatMessageModel.role, func.count(ChatMessageModel.id))
                    .group_by(ChatMessageModel.role)
                    .all()
                )
                by_role = {r: int(c) for r, c in by_role_rows}
                avg_resp = (
                    base.filter(ChatMessageModel.role == "assistant")
                    .with_entities(func.avg(ChatMessageModel.response_time_ms))
                    .scalar()
                )

                return {
                    "total_messages": int(total_messages),
                    "total_sessions": int(total_sessions),
                    "by_role": by_role,
                    "avg_response_time_ms": float(avg_resp) if avg_resp is not None else 0.0,
                }

        return await asyncio.to_thread(_query)

    async def export_messages_csv(
        self,
        *,
        session_name: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> bytes:
        def _query_rows() -> list[dict[str, Any]]:
            from infrastructure.database import init_database, get_db_session
            from infrastructure.database.models import ChatMessageModel

            init_database()

            with get_db_session() as session:
                q = session.query(ChatMessageModel).filter(ChatMessageModel.session_name == session_name)
                if start_time is not None:
                    q = q.filter(ChatMessageModel.created_at >= float(start_time))
                if end_time is not None:
                    q = q.filter(ChatMessageModel.created_at <= float(end_time))
                rows = q.order_by(ChatMessageModel.created_at.asc()).all()

                return [
                    {
                        "created_at": r.created_at,
                        "role": r.role,
                        "content": r.content,
                        "conversation_id": r.conversation_id or "",
                        "agent_id": r.agent_id or "",
                        "agent_name": r.agent_name or "",
                        "response_time_ms": r.response_time_ms if r.response_time_ms is not None else "",
                    }
                    for r in rows
                ]

        rows = await asyncio.to_thread(_query_rows)

        buf = io.StringIO()
        writer = csv.DictWriter(
            buf,
            fieldnames=[
                "created_at",
                "role",
                "content",
                "conversation_id",
                "agent_id",
                "agent_name",
                "response_time_ms",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
        return buf.getvalue().encode("utf-8")
