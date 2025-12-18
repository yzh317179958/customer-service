# 坐席工作台模块规范

> **模块定位**：人工客服后台管理系统
> **模块状态**：已上线
> **最后更新**：2025-12-18

---

## 一、模块职责

坐席工作台模块提供：

- 待接入会话列表
- 实时对话界面
- 会话接管/转回
- 工单管理

---

## 二、API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| /api/agent/sessions | GET | 获取会话列表 |
| /api/agent/takeover | POST | 接管会话 |
| /api/agent/release | POST | 释放会话 |
| /api/agent/send | POST | 发送消息 |

---

## 三、依赖服务

```python
# 允许的依赖
from services.session import SessionService
from services.ticket import TicketService
from infrastructure.database import get_redis_client
```

---

## 四、目录结构

```
products/agent_workbench/
├── __init__.py
├── README.md            # 本文档
├── routes.py            # API 路由
├── handlers/
│   ├── session_handler.py
│   └── message_handler.py
├── memory-bank/         # Vibe Coding 文档
│   ├── prd.md
│   ├── tech-stack.md
│   ├── implementation-plan.md
│   ├── progress.md
│   └── architecture.md
└── tests/
    └── test_agent.py
```

---

## 五、核心约束

### 5.1 鉴权要求

- 所有 API 必须 JWT 认证
- 坐席必须登录后才能操作

### 5.2 会话状态同步

- 接管后必须同步到 Redis
- AI 客服必须感知接管状态

---

## 六、配置项

| 环境变量 | 说明 |
|----------|------|
| ENABLE_AGENT_WORKBENCH | 模块启用开关 |
| JWT_SECRET_KEY | JWT 密钥 |

---

## 七、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-18 | 初始版本 |
