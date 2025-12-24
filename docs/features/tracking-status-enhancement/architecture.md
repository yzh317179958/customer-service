# 物流状态增强 - 架构说明

> **文档类型**：架构说明
> **创建日期**：2025-12-24
> **对应计划**：`implementation-plan.md`

---

## 数据流图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         订单查询流程                                 │
└─────────────────────────────────────────────────────────────────────┘

用户查询订单
     │
     ▼
┌─────────────────┐
│ ShopifyClient   │
│ search_order    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    _parse_order_detail()                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  遍历 line_items:                                                   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 退款状态判断                                                  │   │
│  │   └── is_refunded? → returned/refunded/cancelled            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                          │ 否                                       │
│                          ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Shopify shipment_status 判断                                 │   │
│  │   └── delivered? → success (已收货)                          │   │
│  │   └── in_transit? → in_transit (运输中)                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                          │ 无数据                                   │
│                          ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 【新增】17track 缓存查询                                      │   │
│  │                                                              │   │
│  │   tracking_number 存在?                                      │   │
│  │      │                                                       │   │
│  │      ▼                                                       │   │
│  │   TrackingService.get_cached_status()                        │   │
│  │      │                                                       │   │
│  │      ├── DELIVERED → success (已收货)                        │   │
│  │      ├── IN_TRANSIT → in_transit (运输中)                    │   │
│  │      └── None/其他 → 继续原逻辑                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                          │                                          │
│                          ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Shopify fulfillment_status 判断                              │   │
│  │   └── fulfilled → 已发货                                     │   │
│  │   └── null → 待发货                                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 模块依赖

```
services/shopify/client.py
         │
         │ 依赖
         ▼
services/tracking/service.py
         │
         │ 依赖
         ▼
infrastructure/database/connection.py (Redis)
```

---

## 文件改动清单

### services/tracking/service.py

**新增方法：**

1. `get_cached_status(tracking_number)` (第 434-473 行)
   - 异步方法，只读 Redis/内存缓存
   - 返回 `TrackingStatus` 枚举值或 `None`
   - 用途：获取已缓存的 17track 物流状态

2. `get_cached_status_sync(tracking_number)` (第 475-509 行)
   - 同步方法，只读内存缓存（不查 Redis）
   - 执行时间 < 1ms
   - 用途：在同步方法中快速获取物流状态

### services/shopify/client.py

**重构方法：**

1. `_parse_order_detail(order)` (第 612-619 行)
   - 保留同步版本，向后兼容
   - 调用 `_parse_order_detail_impl(order, track17_service=None)`

2. `_parse_order_detail_with_tracking(order)` (第 621-637 行)
   - 新增异步版本，支持 17track 缓存查询
   - 获取 TrackingService 并传入核心实现

3. `_parse_order_detail_impl(order, track17_service)` (第 639-889 行)
   - 核心实现，接受可选的 track17_service 参数
   - 状态判断逻辑增强（第 779-805 行）

**调用方更新：**

- `get_order_detail()` 改用 `_parse_order_detail_with_tracking()`
- `search_order_by_number()` 改用 `_parse_order_detail_with_tracking()`

---

## 状态判断优先级

```
1. 退款状态（最高优先级）
   └── returned / refunded / cancelled / expired

2. Shopify shipment_status（次优先级）
   └── delivered → success (已收货)
   └── in_transit → in_transit (运输中)
   └── out_for_delivery → out_for_delivery (派送中)
   └── failure → failure (投递失败)

3. 【新增】17track 缓存状态（Shopify 无数据时补充）
   └── DELIVERED → success (已收货)
   └── IN_TRANSIT → in_transit (运输中)
   └── OUT_FOR_DELIVERY → out_for_delivery (派送中)
   └── ALERT/UNDELIVERED → failure (投递失败)

4. Shopify fulfillment_status（最低优先级）
   └── fulfilled → 已发货
   └── null → 待发货
```

---

## 性能说明

- 缓存查询执行时间：< 1ms（内存缓存）/ < 10ms（Redis 缓存）
- 不发起 17track API 请求，不阻塞订单查询
- 缓存 TTL：6 小时（由用户点击"查看物流"时刷新）
