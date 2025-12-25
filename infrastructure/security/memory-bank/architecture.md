# 安全防护组件 - 架构说明

> **功能**: 安全防护组件 (Security Module)
> **模块位置**: `infrastructure/security/`
> **最后更新**: 2025-12-25
> **遵循规范**: CLAUDE.md 三层架构

---

## 1. 模块定位

```
┌─────────────────────────────────────────────────────────────────┐
│                      products/ 产品层                            │
│  ┌─────────────────┐         ┌─────────────────┐                │
│  │  AI 智能客服     │         │   坐席工作台     │                │
│  │  (ai_chatbot)   │         │(agent_workbench)│                │
│  └────────┬────────┘         └────────┬────────┘                │
│           │                           │                          │
│           │  import                   │  import                  │
│           ▼                           ▼                          │
├─────────────────────────────────────────────────────────────────┤
│                    infrastructure/security/                       │
│                       【本模块】                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  限流器 │ IP黑名单 │ 登录保护 │ 输入校验 │ 中间件 │ 指标  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│                    infrastructure/database/                       │
│                          (Redis)                                 │
└─────────────────────────────────────────────────────────────────┘
```

**架构原则**：
- 本模块属于 `infrastructure/` 基础设施层
- 可被 `services/` 和 `products/` 依赖
- 不依赖上层模块
- 使用 Redis 存储（通过 `infrastructure/database/`）

---

## 2. 文件结构

```
infrastructure/security/
├── __init__.py              # 模块导出（已有 + 新增）
├── README.md                # 组件规范文档
├── memory-bank/             # 开发文档
│   ├── prd.md              # 产品需求
│   ├── tech-stack.md       # 技术栈
│   ├── implementation-plan.md  # 实现计划
│   ├── progress.md         # 进度追踪
│   └── architecture.md     # 本文档
│
├── 【已有文件】
├── jwt_signer.py            # Coze JWT 签名
├── agent_auth.py            # 坐席认证系统
│   ├── PasswordHasher       # 密码加密
│   ├── AgentTokenManager    # JWT Token 管理
│   ├── AgentManager         # 坐席账号管理
│   └── create_jwt_dependencies()
│
├── 【新增文件】
├── config.py                # 安全配置模型
│   ├── RateLimiterConfig    # 限流配置
│   └── SecurityConfig       # 统一配置
│
├── rate_limiter.py          # 通用限流器
│   ├── create_rate_limiter()    # 工厂函数
│   └── get_rate_limit_handler() # 429 处理器
│
├── blacklist.py             # IP 黑名单
│   └── IPBlacklist          # 黑名单管理类
│
├── login_protector.py       # 登录保护
│   └── LoginProtector       # 防暴力破解
│
├── validators.py            # 输入校验
│   ├── validate_message_length()
│   ├── sanitize_input()
│   └── validate_order_number()
│
├── middleware.py            # FastAPI 中间件
│   ├── SecurityMiddleware
│   └── SecurityMiddlewareConfig
│
└── metrics.py               # Prometheus 指标
    ├── rate_limit_hits
    ├── blocked_ips
    ├── login_failures
    └── get_metrics_handler()
```

---

## 3. 数据流

### 3.1 请求限流流程

```
客户端请求
    │
    ▼
┌─────────────────────────────────────┐
│        FastAPI 应用                  │
│  ┌─────────────────────────────┐    │
│  │   SecurityMiddleware        │    │
│  │   1. 检查 IP 黑名单         │◄───┼─── Redis: security:blacklist:ip
│  │   2. 被封禁 → 返回 403      │    │
│  └─────────────┬───────────────┘    │
│                │                     │
│                ▼                     │
│  ┌─────────────────────────────┐    │
│  │   @limiter.limit() 装饰器   │    │
│  │   1. 检查限流计数           │◄───┼─── Redis: LIMITER/...
│  │   2. 超限 → 返回 429        │    │
│  └─────────────┬───────────────┘    │
│                │                     │
│                ▼                     │
│  ┌─────────────────────────────┐    │
│  │   Handler 业务逻辑          │    │
│  │   1. 输入校验               │    │
│  │   2. 业务处理               │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

### 3.2 登录保护流程

```
登录请求 POST /agent/login
    │
    ▼
┌─────────────────────────────────────┐
│   LoginProtector.is_locked()        │
│   检查账户是否被锁定                 │◄─── Redis: security:account_locked:{username}
└─────────────┬───────────────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
  已锁定              未锁定
    │                   │
    ▼                   ▼
  返回 423         验证密码
  (Locked)              │
              ┌─────────┴─────────┐
              │                   │
            失败                成功
              │                   │
              ▼                   ▼
    LoginProtector           LoginProtector
    .record_failure()        .reset()
         │                        │
         ▼                        ▼
    Redis: security:         清除失败计数
    login_failures:{user}    返回 Token
         │
         ▼
    失败次数 >= 5?
    是 → 锁定账户 15 分钟
```

---

## 4. 接口规范

### 4.1 对外导出

```python
# infrastructure/security/__init__.py

# 限流器
from .config import RateLimiterConfig, SecurityConfig
from .rate_limiter import create_rate_limiter, get_rate_limit_handler

# IP 黑名单
from .blacklist import IPBlacklist

# 登录保护
from .login_protector import LoginProtector

# 输入校验
from .validators import validate_message_length, sanitize_input, validate_order_number

# 中间件
from .middleware import SecurityMiddleware, SecurityMiddlewareConfig

# 监控指标
from .metrics import security_metrics, get_metrics_handler

# 现有导出（保持不变）
from .jwt_signer import JWTSigner
from .agent_auth import (
    AgentManager,
    AgentTokenManager,
    Agent,
    AgentStatus,
    # ...
)
```

### 4.2 产品接入示例

```python
# products/ai_chatbot/main.py

from infrastructure.security import (
    create_rate_limiter,
    RateLimiterConfig,
    SecurityMiddleware,
    SecurityMiddlewareConfig,
    get_rate_limit_handler,
)
from slowapi.errors import RateLimitExceeded

# 1. 创建限流器
config = RateLimiterConfig(
    default_limit="60/minute",
    storage_uri=os.getenv("REDIS_URL"),
    endpoint_limits={
        "/api/chat/stream": "10/minute",
        "/api/chat": "10/minute",
    }
)
limiter = create_rate_limiter(config)

# 2. 挂载到 app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, get_rate_limit_handler())

# 3. 添加安全中间件（可选，用于 IP 黑名单）
# app.add_middleware(SecurityMiddleware, config=SecurityMiddlewareConfig(...))
```

---

## 5. Redis Key 规范

| Key 模式 | 用途 | TTL |
|----------|------|-----|
| `LIMITER/{endpoint}/{ip}` | 限流计数（slowapi 内置） | 按限流周期 |
| `security:blacklist:ip:{ip}` | IP 封禁标记 | 按封禁时长 |
| `security:blacklist:ip` | IP 封禁详情 Hash | 永久 |
| `security:login_failures:{username}` | 登录失败计数 | 15 分钟 |
| `security:account_locked:{username}` | 账户锁定标记 | 15 分钟 |

---

## 6. 关键设计决策

| 决策 | 选择 | 原因 |
|------|------|------|
| 限流库 | slowapi | 成熟、与 FastAPI 集成好、支持 Redis |
| 存储 | Redis | 支持分布式、TTL、已有基础设施 |
| 黑名单粒度 | IP | 简单有效，后续可扩展到用户级别 |
| 登录锁定时长 | 15 分钟 | 平衡安全与用户体验 |
| 中间件顺序 | 黑名单 → 限流 → 业务 | 先拦截明确恶意，再限流 |

---

## 7. 文档更新记录

| 日期 | 变更内容 |
|------|----------|
| 2025-12-25 | Step 6 完成: 新增 middleware.py 安全中间件 |
| 2025-12-25 | Step 5 完成: 新增 validators.py 输入校验工具 |
| 2025-12-25 | Step 4 完成: 新增 login_protector.py 登录保护器 |
| 2025-12-25 | Step 3 完成: 新增 blacklist.py IP 黑名单管理 |
| 2025-12-25 | Step 2 完成: 新增 rate_limiter.py 限流器工厂 |
| 2025-12-25 | Step 1 完成: 新增 config.py 配置模型文件 |
| 2025-12-24 | 初始版本 |

---

## 8. 已实现文件详情

### 8.1 config.py - 安全配置模型

**用途:** 提供安全组件的配置数据类

**主要类:**
- `RateLimiterConfig` - 限流器配置
  - `default_limit`: 默认限流规则 (如 "60/minute")
  - `storage_uri`: Redis 连接 URI
  - `endpoint_limits`: 端点级别限流覆盖
  - `from_env()`: 从环境变量加载配置

- `LoginProtectorConfig` - 登录保护配置
  - `max_failures`: 最大失败次数 (默认 5)
  - `lockout_duration`: 锁定时长 (默认 900 秒)
  - `from_env()`: 从环境变量加载配置

- `SecurityConfig` - 统一安全配置
  - 聚合 RateLimiterConfig 和 LoginProtectorConfig
  - `from_env()`: 从环境变量加载完整配置

**依赖关系:**
- 依赖: 无（纯数据类）
- 被依赖: rate_limiter.py, login_protector.py, middleware.py (待实现)

---

### 8.2 rate_limiter.py - 通用限流器

**用途:** 基于 slowapi 封装的限流器工厂

**主要函数:**
- `create_rate_limiter(config)` - 创建限流器实例
  - 支持 Redis 存储（分布式限流）
  - 支持内存存储（单机降级）
  - 自动从环境变量读取配置

- `get_rate_limit_handler(error_message, include_retry_after)` - 获取 429 异常处理器
  - 返回标准化 JSON 响应
  - 包含 Retry-After 头

- `get_client_ip(request)` - 获取客户端真实 IP
  - 支持 X-Forwarded-For
  - 支持 X-Real-IP

**依赖关系:**
- 依赖: config.py, slowapi
- 被依赖: products/ai_chatbot/main.py, products/agent_workbench/main.py (待接入)

---

### 8.3 blacklist.py - IP 黑名单管理

**用途:** 提供 IP 封禁功能

**主要类:**
- `IPBlacklist` - IP 黑名单管理类
  - `is_blocked(ip)` - 检查 IP 是否被封禁
  - `add(ip, duration, reason)` - 添加 IP 到黑名单
  - `remove(ip)` - 从黑名单移除 IP
  - `get_info(ip)` - 获取封禁详情
  - `list_all()` - 列出所有被封禁的 IP
  - `count()` - 获取封禁数量

**单例函数:**
- `get_ip_blacklist(redis_client)` - 获取黑名单单例
- `init_ip_blacklist(redis_client)` - 初始化黑名单

**Redis Key:**
- `security:blacklist:ip:{ip}` - 封禁标记（带 TTL）
- `security:blacklist:ip` - Hash 存储封禁详情

**依赖关系:**
- 依赖: infrastructure/bootstrap (get_redis_client)
- 被依赖: middleware.py (待实现)

---

### 8.4 login_protector.py - 登录保护器

**用途:** 防止暴力破解攻击

**主要类:**
- `LoginProtector` - 登录保护器
  - `is_locked(username)` - 检查账户是否锁定
  - `record_failure(username)` - 记录登录失败
  - `reset(username)` - 重置登录状态
  - `get_failures(username)` - 获取失败次数
  - `get_lockout_remaining(username)` - 获取剩余锁定时间
  - `from_config(redis, config)` - 从配置创建

**单例函数:**
- `get_login_protector(redis_client)` - 获取保护器单例
- `init_login_protector(redis_client, config)` - 初始化保护器

**Redis Key:**
- `security:login_failures:{username}` - 失败计数（带 TTL）
- `security:account_locked:{username}` - 锁定标记（带 TTL）

**依赖关系:**
- 依赖: config.py, infrastructure/bootstrap (get_redis_client)
- 被依赖: products/agent_workbench/handlers/auth.py (待接入)

---

### 8.5 validators.py - 输入校验工具

**用途:** 输入验证和清理，防止 XSS 攻击

**主要函数:**
- `validate_message_length(message, max_length)` - 消息长度限制
- `sanitize_input(text, escape_html)` - XSS 防护（HTML 转义）
- `validate_order_number(order_number)` - 订单号格式校验
- `validate_tracking_number(tracking_number)` - 物流单号格式校验
- `validate_email(email)` - 邮箱格式校验
- `validate_username(username)` - 用户名格式校验

**XSS 防护原理:**
- 使用 `html.escape()` 转义特殊字符
- `<` → `&lt;`, `>` → `&gt;`, `&` → `&amp;`
- 防止 `<script>`, `<img onerror=...>` 等攻击

**依赖关系:**
- 依赖: fastapi.HTTPException
- 被依赖: products/ai_chatbot/handlers/chat.py (待接入)

---

### 8.6 middleware.py - FastAPI 安全中间件

**用途:** 统一的请求安全检查中间件

**主要类:**
- `SecurityMiddlewareConfig` - 中间件配置
  - `enable_blacklist`: 是否启用 IP 黑名单检查（默认 True）
  - `excluded_paths`: 排除路径列表（默认 ['/health', '/metrics']）
  - `blacklist_error_message`: 自定义错误消息
  - `get_client_ip`: 自定义 IP 获取函数

- `SecurityMiddleware` - 安全中间件
  - 继承 `starlette.middleware.base.BaseHTTPMiddleware`
  - 在请求进入路由前检查 IP 黑名单
  - 被封禁返回 403 JSON 响应

**主要函数:**
- `get_client_ip(request)` - 获取客户端真实 IP
  - 支持 X-Forwarded-For（nginx 反向代理）
  - 支持 X-Real-IP

**403 响应格式:**
```json
{
    "success": false,
    "error": "Access denied. Your IP has been blocked.",
    "code": "IP_BLOCKED"
}
```

**依赖关系:**
- 依赖: blacklist.py (IPBlacklist)
- 被依赖: products/ai_chatbot/main.py, products/agent_workbench/main.py (待接入)
