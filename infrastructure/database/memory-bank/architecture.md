# 架构说明

> **模块**: infrastructure/database/
> **功能**: PostgreSQL 数据库持久化模块
> **最后更新**: 2025-12-22
> **遵循规范**: CLAUDE.md 三层架构

---

## 文件结构

（每新增文件在此说明用途）

### 目标结构

```
infrastructure/database/
├── __init__.py              # 模块导出
├── connection.py            # 连接池管理
├── base.py                  # SQLAlchemy Base
├── models/                  # ORM 模型
│   ├── __init__.py
│   ├── agent.py            # AgentModel
│   ├── ticket.py           # TicketModel, TicketCommentModel, ...
│   ├── audit.py            # AuditLogModel
│   ├── session.py          # SessionArchiveModel
│   └── email.py            # EmailRecordModel
├── migrations/              # Alembic 迁移
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
├── converters.py            # Pydantic ↔ ORM 转换器
├── memory-bank/             # 文档
└── README.md
```

---

## 数据流

```
产品层 (products/)
    │
    ▼
服务层 (services/)
    │ 调用 Store 接口
    ▼
┌─────────────────────────────────────────────────┐
│            Store (TicketStore, etc.)            │
│                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    │
│  │   PostgreSQL    │◄───│     Redis       │    │
│  │   (持久化)      │    │   (缓存)        │    │
│  └─────────────────┘    └─────────────────┘    │
│            ▲                    ▲               │
│            │                    │               │
│     converters.py         直接存取             │
│     (Pydantic ↔ ORM)                           │
└─────────────────────────────────────────────────┘
    │
    ▼
基础设施层 (infrastructure/database/)
    │
    ▼
SQLAlchemy + PostgreSQL
```

---

## 关键设计决策

（记录重要的设计选择及原因）

### 1. 技术选型

| 决策 | 选择 | 原因 |
|------|------|------|
| 数据库 | PostgreSQL | 原生 JSONB 支持，适合现有 JSON 数据模型 |
| ORM | SQLAlchemy 2.0 | Python 生态最成熟，文档完善 |
| 迁移 | Alembic | SQLAlchemy 官方配套 |

### 2. 数据分层

| 数据类型 | 存储位置 | 原因 |
|---------|---------|------|
| 活跃会话 | Redis | 高频读写，需要低延迟 |
| 工单数据 | PostgreSQL | 需要持久化和复杂查询 |
| 审计日志 | PostgreSQL | 需要长期保存 |
| Shopify 缓存 | Redis | 纯缓存，TTL 过期 |

### 3. 双写策略

采用"先写 PostgreSQL，再写 Redis"策略：
- PostgreSQL 作为数据源
- Redis 作为缓存加速
- 保证数据一致性

---

## 已创建文件

| 文件 | 用途 | 创建步骤 |
|------|------|---------|
| `infrastructure/database/__init__.py` | 模块导出，暴露 Base、连接管理等公共接口 | Step 1 |
| `infrastructure/database/base.py` | SQLAlchemy 声明式基类 + TimestampMixin | Step 1 |
| `infrastructure/database/connection.py` | 连接池管理、会话工厂、健康检查 | Step 1 |
| `infrastructure/database/models/__init__.py` | ORM 模型导出 | Step 2 |
| `infrastructure/database/models/ticket.py` | 工单相关 ORM 模型（5 个表） | Step 2 |
| `infrastructure/database/models/agent.py` | 坐席账号 ORM 模型 | Step 3 |
| `infrastructure/database/models/audit.py` | 审计日志 ORM 模型 | Step 4 |
| `infrastructure/database/models/session.py` | 会话归档 ORM 模型 | Step 4 |
| `infrastructure/database/models/email.py` | 邮件记录 ORM 模型 | Step 4 |
| `infrastructure/database/migrations/alembic.ini` | Alembic 配置 | Step 5 |
| `infrastructure/database/migrations/env.py` | 迁移环境配置 | Step 5 |
| `infrastructure/database/migrations/script.py.mako` | 迁移脚本模板 | Step 5 |
| `infrastructure/database/migrations/versions/*.py` | 迁移版本脚本 | Step 5 |
| `infrastructure/database/converters.py` | Pydantic ↔ ORM 转换器 | Step 6 |
| `infrastructure/bootstrap/database.py` | Bootstrap 数据库集成 | Step 7 |

---

## 文件详细说明

### infrastructure/database/base.py

**用途:** 定义 SQLAlchemy ORM 基类和通用 Mixin

**主要组件:**
- `Base` - SQLAlchemy declarative_base()，所有 ORM 模型的父类
- `TimestampMixin` - 自动添加 created_at 和 updated_at 字段

**依赖关系:**
- 依赖: sqlalchemy
- 被依赖: connection.py, 所有 ORM 模型

---

### infrastructure/database/connection.py

**用途:** 数据库连接池管理和会话生命周期管理

**主要函数:**
- `DatabaseConfig` - 数据库配置类，支持环境变量加载
- `init_database()` - 初始化数据库连接（单例模式）
- `get_engine()` - 获取 SQLAlchemy Engine
- `get_db_session()` - 获取数据库会话（上下文管理器）
- `check_connection()` - 连接健康检查
- `get_pool_status()` - 获取连接池状态
- `create_all_tables()` - 创建所有表（开发用）
- `drop_all_tables()` - 删除所有表（测试用）
- `reset()` - 重置连接（测试用）

**依赖关系:**
- 依赖: base.py, sqlalchemy, os
- 被依赖: services 层的 Store 类

---

### infrastructure/database/__init__.py

**用途:** 模块公共接口导出

**导出内容:**
- `Base`, `TimestampMixin` - ORM 基类
- `DatabaseConfig` - 配置类
- `init_database`, `get_engine`, `get_db_session` - 连接管理
- `create_all_tables`, `drop_all_tables` - 表管理
- `check_connection`, `get_pool_status`, `reset` - 工具函数

---

### infrastructure/database/models/ticket.py

**用途:** 工单相关 ORM 模型定义

**主要模型:**
- `TicketModel` - 工单主表（23 字段）
  - 基本信息：ticket_id, title, description, session_name
  - 分类状态：ticket_type, status, priority
  - 人员：created_by, assigned_agent_id
  - 时间戳：created_at, updated_at, closed_at, resolved_at 等
  - JSONB 字段：customer, extra_data
- `TicketCommentModel` - 工单评论表
- `TicketAttachmentModel` - 工单附件表
- `TicketStatusHistoryModel` - 工单状态变更历史
- `TicketAssignmentModel` - 工单指派历史

**表关系:**
```
TicketModel (1) ──┬── (N) TicketCommentModel
                  ├── (N) TicketAttachmentModel
                  ├── (N) TicketStatusHistoryModel
                  └── (N) TicketAssignmentModel
```

**依赖关系:**
- 依赖: base.py (Base, TimestampMixin)
- 被依赖: converters.py, services/ticket/

---

### services/ticket/store.py (修改)

**用途:** 工单存储管理（支持 PostgreSQL + Redis 双写）

**主要改动:**
- `__init__(redis_client, enable_postgres)` - 新增 enable_postgres 参数
- `enable_postgres()` / `disable_postgres()` - 运行时启用/禁用 PG 双写
- `_save_ticket(ticket)` - 实现双写逻辑（先 PG 后 Redis/内存）
- `_pg_save_ticket(ticket)` - PostgreSQL 写入实现

**双写策略:**
1. 先写入 PostgreSQL（主存储）
2. 再写入 Redis/内存（缓存）
3. Redis 失败重试一次，仍失败记录日志但不阻塞

**依赖关系:**
- 依赖: infrastructure.database.get_db_session
- 依赖: infrastructure.database.models (TicketModel 等)
- 依赖: infrastructure.database.converters (ticket_to_orm 等)

---

### infrastructure/security/agent_auth.py (修改)

**用途:** 坐席账号管理（支持 PostgreSQL + Redis 双写）

**主要改动:**
- `AgentManager.__init__(redis_store, enable_postgres)` - 新增 enable_postgres 参数
- `enable_postgres()` / `disable_postgres()` - 运行时启用/禁用 PG 双写
- `_store_agent_record(agent)` - 实现双写逻辑
- `_pg_save_agent(agent)` - PostgreSQL 写入实现
- `_pg_delete_agent(agent_id)` - PostgreSQL 删除实现
- `delete_agent(username)` - 支持双写删除

**双写策略:**
1. 先写入 PostgreSQL（主存储）
2. 再写入 Redis（缓存）
3. Redis 失败重试一次，仍失败记录日志但不阻塞
4. 认证操作仍走 Redis（高频操作，需要低延迟）

**依赖关系:**
- 依赖: infrastructure.database.get_db_session
- 依赖: infrastructure.database.models.AgentModel
- 依赖: infrastructure.database.converters.agent_to_orm

---

### services/ticket/audit.py (修改)

**用途:** 审计日志存储（支持 PostgreSQL + Redis/内存）

**主要改动:**
- `AuditLogStore.__init__(redis_client, max_logs, enable_postgres)` - 新增 enable_postgres 参数
- `enable_postgres()` / `disable_postgres()` - 运行时启用/禁用 PG
- `add_log()` - 先写入 PostgreSQL 再写入缓存
- `_pg_add_log(log)` - PostgreSQL 写入实现
- `list_logs(ticket_id, limit)` - 优先从 PostgreSQL 查询
- `_pg_list_logs(ticket_id, limit)` - PostgreSQL 查询实现

**查询策略:**
1. 优先从 PostgreSQL 查询
2. PostgreSQL 失败时降级到 Redis/内存
3. 保证服务可用性

**依赖关系:**
- 依赖: infrastructure.database.get_db_session
- 依赖: infrastructure.database.models.AuditLogModel
- 依赖: infrastructure.database.converters (audit_log_to_orm, audit_log_from_orm)

---

### services/email/service.py (修改)

**用途:** 邮件发送服务（支持 PostgreSQL 记录）

**主要改动:**
- `EmailService.__init__(config, enable_postgres)` - 新增 enable_postgres 参数
- `enable_postgres()` / `disable_postgres()` - 运行时启用/禁用记录
- `send_email()` - 新增 email_type, related_id, metadata 参数
- `_record_email()` - 新增方法，记录邮件到 PostgreSQL

**依赖关系:**
- 依赖: infrastructure.database.get_db_session
- 依赖: infrastructure.database.models.EmailRecordModel

---

### services/session/archive.py (新建)

**用途:** 会话归档服务

**主要组件:**
- `SessionArchiveService` - 会话归档服务类
- `archive_session()` - 归档会话到 PostgreSQL
- `get_archived_session()` - 查询单个归档
- `list_archived_sessions()` - 列表查询（支持过滤）
- `get_archive_service()` - 获取全局实例

**依赖关系:**
- 依赖: infrastructure.database.get_db_session
- 依赖: infrastructure.database.models.SessionArchiveModel

---

## 模块完成状态

| 步骤 | 内容 | 状态 |
|------|------|------|
| Step 1 | PostgreSQL 安装与模块骨架 | ✅ 完成 |
| Step 2 | 核心 ORM 模型 - 工单 | ✅ 完成 |
| Step 3 | 核心 ORM 模型 - 坐席 | ✅ 完成 |
| Step 4 | 扩展 ORM 模型 | ✅ 完成 |
| Step 5 | Alembic 迁移配置 | ✅ 完成 |
| Step 6 | Pydantic ↔ ORM 转换器 | ✅ 完成 |
| Step 7 | Bootstrap 集成 | ✅ 完成 |
| Step 8 | TicketStore 双写改造 | ✅ 完成 |
| Step 9 | AgentManager 双写改造 | ✅ 完成 |
| Step 10 | 审计日志改造 | ✅ 完成 |
| Step 11 | 邮件发送记录与会话归档 | ✅ 完成 |
| Step 12 | 测试与文档更新 | ✅ 完成 |
