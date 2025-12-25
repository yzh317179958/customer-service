# Services 服务层规范

> **层级定位**：可复用的业务服务，被多个产品共享
> **最后更新**：2025-12-23
> **文档版本**：v2.0

---

## 一、层级职责

服务层封装可复用的业务能力：

- 被多个产品（微服务）共享调用
- 封装外部 API 调用（Shopify、Coze、17track 等）
- 封装业务数据操作（工单、会话、邮件记录）
- 无独立 API 端点（通过产品层暴露）
- 支持 PostgreSQL + Redis 双写策略

---

## 二、当前服务清单

| 服务 | 目录 | 状态 | 说明 |
|------|------|------|------|
| 依赖注入 | bootstrap/ | ✅ 已完成 | 服务注册到基础设施层 |
| Shopify 订单 | shopify/ | ✅ 已完成 | 多站点订单查询、缓存预热 |
| 邮件服务 | email/ | ✅ 已完成 | SMTP 邮件发送、记录存储 |
| Coze AI | coze/ | ✅ 已完成 | AI 对话、JWT 签名、Token 管理 |
| 工单服务 | ticket/ | ✅ 已完成 | 工单 CRUD、分配、SLA、审计 |
| 会话服务 | session/ | ✅ 已完成 | 会话状态、归档、Redis 存储 |
| 素材服务 | asset/ | ✅ 已完成 | 产品图片匹配、CDN 素材 |
| 物流追踪 | tracking/ | ✅ 已完成 | 17track API 集成、运单注册 |
| 计费服务 | billing/ | 📋 规划中 | 套餐、订阅、用量统计 |

---

## 三、依赖规则

### 3.1 允许的依赖

```python
# ✅ 可以依赖 infrastructure 层
from infrastructure.database import get_redis_client, get_async_session
from infrastructure.database.models import Ticket, Agent
from infrastructure.log import logger

# ✅ 可以依赖同层其他服务（谨慎使用）
from services.session import SessionService
from services.shopify import search_order_across_sites
```

### 3.2 禁止的依赖

```python
# ❌ 禁止依赖 products 层
from products.ai_chatbot import xxx  # 禁止！
from products.agent_workbench import xxx  # 禁止！
```

---

## 四、数据库双写策略

服务层统一采用 PostgreSQL + Redis 双写模式：

```
写入流程：
1. 先写入 PostgreSQL（主存储，数据源）
2. 再写入 Redis（缓存，高频访问）
3. Redis 失败重试一次，仍失败则记录日志但不阻塞业务

读取流程：
1. 优先从 PostgreSQL 查询（保证数据一致性）
2. PostgreSQL 失败时降级到 Redis/内存
```

**支持双写的服务：**

| 服务 | 双写模块 | 说明 |
|------|----------|------|
| ticket/ | store.py | 工单存储 |
| ticket/ | audit.py | 审计日志 |
| session/ | archive.py | 会话归档 |
| email/ | service.py | 邮件记录 |

---

## 五、服务目录结构

```
services/xxx/
├── __init__.py          # 模块初始化，导出公开接口
├── README.md            # 【必须】服务规范文档
├── client.py            # 外部 API 客户端（如有）
├── service.py           # 业务服务类
├── models.py            # Pydantic 数据模型（如有）
├── store.py             # 数据存储（如有，支持双写）
├── cache.py             # 缓存逻辑（如有）
└── tests/               # 单元测试
```

---

## 六、开发规范

### 6.1 新建服务流程

1. 在 services/ 下创建服务目录
2. 创建 README.md 定义服务接口
3. 如需数据库，在 infrastructure/database/models/ 创建 ORM 模型
4. 如需迁移，创建 Alembic migration
5. 实现服务代码
6. 编写单元测试
7. 在使用的产品中 import

### 6.2 接口设计原则

| 原则 | 说明 |
|------|------|
| 简洁清晰 | 接口命名直观，参数明确 |
| 封装内部实现 | 不暴露内部细节 |
| 异常处理 | 统一的异常定义和处理 |
| 向后兼容 | 修改接口时保持兼容 |
| 双写支持 | 数据操作支持 PG + Redis |

### 6.3 服务类模板

```python
# service.py 示例
from typing import Optional, List
from infrastructure.database import get_async_session, get_redis_client

class XxxService:
    """服务说明"""

    def __init__(self):
        self.redis = get_redis_client()

    async def get_xxx(self, id: str) -> Optional[dict]:
        """获取 xxx"""
        # 优先从 PostgreSQL 查询
        async with get_async_session() as session:
            result = await session.execute(...)
            return result

    async def create_xxx(self, data: dict) -> dict:
        """创建 xxx（双写）"""
        # 1. 写入 PostgreSQL
        async with get_async_session() as session:
            obj = XxxModel(**data)
            session.add(obj)
            await session.commit()

        # 2. 写入 Redis 缓存
        await self.redis.setex(f"xxx:{obj.id}", 3600, json.dumps(data))

        return obj


# 全局实例
_service: Optional[XxxService] = None

def get_xxx_service() -> XxxService:
    global _service
    if _service is None:
        _service = XxxService()
    return _service
```

---

## 七、外部 API 客户端模板

```python
# client.py 示例
import os
import httpx
from typing import Optional, Dict, Any

class XxxClient:
    """外部 API 客户端"""

    DEFAULT_BASE_URL = "https://api.example.com/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or os.getenv("XXX_API_KEY")
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def get_something(self, id: str) -> Dict[str, Any]:
        client = await self._get_client()
        response = await client.get(f"{self.base_url}/something/{id}")
        return response.json()


# 全局客户端
_client: Optional[XxxClient] = None

def get_xxx_client() -> XxxClient:
    global _client
    if _client is None:
        _client = XxxClient()
    return _client
```

---

## 八、测试要求

- 每个服务必须有单元测试
- 覆盖核心方法
- Mock 外部依赖（API、数据库）
- 测试双写逻辑

---

## 九、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0 | 2025-12-23 | 更新服务清单，添加双写策略说明，更新代码模板 |
| v1.0 | 2025-12-18 | 初始版本 |
