# 物流通知 - 技术栈说明

> **创建日期**：2025-12-23

---

## 一、后端技术

| 技术 | 用途 |
|------|------|
| FastAPI | Web 框架、Webhook 接收 |
| Pydantic | 数据验证 |
| Jinja2 | 邮件模板渲染 |
| httpx | HTTP 客户端 |

---

## 二、依赖服务

| 服务 | 模块 | 说明 |
|------|------|------|
| 17track API | services/tracking | 物流追踪 |
| Shopify API | services/shopify | 订单数据 |
| 邮件服务 | services/email | 通知发送 |

---

## 三、外部集成

| 服务 | 方式 | 说明 |
|------|------|------|
| 17track | Webhook 推送 | 物流状态变更通知 |
| Shopify | Webhook 推送 | 发货事件通知 |

---

## 四、数据存储

| 存储 | 用途 |
|------|------|
| Redis | 缓存、去重 |
| PostgreSQL | 通知记录持久化 |

---

## 五、部署方式

- **独立模式**：`uvicorn products.notification.main:app --port 8001`
- **全家桶模式**：通过 `backend.py` 注册路由
