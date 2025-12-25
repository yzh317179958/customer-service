# 数据埋点与统计分析服务 - 架构说明

> **功能**: 数据埋点与统计分析服务 (Analytics Service)
> **模块位置**: `services/analytics/`
> **最后更新**: 2025-12-25
> **遵循规范**: CLAUDE.md 三层架构

---

## 1. 模块定位

```
┌─────────────────────────────────────────────────────────────────┐
│                      products/ 产品层                            │
│  ┌─────────────────┐         ┌─────────────────┐                │
│  │  AI 智能客服     │         │   坐席工作台     │                │
│  │  (ai_chatbot)   │         │(agent_workbench)│                │
│  └────────┬────────┘         └────────┬────────┘                │
│           │                           │                          │
│           │  import                   │  import                  │
│           ▼                           ▼                          │
├─────────────────────────────────────────────────────────────────┤
│                      services/analytics/                         │
│                         【本模块】                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Tracker │ Stats │ Aggregator │ Models │ Config         │    │
│  │  (埋点)   │(统计) │  (聚合)    │ (模型)  │ (配置)         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
├─────────────────────────────────────────────────────────────────┤
│                    infrastructure/                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                 │
│  │  database  │  │ scheduler  │  │  bootstrap │                 │
│  │ (PG+Redis) │  │ (定时任务)  │  │ (组件工厂)  │                 │
│  └────────────┘  └────────────┘  └────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
```

**架构原则**：
- 本模块属于 `services/` 服务层
- 可被 `products/` 产品层依赖
- 依赖 `infrastructure/` 基础设施层
- 不依赖其他产品或服务

---

## 2. 文件结构

```
services/analytics/
├── __init__.py              # 模块导出
├── README.md                # 使用说明
├── memory-bank/             # 开发文档
│   ├── prd.md              # 产品需求
│   ├── tech-stack.md       # 技术栈
│   ├── implementation-plan.md  # 实现计划
│   ├── progress.md         # 进度追踪
│   └── architecture.md     # 本文档
│
├── 【核心文件】
├── config.py                # 配置模型
│   └── AnalyticsConfig      # 埋点配置
│
├── models.py                # 数据模型
│   ├── AnalyticsEvent       # 事件模型
│   └── DailyStats           # 日统计模型
│
├── tracker.py               # 埋点追踪器
│   ├── AnalyticsTracker     # 追踪器类
│   ├── get_tracker()        # 单例获取
│   └── init_tracker()       # 初始化
│
├── stats.py                 # 统计查询器
│   ├── AnalyticsStats       # 统计类
│   └── get_stats()          # 单例获取
│
├── aggregator.py            # 数据聚合器
│   └── AnalyticsAggregator  # 聚合类
│
└── api.py                   # API 路由（可选）
    └── router               # FastAPI 路由
```

---

## 3. 数据流

### 3.1 埋点数据流

```
产品层 (ai_chatbot / agent_workbench)
    │
    │ tracker.track(event_name, data)
    ▼
┌─────────────────────────────────────┐
│        AnalyticsTracker             │
│  ┌─────────────────────────────┐    │
│  │   asyncio.Queue (缓冲区)    │    │
│  │   - 异步非阻塞              │    │
│  │   - 批量处理                │    │
│  └─────────────┬───────────────┘    │
│                │                     │
│                ▼ flush() 定时/满量  │
└────────────────┼────────────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
    ▼                         ▼
┌──────────────┐      ┌──────────────┐
│    Redis     │      │  PostgreSQL  │
│  (实时计数)   │      │  (事件明细)  │
│              │      │              │
│ analytics:   │      │ analytics_   │
│ daily:{date} │      │ events       │
└──────────────┘      └──────────────┘
```

### 3.2 统计查询流

```
查询请求 (GET /api/analytics/...)
    │
    ▼
┌─────────────────────────────────────┐
│         AnalyticsStats              │
│                                     │
│  get_realtime_stats()               │
│         │                           │
│         ▼                           │
│    ┌──────────┐                     │
│    │  Redis   │ ◄─── 实时数据       │
│    └──────────┘                     │
│                                     │
│  get_daily_stats() / get_range()    │
│         │                           │
│         ▼                           │
│    ┌──────────────┐                 │
│    │  PostgreSQL  │ ◄─── 历史数据   │
│    │ daily_stats  │                 │
│    └──────────────┘                 │
└─────────────────────────────────────┘
```

### 3.3 数据聚合流

```
定时任务 (每日凌晨 / 每 5 分钟)
    │
    ▼
┌─────────────────────────────────────┐
│       AnalyticsAggregator           │
│                                     │
│  sync_redis_to_pg()                 │
│    Redis 实时计数 ──► PG 日统计表   │
│                                     │
│  aggregate_daily()                  │
│    PG 事件明细 ──► PG 日统计表      │
│                                     │
│  cleanup_old_events()               │
│    删除 90 天前的事件明细           │
└─────────────────────────────────────┘
```

---

## 4. 接口规范

### 4.1 对外导出

```python
# services/analytics/__init__.py

# 配置
from .config import AnalyticsConfig

# 模型
from .models import AnalyticsEvent, DailyStats

# 埋点追踪器
from .tracker import AnalyticsTracker, get_tracker, init_tracker

# 统计查询
from .stats import AnalyticsStats, get_stats

# 数据聚合
from .aggregator import AnalyticsAggregator
```

### 4.2 产品接入示例

```python
# products/ai_chatbot/lifespan.py

from services.analytics import init_tracker

async def lifespan(app):
    # 启动时初始化
    tracker = init_tracker(
        product="ai_chatbot",
        redis=get_redis_client(),
        pg=get_pg_pool()
    )
    await tracker.start()

    yield

    # 关闭时刷新剩余事件
    await tracker.stop()
```

```python
# products/ai_chatbot/handlers/chat.py

from services.analytics import get_tracker

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    tracker = get_tracker()

    # 记录会话开始
    await tracker.track("session.start", {
        "session_id": request.session_id,
        "user_agent": request.headers.get("User-Agent")
    })

    # 业务逻辑...
    start = time.time()
    response = await process_chat(request)
    response_time = (time.time() - start) * 1000

    # 记录 AI 回复
    await tracker.track("message.ai", {
        "session_id": request.session_id,
        "response_time": response_time,
        "tokens": response.token_count
    })
```

---

## 5. Redis Key 规范

| Key 模式 | 用途 | TTL |
|----------|------|-----|
| `analytics:daily:{date}` | 日统计计数 (Hash) | 7 天 |
| `analytics:active_sessions` | 活跃会话集合 (Set) | 无 |
| `analytics:event_buffer` | 事件缓冲队列 (List) | 无 |
| `analytics:hourly:{date}:{hour}` | 小时统计 (Hash) | 2 天 |

---

## 6. PostgreSQL 表规范

| 表名 | 用途 | 保留策略 |
|------|------|----------|
| `analytics_events` | 事件明细 | 90 天 |
| `analytics_daily_stats` | 日统计汇总 | 永久 |

---

## 7. 关键设计决策

| 决策 | 选择 | 原因 |
|------|------|------|
| 埋点方式 | 异步队列 + 批量写入 | 不阻塞业务流程 |
| 实时数据 | Redis Hash | 原子计数、高性能 |
| 历史数据 | PostgreSQL | 复杂查询、持久化 |
| 聚合策略 | 定时任务 | 避免实时计算压力 |
| 事件保留 | 90 天 | 平衡存储成本和分析需求 |

---

## 8. 文档更新记录

| 日期 | 变更内容 |
|------|----------|
| 2025-12-25 | 初始版本 |
