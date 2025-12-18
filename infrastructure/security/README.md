# 安全组件规范

> **组件定位**：限流与安全校验
> **组件状态**：待创建
> **最后更新**：2025-12-18

---

## 一、组件职责

- API 请求限流
- IP 黑名单管理
- 输入参数校验

---

## 二、公开接口

```python
class RateLimiter:
    def check(self, key: str) -> bool
    def block(self, key: str, duration: int) -> None

class IPBlacklist:
    def is_blocked(self, ip: str) -> bool
    def add(self, ip: str, duration: int) -> None
    def remove(self, ip: str) -> None

def get_rate_limiter() -> RateLimiter
def get_ip_blacklist() -> IPBlacklist
```

---

## 三、目录结构

```
infrastructure/security/
├── __init__.py
├── README.md           # 本文档
├── rate_limiter.py     # 限流器
├── blacklist.py        # IP 黑名单
├── validator.py        # 输入校验
└── tests/
    └── test_security.py
```

---

## 四、限流配置

| 场景 | 限制 |
|------|------|
| 对话接口 | 20 次/分钟/IP |
| 订单查询 | 10 次/分钟/IP |
| 全局 | 1000 次/分钟 |

---

## 五、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-18 | 初始版本 |
