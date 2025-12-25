# 安全控制架构分析计划

> **分析目标**: 评估限流/安全控制应该独立模块还是融入产品
> **创建日期**: 2025-12-24
> **状态**: 分析中

---

## 一、问题背景

### 1.1 当前需求

`implementation-plan.md` Phase 2 中定义的限流控制:
- Step 2.1: 添加 slowapi 依赖
- Step 2.2: main.py 集成限流中间件
- Step 2.3: chat 端点添加限流装饰器
- Step 2.4: 监控指标端点

### 1.2 未来扩展需求

- AI 客服需要限流
- 坐席工作台需要限流
- 未来其他产品也需要限流
- 可能还有其他安全控制措施 (IP 黑名单、输入校验、防刷等)

---

## 二、现有架构分析

### 2.1 三层架构

```
products/          # 产品层 - 独立微服务
├── ai_chatbot/    # AI 智能客服 (端口 8000)
└── agent_workbench/  # 坐席工作台 (端口 8002)

services/          # 服务层 - 可复用业务服务
└── (无安全服务)

infrastructure/    # 基础设施层 - 底层技术组件
└── security/      # 已有: JWT 签名、坐席认证
    ├── jwt_signer.py
    └── agent_auth.py
```

### 2.2 现有 security 模块规划

`infrastructure/security/README.md` 已规划但未实现:
- `rate_limiter.py` - 限流器
- `blacklist.py` - IP 黑名单
- `validator.py` - 输入校验

---

## 三、方案对比

### 方案 A: 融入各产品模块

```
products/ai_chatbot/
├── main.py              # 直接集成 slowapi
└── middleware/
    └── rate_limit.py    # 产品特定限流逻辑

products/agent_workbench/
├── main.py              # 直接集成 slowapi
└── middleware/
    └── rate_limit.py    # 产品特定限流逻辑
```

**优点:**
- 简单直接，快速实现
- 每个产品可以有独立的限流策略
- 符合微服务独立部署原则

**缺点:**
- 代码重复，每个产品都要写一遍
- 限流配置分散，难以统一管理
- 新产品需要从头实现

---

### 方案 B: 放入 infrastructure/security (推荐)

```
infrastructure/security/
├── __init__.py          # 导出公开接口
├── README.md            # 规范文档
├── jwt_signer.py        # 已有 - JWT 签名
├── agent_auth.py        # 已有 - 坐席认证
├── rate_limiter.py      # 新增 - 通用限流器
├── blacklist.py         # 新增 - IP 黑名单
├── validator.py         # 新增 - 输入校验
└── middleware.py        # 新增 - FastAPI 中间件工厂

products/ai_chatbot/main.py:
  from infrastructure.security import create_rate_limiter
  limiter = create_rate_limiter(config=AI_CHATBOT_CONFIG)

products/agent_workbench/main.py:
  from infrastructure.security import create_rate_limiter
  limiter = create_rate_limiter(config=WORKBENCH_CONFIG)
```

**优点:**
- 代码复用，减少重复
- 统一管理安全策略
- 新产品快速接入
- 符合架构分层原则 (infrastructure 是底层技术组件)
- 与现有 security 模块定位一致

**缺点:**
- 需要设计通用接口
- 初期开发成本稍高

---

### 方案 C: 放入 services 层

```
services/security/
├── rate_limiter.py
├── blacklist.py
└── validator.py
```

**优点:**
- services 层支持业务逻辑

**缺点:**
- 限流是技术组件，不是业务服务
- 与 services 层 "可复用业务服务" 定位不符
- infrastructure 已有 security 模块，会造成混乱

---

## 四、推荐方案: B (infrastructure/security 扩展)

### 4.1 理由

1. **架构一致性**: infrastructure 层已有 security 模块，扩展它是自然选择
2. **职责清晰**: 限流是技术组件，无业务逻辑，属于基础设施
3. **代码复用**: 所有产品共享同一套实现
4. **配置灵活**: 每个产品可以传入不同配置
5. **已有规划**: README.md 已规划 rate_limiter.py 等文件

### 4.2 设计原则

```python
# infrastructure/security/rate_limiter.py

from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional, Dict, Callable

class RateLimiterConfig:
    """限流配置"""
    def __init__(
        self,
        default_limit: str = "60/minute",
        storage_uri: Optional[str] = None,  # Redis URI
        key_func: Callable = get_remote_address,
        endpoint_limits: Optional[Dict[str, str]] = None,
    ):
        self.default_limit = default_limit
        self.storage_uri = storage_uri
        self.key_func = key_func
        self.endpoint_limits = endpoint_limits or {}


def create_rate_limiter(config: RateLimiterConfig) -> Limiter:
    """创建限流器实例"""
    return Limiter(
        key_func=config.key_func,
        default_limits=[config.default_limit],
        storage_uri=config.storage_uri,
    )
```

### 4.3 产品层使用方式

```python
# products/ai_chatbot/main.py

from infrastructure.security import create_rate_limiter, RateLimiterConfig
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# AI 客服限流配置
config = RateLimiterConfig(
    default_limit="60/minute",
    storage_uri=os.getenv("REDIS_URL"),
    endpoint_limits={
        "/api/chat/stream": "10/minute",
        "/api/tracking/{order_number}": "30/minute",
    }
)

limiter = create_rate_limiter(config)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

```python
# products/agent_workbench/main.py

from infrastructure.security import create_rate_limiter, RateLimiterConfig

# 坐席工作台限流配置 (比客服宽松)
config = RateLimiterConfig(
    default_limit="120/minute",
    storage_uri=os.getenv("REDIS_URL"),
)

limiter = create_rate_limiter(config)
```

---

## 五、实施计划

### Phase 1: 扩展 infrastructure/security

1. 创建 `infrastructure/security/rate_limiter.py`
   - RateLimiterConfig 类
   - create_rate_limiter() 工厂函数
   - FastAPI 中间件集成帮助函数

2. 创建 `infrastructure/security/blacklist.py` (预留)
   - IPBlacklist 类
   - Redis 存储支持

3. 更新 `infrastructure/security/__init__.py`
   - 导出新接口

### Phase 2: AI 客服集成

1. `products/ai_chatbot/main.py` 集成限流
2. 配置端点级限流规则
3. 测试验证

### Phase 3: 坐席工作台集成

1. `products/agent_workbench/main.py` 集成限流
2. 配置适合坐席的限流规则
3. 测试验证

---

## 六、结论

**推荐: 方案 B - 放入 infrastructure/security**

原因:
1. 符合三层架构设计原则
2. infrastructure 已有 security 模块，是自然扩展
3. 技术组件不是业务服务，不应放 services
4. 代码复用，配置灵活
5. 便于统一管理和未来扩展

---

## 七、待确认问题

1. 是否需要支持分布式限流 (Redis 存储)?
2. 限流超出后返回的错误格式是否需要统一?
3. 是否需要限流监控指标 (Prometheus)?
4. IP 黑名单是否需要动态配置 (API 管理)?
