# -*- coding: utf-8 -*-
"""
Alembic 迁移环境配置

此文件配置 Alembic 如何连接数据库并发现 ORM 模型。
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 添加项目根目录到 Python 路径
# 从 infrastructure/database/migrations/ 向上三级到项目根目录
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

# 导入所有 ORM 模型（必须在 target_metadata 之前导入）
from infrastructure.database.base import Base
from infrastructure.database.models import (
    TicketModel,
    TicketCommentModel,
    TicketAttachmentModel,
    TicketStatusHistoryModel,
    TicketAssignmentModel,
    AgentModel,
    AuditLogModel,
    SessionArchiveModel,
    EmailRecordModel,
    ChatMessageModel,
    ChatSessionMetaModel,
    ChatExportJobModel,
)

# Alembic Config 对象
config = context.config

# 日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 目标元数据（用于自动生成迁移）
target_metadata = Base.metadata

# 从环境变量覆盖数据库 URL（如果存在）
def get_url():
    return os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))


def run_migrations_offline() -> None:
    """
    离线模式运行迁移

    不需要实际的数据库连接，只生成 SQL 语句。
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    在线模式运行迁移

    需要实际的数据库连接。
    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
