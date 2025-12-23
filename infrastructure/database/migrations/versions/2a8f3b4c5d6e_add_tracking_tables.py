"""add_tracking_tables

Revision ID: 2a8f3b4c5d6e
Revises: 1df7162a1a3e
Create Date: 2025-12-23

新增物流追踪相关表：
- tracking_registrations: 运单注册记录
- notification_records: 通知发送记录
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2a8f3b4c5d6e'
down_revision: Union[str, None] = '1df7162a1a3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建运单注册记录表
    op.create_table('tracking_registrations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tracking_number', sa.String(length=100), nullable=False, comment='运单号'),
        sa.Column('carrier_code', sa.Integer(), nullable=True, comment='承运商代码(17track)'),
        sa.Column('carrier_name', sa.String(length=100), nullable=True, comment='承运商名称'),
        sa.Column('order_id', sa.String(length=50), nullable=True, comment='Shopify订单ID'),
        sa.Column('order_number', sa.String(length=50), nullable=True, comment='订单显示号(如#1234)'),
        sa.Column('site', sa.String(length=20), nullable=True, comment='站点(uk/de/us)'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='registered', comment='状态: registered/tracking/delivered/exception/stopped'),
        sa.Column('current_tracking_status', sa.String(length=30), nullable=True, comment='17track当前状态: NotFound/InTransit/Delivered等'),
        sa.Column('is_delivered', sa.Boolean(), nullable=False, server_default='false', comment='是否已签收'),
        sa.Column('is_exception', sa.Boolean(), nullable=False, server_default='false', comment='是否有异常'),
        sa.Column('register_response', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='注册API响应'),
        sa.Column('last_event', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='最新物流事件'),
        sa.Column('created_at', sa.Float(), nullable=False, comment='创建时间(Unix时间戳)'),
        sa.Column('updated_at', sa.Float(), nullable=False, comment='更新时间(Unix时间戳)'),
        sa.Column('delivered_at', sa.Float(), nullable=True, comment='签收时间(Unix时间戳)'),
        sa.PrimaryKeyConstraint('id'),
        comment='运单注册记录表'
    )
    op.create_index(op.f('ix_tracking_registrations_tracking_number'), 'tracking_registrations', ['tracking_number'], unique=True)
    op.create_index(op.f('ix_tracking_registrations_order_id'), 'tracking_registrations', ['order_id'], unique=False)
    op.create_index(op.f('ix_tracking_registrations_site'), 'tracking_registrations', ['site'], unique=False)
    op.create_index(op.f('ix_tracking_registrations_status'), 'tracking_registrations', ['status'], unique=False)
    op.create_index(op.f('ix_tracking_registrations_created_at'), 'tracking_registrations', ['created_at'], unique=False)
    op.create_index('ix_tracking_reg_order_site', 'tracking_registrations', ['order_id', 'site'], unique=False)
    op.create_index('ix_tracking_reg_status_created', 'tracking_registrations', ['status', 'created_at'], unique=False)

    # 创建通知发送记录表
    op.create_table('notification_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('notification_id', sa.String(length=50), nullable=False, comment='通知ID'),
        sa.Column('tracking_number', sa.String(length=100), nullable=True, comment='关联运单号'),
        sa.Column('order_id', sa.String(length=50), nullable=True, comment='关联订单ID'),
        sa.Column('order_number', sa.String(length=50), nullable=True, comment='订单显示号'),
        sa.Column('site', sa.String(length=20), nullable=True, comment='站点'),
        sa.Column('notification_type', sa.String(length=30), nullable=False, comment='类型: split_package/presale/exception/delivery'),
        sa.Column('exception_type', sa.String(length=30), nullable=True, comment='异常类型: address_issue/customs/lost等'),
        sa.Column('to_email', sa.String(length=200), nullable=False, comment='收件人邮箱'),
        sa.Column('customer_name', sa.String(length=200), nullable=True, comment='客户姓名'),
        sa.Column('subject', sa.String(length=500), nullable=False, comment='邮件主题'),
        sa.Column('template_name', sa.String(length=100), nullable=True, comment='使用的模板名'),
        sa.Column('template_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='模板渲染数据'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending', comment='状态: pending/sent/failed'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0', comment='重试次数'),
        sa.Column('trigger_event', sa.String(length=50), nullable=True, comment='触发事件: fulfillment_create/tracking_update等'),
        sa.Column('trigger_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='触发事件数据'),
        sa.Column('created_at', sa.Float(), nullable=False, comment='创建时间'),
        sa.Column('sent_at', sa.Float(), nullable=True, comment='发送时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='物流通知发送记录表'
    )
    op.create_index(op.f('ix_notification_records_notification_id'), 'notification_records', ['notification_id'], unique=True)
    op.create_index(op.f('ix_notification_records_tracking_number'), 'notification_records', ['tracking_number'], unique=False)
    op.create_index(op.f('ix_notification_records_order_id'), 'notification_records', ['order_id'], unique=False)
    op.create_index(op.f('ix_notification_records_notification_type'), 'notification_records', ['notification_type'], unique=False)
    op.create_index(op.f('ix_notification_records_to_email'), 'notification_records', ['to_email'], unique=False)
    op.create_index(op.f('ix_notification_records_status'), 'notification_records', ['status'], unique=False)
    op.create_index(op.f('ix_notification_records_created_at'), 'notification_records', ['created_at'], unique=False)
    op.create_index('ix_notification_type_created', 'notification_records', ['notification_type', 'created_at'], unique=False)
    op.create_index('ix_notification_order_type', 'notification_records', ['order_id', 'notification_type'], unique=False)


def downgrade() -> None:
    # 删除通知记录表
    op.drop_index('ix_notification_order_type', table_name='notification_records')
    op.drop_index('ix_notification_type_created', table_name='notification_records')
    op.drop_index(op.f('ix_notification_records_created_at'), table_name='notification_records')
    op.drop_index(op.f('ix_notification_records_status'), table_name='notification_records')
    op.drop_index(op.f('ix_notification_records_to_email'), table_name='notification_records')
    op.drop_index(op.f('ix_notification_records_notification_type'), table_name='notification_records')
    op.drop_index(op.f('ix_notification_records_order_id'), table_name='notification_records')
    op.drop_index(op.f('ix_notification_records_tracking_number'), table_name='notification_records')
    op.drop_index(op.f('ix_notification_records_notification_id'), table_name='notification_records')
    op.drop_table('notification_records')

    # 删除运单注册表
    op.drop_index('ix_tracking_reg_status_created', table_name='tracking_registrations')
    op.drop_index('ix_tracking_reg_order_site', table_name='tracking_registrations')
    op.drop_index(op.f('ix_tracking_registrations_created_at'), table_name='tracking_registrations')
    op.drop_index(op.f('ix_tracking_registrations_status'), table_name='tracking_registrations')
    op.drop_index(op.f('ix_tracking_registrations_site'), table_name='tracking_registrations')
    op.drop_index(op.f('ix_tracking_registrations_order_id'), table_name='tracking_registrations')
    op.drop_index(op.f('ix_tracking_registrations_tracking_number'), table_name='tracking_registrations')
    op.drop_table('tracking_registrations')
