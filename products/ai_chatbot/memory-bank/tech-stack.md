# AI 智能客服 - 技术栈说明

> **创建日期**：2025-12-21
> **最后更新**：2025-12-21
> **原则**：优先复用三层架构现有能力，避免引入不必要新依赖

---

## 一、后端技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 产品层 | FastAPI | API 框架，支持异步和流式响应 |
| 产品层 | Pydantic | 请求/响应模型验证 |
| 服务层 | cozepy | Coze API 客户端 |
| 服务层 | Redis | 会话状态持久化 |
| 服务层 | SMTP | 邮件发送（可选） |
| 基础设施层 | APScheduler | 定时任务（缓存预热） |
| 基础设施层 | JWT | OAuth 鉴权 |

---

## 二、前端技术栈

| 模块 | 技术 | 说明 |
|------|------|------|
| 框架 | Vue 3 | Composition API |
| 构建工具 | Vite | 快速开发和构建 |
| 状态管理 | Pinia | 轻量级状态管理 |
| 类型检查 | TypeScript | 类型安全 |
| 样式 | CSS3 | 原生 CSS，无框架依赖 |

---

## 三、依赖的服务层

| 服务 | 模块路径 | 功能 |
|------|----------|------|
| Coze AI | services.coze | AI 对话、Token 管理、JWT 签名 |
| 会话管理 | services.session | 会话状态存储、监管引擎 |
| Shopify | services.shopify | 订单查询、物流追踪（可选） |
| 邮件 | services.email | 邮件发送（可选） |
| 素材 | services.asset | 产品图片匹配 |

---

## 四、依赖的基础设施层

| 组件 | 模块路径 | 功能 |
|------|----------|------|
| Bootstrap | infrastructure.bootstrap | 组件工厂、依赖注入 |
| 安全 | infrastructure.security | JWT 签名（如独立认证需要） |
| 定时任务 | infrastructure.scheduler | 缓存预热调度 |

---

## 五、API 鉴权约定

### 5.1 Coze API 鉴权

- 模式：OAuth + JWT（COZE_AUTH_MODE=OAUTH_JWT）
- 私钥：`config/private_key.pem`
- Token 自动刷新：OAuthTokenManager 管理

### 5.2 API 端点（无需鉴权）

AI 客服面向终端用户，所有端点无需认证：

| 端点 | 说明 |
|------|------|
| POST /api/chat | 同步聊天 |
| POST /api/chat/stream | 流式聊天 |
| GET /api/health | 健康检查 |

---

## 六、环境配置

### 6.1 必需配置

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
```

### 6.2 可选配置

```bash
# 功能开关
ENABLE_REGULATOR=true      # 监管引擎
WARMUP_ENABLED=true        # 缓存预热

# 工作时间
HUMAN_SHIFT_START=09:00
HUMAN_SHIFT_END=18:00
```

---

## 七、启动模式

### 7.1 独立模式

```bash
uvicorn products.ai_chatbot.main:app --host 0.0.0.0 --port 8001
```

### 7.2 全家桶模式

```bash
uvicorn backend:app --host 0.0.0.0 --port 8000
```

---

## 八、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-21 | 初始版本 |
