# 物流通知 - 技术栈说明

> **创建日期**：2025-12-23
> **最后更新**：2026-01-07

---

## 一、复用现有技术栈（最小引入）

| 技术 | 用途 |
|------|------|
| FastAPI | Webhook 接收、健康检查（产品层） |
| httpx | 调用外部 API（Shopify/17track/易仓） |
| Pydantic | 数据验证、事件模型 |
| Jinja2 | 邮件模板渲染（HTML） |
| Redis | 缓存、幂等去重（推荐） |
| PostgreSQL | 持久化（通知记录、运单映射、重试队列） |

---

## 二、依赖服务

| 服务 | 模块 | 说明 |
|------|------|------|
| Shopify API | `services/shopify` | 多店铺订单/履约查询（Token 从环境变量读取，Redis 做缓存） |
| 邮件服务 | `services/email` | SMTP 发送（可对接 SES/SendGrid 等，避免自建发信） |
| 追踪服务（可选） | `services/tracking` | 当前实现为 17track 聚合追踪；负责“运单注册 + 状态查询 + Webhook 解析” |
| 易仓接口（规划） | `services/yicang`（待建） | 售后配件订单与物流更新（优先 Webhook/回调） |

---

## 三、外部集成选型结论（最优默认）

| 服务 | 方式 | 说明 |
|------|------|------|
| Shopify | Webhook 推送 | 发货事件最可靠、延迟最低；用于拆包裹/预售触发与追踪注册 |
| 17track（推荐但可选） | Webhook 推送 + API 查询 | 能覆盖大量承运商的异常/签收状态变化；最适合自动通知（无需对接每家承运商） |
| 易仓（可选） | Webhook/回调（优先） | 易仓若能推送“物流状态变更”，可直接驱动通知；否则需要轮询（依赖定时任务能力） |

---

## 四、数据存储

| 存储 | 用途 |
|------|------|
| Redis | 幂等去重 key、短期缓存（如 tracking status、重试节流） |
| PostgreSQL | 权威数据：运单登记、通知发送记录、重试队列（Outbox） |

---

## 五、部署方式

- **独立模式**：`uvicorn products.notification.main:app --port 8001`
- **全家桶模式**：按项目统一入口注册路由（如存在网关/聚合进程）

---

## 六、已发现的“代码-文档差异”（需要在实现中对齐）

- `infrastructure/database` 已包含 `tracking_registrations` 与 `notification_records` 表，但当前 `services/tracking` 与 `products/notification` 主要依赖 Redis/内存映射，未充分使用 PostgreSQL 作为权威数据源。

---

## 七、易仓开放平台文档待补齐（[[YICANG_TBD]]）

为实现“Webhook-first”且可直接联调上线，需要从易仓开放平台文档补齐并固化到本模块：
- Webhook 鉴权/验签规则（签名算法、字段、时间戳/nonce、防重放、IP 白名单）（[[YICANG_TBD]]）
- 发货/运单生成回调的 payload 字段表 + 示例 JSON（[[YICANG_TBD]]）
