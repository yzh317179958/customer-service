# 17track 物流追踪集成 - 架构说明

> **创建日期**：2025-12-22
> **最后更新**：2025-12-23

---

## Phase 5 架构改进（2025-12-23 新增）

### 自动注册流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     Phase 5: 自动注册机制                         │
└─────────────────────────────────────────────────────────────────┘

用户点击「查看物流」
        │
        ▼
GET /api/tracking/{tracking_number}
        │
        ▼
┌───────────────────┐
│ 查询 17track API  │
└─────────┬─────────┘
          │
    ┌─────┴─────┐
    │           │
 有数据?      无数据
    │           │
    ▼           ▼
┌─────────┐  ┌──────────────────────┐
│返回轨迹  │  │ 后台异步注册运单      │
│events[] │  │ asyncio.create_task()│
└─────────┘  └──────────────────────┘
                    │
                    ▼
            ┌───────────────────┐
            │ 立即返回          │
            │ is_pending: true  │
            │ status_zh: "追踪中"│
            └───────────────────┘
                    │
                    ▼
            前端显示"物流信息更新中，请稍后刷新"
                    │
              (用户刷新)
                    │
                    ▼
            17track 已注册完成，返回实际数据
```

### 改进后的数据流

```
┌─────────────────────────────────────────────────────────────────┐
│                          改进点                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 自动注册：查询失败时自动注册运单（异步，不阻塞）              │
│                                                                 │
│  2. 承运商识别：从 Shopify fulfillment 提取并映射                │
│     Royal Mail → 21051                                         │
│     DPD → 100143                                               │
│     Evri → 100003                                              │
│                                                                 │
│  3. 状态区分：                                                  │
│     is_pending=true  → "物流信息更新中"                         │
│     events=[]        → "暂无物流轨迹"                           │
│     is_delivered     → "已签收" (绿色)                          │
│     is_exception     → "异常" (红色)                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 5 涉及文件

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `services/tracking/service.py` | 修改 | 添加 `get_tracking_info_with_auto_register()` |
| `products/ai_chatbot/handlers/tracking.py` | 修改 | 调用新方法，传递承运商 |
| `services/tracking/client.py` | 修改 | 扩展承运商映射 |
| `ChatMessage.vue` | 修改 | 优化错误状态显示 |
| `.env` | 修改 | 添加 SMTP 配置说明 |

---

## v1.0 架构（已完成）

---

## 配置信息

| 配置项 | 值 | 说明 |
|--------|-----|------|
| API 版本 | V2.4 | 17track 最新 API 版本 |
| API URL | `https://api.17track.net/track/v2.4` | API 基础地址 |
| API Key | 已配置 (.env) | `TRACK17_API_KEY` |
| Webhook URL | `https://api.fiido.com/webhook/17track` | 待 Phase 2 实现后配置 |

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         Products 产品层                          │
│                                                                 │
│  ┌──────────────────┐          ┌──────────────────┐            │
│  │   ai_chatbot     │          │   notification   │            │
│  │  (物流轨迹展示)   │          │  (物流状态通知)   │            │
│  └────────┬─────────┘          └────────┬─────────┘            │
│           │                             │                       │
├───────────┴─────────────────────────────┴───────────────────────┤
│                         Services 服务层                          │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   tracking   │  │   shopify    │  │    email     │          │
│  │ (17track API)│  │  (订单数据)   │  │  (邮件发送)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                     Infrastructure 基础设施层                    │
│                                                                 │
│  ┌────────┐  ┌────────┐  ┌────────┐                           │
│  │database│  │  redis │  │security│                           │
│  └────────┘  └────────┘  └────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 模块依赖

```
products/notification
    ├── services/tracking      # 17track API 封装
    ├── services/shopify       # 订单数据查询
    └── services/email         # 邮件发送

products/ai_chatbot
    ├── services/tracking      # 物流轨迹查询
    └── services/shopify       # 订单数据查询

services/tracking
    └── infrastructure/database  # 运单注册记录存储
```

---

## 数据流

### Webhook 推送流程

```
Shopify 发货
    │
    ▼
notification/routes.py
POST /webhook/shopify
    │
    ▼
handlers/shopify_handler.py
handle_fulfillment_create()
    │
    ▼
services/tracking/service.py
register_order_tracking()
    │
    ▼
services/tracking/client.py
17track API 注册运单
    │
    ▼
database: tracking_registrations 表
保存运单→订单映射
```

### 状态通知流程

```
17track 状态变更推送
    │
    ▼
notification/routes.py
POST /webhook/17track
    │
    ▼
handlers/tracking_handler.py
handle_status_change()
    │
    ├─ 异常状态 → handle_exception()
    └─ 签收状态 → handle_delivered()
    │
    ▼
handlers/notification_sender.py
send_xxx_notice()
    │
    ▼
services/email/service.py
发送邮件
    │
    ▼
database: notification_records 表
记录发送状态
```

### AI 客服轨迹查询流程

```
前端点击「查看物流」
    │
    ▼
GET /api/tracking/{tracking_number}
    │
    ▼
services/tracking/service.py
get_tracking_events()
    │
    ▼
services/tracking/client.py
17track API 查询轨迹
    │
    ▼
返回 events[] 数组
    │
    ▼
前端展示时间线
```

---

## 文件结构

*随开发进度更新*

### services/tracking/

| 文件 | 用途 | 状态 |
|------|------|------|
| `__init__.py` | 模块导出 | ✅ 完成 |
| `README.md` | 服务规范 | ✅ 完成 |
| `client.py` | 17track API V2.4 客户端 | ✅ 完成 |
| `models.py` | 数据模型 | ✅ 完成 |
| `webhook.py` | Webhook 数据解析 | ✅ 完成 |
| `service.py` | 业务逻辑层 | ✅ 完成 |

---

## 已完成文件详情

### services/tracking/client.py

**用途:** 封装 17track API V2.4 调用

**主要类/函数:**
- `Track17Client` - API 客户端类
  - `register_tracking()` - 注册运单
  - `register_batch()` - 批量注册
  - `get_tracking_info()` - 查询物流轨迹
  - `retrack()` - 重新追踪
  - `stop_tracking()` - 停止追踪
  - `change_carrier()` - 更改承运商
- `Track17Error` - API 错误异常类
- `get_track17_client()` - 获取默认客户端实例

**跨模块交互:**
- 被调用: `services/tracking/service.py`（待实现）
- 被调用: `products/notification/handlers/`（待实现）
- 被调用: `products/ai_chatbot/`（物流轨迹查询，待实现）

---

### services/tracking/models.py

**用途:** 定义物流追踪相关的数据模型

**主要类/枚举:**
- `TrackingStatus` - 主状态枚举（9 种）
  - NotFound、InfoReceived、InTransit、PickUp、OutForDelivery
  - Undelivered、Delivered、Alert、Expired
  - 支持 `from_code()` 从状态码转换
  - 支持 `.zh` 获取中文名称
  - 支持 `.is_final` / `.is_exception` 判断
- `TrackingSubStatus` - 子状态枚举（详细状态）
- `TrackingEvent` - 物流事件
  - 时间戳、状态、地点、描述
  - 支持 `from_17track_event()` 从 API 数据创建
- `CarrierInfo` - 承运商信息
- `TrackingInfo` - 完整物流信息
  - 运单号、承运商、状态、事件列表
  - 支持 `from_17track_response()` 从 API 响应创建
- `WebhookEvent` - Webhook 推送事件

**跨模块交互:**
- 被使用: `services/tracking/webhook.py`
- 被使用: `services/tracking/service.py`（待实现）
- 被使用: `products/notification/handlers/`（待实现）

---

### services/tracking/webhook.py

**用途:** 解析和验证 17track Webhook 推送数据

**主要函数:**
- `verify_webhook_signature(payload, signature, secret)` - 验证 HMAC-SHA256 签名
- `parse_17track_push(data)` - 解析单条推送，返回 WebhookEvent
- `parse_17track_batch_push(data)` - 解析批量推送，返回 List[WebhookEvent]
- `is_delivery_event(event)` - 判断是否为签收事件
- `is_exception_event(event)` - 判断是否为异常事件
- `get_exception_type(event)` - 获取异常类型（address_issue/customs_issue/lost 等）

**跨模块交互:**
- 依赖: `services/tracking/models.py`
- 被调用: `products/notification/routes.py`（待实现）
- 被调用: `products/notification/handlers/tracking_handler.py`（待实现）

---

### services/tracking/service.py

**用途:** 封装业务逻辑，提供统一的物流追踪接口

**主要类:**
- `TrackingService` - 物流追踪服务
  - `register_order_tracking(order_id, tracking_number, carrier)` - 注册订单物流追踪
  - `get_tracking_events(tracking_number)` - 获取物流事件列表
  - `get_tracking_info(tracking_number)` - 获取完整物流信息
  - `find_order_by_tracking(tracking_number)` - 通过运单号查找订单
  - `get_status(tracking_number)` - 获取当前状态
  - `is_delivered(tracking_number)` - 检查是否已签收
  - `has_exception(tracking_number)` - 检查是否有异常
  - `clear_cache(tracking_number)` - 清除缓存
- `get_tracking_service()` - 获取默认服务实例

**缓存策略:**
- 优先使用 Redis 缓存
- Redis 不可用时降级到内存缓存
- 物流信息缓存 6 小时（可配置）
- 运单-订单映射缓存 7 天

**跨模块交互:**
- 依赖: `services/tracking/client.py`、`services/tracking/models.py`
- 依赖: `infrastructure/database/connection.py`（Redis 客户端）
- 被调用: `products/notification/handlers/`（待实现）
- 被调用: `products/ai_chatbot/`（物流轨迹查询，待实现）

---

### products/notification/

| 文件 | 用途 |
|------|------|
| `main.py` | 独立模式入口 |
| `routes.py` | Webhook 端点 |
| `config.py` | 配置 |
| `handlers/shopify_handler.py` | Shopify 事件处理 |
| `handlers/tracking_handler.py` | 17track 推送处理 |
| `handlers/notification_sender.py` | 通知发送器 |
| `templates/*.html` | 邮件模板 |

### 修改的文件

| 文件 | 修改内容 |
|------|----------|
| `products/ai_chatbot/frontend/src/components/ChatMessage.vue` | 添加物流轨迹展示 |
| `products/ai_chatbot/handlers/tracking.py` | 物流轨迹查询 API |
| `products/ai_chatbot/routes.py` | 注册 tracking 路由 |
| `backend.py` | 注册 notification 路由 |
| `.env` | 添加 17track 配置 |

---

## Phase 3 新增文件详情

### products/ai_chatbot/handlers/tracking.py

**用途:** 提供物流轨迹查询 API，供前端展示物流时间线

**主要端点:**
- `GET /api/tracking/{tracking_number}` - 查询完整物流轨迹
- `GET /api/tracking/{tracking_number}/status` - 查询物流状态（轻量接口）

**响应模型:**
- `TrackingResponse` - 完整物流信息响应
- `TrackingEventResponse` - 单个物流事件
- `CarrierResponse` - 承运商信息

**跨模块交互:**
- 依赖: `services/tracking/service.py`
- 被调用: `products/ai_chatbot/frontend/ChatMessage.vue`

---

### products/ai_chatbot/frontend/src/components/ChatMessage.vue

**用途:** AI 客服聊天消息组件，包含可折叠物流时间线

**新增功能:**
- `trackingDataMap` - 存储物流轨迹数据
- `expandedTrackings` - 存储展开状态
- `fetchTrackingData()` - 调用 API 获取物流轨迹
- `toggleTracking()` - 切换展开/收起
- `updateTimelineDOM()` - 更新时间线 DOM

**交互流程:**
1. 商品卡片显示「查看物流」按钮
2. 点击展开时间线，显示加载动画
3. 调用 `/api/tracking/{tracking_number}` 获取数据
4. 渲染时间线事件列表
5. 再次点击收起
