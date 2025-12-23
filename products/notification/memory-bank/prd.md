# 物流通知（Notification）- 产品需求文档

> **产品名称**：Fiido 物流通知服务
> **版本**：v1.0
> **创建日期**：2025-12-21
> **更新日期**：2025-12-23
> **状态**：开发中

---

## 一、产品概述

物流通知服务是 Fiido 智能服务平台的核心产品，基于 17track API 提供物流状态监控和自动通知功能。

### 1.1 目标用户
- 终端消费者：获取物流状态更新和签收确认
- 坐席：处理物流异常
- 运营人员：监控物流服务质量

### 1.2 核心价值
- 物流状态实时推送（基于 17track Webhook）
- 异常情况自动预警
- 拆包裹/预售发货通知
- 签收确认邮件

---

## 二、核心功能

### 2.1 拆包裹发货通知
**触发条件**：一个订单拆分为多个包裹发货
**通知内容**：告知用户订单将分批到达
**触发方式**：Shopify fulfillment.create Webhook

### 2.2 预售商品发货通知
**触发条件**：预售商品开始发货
**通知内容**：告知用户预售商品已发出
**触发方式**：Shopify fulfillment.create + SKU 前缀判断

### 2.3 物流异常告警
**触发条件**：17track 推送异常状态（Alert、Undelivered）
**通知内容**：告知用户物流出现问题，提供解决方案
**触发方式**：17track Webhook 推送

### 2.4 签收确认通知
**触发条件**：17track 推送 Delivered 状态
**通知内容**：确认签收，引导评价
**触发方式**：17track Webhook 推送

---

## 三、Webhook 端点

| 端点 | 来源 | 用途 |
|------|------|------|
| `POST /webhook/shopify` | Shopify | 接收发货事件 |
| `POST /webhook/17track` | 17track | 接收状态变更 |

---

## 四、依赖服务

| 服务 | 用途 |
|------|------|
| services/tracking | 17track API 封装、运单注册 |
| services/shopify | 订单数据查询 |
| services/email | 邮件发送 |
| infrastructure/database | 通知记录持久化 |

---

## 五、邮件模板

| 模板 | 用途 |
|------|------|
| split_package.html | 拆包裹通知 |
| presale_shipped.html | 预售发货通知 |
| exception_alert.html | 异常告警 |
| delivery_confirm.html | 签收确认 |

---

## 六、跨模块引用

本模块是 **17track 物流追踪集成** 跨模块功能的一部分。

完整文档：`docs/features/17track-integration/`
