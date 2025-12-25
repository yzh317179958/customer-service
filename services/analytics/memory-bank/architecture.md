# 数据埋点服务 - 架构说明

> **版本**: v4.0
> **模块位置**: `services/analytics/`
> **最后更新**: 2025-12-25
> **遵循规范**: CLAUDE.md 三层架构

---

## 1. 模块定位

### 1.1 三层架构位置

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           products/ 产品层                                   │
│                                                                              │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────────┐   │
│  │     AI 智能客服 (ai_chatbot)     │  │   坐席工作台 (agent_workbench)   │   │
│  │                                  │  │                                  │   │
│  │  chat.py ──────────┐             │  │  auth.py ─────────┐              │   │
│  │  tracking.py ──────┼──► track()  │  │  sessions.py ─────┼──► track()   │   │
│  │  lifespan.py ──────┘             │  │  tickets.py ──────┘              │   │
│  └──────────────────────────────────┘  └──────────────────────────────────┘   │
│                         │                              │                      │
│                         └──────────────┬───────────────┘                      │
│                                        │ import                               │
│                                        ▼                                      │
├───────────────────────────────────────────────────────────────────────────────┤
│                         services/analytics/ 【本模块】                         │
│                                                                               │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                    │
│   │  tracker.py │     │  stats.py   │     │  models.py  │                    │
│   │  埋点追踪器  │     │  商业统计    │     │  数据模型   │                    │
│   └──────┬──────┘     └──────┬──────┘     └─────────────┘                    │
│          │                   │                                                │
├──────────┼───────────────────┼────────────────────────────────────────────────┤
│          │                   │                                                │
│          ▼                   ▼                                                │
│   ┌─────────────────────────────────────────┐                                 │
│   │         infrastructure/database          │                                 │
│   │         Redis + PostgreSQL               │                                 │
│   └─────────────────────────────────────────┘                                 │
└───────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 模块职责

| 职责 | 说明 |
|------|------|
| **被依赖** | products/ai_chatbot + products/agent_workbench 调用埋点 API |
| **依赖** | infrastructure/database (Redis + PostgreSQL) |
| **核心功能** | 收集 AI 客服 + 坐席工作台运营数据，输出商业案例指标 |

---

## 2. 文件结构

```
services/analytics/
├── __init__.py          # 统一导出
├── config.py            # 配置类
├── models.py            # 数据模型
├── tracker.py           # 埋点追踪器（核心）
├── stats.py             # 商业指标统计
└── memory-bank/         # 开发文档
    ├── prd.md
    ├── tech-stack.md
    ├── implementation-plan.md
    ├── progress.md
    └── architecture.md   # 本文件
```

---

## 3. 数据流

### 3.1 AI 客服埋点写入流程

```
AI 客服业务代码
      │
      │ await tracker.track("session.start", {...})
      ▼
┌─────────────────────────────────────┐
│       AnalyticsTracker              │
│                                     │
│  ┌─────────────────────────────┐    │
│  │   asyncio.Queue (缓冲区)    │    │ ◄── 非阻塞，不影响业务
│  │   buffer_size: 1000        │    │
│  └─────────────┬───────────────┘    │
│                │                     │
│                ▼ 后台任务（每 5 秒）  │
│           _flush()                   │
└────────────────┬────────────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
    ▼                         ▼
┌──────────────┐      ┌──────────────┐
│    Redis     │      │  PostgreSQL  │
│   实时计数    │      │   事件明细   │
│              │      │              │
│ analytics:   │      │ analytics_   │
│ daily:{date} │      │ events       │
│ monthly:{m}  │      │              │
└──────────────┘      └──────────────┘
```

### 3.2 坐席工作台埋点写入流程

```
坐席工作台业务代码
      │
      │ await tracker.track("agent.login", {...})
      │ await tracker.track("agent.session_takeover", {...})
      │ await tracker.track("ticket.created", {...})
      ▼
┌─────────────────────────────────────┐
│       AnalyticsTracker (共享)        │
│                                     │
│  ┌─────────────────────────────┐    │
│  │   asyncio.Queue (缓冲区)    │    │
│  └─────────────┬───────────────┘    │
│                │                     │
│                ▼ 后台任务（每 5 秒）  │
│           _flush()                   │
└────────────────┬────────────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
    ▼                         ▼
┌──────────────┐      ┌──────────────┐
│    Redis     │      │  PostgreSQL  │
│   实时计数    │      │   事件明细   │
│              │      │              │
│ analytics:   │      │ analytics_   │
│ agent:daily  │      │ events       │
│ agent:monthly│      │              │
└──────────────┘      └──────────────┘
```

### 3.3 统计查询流程

```
商业案例 API 请求
      │
      │ GET /api/analytics/case-study?month=2025-12
      ▼
┌─────────────────────────────────────┐
│         BusinessStats               │
│                                     │
│  get_monthly_summary()              │  ◄── AI 客服指标
│  get_agent_performance()            │  ◄── 坐席效能指标
│  get_ticket_metrics()               │  ◄── 工单处理指标
│  get_case_study_data()              │  ◄── 完整商业案例
└────────────────┬────────────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
    ▼                         ▼
┌──────────────┐      ┌──────────────┐
│    Redis     │      │  PostgreSQL  │
│   当月计数    │      │   汇总表     │
└──────────────┘      └──────────────┘
                 │
                 ▼
        ┌─────────────────┐
        │   商业案例输出   │
        │                 │
        │ "本月 AI 客服   │
        │  服务 5,420 位  │
        │  客户，坐席处理 │
        │  812 个会话..." │
        └─────────────────┘
```

---

## 4. 核心事件定义

### 4.1 AI 客服事件

| 事件名 | 触发位置 | 商业含义 |
|--------|----------|----------|
| `session.start` | chat.py 会话开始 | 服务了一位客户 |
| `session.message` | chat.py 每轮对话 | AI 响应效率 |
| `session.escalate` | chat.py 转人工 | AI 无法解决的问题 |
| `session.end` | chat.py 会话结束 | 会话完成 |
| `query.order` | shopify 订单查询 | 订单服务能力 |
| `query.tracking` | tracking.py 物流查询 | 物流服务能力 |

### 4.2 坐席工作台事件

| 事件名 | 触发位置 | 商业含义 |
|--------|----------|----------|
| `agent.login` | auth.py 登录 | 工作时长统计 |
| `agent.logout` | auth.py 登出 | 工作时长统计 |
| `agent.status_change` | auth.py 状态切换 | 在线状态分析 |
| `agent.session_takeover` | sessions.py 接管 | 响应速度 |
| `agent.session_message` | sessions.py 发消息 | 消息量统计 |
| `agent.session_release` | sessions.py 释放 | 处理效率 |
| `agent.session_transfer` | sessions.py 转接 | 转接分析 |

### 4.3 工单事件

| 事件名 | 触发位置 | 商业含义 |
|--------|----------|----------|
| `ticket.created` | tickets.py 创建 | 工单来源 |
| `ticket.assigned` | tickets.py 分配 | 分配效率 |
| `ticket.status_changed` | tickets.py 状态变更 | 状态流转 |
| `ticket.closed` | tickets.py 关闭 | SLA 达标率 |

---

## 5. 商业指标输出

### 5.1 核心指标

| 分类 | 指标 | 计算公式 | 商业价值 |
|------|------|----------|----------|
| AI 客服 | 月度服务量 | COUNT(session.start) | 规模证明 |
| AI 客服 | AI 解决率 | (总会话 - 转人工) / 总会话 | AI 能力证明 |
| AI 客服 | 平均响应时间 | AVG(response_time_ms) | 效率证明 |
| AI 客服 | 成本节省 | AI 解决数 × ¥10 | ROI 证明 |
| 坐席 | 处理会话数 | COUNT(agent.session_takeover) | 人效统计 |
| 坐席 | 平均首次响应 | AVG(wait_duration_seconds) | 服务质量 |
| 坐席 | 平均处理时长 | AVG(handle_duration_seconds) | 处理效率 |
| 工单 | 工单解决量 | COUNT(ticket.closed) | 服务能力 |
| 工单 | 平均解决时长 | AVG(resolution_duration_hours) | 处理效率 |
| 工单 | SLA 达标率 | SUM(sla_met) / COUNT(closed) | 服务承诺 |

### 5.2 输出格式

```json
{
  "period": "2025年12月",
  "ai_chatbot": {
    "total_customers_served": 5420,
    "ai_resolution_rate": "85.3%",
    "avg_response_time": "1.5秒",
    "cost_saved": "¥54,200"
  },
  "agent_workbench": {
    "sessions_handled": 812,
    "avg_first_response": "30秒",
    "avg_handle_time": "8分钟"
  },
  "tickets": {
    "tickets_resolved": 156,
    "avg_resolution_time": "4小时",
    "sla_met_rate": "95.2%"
  },
  "story": "本月 AI 客服共服务 5,420 位客户，其中 85.3% 的问题由 AI 独立解决，平均响应时间仅 1.5 秒。需人工介入的 812 个会话，坐席平均 30 秒内响应，8 分钟内解决。共处理 156 个工单，平均 4 小时解决，SLA 达标率 95.2%。预估节省人工成本 ¥54,200。"
}
```

---

## 6. 关键设计决策

| 决策 | 选择 | 原因 |
|------|------|------|
| 埋点方式 | 异步队列 + 批量写入 | 不阻塞业务流程 |
| 实时数据 | Redis Hash | 原子计数、高性能 |
| 历史数据 | PostgreSQL | 持久化、复杂查询 |
| 商业指标 | 服务端计算 | 统一口径、便于调整 |
| 成本假设 | ¥10/次 | 可配置，后续可调整 |
| 两产品共享 | 同一 Tracker 实例 | 统一数据源、简化管理 |

---

## 7. 文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v4.0 | 2025-12-25 | 扩展坐席工作台：添加认证、会话、工单事件，更新架构图 |
| v3.0 | 2025-12-25 | 完全重写：聚焦商业案例数据，删除坐席工作台 UI 相关内容 |
