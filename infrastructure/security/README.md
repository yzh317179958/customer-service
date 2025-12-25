# 安全防护组件

> **组件定位**：API 安全防护（限流、黑名单、登录保护、输入校验）
> **组件状态**：✅ Phase 1 已完成
> **最后更新**：2025-12-25

---

## 一、组件职责

| 功能 | 说明 | 防护目标 |
|------|------|----------|
| API 限流 | 限制请求频率 | CC 攻击、接口滥用 |
| IP 黑名单 | 封禁恶意 IP | 攻击者、爬虫 |
| 登录保护 | 失败锁定 | 暴力破解 |
| 输入校验 | 参数验证、XSS 防护 | 注入攻击 |
| 安全中间件 | 统一入口检查 | 请求拦截 |

---

## 二、快速开始

### 2.1 限流器

```python
from infrastructure.security import (
    create_rate_limiter,
    RateLimiterConfig,
    get_rate_limit_handler,
)
from slowapi.errors import RateLimitExceeded

# 创建限流器
config = RateLimiterConfig(
    default_limit="60/minute",
    storage_uri="redis://localhost:6379/0",  # 可选，默认内存存储
    endpoint_limits={
        "/api/chat/stream": "10/minute",
        "/api/agent/login": "5/minute",
    }
)
limiter = create_rate_limiter(config)

# 挂载到 FastAPI
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, get_rate_limit_handler())

# 在路由上使用
@app.post("/api/chat")
@limiter.limit("10/minute")
async def chat(request: Request):
    ...
```

### 2.2 IP 黑名单

```python
from infrastructure.security import IPBlacklist, init_ip_blacklist
import redis

# 初始化
redis_client = redis.Redis(host='localhost', port=6379, db=0)
blacklist = init_ip_blacklist(redis_client)

# 封禁 IP（1 小时）
await blacklist.add("192.168.1.100", duration=3600, reason="恶意请求")

# 检查是否封禁
if await blacklist.is_blocked("192.168.1.100"):
    return JSONResponse(status_code=403, content={"error": "IP blocked"})

# 解封
await blacklist.remove("192.168.1.100")

# 列出所有封禁
blocked_list = await blacklist.list_all()
```

### 2.3 登录保护

```python
from infrastructure.security import LoginProtector, init_login_protector

# 初始化（5 次失败后锁定 15 分钟）
protector = init_login_protector(redis_client)

# 登录流程
async def login(username: str, password: str):
    # 检查是否锁定
    if await protector.is_locked(username):
        remaining = await protector.get_lockout_remaining(username)
        raise HTTPException(423, f"账户已锁定，请 {remaining} 秒后重试")

    # 验证密码
    if not verify_password(password, user.password_hash):
        failures = await protector.record_failure(username)
        raise HTTPException(401, f"密码错误，已失败 {failures} 次")

    # 登录成功，重置计数
    await protector.reset(username)
    return create_token(user)
```

### 2.4 输入校验

```python
from infrastructure.security import (
    validate_message_length,
    sanitize_input,
    validate_order_number,
    validate_email,
)

# 消息长度限制
message = validate_message_length(request.message, max_length=2000)

# XSS 防护
safe_input = sanitize_input(user_input)
# <script>alert(1)</script> → &lt;script&gt;alert(1)&lt;/script&gt;

# 订单号格式验证
order_number = validate_order_number("#UK12345")  # → "UK12345"

# 邮箱验证
email = validate_email("user@example.com")
```

### 2.5 安全中间件

```python
from infrastructure.security import (
    SecurityMiddleware,
    SecurityMiddlewareConfig,
    init_ip_blacklist,
)

# 初始化黑名单
blacklist = init_ip_blacklist(redis_client)

# 配置中间件
config = SecurityMiddlewareConfig(
    enable_blacklist=True,
    excluded_paths=["/health", "/metrics"],
    blacklist_error_message="Access denied"
)

# 添加到 FastAPI
app.add_middleware(SecurityMiddleware, blacklist=blacklist, config=config)
```

---

## 三、目录结构

```
infrastructure/security/
├── __init__.py           # 模块导出
├── README.md             # 本文档
├── memory-bank/          # 开发文档
│   ├── prd.md           # 产品需求
│   ├── tech-stack.md    # 技术栈
│   ├── implementation-plan.md  # 实现计划
│   ├── progress.md      # 进度追踪
│   └── architecture.md  # 架构说明
│
├── 【已有文件】
├── jwt_signer.py         # Coze JWT 签名
├── agent_auth.py         # 坐席认证系统
│
├── 【新增文件 - Phase 1】
├── config.py             # 安全配置模型
├── rate_limiter.py       # 通用限流器
├── blacklist.py          # IP 黑名单
├── login_protector.py    # 登录保护
├── validators.py         # 输入校验
└── middleware.py         # 安全中间件
```

---

## 四、公开接口

### 配置模型

```python
@dataclass
class RateLimiterConfig:
    default_limit: str = "60/minute"
    storage_uri: Optional[str] = None
    endpoint_limits: Dict[str, str] = field(default_factory=dict)

@dataclass
class LoginProtectorConfig:
    max_failures: int = 5
    lockout_duration: int = 900  # 15 分钟

@dataclass
class SecurityConfig:
    rate_limiter: RateLimiterConfig
    login_protector: LoginProtectorConfig
```

### 限流器

```python
def create_rate_limiter(config: RateLimiterConfig) -> Limiter
def get_rate_limit_handler() -> Callable
def get_client_ip(request: Request) -> str
```

### IP 黑名单

```python
class IPBlacklist:
    async def is_blocked(self, ip: str) -> bool
    async def add(self, ip: str, duration: int = None, reason: str = "") -> bool
    async def remove(self, ip: str) -> bool
    async def get_info(self, ip: str) -> Optional[Dict]
    async def list_all(self) -> List[Dict]

def init_ip_blacklist(redis_client) -> IPBlacklist
def get_ip_blacklist() -> IPBlacklist
```

### 登录保护

```python
class LoginProtector:
    async def is_locked(self, username: str) -> bool
    async def record_failure(self, username: str) -> int
    async def reset(self, username: str) -> bool
    async def get_failures(self, username: str) -> int
    async def get_lockout_remaining(self, username: str) -> int

def init_login_protector(redis_client, config: LoginProtectorConfig = None) -> LoginProtector
def get_login_protector() -> LoginProtector
```

### 输入校验

```python
def validate_message_length(message: str, max_length: int = 2000) -> str
def sanitize_input(text: str, escape_html: bool = True) -> str
def validate_order_number(order_number: str) -> str
def validate_tracking_number(tracking_number: str) -> str
def validate_email(email: str) -> str
def validate_username(username: str) -> str
```

### 安全中间件

```python
@dataclass
class SecurityMiddlewareConfig:
    enable_blacklist: bool = True
    excluded_paths: List[str] = field(default_factory=lambda: ["/health", "/metrics"])
    blacklist_error_message: str = "Access denied"

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, blacklist: IPBlacklist, config: SecurityMiddlewareConfig)
```

---

## 五、限流配置建议

| 场景 | 限制 | 说明 |
|------|------|------|
| 对话接口 | 10/minute | 防止滥用 AI |
| 登录接口 | 5/minute | 防止暴力破解 |
| 订单查询 | 30/minute | 正常使用足够 |
| 全局默认 | 60/minute | 基础保护 |

---

## 六、Redis Key 规范

| Key 模式 | 用途 | TTL |
|----------|------|-----|
| `LIMITER/{endpoint}/{ip}` | 限流计数 | 按限流周期 |
| `security:blacklist:ip:{ip}` | IP 封禁标记 | 按封禁时长 |
| `security:blacklist:ip` | 封禁详情 Hash | 永久 |
| `security:login_failures:{username}` | 登录失败计数 | 15 分钟 |
| `security:account_locked:{username}` | 账户锁定标记 | 15 分钟 |

---

## 七、错误响应格式

### 429 限流响应

```json
{
    "success": false,
    "error": "Too many requests. Please try again later.",
    "retry_after": 60
}
```

### 403 IP 封禁响应

```json
{
    "success": false,
    "error": "Access denied. Your IP has been blocked.",
    "code": "IP_BLOCKED"
}
```

### 423 账户锁定响应

```json
{
    "success": false,
    "error": "Account locked. Please try again in 15 minutes.",
    "remaining_seconds": 900
}
```

---

## 八、环境变量配置

```bash
# 安全防护配置（可选，有默认值）
RATE_LIMIT_DEFAULT=60/minute
RATE_LIMIT_BURST=10/second
RATE_LIMIT_CHAT=10/minute
RATE_LIMIT_LOGIN=5/minute
RATE_LIMIT_REFRESH=10/minute
LOGIN_MAX_FAILURES=5
LOGIN_LOCKOUT_SECONDS=900
MAX_MESSAGE_LENGTH=2000

# Redis 连接（已有）
REDIS_URL=redis://localhost:6379/0
```

---

## 九、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0 | 2025-12-25 | Phase 1 完成：添加限流器、黑名单、登录保护、输入校验、安全中间件 |
| v1.0 | 2025-12-18 | 初始版本 |
