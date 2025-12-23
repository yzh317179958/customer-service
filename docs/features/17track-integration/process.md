# 17track 集成问题处理记录（process）

> 用于记录用户验收/手动测试中发现的问题、定位过程与修复结果
> 格式参考：`docs/features/17track-integration/progress.md`

---

## 2025-12-23：17track API V2.4 响应格式不兼容导致物流轨迹为空

### 问题描述

- 复现场景：在 AI 客服中查询订单 `UK22080`，对应运单号 `YT2534600708756851`（承运商 YUNWAY/云途物流）
- 现象：商品卡片展示承运商与运单号；点击「查看物流」后显示"暂无物流轨迹"
- 调试发现：直接调用 17track API 可返回 16 条轨迹事件，但 `TrackingService.get_tracking_info()` 返回 `events=[]`

### 根因分析

**核心问题：17track API V2.4 响应格式与代码解析逻辑不匹配**

1. **事件解析位置错误**
   - 旧代码（V2.2 格式）：从 `track.z1[]` 读取事件
   - V2.4 实际格式：事件在 `track_info.tracking.providers[0].events[]`
   - 结果：`_parse_events()` 返回空列表

2. **状态字段格式变化**
   - 旧代码：使用 `track.e`（数字状态码）+ `TrackingStatus.from_code()`
   - V2.4 实际格式：状态在 `track_info.latest_status.status`（字符串如 `"InTransit"`）
   - 结果：`status=None`，无法正确判断物流状态

3. **事件字段名称变化**
   - 旧格式：`a`（时间）、`c`（描述）、`d`（地点）、`b`（状态码）
   - V2.4 格式：`time_iso`（时间）、`description`（描述）、`location`/`address`（地点）、`sub_status`（子状态字符串）

### 修复方案

1. **client.py：新增 V2.4 事件解析方法**
   ```python
   def _parse_events_v2(self, track_info: Dict) -> List[Dict]:
       # 从 track_info.tracking.providers[0].events 提取
       # 字段映射：time_iso -> timestamp, description -> status, location/address -> location
   ```

2. **client.py：更新 `get_tracking_info()` 返回结构**
   - 状态：从 `track_info.latest_status.status` 读取字符串
   - 事件：调用 `_parse_events_v2()` 解析 V2.4 格式
   - 最新事件：从 `track_info.latest_event` 读取

3. **models.py：新增 `TrackingStatus.from_string()` 方法**
   ```python
   @classmethod
   def from_string(cls, status_str: str) -> "TrackingStatus":
       # 支持 V2.4 字符串状态：InTransit -> IN_TRANSIT
   ```

4. **models.py：调整 `TrackingEvent.status_code` 类型**
   - 从 `int` 改为 `str`，兼容 V2.4 的子状态字符串（如 `"InTransit_Other"`）

5. **service.py：更新 `get_tracking_info()` 解析逻辑**
   - 使用 `TrackingStatus.from_string()` 解析状态
   - 正确处理 V2.4 格式的 `last_event`

### 修改文件

- `services/tracking/client.py` - 新增 `_parse_events_v2()`，更新 `get_tracking_info()` 返回结构
- `services/tracking/models.py` - 新增 `TrackingStatus.from_string()`，调整 `status_code` 类型
- `services/tracking/service.py` - 更新状态和事件解析逻辑
- `docs/features/17track-integration/process.md` - 本记录

### 验证记录

- ✅ `python3 -m py_compile services/tracking/client.py services/tracking/service.py services/tracking/models.py`
- ✅ 直接调用测试：
  ```
  tracking_number: YT2534600708756851
  status: InTransit
  status_zh: 运输中
  events count: 16
  ```
- ✅ `npm -C products/ai_chatbot/frontend run type-check`

### 测试命令

```bash
# 设置 API Key 并测试
TRACK17_API_KEY='B5670455769EB01CC5B5A5685A6F408E' python3 << 'EOF'
import asyncio
from services.tracking.client import Track17Client
from services.tracking.service import TrackingService

async def test():
    client = Track17Client()
    service = TrackingService(client=client)
    info = await service.get_tracking_info('YT2534600708756851', use_cache=False)
    print(f"status: {info.status}, events: {len(info.events)}")
    for e in info.events[:3]:
        print(f"  {e.timestamp_str[:16]} - {e.status}")

asyncio.run(test())
EOF
```

---

## 2025-12-23：订单 UK22080 展开物流显示"暂无物流信息"

### 问题描述

- 复现场景：按 `Step 3.3: 集成测试完整流程` 在 AI 客服中查询订单 `UK22080`
- 现象：商品卡片已展示承运商与运单号；点击「查看物流」展开后提示“暂无物流信息”
- 期望：首次查询未注册运单时提示“物流信息更新中，请稍后刷新”，并在后台完成 17track 注册；再次刷新可看到轨迹

### 根因分析

1. **前端错误兜底过强且不重试**
   - `ChatMessage.vue` 中 `fetchTrackingData()` 对非 2xx 或 JSON 解析失败统一进入 `error` 分支，UI 固定展示“暂无物流信息”
   - 同一运单号请求失败后会被缓存，后续展开不再重试（`trackingDataMap.has()` 直接返回）

2. **后端自动注册依赖 order_id，但商品卡片数据不包含**
   - `TrackingService.get_tracking_info_with_auto_register()` 原本仅在传入 `order_id` 时才会异步注册
   - 商品卡片的 `[PRODUCT]` 格式仅提供承运商/运单号/追踪链接等字段，不包含 `order_id`，导致即使返回 `pending`，也可能一直无法产生轨迹数据

### 修复方案

1. **前端：统一 API Base + 传递承运商 + 允许重试**
   - 物流查询使用 `VITE_API_BASE`（为空则走同域 `/api`），避免环境差异导致命中错误服务
   - 从商品卡片按钮透传 `carrier`，请求 `/api/tracking/{tracking_number}?carrier=...`
   - 对 `error` 或 `is_pending` 状态允许强制重试，避免一次失败后永久显示“暂无物流信息”

2. **后端：无 order_id 也可注册到 17track（去重）**
   - 当查询无数据时，若未提供 `order_id` 也会异步调用 17track `register` 完成注册（不建立订单映射）
   - 增加 5 分钟注册触发去重，避免短时间内重复注册

### 修改文件

- `products/ai_chatbot/frontend/src/components/ChatMessage.vue`
- `services/tracking/service.py`
- `docs/features/17track-integration/process.md`（本文件新增）

### 验证记录

- ✅ `npm -C products/ai_chatbot/frontend run type-check`
- ✅ `npm -C products/ai_chatbot/frontend run build-only`
- ✅ `python3 -m py_compile services/tracking/service.py`
- ✅ 本地逻辑验证：使用 DummyClient 调用 `TrackingService.get_tracking_info_with_auto_register()`，确认无 `order_id` 也会返回 `is_pending=true` 并触发异步注册

### 补充改进（稳定性）

- 为 tracking 服务的 Redis 读写增加短超时降级（默认 `0.5s`，可用环境变量 `TRACKING_REDIS_IO_TIMEOUT` 调整），避免 Redis 异常时接口卡住
- 修复“二次请求导致轨迹丢失”：`get_tracking_info()` 过去会再次调用 17track 获取 events（`get_tracking_events()`），在限流/偶发失败时会导致 `events=[]`，前端显示“暂无物流轨迹”；现改为 **单次请求解析 events**，并让 `get_tracking_events()` 复用 `get_tracking_info()`
- 修复“status 缺失误判有数据”：当 17track 响应缺少主状态码时，过去会返回 `current_status=unknown` 且不触发自动注册；现改为 status 缺失+无 events 视为“无数据”并走 pending/自动注册
- `refresh` 参数生效：`GET /api/tracking/{tracking_number}?refresh=true` 会清理缓存并跳过缓存读取

### 预期验收表现（手动）

1. 打开订单 `UK22080` 商品卡片，点击「查看物流」
2. 首次：展示“物流信息更新中，请稍后刷新”
3. 等待数十秒~数分钟后刷新/重新展开：展示轨迹时间线（或“暂无物流轨迹”，不再是“暂无物流信息”）

### 排查/测试建议（以 UK22080 为例）

1. 打开浏览器 DevTools → Network，点「查看物流」，确认请求为：
   - `GET /api/tracking/<UK22080的运单号>?carrier=<承运商>`
2. 首次若返回 `is_pending=true`：等待 30~120 秒后再次请求：
   - `GET /api/tracking/<运单号>?carrier=<承运商>&refresh=true`
3. 若仍 `events=[]` 但 `current_status` 不是 `NotFound`：
   - 说明 17track 已注册但暂未回传轨迹（常见于刚注册/承运商尚未同步），需稍后再试
