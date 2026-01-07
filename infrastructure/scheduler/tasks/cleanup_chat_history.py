# -*- coding: utf-8 -*-
"""
Chat history cleanup task.

Deletes `chat_messages` rows older than the configured retention window.
"""

import os
import time


def _get_retention_days() -> int:
    raw = os.getenv("CHAT_HISTORY_RETENTION_DAYS", "30").strip()
    try:
        days = int(raw)
        return max(days, 0)
    except ValueError:
        return 30


async def cleanup_old_chat_messages() -> int:
    """
    Cleanup old chat messages.

    Returns:
        Number of deleted rows.
    """
    retention_days = _get_retention_days()
    if retention_days <= 0:
        return 0

    cutoff = time.time() - (retention_days * 24 * 60 * 60)

    from infrastructure.database import init_database, get_db_session
    from infrastructure.database.models import ChatMessageModel

    # Ensure DB is initialized in worker contexts (idempotent).
    init_database()

    with get_db_session() as session:
        deleted = (
            session.query(ChatMessageModel)
            .filter(ChatMessageModel.created_at < cutoff)
            .delete(synchronize_session=False)
        )
        session.commit()

    return int(deleted or 0)
