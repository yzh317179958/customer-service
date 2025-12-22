# 坐席工作台 - 技术栈

> 产品模块：products/agent_workbench
> 创建日期：2025-12-21
> 最后更新：2025-12-22

---

## 复用现有技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **产品层** | FastAPI | products/agent_workbench（后端已完成） |
| **服务层** | services/session | 会话状态管理 |
| | services/ticket | 工单服务（PostgreSQL 双写） |
| | services/shopify | 订单查询 |
| | services/coze | AI 对话（用于智能建议） |
| **基础设施层** | infrastructure/bootstrap | 组件工厂、依赖注入 |
| | infrastructure/security | JWT 认证、坐席管理（PostgreSQL 双写） |
| | infrastructure/database | PostgreSQL + Redis 双写 |
| **前端** | React 19 + TypeScript | 复用 fronted_origin 原型 |
| | Tailwind CSS（CDN） | 样式框架（原型使用 CDN） |
| | Zustand | 轻量状态管理（待安装） |
| | Axios | HTTP 客户端（待安装） |
| | Lucide React | 图标库（已有） |
| | Recharts | 图表库（已有） |
| **数据存储** | PostgreSQL | 工单、坐席、审计日志（主存储） |
| | Redis | 会话、快捷回复（缓存） |
| **实时通信** | SSE | 服务端推送事件 |

---

## 新增依赖

### 前端原型已有依赖

```json
{
  "dependencies": {
    "react": "^19.2.3",
    "react-dom": "^19.2.3",
    "lucide-react": "^0.561.0",
    "recharts": "^3.6.0",
    "@google/genai": "^1.34.0"
  },
  "devDependencies": {
    "@types/node": "^22.14.0",
    "@vitejs/plugin-react": "^5.0.0",
    "typescript": "~5.8.2",
    "vite": "^6.2.0"
  }
}
```

### 需要新增的依赖

```json
{
  "dependencies": {
    "react-router-dom": "^6.x",
    "axios": "^1.6.0",
    "zustand": "^4.4.0",
    "clsx": "^2.0.0"
  },
  "devDependencies": {
    "@types/react": "^19.0.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }
}
```

**说明**：
- 原型使用 CDN 加载 Tailwind，生产环境需本地化
- @google/genai 是原型中的依赖，生产环境可能不需要

---

## 数据存储方案

### PostgreSQL 数据表（主存储）

| 表名 | 用途 | 双写模式 |
|------|------|----------|
| tickets | 工单主表 | ✅ |
| ticket_comments | 工单评论 | ✅ |
| ticket_attachments | 工单附件 | ✅ |
| ticket_status_history | 状态历史 | ✅ |
| ticket_assignments | 指派历史 | ✅ |
| agents | 坐席账号 | ✅ |
| audit_logs | 审计日志 | ✅ |
| session_archives | 会话归档 | - |
| email_records | 邮件记录 | - |

### Redis 数据结构（缓存）

```
# 会话状态
session:{session_name} → Hash {
  status, agent_id, customer_info, messages, ...
}

# 会话队列
session:queue:{priority} → Sorted Set (score=timestamp)

# 工单
ticket:{ticket_id} → Hash {
  id, title, status, priority, assignee, sla_deadline, ...
}

# 坐席状态
agent:{agent_id}:status → String (online/busy/offline)

# 快捷回复
quick_reply:{agent_id}:{reply_id} → Hash
```

---

## API 设计

### 认证模块 `/api/agent/*`

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| POST | /api/login | 坐席登录 | ✅ 已有 |
| POST | /api/logout | 坐席登出 | ✅ 已有 |
| POST | /api/refresh | Token 刷新 | ✅ 已有 |
| GET | /api/profile | 获取坐席信息 | ✅ 已有 |
| PUT | /api/profile | 更新坐席信息 | ✅ 已有 |
| GET | /api/status | 获取坐席状态 | ✅ 已有 |
| PUT | /api/status | 更新坐席状态 | ✅ 已有 |
| POST | /api/change-password | 修改密码 | ✅ 已有 |

### 会话模块 `/api/sessions/*`

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | /api/sessions | 获取会话列表 | ✅ 已有 |
| GET | /api/sessions/queue | 获取待接入队列 | ✅ 已有 |
| GET | /api/sessions/stats | 会话统计 | ✅ 已有 |
| GET | /api/sessions/{id} | 获取会话详情 | ✅ 已有 |
| POST | /api/sessions/{id}/takeover | 接管会话 | ✅ 已有 |
| POST | /api/sessions/{id}/transfer | 转接会话 | ✅ 已有 |
| POST | /api/sessions/{id}/release | 释放会话 | ✅ 已有 |
| POST | /api/sessions/{id}/messages | 发送消息 | ✅ 已有 |
| GET | /api/sessions/{id}/events | SSE 事件流 | ✅ 已有 |

### 工单模块 `/api/tickets/*`

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | /api/tickets | 工单列表 | ✅ 已有 |
| POST | /api/tickets | 创建工单 | ✅ 已有 |
| GET | /api/tickets/{id} | 工单详情 | ✅ 已有 |
| PATCH | /api/tickets/{id} | 更新工单 | ✅ 已有 |
| POST | /api/tickets/{id}/assign | 分配工单 | ✅ 已有 |
| POST | /api/tickets/{id}/comments | 添加评论 | ✅ 已有 |
| GET | /api/tickets/sla-dashboard | SLA 仪表盘 | ✅ 已有 |
| POST | /api/tickets/filter | 高级筛选 | ✅ 已有 |
| POST | /api/tickets/export | 导出工单 | ✅ 已有 |

### 快捷回复 `/api/quick-replies/*`

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | /api/quick-replies | 获取快捷回复列表 | ✅ 已有 |
| POST | /api/quick-replies | 创建快捷回复 | ✅ 已有 |
| PUT | /api/quick-replies/{id} | 更新快捷回复 | ✅ 已有 |
| DELETE | /api/quick-replies/{id} | 删除快捷回复 | ✅ 已有 |

### Shopify 订单 `/api/shopify/*`

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | /api/shopify/order/{order_id} | 查询订单 | ✅ 已有 |
| GET | /api/shopify/customer/{email} | 客户订单 | ✅ 已有 |

### 模板管理 `/api/templates/*`

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | /api/templates | 模板列表 | ✅ 已有 |
| POST | /api/templates | 创建模板 | ✅ 已有 |
| PUT | /api/templates/{id} | 更新模板 | ✅ 已有 |
| DELETE | /api/templates/{id} | 删除模板 | ✅ 已有 |

### 客户信息 `/api/customers/*`

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | /api/customers/{id} | 客户详情 | ✅ 已有 |
| PUT | /api/customers/{id} | 更新客户 | ✅ 已有 |

### 管理员操作 `/api/admin/*`

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | /api/admin/agents | 坐席列表 | ✅ 已有 |
| POST | /api/admin/agents | 创建坐席 | ✅ 已有 |

---

## 前端架构

### 原型目录结构（fronted_origin/）

```
products/agent_workbench/fronted_origin/
├── index.html                  # 入口（CDN Tailwind）
├── index.tsx                   # React 入口
├── App.tsx                     # 根组件
├── types.ts                    # 类型定义
├── constants.tsx               # 常量
├── components/                 # 12 个页面组件
│   ├── LoginView.tsx
│   ├── Sidebar.tsx
│   ├── Topbar.tsx
│   ├── Workspace.tsx
│   ├── TicketsView.tsx
│   ├── Dashboard.tsx
│   ├── KnowledgeBase.tsx
│   ├── Monitoring.tsx
│   ├── QualityAudit.tsx
│   ├── BillingView.tsx
│   ├── BillingPortal.tsx
│   └── Settings.tsx
├── vite.config.ts
├── tsconfig.json
└── package.json
```

### 改造后目录结构（frontend/，规划中）

```
products/agent_workbench/frontend/
├── public/
│   └── index.html
├── src/
│   ├── api/                    # API 服务层（新增）
│   │   ├── client.ts          # Axios 实例（拦截器）
│   │   ├── auth.ts            # 认证 API
│   │   ├── sessions.ts        # 会话 API
│   │   ├── tickets.ts         # 工单 API
│   │   └── index.ts           # 统一导出
│   ├── stores/                 # Zustand 状态管理（新增）
│   │   ├── authStore.ts       # 认证状态
│   │   ├── sessionStore.ts    # 会话状态
│   │   ├── ticketStore.ts     # 工单状态
│   │   └── index.ts
│   ├── components/             # 页面组件（迁移自原型）
│   │   └── ...
│   ├── hooks/                  # 自定义 Hooks（新增）
│   │   └── useSSE.ts          # SSE 连接管理
│   ├── types/                  # TypeScript 类型
│   │   └── index.ts
│   ├── App.tsx                 # 根组件
│   ├── main.tsx               # 入口
│   └── index.css              # Tailwind 入口
├── tailwind.config.js
├── vite.config.ts
├── tsconfig.json
└── package.json
```

### 状态管理架构

```
┌─────────────────────────────────────────────────────┐
│                    React Components                   │
└─────────────────────────────────────────────────────┘
                         ↓ use hooks
┌─────────────────────────────────────────────────────┐
│                    Zustand Stores                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ authStore│  │sessionStore│  │ticketStore│         │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
└───────┼─────────────┼─────────────┼─────────────────┘
        ↓             ↓             ↓
┌─────────────────────────────────────────────────────┐
│                    API Services                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ auth.ts  │  │sessions.ts│  │tickets.ts │          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
└───────┼─────────────┼─────────────┼─────────────────┘
        ↓             ↓             ↓
┌─────────────────────────────────────────────────────┐
│                    Axios Client                       │
│  - BaseURL 配置                                      │
│  - JWT 自动注入                                      │
│  - 401 拦截跳转                                      │
│  - 错误统一处理                                      │
└─────────────────────────────────────────────────────┘
```

---

## 生产环境要求

### 安全性
- HTTPS 强制
- JWT Token 过期自动刷新
- 敏感操作二次确认
- CORS 白名单配置

### 性能
- 代码分割（React.lazy）
- 资源 CDN 加速
- API 响应缓存
- SSE 断线重连

### 可维护性
- TypeScript 类型安全
- ESLint + Prettier 代码规范
- 环境变量配置分离
- 统一错误处理

### 监控
- API 请求日志
- 错误上报
- 性能指标收集
