# 物流追踪服务

> **服务定位**：封装 17track API，提供物流追踪能力
> **服务状态**：开发中
> **最后更新**：2025-12-22

---

## 一、服务职责

物流追踪服务（tracking）封装 17track API，提供：

- 运单注册：将运单号注册到 17track 进行追踪
- 轨迹查询：获取完整物流轨迹事件
- Webhook 解析：解析 17track 推送的状态变更数据
- 运单→订单映射：通过运单号查找关联订单

---

## 二、核心接口

### 2.1 TrackingService

```python
from services.tracking import TrackingService, get_tracking_service

# 获取服务实例
tracking_service = get_tracking_service()

# 注册运单
await tracking_service.register_tracking(
    tracking_number="AB123456789GB",
    carrier_code="royalmail",
    order_id="UK22080",
    customer_email="customer@example.com"
)

# 获取物流轨迹
events = await tracking_service.get_tracking_events("AB123456789GB")

# 通过运单号找订单
order_id = await tracking_service.find_order_by_tracking("AB123456789GB")
```

### 2.2 Track17Client

```python
from services.tracking.client import Track17Client

client = Track17Client(api_key="your_api_key")

# 注册运单
result = await client.register_tracking("AB123456789GB", "royalmail")

# 查询轨迹
info = await client.get_tracking_info("AB123456789GB")
```

---

## 三、数据模型

### 3.1 TrackingEvent（物流事件）

```python
class TrackingEvent(BaseModel):
    timestamp: datetime           # 事件时间
    status: str                   # 状态码
    status_zh: Optional[str]      # 中文状态
    location: Optional[str]       # 地点
    description: str              # 事件描述
    description_zh: Optional[str] # 中文描述
```

### 3.2 TrackingStatus（状态枚举）

| 状态 | 英文 | 说明 |
|------|------|------|
| NotFound | 未找到 | 运单号无信息 |
| InfoReceived | 已揽收 | 等待揽收 |
| InTransit | 运输中 | 运输途中 |
| PickUp | 待取件 | 到达待取 |
| OutForDelivery | 派送中 | 正在派送 |
| Undelivered | 未送达 | 派送失败 |
| Delivered | 已签收 | 成功签收 |
| Alert | 异常 | 发生异常 |
| Expired | 过期 | 长时间无更新 |

---

## 四、目录结构

```
services/tracking/
├── __init__.py           # 模块导出
├── README.md             # 本文档
├── client.py             # 17track API 客户端
├── service.py            # 业务逻辑层
├── models.py             # 数据模型
├── webhook.py            # Webhook 数据解析
└── cache.py              # Redis 缓存（可选）
```

---

## 五、依赖关系

```python
# 允许的依赖
from infrastructure.database import get_db_session
from infrastructure.database.models import TrackingRegistration

# 禁止的依赖
# from products.xxx import ...  # 服务层不能依赖产品层
```

---

## 六、配置项

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| TRACK17_API_KEY | 17track API Key | 必填 |
| TRACK17_WEBHOOK_SECRET | Webhook 签名密钥 | 必填 |
| TRACK17_API_URL | API 地址 | https://api.17track.net |

---

## 七、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-22 | 初始版本 |
