# -*- coding: utf-8 -*-
"""
会话归档服务

功能：
- 将会话数据归档到 PostgreSQL
- 支持按条件查询历史会话
- 支持会话分析和统计
"""

import time
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class SessionArchiveService:
    """会话归档服务"""

    def __init__(self, enable_postgres: bool = True):
        self._pg_enabled = enable_postgres

    def enable_postgres(self):
        """启用 PostgreSQL"""
        self._pg_enabled = True
        logger.info("[SessionArchive] PostgreSQL 已启用")

    def disable_postgres(self):
        """禁用 PostgreSQL"""
        self._pg_enabled = False
        logger.info("[SessionArchive] PostgreSQL 已禁用")

    def archive_session(
        self,
        session_state: Any,
        archived_by: str = "system",
        archive_reason: Optional[str] = None
    ) -> Optional[str]:
        """
        归档会话到 PostgreSQL

        Args:
            session_state: SessionState 对象
            archived_by: 归档操作者
            archive_reason: 归档原因

        Returns:
            归档记录 ID 或 None
        """
        if not self._pg_enabled:
            logger.warning("[SessionArchive] PostgreSQL 未启用，跳过归档")
            return None

        try:
            from infrastructure.database import get_db_session
            from infrastructure.database.models import SessionArchiveModel

            # 提取会话消息
            messages_data = []
            if hasattr(session_state, 'history') and session_state.history:
                for msg in session_state.history:
                    messages_data.append({
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp
                    })

            # 提取客户信息
            customer_id = None
            customer_email = None
            customer_name = None
            if hasattr(session_state, 'customer') and session_state.customer:
                customer = session_state.customer
                customer_id = getattr(customer, 'id', None)
                customer_email = getattr(customer, 'email', None)
                customer_name = getattr(customer, 'name', None)

            # 计算会话时长
            started_at = getattr(session_state, 'created_at', time.time())
            ended_at = getattr(session_state, 'closed_at', time.time())
            duration = int(ended_at - started_at) if ended_at and started_at else 0

            archive_id = f"archive_{session_state.session_name}_{int(time.time())}"

            with get_db_session() as session:
                archive = SessionArchiveModel(
                    archive_id=archive_id,
                    session_id=session_state.session_name,
                    session_name=archive_reason or "archived_session",
                    customer_id=customer_id,
                    customer_email=customer_email,
                    customer_name=customer_name,
                    agent_id=getattr(session_state, 'assigned_agent_id', None),
                    agent_name=getattr(session_state, 'assigned_agent_name', None),
                    messages=messages_data,
                    message_count=len(messages_data),
                    duration_seconds=duration,
                    started_at=started_at,
                    ended_at=ended_at,
                    archived_at=time.time()
                )
                session.add(archive)

            logger.info(f"[SessionArchive] 会话归档成功: {archive_id}")
            return archive_id

        except Exception as e:
            logger.error(f"[SessionArchive] 会话归档失败: {e}")
            return None

    def get_archived_session(self, archive_id: str) -> Optional[Dict[str, Any]]:
        """获取归档会话"""
        if not self._pg_enabled:
            return None

        try:
            from infrastructure.database import get_db_session
            from infrastructure.database.models import SessionArchiveModel

            with get_db_session() as session:
                archive = session.query(SessionArchiveModel).filter_by(
                    archive_id=archive_id
                ).first()

                if not archive:
                    return None

                return {
                    "archive_id": archive.archive_id,
                    "session_id": archive.session_id,
                    "session_name": archive.session_name,
                    "customer_id": archive.customer_id,
                    "customer_email": archive.customer_email,
                    "customer_name": archive.customer_name,
                    "agent_id": archive.agent_id,
                    "agent_name": archive.agent_name,
                    "messages": archive.messages,
                    "message_count": archive.message_count,
                    "duration_seconds": archive.duration_seconds,
                    "started_at": archive.started_at,
                    "ended_at": archive.ended_at,
                    "archived_at": archive.archived_at
                }

        except Exception as e:
            logger.error(f"[SessionArchive] 查询归档会话失败: {e}")
            return None

    def list_archived_sessions(
        self,
        *,
        customer_email: Optional[str] = None,
        agent_id: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[int, List[Dict[str, Any]]]:
        """
        查询归档会话列表

        Args:
            customer_email: 客户邮箱
            agent_id: 坐席 ID
            start_time: 开始时间
            end_time: 结束时间
            limit: 每页数量
            offset: 偏移量

        Returns:
            (总数, 会话列表)
        """
        if not self._pg_enabled:
            return 0, []

        try:
            from infrastructure.database import get_db_session
            from infrastructure.database.models import SessionArchiveModel

            with get_db_session() as db_session:
                query = db_session.query(SessionArchiveModel)

                # 应用过滤条件
                if customer_email:
                    query = query.filter(
                        SessionArchiveModel.customer_email == customer_email
                    )
                if agent_id:
                    query = query.filter(
                        SessionArchiveModel.agent_id == agent_id
                    )
                if start_time:
                    query = query.filter(
                        SessionArchiveModel.archived_at >= start_time
                    )
                if end_time:
                    query = query.filter(
                        SessionArchiveModel.archived_at <= end_time
                    )

                # 获取总数
                total = query.count()

                # 分页查询
                archives = query.order_by(
                    SessionArchiveModel.archived_at.desc()
                ).offset(offset).limit(limit).all()

                result = []
                for archive in archives:
                    result.append({
                        "archive_id": archive.archive_id,
                        "session_id": archive.session_id,
                        "customer_name": archive.customer_name,
                        "customer_email": archive.customer_email,
                        "agent_name": archive.agent_name,
                        "message_count": archive.message_count,
                        "duration_seconds": archive.duration_seconds,
                        "archived_at": archive.archived_at
                    })

                return total, result

        except Exception as e:
            logger.error(f"[SessionArchive] 查询归档列表失败: {e}")
            return 0, []


# 全局实例
_archive_service: Optional[SessionArchiveService] = None


def get_archive_service() -> SessionArchiveService:
    """获取全局归档服务实例"""
    global _archive_service
    if _archive_service is None:
        _archive_service = SessionArchiveService()
    return _archive_service
