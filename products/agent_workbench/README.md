# 坐席工作台（Agent Workbench）模块规范

> **模块定位**：人工客服后台（会话接管、工单、协作、订单查询、监控）
> **模块状态**：后端已实现；前端待落地（复用 `fronted_origin` 原型）
> **最后更新**：2025-12-19

---

## 一、模块职责

- 坐席认证与在线状态管理
- 会话队列、会话详情、接管/释放/转接
- 工单中心：创建、分配、评论、附件、审计日志、SLA 与告警
- 快捷回复与模板管理（提升效率与标准化）
- 多坐席协作：协助请求、内部备注（含 @提醒）、转接请求处理
- Shopify 订单与物流查询（多站点）
- 运维能力：缓存预热、CDN 健康检查

---

## 二、运行方式

### 2.1 独立模式（推荐开发/联调）

```bash
uvicorn products.agent_workbench.main:app --host 0.0.0.0 --port 8002
```

文档地址：`http://localhost:8002/docs`

### 2.2 全家桶模式（统一入口）

```bash
uvicorn backend:app --host 0.0.0.0 --port 8000
```

说明：全家桶模式下坐席工作台 API 仍位于 `http://localhost:8000/api/*`。

---

## 三、API 端点概览（prefix=`/api`）

| 路径前缀 | 说明 |
|---|---|
| `/agent/*` | 坐席登录/登出、刷新 token、个人信息、状态、心跳、当日统计 |
| `/sessions/*` | 会话队列、详情、接管/释放/转接、从会话创建工单 |
| `/tickets/*` | 工单 CRUD、搜索/筛选、指派、批量操作、评论、附件、审计、SLA |
| `/quick-replies/*` | 快捷回复管理与统计 |
| `/templates/*` | 工单模板管理与渲染 |
| `/agents/*` | 坐席管理（Admin） |
| `/assist-requests/*` | 协助请求创建/处理 |
| `/shopify/*` | 订单查询/物流追踪/健康检查 |
| `/warmup/*` | Shopify 缓存预热 |
| `/cdn/*` | CDN 健康检查 |
| `/customers/*` | 客户档案（当前基于 session_id） |
| `/agent/events` | 坐席事件 SSE（@提醒/协助等） |
| `/admin/sessions/clear` | 清除会话数据（Admin） |

鉴权：除少量健康检查类接口外，坐席侧接口默认需 `Authorization: Bearer <token>`。

---

## 四、前端说明

- **前端原型**：`products/agent_workbench/fronted_origin`（React/Vite，静态数据，需工程化改造）
- **生产前端建议目录**：`products/agent_workbench/frontend`（待创建，详见 `products/agent_workbench/memory-bank/implementation-plan.md`）
- **计费模块**：按原型 `BillingView` 设计，建议 iframe 嵌入 `products/customer_portal`

---

## 五、三层架构与依赖约束（必须遵守）

```python
# ✅ 允许依赖 services
from services.session.state import SessionStateStore
from services.ticket.store import TicketStore

# ✅ 允许依赖 infrastructure
from infrastructure.security.agent_auth import AgentManager

# ❌ 禁止依赖其他 products（后端代码层面）
from products.ai_chatbot import xxx  # 禁止！
```

---

## 六、配置项（环境变量）

| 环境变量 | 默认值 | 说明 |
|---|---:|---|
| `AGENT_WORKBENCH_HOST` | `0.0.0.0` | 独立模式监听地址 |
| `AGENT_WORKBENCH_PORT` | `8002` | 独立模式端口 |
| `DEBUG` | `false` | 调试模式 |
| `ENABLE_SLA_ALERTS` | `true` | SLA 预警后台任务开关 |
| `ENABLE_HEARTBEAT_MONITOR` | `true` | 坐席心跳监控任务开关 |
| `CORS_ORIGINS` | 空 | 追加 CORS origins（逗号分隔） |
| `AGENT_AUTO_BUSY_SECONDS` | `300` | 无活动自动 busy 的阈值 |
| `ATTACHMENTS_DIR` | `attachments` | 工单附件存储目录 |

---

## 七、Vibe Coding 文档（开发必读）

位于 `products/agent_workbench/memory-bank/`：
- `prd.md`
- `tech-stack.md`
- `implementation-plan.md`
- `progress.md`
- `architecture.md`
