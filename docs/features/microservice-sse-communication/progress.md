# 微服务跨进程 SSE 通信 - 开发进度追踪

> **功能名称**：微服务跨进程 SSE 实时通信
> **版本**：v1.2
> **开始日期**：2025-12-22
> **当前步骤**：Step 8 ⏳ 待开始

---

## 完成记录

---

## Step 1: 实现 Redis Pub/Sub SSE 管理器

**完成时间:** 2025-12-22 17:30
**版本号:** v7.6.1
**所属模块:** infrastructure/bootstrap

**完成内容:**
- 创建 `infrastructure/bootstrap/redis_sse.py`
- 实现 `RedisSseManager` 类，使用 `redis.asyncio` 异步 Pub/Sub
- 提供 `publish()` 和 `subscribe()` 异步方法
- 实现单例模式 `init_redis_sse()` / `get_redis_sse_manager()`
- 支持健康检查和优雅关闭

**测试结果:**
- ✅ 管理器初始化成功
- ✅ 单例模式正常工作
- ✅ Redis 连接成功
- ✅ 发布消息到频道成功
- ✅ 订阅频道接收消息成功（跨实例 Pub/Sub 测试通过）
- ✅ 健康检查返回正常
- ✅ 关闭连接正常

**备注:**
- 使用 `redis.asyncio`（redis-py 内置），无需额外依赖
- 订阅者数量为 0 时发布不报错，符合 Redis Pub/Sub 设计

---

## Step 2: 改造 enqueue_sse_message 支持 Redis 发布

**完成时间:** 2025-12-22 18:30
**版本号:** v7.6.2
**所属模块:** infrastructure/bootstrap

**完成内容:**
- 修改 `infrastructure/bootstrap/sse.py`
- 添加 `USE_REDIS_SSE` 环境变量控制（默认 true）
- 添加 `_get_redis_sse_manager()` 延迟加载函数
- 改造 `enqueue_sse_message()` 优先使用 Redis Pub/Sub
- 添加 `_enqueue_to_memory()` 内存队列降级函数
- Redis 失败时自动降级到内存队列，不抛出错误

**测试结果:**
- ✅ USE_REDIS_SSE=true 时消息通过 Redis 发布
- ✅ USE_REDIS_SSE=false 时使用内存队列
- ✅ Redis 异常时自动降级到内存队列

**备注:**
- 延迟加载避免启动时强制依赖 Redis
- 函数签名保持不变，对调用方透明

---

## Step 3: 新增 subscribe_sse_events 订阅接口

**完成时间:** 2025-12-22 19:00
**版本号:** v7.6.3
**所属模块:** infrastructure/bootstrap

**完成内容:**
- 修改 `infrastructure/bootstrap/sse.py`
- 新增 `subscribe_sse_events(target)` 异步生成器函数
- 新增 `_subscribe_from_memory(target)` 内存队列订阅辅助函数
- Redis 模式：订阅 `sse:session:{target}` 频道
- 降级模式：从内存队列读取
- 更新 `infrastructure/bootstrap/__init__.py` 导出

**测试结果:**
- ✅ Redis 模式：订阅频道并接收消息成功
- ✅ 降级模式：从内存队列接收消息成功
- ✅ 发布-订阅端到端通信正常

**备注:**
- 异步生成器支持 `async for` 迭代
- 调用方需在 try/finally 中处理取消

---

## Step 4: 删除本地函数，改用统一接口

**完成时间:** 2025-12-22 19:30
**版本号:** v7.6.4
**所属模块:** products/agent_workbench

**完成内容:**
- 删除 `sessions.py` 中本地定义的 `enqueue_sse_message()` 函数
- 添加 `from infrastructure.bootstrap.sse import enqueue_sse_message` 导入
- 改造 release 端点：2 处 `sse_queues[].put()` → `await enqueue_sse_message()`
- 改造 takeover 端点：2 处 `sse_queues[].put()` → `await enqueue_sse_message()`
- 移除 `if session_name in sse_queues` 检查（统一接口内部处理）

**测试结果:**
- ✅ 模块导入成功
- ✅ 无本地 enqueue_sse_message 定义
- ✅ 无 sse_queues 直接操作

**备注:**
- 统一接口自动处理队列检查，简化调用代码

---

## Step 5: 改造 SSE 事件流端点

**完成时间:** 2025-12-22 19:45
**版本号:** v7.6.5
**所属模块:** products/agent_workbench

**完成内容:**
- 添加 `subscribe_sse_events` 导入
- 删除 `queue = get_or_create_sse_queue()` 直接队列操作
- 使用 `subscribe_sse_events(session_name)` 统一订阅接口
- 保留 30 秒超时心跳机制
- 添加 `StopAsyncIteration` 处理

**测试结果:**
- ✅ 模块导入成功
- ✅ 使用统一订阅接口
- ✅ 无 queue.get() 直接操作
- ✅ 服务启动正常，SSE 端点可访问

**备注:**
- 使用 `subscription.__anext__()` 配合 `asyncio.wait_for` 实现超时心跳
- 跨进程消息通过 Redis Pub/Sub 传递

---

## Step 6: 改造 manual.py 使用统一接口

**完成时间:** 2025-12-22 20:00
**版本号:** v7.6.6
**所属模块:** products/ai_chatbot

**完成内容:**
- 移除 `get_sse_queues` 导入，添加 `enqueue_sse_message` 导入
- 改造 `notify_callback`：使用统一接口
- 改造 `manual_escalate` 端点：状态变化推送改用统一接口
- 改造 `manual_message` 端点：消息推送改用统一接口
- 移除所有 `if session_name in sse_queues` 检查

**测试结果:**
- ✅ 模块导入成功
- ✅ 无 sse_queues 直接操作
- ✅ 使用了 3 次 enqueue_sse_message

**备注:**
- 统一接口自动处理队列检查和 Redis 发布

---

## Step 7: 跨进程端到端测试

**完成时间:** 2025-12-23 00:30
**版本号:** v7.6.7
**所属模块:** 全部

**完成内容:**
- 场景1: 跨进程通信测试 - 使用 Python multiprocessing 模拟两个独立进程
- 场景2: 内存队列降级测试 - USE_REDIS_SSE=false 时使用内存队列
- 场景3: Redis 故障降级测试 - Redis 不可用时自动降级到内存队列
- 场景4: 真实场景测试 - AI客服前端 → 转人工 → 坐席工作台接管 → 发送消息 → AI客服前端同步

**测试中发现的问题及修复:**
- **问题**: AI 客服前端轮询 `/api/sessions/{session_name}` 获取状态，但 AI 客服后端没有此端点
- **原因**: 该端点只存在于坐席工作台后端（8002），AI 客服后端（8000）缺失
- **修复**: 新增 `products/ai_chatbot/handlers/sessions.py`，提供：
  - `GET /api/sessions/{session_name}` - 会话状态查询（供轮询）
  - `GET /api/sessions/{session_name}/events` - SSE 事件流（实时订阅）
- **修改**: 更新 `products/ai_chatbot/routes.py` 注册新路由

**测试结果:**
- ✅ 场景1: 3 条消息通过 Redis Pub/Sub 跨进程传递成功
- ✅ 场景2: USE_REDIS_SSE=false 时正确使用内存队列
- ✅ 场景3: Redis 不可用时自动降级，不中断服务
- ✅ 场景4: AI客服前端能正确同步坐席状态和消息

**备注:**
- 跨进程消息延迟 < 100ms（Redis Pub/Sub 原生支持）
- 降级机制透明，不影响业务逻辑
- 日志清晰标识当前使用模式（Redis/内存）

---

## 步骤总览

| Phase | Step | 标题 | 模块 | 状态 |
|-------|------|------|------|------|
| Phase 1 | Step 1 | 创建 Redis Pub/Sub 管理器 | infrastructure/bootstrap | ✅ 完成 |
| Phase 1 | Step 2 | 改造 enqueue_sse_message 支持 Redis 发布 | infrastructure/bootstrap | ✅ 完成 |
| Phase 1 | Step 3 | 新增 subscribe_sse_events 订阅接口 | infrastructure/bootstrap | ✅ 完成 |
| Phase 2 | Step 4 | 删除本地函数，改用统一接口 | products/agent_workbench | ✅ 完成 |
| Phase 2 | Step 5 | 改造 SSE 事件流端点 | products/agent_workbench | ✅ 完成 |
| Phase 3 | Step 6 | 改造 manual.py 使用统一接口 | products/ai_chatbot | ✅ 完成 |
| Phase 4 | Step 7 | 跨进程端到端测试 | 全部 | ✅ 完成 |
| Phase 4 | Step 8 | 部署验证 | 全部 | ⏳ 待开始 |

---

## 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v7.6.7 | 2025-12-23 | Step 7 完成：跨进程端到端测试通过 |
| v7.6.6 | 2025-12-22 | Step 6 完成：AI 客服改用统一 SSE 接口 |
| v7.6.5 | 2025-12-22 | Step 5 完成：SSE 事件流端点改用订阅接口 |
| v7.6.4 | 2025-12-22 | Step 4 完成：坐席工作台改用统一 SSE 接口 |
| v7.6.3 | 2025-12-22 | Step 3 完成：subscribe_sse_events 订阅接口 |
| v7.6.2 | 2025-12-22 | Step 2 完成：enqueue_sse_message 支持 Redis |
| v7.6.1 | 2025-12-22 | Step 1 完成：Redis SSE 管理器 |
| v7.6.0 | 2025-12-22 | 微服务架构分离，发现 SSE 跨进程问题 |

---

## 技术决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| Redis 客户端 | `redis.asyncio` | 原生异步，高并发性能好 |
| 初始化时机 | lifespan 事件 | 启动时检测连接问题，符合现有模式 |
