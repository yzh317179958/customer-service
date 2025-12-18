# Shopify 订单服务规范

> **服务定位**：多站点 Shopify 订单查询与物流跟踪
> **服务状态**：已完成
> **最后更新**：2025-12-18

---

## 一、服务职责

- 多站点订单查询（9 个站点）
- 物流状态跟踪（17track 集成）
- 订单数据缓存
- 状态预翻译（中英文）

---

## 二、公开接口

```python
class ShopifyService:
    async def query_order(self, email: str, order_number: str) -> dict
    async def get_tracking_info(self, tracking_number: str) -> dict

def get_shopify_service(site: str) -> ShopifyService
```

---

## 三、目录结构

```
services/shopify/
├── __init__.py
├── README.md           # 本文档
├── client.py           # Shopify API 客户端
├── service.py          # 业务服务
├── cache.py            # 缓存逻辑
├── tracking.py         # 物流跟踪
├── models.py           # 数据模型
└── tests/
    └── test_shopify.py
```

---

## 四、支持站点

| 站点代码 | 说明 |
|----------|------|
| uk | 英国站 |
| de | 德国站 |
| fr | 法国站 |
| ... | 其他站点 |

---

## 五、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-18 | 初始版本 |
