# 客户控制台 - 实现计划

> **创建日期**：2025-12-19
> **预计步骤数**：12
> **核心功能步骤**：Step 1-8
> **扩展功能步骤**：Step 9-12

---

## 开发顺序说明

遵循 CLAUDE.md 自底向上开发原则：

```
1. services/billing（计费服务）  ← 先开发底层服务
        ↓
2. products/customer_portal（控制台 API）
        ↓
3. 前端页面（可选独立或嵌入工作台）
        ↓
4. 工作台集成（iframe 嵌入）
```

---

## Phase 1: 基础设施层（services/billing）

### Step 1: 创建 billing 服务基础结构

**任务描述：**
创建 services/billing 服务模块的基础结构

**涉及文件：**
- services/billing/__init__.py
- services/billing/README.md
- services/billing/service.py
- services/billing/models.py

**验收标准：**
- 目录结构符合 services/README.md 规范
- 可以 import services.billing

---

### Step 2: 实现套餐管理功能

**任务描述：**
实现套餐的定义、查询功能

**涉及文件：**
- services/billing/plans.py

**接口规格：**
```python
class PlanService:
    def get_all_plans() -> List[Plan]       # 获取所有套餐
    def get_plan(plan_id: str) -> Plan      # 获取单个套餐
```

**测试方法：**
```python
from services.billing import PlanService
plans = PlanService.get_all_plans()
assert len(plans) > 0
```

---

### Step 3: 实现订阅管理功能

**任务描述：**
实现客户订阅的查询、创建、升级功能

**涉及文件：**
- services/billing/subscription.py

**接口规格：**
```python
class SubscriptionService:
    def get_subscription(customer_id: str) -> Subscription
    def create_subscription(customer_id: str, plan_id: str) -> Subscription
    def upgrade_subscription(customer_id: str, new_plan_id: str) -> Subscription
    def check_subscription_status(customer_id: str) -> bool
```

**测试方法：**
```python
from services.billing import SubscriptionService
sub = SubscriptionService.get_subscription("test_customer")
assert sub.status == "active"
```

---

### Step 4: 实现用量统计功能

**任务描述：**
实现用量记录、查询、扣减功能

**涉及文件：**
- services/billing/usage.py

**接口规格：**
```python
class UsageService:
    def record_usage(customer_id: str, product: str, count: int)
    def get_usage_summary(customer_id: str, period: str) -> UsageSummary
    def get_usage_detail(customer_id: str, start_date: str, end_date: str) -> List[UsageRecord]
    def check_quota(customer_id: str, product: str) -> bool
    def get_remaining_quota(customer_id: str, product: str) -> int
```

**测试方法：**
```python
from services.billing import UsageService
UsageService.record_usage("test_customer", "ai_chat", 1)
summary = UsageService.get_usage_summary("test_customer", "2025-12")
assert summary.ai_chat > 0
```

---

### Step 5: 实现账单管理功能

**任务描述：**
实现账单生成、查询功能

**涉及文件：**
- services/billing/invoice.py

**接口规格：**
```python
class InvoiceService:
    def generate_invoice(customer_id: str, period: str) -> Invoice
    def get_invoices(customer_id: str) -> List[Invoice]
    def get_invoice(invoice_id: str) -> Invoice
    def generate_pdf(invoice_id: str) -> bytes
```

**测试方法：**
```python
from services.billing import InvoiceService
invoices = InvoiceService.get_invoices("test_customer")
assert isinstance(invoices, list)
```

---

## Phase 2: 产品层（products/customer_portal API）

### Step 6: 实现账户信息 API

**任务描述：**
实现账户信息的查询和更新 API

**涉及文件：**
- products/customer_portal/handlers/account.py
- products/customer_portal/routes.py

**接口规格：**
```
GET  /api/portal/account    # 获取账户信息
PUT  /api/portal/account    # 更新账户信息
```

**测试方法：**
```bash
curl -H "Authorization: Bearer xxx" http://localhost:8000/api/portal/account
```

---

### Step 7: 实现订阅管理 API

**任务描述：**
实现订阅查询、套餐列表、升级 API

**涉及文件：**
- products/customer_portal/handlers/subscription.py
- products/customer_portal/routes.py

**接口规格：**
```
GET  /api/portal/subscription           # 获取当前订阅
GET  /api/portal/plans                  # 获取可用套餐
POST /api/portal/subscription/upgrade   # 升级套餐
```

**测试方法：**
```bash
curl -H "Authorization: Bearer xxx" http://localhost:8000/api/portal/subscription
curl -H "Authorization: Bearer xxx" http://localhost:8000/api/portal/plans
```

---

### Step 8: 实现用量统计 API

**任务描述：**
实现用量概览和明细查询 API

**涉及文件：**
- products/customer_portal/handlers/usage.py
- products/customer_portal/routes.py

**接口规格：**
```
GET /api/portal/usage                    # 用量概览
GET /api/portal/usage/detail?start=&end= # 用量明细
```

**测试方法：**
```bash
curl -H "Authorization: Bearer xxx" http://localhost:8000/api/portal/usage
```

---

### Step 9: 实现账单管理 API

**任务描述：**
实现账单列表、详情、PDF 下载 API

**涉及文件：**
- products/customer_portal/handlers/billing.py
- products/customer_portal/routes.py

**接口规格：**
```
GET /api/portal/invoices           # 账单列表
GET /api/portal/invoices/{id}      # 账单详情
GET /api/portal/invoices/{id}/pdf  # 下载 PDF
```

**测试方法：**
```bash
curl -H "Authorization: Bearer xxx" http://localhost:8000/api/portal/invoices
```

---

## Phase 3: 前端与集成

### Step 10: 创建控制台前端页面

**任务描述：**
创建客户控制台的前端页面（Vue）

**涉及文件：**
- products/customer_portal/frontend/ 或 frontend/src/views/portal/

**页面列表：**
- AccountView.vue - 账户信息
- SubscriptionView.vue - 订阅管理
- UsageView.vue - 用量统计
- BillingView.vue - 账单管理

**测试方法：**
- 启动前端 `npm run dev`
- 访问 /portal 页面
- 验证各功能正常

---

### Step 11: 工作台侧边栏集成

**任务描述：**
在坐席工作台添加侧边栏入口，通过 iframe 嵌入控制台

**涉及文件：**
- agent-workbench/src/components/Sidebar.vue
- agent-workbench/src/views/PortalFrame.vue

**测试方法：**
- 登录坐席工作台
- 点击侧边栏"账户与订阅"
- 验证 iframe 正常加载控制台页面

---

### Step 12: backend.py 注册 + 集成测试

**任务描述：**
在 backend.py 注册客户控制台路由，进行完整集成测试

**涉及文件：**
- backend.py
- .env (添加 ENABLE_CUSTOMER_PORTAL)

**测试方法：**
```bash
# 设置环境变量
export ENABLE_CUSTOMER_PORTAL=true

# 启动服务
python backend.py

# 验证路由
curl http://localhost:8000/api/portal/account
```

---

## 开发检查清单

### 每个 Step 完成后必须：

- [ ] 测试验证通过
- [ ] 更新 progress.md
- [ ] 更新 architecture.md
- [ ] Git commit + tag
- [ ] 告知用户可继续下一步

### 功能完成后必须：

- [ ] 所有 P0 功能通过测试
- [ ] 更新 PROJECT_OVERVIEW.md 产品清单
- [ ] 回归测试通过
- [ ] 用户确认后部署
