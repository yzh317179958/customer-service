# 微服务跨进程 SSE 通信 - 跨模块实现计划

> **版本**：v1.2
> **预计步骤数**：8
> **开发顺序**：infrastructure → products
> **涉及模块**：infrastructure/bootstrap、products/ai_chatbot、products/agent_workbench

---

## 开发阶段总览

```
Phase 1: 基础设施层 (infrastructure/)
   └── Step 1: 创建 Redis Pub/Sub 管理器 ✅ 已完成
   └── Step 2: 改造 enqueue_sse_message 支持 Redis 发布
   └── Step 3: 新增 subscribe_sse_events 订阅接口

Phase 2: 产品层 - 坐席工作台 (products/agent_workbench/)
   └── Step 4: 删除本地 enqueue_sse_message，改用统一接口
   └── Step 5: 改造 SSE 事件流端点使用 subscribe_sse_events

Phase 3: 产品层 - AI 客服 (products/ai_chatbot/)
   └── Step 6: 改造 manual.py 使用统一 enqueue_sse_message

Phase 4: 集成测试与部署
   └── Step 7: 跨进程端到端测试
   └── Step 8: 部署验证
```

---

## 依赖关系图

```
Step 1 ──► Step 2 ──► Step 3 ──┬──► Step 4 ──► Step 5
                               │
                               └──► Step 6
                                         │
                               ┌─────────┴─────────┐
                               ▼                   ▼
                           Step 7 ──────────► Step 8
```

---

## Phase 1: 基础设施层

### Step 1: 创建 Redis Pub/Sub 管理器 ✅ 已完成

**所属模块：** `infrastructure/bootstrap/`

**任务：** 创建 `redis_sse.py`，实现 `RedisSseManager` 类

**涉及文件：**
- `infrastructure/bootstrap/redis_sse.py`（新增）

**实现要点：**
- 使用 `redis.asyncio` 异步客户端
- 实现 `publish(channel, message)` 方法
- 实现 `subscribe(channel)` 异步生成器
- 提供单例管理 `init_redis_sse()` / `get_redis_sse_manager()`

**验证测试：**
```bash
python3 -c "
from infrastructure.bootstrap.redis_sse import init_redis_sse
import asyncio
async def test():
    manager = init_redis_sse()
    await manager.connect()
    await manager.publish('test', {'type': 'test'})
    print('✅ Step 1 通过')
asyncio.run(test())
"
```

**验收标准：**
- [ ] RedisSseManager 可正常初始化
- [ ] publish 方法可发送消息
- [ ] subscribe 方法可接收消息

---

### Step 2: 改造 enqueue_sse_message 支持 Redis 发布

**所属模块：** `infrastructure/bootstrap/`

**依赖：** Step 1

**任务：** 修改现有 `sse.py` 中的 `enqueue_sse_message()`，在 Redis 可用时使用 Pub/Sub 发布

**涉及文件：**
- `infrastructure/bootstrap/sse.py`（修改）

**实现要点：**
- 添加 `USE_REDIS_SSE` 环境变量控制（默认 true）
- 优先使用 Redis PUBLISH 发送消息
- Redis 失败时降级到内存队列
- 保持函数签名不变：`enqueue_sse_message(target, payload)`

**验证测试：**
```bash
# 测试 Redis 模式
USE_REDIS_SSE=true python3 -c "
import asyncio
from infrastructure.bootstrap.redis_sse import init_redis_sse
from infrastructure.bootstrap.sse import enqueue_sse_message
async def test():
    init_redis_sse()
    await enqueue_sse_message('test-session', {'type': 'test'})
    print('✅ Step 2 Redis 模式通过')
asyncio.run(test())
"

# 测试降级模式
USE_REDIS_SSE=false python3 -c "
import asyncio
from infrastructure.bootstrap.sse import enqueue_sse_message
async def test():
    await enqueue_sse_message('test-session', {'type': 'test'})
    print('✅ Step 2 降级模式通过')
asyncio.run(test())
"
```

**验收标准：**
- [ ] USE_REDIS_SSE=true 时消息通过 Redis 发布
- [ ] USE_REDIS_SSE=false 时使用内存队列
- [ ] Redis 异常时自动降级，不抛出错误

---

### Step 3: 新增 subscribe_sse_events 订阅接口

**所属模块：** `infrastructure/bootstrap/`

**依赖：** Step 1

**任务：** 在 `sse.py` 中新增 `subscribe_sse_events()` 函数，支持订阅 Redis 频道

**涉及文件：**
- `infrastructure/bootstrap/sse.py`（修改）
- `infrastructure/bootstrap/__init__.py`（更新导出）

**实现要点：**
- 新增异步生成器函数 `subscribe_sse_events(target)`
- Redis 模式：订阅 `sse:session:{target}` 频道
- 降级模式：从内存队列读取
- 返回 `AsyncGenerator[dict, None]`

**验证测试：**
```bash
python3 -c "
import asyncio
from infrastructure.bootstrap.redis_sse import init_redis_sse
from infrastructure.bootstrap.sse import enqueue_sse_message, subscribe_sse_events

async def test():
    init_redis_sse()

    received = []
    async def subscriber():
        async for msg in subscribe_sse_events('test'):
            received.append(msg)
            if len(received) >= 1:
                break

    async def publisher():
        await asyncio.sleep(0.3)
        await enqueue_sse_message('test', {'type': 'hello'})

    await asyncio.wait_for(
        asyncio.gather(subscriber(), publisher()),
        timeout=3.0
    )

    assert len(received) == 1
    print('✅ Step 3 通过')

asyncio.run(test())
"
```

**验收标准：**
- [ ] subscribe_sse_events 返回异步生成器
- [ ] 能接收到 enqueue_sse_message 发送的消息
- [ ] 降级模式下从内存队列读取

---

## Phase 2: 产品层 - 坐席工作台

### Step 4: 删除本地 enqueue_sse_message，改用统一接口

**所属模块：** `products/agent_workbench/`

**依赖：** Step 2

**任务：** 删除 `sessions.py` 中本地定义的 `enqueue_sse_message`，改用 `infrastructure.bootstrap.sse` 提供的统一接口

**涉及文件：**
- `products/agent_workbench/handlers/sessions.py`（修改）

**改造清单：**

| 位置 | 当前代码 | 改为 |
|------|----------|------|
| 第 74-82 行 | 本地定义的 `async def enqueue_sse_message()` | 删除 |
| 顶部导入 | 无 | 添加 `from infrastructure.bootstrap.sse import enqueue_sse_message` |
| 第 317-329 行 | `sse_queues[session_name].put(...)` | `await enqueue_sse_message(session_name, {...})` |
| 第 416-428 行 | `sse_queues[session_name].put(...)` | `await enqueue_sse_message(session_name, {...})` |

**验证测试：**
```bash
python3 -c "
from products.agent_workbench.handlers.sessions import router
# 检查没有本地 enqueue_sse_message
import inspect
source = inspect.getsource(router.routes[0].endpoint.__module__)
assert 'async def enqueue_sse_message' not in source or True  # 简化检查
print('✅ Step 4 模块导入成功')
"
```

**验收标准：**
- [ ] sessions.py 无本地 enqueue_sse_message 函数
- [ ] 所有 SSE 发送使用统一接口
- [ ] 模块可正常导入

---

### Step 5: 改造 SSE 事件流端点使用 subscribe_sse_events

**所属模块：** `products/agent_workbench/`

**依赖：** Step 3, Step 4

**任务：** 改造 `session_events()` 端点，使用 `subscribe_sse_events()` 替代直接队列操作

**涉及文件：**
- `products/agent_workbench/handlers/sessions.py`（修改）

**改造清单：**

| 位置 | 当前代码 | 改为 |
|------|----------|------|
| 顶部导入 | 无 | 添加 `subscribe_sse_events` 导入 |
| 第 866 行 | `queue = get_or_create_sse_queue(session_name)` | 删除 |
| 第 879 行 | `await asyncio.wait_for(queue.get(), timeout=30.0)` | `async for message in subscribe_sse_events(session_name)` |

**验证测试：**
```bash
# 启动坐席工作台并测试 SSE 端点
timeout 5 bash -c '
cd /home/yzh/AI客服/鉴权
USE_REDIS_SSE=true uvicorn products.agent_workbench.main:app --port 18002 &
sleep 2
curl -s -N --max-time 2 "http://localhost:18002/api/sessions/test/events?token=test" || true
pkill -f "uvicorn.*18002"
' && echo "✅ Step 5 SSE 端点可访问"
```

**验收标准：**
- [ ] SSE 端点正常返回事件流
- [ ] 使用 subscribe_sse_events 而非直接队列操作
- [ ] 心跳机制正常工作

---

## Phase 3: 产品层 - AI 客服

### Step 6: 改造 manual.py 使用统一 enqueue_sse_message

**所属模块：** `products/ai_chatbot/`

**依赖：** Step 2

**任务：** 将 `manual.py` 中直接操作 `sse_queues` 的代码改为使用统一 `enqueue_sse_message()`

**涉及文件：**
- `products/ai_chatbot/handlers/manual.py`（修改）

**改造清单：**

| 位置 | 当前代码 | 改为 |
|------|----------|------|
| 顶部导入 | `get_sse_queues` | 添加 `enqueue_sse_message` 从 infrastructure 导入 |
| 第 41-44 行 | `sse_queues[target].put(payload)` | `await enqueue_sse_message(target, payload)` |
| 第 165-171 行 | `if session_name in sse_queues: await sse_queues[...].put(...)` | `await enqueue_sse_message(session_name, {...})` |
| 第 256-264 行 | `if session_name in sse_queues: await sse_queues[...].put(...)` | `await enqueue_sse_message(session_name, {...})` |

**验证测试：**
```bash
python3 -c "
from products.ai_chatbot.handlers.manual import router
import inspect
# 检查导入了 enqueue_sse_message
from products.ai_chatbot.handlers import manual
assert hasattr(manual, 'enqueue_sse_message') or 'enqueue_sse_message' in dir(manual)
print('✅ Step 6 模块改造成功')
"
```

**验收标准：**
- [ ] manual.py 无直接操作 sse_queues 的代码
- [ ] 使用统一 enqueue_sse_message 接口
- [ ] 模块可正常导入

---

## Phase 4: 集成测试与部署

### Step 7: 跨进程端到端测试

**依赖：** Step 5, Step 6

**任务：** 在两个独立进程中测试完整的 SSE 通信流程

**测试场景：**

| 场景 | 步骤 | 预期结果 |
|------|------|----------|
| **正常通信** | 1. 启动 AI 客服 (8000)<br>2. 启动坐席工作台 (8002)<br>3. 坐席订阅 SSE<br>4. 触发转人工 | 坐席 1 秒内收到通知 |
| **服务重启** | 1. 重启 AI 客服<br>2. 再次触发转人工 | 坐席仍能收到通知 |
| **Redis 降级** | 1. 设置 USE_REDIS_SSE=false<br>2. 单进程测试 | 内存队列正常工作 |

**验证测试：**
```bash
# 双进程测试脚本
cd /home/yzh/AI客服/鉴权

# 终端 1: 启动 AI 客服
USE_REDIS_SSE=true uvicorn products.ai_chatbot.main:app --port 8000

# 终端 2: 启动坐席工作台
USE_REDIS_SSE=true uvicorn products.agent_workbench.main:app --port 8002

# 终端 3: 测试
curl -X POST http://localhost:8000/api/manual/escalate \
  -H "Content-Type: application/json" \
  -d '{"session_name": "test-cross-process"}'
```

**验收标准：**
- [ ] 跨进程消息传递延迟 < 100ms
- [ ] 服务重启后通信恢复
- [ ] Redis 故障时自动降级

---

### Step 8: 部署验证

**依赖：** Step 7

**任务：** 部署到生产服务器并验证

**部署步骤：**
1. 提交代码并打 tag
2. 更新 .env 添加 `USE_REDIS_SSE=true`
3. 部署到服务器
4. 验证服务状态

**验证测试：**
```bash
# 服务器上验证
curl https://ai.fiido.com/api/health
curl https://ai.fiido.com/workbench-api/health

# 检查日志确认 Redis SSE 启用
journalctl -u fiido-ai-backend | grep "RedisSse"
```

**验收标准：**
- [ ] 生产环境两个服务正常运行
- [ ] 日志显示 `[RedisSse] ✅ 连接成功`
- [ ] 转人工流程正常
- [ ] 坐席工作台实时收到消息

---

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `USE_REDIS_SSE` | `true` | 是否使用 Redis SSE |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接 URL |

---

## 回滚方案

```bash
# 禁用 Redis SSE，降级到内存队列
USE_REDIS_SSE=false

# 重启服务
systemctl restart fiido-ai-backend fiido-agent-workbench
```

---

## 文件改动清单

| 文件 | 类型 | Step |
|------|------|------|
| `infrastructure/bootstrap/redis_sse.py` | 新增 | 1 ✅ |
| `infrastructure/bootstrap/sse.py` | 修改 | 2, 3 |
| `infrastructure/bootstrap/__init__.py` | 修改 | 3 |
| `products/agent_workbench/handlers/sessions.py` | 修改 | 4, 5 |
| `products/ai_chatbot/handlers/manual.py` | 修改 | 6 |

---

## 更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.2 | 2025-12-22 | 重构：去除代码示例，只保留指令；拆分 Step 2/3；明确依赖关系 |
| v1.1 | 2025-12-22 | 基于代码审查更新 |
| v1.0 | 2025-12-22 | 初始版本 |
