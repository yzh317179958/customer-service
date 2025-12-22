import json
import time
import uuid
import logging
from typing import Optional, Dict, Any, List, Literal

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

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
    """审计日志存储（支持 PostgreSQL + Redis/内存）"""

    def __init__(
        self,
        redis_client: Optional["redis.Redis"] = None,
        max_logs: int = 500,
        enable_postgres: bool = False
    ):
        self.redis = redis_client
        self.max_logs = max_logs
        self.key_prefix = "audit_log"
        self._memory_store: Dict[str, List[str]] = {} if redis_client is None else None  # type: ignore
        self._pg_enabled = enable_postgres

    def enable_postgres(self):
        """启用 PostgreSQL"""
        self._pg_enabled = True
        logger.info("[AuditLogStore] PostgreSQL 已启用")

    def disable_postgres(self):
        """禁用 PostgreSQL"""
        self._pg_enabled = False
        logger.info("[AuditLogStore] PostgreSQL 已禁用")

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

        # 1. 写入 PostgreSQL（主存储）
        if self._pg_enabled:
            self._pg_add_log(log)

        # 2. 写入 Redis/内存（缓存，保留兼容性）
        payload = json.dumps(log.dict(), ensure_ascii=False)
        if self.redis:
            try:
                pipe = self.redis.pipeline()
                pipe.lpush(self._key(ticket_id), payload)
                pipe.ltrim(self._key(ticket_id), 0, self.max_logs - 1)
                pipe.execute()
            except Exception as e:
                logger.warning(f"[AuditLogStore] Redis 缓存写入失败: {e}")
        else:
            logs = self._memory_store.setdefault(ticket_id, [])
            logs.insert(0, payload)
            if len(logs) > self.max_logs:
                del logs[self.max_logs:]

        return log

    def _pg_add_log(self, log: AuditLog):
        """写入 PostgreSQL"""
        try:
            from infrastructure.database import get_db_session
            from infrastructure.database.converters import audit_log_to_orm

            with get_db_session() as session:
                orm_log = audit_log_to_orm(log)
                session.add(orm_log)
        except Exception as e:
            logger.error(f"[AuditLogStore] PostgreSQL 写入失败: {e}")

    def list_logs(self, ticket_id: str, limit: int = 100) -> List[AuditLog]:
        """获取工单审计日志"""
        limit = max(1, min(limit, self.max_logs))

        # 优先从 PostgreSQL 查询
        if self._pg_enabled:
            logs = self._pg_list_logs(ticket_id, limit)
            if logs is not None:
                return logs

        # 降级到 Redis/内存
        if self.redis:
            raw_logs = self.redis.lrange(self._key(ticket_id), 0, limit - 1) or []
            return [AuditLog(**json.loads(raw.decode("utf-8"))) for raw in raw_logs]

        logs = self._memory_store.get(ticket_id, []) if self._memory_store else []
        return [AuditLog(**json.loads(raw)) for raw in logs[:limit]]

    def _pg_list_logs(self, ticket_id: str, limit: int) -> Optional[List[AuditLog]]:
        """从 PostgreSQL 查询审计日志"""
        try:
            from infrastructure.database import get_db_session
            from infrastructure.database.models import AuditLogModel
            from infrastructure.database.converters import audit_log_from_orm

            with get_db_session() as session:
                orm_logs = session.query(AuditLogModel).filter_by(
                    ticket_id=ticket_id
                ).order_by(
                    AuditLogModel.created_at.desc()
                ).limit(limit).all()

                return [audit_log_from_orm(m) for m in orm_logs]
        except Exception as e:
            logger.error(f"[AuditLogStore] PostgreSQL 查询失败: {e}")
            return None
