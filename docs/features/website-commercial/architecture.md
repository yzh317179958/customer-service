# 官网商业化 - 架构说明

> **功能名称**：官网商业化
> **最后更新**：2025-12-30
> **遵循规范**：CLAUDE.md 三层架构

---

## 一、整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                               nginx (443/80)                                 │
│                            ai.fiido.com SSL 终结                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  /                →  /var/www/fiido-website (官网前端)                       │
│  /api/*           →  127.0.0.1:8003 (官网后端)                               │
│  /chat-test       →  /var/www/fiido-frontend (AI客服前端)                    │
│  /chat-api/*      →  127.0.0.1:8000 (AI客服后端)                             │
│  /workbench       →  /var/www/fiido-workbench (工作台前端)                   │
│  /workbench-api/* →  127.0.0.1:8002 (工作台后端)                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐
│  官网 (website)   │    │  AI 客服           │    │  坐席工作台        │
│  Port: 8003       │    │  Port: 8000        │    │  Port: 8002        │
│  fiido-website    │    │  fiido-ai-chatbot  │    │  fiido-agent-      │
│  .service         │    │  .service          │    │  workbench.service │
└─────────┬─────────┘    └─────────┬──────────┘    └─────────┬─────────┘
          │                        │                          │
          └────────────────────────┼──────────────────────────┘
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Services 服务层                                    │
│                                                                             │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │
│  │billing │ │shopify │ │ email  │ │ coze   │ │ ticket │ │session │        │
│  │(扩展)  │ │        │ │        │ │        │ │        │ │        │        │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Infrastructure 基础设施层                             │
│                                                                             │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐                   │
│  │database│ │security│ │bootstrap│ │scheduler│ │ log    │                   │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │  Redis + PgSQL  │
                          └─────────────────┘
```

---

## 二、模块详情

### 2.1 products/website/

**职责**：官网前端展示 + 后端 API

**目录结构**（规划）：
```
products/website/
├── main.py                # FastAPI 入口
├── routes.py              # 路由定义
├── models.py              # Pydantic 模型
├── handlers/
│   ├── auth.py           # 认证处理
│   ├── leads.py          # 表单收集
│   └── payment.py        # 支付处理
├── frontend/
│   └── crossborder-ai-solutions/  # 官网原型
└── memory-bank/
    └── cross-module-refs.md
```

### 2.2 services/billing/

**职责**：计费核心逻辑（套餐、订阅、支付、用量）

**目录结构**（规划）：
```
services/billing/
├── __init__.py
├── service.py             # 统一入口
├── plans.py               # 套餐管理
├── subscriptions.py       # 订阅管理
├── usage.py               # 用量计费
├── stripe_gateway.py      # Stripe 集成
├── models.py              # 数据模型
└── migrations/
    └── 001_billing_tables.sql
```

### 2.3 products/customer_portal/

**职责**：客户自助管理（订阅、用量、账单）

**状态**：规划中，已有 PRD

---

## 三、数据流

### 3.1 注册流程

```
用户 → 官网前端 → POST /api/auth/register
                       │
                       ▼
               products/website/handlers/auth.py
                       │
                       ├── 验证输入
                       ├── 密码 bcrypt 哈希
                       ├── 创建 tenant
                       ├── 创建 user
                       ├── 创建免费版订阅
                       └── 签发 JWT Token
                               │
                               ▼
                         返回 Token + User
```

### 3.2 支付流程

```
用户选择套餐 → POST /api/payment/create-session
                       │
                       ▼
               products/website/handlers/payment.py
                       │
                       ▼
               services/billing/stripe_gateway.py
                       │
                       ├── 创建 Stripe Checkout Session
                       └── 返回 Session URL
                               │
                               ▼
用户跳转 Stripe Checkout → 完成支付
                               │
                               ▼
               Stripe Webhook → POST /api/payment/webhook
                               │
                               ▼
               services/billing/subscriptions.py
                       │
                       ├── 更新订阅状态
                       ├── 记录支付信息
                       └── 发送确认邮件
```

---

## 四、接口定义

（开发过程中逐步补充详细接口文档）

---

## 五、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-30 | 初始版本 |
