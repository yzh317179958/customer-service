# 17track 物流追踪集成 - 实施计划

> **文档版本**：v1.0
> **创建日期**：2025-12-22

---

## 开发阶段

| 阶段 | 内容 | 步骤数 |
|------|------|--------|
| Phase 1 | services/tracking 服务层 | 4 步 |
| Phase 2 | products/notification 产品层 | 6 步 |
| Phase 3 | ai_chatbot 物流轨迹展示 | 3 步 |
| Phase 4 | 集成测试与部署 | 2 步 |

---

## Phase 1: services/tracking（17track API 封装）

### Step 1.1: 创建模块结构

**目标**：创建 tracking 服务的目录结构和基础文件

**创建文件**：
```
services/tracking/
├── __init__.py
├── README.md
```

**测试方法**：目录结构检查

---

### Step 1.2: 实现 17track API 客户端

**目标**：封装 17track API 调用

**创建文件**：
- `services/tracking/client.py`

**核心功能**：
```python
class Track17Client:
    async def register_tracking(tracking_number, carrier_code) -> dict
    async def get_tracking_info(tracking_number) -> dict
    async def retrack(tracking_number) -> dict
```

**测试方法**：
```bash
python3 -c "
from services.tracking.client import Track17Client
client = Track17Client()
# 测试注册
result = await client.register_tracking('TEST123', 'royalmail')
print(result)
"
```

---

### Step 1.3: 实现数据模型和 Webhook 解析

**目标**：定义数据结构，解析 17track 推送数据

**创建文件**：
- `services/tracking/models.py` - 数据模型
- `services/tracking/webhook.py` - Webhook 解析

**核心模型**：
```python
class TrackingStatus(str, Enum):
    NOT_FOUND = "NotFound"
    INFO_RECEIVED = "InfoReceived"
    IN_TRANSIT = "InTransit"
    # ...

class TrackingEvent(BaseModel):
    timestamp: datetime
    status: str
    location: str
    description: str
    description_zh: Optional[str]
```

**测试方法**：数据解析单元测试

---

### Step 1.4: 实现服务层业务逻辑

**目标**：封装业务逻辑，提供统一接口

**创建文件**：
- `services/tracking/service.py`

**核心接口**：
```python
class TrackingService:
    async def register_order_tracking(order_id, tracking_number, carrier)
    async def get_tracking_events(tracking_number) -> List[TrackingEvent]
    async def find_order_by_tracking(tracking_number) -> Optional[str]
```

**测试方法**：集成测试

---

## Phase 2: products/notification（物流通知）

### Step 2.1: 创建模块结构和 memory-bank 文档

**目标**：创建 notification 模块的完整目录结构

**创建文件**：
```
products/notification/
├── __init__.py
├── main.py
├── config.py
├── handlers/
│   └── __init__.py
├── templates/
├── memory-bank/
│   ├── prd.md
│   ├── tech-stack.md
│   ├── implementation-plan.md
│   ├── progress.md
│   └── architecture.md
```

**测试方法**：目录结构检查

---

### Step 2.2: 实现 Webhook 路由

**目标**：创建接收 Webhook 的 API 端点

**创建文件**：
- `products/notification/routes.py`

**端点**：
```python
POST /webhook/shopify    # Shopify 发货事件
POST /webhook/17track    # 17track 状态推送
```

**测试方法**：
```bash
curl -X POST http://localhost:8000/webhook/17track \
  -H "Content-Type: application/json" \
  -d '{"event": "test"}'
```

---

### Step 2.3: 实现 Shopify Webhook 处理

**目标**：处理 Shopify 发货事件，注册运单到 17track

**创建文件**：
- `products/notification/handlers/shopify_handler.py`

**功能**：
- `handle_fulfillment_create()` - 发货事件处理
- `handle_order_create()` - 订单创建（预售检测）

**测试方法**：模拟 Shopify Webhook 推送

---

### Step 2.4: 实现 17track 推送处理

**目标**：处理 17track 状态变更推送

**创建文件**：
- `products/notification/handlers/tracking_handler.py`

**功能**：
- `handle_status_change()` - 状态变更处理
- `handle_delivered()` - 签收处理
- `handle_exception()` - 异常处理

**测试方法**：模拟 17track Webhook 推送

---

### Step 2.5: 创建邮件模板

**目标**：设计通知邮件的 HTML 模板

**创建文件**：
- `products/notification/templates/split_package.html`
- `products/notification/templates/presale_shipped.html`
- `products/notification/templates/exception_alert.html`
- `products/notification/templates/delivery_confirm.html`

**测试方法**：浏览器预览模板

---

### Step 2.6: 实现通知发送器

**目标**：封装邮件发送逻辑

**创建文件**：
- `products/notification/handlers/notification_sender.py`

**功能**：
- `send_split_package_notice()` - 拆分通知
- `send_presale_notice()` - 预售通知
- `send_exception_alert()` - 异常告警
- `send_delivery_confirm()` - 签收确认

**测试方法**：发送测试邮件

---

## Phase 3: ai_chatbot 物流轨迹展示

### Step 3.1: 新增物流轨迹查询 API

**目标**：为 AI 客服提供物流轨迹查询接口

**修改文件**：
- `products/ai_chatbot/routes.py` 或新增文件

**端点**：
```python
GET /api/tracking/{tracking_number}
```

**返回**：
```json
{
  "tracking_number": "AB123456789GB",
  "carrier": "Royal Mail",
  "current_status": "in_transit",
  "events": [
    {
      "timestamp": "2024-12-22T10:30:00Z",
      "status": "in_transit",
      "location": "London, UK",
      "description": "Package in transit"
    }
  ]
}
```

**测试方法**：curl 测试

---

### Step 3.2: 前端添加可折叠物流时间线

**目标**：商品卡片支持展开物流轨迹

**修改文件**：
- `products/ai_chatbot/frontend/src/components/ChatMessage.vue`

**交互**：
1. 卡片底部添加「查看物流 ▼」按钮
2. 点击后展开时间线
3. 再次点击收起

**测试方法**：浏览器测试

---

### Step 3.3: 集成测试完整流程

**目标**：验证端到端流程

**测试流程**：
1. 在 AI 客服中查询订单
2. 商品卡片正确显示物流状态
3. 点击展开显示完整轨迹
4. 轨迹数据正确、多语言显示

---

## Phase 4: 集成与部署

### Step 4.1: 数据库迁移

**目标**：创建 tracking 相关数据表

**创建文件**：
- `infrastructure/database/migrations/versions/xxx_add_tracking_tables.py`

**新增表**：
- `tracking_registrations` - 运单注册记录
- `notification_records` - 通知记录

**测试方法**：
```bash
alembic upgrade head
```

---

### Step 4.2: 环境变量配置和部署

**目标**：配置生产环境并部署

**配置项**：
```bash
TRACK17_API_KEY=<your_api_key>
TRACK17_WEBHOOK_SECRET=<webhook_secret>
ENABLE_NOTIFICATION=true
```

**部署步骤**：
1. 更新 .env 文件
2. 执行数据库迁移
3. 重启服务
4. 在 17track 控制台配置 Webhook URL

---

## 完成标志

- [ ] 所有 Step 完成并测试通过
- [ ] 跨模块文档更新完毕
- [ ] PROJECT_OVERVIEW.md 更新
- [ ] 用户验收通过
