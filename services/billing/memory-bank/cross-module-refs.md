# 计费服务 - 跨模块功能引用

> **模块路径**：services/billing/
> **最后更新**：2025-12-30

---

## 官网商业化

**主文档**：`docs/features/website-commercial/`

**状态**：⏳ 开发中

**本模块职责**：
- 套餐定义和管理
- 订阅创建和状态管理
- Stripe 支付集成
- 用量计费和配额检查
- 账单生成

**涉及文件**：

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| models.py | 新增 | 数据模型定义 |
| service.py | 扩展 | 统一服务入口 |
| plans.py | 新增 | 套餐管理 |
| subscriptions.py | 新增 | 订阅管理 |
| usage.py | 新增 | 用量计费 |
| stripe_gateway.py | 新增 | Stripe 集成 |
| migrations/001_billing_tables.sql | 新增 | 数据库表 |

**对接模块**：
- `products/website` - 提供套餐/订阅/支付服务
- `products/customer_portal` - 提供用量/账单查询
- `infrastructure/database` - 数据存储
