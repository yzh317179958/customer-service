# 定时任务组件规范

> **组件定位**：APScheduler 封装
> **组件状态**：待迁移
> **最后更新**：2025-12-18

---

## 一、组件职责

- 定时任务调度
- Cron 表达式支持
- 任务持久化

---

## 二、公开接口

```python
class Scheduler:
    def add_job(self, func, trigger, **kwargs) -> str
    def remove_job(self, job_id: str) -> bool
    def start(self) -> None
    def shutdown(self) -> None

def get_scheduler() -> Scheduler
```

---

## 三、目录结构

```
infrastructure/scheduler/
├── __init__.py
├── README.md           # 本文档
├── scheduler.py        # 调度器
├── config.py           # 配置
└── tests/
    └── test_scheduler.py
```

---

## 四、使用示例

```python
from infrastructure.scheduler import get_scheduler

scheduler = get_scheduler()
scheduler.add_job(
    my_task,
    CronTrigger(hour='10,16', minute=0),
    id='daily_task'
)
```

---

## 五、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-18 | 初始版本 |
