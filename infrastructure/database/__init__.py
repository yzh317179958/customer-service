# -*- coding: utf-8 -*-
"""
Infrastructure - Database Module

Provides PostgreSQL database support:
- Connection pool management
- ORM base class
- Database migrations (Alembic)

Usage:
    from infrastructure.database import init_database, get_db_session

    # Initialize database
    init_database()

    # Use session
    with get_db_session() as session:
        result = session.execute(text("SELECT 1"))
        print(result.scalar())
"""

# Base class
from .base import Base, TimestampMixin

# Connection management
from .connection import (
    DatabaseConfig,
    init_database,
    get_engine,
    get_db_session,
    create_all_tables,
    drop_all_tables,
    check_connection,
    get_pool_status,
    reset,
)

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    # Connection
    "DatabaseConfig",
    "init_database",
    "get_engine",
    "get_db_session",
    "create_all_tables",
    "drop_all_tables",
    "check_connection",
    "get_pool_status",
    "reset",
]
