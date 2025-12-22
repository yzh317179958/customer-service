# PostgreSQL 数据库模块

> **位置**: infrastructure/database/
> **功能**: PostgreSQL 数据库持久化层
> **版本**: v7.5.10
> **最后更新**: 2025-12-22

---

## 概述

本模块提供 PostgreSQL 数据库支持，采用 SQLAlchemy 2.0 ORM 实现。支持与 Redis 双写模式，确保数据持久化的同时保持高性能。

---

## 技术栈

| 组件 | 版本 | 说明 |
|------|------|------|
| PostgreSQL | 14.x | 关系型数据库 |
| SQLAlchemy | 2.0+ | ORM 框架（同步模式） |
| psycopg2-binary | 2.9+ | PostgreSQL 驱动 |
| Alembic | 1.12+ | 数据库迁移工具 |

---

## 目录结构

```
infrastructure/database/
├── __init__.py              # 模块导出
├── base.py                  # SQLAlchemy Base 类
├── connection.py            # 连接池管理
├── converters.py            # Pydantic ↔ ORM 转换器
├── README.md                # 本文件
├── models/                  # ORM 模型
│   ├── __init__.py
│   ├── ticket.py           # 工单相关（5 个模型）
│   ├── agent.py            # 坐席账号
│   ├── audit.py            # 审计日志
│   ├── session.py          # 会话归档
│   └── email.py            # 邮件记录
├── migrations/              # Alembic 迁移
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
└── memory-bank/             # 开发文档
```

---

## 数据表

| 表名 | 模型 | 说明 |
|------|------|------|
| tickets | TicketModel | 工单主表 |
| ticket_comments | TicketCommentModel | 工单评论 |
| ticket_attachments | TicketAttachmentModel | 工单附件 |
| ticket_status_history | TicketStatusHistoryModel | 状态变更历史 |
| ticket_assignments | TicketAssignmentModel | 指派历史 |
| agents | AgentModel | 坐席账号 |
| audit_logs | AuditLogModel | 审计日志 |
| session_archives | SessionArchiveModel | 会话归档 |
| email_records | EmailRecordModel | 邮件发送记录 |

---

## 使用方法

### 初始化数据库

```python
from infrastructure.database import init_database

# 初始化连接池
init_database()
```

### 获取数据库会话

```python
from infrastructure.database import get_db_session

with get_db_session() as session:
    # 执行查询
    tickets = session.query(TicketModel).all()
```

### 使用 ORM 模型

```python
from infrastructure.database.models import TicketModel, AgentModel

# 创建记录
with get_db_session() as session:
    ticket = TicketModel(
        ticket_id='TKT-001',
        title='测试工单',
        created_by='admin'
    )
    session.add(ticket)
```

### Pydantic - ORM 转换

```python
from services.ticket.models import Ticket
from infrastructure.database.converters import ticket_to_orm, ticket_from_orm

# Pydantic -> ORM
orm_model = ticket_to_orm(pydantic_ticket)

# ORM -> Pydantic
pydantic_ticket = ticket_from_orm(orm_model)
```

---

## 双写策略

本模块采用 **PostgreSQL 主存储 + Redis 缓存** 的双写模式：

```
写入流程：
1. 先写入 PostgreSQL（主存储）
2. 再写入 Redis（缓存）
3. Redis 失败重试一次，仍失败则记录日志但不阻塞

读取流程：
1. 优先从 PostgreSQL 查询
2. PostgreSQL 失败时降级到 Redis/内存
```

### 启用双写

```python
# TicketStore
from services.ticket.store import TicketStore
store = TicketStore(redis_client=redis, enable_postgres=True)

# AgentManager
from infrastructure.security.agent_auth import AgentManager
manager = AgentManager(redis_store=redis_store, enable_postgres=True)

# AuditLogStore
from services.ticket.audit import AuditLogStore
audit = AuditLogStore(redis_client=redis, enable_postgres=True)
```

---

## 连接池配置

环境变量（`.env`）：

```bash
DATABASE_URL=postgresql://fiido:fiido123@localhost:5432/fiido_db
DB_POOL_SIZE=10       # 连接池大小
DB_MAX_OVERFLOW=20    # 最大溢出连接数
DB_POOL_TIMEOUT=30    # 获取连接超时（秒）
DB_POOL_RECYCLE=1800  # 连接回收时间（秒）
DB_ECHO=false         # 是否打印 SQL
```

---

## 数据库迁移

### 生成迁移脚本

```bash
cd /home/yzh/AI客服/鉴权
alembic -c infrastructure/database/migrations/alembic.ini revision --autogenerate -m "描述"
```

### 执行迁移

```bash
alembic -c infrastructure/database/migrations/alembic.ini upgrade head
```

### 回滚迁移

```bash
alembic -c infrastructure/database/migrations/alembic.ini downgrade -1
```

---

## 健康检查

```python
from infrastructure.database import check_connection, get_pool_status

# 检查连接
is_ok = check_connection()

# 获取连接池状态
status = get_pool_status()
# {'pool_size': 10, 'checked_out': 1, 'overflow': 0, 'invalid': 0}
```

---

## 依赖关系

```
infrastructure/database/
       ↑
       │ 被调用
       │
services/ticket/store.py      # 工单存储（双写）
services/ticket/audit.py      # 审计日志（双写）
services/session/archive.py   # 会话归档
services/email/service.py     # 邮件记录
infrastructure/security/agent_auth.py  # 坐席管理（双写）
```

---

## 注意事项

1. **同步模式**: 本模块使用 SQLAlchemy 同步模式（psycopg2），在 async 函数中需使用 `run_in_executor`
2. **会话管理**: 使用 `with get_db_session()` 上下文管理器自动处理提交和回滚
3. **连接池**: 生产环境建议 pool_size=10, max_overflow=20
4. **迁移安全**: 修改模型后必须生成并执行迁移脚本

---

## 开发文档

详细的开发进度和架构说明请参阅 `memory-bank/` 目录：
- `prd.md` - 需求文档
- `implementation-plan.md` - 实现计划
- `progress.md` - 进度追踪
- `architecture.md` - 架构说明

---

## 文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0 | 2025-12-22 | PostgreSQL 模块完成，包含 9 个 ORM 模型、双写策略、Alembic 迁移 |
| v1.0 | 2025-12-18 | 初始版本（Redis 占位） |
