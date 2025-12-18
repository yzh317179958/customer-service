# 监控组件规范

> **组件定位**：健康检查与指标监控
> **组件状态**：待迁移
> **最后更新**：2025-12-18

---

## 一、组件职责

- 服务健康检查
- 性能指标采集
- 告警通知

---

## 二、公开接口

```python
class HealthChecker:
    async def check_all(self) -> dict
    async def check_redis(self) -> bool
    async def check_coze(self) -> bool

def get_health_checker() -> HealthChecker
```

---

## 三、目录结构

```
infrastructure/monitoring/
├── __init__.py
├── README.md           # 本文档
├── health.py           # 健康检查
├── metrics.py          # 指标采集
└── tests/
    └── test_health.py
```

---

## 四、健康检查端点

| 端点 | 说明 |
|------|------|
| /health | 服务健康状态 |
| /health/ready | 就绪检查 |
| /health/live | 存活检查 |

---

## 五、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-18 | 初始版本 |
