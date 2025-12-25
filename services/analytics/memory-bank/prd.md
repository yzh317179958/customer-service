# 数据分析服务 - PRD

> **版本**: v2.0
> **创建日期**: 2025-12-25
> **更新日期**: 2025-12-25
> **模块位置**: `services/analytics/`
> **模块类型**: 独立服务模块（被多产品复用）

---

## 1. 产品概述

### 产品名称

数据分析服务 (Analytics Service)

### 目标用户

| 用户类型 | 使用场景 | 对应 UI 页面 |
|----------|----------|--------------|
| 平台运营 | 实时监控系统状态、流量分布 | 实时大屏 (Monitoring) |
| 产品经理 | 分析效能指标、评估优化效果 | 效能报表 (Dashboard) |
| 质检主管 | 审核服务质量、识别违规行为 | 智能质检 (QualityAudit) |
| 财务/管理 | 监控 AI 消耗、成本核算 | 计费管理 (BillingPortal) |
| 客户 | 查看自己店铺的服务数据 | 客户门户 (规划中) |

### 核心价值

1. **数据驱动决策**：用真实数据证明产品价值，替代 Mock 数据
2. **商业闭环支撑**：为获客→转化→交付→续费提供数据依据
3. **产品优化指导**：发现瓶颈、验证假设、持续改进
4. **客户价值展示**：向客户证明 AI 客服的 ROI

### 业务背景

**现状分析**（基于前端代码审查）：
- `Dashboard.tsx` 使用 `mockTrendData`、`mockSatisfactionData` 假数据
- `Monitoring.tsx` 全部硬编码展示数据
- `QualityAudit.tsx` 使用 `auditRecords` Mock 数组
- 后端缺少统计 API，前端 UI 已就绪但无真实数据

**目标**：
- 为坐席工作台 4 个数据页面提供真实数据 API
- 为 AI 客服提供运营指标采集

---

## 2. 功能模块

### 2.1 模块划分

| 子模块 | 职责 | 对应 UI | 优先级 |
|--------|------|---------|--------|
| **tracker** | 事件埋点采集 | (后端基础) | P0 |
| **stats** | 会话/效能统计 | Monitoring + Dashboard | P0 |
| **quality** | 质检评分分析 | QualityAudit | P1 |
| **billing** | Token 消耗统计 | BillingPortal | P1 |

### 2.2 功能列表

#### Phase 1: 核心统计 (P0)

| 功能 | 说明 | 对应 UI 组件 |
|------|------|--------------|
| 事件埋点 SDK | 统一埋点接口，异步非阻塞 | - |
| 实时会话统计 | 活跃会话、排队人数、坐席状态 | Monitoring.tsx 核心指标 |
| 渠道流量分布 | App/Web/微信/电话各渠道流量 | Monitoring.tsx 流量矩阵 |
| 坐席健康度 | 坐席在线状态、服务时长、负载 | Monitoring.tsx 坐席看板 |
| 今日会话统计 | 总数、响应时长、满意度 | Dashboard.tsx 核心卡片 |
| 会话趋势图 | 近 7 日会话量趋势 | Dashboard.tsx 趋势图 |
| 满意度分析 | 评分分布、合格率 | Dashboard.tsx 满意度图 |

#### Phase 2: 质检与计费 (P1)

| 功能 | 说明 | 对应 UI 组件 |
|------|------|--------------|
| 质检评分记录 | 会话质检分数、合格/不合格 | QualityAudit.tsx 质检流水 |
| 质检汇总统计 | 本月合格率、已质检数、待复核数 | QualityAudit.tsx 概览卡片 |
| Token 消耗统计 | Coze 平台 Token 使用量 | BillingPortal.tsx 算力余量 |
| ROI 估算 | AI 节省的人工成本 | BillingPortal.tsx ROI 面板 |
| 套餐用量跟踪 | 坐席数、功能使用情况 | BillingPortal.tsx 订阅状态 |

#### Phase 3: 高级分析 (P2)

| 功能 | 说明 | 优先级 |
|------|------|--------|
| 多租户数据隔离 | 按 tenant_id 隔离统计 | P2 |
| 数据导出 | CSV/Excel 报表导出 | P2 |
| 智能告警 | 异常指标自动告警 | P2 |
| 预测分析 | 基于历史数据预测趋势 | P2 |

---

## 3. 核心指标定义

### 3.1 实时大屏指标 (Monitoring)

| 指标 | 定义 | 对应 UI 位置 |
|------|------|--------------|
| 系统并发负载 | 当前处理中请求 / 最大并发 | 核心集群指标卡片 |
| 全球实时排队 | 等待人工的会话数 | 核心集群指标卡片 |
| 坐席活跃率 | 在线坐席数 / 总坐席数 | 核心集群指标卡片 |
| SLA 告警事件 | 超时/异常事件数 | 核心集群指标卡片 |
| 渠道在线人数 | 各渠道当前在线用户 | 流量分布图 |
| 渠道负载率 | 各渠道流量占比 | 流量分布图 |
| 坐席服务状态 | 在线/服务中/小休 | 坐席健康度看板 |
| 坐席服务时长 | 当前会话持续时间 | 坐席健康度看板 |

### 3.2 效能报表指标 (Dashboard)

| 指标 | 定义 | 计算方式 |
|------|------|----------|
| 今日会话总数 | 当日会话数量 | COUNT(session_id) WHERE date=today |
| 平均响应时长 | AI/坐席平均响应时间 | AVG(response_time) |
| 全渠道满意度 | 用户评分平均值 | AVG(rating) |
| 服务质检评级 | 综合质检等级 | 根据合格率映射 |
| 近 7 日趋势 | 每日会话量变化 | GROUP BY date |
| 满意度分布 | 各评分段占比 | GROUP BY rating_level |

### 3.3 智能质检指标 (QualityAudit)

| 指标 | 定义 | 计算方式 |
|------|------|----------|
| 本月合格率 | 合格会话 / 已质检会话 | passed / total * 100 |
| 已质检会话数 | 本月完成质检的会话 | COUNT(audited=true) |
| 待人工复核 | 不合格需复核的数量 | COUNT(status='pending_review') |
| 质检评分 | 单次会话质检分数 | 0-100 分 |

### 3.4 计费管理指标 (BillingPortal)

| 指标 | 定义 | 数据来源 |
|------|------|----------|
| AI 节省成本 | AI 处理会话 × 单次人工成本 | 计算公式 |
| 算力余量 | 已用 Token / 套餐 Token | Coze API 回调 |
| 自动完成率 | AI 独立解决的会话比例 | stats 模块 |
| 当前订阅 | 套餐类型、到期时间 | 订阅表 |

---

## 4. 用户故事

### 4.1 实时大屏场景

```
作为值班主管，
我希望在实时大屏上看到当前系统负载和排队人数，
以便及时调配坐席资源应对高峰。
```

### 4.2 效能报表场景

```
作为产品经理，
我希望查看近 7 日会话趋势和响应时长变化，
以便评估最近一次提示词优化的效果。
```

### 4.3 智能质检场景

```
作为质检主管，
我希望查看本月质检合格率和待复核列表，
以便安排人工复核并发现服务问题。
```

### 4.4 计费管理场景

```
作为运营负责人，
我希望看到 AI 本月节省的人工成本和 Token 消耗，
以便评估投资回报率并决定是否续费。
```

---

## 5. 埋点事件设计

### 5.1 会话生命周期事件

| 事件名 | 触发时机 | 携带数据 |
|--------|----------|----------|
| `session.start` | 用户开始对话 | session_id, product, channel, tenant_id, user_agent |
| `session.end` | 会话结束 | session_id, duration, message_count, resolved, rating |
| `session.transfer` | 转接人工 | session_id, reason, wait_time, from_ai |
| `session.queue` | 进入排队 | session_id, queue_position |

### 5.2 消息事件

| 事件名 | 触发时机 | 携带数据 |
|--------|----------|----------|
| `message.user` | 用户发送消息 | session_id, length, intent |
| `message.ai` | AI 回复消息 | session_id, response_time, tokens, model |
| `message.agent` | 坐席回复消息 | session_id, agent_id, response_time |

### 5.3 坐席状态事件

| 事件名 | 触发时机 | 携带数据 |
|--------|----------|----------|
| `agent.login` | 坐席登录 | agent_id, timestamp |
| `agent.logout` | 坐席登出 | agent_id, duration, sessions_handled |
| `agent.status_change` | 状态切换 | agent_id, from_status, to_status |
| `agent.session_accept` | 接待会话 | agent_id, session_id |

### 5.4 质检事件

| 事件名 | 触发时机 | 携带数据 |
|--------|----------|----------|
| `audit.auto` | AI 自动质检完成 | session_id, score, issues[] |
| `audit.manual` | 人工复核完成 | session_id, agent_id, final_score |

### 5.5 业务事件（用于商业案例数据收集）

| 事件名 | 触发时机 | 携带数据 | 商业价值 |
|--------|----------|----------|----------|
| `order.query` | 查询订单 | session_id, order_id, success | 统计订单查询频次 |
| `tracking.query` | 查询物流 | session_id, tracking_number, carrier | 统计物流查询频次 |
| `feedback.submit` | 用户评价 | session_id, rating, comment | 客户满意度分析 |
| `issue.resolved` | 问题解决 | session_id, issue_type, resolution_time | AI 解决能力证明 |
| `cost.saved` | 成本节省 | session_id, saved_amount, method | ROI 计算依据 |

### 5.6 计费事件

| 事件名 | 触发时机 | 携带数据 |
|--------|----------|----------|
| `billing.token_usage` | Coze 调用完成 | session_id, tokens_used, model |
| `billing.quota_alert` | 额度预警 | tenant_id, usage_percent |

---

## 6. API 设计

### 6.1 实时大屏 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/analytics/realtime/overview | 核心指标概览 |
| GET | /api/analytics/realtime/channels | 渠道流量分布 |
| GET | /api/analytics/realtime/agents | 坐席状态列表 |

### 6.2 效能报表 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/analytics/stats/today | 今日统计 |
| GET | /api/analytics/stats/trend?days=7 | 趋势数据 |
| GET | /api/analytics/stats/satisfaction | 满意度分布 |

### 6.3 智能质检 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/analytics/quality/summary | 质检汇总 |
| GET | /api/analytics/quality/records | 质检记录列表 |
| POST | /api/analytics/quality/audit | 执行质检 |

### 6.4 计费统计 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/analytics/billing/usage | Token 使用量 |
| GET | /api/analytics/billing/roi | ROI 估算 |
| GET | /api/analytics/billing/quota | 套餐余量 |

---

## 7. 成功标准

### 7.1 功能验收标准

- [ ] 实时大屏 4 个核心指标卡片显示真实数据
- [ ] 效能报表近 7 日趋势图显示真实数据
- [ ] 智能质检合格率和质检记录显示真实数据
- [ ] 计费管理 Token 余量和 ROI 显示真实数据
- [ ] 所有 API 响应时间 < 200ms

### 7.2 业务验收标准

- [ ] 能够替换前端所有 Mock 数据
- [ ] 数据准确率 > 99%（与实际日志对比）
- [ ] 支持按天/周/月聚合查询

### 7.3 技术验收标准

- [ ] 埋点不影响主流程性能（异步处理）
- [ ] 数据丢失率 < 0.1%
- [ ] 支持高并发埋点（1000 QPS）

---

## 8. 约束与假设

### 约束

1. 必须遵循三层架构，放在 `services/analytics/`
2. 使用现有的 Redis 和 PostgreSQL
3. 不引入额外的数据分析引擎
4. 埋点必须异步，不能阻塞业务流程
5. Token 消耗数据需从 Coze 回调获取

### 假设

1. 当前数据量不大（日均 < 10 万事件），PostgreSQL 足够
2. 无需实时流处理，秒级/分钟级延迟可接受
3. Coze 平台提供 Token 使用量回调
4. 多租户场景在 Phase 3 实现

---

## 9. 文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0 | 2025-12-25 | 基于前端 UI 组件分析，扩展为 4 个子模块（stats/quality/billing）；新增完整 API 设计和指标定义 |
| v1.0 | 2025-12-25 | 初始版本 |
