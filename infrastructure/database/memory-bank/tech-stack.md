# PostgreSQL 数据库模块 - 技术栈

> **模块位置**: infrastructure/database/
> **创建日期**: 2025-12-22

---

## 1. 复用现有技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 基础设施层 | infrastructure/bootstrap | 组件工厂、依赖注入 |
| 基础设施层 | infrastructure/security | JWT 认证、坐席管理 |
| 服务层 | services/ticket | 工单服务（需双写改造） |
| 服务层 | services/session | 会话服务（归档功能） |
| 服务层 | services/email | 邮件服务（记录功能） |
| 数据存储 | Redis | 保留用于热数据缓存 |

---

## 2. 新增依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| SQLAlchemy | >= 2.0.0 | ORM 框架，Python 生态最成熟 |
| psycopg2-binary | >= 2.9.0 | PostgreSQL 驱动 |
| alembic | >= 1.12.0 | 数据库迁移管理 |

**requirements.txt 新增：**
```txt
SQLAlchemy>=2.0.0
psycopg2-binary>=2.9.0
alembic>=1.12.0
```

---

## 3. 数据存储方案

### 3.1 数据分层架构

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

### 3.2 数据同步策略

| 数据类型 | 写入策略 | 读取策略 |
|---------|---------|---------|
| 工单 | 双写（PG 优先，Redis 缓存） | PostgreSQL |
| 坐席账号 | 双写（PG + Redis） | 认证走 Redis，管理走 PG |
| 审计日志 | 仅写 PostgreSQL | PostgreSQL |
| 邮件记录 | 仅写 PostgreSQL | PostgreSQL |
| 活跃会话 | 仅写 Redis | Redis |
| 会话归档 | 关闭时异步迁移到 PG | PostgreSQL |

### 3.3 核心表结构

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

---

## 4. 环境配置

### 4.1 新增环境变量

```bash
# .env 新增配置
DATABASE_URL=postgresql://fiido:password@localhost:5432/fiido_db
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_ECHO=false
```

### 4.2 配置类设计

```python
@dataclass
class DatabaseConfig:
    url: str = "postgresql://fiido:password@localhost:5432/fiido_db"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 1800
    echo: bool = False

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        # 从环境变量加载
```

---

## 5. 模块结构设计

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
├── repositories/            # Repository 模式（可选）
│   └── ...
├── migrations/              # Alembic 迁移
│   ├── env.py
│   ├── alembic.ini
│   └── versions/
├── converters.py            # Pydantic ↔ ORM 转换器
├── memory-bank/             # 本目录
└── README.md
```

---

## 6. API 设计

本模块是基础设施层，不直接暴露 API。通过以下方式集成：

### 6.1 Bootstrap 集成

```python
# infrastructure/bootstrap/factory.py
class Component(Enum):
    DATABASE = "database"  # 新增

# 初始化函数
def init_database(config: DatabaseConfig = None) -> Engine
def get_db_session() -> Session
```

### 6.2 服务层调用

```python
# services/ticket/store.py
from infrastructure.database import get_db_session

class TicketStore:
    async def create(self, ticket: Ticket) -> Ticket:
        # 双写：先 PostgreSQL，再 Redis 缓存
```

---

## 7. 扩展性设计

| 扩展阶段 | 操作 | 影响范围 |
|---------|------|---------|
| 垂直扩展 | 增加服务器配置 | 配置调整 |
| 读写分离 | PG 主从复制 | 连接配置 |
| 分区 | 审计日志按月分区 | 表结构 |
| 分库 | 按租户/业务分库 | 架构改动 |

---

## 8. 文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-22 | 初始版本 |
