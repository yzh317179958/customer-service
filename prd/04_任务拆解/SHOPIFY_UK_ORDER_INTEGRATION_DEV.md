# Shopify UK 订单查询集成 - 开发周期文档

> **文档编号**: SHOPIFY-UK-INT-001
> **文档版本**: v1.0
> **优先级**: P0（核心功能）
> **状态**: ❌ 待开发
> **创建时间**: 2025-12-09
> **最后更新**: 2025-12-09
> **目标系统**: Coze AI 客服集成

---

## 📋 文档导航

- **上级文档**: [L2-1_Shopify订单集成.md](./L2-1_Shopify订单集成.md)（完整版方案参考）
- **开发规范**: [CLAUDE.md](../../CLAUDE.md)
- **技术约束**: [prd/02_约束与原则/](../02_约束与原则/)

---

## 🎯 项目概述

### 1.1 背景

为 Fiido UK 电动自行车店铺 (`fiidouk.myshopify.com`) 的 Coze AI 客服系统集成 Shopify 订单查询功能，提升客服效率和用户体验。

### 1.2 现有资源

| 资源 | 值 | 说明 |
|------|-----|------|
| 店铺域名 | `fiidouk.myshopify.com` | Shopify UK 店铺 |
| API Token | `shpat_YOUR_ACCESS_TOKEN` | Admin API Access Token |
| 权限范围 | `read_orders`, `read_shipping` | **只读权限** |
| API 版本 | `2024-01` | 建议使用稳定版本 |

### 1.3 权限分析

**✅ 可实现功能**（基于现有权限）：
- 订单列表查询（按邮箱、订单号）
- 订单详情查看（商品、金额、地址）
- 物流信息查询（承运商、运单号、状态）
- 订单数量统计

**❌ 不可实现功能**（需要额外权限）：
- 退款申请（需 `write_orders`）
- 修改订单（需 `write_orders`）
- 添加订单备注（需 `write_orders`）
- Webhook 订阅（需 OAuth 应用配置）
- 客户信息修改（需 `write_customers`）

### 1.4 业务价值

参考市场最佳实践（来源：[Shopify AI Customer Service](https://www.shopify.com/blog/ai-customer-service)、[AI Chatbot Customer Service](https://www.shopify.com/blog/ai-chatbot-customer-service)）：

| 指标 | 当前痛点 | 集成后收益 |
|------|---------|-----------|
| 响应时间 | 需手动切换系统查询 | 提升 60%+ |
| 物流咨询 | 坐席需登录 Shopify 后台 | AI 直接回答 |
| 客户满意度 | 等待时间长 | 预计提升 40% |
| 成本控制 | 人工处理所有查询 | AI 自动处理 80%+ |

---

## 🏗️ 技术方案

### 2.1 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         Coze AI 客服系统                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   用户输入: "我的订单 #UK22080 什么时候发货？"                    │
│                      ↓                                            │
│   ┌─────────────────────────────────────────┐                    │
│   │           Coze AI 意图识别               │                    │
│   │   识别为: 订单查询 (order_query)         │                    │
│   └─────────────────────────────────────────┘                    │
│                      ↓                                            │
│   ┌─────────────────────────────────────────┐                    │
│   │         Coze 插件: Shopify 订单          │                    │
│   │   调用: query_order(order_number)        │                    │
│   └─────────────────────────────────────────┘                    │
│                      ↓                                            │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP API 调用
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│                    中间件服务 (本项目开发)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   ┌────────────────┐    ┌────────────────┐    ┌───────────────┐ │
│   │  订单查询 API   │    │   物流查询 API  │    │  缓存层 Redis │ │
│   │ /api/orders     │    │ /api/tracking   │    │  TTL: 5-30min │ │
│   └────────┬───────┘    └────────┬───────┘    └───────────────┘ │
│            │                     │                               │
│            └─────────┬───────────┘                               │
│                      ↓                                            │
│   ┌─────────────────────────────────────────┐                    │
│   │         Shopify API 封装层               │                    │
│   │   - 认证管理 (Token)                     │                    │
│   │   - 速率限制 (2次/秒)                    │                    │
│   │   - 错误处理 & 重试                      │                    │
│   └─────────────────────────────────────────┘                    │
│                                                                   │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTPS
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Shopify Admin API                                │
│            https://fiidouk.myshopify.com/admin/api/2024-01/       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Coze 集成方式

**方式一：Coze 插件（推荐）**

在 Coze 平台创建自定义插件，调用本项目开发的中间件 API：

```yaml
# Coze 插件配置示例
name: shopify_uk_orders
description: Fiido UK Shopify 订单查询插件
endpoints:
  - name: query_order_by_number
    method: GET
    path: /api/orders/search
    params:
      - name: order_number
        type: string
        required: true

  - name: query_orders_by_email
    method: GET
    path: /api/orders
    params:
      - name: email
        type: string
        required: true

  - name: get_tracking_info
    method: GET
    path: /api/orders/{order_id}/tracking
```

**方式二：Coze 工作流 + HTTP 节点**

在 Coze 工作流中使用 HTTP 请求节点直接调用中间件 API。

### 2.3 API 端点设计

#### 2.3.1 订单查询 API

```
GET  /api/shopify/orders                    # 按邮箱查询订单列表
GET  /api/shopify/orders/search             # 按订单号搜索
GET  /api/shopify/orders/{order_id}         # 获取订单详情
GET  /api/shopify/orders/{order_id}/tracking # 获取物流信息
GET  /api/shopify/orders/count              # 获取订单数量
POST /api/shopify/orders/batch              # 批量查询订单
```

#### 2.3.2 请求/响应示例

**按订单号搜索**：
```bash
GET /api/shopify/orders/search?q=UK22080
Authorization: Bearer {internal_token}
```

**响应**：
```json
{
  "success": true,
  "data": {
    "order": {
      "order_id": "6615015620909",
      "order_number": "#UK22080",
      "created_at": "2025-12-09T07:36:10+08:00",
      "status": {
        "financial": "paid",
        "fulfillment": "unfulfilled"
      },
      "total_price": "1637.69",
      "currency": "GBP",
      "customer": {
        "name": "Daniel Harris",
        "email": "danielharris343@gmail.com"
      },
      "shipping_address": {
        "address": "32 Mount Pleasant Walk",
        "city": "Manchester",
        "zip": "M26 4FJ",
        "country": "United Kingdom"
      },
      "line_items": [
        {
          "title": "Titan Fat Tire Touring Ebike - Long range",
          "variant": "Standard (115 km)",
          "sku": "M25-145G1-UK",
          "quantity": 1,
          "price": "1545.00"
        },
        {
          "title": "Bike Rack Pannier Bag",
          "sku": "A5901",
          "quantity": 1,
          "price": "60.00"
        }
      ],
      "fulfillments": [],
      "tracking": null
    },
    "cached": false,
    "cache_ttl": 300
  }
}
```

**物流信息查询**：
```bash
GET /api/shopify/orders/6615015620909/tracking
```

**响应**（已发货订单）：
```json
{
  "success": true,
  "data": {
    "order_id": "6615015620909",
    "order_number": "#UK22080",
    "tracking": {
      "company": "Royal Mail",
      "number": "AB123456789GB",
      "url": "https://www.royalmail.com/track?trackNumber=AB123456789GB",
      "status": "in_transit",
      "estimated_delivery": "2025-12-12"
    },
    "message_template": "您的订单 #UK22080 物流信息：\n承运商: Royal Mail\n运单号: AB123456789GB\n当前状态: 运输中\n预计送达: 2025-12-12\n\n追踪链接: https://www.royalmail.com/track?trackNumber=AB123456789GB"
  }
}
```

### 2.4 数据模型

#### 2.4.1 订单摘要 (OrderSummary)

```python
class OrderSummary(BaseModel):
    """订单摘要 - 用于列表显示"""
    order_id: str                    # Shopify Order ID
    order_number: str                # 订单号 (#UK22080)
    created_at: datetime             # 下单时间
    financial_status: str            # 支付状态: pending/paid/refunded
    fulfillment_status: Optional[str] # 发货状态: null/partial/fulfilled
    total_price: Decimal             # 总金额
    currency: str                    # 货币 (GBP)
    items_count: int                 # 商品数量
    customer_email: str              # 客户邮箱
    customer_name: str               # 客户姓名
```

#### 2.4.2 订单详情 (OrderDetail)

```python
class OrderDetail(OrderSummary):
    """订单详情 - 完整信息"""

    # 商品列表
    line_items: List[LineItem]

    # 价格明细
    subtotal_price: Decimal          # 小计
    total_shipping: Decimal          # 运费
    total_discounts: Decimal         # 折扣
    total_tax: Decimal               # 税费

    # 收货地址
    shipping_address: ShippingAddress

    # 物流信息
    fulfillments: List[Fulfillment]

    # 备注和标签
    note: Optional[str]
    tags: List[str]
    discount_codes: List[str]
```

#### 2.4.3 物流信息 (TrackingInfo)

```python
class TrackingInfo(BaseModel):
    """物流追踪信息"""
    tracking_company: str            # 承运商 (Royal Mail, DPD, etc.)
    tracking_number: str             # 运单号
    tracking_url: str                # 追踪链接
    status: str                      # 状态: pending/in_transit/delivered
    shipped_at: Optional[datetime]   # 发货时间
    estimated_delivery: Optional[date] # 预计送达
```

### 2.5 缓存策略

```python
# Redis 缓存键设计
CACHE_KEYS = {
    "order_list": "shopify:uk:orders:list:{email}",      # TTL: 5 分钟
    "order_detail": "shopify:uk:orders:detail:{order_id}", # TTL: 10 分钟
    "tracking": "shopify:uk:tracking:{order_id}",         # TTL: 30 分钟
    "order_count": "shopify:uk:orders:count",             # TTL: 60 分钟
}

# 缓存配置
CACHE_TTL = {
    "order_list": 300,      # 5 分钟
    "order_detail": 600,    # 10 分钟
    "tracking": 1800,       # 30 分钟
    "order_count": 3600,    # 60 分钟
}
```

### 2.6 错误处理

```python
# 错误码定义
ERROR_CODES = {
    "SHOPIFY_API_ERROR": {"code": 5001, "message": "Shopify API 调用失败"},
    "ORDER_NOT_FOUND": {"code": 5002, "message": "订单不存在"},
    "INVALID_ORDER_NUMBER": {"code": 5003, "message": "无效的订单号格式"},
    "RATE_LIMITED": {"code": 5004, "message": "请求过于频繁，请稍后重试"},
    "TOKEN_INVALID": {"code": 5005, "message": "API Token 无效或已过期"},
    "PERMISSION_DENIED": {"code": 5006, "message": "权限不足"},
}
```

---

## 📝 开发任务拆解

### 遵循原则

按照 `CLAUDE.md` **铁律 0: 渐进式增量化开发**：
- ✅ 每个增量 < 2 小时开发量
- ✅ 每次修改文件 < 5 个
- ✅ 每次代码变更 < 300 行
- ✅ 每个增量独立测试和提交

---

### 阶段一：基础设施搭建 (P0)

#### 增量 1.1: Shopify API 客户端封装

**开发内容**：
- 创建 `src/shopify_client.py`
- 实现 Token 认证
- 实现基础 HTTP 请求封装
- 实现速率限制 (2次/秒)

**文件清单**：
```
src/shopify_client.py    # 新建
.env                     # 添加配置
```

**代码示例**：
```python
# src/shopify_client.py
import httpx
import asyncio
from typing import Optional, Dict, Any
import os

class ShopifyClient:
    """Shopify Admin API 客户端"""

    def __init__(self):
        self.shop_domain = os.getenv("SHOPIFY_UK_SHOP_DOMAIN", "fiidouk.myshopify.com")
        self.access_token = os.getenv("SHOPIFY_UK_ACCESS_TOKEN")
        self.api_version = os.getenv("SHOPIFY_UK_API_VERSION", "2024-01")
        self.base_url = f"https://{self.shop_domain}/admin/api/{self.api_version}"

        # 速率限制: 2次/秒
        self._rate_limiter = asyncio.Semaphore(2)
        self._last_request_time = 0

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """带速率限制的 HTTP 请求"""
        async with self._rate_limiter:
            # 确保请求间隔 >= 500ms
            await self._wait_for_rate_limit()

            headers = {
                "X-Shopify-Access-Token": self.access_token,
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method,
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    **kwargs
                )
                response.raise_for_status()
                return response.json()
```

**验收标准**：
- [ ] Token 认证正确
- [ ] 速率限制生效 (2次/秒)
- [ ] 错误处理完善
- [ ] 单元测试通过

**预计时间**: 1.5 小时

---

#### 增量 1.2: Redis 缓存层实现

**开发内容**：
- 创建 `src/shopify_cache.py`
- 实现缓存读写
- 实现 TTL 管理
- 实现缓存失效

**文件清单**：
```
src/shopify_cache.py     # 新建
```

**代码示例**：
```python
# src/shopify_cache.py
import json
import redis
from typing import Optional, Any

class ShopifyCache:
    """Shopify 订单缓存"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.prefix = "shopify:uk"

    async def get_order(self, order_id: str) -> Optional[dict]:
        """获取订单缓存"""
        key = f"{self.prefix}:orders:detail:{order_id}"
        data = self.redis.get(key)
        return json.loads(data) if data else None

    async def set_order(self, order_id: str, data: dict, ttl: int = 600):
        """设置订单缓存"""
        key = f"{self.prefix}:orders:detail:{order_id}"
        self.redis.setex(key, ttl, json.dumps(data))

    async def invalidate_order(self, order_id: str):
        """清除订单缓存"""
        pattern = f"{self.prefix}:*:{order_id}"
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)
```

**验收标准**：
- [ ] 缓存读写正确
- [ ] TTL 过期正常
- [ ] 缓存失效机制正常

**预计时间**: 1 小时

---

### 阶段二：订单查询功能 (P0)

#### 增量 2.1: 订单列表查询 API

**开发内容**：
- 在 `backend.py` 添加 `/api/shopify/orders` 端点
- 实现按邮箱查询订单
- 返回订单摘要列表

**文件清单**：
```
backend.py               # 添加 API 端点
src/shopify_client.py    # 添加 get_orders 方法
```

**API 定义**：
```python
@app.get("/api/shopify/orders")
async def get_shopify_orders(
    email: str = Query(..., description="客户邮箱"),
    limit: int = Query(10, ge=1, le=50, description="返回数量")
):
    """按客户邮箱查询订单列表"""
    pass
```

**验收标准**：
- [ ] 按邮箱查询返回订单列表
- [ ] 分页功能正常 (limit)
- [ ] 缓存命中时响应 < 100ms
- [ ] 首次查询响应 < 2s

**预计时间**: 1.5 小时

---

#### 增量 2.2: 订单号搜索 API

**开发内容**：
- 添加 `/api/shopify/orders/search` 端点
- 支持订单号模糊搜索
- 支持 #UK22080 和 UK22080 两种格式

**文件清单**：
```
backend.py               # 添加 API 端点
src/shopify_client.py    # 添加 search_order 方法
```

**API 定义**：
```python
@app.get("/api/shopify/orders/search")
async def search_shopify_order(
    q: str = Query(..., min_length=3, description="订单号关键词")
):
    """按订单号搜索订单"""
    pass
```

**验收标准**：
- [ ] 支持完整订单号搜索
- [ ] 支持去除 # 前缀
- [ ] 订单号不存在时返回 404
- [ ] 响应时间 < 2s

**预计时间**: 1 小时

---

#### 增量 2.3: 订单详情 API

**开发内容**：
- 添加 `/api/shopify/orders/{order_id}` 端点
- 返回完整订单信息
- 包含商品、地址、价格明细

**文件清单**：
```
backend.py               # 添加 API 端点
src/shopify_client.py    # 添加 get_order_detail 方法
```

**API 定义**：
```python
@app.get("/api/shopify/orders/{order_id}")
async def get_shopify_order_detail(
    order_id: str = Path(..., description="Shopify 订单 ID")
):
    """获取订单详情"""
    pass
```

**验收标准**：
- [ ] 返回完整订单信息
- [ ] 包含所有商品详情
- [ ] 包含收货地址
- [ ] 包含价格明细 (小计、运费、折扣、税费)

**预计时间**: 1.5 小时

---

### 阶段三：物流查询功能 (P1)

#### 增量 3.1: 物流信息查询 API

**开发内容**：
- 添加 `/api/shopify/orders/{order_id}/tracking` 端点
- 提取物流信息 (承运商、运单号、状态)
- 生成客服话术模板

**文件清单**：
```
backend.py               # 添加 API 端点
src/shopify_client.py    # 添加 get_tracking 方法
```

**API 定义**：
```python
@app.get("/api/shopify/orders/{order_id}/tracking")
async def get_shopify_tracking(
    order_id: str = Path(..., description="Shopify 订单 ID")
):
    """获取订单物流信息"""
    pass
```

**验收标准**：
- [ ] 返回物流承运商和运单号
- [ ] 生成追踪链接
- [ ] 生成客服话术模板
- [ ] 未发货订单返回空

**预计时间**: 1.5 小时

---

#### 增量 3.2: 物流状态翻译

**开发内容**：
- 创建物流状态映射表
- 支持中英文状态显示
- 支持常见承运商识别

**文件清单**：
```
src/shopify_tracking.py  # 新建
```

**代码示例**：
```python
# 承运商追踪链接模板
CARRIER_TRACKING_URLS = {
    "Royal Mail": "https://www.royalmail.com/track-your-item#/tracking-results/{tracking_number}",
    "DPD": "https://www.dpd.co.uk/tracking/trackingSearch.do?parcelNumber={tracking_number}",
    "Hermes": "https://www.myhermes.co.uk/tracking-results?barcode={tracking_number}",
    "UPS": "https://www.ups.com/track?tracknum={tracking_number}",
    "DHL": "https://www.dhl.com/en/express/tracking.html?AWB={tracking_number}",
}

# 状态翻译
STATUS_TRANSLATION = {
    "pending": {"en": "Pending", "zh": "待处理"},
    "in_transit": {"en": "In Transit", "zh": "运输中"},
    "out_for_delivery": {"en": "Out for Delivery", "zh": "派送中"},
    "delivered": {"en": "Delivered", "zh": "已签收"},
}
```

**验收标准**：
- [ ] 支持 5+ 常见承运商
- [ ] 状态翻译准确
- [ ] 追踪链接可点击

**预计时间**: 1 小时

---

### 阶段四：Coze 集成 (P1)

#### 增量 4.1: Coze 插件配置文件

**开发内容**：
- 创建 Coze 插件 OpenAPI 规范文件
- 定义插件端点和参数
- 编写使用说明

**文件清单**：
```
coze/shopify_plugin.yaml   # 新建
coze/README.md             # 新建
```

**插件配置示例**：
```yaml
# coze/shopify_plugin.yaml
openapi: 3.0.0
info:
  title: Fiido UK Shopify 订单查询
  version: 1.0.0
  description: 用于查询 Fiido UK Shopify 店铺的订单和物流信息

servers:
  - url: https://your-api-domain.com

paths:
  /api/shopify/orders/search:
    get:
      operationId: searchOrder
      summary: 按订单号搜索订单
      parameters:
        - name: q
          in: query
          required: true
          schema:
            type: string
          description: 订单号 (如 UK22080 或 #UK22080)
      responses:
        '200':
          description: 订单信息
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OrderDetail'

  /api/shopify/orders:
    get:
      operationId: getOrdersByEmail
      summary: 按客户邮箱查询订单
      parameters:
        - name: email
          in: query
          required: true
          schema:
            type: string
            format: email
          description: 客户邮箱
      responses:
        '200':
          description: 订单列表

  /api/shopify/orders/{order_id}/tracking:
    get:
      operationId: getTracking
      summary: 获取订单物流信息
      parameters:
        - name: order_id
          in: path
          required: true
          schema:
            type: string
          description: Shopify 订单 ID
      responses:
        '200':
          description: 物流信息
```

**验收标准**：
- [ ] OpenAPI 规范文件有效
- [ ] 可在 Coze 平台导入
- [ ] 端点描述清晰

**预计时间**: 1 小时

---

#### 增量 4.2: Coze 工作流对接指南

**开发内容**：
- 编写 Coze 工作流配置指南
- 包含意图识别配置
- 包含话术模板

**文件清单**：
```
coze/WORKFLOW_GUIDE.md   # 新建
```

**工作流设计**：
```
用户输入
    ↓
意图识别 (Intent Recognition)
    ├── order_status_query    → 订单状态查询
    ├── order_detail_query    → 订单详情查询
    ├── shipping_query        → 物流查询
    └── general_question      → 通用问答
    ↓
订单号/邮箱提取 (Entity Extraction)
    ↓
调用 Shopify 插件
    ↓
格式化回复
    ↓
输出给用户
```

**话术模板示例**：
```
# 订单状态查询回复模板
您好，您的订单 {{order_number}} 当前状态如下：
- 订单状态：{{fulfillment_status}}
- 支付状态：{{financial_status}}
- 下单时间：{{created_at}}
- 订单金额：{{total_price}} {{currency}}

{{#if tracking}}
物流信息：
- 承运商：{{tracking.company}}
- 运单号：{{tracking.number}}
- 追踪链接：{{tracking.url}}
{{else}}
您的订单尚未发货，我们会尽快为您安排发货。
{{/if}}

如有其他问题，请随时告诉我。
```

**验收标准**：
- [ ] 指南清晰易懂
- [ ] 包含截图说明
- [ ] 话术模板完整

**预计时间**: 1.5 小时

---

### 阶段五：测试与文档 (P0)

#### 增量 5.1: 自动化测试脚本

**开发内容**：
- 创建 `tests/test_shopify_api.sh`
- 覆盖所有 API 端点
- 包含正常和异常场景

**文件清单**：
```
tests/test_shopify_api.sh   # 新建
```

**测试用例**：
```bash
#!/bin/bash
# tests/test_shopify_api.sh

BASE_URL="http://localhost:8000"
PASSED=0
FAILED=0

echo "=========================================="
echo "Shopify UK 订单 API 测试"
echo "=========================================="

# 测试 1: 按邮箱查询订单
echo "测试 1: 按邮箱查询订单"
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/shopify/orders?email=danielharris343@gmail.com")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" -eq 200 ]; then
    echo "✅ PASS"
    ((PASSED++))
else
    echo "❌ FAIL - HTTP $HTTP_CODE"
    ((FAILED++))
fi

# 测试 2: 按订单号搜索
echo "测试 2: 按订单号搜索"
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/shopify/orders/search?q=UK22080")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" -eq 200 ]; then
    echo "✅ PASS"
    ((PASSED++))
else
    echo "❌ FAIL - HTTP $HTTP_CODE"
    ((FAILED++))
fi

# 测试 3: 订单不存在
echo "测试 3: 订单不存在"
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/shopify/orders/search?q=NOTEXIST999")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" -eq 404 ]; then
    echo "✅ PASS"
    ((PASSED++))
else
    echo "❌ FAIL - 预期 404，实际 $HTTP_CODE"
    ((FAILED++))
fi

# ... 更多测试用例

echo "=========================================="
echo "测试完成: $PASSED 通过, $FAILED 失败"
echo "=========================================="

exit $FAILED
```

**验收标准**：
- [ ] 覆盖所有 API 端点
- [ ] 包含正常和异常场景
- [ ] 所有测试通过

**预计时间**: 1 小时

---

#### 增量 5.2: 集成到回归测试

**开发内容**：
- 更新 `tests/regression_test.sh`
- 添加 Shopify API 测试

**文件清单**：
```
tests/regression_test.sh   # 更新
```

**验收标准**：
- [ ] 测试集成到回归测试
- [ ] 回归测试全部通过

**预计时间**: 0.5 小时

---

## 📊 开发进度汇总

| 阶段 | 增量 | 功能 | 状态 | 预计时间 |
|------|------|------|------|---------|
| **阶段一** | 1.1 | Shopify API 客户端 | ❌ 待开发 | 1.5h |
| | 1.2 | Redis 缓存层 | ❌ 待开发 | 1h |
| **阶段二** | 2.1 | 订单列表查询 API | ❌ 待开发 | 1.5h |
| | 2.2 | 订单号搜索 API | ❌ 待开发 | 1h |
| | 2.3 | 订单详情 API | ❌ 待开发 | 1.5h |
| **阶段三** | 3.1 | 物流信息查询 API | ❌ 待开发 | 1.5h |
| | 3.2 | 物流状态翻译 | ❌ 待开发 | 1h |
| **阶段四** | 4.1 | Coze 插件配置 | ❌ 待开发 | 1h |
| | 4.2 | Coze 工作流指南 | ❌ 待开发 | 1.5h |
| **阶段五** | 5.1 | 自动化测试 | ❌ 待开发 | 1h |
| | 5.2 | 回归测试集成 | ❌ 待开发 | 0.5h |

**总计**: 约 **13 小时** 开发时间

---

## ✅ 验收标准

### 功能验收

- [ ] 可按客户邮箱查询订单列表
- [ ] 可按订单号搜索订单
- [ ] 可查看订单详情（商品、地址、价格）
- [ ] 可查询物流信息
- [ ] 缓存机制正常（5/10/30分钟 TTL）
- [ ] Coze 插件可正常导入使用

### 性能验收

- [ ] 首次查询响应时间 < 2s
- [ ] 缓存命中响应时间 < 100ms
- [ ] Shopify API 调用频率 < 2次/秒
- [ ] 支持 10+ 并发查询

### 安全验收

- [ ] API Token 不暴露在日志中
- [ ] 错误信息不泄露敏感数据
- [ ] 接口有访问限制（防滥用）

---

## 📚 参考资料

- **Shopify Admin API 文档**: https://shopify.dev/docs/api/admin-rest/2024-01/resources/order
- **Coze 插件开发文档**: https://www.coze.com/docs/developer-guides/plugins
- **项目 CLAUDE.md 规范**: `/home/yzh/AI客服/鉴权/CLAUDE.md`
- **完整版 Shopify 集成方案**: `/home/yzh/AI客服/鉴权/prd/04_任务拆解/L2-1_Shopify订单集成.md`

### 市场参考

- [Shopify AI Customer Service](https://www.shopify.com/blog/ai-customer-service) - AI 客服最佳实践
- [AI Chatbot Customer Service](https://www.shopify.com/blog/ai-chatbot-customer-service) - 电商 AI 聊天机器人方案
- [Chatbots for Retail](https://www.shopify.com/enterprise/blog/chatbots-for-retail) - 零售业聊天机器人用例

---

## ⚠️ 注意事项

### 1. API Token 安全

```bash
# .env 文件配置（敏感信息，勿提交到 Git）
SHOPIFY_UK_SHOP_DOMAIN=fiidouk.myshopify.com
SHOPIFY_UK_ACCESS_TOKEN=shpat_YOUR_ACCESS_TOKEN
SHOPIFY_UK_API_VERSION=2024-01
```

### 2. 速率限制

Shopify Admin API 限制：
- 标准计划: **2 次/秒**
- Plus 计划: 4 次/秒

务必实现客户端速率限制，避免被 Shopify 封禁。

### 3. 权限限制

当前 Token 只有 `read_orders` 和 `read_shipping` 权限，**不能**：
- 修改订单
- 发起退款
- 添加订单备注

如需这些功能，需要重新申请 Token 并授予相应权限。

### 4. 缓存更新

由于没有 Webhook 订阅权限，订单状态更新只能依赖：
- 用户手动刷新
- 缓存 TTL 过期

建议在 UI 上提供"刷新"按钮，让用户可以获取最新状态。

---

## 📖 附录A: Coze Workflow 插件配置详细指南

本节详细说明如何在 Coze 平台配置插件，使 AI 工作流能够调用本地后端的 Shopify API。

### A.1 整体架构回顾

```
┌─────────────────────────────────────────────────────────────────────┐
│                           用户交互流程                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  用户 → Vue前端 → FastAPI后端 → Coze Workflow API                   │
│                                     ↓                                 │
│                              Coze AI 处理                            │
│                                     ↓                                 │
│                      ┌──────────────────────────┐                    │
│                      │  识别到订单查询意图       │                    │
│                      │  调用"Shopify插件"       │                    │
│                      └──────────────────────────┘                    │
│                                     ↓                                 │
│                      Coze 插件 HTTP 请求                              │
│                                     ↓                                 │
│                      FastAPI 后端 /api/shopify/*                     │
│                                     ↓                                 │
│                      Shopify Admin API                                │
│                                     ↓                                 │
│                      返回订单数据给 Coze                              │
│                                     ↓                                 │
│                      Coze 格式化回复给用户                            │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

**关键点**：Coze 插件是 Coze Workflow 中的一个节点，它会发起 HTTP 请求到你的后端 API。

### A.2 前置条件

在配置 Coze 插件之前，确保：

1. **后端 API 已部署并可公网访问**
   ```bash
   # 本地开发时可使用 ngrok 暴露
   ngrok http 8000
   # 得到类似 https://abc123.ngrok.io 的公网地址

   # 生产环境应部署到云服务器
   # 例如: https://api.your-domain.com
   ```

2. **API 端点已实现并测试通过**
   ```bash
   # 测试订单搜索 API
   curl "https://your-api.com/api/shopify/orders/search?q=UK22080"
   # 应返回订单数据
   ```

### A.3 在 Coze 平台创建插件

#### 步骤 1: 进入插件管理

1. 登录 [Coze 平台](https://www.coze.com)
2. 进入你的 Bot/应用
3. 左侧菜单选择 **"插件"** 或 **"Plugins"**
4. 点击 **"创建插件"** 或 **"Create Plugin"**

#### 步骤 2: 配置插件基本信息

```yaml
插件名称: Shopify UK 订单查询
插件描述: 查询 Fiido UK 店铺的订单信息和物流状态
插件图标: 选择一个合适的图标
```

#### 步骤 3: 添加 API 端点（工具）

**工具 1: 按订单号搜索**

```yaml
工具名称: search_order_by_number
工具描述: 根据订单号搜索订单信息，支持 #UK22080 或 UK22080 格式

请求配置:
  方法: GET
  URL: https://your-api.com/api/shopify/orders/search

参数:
  - 名称: q
    类型: string
    必填: 是
    描述: 订单号，如 UK22080

请求头:
  Content-Type: application/json
  # 如果你的 API 需要认证
  # Authorization: Bearer {{YOUR_INTERNAL_TOKEN}}
```

**工具 2: 按邮箱查询订单列表**

```yaml
工具名称: get_orders_by_email
工具描述: 根据客户邮箱查询订单列表

请求配置:
  方法: GET
  URL: https://your-api.com/api/shopify/orders

参数:
  - 名称: email
    类型: string
    必填: 是
    描述: 客户邮箱地址
  - 名称: limit
    类型: integer
    必填: 否
    默认值: 10
    描述: 返回订单数量限制
```

**工具 3: 获取物流信息**

```yaml
工具名称: get_tracking_info
工具描述: 获取订单的物流追踪信息

请求配置:
  方法: GET
  URL: https://your-api.com/api/shopify/orders/{order_id}/tracking

路径参数:
  - 名称: order_id
    类型: string
    必填: 是
    描述: Shopify 订单 ID（数字格式）
```

#### 步骤 4: 配置响应解析

Coze 需要知道如何解析 API 返回的数据：

```yaml
响应配置:
  成功状态码: 200
  响应体格式: JSON

响应字段映射:
  - 字段路径: data.order.order_number
    字段名称: 订单号
    字段类型: string

  - 字段路径: data.order.status.fulfillment
    字段名称: 发货状态
    字段类型: string

  - 字段路径: data.order.tracking.number
    字段名称: 运单号
    字段类型: string

  - 字段路径: data.order.tracking.url
    字段名称: 追踪链接
    字段类型: string
```

### A.4 在 Workflow 中使用插件

#### 步骤 1: 编辑 Workflow

1. 进入你的 Coze Workflow 编辑器
2. 当前 Workflow ID: `7577578868671037445`

#### 步骤 2: 添加意图识别节点

```yaml
节点类型: LLM 节点
节点名称: 意图识别

Prompt:
  分析用户输入，判断用户意图：

  意图类型：
  1. order_query - 查询订单状态/详情（关键词：订单、查询、状态、发货）
  2. tracking_query - 查询物流信息（关键词：物流、快递、到哪了、运单）
  3. order_list - 查询所有订单（关键词：我的订单、历史订单）
  4. general - 其他问题

  提取实体：
  - order_number: 订单号（如 UK22080, #UK22080）
  - email: 邮箱地址

  用户输入: {{user_input}}

  输出 JSON:
  {
    "intent": "order_query|tracking_query|order_list|general",
    "order_number": "提取的订单号或null",
    "email": "提取的邮箱或null"
  }
```

#### 步骤 3: 添加条件分支节点

```yaml
节点类型: 条件分支
条件:
  - 当 intent == "order_query" 且 order_number 不为空 → 调用 search_order_by_number
  - 当 intent == "tracking_query" → 调用 get_tracking_info
  - 当 intent == "order_list" 且 email 不为空 → 调用 get_orders_by_email
  - 其他 → 通用对话回复
```

#### 步骤 4: 添加插件调用节点

```yaml
节点类型: 插件调用
插件名称: Shopify UK 订单查询
工具名称: search_order_by_number

输入参数:
  q: {{extracted_order_number}}

输出变量:
  order_data: 插件返回的订单数据
```

#### 步骤 5: 添加回复格式化节点

```yaml
节点类型: LLM 节点
节点名称: 格式化回复

Prompt:
  根据订单数据生成友好的回复：

  订单数据: {{order_data}}

  回复模板:
  您好！您的订单 {{order_number}} 信息如下：

  📦 订单状态：{{fulfillment_status}}
  💰 订单金额：{{total_price}} {{currency}}
  📅 下单时间：{{created_at}}

  {{#if tracking}}
  🚚 物流信息：
  - 承运商：{{tracking.company}}
  - 运单号：{{tracking.number}}
  - 追踪链接：{{tracking.url}}
  {{else}}
  📝 您的订单正在处理中，发货后我会通知您物流信息。
  {{/if}}

  如有其他问题，请随时告诉我！
```

### A.5 Workflow 节点连接示意图

```
┌──────────────┐
│   开始节点   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  意图识别    │ ← LLM 节点
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  条件分支    │
└──┬───┬───┬───┘
   │   │   │
   ▼   ▼   ▼
┌────┐┌────┐┌────┐
│插件││插件││通用│
│调用││调用││回复│
│订单││物流││    │
└─┬──┘└─┬──┘└─┬──┘
  │     │     │
  └──┬──┘     │
     │        │
     ▼        │
┌──────────┐  │
│ 格式化   │  │
│ 回复     │  │
└────┬─────┘  │
     │        │
     └────┬───┘
          │
          ▼
   ┌──────────────┐
   │   结束节点   │
   └──────────────┘
```

### A.6 测试与调试

#### 测试用例

```bash
# 测试 1: 订单号查询
用户输入: "我的订单 UK22080 什么时候发货？"
预期: 调用 search_order_by_number，返回订单详情

# 测试 2: 物流查询
用户输入: "帮我查一下物流到哪了"
预期: 提示用户提供订单号，然后调用 get_tracking_info

# 测试 3: 邮箱查询
用户输入: "我的邮箱是 test@example.com，查一下我的订单"
预期: 调用 get_orders_by_email，返回订单列表
```

#### 调试技巧

1. **查看 Coze 调试日志**
   - 在 Workflow 编辑器中点击"测试"
   - 查看每个节点的输入输出

2. **检查后端日志**
   ```bash
   # 监控后端 API 请求
   tail -f /var/log/your-api/access.log
   ```

3. **常见问题排查**
   - 插件调用失败：检查 API URL 是否可公网访问
   - 响应解析错误：检查响应字段映射是否正确
   - 超时错误：检查后端 API 响应时间

### A.7 生产环境注意事项

1. **API 安全**
   ```python
   # 建议为 Coze 插件调用添加认证
   @app.get("/api/shopify/orders/search")
   async def search_order(
       q: str,
       x_coze_token: str = Header(None)  # Coze 插件携带的 Token
   ):
       if x_coze_token != EXPECTED_COZE_TOKEN:
           raise HTTPException(401, "Unauthorized")
       # ... 处理逻辑
   ```

2. **CORS 配置**
   ```python
   # 允许 Coze 平台调用
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://www.coze.com", "https://api.coze.com"],
       allow_methods=["GET", "POST"],
       allow_headers=["*"],
   )
   ```

3. **监控告警**
   - 监控插件调用成功率
   - 设置响应时间告警阈值
   - 记录所有 API 调用日志

---

**文档维护者**: Claude Code
**创建时间**: 2025-12-09
**最后更新**: 2025-12-09
