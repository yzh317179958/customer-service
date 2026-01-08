# 物流通知 - 架构说明

> **创建日期**：2025-12-23
> **最后更新**：2026-01-08

---

## 模块结构（产品层）

```
products/notification/
├── __init__.py              # 模块导出 ✅
├── main.py                  # 独立模式入口 ✅
├── config.py                # 配置管理 ✅
├── routes.py                # Webhook 路由 ✅
├── handlers/
│   ├── __init__.py          # 处理器导出 ✅
│   ├── shopify_handler.py   # Shopify 事件 ✅
│   ├── tracking_handler.py  # 17track 推送 ✅
│   ├── notification_sender.py # 通知发送 ✅
│   └── yicang_handler.py    # 易仓轮询处理（规划）
├── templates/               # 邮件模板 ✅
│   ├── split_package.html
│   ├── presale_shipped.html
│   ├── exception_alert.html
│   └── delivery_confirm.html
└── memory-bank/             # 文档 ✅
```

---

## 总体架构（事件驱动）

本模块采用"事件接入 → 事件归一化 → 通知规则 → 发送与记录"的形态：

1. **事件接入（Webhook / API / 轮询）**：Shopify 发货、17track 状态推送、易仓定时轮询
2. **归一化（Domain Event）**：将不同来源的 payload 转换为内部统一的"物流事件"语义
3. **规则判断**：拆包裹 / 预售 / 异常 / 签收
4. **发送与幂等**：同一运单同一事件只发一次，并落库可追踪

依赖方向严格遵循三层架构：
`products/notification → services/* → infrastructure/*`

---

## 数据流（已实现）

### Shopify 发货 → 运单注册（17track 可选）

```
Shopify 发货事件
    │
    ▼
POST /webhook/shopify
    │
    ▼
shopify_handler.handle_fulfillment_create()
    │
    ├─ 检测拆包裹 → send_split_package_notice()
    ├─ 检测预售商品 → send_presale_notice()
    │
    ▼
services/tracking.register_order_tracking()
    │
    ▼
17track API 注册运单
```

### 17track 推送 → 通知发送

```
17track 状态变更推送
    │
    ▼
POST /webhook/17track
    │
    ▼
tracking_handler.handle_tracking_update()
    │
    ├─ 签收状态 → send_delivery_confirm()
    ├─ 异常状态 → send_exception_alert()
    │
    ▼
services/email.send_email()
```

---

## 数据流（规划：易仓 ERP 售后配件 - 轮询模式）

> **重要发现**：易仓开放平台采用"主动拉取 API"模式，暂无公开的 Webhook 推送机制。
> 因此采用**定时轮询**方案。

### 轮询架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                    定时任务（每 5-10 分钟）                           │
│                    infrastructure/scheduler                          │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    services/yicang（服务层）                         │
│                                                                      │
│  1. 生成签名（MD5）                                                  │
│  2. 调用 getOrderList 获取最近更新的订单                             │
│  3. 返回订单列表                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    handlers/yicang_handler.py（产品层）              │
│                                                                      │
│  1. 按 shipping_method/warehouse_code 筛选售后订单                  │
│  2. 对比本地记录，识别状态变更                                       │
│  3. 触发对应通知（发货/签收/异常）                                   │
│  4. 更新本地状态记录（幂等去重）                                     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    notification_sender.py                            │
│                    发送邮件模板                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 详细流程

```
定时任务触发（每 5-10 分钟）
    │
    ▼
services/yicang.poll_order_updates()
    │
    ├─ 构建请求参数（app_key, timestamp, nonce_str, biz_content）
    ├─ 生成 MD5 签名
    ├─ 调用 getOrderList API（增量查询，按 modify_date 筛选）
    │
    ▼
返回订单列表
    │
    ▼
handlers/yicang_handler.process_order_updates()
    │
    ├─ 遍历订单列表
    │   │
    │   ├─ 检查 shipping_method / warehouse_code / mail_cargo_type
    │   │   └─ 是否匹配售后配件订单规则
    │   │
    │   ├─ 查询本地记录（tracking_registrations）
    │   │   └─ 是否已存在？状态是否变更？
    │   │
    │   ├─ 状态变更时：
    │   │   ├─ status: P→S（发货）→ 发送发货通知
    │   │   ├─ status: S→C（签收）→ 发送签收确认
    │   │   ├─ status: *→E（异常）→ 发送异常告警
    │   │   └─ 写入 notification_records（幂等 key: reference_no + status）
    │   │
    │   └─ 更新本地状态记录
    │
    ▼
services/email.send_email()
```

### 易仓轮询安全与幂等策略

**已明确（基于官方文档调研）**：

| 项目 | 策略 |
|------|------|
| **签名算法** | MD5：参数按 key 字典序排序 → 拼接 `key=value&` → 末尾追加 `app_secret` → MD5 大写 |
| **时间戳** | 毫秒级，有效期 **1 分钟** |
| **防重放** | `nonce_str` 随机字符串，每次请求唯一 |
| **幂等去重** | 以 `reference_no + status` 作为 `notification_id` 组成，防止重复发送 |
| **增量查询** | 按 `modify_date` 筛选，只拉取最近变更（建议 5-10 分钟窗口） |
| **重试策略** | 我方轮询失败时自动重试；下次轮询会重新拉取 |

**待业务确认**：

| 项目 | 说明 |
|------|------|
| **售后订单识别** | 需确认使用哪个字段识别：`shipping_method` / `warehouse_code` / `mail_cargo_type` |

---

## 文件说明（现状与差异）

### config.py

**用途:** 配置管理

**主要内容:**
- `NotificationConfig` - 配置类（enabled, email_from, timeout 阈值）
- `NotificationType` - 通知类型常量
- `OVERSEAS_CARRIERS` / `CHINA_CARRIERS` - 承运商分类
- `get_carrier_timeout()` - 获取超时阈值
- `is_presale_sku()` - 预售商品判断

---

### main.py

**用途:** 独立模式入口

**端点:**
- `GET /` - 服务状态
- `GET /api/health` - 健康检查
- `GET /api/config` - 配置信息

---

### routes.py

**用途:** Webhook 端点定义

**端点:**
- `POST /webhook/shopify` - Shopify 发货 Webhook
  - Headers: X-Shopify-Topic, X-Shopify-Hmac-SHA256, X-Shopify-Shop-Domain
- `POST /webhook/17track` - 17track 状态推送
  - Headers: X-17track-Signature
- `GET /webhook/health` - 健康检查

> 注：易仓采用轮询模式，无需 Webhook 端点。

---

### handlers/shopify_handler.py

**用途:** Shopify 发货事件处理

**主要函数:**
- `handle_fulfillment_create()` - 处理发货创建事件
- `handle_order_create()` - 处理订单创建事件
- `_register_tracking()` - 注册运单到 17track
- `_check_split_package()` - 检测是否拆包裹
- `_detect_presale_items()` - 检测预售商品
- `_get_site_code()` - 站点域名映射（fiidouk → uk）
- `_send_split_package_notification()` - 发送拆包裹通知
- `_send_presale_notification()` - 发送预售通知
- `_generate_tracking_url()` - 生成追踪链接

---

### handlers/tracking_handler.py

**用途:** 17track 状态推送处理

**主要函数:**
- `handle_tracking_update()` - 处理状态推送
- `_process_event()` - 处理单个事件
- `handle_delivered()` - 处理签收事件
- `handle_exception()` - 处理异常事件
- `_get_order_info()` - 获取订单信息
- `handle_status_change()` - 处理状态变更

---

### handlers/yicang_handler.py（规划）

**用途:** 易仓订单轮询处理

**规划函数:**
- `process_order_updates()` - 处理订单更新列表
- `_is_aftersales_order()` - 判断是否售后配件订单
- `_detect_status_change()` - 检测状态变更
- `_trigger_notification()` - 触发对应通知

---

### handlers/notification_sender.py

**用途:** 邮件通知发送

**主要函数:**
- `render_template()` - Jinja2 模板渲染
- `send_split_package_notice()` - 拆包裹通知
- `send_presale_notice()` - 预售发货通知
- `send_exception_alert()` - 异常警报
- `send_delivery_confirm()` - 签收确认
- `check_templates()` - 检查模板是否存在

---

### templates/

**用途:** 邮件 HTML 模板（Jinja2）

| 模板 | 用途 |
|------|------|
| split_package.html | 拆包裹通知 |
| presale_shipped.html | 预售发货通知 |
| exception_alert.html | 异常警报（支持多种类型） |
| delivery_confirm.html | 签收确认（含评价引导） |

---

## 生产化必须补齐（当前缺口）

- **幂等与去重的权威落库**：`infrastructure/database` 已有 `notification_records` / `tracking_registrations` 表，但当前通知链路主要依赖 Redis/内存映射，长链路（跨境时长）存在丢关联风险。
- **易仓轮询适配层**：需新增 `services/yicang`（服务层）与 `products/notification/handlers/yicang_handler.py`（产品层）。
- **定时任务调度**：依赖 `infrastructure/scheduler` 组件支持可靠的定时轮询。

---

## 跨模块依赖

```
products/notification
    ├── services/tracking      # 17track API 封装
    ├── services/shopify       # 订单数据查询
    ├── services/email         # 邮件发送
    └── services/yicang        # 易仓 API 封装（规划）
```

---

## 异常类型

| 类型 | 说明 |
|------|------|
| lost | 包裹丢失 |
| damaged | 包裹损坏 |
| address_issue | 地址问题 |
| customs_issue | 海关问题 |
| no_one_home | 无人签收 |
| refused | 拒收 |
| returned | 退回发件人 |
