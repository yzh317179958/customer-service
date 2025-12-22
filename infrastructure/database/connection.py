# -*- coding: utf-8 -*-
"""
基础设施 - 数据库连接管理模块

提供 PostgreSQL 连接池管理，支持：
- 单例模式：避免重复初始化
- 连接池：高效复用数据库连接
- 上下文管理器：自动管理会话生命周期
- 配置外部化：通过环境变量配置
"""

import os
from dataclasses import dataclass
from typing import Optional, Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from .base import Base


@dataclass
class DatabaseConfig:
    """
    数据库配置类

    支持从环境变量加载配置。
    """
    url: str = "postgresql://fiido:fiido123@localhost:5432/fiido_db"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 1800
    echo: bool = False

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """从环境变量加载配置"""
        return cls(
            url=os.getenv("DATABASE_URL", cls.url),
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "1800")),
            echo=os.getenv("DB_ECHO", "false").lower() == "true"
        )


# ============================================================================
# 全局单例
# ============================================================================

_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None
_initialized: bool = False


def init_database(config: Optional[DatabaseConfig] = None) -> Engine:
    """
    初始化数据库连接（单例模式）

    Args:
        config: 数据库配置，默认从环境变量读取

    Returns:
        SQLAlchemy Engine 实例

    注意:
        - 重复调用会返回已初始化的 Engine
        - 使用 QueuePool 连接池管理连接
    """
    global _engine, _session_factory, _initialized

    if _initialized and _engine is not None:
        return _engine

    config = config or DatabaseConfig.from_env()

    # 创建引擎（同步模式，使用 psycopg2）
    _engine = create_engine(
        config.url,
        poolclass=QueuePool,
        pool_size=config.pool_size,
        max_overflow=config.max_overflow,
        pool_timeout=config.pool_timeout,
        pool_recycle=config.pool_recycle,
        echo=config.echo,
        # 连接参数
        connect_args={
            "connect_timeout": 10,
            "options": "-c timezone=UTC"
        }
    )

    # 创建会话工厂
    _session_factory = sessionmaker(
        bind=_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False
    )

    _initialized = True

    print(f"[Database] ✅ PostgreSQL 初始化成功")
    print(f"   连接池大小: {config.pool_size}")
    print(f"   最大溢出: {config.max_overflow}")
    print(f"   回收时间: {config.pool_recycle}s")

    return _engine


def get_engine() -> Engine:
    """
    获取数据库引擎

    Returns:
        SQLAlchemy Engine 实例

    Raises:
        RuntimeError: 未初始化时抛出
    """
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _engine


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    获取数据库会话（上下文管理器）

    使用示例:
        with get_db_session() as session:
            result = session.execute(text("SELECT 1"))
            session.commit()

    Yields:
        SQLAlchemy Session 实例

    Raises:
        RuntimeError: 未初始化时抛出

    注意:
        - 自动处理事务提交/回滚
        - 自动关闭会话
    """
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")

    session = _session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_all_tables() -> None:
    """
    创建所有表（仅用于开发/测试）

    生产环境应使用 Alembic 迁移。
    """
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    Base.metadata.create_all(_engine)
    print("[Database] ✅ 所有表创建成功")


def drop_all_tables() -> None:
    """
    删除所有表（危险操作，仅用于测试）
    """
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    Base.metadata.drop_all(_engine)
    print("[Database] ⚠️ 所有表已删除")


def check_connection() -> bool:
    """
    检查数据库连接是否正常

    Returns:
        True 表示连接正常，False 表示连接失败
    """
    try:
        with get_db_session() as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"[Database] ❌ 连接检查失败: {e}")
        return False


def get_pool_status() -> dict:
    """
    获取连接池状态

    Returns:
        包含连接池信息的字典
    """
    if _engine is None:
        return {"status": "not_initialized"}

    pool = _engine.pool
    return {
        "status": "ok",
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.invalidatedcount() if hasattr(pool, 'invalidatedcount') else 0
    }


def reset() -> None:
    """
    重置数据库连接（仅用于测试）
    """
    global _engine, _session_factory, _initialized

    if _engine is not None:
        _engine.dispose()

    _engine = None
    _session_factory = None
    _initialized = False
