# 数据埋点服务 - 技术栈

> **版本**: v4.0
> **创建日期**: 2025-12-25
> **模块位置**: `services/analytics/`

---

## 1. 复用现有技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 产品层 | FastAPI | products/ai_chatbot + agent_workbench（埋点调用方）|
| 服务层 | Python 异步 | services/analytics（本模块）|
| 基础设施层 | infrastructure/bootstrap | 组件工厂、依赖注入 |
| 数据存储 | Redis + PostgreSQL | 双写策略 |

---

## 2. 新增依赖

**无需新增依赖**

---

## 3. 商业案例导向的数据设计

### 3.1 核心商业指标（Case Study Anchors）

| 商业指标 | 计算方式 | 展示口径 |
|----------|----------|----------|
| **月度服务量** | 累计会话数 | "本月 AI 客服服务了 5,000+ 客户" |
| **AI 自主解决率** | AI 独立解决 / 总会话 | "85% 的问题由 AI 独立解决" |
| **AI 响应速度** | 总响应时间 / 回复数 | "平均 1.5 秒内响应" |
| **坐席响应速度** | 接管后首次回复时间 | "人工接管后 30 秒内响应" |
| **坐席处理效率** | 平均会话处理时长 | "人均处理时长 8 分钟" |
| **工单解决效率** | 平均工单解决时长 | "工单平均 4 小时内解决" |
| **工单 SLA 达标率** | 达标工单 / 总工单 | "SLA 达标率 95%" |
| **人工成本节省** | AI 解决数 × 单次人工成本 | "月节省人工成本 ¥50,000" |
| **查询成功率** | 成功查询 / 总查询 | "订单查询成功率 98%" |

### 3.2 Redis 结构（实时聚合）

```redis
# AI 客服指标聚合（按月）
analytics:monthly:2025-12
    ├── total_sessions          # 总服务量
    ├── ai_resolved_sessions    # AI 独立解决
    ├── escalated_sessions      # 转人工数
    ├── total_messages          # 消息总数
    ├── total_response_time_ms  # 响应时间累计
    ├── order_queries_success   # 订单查询成功
    ├── order_queries_failed    # 订单查询失败
    ├── tracking_queries_success # 物流查询成功
    └── tracking_queries_failed  # 物流查询失败

# 坐席工作台指标聚合（按月）
analytics:agent:monthly:2025-12
    ├── agent_logins            # 坐席登录次数
    ├── total_work_minutes      # 累计工作时长（分钟）
    ├── sessions_handled        # 处理会话数
    ├── total_handle_time_sec   # 累计会话处理时长（秒）
    ├── total_first_response_ms # 累计首次响应时间（毫秒）
    ├── agent_messages_sent     # 坐席发送消息数
    ├── sessions_transferred    # 转接会话数
    ├── tickets_created         # 创建工单数
    ├── tickets_closed          # 关闭工单数
    ├── tickets_sla_met         # SLA 达标工单数
    └── total_resolution_hours  # 累计工单解决时长（小时）

# 日统计（用于趋势）
analytics:daily:2025-12-25
    └── [同上字段]
```

### 3.3 PostgreSQL 表结构

```sql
-- 商业指标汇总表（核心）
CREATE TABLE analytics_business_metrics (
    id SERIAL PRIMARY KEY,
    period_type VARCHAR(10) NOT NULL,  -- daily, monthly
    period_value VARCHAR(10) NOT NULL, -- 2025-12-25 或 2025-12

    -- AI 客服服务量指标
    total_sessions INT DEFAULT 0,
    ai_resolved_sessions INT DEFAULT 0,
    escalated_sessions INT DEFAULT 0,

    -- AI 效率指标
    total_messages INT DEFAULT 0,
    avg_response_time_ms INT DEFAULT 0,

    -- 查询成功率
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

    -- 商业价值（计算字段）
    ai_resolution_rate DECIMAL(5,2),     -- AI 解决率 %
    sla_met_rate DECIMAL(5,2),           -- SLA 达标率 %
    estimated_cost_saved DECIMAL(10,2),  -- 预估节省成本

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE (period_type, period_value)
);

-- 事件明细表（追溯用）
CREATE TABLE analytics_events (
    id BIGSERIAL PRIMARY KEY,
    event_name VARCHAR(50) NOT NULL,
    session_id VARCHAR(64),
    agent_id INT,                        -- 新增：坐席 ID
    ticket_id INT,                       -- 新增：工单 ID
    event_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_events_name ON analytics_events(event_name);
CREATE INDEX idx_events_session ON analytics_events(session_id);
CREATE INDEX idx_events_agent ON analytics_events(agent_id);
CREATE INDEX idx_events_ticket ON analytics_events(ticket_id);
CREATE INDEX idx_events_created ON analytics_events(created_at);
```

---

## 4. 核心类设计

```python
# services/analytics/tracker.py
class AnalyticsTracker:
    """埋点追踪器"""

    async def track(self, event_name: str, data: dict):
        """记录事件（异步非阻塞）"""

    async def start(self):
        """启动后台任务"""

    async def stop(self):
        """停止并刷新"""

# services/analytics/stats.py
class BusinessStats:
    """商业指标统计"""

    async def get_monthly_summary(self, month: str) -> dict:
        """获取月度商业摘要（用于 Case Study）"""
        # 返回: AI服务量、解决率、响应速度、成本节省
        #       坐席效率、工单处理、SLA达标率

    async def get_daily_trend(self, days: int = 30) -> list:
        """获取日趋势数据"""

    async def get_query_success_rates(self) -> dict:
        """获取查询成功率"""

    async def get_agent_performance(self, month: str) -> dict:
        """获取坐席效能数据"""

    async def get_ticket_metrics(self, month: str) -> dict:
        """获取工单处理指标"""
```

---

## 5. 商业案例输出示例

```json
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
  "story": "本月 AI 客服共服务 5,420 位客户，其中 85.3% 的问题由 AI 独立解决，平均响应时间仅 1.5 秒。需人工介入的 812 个会话，坐席平均 30 秒内响应，8 分钟内解决。共处理 156 个工单，平均 4 小时解决，SLA 达标率 95.2%。预估节省人工成本 ¥54,200。"
}
```

---

## 6. 文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v4.0 | 2025-12-25 | 扩展坐席工作台指标：坐席效能、会话处理、工单 SLA |
| v3.0 | 2025-12-25 | 重写：聚焦商业案例指标，删除 UI 相关内容 |
