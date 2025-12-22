# -*- coding: utf-8 -*-
"""
坐席相关 ORM 模型

包含：
- AgentModel: 坐席账号表
"""

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, Index
)
from sqlalchemy.dialects.postgresql import JSONB

from ..base import Base, TimestampMixin


class AgentModel(Base, TimestampMixin):
    """坐席账号表"""
    __tablename__ = "agents"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(50), unique=True, nullable=False, index=True, comment="坐席业务ID")

    # 认证信息
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")

    # 基本信息
    name = Column(String(100), nullable=False, comment="显示名称")
    avatar_url = Column(String(500), nullable=True, comment="头像URL")

    # 角色与权限
    role = Column(String(20), nullable=False, default="agent", index=True, comment="角色: agent/admin")

    # 状态
    status = Column(String(20), nullable=False, default="offline", index=True, comment="状态: online/busy/break/lunch/training/offline")
    status_note = Column(String(200), nullable=True, comment="状态说明")
    status_updated_at = Column(Float, nullable=True, comment="状态更新时间")

    # 活跃时间
    last_active_at = Column(Float, nullable=True, comment="最近活跃时间")
    last_login_at = Column(Float, nullable=True, comment="最后登录时间")

    # 配置
    max_sessions = Column(Integer, nullable=False, default=5, comment="最大同时服务会话数")

    # 技能标签 (JSONB 存储)
    # 格式: [{"category": "ebike", "level": "senior", "tags": ["battery", "motor"]}]
    skills = Column(JSONB, nullable=True, default=list, comment="技能标签列表")

    # 索引
    __table_args__ = (
        Index("ix_agents_role_status", "role", "status"),
        {"comment": "坐席账号表"},
    )

    def __repr__(self):
        return f"<Agent(agent_id='{self.agent_id}', username='{self.username}', role='{self.role}')>"
