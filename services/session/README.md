# 会话服务规范

> **服务定位**：会话状态管理与 Redis 存储
> **服务状态**：已完成
> **最后更新**：2025-12-18

---

## 一、服务职责

- 会话状态管理
- Redis 存储封装
- 会话超时处理
- 产品间数据共享

---

## 二、公开接口

```python
class SessionService:
    async def create_session(self, user_id: str) -> str
    async def get_session(self, session_id: str) -> dict
    async def update_session(self, session_id: str, data: dict) -> bool
    async def get_session_state(self, session_id: str) -> str
    async def set_session_state(self, session_id: str, state: str) -> bool

def get_session_service() -> SessionService
```

---

## 三、目录结构

```
services/session/
├── __init__.py
├── README.md           # 本文档
├── service.py          # 会话服务
├── models.py           # 数据模型
└── tests/
    └── test_session.py
```

---

## 四、会话状态

| 状态 | 说明 |
|------|------|
| bot_active | AI 对话中 |
| pending_manual | 等待人工接管 |
| manual_live | 人工对话中 |

---

## 五、Redis 键设计

```
session:{session_id}           # 会话数据
session:{session_id}:state     # 会话状态
session:{session_id}:messages  # 消息历史
```

---

## 六、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-18 | 初始版本 |
