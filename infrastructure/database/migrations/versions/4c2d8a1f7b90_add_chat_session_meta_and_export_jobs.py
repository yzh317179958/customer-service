# -*- coding: utf-8 -*-
"""
add chat_session_meta and chat_export_jobs

Revision ID: 4c2d8a1f7b90
Revises: 3b6c9e2f4a7d
Create Date: 2026-01-07
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "4c2d8a1f7b90"
down_revision = "3b6c9e2f4a7d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_session_meta",
        sa.Column("session_name", sa.String(length=200), primary_key=True, nullable=False, comment="会话标识(session_name)"),
        sa.Column("display_name", sa.String(length=200), nullable=True, comment="业务友好展示名（可编辑）"),
        sa.Column("note", sa.String(length=2000), nullable=True, comment="会话备注（可编辑）"),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment="会话标签（数组/对象）"),
        sa.Column("updated_by", sa.String(length=100), nullable=True, comment="最后编辑人（坐席 username）"),
        sa.Column("created_at", sa.Float(), nullable=False, comment="创建时间(Unix时间戳)"),
        sa.Column("updated_at", sa.Float(), nullable=False, comment="更新时间(Unix时间戳)"),
        sa.PrimaryKeyConstraint("session_name"),
        comment="聊天会话元信息（展示名/备注/标签）",
    )

    op.create_index("ix_chat_session_meta_updated_at", "chat_session_meta", ["updated_at"], unique=False)

    op.create_table(
        "chat_export_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("job_id", sa.String(length=36), nullable=False, comment="导出任务ID(UUID)"),
        sa.Column("created_by", sa.String(length=100), nullable=False, comment="创建人（坐席 username）"),
        sa.Column("status", sa.String(length=20), nullable=False, comment="状态: pending/running/done/failed"),
        sa.Column("request", postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment="导出参数（JSON）"),
        sa.Column("row_count", sa.Integer(), nullable=True, comment="导出行数（消息条数）"),
        sa.Column("file_path", sa.String(length=500), nullable=True, comment="CSV 文件路径（本地/挂载卷）"),
        sa.Column("error", sa.Text(), nullable=True, comment="失败原因"),
        sa.Column("created_at", sa.Float(), nullable=False, comment="创建时间(Unix时间戳)"),
        sa.Column("updated_at", sa.Float(), nullable=False, comment="更新时间(Unix时间戳)"),
        sa.Column("finished_at", sa.Float(), nullable=True, comment="完成时间(Unix时间戳)"),
        sa.UniqueConstraint("job_id", name="uq_chat_export_jobs_job_id"),
        comment="聊天记录导出任务",
    )

    op.create_index("ix_chat_export_jobs_job_id", "chat_export_jobs", ["job_id"], unique=False)
    op.create_index("ix_chat_export_jobs_created_by", "chat_export_jobs", ["created_by"], unique=False)
    op.create_index("ix_chat_export_jobs_status", "chat_export_jobs", ["status"], unique=False)
    op.create_index("ix_chat_export_jobs_created_at", "chat_export_jobs", ["created_at"], unique=False)
    op.create_index("ix_chat_export_jobs_updated_at", "chat_export_jobs", ["updated_at"], unique=False)
    op.create_index("ix_chat_export_jobs_created_by_time", "chat_export_jobs", ["created_by", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_chat_export_jobs_created_by_time", table_name="chat_export_jobs")
    op.drop_index("ix_chat_export_jobs_updated_at", table_name="chat_export_jobs")
    op.drop_index("ix_chat_export_jobs_created_at", table_name="chat_export_jobs")
    op.drop_index("ix_chat_export_jobs_status", table_name="chat_export_jobs")
    op.drop_index("ix_chat_export_jobs_created_by", table_name="chat_export_jobs")
    op.drop_index("ix_chat_export_jobs_job_id", table_name="chat_export_jobs")
    op.drop_table("chat_export_jobs")

    op.drop_index("ix_chat_session_meta_updated_at", table_name="chat_session_meta")
    op.drop_table("chat_session_meta")

