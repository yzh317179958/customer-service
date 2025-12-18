# L2-1: Shopify订单集成功能需求

> **文档编号**: L2-1
> **文档版本**: v1.0
> **优先级**: P1（增强层 - 重要）
> **状态**: ❌ 待开发
> **创建时间**: 2025-01-27
> **最后更新**: 2025-01-27

---

## 📑 文档导航

- **上级文档**: [ENTERPRISE_EBIKE_SUPPORT_TASKS.md](./ENTERPRISE_EBIKE_SUPPORT_TASKS.md)
- **同级文档**:
  - 当前: L2-1 Shopify订单集成
  - 下一篇: L2-2-Part1 客户基础信息与行为
- **依赖关系**: 依赖 v3.2.0 客户画像功能和会话管理

---

## 🎯 功能概述

### 涵盖模块

本文档包含 Shopify 电商平台集成的全部功能模块（不拆分）：

| 模块编号 | 模块名称 | 核心功能 |
|---------|---------|---------|
| **模块1** | Shopify API连接配置 | OAuth认证、Webhook配置、连接测试 |
| **模块2** | 订单实时查询 | 根据订单号/邮箱查询、查询缓存 |
| **模块3** | 订单状态追踪 | 物流跟踪、状态变更通知 |
| **模块4** | 订单操作集成 | 退款申请、订单修改、备注添加 |

### 业务价值

**当前痛点**（v3.3.0）：
- ✅ 已有客户画像基础功能（`user_profile`）
- ❌ 缺少订单数据集成：坐席无法直接查看客户订单
- ❌ 缺少物流追踪：客户询问物流需要手动去Shopify后台查询
- ❌ 缺少订单操作：退款、修改订单需要离开客服系统操作
- ❌ VIP识别不准确：无法基于订单金额自动识别VIP

**实现后收益**：
- 📈 坐席响应效率提升 **60%**（不需要切换系统查询订单）
- 📈 物流咨询处理速度提升 **70%**（实时显示物流状态）
- 📈 退款处理效率提升 **50%**（直接在客服系统发起）
- 📊 VIP客户识别准确率提升至 **95%**（基于真实订单数据）
- 📊 客户满意度预计提升 **40%**

**Fiido 电动自行车场景示例**：
> 客户："我的订单什么时候发货？订单号 #FD20250127001"
>
> 坐席（不集成前）：
> 1. 让我帮您查询...（切换到Shopify后台）
> 2. 登录Shopify，搜索订单号
> 3. 查看订单状态，复制物流信息
> 4. 回到客服系统，粘贴回复
> **总耗时**: 约 3 分钟
>
> 坐席（集成后）：
> 1. 系统自动显示该客户的所有订单
> 2. 点击订单号，查看详情（包含物流追踪）
> 3. 一键复制物流单号，或直接发送物流链接
> **总耗时**: 约 30 秒

---

## 📋 模块1: Shopify API连接配置

### 1.1 功能概述

为系统管理员提供 Shopify API 连接配置界面，实现 OAuth 认证和 Webhook 自动配置。

**参考对标**：
- 有赞客服：支持有赞店铺一键授权
- 拼多多开放平台：提供授权配置向导

### 1.2 功能需求

#### 1.2.1 Shopify OAuth 认证

**F1-1: OAuth 授权流程**

Shopify 使用 OAuth 2.0 授权，需要实现标准授权流程：

**授权步骤**：
1. 管理员在系统中输入 Shopify 店铺域名（如：`fiido-ebike.myshopify.com`）
2. 系统生成授权链接，引导管理员跳转到 Shopify 授权页面
3. 管理员在 Shopify 确认授权权限
4. Shopify 回调系统，返回 `access_token`
5. 系统保存 `access_token`，完成授权

**所需权限（Scopes）**：
```
read_orders          # 读取订单信息
write_orders         # 修改订单（添加备注、取消订单）
read_customers       # 读取客户信息
read_fulfillments    # 读取物流信息
write_fulfillments   # 更新物流信息
```

**F1-2: 配置存储**

需要存储的配置信息：

| 字段 | 说明 | 示例 |
|-----|------|------|
| `shop_domain` | 店铺域名 | `fiido-ebike.myshopify.com` |
| `access_token` | 访问令牌 | `shpat_xxx...` |
| `api_version` | API版本 | `2024-01` |
| `created_at` | 配置创建时间 | `2025-01-27T10:00:00Z` |
| `expires_at` | Token过期时间（如有） | `null`（Shopify Token永久有效） |
| `status` | 连接状态 | `active` / `inactive` / `error` |

**存储方式**：
- 使用 Redis 存储（`shopify:config`）
- 使用环境变量备份（`.env` 文件）
- **安全要求**：`access_token` 必须加密存储

#### 1.2.2 连接测试

**F1-3: 连接健康检查**

提供连接测试功能，验证 API 配置是否正确：

**测试内容**：
1. API 连接性测试：调用 `/admin/api/2024-01/shop.json`
2. 权限验证：检查所需的 Scopes 是否全部授权
3. 速率限制检查：获取当前 API 调用配额

**测试结果显示**：
```
✅ 连接成功
✅ 店铺信息: Fiido E-bike Official Store
✅ 权限验证: 5/5 通过
✅ API配额: 38/40 (剩余调用次数)
```

**失败情况提示**：
```
❌ 连接失败
原因: 访问令牌无效或已过期
建议: 请重新授权 Shopify 应用
```

#### 1.2.3 Webhook 配置

**F1-4: 自动配置 Webhook**

为了实时接收订单状态变更，需要配置 Webhook：

**需要订阅的事件**：

| 事件名称 | 触发时机 | 用途 |
|---------|---------|------|
| `orders/create` | 新订单创建 | 更新客户订单历史 |
| `orders/updated` | 订单状态变更 | 同步订单状态到客服系统 |
| `orders/cancelled` | 订单取消 | 通知坐席，及时跟进 |
| `fulfillments/create` | 发货 | 更新物流信息 |
| `fulfillments/update` | 物流状态更新 | 同步物流追踪 |
| `refunds/create` | 退款完成 | 更新退款状态 |

**Webhook 配置信息**：
```json
{
  "webhook": {
    "topic": "orders/updated",
    "address": "https://your-domain.com/api/webhooks/shopify/orders",
    "format": "json"
  }
}
```

**F1-5: Webhook 验证与安全**

接收 Webhook 时必须验证签名，防止伪造请求：

**验证步骤**：
1. 从请求头获取 `X-Shopify-Hmac-SHA256`
2. 使用 Shopify API Secret 计算请求体的 HMAC-SHA256
3. 对比计算结果与请求头中的签名
4. 签名一致才处理请求

### 1.3 数据模型

**Shopify 配置模型**：

```typescript
interface ShopifyConfig {
  shop_domain: string              // 店铺域名
  access_token: string             // 访问令牌（加密存储）
  api_version: string              // API版本
  scopes: string[]                 // 已授权的权限
  created_at: Date                 // 配置创建时间
  updated_at: Date                 // 最后更新时间
  status: 'active' | 'inactive' | 'error'  // 连接状态
  last_health_check: Date          // 最后一次健康检查时间
  health_check_result: {
    success: boolean
    api_quota_remaining: number
    error_message?: string
  }
}
```

**Webhook 配置模型**：

```typescript
interface WebhookConfig {
  webhook_id: string               // Shopify Webhook ID
  topic: string                    // 事件主题
  address: string                  // 回调地址
  status: 'active' | 'inactive'    // 状态
  created_at: Date
}
```

### 1.4 后端API设计

**配置管理API**：

```
POST   /api/admin/shopify/connect           # 发起授权（生成授权URL）
GET    /api/admin/shopify/callback          # 授权回调（接收access_token）
GET    /api/admin/shopify/config            # 获取当前配置
PUT    /api/admin/shopify/config            # 更新配置
DELETE /api/admin/shopify/disconnect        # 断开连接
POST   /api/admin/shopify/test              # 连接测试
```

**Webhook管理API**：

```
POST   /api/admin/shopify/webhooks          # 创建Webhook
GET    /api/admin/shopify/webhooks          # 获取Webhook列表
DELETE /api/admin/shopify/webhooks/:id      # 删除Webhook
POST   /api/webhooks/shopify/:topic         # 接收Webhook（公开，需验证签名）
```

### 1.5 UI设计

**配置界面布局**：

```
┌─────────────────────────────────────────────┐
│ Shopify 集成配置                             │
├─────────────────────────────────────────────┤
│                                              │
│ 连接状态: ✅ 已连接                          │
│ 店铺名称: Fiido E-bike Official Store        │
│ 店铺域名: fiido-ebike.myshopify.com         │
│ API版本:  2024-01                           │
│                                              │
│ ┌─────────────────────────────────────────┐ │
│ │ 权限状态                                  │ │
│ │ ✅ read_orders        读取订单            │ │
│ │ ✅ write_orders       修改订单            │ │
│ │ ✅ read_customers     读取客户            │ │
│ │ ✅ read_fulfillments  读取物流            │ │
│ │ ✅ write_fulfillments 更新物流            │ │
│ └─────────────────────────────────────────┘ │
│                                              │
│ ┌─────────────────────────────────────────┐ │
│ │ Webhook 状态                              │ │
│ │ ✅ orders/create      已配置              │ │
│ │ ✅ orders/updated     已配置              │ │
│ │ ✅ fulfillments/create 已配置             │ │
│ │ ✅ refunds/create     已配置              │ │
│ └─────────────────────────────────────────┘ │
│                                              │
│ 最后检查: 2025-01-27 10:30:00               │
│ API配额:  38/40 (可用)                       │
│                                              │
│ [测试连接] [重新授权] [断开连接]             │
└─────────────────────────────────────────────┘
```

**初次配置向导**（未连接时）：

```
┌─────────────────────────────────────────────┐
│ 连接 Shopify 店铺                            │
├─────────────────────────────────────────────┤
│                                              │
│ 步骤1: 输入店铺域名                          │
│ ┌─────────────────────────────────────────┐ │
│ │ 店铺域名: [__________________.myshopify.com] │ │
│ └─────────────────────────────────────────┘ │
│                                              │
│ 步骤2: 授权应用                              │
│ 点击下方按钮，跳转到Shopify授权页面          │
│                                              │
│ [前往授权]                                   │
│                                              │
│ 💡 提示：授权后将自动返回此页面              │
└─────────────────────────────────────────────┘
```

### 1.6 验收标准

**功能验收**：
- [ ] 可输入店铺域名，生成授权链接
- [ ] 授权后正确接收 `access_token`
- [ ] 配置信息加密存储到 Redis
- [ ] 连接测试功能正常（显示店铺信息、权限、配额）
- [ ] 自动创建 6 个必需的 Webhook
- [ ] Webhook 签名验证正确
- [ ] 管理员可以重新授权
- [ ] 管理员可以断开连接

**安全验收**：
- [ ] `access_token` 加密存储（不以明文形式保存）
- [ ] Webhook 签名验证通过才处理请求
- [ ] 配置管理API需要管理员权限（`require_admin()`）
- [ ] 错误信息不泄露敏感数据

**性能验收**：
- [ ] 连接测试响应时间 < 2秒
- [ ] Webhook 接收延迟 < 500ms
- [ ] API调用遵守 Shopify 速率限制（2次/秒）

---

## 📋 模块2: 订单实时查询

### 2.1 功能概述

在坐席工作台和对话窗口中，实时查询和显示客户的订单信息。

**参考对标**：
- 拼多多客服：右侧显示客户订单列表
- 京东客服：支持订单号快速搜索

### 2.2 功能需求

#### 2.2.1 订单查询方式

**F2-1: 按客户邮箱查询**

当坐席接入会话时，自动根据客户邮箱查询订单：

**查询逻辑**：
1. 从 `user_profile` 获取客户邮箱
2. 调用 Shopify API: `GET /admin/api/2024-01/orders.json?email={email}&limit=10`
3. 返回该客户的最近 10 个订单

**F2-2: 按订单号查询**

支持坐席手动输入订单号查询：

**输入支持**：
- 完整订单号：`#FD20250127001` 或 `FD20250127001`
- Shopify 订单ID：`5123456789012`
- 模糊匹配：输入部分订单号，返回匹配列表

**F2-3: 订单号自动识别**

当客户在对话中提到订单号时，系统自动识别并提供快捷查询：

**识别规则**：
- 正则匹配：`#?[A-Z]{2}\d{11}` 或 `#?\d{10,}`
- 识别后在消息旁显示"查看订单"按钮
- 点击按钮直接打开订单详情

**示例场景**：
```
客户: 我的订单 #FD20250127001 什么时候发货？
系统: [自动识别到订单号，显示快捷按钮]
       📦 查看订单 #FD20250127001
坐席: [点击按钮，订单详情面板展开]
```

#### 2.2.2 订单信息显示

**F2-4: 订单列表展示**

显示客户的订单列表，包含关键信息：

| 字段 | 说明 | 示例 |
|-----|------|------|
| 订单号 | Shopify Order Name | `#FD20250127001` |
| 订单状态 | 订单状态 | `已支付` / `待发货` / `已发货` / `已完成` |
| 订单金额 | 总金额 | `$1,299.00` |
| 下单时间 | 创建时间 | `2025-01-27 10:30` |
| 商品数量 | 商品SKU数量 | `2件商品` |
| 缩略图 | 主商品图片 | 🖼️ |

**排序规则**：
- 默认按下单时间倒序（最新订单在前）
- 支持按金额排序
- 支持按状态筛选

**F2-5: 订单详情展示**

点击订单后，展开详细信息：

**基础信息**：
```
订单号: #FD20250127001
下单时间: 2025-01-27 10:30:15
订单状态: 已发货
支付状态: 已支付
支付方式: PayPal
```

**商品列表**：
```
┌─────────────────────────────────────────┐
│ [图片] Fiido D11 电动自行车 - 黑色       │
│        SKU: FD-D11-BLK                   │
│        数量: 1  单价: $1,099.00          │
├─────────────────────────────────────────┤
│ [图片] 充电器套装                        │
│        SKU: FD-CHARGER-SET               │
│        数量: 1  单价: $49.00             │
└─────────────────────────────────────────┘

小计:   $1,148.00
运费:      $30.00
折扣:     -$10.00
税费:      $91.84
总计:   $1,259.84
```

**收货地址**：
```
收货人: John Doe
地址: 123 Main St, Apt 4B
     New York, NY 10001
     United States
电话: +1 234-567-8900
```

**物流信息**（如已发货）：
```
承运商: UPS
运单号: 1Z999AA10123456784
状态:   运输中
预计送达: 2025-01-30
[查看物流详情]
```

#### 2.2.3 查询缓存

**F2-6: 智能缓存机制**

为了减少 Shopify API 调用，实现缓存策略：

**缓存规则**：
- 订单列表缓存：5 分钟
- 订单详情缓存：10 分钟
- 物流信息缓存：30 分钟
- 缓存存储：Redis（`shopify:order:{order_id}`）

**缓存刷新**：
- 手动刷新：坐席点击"刷新"按钮
- 自动刷新：收到 Webhook 后清除相关缓存
- TTL过期：自动失效

**缓存优化**：
- 预加载：坐席接入会话时，后台预加载订单列表
- 批量查询：一次查询多个订单（最多50个）
- 增量更新：只更新变化的订单

### 2.3 数据模型

**订单摘要模型**（列表显示）：

```typescript
interface OrderSummary {
  order_id: string                 // Shopify Order ID
  order_number: string             // 订单号（如: #FD20250127001）
  created_at: Date                 // 下单时间
  financial_status: string         // 支付状态: pending/paid/refunded
  fulfillment_status: string       // 发货状态: unfulfilled/partial/fulfilled
  total_price: number              // 总金额
  currency: string                 // 货币: USD/EUR/CNY
  items_count: number              // 商品数量
  customer_email: string           // 客户邮箱
  thumbnail_url: string            // 商品缩略图
}
```

**订单详情模型**：

```typescript
interface OrderDetail extends OrderSummary {
  // 商品列表
  line_items: Array<{
    product_id: string
    variant_id: string
    title: string                  // 商品名称
    variant_title: string          // 规格（如: 黑色 / M码）
    sku: string
    quantity: number
    price: number
    image_url: string
  }>

  // 价格明细
  subtotal_price: number           // 小计
  total_shipping: number           // 运费
  total_discounts: number          // 折扣
  total_tax: number                // 税费

  // 收货地址
  shipping_address: {
    name: string
    address1: string
    address2: string
    city: string
    province: string
    zip: string
    country: string
    phone: string
  }

  // 物流信息
  fulfillments: Array<{
    tracking_company: string       // 承运商
    tracking_number: string        // 运单号
    tracking_url: string           // 跟踪链接
    status: string                 // 状态: pending/in_transit/delivered
    estimated_delivery: Date       // 预计送达
  }>

  // 退款信息
  refunds: Array<{
    refund_id: string
    created_at: Date
    amount: number
    reason: string
  }>

  // 备注
  note: string                     // 订单备注
  tags: string[]                   // 订单标签
}
```

### 2.4 后端API设计

**订单查询API**：

```
GET  /api/shopify/orders?email={email}              # 按邮箱查询
GET  /api/shopify/orders/{order_id}                  # 获取订单详情
GET  /api/shopify/orders/search?q={order_number}    # 按订单号搜索
POST /api/shopify/orders/batch                       # 批量查询（传订单ID数组）
POST /api/shopify/orders/{order_id}/refresh          # 强制刷新缓存
```

**请求示例**：
```bash
# 查询客户订单
curl "http://localhost:8000/api/shopify/orders?email=john@example.com"

# 获取订单详情
curl "http://localhost:8000/api/shopify/orders/5123456789012"

# 搜索订单号
curl "http://localhost:8000/api/shopify/orders/search?q=FD20250127001"
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "orders": [
      {
        "order_id": "5123456789012",
        "order_number": "#FD20250127001",
        "created_at": "2025-01-27T10:30:15Z",
        "financial_status": "paid",
        "fulfillment_status": "fulfilled",
        "total_price": 1259.84,
        "currency": "USD",
        "items_count": 2,
        "thumbnail_url": "https://cdn.shopify.com/...",
        "customer_email": "john@example.com"
      }
    ],
    "total_count": 1,
    "cached": false
  }
}
```

### 2.5 UI设计

**坐席工作台右侧面板**：

```
┌─────────────────────────────────────┐
│ 客户订单 (3)          [刷新]         │
├─────────────────────────────────────┤
│                                      │
│ ┌─────────────────────────────────┐ │
│ │ 🖼️ #FD20250127001               │ │
│ │    已发货 | $1,259.84            │ │
│ │    2025-01-27 | 2件商品          │ │
│ │    [查看详情]                    │ │
│ └─────────────────────────────────┘ │
│                                      │
│ ┌─────────────────────────────────┐ │
│ │ 🖼️ #FD20250120003               │ │
│ │    已完成 | $599.00              │ │
│ │    2025-01-20 | 1件商品          │ │
│ │    [查看详情]                    │ │
│ └─────────────────────────────────┘ │
│                                      │
│ ┌─────────────────────────────────┐ │
│ │ 🖼️ #FD20250110007               │ │
│ │    已退款 | $1,099.00            │ │
│ │    2025-01-10 | 1件商品          │ │
│ │    [查看详情]                    │ │
│ └─────────────────────────────────┘ │
│                                      │
│ [查看更多订单]                       │
└─────────────────────────────────────┘
```

**订单详情弹窗**：

```
┌───────────────────────────────────────────┐
│ 订单详情 - #FD20250127001         [关闭]  │
├───────────────────────────────────────────┤
│                                            │
│ 订单状态: ✅ 已发货                        │
│ 下单时间: 2025-01-27 10:30:15             │
│ 支付方式: PayPal                           │
│                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                            │
│ 商品列表:                                  │
│ ┌────────────────────────────────────┐   │
│ │ [图] Fiido D11 电动自行车 - 黑色    │   │
│ │      SKU: FD-D11-BLK                │   │
│ │      ×1    $1,099.00                │   │
│ └────────────────────────────────────┘   │
│ ┌────────────────────────────────────┐   │
│ │ [图] 充电器套装                     │   │
│ │      SKU: FD-CHARGER-SET            │   │
│ │      ×1    $49.00                   │   │
│ └────────────────────────────────────┘   │
│                                            │
│ 小计:   $1,148.00                         │
│ 运费:      $30.00                         │
│ 折扣:     -$10.00                         │
│ 税费:      $91.84                         │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ 总计:   $1,259.84                         │
│                                            │
│ 收货地址:                                  │
│ John Doe                                   │
│ 123 Main St, Apt 4B                       │
│ New York, NY 10001, United States         │
│ +1 234-567-8900                           │
│                                            │
│ 物流信息:                                  │
│ UPS | 1Z999AA10123456784                  │
│ 运输中 | 预计 2025-01-30                  │
│ [查看物流详情]                             │
│                                            │
│ [申请退款] [添加备注] [在Shopify中查看]    │
└───────────────────────────────────────────┘
```

### 2.6 验收标准

**功能验收**：
- [ ] 可按客户邮箱自动查询订单
- [ ] 可按订单号手动搜索
- [ ] 自动识别对话中的订单号
- [ ] 订单列表显示正确（订单号、状态、金额、时间）
- [ ] 订单详情显示完整（商品、地址、物流）
- [ ] 缓存机制正常（5/10/30分钟）
- [ ] 手动刷新正确清除缓存
- [ ] 支持批量查询（最多50个订单）

**性能验收**：
- [ ] 首次查询响应时间 < 2秒
- [ ] 缓存命中响应时间 < 100ms
- [ ] 批量查询50个订单 < 3秒
- [ ] Shopify API调用频率 < 2次/秒

**UI验收**：
- [ ] 订单列表布局清晰
- [ ] 订单详情弹窗完整
- [ ] 缩略图正确显示
- [ ] 物流状态实时更新
- [ ] 响应式布局（支持1366px+分辨率）

---

## 📋 模块3: 订单状态追踪

### 3.1 功能概述

实时追踪订单物流状态，主动通知坐席订单状态变化。

**参考对标**：
- 菜鸟物流：提供详细的物流轨迹
- 京东物流：状态变更实时通知

### 3.2 功能需求

#### 3.2.1 物流追踪

**F3-1: 物流轨迹查询**

通过 Shopify API 获取物流追踪信息：

**数据来源**：
1. Shopify Fulfillment API：`/admin/api/2024-01/orders/{order_id}/fulfillments.json`
2. 第三方物流API（如 AfterShip、17Track）

**显示信息**：

| 字段 | 说明 | 示例 |
|-----|------|------|
| 承运商 | 物流公司 | `UPS` / `USPS` / `FedEx` |
| 运单号 | 跟踪号码 | `1Z999AA10123456784` |
| 当前状态 | 最新状态 | `运输中` / `派送中` / `已签收` |
| 最新位置 | 当前位置 | `纽约分拨中心` |
| 预计送达 | 预计送达时间 | `2025-01-30` |

**F3-2: 物流轨迹时间线**

显示详细的物流节点：

```
┌────────────────────────────────────┐
│ 物流轨迹                            │
├────────────────────────────────────┤
│                                     │
│ ✅ 2025-01-27 14:30               │
│    已揽收 - 纽约仓库                │
│                                     │
│ ✅ 2025-01-27 18:45               │
│    运输中 - 离开纽约分拨中心        │
│                                     │
│ ✅ 2025-01-28 09:20               │
│    运输中 - 到达费城转运中心        │
│                                     │
│ 🚚 2025-01-28 12:00 (预计)        │
│    派送中                           │
│                                     │
│ 📦 2025-01-30 (预计)              │
│    送达                             │
└────────────────────────────────────┘
```

**F3-3: 一键复制物流信息**

提供快捷功能，方便坐席回复客户：

**复制内容模板**：
```
您的订单 #FD20250127001 物流信息：
承运商: UPS
运单号: 1Z999AA10123456784
当前状态: 运输中
最新位置: 费城转运中心
预计送达: 2025-01-30

您可以通过以下链接查看详细物流：
https://www.ups.com/track?tracknum=1Z999AA10123456784
```

#### 3.2.2 状态变更通知

**F3-4: Webhook 事件处理**

接收 Shopify Webhook，实时更新订单状态：

**监听事件**：
- `orders/updated`：订单状态变更
- `fulfillments/create`：订单已发货
- `fulfillments/update`：物流状态更新

**处理流程**：
1. 接收 Webhook 事件
2. 验证签名
3. 解析订单数据
4. 更新 Redis 缓存
5. 通过 SSE 推送给坐席（如果该订单的会话正在进行）

**F3-5: 坐席端实时通知**

当订单状态变化时，通知正在处理该会话的坐席：

**通知方式**：
- SSE 推送：实时更新订单状态
- 浏览器通知：弹出通知提示
- 消息提示：在对话窗口显示提示

**通知文案示例**：
```
🔔 订单状态更新
订单 #FD20250127001 已发货
物流公司: UPS
运单号: 1Z999AA10123456784
[查看详情]
```

**F3-6: 主动提醒客户**

订单状态变化后，系统自动生成提醒消息建议：

**触发条件**：
- 订单已发货
- 订单即将送达（预计1天内）
- 订单已签收

**建议文案**：
```
# 订单已发货
"您好，您的订单 #FD20250127001 已发货，物流单号 1Z999AA10123456784，预计 2025-01-30 送达。"

# 即将送达
"您的订单 #FD20250127001 预计今天送达，请保持电话畅通。"

# 已签收
"您的订单 #FD20250127001 已签收，感谢您的购买！如有任何问题请随时联系我们。"
```

### 3.3 数据模型

**物流追踪模型**：

```typescript
interface FulfillmentTracking {
  fulfillment_id: string           // Shopify Fulfillment ID
  order_id: string                 // 订单ID
  tracking_company: string         // 承运商
  tracking_number: string          // 运单号
  tracking_url: string             // 跟踪链接
  status: string                   // 状态: pending/in_transit/out_for_delivery/delivered
  created_at: Date                 // 发货时间
  estimated_delivery: Date         // 预计送达
  current_location: string         // 当前位置

  // 物流轨迹
  tracking_events: Array<{
    timestamp: Date
    status: string
    location: string
    description: string
  }>
}
```

**状态通知模型**：

```typescript
interface OrderStatusNotification {
  notification_id: string
  order_id: string
  order_number: string
  event_type: 'shipped' | 'delivered' | 'updated'
  message: string                  // 通知消息
  created_at: Date
  session_name: string             // 关联会话（如有）
  agent_id: string                 // 通知坐席（如有）
}
```

### 3.4 后端API设计

**物流追踪API**：

```
GET  /api/shopify/orders/{order_id}/tracking         # 获取物流信息
GET  /api/shopify/tracking/{tracking_number}         # 根据运单号查询
POST /api/shopify/orders/{order_id}/tracking/refresh # 刷新物流信息
```

**Webhook 接收API**：

```
POST /api/webhooks/shopify/fulfillments/create       # 订单已发货
POST /api/webhooks/shopify/fulfillments/update       # 物流状态更新
```

### 3.5 验收标准

**功能验收**：
- [ ] 可查询订单的物流信息
- [ ] 物流轨迹时间线正确显示
- [ ] 一键复制物流信息功能正常
- [ ] Webhook 正确处理订单状态变更
- [ ] 状态变更时正确通知坐席
- [ ] 自动生成提醒消息建议
- [ ] 支持第三方物流API查询（可选）

**实时性验收**：
- [ ] Webhook 接收延迟 < 500ms
- [ ] SSE 推送延迟 < 1秒
- [ ] 物流信息刷新延迟 < 2秒

**UI验收**：
- [ ] 物流轨迹时间线清晰
- [ ] 状态图标正确显示
- [ ] 通知提示明显
- [ ] 复制功能正常

---

## 📋 模块4: 订单操作集成

### 4.1 功能概述

在客服系统中直接执行订单操作，无需跳转到 Shopify 后台。

**参考对标**：
- 拼多多客服：支持直接退款、修改订单
- 有赞客服：支持添加订单备注

### 4.2 功能需求

#### 4.2.1 退款申请

**F4-1: 发起退款**

坐席可在客服系统中直接发起退款：

**退款类型**：
1. 全额退款：退还订单全部金额
2. 部分退款：退还指定金额或指定商品
3. 运费退款：仅退还运费

**退款流程**：
```
1. 坐席选择订单
2. 点击"申请退款"
3. 填写退款信息：
   - 退款类型（全额/部分）
   - 退款金额
   - 退款商品（部分退款需选择）
   - 退款原因
   - 备注说明
4. 提交申请
5. 系统调用 Shopify API 创建退款
6. 返回结果（成功/失败）
```

**F4-2: 退款原因选项**

提供标准退款原因：

| 退款原因 | 说明 |
|---------|------|
| 商品质量问题 | 产品存在缺陷 |
| 收到商品与描述不符 | 商品与页面描述不一致 |
| 客户不想要了 | 客户主动取消 |
| 商品损坏 | 运输过程中损坏 |
| 发错货 | 发送了错误的商品 |
| 其他 | 其他原因（需填写备注） |

**F4-3: 退款记录**

记录所有退款操作：

```typescript
interface RefundRecord {
  refund_id: string                // Shopify Refund ID
  order_id: string                 // 订单ID
  amount: number                   // 退款金额
  reason: string                   // 退款原因
  note: string                     // 备注
  created_at: Date                 // 退款时间
  processed_by: string             // 操作坐席
  status: string                   // 状态: pending/success/failed
}
```

#### 4.2.2 订单修改

**F4-4: 添加订单备注**

坐席可为订单添加内部备注（仅坐席可见）：

**备注类型**：
- 客户需求备注：如"客户要求加急发货"
- 问题记录备注：如"客户反馈电池续航问题"
- 处理记录备注：如"已联系仓库，明天发货"

**F4-5: 修改收货地址**（有限支持）

**约束条件**：
- 仅未发货订单可修改
- 需客户确认新地址
- 修改后发送确认邮件

**修改流程**：
```
1. 坐席点击"修改地址"
2. 弹出地址编辑表单
3. 填写新地址信息
4. 提交修改
5. 系统调用 Shopify API 更新地址
6. 发送确认邮件给客户
```

**F4-6: 取消订单**

**允许取消条件**：
- 订单状态为"待发货"（`unfulfilled`）
- 订单未标记为"已支付且正在处理"

**取消流程**：
```
1. 坐席点击"取消订单"
2. 选择取消原因
3. 确认取消
4. 系统调用 Shopify API 取消订单
5. 自动触发退款（如已支付）
```

#### 4.2.3 权限控制

**F4-7: 操作权限分级**

不同操作需要不同权限：

| 操作 | 普通坐席 | 高级坐席 | 管理员 |
|-----|---------|---------|--------|
| 查看订单 | ✅ | ✅ | ✅ |
| 添加备注 | ✅ | ✅ | ✅ |
| 部分退款（< $50） | ✅ | ✅ | ✅ |
| 部分退款（> $50） | ❌ 需审批 | ✅ | ✅ |
| 全额退款 | ❌ 需审批 | ✅ | ✅ |
| 修改地址 | ❌ | ✅ | ✅ |
| 取消订单 | ❌ | ✅ | ✅ |

**审批流程**（可选实现）：
```
1. 普通坐席发起退款申请
2. 系统通知管理员
3. 管理员审批（同意/拒绝）
4. 系统执行退款或通知坐席
```

### 4.3 数据模型

**订单操作记录模型**：

```typescript
interface OrderOperation {
  operation_id: string
  order_id: string
  operation_type: 'refund' | 'update_address' | 'cancel' | 'add_note'
  operator: string                 // 操作坐席
  operation_data: any              // 操作数据（JSON）
  result: 'success' | 'failed' | 'pending'
  error_message?: string
  created_at: Date
}
```

### 4.4 后端API设计

**订单操作API**：

```
POST /api/shopify/orders/{order_id}/refund           # 发起退款
POST /api/shopify/orders/{order_id}/note             # 添加备注
PUT  /api/shopify/orders/{order_id}/address          # 修改地址
POST /api/shopify/orders/{order_id}/cancel           # 取消订单
GET  /api/shopify/orders/{order_id}/operations       # 获取操作历史
```

**请求示例**（发起退款）：

```json
POST /api/shopify/orders/5123456789012/refund
{
  "refund_type": "partial",
  "amount": 100.00,
  "reason": "商品质量问题",
  "note": "客户反馈电池续航不足，同意退款",
  "notify_customer": true
}
```

**响应示例**：

```json
{
  "success": true,
  "data": {
    "refund_id": "789012345678",
    "amount": 100.00,
    "status": "success",
    "created_at": "2025-01-27T15:30:00Z",
    "message": "退款成功，预计3-5个工作日到账"
  }
}
```

### 4.5 UI设计

**退款申请弹窗**：

```
┌─────────────────────────────────────────┐
│ 退款申请 - 订单 #FD20250127001   [关闭] │
├─────────────────────────────────────────┤
│                                          │
│ 退款类型: (*) 全额退款                   │
│           ( ) 部分退款                   │
│           ( ) 仅退运费                   │
│                                          │
│ 退款金额: $1,259.84  (不可编辑)         │
│                                          │
│ 退款原因: [商品质量问题 ▼]              │
│                                          │
│ 备注说明:                                │
│ ┌────────────────────────────────────┐  │
│ │ 客户反馈电池续航不足，同意退款      │  │
│ │                                     │  │
│ └────────────────────────────────────┘  │
│                                          │
│ [ ] 通知客户（发送邮件）                 │
│                                          │
│ ⚠️ 提示：退款将在3-5个工作日内到账      │
│                                          │
│         [取消]  [确认退款]               │
└─────────────────────────────────────────┘
```

**订单操作按钮组**：

```
┌─────────────────────────────────────┐
│ 订单操作:                            │
│ [📝 添加备注] [✏️ 修改地址]          │
│ [💰 申请退款] [❌ 取消订单]          │
└─────────────────────────────────────┘
```

### 4.6 验收标准

**功能验收**：
- [ ] 可发起全额退款
- [ ] 可发起部分退款
- [ ] 可添加订单备注
- [ ] 可修改未发货订单的地址
- [ ] 可取消未发货订单
- [ ] 退款记录正确保存
- [ ] 操作权限控制正确
- [ ] 操作失败时正确提示错误

**安全验收**：
- [ ] 退款操作需要二次确认
- [ ] 大额退款（> $50）需要管理员权限
- [ ] 操作日志完整记录
- [ ] 敏感操作有审批流程（可选）

**性能验收**：
- [ ] 退款请求响应时间 < 3秒
- [ ] 订单修改响应时间 < 2秒

**UI验收**：
- [ ] 退款申请弹窗清晰
- [ ] 操作按钮明显
- [ ] 成功/失败提示明确
- [ ] 权限不足时禁用按钮

---

## 🔗 与其他模块的关系

**依赖关系**：
- **依赖**: v3.3.0 客户画像功能（`user_profile`）
- **依赖**: v3.2.0 会话管理（`session_name`）
- **被依赖**: L2-2 客户画像增强（订单数据用于VIP识别）

**数据流**：
```
Shopify API
  ↓
订单查询 → 显示在坐席工作台
  ↓
坐席操作（退款/修改）
  ↓
Shopify API 更新
  ↓
Webhook 回调
  ↓
更新客服系统缓存
```

---

## 📊 开发优先级

### 第一阶段（P0 - 必须实现）
- [ ] Shopify OAuth 认证
- [ ] 基础连接配置和测试
- [ ] 按邮箱查询订单
- [ ] 订单列表显示
- [ ] 订单详情显示

### 第二阶段（P1 - 重要）
- [ ] 订单号自动识别
- [ ] 物流追踪功能
- [ ] Webhook 配置和处理
- [ ] 状态变更通知
- [ ] 添加订单备注

### 第三阶段（P2 - 优化）
- [ ] 退款申请功能
- [ ] 修改订单地址
- [ ] 取消订单
- [ ] 操作权限控制
- [ ] 第三方物流API集成

---

## 🧪 测试要点

### 单元测试
- Shopify API 调用逻辑
- Webhook 签名验证
- 缓存机制
- 权限控制逻辑

### 集成测试
- OAuth 授权流程
- 订单查询和显示
- Webhook 接收和处理
- 退款申请流程

### 性能测试
- 订单查询响应时间
- 缓存命中率
- Shopify API调用频率
- 并发查询能力

---

## 📝 实施注意事项

### 技术约束
1. **Shopify API 速率限制**：标准计划 2次/秒，Plus计划 4次/秒
2. **Webhook 签名验证**：必须验证 `X-Shopify-Hmac-SHA256`
3. **Access Token 安全**：必须加密存储，不可明文
4. **缓存策略**：合理使用缓存，减少API调用

### 开发建议
1. 先实现查询功能，再实现操作功能
2. 先实现OAuth认证，再实现Webhook
3. 使用 Shopify 官方 SDK（如有）
4. 测试环境使用 Shopify 开发店铺

### Shopify API 版本
- 使用最新稳定版本：`2024-01`
- 定期检查版本更新
- 做好版本兼容性处理

### Fiido 电动自行车业务特点
- 商品单价较高（$500 - $2000）
- 物流周期较长（3-7天）
- 售后问题常见：电池续航、组装问题
- 需要重点追踪物流状态

---

## 📚 参考资料

- **Shopify API 文档**: https://shopify.dev/docs/api/admin-rest
- **OAuth 授权流程**: https://shopify.dev/docs/apps/auth/oauth
- **Webhook 配置**: https://shopify.dev/docs/apps/webhooks
- **技术约束**: `prd/02_约束与原则/CONSTRAINTS_AND_PRINCIPLES.md`
- **API契约**: `prd/03_技术方案/api_contract.md`

---

**下一步**: 阅读 `L2-2-Part1_客户基础信息与行为.md`

**文档维护者**: Claude Code
**最后更新**: 2025-01-27
