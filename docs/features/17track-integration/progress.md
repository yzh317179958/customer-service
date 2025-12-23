# 17track 物流追踪集成 - 进度追踪

> **创建日期**：2025-12-22
> **当前状态**：Phase 5 完成
> **当前步骤**：全部完成

---

## 进度概览

| 阶段 | 状态 | 完成步骤 |
|------|------|----------|
| Phase 1: services/tracking | ✅ 完成 | 4/4 |
| Phase 2: products/notification | ✅ 完成 | 6/6 |
| Phase 3: ai_chatbot 扩展 | ✅ 完成 | 3/3 |
| Phase 4: 集成与部署 | ✅ 完成 | 2/2 |
| **Phase 5: 17track 集成完善** | **✅ 完成** | **4/4** |

---

## Phase 5 步骤总览（2025-12-23 新增）

| Step | 标题 | 模块 | 状态 |
|------|------|------|------|
| Step 5.1 | 运单自动注册机制 | services/tracking | ✅ 完成 |
| Step 5.2 | 承运商自动识别 | services/tracking | ✅ 完成 |
| Step 5.3 | 前端错误信息优化 | ai_chatbot/frontend | ✅ 完成 |
| Step 5.4 | SMTP 邮件配置文档 | 文档 | ✅ 完成 |

---

## Phase 5 开发记录

### Step 5.1: 运单自动注册机制

**完成时间:** 2025-12-23
**版本号:** v7.6.1

**完成内容:**
- 在 `TrackingInfo` 模型中添加 `is_pending` 字段
- 在 `TrackingService` 中添加 `get_tracking_info_with_auto_register()` 方法
- 添加 `_async_register()` 异步注册辅助方法
- 修改 `tracking.py` handler 使用新方法
- 在 `TrackingResponse` 中添加 `is_pending` 字段
- API 新增 `order_id` 参数支持自动注册

**修改文件:**
- `services/tracking/models.py` - 添加 is_pending 字段
- `services/tracking/service.py` - 添加自动注册方法
- `products/ai_chatbot/handlers/tracking.py` - 使用新方法

**测试结果:**
- ✅ TrackingInfo.is_pending 字段可用
- ✅ get_tracking_info_with_auto_register 方法存在
- ✅ 未注册运单返回 pending 状态
- ✅ 传入 order_id 触发异步注册

---

### Step 5.2: 承运商自动识别

**完成时间:** 2025-12-23
**版本号:** v7.6.2

**完成内容:**
- 扩展 `CARRIER_CODES` 字典，支持 30+ 承运商
  - UK 承运商：Royal Mail, DPD, Evri, Yodel, Parcelforce 等
  - 欧洲承运商：DHL, GLS, Chronopost, Colissimo, PostNL 等
  - 国际承运商：UPS, FedEx, TNT, USPS
  - 中国承运商：云途、燕文、4PX、顺丰、菜鸟等
- 添加 `CARRIER_NAME_MAP` Shopify 名称 → 标准名称映射
- 添加 `normalize_carrier()` 类方法，标准化承运商名称
- 添加 `get_carrier_code()` 类方法，获取 17track 承运商代码

**修改文件:**
- `services/tracking/client.py` - 扩展承运商映射和标准化方法

**测试结果:**
- ✅ Royal Mail 标准化为 royal mail，代码 21051
- ✅ Hermes/Evri 标准化为 evri，代码 21067
- ✅ YunExpress 标准化为 yunexpress，代码 190012
- ✅ 未知承运商返回 None

---

### Step 5.3: 前端错误信息优化

**完成时间:** 2025-12-23
**版本号:** v7.6.3

**完成内容:**
- 添加 `is_pending` 字段到 TrackingData 接口
- 修改 `fetchTrackingData()` 函数，支持 is_pending 状态
- 修改 `updateTimelineDOM()` 函数，添加 pending 状态显示
- 添加 CSS 样式：`.timeline-pending`（蓝色背景，⏳图标）

**状态显示逻辑:**
| 状态 | 显示内容 |
|------|----------|
| loading | 加载动画 + "加载中..." |
| is_pending=true | ⏳ "物流信息更新中，请稍后刷新" |
| events=[] | 📦 "暂无物流轨迹" |
| error | ⚠️ "暂无物流信息" |
| 正常 | 物流时间线 |

**修改文件:**
- `products/ai_chatbot/frontend/src/components/ChatMessage.vue`

**测试结果:**
- ✅ TypeScript 类型检查通过
- ✅ Vite 构建成功

---

### Step 5.4: SMTP 邮件配置文档

**完成时间:** 2025-12-23
**版本号:** v7.6.4

**完成内容:**
- 创建 `smtp-config.md` 配置文档
- 包含环境变量配置说明
- 包含常用 SMTP 服务商配置（QQ、Gmail、Outlook、SES、SendGrid、阿里云）
- 包含验证配置脚本
- 包含故障排除指南
- 包含生产环境注意事项

**新增文件:**
- `docs/features/17track-integration/smtp-config.md`

**测试结果:**
- ✅ 文档创建成功

---

## Phase 5 完成总结

**完成时间:** 2025-12-23
**版本号:** v7.6.4

### 功能清单

| Step | 功能 | 模块 | 状态 |
|------|------|------|------|
| 5.1 | 运单自动注册机制 | services/tracking | ✅ 完成 |
| 5.2 | 承运商自动识别 | services/tracking | ✅ 完成 |
| 5.3 | 前端错误信息优化 | ai_chatbot/frontend | ✅ 完成 |
| 5.4 | SMTP 邮件配置文档 | 文档 | ✅ 完成 |

### 文件变更清单

**修改文件:**
```
services/tracking/
├── models.py       # 添加 is_pending 字段
├── service.py      # 添加自动注册方法
└── client.py       # 扩展承运商映射

products/ai_chatbot/
├── handlers/tracking.py         # 支持 is_pending
└── frontend/src/components/
    └── ChatMessage.vue          # 前端 pending 状态显示

docs/features/17track-integration/
├── prd.md              # Phase 5 需求
├── implementation-plan.md  # Phase 5 步骤
├── progress.md         # 进度记录
├── architecture.md     # 架构说明
└── smtp-config.md      # SMTP 配置文档（新增）
```

### 核心改进

1. **运单自动注册**: 用户查询未注册运单时，后台自动异步注册到 17track
2. **友好提示**: 前端显示"物流信息更新中，请稍后刷新"而非错误
3. **承运商识别**: 支持 30+ 承运商名称自动标准化
4. **配置文档**: 完整的 SMTP 配置和故障排除指南

---

## Phase 1-4 完成记录

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

---

### Step 3.2: 前端添加可折叠物流时间线

**完成时间:** 2025-12-23
**所属模块:** products/ai_chatbot/frontend

**完成内容:**
- 修改 `ChatMessage.vue` 组件
- 添加物流时间线状态管理（trackingDataMap、expandedTrackings）
- 实现 `fetchTrackingData()` 调用后端 API
- 实现 `toggleTracking()` 展开/收起切换
- 实现 `updateTimelineDOM()` 动态更新时间线内容
- 商品卡片新增「查看物流」按钮
- 时间线展示：状态徽章、事件列表、地点信息
- 支持加载状态、错误状态、空数据状态
- 添加完整 CSS 样式（时间线、按钮、动画）

**交互设计:**
1. 商品卡片底部显示「查看物流 ▼」按钮
2. 点击展开时间线，显示加载动画
3. 加载完成后显示物流轨迹列表
4. 再次点击收起时间线
5. 最新事件高亮显示

**测试结果:**
- ✅ TypeScript 类型检查通过
- ✅ Vite 构建成功
- ✅ 产出文件正常（index.html, index.css, index.js）

---

*下一步: Step 3.3 集成测试完整流程*

---

### Step 3.3: 集成测试完整流程

**完成时间:** 2025-12-23
**所属模块:** 跨模块集成

**测试内容:**
1. tracking 服务导入测试
2. API handler 导入测试
3. 响应模型序列化测试
4. 路由注册验证
5. ai_chatbot 独立模式测试

**测试结果:**
- ✅ tracking 服务初始化成功
- ✅ API handler 导入成功
- ✅ 响应模型序列化正常
- ✅ tracking 路由数量: 5
  - GET /api/tracking/{tracking_number}
  - GET /api/tracking/{tracking_number}/status
  - GET /api/shopify/{site}/orders/{order_id}/tracking
  - GET /api/shopify/tracking
  - GET /api/shopify/orders/{order_id}/tracking
- ✅ AI 客服路由总数: 40

---

## Phase 3 完成总结

**完成时间:** 2025-12-23

**修改文件:**
```
products/ai_chatbot/
├── handlers/tracking.py         # 新增：物流轨迹查询 API
├── routes.py                    # 修改：注册 tracking 路由
└── frontend/
    └── src/components/
        └── ChatMessage.vue      # 修改：添加物流时间线
```

**核心能力:**
- 物流轨迹查询 API（GET /api/tracking/{tracking_number}）
- 物流状态查询 API（GET /api/tracking/{tracking_number}/status）
- 前端可折叠物流时间线组件
- 支持加载状态、错误处理、空数据展示
- 响应式 UI，支持中英文

**交互流程:**
1. 用户在 AI 客服查询订单
2. 商品卡片显示物流状态和「查看物流」按钮
3. 点击按钮展开时间线，调用 /api/tracking API
4. 显示物流轨迹列表，最新事件高亮
5. 再次点击收起时间线

**下一步:** Phase 4 集成与部署

---

## Phase 4: 集成与部署

### Step 4.1: 数据库迁移

**完成时间:** 2025-12-23
**所属模块:** infrastructure/database

**完成内容:**
- 创建 `infrastructure/database/models/tracking.py` - ORM 模型
  - `TrackingRegistrationModel` - 运单注册记录表（16 字段）
  - `NotificationRecordModel` - 通知发送记录表（20 字段）
- 更新 `infrastructure/database/models/__init__.py` - 导出新模型
- 创建迁移文件 `2a8f3b4c5d6e_add_tracking_tables.py`

**表结构:**
```
tracking_registrations (16 字段, 8 索引)
├── tracking_number (唯一索引)
├── carrier_code, carrier_name
├── order_id, order_number, site
├── status, current_tracking_status
├── is_delivered, is_exception
├── register_response, last_event (JSONB)
└── created_at, updated_at, delivered_at

notification_records (20 字段, 10 索引)
├── notification_id (唯一索引)
├── tracking_number, order_id, site
├── notification_type, exception_type
├── to_email, customer_name
├── subject, template_name, template_data
├── status, error_message, retry_count
├── trigger_event, trigger_data
└── created_at, sent_at
```

**测试结果:**
- ✅ ORM 模型导入成功
- ✅ Alembic 迁移执行成功
- ✅ 表结构验证通过（字段、索引完整）

---

## Step 4.2: 环境变量配置和部署

**完成时间:** 2025-12-23
**所属模块:** 跨模块集成

**完成内容:**
- 验证 `.env` 中 17track 配置项完整性
  - `TRACK17_API_KEY` - 已配置
  - `TRACK17_API_URL` - 已配置
  - `TRACK17_WEBHOOK_SECRET` - 暂留空（可选，后续按需配置）
- 启用 notification 模块：`ENABLE_NOTIFICATION=true`
- 验证所有模块导入正常

**测试结果:**
- ✅ 环境变量配置完整
- ✅ notification 模块导入成功（routes, handlers, notification_sender）
- ✅ tracking 服务初始化成功
- ✅ 数据库模型导入成功（TrackingRegistrationModel, NotificationRecordModel）

**备注:**
- WEBHOOK_SECRET 暂留空，17track 推送时不验证签名
- 如需验证签名安全性，后续可在 17track 控制台获取并配置

---

## 🎉 17track 物流追踪集成 - 开发完成

**完成时间:** 2025-12-23
**版本号:** v7.6.0

### 功能清单

| 模块 | 功能 | 状态 |
|------|------|------|
| services/tracking | 17track API V2.4 客户端 | ✅ |
| services/tracking | 运单注册、轨迹查询 | ✅ |
| services/tracking | Webhook 解析、签名验证 | ✅ |
| services/tracking | 缓存机制（Redis/内存） | ✅ |
| products/notification | Shopify 发货 Webhook | ✅ |
| products/notification | 17track 状态推送处理 | ✅ |
| products/notification | 拆包裹/预售通知 | ✅ |
| products/notification | 异常警报/签收确认 | ✅ |
| products/ai_chatbot | 物流轨迹查询 API | ✅ |
| products/ai_chatbot | 前端物流时间线 | ✅ |
| infrastructure/database | 运单注册记录表 | ✅ |
| infrastructure/database | 通知发送记录表 | ✅ |

### 文件清单

```
新增文件:
├── services/tracking/
│   ├── __init__.py
│   ├── README.md
│   ├── client.py           # 17track API 客户端
│   ├── models.py           # 数据模型
│   ├── webhook.py          # Webhook 解析
│   └── service.py          # 业务逻辑层
│
├── products/notification/
│   ├── __init__.py
│   ├── main.py             # 独立模式入口
│   ├── config.py           # 配置管理
│   ├── routes.py           # Webhook 路由
│   ├── handlers/
│   │   ├── shopify_handler.py
│   │   ├── tracking_handler.py
│   │   └── notification_sender.py
│   └── templates/          # 4 个邮件模板
│
├── products/ai_chatbot/handlers/tracking.py  # 物流轨迹 API
│
└── infrastructure/database/
    ├── models/tracking.py                    # ORM 模型
    └── migrations/versions/2a8f3b4c5d6e_*.py  # 迁移脚本

修改文件:
├── .env                                      # ENABLE_NOTIFICATION=true
├── products/ai_chatbot/routes.py             # 注册 tracking 路由
├── products/ai_chatbot/frontend/.../ChatMessage.vue  # 物流时间线
└── infrastructure/database/models/__init__.py        # 导出新模型
```

### 下一步（可选）

1. 配置 Shopify Webhook（发货事件回调）
2. 配置 17track Webhook Secret（安全验证）
3. 部署到生产服务器
