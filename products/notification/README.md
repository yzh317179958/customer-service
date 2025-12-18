# 物流通知模块规范

> **模块定位**：物流通知与异常监控系统
> **模块状态**：规划中
> **最后更新**：2025-12-18

---

## 一、模块职责

物流通知模块提供：

- 预售商品发货通知
- 拆包裹发货通知
- 物流异常监控与告警

---

## 二、核心功能

| 功能 | 触发方式 | 说明 |
|------|----------|------|
| 预售通知 | Webhook | 订单创建时检测预售商品 |
| 拆包裹通知 | Webhook | 首个包裹发出时通知 |
| 异常监控 | 定时任务 | 每日扫描超时订单 |

---

## 三、依赖服务

```python
# 允许的依赖
from services.shopify import ShopifyService
from services.email import EmailService
from infrastructure.database import get_redis_client
from infrastructure.scheduler import Scheduler
```

---

## 四、目录结构

```
products/notification/
├── __init__.py
├── README.md                   # 本文档
├── routes.py                   # Webhook 接收端点
├── handlers/
│   ├── presale_handler.py      # 预售通知
│   ├── split_package_handler.py # 拆包裹通知
│   └── anomaly_handler.py      # 异常监控
├── config.py                   # 渠道、SKU 配置
├── templates/                  # 邮件模板
├── memory-bank/                # Vibe Coding 文档
│   ├── prd.md
│   ├── tech-stack.md
│   ├── implementation-plan.md
│   ├── progress.md
│   └── architecture.md
└── tests/
    └── test_notification.py
```

---

## 五、异常监控规则

| 渠道类型 | 超时阈值 | 承运商示例 |
|----------|----------|------------|
| 海外仓 | > 7 天 | Royal Mail, DPD, UPS |
| 中国仓 | > 12 天 | 4PX, YunExpress, SF |

---

## 六、配置项

| 环境变量 | 说明 |
|----------|------|
| ENABLE_NOTIFICATION | 模块启用开关 |
| NOTIFICATION_SMTP_* | 邮件服务配置 |

---

## 七、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-18 | 初始版本 |
