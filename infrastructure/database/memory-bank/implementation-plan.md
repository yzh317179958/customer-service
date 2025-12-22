# PostgreSQL 数据库模块 - 实现计划

> **模块位置**: infrastructure/database/
> **创建日期**: 2025-12-22
> **预计步骤数**: 12
> **核心功能步骤**: Step 1-8
> **扩展功能步骤**: Step 9-12

---

## 关键设计决策（已确认）

| 决策项 | 选择 | 理由 |
|--------|------|------|
| SQLAlchemy 模式 | **同步模式** (psycopg2) | 更稳定，企业级首选，调试方便 |
| Redis 失败处理 | **重试后忽略** | PG 是数据源，Redis 是缓存，不因缓存失败阻塞业务 |
| 历史数据迁移 | **无需迁移** | 从零开始，无历史包袱 |
| 异步调用方式 | `run_in_executor` | 在 async 函数中调用同步数据库操作 |

---

## 开发顺序说明

遵循 `CLAUDE.md` 自底向上原则：

```
PostgreSQL 安装配置（前置条件）
        ↓
infrastructure/database/ (本模块)
        ↓
infrastructure/bootstrap/ (集成)
        ↓
services/ticket, services/session (改造)
        ↓
测试验证
```

---

## Step 1: PostgreSQL 安装与模块骨架

**任务描述：**
1. 安装配置 PostgreSQL 数据库
2. 创建 `infrastructure/database/` 模块骨架
3. 实现连接池管理

**涉及文件：**
- `infrastructure/database/__init__.py`（新增）
- `infrastructure/database/connection.py`（新增）
- `infrastructure/database/base.py`（新增）
- `requirements.txt`（修改）
- `.env`（修改）

**具体内容：**

### 1.1 安装 PostgreSQL
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# 启动服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库和用户
sudo -u postgres psql -c "CREATE USER fiido WITH PASSWORD 'fiido123';"
sudo -u postgres psql -c "CREATE DATABASE fiido_db OWNER fiido;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE fiido_db TO fiido;"
```

### 1.2 添加 Python 依赖
```txt
# requirements.txt 新增
SQLAlchemy>=2.0.0
psycopg2-binary>=2.9.0
alembic>=1.12.0
```

### 1.3 配置环境变量
```bash
# .env 新增
DATABASE_URL=postgresql://fiido:fiido123@localhost:5432/fiido_db
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_ECHO=false
```

### 1.4 实现连接管理
- `DatabaseConfig` 配置类（从环境变量加载）
- `init_database()` 初始化函数（同步模式，连接池）
- `get_db_session()` 获取数据库会话（上下文管理器）
- `Base = declarative_base()` ORM 基类

**测试方法：**
```bash
# 1. 验证 PostgreSQL 运行
sudo systemctl status postgresql

# 2. 验证数据库连接
psql -h localhost -U fiido -d fiido_db -c "SELECT 1;"

# 3. 验证 Python 连接
python3 -c "
from infrastructure.database import init_database, get_db_session
init_database()
with get_db_session() as session:
    result = session.execute('SELECT 1')
    print('数据库连接成功:', result.scalar())
"
```

**预期结果：**
- PostgreSQL 服务运行正常
- Python 能成功连接数据库
- 输出"数据库连接成功: 1"

---

## Step 2: 核心 ORM 模型 - 工单（Ticket）

**任务描述：**
实现工单相关的 ORM 模型，包括主表和关联表。

**涉及文件：**
- `infrastructure/database/models/__init__.py`（新增）
- `infrastructure/database/models/ticket.py`（新增）

**具体内容：**
实现以下 ORM 模型：
1. `TicketModel` - 工单主表
2. `TicketCommentModel` - 工单评论表
3. `TicketAttachmentModel` - 工单附件表
4. `TicketStatusHistoryModel` - 工单状态历史表

**字段参考 `services/ticket/models.py` 中的 Pydantic 模型。**

**测试方法：**
```bash
python3 -c "
from infrastructure.database.models import TicketModel, TicketCommentModel
print('TicketModel 字段:', TicketModel.__table__.columns.keys())
print('工单 ORM 模型加载成功')
"
```

**预期结果：**
- 输出工单模型的字段列表
- 无导入错误

---

## Step 3: 核心 ORM 模型 - 坐席（Agent）

**任务描述：**
实现坐席账号的 ORM 模型。

**涉及文件：**
- `infrastructure/database/models/agent.py`（新增）
- `infrastructure/database/models/__init__.py`（修改，导出）

**具体内容：**
实现 `AgentModel`，字段包括：
- id, agent_id, username, password_hash
- name, role, status, status_note
- max_sessions, avatar_url, skills (JSONB)
- status_updated_at, last_active_at, last_login_at
- created_at, updated_at

**测试方法：**
```bash
python3 -c "
from infrastructure.database.models import AgentModel
print('AgentModel 字段:', AgentModel.__table__.columns.keys())
print('坐席 ORM 模型加载成功')
"
```

**预期结果：**
- 输出坐席模型的字段列表
- 无导入错误

---

## Step 4: 扩展 ORM 模型 - 审计日志、会话归档、邮件记录

**任务描述：**
实现剩余的 ORM 模型。

**涉及文件：**
- `infrastructure/database/models/audit.py`（新增）
- `infrastructure/database/models/session.py`（新增）
- `infrastructure/database/models/email.py`（新增）
- `infrastructure/database/models/__init__.py`（修改，导出）

**具体内容：**
1. `AuditLogModel` - 审计日志表
2. `SessionArchiveModel` - 会话归档表
3. `EmailRecordModel` - 邮件发送记录表

**测试方法：**
```bash
python3 -c "
from infrastructure.database.models import (
    AuditLogModel, SessionArchiveModel, EmailRecordModel
)
print('所有 ORM 模型加载成功')
"
```

**预期结果：**
- 所有模型正常加载
- 无导入错误

---

## Step 5: Alembic 迁移配置

**任务描述：**
配置 Alembic 数据库迁移环境，生成初始迁移脚本。

**涉及文件：**
- `infrastructure/database/migrations/alembic.ini`（新增）
- `infrastructure/database/migrations/env.py`（新增）
- `infrastructure/database/migrations/versions/`（新增目录）

**具体内容：**
1. 初始化 Alembic 配置
2. 配置 env.py 导入所有 ORM 模型
3. 生成初始迁移脚本（包含所有表）
4. 执行迁移，创建数据库表

**测试方法：**
```bash
# 生成迁移
cd /home/yzh/AI客服/鉴权
alembic -c infrastructure/database/migrations/alembic.ini revision --autogenerate -m "initial tables"

# 执行迁移
alembic -c infrastructure/database/migrations/alembic.ini upgrade head

# 验证表创建
python3 -c "
from infrastructure.database import init_database, get_db_session
from sqlalchemy import inspect
init_database()
session = get_db_session()
inspector = inspect(session.bind)
tables = inspector.get_table_names()
print('已创建的表:', tables)
"
```

**预期结果：**
- 迁移脚本生成成功
- 数据库表创建成功
- 输出包含 agents, tickets, ticket_comments 等表名

---

## Step 6: Pydantic ↔ ORM 转换器

**任务描述：**
实现 Pydantic 模型与 ORM 模型之间的转换器。

**涉及文件：**
- `infrastructure/database/converters.py`（新增）

**具体内容：**
实现以下转换函数：
1. `ticket_to_orm(ticket: Ticket) -> TicketModel`
2. `ticket_from_orm(model: TicketModel) -> Ticket`
3. `agent_to_orm(agent: Agent) -> AgentModel`
4. `agent_from_orm(model: AgentModel) -> Agent`
5. 其他模型的转换器

**测试方法：**
```bash
python3 -c "
from services.ticket.models import Ticket
from infrastructure.database.converters import ticket_to_orm, ticket_from_orm

# 创建测试工单
ticket = Ticket(
    ticket_id='TKT-TEST-001',
    title='测试工单',
    description='测试描述',
    created_by='admin'
)

# 转换测试
orm_model = ticket_to_orm(ticket)
print('转为 ORM:', orm_model.ticket_id)

back_ticket = ticket_from_orm(orm_model)
print('转回 Pydantic:', back_ticket.ticket_id)
print('转换器测试成功')
"
```

**预期结果：**
- 双向转换正常
- 数据不丢失

---

## Step 7: Bootstrap 集成

**任务描述：**
将数据库模块集成到 Bootstrap 工厂。

**涉及文件：**
- `infrastructure/bootstrap/database.py`（新增）
- `infrastructure/bootstrap/factory.py`（修改）
- `infrastructure/bootstrap/__init__.py`（修改）

**具体内容：**
1. 新增 `Component.DATABASE` 枚举
2. 实现 `init_database()` 初始化函数
3. 添加 `get_db_session()` 获取器
4. 更新组件依赖关系

**测试方法：**
```bash
python3 -c "
from infrastructure.bootstrap import BootstrapFactory, Component

factory = BootstrapFactory()
factory.init_components([Component.DATABASE])
print('Bootstrap 集成成功')
"
```

**预期结果：**
- 输出"Bootstrap 集成成功"
- 数据库组件正常初始化

---

## Step 8: TicketStore 双写改造

**任务描述：**
改造 TicketStore，实现 PostgreSQL + Redis 双写策略。

**涉及文件：**
- `services/ticket/store.py`（修改）

**具体内容：**
1. 添加 PostgreSQL 写入逻辑
2. 保持 Redis 缓存逻辑
3. 查询切换到 PostgreSQL
4. 保持接口不变

**双写策略（已确认）：**
```python
import asyncio
from functools import partial

async def create(self, ticket: Ticket) -> Ticket:
    # 1. 同步写入 PostgreSQL（主，使用 run_in_executor）
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, partial(self._pg_create, ticket))

    # 2. 写入 Redis 缓存（可选，失败不阻塞）
    try:
        await self._redis_set(ticket.ticket_id, ticket)
    except Exception as e:
        # 重试一次
        try:
            await self._redis_set(ticket.ticket_id, ticket)
        except Exception:
            # 记录日志，但不阻塞业务
            logger.warning(f"Redis 缓存写入失败: {e}")

    return ticket

def _pg_create(self, ticket: Ticket) -> None:
    """同步写入 PostgreSQL"""
    with get_db_session() as session:
        orm_model = ticket_to_orm(ticket)
        session.add(orm_model)
        session.commit()
```

**Redis 失败处理策略：**
- PostgreSQL 是数据源，写入成功即可
- Redis 失败重试 1 次
- 仍失败则记录日志，不回滚 PG
- 下次读取时会从 PG 重新加载到缓存

**测试方法：**
```bash
# 启动服务
uvicorn backend:app --port 8000 &

# 测试创建工单
curl -X POST http://localhost:8000/api/tickets \
  -H "Content-Type: application/json" \
  -d '{"title":"测试工单","description":"测试","created_by":"admin"}'

# 验证数据库
python3 -c "
from infrastructure.database import get_db_session
from infrastructure.database.models import TicketModel

session = get_db_session()
tickets = session.query(TicketModel).all()
print(f'数据库中工单数量: {len(tickets)}')
"
```

**预期结果：**
- 工单创建成功
- 数据同时存在于 PostgreSQL 和 Redis

---

## Step 9: AgentManager 双写改造

**任务描述：**
改造坐席管理，实现 PostgreSQL 持久化。

**涉及文件：**
- `infrastructure/security/agent_auth.py`（修改）

**具体内容：**
1. 坐席账号存储到 PostgreSQL
2. 认证逻辑仍走 Redis（高频）
3. 管理操作（列表、搜索）走 PostgreSQL

**测试方法：**
```bash
# 测试坐席登录
curl -X POST http://localhost:8000/api/agent/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"xxx"}'

# 验证数据库
python3 -c "
from infrastructure.database import get_db_session
from infrastructure.database.models import AgentModel

session = get_db_session()
agents = session.query(AgentModel).all()
print(f'数据库中坐席数量: {len(agents)}')
"
```

**预期结果：**
- 坐席登录正常
- 坐席数据持久化到 PostgreSQL

---

## Step 10: 审计日志改造

**任务描述：**
将审计日志存储切换到 PostgreSQL。

**涉及文件：**
- `services/ticket/audit.py`（修改）

**具体内容：**
1. 审计日志直接写入 PostgreSQL
2. 不再使用 Redis 存储
3. 查询接口切换到 PostgreSQL

**测试方法：**
```bash
# 执行一些操作生成审计日志
# 验证数据库
python3 -c "
from infrastructure.database import get_db_session
from infrastructure.database.models import AuditLogModel

session = get_db_session()
logs = session.query(AuditLogModel).order_by(AuditLogModel.created_at.desc()).limit(10).all()
print(f'最近审计日志: {len(logs)} 条')
"
```

**预期结果：**
- 审计日志写入 PostgreSQL
- 查询正常返回

---

## Step 11: 邮件发送记录与会话归档

**任务描述：**
实现邮件发送记录和会话归档功能。

**涉及文件：**
- `services/email/service.py`（修改）
- `services/session/archive.py`（新增）

**具体内容：**
1. 邮件发送后记录到 PostgreSQL
2. 会话关闭时归档到 PostgreSQL
3. 添加定时任务清理过期归档（可选）

**注意：无需历史数据迁移（已确认）**

**测试方法：**
```bash
# 验证邮件记录
python3 -c "
from infrastructure.database import get_db_session
from infrastructure.database.models import EmailRecordModel

with get_db_session() as session:
    records = session.query(EmailRecordModel).count()
    print(f'邮件记录数: {records}')
"

# 验证会话归档
python3 -c "
from infrastructure.database import get_db_session
from infrastructure.database.models import SessionArchiveModel

with get_db_session() as session:
    archives = session.query(SessionArchiveModel).count()
    print(f'会话归档数: {archives}')
"
```

**预期结果：**
- 邮件发送有记录
- 会话归档正常

---

## Step 12: 测试与文档更新

**任务描述：**
全面测试，更新文档。

**涉及文件：**
- `infrastructure/database/README.md`（新增/更新）
- `infrastructure/database/memory-bank/progress.md`（更新）
- `infrastructure/database/memory-bank/architecture.md`（更新）
- `PROJECT_OVERVIEW.md`（更新）

**具体内容：**
1. 运行所有 API 接口测试
2. 验证数据一致性
3. 更新模块文档
4. 更新项目总览

**测试方法：**
```bash
# 完整测试脚本
python3 -c "
print('=== 数据库升级验证 ===')

# 1. 连接测试
from infrastructure.database import init_database, get_db_session
init_database()
session = get_db_session()
print('✅ 数据库连接正常')

# 2. 表结构测试
from sqlalchemy import inspect
inspector = inspect(session.bind)
tables = inspector.get_table_names()
expected = ['agents', 'tickets', 'ticket_comments', 'audit_logs']
for t in expected:
    if t in tables:
        print(f'✅ 表 {t} 存在')
    else:
        print(f'❌ 表 {t} 不存在')

# 3. CRUD 测试
from infrastructure.database.models import TicketModel
count = session.query(TicketModel).count()
print(f'✅ 工单数量: {count}')

print('=== 验证完成 ===')
"
```

**预期结果：**
- 所有测试通过
- 文档更新完成

---

## 风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| 数据迁移丢失 | 先双写，验证后再切换 |
| 性能下降 | 保持 Redis 热数据缓存 |
| 迁移脚本失败 | 分批迁移，支持回滚 |
| 连接池耗尽 | 合理配置 pool_size，添加监控 |

---

## 预估工作量

| 阶段 | 步骤 | 预估时间 |
|------|------|---------|
| 基础设施 | Step 1-5 | 3-4 天 |
| 模型转换 | Step 6-7 | 1-2 天 |
| 核心改造 | Step 8-10 | 3-4 天 |
| 扩展功能 | Step 11 | 1-2 天 |
| 测试文档 | Step 12 | 1-2 天 |
| **总计** | | **9-14 天** |

---

## 文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-22 | 初始版本，整理自 DATABASE_UPGRADE_PLAN.md |
