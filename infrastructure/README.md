# Infrastructure 基础设施层规范

> **层级定位**：底层技术组件，无业务逻辑
> **最后更新**：2025-12-23
> **文档版本**：v2.0

---

## 一、层级职责

基础设施层提供底层技术能力：

- 纯技术封装，无业务逻辑
- 被 services 和 products 依赖
- 提供通用的技术组件
- 支持 PostgreSQL + Redis 双存储

---

## 二、当前组件清单

| 组件 | 目录 | 状态 | 说明 |
|------|------|------|------|
| 启动引导 | bootstrap/ | ✅ 已完成 | 组件工厂、依赖注入、SSE |
| 数据库 | database/ | ✅ 已完成 | PostgreSQL + Redis 双写 |
| 安全认证 | security/ | ✅ 已完成 | JWT 签名、坐席认证 |
| 监控 | monitoring/ | ✅ 已完成 | CDN 健康检查 |
| 定时任务 | scheduler/ | ⚙️ 待完善 | APScheduler 封装 |
| 日志 | logging/ | ⚙️ 待完善 | 日志配置 |

---

## 三、数据库组件详情

### 3.1 目录结构

```
infrastructure/database/
├── __init__.py              # 导出公开接口
├── connection.py            # 连接池管理（PG + Redis）
├── converters.py            # Pydantic ↔ ORM 转换器
├── models/                  # ORM 模型
│   ├── __init__.py
│   ├── base.py             # 基类
│   ├── ticket.py           # 工单相关表
│   ├── agent.py            # 坐席表
│   ├── session.py          # 会话归档表
│   ├── email.py            # 邮件记录表
│   └── tracking.py         # 物流追踪表
└── migrations/              # Alembic 数据库迁移
    ├── env.py
    ├── alembic.ini
    └── versions/
```

### 3.2 数据表清单

| 表名 | 模型 | 说明 |
|------|------|------|
| tickets | Ticket | 工单主表 |
| ticket_comments | TicketComment | 工单评论 |
| ticket_attachments | TicketAttachment | 工单附件 |
| ticket_status_history | TicketStatusHistory | 状态变更历史 |
| ticket_assignments | TicketAssignment | 工单分配记录 |
| agents | Agent | 坐席账号 |
| audit_logs | AuditLog | 审计日志 |
| session_archives | SessionArchive | 会话归档 |
| email_records | EmailRecord | 邮件发送记录 |
| tracking_registrations | TrackingRegistration | 运单注册记录 |
| notification_records | NotificationRecord | 通知发送记录 |

### 3.3 使用示例

```python
from infrastructure.database import (
    get_async_session,
    get_redis_client,
)
from infrastructure.database.models import Ticket, Agent

# PostgreSQL 异步会话
async with get_async_session() as session:
    result = await session.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()

# Redis 客户端
redis = get_redis_client()
await redis.setex("key", 3600, "value")
```

---

## 四、依赖规则

### 4.1 允许的依赖

```python
# ✅ 可以依赖 Python 标准库和第三方库
import redis
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ✅ 可以依赖同层其他组件
from infrastructure.log import logger
```

### 4.2 禁止的依赖

```python
# ❌ 禁止依赖 services 层
from services.shopify import xxx  # 禁止！

# ❌ 禁止依赖 products 层
from products.ai_chatbot import xxx  # 禁止！
```

---

## 五、组件目录结构

```
infrastructure/xxx/
├── __init__.py          # 模块初始化，导出公开接口
├── README.md            # 【必须】组件规范文档
├── client.py            # 客户端/连接管理
├── config.py            # 配置（如有）
└── tests/               # 单元测试
```

---

## 六、开发规范

### 6.1 设计原则

| 原则 | 说明 |
|------|------|
| 无业务逻辑 | 只做技术封装 |
| 简单通用 | 接口简洁，易于使用 |
| 可配置 | 通过环境变量配置 |
| 高可用 | 连接池、重试、超时 |

### 6.2 数据库连接模板

```python
# connection.py 示例
import os
from typing import Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
import redis.asyncio as redis

# PostgreSQL 配置
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://...")

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

# 会话工厂
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session

# Redis 配置
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_redis_client: Optional[redis.Redis] = None

def get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL)
    return _redis_client
```

### 6.3 ORM 模型模板

```python
# models/xxx.py 示例
from sqlalchemy import Column, Integer, String, Float, Boolean, Text
from sqlalchemy.dialects.postgresql import JSONB
from .base import Base

class Xxx(Base):
    __tablename__ = "xxx"
    __table_args__ = {"comment": "表注释"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="名称")
    status = Column(String(20), nullable=False, default="pending")
    data = Column(JSONB, nullable=True)
    created_at = Column(Float, nullable=False)
    updated_at = Column(Float, nullable=False)
```

### 6.4 Alembic 迁移命令

```bash
# 创建新迁移
cd infrastructure/database
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

---

## 七、安全认证组件

### 7.1 JWT 签名

```python
from infrastructure.security import create_coze_jwt

# 创建 Coze API 的 JWT Token
token = create_coze_jwt()
```

### 7.2 坐席认证

```python
from infrastructure.security import require_agent_auth, get_current_agent

@router.get("/protected")
async def protected_endpoint(agent: Agent = Depends(get_current_agent)):
    return {"agent_id": agent.id}
```

---

## 八、测试要求

- 每个组件必须有单元测试
- 测试连接、超时、异常处理
- Mock 外部依赖

---

## 九、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0 | 2025-12-23 | 更新组件清单状态，添加数据库详细说明、ORM 模板、迁移命令 |
| v1.0 | 2025-12-18 | 初始版本 |
