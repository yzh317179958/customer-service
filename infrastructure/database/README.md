# 数据库组件规范

> **组件定位**：Redis 连接管理
> **组件状态**：待迁移
> **最后更新**：2025-12-18

---

## 一、组件职责

- Redis 连接池管理
- 连接健康检查
- 自动重连机制

---

## 二、公开接口

```python
class RedisClient:
    def get_connection(self) -> Redis
    async def ping(self) -> bool

def get_redis_client() -> RedisClient
```

---

## 三、目录结构

```
infrastructure/database/
├── __init__.py
├── README.md           # 本文档
├── client.py           # Redis 客户端
├── config.py           # 配置
└── tests/
    └── test_redis.py
```

---

## 四、配置项

| 环境变量 | 说明 |
|----------|------|
| REDIS_HOST | Redis 主机 |
| REDIS_PORT | Redis 端口 |
| REDIS_PASSWORD | Redis 密码 |
| REDIS_DB | Redis 数据库 |

---

## 五、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-18 | 初始版本 |
