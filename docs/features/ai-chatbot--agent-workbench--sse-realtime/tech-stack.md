# 微服务跨进程 SSE 通信 - 跨模块技术栈

> **功能名称**：微服务跨进程 SSE 实时通信
> **版本**：v1.0
> **创建日期**：2025-12-22
> **最后更新**：2025-12-22
> **涉及模块**：infrastructure/bootstrap、products/ai_chatbot、products/agent_workbench

---

## 一、复用现有技术栈

| 层级 | 技术/服务 | 用途 |
|------|----------|------|
| 产品层 | products/ai_chatbot | 发送转人工消息、状态变化消息 |
| 产品层 | products/agent_workbench | 订阅并接收实时消息 |
| 服务层 | services/session | 会话状态管理（已 Redis 化） |
| 基础设施层 | infrastructure/bootstrap/sse.py | SSE 消息队列管理 |
| 基础设施层 | infrastructure/bootstrap/redis.py | Redis 客户端单例 |
| 数据存储 | Redis | Pub/Sub 跨进程消息传递 |

---

## 二、新增依赖

| 依赖 | 版本 | 用途 | 原因 |
|------|------|------|------|
| 无 | - | - | 项目已有 redis-py，支持 Pub/Sub |

**说明**：无需新增 Python 依赖，项目已使用的 `redis` 库原生支持 Pub/Sub 功能。

---

## 三、跨模块通信方案

### 通信方式选型

| 方式 | 优点 | 缺点 | 是否采用 |
|------|------|------|----------|
| **Redis Pub/Sub** | 实时、简单、项目已有 Redis | 不持久化 | ✅ **采用** |
| HTTP API 轮询 | 简单 | 延迟高、浪费资源 | ❌ |
| Redis Stream | 持久化、消费者组 | 复杂度高 | ❌ |
| RabbitMQ/Kafka | 可靠、功能强大 | 需新增组件、复杂 | ❌ |

### 选择 Redis Pub/Sub 的原因

1. **项目已有 Redis**：无需引入新组件
2. **SSE 场景适合**：实时推送，不需要消息持久化
3. **实现简单**：改动最小，API 保持兼容
4. **支持降级**：Redis 不可用时可降级到内存队列

### Channel 命名规范

| Channel 模式 | 用途 | 示例 |
|-------------|------|------|
| `sse:session:{session_name}` | 会话级消息 | `sse:session:user_123_abc` |
| `sse:agent:{agent_id}` | 坐席级消息 | `sse:agent:agent_001` |
| `sse:broadcast` | 全局广播 | `sse:broadcast` |

### 消息格式

```json
{
  "type": "status_change|new_message|transfer_request|heartbeat",
  "payload": {
    "session_name": "user_123_abc",
    "status": "waiting_agent",
    "data": {}
  },
  "timestamp": 1703246400,
  "source": "ai_chatbot|agent_workbench|system"
}
```

### 消息类型定义

| type | 发布者 | 订阅者 | 说明 |
|------|--------|--------|------|
| `status_change` | ai_chatbot | agent_workbench | 会话状态变化 |
| `transfer_request` | ai_chatbot | agent_workbench | 转人工请求 |
| `new_message` | ai_chatbot/agent | 双方 | 新消息通知 |
| `agent_joined` | agent_workbench | ai_chatbot | 坐席接入 |
| `agent_left` | agent_workbench | ai_chatbot | 坐席离开 |

---

## 四、数据存储方案

### Redis 使用方式

本功能不新增 Redis Key 存储，仅使用 Pub/Sub 功能：

| 功能 | Redis 命令 | 说明 |
|------|-----------|------|
| 发布消息 | `PUBLISH sse:session:{name} {json}` | 发送 SSE 消息 |
| 订阅频道 | `SUBSCRIBE sse:session:{name}` | 订阅 SSE 消息 |
| 模式订阅 | `PSUBSCRIBE sse:session:*` | 订阅所有会话消息 |

### 现有 Redis 数据结构（不变）

| Key 模式 | 类型 | 用途 | 所属服务 |
|---------|------|------|---------|
| `session:{name}` | String(JSON) | 会话状态数据 | services/session |
| `status:{status}` | Set | 会话状态索引 | services/session |

---

## 五、API 设计

### 现有 API（无需修改）

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| ai_chatbot | POST | /api/manual/escalate | 触发转人工 |
| agent_workbench | GET | /api/sessions/{name}/events | SSE 事件流 |

### 内部接口（需改造）

| 模块 | 函数 | 当前实现 | 改造后 |
|------|------|---------|--------|
| infrastructure | `enqueue_sse_message()` | 内存队列 | Redis PUBLISH |
| infrastructure | `subscribe_sse_events()` | 新增 | Redis SUBSCRIBE |

---

## 六、降级策略

```python
# 环境变量控制
USE_REDIS_SSE = os.getenv("USE_REDIS_SSE", "true").lower() == "true"

# 自动降级逻辑
if USE_REDIS_SSE and redis_available:
    # 使用 Redis Pub/Sub（支持跨进程）
    await redis_sse_manager.publish(channel, message)
else:
    # 降级到内存队列（仅单进程有效）
    await memory_queue.put(message)
    logger.warning("Redis SSE 不可用，降级到内存队列")
```

---

## 七、性能考虑

| 指标 | 目标 | 方案 |
|------|------|------|
| 消息延迟 | < 100ms | Redis Pub/Sub 内网延迟极低 |
| 并发订阅 | 1000+ | Redis 单实例支持百万级订阅 |
| 内存占用 | 最小化 | Pub/Sub 不存储消息 |

---

## 八、安全考虑

| 风险 | 措施 |
|------|------|
| Channel 注入 | session_name 校验，禁止特殊字符 |
| 消息伪造 | 消息包含 source 字段，接收方验证 |
| 订阅泛滥 | 限制单连接订阅 Channel 数量 |
