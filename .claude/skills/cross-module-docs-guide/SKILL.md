---
name: cross-module-docs-guide
description: 创建或更新跨模块功能文档。支持两种场景：1）新建跨模块功能时生成完整 docs/features 文档；2）已有功能新增需求时迭代更新文档。当用户说"创建跨模块文档"、"生成跨模块需求"、"跨模块功能初始化"、"涉及多个模块的功能"、"扩展跨模块功能"、"新增跨模块需求"、"跨模块 Phase 2"时自动激活
---
# 跨模块文档生成指南

> 遵循 `CLAUDE.md` 最高开发规范 + `Vibe_Coding开发规范流程说明.md` 方法论

## 核心原则

> **"规划就是一切。不要让 AI 自主规划，否则你的代码库会变成一团乱麻。"**

**必须遵守的铁律（来自 CLAUDE.md）：**

- 三层架构：`products/` → `services/` → `infrastructure/`
- 单向依赖：上层可依赖下层，下层不可依赖上层，产品间禁止互相依赖
- 自底向上开发：先 infrastructure → 再 services → 最后 products
- 文档驱动：跨模块功能使用主从文档模式

**跨模块开发特殊规则：**

- 主文档位于 `docs/features/[功能名]/`
- 各模块保留引用文件 `memory-bank/cross-module-refs.md`
- 产品间通过 services 层间接通信，禁止直接 import

---

## 何时使用

### 场景一：新建跨模块功能（从零开始）

- 用户说"创建跨模块文档"
- 用户说"生成跨模块需求"
- 用户说"跨模块功能初始化"
- 用户说"涉及多个模块的功能"
- 需求明确涉及两个或以上 products（如 ai_chatbot + agent_workbench）

### 场景二：迭代更新（已有功能新增需求）

- 用户说"扩展跨模块功能"
- 用户说"新增跨模块需求"
- 用户说"跨模块 Phase 2"
- 用户说"给 [功能名] 添加新功能"
- 用户说"继续开发跨模块功能"

---

## 判断场景的逻辑

**在执行任何操作前，先检查目标功能文档是否已存在：**

```
1. 检查 docs/features/[功能名]/ 是否存在
   ├── 不存在 → 场景一：新建功能，执行完整生成流程
   └── 已存在 → 场景二：迭代更新，执行增量更新流程
```

---

## 主从文档模式

```
┌─────────────────────────────────────────────────────────────┐
│  主文档（docs/features/[功能名]/）                           │
│                                                             │
│  ├── prd.md                  # 完整需求（涵盖所有模块）       │
│  ├── implementation-plan.md  # 分步计划（按模块拆分）        │
│  ├── progress.md             # 统一进度追踪                 │
│  └── architecture.md         # 整体架构说明                 │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  从文档（各模块 memory-bank/cross-module-refs.md）           │
│                                                             │
│  products/ai_chatbot/memory-bank/cross-module-refs.md       │
│  products/agent_workbench/memory-bank/cross-module-refs.md  │
│  ...                                                        │
│                                                             │
│  记录：本模块参与的功能、职责、涉及文件                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 第一步：询问用户需求（必做）

**在生成任何文档之前，必须先向用户询问：**

```
在生成跨模块功能文档之前，请告诉我：

**你要开发什么跨模块功能？**

请用口语化的方式描述：
- 这个功能是什么？解决什么问题？
- 涉及哪些模块？（如 AI 客服、坐席工作台等）
- 各模块的职责分工？
- 有什么技术偏好或限制？

我会根据你的描述，分析涉及的模块，生成完整的跨模块文档。
```

---

## 第二步：分析涉及模块

**收到用户需求后，进行模块分析：**

**分析提示词（内部使用）：**

```
根据用户需求：[需求描述]

请分析：

1. 涉及的产品层模块（products/）
   - 列出每个模块的职责

2. 需要的服务层模块（services/）
   - 标注：✓ 已有 / ✗ 需新建 / ↑ 需扩展

3. 需要的基础设施层模块（infrastructure/）
   - 标注：✓ 已有 / ✗ 需新建 / ↑ 需扩展

4. 开发顺序（自底向上）
   - infrastructure → services → products
```

**输出模板：**

```markdown
【跨模块需求分析】

用户需求：[需求描述]

1. 涉及模块：

   产品层：
   - products/ai_chatbot - [职责描述]
   - products/agent_workbench - [职责描述]

   服务层：
   - services/session - ✓ 已有，需扩展（添加XXX功能）
   - services/xxx - ✗ 需新建

   基础设施层：
   - infrastructure/database - ✓ 已有

2. 开发顺序（自底向上）：
   Phase 1: [基础设施层改动]
   Phase 2: [服务层改动]
   Phase 3: [产品层A改动]
   Phase 4: [产品层B改动]
   Phase 5: 集成测试

是否确认创建跨模块功能文档？
```

---

## 第三步：生成产品需求文档 (prd.md)

**文件名：** `docs/features/[功能名]/prd.md`

**生成提示词（内部使用，将 [功能描述] 替换为用户描述）：**

```
我要开发一个跨模块功能：[功能描述]

涉及模块：[模块列表]

请帮我生成一个跨模块产品需求文档 (PRD)，包含以下部分：

1. 功能概述
   - 功能名称
   - 背景与目标
   - 涉及模块及职责

2. 各模块需求
   - [模块A] 需求（输入/输出/交互流程）
   - [模块B] 需求（输入/输出/交互流程）
   - ...

3. 模块间交互
   - 数据流图
   - 接口定义（API/事件）

4. 用户故事
   - 列出 3-5 个主要场景

5. 成功标准
   - 功能验收标准
   - 性能/安全要求

要求：
- 保持简洁，不要过度设计
- 使用 Markdown 格式
- 明确各模块边界和职责
```

**输出格式：**

```markdown
# [功能名] - 跨模块 PRD

> **文档类型**：跨模块功能 PRD
> **创建日期**：YYYY-MM-DD
> **涉及模块**：[模块1]、[模块2]、...

---

## 一、功能概述

### 1.1 功能名称
[功能名称]

### 1.2 背景与目标
[背景描述、要解决的问题、期望目标]

### 1.3 涉及模块

| 模块 | 路径 | 职责 |
|------|------|------|
| [模块1] | `products/xxx/` | [该模块职责] |
| [模块2] | `products/yyy/` | [该模块职责] |
| [服务] | `services/zzz/` | [该服务职责] |

---

## 二、各模块需求

### 2.1 [模块1] 需求

**输入：**
- [输入描述]

**输出：**
- [输出描述]

**交互流程：**
1. [步骤1]
2. [步骤2]

### 2.2 [模块2] 需求

**输入：**
- [输入描述]

**输出：**
- [输出描述]

**交互流程：**
1. [步骤1]
2. [步骤2]

---

## 三、模块间交互

### 3.1 数据流

（此处绘制数据流图）

### 3.2 接口定义

#### API 接口

| 方法 | 路径 | 调用方 | 提供方 | 说明 |
|------|------|--------|--------|------|
| POST | /api/xxx | [模块1] | [服务] | [说明] |

#### 事件定义

| 事件名 | 发布者 | 订阅者 | 数据格式 |
|--------|--------|--------|----------|
| [事件1] | [模块1] | [模块2] | `{ ... }` |

---

## 四、用户故事

1. 作为[用户角色]，我希望[功能描述]，以便[价值]
2. ...

---

## 五、成功标准

### 5.1 功能验收
- [ ] [验收标准1]
- [ ] [验收标准2]

### 5.2 非功能要求
- 性能：[要求]
- 安全：[要求]
```

**示例输出（微服务 SSE 通信）：**

```markdown
# 微服务跨进程 SSE 通信 - 跨模块 PRD

> **文档类型**：跨模块功能 PRD
> **创建日期**：2025-12-22
> **涉及模块**：ai_chatbot、agent_workbench、infrastructure/bootstrap

---

## 一、功能概述

### 1.1 功能名称
微服务跨进程 SSE 实时通信

### 1.2 背景与目标
当前 AI 客服和坐席工作台作为独立微服务运行，SSE 使用内存队列无法跨进程。
需要改造为 Redis Pub/Sub 实现跨进程实时消息传递。

### 1.3 涉及模块

| 模块 | 路径 | 职责 |
|------|------|------|
| AI 客服 | `products/ai_chatbot/` | 发送转人工消息、状态变化 |
| 坐席工作台 | `products/agent_workbench/` | 订阅并接收实时消息 |
| SSE 管理 | `infrastructure/bootstrap/sse.py` | 统一 SSE 接口 |

---

## 二、各模块需求

### 2.1 AI 客服需求

**输入：**
- 用户触发转人工请求
- 会话状态变化事件

**输出：**
- 发布 SSE 消息到 Redis

**交互流程：**
1. 用户请求转人工
2. 调用 `enqueue_sse_message()` 发送消息
3. 底层自动通过 Redis Pub/Sub 发布

### 2.2 坐席工作台需求

**输入：**
- 订阅 Redis Channel 接收消息

**输出：**
- SSE 事件流推送到前端

**交互流程：**
1. 前端建立 SSE 连接
2. 后端订阅 Redis Channel
3. 收到消息后推送到前端

---

## 三、模块间交互

### 3.1 数据流

AI 客服 ──(PUBLISH)──► Redis Pub/Sub ──(SUBSCRIBE)──► 坐席工作台
                              │
                              ▼
                         sse:session:{name}

### 3.2 接口定义

#### 事件定义

| 事件名 | 发布者 | 订阅者 | 数据格式 |
|--------|--------|--------|----------|
| status_change | ai_chatbot | agent_workbench | `{"type":"status_change","payload":{...}}` |
| transfer_request | ai_chatbot | agent_workbench | `{"type":"transfer_request","payload":{...}}` |

---

## 四、用户故事

1. 作为坐席，我希望在用户请求转人工时立即收到通知，以便快速响应
2. 作为系统管理员，我希望 AI 客服和坐席工作台可以独立部署，互不影响

---

## 五、成功标准

### 5.1 功能验收
- [ ] AI 客服发送消息后，坐席工作台 100ms 内收到
- [ ] Redis 不可用时自动降级到内存队列

### 5.2 非功能要求
- 性能：消息延迟 < 100ms
- 可靠性：支持降级策略
```

---

## 第四步：生成技术栈文档 (tech-stack.md)

**文件名：** `docs/features/[功能名]/tech-stack.md`

**生成提示词（内部使用）：**

```
我正在开发跨模块功能：[功能描述]

涉及模块：[模块列表]

当前项目已有技术栈（Fiido 智能服务平台）：
- 后端: Python/FastAPI
- 前端: React/Vue + TypeScript + Tailwind CSS
- 数据库: PostgreSQL + SQLAlchemy
- 缓存: Redis
- 三层架构: products/ → services/ → infrastructure/

请基于现有技术栈，为跨模块功能推荐：
1. 各模块复用的现有服务
2. 需要的新依赖（如果有）
3. 跨模块通信方案
4. 数据存储方案
5. API 设计建议

要求：
- 优先复用现有技术栈和 services/ 服务
- 避免引入不必要的新依赖
- 遵循三层架构依赖规则
- 考虑企业级场景：高并发、容错、可维护性
```

**输出格式：**

````markdown
# [功能名] - 跨模块技术栈

> **功能名称**：[功能名]
> **创建日期**：YYYY-MM-DD
> **涉及模块**：[模块列表]

---

## 一、复用现有技术栈

| 层级 | 技术/服务 | 用途 |
|------|----------|------|
| 产品层 | products/ai_chatbot | [用途] |
| 产品层 | products/agent_workbench | [用途] |
| 服务层 | services/session | [用途] |
| 基础设施层 | infrastructure/bootstrap | [用途] |
| 数据存储 | Redis / PostgreSQL | [用途] |

## 二、新增依赖

| 依赖 | 版本 | 用途 | 原因 |
|------|------|------|------|
| 无 / [依赖名] | - | - | - |

## 三、跨模块通信方案

### 通信方式选型

| 方式 | 优点 | 缺点 | 是否采用 |
|------|------|------|----------|
| Redis Pub/Sub | 实时、简单 | 不持久化 | ✅ |
| HTTP API | 简单 | 延迟高 | ❌ |
| 消息队列 | 可靠 | 复杂 | ❌ |

### 消息格式

```json
{
  "type": "xxx",
  "payload": {},
  "timestamp": 0
}
```

## 四、数据存储方案

### Redis 数据结构

| Key 模式 | 类型 | 用途 | TTL |
|---------|------|------|-----|
| `xxx:{id}` | String/Hash | [用途] | [时间] |

### 数据库表（如需要）

| 表名 | 用途 |
|------|------|
| [表名] | [用途] |

## 五、API 设计

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| [模块] | POST | /api/xxx | [说明] |
````

**示例输出（微服务 SSE 通信）：**

````markdown
# 微服务跨进程 SSE 通信 - 跨模块技术栈

> **功能名称**：微服务跨进程 SSE 实时通信
> **创建日期**：2025-12-22
> **涉及模块**：infrastructure/bootstrap、products/ai_chatbot、products/agent_workbench

---

## 一、复用现有技术栈

| 层级 | 技术/服务 | 用途 |
|------|----------|------|
| 产品层 | products/ai_chatbot | 发送转人工消息、状态变化消息 |
| 产品层 | products/agent_workbench | 订阅并接收实时消息 |
| 服务层 | services/session | 会话状态管理（已 Redis 化） |
| 基础设施层 | infrastructure/bootstrap/sse.py | SSE 消息队列管理 |
| 数据存储 | Redis | Pub/Sub 跨进程消息传递 |

## 二、新增依赖

| 依赖 | 版本 | 用途 | 原因 |
|------|------|------|------|
| 无 | - | - | 项目已有 redis-py，支持 Pub/Sub |

## 三、跨模块通信方案

### 通信方式选型

| 方式 | 优点 | 缺点 | 是否采用 |
|------|------|------|----------|
| **Redis Pub/Sub** | 实时、简单、项目已有 | 不持久化 | ✅ **采用** |
| HTTP API 轮询 | 简单 | 延迟高、浪费资源 | ❌ |
| Redis Stream | 持久化、消费者组 | 复杂度高 | ❌ |

### Channel 命名规范

| Channel 模式 | 用途 | 示例 |
|-------------|------|------|
| `sse:session:{session_name}` | 会话级消息 | `sse:session:user_123` |
| `sse:agent:{agent_id}` | 坐席级消息 | `sse:agent:agent_001` |
| `sse:broadcast` | 全局广播 | `sse:broadcast` |

### 消息格式

```json
{
  "type": "status_change|new_message|transfer_request",
  "payload": {
    "session_name": "user_123",
    "status": "waiting_agent",
    "data": {}
  },
  "timestamp": 1703246400,
  "source": "ai_chatbot"
}
```

## 四、数据存储方案

### Redis 使用方式

本功能不新增 Redis Key 存储，仅使用 Pub/Sub 功能：

| 功能 | Redis 命令 | 说明 |
|------|-----------|------|
| 发布消息 | `PUBLISH sse:session:{name} {json}` | 发送 SSE 消息 |
| 订阅频道 | `SUBSCRIBE sse:session:{name}` | 订阅 SSE 消息 |

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
````

---

## 第五步：生成实现计划 (implementation-plan.md)

**文件名：** `docs/features/[功能名]/implementation-plan.md`

**生成提示词（内部使用）：**

```

请根据以下 PRD 和技术栈文档生成跨模块实现计划：

【PRD 文档】@prd.md

【技术栈文档】@tech-stack.md

【最高约束性文档】@CLAUDE.md

请生成 implementation-plan.md，要求：

1. 严格遵循自底向上开发顺序：
   Phase 1: infrastructure/（如需要）
   Phase 2: services/（如需要）
   Phase 3: products/[模块A]
   Phase 4: products/[模块B]
   Phase 5: 集成测试
2. 每个 Step 要小且具体
3. 每个 Step 标注所属模块
4. 每个 Step 包含测试方法
5. 只写指令，不写具体代码

格式要求：

## Phase N: [阶段标题]

### Step X: [步骤标题]

- **所属模块**：products/xxx 或 services/xxx
- **任务描述**：做什么
- **涉及文件**：改哪里
- **测试方法**：如何验证
- **验收标准**：通过条件

```

**输出格式：**

````markdown
# [功能名] - 跨模块实现计划

> **预计步骤数**：N
> **开发顺序**：infrastructure → services → products
> **涉及模块**：[模块列表]

---

## 开发阶段总览

```
Phase 1: 基础设施层 (infrastructure/)
└── Step 1-X

Phase 2: 服务层 (services/)
└── Step X+1-Y

Phase 3: 产品层 - [模块A] (products/xxx/)
└── Step Y+1-Z

Phase 4: 产品层 - [模块B] (products/yyy/)
└── Step Z+1-W

Phase 5: 集成测试
└── Step W+1
```

---

## Phase 1: 基础设施层

### Step 1: [步骤标题]

**所属模块：** `infrastructure/xxx/`

**任务描述：**
[具体做什么]

**涉及文件：**
- `infrastructure/xxx/file.py`（新增/修改）

**测试方法：**
```bash
[测试命令]
```

**验收标准：**

- [ ] [标准1]
- [ ] [标准2]

---

## Phase 2: 服务层

### Step 2: [步骤标题]

**所属模块：** `services/xxx/`

[同上结构]

---

## Phase 3: 产品层 - [模块A]

### Step 3: [步骤标题]

**所属模块：** `products/xxx/`

[同上结构]

---

## Phase 4: 产品层 - [模块B]

### Step 4: [步骤标题]

**所属模块：** `products/yyy/`

[同上结构]

---

## Phase 5: 集成测试

### Step 5: 端到端测试

**任务描述：**
验证完整业务流程

**测试场景：**

| 场景 | 步骤 | 预期结果 |
|------|------|----------|
| [场景1] | 1. xxx 2. yyy | [预期] |

**验收标准：**

- [ ] 完整流程通过
- [ ] 模块间数据正确传递
- [ ] 异常处理正常
````

**示例输出（微服务 SSE 通信）：**

````markdown
# 微服务跨进程 SSE 通信 - 跨模块实现计划

> **预计步骤数**：6
> **开发顺序**：infrastructure → products
> **涉及模块**：infrastructure/bootstrap、products/ai_chatbot、products/agent_workbench

---

## 开发阶段总览

```
Phase 1: 基础设施层 (infrastructure/)
└── Step 1-3: Redis SSE 管理器实现

Phase 2: 产品层 - AI 客服 (products/ai_chatbot/)
└── Step 4: 消息发送方改造

Phase 3: 产品层 - 坐席工作台 (products/agent_workbench/)
└── Step 5: SSE 订阅改造

Phase 4: 集成测试
└── Step 6: 端到端测试
```

---

## Phase 1: 基础设施层

### Step 1: 创建 Redis SSE 管理器

**所属模块：** `infrastructure/bootstrap/`

**任务描述：**
创建 `redis_sse.py`，实现 Redis Pub/Sub 的 SSE 消息管理

**涉及文件：**
- `infrastructure/bootstrap/redis_sse.py`（新增）

**接口规格：**
```python
class RedisSSEManager:
    async def publish(self, channel: str, message: dict) -> bool
    async def subscribe(self, channel: str) -> AsyncIterator[dict]
```

**测试方法：**
```bash
python3 -c "
from infrastructure.bootstrap.redis_sse import RedisSSEManager
import asyncio
manager = RedisSSEManager()
asyncio.run(manager.publish('test', {'type': 'test'}))
print('Publish test passed')
"
```

**验收标准：**
- [ ] 可以发布消息到 Redis Channel
- [ ] 可以订阅 Redis Channel 接收消息

---

### Step 2: 改造 SSE 接口支持双模式

**所属模块：** `infrastructure/bootstrap/`

**任务描述：**
修改 `sse.py`，支持 Redis 和内存队列双模式，自动降级

**涉及文件：**
- `infrastructure/bootstrap/sse.py`（修改）

**测试方法：**
```bash
# 测试 Redis 模式
USE_REDIS_SSE=true python3 -c "from infrastructure.bootstrap.sse import enqueue_sse_message"

# 测试降级模式
USE_REDIS_SSE=false python3 -c "from infrastructure.bootstrap.sse import enqueue_sse_message"
```

**验收标准：**
- [ ] USE_REDIS_SSE=true 时使用 Redis
- [ ] USE_REDIS_SSE=false 时使用内存队列

---

## Phase 2: 产品层 - AI 客服

### Step 3: 验证 AI 客服消息发送

**所属模块：** `products/ai_chatbot/`

**任务描述：**
验证现有 `enqueue_sse_message()` 调用自动使用 Redis

**涉及文件：**
- `products/ai_chatbot/handlers/manual.py`（检查，无需修改）

**测试方法：**
```bash
curl -X POST http://localhost:8000/api/manual/escalate \
  -H "Content-Type: application/json" \
  -d '{"session_name": "test_001"}'
```

**验收标准：**
- [ ] 转人工消息通过 Redis 发布
- [ ] 日志显示使用 Redis SSE

---

## Phase 3: 产品层 - 坐席工作台

### Step 4: 改造 SSE 订阅

**所属模块：** `products/agent_workbench/`

**任务描述：**
修改 SSE 事件流端点，使用 `subscribe_sse_events()` 订阅 Redis

**涉及文件：**
- `products/agent_workbench/handlers/sessions.py`（修改）

**测试方法：**
```bash
# 终端1: 启动 SSE 订阅
curl -N http://localhost:8002/api/sessions/test_001/events

# 终端2: 发送消息
curl -X POST http://localhost:8000/api/manual/escalate \
  -d '{"session_name": "test_001"}'
```

**验收标准：**
- [ ] SSE 端点能接收 Redis 消息
- [ ] 消息延迟 < 100ms

---

## Phase 4: 集成测试

### Step 5: 跨进程通信测试

**任务描述：**
验证两个独立进程间的 SSE 通信

**测试场景：**

| 场景 | 步骤 | 预期结果 |
|------|------|----------|
| 正常通信 | 1. 启动两个服务 2. 发送转人工 3. 检查接收 | 100ms 内收到消息 |
| Redis 降级 | 1. 停止 Redis 2. 发送消息 | 日志警告，内存队列工作 |

**验收标准：**
- [ ] 跨进程消息正常传递
- [ ] 降级策略正常工作
- [ ] 无消息丢失
````

---

## 第六步：创建空白追踪文件

### progress.md

**文件名：** `docs/features/[功能名]/progress.md`

```markdown
# [功能名] - 开发进度追踪

> **功能名称**：[功能名]
> **开始日期**：YYYY-MM-DD
> **当前步骤**：Step 1 ⏳ 待开始

---

## 完成记录

（每完成一步在此记录）

---

## 步骤总览

| Phase | Step | 标题 | 模块 | 状态 |
|-------|------|------|------|------|
| Phase 1 | Step 1 | [标题] | infrastructure/xxx | ⏳ 待开始 |
| Phase 2 | Step 2 | [标题] | services/xxx | ⏳ 待开始 |
| Phase 3 | Step 3 | [标题] | products/xxx | ⏳ 待开始 |
| Phase 4 | Step 4 | [标题] | products/yyy | ⏳ 待开始 |
| Phase 5 | Step 5 | 集成测试 | 全部 | ⏳ 待开始 |
```

### architecture.md

**文件名：** `docs/features/[功能名]/architecture.md`

```markdown
# [功能名] - 架构说明

> **功能名称**：[功能名]
> **最后更新**：YYYY-MM-DD
> **遵循规范**：CLAUDE.md 三层架构

---

## 整体架构

（开发过程中逐步补充）

## 模块详情

### products/xxx/

**职责**：[职责描述]

**新增/修改文件**：
（开发时记录）

### products/yyy/

**职责**：[职责描述]

**新增/修改文件**：
（开发时记录）

## 数据流

（开发时记录）

## 接口定义

（开发时记录）
```

---

## 第七步：更新各模块引用

**在每个涉及模块的 `memory-bank/cross-module-refs.md` 添加引用：**

```markdown
## [功能名称]

**主文档**：`docs/features/[功能名]/`

**状态**：⏳ 开发中

**本模块职责**：
[描述本模块在该功能中的职责]

**涉及文件**：
| 文件 | 改动类型 | 说明 |
|------|----------|------|
| （开发时填写） | | |

**对接模块**：
- `products/yyy` - [协作说明]
- `services/zzz` - [依赖说明]
```

---

## 完成后的检查清单

- [ ] 已询问用户需求描述
- [ ] 已分析涉及模块并获用户确认
- [ ] 创建 `docs/features/[功能名]/` 目录
- [ ] 生成 `prd.md`
- [ ] 生成 `tech-stack.md`
- [ ] 生成 `implementation-plan.md`
- [ ] 创建空白 `progress.md`
- [ ] 创建空白 `architecture.md`
- [ ] 更新各模块 `cross-module-refs.md`

---

## 后续：开始开发

文档生成完成后，告知用户：

```
跨模块功能文档已生成完成！

文档位置：docs/features/[功能名]/
- prd.md（完整需求）
- tech-stack.md（技术栈）
- implementation-plan.md（分步计划）
- progress.md（进度追踪）
- architecture.md（架构说明）

已更新模块引用：
- products/xxx/memory-bank/cross-module-refs.md
- products/yyy/memory-bank/cross-module-refs.md

接下来你可以说：
- "开始跨模块 Step 1" 或 "跨模块继续开发" - 执行开发步骤

我会按照 cross-module-workflow 流程：
1. 阅读主文档 + 模块 memory-bank
2. 执行当前步骤（自底向上）
3. 等待你测试验证
4. 更新主文档 progress.md + architecture.md
5. 更新模块 cross-module-refs.md
6. Git commit + tag
7. 继续下一步
```

---

## 模板文件位置

所有模板可从 `docs/features/_templates/` 复制：

```
docs/features/_templates/
├── prd.md                  # PRD 模板
├── implementation-plan.md  # 实现计划模板
├── progress.md             # 进度追踪模板
├── architecture.md         # 架构说明模板
└── cross-module-refs.md    # 模块引用模板
```

---

## 场景二：迭代更新流程（已有功能新增需求）

> **核心原则：在现有文档基础上追加，不要清空重建**

### 第一步：阅读现有文档

**必须先阅读 docs/features/[功能名]/ 中的所有文档，了解：**

- 当前已完成的功能（progress.md）
- 现有架构设计（architecture.md）
- 已有需求（prd.md）
- 已完成的步骤（implementation-plan.md）

同时阅读各模块的 `memory-bank/cross-module-refs.md`，了解各模块已完成的工作。

### 第二步：询问用户新需求

```
我已阅读现有的跨模块功能文档。

当前功能状态：
- 功能名称：[功能名]
- 已完成 Phase N，共 X 个步骤
- 涉及模块：[模块列表]
- 核心功能：[列出已完成功能]

请描述你要新增的功能/需求：
- 这个新功能是什么？
- 与现有功能的关系？
- 是否涉及新的模块？
- 有什么技术约束？
```

### 第三步：增量更新 prd.md

**在文件开头插入新版本章节：**

```markdown
## v2.0 新增需求（YYYY-MM-DD）

### 背景
基于 v1.0 已上线功能，[新需求背景]

### 新增功能（P0）
- [ ] [新功能1]
- [ ] [新功能2]

### 新增模块（如有）

| 模块 | 路径 | 职责 |
|------|------|------|
| [新模块] | `products/zzz/` | [职责] |

### 新增接口（如有）

| 方法 | 路径 | 调用方 | 提供方 | 说明 |
|------|------|--------|--------|------|
| POST | /api/xxx | [模块] | [服务] | [说明] |

### 成功标准
- [ ] [新标准]

---

## v1.0 需求（已完成）
[保留原有内容不变]
```

### 第四步：增量更新 implementation-plan.md

**在文件开头插入新阶段：**

```markdown
## Phase N+1: [新功能名称]（YYYY-MM-DD）

> **前置条件**：Phase 1-N 已完成
> **预计步骤**：Step M+1 ~ Step P
> **涉及模块**：[模块列表]

### Step M+1: [步骤标题]

**所属模块：** `products/xxx/` 或 `services/xxx/`

**任务描述：**
[做什么]

**涉及文件：**
- `path/file.py`（新增/修改）

**测试方法：**
```bash
[测试命令]
\```

**验收标准：**
- [ ] [标准]

---

## Phase 1-N: 初始开发（已完成）

[保留原有内容不变]
```

### 第五步：更新 progress.md

**在步骤总览表格中追加新步骤：**

```markdown
> **当前步骤**：Step M+1 ⏳ 待开始

---

## v2.0 新增步骤

| Phase | Step | 标题 | 模块 | 状态 |
|-------|------|------|------|------|
| Phase N+1 | Step M+1 | [标题] | products/xxx | ⏳ 待开始 |
| Phase N+1 | Step M+2 | [标题] | products/yyy | ⏳ 待开始 |
| Phase N+2 | Step P | 集成测试 | 全部 | ⏳ 待开始 |

---

## v1.0 完成记录

[保留原有内容不变]
```

### 第六步：更新各模块引用

**在各模块 `memory-bank/cross-module-refs.md` 中更新状态：**

```markdown
## [功能名称]

**主文档**：`docs/features/[功能名]/`

**状态**：⏳ v2.0 开发中

**版本历史**：
- v1.0：✅ 已完成（[完成日期]）
- v2.0：⏳ 开发中

**本模块 v2.0 新增职责**：
[描述本模块在新版本中的新增职责]

**v2.0 涉及文件**：
| 文件 | 改动类型 | 说明 |
|------|----------|------|
| （开发时填写） | | |
```

### 第七步：通知用户

```
跨模块功能文档已更新完成！

新增内容：
- prd.md: 添加了 v2.0 需求章节
- implementation-plan.md: 添加了 Phase N+1，共 X 个新步骤
- progress.md: 添加了 v2.0 步骤总览
- 各模块 cross-module-refs.md: 更新了状态和版本历史

接下来你可以说：
- "开始跨模块 Step M+1" - 执行新功能开发
- "跨模块继续开发" - 从 Phase N+1 第一步开始

我会继续按照 cross-module-workflow 流程执行。
```

---

## 迭代更新的检查清单

- [ ] 已阅读现有 docs/features/[功能名]/ 所有文档
- [ ] 已阅读各模块 cross-module-refs.md
- [ ] 已询问用户新需求描述
- [ ] 已在 prd.md 开头追加 v2.0 章节
- [ ] 已在 implementation-plan.md 追加新 Phase
- [ ] 已在 progress.md 追加 v2.0 步骤
- [ ] 已更新各模块 cross-module-refs.md 状态
- [ ] 保留了所有历史内容
- [ ] 通知用户可以继续开发

---

## 相关资源

| 资源             | 路径                                              |
| ---------------- | ------------------------------------------------- |
| 单模块文档生成   | `.claude/skills/memory-bank-guide/SKILL.md`     |
| 跨模块开发执行   | `.claude/skills/cross-module-workflow/SKILL.md` |
| Vibe Coding 规范 | `docs/参考资料/Vibe_Coding开发规范流程说明.md`  |
| 架构规范         | `CLAUDE.md`                                     |
| 模块清单         | `PROJECT_OVERVIEW.md`                           |
