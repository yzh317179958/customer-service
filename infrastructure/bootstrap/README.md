# 启动引导组件规范

> **组件定位**：应用启动引导、组件工厂、依赖注入
> **组件状态**：已完成
> **最后更新**：2025-12-21

---

## 一、组件职责

- 提供组件工厂（BootstrapFactory），按需初始化组件
- 管理组件依赖关系，自动解析初始化顺序
- 暴露依赖注入接口，供服务层注册实现
- 提供组件实例的统一获取方式

---

## 二、支持的组件

| 组件 | 枚举值 | 依赖 | 说明 |
|------|--------|------|------|
| REDIS | `Component.REDIS` | 无 | Redis 连接、会话存储 |
| COZE | `Component.COZE` | 无 | Coze AI 客户端 |
| REGULATOR | `Component.REGULATOR` | 无 | 监管引擎（人工接管） |
| AGENT_AUTH | `Component.AGENT_AUTH` | REDIS | 坐席认证系统 |
| TICKET | `Component.TICKET` | REDIS | 工单系统 |
| SSE | `Component.SSE` | 无 | SSE 队列管理 |
| SCHEDULER | `Component.SCHEDULER` | 无 | 后台任务调度 |

---

## 三、目录结构

```
infrastructure/bootstrap/
├── __init__.py          # 模块导出
├── README.md            # 本文档
├── factory.py           # 组件工厂（BootstrapFactory）
├── redis.py             # Redis/Session 初始化
├── coze.py              # Coze Client 初始化
├── auth.py              # 坐席认证系统初始化
├── ticket.py            # 工单系统初始化
├── sse.py               # SSE 队列管理
└── scheduler.py         # 后台任务调度器
```

---

## 四、核心接口

### 4.1 组件工厂

```python
from infrastructure.bootstrap import BootstrapFactory, Component

# 创建工厂实例
factory = BootstrapFactory()

# 按需初始化组件（自动解析依赖）
instances = factory.init_components([
    Component.REDIS,
    Component.COZE,
    Component.SSE,
])

# 获取组件实例
regulator = factory.get_instance(Component.REGULATOR)
```

### 4.2 Getter 函数

```python
from infrastructure.bootstrap import (
    # Redis
    get_redis_client,
    get_session_store,
    is_redis_enabled,

    # Coze
    get_coze_client,
    get_token_manager,
    get_jwt_oauth_app,
    get_workflow_id,
    get_app_id,

    # Agent Auth
    get_agent_manager,
    get_agent_token_manager,

    # Ticket
    get_ticket_store,
    get_ticket_template_store,
    get_audit_log_store,
    get_quick_reply_store,

    # SSE
    get_sse_queues,
    get_or_create_sse_queue,
    enqueue_sse_message,
)
```

### 4.3 依赖注入注册

```python
from infrastructure.bootstrap import (
    register_session_store_impls,
    register_ticket_store_impls,
    register_token_manager_factory,
    register_component_initializer,
    register_warmup_service_factory,
)

# 注册自定义组件初始化器
register_component_initializer(Component.REGULATOR, my_init_func)
```

---

## 五、启动流程

```
1. 创建 BootstrapFactory 实例
   │
2. 调用 init_components([...])
   │
   ├─ 解析依赖关系（拓扑排序）
   │
   ├─ 按顺序初始化各组件
   │   ├─ REDIS → init_redis()
   │   ├─ COZE → init_coze_client()
   │   ├─ AGENT_AUTH → init_agent_auth()
   │   ├─ TICKET → init_ticket_system()
   │   └─ SSE → get_sse_queues()
   │
3. 启动后台任务
   │
   └─ start_background_tasks()
       start_warmup_scheduler()
```

---

## 六、使用示例

### 6.1 全家桶模式（backend.py）

```python
from infrastructure.bootstrap import (
    BootstrapFactory, Component,
    get_session_store, get_coze_client,
    start_background_tasks, start_warmup_scheduler,
)

factory = BootstrapFactory()
factory.init_components([
    Component.REDIS,
    Component.COZE,
    Component.REGULATOR,
    Component.AGENT_AUTH,
    Component.TICKET,
    Component.SSE,
])

# 获取组件实例
session_store = get_session_store()
coze_client = get_coze_client()

# 启动后台任务
start_background_tasks(ticket_store, agent_manager, sse_queues)
start_warmup_scheduler()
```

### 6.2 独立模式（products/xxx/lifespan.py）

```python
import services.bootstrap  # 注册服务层实现

from infrastructure.bootstrap import BootstrapFactory, Component

factory = BootstrapFactory()
factory.init_components([
    Component.REDIS,
    Component.COZE,
    Component.SSE,
])
```

---

## 七、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-21 | 初始版本 |
