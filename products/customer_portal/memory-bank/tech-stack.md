# 客户控制台 - 技术栈说明

> **创建日期**：2025-12-19
> **最后更新**：2025-12-22

---

## 1. 复用现有技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端框架 | FastAPI | 已有，直接复用 |
| 数据存储 | PostgreSQL + Redis | 已有，PostgreSQL 主存储 + Redis 缓存（双写模式） |
| ORM | SQLAlchemy 2.0 | 已有，infrastructure/database |
| 认证鉴权 | JWT | 已有 infrastructure/security |
| 前端框架 | Vue 3 + TypeScript | 已有，复用工作台技术栈 |

---

## 2. 新增依赖

### 2.1 后端

| 依赖 | 用途 | 是否新增 |
|------|------|----------|
| pydantic | 数据模型 | 已有 |
| redis | 缓存 | 已有 |
| 无新增 | - | - |

### 2.2 前端（如果独立部署）

| 依赖 | 用途 | 是否新增 |
|------|------|----------|
| Vue 3 | 前端框架 | 已有 |
| Vue Router | 路由 | 已有 |
| Pinia | 状态管理 | 已有 |
| Axios | HTTP 请求 | 已有 |
| ECharts | 用量图表 | 可选新增 |

---

## 3. 数据存储方案

### 3.1 Redis 数据结构

```python
# 客户账户信息（缓存）
customer:{customer_id}:info = {
    "company_name": "xxx公司",
    "contact_name": "张三",
    "contact_email": "xxx@example.com",
    "created_at": "2025-01-01T00:00:00Z"
}

# 客户订阅信息
customer:{customer_id}:subscription = {
    "plan_id": "pro",
    "plan_name": "专业版",
    "start_date": "2025-01-01",
    "end_date": "2025-12-31",
    "status": "active"  # active/expired/cancelled
}

# 套餐定义
plans:{plan_id} = {
    "name": "专业版",
    "price": 999,
    "period": "month",
    "features": {
        "ai_chat_quota": 10000,      # AI对话次数
        "agent_seats": 5,             # 坐席数量
        "email_quota": 1000           # 邮件发送数
    }
}

# 用量统计（按日）
usage:{customer_id}:{date}:{product} = {
    "count": 150,
    "updated_at": "2025-12-19T10:00:00Z"
}

# 用量汇总（按月）
usage:{customer_id}:{month}:summary = {
    "ai_chat": 3000,
    "email": 500,
    "updated_at": "2025-12-19T10:00:00Z"
}

# 账单记录
billing:{customer_id}:invoices = [
    {
        "invoice_id": "INV202512001",
        "amount": 999,
        "period": "2025-12",
        "status": "paid",
        "created_at": "2025-12-01"
    }
]
```

### 3.2 PostgreSQL 数据表（推荐）

使用 `infrastructure/database` 提供的 PostgreSQL 持久化：

```sql
-- 客户表
CREATE TABLE customers (
    id VARCHAR(32) PRIMARY KEY,
    company_name VARCHAR(200),
    contact_name VARCHAR(100),
    contact_email VARCHAR(200),
    created_at TIMESTAMP
);

-- 订阅表
CREATE TABLE subscriptions (
    id VARCHAR(32) PRIMARY KEY,
    customer_id VARCHAR(32) REFERENCES customers(id),
    plan_id VARCHAR(32),
    start_date DATE,
    end_date DATE,
    status VARCHAR(20)  -- active/expired/cancelled
);

-- 用量表
CREATE TABLE usage_logs (
    id BIGSERIAL PRIMARY KEY,
    customer_id VARCHAR(32),
    product VARCHAR(50),
    count INT,
    date DATE,
    CONSTRAINT idx_customer_date UNIQUE (customer_id, date, product)
);

-- 账单表
CREATE TABLE invoices (
    id VARCHAR(32) PRIMARY KEY,
    customer_id VARCHAR(32),
    amount DECIMAL(10,2),
    period VARCHAR(7),  -- 2025-12
    status VARCHAR(20),  -- pending/paid/overdue
    created_at TIMESTAMP
);
```

**注意**：PostgreSQL 已在 infrastructure/database 模块中配置完成，开发时直接使用 SQLAlchemy ORM 模型即可。

---

## 4. API 设计

### 4.1 RESTful 风格

```
GET    /api/portal/account           # 获取账户信息
PUT    /api/portal/account           # 更新账户信息
GET    /api/portal/subscription      # 获取当前订阅
GET    /api/portal/plans             # 获取可用套餐
POST   /api/portal/subscription/upgrade  # 升级套餐
GET    /api/portal/usage             # 获取用量概览
GET    /api/portal/usage/detail      # 获取用量明细
GET    /api/portal/invoices          # 获取账单列表
GET    /api/portal/invoices/{id}     # 获取账单详情
GET    /api/portal/invoices/{id}/pdf # 下载发票 PDF
```

### 4.2 认证方式

```
Authorization: Bearer <jwt_token>

# Token 中包含
{
    "customer_id": "cust_xxx",
    "user_id": "user_xxx",
    "role": "admin"  # admin/member
}
```

---

## 5. 嵌入方案

### 5.1 iframe 嵌入（推荐 MVP）

```html
<!-- 坐席工作台中 -->
<iframe
  :src="`${portalUrl}?token=${userToken}`"
  width="100%"
  height="100%"
  frameborder="0"
  allow="clipboard-write"
/>
```

### 5.2 消息通信

```javascript
// 父页面（工作台）发送 token
iframe.contentWindow.postMessage({
  type: 'auth',
  token: userToken
}, portalOrigin);

// 子页面（控制台）接收
window.addEventListener('message', (event) => {
  if (event.data.type === 'auth') {
    setToken(event.data.token);
  }
});
```

---

## 6. 技术约束

| 约束 | 说明 |
|------|------|
| 后端复用 | 必须使用 FastAPI，保持技术栈一致 |
| 服务调用 | 必须通过 services/billing，不直接操作数据 |
| 认证复用 | 必须使用 infrastructure/security |
| 无外部依赖 | MVP 阶段不引入新的外部服务 |
