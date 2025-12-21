# 坐席工作台（Agent Workbench）- 架构说明

> **创建日期**：2025-12-19
> **最后更新**：2025-12-19
> **遵循规范**：`CLAUDE.md` 三层架构与单向依赖；`products` 之间禁止互相 import。

---

## 1. 整体架构（系统视角）

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Agent Workbench Frontend                      │
│   （待落地：基于 products/agent_workbench/fronted_origin 工程化）       │
└───────────────┬───────────────────────────────┬──────────────────────┘
                │                               │
                │ HTTP(S)                       │ HTTP(S)
                ▼                               ▼
┌──────────────────────────────┐    ┌───────────────────────────────────┐
│ products/agent_workbench      │    │ products/ai_chatbot               │
│ 坐席侧 API（/api/*）           │    │ 用户端对话/人工消息写入（/api/*） │
│ - auth/sessions/tickets/...   │    │ - /api/manual/messages            │
│ - agent events SSE            │    │ - /api/chat, /api/chat/stream     │
└───────────────┬──────────────┘    └───────────────────┬──────────────┘
                │                                       │
                ▼                                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│                           services/ 服务层                             │
│  session / ticket / shopify / email / ...（可复用业务能力）             │
└──────────────────────────────┬───────────────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     infrastructure/ 基础设施层                          │
│  bootstrap / security / database / scheduler / monitoring / ...         │
└──────────────────────────────────────────────────────────────────────┘
```

说明：
- 坐席工作台前端允许调用多个后端产品 API（属于“客户端集成”），但后端代码层面保持产品隔离（通过 services 或 HTTP API 协作）。
- Billing 模块建议以 iframe 嵌入 `products/customer_portal`（见原型 `BillingView` 注释与 `products/customer_portal/memory-bank/*`）。

---

## 2. 目录结构

> **决策**：直接改造 `fronted_origin/` 目录，不新建 `frontend/`

```
products/agent_workbench/
├── main.py                 # 独立启动入口（端口默认 8002）
├── config.py               # 配置（CORS、开关等）
├── lifespan.py             # 使用 infrastructure/bootstrap 初始化组件
├── dependencies.py         # 依赖注入（AgentManager/SessionStore/TicketStore/...）
├── routes.py               # 汇总各 handler 路由（prefix=/api）
├── handlers/               # auth/sessions/tickets/...（后端 API）
├── fronted_origin/         # 前端（改造后的生产工程）
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js  # 新增：Tailwind 本地配置
│   ├── postcss.config.js   # 新增：PostCSS 配置
│   ├── .env.development    # 新增：开发环境变量
│   ├── .env.production     # 新增：生产环境变量
│   └── src/
│       ├── api/            # 新增：API Client
│       ├── stores/         # 新增：全局状态（zustand）
│       ├── pages/          # 新增：登录页等
│       └── components/     # 现有组件（改造）
└── memory-bank/            # 文档驱动（本文件夹）
```

---

## 3. 关键后端模块（已存在）

### 3.1 API 路由聚合
- `products/agent_workbench/routes.py`：注册 auth/sessions/tickets/quick_replies/templates/agents/assist_requests/shopify/warmup/cdn/misc

### 3.2 认证与权限
- `products/agent_workbench/handlers/auth.py`：`/api/agent/*`（登录、刷新、状态、心跳、当日统计）
- `products/agent_workbench/dependencies.py`：`require_agent()`、`require_admin()` 统一保护

### 3.3 会话与协作
- `products/agent_workbench/handlers/sessions.py`：队列、接管/释放/转接、详情、从会话创建工单
- `products/agent_workbench/handlers/misc.py`：内部备注 CRUD、转接请求处理、坐席事件 SSE（`/api/agent/events`）

### 3.4 工单系统
- `products/agent_workbench/handlers/tickets.py`：工单全链路 + SLA + 附件 + 审计日志
- 依赖 `services/ticket/*`

---

## 4. 为“完整前端接入”建议新增的后端能力（P0）

> 目的：让前端能在不轮询过重的情况下实现实时会话体验，并保证坐席消息写入的安全性。

### 4.1 会话事件 SSE（建议新增）
- `GET /api/sessions/{session_name}/events`
- 推送事件类型对齐现有约定：`manual_message`、`status_change`、`error`
- 数据源：复用 `infrastructure/bootstrap.get_sse_queues()` 中以 `session_name` 为 key 的队列

### 4.2 坐席发送消息（建议新增）
- `POST /api/sessions/{session_name}/messages`
- 保护：`require_agent()`
- 行为：
  - 写入 `services/session` 的 `SessionState.history`
  - 通过 SSE 队列向 session 推送 `manual_message`（role=agent，包含 agent_id/agent_name）

> 备注：当前 `/api/manual/messages` 位于 `ai_chatbot`，建议坐席侧不直接依赖该“未绑定坐席 JWT”的入口。

---

## 5. 核心数据流（示例）

### 5.1 坐席接管会话
```
前端选择 pending_manual 会话
  → POST /api/sessions/{session}/takeover
  → 后端更新 SessionState.status=manual_live、assigned_agent、history(system msg)
  → 推送 status_change / manual_message（system）到 session SSE
  → 前端刷新会话详情
```

### 5.2 坐席发送消息
```
前端输入并发送
  → POST /api/sessions/{session}/messages (建议新增)
  → 写入 SessionState.history(role=agent)
  → 推送 manual_message(role=agent) 到 session SSE
  → 用户端/坐席端实时展示
```

### 5.3 从会话创建工单
```
前端点击"创建工单"
  → POST /api/sessions/{session}/ticket
  → services/ticket.store 保存 Ticket，并回写 session.tickets
  → 前端跳转工单详情
```

---

## 6. 前端架构说明

### 6.1 技术栈

| 模块 | 技术 | 版本 |
|------|------|------|
| 构建工具 | Vite | ^6.2.0 |
| 框架 | React + TypeScript | ^19.2.3 / ~5.8.2 |
| UI 样式 | Tailwind CSS (本地) | ^3.4.0 |
| 状态管理 | zustand | ^4.5.0 |
| 图标 | lucide-react | ^0.561.0 |
| 图表 | recharts | ^3.6.0 |

### 6.2 目录结构规范

```
fronted_origin/src/
├── api/                    # API 请求封装
│   ├── client.ts           # 基础请求（拦截器、token 注入）
│   ├── agent.ts            # 坐席认证 API
│   ├── sessions.ts         # 会话管理 API
│   ├── tickets.ts          # 工单 API
│   ├── quick-replies.ts    # 快捷回复 API
│   ├── templates.ts        # 模板 API
│   ├── agents.ts           # 坐席管理 API（Admin）
│   ├── assist-requests.ts  # 协助请求 API
│   ├── shopify.ts          # Shopify 订单 API
│   ├── warmup.ts           # 缓存预热 API
│   ├── cdn.ts              # CDN 健康检查 API
│   ├── misc.ts             # 杂项（客户档案、内部备注等）
│   └── sse.ts              # SSE 连接封装
│
├── stores/                 # 全局状态（zustand）
│   ├── auth.ts             # 登录状态、token、当前用户
│   ├── sessions.ts         # 会话列表、选中会话
│   └── notifications.ts    # 通知/提醒状态
│
├── pages/                  # 页面组件
│   └── Login.tsx           # 登录页
│
├── components/             # 现有组件（改造）
│   ├── App.tsx             # 根组件（路由守卫）
│   ├── Sidebar.tsx         # 侧边栏
│   ├── Topbar.tsx          # 顶部栏
│   ├── Workspace.tsx       # 会话工作台
│   ├── TicketsView.tsx     # 工单中心
│   ├── Dashboard.tsx       # 仪表盘
│   ├── Monitoring.tsx      # 监控页
│   ├── Settings.tsx        # 设置
│   ├── KnowledgeBase.tsx   # 知识库（P2）
│   ├── QualityAudit.tsx    # 质检（P2）
│   └── BillingView.tsx     # 计费（iframe）
│
├── hooks/                  # 自定义 Hooks（可选）
│   └── useSSE.ts           # SSE 连接 Hook
│
└── types/                  # TypeScript 类型定义
    └── index.ts            # 统一导出
```

### 6.3 状态管理架构

```
┌─────────────────────────────────────────────────────────────┐
│                        React App                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ auth store  │  │sessions store│  │ notifications store│ │
│  ├─────────────┤  ├─────────────┤  ├─────────────────────┤ │
│  │ token       │  │ list        │  │ items               │ │
│  │ user        │  │ selected    │  │ unreadCount         │ │
│  │ isAdmin     │  │ filters     │  │                     │ │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
│         │                │                     │            │
│         ▼                ▼                     ▼            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    api/client.ts                      │  │
│  │  - 自动注入 Authorization header                      │  │
│  │  - 401 自动跳转登录                                   │  │
│  │  - 错误统一处理                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                              │                              │
└──────────────────────────────┼──────────────────────────────┘
                               ▼
                    ┌──────────────────┐
                    │  Backend API     │
                    │  /api/*          │
                    └──────────────────┘
```
