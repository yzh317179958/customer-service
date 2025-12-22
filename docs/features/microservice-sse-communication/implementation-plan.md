# 微服务跨进程 SSE 通信 - 跨模块实现计划

> **版本**：v1.1
> **预计步骤数**：7
> **开发顺序**：infrastructure → products
> **涉及模块**：infrastructure/bootstrap、products/ai_chatbot、products/agent_workbench

---

## 开发阶段总览

```
Phase 1: 基础设施层 (infrastructure/)
   └── Step 1: 实现 Redis Pub/Sub SSE 管理器（使用 redis.asyncio）
   └── Step 2: 改造 sse.py 支持双模式（发布 + 订阅）

Phase 2: 产品层 - 坐席工作台 (products/agent_workbench/)
   └── Step 3: 改造所有 SSE 调用点（删除本地函数，使用统一接口）
   └── Step 4: 改造 SSE 事件流订阅（使用 subscribe_sse_events）

Phase 3: 产品层 - AI 客服 (products/ai_chatbot/)
   └── Step 5: 改造所有 SSE 调用点（使用统一接口）

Phase 4: 集成测试
   └── Step 6: 端到端测试
   └── Step 7: 部署验证
```

---

## Phase 1: 基础设施层

### Step 1: 实现 Redis Pub/Sub SSE 管理器

**所属模块：** `infrastructure/bootstrap/`

**任务描述：**
创建 `redis_sse.py`，使用 `redis.asyncio` 实现异步 Pub/Sub SSE 消息管理

**涉及文件：**
- `infrastructure/bootstrap/redis_sse.py`（新增）

**实现要点：**
```python
# -*- coding: utf-8 -*-
"""
基础设施 - Redis Pub/Sub SSE 管理器

使用 redis.asyncio 实现跨进程 SSE 消息传递
"""

import json
import asyncio
from typing import AsyncGenerator, Optional, Any
import redis.asyncio as aioredis


class RedisSseManager:
    """Redis Pub/Sub SSE 管理器"""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self._redis: Optional[aioredis.Redis] = None
        self._pubsub: Optional[aioredis.client.PubSub] = None

    async def connect(self):
        """连接 Redis"""
        if self._redis is None:
            self._redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            print(f"[RedisSse] ✅ 连接成功: {self.redis_url}")

    async def publish(self, channel: str, message: dict) -> int:
        """
        发布消息到 Redis 频道

        Args:
            channel: 频道名（如 sse:session:xxx）
            message: 消息内容 dict

        Returns:
            订阅者数量
        """
        if self._redis is None:
            await self.connect()

        payload = json.dumps(message, ensure_ascii=False)
        result = await self._redis.publish(channel, payload)
        return result

    async def subscribe(self, channel: str) -> AsyncGenerator[dict, None]:
        """
        订阅 Redis 频道，返回异步生成器

        Args:
            channel: 频道名

        Yields:
            解析后的消息 dict
        """
        if self._redis is None:
            await self.connect()

        pubsub = self._redis.pubsub()
        await pubsub.subscribe(channel)
        print(f"[RedisSse] 📡 订阅频道: {channel}")

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        yield json.loads(message["data"])
                    except json.JSONDecodeError:
                        print(f"[RedisSse] ⚠️ JSON 解析失败: {message['data']}")
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            print(f"[RedisSse] 🔌 取消订阅: {channel}")

    async def close(self):
        """关闭连接"""
        if self._redis:
            await self._redis.close()
            self._redis = None
            print("[RedisSse] 🔌 连接关闭")


# 全局单例
_redis_sse_manager: Optional[RedisSseManager] = None


def init_redis_sse(redis_url: str = None) -> RedisSseManager:
    """
    初始化 Redis SSE 管理器（单例）

    Args:
        redis_url: Redis 连接 URL，默认从环境变量读取

    Returns:
        RedisSseManager 实例
    """
    global _redis_sse_manager

    if _redis_sse_manager is not None:
        return _redis_sse_manager

    import os
    url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
    _redis_sse_manager = RedisSseManager(redis_url=url)

    return _redis_sse_manager


def get_redis_sse_manager() -> Optional[RedisSseManager]:
    """获取 Redis SSE 管理器实例"""
    return _redis_sse_manager
```

**测试方法：**
```bash
cd /home/yzh/AI客服/鉴权
python3 -c "
import asyncio
from infrastructure.bootstrap.redis_sse import init_redis_sse

async def test():
    manager = init_redis_sse()
    await manager.connect()

    # 测试发布
    result = await manager.publish('sse:test', {'type': 'test', 'data': 'hello'})
    print(f'✅ 发布成功，订阅者数量: {result}')

    await manager.close()

asyncio.run(test())
"
```

**验收标准：**
- [ ] RedisSseManager 类可正常初始化和连接
- [ ] publish 方法可发送消息到 Redis 频道
- [ ] subscribe 方法返回异步生成器，可接收消息
- [ ] 连接异常时抛出明确错误

---

### Step 2: 改造 sse.py 支持双模式

**所属模块：** `infrastructure/bootstrap/`

**任务描述：**
改造现有 `sse.py`，新增 `subscribe_sse_events` 函数，支持 Redis Pub/Sub 和内存队列双模式

**涉及文件：**
- `infrastructure/bootstrap/sse.py`（修改）
- `infrastructure/bootstrap/__init__.py`（修改导出）

**实现要点：**

```python
# 新增到 sse.py

import os
from typing import AsyncGenerator

# 模式控制
USE_REDIS_SSE = os.getenv("USE_REDIS_SSE", "true").lower() == "true"

# 延迟导入避免循环依赖
_redis_sse_manager = None


def _get_redis_sse():
    """获取 Redis SSE 管理器（延迟加载）"""
    global _redis_sse_manager
    if _redis_sse_manager is None and USE_REDIS_SSE:
        try:
            from infrastructure.bootstrap.redis_sse import get_redis_sse_manager
            _redis_sse_manager = get_redis_sse_manager()
        except Exception as e:
            print(f"[SSE] ⚠️ Redis SSE 不可用: {e}")
    return _redis_sse_manager


async def enqueue_sse_message(target: str, payload: dict):
    """
    发送 SSE 消息（自动选择 Redis 或内存）

    Args:
        target: 目标标识（session_name 或 agent_id）
        payload: 消息内容
    """
    manager = _get_redis_sse()

    if manager:
        # Redis 模式：发布到频道
        channel = f"sse:session:{target}"
        try:
            await manager.publish(channel, payload)
            return
        except Exception as e:
            print(f"[SSE] ⚠️ Redis 发布失败，降级到内存: {e}")

    # 降级到内存队列
    global _sse_queues
    if target not in _sse_queues:
        _sse_queues[target] = asyncio.Queue()
        print(f"[SSE] ✅ 创建内存队列: {target}")

    queue = _sse_queues[target]
    try:
        queue.put_nowait(payload)
    except asyncio.QueueFull:
        try:
            queue.get_nowait()
        except asyncio.QueueEmpty:
            pass
        queue.put_nowait(payload)


async def subscribe_sse_events(target: str) -> AsyncGenerator[dict, None]:
    """
    订阅 SSE 事件（自动选择 Redis 或内存）

    Args:
        target: 目标标识

    Yields:
        消息 dict
    """
    manager = _get_redis_sse()

    if manager:
        # Redis 模式：订阅频道
        channel = f"sse:session:{target}"
        try:
            async for message in manager.subscribe(channel):
                yield message
            return
        except Exception as e:
            print(f"[SSE] ⚠️ Redis 订阅失败，降级到内存: {e}")

    # 降级到内存队列
    global _sse_queues
    if target not in _sse_queues:
        _sse_queues[target] = asyncio.Queue()

    queue = _sse_queues[target]
    while True:
        message = await queue.get()
        yield message
```

**更新 `__init__.py` 导出：**
```python
from infrastructure.bootstrap.sse import (
    get_sse_queues,
    get_or_create_sse_queue,
    enqueue_sse_message,
    subscribe_sse_events,  # 新增
    remove_sse_queue,
    reset
)
```

**测试方法：**
```bash
cd /home/yzh/AI客服/鉴权

# 测试 Redis 模式
USE_REDIS_SSE=true python3 -c "
import asyncio
from infrastructure.bootstrap.redis_sse import init_redis_sse
from infrastructure.bootstrap.sse import enqueue_sse_message, subscribe_sse_events

async def test():
    # 先初始化 Redis SSE
    manager = init_redis_sse()
    await manager.connect()

    # 测试发送
    await enqueue_sse_message('test-session', {'type': 'test'})
    print('✅ enqueue_sse_message Redis 模式成功')

asyncio.run(test())
"

# 测试降级模式
USE_REDIS_SSE=false python3 -c "
import asyncio
from infrastructure.bootstrap.sse import enqueue_sse_message

async def test():
    await enqueue_sse_message('test-session', {'type': 'test'})
    print('✅ enqueue_sse_message 内存模式成功')

asyncio.run(test())
"
```

**验收标准：**
- [ ] `enqueue_sse_message` 支持 Redis 和内存双模式
- [ ] `subscribe_sse_events` 新增成功，支持双模式
- [ ] `USE_REDIS_SSE=false` 时降级到内存队列
- [ ] Redis 异常时自动降级，不影响业务

---

## Phase 2: 产品层 - 坐席工作台

### Step 3: 改造所有 SSE 调用点

**所属模块：** `products/agent_workbench/`

**任务描述：**
1. 删除 `handlers/sessions.py` 中本地定义的 `enqueue_sse_message` 函数
2. 将所有直接操作 `sse_queues[target].put()` 的代码改为使用 `enqueue_sse_message()`

**涉及文件：**
- `products/agent_workbench/handlers/sessions.py`（修改）
- `products/agent_workbench/dependencies.py`（可能需要更新导入）

**改造清单：**

| 行号 | 原代码 | 改为 |
|------|--------|------|
| 74-82 | 本地 `enqueue_sse_message` 函数 | 删除，改用 infrastructure 层 |
| 317-329 | `sse_queues[session_name].put({...})` | `await enqueue_sse_message(session_name, {...})` |
| 416-428 | `sse_queues[session_name].put({...})` | `await enqueue_sse_message(session_name, {...})` |

**改造示例：**
```python
# 删除本地函数（第 74-82 行）
# async def enqueue_sse_message(target: str, message: dict):  # 删除

# 顶部导入改为
from infrastructure.bootstrap.sse import enqueue_sse_message, subscribe_sse_events

# 原代码（第 317-329 行）
if session_name in sse_queues:
    await sse_queues[session_name].put({
        "type": "status_change",
        ...
    })

# 改为
await enqueue_sse_message(session_name, {
    "type": "status_change",
    ...
})
```

**测试方法：**
```bash
cd /home/yzh/AI客服/鉴权
python3 -c "
from products.agent_workbench.handlers.sessions import router
print('✅ sessions.py 导入成功，无本地 enqueue_sse_message')
"
```

**验收标准：**
- [ ] `handlers/sessions.py` 无本地 `enqueue_sse_message` 函数
- [ ] 所有 SSE 消息发送使用 `infrastructure.bootstrap.sse.enqueue_sse_message`
- [ ] 模块可正常导入

---

### Step 4: 改造 SSE 事件流订阅

**所属模块：** `products/agent_workbench/`

**任务描述：**
改造 `session_events()` 端点，使用 `subscribe_sse_events()` 替代直接队列操作

**涉及文件：**
- `products/agent_workbench/handlers/sessions.py`（修改）

**原代码（第 834-899 行）：**
```python
@router.get("/{session_name}/events")
async def session_events(session_name: str, ...):
    # ...
    queue = get_or_create_sse_queue(session_name)

    async def event_generator():
        # ...
        while True:
            payload = await asyncio.wait_for(queue.get(), timeout=30.0)
            yield f"data: {json.dumps(payload)}\n\n"
```

**改为：**
```python
from infrastructure.bootstrap.sse import subscribe_sse_events

@router.get("/{session_name}/events")
async def session_events(session_name: str, ...):
    # ...

    async def event_generator():
        try:
            # 发送连接成功事件
            yield f"data: {json.dumps({'type': 'connected', 'session_name': session_name, 'timestamp': int(time.time())})}\n\n"

            # 使用统一的订阅接口
            async for message in subscribe_sse_events(session_name):
                yield f"data: {json.dumps(message, ensure_ascii=False)}\n\n"

        except asyncio.CancelledError:
            print(f"⏹️  SSE 断开: {session_name}")
            raise
```

**注意：** 心跳机制需要调整。由于 `subscribe_sse_events` 内部已处理阻塞，心跳可以通过定期发送特殊消息实现，或在 Redis 层面实现。

**测试方法：**
```bash
# 启动坐席工作台
cd /home/yzh/AI客服/鉴权
uvicorn products.agent_workbench.main:app --port 8002 &

# 测试 SSE 端点（需要有效 token）
curl -N "http://localhost:8002/api/sessions/test-session/events?token=xxx"
```

**验收标准：**
- [ ] SSE 端点正常返回事件流
- [ ] Redis 模式下能接收跨进程消息
- [ ] 内存模式下保持原有行为

---

## Phase 3: 产品层 - AI 客服

### Step 5: 改造所有 SSE 调用点

**所属模块：** `products/ai_chatbot/`

**任务描述：**
将所有直接操作 `sse_queues[target].put()` 的代码改为使用 `enqueue_sse_message()`

**涉及文件：**
- `products/ai_chatbot/handlers/manual.py`（修改）

**改造清单：**

| 行号 | 原代码 | 改为 |
|------|--------|------|
| 41-44 | `sse_queues[target].put(payload)` | `await enqueue_sse_message(target, payload)` |
| 165-171 | `sse_queues[session_name].put({...})` | `await enqueue_sse_message(session_name, {...})` |
| 256-264 | `sse_queues[session_name].put({...})` | `await enqueue_sse_message(session_name, {...})` |

**改造示例：**
```python
# 顶部导入
from infrastructure.bootstrap.sse import enqueue_sse_message

# 原代码（第 165-171 行）
if session_name in sse_queues:
    await sse_queues[session_name].put({
        "type": "status_change",
        "status": session_state.status,
        ...
    })

# 改为（无需检查 session_name in sse_queues）
await enqueue_sse_message(session_name, {
    "type": "status_change",
    "status": session_state.status,
    ...
})
```

**测试方法：**
```bash
cd /home/yzh/AI客服/鉴权
python3 -c "
from products.ai_chatbot.handlers.manual import router
print('✅ manual.py 导入成功')
"
```

**验收标准：**
- [ ] `handlers/manual.py` 所有 SSE 发送使用统一接口
- [ ] 无直接操作 `sse_queues` 的代码
- [ ] 模块可正常导入

---

## Phase 4: 集成测试

### Step 6: 端到端测试

**任务描述：**
测试完整的跨进程通信流程

**前置条件：**
1. 确保 Redis 服务运行
2. 在两个独立终端启动两个微服务

**启动命令：**
```bash
# 终端 1: AI 客服
cd /home/yzh/AI客服/鉴权
USE_REDIS_SSE=true uvicorn products.ai_chatbot.main:app --port 8000

# 终端 2: 坐席工作台
cd /home/yzh/AI客服/鉴权
USE_REDIS_SSE=true uvicorn products.agent_workbench.main:app --port 8002
```

**测试场景：**

| 场景 | 步骤 | 预期结果 |
|------|------|----------|
| **正常跨进程通信** | 1. 启动两个微服务<br>2. 坐席登录并订阅 SSE<br>3. AI 客服触发转人工 | 坐席工作台 1 秒内收到 status_change 通知 |
| **服务重启** | 1. 重启 AI 客服<br>2. 再次触发转人工 | 坐席工作台仍能收到（Redis 连接自动恢复） |
| **Redis 降级** | 1. 停止 Redis<br>2. 单进程模式测试 | 内存队列正常工作，日志显示降级警告 |
| **消息格式验证** | 检查 SSE 消息内容 | 包含 type、payload、timestamp 字段 |

**验收标准：**
- [ ] 跨进程消息传递延迟 < 100ms
- [ ] 服务重启不影响通信
- [ ] Redis 故障时自动降级
- [ ] 日志清晰显示运行模式

---

### Step 7: 部署验证

**任务描述：**
部署到生产服务器并验证

**部署步骤：**

```bash
# 1. 提交代码
git add .
git commit -m "feat: Redis Pub/Sub SSE 跨进程通信 v7.7.0

- 新增 infrastructure/bootstrap/redis_sse.py（异步 Pub/Sub）
- 改造 sse.py 支持 Redis/内存双模式
- 改造 ai_chatbot 和 agent_workbench SSE 调用点
- 支持 USE_REDIS_SSE 环境变量切换

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

git tag v7.7.0
git push origin main --tags

# 2. 更新 .env
echo "USE_REDIS_SSE=true" >> /opt/fiido-ai-service/.env

# 3. 部署到服务器
ssh root@8.211.27.199 'cd /opt/fiido-ai-service && git pull && \
  systemctl restart fiido-ai-backend && \
  systemctl restart fiido-agent-workbench'

# 4. 验证
curl https://ai.fiido.com/api/health
curl https://ai.fiido.com/workbench-api/health
```

**验收标准：**
- [ ] 生产环境两个服务正常运行
- [ ] 日志显示 `[RedisSse] ✅ 连接成功`
- [ ] 转人工流程正常
- [ ] 坐席工作台实时收到消息

---

## 环境变量配置

```bash
# .env 新增配置
USE_REDIS_SSE=true                    # 启用 Redis SSE（默认 true）
REDIS_URL=redis://localhost:6379/0    # Redis 连接 URL（已有）
```

---

## 回滚方案

如果出现问题，可以通过环境变量快速回滚：

```bash
# 禁用 Redis SSE，降级到内存队列
USE_REDIS_SSE=false

# 重启服务
systemctl restart fiido-ai-backend fiido-agent-workbench
```

---

## 附录：需要改造的文件清单

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `infrastructure/bootstrap/redis_sse.py` | 新增 | Redis Pub/Sub 管理器 |
| `infrastructure/bootstrap/sse.py` | 修改 | 新增 subscribe_sse_events，改造 enqueue |
| `infrastructure/bootstrap/__init__.py` | 修改 | 更新导出 |
| `products/agent_workbench/handlers/sessions.py` | 修改 | 删除本地函数，改用统一接口 |
| `products/agent_workbench/lifespan.py` | 修改 | 初始化 RedisSseManager |
| `products/ai_chatbot/handlers/manual.py` | 修改 | 改用统一接口 |
| `products/ai_chatbot/lifespan.py` | 修改 | 初始化 RedisSseManager |

---

## 更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.1 | 2025-12-22 | 基于代码审查更新：明确使用 redis.asyncio、修正 Step 调整为 7 步、增加具体行号和改造清单 |
| v1.0 | 2025-12-22 | 初始版本 |
