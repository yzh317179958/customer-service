# 架构说明

> 产品模块：products/agent_workbench
> 最后更新：2025-12-22
> 遵循规范：CLAUDE.md 三层架构

---

## 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Frontend (React 19)                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  App.tsx (路由 + 认证守卫)                                    │  │
│  │  ├── Topbar           ← 顶部导航栏                           │  │
│  │  ├── Sidebar          ← 侧边栏导航                           │  │
│  │  ├── LoginView        ← 登录页                               │  │
│  │  ├── Workspace        ← 会话工作台 (核心)                     │  │
│  │  ├── TicketsView      ← 工单中心                             │  │
│  │  ├── Dashboard        ← 效能报表                             │  │
│  │  ├── KnowledgeBase    ← 知识库                               │  │
│  │  ├── Monitoring       ← 实时大屏                             │  │
│  │  ├── QualityAudit     ← 智能质检                             │  │
│  │  ├── BillingView      ← 计费入口                             │  │
│  │  ├── BillingPortal    ← 计费详情页 (16KB)                    │  │
│  │  └── Settings         ← 系统设置                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              ↓ API 调用                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  API Services (Step 4-7 已完成)                              │  │
│  │  ├── client.ts        ← Axios 实例 (JWT, 拦截器)              │  │
│  │  ├── auth.ts          ← 认证 API                             │  │
│  │  ├── sessions.ts      ← 会话 API                             │  │
│  │  ├── tickets.ts       ← 工单 API                             │  │
│  │  ├── quickReplies.ts  ← 快捷回复 API                         │  │
│  │  └── index.ts         ← 统一导出                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              ↓ 状态管理                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Zustand Stores (Step 8-9 已完成)                            │  │
│  │  ├── authStore.ts     ← 认证状态                             │  │
│  │  ├── sessionStore.ts  ← 会话状态 + SSE                       │  │
│  │  ├── ticketStore.ts   ← 工单状态 + 批量操作                   │  │
│  │  └── index.ts         ← 统一导出                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ HTTP/SSE
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                                  │
│  products/agent_workbench/                                          │
│  ├── routes.py           ← 路由注册                                 │
│  ├── handlers/                                                      │
│  │   ├── auth.py         ← 认证 (17KB)                             │
│  │   ├── sessions.py     ← 会话管理 (31KB)                         │
│  │   ├── tickets.py      ← 工单系统 (51KB)                         │
│  │   ├── quick_replies.py← 快捷回复 (10KB)                         │
│  │   ├── templates.py    ← 模板管理 (6KB)                          │
│  │   ├── agents.py       ← 坐席管理 (8KB)                          │
│  │   ├── assist_requests.py ← 协助请求 (7KB)                       │
│  │   ├── shopify.py      ← 订单查询 (27KB)                         │
│  │   ├── warmup.py       ← 缓存预热 (5KB)                          │
│  │   ├── cdn.py          ← CDN 健康 (2KB)                          │
│  │   └── misc.py         ← 其他接口 (18KB)                         │
│  └── dependencies.py     ← 依赖注入                                 │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Services Layer                                     │
│  ├── services/session/   ← 会话状态管理                             │
│  ├── services/ticket/    ← 工单服务                                 │
│  ├── services/shopify/   ← Shopify 订单                             │
│  ├── services/coze/      ← AI 服务                                  │
│  └── services/bootstrap/ ← 依赖注入注册                             │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                                 │
│  ├── infrastructure/bootstrap/ ← 组件工厂                           │
│  ├── infrastructure/security/  ← JWT 认证、坐席管理（PG 双写）      │
│  └── infrastructure/database/  ← PostgreSQL + Redis 双写            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 文件结构

### 后端结构（已完成）

```
products/agent_workbench/
├── __init__.py
├── README.md
├── routes.py                   # 路由注册入口
├── dependencies.py             # FastAPI 依赖注入
├── config.py                   # 模块配置
├── handlers/                   # API 处理器
│   ├── __init__.py
│   ├── auth.py                # 坐席认证 (17KB)
│   ├── sessions.py            # 会话管理 (31KB)
│   ├── tickets.py             # 工单系统 (51KB)
│   ├── quick_replies.py       # 快捷回复 (10KB)
│   ├── templates.py           # 模板管理 (6KB)
│   ├── agents.py              # 坐席管理 (8KB)
│   ├── assist_requests.py     # 协助请求 (7KB)
│   ├── shopify.py             # 订单查询 (27KB)
│   ├── warmup.py              # 缓存预热 (5KB)
│   ├── cdn.py                 # CDN 健康 (2KB)
│   └── misc.py                # 其他接口 (18KB)
├── memory-bank/               # 开发文档
│   ├── prd.md
│   ├── tech-stack.md
│   ├── implementation-plan.md
│   ├── progress.md
│   └── architecture.md
└── fronted_origin/            # 前端原型（待改造）
    └── ...
```

### 前端原型结构（已重命名为 frontend/）

```
products/agent_workbench/frontend/   # Step 1: 已从 fronted_origin 重命名
├── index.html                  # 入口 HTML（Step 3: 已移除 CDN Tailwind）
├── index.tsx                   # React 入口（Step 3: 已添加 CSS 导入）
├── index.css                   # Step 3: Tailwind CSS 本地化入口
├── App.tsx                     # 根组件（路由管理）
├── types.ts                    # TypeScript 类型定义
├── constants.tsx               # 常量配置
├── vite.config.ts              # Vite 配置
├── tsconfig.json               # TypeScript 配置（Step 4: 已添加 vite/client）
├── package.json                # 依赖配置（Step 2: 已添加 axios, zustand 等）
├── tailwind.config.js          # Step 3: Tailwind 配置
├── postcss.config.js           # Step 3: PostCSS 配置
├── .env.local                  # 本地环境变量
├── src/                        # Step 4: 新增源码目录
│   ├── api/                   # API 服务层
│   │   ├── client.ts         # Step 4: Axios 实例 + JWT 拦截
│   │   ├── auth.ts           # Step 5: 认证 API 封装
│   │   ├── sessions.ts       # Step 6: 会话 API 封装（列表/接管/消息/SSE）
│   │   ├── tickets.ts        # Step 7: 工单 API 封装（CRUD/SLA/批量操作）
│   │   ├── quickReplies.ts   # Step 7: 快捷回复 API 封装
│   │   └── index.ts          # Step 7: 统一导出
│   ├── stores/               # Step 8-9: 状态管理
│   │   ├── authStore.ts      # Step 8: 认证状态 Store
│   │   ├── sessionStore.ts   # Step 9: 会话状态 Store
│   │   ├── ticketStore.ts    # Step 9: 工单状态 Store
│   │   └── index.ts          # Step 9: 统一导出
│   └── vite-env.d.ts         # Step 4: Vite 环境类型声明
├── components/                 # 页面组件
│   ├── LoginView.tsx          # 登录页 (9KB)
│   ├── Sidebar.tsx            # 侧边栏 (4KB)
│   ├── Topbar.tsx             # 顶部栏 (5KB)
│   ├── Workspace.tsx          # 会话工作台 (15KB) - 核心
│   ├── TicketsView.tsx        # 工单中心 (10KB)
│   ├── Dashboard.tsx          # 效能报表 (8KB)
│   ├── KnowledgeBase.tsx      # 知识库 (7KB)
│   ├── Monitoring.tsx         # 实时监控 (7KB)
│   ├── QualityAudit.tsx       # 智能质检 (7KB)
│   ├── BillingView.tsx        # 计费入口 (1KB)
│   ├── BillingPortal.tsx      # 计费详情 (16KB)
│   └── Settings.tsx           # 系统设置 (6KB)
└── docs/                       # 原型文档
```

### 前端改造后结构（规划中）

```
products/agent_workbench/frontend/
├── public/
│   └── index.html
├── src/
│   ├── api/                   # API 服务层（新增）
│   │   ├── client.ts         # Axios 实例
│   │   ├── auth.ts           # 认证 API
│   │   ├── sessions.ts       # 会话 API
│   │   ├── tickets.ts        # 工单 API
│   │   ├── quickReplies.ts   # 快捷回复 API
│   │   └── index.ts
│   ├── stores/                # Zustand 状态（新增）
│   │   ├── authStore.ts
│   │   ├── sessionStore.ts
│   │   ├── ticketStore.ts
│   │   └── index.ts
│   ├── components/            # 页面组件
│   │   ├── LoginView.tsx
│   │   ├── Sidebar.tsx
│   │   ├── Topbar.tsx
│   │   ├── Workspace.tsx          # 集成快捷回复面板
│   │   ├── TicketsView.tsx
│   │   ├── Dashboard.tsx
│   │   ├── KnowledgeBase.tsx
│   │   ├── Monitoring.tsx
│   │   ├── QualityAudit.tsx
│   │   ├── BillingView.tsx
│   │   ├── BillingPortal.tsx
│   │   ├── Settings.tsx           # 集成话术短语库入口
│   │   ├── QuickReplyPanel.tsx    # 快捷回复弹出面板（Step 13）
│   │   ├── QuickReplyManager.tsx  # 话术短语库管理页面（Step 13）
│   │   └── MessageContent.tsx
│   ├── hooks/                 # 自定义 Hooks
│   │   └── useSSE.ts
│   ├── types/
│   │   └── index.ts
│   ├── constants.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── tailwind.config.js
├── vite.config.ts
├── tsconfig.json
└── package.json
```

---

## 数据流

### 认证流程

```
LoginView
    │
    ├─ 输入账号密码
    │
    ├─ authApi.login()
    │       │
    │       ▼
    │   POST /api/login
    │       │
    │       ▼
    │   返回 { token, agent }
    │
    ├─ authStore.setToken()
    │       │
    │       ▼
    │   localStorage.setItem('token', ...)
    │
    └─ 跳转到 Workspace
```

### 会话工作流

```
AI 客服转人工
    │
    ▼
会话进入队列 (SSE: new_session)
    │
    ▼
Workspace 显示新会话
    │
    ├─ 坐席点击接管
    │       │
    │       ▼
    │   POST /api/sessions/{id}/takeover
    │
    ├─ 收发消息 (SSE 双向)
    │       │
    │       ▼
    │   POST /api/sessions/{id}/messages
    │   GET  /api/sessions/{id}/events (SSE)
    │
    └─ 结束会话
            │
            ▼
        POST /api/sessions/{id}/release
```

---

## 关键设计决策

### 1. 复用原型界面

**决策**：直接迁移 `fronted_origin` 组件，保持 UI 设计不变。

**原因**：
- 原型已经过设计审核
- 减少重复工作
- 保持视觉一致性

**注意**：目录名 `fronted_origin` 存在拼写错误（少了字母 n），改造时重命名为 `frontend`。

### 2. Zustand 状态管理

**决策**：使用 Zustand 而非 Redux。

**原因**：
- 轻量级，学习成本低
- 与 React 无缝集成
- 足够应对当前规模

### 3. SSE 实时通信

**决策**：使用 SSE 而非 WebSocket。

**原因**：
- 后端已有 SSE 实现
- 单向推送场景足够
- 更简单的错误处理

### 4. JWT 自动续期

**决策**：通过 Axios 拦截器实现 Token 自动刷新。

**原因**：
- 用户无感知
- 避免频繁登录
- 安全性保障

### 5. 计费模块 iframe

**决策**：BillingView 通过 iframe 嵌入 customer_portal。

**原因**：
- 计费是独立产品
- 避免代码耦合
- 支持独立部署

---

## 依赖关系

```
products/agent_workbench
    │
    ├── services/session (会话状态)
    │
    ├── services/ticket (工单服务 - PostgreSQL 双写)
    │       └── store.py, audit.py
    │
    ├── services/shopify (订单查询)
    │
    ├── services/coze (AI 服务)
    │
    ├── infrastructure/bootstrap (组件工厂)
    │
    ├── infrastructure/security (JWT 认证、坐席管理 - PostgreSQL 双写)
    │       └── agent_auth.py
    │
    └── infrastructure/database (PostgreSQL + Redis)
            ├── models/      (ORM 模型)
            ├── converters.py (Pydantic ↔ ORM)
            └── connection.py (连接池)
```

### 数据存储策略

| 数据类型 | 主存储 | 缓存 | 说明 |
|----------|--------|------|------|
| 工单数据 | PostgreSQL | Redis | 双写模式 |
| 坐席账号 | PostgreSQL | Redis | 双写模式 |
| 审计日志 | PostgreSQL | Redis | 双写模式 |
| 活跃会话 | Redis | - | 高频读写 |
| 快捷回复 | Redis | - | 缓存 |

**禁止依赖**：
- ❌ products/ai_chatbot（产品间禁止互相依赖）
- ❌ products/customer_portal
