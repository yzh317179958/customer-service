# 17track 物流追踪集成 - 进度追踪

> **创建日期**：2025-12-22
> **当前状态**：开发中

---

## 进度概览

| 阶段 | 状态 | 完成步骤 |
|------|------|----------|
| Phase 1: services/tracking | ✅ 完成 | 4/4 |
| Phase 2: products/notification | ✅ 完成 | 6/6 |
| Phase 3: ai_chatbot 扩展 | ⏳ 开发中 | 2/3 |
| Phase 4: 集成与部署 | 待开始 | 0/2 |

---

## 开发记录

### 2025-12-22

**完成内容**：
- 创建跨模块文档结构 `docs/features/17track-integration/`
- 编写 PRD 文档
- 编写实施计划

**下一步**：
- 开始 Phase 1 Step 1.1：创建 services/tracking 模块结构

---

## Step 1.1: 创建模块结构

**完成时间:** 2025-12-22
**版本号:** v7.6.0
**所属模块:** services/tracking

**完成内容:**
- 创建 `services/tracking/` 目录
- 创建 `__init__.py` 模块导出
- 创建 `README.md` 服务规范文档

**测试结果:**
- ✅ 目录结构检查通过

---

## Step 1.2: 实现 17track API 客户端

**完成时间:** 2025-12-22
**版本号:** v7.6.0
**所属模块:** services/tracking

**完成内容:**
- 创建 `services/tracking/client.py` - 17track API V2.4 客户端
- 实现 `Track17Client` 类，包含：
  - `register_tracking()` - 注册运单
  - `register_batch()` - 批量注册
  - `get_tracking_info()` - 查询物流轨迹
  - `retrack()` - 重新追踪
  - `stop_tracking()` - 停止追踪
  - `change_carrier()` - 更改承运商
- 配置 `.env` 中的 17track 配置项

**配置信息:**
- API Key: `B5670455769EB01CC5B5A5685A6F408E`（已配置）
- API URL: `https://api.17track.net/track/v2.4`
- Webhook URL: `https://api.fiido.com/webhook/17track`（已在 17track 控制台配置，端点待 Phase 2 实现）

**测试结果:**
- ✅ 模块导入正常
- ✅ 配置读取正常（API Key、API URL）
- ✅ 承运商代码映射正常（Royal Mail: 21051, DPD: 100143）
- ✅ API 真实调用测试通过（运单 TEST123456789 注册成功）

**备注:**
- Webhook URL 已在 17track 控制台配置，但端点尚未实现（Phase 2）
- 17track 会推送到该 URL，目前会返回 404，不影响运单注册和查询功能

---

*后续开发记录将按步骤追加*

---

## Step 1.3: 实现数据模型和 Webhook 解析

**完成时间:** 2025-12-23
**版本号:** v7.6.0
**所属模块:** services/tracking

**完成内容:**
- 创建 `services/tracking/models.py` - 数据模型定义
  - `TrackingStatus` - 9 种主状态枚举（NotFound → Expired）
  - `TrackingSubStatus` - 子状态枚举（详细物流状态）
  - `TrackingEvent` - 单个物流事件
  - `CarrierInfo` - 承运商信息
  - `TrackingInfo` - 完整物流信息
  - `WebhookEvent` - Webhook 推送事件
- 创建 `services/tracking/webhook.py` - Webhook 解析
  - `verify_webhook_signature()` - 验证签名
  - `parse_17track_push()` - 解析单条推送
  - `parse_17track_batch_push()` - 解析批量推送
  - `is_delivery_event()` - 判断签收事件
  - `is_exception_event()` - 判断异常事件
  - `get_exception_type()` - 获取异常类型
- 更新 `__init__.py` 导出所有模型和函数

**测试结果:**
- ✅ 模块导入正常
- ✅ 状态枚举测试通过（状态码转换、中文名称）
- ✅ Webhook 解析测试通过（运输中、签收、异常三种场景）
- ✅ 事件判断函数测试通过

**数据模型说明:**
- 基于 17track API V2.4 数据格式设计
- 支持从状态码转换为枚举（`from_code()`）
- 支持获取中文名称（`.zh` 属性）
- 支持判断终态和异常状态

---

*下一步: Step 1.4 实现 service.py 业务逻辑层*

---

## Step 1.4: 实现服务层业务逻辑

**完成时间:** 2025-12-23
**版本号:** v7.6.0
**所属模块:** services/tracking

**完成内容:**
- 创建 `services/tracking/service.py` - 业务逻辑层
- 实现 `TrackingService` 类，包含：
  - `register_order_tracking()` - 注册订单物流追踪
  - `get_tracking_events()` - 获取物流事件列表
  - `get_tracking_info()` - 获取完整物流信息
  - `find_order_by_tracking()` - 通过运单号查找订单
  - `get_status()` - 获取运单当前状态
  - `is_delivered()` - 检查是否已签收
  - `has_exception()` - 检查是否有异常
  - `clear_cache()` - 清除缓存
- 实现缓存机制（Redis 优先，内存降级）
- 实现运单-订单映射存储
- 更新 `__init__.py` 导出服务

**测试结果:**
- ✅ 模块导入正常
- ✅ 运单注册成功
- ✅ 映射查询正常
- ✅ 物流查询正常（测试运单无事件）
- ✅ 辅助函数正常
- ✅ 缓存清除正常

**备注:**
- 缓存默认使用 `SHOPIFY_CACHE_TRACKING` 配置（6 小时）
- 映射缓存 7 天
- 支持 Redis 和内存双模式

---

## Phase 1 完成总结

**完成时间:** 2025-12-23
**文件清单:**
```
services/tracking/
├── __init__.py      # 模块导出
├── README.md        # 服务规范
├── client.py        # 17track API 客户端
├── models.py        # 数据模型
├── webhook.py       # Webhook 解析
└── service.py       # 业务逻辑层
```

**核心能力:**
- 17track API V2.4 完整封装
- 运单注册、轨迹查询、状态监控
- Webhook 推送解析和签名验证
- 运单-订单映射管理
- 缓存机制（Redis/内存）

**下一步:** Phase 2 开发 products/notification 模块

---

## Phase 2: products/notification 模块

### Step 2.1: 创建模块结构

**完成时间:** 2025-12-23
**所属模块:** products/notification

**完成内容:**
- 创建 `config.py` - 配置管理（NotificationConfig, 承运商分类, 预售判断）
- 创建 `main.py` - 独立模式入口
- 创建 `handlers/__init__.py` - 处理器模块
- 创建 `templates/` 目录

---

### Step 2.2: 实现 Webhook 路由

**完成时间:** 2025-12-23
**所属模块:** products/notification

**完成内容:**
- 创建 `routes.py` - Webhook 端点
  - `POST /webhook/shopify` - Shopify 发货 Webhook
  - `POST /webhook/17track` - 17track 状态推送
  - `GET /webhook/health` - 健康检查
- HMAC-SHA256 签名验证

---

### Step 2.3: 实现 Shopify Webhook 处理

**完成时间:** 2025-12-23
**所属模块:** products/notification

**完成内容:**
- 创建 `handlers/shopify_handler.py`
- 实现 `handle_fulfillment_create()` - 处理发货事件
- 实现运单注册到 17track
- 实现拆包裹检测和预售商品检测
- 站点域名映射（fiidouk → uk）

---

### Step 2.4: 实现 17track 推送处理

**完成时间:** 2025-12-23
**所属模块:** products/notification

**完成内容:**
- 创建 `handlers/tracking_handler.py`
- 实现 `handle_tracking_update()` - 处理状态推送
- 实现签收事件处理
- 实现异常事件分类和处理

---

### Step 2.5: 创建邮件模板

**完成时间:** 2025-12-23
**所属模块:** products/notification

**完成内容:**
- `templates/split_package.html` - 拆包裹通知
- `templates/presale_shipped.html` - 预售发货通知
- `templates/exception_alert.html` - 异常警报（支持 7 种异常类型）
- `templates/delivery_confirm.html` - 签收确认（含评价引导）

---

### Step 2.6: 实现通知发送器

**完成时间:** 2025-12-23
**所属模块:** products/notification

**完成内容:**
- 创建 `handlers/notification_sender.py`
  - `render_template()` - Jinja2 模板渲染
  - `send_split_package_notice()` - 拆包裹通知
  - `send_presale_notice()` - 预售发货通知
  - `send_exception_alert()` - 异常警报
  - `send_delivery_confirm()` - 签收确认
- 集成 services/email 邮件发送
- 更新所有 handlers 调用通知发送器

**测试结果:**
- ✅ 4 个邮件模板检查通过
- ✅ 所有模板渲染成功
- ✅ handlers 模块导入成功

---

## Phase 2 完成总结

**完成时间:** 2025-12-23
**文件清单:**
```
products/notification/
├── __init__.py              # 模块导出
├── main.py                  # 独立模式入口
├── config.py                # 配置管理
├── routes.py                # Webhook 路由
├── handlers/
│   ├── __init__.py          # 处理器导出
│   ├── shopify_handler.py   # Shopify 事件
│   ├── tracking_handler.py  # 17track 推送
│   └── notification_sender.py # 通知发送
├── templates/
│   ├── split_package.html
│   ├── presale_shipped.html
│   ├── exception_alert.html
│   └── delivery_confirm.html
└── memory-bank/
```

**核心能力:**
- Shopify 发货 Webhook 接收和处理
- 17track 状态推送接收和处理
- 拆包裹检测和通知
- 预售商品发货通知
- 签收确认邮件（含评价引导）
- 异常警报邮件（7 种类型）

**下一步:** Phase 3 扩展 ai_chatbot 物流轨迹展示

---

## Phase 3: ai_chatbot 物流轨迹展示

### Step 3.1: 新增物流轨迹查询 API

**完成时间:** 2025-12-23
**所属模块:** products/ai_chatbot

**完成内容:**
- 创建 `products/ai_chatbot/handlers/tracking.py` - 物流轨迹查询 handler
- 实现 `GET /api/tracking/{tracking_number}` - 查询完整物流轨迹
- 实现 `GET /api/tracking/{tracking_number}/status` - 查询物流状态（轻量接口）
- 更新 `routes.py` 注册新路由
- 定义响应模型：TrackingResponse、TrackingEventResponse、CarrierResponse

**API 响应格式:**
```json
{
  "tracking_number": "AB123456789GB",
  "carrier": {"code": 21051, "name": "Royal Mail"},
  "current_status": "InTransit",
  "current_status_zh": "运输中",
  "is_delivered": false,
  "is_exception": false,
  "event_count": 5,
  "events": [
    {"timestamp": "...", "status": "...", "location": "...", "description": "..."}
  ]
}
```

**测试结果:**
- ✅ tracking handler 导入成功
- ✅ routes 导入成功
- ✅ 路由注册正常（/tracking/{tracking_number}、/tracking/{tracking_number}/status）
- ✅ tracking 服务获取成功

---

*下一步: Step 3.2 前端添加可折叠物流时间线*
