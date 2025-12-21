# Customer Portal 客户控制台

> **产品定位**：客户自助服务平台，管理账户、订阅、计费
> **状态**：规划中
> **最后更新**：2025-12-19

---

## 一、产品概述

客户控制台是一个独立的产品模块，为使用 Fiido AI 平台的客户提供自助服务能力，包括账户管理、套餐订阅、用量查看、账单管理等功能。

### 核心价值

- 客户自助管理订阅，减少人工干预
- 透明的用量和账单展示，提升客户信任
- 独立模块设计，可复用计费服务

---

## 二、UI 入口设计

### 2.1 主要入口

客户控制台通过**坐席工作台侧边栏**进入，采用 iframe 嵌入方式展示：

```
坐席工作台
├── 会话管理
├── 工单管理
├── 客户管理
└── 💳 账户与订阅 ← 点击进入客户控制台（iframe）
```

### 2.2 设计理由

| 考量 | 说明 |
|------|------|
| 用户习惯 | 客户日常使用工作台，入口在侧边栏体验连贯 |
| 架构解耦 | 控制台是独立产品，通过 iframe 嵌入 |
| 未来扩展 | 可独立访问，支持官网/App 等其他入口 |

---

## 三、依赖关系

### 3.1 允许的依赖

```python
# ✅ 依赖 services/billing
from services.billing import BillingService

# ✅ 依赖 infrastructure
from infrastructure.database import get_redis_client
from infrastructure.security import verify_token
```

### 3.2 禁止的依赖

```python
# ❌ 禁止依赖其他产品
from products.agent_workbench import xxx  # 禁止！
from products.ai_chatbot import xxx       # 禁止！
```

---

## 四、目录结构

```
products/customer_portal/
├── __init__.py                 # 模块入口
├── README.md                   # 【本文件】模块规范
├── routes.py                   # API 路由定义
├── models.py                   # 请求/响应模型
├── handlers/                   # 业务处理器
│   ├── __init__.py
│   ├── account.py             # 账户信息
│   ├── subscription.py        # 订阅管理
│   ├── usage.py               # 用量统计
│   └── billing.py             # 账单管理
├── memory-bank/                # Vibe Coding 文档
│   ├── prd.md                 # 产品需求文档
│   ├── tech-stack.md          # 技术栈说明
│   ├── implementation-plan.md # 实现计划
│   ├── progress.md            # 进度追踪
│   └── architecture.md        # 架构说明
└── tests/                      # 单元测试
    └── test_portal.py
```

---

## 五、API 端点规划

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/portal/account` | GET | 获取账户信息 |
| `/api/portal/account` | PUT | 更新账户信息 |
| `/api/portal/subscription` | GET | 获取当前订阅 |
| `/api/portal/subscription/plans` | GET | 获取可用套餐列表 |
| `/api/portal/subscription/upgrade` | POST | 升级套餐 |
| `/api/portal/usage` | GET | 获取用量统计 |
| `/api/portal/usage/detail` | GET | 获取用量明细 |
| `/api/portal/billing/invoices` | GET | 获取账单列表 |
| `/api/portal/billing/invoice/{id}` | GET | 获取账单详情 |

---

## 六、关键设计决策

### 6.1 计费逻辑下沉

- 计费核心逻辑放在 `services/billing`
- 客户控制台只负责 UI 展示和调用服务
- 其他产品（如 AI 客服）也可以调用 billing 服务

### 6.2 嵌入式展示

- 坐席工作台通过 iframe 嵌入控制台页面
- 控制台有独立的前端（可选 Vue/React）
- 通过 token 传递实现身份验证

---

## 七、开发规范

### 7.1 遵循顶层规范

- 遵循 `CLAUDE.md` 全局开发规范
- 遵循 `products/README.md` 产品层规范
- 使用 Vibe Coding 工作流

### 7.2 开发原则

| 原则 | 说明 |
|------|------|
| 文档先行 | 先完善 memory-bank 文档，再写代码 |
| 小步快跑 | 每步只做一件事，立即测试 |
| 调用服务 | 业务逻辑通过 services/billing 实现 |
| 不破坏现有 | 任何改动不能影响其他产品 |

---

## 八、启用控制

### 8.1 环境变量

```bash
# .env
ENABLE_CUSTOMER_PORTAL=false  # 开发完成后改为 true
```

### 8.2 路由注册

```python
# backend.py
if config.ENABLE_CUSTOMER_PORTAL:
    from products.customer_portal.routes import router
    app.include_router(router)
```

---

## 九、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-19 | 初始版本，创建模块框架 |
