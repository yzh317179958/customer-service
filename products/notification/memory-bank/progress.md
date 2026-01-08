# 物流通知 - 开发进度追踪

> **模块**：物流通知（Notification）
> **目标**：物流状态监控与自动通知
> **开始日期**：2025-12-23
> **当前状态**：基础链路完成，易仓技术调研完成，待业务确认后开始 Phase 4

---

## 进度概览

| 步骤 | 内容 | 状态 |
|------|------|------|
| Step 2.1 | 创建模块结构 | ✅ 完成 |
| Step 2.2 | 实现 Webhook 路由 | ✅ 完成 |
| Step 2.3 | 实现 Shopify Webhook 处理 | ✅ 完成 |
| Step 2.4 | 实现 17track 推送处理 | ✅ 完成 |
| Step 2.5 | 创建邮件模板 | ✅ 完成 |
| Step 2.6 | 实现通知发送器 | ✅ 完成 |
| Step 3.1 | 运单映射持久化（PG） | ⏳ 待开始 |
| Step 3.2 | 通知记录持久化（PG） | ⏳ 待开始 |
| Step 3.3 | 失败重试/Outbox | ⏳ 待开始 |
| Step 4.1 | 易仓接口能力调研 | ✅ 完成 |
| Step 4.2 | 新增服务层适配 | ⏳ 待业务确认 |

---

## Step 2.1: 创建模块结构

**完成时间:** 2025-12-23
**版本号:** v7.6.0

**完成内容:**
- 创建 `config.py` - 配置管理
  - NotificationConfig 配置类
  - 承运商分类和超时阈值
  - 预售 SKU 判断
- 创建 `main.py` - 独立模式入口
- 创建 `handlers/__init__.py` - 处理器模块
- 创建 `templates/` 目录
- 更新 `__init__.py` 模块导出
- 更新 memory-bank 文档

**测试结果:**
- ✅ 模块导入成功
- ✅ 配置加载正常
- ✅ 承运商超时判断正确
- ✅ 预售 SKU 判断正确
- ✅ 目录结构完整

---

## Step 2.2: 实现 Webhook 路由

**完成时间:** 2025-12-23

**完成内容:**
- 创建 `routes.py` - Webhook 端点
  - `POST /webhook/shopify` - Shopify 发货 Webhook
  - `POST /webhook/17track` - 17track 状态推送
  - `GET /webhook/health` - 健康检查
- HMAC-SHA256 签名验证
- 更新 `main.py` 注册路由

**测试结果:**
- ✅ Webhook 路由注册成功
- ✅ 请求参数正确解析

---

## Step 2.3: 实现 Shopify Webhook 处理

**完成时间:** 2025-12-23

**完成内容:**
- 创建 `handlers/shopify_handler.py`
  - `handle_fulfillment_create()` - 处理发货事件
  - `handle_order_create()` - 处理订单创建
  - `_register_tracking()` - 注册运单到 17track
  - `_check_split_package()` - 检测拆包裹
  - `_detect_presale_items()` - 检测预售商品
  - `_get_site_code()` - 站点域名映射

**测试结果:**
- ✅ 站点代码映射正确
- ✅ 预售商品检测正确
- ✅ 发货事件处理流程正常

---

## Step 2.4: 实现 17track 推送处理

**完成时间:** 2025-12-23

**完成内容:**
- 创建 `handlers/tracking_handler.py`
  - `handle_tracking_update()` - 处理状态推送
  - `_process_event()` - 处理单个事件
  - `handle_delivered()` - 处理签收事件
  - `handle_exception()` - 处理异常事件
  - `_get_order_info()` - 获取订单信息
  - `handle_status_change()` - 处理状态变更

**测试结果:**
- ✅ 签收事件识别正确
- ✅ 异常事件分类正确
- ✅ 批量事件处理正常

---

## Step 2.5: 创建邮件模板

**完成时间:** 2025-12-23

**完成内容:**
- 创建 `templates/split_package.html` - 拆包裹通知
- 创建 `templates/presale_shipped.html` - 预售发货通知
- 创建 `templates/exception_alert.html` - 异常警报
  - 支持多种异常类型：lost, damaged, address_issue, customs_issue, no_one_home, refused, returned
- 创建 `templates/delivery_confirm.html` - 签收确认
  - 包含评价引导和支持链接

**测试结果:**
- ✅ 所有模板文件创建成功
- ✅ 模板使用 Jinja2 语法
- ✅ 响应式邮件设计

---

## Step 2.6: 实现通知发送器

**完成时间:** 2025-12-23

**完成内容:**
- 创建 `handlers/notification_sender.py`
  - `render_template()` - Jinja2 模板渲染
  - `send_split_package_notice()` - 拆包裹通知
  - `send_presale_notice()` - 预售发货通知
  - `send_exception_alert()` - 异常警报
  - `send_delivery_confirm()` - 签收确认
  - `check_templates()` - 模板检查
- 更新 `handlers/shopify_handler.py`
  - 添加 `_send_split_package_notification()` 辅助函数
  - 添加 `_send_presale_notification()` 辅助函数
  - 添加 `_generate_tracking_url()` 生成追踪链接
- 更新 `handlers/tracking_handler.py`
  - 集成签收确认发送
  - 集成异常警报发送
- 更新 `handlers/__init__.py` 导出所有函数

**测试结果:**
- ✅ 4 个邮件模板检查通过
- ✅ 所有模板渲染成功
- ✅ handlers 模块导入成功
- ✅ 函数类型正确（async functions）

---

## Step 4.1: 易仓接口能力调研

**完成时间:** 2026-01-08

**调研结论:**

### 重要发现

| 发现 | 说明 |
|------|------|
| **无 Webhook 推送** | 易仓开放平台采用"主动拉取 API"模式，暂无公开 Webhook 机制 |
| **采用轮询方案** | 需定时轮询 `getOrderList` API 获取状态更新 |
| **签名算法已明确** | MD5：参数按 key 字典序排序 → 拼接 → 追加 app_secret → MD5 大写 |
| **时间戳有效期** | 1 分钟，需注意服务器时间同步 |

### 已明确的技术细节

| 项目 | 详情 |
|------|------|
| API 地址 | `http://openapi-web.eccang.com/openApi/api/unity` |
| 签名类型 | MD5（默认） |
| 时间戳 | 毫秒级，有效期 1 分钟 |
| 防重放 | nonce_str 随机字符串 |
| 增量查询 | 按 `modify_date` 筛选 |
| 幂等策略 | `reference_no + status` 组合去重 |

### 订单相关 API

| 接口 | 用途 |
|------|------|
| `getOrder` | 查询单个订单详情 |
| `getOrderList` | 获取订单列表（支持分页、时间筛选） |
| `getOrderStatus` | 获取订单状态 |
| `getShippingMethod` | 获取配送方式列表 |

### 关键字段

| 字段 | 用途 |
|------|------|
| `reference_no` | 订单关联 |
| `shipper_hawbcode` | 运单追踪 |
| `shipping_method` | **可用于识别售后订单** |
| `mail_cargo_type` | **可用于识别配件订单** |
| `warehouse_code` | **可用于识别售后订单** |
| `status` | 状态变更检测（P/S/C/E） |
| `Consignee.consignee_email` | 通知发送 |
| `modify_date` | 增量查询 |

### 唯一阻塞项

| 事项 | 说明 |
|------|------|
| **售后订单识别字段** | 需业务确认用 `shipping_method` / `warehouse_code` / `mail_cargo_type` 哪个字段 |

**建议操作**：
1. 调用 `getShippingMethod` 获取配送方式列表，识别售后专用代码
2. 或确认售后配件订单统一从哪个仓库发货
3. 或确认 `mail_cargo_type` 的配件类型编码

---

## 待补齐事项（面向业务落地）

- 幂等去重：同一运单同一通知类型只发送一次（以 `notification_records.notification_id` 为权威）
- 落库与可追踪：通知发送必须写入 `notification_records`，便于客服排查与补发
- 运单关联：长期运输场景中，避免仅依赖 Redis/内存映射导致"状态推送找不到订单/邮箱"
- 易仓轮询：落地 `services/yicang` + 定时任务（待业务确认售后订单识别规则）

---

## 跨模块引用

本模块是 **17track 物流追踪集成** 的 Phase 2。

主文档：`docs/features/17track-integration/`

---

## 文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.7 | 2026-01-08 | 完成 Step 4.1 易仓调研，更新所有 memory-bank 文档 |
| v1.6 | 2025-12-23 | 完成 Step 2.6，Phase 2 全部完成 |
| v1.5 | 2025-12-23 | 完成 Step 2.5 邮件模板 |
| v1.4 | 2025-12-23 | 完成 Step 2.4 17track 处理 |
| v1.3 | 2025-12-23 | 完成 Step 2.3 Shopify 处理 |
| v1.2 | 2025-12-23 | 完成 Step 2.2 Webhook 路由 |
| v1.0 | 2025-12-23 | 开始开发，完成 Step 2.1 |
| v0.1 | 2025-12-21 | 创建占位文档 |
