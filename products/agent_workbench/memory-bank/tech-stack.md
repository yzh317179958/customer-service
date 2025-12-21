# 坐席工作台（Agent Workbench）- 技术栈说明

> **创建日期**：2025-12-19
> **最后更新**：2025-12-19
> **原则**：优先复用现有三层架构与服务能力；避免引入不必要新依赖。

---

## 1. 后端（复用现有）

| 层级 | 技术 | 说明 |
|---|---|---|
| 产品层 | FastAPI（`products/agent_workbench`） | 已实现坐席工作台 API（多模块路由） |
| 服务层 | `services/session`、`services/ticket`、`services/shopify`… | 会话/工单/订单查询等复用能力 |
| 基础设施层 | `infrastructure/bootstrap`、`infrastructure/security`、`infrastructure/database` | 组件工厂、JWT 坐席认证、Redis 等 |
| 实时推送 | SSE（队列 + `StreamingResponse`） | 已有坐席事件 SSE；建议补齐会话级 SSE |
| 存储 | Redis（优先）+ 本地文件（附件） | 工单附件默认落到 `ATTACHMENTS_DIR` |

---

## 2. 前端（基于原型复用）

### 2.1 技术栈与依赖版本

> **决策**：直接改造 `fronted_origin/` 目录，保持 React 技术栈

| 模块 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 构建工具 | Vite | ^6.2.0 | 原型已使用 |
| 框架 | React | ^19.2.3 | 原型已使用 |
| 类型 | TypeScript | ~5.8.2 | 原型已使用 |
| UI 样式 | Tailwind CSS | ^3.4.0 | 改为本地依赖（移除 CDN） |
| 样式处理 | PostCSS | ^8.4.0 | Tailwind 必需 |
| 样式处理 | Autoprefixer | ^10.4.0 | 浏览器兼容 |
| 状态管理 | zustand | ^4.5.0 | **新增**：轻量状态管理 |
| 图标 | lucide-react | ^0.561.0 | 原型已使用 |
| 图表 | recharts | ^3.6.0 | Dashboard/报表使用 |

### 2.2 完整依赖清单

**package.json dependencies:**
```json
{
  "react": "^19.2.3",
  "react-dom": "^19.2.3",
  "lucide-react": "^0.561.0",
  "recharts": "^3.6.0",
  "zustand": "^4.5.0"
}
```

**package.json devDependencies:**
```json
{
  "@types/node": "^22.14.0",
  "@types/react": "^19.0.0",
  "@types/react-dom": "^19.0.0",
  "@vitejs/plugin-react": "^5.0.0",
  "autoprefixer": "^10.4.0",
  "postcss": "^8.4.0",
  "tailwindcss": "^3.4.0",
  "typescript": "~5.8.2",
  "vite": "^6.2.0"
}
```

### 2.3 前端目录结构

```
fronted_origin/
├── package.json
├── vite.config.ts
├── tailwind.config.js      # 新增
├── postcss.config.js       # 新增
├── .env.development        # 新增：VITE_API_BASE=http://localhost:8002
├── .env.production         # 新增：VITE_API_BASE=/
└── src/
    ├── api/                # 新增：API 请求封装
    ├── stores/             # 新增：zustand 状态
    ├── pages/              # 新增：登录页等
    ├── components/         # 现有：Workspace/TicketsView/...
    ├── hooks/              # 新增：自定义 Hooks
    └── types/              # 新增：TypeScript 类型
```

---

## 3. 接口与鉴权约定

### 3.1 API Base
开发建议同时支持两种模式：
- **独立模式**：`agent_workbench` 后端 `http://localhost:8002/api`；`ai_chatbot` 后端 `http://localhost:8001/api`
- **全家桶模式**：统一 `http://localhost:8000/api`（按部署脚本与后端注册情况）

### 3.2 鉴权
- 坐席侧 API 使用 `Authorization: Bearer <token>`（`/api/agent/login` 获取）
- 管理员能力需 `require_admin()` 保护（403）

---

## 4. 前端工程化约束（建议）

### 4.1 环境变量（示例）
- `VITE_AGENT_WORKBENCH_API_BASE`：坐席工作台 API Base（如 `http://localhost:8002`）
- `VITE_AI_CHATBOT_API_BASE`：AI 客服 API Base（如 `http://localhost:8001`）
- `VITE_CUSTOMER_PORTAL_URL`：计费门户 iframe 地址（如 `https://portal.fiido.com`）

### 4.2 CORS / Proxy
- 后端 `cors_origins` 目前未包含 `http://localhost:5174`（坐席端常用 dev 端口），建议：
  - 方案A：后端补充 origin；或
  - 方案B：前端 dev server 配置 proxy 到后端，避免跨域。

