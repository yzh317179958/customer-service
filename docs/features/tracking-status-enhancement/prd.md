# 物流状态增强 - 17track 数据补充

> **文档类型**：产品需求文档
> **创建日期**：2025-12-24
> **版本**：v1.0

---

## 一、问题背景

### 1.1 现象描述

用户查询订单时，部分商品的物流状态显示不准确：

- 17track 显示包裹已签收（Delivered）
- 商品卡片却显示"已发货"而非"已收货"

### 1.2 具体案例

**问题订单：DE10091**

- 商品：Frontkorb für E-Gravel C22/C11
- 承运商：YUNWAY
- 运单号：YT2418521272165525
- 17track 状态：Delivered（已签收，2024-07-03）
- Shopify `shipment_status`：null
- 前端显示：已发货（错误）

**对比订单：UK22088**

- 同样是 YUNWAY 承运商
- Shopify `shipment_status`：delivered（2025-12-23 更新）
- 前端显示：已收货（正确）

### 1.3 根本原因

1. **Shopify API 局限性**：

   - `fulfillment.status = "success"` 仅表示"发货记录创建成功"，不是送达状态
   - `fulfillment.shipment_status` 才是真正的物流送达状态
   - 旧订单的 `shipment_status` 字段不会被 Shopify 自动更新
2. **当前逻辑缺陷**：

   - 当 `shipment_status` 为 null 时，系统默认显示"已发货"
   - 没有利用 17track 的准确送达数据来补充 Shopify 的缺失信息

---

## 二、需求目标

### 2.1 核心目标

**让物流状态显示与实际送达情况一致**，用户体验优先。

### 2.2 具体目标

1. 当 Shopify `shipment_status` 为空时，使用 17track 数据补充
2. 17track 显示已送达（Delivered），商品状态应显示"已收货"
3. 保持现有逻辑的向后兼容性
4. 不影响系统性能（合理使用缓存）

---

## 三、解决方案

### 3.1 方案概述

在订单详情解析时，对于 `shipment_status` 为空的商品：

1. 检查是否有运单号
2. 有运单号则查询 17track 缓存
3. 17track 显示 Delivered，则设置 `delivery_status = "success"`

### 3.2 状态判断优先级（增强版）

```
1. 退款状态（最高优先级）
   └── returned / refunded / cancelled

2. Shopify 物流运输状态（次优先级）
   └── shipment_status = delivered → 已收货
   └── shipment_status = in_transit → 运输中

3. 【新增】17track 物流状态（Shopify 无数据时补充）
   └── 17track status = Delivered → 已收货
   └── 17track status = InTransit → 运输中

4. Shopify 发货状态（最低优先级）
   └── fulfillment_status = fulfilled → 已发货
   └── fulfillment_status = null → 待发货
```

### 3.3 技术要点

1. **只查缓存，不发起新请求**：

   - 17track 查询可能耗时，不应阻塞订单查询
   - 只读取已缓存的 17track 数据
   - 如果缓存不存在，保持原有逻辑
2. **异步预加载**：

   - 订单查询时，后台异步预加载所有运单的 17track 数据
   - 下次查询时缓存可用
3. **缓存配置**：

   - 17track 缓存 TTL：6 小时
   - 订单详情缓存 TTL：48 小时

---

## 四、涉及模块


| 模块                | 改动             | 文件       |
| ------------------- | ---------------- | ---------- |
| services/shopify    | 订单解析逻辑增强 | client.py  |
| services/tracking   | 提供缓存查询接口 | service.py |
| products/ai_chatbot | 无改动           | -          |

---

## 五、验收标准

1. DE10091 订单的 "Frontkorb" 商品显示"已收货"
2. 其他正常订单不受影响
3. 订单查询响应时间不明显增加（<100ms）
4. 17track 缓存不存在时，保持原有"已发货"显示

---

## 六、风险与注意事项

### 6.1 性能风险

- **风险**：17track 查询可能导致订单查询变慢
- **缓解**：只读缓存，不发起新请求；异步预加载

### 6.2 一致性风险

- **风险**：17track 数据与 Shopify 数据不一致
- **缓解**：17track 只用于补充 Shopify 缺失的数据，不覆盖已有数据

### 6.3 缓存失效

- **风险**：17track 缓存过期后状态可能暂时不准确
- **缓解**：用户点击"查看物流"会刷新缓存
