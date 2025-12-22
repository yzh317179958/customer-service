# 微服务跨进程 SSE 通信 - 架构说明

> **功能名称**：微服务跨进程 SSE 实时通信
> **版本**：v1.1
> **最后更新**：2025-12-22
> **遵循规范**：CLAUDE.md 三层架构

---

## 整体架构

### 改造前（内存队列）

```
┌─────────────────┐                    ┌─────────────────┐
│   AI 客服       │                    │  坐席工作台      │
│   (8000)        │                    │    (8002)        │
│                 │                    │                  │
│ _sse_queues     │    ❌ 隔离         │ _sse_queues     │
│ (asyncio.Queue) │ ←───────────────→  │ (asyncio.Queue) │
└─────────────────┘                    └─────────────────┘
```

### 改造后（Redis Pub/Sub）

```
┌─────────────────┐                    ┌─────────────────┐
│   AI 客服       │                    │  坐席工作台      │
│   (8000)        │                    │    (8002)        │
│                 │                    │                  │
│ enqueue_sse_    │                    │ subscribe_sse_  │
│   message()     │                    │   events()      │
└────────┬────────┘                    └────────┬────────┘
         │                                      │
         │ PUBLISH                    SUBSCRIBE │
         │                                      │
         └──────────────┬───────────────────────┘
                        │
                        ▼
               ┌─────────────────┐
               │     Redis       │
               │   Pub/Sub       │
               │                 │
               │ Channel:        │
               │ sse:session:*   │
               │ sse:agent:*     │
               └─────────────────┘
```

---

## 模块详情

### infrastructure/bootstrap/redis_sse.py

**职责**：提供 Redis Pub/Sub 的 SSE 消息管理

**新增文件**：`infrastructure/bootstrap/redis_sse.py`（Step 1 完成）

**主要类/函数：**

| 名称 | 类型 | 说明 |
|------|------|------|
| `RedisSseManager` | 类 | Redis Pub/Sub 管理器 |
| `publish(channel, message)` | 异步方法 | 发布消息到频道 |
| `subscribe(channel)` | 异步生成器 | 订阅频道，返回消息流 |
| `connect()` | 异步方法 | 建立 Redis 连接 |
| `close()` | 异步方法 | 关闭连接 |
| `health_check()` | 异步方法 | 健康检查 |
| `init_redis_sse()` | 函数 | 初始化单例 |
| `get_redis_sse_manager()` | 函数 | 获取单例实例 |
| `shutdown_redis_sse()` | 异步函数 | 关闭管理器 |

**技术实现：**
- 使用 `redis.asyncio`（redis-py 内置）
- 单例模式，全局共享实例
- 支持自动连接和重连
- 优雅关闭和资源清理

### infrastructure/bootstrap/sse.py

**职责**：统一 SSE 接口，支持双模式（Redis/内存）

**修改文件**：
（开发时记录）

### products/ai_chatbot/

**职责**：发送 SSE 消息（转人工、状态变化等）

**涉及文件**：
- `handlers/manual.py` - 转人工消息发送

### products/agent_workbench/

**职责**：订阅并接收 SSE 消息

**涉及文件**：
- `handlers/sessions.py` - SSE 事件流端点

---

## 数据流

### 转人工消息流

```
1. 用户请求转人工
   │
   ▼
2. AI 客服 POST /api/manual/escalate
   │
   ▼
3. enqueue_sse_message(session_name, {...})
   │
   ▼
4. Redis PUBLISH sse:session:{name}
   │
   ▼
5. 坐席工作台 SUBSCRIBE sse:session:{name}
   │
   ▼
6. SSE 事件推送到前端
   │
   ▼
7. 前端显示转接通知
```

---

## 接口定义

### Redis Channel 命名规范

| Channel | 格式 | 用途 |
|---------|------|------|
| 会话级 | `sse:session:{session_name}` | 特定会话的消息 |
| 坐席级 | `sse:agent:{agent_id}` | 特定坐席的消息 |
| 广播 | `sse:broadcast` | 全局广播 |

### 消息格式

```json
{
  "type": "status_change|new_message|transfer_request",
  "payload": {
    "session_name": "xxx",
    "status": "waiting_agent",
    "...": "..."
  },
  "timestamp": 1703246400,
  "source": "ai_chatbot"
}
```

---

## 配置项

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `USE_REDIS_SSE` | `true` | 是否使用 Redis SSE |
| `REDIS_SSE_CHANNEL_PREFIX` | `sse:` | 频道前缀 |

---

## 降级策略

```python
# 自动降级逻辑
if USE_REDIS_SSE and redis_available:
    # 使用 Redis Pub/Sub
    await redis_sse_manager.publish(channel, message)
else:
    # 降级到内存队列（仅单进程有效）
    await memory_queue.put(message)
```
