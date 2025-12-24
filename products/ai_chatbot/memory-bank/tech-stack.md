# AI 智能客服 - 技术栈说明

> **版本**: v7.7.0
> **创建日期**: 2025-12-24
> **原则**: 优先复用三层架构现有能力，避免引入不必要新依赖

---

## 一、部署架构

### 1.1 微服务模式

AI 智能客服作为独立微服务运行：

| 配置项 | 值 |
|--------|-----|
| 服务端口 | 8000 |
| systemd 服务 | fiido-ai-chatbot |
| 前端部署 | /var/www/fiido-frontend/ |
| API 路径 | /api/* |
| 访问地址 | https://ai.fiido.com/chat-test/ |

### 1.2 启动方式

```bash
# 微服务启动（生产环境）
uvicorn products.ai_chatbot.main:app --host 127.0.0.1 --port 8000

# systemd 管理
systemctl start fiido-ai-chatbot
systemctl status fiido-ai-chatbot
journalctl -u fiido-ai-chatbot -f
```

---

## 二、后端技术栈

### 2.1 核心依赖

| 层级 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 产品层 | FastAPI | 0.104+ | API 框架，支持异步和流式响应 |
| 产品层 | Pydantic | 2.0+ | 请求/响应模型验证 |
| 服务层 | cozepy | latest | Coze API 客户端 |
| 服务层 | Redis | 7.0+ | 会话状态缓存 |
| 服务层 | httpx | 0.24+ | 17track API 客户端 |
| 基础设施层 | PostgreSQL | 15+ | 数据持久化 |
| 基础设施层 | SQLAlchemy | 2.0+ | ORM 框架 |
| 基础设施层 | APScheduler | 3.10+ | 定时任务 |

### 2.2 v7.7.0 新增依赖

| 技术 | 用途 | 优先级 |
|------|------|--------|
| slowapi | 请求限流 | P1 |
| prometheus-client | 监控指标采集 | P1 |

---

## 三、前端技术栈

| 模块 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 框架 | Vue | 3.3+ | Composition API |
| 构建工具 | Vite | 5.0+ | 快速开发和构建 |
| 状态管理 | Pinia | 2.1+ | 轻量级状态管理 |
| 类型检查 | TypeScript | 5.0+ | 类型安全 |
| 样式 | CSS3 | - | 原生 CSS，无框架依赖 |
| Markdown | marked | 9.0+ | AI 回复渲染 |

---

## 四、依赖的服务层

| 服务 | 模块路径 | 功能 |
|------|----------|------|
| Coze AI | `services.coze` | AI 对话、Token 管理、JWT 签名 |
| 会话管理 | `services.session` | 会话状态存储、监管引擎 |
| Shopify | `services.shopify` | 订单查询、物流追踪 |
| 邮件 | `services.email` | 邮件发送（可选） |
| 素材 | `services.asset` | 产品图片匹配 |
| 物流追踪 | `services.tracking` | 17track API 集成、运单注册 |

---

## 五、依赖的基础设施层

| 组件 | 模块路径 | 功能 |
|------|----------|------|
| Bootstrap | `infrastructure.bootstrap` | 组件工厂、依赖注入、SSE |
| 安全 | `infrastructure.security` | JWT 签名 |
| 定时任务 | `infrastructure.scheduler` | 缓存预热调度 |
| 数据库 | `infrastructure.database` | PostgreSQL + Redis 双写 |
| 监控 | `infrastructure.monitoring` | 指标采集（v7.7.0 新增） |

---

## 六、API 鉴权约定

### 6.1 Coze API 鉴权

- 模式：OAuth + JWT（COZE_AUTH_MODE=OAUTH_JWT）
- 私钥：`config/private_key.pem`
- Token 自动刷新：OAuthTokenManager 管理

### 6.2 API 端点（无需鉴权）

AI 客服面向终端用户，所有端点无需认证：

| 端点 | 说明 |
|------|------|
| POST /api/chat | 同步聊天 |
| POST /api/chat/stream | 流式聊天 |
| GET /api/health | 健康检查 |
| GET /api/config | 配置信息 |

### 6.3 v7.7.0 新增：请求限流

| 维度 | 限制 | 说明 |
|------|------|------|
| session_id | 10 次/分钟 | 防止单用户滥用 |
| IP | 100 次/分钟 | 防止 IP 攻击 |
| 全局 | 1000 次/分钟 | 系统保护 |

---

## 七、环境配置

### 7.1 必需配置

```bash
# Coze API
COZE_API_BASE=https://api.coze.com
COZE_WORKFLOW_ID=7577578868671037445
COZE_APP_ID=7577213576494989365
COZE_AUTH_MODE=OAUTH_JWT
COZE_OAUTH_CLIENT_ID=...
COZE_OAUTH_PRIVATE_KEY_FILE=./config/private_key.pem

# Redis
USE_REDIS=true
REDIS_URL=redis://localhost:6379/0

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://fiido:password@localhost:5432/fiido
```

### 7.2 可选配置

```bash
# 功能开关
ENABLE_REGULATOR=true      # 监管引擎
WARMUP_ENABLED=true        # 缓存预热

# 工作时间
HUMAN_SHIFT_START=09:00
HUMAN_SHIFT_END=18:00

# 17track（物流追踪）
TRACK17_API_KEY=...

# v7.7.0 新增
RATE_LIMIT_ENABLED=true    # 限流开关
MONITORING_ENABLED=true    # 监控开关
```

---

## 八、systemd 服务配置

```ini
# /etc/systemd/system/fiido-ai-chatbot.service
[Unit]
Description=Fiido AI Chatbot Microservice
After=network.target redis-server.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/fiido-ai-service
Environment="PATH=/opt/fiido-ai-service/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=/opt/fiido-ai-service"
EnvironmentFile=/opt/fiido-ai-service/.env
ExecStart=/opt/fiido-ai-service/venv/bin/uvicorn products.ai_chatbot.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
MemoryMax=8G

[Install]
WantedBy=multi-user.target
```

---

## 九、nginx 配置

```nginx
# AI 客服前端
location /chat-test/ {
    alias /var/www/fiido-frontend/;
    try_files $uri $uri/ /chat-test/index.html;
}

# AI 客服 API
location /api/ {
    proxy_pass http://127.0.0.1:8000;
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

## 十、v7.7.0 新增技术组件

### 10.1 Intent 意图识别

```python
# products/ai_chatbot/models.py
class UserIntent(str, Enum):
    PRESALE = "presale"           # 售前咨询
    ORDER_STATUS = "order_status" # 订单查询
    AFTER_SALE = "after_sale"     # 售后问题
    CONTACT_AGENT = "contact_agent" # 人工转接
    GENERAL = "general"           # 通用对话
```

### 10.2 售后流程状态机

```typescript
// frontend/src/stores/chatStore.ts
type AfterSaleState =
  | 'idle'           // 空闲
  | 'awaiting_order' // 等待订单号
  | 'validating'     // 校验中
  | 'order_found'    // 订单已找到
  | 'awaiting_issue' // 等待问题描述
```

### 10.3 监控指标

| 指标 | 类型 | 说明 |
|------|------|------|
| request_duration | Histogram | 请求响应时间 |
| coze_api_calls | Counter | Coze 调用次数 |
| coze_api_errors | Counter | Coze 错误次数 |
| human_transfer_total | Counter | 人工转接次数 |
| session_duration | Histogram | 会话时长 |

---

## 十一、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v7.7.0 | 2025-12-24 | 全新创建，新增限流、监控、Intent 技术组件 |
