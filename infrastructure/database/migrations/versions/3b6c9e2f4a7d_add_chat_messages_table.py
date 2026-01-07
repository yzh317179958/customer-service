"""add_chat_messages_table

Revision ID: 3b6c9e2f4a7d
Revises: 2a8f3b4c5d6e
Create Date: 2026-01-07 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "3b6c9e2f4a7d"
down_revision: Union[str, None] = "2a8f3b4c5d6e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("message_id", sa.String(length=36), nullable=False, comment="消息ID(UUID)"),
        sa.Column("session_name", sa.String(length=200), nullable=False, comment="会话标识(session_name)"),
        sa.Column("conversation_id", sa.String(length=100), nullable=True, comment="Coze conversation_id"),
        sa.Column("role", sa.String(length=20), nullable=False, comment="角色: user/assistant/agent"),
        sa.Column("content", sa.Text(), nullable=False, comment="消息内容"),
        sa.Column("agent_id", sa.String(length=100), nullable=True, comment="坐席ID"),
        sa.Column("agent_name", sa.String(length=100), nullable=True, comment="坐席名称"),
        sa.Column("response_time_ms", sa.Integer(), nullable=True, comment="AI响应耗时(毫秒)"),
        sa.Column("created_at", sa.Float(), nullable=False, comment="创建时间(Unix时间戳)"),
        sa.Column("content_tsv", postgresql.TSVECTOR(), nullable=False, comment="全文检索向量(to_tsvector)"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id", name="uq_chat_messages_message_id"),
        comment="聊天消息表",
    )

    # Indexes
    op.create_index(op.f("ix_chat_messages_session_name"), "chat_messages", ["session_name"], unique=False)
    op.create_index(op.f("ix_chat_messages_conversation_id"), "chat_messages", ["conversation_id"], unique=False)
    op.create_index(op.f("ix_chat_messages_role"), "chat_messages", ["role"], unique=False)
    op.create_index(op.f("ix_chat_messages_created_at"), "chat_messages", ["created_at"], unique=False)
    op.create_index("ix_chat_messages_time_session", "chat_messages", ["created_at", "session_name"], unique=False)

    # Full-text search support (PostgreSQL 15+; plpgsql is available by default)
    op.execute(
        """
CREATE FUNCTION chat_messages_content_tsv_update() RETURNS trigger AS $$
BEGIN
  NEW.content_tsv := to_tsvector('simple', coalesce(NEW.content, ''));
  RETURN NEW;
END
$$ LANGUAGE plpgsql;
"""
    )
    op.execute(
        """
CREATE TRIGGER chat_messages_content_tsv_trigger
BEFORE INSERT OR UPDATE OF content ON chat_messages
FOR EACH ROW EXECUTE FUNCTION chat_messages_content_tsv_update();
"""
    )
    op.create_index(
        "ix_chat_messages_content_tsv",
        "chat_messages",
        ["content_tsv"],
        unique=False,
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_chat_messages_content_tsv", table_name="chat_messages")
    op.execute("DROP TRIGGER IF EXISTS chat_messages_content_tsv_trigger ON chat_messages;")
    op.execute("DROP FUNCTION IF EXISTS chat_messages_content_tsv_update;")

    op.drop_index("ix_chat_messages_time_session", table_name="chat_messages")
    op.drop_index(op.f("ix_chat_messages_created_at"), table_name="chat_messages")
    op.drop_index(op.f("ix_chat_messages_role"), table_name="chat_messages")
    op.drop_index(op.f("ix_chat_messages_conversation_id"), table_name="chat_messages")
    op.drop_index(op.f("ix_chat_messages_session_name"), table_name="chat_messages")
    op.drop_table("chat_messages")
