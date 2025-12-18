import json
import time
import uuid
from typing import Optional, Dict, Any, List, Literal

from pydantic import BaseModel, Field

AuditEventType = Literal[
    "created",
    "status_changed",
    "priority_changed",
    "assigned",
    "commented",
    "attachment_uploaded"
]


class AuditLog(BaseModel):
    id: str
    ticket_id: str
    event_type: AuditEventType
    operator_id: str
    operator_name: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=lambda: time.time())


class AuditLogStore:
    def __init__(self, redis_client: Optional["redis.Redis"] = None, max_logs: int = 500):
        self.redis = redis_client
        self.max_logs = max_logs
        self.key_prefix = "audit_log"
        self._memory_store: Dict[str, List[str]] = {} if redis_client is None else None  # type: ignore

    def _key(self, ticket_id: str) -> str:
        return f"{self.key_prefix}:{ticket_id}"

    def add_log(
        self,
        ticket_id: str,
        event_type: AuditEventType,
        operator_id: str,
        operator_name: Optional[str],
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        log = AuditLog(
            id=f"audit_{uuid.uuid4().hex[:16]}",
            ticket_id=ticket_id,
            event_type=event_type,
            operator_id=operator_id,
            operator_name=operator_name,
            details=details or {}
        )
        payload = json.dumps(log.dict(), ensure_ascii=False)
        if self.redis:
            pipe = self.redis.pipeline()
            pipe.lpush(self._key(ticket_id), payload)
            pipe.ltrim(self._key(ticket_id), 0, self.max_logs - 1)
            pipe.execute()
        else:
            logs = self._memory_store.setdefault(ticket_id, [])
            logs.insert(0, payload)
            if len(logs) > self.max_logs:
                del logs[self.max_logs:]
        return log

    def list_logs(self, ticket_id: str, limit: int = 100) -> List[AuditLog]:
        limit = max(1, min(limit, self.max_logs))
        if self.redis:
            raw_logs = self.redis.lrange(self._key(ticket_id), 0, limit - 1) or []
            return [AuditLog(**json.loads(raw.decode("utf-8"))) for raw in raw_logs]

        logs = self._memory_store.get(ticket_id, []) if self._memory_store else []
        return [AuditLog(**json.loads(raw)) for raw in logs[:limit]]
