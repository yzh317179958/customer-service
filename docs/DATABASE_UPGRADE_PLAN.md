# Fiido 智能服务平台 - PostgreSQL 数据库架构升级计划

> **版本**: v1.0
> **制定日期**: 2025-12-22
> **状态**: 待实施（客服工作台完成后执行）
> **预计工作量**: 13-17 个工作日

---

## 一、项目概述

### 1.1 目标
为 Fiido 智能服务平台引入 PostgreSQL 关系型数据库，实现核心业务数据的持久化存储，解决当前纯 Redis 存储的数据丢失风险。

### 1.2 当前存储架构问题

| 数据类型 | 当前存储 | 问题 |
|----------|----------|------|
| 会话状态 | Redis (24h TTL) | 会话历史丢失，无法归档分析 |
| 工单数据 | Redis/内存 | 重启丢失，无持久化 |
| 坐席账号 | Redis (365d TTL) | 无法审计，无历史追踪 |
| 审计日志 | Redis (List) | 数量有限，无法长期保存 |
| Shopify 订单 | Redis 缓存 | 仅缓存，符合预期 |
| 邮件发送 | 无记录 | 需要新增 |

### 1.3 技术选型

| 组件 | 选择 | 理由 |
|------|------|------|
| 数据库 | PostgreSQL 15+ | 原生 JSONB 支持，适合当前 JSON 数据模型 |
| ORM | SQLAlchemy 2.0 | Python 生态最成熟，功能强大，社区支持好 |
| 迁移工具 | Alembic | SQLAlchemy 官方配套，版本管理可靠 |
| Redis | 保留 | 继续用于热数据缓存、实时队列 |

### 1.4 目标架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Redis (热数据层)                          │
│  - 活跃会话状态 (24h TTL)                                    │
│  - Shopify 订单缓存 (5分钟~48小时)                           │
│  - SSE 消息队列                                             │
│  - 分布式锁、速率限制                                        │
└─────────────────────────────────────────────────────────────┘
                              ↓ 归档/同步
┌─────────────────────────────────────────────────────────────┐
│                PostgreSQL (持久化层)                         │
│  - 工单数据（完整生命周期）                                   │
│  - 坐席账号                                                 │
│  - 审计日志                                                 │
│  - 已关闭会话归档                                            │
│  - 邮件发送记录                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、数据库表设计

### 2.1 核心表清单

| 表名 | 用途 | 主要字段 |
|------|------|---------|
| `agents` | 坐席账号 | id, username, password_hash, role, status, skills(JSONB) |
| `tickets` | 工单 | id, ticket_id, title, status, priority, customer(JSONB) |
| `ticket_comments` | 工单评论 | id, ticket_id(FK), content, author_id, type |
| `ticket_attachments` | 工单附件 | id, ticket_id(FK), filename, stored_path, size |
| `ticket_status_history` | 状态历史 | id, ticket_id(FK), from_status, to_status, changed_by |
| `audit_logs` | 审计日志 | id, event_type, operator_id, details(JSONB) |
| `session_archives` | 会话归档 | id, session_name, user_profile(JSONB), history(JSONB) |
| `email_records` | 邮件记录 | id, recipients(JSONB), subject, status |

### 2.2 详细表结构

#### 2.2.1 坐席表 (agents)

```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(64) UNIQUE NOT NULL,  -- 业务ID: agent_xxx
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'agent',  -- agent/admin
    status VARCHAR(20) NOT NULL DEFAULT 'offline',
    status_note TEXT,
    max_sessions INT NOT NULL DEFAULT 5,
    avatar_url TEXT,
    skills JSONB DEFAULT '[]',  -- 技能标签数组

    status_updated_at TIMESTAMPTZ,
    last_active_at TIMESTAMPTZ,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agents_username ON agents(username);
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_role ON agents(role);
```

#### 2.2.2 工单表 (tickets)

```sql
CREATE TABLE tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id VARCHAR(50) UNIQUE NOT NULL,  -- TKT-YYYYMMDDHHMMSS-XXXXXX
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    session_name VARCHAR(255),

    ticket_type VARCHAR(20) NOT NULL DEFAULT 'after_sale',
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',

    created_by VARCHAR(64) NOT NULL,
    created_by_name VARCHAR(100),
    assigned_agent_id VARCHAR(64),
    assigned_agent_name VARCHAR(100),

    customer JSONB,  -- {name, email, phone, country}
    metadata JSONB DEFAULT '{}',

    first_response_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    archived_at TIMESTAMPTZ,

    reopened_count INT DEFAULT 0,
    reopened_at TIMESTAMPTZ,
    reopened_by VARCHAR(64),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_priority ON tickets(priority);
CREATE INDEX idx_tickets_assigned ON tickets(assigned_agent_id);
CREATE INDEX idx_tickets_session ON tickets(session_name);
CREATE INDEX idx_tickets_created ON tickets(created_at DESC);
CREATE INDEX idx_tickets_customer_email ON tickets((customer->>'email'));
```

#### 2.2.3 工单状态历史表

```sql
CREATE TABLE ticket_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    history_id VARCHAR(50) NOT NULL,
    ticket_id UUID NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    from_status VARCHAR(30),
    to_status VARCHAR(30) NOT NULL,
    changed_by VARCHAR(64) NOT NULL,
    change_reason VARCHAR(255),
    comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ticket_history_ticket ON ticket_status_history(ticket_id);
```

#### 2.2.4 工单评论表

```sql
CREATE TABLE ticket_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    comment_id VARCHAR(50) UNIQUE NOT NULL,
    ticket_id UUID NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    author_id VARCHAR(64) NOT NULL,
    author_name VARCHAR(100),
    comment_type VARCHAR(20) NOT NULL DEFAULT 'internal',
    mentions JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ticket_comments_ticket ON ticket_comments(ticket_id);
```

#### 2.2.5 工单附件表

```sql
CREATE TABLE ticket_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attachment_id VARCHAR(50) UNIQUE NOT NULL,
    ticket_id UUID NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    stored_path TEXT NOT NULL,
    size BIGINT NOT NULL,
    content_type VARCHAR(100),
    uploader_id VARCHAR(64) NOT NULL,
    uploader_name VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ticket_attachments_ticket ON ticket_attachments(ticket_id);
```

#### 2.2.6 审计日志表

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_id VARCHAR(50) NOT NULL,
    ticket_id VARCHAR(50),
    event_type VARCHAR(50) NOT NULL,
    operator_id VARCHAR(64) NOT NULL,
    operator_name VARCHAR(100),
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_created ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_ticket ON audit_logs(ticket_id);
CREATE INDEX idx_audit_operator ON audit_logs(operator_id);
CREATE INDEX idx_audit_event_type ON audit_logs(event_type);
```

#### 2.2.7 会话归档表

```sql
CREATE TABLE session_archives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_name VARCHAR(255) UNIQUE NOT NULL,
    conversation_id VARCHAR(255),
    status VARCHAR(30) NOT NULL,

    user_profile JSONB NOT NULL,
    history JSONB NOT NULL DEFAULT '[]',
    message_count INT NOT NULL DEFAULT 0,
    escalation JSONB,
    assigned_agent JSONB,
    priority JSONB,
    ticket_ids JSONB DEFAULT '[]',

    session_created_at TIMESTAMPTZ NOT NULL,
    session_updated_at TIMESTAMPTZ NOT NULL,
    closed_at TIMESTAMPTZ NOT NULL,
    archived_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archive_reason VARCHAR(100),
    archived_by VARCHAR(64)
);

CREATE INDEX idx_session_archives_closed ON session_archives(closed_at DESC);
CREATE INDEX idx_session_archives_email ON session_archives((user_profile->>'email'));
```

#### 2.2.8 邮件发送记录表

```sql
CREATE TABLE email_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id VARCHAR(100) UNIQUE,
    session_name VARCHAR(255),
    ticket_id VARCHAR(50),

    recipients JSONB NOT NULL,
    subject VARCHAR(500) NOT NULL,
    template_type VARCHAR(50),
    html_content TEXT,

    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    retry_count INT DEFAULT 0,

    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_email_records_status ON email_records(status);
CREATE INDEX idx_email_records_session ON email_records(session_name);
CREATE INDEX idx_email_records_created ON email_records(created_at DESC);
```

---

## 三、模块结构设计

### 3.1 infrastructure/database 目录结构

```
infrastructure/database/
├── __init__.py              # 模块导出
├── connection.py            # 连接池管理（DatabaseConfig, init_database, get_session）
├── base.py                  # SQLAlchemy Base 定义
├── models/                  # ORM 模型
│   ├── __init__.py
│   ├── agent.py            # AgentModel
│   ├── ticket.py           # TicketModel, TicketCommentModel, ...
│   ├── audit.py            # AuditLogModel
│   ├── session.py          # SessionArchiveModel
│   └── email.py            # EmailRecordModel
├── repositories/            # 数据访问层（Repository 模式）
│   ├── __init__.py
│   ├── base.py             # BaseRepository
│   ├── agent.py            # AgentRepository
│   ├── ticket.py           # TicketRepository
│   └── audit.py            # AuditLogRepository
├── migrations/              # Alembic 迁移
│   ├── env.py
│   ├── alembic.ini
│   └── versions/
├── converters.py            # Pydantic ↔ ORM 转换器
└── README.md
```

### 3.2 Pydantic 与 ORM 模型关系

```
services/ticket/models.py (Pydantic - 保持不变)
       ↑↓ converters.py 转换
infrastructure/database/models/ticket.py (SQLAlchemy ORM)
       ↑↓
services/ticket/store.py (添加 PostgreSQL 支持)
```

---

## 四、数据同步策略

| 数据类型 | 写入策略 | 读取策略 |
|---------|---------|---------|
| 工单 | 双写（PG 优先，Redis 缓存） | PostgreSQL |
| 坐席账号 | 双写（PG + Redis） | 认证走 Redis，管理走 PG |
| 审计日志 | 仅写 PostgreSQL | PostgreSQL |
| 邮件记录 | 仅写 PostgreSQL | PostgreSQL |
| 活跃会话 | 仅写 Redis | Redis |
| 会话归档 | 关闭时异步迁移到 PG | PostgreSQL |

---

## 五、环境配置

### 5.1 新增环境变量

```bash
# .env 新增配置
DATABASE_URL=postgresql://fiido:password@localhost:5432/fiido_db
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_ECHO=false
```

### 5.2 依赖新增

```txt
# requirements.txt 新增
SQLAlchemy>=2.0.0
psycopg2-binary>=2.9.0
alembic>=1.12.0
```

---

## 六、分步实施计划

### Step 1: 基础设施准备
- 创建 `infrastructure/database/` 模块骨架
- 实现 `connection.py` 连接池管理
- 实现 `base.py` SQLAlchemy Base
- 配置 Alembic 迁移环境

### Step 2: 核心 ORM 模型 - 工单
- 实现 `models/ticket.py`（TicketModel, TicketCommentModel, TicketAttachmentModel, TicketStatusHistoryModel）
- 创建初始迁移脚本
- 实现 `converters.py` 中的工单转换器

### Step 3: 核心 ORM 模型 - 坐席
- 实现 `models/agent.py`（AgentModel）
- 添加迁移脚本

### Step 4: 扩展 ORM 模型
- 实现 `models/audit.py`（AuditLogModel）
- 实现 `models/session.py`（SessionArchiveModel）
- 实现 `models/email.py`（EmailRecordModel）
- 添加迁移脚本

### Step 5: Bootstrap 集成
- 修改 `infrastructure/bootstrap/factory.py`，添加 DATABASE 组件
- 实现数据库初始化逻辑
- 更新 `services/bootstrap/__init__.py`

### Step 6: TicketStore 双写改造
- 修改 `services/ticket/store.py`
- 添加 PostgreSQL 写入逻辑
- 保持 Redis 缓存逻辑
- 切换查询到 PostgreSQL

### Step 7: AgentManager 双写改造
- 修改 `infrastructure/security/agent_auth.py`
- 添加 PostgreSQL 持久化
- 认证仍走 Redis，管理走 PG

### Step 8: 审计日志改造
- 修改 `services/ticket/audit.py`
- 切换到 PostgreSQL 存储

### Step 9: 邮件发送记录
- 修改 `services/email/` 模块
- 添加邮件发送记录

### Step 10: 会话归档服务
- 实现会话归档逻辑
- 添加定时任务（已关闭会话迁移到 PG）

### Step 11: 历史数据迁移
- 编写迁移脚本（Redis → PostgreSQL）
- 执行数据迁移
- 验证数据完整性

### Step 12: 测试与文档
- 全面测试
- 更新 memory-bank 文档
- 部署指南

---

## 七、扩展性设计

### 7.1 当前设计支持的扩展路径

| 扩展阶段 | 操作 | 影响范围 |
|---------|------|---------|
| 垂直扩展 | 增加服务器配置 | 配置调整 |
| 读写分离 | PG 主从复制 | 连接配置 |
| 分区 | 审计日志按月分区 | 表结构 |
| 分库 | 按租户/业务分库 | 架构改动 |

### 7.2 设计原则

1. **Repository 模式**：数据访问逻辑集中在 Store/Repository 类，便于后期切换
2. **接口不变**：服务层对外接口保持不变，内部实现透明切换
3. **配置外部化**：所有数据库参数通过环境变量配置

---

## 八、关键文件清单

### 需要修改的现有文件

| 文件 | 改动说明 |
|------|---------|
| `infrastructure/bootstrap/factory.py` | 添加 DATABASE 组件 |
| `infrastructure/bootstrap/__init__.py` | 导出数据库组件 |
| `services/bootstrap/__init__.py` | 注册数据库依赖 |
| `services/ticket/store.py` | 添加 PostgreSQL 支持 |
| `infrastructure/security/agent_auth.py` | 添加 PostgreSQL 持久化 |
| `services/ticket/audit.py` | 切换到 PostgreSQL |
| `services/email/service.py` | 添加邮件记录 |
| `.env` | 添加数据库配置 |
| `requirements.txt` | 添加依赖 |

### 需要新建的文件

| 文件 | 说明 |
|------|------|
| `infrastructure/database/__init__.py` | 模块导出 |
| `infrastructure/database/connection.py` | 连接管理 |
| `infrastructure/database/base.py` | SQLAlchemy Base |
| `infrastructure/database/models/*.py` | ORM 模型 |
| `infrastructure/database/repositories/*.py` | 数据访问层 |
| `infrastructure/database/converters.py` | 模型转换器 |
| `infrastructure/database/migrations/*` | Alembic 迁移 |
| `infrastructure/database/README.md` | 模块文档 |

---

## 九、风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| 数据迁移丢失 | 先双写，验证后再切换 |
| 性能下降 | 保持 Redis 热数据缓存 |
| 迁移脚本失败 | 分批迁移，支持回滚 |
| 连接池耗尽 | 合理配置 pool_size，添加监控 |

---

## 十、预估工作量

| 阶段 | 预估时间 |
|------|---------|
| Step 1-4: 基础设施 + 模型 | 3-4 天 |
| Step 5: Bootstrap 集成 | 1 天 |
| Step 6-8: 核心改造 | 4-5 天 |
| Step 9-10: 扩展功能 | 2-3 天 |
| Step 11-12: 迁移与测试 | 3-4 天 |
| **总计** | **13-17 天** |

---

## 十一、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-22 | 初始版本，完成架构设计和实施计划 |

---

## 十二、实施前提条件

- [ ] 客服工作台（agent_workbench）开发完成
- [ ] 现有功能稳定运行
- [ ] 用户确认开始实施
