# Infrastructure 基础设施层规范

> **层级定位**：底层技术组件，无业务逻辑
> **最后更新**：2025-12-18

---

## 一、层级职责

基础设施层提供底层技术能力：

- 纯技术封装，无业务逻辑
- 被 services 和 products 依赖
- 提供通用的技术组件

---

## 二、当前组件清单

| 组件 | 目录 | 状态 | 说明 |
|------|------|------|------|
| 数据库 | database/ | 待迁移 | Redis 连接管理 |
| 定时任务 | scheduler/ | 待迁移 | APScheduler 封装 |
| 日志 | logging/ | 待创建 | 日志配置 |
| 监控 | monitoring/ | 待迁移 | 健康检查、指标 |
| 安全 | security/ | 待创建 | 限流、校验 |

---

## 三、依赖规则

### 3.1 允许的依赖

```python
# ✅ 可以依赖 Python 标准库和第三方库
import redis
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
```

### 3.2 禁止的依赖

```python
# ❌ 禁止依赖 services 层
from services.shopify import xxx  # 禁止！

# ❌ 禁止依赖 products 层
from products.ai_chatbot import xxx  # 禁止！
```

---

## 四、组件目录结构

```
infrastructure/xxx/
├── __init__.py          # 模块初始化，导出公开接口
├── README.md            # 【必须】组件规范文档
├── client.py            # 客户端/连接管理
├── config.py            # 配置（如有）
└── tests/               # 单元测试
```

---

## 五、开发规范

### 5.1 设计原则

| 原则 | 说明 |
|------|------|
| 无业务逻辑 | 只做技术封装 |
| 简单通用 | 接口简洁，易于使用 |
| 可配置 | 通过环境变量配置 |
| 高可用 | 连接池、重试、超时 |

### 5.2 组件模板

```python
# client.py 示例
import os
from typing import Optional

class XxxClient:
    """组件说明"""

    _instance: Optional["XxxClient"] = None

    def __init__(self):
        self.config = self._load_config()

    def _load_config(self):
        return {
            "host": os.getenv("XXX_HOST", "localhost"),
            "port": int(os.getenv("XXX_PORT", "6379")),
        }

    @classmethod
    def get_instance(cls) -> "XxxClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


# 便捷函数
def get_xxx_client() -> XxxClient:
    return XxxClient.get_instance()
```

---

## 六、测试要求

- 每个组件必须有单元测试
- 测试连接、超时、异常处理

---

## 七、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-18 | 初始版本 |
