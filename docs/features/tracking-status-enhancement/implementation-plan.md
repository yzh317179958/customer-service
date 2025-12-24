# 物流状态增强 - 实现计划

> **文档类型**：功能实现计划
> **创建日期**：2025-12-24
> **对应 PRD**：`docs/features/tracking-status-enhancement/prd.md`

---

## 一、开发阶段总览

```
┌─────────────────────────────────────────────────────────────────┐
│                        开发阶段                                  │
├─────────────────────────────────────────────────────────────────┤
│  Phase 1: 服务层 - tracking 服务 (services/tracking/)           │
│     └── Step 1: 添加缓存查询接口                                │
│                                                                 │
│  Phase 2: 服务层 - shopify 服务 (services/shopify/)             │
│     └── Step 2: 增强订单解析逻辑                                │
│                                                                 │
│  Phase 3: 集成测试                                              │
│     └── Step 3: 验证 DE10091 订单显示正确                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、详细步骤

### Phase 1: 服务层 - tracking 服务

#### Step 1: 添加缓存查询接口

**目标**：在 TrackingService 中添加只读缓存的状态查询方法

**所属模块**：`services/tracking/`

**具体任务**：
1. 在 `service.py` 中添加 `get_cached_status()` 方法
2. 该方法只读取 Redis/内存缓存，不发起 17track API 请求
3. 返回 TrackingStatus 枚举值或 None

**涉及文件**：
- `services/tracking/service.py` - 添加缓存查询方法

**新增方法**：
```python
async def get_cached_status(
    self,
    tracking_number: str,
) -> Optional[TrackingStatus]:
    """
    获取缓存中的物流状态（只读缓存，不发起 API 请求）

    用于订单解析时快速获取已缓存的物流状态，
    避免阻塞订单查询。

    Args:
        tracking_number: 运单号

    Returns:
        TrackingStatus 枚举值，缓存不存在返回 None
    """
```

**测试方法**：
```bash
cd /home/yzh/AI客服/鉴权
python3 -c "
import asyncio
from services.tracking import get_tracking_service

async def test():
    service = get_tracking_service()
    # 已有缓存的运单
    status = await service.get_cached_status('YT2418521272165525')
    print(f'YUNWAY 运单状态: {status}')
    # 不存在的运单
    status2 = await service.get_cached_status('NONEXISTENT')
    print(f'不存在的运单: {status2}')

asyncio.run(test())
"
```

**验收标准**：
- [ ] 已缓存的运单返回正确的 TrackingStatus
- [ ] 未缓存的运单返回 None
- [ ] 方法执行时间 < 10ms（只读缓存）

---

### Phase 2: 服务层 - shopify 服务

#### Step 2: 增强订单解析逻辑

**目标**：在 `_parse_order_detail` 方法中，当 `shipment_status` 为空时，使用 17track 缓存补充状态

**所属模块**：`services/shopify/`

**具体任务**：
1. 在 `ShopifyClient` 中注入 tracking 服务依赖
2. 修改 `_parse_order_detail` 方法，在状态判断逻辑中添加 17track 补充
3. 只在 `shipment_status` 为空且有运单号时查询 17track 缓存
4. 17track 返回 Delivered，则设置 `delivery_status = "success"`

**涉及文件**：
- `services/shopify/client.py` - 修改订单解析逻辑

**修改位置**：`_parse_order_detail` 方法中的物流状态判断部分（约第 720-746 行）

**现有代码**：
```python
if shipment_status:
    if shipment_status == "delivered":
        delivery_status = "success"
    else:
        delivery_status = shipment_status
elif f_status == "success":
    # 发货成功但没有 shipment_status，说明已发货但物流状态未知
    delivery_status = None  # 让前端显示"已发货"
```

**修改后代码**：
```python
if shipment_status:
    if shipment_status == "delivered":
        delivery_status = "success"
    else:
        delivery_status = shipment_status
elif f_status == "success":
    # 发货成功但没有 shipment_status
    # 尝试从 17track 缓存获取状态
    tracking_number = fulfillment_info.get("tracking_number")
    if tracking_number:
        track17_status = await self._get_track17_cached_status(tracking_number)
        if track17_status == TrackingStatus.DELIVERED:
            delivery_status = "success"  # 17track 显示已送达
        elif track17_status == TrackingStatus.IN_TRANSIT:
            delivery_status = "in_transit"
        else:
            delivery_status = None  # 无缓存或其他状态，保持"已发货"
    else:
        delivery_status = None
```

**注意事项**：
- `_parse_order_detail` 是同步方法，需要改为异步或使用同步缓存接口
- 考虑到 `ShopifyClient` 的设计，可能需要添加同步版本的缓存查询

**测试方法**：
```bash
cd /home/yzh/AI客服/鉴权
python3 -c "
import asyncio
from services.shopify import get_shopify_service

async def test():
    service = get_shopify_service('de')
    result = await service.search_order_by_number('DE10091')
    order = result.get('order', {})
    for item in order.get('line_items', []):
        if 'Frontkorb' in item.get('title', ''):
            print(f'商品: {item.get(\"title\")}')
            print(f'delivery_status: {item.get(\"delivery_status\")}')
            print(f'delivery_status_zh: {item.get(\"delivery_status_zh\")}')

asyncio.run(test())
"
```

**验收标准**：
- [ ] DE10091 的 "Frontkorb" 商品 `delivery_status = "success"`
- [ ] DE10091 的 "Frontkorb" 商品 `delivery_status_zh = "已收货"`
- [ ] 其他订单不受影响
- [ ] 订单查询响应时间增加 < 50ms

---

### Phase 3: 集成测试

#### Step 3: 端到端测试

**目标**：验证完整流程，确保用户体验正确

**测试场景**：

| 场景 | 订单号 | 商品 | 预期显示 |
|------|--------|------|----------|
| 17track 已送达 + Shopify 无状态 | DE10091 | Frontkorb | 已收货 |
| Shopify 有状态 | UK22088 | Brake Pads | 已收货 |
| 无运单号 | - | 服务类商品 | 已生效 |
| 未发货 | - | - | 待发货 |

**测试方法**：
```bash
# 1. 确保 17track 缓存存在
cd /home/yzh/AI客服/鉴权
curl "http://localhost:8000/api/tracking/YT2418521272165525?order_number=DE10091"

# 2. 查询订单，检查商品状态
curl "http://localhost:8000/api/orders/search?order_number=DE10091" | jq '.order.line_items[] | {title, delivery_status, delivery_status_zh}'

# 3. 验证前端显示
# 访问 AI 客服，输入 "订单查询 DE10091"
```

**验收标准**：
- [ ] DE10091 的 "Frontkorb" 显示"已收货"
- [ ] UK22088 的 "Brake Pads" 仍显示"已收货"
- [ ] 无运单号的商品不受影响
- [ ] 前端商品卡片状态正确

---

## 三、步骤总览表

| Phase | Step | 标题 | 模块 | 状态 |
|-------|------|------|------|------|
| Phase 1 | Step 1 | 添加缓存查询接口 | services/tracking | ⏳ 待开始 |
| Phase 2 | Step 2 | 增强订单解析逻辑 | services/shopify | ⏳ 待开始 |
| Phase 3 | Step 3 | 集成测试 | 全部 | ⏳ 待开始 |

---

## 四、模块职责分工

| 模块 | 负责步骤 | 主要改动 |
|------|----------|----------|
| `services/tracking/` | Step 1 | 添加 `get_cached_status()` 方法 |
| `services/shopify/` | Step 2 | 修改 `_parse_order_detail()` 状态判断逻辑 |

---

## 五、依赖关系

```
Step 1 ──► Step 2 ──► Step 3
```

**说明**：
- Step 2 依赖 Step 1 提供的缓存查询接口
- Step 3 需要 Step 1 和 Step 2 都完成

---

## 六、风险与注意事项

### 6.1 技术风险

| 风险 | 影响步骤 | 缓解措施 |
|------|----------|----------|
| 同步/异步兼容 | Step 2 | 使用同步缓存接口或将解析方法改为异步 |
| 缓存不存在 | Step 2 | 降级到原有逻辑，显示"已发货" |

### 6.2 注意事项

- Step 1 完成后必须先测试缓存查询功能
- Step 2 修改需要保持向后兼容
- 每步完成后更新 `progress.md` 和 `architecture.md`
- 每步完成后 Git commit + tag

---

## 七、版本规划

- Step 1 完成：v7.6.19
- Step 2 完成：v7.6.20
- Step 3 完成：v7.6.21（可部署版本）
