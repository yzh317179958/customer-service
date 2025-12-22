# -*- coding: utf-8 -*-
"""
基础设施 - 数据库基类模块

定义 SQLAlchemy ORM 基类和通用 Mixin。
"""

import time
from sqlalchemy import Column, Float
from sqlalchemy.orm import declarative_base


# SQLAlchemy 声明式基类
Base = declarative_base()


class TimestampMixin:
    """
    时间戳 Mixin

    自动添加 created_at 和 updated_at 字段。
    使用 Float 存储 Unix 时间戳，与 Pydantic 模型保持一致。
    """
    created_at = Column(
        Float,
        nullable=False,
        default=time.time,
        comment="创建时间(Unix时间戳)"
    )
    updated_at = Column(
        Float,
        nullable=False,
        default=time.time,
        onupdate=time.time,
        comment="更新时间(Unix时间戳)"
    )
