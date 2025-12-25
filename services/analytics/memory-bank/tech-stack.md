# 数据分析服务 - 技术栈

> **版本**: v2.0
> **创建日期**: 2025-12-25
> **模块位置**: `services/analytics/`

---

## 1. 复用现有技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 服务层 | `services/analytics/` | 本模块位置 |
| 数据存储 | Redis + PostgreSQL | 双写策略（实时 + 历史） |
| 基础设施 | `infrastructure/bootstrap/` | 组件工厂、Redis/PG 客户端 |
| 基础设施 | `infrastructure/database/` | 数据库连接池 |
| 调度任务 | `infrastructure/scheduler/` | 定时聚合任务 |

---

## 2. 新增依赖

**无需新增 Python 依赖**

理由：
- 埋点采集：使用 Python 原生 `asyncio` 异步队列
- 数据存储：复用现有 Redis + PostgreSQL
- 数据聚合：使用 SQL 聚合函数
- API 接口：复用 FastAPI

---

## 3. 架构设计

### 3.1 服务与产品的关系

```
┌─────────────────────────────────────────────────────────────────────┐
│                         products/ 产品层                             │
│                                                                      │
│  ┌─────────────────────┐         ┌─────────────────────┐            │
│  │   AI 智能客服        │         │    坐席工作台         │            │
│  │   (ai_chatbot)      │         │ (agent_workbench)   │            │
│  │                     │         │                     │            │
│  │  埋点数据发送 ───────┼────────►  前端 UI 展示         │            │
│  │                     │         │  ├── Monitoring     │            │
│  │  ├── chat.py        │         │  ├── Dashboard      │            │
│  │  └── 埋点调用        │         │  ├── QualityAudit   │            │
│  │                     │         │  └── BillingPortal  │            │
│  └──────────┬──────────┘         └──────────┬──────────┘            │
│             │                               │                        │
│             │ import                        │ import                 │
│             ▼                               ▼                        │
├─────────────────────────────────────────────────────────────────────┤
│                      services/analytics/                             │
│                        【本模块】                                     │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  tracker/     │  stats/      │  quality/    │  billing/     │    │
│  │  (埋点采集)    │  (会话统计)   │  (质检分析)   │  (Token统计)  │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                       │
│                              ▼                                       │
├─────────────────────────────────────────────────────────────────────┤
│                    infrastructure/                                   │
│                                                                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                     │
│  │  database  │  │ scheduler  │  │  bootstrap │                     │
│  │ (PG+Redis) │  │ (定时任务)  │  │ (组件工厂)  │                     │
│  └────────────┘  └────────────┘  └────────────┘                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 子模块职责

| 子模块 | 职责 | 数据流向 |
|--------|------|----------|
| **tracker** | 事件采集、缓冲、持久化 | 产品 → Redis → PostgreSQL |
| **stats** | 会话/效能统计查询 | PostgreSQL/Redis → API |
| **quality** | 质检评分记录和查询 | PostgreSQL → API |
| **billing** | Token 消耗统计、ROI 计算 | Coze 回调 → PostgreSQL → API |

---

## 4. 数据存储方案

### 4.1 双写策略

```
埋点事件 ──► 异步队列 ──┬──► Redis (实时计数/状态)
                        │
                        └──► PostgreSQL (历史明细/汇总)
```

### 4.2 Redis 数据结构

**实时统计 (stats 子模块使用)**
```redis
# 实时大屏 - 核心指标
HSET analytics:realtime:overview \
  active_sessions 128 \
  queue_count 14 \
  online_agents 42 \
  total_agents 50 \
  sla_alerts 0

# 实时大屏 - 渠道流量
HSET analytics:realtime:channels:app \
  online_users 1202 \
  load_percent 88 \
  trend "up"

HSET analytics:realtime:channels:web \
  online_users 840 \
  load_percent 56 \
  trend "stable"

# 实时大屏 - 坐席状态
HSET analytics:realtime:agents:agent_001 \
  name "李建国" \
  status "serving" \
  current_session_duration 720 \
  load "high"

# 今日统计计数器
HINCRBY analytics:daily:2025-12-25 sessions 1
HINCRBY analytics:daily:2025-12-25 ai_resolved 1
HINCRBY analytics:daily:2025-12-25 transferred 1
HINCRBY analytics:daily:2025-12-25 total_response_time 1500
```

**事件缓冲 (tracker 子模块使用)**
```redis
# 待持久化的事件队列
LPUSH analytics:event_buffer '{...event_json...}'
```

**Token 使用量 (billing 子模块使用)**
```redis
# 当日 Token 消耗
HINCRBY analytics:billing:2025-12-25 tokens_used 1500
HINCRBY analytics:billing:2025-12-25 api_calls 1
```

### 4.3 PostgreSQL 表结构

**事件明细表 (tracker)**
```sql
CREATE TABLE analytics_events (
    id BIGSERIAL PRIMARY KEY,
    event_name VARCHAR(50) NOT NULL,
    event_data JSONB NOT NULL,
    session_id VARCHAR(36),
    product VARCHAR(30) NOT NULL,
    tenant_id VARCHAR(36),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_events_name ON analytics_events(event_name);
CREATE INDEX idx_events_session ON analytics_events(session_id);
CREATE INDEX idx_events_created ON analytics_events(created_at);
CREATE INDEX idx_events_product ON analytics_events(product);
```

**日统计汇总表 (stats)**
```sql
CREATE TABLE analytics_daily_stats (
    id SERIAL PRIMARY KEY,
    stat_date DATE NOT NULL,
    product VARCHAR(30) NOT NULL,
    tenant_id VARCHAR(36),

    -- 会话指标
    total_sessions INT DEFAULT 0,
    completed_sessions INT DEFAULT 0,
    ai_resolved INT DEFAULT 0,
    transferred INT DEFAULT 0,
    avg_session_duration INT DEFAULT 0,

    -- 响应指标
    avg_response_time INT DEFAULT 0,
    total_messages INT DEFAULT 0,

    -- 满意度
    avg_rating DECIMAL(3,2) DEFAULT 0,
    rating_count INT DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (stat_date, product, tenant_id)
);
```

**质检记录表 (quality)**
```sql
CREATE TABLE analytics_quality_audits (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    agent_id VARCHAR(36),
    customer_name VARCHAR(100),

    -- 质检结果
    score INT NOT NULL,
    status VARCHAR(20) NOT NULL,  -- passed, failed, pending_review
    audit_type VARCHAR(20) NOT NULL,  -- auto, manual
    issues JSONB,  -- 问题列表

    -- 元数据
    session_type VARCHAR(50),  -- 会话场景
    audited_at TIMESTAMP DEFAULT NOW(),
    reviewed_by VARCHAR(36),
    reviewed_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audits_session ON analytics_quality_audits(session_id);
CREATE INDEX idx_audits_agent ON analytics_quality_audits(agent_id);
CREATE INDEX idx_audits_status ON analytics_quality_audits(status);
CREATE INDEX idx_audits_date ON analytics_quality_audits(audited_at);
```

**Token 消耗表 (billing)**
```sql
CREATE TABLE analytics_token_usage (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(36),
    tenant_id VARCHAR(36),

    -- Token 详情
    tokens_used INT NOT NULL,
    model VARCHAR(50),
    api_type VARCHAR(30),  -- chat, workflow, etc.

    -- 时间
    used_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tokens_tenant ON analytics_token_usage(tenant_id);
CREATE INDEX idx_tokens_date ON analytics_token_usage(used_at);

-- 日汇总表（定时聚合）
CREATE TABLE analytics_billing_daily (
    id SERIAL PRIMARY KEY,
    stat_date DATE NOT NULL,
    tenant_id VARCHAR(36),

    total_tokens INT DEFAULT 0,
    total_api_calls INT DEFAULT 0,
    estimated_cost DECIMAL(10,2) DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (stat_date, tenant_id)
);
```

---

## 5. 核心类设计

### 5.1 tracker 子模块

```python
# services/analytics/tracker.py

class AnalyticsTracker:
    """埋点追踪器（各产品使用）"""

    async def track(self, event_name: str, data: dict, session_id: str = None):
        """记录埋点事件（异步非阻塞）"""

    async def start(self):
        """启动后台刷新任务"""

    async def stop(self):
        """停止并刷新剩余事件"""

    async def flush(self):
        """批量写入数据库"""

def get_tracker(product: str) -> AnalyticsTracker:
    """获取追踪器单例"""

def init_tracker(product: str, redis, pg) -> AnalyticsTracker:
    """初始化追踪器"""
```

### 5.2 stats 子模块

```python
# services/analytics/stats.py

class RealtimeStats:
    """实时统计（供 Monitoring 页面使用）"""

    async def get_overview(self) -> dict:
        """获取核心指标概览"""

    async def get_channels(self) -> list:
        """获取渠道流量分布"""

    async def get_agents(self) -> list:
        """获取坐席状态列表"""

    async def update_agent_status(self, agent_id: str, status: str):
        """更新坐席状态"""


class DashboardStats:
    """效能统计（供 Dashboard 页面使用）"""

    async def get_today_stats(self) -> dict:
        """获取今日统计"""

    async def get_trend(self, days: int = 7) -> list:
        """获取趋势数据"""

    async def get_satisfaction(self) -> dict:
        """获取满意度分布"""
```

### 5.3 quality 子模块

```python
# services/analytics/quality.py

class QualityAuditService:
    """质检服务（供 QualityAudit 页面使用）"""

    async def get_summary(self) -> dict:
        """获取质检汇总"""

    async def get_records(self, page: int, size: int) -> list:
        """获取质检记录列表"""

    async def create_audit(self, session_id: str, score: int, issues: list):
        """创建质检记录"""

    async def review_audit(self, audit_id: int, reviewer_id: str, final_score: int):
        """人工复核"""
```

### 5.4 billing 子模块

```python
# services/analytics/billing.py

class BillingStats:
    """计费统计（供 BillingPortal 页面使用）"""

    async def get_usage(self, tenant_id: str = None) -> dict:
        """获取 Token 使用量"""

    async def get_roi(self, tenant_id: str = None) -> dict:
        """获取 ROI 估算"""

    async def get_quota(self, tenant_id: str = None) -> dict:
        """获取套餐余量"""

    async def record_token_usage(self, session_id: str, tokens: int, model: str):
        """记录 Token 消耗（Coze 回调时调用）"""
```

---

## 6. API 设计

### 6.1 实时大屏 API (Monitoring)

```python
# GET /api/analytics/realtime/overview
{
    "active_sessions": 128,
    "queue_count": 14,
    "online_agents": 42,
    "total_agents": 50,
    "sla_alerts": 0,
    "system_load": "28.4%"
}

# GET /api/analytics/realtime/channels
[
    {"name": "Fiido App", "online_users": 1202, "load": 88, "trend": "up"},
    {"name": "Fiido Global", "online_users": 840, "load": 56, "trend": "stable"},
    {"name": "微信小程序", "online_users": 2100, "load": 74, "trend": "up"},
    {"name": "电话呼叫中心", "online_users": 156, "load": 32, "trend": "down"}
]

# GET /api/analytics/realtime/agents
[
    {"agent_id": "001", "name": "李建国", "status": "serving", "duration": "12m", "load": "high"},
    {"agent_id": "002", "name": "王小美", "status": "online", "duration": "4h", "load": "low"}
]
```

### 6.2 效能报表 API (Dashboard)

```python
# GET /api/analytics/stats/today
{
    "total_sessions": 1582,
    "avg_response_time": 28,
    "satisfaction_rate": 98.5,
    "quality_rating": "卓越",
    "changes": {
        "sessions": "+12%",
        "response_time": "-4s",
        "satisfaction": "+0.2%"
    }
}

# GET /api/analytics/stats/trend?days=7
[
    {"date": "2025-12-19", "name": "周一", "sessions": 400},
    {"date": "2025-12-20", "name": "周二", "sessions": 300},
    ...
]

# GET /api/analytics/stats/satisfaction
{
    "distribution": [
        {"label": "非常满意", "value": 88, "color": "#00a6a0"},
        {"label": "满意", "value": 10, "color": "#ffffff"},
        {"label": "待改进", "value": 2, "color": "#ef4444"}
    ]
}
```

### 6.3 智能质检 API (QualityAudit)

```python
# GET /api/analytics/quality/summary
{
    "pass_rate": 99.1,
    "audited_count": 1204,
    "pending_review": 12
}

# GET /api/analytics/quality/records?page=1&size=10
{
    "items": [
        {
            "id": "QA-001",
            "agent": "李建国",
            "customer": "John Doe",
            "score": 98,
            "status": "passed",
            "type": "Titan续航疑虑回复",
            "date": "2024-03-22"
        }
    ],
    "total": 1204,
    "page": 1
}
```

### 6.4 计费统计 API (BillingPortal)

```python
# GET /api/analytics/billing/usage
{
    "tokens_used": 7420,
    "tokens_total": 10000,
    "usage_percent": 74.2,
    "reset_date": "2025-04-20"
}

# GET /api/analytics/billing/roi
{
    "saved_cost": 4800,
    "auto_resolve_rate": 78,
    "equivalent_headcount": 1.1,
    "period": "本月"
}
```

---

## 7. 产品接入方式

### 7.1 AI 客服接入（埋点发送方）

```python
# products/ai_chatbot/lifespan.py
from services.analytics import init_tracker

async def lifespan(app):
    tracker = init_tracker("ai_chatbot", redis, pg)
    await tracker.start()
    yield
    await tracker.stop()

# products/ai_chatbot/handlers/chat.py
from services.analytics import get_tracker

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    tracker = get_tracker()
    await tracker.track("session.start", {...})
    # 业务逻辑
    await tracker.track("message.ai", {"response_time": 150, "tokens": 500})
```

### 7.2 坐席工作台接入（API 调用方）

```python
# products/agent_workbench/handlers/analytics.py
from services.analytics import (
    RealtimeStats, DashboardStats, QualityAuditService, BillingStats
)

# 实时大屏
@router.get("/api/analytics/realtime/overview")
async def get_realtime_overview():
    return await RealtimeStats().get_overview()

# 效能报表
@router.get("/api/analytics/stats/today")
async def get_today_stats():
    return await DashboardStats().get_today_stats()

# 智能质检
@router.get("/api/analytics/quality/summary")
async def get_quality_summary():
    return await QualityAuditService().get_summary()

# 计费统计
@router.get("/api/analytics/billing/usage")
async def get_billing_usage():
    return await BillingStats().get_usage()
```

---

## 8. 性能考虑

### 8.1 异步非阻塞

- 埋点使用 `asyncio.Queue` 缓冲
- 后台任务批量写入数据库
- 埋点失败不影响主流程

### 8.2 数据聚合策略

```
实时数据（Redis）
    │
    ▼ 定时聚合（每 5 分钟）
日统计表（PostgreSQL）
    │
    ▼ 定期清理（90 天）
事件明细表（PostgreSQL）
```

### 8.3 查询优化

- 实时查询走 Redis
- 历史查询走 PostgreSQL 汇总表
- 明细查询限制时间范围

---

## 9. 文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0 | 2025-12-25 | 基于 UI 组件分析，扩展为 4 个子模块；新增完整 API 响应示例；明确服务与产品的关系 |
| v1.0 | 2025-12-25 | 初始版本 |
