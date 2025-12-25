# 数据埋点服务 - 实现计划

> **版本**: v4.0
> **创建日期**: 2025-12-25
> **方法论**: Vibe Coding 分步骤开发
> **预计步骤数**: 15 步
> **核心目标**: 为 AI 客服 + 坐席工作台添加埋点，收集商业案例数据

---

## 一、开发原则

1. **自底向上**: infrastructure → services → products 接入
2. **增量开发**: 每步只做一件事，立即测试验证
3. **商业导向**: 数据采集服务于商业案例制作
4. **异步非阻塞**: 埋点不影响业务性能

---

## 二、埋点位置分析（基于现有代码）

### 2.1 AI 客服埋点位置

| 文件 | 埋点事件 | 商业价值 |
|------|----------|----------|
| `chat.py:79-296` 同步聊天 | session.start, session.message, session.end | 服务量、响应速度 |
| `chat.py:316-571` 流式聊天 | 同上 | 同上 |
| `chat.py:270-287` 转人工触发 | session.escalate | AI 解决率 |
| `tracking.py` 物流查询 | query.tracking | 查询成功率 |
| `services/shopify/` 订单查询 | query.order | 查询成功率 |

### 2.2 坐席工作台埋点位置

| 文件 | 埋点事件 | 商业价值 |
|------|----------|----------|
| `auth.py:agent_login` | agent.login | 工作时长统计 |
| `auth.py:agent_logout` | agent.logout | 工作时长统计 |
| `auth.py:update_agent_status` | agent.status_change | 在线状态分析 |
| `sessions.py:takeover_session` | agent.session_takeover | 响应速度 |
| `sessions.py:agent_send_message` | agent.session_message | 消息量统计 |
| `sessions.py:release_session` | agent.session_release | 处理效率 |
| `sessions.py:transfer_session` | agent.session_transfer | 转接分析 |
| `tickets.py:create_ticket` | ticket.created | 工单来源 |
| `tickets.py:assign_ticket` | ticket.assigned | 分配效率 |
| `tickets.py:update_ticket` | ticket.status_changed | 状态流转 |
| `tickets.py:close_ticket` | ticket.closed | SLA 达标率 |

---

## Step 1: 创建数据库表

**任务描述：**
创建 PostgreSQL 表存储商业指标和事件明细

**涉及文件：**
- `infrastructure/database/migrations/003_analytics_tables.sql`（新增）

**改动：**
```sql
-- 商业指标汇总表
CREATE TABLE analytics_business_metrics (
    id SERIAL PRIMARY KEY,
    period_type VARCHAR(10) NOT NULL,
    period_value VARCHAR(10) NOT NULL,
    -- AI 客服指标
    total_sessions INT DEFAULT 0,
    ai_resolved_sessions INT DEFAULT 0,
    escalated_sessions INT DEFAULT 0,
    total_messages INT DEFAULT 0,
    avg_response_time_ms INT DEFAULT 0,
    order_queries_success INT DEFAULT 0,
    order_queries_failed INT DEFAULT 0,
    tracking_queries_success INT DEFAULT 0,
    tracking_queries_failed INT DEFAULT 0,
    -- 坐席工作台指标
    agent_logins INT DEFAULT 0,
    total_work_minutes INT DEFAULT 0,
    sessions_handled INT DEFAULT 0,
    avg_handle_time_sec INT DEFAULT 0,
    avg_first_response_ms INT DEFAULT 0,
    agent_messages_sent INT DEFAULT 0,
    sessions_transferred INT DEFAULT 0,
    -- 工单指标
    tickets_created INT DEFAULT 0,
    tickets_closed INT DEFAULT 0,
    tickets_sla_met INT DEFAULT 0,
    avg_resolution_hours DECIMAL(5,2) DEFAULT 0,
    -- 商业价值
    ai_resolution_rate DECIMAL(5,2),
    sla_met_rate DECIMAL(5,2),
    estimated_cost_saved DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (period_type, period_value)
);

-- 事件明细表
CREATE TABLE analytics_events (
    id BIGSERIAL PRIMARY KEY,
    event_name VARCHAR(50) NOT NULL,
    session_id VARCHAR(64),
    agent_id INT,
    ticket_id INT,
    event_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_events_name ON analytics_events(event_name);
CREATE INDEX idx_events_session ON analytics_events(session_id);
CREATE INDEX idx_events_agent ON analytics_events(agent_id);
CREATE INDEX idx_events_ticket ON analytics_events(ticket_id);
CREATE INDEX idx_events_created ON analytics_events(created_at);
```

**测试方法：**
```bash
# 在服务器执行
psql -U fiido -d fiido_db -f infrastructure/database/migrations/003_analytics_tables.sql
psql -U fiido -d fiido_db -c "\dt analytics_*"
```

**预期结果：** 2 张表创建成功

**状态：** ⬜ 待开发

---

## Step 2: 创建配置和模型

**任务描述：**
创建埋点服务的配置类和数据模型

**涉及文件：**
- `services/analytics/__init__.py`（新增）
- `services/analytics/config.py`（新增）
- `services/analytics/models.py`（新增）

**改动：**
- `AnalyticsConfig`: buffer_size, flush_interval, cost_per_manual_session
- `AnalyticsEvent`: event_name, session_id, data, timestamp
- `BusinessMetrics`: 商业指标数据类

**测试方法：**
```bash
python3 -c "from services.analytics.config import AnalyticsConfig; print(AnalyticsConfig())"
```

**预期结果：** 配置类实例化成功

**状态：** ⬜ 待开发

---

## Step 3: 实现埋点追踪器

**任务描述：**
实现异步埋点追踪器，支持批量写入

**涉及文件：**
- `services/analytics/tracker.py`（新增）

**改动：**
```python
class AnalyticsTracker:
    async def track(self, event_name: str, data: dict)
    async def start(self)
    async def stop(self)
    async def _flush(self)
    async def _update_redis_counters(self, event_name: str, data: dict)

_tracker_instance: AnalyticsTracker = None

def get_tracker() -> AnalyticsTracker
def init_tracker(redis, pg_pool, config) -> AnalyticsTracker
```

**测试方法：**
```bash
python3 -c "
import asyncio
from services.analytics.tracker import AnalyticsTracker
from services.analytics.config import AnalyticsConfig

async def test():
    tracker = AnalyticsTracker(redis=None, pg_pool=None, config=AnalyticsConfig())
    await tracker.track('test.event', {'key': 'value'})
    print(f'Buffer size: {tracker.buffer.qsize()}')

asyncio.run(test())
"
```

**预期结果：** 事件成功入队

**状态：** ⬜ 待开发

---

## Step 4: 实现商业指标统计

**任务描述：**
实现商业案例数据查询接口

**涉及文件：**
- `services/analytics/stats.py`（新增）

**改动：**
```python
class BusinessStats:
    async def get_monthly_summary(self, month: str) -> dict
        # 返回: 总服务量、AI解决率、响应速度、成本节省

    async def get_case_study_data(self, start_date: str, end_date: str) -> dict
        # 返回: 商业案例完整数据包

    async def get_query_success_rates(self) -> dict
        # 返回: 订单/物流查询成功率
```

**测试方法：**
```bash
python3 -c "from services.analytics.stats import BusinessStats; print('OK')"
```

**预期结果：** 类创建成功

**状态：** ⬜ 待开发

---

## Step 5: 更新模块导出

**任务描述：**
创建 `__init__.py`，统一导出公开接口

**涉及文件：**
- `services/analytics/__init__.py`（修改）

**改动：**
```python
from .config import AnalyticsConfig
from .models import AnalyticsEvent, BusinessMetrics
from .tracker import AnalyticsTracker, get_tracker, init_tracker
from .stats import BusinessStats

__all__ = [
    'AnalyticsConfig',
    'AnalyticsEvent',
    'BusinessMetrics',
    'AnalyticsTracker',
    'get_tracker',
    'init_tracker',
    'BusinessStats',
]
```

**测试方法：**
```bash
python3 -c "from services.analytics import get_tracker, BusinessStats; print('All exports OK')"
```

**预期结果：** 所有导入成功

**状态：** ⬜ 待开发

---

## Step 6: AI 客服 - 初始化埋点

**任务描述：**
在 AI 客服启动时初始化埋点追踪器

**涉及文件：**
- `products/ai_chatbot/lifespan.py`（修改）
- `products/ai_chatbot/dependencies.py`（修改，添加 get_tracker）

**改动：**
```python
# lifespan.py
from services.analytics import init_tracker

async def lifespan(app):
    # ... 现有初始化 ...

    # 初始化埋点
    tracker = init_tracker(
        redis=app.state.redis,
        pg_pool=app.state.pg_pool,
        config=AnalyticsConfig()
    )
    await tracker.start()
    app.state.tracker = tracker

    yield

    await tracker.stop()
```

**测试方法：**
```bash
# 启动服务，检查日志
uvicorn products.ai_chatbot.main:app --port 8000
# 应看到 "Analytics tracker started" 日志
```

**预期结果：** 服务启动时埋点初始化成功

**状态：** ⬜ 待开发

---

## Step 7: AI 客服 - 聊天埋点

**任务描述：**
在聊天接口添加埋点

**涉及文件：**
- `products/ai_chatbot/handlers/chat.py`（修改）

**埋点位置：**

```python
# 同步聊天接口 chat() - 约 line 81
@router.post("/chat")
async def chat(chat_request: ChatRequest, request: Request):
    tracker = get_tracker()
    start_time = time.time()

    # 【埋点】会话开始
    await tracker.track("session.start", {
        "session_id": session_id,
        "channel": "api",
    })

    # ... 现有业务逻辑 ...

    # 【埋点】AI 回复（约 line 296 之前）
    response_time = int((time.time() - start_time) * 1000)
    await tracker.track("session.message", {
        "session_id": session_id,
        "role": "ai",
        "message_length": len(final_message),
        "response_time_ms": response_time,
    })

    # 【埋点】转人工（在 regulator_result.should_escalate 块内，约 line 270）
    if regulator_result.should_escalate:
        await tracker.track("session.escalate", {
            "session_id": session_id,
            "reason": regulator_result.reason,
            "severity": regulator_result.severity,
        })
```

**测试方法：**
```bash
# 发送测试消息
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"hello","user_id":"test-123"}'

# 检查 Redis
redis-cli HGETALL analytics:daily:$(date +%Y-%m-%d)
```

**预期结果：** Redis 中有 total_sessions、total_messages 计数

**状态：** ⬜ 待开发

---

## Step 8: AI 客服 - 物流查询埋点

**任务描述：**
在物流查询接口添加埋点

**涉及文件：**
- `products/ai_chatbot/handlers/tracking.py`（修改）

**埋点位置：**
```python
# 在查询结果返回处
await tracker.track("query.tracking", {
    "session_id": session_id,
    "tracking_number": tracking_number,
    "carrier": carrier_code,
    "success": True/False,
    "status": tracking_status,
})
```

**测试方法：**
```bash
curl http://localhost:8000/api/tracking/TEST123456

redis-cli HGETALL analytics:daily:$(date +%Y-%m-%d)
# 应看到 tracking_queries_success 或 tracking_queries_failed
```

**预期结果：** 物流查询埋点正常记录

**状态：** ⬜ 待开发

---

## Step 9: 订单查询埋点

**任务描述：**
在 Shopify 订单查询服务添加埋点

**涉及文件：**
- `services/shopify/client.py`（修改）

**埋点位置：**
```python
# 在 query_order() 方法返回处
await tracker.track("query.order", {
    "session_id": session_id,
    "order_number": order_number,
    "site": site_name,
    "success": True/False,
    "response_time_ms": response_time,
})
```

**测试方法：**
```bash
# 通过聊天触发订单查询
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"查询订单 FD12345","user_id":"test-123"}'

redis-cli HGETALL analytics:daily:$(date +%Y-%m-%d)
```

**预期结果：** 订单查询埋点正常记录

**状态：** ⬜ 待开发

---

## Step 10: 商业案例 API 接口

**任务描述：**
添加商业案例数据查询 API

**涉及文件：**
- `products/ai_chatbot/handlers/analytics.py`（新增）
- `products/ai_chatbot/routes.py`（修改）

**API 设计：**
```python
# GET /api/analytics/case-study?month=2025-12
{
    "period": "2025年12月",
    "highlights": {
        "total_customers_served": 5420,
        "ai_resolution_rate": "85.3%",
        "avg_response_time": "1.5秒",
        "cost_saved": "¥54,200",
        "order_query_success_rate": "98.2%",
        "tracking_query_success_rate": "96.8%"
    },
    "story": "本月 AI 客服共服务 5,420 位客户..."
}
```

**测试方法：**
```bash
curl http://localhost:8000/api/analytics/case-study?month=2025-12
```

**预期结果：** 返回格式化的商业案例数据

**状态：** ⬜ 待开发

---

## Step 11: 坐席工作台 - 初始化埋点

**任务描述：**
在坐席工作台启动时初始化埋点追踪器

**涉及文件：**
- `products/agent_workbench/lifespan.py`（修改）
- `products/agent_workbench/dependencies.py`（修改，添加 get_tracker）

**改动：**
```python
# lifespan.py
from services.analytics import init_tracker, AnalyticsConfig

async def lifespan(app):
    # ... 现有初始化 ...

    # 初始化埋点
    tracker = init_tracker(
        redis=app.state.redis,
        pg_pool=app.state.pg_pool,
        config=AnalyticsConfig()
    )
    await tracker.start()
    app.state.tracker = tracker

    yield

    await tracker.stop()
```

**测试方法：**
```bash
# 启动服务，检查日志
uvicorn products.agent_workbench.main:app --port 8002
# 应看到 "Analytics tracker started" 日志
```

**预期结果：** 坐席工作台启动时埋点初始化成功

**状态：** ⬜ 待开发

---

## Step 12: 坐席工作台 - 认证埋点

**任务描述：**
在坐席登录/登出/状态切换时添加埋点

**涉及文件：**
- `products/agent_workbench/handlers/auth.py`（修改）

**埋点位置：**
```python
# 在 agent_login() 成功后
await tracker.track("agent.login", {
    "agent_id": agent.id,
    "agent_name": agent.name,
})

# 在 agent_logout() 成功后
await tracker.track("agent.logout", {
    "agent_id": agent.id,
    "work_duration_minutes": work_duration,
    "sessions_handled": sessions_count,
})

# 在 update_agent_status_api() 成功后
await tracker.track("agent.status_change", {
    "agent_id": agent.id,
    "from_status": old_status,
    "to_status": new_status,
})
```

**测试方法：**
```bash
# 登录坐席
curl -X POST http://localhost:8002/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"agent1","password":"xxx"}'

# 检查 Redis
redis-cli HGETALL analytics:agent:daily:$(date +%Y-%m-%d)
```

**预期结果：** agent_logins 计数增加

**状态：** ⬜ 待开发

---

## Step 13: 坐席工作台 - 会话服务埋点

**任务描述：**
在会话接管/释放/转接/发消息时添加埋点

**涉及文件：**
- `products/agent_workbench/handlers/sessions.py`（修改）

**埋点位置：**
```python
# 在 takeover_session() 成功后
await tracker.track("agent.session_takeover", {
    "agent_id": agent_id,
    "session_id": session_id,
    "wait_duration_seconds": wait_time,
})

# 在 agent_send_message() 成功后
await tracker.track("agent.session_message", {
    "agent_id": agent_id,
    "session_id": session_id,
    "message_length": len(message),
})

# 在 release_session() 成功后
await tracker.track("agent.session_release", {
    "agent_id": agent_id,
    "session_id": session_id,
    "handle_duration_seconds": handle_time,
    "message_count": msg_count,
})

# 在 transfer_session() 成功后
await tracker.track("agent.session_transfer", {
    "agent_id": agent_id,
    "session_id": session_id,
    "target_agent_id": target_id,
    "reason": transfer_reason,
})
```

**测试方法：**
```bash
# 接管会话
curl -X POST http://localhost:8002/api/sessions/{session_id}/takeover \
  -H "Authorization: Bearer xxx"

# 检查 Redis
redis-cli HGETALL analytics:agent:daily:$(date +%Y-%m-%d)
```

**预期结果：** sessions_handled 计数增加

**状态：** ⬜ 待开发

---

## Step 14: 坐席工作台 - 工单埋点

**任务描述：**
在工单创建/分配/状态变更/关闭时添加埋点

**涉及文件：**
- `products/agent_workbench/handlers/tickets.py`（修改）

**埋点位置：**
```python
# 在 create_ticket_endpoint() 成功后
await tracker.track("ticket.created", {
    "ticket_id": ticket.id,
    "source": ticket.source,
    "type": ticket.type,
    "priority": ticket.priority,
    "agent_id": current_agent.id,
})

# 在 assign_ticket_endpoint() 成功后
await tracker.track("ticket.assigned", {
    "ticket_id": ticket_id,
    "from_agent_id": old_assignee,
    "to_agent_id": new_assignee,
})

# 在 update_ticket_endpoint() 状态变更时
if old_status != new_status:
    await tracker.track("ticket.status_changed", {
        "ticket_id": ticket_id,
        "from_status": old_status,
        "to_status": new_status,
        "agent_id": current_agent.id,
    })

# 在工单关闭时
await tracker.track("ticket.closed", {
    "ticket_id": ticket_id,
    "resolution_duration_hours": resolution_hours,
    "sla_met": is_sla_met,
})
```

**测试方法：**
```bash
# 创建工单
curl -X POST http://localhost:8002/api/tickets \
  -H "Authorization: Bearer xxx" \
  -d '{"subject":"test","type":"inquiry"}'

# 检查 Redis
redis-cli HGETALL analytics:agent:daily:$(date +%Y-%m-%d)
```

**预期结果：** tickets_created 计数增加

**状态：** ⬜ 待开发

---

## Step 15: 扩展商业案例 API

**任务描述：**
扩展商业案例 API，包含坐席工作台指标

**涉及文件：**
- `products/ai_chatbot/handlers/analytics.py`（修改）
- `services/analytics/stats.py`（修改）

**API 扩展：**
```python
# GET /api/analytics/case-study?month=2025-12
{
    "period": "2025年12月",
    "ai_chatbot": {
        "total_customers_served": 5420,
        "ai_resolution_rate": "85.3%",
        "avg_response_time": "1.5秒",
        "cost_saved": "¥54,200",
        "order_query_success_rate": "98.2%",
        "tracking_query_success_rate": "96.8%"
    },
    "agent_workbench": {
        "sessions_handled": 812,
        "avg_first_response": "30秒",
        "avg_handle_time": "8分钟",
        "tickets_resolved": 156,
        "avg_resolution_time": "4小时",
        "sla_met_rate": "95.2%"
    },
    "story": "本月 AI 客服共服务 5,420 位客户..."
}
```

**测试方法：**
```bash
curl http://localhost:8000/api/analytics/case-study?month=2025-12
```

**预期结果：** 返回包含坐席工作台指标的完整商业案例数据

**状态：** ⬜ 待开发

---

## 三、商业指标计算公式

### 3.1 AI 客服指标

| 指标 | 公式 | 说明 |
|------|------|------|
| AI 解决率 | `ai_resolved / total_sessions × 100` | 越高越好 |
| 转人工率 | `escalated / total_sessions × 100` | 越低越好 |
| 平均响应时间 | `total_response_time / total_messages` | 单位 ms |
| 成本节省 | `ai_resolved × ¥10` | 假设单次人工成本 ¥10 |
| 订单查询成功率 | `order_success / (order_success + order_failed) × 100` | |
| 物流查询成功率 | `tracking_success / (tracking_success + tracking_failed) × 100` | |

### 3.2 坐席工作台指标

| 指标 | 公式 | 说明 |
|------|------|------|
| 平均首次响应时间 | `total_first_response_ms / sessions_handled` | 越短越好 |
| 平均会话处理时长 | `total_handle_time_sec / sessions_handled` | 效率指标 |
| 坐席人均消息数 | `agent_messages_sent / sessions_handled` | 服务深度 |
| 转接率 | `sessions_transferred / sessions_handled × 100` | 越低越好 |

### 3.3 工单指标

| 指标 | 公式 | 说明 |
|------|------|------|
| 工单解决率 | `tickets_closed / tickets_created × 100` | |
| 平均解决时长 | `total_resolution_hours / tickets_closed` | 小时 |
| SLA 达标率 | `tickets_sla_met / tickets_closed × 100` | 越高越好 |

---

## 四、开发检查清单

每个 Step 完成后：

- [ ] 代码无语法错误
- [ ] 按验证方法测试通过
- [ ] 不破坏现有功能
- [ ] 更新 `progress.md` 状态
- [ ] Git 提交

---

## 五、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v4.0 | 2025-12-25 | 扩展坐席工作台埋点：Step 11-15，共 15 步 |
| v3.0 | 2025-12-25 | 完全重写：10 步聚焦现有功能埋点，删除坐席工作台 UI 内容 |
