# -*- coding: utf-8 -*-
"""
基础设施 - 数据库启动引导模块

提供 PostgreSQL 数据库初始化和访问接口。
"""

from typing import Optional, Generator
from contextlib import contextmanager

from infrastructure.database import (
    init_database as _init_database,
    get_db_session as _get_db_session,
    check_connection,
    get_pool_status,
    DatabaseConfig,
)
from infrastructure.database.base import Base
from sqlalchemy.orm import Session


# 全局状态
_db_initialized = False


def init_database(config: Optional[DatabaseConfig] = None):
    """
    初始化数据库连接

    Args:
        config: 数据库配置，默认从环境变量读取

    Returns:
        SQLAlchemy Engine 实例
    """
    global _db_initialized

    engine = _init_database(config)
    _db_initialized = True

    return engine


def get_db_session() -> Generator[Session, None, None]:
    """
    获取数据库会话（上下文管理器）

    使用示例:
        with get_db_session() as session:
            result = session.execute(text("SELECT 1"))
    """
    if not _db_initialized:
        init_database()

    return _get_db_session()


def is_database_initialized() -> bool:
    """检查数据库是否已初始化"""
    return _db_initialized


def get_database_status() -> dict:
    """
    获取数据库状态信息

    Returns:
        包含连接状态和连接池信息的字典
    """
    if not _db_initialized:
        return {"status": "not_initialized"}

    pool_status = get_pool_status()
    connection_ok = check_connection()

    return {
        "status": "ok" if connection_ok else "error",
        "connection": "ok" if connection_ok else "failed",
        "pool": pool_status,
    }
