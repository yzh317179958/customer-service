# 物流通知 - 实现计划

> **创建日期**：2025-12-23
> **最后更新**：2026-01-08
> **关联文档**：`docs/features/17track-integration/implementation-plan.md`

---

## 说明

本模块已完成 Shopify + 17track 的基础版通知链路（Webhook 接入 + 模板邮件发送）。

下一阶段的重点不是"更多功能堆叠"，而是面向真实业务的生产化补齐：
- 通知幂等、去重、可追踪（落库、可重试）
- 易仓 ERP 售后配件订单的物流更新通知（已明确采用轮询方案）

---

## Phase 2（已完成）：Shopify + 17track 基础链路

| 步骤 | 内容 | 状态 |
|------|------|------|
| Step 2.1 | 创建模块结构 | ✅ 完成 |
| Step 2.2 | 实现 Webhook 路由 | ✅ 完成 |
| Step 2.3 | 实现 Shopify Webhook 处理 | ✅ 完成 |
| Step 2.4 | 实现 17track 推送处理 | ✅ 完成 |
| Step 2.5 | 创建邮件模板 | ✅ 完成 |
| Step 2.6 | 实现通知发送器 | ✅ 完成 |

---

## Phase 3（规划）：生产化补齐（幂等/落库/重试）

| 步骤 | 内容 | 产出 |
|------|------|------|
| Step 3.1 | 落库运单映射 | `tracking_registrations` 写入与查询（替代仅 Redis 映射） |
| Step 3.2 | 落库通知记录 | `notification_records` 写入；按 `notification_id` 幂等 |
| Step 3.3 | 失败重试 Outbox | 失败记录可重试；重试次数与节流可配置 |
| Step 3.4 | 规则开关配置 | 按店铺/通知类型启停；默认安全关闭 |

---

## Phase 4（规划）：易仓 ERP 售后配件物流通知

> **重要**：基于 2026-01-08 调研，易仓开放平台采用"主动拉取 API"模式，暂无公开 Webhook 推送机制。
> 因此采用**定时轮询**方案，而非原计划的 Webhook 回调。

| 步骤 | 内容 | 产出 | 阻塞项 |
|------|------|------|--------|
| Step 4.1 | 确认售后订单识别规则 | 明确用 `shipping_method` / `warehouse_code` / `mail_cargo_type` 哪个字段 | **业务确认** |
| Step 4.2 | 新增服务层适配 | `services/yicang`：签名生成、API 调用、数据模型 | 无 |
| Step 4.3 | 新增轮询任务 | `infrastructure/scheduler` 定时任务（每 5-10 分钟） | 依赖 scheduler 组件 |
| Step 4.4 | 新增产品层处理器 | `handlers/yicang_handler.py`：订单筛选、状态变更检测、通知触发 | 无 |
| Step 4.5 | 幂等与增量查询 | 按 `reference_no + status` 去重；按 `modify_date` 增量拉取 | 无 |
| Step 4.6 | 集成测试 | 小批量生产环境测试（无沙箱） | 无 |

### Step 4.2 详细设计：services/yicang

```python
# services/yicang/client.py

class YicangClient:
    """易仓开放平台 API 客户端"""

    def __init__(self, app_key: str, app_secret: str, service_id: str):
        self.app_key = app_key
        self.app_secret = app_secret
        self.service_id = service_id
        self.base_url = "http://openapi-web.eccang.com/openApi/api/unity"

    def generate_sign(self, params: dict) -> str:
        """MD5 签名算法"""
        sorted_params = sorted(
            [(k, v) for k, v in params.items() if k != 'sign' and v],
            key=lambda x: x[0]
        )
        sign_str = '&'.join(f'{k}={v}' for k, v in sorted_params)
        sign_str += self.app_secret
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()

    async def get_order_list(
        self,
        modify_date_from: str,
        modify_date_to: str,
        page: int = 1,
        page_size: int = 100
    ) -> dict:
        """获取订单列表（增量查询）"""
        ...

    async def get_order(self, reference_no: str) -> dict:
        """获取单个订单详情"""
        ...
```

### Step 4.4 详细设计：handlers/yicang_handler.py

```python
# products/notification/handlers/yicang_handler.py

async def process_order_updates(orders: list[dict]) -> int:
    """处理订单更新列表，返回发送通知数"""
    sent_count = 0
    for order in orders:
        # 1. 判断是否售后配件订单
        if not _is_aftersales_order(order):
            continue

        # 2. 检测状态变更
        status_change = await _detect_status_change(order)
        if not status_change:
            continue

        # 3. 触发对应通知
        await _trigger_notification(order, status_change)
        sent_count += 1

    return sent_count

def _is_aftersales_order(order: dict) -> bool:
    """判断是否售后配件订单（待业务确认具体字段）"""
    # 方案 A：按配送方式
    # return order.get('shipping_method') in AFTERSALES_SHIPPING_METHODS

    # 方案 B：按仓库
    # return order.get('warehouse_code') in AFTERSALES_WAREHOUSES

    # 方案 C：按货物类型
    # return order.get('mail_cargo_type') == SPARE_PARTS_TYPE
    pass
```

---

## 待业务确认事项

| 事项 | 说明 | 阻塞 Phase 4 |
|------|------|-------------|
| **售后订单识别字段** | 需确认用 `shipping_method` / `warehouse_code` / `mail_cargo_type` 哪个字段识别售后配件订单 | **是** |

**建议操作**：
1. 调用 `getShippingMethod` 接口获取所有配送方式列表
2. 从中识别售后专用的配送方式代码
3. 或者确认售后配件订单统一从哪个仓库发货

---

## 文件清单（当前 + 规划）

```
products/notification/
├── __init__.py          # 模块导出
├── main.py              # 独立模式入口
├── config.py            # 配置管理
├── routes.py            # Webhook 路由 (Step 2.2)
├── handlers/
│   ├── __init__.py
│   ├── shopify_handler.py      # Shopify 事件 (Step 2.3)
│   ├── tracking_handler.py     # 17track 推送 (Step 2.4)
│   ├── notification_sender.py  # 通知发送 (Step 2.6)
│   └── yicang_handler.py       # 易仓轮询处理 (Step 4.4, 规划)
├── templates/           # 邮件模板 (Step 2.5)
│   ├── split_package.html
│   ├── presale_shipped.html
│   ├── exception_alert.html
│   └── delivery_confirm.html
└── memory-bank/
    ├── prd.md
    ├── tech-stack.md
    ├── implementation-plan.md
    ├── progress.md
    └── architecture.md

services/yicang/          # (Step 4.2, 规划)
├── __init__.py
├── client.py            # API 客户端
├── models.py            # 数据模型
└── config.py            # 配置
```
