# 安全防护组件 - 实现计划

> **版本**: v1.1
> **创建日期**: 2025-12-24
> **更新日期**: 2025-12-25
> **方法论**: Vibe Coding 分步骤开发
> **预计步骤数**: 12 步
> **核心功能步骤**: Step 1-8 (P0)
> **扩展功能步骤**: Step 9-12 (P1)

---

## 〇、技术决策（基于代码分析）

> 本节基于对实际代码的分析，明确所有实现细节，消除歧义。

### 决策 1: Redis 客户端获取方式

**结论**: 使用 `infrastructure.bootstrap` 模块

```python
from infrastructure.bootstrap import get_redis_client, init_redis

# 获取 Redis 客户端（可能为 None，表示内存模式）
redis = get_redis_client()
```

**原因**: 代码分析发现 `infrastructure/bootstrap/redis.py` 提供了统一的 Redis 初始化和获取接口，支持降级到内存存储。

---

### 决策 2: slowapi storage_uri 格式

**结论**: 使用环境变量 `REDIS_URL`，格式为 `redis://localhost:6379/0`

```python
import os
from slowapi import Limiter
from slowapi.util import get_remote_address

# 从环境变量获取 Redis URL
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# slowapi 使用 storage_uri 格式
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=redis_url  # 直接使用 Redis URL
)
```

**原因**: 代码分析发现 `RedisConfig.from_env()` 使用 `REDIS_URL` 环境变量，slowapi 直接支持此格式。

---

### 决策 3: 中间件与装饰器的关系

**结论**: **分层防护，互不冲突**

```
请求 → SecurityMiddleware (IP黑名单) → @limiter.limit() (API限流) → Handler
```

| 组件 | 职责 | 拦截时机 |
|------|------|----------|
| SecurityMiddleware | IP 黑名单检查 | 请求进入时，返回 403 |
| @limiter.limit() | API 限流 | 路由匹配后，返回 429 |

**原因**: 黑名单是「是否允许访问」，限流是「访问频率控制」，两者独立。

---

### 决策 4: Handler 文件路径确认

**AI 智能客服**:
- `products/ai_chatbot/handlers/chat.py` - `/chat` 和 `/chat/stream` 端点
- 需要限流的端点: `POST /chat`, `POST /chat/stream`

**坐席工作台**:
- `products/agent_workbench/handlers/auth.py` - `/agent/login` 等端点
- 需要限流的端点: `POST /agent/login`, `POST /agent/refresh`
- 需要登录保护: `POST /agent/login`

---

### 决策 5: 限流 Key 策略

**结论**: 使用 **IP 地址** 作为限流 Key（默认行为）

```python
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

**原因**:
1. AI 客服匿名访问，无 user_id
2. 坐席工作台登录前无 user_id
3. IP 限流足够防护 CC 攻击
4. 后续可扩展为 IP + user_id 组合

---

### 决策 6: 并发测试方案

**结论**: 使用 Bash 循环 + curl 进行基础验证

```bash
# 验证限流（10/minute 配置）
for i in {1..11}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:8000/api/chat/stream \
    -H "Content-Type: application/json" \
    -d '{"message":"test"}'
done
# 预期: 前 10 次返回 200，第 11 次返回 429
```

**原因**: 验证目的是确认限流生效，不需要压力测试。生产环境压力测试使用专业工具。

---

### 决策 7: 错误响应格式

**结论**: 遵循现有 API 响应格式

```python
# 429 限流响应
{
    "success": False,
    "error": "Too many requests. Please try again later.",
    "retry_after": 60  # 秒
}

# 403 IP 封禁响应
{
    "success": False,
    "error": "Access denied. Your IP has been blocked."
}

# 423 账户锁定响应
{
    "success": False,
    "error": "Account locked. Please try again in 15 minutes."
}
```

**原因**: 代码分析发现现有 API 使用 `{"success": bool, "error": str}` 格式。

---

### 决策 8: 环境变量配置

**新增环境变量**（添加到 `.env`）:

```bash
# 安全防护配置
RATE_LIMIT_DEFAULT=60/minute
RATE_LIMIT_CHAT=10/minute
RATE_LIMIT_LOGIN=5/minute
LOGIN_MAX_FAILURES=5
LOGIN_LOCKOUT_SECONDS=900
```

**现有可用变量**:
- `REDIS_URL` - Redis 连接地址
- `USE_REDIS` - 是否启用 Redis

---

## 一、开发原则

1. **自底向上**: 先完成 infrastructure/security 模块，再让产品层接入
2. **增量开发**: 每步只做一件事，立即测试验证
3. **频繁提交**: 每个功能点完成即提交
4. **单次提交**: < 10 个文件，< 500 行代码

---

## 二、依赖关系

```
Phase 1 核心功能:

Step 1 (依赖) ─→ Step 2 ─→ Step 3 ─→ Step 4
                                        │
Step 5 ─→ Step 6 ─────────────────────→ │
                                        ▼
                                     Step 7 ─→ Step 8

Phase 2 产品接入 (依赖 Phase 1 完成):

Step 9 ─→ Step 10

Phase 3 监控指标 (可并行):

Step 11 ─→ Step 12
```

---

## 三、Phase 1 - P0 核心功能

### Step 1: 添加依赖并创建配置模型

**目标**: 添加 slowapi 依赖，创建安全配置数据模型

**涉及文件**:
- `requirements.txt`（修改）
- `infrastructure/security/config.py`（新增）

**改动**:
- requirements.txt 添加 `slowapi==0.1.9`
- 创建 `RateLimiterConfig` 数据类
- 创建 `SecurityConfig` 统一配置类

**验证**:
```bash
pip install slowapi==0.1.9
python3 -c "from infrastructure.security.config import RateLimiterConfig; print(RateLimiterConfig())"
```

**预期结果**:
- slowapi 安装成功
- RateLimiterConfig 可正常实例化

**状态**: ⬜ 待开发

---

### Step 2: 实现通用限流器工厂

**目标**: 创建 `rate_limiter.py`，封装 slowapi 限流器

**依赖**: Step 1

**涉及文件**:
- `infrastructure/security/rate_limiter.py`（新增）

**改动**:
- 实现 `create_rate_limiter(config)` 工厂函数
- 实现 `get_rate_limit_handler()` 返回标准 429 处理器
- 支持 Redis 存储（分布式限流）
- 支持内存存储（单机降级）

**验证**:
```bash
python3 -c "
from infrastructure.security.rate_limiter import create_rate_limiter
from infrastructure.security.config import RateLimiterConfig
config = RateLimiterConfig(default_limit='10/minute')
limiter = create_rate_limiter(config)
print(f'Limiter created: {limiter}')
"
```

**预期结果**:
- Limiter 对象创建成功
- 无报错

**状态**: ⬜ 待开发

---

### Step 3: 实现 IP 黑名单管理

**目标**: 创建 `blacklist.py`，实现 IP 封禁功能

**依赖**: Step 1

**涉及文件**:
- `infrastructure/security/blacklist.py`（新增）

**改动**:
- 实现 `IPBlacklist` 类
- 方法: `is_blocked()`, `add()`, `remove()`, `list_all()`
- 支持过期时间（自动解封）
- 支持永久封禁

**验证**:
```bash
python3 -c "
import asyncio
from infrastructure.security.blacklist import IPBlacklist
from infrastructure.bootstrap import get_redis_client

async def test():
    redis = get_redis_client()
    if redis is None:
        print('Redis not initialized, skip test')
        return
    bl = IPBlacklist(redis)
    await bl.add('192.168.1.100', duration=60, reason='test')
    print(f'Is blocked: {await bl.is_blocked(\"192.168.1.100\")}')
    await bl.remove('192.168.1.100')
    print(f'After remove: {await bl.is_blocked(\"192.168.1.100\")}')

asyncio.run(test())
"
```

**预期结果**:
- 添加后返回 `True`
- 移除后返回 `False`

**状态**: ⬜ 待开发

---

### Step 4: 实现登录保护器

**目标**: 创建登录失败计数和账户锁定功能

**依赖**: Step 3

**涉及文件**:
- `infrastructure/security/login_protector.py`（新增）

**改动**:
- 实现 `LoginProtector` 类
- 方法: `record_failure()`, `is_locked()`, `reset()`
- 配置: `max_failures=5`, `lockout_duration=900`

**验证**:
```bash
python3 -c "
import asyncio
from infrastructure.security.login_protector import LoginProtector
from infrastructure.bootstrap import get_redis_client

async def test():
    redis = get_redis_client()
    if redis is None:
        print('Redis not initialized, skip test')
        return
    lp = LoginProtector(redis, max_failures=3, lockout_duration=60)

    # 模拟 3 次失败
    for i in range(3):
        count = await lp.record_failure('testuser')
        print(f'Failure {i+1}: count={count}')

    print(f'Is locked: {await lp.is_locked(\"testuser\")}')
    await lp.reset('testuser')
    print(f'After reset: {await lp.is_locked(\"testuser\")}')

asyncio.run(test())
"
```

**预期结果**:
- 3 次失败后 `is_locked` 返回 `True`
- reset 后返回 `False`

**状态**: ⬜ 待开发

---

### Step 5: 实现输入校验工具

**目标**: 创建消息长度限制和输入清理工具

**依赖**: Step 1

**涉及文件**:
- `infrastructure/security/validators.py`（新增）

**改动**:
- 实现 `validate_message_length(message, max_length)` - 超长抛出 HTTPException
- 实现 `sanitize_input(text)` - 清理危险字符
- 实现 `validate_order_number(order_number)` - 订单号格式校验

**验证**:
```bash
python3 -c "
from infrastructure.security.validators import validate_message_length, sanitize_input

# 正常消息
validate_message_length('Hello', max_length=1000)
print('Normal message: OK')

# 超长消息
try:
    validate_message_length('x' * 1001, max_length=1000)
except Exception as e:
    print(f'Long message rejected: {e}')

# 输入清理
clean = sanitize_input('<script>alert(1)</script>')
print(f'Sanitized: {clean}')
"
```

**预期结果**:
- 正常消息通过
- 超长消息抛出异常
- 危险字符被清理

**状态**: ⬜ 待开发

---

### Step 6: 实现安全中间件

**目标**: 创建统一的 FastAPI 安全中间件

**依赖**: Step 3, Step 5

**涉及文件**:
- `infrastructure/security/middleware.py`（新增）

**改动**:
- 实现 `SecurityMiddleware` 类
- 集成 IP 黑名单检查
- 返回标准 403 响应（被封禁时）

**验证**:
```bash
python3 -c "
from infrastructure.security.middleware import SecurityMiddleware, SecurityMiddlewareConfig
print('SecurityMiddleware class created successfully')
"
```

**预期结果**:
- 类定义无语法错误

**状态**: ⬜ 待开发

---

### Step 7: 更新模块导出

**目标**: 更新 `__init__.py`，导出所有新增接口

**依赖**: Step 2, 3, 4, 5, 6

**涉及文件**:
- `infrastructure/security/__init__.py`（修改）

**改动**:
- 导出 `RateLimiterConfig`, `create_rate_limiter`, `get_rate_limit_handler`
- 导出 `IPBlacklist`, `get_ip_blacklist`
- 导出 `LoginProtector`
- 导出 `validate_message_length`, `sanitize_input`
- 导出 `SecurityMiddleware`, `SecurityMiddlewareConfig`
- 保留现有导出（JWTSigner, AgentManager 等）

**验证**:
```bash
python3 -c "
from infrastructure.security import (
    RateLimiterConfig,
    create_rate_limiter,
    IPBlacklist,
    LoginProtector,
    validate_message_length,
    SecurityMiddleware,
    # 现有导出
    JWTSigner,
    AgentManager,
)
print('All exports working!')
"
```

**预期结果**:
- 所有导入成功

**状态**: ⬜ 待开发

---

### Step 8: 更新 README 文档

**目标**: 更新组件 README，添加使用说明

**依赖**: Step 7

**涉及文件**:
- `infrastructure/security/README.md`（修改）

**改动**:
- 更新组件状态为「已完成」
- 添加新增功能说明
- 添加产品接入示例代码
- 添加配置参数说明

**验证**:
- 文档格式正确
- 示例代码可运行

**状态**: ⬜ 待开发

---

## 四、Phase 2 - 产品接入

### Step 9: AI 智能客服接入限流

**目标**: AI 客服集成限流和消息长度限制

**依赖**: Step 8

**涉及文件**:
- `products/ai_chatbot/main.py`（修改）
- `products/ai_chatbot/handlers/chat.py`（修改）

**改动**:
- main.py 添加限流器初始化
- main.py 添加 RateLimitExceeded 异常处理
- chat.py 的 `/chat/stream` 添加 `@limiter.limit("10/minute")`
- chat.py 添加消息长度校验

**验证**:
```bash
# 启动服务
uvicorn products.ai_chatbot.main:app --port 8000 &

# 快速发送 11 次请求
for i in {1..11}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:8000/api/chat/stream \
    -H "Content-Type: application/json" \
    -d '{"message":"test"}'
done

# 测试超长消息
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"$(python3 -c 'print(\"x\"*1001)')\"}"
```

**预期结果**:
- 第 11 次请求返回 429
- 超长消息返回 400

**状态**: ⬜ 待开发

---

### Step 10: 坐席工作台接入限流和登录保护

**目标**: 坐席工作台集成限流和登录保护

**依赖**: Step 8

**涉及文件**:
- `products/agent_workbench/main.py`（修改）
- `products/agent_workbench/handlers/auth.py`（修改）

**改动**:
- main.py 添加限流器初始化
- auth.py 的 `/agent/login` 添加 `@limiter.limit("5/minute")`
- auth.py 集成 LoginProtector，登录失败时记录

**验证**:
```bash
# 启动服务
uvicorn products.agent_workbench.main:app --port 8002 &

# 快速发送 6 次登录请求
for i in {1..6}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:8002/api/agent/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"wrong"}'
done
```

**预期结果**:
- 第 6 次请求返回 429
- 连续 5 次失败后返回账户锁定提示

**状态**: ⬜ 待开发

---

## 五、Phase 3 - P1 监控指标

### Step 11: 添加 Prometheus 指标

**目标**: 添加安全监控指标

**依赖**: Step 8

**涉及文件**:
- `requirements.txt`（修改）
- `infrastructure/security/metrics.py`（新增）

**改动**:
- requirements.txt 添加 `prometheus-client==0.19.0`
- 定义指标: `rate_limit_hits`, `blocked_ips`, `login_failures`
- 实现 `get_metrics_handler()` 返回指标端点

**验证**:
```bash
pip install prometheus-client==0.19.0
python3 -c "
from infrastructure.security.metrics import security_metrics, get_metrics_handler
print('Metrics module loaded successfully')
"
```

**预期结果**:
- 指标模块加载成功

**状态**: ⬜ 待开发

---

### Step 12: 产品添加 /metrics 端点

**目标**: AI 客服和坐席工作台暴露监控指标

**依赖**: Step 11

**涉及文件**:
- `products/ai_chatbot/main.py`（修改）
- `products/agent_workbench/main.py`（修改）

**改动**:
- 添加 `/metrics` 路由
- 集成 Prometheus 指标

**验证**:
```bash
curl http://localhost:8000/metrics
curl http://localhost:8002/metrics
```

**预期结果**:
- 返回 Prometheus 格式文本
- 包含 `security_rate_limit_hits_total` 等指标

**状态**: ⬜ 待开发

---

## 六、开发检查清单

每个 Step 完成后：

- [ ] 代码无语法错误
- [ ] 按验证方法测试通过
- [ ] 不破坏现有功能
- [ ] 更新 `progress.md` 状态
- [ ] Git 提交（message 包含 Step 编号）

---

## 七、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.1 | 2025-12-25 | 新增「技术决策」章节，澄清 8 个实现细节；修正验证脚本中的 Redis 导入路径 |
| v1.0 | 2025-12-24 | 初始版本，12 个步骤 |
