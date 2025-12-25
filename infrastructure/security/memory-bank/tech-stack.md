# 安全防护组件 - 技术栈

> **版本**: v1.0
> **创建日期**: 2025-12-24
> **模块位置**: `infrastructure/security/`

---

## 1. 复用现有技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 基础设施层 | `infrastructure/security/` | 本模块位置，扩展现有安全组件 |
| 数据存储 | Redis | 限流计数、黑名单存储（已有） |
| Web 框架 | FastAPI | 中间件集成（已有） |
| 认证 | JWT + bcrypt | 坐席认证（已有 `agent_auth.py`） |

---

## 2. 新增依赖

| 依赖 | 版本 | 用途 | 原因 |
|------|------|------|------|
| `slowapi` | 0.1.9 | API 请求限流 | 成熟的 FastAPI 限流库，基于 limits |
| `prometheus-client` | 0.19.0 | 监控指标暴露 | Prometheus 标准格式，便于 Grafana 集成 |

**requirements.txt 新增：**
```
slowapi==0.1.9
prometheus-client==0.19.0
```

---

## 3. 现有模块分析

### 3.1 已有文件（保留）

```
infrastructure/security/
├── __init__.py          # 模块导出
├── README.md            # 组件规范
├── jwt_signer.py        # Coze JWT 签名（已完成）
└── agent_auth.py        # 坐席认证系统（已完成）
    ├── PasswordHasher   # 密码加密
    ├── AgentTokenManager # JWT Token 管理
    ├── AgentManager     # 坐席账号管理
    └── create_jwt_dependencies() # FastAPI 依赖注入
```

### 3.2 新增文件（待开发）

```
infrastructure/security/
├── rate_limiter.py      # 【新增】通用限流器
├── blacklist.py         # 【新增】IP 黑名单
├── middleware.py        # 【新增】FastAPI 中间件工厂
├── validators.py        # 【新增】输入校验工具
├── metrics.py           # 【新增】Prometheus 指标
└── config.py            # 【新增】安全配置模型
```

---

## 4. 数据存储方案

### 4.1 Redis 数据结构

**限流计数（使用 slowapi 内置）：**
```
# slowapi 默认使用 Redis 存储
# Key 格式: LIMITER/{endpoint}/{identifier}
# 示例: LIMITER:/api/chat/stream/192.168.1.1
```

**IP 黑名单：**
```redis
# Hash 结构存储黑名单
HSET security:blacklist:ip {ip} {json_data}

# 示例
HSET security:blacklist:ip "192.168.1.100" '{"reason":"auto_ban","expires_at":1735084800,"created_at":1735000000}'

# 支持过期时间的单独 Key（用于自动解封）
SETEX security:blacklist:ip:192.168.1.100 600 "1"
```

**登录失败计数：**
```redis
# String + TTL
SETEX security:login_failures:{username} 900 {count}

# 示例：admin 用户失败 3 次，15 分钟后重置
SETEX security:login_failures:admin 900 "3"
```

**账户锁定：**
```redis
# String + TTL
SETEX security:account_locked:{username} 900 "1"
```

### 4.2 无 PostgreSQL 依赖

安全组件不需要持久化存储：
- 限流计数：临时数据，Redis 足够
- 黑名单：Redis 持久化即可，重启后保留
- 登录失败：临时计数，自动过期

---

## 5. API 设计

### 5.1 对外接口（供产品层使用）

```python
# infrastructure/security/__init__.py 导出

# 限流器
from .rate_limiter import (
    RateLimiterConfig,
    create_rate_limiter,
    get_rate_limit_handler,
)

# IP 黑名单
from .blacklist import (
    IPBlacklist,
    get_ip_blacklist,
)

# 中间件
from .middleware import (
    create_security_middleware,
    SecurityMiddlewareConfig,
)

# 输入校验
from .validators import (
    validate_message_length,
    sanitize_input,
)

# 监控指标
from .metrics import (
    security_metrics,
    get_metrics_handler,
)

# 现有导出（保持不变）
from .jwt_signer import JWTSigner
from .agent_auth import (
    AgentManager,
    AgentTokenManager,
    # ... 其他
)
```

### 5.2 产品层使用示例

**AI 智能客服接入：**
```python
# products/ai_chatbot/main.py
from infrastructure.security import (
    create_rate_limiter,
    RateLimiterConfig,
    create_security_middleware,
)
from slowapi.errors import RateLimitExceeded

# 配置限流
config = RateLimiterConfig(
    default_limit="60/minute",
    storage_uri=os.getenv("REDIS_URL"),
    endpoint_limits={
        "/api/chat/stream": "10/minute",
        "/api/chat": "10/minute",
        "/api/tracking/{tracking_number}": "30/minute",
    }
)

limiter = create_rate_limiter(config)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, get_rate_limit_handler())
```

**坐席工作台接入：**
```python
# products/agent_workbench/main.py
from infrastructure.security import (
    create_rate_limiter,
    RateLimiterConfig,
)

config = RateLimiterConfig(
    default_limit="120/minute",
    storage_uri=os.getenv("REDIS_URL"),
    endpoint_limits={
        "/agent/login": "5/minute",
        "/agent/refresh": "10/minute",
    }
)

limiter = create_rate_limiter(config)
```

---

## 6. 核心类设计

### 6.1 RateLimiterConfig

```python
@dataclass
class RateLimiterConfig:
    """限流配置"""
    default_limit: str = "60/minute"
    storage_uri: Optional[str] = None  # Redis URI，None 则使用内存
    key_func: Callable = get_remote_address  # IP 提取函数
    endpoint_limits: Dict[str, str] = field(default_factory=dict)

    # 错误响应配置
    error_message: str = "Too many requests. Please try again later."
    retry_after_header: bool = True
```

### 6.2 IPBlacklist

```python
class IPBlacklist:
    """IP 黑名单管理"""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.prefix = "security:blacklist:ip"

    async def is_blocked(self, ip: str) -> bool:
        """检查 IP 是否被封禁"""

    async def add(self, ip: str, duration: int, reason: str) -> None:
        """添加 IP 到黑名单"""

    async def remove(self, ip: str) -> bool:
        """移除 IP"""

    async def list_all(self) -> List[Dict]:
        """列出所有被封禁的 IP"""
```

### 6.3 LoginProtector

```python
class LoginProtector:
    """登录保护（防暴力破解）"""

    def __init__(self, redis_client, max_failures: int = 5, lockout_duration: int = 900):
        self.redis = redis_client
        self.max_failures = max_failures
        self.lockout_duration = lockout_duration

    async def record_failure(self, username: str) -> int:
        """记录登录失败，返回失败次数"""

    async def is_locked(self, username: str) -> bool:
        """检查账户是否被锁定"""

    async def reset(self, username: str) -> None:
        """重置失败计数（登录成功后调用）"""
```

---

## 7. 中间件集成

### 7.1 FastAPI 中间件

```python
# middleware.py

class SecurityMiddleware:
    """统一安全中间件"""

    def __init__(self, app, config: SecurityMiddlewareConfig):
        self.app = app
        self.config = config
        self.blacklist = IPBlacklist(config.redis_client)

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # 1. 检查 IP 黑名单
            client_ip = get_client_ip(scope)
            if await self.blacklist.is_blocked(client_ip):
                return await self._send_blocked_response(send)

            # 2. 限流检查由 slowapi 装饰器处理

        await self.app(scope, receive, send)
```

### 7.2 端点装饰器

```python
# 在 handler 中使用
from infrastructure.security import limiter

@router.post("/chat/stream")
@limiter.limit("10/minute")
async def chat_stream(request: ChatRequest):
    # 消息长度校验
    validate_message_length(request.message, max_length=1000)
    ...
```

---

## 8. 监控指标

### 8.1 Prometheus 指标

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge

# 限流触发次数
rate_limit_hits = Counter(
    'security_rate_limit_hits_total',
    'Total rate limit hits',
    ['endpoint', 'product']
)

# IP 封禁数量
blocked_ips = Gauge(
    'security_blocked_ips',
    'Current number of blocked IPs'
)

# 登录失败次数
login_failures = Counter(
    'security_login_failures_total',
    'Total login failures',
    ['username']
)

# 请求处理时间（安全检查开销）
security_check_duration = Histogram(
    'security_check_duration_seconds',
    'Time spent on security checks',
    ['check_type']
)
```

### 8.2 指标端点

```python
# 在产品 main.py 中添加
from infrastructure.security.metrics import get_metrics_handler

app.add_route("/metrics", get_metrics_handler())
```

---

## 9. 文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-24 | 初始版本 |
