# 服务层 Bootstrap 注册模块规范

> **模块定位**：服务层依赖注入注册，连接 services 与 infrastructure
> **模块状态**：已完成
> **最后更新**：2025-12-21

---

## 一、模块职责

- 将服务层实现类注册到基础设施层的依赖注入接口
- 确保 `infrastructure/bootstrap` 无需直接 import `services`
- 遵循三层架构的单向依赖原则

---

## 二、设计原理

```
┌─────────────────────────────────────────────────────────────┐
│  products/xxx/lifespan.py                                   │
│                                                             │
│  import services.bootstrap  # ← 触发注册                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  services/bootstrap/__init__.py                             │
│                                                             │
│  register_session_store_impls(RedisSessionStore, ...)       │
│  register_ticket_store_impls(TicketStore, ...)              │
│  register_token_manager_factory(OAuthTokenManager.from_env) │
│  register_component_initializer(REGULATOR, _init_regulator) │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  infrastructure/bootstrap/factory.py                        │
│                                                             │
│  使用注册的实现类初始化组件                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、注册的实现类

| 注册函数 | 注册内容 | 来源模块 |
|----------|----------|----------|
| `register_session_store_impls` | RedisSessionStore, InMemorySessionStore | services.session |
| `register_ticket_store_impls` | TicketStore, TicketTemplateStore, AuditLogStore, QuickReplyStore | services.ticket |
| `register_token_manager_factory` | OAuthTokenManager.from_env | services.coze |
| `register_component_initializer` | Regulator 初始化函数 | services.session |
| `register_warmup_service_factory` | get_warmup_service | services.shopify |

---

## 四、使用方式

在产品层的 `lifespan.py` 中导入即可完成注册：

```python
# products/xxx/lifespan.py
import services.bootstrap  # noqa: F401  # 确保服务层依赖注册
```

**注意**：只需导入一次，后续的 `BootstrapFactory.init_components()` 会自动使用注册的实现。

---

## 五、目录结构

```
services/bootstrap/
├── __init__.py          # 注册逻辑（核心文件）
└── README.md            # 本文档
```

---

## 六、扩展指南

添加新的服务注册：

1. 在 `infrastructure/bootstrap` 中添加注册接口函数
2. 在 `services/bootstrap/__init__.py` 中调用注册函数

```python
# infrastructure/bootstrap/xxx.py
_xxx_factory = None

def register_xxx_factory(factory):
    global _xxx_factory
    _xxx_factory = factory

# services/bootstrap/__init__.py
from infrastructure.bootstrap import register_xxx_factory
from services.xxx import XxxService

register_xxx_factory(XxxService.create)
```

---

## 七、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-21 | 初始版本 |
