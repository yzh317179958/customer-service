# 数据埋点服务 - PRD

> **版本**: v4.0
> **创建日期**: 2025-12-25
> **更新日期**: 2025-12-25
> **模块位置**: `services/analytics/`
> **模块类型**: 独立服务模块（被 AI 客服 + 坐席工作台调用）

---

## 1. 产品概述

### 产品名称

数据埋点服务 (Analytics Tracking Service)

### 目标用户

| 用户类型 | 使用场景 |
|----------|----------|
| 产品运营 | 分析 AI 客服使用情况，制作商业案例 |
| 销售团队 | 展示 AI 客服价值，说服潜在客户 |
| 技术团队 | 监控系统健康度，优化性能 |

### 核心价值

1. **数据驱动商业案例**：收集真实数据证明 AI 客服 + 人工协作的价值
2. **量化 AI 效能**：统计 AI 处理了多少会话、解决了多少问题
3. **量化人工效能**：统计坐席响应速度、工单处理效率
4. **成本节省证明**：计算 AI 替代人工节省的成本
5. **服务质量追踪**：监控人工接管后的处理质量
6. **持续优化依据**：发现瓶颈，指导产品改进

### 业务背景

**现状**：
- AI 客服已上线运行，但缺少数据采集
- 坐席工作台已上线，人工服务数据未统计
- 无法证明 AI 客服 + 人工协作的实际价值
- 销售缺少商业案例数据支撑

**目标**：
- 为 AI 客服和坐席工作台添加数据埋点
- 收集完整的客服服务链路数据
- 输出可用于商业案例的业务指标

---

## 2. 埋点范围（基于现有功能）

### 2.1 AI 客服功能清单

| 功能模块 | 文件位置 | 核心功能 |
|----------|----------|----------|
| 聊天接口 | `products/ai_chatbot/handlers/chat.py` | 同步聊天、流式聊天、会话隔离 |
| 物流查询 | `products/ai_chatbot/handlers/tracking.py` | 17track 物流轨迹查询 |
| 订单查询 | `services/shopify/` | Shopify 多站点订单查询 |
| 会话管理 | `services/session/` | 会话状态、人工接管 |
| 监管触发 | `services/session/regulator.py` | 敏感词检测、情绪识别 |

### 2.2 坐席工作台功能清单

| 功能模块 | 文件位置 | 核心功能 |
|----------|----------|----------|
| 坐席认证 | `products/agent_workbench/handlers/auth.py` | 登录、登出、状态切换、心跳 |
| 会话服务 | `products/agent_workbench/handlers/sessions.py` | 接管、释放、转接、发消息、添加备注 |
| 工单系统 | `products/agent_workbench/handlers/tickets.py` | 创建、分配、更新、关闭、SLA 追踪 |

### 2.3 埋点目标

| 目标 | 说明 | 商业价值 |
|------|------|----------|
| 会话量统计 | 每日/每周/每月会话数 | 展示使用规模 |
| AI 解决率 | AI 独立解决 vs 转人工 | 证明 AI 能力 |
| AI 响应时长 | AI 回复速度 | 证明效率优势 |
| 坐席响应时长 | 人工接管后首次响应时间 | 服务质量指标 |
| 坐席处理效率 | 平均会话处理时长 | 人效评估 |
| 工单处理效率 | 工单平均解决时长 | 服务能力证明 |
| 查询成功率 | 订单/物流查询成功率 | 证明功能可靠性 |
| 成本节省 | AI 替代人工节省成本 | ROI 证明 |

---

## 3. 功能列表

### Phase 1: AI 客服埋点 (P0)

| 功能 | 说明 | 埋点位置 |
|------|------|----------|
| 会话生命周期 | 会话开始、结束、时长 | chat.py |
| 消息统计 | 用户消息数、AI 回复数 | chat.py |
| AI 响应时间 | Coze API 调用耗时 | chat.py |
| 转人工事件 | 触发原因、等待时长 | chat.py + regulator |
| 订单查询 | 查询次数、成功/失败 | shopify 服务 |
| 物流查询 | 查询次数、运营商分布 | tracking.py |

### Phase 2: 坐席工作台埋点 (P0)

| 功能 | 说明 | 埋点位置 |
|------|------|----------|
| 坐席登录/登出 | 工作时长、在线状态 | auth.py |
| 会话接管 | 接管时间、等待时长 | sessions.py |
| 会话处理 | 消息数、处理时长 | sessions.py |
| 会话转接/释放 | 转接原因、目标坐席 | sessions.py |
| 工单创建 | 来源、类型、优先级 | tickets.py |
| 工单处理 | 状态变更、处理时长 | tickets.py |
| 工单 SLA | 响应时效、解决时效 | tickets.py |

### Phase 3: 扩展埋点 (P1)

| 功能 | 说明 | 依赖条件 |
|------|------|----------|
| Token 消耗 | Coze API Token 用量 | Coze 回调接口 |
| 意图分布 | 用户问题意图分类 | Intent 识别数据 |
| 满意度评分 | 用户评价数据 | 前端评价功能 |

---

## 4. 埋点事件设计

### 4.1 AI 客服会话事件

| 事件名 | 触发时机 | 携带数据 |
|--------|----------|----------|
| `session.start` | 用户首次发消息 | session_id, channel, user_agent, timestamp |
| `session.message` | 每轮对话 | session_id, role(user/ai), message_length, response_time_ms |
| `session.escalate` | 转人工触发 | session_id, reason, severity, trigger_keyword |
| `session.end` | 会话结束 | session_id, duration_seconds, message_count, resolved_by(ai/human) |

### 4.2 业务查询事件

| 事件名 | 触发时机 | 携带数据 |
|--------|----------|----------|
| `query.order` | 订单查询 | session_id, order_number, site, success, response_time_ms |
| `query.tracking` | 物流查询 | session_id, tracking_number, carrier, success, status |

### 4.3 坐席工作事件

| 事件名 | 触发时机 | 携带数据 |
|--------|----------|----------|
| `agent.login` | 坐席登录 | agent_id, agent_name, timestamp |
| `agent.logout` | 坐席登出 | agent_id, work_duration_minutes, sessions_handled |
| `agent.status_change` | 状态切换 | agent_id, from_status, to_status |

### 4.4 坐席会话事件

| 事件名 | 触发时机 | 携带数据 |
|--------|----------|----------|
| `agent.session_takeover` | 接管会话 | agent_id, session_id, wait_duration_seconds |
| `agent.session_message` | 发送消息 | agent_id, session_id, message_length |
| `agent.session_release` | 释放会话 | agent_id, session_id, handle_duration_seconds, message_count |
| `agent.session_transfer` | 转接会话 | agent_id, session_id, target_agent_id, reason |

### 4.5 工单事件

| 事件名 | 触发时机 | 携带数据 |
|--------|----------|----------|
| `ticket.created` | 创建工单 | ticket_id, source, type, priority, agent_id |
| `ticket.assigned` | 分配工单 | ticket_id, from_agent_id, to_agent_id |
| `ticket.status_changed` | 状态变更 | ticket_id, from_status, to_status, agent_id |
| `ticket.closed` | 关闭工单 | ticket_id, resolution_duration_hours, sla_met |

### 4.6 系统事件

| 事件名 | 触发时机 | 携带数据 |
|--------|----------|----------|
| `api.coze_call` | Coze API 调用 | session_id, workflow_id, response_time_ms, success |
| `api.error` | 任何 API 错误 | session_id, endpoint, error_type, error_message |

---

## 5. 用户故事

### 5.1 销售展示场景

```
作为销售人员，
我希望能够展示"上月 AI 客服共处理 5000 个会话，其中 85% 由 AI 独立解决"，
以便向潜在客户证明 AI 客服的价值。
```

### 5.2 成本核算场景

```
作为运营负责人，
我希望能够计算"本月 AI 客服节省了约 ¥50,000 人工成本"，
以便评估投资回报率并决定是否续费。
```

### 5.3 性能优化场景

```
作为技术负责人，
我希望能够查看"平均 AI 响应时间为 1.5 秒，物流查询成功率为 98%"，
以便发现性能瓶颈并针对性优化。
```

### 5.4 坐席效能场景

```
作为客服主管，
我希望能够查看"本月坐席平均响应时间 30 秒，会话处理时长 8 分钟"，
以便评估团队服务质量并指导培训。
```

### 5.5 工单效率场景

```
作为运营负责人，
我希望能够查看"工单平均解决时长 4 小时，SLA 达标率 95%"，
以便向客户展示售后服务能力。
```

---

## 6. 成功标准

### 6.1 AI 客服功能验收

- [ ] 会话开始/结束事件正确记录
- [ ] 每轮消息的响应时间被记录
- [ ] 转人工事件包含完整原因
- [ ] 订单/物流查询成功率可统计

### 6.2 坐席工作台功能验收

- [ ] 坐席登录/登出事件正确记录
- [ ] 会话接管/释放/转接事件完整
- [ ] 工单生命周期事件可追溯
- [ ] SLA 达标率可统计

### 6.3 数据质量

- [ ] 事件丢失率 < 0.1%
- [ ] 埋点不影响业务响应时间（异步处理）
- [ ] 数据可追溯到具体会话

### 6.4 商业案例数据

- [ ] 可生成"月度会话量报告"
- [ ] 可计算"AI 解决率"
- [ ] 可估算"人工成本节省"
- [ ] 可展示"坐席响应效率"
- [ ] 可统计"工单 SLA 达标率"

---

## 7. 约束与假设

### 约束

1. 必须遵循三层架构，放在 `services/analytics/`
2. 使用现有的 Redis 和 PostgreSQL
3. 埋点必须异步，不能阻塞业务流程
4. 只针对现有功能埋点，不涉及新功能开发

### 假设

1. Coze Token 消耗数据暂时不可获取，先预留接口
2. 用户满意度评分暂时无数据源，先预留接口
3. 当前数据量不大（日均 < 1 万事件），PostgreSQL 足够
4. 单次人工成本假设为 ¥10/次（可配置）

---

## 8. 文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v4.0 | 2025-12-25 | 扩展坐席工作台埋点：坐席认证、会话服务、工单系统 |
| v3.0 | 2025-12-25 | 完全重写：删除坐席工作台 UI 功能，聚焦现有 AI 客服功能埋点 |
| v2.0 | 2025-12-25 | 扩展为 4 个子模块（已废弃）|
| v1.0 | 2025-12-25 | 初始版本 |
