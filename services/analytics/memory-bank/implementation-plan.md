# 数据分析服务 - 实现计划

> **版本**: v2.0
> **创建日期**: 2025-12-25
> **方法论**: Vibe Coding 分步骤开发
> **预计步骤数**: 20 步
> **核心功能步骤**: Step 1-12 (P0)
> **扩展功能步骤**: Step 13-20 (P1)

---

## 一、开发原则

1. **自底向上**: infrastructure → services → products 接入
2. **增量开发**: 每步只做一件事，立即测试验证
3. **频繁提交**: 每个功能点完成即提交
4. **单次提交**: < 10 个文件，< 500 行代码

---

## 二、模块依赖关系

```
services/analytics/
├── tracker/      # 埋点采集（基础，被其他模块依赖）
├── stats/        # 会话/效能统计（依赖 tracker）
├── quality/      # 质检分析（依赖 tracker）
└── billing/      # Token 统计（依赖 tracker）

products/agent_workbench/
├── handlers/analytics.py  # API 路由（依赖 services/analytics）
└── frontend/
    ├── Monitoring.tsx     # 调用 stats API
    ├── Dashboard.tsx      # 调用 stats API
    ├── QualityAudit.tsx   # 调用 quality API
    └── BillingPortal.tsx  # 调用 billing API
```

---

## 三、Phase 1 - P0 核心功能 (Step 1-12)

### Step 1: 创建数据库表

**目标**: 创建所有分析相关的 PostgreSQL 表

**涉及文件**:
- `infrastructure/database/migrations/003_analytics_tables.sql`（新增）

**改动**:
- 创建 `analytics_events` 事件明细表
- 创建 `analytics_daily_stats` 日统计汇总表
- 创建 `analytics_quality_audits` 质检记录表
- 创建 `analytics_token_usage` Token 消耗表
- 创建 `analytics_billing_daily` 计费日汇总表
- 添加必要索引

**验证**:
```bash
psql -U fiido -d fiido_db -f infrastructure/database/migrations/003_analytics_tables.sql
psql -U fiido -d fiido_db -c "\\dt analytics_*"
```

**预期结果**: 5 张表创建成功

**状态**: ⬜ 待开发

---

### Step 2: 创建配置模型

**目标**: 创建埋点服务的配置数据类

**涉及文件**:
- `services/analytics/config.py`（新增）

**改动**:
- 实现 `AnalyticsConfig` 数据类
  - `buffer_size`: 事件缓冲区大小（默认 1000）
  - `flush_interval`: 刷新间隔（默认 5 秒）
  - `retention_days`: 事件明细保留天数（默认 90）
- 支持从环境变量加载

**验证**:
```bash
python3 -c "from services.analytics.config import AnalyticsConfig; print(AnalyticsConfig())"
```

**预期结果**: 配置类实例化成功

**状态**: ⬜ 待开发

---

### Step 3: 定义事件模型

**目标**: 定义埋点事件和统计结果的数据结构

**涉及文件**:
- `services/analytics/models.py`（新增）

**改动**:
- 实现 `AnalyticsEvent` 数据类（事件模型）
- 实现 `RealtimeOverview` 数据类（实时概览）
- 实现 `ChannelStats` 数据类（渠道统计）
- 实现 `AgentStatus` 数据类（坐席状态）
- 实现 `DailyStats` 数据类（日统计）
- 实现 `QualityAuditRecord` 数据类（质检记录）
- 实现 `BillingUsage` 数据类（计费统计）

**验证**:
```bash
python3 -c "from services.analytics.models import AnalyticsEvent; print(AnalyticsEvent.__annotations__)"
```

**预期结果**: 所有模型类定义成功

**状态**: ⬜ 待开发

---

### Step 4: 实现埋点追踪器 (tracker)

**目标**: 创建核心埋点 SDK，支持异步非阻塞

**依赖**: Step 2, 3

**涉及文件**:
- `services/analytics/tracker.py`（新增）

**改动**:
- 实现 `AnalyticsTracker` 类
  - `track(event_name, data, session_id)` - 记录事件（入队列）
  - `start()` - 启动后台刷新任务
  - `stop()` - 停止并刷新剩余事件
  - `flush()` - 批量写入数据库
  - `update_realtime()` - 更新 Redis 实时计数
- 实现 `get_tracker(product)` 单例获取函数
- 实现 `init_tracker(product, redis, pg)` 初始化函数

**验证**:
```bash
python3 -c "
import asyncio
from services.analytics.tracker import AnalyticsTracker
from services.analytics.config import AnalyticsConfig

async def test():
    tracker = AnalyticsTracker('test', config=AnalyticsConfig())
    await tracker.track('test.event', {'key': 'value'})
    print(f'Buffer size: {tracker.buffer.qsize()}')

asyncio.run(test())
"
```

**预期结果**: 事件成功入队，缓冲区大小为 1

**状态**: ⬜ 待开发

---

### Step 5: 实现实时统计 (stats - RealtimeStats)

**目标**: 实现实时大屏的数据查询接口

**依赖**: Step 4

**涉及文件**:
- `services/analytics/stats.py`（新增）

**改动**:
- 实现 `RealtimeStats` 类
  - `get_overview()` - 获取核心指标概览
  - `get_channels()` - 获取渠道流量分布
  - `get_agents()` - 获取坐席状态列表
  - `update_agent_status(agent_id, status)` - 更新坐席状态

**验证**:
```bash
python3 -c "
from services.analytics.stats import RealtimeStats
stats = RealtimeStats(redis=None)
print('RealtimeStats created successfully')
"
```

**预期结果**: 类创建成功

**状态**: ⬜ 待开发

---

### Step 6: 实现效能统计 (stats - DashboardStats)

**目标**: 实现效能报表的数据查询接口

**依赖**: Step 1, 4

**涉及文件**:
- `services/analytics/stats.py`（修改）

**改动**:
- 实现 `DashboardStats` 类
  - `get_today_stats()` - 获取今日统计
  - `get_trend(days=7)` - 获取趋势数据
  - `get_satisfaction()` - 获取满意度分布

**验证**:
```bash
python3 -c "
from services.analytics.stats import DashboardStats
stats = DashboardStats(redis=None, pg=None)
print('DashboardStats created successfully')
"
```

**预期结果**: 类创建成功

**状态**: ⬜ 待开发

---

### Step 7: 实现质检服务 (quality)

**目标**: 实现智能质检的数据查询和记录接口

**依赖**: Step 1, 3

**涉及文件**:
- `services/analytics/quality.py`（新增）

**改动**:
- 实现 `QualityAuditService` 类
  - `get_summary()` - 获取质检汇总
  - `get_records(page, size)` - 获取质检记录列表
  - `create_audit(session_id, score, issues)` - 创建质检记录
  - `review_audit(audit_id, reviewer_id, final_score)` - 人工复核

**验证**:
```bash
python3 -c "
from services.analytics.quality import QualityAuditService
service = QualityAuditService(pg=None)
print('QualityAuditService created successfully')
"
```

**预期结果**: 类创建成功

**状态**: ⬜ 待开发

---

### Step 8: 实现计费统计 (billing)

**目标**: 实现 Token 消耗和 ROI 计算接口

**依赖**: Step 1, 3

**涉及文件**:
- `services/analytics/billing.py`（新增）

**改动**:
- 实现 `BillingStats` 类
  - `get_usage(tenant_id)` - 获取 Token 使用量
  - `get_roi(tenant_id)` - 获取 ROI 估算
  - `get_quota(tenant_id)` - 获取套餐余量
  - `record_token_usage(session_id, tokens, model)` - 记录 Token 消耗

**验证**:
```bash
python3 -c "
from services.analytics.billing import BillingStats
billing = BillingStats(redis=None, pg=None)
print('BillingStats created successfully')
"
```

**预期结果**: 类创建成功

**状态**: ⬜ 待开发

---

### Step 9: 更新模块导出

**目标**: 创建 `__init__.py`，统一导出公开接口

**依赖**: Step 2-8

**涉及文件**:
- `services/analytics/__init__.py`（新增）

**改动**:
- 导出配置: `AnalyticsConfig`
- 导出模型: `AnalyticsEvent`, `RealtimeOverview`, `DailyStats`, 等
- 导出追踪器: `AnalyticsTracker`, `get_tracker`, `init_tracker`
- 导出统计: `RealtimeStats`, `DashboardStats`
- 导出质检: `QualityAuditService`
- 导出计费: `BillingStats`

**验证**:
```bash
python3 -c "
from services.analytics import (
    AnalyticsConfig,
    AnalyticsEvent,
    AnalyticsTracker,
    RealtimeStats,
    DashboardStats,
    QualityAuditService,
    BillingStats,
    get_tracker,
)
print('All exports working!')
"
```

**预期结果**: 所有导入成功

**状态**: ⬜ 待开发

---

### Step 10: 创建坐席工作台 API 路由

**目标**: 在坐席工作台添加 analytics API 路由

**依赖**: Step 9

**涉及文件**:
- `products/agent_workbench/handlers/analytics.py`（新增）
- `products/agent_workbench/routes.py`（修改）

**改动**:
- 创建 `analytics.py` 路由文件
  - `GET /api/analytics/realtime/overview`
  - `GET /api/analytics/realtime/channels`
  - `GET /api/analytics/realtime/agents`
  - `GET /api/analytics/stats/today`
  - `GET /api/analytics/stats/trend`
  - `GET /api/analytics/stats/satisfaction`
  - `GET /api/analytics/quality/summary`
  - `GET /api/analytics/quality/records`
  - `GET /api/analytics/billing/usage`
  - `GET /api/analytics/billing/roi`
- 在 `routes.py` 注册路由

**验证**:
```bash
curl http://localhost:8002/api/analytics/realtime/overview
curl http://localhost:8002/api/analytics/stats/today
```

**预期结果**: API 返回 JSON 数据

**状态**: ⬜ 待开发

---

### Step 11: AI 客服接入埋点

**目标**: AI 客服集成埋点 SDK

**依赖**: Step 9

**涉及文件**:
- `products/ai_chatbot/lifespan.py`（修改）
- `products/ai_chatbot/handlers/chat.py`（修改）

**改动**:
- lifespan.py 初始化埋点追踪器
- chat.py 添加埋点：
  - `session.start` - 会话开始
  - `message.user` - 用户消息
  - `message.ai` - AI 回复（含响应时间、Token）
  - `session.end` - 会话结束
  - `order.query` - 订单查询
  - `tracking.query` - 物流查询

**验证**:
```bash
# 发送测试消息
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"hello","session_id":"test-123"}'

# 检查 Redis 计数
redis-cli HGETALL analytics:daily:$(date +%Y-%m-%d)
```

**预期结果**: Redis 中有埋点计数

**状态**: ⬜ 待开发

---

### Step 12: 坐席工作台接入埋点

**目标**: 坐席工作台集成埋点 SDK

**依赖**: Step 9

**涉及文件**:
- `products/agent_workbench/lifespan.py`（修改）
- `products/agent_workbench/handlers/auth.py`（修改）
- `products/agent_workbench/handlers/session.py`（修改）

**改动**:
- lifespan.py 初始化埋点追踪器
- 添加埋点：
  - `agent.login` - 坐席登录
  - `agent.logout` - 坐席登出
  - `agent.status_change` - 状态切换
  - `session.transfer` - 会话转接
  - `message.agent` - 坐席回复

**验证**:
```bash
# 登录测试
curl -X POST http://localhost:8002/api/agent/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"test"}'

# 检查 Redis
redis-cli HGETALL analytics:realtime:overview
```

**预期结果**: Redis 中有坐席相关数据

**状态**: ⬜ 待开发

---

## 四、Phase 2 - P1 扩展功能 (Step 13-20)

### Step 13: 实现定时聚合任务

**目标**: 添加定时任务，定期聚合数据

**依赖**: Step 4

**涉及文件**:
- `infrastructure/scheduler/tasks/analytics_tasks.py`（新增）

**改动**:
- 实现 `aggregate_daily_stats` 任务（每日凌晨执行）
- 实现 `sync_realtime_stats` 任务（每 5 分钟执行）
- 实现 `cleanup_old_events` 任务（每周执行）
- 注册到调度器

**验证**:
```bash
python3 -c "
from infrastructure.scheduler.tasks.analytics_tasks import aggregate_daily_stats
print('Task function loaded successfully')
"
```

**预期结果**: 任务函数加载成功

**状态**: ⬜ 待开发

---

### Step 14: 前端 Monitoring 页面对接

**目标**: 实时大屏页面调用真实 API

**依赖**: Step 10

**涉及文件**:
- `products/agent_workbench/frontend/components/Monitoring.tsx`（修改）
- `products/agent_workbench/frontend/src/api.ts`（修改）

**改动**:
- 添加 analyticsApi 方法
- Monitoring.tsx 替换硬编码数据为 API 调用
- 添加自动刷新（每 30 秒）

**验证**:
- 打开 /monitoring 页面
- 检查数据是否来自 API
- 确认自动刷新正常

**预期结果**: 页面显示真实数据

**状态**: ⬜ 待开发

---

### Step 15: 前端 Dashboard 页面对接

**目标**: 效能报表页面调用真实 API

**依赖**: Step 10

**涉及文件**:
- `products/agent_workbench/frontend/components/Dashboard.tsx`（修改）

**改动**:
- 替换 mockTrendData 为 API 调用
- 替换 mockSatisfactionData 为 API 调用
- 保留自动刷新逻辑

**验证**:
- 打开 /dashboard 页面
- 检查趋势图和满意度图数据
- 确认同比变化计算正确

**预期结果**: 页面显示真实数据

**状态**: ⬜ 待开发

---

### Step 16: 前端 QualityAudit 页面对接

**目标**: 智能质检页面调用真实 API

**依赖**: Step 10

**涉及文件**:
- `products/agent_workbench/frontend/components/QualityAudit.tsx`（修改）

**改动**:
- 替换 auditRecords 为 API 调用
- 添加分页加载
- 添加搜索过滤

**验证**:
- 打开 /audit 页面
- 检查质检汇总和记录列表
- 测试分页和搜索

**预期结果**: 页面显示真实数据

**状态**: ⬜ 待开发

---

### Step 17: 前端 BillingPortal 页面对接

**目标**: 计费管理页面调用真实 API

**依赖**: Step 10

**涉及文件**:
- `products/agent_workbench/frontend/components/BillingPortal.tsx`（修改）

**改动**:
- 算力余量调用 API
- ROI 面板调用 API
- 保留套餐选择 UI（Mock 数据）

**验证**:
- 打开 /billing 页面
- 检查算力余量和 ROI 数据

**预期结果**: 关键指标显示真实数据

**状态**: ⬜ 待开发

---

### Step 18: Coze Token 回调集成

**目标**: 集成 Coze Token 使用量回调

**依赖**: Step 8

**涉及文件**:
- `services/coze/client.py`（修改）
- `products/ai_chatbot/handlers/chat.py`（修改）

**改动**:
- Coze 调用后记录 Token 消耗
- 调用 `BillingStats.record_token_usage()`

**验证**:
```bash
# 发送消息后检查 Token 记录
curl -X POST http://localhost:8000/api/chat/stream ...
redis-cli HGETALL analytics:billing:$(date +%Y-%m-%d)
```

**预期结果**: Token 使用量被记录

**状态**: ⬜ 待开发

---

### Step 19: 创建 README 文档

**目标**: 编写模块使用说明

**依赖**: Step 9

**涉及文件**:
- `services/analytics/README.md`（新增）

**改动**:
- 模块职责说明
- 快速开始示例
- API 接口文档
- 埋点事件规范
- 配置说明

**验证**:
- 文档格式正确
- 示例代码可运行

**状态**: ⬜ 待开发

---

### Step 20: 数据验证与上线

**目标**: 全面测试并部署上线

**依赖**: Step 1-19

**涉及文件**:
- 无新增文件

**改动**:
- 验证所有 API 响应正确
- 验证前端所有页面显示正常
- 验证埋点数据完整性
- 部署到生产环境

**验证**:
```bash
# 部署到服务器
rsync -avz services/analytics/ root@8.211.27.199:/opt/fiido-ai-service/services/analytics/
ssh root@8.211.27.199 "systemctl restart fiido-ai-chatbot fiido-agent-workbench"

# 验证生产环境
curl https://ai.fiido.com/workbench-api/analytics/realtime/overview
```

**预期结果**: 生产环境正常运行

**状态**: ⬜ 待开发

---

## 五、开发检查清单

每个 Step 完成后：

- [ ] 代码无语法错误
- [ ] 按验证方法测试通过
- [ ] 不破坏现有功能
- [ ] 更新 `progress.md` 状态
- [ ] Git 提交（message 包含 Step 编号）

---

## 六、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0 | 2025-12-25 | 基于 UI 组件分析，扩展为 20 步；新增 quality/billing 子模块；新增前端对接步骤 |
| v1.0 | 2025-12-25 | 初始版本，12 个步骤 |
