# 物流通知（Notification）- 产品需求文档

> **产品名称**：Fiido 物流通知服务
> **版本**：v1.2
> **创建日期**：2025-12-21
> **更新日期**：2026-01-08
> **状态**：已实现基础版，待生产化补齐

---

## 一、产品概述

物流通知服务是 Fiido 智能服务平台的独立产品模块，用于把"发货后关键物流事件"自动通知到客户邮箱，并为客服提供可追踪的通知记录。

本模块面向两类业务来源：
1. **Shopify 独立站订单**：来自 Shopify 的发货（fulfillment）信息。
2. **易仓 ERP 售后配件订单**：来自易仓下单的售后配件（可按店铺/来源识别），需要在物流更新时自动通知客户（易仓可提供接口，但不保证有现成能力）。

### 1.1 目标用户
- 终端消费者：获取物流状态更新和签收确认
- 坐席：处理物流异常
- 运营人员：监控物流服务质量

### 1.2 核心价值
- 客户：主动获知"拆包裹 / 预售发货 / 异常 / 签收"等关键节点，减少不确定性
- 客服：减少重复解释与催件咨询，遇到异常能更早介入
- 企业：通知可审计、可追踪、可配置，支持多店铺与售后场景扩展

---

## 二、核心功能

### 2.1 拆包裹发货通知
**触发条件**：一个订单拆分为多个包裹发货
**通知内容**：告知用户订单将分批到达
**触发方式**：Shopify `fulfillments/create` Webhook（或等价发货事件）

### 2.2 预售商品发货通知
**触发条件**：预售商品开始发货
**通知内容**：告知用户预售商品已发出
**触发方式**：Shopify `fulfillments/create` + 预售识别规则（默认 SKU 前缀，可后续改为标签/元字段规则）

### 2.3 物流异常告警
**触发条件**：追踪服务推送/检测到异常状态（如 Alert、Undelivered、退回、派送失败等）
**通知内容**：告知用户物流出现问题，提供解决方案
**触发方式**：优先 Webhook（17track 或易仓），不具备推送时降级为定时轮询（后续迭代）

### 2.4 签收确认通知
**触发条件**：追踪服务推送/检测到 Delivered/签收状态
**通知内容**：确认签收，引导评价
**触发方式**：优先 Webhook（17track 或易仓），不具备推送时降级为定时轮询（后续迭代）

---

## 三、Webhook / 接口端点（产品层）

| 端点 | 来源 | 用途 |
|------|------|------|
| `POST /webhook/shopify` | Shopify | 接收发货事件 |
| `POST /webhook/17track` | 17track（可选） | 接收状态变更 |
| `POST /webhook/yicang` | 易仓（规划） | 接收售后配件订单/物流更新 |

---

## 四、依赖服务

| 服务 | 用途 |
|------|------|
| services/tracking | 追踪服务（默认 17track 实现，允许扩展/替换） |
| services/shopify | 订单数据查询 |
| services/email | 邮件发送 |
| infrastructure/database | 通知记录与映射持久化（推荐作为权威数据源） |

---

## 五、邮件模板

| 模板 | 用途 |
|------|------|
| split_package.html | 拆包裹通知 |
| presale_shipped.html | 预售发货通知 |
| exception_alert.html | 异常告警 |
| delivery_confirm.html | 签收确认 |

---

## 六、成功标准（最小可验收）

- Shopify 订单：能从 `fulfillments/create` 触发拆包裹/预售通知；能对运单建立"运单→订单→客户邮箱"关联
- 异常/签收：在开启追踪集成后，能对同一运单状态变化做到幂等不重复发送
- 售后配件：能识别"易仓售后配件订单"并在物流状态变化时发送邮件（接口能力允许的情况下）
- 可追踪：每封通知具备发送记录（成功/失败/错误原因），便于客服排查

---

## 七、易仓对接技术规范

> **调研日期**：2026-01-08
> **数据来源**：易仓开放平台公开文档、第三方集成指南、官方 PHP SDK
> **重要发现**：易仓开放平台采用"主动拉取 API"模式，暂无公开的 Webhook 推送机制

### 7.1 对接模式选型

| 模式 | 易仓支持情况 | 我方实现方案 |
|------|-------------|-------------|
| Webhook 推送 | ❌ 未公开支持 | 不可用 |
| 主动拉取 API | ✅ 支持 | **采用轮询方案** |

**结论**：需采用定时轮询易仓 API 获取订单/物流状态更新，而非 Webhook 回调。

### 7.2 API 鉴权与签名规则

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

**签名算法**（MD5）：

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

**安全约束**：
- 时间戳有效期：**1 分钟**，超时请求无效
- nonce_str：每次请求必须唯一，防止重放攻击
- 签名顺序：必须与接口文档一致，否则报签名错误

### 7.3 订单/物流相关 API

| 接口方法 | 用途 | 关键返回字段 |
|----------|------|-------------|
| `getOrder` | 查询订单详情 | 见下方 JSON 示例 |
| `getOrderList` | 获取订单列表 | 支持分页、时间范围筛选 |
| `getOrderStatus` | 获取订单状态 | status, exception_info |
| `getTrackingNumberChangeRecord` | 获取运单号变更记录 | 新旧运单号、变更时间 |
| `getShippingMethod` | 获取配送方式 | 用于识别订单来源 |

**getOrder 返回示例**（来源：公开集成文档）：

```json
{
  "ask": "Success",
  "message": "Success",
  "reference_no": "QGADCX18041700000003",
  "data": {
    "shipping_method": "PK0068",
    "country_code": "AD",
    "reference_no": "",
    "shipper_hawbcode": "QGADCX18041700000003",
    "shipping_method_no": "QGADCX18041700000003",
    "channel_hawbcode": "34161184947327",
    "system_hawbcode": null,
    "clearance_system_hawbcode": "AG96445156",
    "order_weight": "1.000",
    "order_pieces": "1",
    "buyer_id": "",
    "modify_date": "2018-04-17 17:39:08",
    "mail_cargo_type": "1",
    "insurance_value": null,
    "is_return": "N",
    "status": "C",
    "Consignee": {
      "consignee_countrycode": "AD",
      "consignee_company": "",
      "consignee_province": "",
      "consignee_name": "",
      "consignee_city": "",
      "consignee_telephone": "",
      "consignee_mobile": "",
      "consignee_postcode": null,
      "consignee_email": "",
      "consignee_street": "dfdfdfdf"
    }
  }
}
```

**关键字段映射**：

| 易仓字段 | 含义 | 我方用途 |
|----------|------|----------|
| `reference_no` | 客户参考号 | 订单关联 |
| `shipper_hawbcode` | 发货方运单号 | 运单追踪 |
| `channel_hawbcode` | 渠道运单号 | 运单追踪（备选） |
| `shipping_method` | 配送方式代码 | **可用于识别售后订单** |
| `mail_cargo_type` | 货物类型 | **可用于识别配件订单** |
| `status` | 订单状态码 | 状态变更检测 |
| `is_return` | 是否退货 | 识别退货订单 |
| `Consignee.consignee_email` | 收件人邮箱 | 通知发送 |
| `Consignee.consignee_name` | 收件人姓名 | 邮件称呼 |
| `modify_date` | 修改时间 | 增量查询 |

**订单状态码**（推测，需确认）：

| 状态码 | 含义 |
|--------|------|
| `P` | Pending（待处理） |
| `S` | Shipped（已发货） |
| `C` | Completed（已完成/签收） |
| `E` | Exception（异常） |

### 7.4 售后配件订单识别方案

根据调研，易仓 API **没有专门的 `order_type` 字段**来直接标识"售后配件订单"。需要通过以下方式之一识别：

| 识别方式 | 字段 | 说明 | 可行性 |
|----------|------|------|--------|
| **配送方式** | `shipping_method` | 售后配件使用特定配送方式代码 | ✅ 推荐 |
| **货物类型** | `mail_cargo_type` | 配件使用特定货物类型编码 | ✅ 推荐 |
| **仓库代码** | `warehouse_code` | 售后配件从特定仓库发货 | ✅ 可行 |
| **参考号前缀** | `reference_no` | 售后订单有统一的单号前缀 | ⚠️ 需业务配置 |
| **退货标识** | `is_return` | 退货相关订单 | ⚠️ 仅限退货场景 |

**业务方需确认**：
1. 售后配件订单在易仓中使用哪个 `shipping_method` 代码？
2. 或者，售后配件订单从哪个 `warehouse_code` 仓库发货？
3. 或者，售后订单的 `reference_no` 是否有统一前缀？

> 可调用 `getShippingMethod` 接口获取所有配送方式列表，从中识别售后专用的方式。

### 7.5 轮询方案设计

由于易仓不支持 Webhook，需采用定时轮询：

```
┌─────────────────────────────────────────────────────────┐
│                    定时任务（每 5-10 分钟）              │
│                                                         │
│  1. 调用 getOrderList 获取最近更新的订单                │
│  2. 按 shipping_method/warehouse_code 筛选售后订单     │
│  3. 对比本地记录，识别状态变更                          │
│  4. 触发对应通知（发货/签收/异常）                      │
│  5. 更新本地状态记录                                    │
└─────────────────────────────────────────────────────────┘
```

**轮询策略**：
- 频率：5-10 分钟（避免触发限流）
- 增量查询：按 `modify_date` 筛选，只拉取最近变更
- 幂等保障：以 `reference_no + status` 做去重

### 7.6 待确认事项分析

| 事项 | 状态 | 是否阻塞开发 | 说明 |
|------|------|-------------|------|
| 订单字段 JSON Schema | ✅ 已获取 | 否 | 上方已有完整示例 |
| API 限流策略（QPS） | ⏸️ 可推迟 | 否 | 初期轮询频率低，不会触发 |
| **售后订单识别字段** | ⚠️ 需业务确认 | **是** | 需确认用哪个字段识别 |
| 沙箱环境地址 | ⏸️ 可绕过 | 否 | 直接用生产环境小批量测试 |

**官方资源**：
- 开放平台：https://open.eccang.com/
- 文档中心：https://open.eccang.com/#/documentCenter
- Wiki 文档：https://ecwiki.eccang.com/（需授权）
- 应用管理：https://home.eccang.com/#/company/develop/app-manager
- 售后咨询：400-8199-388

---

## 八、跨模块引用

本模块是 **17track 物流追踪集成** 跨模块功能的一部分。

完整文档：`docs/features/17track-integration/`
