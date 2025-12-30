# 官网商业化 - 跨模块 PRD

> **文档类型**：跨模块功能 PRD
> **创建日期**：2025-12-30
> **涉及模块**：website、billing、customer_portal、ai_chatbot

---

## 一、功能概述

### 1.1 功能名称

官网商业化（Website Commercialization）

### 1.2 背景与目标

**背景**：
- Fiido AI 客服产品已完成核心功能开发（AI 智能客服 + 坐席工作台）
- 已使用 Gemini 生成官网原型（React + Vite + Tailwind）
- 需要完成商业闭环：客户触达 → 注册试用 → 付费转化 → 持续服务

**目标**：
1. 将官网原型适配为正式官网，替换品牌和定价内容
2. 实现用户注册、登录、试用功能
3. 集成支付网关（Stripe/支付宝）
4. 提供客户自助管理能力

### 1.3 涉及模块

| 模块 | 路径 | 职责 |
|------|------|------|
| 官网 | `products/website/` | 官网前端展示 + 后端 API（注册、表单、支付） |
| 计费服务 | `services/billing/` | 套餐管理、订阅、支付集成、用量计费 |
| 客户控制台 | `products/customer_portal/` | 客户自助管理（订阅、用量、账单） |
| AI 客服 | `products/ai_chatbot/` | 嵌入官网作为在线咨询演示 |
| 安全认证 | `infrastructure/security/` | JWT 认证（复用现有） |

---

## 二、各模块需求

### 2.1 官网模块 (products/website)

#### 2.1.1 前端需求

**内容适配（P0）**：
- 品牌替换：CrossBorderAI → Fiido
- 定价替换：美元 → 人民币，套餐结构按策略文档调整
- FAQ 替换：使用 marketing-landing-page.md 中的内容
- 案例处理：泛化描述或标注"示例"

**交互功能（P0）**：
- 免费试用按钮 → 跳转注册页面
- 登录按钮 → 跳转登录页面
- 套餐购买 → 跳转支付流程
- 预约演示 → 表单收集

**增强功能（P1）**：
- 嵌入 Fiido AI 客服组件
- ROI 计算器保留并适配

#### 2.1.2 后端需求

**认证 API（P0）**：
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/register | 用户注册（邮箱+密码+店铺URL） |
| POST | /api/auth/login | 用户登录 |
| GET | /api/auth/me | 获取当前用户信息 |

**表单 API（P0）**：
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/leads/demo | 预约演示表单 |
| POST | /api/leads/contact | 联系我们表单 |

**支付 API（P1）**：
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/payment/create-session | 创建 Stripe Checkout |
| POST | /api/payment/webhook | Stripe 回调处理 |

### 2.2 计费服务 (services/billing)

**套餐管理**：
```python
class BillingService:
    def get_plans() -> List[Plan]              # 获取套餐列表
    def get_plan(plan_id: str) -> Plan         # 获取单个套餐
```

**订阅管理**：
```python
    def create_subscription(tenant_id, plan_id)  # 创建订阅
    def get_subscription(tenant_id)              # 获取订阅
    def cancel_subscription(tenant_id)           # 取消订阅
    def upgrade_subscription(tenant_id, plan_id) # 升级套餐
```

**支付集成**：
```python
    def create_checkout_session(plan_id, email)  # Stripe Checkout
    def handle_webhook(payload, signature)       # 处理回调
```

**用量计费**：
```python
    def check_quota(tenant_id, action)           # 检查配额
    def record_usage(tenant_id, usage_type)      # 记录用量
    def get_usage_stats(tenant_id)               # 用量统计
```

### 2.3 客户控制台 (products/customer_portal)

> 已有 PRD：`products/customer_portal/memory-bank/prd.md`

**核心功能**：
- 账户信息管理
- 当前订阅查看
- 用量统计展示
- 套餐升级入口

### 2.4 AI 客服嵌入 (products/ai_chatbot)

**需求**：
- 在官网嵌入 AI 客服浮窗
- 作为产品演示 + 实际咨询入口
- 复用现有 widget 代码

---

## 三、模块间交互

### 3.1 数据流

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户访问官网                              │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   浏览产品              注册/登录              购买套餐
        │                     │                     │
        │                     ▼                     ▼
        │              ┌─────────────┐      ┌─────────────┐
        │              │ website API │      │ website API │
        │              │ /auth/*     │      │ /payment/*  │
        │              └──────┬──────┘      └──────┬──────┘
        │                     │                    │
        │                     ▼                    ▼
        │              ┌─────────────┐      ┌─────────────┐
        │              │ security/   │      │ billing/    │
        │              │ JWT 认证    │      │ Stripe 集成 │
        │              └──────┬──────┘      └──────┬──────┘
        │                     │                    │
        │                     └────────┬───────────┘
        │                              ▼
        │                       ┌─────────────┐
        │                       │ database/   │
        │                       │ PostgreSQL  │
        │                       └─────────────┘
        ▼
   在线咨询 ─────────────► ai_chatbot (嵌入)
```

### 3.2 接口定义

#### 服务层接口

| 服务 | 方法 | 调用方 | 说明 |
|------|------|--------|------|
| billing.get_plans() | website | 获取套餐列表 |
| billing.create_subscription() | website | 创建订阅 |
| billing.create_checkout_session() | website | 创建支付 |
| security.create_token() | website | JWT 签发 |
| security.verify_token() | website | JWT 验证 |

---

## 四、用户故事

1. **作为潜在客户**，我希望能在官网了解产品功能和价格，以便评估是否适合我的业务。

2. **作为新用户**，我希望能快速注册并开始免费试用，以便验证产品效果。

3. **作为试用用户**，我希望能方便地升级到付费套餐，以便获得更多服务额度。

4. **作为付费用户**，我希望能自助查看用量和账单，以便掌握使用情况。

5. **作为访客**，我希望能通过在线咨询快速获得解答，以便做出购买决策。

---

## 五、定价方案（来自 pricing-strategy.md）

| 套餐 | 月费 | 年费 | 会话数 | 坐席数 | 核心功能 |
|------|------|------|--------|--------|----------|
| 免费版 | ¥0 | ¥0 | 500/月 | 1 | AI 客服 + 1 站点 |
| 基础版 | ¥199 | ¥1,990 | 3000/月 | 3 | + 坐席工作台 + 工单 |
| 专业版 | ¥499 | ¥4,990 | 10000/月 | 10 | + 全功能 + 1v1 服务 |
| 企业版 | 定制 | 定制 | 不限 | 不限 | + 私有部署 |

**种子用户特权**：前 50 名年付享 5 折 + 终身锁价

---

## 六、成功标准

### 6.1 功能验收

- [ ] 官网内容已适配（品牌、定价、FAQ）
- [ ] 用户可完成注册/登录流程
- [ ] 支付流程可正常完成
- [ ] 客户控制台可查看订阅和用量
- [ ] AI 客服已嵌入官网

### 6.2 非功能要求

| 指标 | 要求 |
|------|------|
| 页面加载 | < 3 秒 |
| API 响应 | < 500ms |
| 支付成功率 | > 99% |
| 可用性 | 99.9% |

---

## 七、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-30 | 初始版本 |
