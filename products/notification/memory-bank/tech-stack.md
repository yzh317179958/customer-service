# 物流通知 - 技术栈说明

> **创建日期**：2025-12-23
> **最后更新**：2026-01-08

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
| 追踪服务（可选） | `services/tracking` | 当前实现为 17track 聚合追踪；负责"运单注册 + 状态查询 + Webhook 解析" |
| 易仓服务（规划） | `services/yicang` | 售后配件订单轮询与状态变更检测 |

---

## 三、外部集成选型结论（最优默认）

| 服务 | 方式 | 说明 |
|------|------|------|
| Shopify | Webhook 推送 | 发货事件最可靠、延迟最低；用于拆包裹/预售触发与追踪注册 |
| 17track（推荐但可选） | Webhook 推送 + API 查询 | 能覆盖大量承运商的异常/签收状态变化；最适合自动通知（无需对接每家承运商） |
| **易仓** | **定时轮询 API** | 易仓开放平台不支持 Webhook 推送，采用 5-10 分钟轮询方案 |

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

## 六、已发现的"代码-文档差异"（需要在实现中对齐）

- `infrastructure/database` 已包含 `tracking_registrations` 与 `notification_records` 表，但当前 `services/tracking` 与 `products/notification` 主要依赖 Redis/内存映射，未充分使用 PostgreSQL 作为权威数据源。

---

## 七、易仓开放平台技术规范

> **调研日期**：2026-01-08
> **数据来源**：易仓开放平台公开文档、第三方集成指南、官方 PHP SDK

### 7.1 API 鉴权与签名规则

**请求地址**：`http://openapi-web.eccang.com/openApi/api/unity`（固定）

**请求参数**：

| 参数 | 必填 | 说明 |
|------|------|------|
| app_key | 是 | 应用 KEY，从开放平台获取 |
| app_secret | 是 | 应用密钥（仅用于签名计算，不传输） |
| service_id | 是 | 服务 ID，在应用管理→授权状态中查看 |
| interface_method | 是 | 接口方法名（如 `getOrder`） |
| biz_content | 是 | 业务参数 JSON 字符串 |
| timestamp | 是 | 时间戳（毫秒），**有效期 1 分钟** |
| nonce_str | 是 | 随机字符串，防重放 |
| sign | 是 | 签名值（自动计算） |
| sign_type | 否 | 签名类型，默认 `MD5` |
| charset | 否 | 字符集，默认 `UTF-8` |
| version | 否 | 版本号，默认 `1.0.0` |

### 7.2 签名算法（MD5）

```python
import hashlib
import json

def generate_sign(params: dict, app_secret: str) -> str:
    """
    易仓 API 签名算法
    1. 将参数按 key 字典序排序
    2. 拼接为 key1=value1&key2=value2... 格式
    3. 末尾追加 app_secret
    4. MD5 加密后转大写
    """
    sorted_params = sorted(
        [(k, v) for k, v in params.items() if k != 'sign' and v],
        key=lambda x: x[0]
    )
    sign_str = '&'.join(f'{k}={v}' for k, v in sorted_params)
    sign_str += app_secret
    return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()
```

### 7.3 安全约束

| 约束 | 说明 |
|------|------|
| 时间戳有效期 | **1 分钟**，超时请求无效 |
| nonce_str | 每次请求必须唯一，防止重放攻击 |
| 签名顺序 | 必须与接口文档一致，否则报签名错误 |

### 7.4 订单/物流相关 API

| 接口方法 | 用途 | 关键返回字段 |
|----------|------|-------------|
| `getOrder` | 查询订单详情 | reference_no, status, Consignee |
| `getOrderList` | 获取订单列表 | 支持分页、时间范围筛选 |
| `getOrderStatus` | 获取订单状态 | status, exception_info |
| `getTrackingNumberChangeRecord` | 获取运单号变更记录 | 新旧运单号、变更时间 |
| `getShippingMethod` | 获取配送方式 | 用于识别订单来源 |

### 7.5 关键字段映射

| 易仓字段 | 含义 | 我方用途 |
|----------|------|----------|
| `reference_no` | 客户参考号 | 订单关联 |
| `shipper_hawbcode` | 发货方运单号 | 运单追踪 |
| `channel_hawbcode` | 渠道运单号 | 运单追踪（备选） |
| `shipping_method` | 配送方式代码 | **可用于识别售后订单** |
| `mail_cargo_type` | 货物类型 | **可用于识别配件订单** |
| `warehouse_code` | 仓库代码 | **可用于识别售后订单** |
| `status` | 订单状态码 | 状态变更检测 |
| `is_return` | 是否退货 | 识别退货订单 |
| `Consignee.consignee_email` | 收件人邮箱 | 通知发送 |
| `Consignee.consignee_name` | 收件人姓名 | 邮件称呼 |
| `modify_date` | 修改时间 | 增量查询 |

### 7.6 订单状态码（推测）

| 状态码 | 含义 |
|--------|------|
| `P` | Pending（待处理） |
| `S` | Shipped（已发货） |
| `C` | Completed（已完成/签收） |
| `E` | Exception（异常） |

### 7.7 轮询策略

| 策略 | 说明 |
|------|------|
| 频率 | 5-10 分钟（避免触发限流） |
| 增量查询 | 按 `modify_date` 筛选，只拉取最近变更 |
| 幂等保障 | 以 `reference_no + status` 做去重 |

### 7.8 官方资源

| 资源 | 地址 |
|------|------|
| 开放平台 | https://open.eccang.com/ |
| 文档中心 | https://open.eccang.com/#/documentCenter |
| Wiki 文档 | https://ecwiki.eccang.com/（需授权） |
| 应用管理 | https://home.eccang.com/#/company/develop/app-manager |
| 售后咨询 | 400-8199-388 |

---

## 八、待业务确认事项

| 事项 | 说明 | 阻塞性 |
|------|------|--------|
| 售后订单识别字段 | 需确认用 `shipping_method` / `warehouse_code` / `mail_cargo_type` 哪个字段 | **是** |
| API 限流策略（QPS） | 初期轮询频率低，可推迟确认 | 否 |
| 沙箱环境地址 | 可直接用生产环境小批量测试 | 否 |
