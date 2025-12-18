# Products 产品层规范

> **层级定位**：面向用户的完整功能模块
> **最后更新**：2025-12-18

---

## 一、层级职责

产品层包含所有面向用户的完整功能，每个产品：

- 有独立的 API 端点
- 有完整的业务逻辑
- 可独立启用/禁用
- 可独立部署（未来）

---

## 二、当前产品清单

| 产品 | 目录 | 状态 | 说明 |
|------|------|------|------|
| AI 智能客服 | ai_chatbot/ | 已上线 | 核心产品 |
| 坐席工作台 | agent_workbench/ | 已上线 | 人工客服后端 |
| 物流通知 | notification/ | 规划中 | 预售/拆包裹/异常监控 |

---

## 三、依赖规则

### 3.1 允许的依赖

```python
# ✅ 可以依赖 services 层
from services.shopify import ShopifyService
from services.email import EmailService

# ✅ 可以依赖 infrastructure 层
from infrastructure.database import get_redis_client
```

### 3.2 禁止的依赖

```python
# ❌ 禁止依赖其他产品
from products.agent_workbench import xxx  # 禁止！

# ❌ 禁止被 services 或 infrastructure 依赖
# services 层不能 import products
```

### 3.3 产品间通信

产品之间需要协作时，通过以下方式：

| 方式 | 说明 |
|------|------|
| 共享服务 | 通过 services/session 共享会话数据 |
| Redis | 通过 infrastructure/database 共享数据 |
| API | 通过 HTTP 调用对方的 API |
| 事件 | 发布/订阅机制 |

---

## 四、产品目录结构

每个产品必须遵循以下结构：

```
products/xxx/
├── __init__.py                 # 模块初始化，导出公开接口
├── README.md                   # 【必须】模块规范文档
├── routes.py                   # API 路由定义
├── handlers/                   # 业务处理器
│   └── xxx_handler.py
├── memory-bank/                # 【必须】Vibe Coding 文档
│   ├── prd.md                 # 产品需求文档
│   ├── tech-stack.md          # 技术栈说明
│   ├── implementation-plan.md # 实现计划
│   ├── progress.md            # 进度追踪
│   └── architecture.md        # 架构说明
└── tests/                      # 单元测试
    └── test_xxx.py
```

---

## 五、开发规范

### 5.1 新建产品流程

1. 在 products/ 下创建产品目录
2. 创建 README.md 定义模块规范
3. 创建 memory-bank/ 并编写文档
4. 实现功能代码
5. 在 main.py 中注册路由
6. 在 config.py 中添加启用开关

### 5.2 开发原则

| 原则 | 说明 |
|------|------|
| 文档先行 | 先写 memory-bank 文档，再写代码 |
| 小步快跑 | 每步只做一件事，立即测试 |
| 复用优先 | 优先使用 services 已有能力 |
| 不破坏现有 | 任何改动不能影响其他产品 |

### 5.3 API 路由规范

```python
# routes.py 示例
from fastapi import APIRouter

router = APIRouter(
    prefix="/api/xxx",      # 产品前缀
    tags=["产品名称"]
)

@router.post("/action")
async def action():
    pass
```

---

## 六、启用控制

### 6.1 环境变量

```bash
# .env
ENABLE_AI_CHATBOT=true
ENABLE_AGENT_WORKBENCH=true
ENABLE_NOTIFICATION=false
```

### 6.2 main.py 注册

```python
if config.ENABLE_XXX:
    from products.xxx.routes import router
    app.include_router(router)
```

---

## 七、测试要求

- 每个产品必须有 tests/ 目录
- 核心功能必须有单元测试
- 新功能必须通过测试才能提交
- 不能破坏现有测试

---

## 八、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-18 | 初始版本 |
