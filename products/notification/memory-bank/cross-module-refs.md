# 跨模块功能引用

> **文档类型**：跨模块功能引用记录
> **所属模块**：products/notification（物流通知）
> **最后更新**：2025-12-23

---

## 说明

本文件记录本模块参与的所有跨模块功能，便于追踪和维护。

每个跨模块功能的完整文档位于 `docs/features/[功能名]/`，本文件仅保存引用和本模块的职责说明。

---

## 参与的跨模块功能

### 17track 物流追踪集成

**主文档**: `docs/features/17track-integration/`

**状态**: ⏳ Phase 5 开发中

**版本历史**:
- v1.0：✅ 已完成（2025-12-23）- Phase 1-4 基础功能
- v2.0：⏳ 开发中 - Phase 5 集成完善

**本模块职责**:
- 接收 Shopify 发货 Webhook
- 自动注册运单到 17track
- 接收 17track 状态推送
- 发送拆包裹/预售/异常/签收通知邮件

**涉及文件**:
| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `routes.py` | 新增 | Webhook 端点 |
| `handlers/shopify_handler.py` | 新增 | Shopify 事件处理 |
| `handlers/tracking_handler.py` | 新增 | 17track 推送处理 |
| `handlers/notification_sender.py` | 新增 | 邮件发送 |
| `templates/*.html` | 新增 | 4 个邮件模板 |

**对接模块**:
- `services/tracking` - 17track API 封装
- `services/shopify` - 订单数据查询
- `services/email` - 邮件发送
- `products/ai_chatbot` - 物流轨迹展示

---

## 快速导航

| 功能 | 主文档 | 状态 | 本模块职责 |
|------|--------|------|-----------|
| 17track 物流集成 | `docs/features/17track-integration/` | ⏳ Phase 5 | Webhook 接收、邮件通知 |
