# Billing Service 计费服务

> **服务定位**：计费核心能力，被多个产品共享
> **状态**：规划中
> **最后更新**：2025-12-19

---

## 一、服务职责

计费服务封装所有计费相关的核心能力：

- 套餐定义与管理
- 客户订阅管理
- 用量统计与扣减
- 账单生成与查询
- 配额检查

---

## 二、被谁依赖

| 产品 | 使用场景 |
|------|----------|
| customer_portal | 展示订阅、用量、账单 |
| ai_chatbot | 检查 AI 对话配额 |
| agent_workbench | 检查坐席数量配额 |
| notification | 检查邮件发送配额 |

---

## 三、依赖规则

### 3.1 允许的依赖

```python
# ✅ 依赖 infrastructure
from infrastructure.database import get_redis_client
from infrastructure.logging import logger
```

### 3.2 禁止的依赖

```python
# ❌ 禁止依赖 products
from products.customer_portal import xxx  # 禁止！
```

---

## 四、目录结构

```
services/billing/
├── __init__.py          # 模块入口
├── README.md            # 【本文件】服务规范
├── service.py           # 服务统一入口
├── plans.py             # 套餐管理（待创建）
├── subscription.py      # 订阅管理（待创建）
├── usage.py             # 用量管理（待创建）
├── invoice.py           # 账单管理（待创建）
├── models.py            # 数据模型（待创建）
└── tests/               # 单元测试
    └── test_billing.py
```

---

## 五、核心接口设计

### 5.1 PlanService 套餐服务

```python
class PlanService:
    @staticmethod
    def get_all_plans() -> List[Plan]:
        """获取所有可用套餐"""

    @staticmethod
    def get_plan(plan_id: str) -> Optional[Plan]:
        """获取单个套餐详情"""
```

### 5.2 SubscriptionService 订阅服务

```python
class SubscriptionService:
    @staticmethod
    def get_subscription(customer_id: str) -> Optional[Subscription]:
        """获取客户当前订阅"""

    @staticmethod
    def create_subscription(customer_id: str, plan_id: str) -> Subscription:
        """创建订阅"""

    @staticmethod
    def upgrade_subscription(customer_id: str, new_plan_id: str) -> Subscription:
        """升级套餐"""

    @staticmethod
    def check_active(customer_id: str) -> bool:
        """检查订阅是否有效"""
```

### 5.3 UsageService 用量服务

```python
class UsageService:
    @staticmethod
    def record_usage(customer_id: str, product: str, count: int = 1):
        """记录用量"""

    @staticmethod
    def get_usage_summary(customer_id: str, period: str) -> UsageSummary:
        """获取用量汇总"""

    @staticmethod
    def check_quota(customer_id: str, product: str) -> bool:
        """检查是否还有配额"""

    @staticmethod
    def get_remaining_quota(customer_id: str, product: str) -> int:
        """获取剩余配额"""
```

### 5.4 InvoiceService 账单服务

```python
class InvoiceService:
    @staticmethod
    def get_invoices(customer_id: str) -> List[Invoice]:
        """获取账单列表"""

    @staticmethod
    def get_invoice(invoice_id: str) -> Optional[Invoice]:
        """获取账单详情"""

    @staticmethod
    def generate_invoice(customer_id: str, period: str) -> Invoice:
        """生成账单"""
```

---

## 六、数据模型

```python
@dataclass
class Plan:
    id: str
    name: str
    price: float
    period: str  # month/year
    features: Dict[str, int]  # {"ai_chat": 10000, "agent_seats": 5}

@dataclass
class Subscription:
    customer_id: str
    plan_id: str
    plan_name: str
    start_date: date
    end_date: date
    status: str  # active/expired/cancelled

@dataclass
class UsageSummary:
    period: str
    items: Dict[str, int]  # {"ai_chat": 3000, "email": 500}

@dataclass
class Invoice:
    id: str
    customer_id: str
    period: str
    amount: float
    status: str  # pending/paid/overdue
    items: List[InvoiceItem]
```

---

## 七、使用示例

```python
from services.billing import BillingService

# 检查配额（AI 客服调用）
if BillingService.check_quota(customer_id, "ai_chat"):
    # 允许对话
    BillingService.record_usage(customer_id, "ai_chat", 1)
else:
    # 配额不足
    return "您的对话次数已用完，请升级套餐"

# 获取订阅信息（客户控制台调用）
subscription = BillingService.get_subscription(customer_id)
usage = BillingService.get_usage_summary(customer_id, "2025-12")
```

---

## 八、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-19 | 初始版本，创建服务框架 |
