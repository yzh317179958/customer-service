# 坐席工作台 - 技术栈

> 产品模块：products/agent_workbench
> 创建日期：2025-12-21
> 最后更新：2025-12-23

---

## 一、部署架构

### 1.1 微服务模式

坐席工作台作为独立微服务运行：

| 配置项 | 值 |
|--------|-----|
| 服务端口 | 8002 |
| systemd 服务 | fiido-agent-workbench |
| 前端部署 | /var/www/fiido-workbench/ |
| API 路径 | /workbench-api/* |
| 访问地址 | https://ai.fiido.com/workbench/ |

### 1.2 启动方式

```bash
# 微服务启动（生产环境）
uvicorn products.agent_workbench.main:app --host 127.0.0.1 --port 8002

# systemd 管理
systemctl start fiido-agent-workbench
systemctl status fiido-agent-workbench
journalctl -u fiido-agent-workbench -f
```

---

## 二、后端技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **产品层** | FastAPI | products/agent_workbench（后端已完成） |
| **服务层** | services/session | 会话状态管理 |
| | services/ticket | 工单服务（PostgreSQL 双写） |
| | services/shopify | 订单查询 |
| | services/coze | AI 对话（用于智能建议） |
| **基础设施层** | infrastructure/bootstrap | 组件工厂、依赖注入、SSE |
| | infrastructure/security | JWT 认证、坐席管理（PostgreSQL 双写） |
| | infrastructure/database | PostgreSQL + Redis 双写 |
| **数据存储** | PostgreSQL | 工单、坐席、审计日志（主存储） |
| | Redis | 会话、快捷回复（缓存） |
| **实时通信** | SSE | 服务端推送事件 |

---

## 三、前端技术栈

| 模块 | 技术 | 说明 |
|------|------|------|
| 框架 | React 19 | 最新 React 版本 |
| 类型检查 | TypeScript | 类型安全 |
| 构建工具 | Vite | 快速开发和构建 |
| 样式 | Tailwind CSS | 实用优先的 CSS 框架 |
| 状态管理 | Zustand | 轻量状态管理 |
| HTTP 客户端 | Axios | API 请求 |
| 图标库 | Lucide React | 图标组件 |
| 图表库 | Recharts | 数据可视化 |
| 路由 | React Router | 页面路由 |

---

## 四、前端依赖

```json
{
  "dependencies": {
    "react": "^19.2.3",
    "react-dom": "^19.2.3",
    "react-router-dom": "^6.x",
    "axios": "^1.6.0",
    "zustand": "^4.4.0",
    "lucide-react": "^0.561.0",
    "recharts": "^3.6.0",
    "clsx": "^2.0.0"
  },
  "devDependencies": {
    "@types/node": "^22.14.0",
    "@types/react": "^19.0.0",
    "@vitejs/plugin-react": "^5.0.0",
    "typescript": "~5.8.2",
    "vite": "^6.2.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }
}
```

---

## 五、数据存储方案

### 5.1 PostgreSQL 数据表（主存储）

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

### 5.2 Redis 数据结构（缓存）

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

## 六、API 端点

### 6.1 认证模块 `/api/agent/*`

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

### 6.2 会话模块 `/api/sessions/*`

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

### 6.3 工单模块 `/api/tickets/*`

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

### 6.4 其他模块

- 快捷回复 `/api/quick-replies/*` - ✅ 已完成
- Shopify 订单 `/api/shopify/*` - ✅ 已完成
- 模板管理 `/api/templates/*` - ✅ 已完成
- 客户信息 `/api/customers/*` - ✅ 已完成
- 管理员操作 `/api/admin/*` - ✅ 已完成

---

## 七、systemd 服务配置

```ini
# /etc/systemd/system/fiido-agent-workbench.service
[Unit]
Description=Fiido Agent Workbench Microservice
After=network.target redis-server.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/fiido-ai-service
Environment="PATH=/opt/fiido-ai-service/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=/opt/fiido-ai-service"
EnvironmentFile=/opt/fiido-ai-service/.env
ExecStart=/opt/fiido-ai-service/venv/bin/uvicorn products.agent_workbench.main:app --host 127.0.0.1 --port 8002
Restart=always
RestartSec=5
MemoryMax=4G

[Install]
WantedBy=multi-user.target
```

---

## 八、nginx 配置

```nginx
# 坐席工作台前端
location /workbench/ {
    alias /var/www/fiido-workbench/;
    try_files $uri $uri/ /workbench/index.html;
}

# 坐席工作台 API
location /workbench-api/ {
    rewrite ^/workbench-api/(.*) /$1 break;
    proxy_pass http://127.0.0.1:8002;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 300s;
    proxy_buffering off;
}
```

---

## 九、生产环境要求

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

---

## 十、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0 | 2025-12-23 | 更新为微服务架构，添加 systemd/nginx 配置，整理 API 端点 |
| v1.0 | 2025-12-21 | 初始版本 |
