# 官网商业化 - 跨模块技术栈

> **功能名称**：官网商业化
> **创建日期**：2025-12-30
> **涉及模块**：website、billing、customer_portal、ai_chatbot

---

## 一、复用现有技术栈

| 层级 | 技术/服务 | 用途 |
|------|----------|------|
| **产品层** | products/ai_chatbot | 嵌入官网的 AI 客服组件 |
| **服务层** | services/billing（扩展） | 套餐、订阅、支付集成 |
| **基础设施层** | infrastructure/security | JWT 认证、Token 签发 |
| **基础设施层** | infrastructure/database | PostgreSQL + Redis |
| **基础设施层** | infrastructure/bootstrap | 依赖注入 |

---

## 二、官网前端技术栈（已有原型）

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 19.x | UI 框架 |
| TypeScript | 5.x | 类型安全 |
| Vite | 6.x | 构建工具 |
| Tailwind CSS | CDN | 样式框架 |
| Framer Motion | 12.x | 动画效果 |
| Lucide React | 0.561 | 图标库 |
| Recharts | 3.x | 图表（ROI 计算器） |

---

## 三、新增依赖

### 3.1 后端依赖

| 依赖 | 用途 | 原因 |
|------|------|------|
| stripe | Stripe 支付集成 | 海外支付标准方案 |
| python-jose | JWT 处理 | 已有，复用 |
| pydantic | 数据验证 | 已有，复用 |

### 3.2 前端依赖

| 依赖 | 用途 | 原因 |
|------|------|------|
| react-router-dom | 客户端路由 | 支持注册/登录等独立页面 |
| @stripe/stripe-js | Stripe 前端 SDK | 支付集成 |

---

## 四、跨模块通信方案

### 4.1 通信方式选型

| 方式 | 使用场景 | 是否采用 |
|------|---------|----------|
| **HTTP API** | website → billing 服务调用 | ✅ 采用 |
| **直接导入** | website → security 模块 | ✅ 采用 |
| **数据库共享** | 租户/订阅数据 | ✅ 采用 |
| Redis Pub/Sub | 实时通知 | ❌ 暂不需要 |

### 4.2 调用关系

```
products/website/
    │
    ├── import infrastructure/security   # JWT 认证
    ├── import infrastructure/database   # 数据库连接
    └── import services/billing          # 计费服务

services/billing/
    │
    ├── import infrastructure/database   # 数据存储
    └── import stripe                    # 支付网关
```

---

## 五、数据存储方案

### 5.1 PostgreSQL 表结构

| 表名 | 用途 | 状态 |
|------|------|------|
| `tenants` | 租户（客户）信息 | 需新建 |
| `users` | 用户账号 | 需新建 |
| `subscriptions` | 订阅记录 | 需新建 |
| `plans` | 套餐定义 | 需新建 |
| `usage_records` | 用量记录 | 需新建 |
| `invoices` | 账单记录 | 需新建 |
| `leads` | 线索收集 | 需新建 |

### 5.2 表设计

```sql
-- 租户表
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    shopify_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 套餐表
CREATE TABLE plans (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price_monthly DECIMAL(10,2),
    price_yearly DECIMAL(10,2),
    features JSONB,
    limits JSONB,
    is_active BOOLEAN DEFAULT true
);

-- 订阅表
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    plan_id VARCHAR(50) REFERENCES plans(id),
    status VARCHAR(50) DEFAULT 'active',
    billing_cycle VARCHAR(20),
    started_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    stripe_subscription_id VARCHAR(255)
);

-- 用量记录表
CREATE TABLE usage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    usage_type VARCHAR(50),
    count INTEGER DEFAULT 1,
    recorded_at TIMESTAMP DEFAULT NOW()
);

-- 线索表
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(50),
    name VARCHAR(255),
    email VARCHAR(255),
    company VARCHAR(255),
    message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 5.3 Redis 数据结构

| Key 模式 | 类型 | 用途 | TTL |
|---------|------|------|-----|
| `session:{user_id}` | String | 用户会话 | 24h |
| `quota:{tenant_id}` | Hash | 当前用量缓存 | 1h |
| `plan:{plan_id}` | Hash | 套餐缓存 | 24h |

---

## 六、API 设计

### 6.1 认证 API

| 方法 | 路径 | 请求体 | 响应 |
|------|------|--------|------|
| POST | /api/auth/register | `{email, password, shopify_url}` | `{token, user}` |
| POST | /api/auth/login | `{email, password}` | `{token, user}` |
| GET | /api/auth/me | - | `{user, tenant, subscription}` |

### 6.2 套餐 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/plans | 获取所有套餐 |
| GET | /api/plans/{id} | 获取单个套餐详情 |

### 6.3 支付 API

| 方法 | 路径 | 请求体 | 说明 |
|------|------|--------|------|
| POST | /api/payment/create-session | `{plan_id, billing_cycle}` | 创建 Stripe Checkout |
| POST | /api/payment/webhook | Stripe Payload | 处理支付回调 |

### 6.4 表单 API

| 方法 | 路径 | 请求体 | 说明 |
|------|------|--------|------|
| POST | /api/leads/demo | `{name, email, company, message}` | 预约演示 |
| POST | /api/leads/contact | `{name, email, message}` | 联系我们 |

---

## 七、部署方案

### 7.1 服务配置

| 服务 | 端口 | systemd 服务名 |
|------|------|----------------|
| 官网后端 | 8003 | fiido-website |
| 官网前端 | 静态文件 | nginx 托管 |

### 7.2 nginx 配置

```nginx
# 官网（主域名根路径）
server {
    server_name ai.fiido.com;

    # 官网前端
    location / {
        alias /var/www/fiido-website/;
        try_files $uri $uri/ /index.html;
    }

    # 官网 API
    location /api/ {
        # 优先匹配官网 API
        proxy_pass http://127.0.0.1:8003;
    }

    # AI 客服 API（保持现有）
    location /chat-api/ {
        proxy_pass http://127.0.0.1:8000/api/;
    }
}
```

---

## 八、安全考虑

| 安全点 | 方案 |
|--------|------|
| 密码存储 | bcrypt 哈希 |
| API 认证 | JWT Token |
| 支付安全 | Stripe Webhook 签名验证 |
| CSRF 防护 | SameSite Cookie |
| 速率限制 | Redis 计数器 |

---

## 九、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-30 | 初始版本 |
