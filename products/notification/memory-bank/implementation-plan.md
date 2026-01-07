# 物流通知 - 实现计划

> **创建日期**：2025-12-23
> **最后更新**：2026-01-07
> **关联文档**：`docs/features/17track-integration/implementation-plan.md`

---

## 说明

本模块已完成 Shopify + 17track 的基础版通知链路（Webhook 接入 + 模板邮件发送）。

下一阶段的重点不是“更多功能堆叠”，而是面向真实业务的生产化补齐：
- 通知幂等、去重、可追踪（落库、可重试）
- 易仓 ERP 售后配件订单的物流更新通知（接口能力明确后落地）

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

| 步骤 | 内容 | 产出 |
|------|------|------|
| Step 4.1 | 明确易仓接口能力 | 是否支持推送（Webhook）/仅查询（Polling）；字段对齐 |
| Step 4.2 | 新增服务层适配 | `services/yicang`：签名校验、数据模型、查询/回调解析 |
| Step 4.3 | 新增产品层入口 | `POST /webhook/yicang` 处理订单/物流更新 |
| Step 4.4 | 售后订单识别规则 | 以“下单店铺维度/订单类型字段”区分售后配件订单 |
| Step 4.5 | 补齐易仓文档要点 | 将 `[[YICANG_TBD]]` 占位替换为最终验签与 payload 示例 |

---

## 文件清单（当前）

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
│   └── notification_sender.py  # 通知发送 (Step 2.6)
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
```
