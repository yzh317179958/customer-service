# Services 服务层规范

> **层级定位**：可复用的业务服务，被多个产品共享
> **最后更新**：2025-12-18

---

## 一、层级职责

服务层封装可复用的业务能力：

- 被多个产品共享调用
- 封装外部 API 调用（Shopify、Coze 等）
- 封装业务数据操作
- 无独立 API 端点（通过产品层暴露）

---

## 二、当前服务清单

| 服务 | 目录 | 状态 | 说明 |
|------|------|------|------|
| Shopify 订单 | shopify/ | 已完成 | 多站点订单查询、物流跟踪 |
| 邮件服务 | email/ | 已完成 | SMTP 邮件发送 |
| Coze AI | coze/ | 已完成 | AI 对话、Token 管理 |
| 工单服务 | ticket/ | 已完成 | 工单 CRUD、分配、SLA |
| 会话服务 | session/ | 已完成 | 会话状态、Redis 存储 |

---

## 三、依赖规则

### 3.1 允许的依赖

```python
# ✅ 可以依赖 infrastructure 层
from infrastructure.database import get_redis_client
from infrastructure.logging import logger

# ✅ 可以依赖同层其他服务（谨慎使用）
from services.session import SessionService
```

### 3.2 禁止的依赖

```python
# ❌ 禁止依赖 products 层
from products.ai_chatbot import xxx  # 禁止！
```

---

## 四、服务目录结构

```
services/xxx/
├── __init__.py          # 模块初始化，导出公开接口
├── README.md            # 【必须】服务规范文档
├── client.py            # 外部 API 客户端（如有）
├── service.py           # 业务服务类
├── models.py            # 数据模型（如有）
├── cache.py             # 缓存逻辑（如有）
└── tests/               # 单元测试
```

---

## 五、开发规范

### 5.1 新建服务流程

1. 在 services/ 下创建服务目录
2. 创建 README.md 定义服务接口
3. 实现服务代码
4. 编写单元测试
5. 在使用的产品中 import

### 5.2 接口设计原则

| 原则 | 说明 |
|------|------|
| 简洁清晰 | 接口命名直观，参数明确 |
| 封装内部实现 | 不暴露内部细节 |
| 异常处理 | 统一的异常定义和处理 |
| 向后兼容 | 修改接口时保持兼容 |

### 5.3 服务类模板

```python
# service.py 示例
class XxxService:
    """服务说明"""

    def __init__(self):
        pass

    async def get_xxx(self, id: str) -> dict:
        """获取 xxx"""
        pass

    async def create_xxx(self, data: dict) -> dict:
        """创建 xxx"""
        pass
```

---

## 六、测试要求

- 每个服务必须有单元测试
- 覆盖核心方法
- Mock 外部依赖

---

## 七、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-18 | 初始版本 |
