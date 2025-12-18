# 工单服务规范

> **服务定位**：工单 CRUD 与 SLA 管理
> **服务状态**：已完成
> **最后更新**：2025-12-18

---

## 一、服务职责

- 工单创建、查询、更新
- 工单分配与转派
- SLA 时效管理
- 工单状态流转

---

## 二、公开接口

```python
class TicketService:
    async def create_ticket(self, data: dict) -> dict
    async def get_ticket(self, ticket_id: str) -> dict
    async def update_ticket(self, ticket_id: str, data: dict) -> dict
    async def assign_ticket(self, ticket_id: str, agent_id: str) -> bool

def get_ticket_service() -> TicketService
```

---

## 三、目录结构

```
services/ticket/
├── __init__.py
├── README.md           # 本文档
├── service.py          # 工单服务
├── models.py           # 数据模型
└── tests/
    └── test_ticket.py
```

---

## 四、工单状态

| 状态 | 说明 |
|------|------|
| open | 新建 |
| assigned | 已分配 |
| in_progress | 处理中 |
| resolved | 已解决 |
| closed | 已关闭 |

---

## 五、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-18 | 初始版本 |
