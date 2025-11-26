# 人工接管功能开发 - 技术约束与开发原则

## 📋 文档信息

- **文档版本**: v1.0
- **创建时间**: 2025-11-21
- **依赖文档**: TECHNICAL_CONSTRAINTS.md
- **文档性质**: 🔴 **强制性开发约束** - 所有开发必须遵守

---

## 🎯 文档目的

本文档基于 `TECHNICAL_CONSTRAINTS.md` 中定义的核心技术约束,明确**人工接管功能开发**的边界和原则,确保:

1. ✅ 人工接管功能不破坏现有AI对话能力
2. ✅ 严格遵守 Coze 平台 API 调用规范
3. ✅ 所有新功能向后兼容
4. ✅ 扩展而非替换核心功能

---

## 🚨 核心铁律(必须遵守)

### 铁律 1: 不可修改的核心接口

以下接口是系统基石,**严禁修改其核心逻辑**:

```
🔴 不可修改:
- POST /api/chat              (同步AI对话)
- POST /api/chat/stream       (流式AI对话)
- POST /api/conversation/new  (创建会话)
```

**允许的操作**:
- ✅ 在调用前添加前置检查(如状态检查)
- ✅ 在返回后添加后置处理(如日志记录)
- ❌ **禁止**修改 Coze API 调用方式
- ❌ **禁止**修改返回的数据结构

**示例 - P0-1任务中的正确做法**:

```python
# ✅ 正确 - 在现有逻辑前添加状态检查
@app.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    # 【新增】人工接管状态检查 - 前置检查
    if session_store and regulator:
        session_state = await session_store.get_or_create(...)

        # 如果在人工接管中,拒绝AI对话
        if session_state.status in [SessionStatus.PENDING_MANUAL, SessionStatus.MANUAL_LIVE]:
            raise HTTPException(
                status_code=409,
                detail=f"SESSION_IN_MANUAL_MODE: {session_state.status}"
            )

    # ... 以下是原有的 Coze API 调用逻辑,完全不动 ...
    access_token = token_manager.get_access_token(session_name=session_id)

    payload = {
        "workflow_id": WORKFLOW_ID,
        "app_id": APP_ID,
        "additional_messages": [...]
    }

    async with async_http_client.stream(...) as response:
        # ... 原有SSE解析逻辑 ...
```

```python
# ❌ 错误 - 修改了核心逻辑
@app.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    # ❌ 错误:改变了Coze API调用方式
    if is_manual_mode:
        # 调用人工API而非Coze API
        return call_manual_agent(request)

    # ❌ 错误:修改了payload结构
    payload = {
        "workflow_id": WORKFLOW_ID,
        "manual_mode": True  # 新增字段会导致Coze API报错
    }
```

---

### 铁律 2: Coze API 调用规范(不可违反)

#### 2.1 必须使用 SSE 流式响应

```python
# ✅ 正确 - 使用 stream() 方法
async with async_http_client.stream(
    "POST",
    f"{api_base}/v1/workflows/chat",
    headers=headers,
    json=payload
) as response:
    async for chunk in response.aiter_bytes():
        # 解析SSE流
        ...

# ❌ 错误 - 使用 post() 方法会失败
response = await async_http_client.post(...)
data = response.json()  # Coze返回的是SSE流,不是JSON!
```

#### 2.2 SSE 事件解析规范

```python
# ✅ 正确 - 从顶层提取字段
event_data = json.loads(data_content)
if event_data.get("type") == "answer" and event_data.get("content"):
    message_content += event_data["content"]

# ❌ 错误 - Coze不返回嵌套结构
if "message" in event_data:
    content = event_data["message"]["content"]  # 这个字段不存在!
```

#### 2.3 必需的请求参数

```python
# ✅ 正确 - 包含所有必需字段
payload = {
    "workflow_id": WORKFLOW_ID,      # 必需
    "app_id": APP_ID,                # 必需
    "additional_messages": [         # 必需
        {
            "content": user_message,
            "content_type": "text",
            "role": "user"
        }
    ],
    "conversation_id": conv_id,      # 可选(多轮对话需要)
    "parameters": custom_params      # 可选
}

# ❌ 错误 - 缺少必需字段
payload = {
    "workflow_id": WORKFLOW_ID,
    # 缺少 app_id 会导致API调用失败!
    "messages": [...]  # 字段名错误,应为 additional_messages
}
```

---

### 铁律 3: OAuth + JWT 鉴权机制(不可绕过)

#### 3.1 Token 获取方式

```python
# ✅ 正确 - 使用 token_manager
access_token = token_manager.get_access_token(
    session_name=session_id  # 必须包含session_name实现隔离
)

# ❌ 错误 - 硬编码Token
access_token = "hardcoded_token"  # Token会过期!

# ❌ 错误 - 绕过token_manager
access_token = jwt.encode(...)  # 缺少缓存和过期管理!
```

#### 3.2 会话隔离机制

```python
# ✅ 正确 - 每个用户独立session_name
session_id = request.user_id or str(uuid.uuid4())
access_token = token_manager.get_access_token(session_name=session_id)

# ❌ 错误 - 所有用户共用一个Token
access_token = token_manager.get_access_token()  # 会导致对话混乱!
```

---

## 📐 人工接管功能开发边界

### ✅ 允许的扩展(不涉及Coze API)

以下功能**完全自由设计**,不受Coze平台限制:

#### 1. 会话状态管理 (`src/session_state.py`)

```python
# ✅ 允许自由设计
class SessionState(BaseModel):
    session_name: str
    status: SessionStatus           # ✅ 可自由定义状态
    escalation: Optional[EscalationInfo]  # ✅ 可添加任意字段
    assigned_agent: Optional[AgentInfo]   # ✅ 可自定义数据模型
    history: List[Message]          # ✅ 可自定义消息格式
```

**约束**:
- ⚠️ 状态管理失败不应影响AI对话功能
- ⚠️ 建议异步保存状态,避免阻塞API响应

#### 2. 监管引擎 (`src/regulator.py`)

```python
# ✅ 允许自由设计
class Regulator:
    def evaluate(self, session, user_message, ai_response):
        # ✅ 可自由实现监管规则
        # ✅ 可添加关键词检测、失败检测、VIP检测等
        # ✅ 可自定义触发条件和优先级
```

**约束**:
- ⚠️ 监管逻辑应异步处理,不阻塞AI回复
- ⚠️ 触发监管后可以拒绝AI请求,但需返回明确错误

#### 3. 人工接管API (新增接口)

```python
# ✅ 允许自由设计新接口
@app.post("/api/manual/escalate")        # ✅ 新增接口
@app.post("/api/manual/messages")        # ✅ 新增接口
@app.post("/api/sessions/{id}/takeover") # ✅ 新增接口
@app.post("/api/sessions/{id}/release")  # ✅ 新增接口
@app.get("/api/sessions")                # ✅ 新增接口
```

**约束**:
- ✅ 可以自由设计接口路径和参数
- ✅ 可以自由设计返回格式
- ⚠️ 不得占用现有路由 (`/api/chat`, `/api/chat/stream`, etc.)

#### 4. SSE 队列管理 (消息推送)

```python
# ✅ 允许扩展SSE事件类型
sse_queues: dict[str, asyncio.Queue] = {}  # ✅ 可自由实现

async def push_sse_event(session_id: str, event: dict):
    # ✅ 可自定义事件类型
    event = {
        "type": "manual_message",   # ✅ 新事件类型
        "role": "agent",            # ✅ 自定义字段
        "content": "...",
        "agent_info": {...}         # ✅ 自定义字段
    }
```

**约束**:
- ✅ 可以添加新的SSE事件类型
- ⚠️ 不得修改现有事件类型格式 (`type: message`, `type: done`)

---

### ❌ 禁止的操作

#### 1. 禁止修改AI对话核心流程

```python
# ❌ 禁止 - 在人工模式下改变AI对话逻辑
@app.post("/api/chat/stream")
async def chat_stream_async(request: ChatRequest):
    if is_manual_mode:
        # ❌ 错误:直接返回人工消息
        return StreamingResponse(manual_stream(), ...)

    # 原有逻辑...
```

**正确做法**:

```python
# ✅ 正确 - 在前置检查中拒绝请求
@app.post("/api/chat/stream")
async def chat_stream_async(request: ChatRequest):
    # 前置检查
    if session_state.status in [PENDING_MANUAL, MANUAL_LIVE]:
        # 返回错误,不继续执行
        async def error_stream():
            yield f"data: {json.dumps({'type': 'error', 'content': 'MANUAL_IN_PROGRESS'})}\n\n"
        return StreamingResponse(error_stream(), ...)

    # ... 原有Coze API调用逻辑完全不动 ...
```

#### 2. 禁止修改SSE流格式

```python
# ❌ 禁止 - 修改Coze返回的事件格式
async def generate_stream():
    # ❌ 错误:改变事件格式
    yield f"{json.dumps({'message': content})}\n\n"  # 缺少 "data: " 前缀!

    # ❌ 错误:改变type字段含义
    yield f"data: {json.dumps({'type': 'ai_message', ...})}\n\n"  # type应为'message'

# ✅ 正确 - 保持格式一致
async def generate_stream():
    # AI消息
    yield f"data: {json.dumps({'type': 'message', 'content': ai_content})}\n\n"

    # 完成标记
    yield f"data: {json.dumps({'type': 'done', 'content': ''})}\n\n"

    # 可以添加新的事件类型(不影响现有)
    yield f"data: {json.dumps({'type': 'manual_message', 'role': 'agent', ...})}\n\n"
```

#### 3. 禁止绕过Token机制

```python
# ❌ 禁止 - 绕过OAuth认证
async with async_http_client.stream(
    "POST",
    f"{api_base}/v1/workflows/chat",
    headers={"Authorization": "Bearer hardcoded_token"},  # ❌ 错误!
    ...
)

# ✅ 正确 - 始终使用token_manager
access_token = token_manager.get_access_token(session_name=session_id)
async with async_http_client.stream(
    "POST",
    f"{api_base}/v1/workflows/chat",
    headers={"Authorization": f"Bearer {access_token}"},  # ✅ 正确
    ...
)
```

---

## 🔧 开发实施指导

### P0-1: 修复状态机逻辑

**任务**: 在 `pending_manual` 状态下阻止AI对话

**技术约束检查**:
- ✅ 不修改 `/api/chat` 核心逻辑
- ✅ 只添加前置状态检查
- ✅ Coze API调用部分完全不动

**实施代码**:

```python
# backend.py line 532-580
@app.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    # ... 现有的session_id提取逻辑 ...

    # 【新增】前置状态检查 - 不影响原有逻辑
    if session_store and regulator:
        session_state = await session_store.get_or_create(
            session_name=session_id,
            conversation_id=conversation_id_for_state
        )

        # 如果正在人工接管中,直接拒绝
        if session_state.status in [SessionStatus.PENDING_MANUAL, SessionStatus.MANUAL_LIVE]:
            raise HTTPException(
                status_code=409,
                detail=f"SESSION_IN_MANUAL_MODE: {session_state.status}"
            )

    # ===== 以下是原有逻辑,完全不动 =====

    # 获取Token (原有逻辑)
    access_token = token_manager.get_access_token(session_name=session_id)

    # 构建payload (原有逻辑)
    payload = {
        "workflow_id": WORKFLOW_ID,
        "app_id": APP_ID,
        "additional_messages": [...]
    }

    # 调用Coze API (原有逻辑)
    async with async_http_client.stream(...) as response:
        # ... 原有SSE解析逻辑 ...

    return ChatResponse(success=True, message=message_content)
```

**验证**:
- ✅ 现有AI对话功能不受影响
- ✅ Coze API调用方式未改变
- ✅ 返回格式保持一致

---

### P0-2: 实现坐席接入API

**任务**: 实现 `POST /api/sessions/{session_name}/takeover`

**技术约束检查**:
- ✅ 这是新增接口,不涉及Coze API
- ✅ 可以自由设计参数和返回格式
- ✅ 不影响现有接口

**实施代码**:

```python
# backend.py (新增接口)
@app.post("/api/sessions/{session_name}/takeover")
async def takeover_session(session_name: str, request: dict):
    """
    坐席接入会话 - 完全新增的业务逻辑
    不涉及Coze API调用,可以自由设计
    """
    if not session_store:
        raise HTTPException(status_code=503, detail="SessionStore not initialized")

    # ✅ 自由设计:获取参数
    agent_id = request.get("agent_id")
    agent_name = request.get("agent_name")

    # ✅ 自由设计:业务逻辑
    session_state = await session_store.get(session_name)

    # 防抢单检查
    if session_state.status == SessionStatus.MANUAL_LIVE:
        raise HTTPException(
            status_code=409,
            detail=f"ALREADY_TAKEN: 已被{session_state.assigned_agent.name}接入"
        )

    # 分配坐席
    session_state.assigned_agent = AgentInfo(id=agent_id, name=agent_name)
    session_state.transition_status(SessionStatus.MANUAL_LIVE)

    await session_store.save(session_state)

    # ✅ 自由设计:返回格式
    return {"success": True, "data": session_state.model_dump()}
```

**验证**:
- ✅ 未修改任何现有接口
- ✅ 不涉及Coze API调用
- ✅ 完全独立的业务逻辑

---

### P0-8: 扩展SSE事件处理

**任务**: 在流式接口中添加人工消息推送

**技术约束检查**:
- ✅ 可以添加新的事件类型
- ❌ 不得修改现有事件格式
- ✅ 保持向后兼容

**实施代码**:

```python
# backend.py line 805-950
@app.post("/api/chat/stream")
async def chat_stream_async(request: ChatRequest):
    async def generate_stream():
        # ... 省略前置逻辑 ...

        # ===== Coze AI响应处理 (原有逻辑,不动) =====
        async with async_http_client.stream(...) as response:
            buffer = ""
            async for chunk in response.aiter_bytes():
                # ... 原有SSE解析逻辑 ...

                # AI消息 (原有格式,不动)
                if event_data.get("type") == "answer":
                    yield f"data: {json.dumps({'type': 'message', 'content': content})}\n\n"

                # 完成标记 (原有格式,不动)
                if event_data.get("status") == "completed":
                    yield f"data: {json.dumps({'type': 'done', 'content': ''})}\n\n"

        # ===== 【新增】人工消息推送 (不影响原有) =====

        # 检查SSE队列中是否有人工消息
        if session_id in sse_queues:
            queue = sse_queues[session_id]

            # 非阻塞检查队列
            while not queue.empty():
                try:
                    manual_event = await asyncio.wait_for(queue.get(), timeout=0.1)

                    # ✅ 新增事件类型 - 不影响前端对现有事件的处理
                    if manual_event.get("type") == "manual_message":
                        yield f"data: {json.dumps(manual_event)}\n\n"

                    elif manual_event.get("type") == "status_change":
                        yield f"data: {json.dumps(manual_event)}\n\n"

                except asyncio.TimeoutError:
                    break

    return StreamingResponse(generate_stream(), media_type="text/event-stream")
```

**验证**:
- ✅ 原有事件格式未改变
- ✅ 新增事件类型独立添加
- ✅ 前端对现有事件的处理不受影响

---

## 📋 开发检查清单

在提交代码前,必须通过以下检查:

### Checklist 1: Coze API约束检查

- [ ] 是否使用 `stream()` 方法调用Coze API? (不使用 `post()`)
- [ ] 是否从顶层提取 `type` 和 `content` 字段? (不假设嵌套结构)
- [ ] payload是否包含 `workflow_id` 和 `app_id`?
- [ ] 是否通过 `token_manager.get_access_token()` 获取Token?
- [ ] 是否支持 `session_name` 参数实现会话隔离?

### Checklist 2: 核心接口兼容性检查

- [ ] `/api/chat` 接口是否仍正常工作?
- [ ] `/api/chat/stream` 接口是否仍正常工作?
- [ ] ChatRequest 和 ChatResponse 数据结构是否未改变?
- [ ] SSE 事件格式是否保持一致?

### Checklist 3: 新功能独立性检查

- [ ] 新增功能是否独立于核心功能?
- [ ] 新增功能失败是否会导致AI对话失败?
- [ ] 是否添加了新增接口的测试用例?
- [ ] 状态管理失败是否会阻塞AI响应?

### Checklist 4: 功能测试

```bash
# 测试1: AI对话功能正常
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"你好","user_id":"test_001"}'
# 预期: {"success":true,"message":"...AI回复..."}

# 测试2: 流式对话功能正常
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"你好","user_id":"test_002"}' \
  --no-buffer
# 预期: 实时SSE流 data: {"type":"message","content":"..."}\n\n

# 测试3: 会话隔离正常
curl -X POST http://localhost:8000/api/chat \
  -d '{"message":"记住我叫张三","user_id":"user_001"}'
curl -X POST http://localhost:8000/api/chat \
  -d '{"message":"我叫什么？","user_id":"user_002"}'
# 预期: user_002的回复不应包含"张三"

# 测试4: 人工接管状态下AI被阻止 (新增)
curl -X POST http://localhost:8000/api/manual/escalate \
  -d '{"session_name":"test_003","reason":"user_request"}'
curl -X POST http://localhost:8000/api/chat \
  -d '{"message":"你好","user_id":"test_003"}'
# 预期: HTTP 409, detail包含"SESSION_IN_MANUAL_MODE"
```

---

## 🎯 总结

### 核心原则

1. **Coze API调用部分 = 不可变区域**
   - 使用 `stream()` 方法
   - 解析顶层 `type` 和 `content`
   - 包含必需参数 `workflow_id`, `app_id`
   - 通过 `token_manager` 获取Token
   - 支持 `session_name` 隔离

2. **本地业务逻辑 = 自由设计区域**
   - SessionState 状态管理
   - Regulator 监管引擎
   - 人工接管API
   - SSE队列推送

3. **扩展策略 = 前置检查 + 后置处理**
   - ✅ 在现有接口前添加状态检查
   - ✅ 在现有流程后添加额外逻辑
   - ❌ 不修改核心Coze API调用
   - ❌ 不改变现有数据结构

### 违规后果

- **轻度违规**: 代码审查拒绝,要求重构
- **重度违规**: 立即回滚,重新设计

---

## 🔄 模块化开发与回归测试流程 ⭐ **强制执行**

### 核心原则

**每完成一个功能模块，必须执行完整的回归测试，确保不破坏任何现有功能。**

开发必须遵循以下原则：
1. **模块化**: 新功能独立封装，不侵入核心代码
2. **向后兼容**: 绝对不能破坏原有功能
3. **渐进式扩展**: 在现有基础上扩展，而非替换
4. **完整验证**: 每次开发后执行全量回归测试

---

### 📋 强制回归测试清单

每完成一个功能模块后，**必须按顺序执行以下所有测试**：

#### 第一层：核心功能测试 (P0 - 必须100%通过)

| 测试项 | 测试命令 | 预期结果 | 说明 |
|--------|----------|----------|------|
| **1. Coze API 连接** | `curl http://localhost:8000/api/health` | `coze_connected: true` | 验证 Coze API 可用 |
| **2. AI 对话 (同步)** | `curl -X POST /api/chat -d '{"message":"你好","user_id":"test"}'` | `success: true` + AI回复 | 核心对话功能 |
| **3. AI 对话 (流式)** | `curl -X POST /api/chat/stream --no-buffer` | SSE 事件流 | 流式响应功能 |
| **4. 会话隔离** | 运行 `python3 tests/test_simple.py` | 全部通过 | 多用户隔离验证 |

```bash
# 测试脚本 - 核心功能验证
echo "=== 核心功能回归测试 ==="

# 1. 健康检查
echo "测试1: 健康检查"
curl -s http://localhost:8000/api/health | grep -q '"coze_connected":true' && echo "✅ 通过" || echo "❌ 失败"

# 2. AI对话
echo "测试2: AI对话"
curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"你好","user_id":"regression_test"}' | grep -q '"success":true' && echo "✅ 通过" || echo "❌ 失败"

# 3. 会话隔离
echo "测试3: 会话隔离"
python3 tests/test_simple.py && echo "✅ 通过" || echo "❌ 失败"
```

#### 第二层：人工接管功能测试 (P0 - 必须100%通过)

| 测试项 | 测试命令 | 预期结果 |
|--------|----------|----------|
| **5. 人工升级** | `POST /api/manual/escalate` | 状态变为 `pending_manual` |
| **6. AI阻止** | 在 manual 状态下调用 `/api/chat` | HTTP 409 |
| **7. 坐席接入** | `POST /api/sessions/{id}/takeover` | 状态变为 `manual_live` |
| **8. 发送消息** | `POST /api/manual/messages` | 消息写入成功 |
| **9. 释放会话** | `POST /api/sessions/{id}/release` | 状态恢复 `bot_active` |

```bash
# 测试脚本 - 人工接管功能
echo "=== 人工接管回归测试 ==="

# 创建测试会话
SESSION="regression_manual_$(date +%s)"
curl -s -X POST http://localhost:8000/api/conversation/new \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION\"}" > /dev/null

# 5. 人工升级
echo "测试5: 人工升级"
curl -s -X POST http://localhost:8000/api/manual/escalate \
  -H "Content-Type: application/json" \
  -d "{\"session_name\": \"$SESSION\", \"reason\": \"manual\"}" | grep -q '"status":"pending_manual"' && echo "✅ 通过" || echo "❌ 失败"

# 6. AI阻止
echo "测试6: AI阻止"
curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"test\", \"user_id\": \"$SESSION\"}" | grep -q 'SESSION_IN_MANUAL_MODE' && echo "✅ 通过" || echo "❌ 失败"

# 7. 坐席接入
echo "测试7: 坐席接入"
curl -s -X POST "http://localhost:8000/api/sessions/$SESSION/takeover" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "test_agent", "agent_name": "测试坐席"}' | grep -q '"status":"manual_live"' && echo "✅ 通过" || echo "❌ 失败"

# 8. 发送消息
echo "测试8: 发送消息"
curl -s -X POST http://localhost:8000/api/manual/messages \
  -H "Content-Type: application/json" \
  -d "{\"session_name\": \"$SESSION\", \"role\": \"agent\", \"content\": \"测试消息\", \"agent_info\": {\"agent_id\": \"test_agent\", \"agent_name\": \"测试坐席\"}}" | grep -q '"success":true' && echo "✅ 通过" || echo "❌ 失败"

# 9. 释放会话
echo "测试9: 释放会话"
curl -s -X POST "http://localhost:8000/api/sessions/$SESSION/release" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "test_agent", "reason": "resolved"}' | grep -q '"status":"bot_active"' && echo "✅ 通过" || echo "❌ 失败"
```

#### 第三层：坐席工作台功能测试 (P0 - 必须100%通过)

| 测试项 | 测试命令 | 预期结果 |
|--------|----------|----------|
| **10. 会话列表** | `GET /api/sessions?status=pending_manual` | 返回会话数组 |
| **11. 统计信息** | `GET /api/sessions/stats` | 返回统计数据 |
| **12. TypeScript** | `npx vue-tsc --noEmit` | 无错误 |

```bash
# 测试脚本 - 坐席工作台
echo "=== 坐席工作台回归测试 ==="

# 10. 会话列表
echo "测试10: 会话列表"
curl -s "http://localhost:8000/api/sessions?status=pending_manual" | grep -q '"success":true' && echo "✅ 通过" || echo "❌ 失败"

# 11. 统计信息
echo "测试11: 统计信息"
curl -s http://localhost:8000/api/sessions/stats | grep -q '"success":true' && echo "✅ 通过" || echo "❌ 失败"

# 12. TypeScript检查
echo "测试12: TypeScript检查"
cd agent-workbench && npx vue-tsc --noEmit && echo "✅ 通过" || echo "❌ 失败"
```

#### 第四层：新增功能测试 (根据本次开发内容)

**每次开发新功能后，在此处添加该功能的测试用例**

---

### 📝 开发完成检查清单

每完成一个功能模块，必须完成以下步骤：

#### Step 1: 执行回归测试
```bash
# 执行全量回归测试
./tests/regression_test.sh

# 或手动执行上述测试脚本
```

**结果要求**: 所有测试必须100%通过，任何失败必须修复后才能继续

#### Step 2: 更新约束文档

在本文档中添加/更新以下内容：

1. **新增约束**: 本次开发引入的技术约束
2. **新增变量**: 引入的新状态、配置项
3. **接口变更**: 新增/修改的 API
4. **依赖关系**: 新模块与现有模块的依赖

格式模板：
```markdown
### 约束N: [约束名称] ⭐ **[日期] 新增**

**来源模块**: [P0-XX 任务名称]

**约束内容**:
- 具体约束1
- 具体约束2

**新增变量**:
- `变量名`: 类型 - 说明

**新增接口**:
- `METHOD /api/path` - 功能说明

**依赖关系**:
- 依赖 [现有模块名]
- 被 [其他模块] 依赖
```

#### Step 3: 更新版本记录

在 `README.md` 中添加版本更新记录

#### Step 4: 代码提交

确认以上步骤完成后，方可提交代码

---

### 🚨 回归测试失败处理

如果回归测试失败：

1. **立即停止开发** - 不继续新功能
2. **定位问题** - 分析是本次修改导致还是环境问题
3. **修复问题** - 优先恢复核心功能
4. **重新测试** - 全量回归测试通过后才能继续
5. **记录问题** - 在文档中记录问题和解决方案

**严禁行为**:
- ❌ 忽略失败的测试继续开发
- ❌ 注释掉失败的测试用例
- ❌ 修改测试预期以通过测试

---

### 📊 功能模块清单

以下是已实现的功能模块及其测试要求：

| 模块 | 功能 | 测试要求 | 状态 |
|------|------|----------|------|
| **核心-1** | Coze API 调用 | 健康检查 + AI对话 | ✅ 必测 |
| **核心-2** | 会话隔离 | test_simple.py | ✅ 必测 |
| **P0-1** | 状态机逻辑 | AI阻止测试 | ✅ 必测 |
| **P0-2** | 坐席接入 | takeover 测试 | ✅ 必测 |
| **P0-3** | 会话列表 | sessions API | ✅ 必测 |
| **P0-4** | 核心人工API | escalate/messages/release | ✅ 必测 |
| **P0-5** | SSE推送 | 状态变化事件 | ✅ 必测 |
| **P0-6~9** | 用户前端 | 转人工/消息渲染 | ✅ 必测 |
| **P0-10** | 工作台项目 | TypeScript检查 | ✅ 必测 |
| **P0-11** | 登录认证 | 路由守卫 | ✅ 必测 |
| **P0-12** | 会话列表UI | 列表显示 | ✅ 必测 |
| **P0-13** | 接入操作 | 防抢单 | ✅ 必测 |
| **P0-14** | 坐席聊天 | 消息发送 | ✅ 必测 |
| **P0-15** | 释放操作 | 状态恢复 | ✅ 必测 |

**后续开发的新模块必须添加到此清单**

---

## 🧪 验证状态 (2025-11-21)

基于 `docs/核心功能全面验证报告.md` 的测试结果:

### 约束遵守验证结果

| 约束项 | 验证状态 | 测试结果 |
|--------|---------|----------|
| **铁律1: 不可修改核心接口** | ✅ 完全遵守 | Coze API 调用逻辑未改变，同步/流式接口均正常 |
| **铁律2: Coze API 调用规范** | ✅ 完全遵守 | SSE 流式响应、事件解析格式完全符合规范 |
| **铁律3: OAuth+JWT 鉴权** | ✅ 完全遵守 | 会话隔离机制正常，session_name 正确传递 |
| **P0-1: AI对话阻止逻辑** | ✅ 验证通过 | pending_manual 和 manual_live 状态正确返回 HTTP 409 |
| **P0-2: 坐席接入API** | ✅ 验证通过 | 防抢单逻辑正常，状态转换正确 |
| **P0-3: 会话列表API** | ✅ 验证通过 | 查询、过滤、分页功能正常 |

**总体通过率**: 15/15 测试通过 (100%)

**系统状态**: 🎉 生产可用 (Production Ready)

---

## 📝 开发过程中的新发现约束

### 约束4: EscalationReason 枚举值强制验证

**发现日期**: 2025-11-21
**问题**: 测试中发现 `POST /api/manual/escalate` 使用非枚举值 `reason: "test"` 会导致 HTTP 500 错误

**强制约束**:
```python
# ✅ 正确 - 必须使用枚举值
class EscalationReason(str, Enum):
    KEYWORD = "keyword"       # 关键词触发
    FAIL_LOOP = "fail_loop"   # AI连续失败
    SENTIMENT = "sentiment"   # 情绪检测
    VIP = "vip"               # VIP用户
    MANUAL = "manual"         # 手动请求

# ❌ 错误 - 使用自定义字符串
{"reason": "test"}           # 会导致验证失败
{"reason": "user_request"}   # 会导致验证失败
```

**正确用法**:
```bash
# 用户主动请求人工
curl -X POST /api/manual/escalate \
  -d '{"session_name":"session_123","reason":"manual"}'

# 关键词触发
curl -X POST /api/manual/escalate \
  -d '{"session_name":"session_123","reason":"keyword"}'
```

**验证代码位置**: `tests/test_核心功能验证.py:305`

---

### 约束5: 会话隔离的正确实现方式 ⭐

**发现日期**: 2025-11-21
**问题**: 初始测试显示会话隔离失败，Session B 知道了 Session A 的信息

**根本原因**: 未遵循 Coze 平台的正确实现方式 - **必须在打开页面时立即调用 `/api/conversation/new`**

**强制约束**:

```python
# ❌ 错误 - 直接发送消息（依赖 Coze 自动生成 conversation_id）
POST /api/chat
{
  "message": "记住，我是张三",
  "user_id": "session_a"
  # 缺少 conversation_id，会导致 Coze 可能复用其他 conversation
}

# ✅ 正确 - 预先创建独立的 conversation_id
# 步骤1: 打开页面时立即创建 conversation
POST /api/conversation/new
{"session_id": "session_a"}
# 响应: {"conversation_id": "7574681165306363909"}

# 步骤2: 携带 conversation_id 发送消息
POST /api/chat
{
  "message": "记住，我是张三",
  "user_id": "session_a",
  "conversation_id": "7574681165306363909"  # 关键！
}
```

**实际验证结果**:
```
Session A conversation_id: 7574681165306363909
Session B conversation_id: 7574686112397737989
✅ 两个 conversation_id 不同，隔离生效

Session A 记得: "你是张三啊，记住了哈..."
Session B 不知道: "你是那个在找fiido骑行乐趣的杨子豪呗..."
✅ 会话完全隔离
```

**前端实现要求**:

```typescript
// Vue 3 前端实现示例
export const useChatStore = defineStore('chat', () => {
  const conversationId = ref<string>('')

  // 初始化时立即创建 conversation
  async function initConversation() {
    const response = await fetch('/api/conversation/new', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId.value })
    })
    const data = await response.json()
    conversationId.value = data.conversation_id
  }

  // 组件挂载时调用
  onMounted(async () => {
    await initConversation()
  })

  return { conversationId, initConversation }
})
```

**参考文档**:
- `Coze会话隔离最终解决方案.md`
- `docs/核心功能全面验证报告.md` 第2节

**验证代码位置**: `tests/test_核心功能验证.py:143-276`

---

### 约束6: API 路由顺序要求

**发现日期**: 2025-11-21
**问题**: `GET /api/sessions/stats` 返回 404，被 `/api/sessions/{session_name}` 路由捕获

**强制约束**:

```python
# ❌ 错误 - stats 在后面会被 {session_name} 捕获
@app.get("/api/sessions/{session_name}")
async def get_session(session_name: str):
    ...

@app.get("/api/sessions/stats")  # "stats" 被当作 session_name!
async def get_stats():
    ...

# ✅ 正确 - 具体路由必须在参数化路由之前
@app.get("/api/sessions/stats")
async def get_stats():
    ...

@app.get("/api/sessions/{session_name}")
async def get_session(session_name: str):
    ...
```

**规则**: 所有包含路径参数的路由必须放在最后定义

**验证代码位置**: `backend.py:1183-1218` (stats路由已移至正确位置)

---

## 🔐 生产环境安全约束

### 约束7: 敏感信息处理

**强制要求**:
```python
# ❌ 禁止 - 在日志中暴露敏感信息
logger.info(f"User token: {access_token}")
logger.info(f"User ID: {user_id}, Password: {password}")

# ✅ 正确 - 脱敏处理
logger.info(f"User token: {access_token[:10]}...")
logger.info(f"User login: {user_id}")
```

### 约束8: 错误信息处理

**强制要求**:
```python
# ❌ 禁止 - 暴露内部实现细节
raise HTTPException(
    status_code=500,
    detail=f"Database error: {str(db_exception)}"
)

# ✅ 正确 - 返回通用错误信息
raise HTTPException(
    status_code=500,
    detail="Internal server error"
)
# 详细错误记录到日志
logger.error(f"DB error: {str(db_exception)}")
```

---

## 🎨 前端开发约束 (P0-4 至 P0-6 新增)

### 约束9: 前端状态变更规范 ⭐ **P0-6 新增**

**发现日期**: 2025-11-21
**问题**: P0-6 转人工按钮依赖 `canEscalate` 计算属性，该属性依赖 `sessionStatus` 和 `isEscalating` 状态

**强制约束**:
```typescript
// ❌ 错误 - 直接修改状态
sessionStatus.value = 'manual_live'  // 不会触发审计日志，破坏状态机

// ✅ 正确 - 使用状态更新方法
updateSessionStatus('manual_live')  // 触发日志，维护状态机一致性
```

**规则**:
1. **任何修改 `sessionStatus` 必须使用 `updateSessionStatus()` 方法**
2. **不能直接修改 `sessionStatus.value`**
3. **确保 `canEscalate` 计算属性能正确响应**
4. **状态变更必须记录到控制台日志**

**验证代码位置**:
- `frontend/src/stores/chatStore.ts:201-205` (updateSessionStatus 方法)
- `frontend/src/stores/chatStore.ts:94-96` (canEscalate 计算属性)

**依赖关系**:
- `canEscalate` 依赖 `sessionStatus` 和 `isEscalating`
- 转人工按钮依赖 `canEscalate`
- 任何破坏状态一致性的修改会导致按钮禁用逻辑失效

---

### 约束10: 系统消息格式规范 ⭐ **P0-6 新增**

**发现日期**: 2025-11-21
**问题**: P0-6 转人工功能添加系统消息，需要统一格式以保持一致性

**强制约束**:
```typescript
// ❌ 错误 - 格式不一致
chatStore.addMessage({
  id: Date.now().toString(),  // 普通ID
  role: 'system',
  content: '转人工成功',
  timestamp: new Date()
  // 缺少 sender
})

// ✅ 正确 - 标准系统消息格式
chatStore.addMessage({
  id: `system-${Date.now()}`,  // 以 'system-' 开头
  role: 'system',
  content: '正在为您转接人工客服，请稍候...',
  timestamp: new Date(),
  sender: 'System'  // 必须为 'System'
})
```

**规则**:
1. **`role` 必须为 `'system'`**
2. **`id` 必须以 `'system-'` 开头**
3. **`sender` 必须为 `'System'`**
4. **`timestamp` 使用 `new Date()` 对象**
5. **`content` 使用用户友好的中文提示**

**验证代码位置**:
- `frontend/src/components/ChatPanel.vue:150-156` (转人工系统消息)
- `frontend/src/components/ChatPanel.vue:90-97` (分隔线系统消息)

**适用场景**:
- 转人工提示
- 会话分隔线
- 人工接入通知
- 人工结束通知
- 错误提示

---

### 约束11: 用户交互确认规范 ⭐ **P0-6 新增**

**发现日期**: 2025-11-21
**问题**: P0-6 转人工需要用户确认，避免误操作

**强制约束**:
```typescript
// ❌ 错误 - 重要操作无确认
const handleEscalateToManual = async () => {
  // 直接执行，用户可能误点击
  await chatStore.escalateToManual('manual')
}

// ✅ 正确 - 添加用户确认
const handleEscalateToManual = async () => {
  if (!confirm('确定要转接人工客服吗？')) {
    return  // 用户取消
  }
  await chatStore.escalateToManual('manual')
}
```

**规则**:
1. **重要操作（转人工、清空对话、删除数据）必须有用户确认**
2. **使用 `confirm()` 对话框**
3. **用户取消时立即返回，不执行操作**
4. **确认文案清晰明确，告知操作后果**

**验证代码位置**:
- `frontend/src/components/ChatPanel.vue:137-139` (转人工确认)
- `frontend/src/components/ChatPanel.vue:56-58` (新对话确认)

**需要确认的操作**:
- ✅ 转人工 (不可撤销)
- ✅ 新建对话 (清空界面)
- ❌ 清除对话分隔线 (不清空数据，无需确认)
- ❌ 发送消息 (常规操作，无需确认)

---

### 约束12: 计算属性依赖管理 ⭐ **P0-4 新增**

**发现日期**: 2025-11-21
**问题**: 前端引入多个计算属性，相互依赖关系需要明确管理

**强制约束**:
```typescript
// ❌ 错误 - 计算属性循环依赖
const canSendMessage = computed(() => {
  return canEscalate.value && !isLoading.value
})

const canEscalate = computed(() => {
  return canSendMessage.value && sessionStatus.value === 'bot_active'
})

// ✅ 正确 - 依赖基础状态，不相互依赖
const canSendMessage = computed(() => {
  return !isLoading.value &&
         sessionStatus.value !== 'pending_manual' &&
         sessionStatus.value !== 'closed'
})

const canEscalate = computed(() => {
  return sessionStatus.value === 'bot_active' && !isEscalating.value
})
```

**规则**:
1. **计算属性只依赖 ref 状态，不依赖其他计算属性**
2. **避免循环依赖**
3. **保持计算逻辑简单明确**
4. **必要时添加注释说明依赖关系**

**当前依赖图** (P0-4/P0-5/P0-6):
```
基础状态:
├─ sessionStatus (ref)
├─ isEscalating (ref)
├─ isLoading (ref)
├─ agentInfo (ref)
└─ escalationInfo (ref)

计算属性:
├─ isManualMode → sessionStatus
├─ canSendMessage → isLoading, sessionStatus
├─ canEscalate → sessionStatus, isEscalating
├─ statusText → sessionStatus, agentInfo
└─ statusColorClass → sessionStatus
```

**验证代码位置**: `frontend/src/stores/chatStore.ts:72-138`

---

---

## 🧪 会话隔离测试规范

### 约束13: 会话隔离的测试标准 ⭐ **必须遵守**

**核心原则**: 会话隔离以**打开新的前端网页**为判定依据，每个新打开的前端界面代表一个独立用户。

**测试场景定义**:

```
场景定义:
├─ 用户A: 浏览器窗口/标签页 #1
├─ 用户B: 浏览器窗口/标签页 #2
└─ 用户C: 浏览器窗口/标签页 #3 (可选)

判定标准:
- ✅ 每个新窗口/标签页 = 一个新的 session_id
- ✅ 每个 session_id 对应独立的 conversation_id
- ✅ 不同 session_id 之间的上下文完全隔离
```

**标准测试流程**:

```python
# 步骤1: 打开用户A的窗口
# 操作: 在浏览器中打开 http://localhost:5173
# 验证: 控制台显示 "✅ 会话初始化成功, Conversation ID: conv_A"

# 步骤2: 打开用户B的窗口
# 操作: 在新标签页/窗口打开 http://localhost:5173
# 验证: 控制台显示 "✅ 会话初始化成功, Conversation ID: conv_B"
# 验证: conv_B ≠ conv_A

# 步骤3: 用户A发送消息
# 操作: 在窗口A中输入 "我叫张三，今年25岁"
# 验证: AI 回复记住了用户A的信息

# 步骤4: 用户B发送消息
# 操作: 在窗口B中输入 "我叫李四，我是程序员"
# 验证: AI 回复记住了用户B的信息

# 步骤5: 验证用户A的隔离
# 操作: 在窗口A中输入 "我叫什么？我多大了？"
# 期望: AI 回答 "张三、25岁"
# 验证: ✅ 能正确回忆用户A的信息

# 步骤6: 验证用户B的隔离
# 操作: 在窗口B中输入 "我的名字和职业是什么？"
# 期望: AI 回答 "李四、程序员"
# 验证: ✅ 能正确回忆用户B的信息

# 步骤7: 关键验证 - 跨会话隔离
# 操作: 在窗口A中输入 "你知道李四是谁吗？"
# 期望: AI 回答 "不知道" 或 "没有相关信息"
# 验证: ✅ 用户A不应该知道用户B的信息（会话完全隔离）

# 步骤8: 关键验证 - 双向隔离
# 操作: 在窗口B中输入 "你知道张三吗？他多大了？"
# 期望: AI 回答 "不知道" 或 "没有相关信息"
# 验证: ✅ 用户B不应该知道用户A的信息（会话完全隔离）
```

**自动化测试实现** (参考 `tests/test_session_name.py`):

```python
def test_session_isolation():
    """测试会话隔离 - 遵循正确的Coze实现方式"""

    # 1. 模拟用户A打开页面 - 立即创建conversation
    response_A = requests.post(
        f"{BASE_URL}/api/conversation/new",
        json={"session_id": "session_A"}
    )
    conv_A = response_A.json()["conversation_id"]

    # 2. 模拟用户B打开页面 - 立即创建conversation
    response_B = requests.post(
        f"{BASE_URL}/api/conversation/new",
        json={"session_id": "session_B"}
    )
    conv_B = response_B.json()["conversation_id"]

    # 3. 验证 conversation_id 不同
    assert conv_A != conv_B, "Conversation ID 应该不同"

    # 4. 用户A发送信息
    requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": "我叫张三，今年25岁",
            "user_id": "session_A",
            "conversation_id": conv_A
        }
    )

    # 5. 用户B发送信息
    requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": "我叫李四，我是程序员",
            "user_id": "session_B",
            "conversation_id": conv_B
        }
    )

    # 6. 验证用户A记住自己的信息
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": "我叫什么？我多大了？",
            "user_id": "session_A",
            "conversation_id": conv_A
        }
    )
    assert "张三" in response.json()["message"]
    assert "25" in response.json()["message"]

    # 7. 关键验证 - 用户A不知道用户B的信息
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": "你知道李四是谁吗？",
            "user_id": "session_A",
            "conversation_id": conv_A
        }
    )
    # 应该不包含李四的信息
    assert "程序员" not in response.json()["message"]
```

**测试脚本位置**:
- `tests/test_session_name.py` - 完整的会话隔离测试
- `tests/test_simple.py` - 简化版测试

**验证要点**:
1. ✅ **前置条件**: 用户打开页面时立即调用 `/api/conversation/new`
2. ✅ **隔离验证**: 不同窗口的 conversation_id 必须不同
3. ✅ **上下文隔离**: 用户A不应该知道用户B的对话内容
4. ✅ **双向验证**: 用户B也不应该知道用户A的对话内容

**重要说明**:
- 🔴 **禁止**在首次对话时依赖 Coze 自动生成 conversation_id
- ✅ **必须**在页面加载时立即调用 `conversations.create()` API
- ✅ **必须**将返回的 conversation_id 保存并用于后续对话
- 📖 详细方案见: `Coze会话隔离最终解决方案.md`

**测试命令**:

```bash
# 运行会话隔离测试
cd /home/yzh/AI客服/鉴权
python3 tests/test_session_name.py

# 运行简化测试
python3 tests/test_simple.py
```

**测试位置**: `prd/CONSTRAINTS_AND_PRINCIPLES.md:975-1100`

---

## 🔧 环境要求

### 约束14: Python 运行环境 ⭐ **强制使用 python3**

**强制要求**: 本项目所有 Python 命令必须使用 `python3`，不使用 `python`。

**原因**: 开发环境中安装的是 `python3`，使用 `python` 可能指向 Python 2 或不存在。

**命令规范**:

```bash
# ✅ 正确 - 使用 python3
python3 backend.py
python3 tests/test_session_name.py
python3 -m pip install -r requirements.txt

# ❌ 错误 - 不使用 python
python backend.py
python tests/test_simple.py
```

**适用范围**:
- 启动后端服务
- 运行测试脚本
- 安装依赖包
- 任何 Python 相关命令

---

### 约束15: 历史回填实现规范 ⭐ **P1-2 新增**

**发现日期**: 2025-11-23
**来源模块**: P1-2 历史回填

**约束内容**:

用户端打开页面时必须加载历史消息，恢复完整的会话状态。

**实现要求**:

```typescript
// ✅ 正确 - 在 onMounted 中初始化后加载历史
onMounted(async () => {
  await initializeConversation()  // 先初始化 conversation_id
  await loadSessionHistory()       // 再加载历史消息
})

// loadSessionHistory 实现
const loadSessionHistory = async () => {
  const response = await fetch(`/api/sessions/${sessionId}`)

  if (response.status === 404) return  // 新会话无历史

  const data = await response.json()
  if (data.success && data.data.session) {
    // 1. 恢复会话状态
    chatStore.updateSessionStatus(session.status)

    // 2. 恢复升级信息
    if (session.escalation) {
      chatStore.setEscalationInfo(session.escalation)
    }

    // 3. 恢复坐席信息
    if (session.assigned_agent) {
      chatStore.setAgentInfo(session.assigned_agent)
    }

    // 4. 恢复历史消息（按时间排序，去重）
    sortedHistory.forEach(msg => {
      if (!exists) {
        chatStore.addMessage({...})
      }
    })

    // 5. 如果是人工模式，启动轮询
    if (status === 'pending_manual' || status === 'manual_live') {
      startStatusPolling()
    }
  }
}
```

**去重逻辑**:
```typescript
// ✅ 正确 - 基于时间戳和内容去重
const exists = chatStore.messages.some(
  m => Math.abs(m.timestamp.getTime() / 1000 - msg.timestamp) < 0.1 &&
       m.content === msg.content
)

// ❌ 错误 - 仅基于 ID 去重（可能不可靠）
const exists = chatStore.messages.some(m => m.id === msg.id)
```

**验证代码位置**:
- `frontend/src/components/ChatPanel.vue:404-504` (loadSessionHistory 函数)
- `frontend/src/components/ChatPanel.vue:507-521` (onMounted 调用)

---

### 约束16: 生产环境安全性与稳定性要求 ⭐ **强制执行**

**发现日期**: 2025-11-24
**适用范围**: 所有新功能开发、工具使用、环境配置

**核心原则**:

开发任何功能、使用任何工具、配置任何环境时，**必须考虑生产环境的安全性、稳定性及风险**。

#### 16.1 资源管理与限制

**问题场景**:
```
AI 客服系统在生产环境运行时：
- Redis 存储会话数据 → 存储量不断增加 → 最终占满磁盘或内存
- 日志文件持续写入 → 磁盘空间耗尽
- 数据库连接池未限制 → 连接数耗尽
- 内存泄漏 → 服务器崩溃
```

**强制要求**:

1. **存储限制**
```python
# ✅ 正确 - Redis 必须设置内存限制和过期策略
# redis.conf 配置
maxmemory 512mb                    # 设置最大内存
maxmemory-policy allkeys-lru       # 内存满时删除最少使用的key

# ✅ 正确 - 所有会话数据必须设置 TTL
redis.setex("session:abc123", 86400, json_data)  # 24小时过期

# ❌ 错误 - 未设置过期时间，数据永久保留
redis.set("session:abc123", json_data)
```

2. **日志管理**
```python
# ✅ 正确 - 使用日志轮转
logging.handlers.RotatingFileHandler(
    filename='app.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5           # 保留5个备份
)

# ❌ 错误 - 日志无限增长
logging.basicConfig(filename='app.log')
```

3. **数据库连接池**
```python
# ✅ 正确 - 限制连接数
redis_pool = redis.ConnectionPool(
    max_connections=50,     # 最大连接数
    socket_timeout=5,       # 超时设置
    socket_connect_timeout=5
)

# ❌ 错误 - 无限制创建连接
redis_client = redis.Redis(host='localhost')
```

#### 16.2 数据清理策略

**强制要求**:

1. **定期清理过期数据**
```python
# ✅ 正确 - 实现定时清理任务
async def cleanup_expired_sessions():
    """清理超过7天未活跃的会话"""
    threshold = time.time() - 7*24*3600

    for key in redis.scan_iter("session:*"):
        session = await get_session(key)
        if session.updated_at < threshold:
            redis.delete(key)

# 每天凌晨3点执行
schedule.every().day.at("03:00").do(cleanup_expired_sessions)
```

2. **监控存储使用量**
```python
# ✅ 正确 - 监控 Redis 内存使用
def check_redis_memory():
    info = redis.info('memory')
    used_memory_mb = info['used_memory'] / 1024 / 1024

    if used_memory_mb > 450:  # 超过450MB告警
        logger.warning(f"Redis memory high: {used_memory_mb}MB")
        send_alert("Redis内存使用率超过90%")
```

#### 16.3 错误处理与降级

**强制要求**:

1. **外部依赖失败不影响核心功能**
```python
# ✅ 正确 - Redis 不可用时降级到内存存储
try:
    session_store = RedisSessionStore(REDIS_URL)
    logger.info("✅ 使用 Redis 存储")
except Exception as e:
    logger.error(f"❌ Redis 连接失败: {e}")
    session_store = InMemorySessionStore()
    logger.warning("⚠️ 降级到内存存储（仅开发环境）")

# ❌ 错误 - Redis 失败导致服务无法启动
session_store = RedisSessionStore(REDIS_URL)  # 连接失败直接崩溃
```

2. **超时保护**
```python
# ✅ 正确 - 所有外部调用必须设置超时
response = await http_client.post(
    url,
    json=data,
    timeout=10.0  # 10秒超时
)

# ❌ 错误 - 无超时限制，可能永久阻塞
response = await http_client.post(url, json=data)
```

#### 16.4 安全性要求

**强制要求**:

1. **敏感信息保护**
```python
# ✅ 正确 - 日志脱敏
logger.info(f"用户登录: {user_id[:8]}***")

# ❌ 错误 - 记录完整敏感信息
logger.info(f"用户密码: {password}")
```

2. **环境变量隔离**
```bash
# ✅ 正确 - 生产环境使用环境变量
REDIS_PASSWORD=your_strong_password
REDIS_URL=redis://:${REDIS_PASSWORD}@prod-redis:6379/0

# ❌ 错误 - 硬编码密码
REDIS_URL=redis://:password123@localhost:6379/0
```

3. **输入验证**
```python
# ✅ 正确 - 验证和限制输入大小
if len(message) > 10000:  # 限制消息长度
    raise HTTPException(400, "消息过长")

# ❌ 错误 - 未限制输入，可能被攻击
redis.set(f"session:{user_input}", data)  # user_input 可能包含恶意内容
```

#### 16.5 监控与告警

**强制要求**:

1. **关键指标监控**
```python
# ✅ 正确 - 记录关键性能指标
@app.middleware("http")
async def log_request_time(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    if duration > 5.0:  # 超过5秒告警
        logger.warning(f"慢请求: {request.url.path} 耗时 {duration:.2f}s")

    return response
```

2. **健康检查端点**
```python
# ✅ 正确 - 实现完整的健康检查
@app.get("/api/health")
async def health_check():
    checks = {
        "redis": check_redis_connection(),
        "disk_space": check_disk_space(),
        "memory": check_memory_usage()
    }

    if all(checks.values()):
        return {"status": "healthy", "checks": checks}
    else:
        raise HTTPException(503, {"status": "unhealthy", "checks": checks})
```

#### 16.6 生产环境检查清单

**每个新功能开发完成后，必须验证**:

- [ ] 是否设置了资源限制（内存、磁盘、连接数）？
- [ ] 是否实现了数据过期和清理策略？
- [ ] 是否有错误降级方案？
- [ ] 是否设置了超时保护？
- [ ] 敏感信息是否已脱敏？
- [ ] 是否添加了监控和告警？
- [ ] 是否进行了压力测试？
- [ ] 是否编写了运维文档？

**验证方式**:

```bash
# 1. 压力测试 - 模拟1000个并发用户
ab -n 10000 -c 1000 http://localhost:8000/api/chat

# 2. 监控资源使用
watch -n 1 'redis-cli INFO memory | grep used_memory_human'
watch -n 1 'df -h | grep /var'

# 3. 检查日志大小
du -sh /var/log/app.log

# 4. 验证降级功能
# 停止 Redis，确认系统仍能正常启动（降级到内存存储）
```

---

**适用场景**:
- ✅ Redis 数据持久化 - 必须设置 maxmemory、TTL、清理策略
- ✅ 日志记录 - 必须使用日志轮转
- ✅ 文件上传 - 必须限制大小和类型
- ✅ 第三方 API 调用 - 必须设置超时和重试
- ✅ 数据库操作 - 必须使用连接池和索引
- ✅ 所有新功能 - 必须通过生产环境检查清单

**违反后果**:
- 🔴 生产环境磁盘/内存耗尽
- 🔴 服务崩溃或不可用
- 🔴 数据泄露或安全事故
- 🔴 无法诊断和恢复故障

---

**文档维护者**: Claude Code
**最后更新**: 2025-11-24
**文档版本**: v1.7 ⭐ 新增坐席认证系统约束 (约束17)
**审核状态**: ✅ 已完成
**验证状态**: ✅ 生产可用 (12/12 测试通过)

---

## 约束17: 坐席认证系统安全性约束 ⭐ 新增 (2025-11-24)

### 17.1 核心原则

坐席认证系统是独立于 Coze API 的本地认证模块，用于保护坐席工作台 API。

**设计原则**:
- ✅ 独立运行：不依赖 Coze API，使用本地 JWT
- ✅ 安全优先：bcrypt 密码加密 + JWT Token
- ✅ 零影响：不修改任何核心 AI 对话接口
- ✅ 可扩展：支持角色权限控制

### 17.2 密码安全约束

```python
# ✅ 正确 - 使用 bcrypt 加密
from bcrypt import hashpw, gensalt, checkpw

def hash_password(password: str) -> str:
    salt = gensalt()  # 自动加盐
    return hashpw(password.encode(), salt).decode()

def verify_password(password: str, hash: str) -> bool:
    return checkpw(password.encode(), hash.encode())

# ❌ 错误 - 明文存储或弱加密
password_hash = md5(password)  # MD5 不安全
password_hash = password       # 明文存储
```

**强制要求**:
- [ ] 密码必须使用 bcrypt 加密（自动加盐）
- [ ] 密码哈希永不返回给前端
- [ ] 生产环境必须修改默认密码
- [ ] 传输必须使用 HTTPS（生产环境）

### 17.3 JWT Token 约束

```python
# ✅ 正确 - JWT 配置
class AgentTokenManager:
    def __init__(
        self,
        secret_key: str,           # 必须从环境变量读取
        algorithm: str = "HS256",  # 使用 HS256 算法
        access_token_expire_minutes: int = 60,   # 1小时
        refresh_token_expire_days: int = 7       # 7天
    ):
        pass

# ❌ 错误 - 硬编码密钥
secret_key = "my_secret_key"  # 硬编码不安全！

# ✅ 正确 - 从环境变量读取
secret_key = os.getenv("JWT_SECRET_KEY")
```

**强制要求**:
- [ ] JWT 密钥必须从环境变量读取
- [ ] Access Token 有效期不超过 2 小时
- [ ] Refresh Token 有效期不超过 30 天
- [ ] 必须验证 Token 签名和过期时间
- [ ] 刷新 Token 必须标记 type=refresh

### 17.4 API 安全约束

```python
# ✅ 正确 - 返回时移除密码
def agent_to_dict(agent: Agent) -> Dict:
    data = agent.dict()
    data.pop("password_hash", None)  # 移除密码
    return data

# ❌ 错误 - 返回完整对象
return agent.dict()  # 包含 password_hash!
```

**强制要求**:
- [ ] 登录失败返回 401，不暴露用户是否存在
- [ ] 获取信息必须移除 password_hash
- [ ] 使用 Pydantic 模型验证输入
- [ ] 所有敏感操作记录审计日志

### 17.5 存储约束

```python
# ✅ 正确 - Redis 存储坐席账号
class AgentManager:
    def __init__(self, redis_store):
        self.redis = redis_store.redis
        self.key_prefix = "agent:"

    def create_agent(self, ...):
        key = f"{self.key_prefix}{username}"
        self.redis.set(key, agent.json(), ex=86400 * 365)  # 1年过期
```

**强制要求**:
- [ ] 坐席数据存储在 Redis（与会话数据分开前缀）
- [ ] 设置合理的过期时间（建议 1 年）
- [ ] 用户名作为唯一标识（防止重复）
- [ ] 支持状态更新（在线/离线/忙碌）

### 17.6 默认账号约束

**默认账号列表**:
| 用户名 | 角色 | 用途 |
|-------|------|------|
| admin | admin | 系统管理 |
| agent001 | agent | 测试坐席1 |
| agent002 | agent | 测试坐席2 |

**强制要求**:
- [ ] ⚠️ 生产环境必须修改默认密码
- [ ] 启动时检查账号是否存在，避免重复创建
- [ ] 默认账号仅用于开发测试
- [ ] 建议生产环境删除或禁用默认账号

### 17.7 生产环境检查清单

每次部署前必须验证:

- [ ] JWT_SECRET_KEY 是否已设置（至少 32 字符强随机密钥）？
- [ ] 默认密码是否已修改？
- [ ] HTTPS 是否已启用？
- [ ] 密码策略是否满足要求（长度、复杂度）？
- [ ] Token 过期时间是否合理？
- [ ] 是否有登录失败次数限制？（建议实现）
- [ ] 是否有审计日志？（建议实现）

### 17.8 API 接口规范

**坐席认证相关接口**:

| 端点 | 方法 | 功能 | 是否需要鉴权 |
|------|------|------|-------------|
| `/api/agent/login` | POST | 坐席登录 | 否 |
| `/api/agent/logout` | POST | 坐席登出 | 否 |
| `/api/agent/profile` | GET | 获取坐席信息 | 否（后续改为是） |
| `/api/agent/refresh` | POST | 刷新 Token | 否 |

**请求/响应格式**:

```json
// POST /api/agent/login
// Request:
{
  "username": "admin",
  "password": "admin123"
}

// Response (200):
{
  "success": true,
  "token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "expires_in": 3600,
  "agent": {
    "id": "agent_xxx",
    "username": "admin",
    "name": "系统管理员",
    "role": "admin",
    "status": "online"
  }
}

// Response (401):
{
  "detail": "用户名或密码错误"
}
```

---

**适用场景**:
- ✅ 坐席登录功能
- ✅ 坐席工作台 API 保护
- ✅ 角色权限控制
- ✅ Token 刷新机制

**违反后果**:
- 🔴 密码泄露
- 🔴 未授权访问坐席工作台
- 🔴 会话劫持
- 🔴 权限提升攻击

---

## 约束18: 坐席工作台 SSE 实时推送 ⭐ 新增 (v2.3.8+)

**约束编号**: 18
**约束类型**: 🟡 强烈推荐
**适用模块**: 前端 - 坐席工作台
**实施时间**: v2.3.8
**文档状态**: ✅ 已完成实施

### 18.1 技术选型约束

**强制要求 - 混合策略**:
```typescript
// ✅ 正确 - 轻量级轮询(30s) + SSE实时推送
const startMonitoring = async () => {
  // 1. 初始加载
  await sessionStore.fetchSessions()
  await sessionStore.fetchStats()

  // 2. 轻量级轮询 - 30秒刷新会话列表
  //   （比5秒轮询节省83%资源）
  pollTimer.value = window.setInterval(async () => {
    await sessionStore.fetchSessions()
    await sessionStore.fetchStats()
  }, 30000) // 30秒

  // 3. SSE连接 - 监听当前选中的会话
  if (sessionStore.selectedSession) {
    monitorCurrentSession() // 建立SSE连接
  }
}

// ❌ 错误 - 短轮询浪费资源
setInterval(refreshData, 5000)  // 5秒轮询

// ❌ 错误 - 纯SSE无法检测新会话
// 只用SSE不轮询会导致新会话无法及时发现
```

**原因**:
1. EventSource 只支持 GET 请求,但 `/api/chat/stream` 是 POST
2. 不可修改后端核心逻辑(约束1)
3. 需要检测新会话出现(轮询) + 实时消息推送(SSE)

### 18.2 FetchSSE 实现约束

**强制要求 - 必须使用 Fetch API + ReadableStream**:

```typescript
// ✅ 正确 - 支持POST的SSE实现
class FetchSSE {
  private controller: AbortController | null = null
  private reader: ReadableStreamDefaultReader<Uint8Array> | null = null

  async connect() {
    this.controller = new AbortController()

    const response = await fetch(this.url, {
      method: 'POST',  // 支持POST请求
      headers: { 'Content-Type': 'application/json' },
      body: this.options.body,
      signal: this.controller.signal
    })

    this.reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await this.reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // 解析SSE消息格式: data: {...}\n\n
      const lines = buffer.split('\n\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.substring(6))
          this.options.onMessage?.(data)
        }
      }
    }
  }
}

// ❌ 错误 - EventSource 不支持POST
const eventSource = new EventSource('/api/chat/stream')  // 只能GET
```

### 18.3 自动切换SSE连接约束

**强制要求 - 监听选中会话变化**:

```typescript
// ✅ 正确 - watch自动切换SSE连接
watch(
  () => sessionStore.selectedSession,
  (newSession, oldSession) => {
    if (!isMonitoring.value) return

    if (newSession?.session_name !== oldSession?.session_name) {
      console.log(`🔄 切换监听会话: ${oldSession?.session_name} -> ${newSession?.session_name}`)

      // 关闭旧连接
      if (currentSessionSSE.value) {
        currentSessionSSE.value.disconnect()
      }

      // 建立新连接
      monitorCurrentSession()
    }
  }
)

// ❌ 错误 - 不切换导致监听错误会话
// 用户选择新会话后仍监听旧会话的消息
```

### 18.4 SSE事件类型约束

**强制支持的事件类型**:

| 事件类型 | 触发时机 | 前端行为 |
|---------|---------|----------|
| `status_change` | 会话状态变化 | 刷新会话列表和详情 |
| `manual_message` | 人工消息到达 | 刷新会话详情 |
| `message` | AI消息(忽略) | 无操作 |
| `done` | 完成标记 | 无操作 |
| `error` | 错误事件 | 打印错误日志 |

**实现示例**:
```typescript
onMessage: (data) => {
  console.log(`📨 收到 SSE 消息:`, data.type)

  switch (data.type) {
    case 'status_change':
      // 状态变化：刷新会话列表和详情
      sessionStore.fetchSessions()
      sessionStore.fetchStats()
      if (sessionName === sessionStore.selectedSession?.session_name) {
        sessionStore.fetchSessionDetail(sessionName)
      }
      break

    case 'manual_message':
      // 人工消息：刷新会话详情
      if (sessionName === sessionStore.selectedSession?.session_name) {
        sessionStore.fetchSessionDetail(sessionName)
      }
      break

    case 'message':
      // AI 消息（坐席工作台不关心）
      break

    case 'done':
      // 完成标记
      break

    case 'error':
      console.error(`❌ SSE 错误: ${data.content}`)
      break

    default:
      console.log(`ℹ️  未知事件: ${data.type}`)
  }
}
```

### 18.5 自动重连约束

**强制要求 - 3秒重连间隔**:

```typescript
// ✅ 正确 - 错误后自动重连
onError: (error) => {
  console.error(`❌ SSE 连接失败:`, error)

  // 3秒后尝试重连
  setTimeout(() => {
    if (isMonitoring.value &&
        sessionStore.selectedSession?.session_name === sessionName) {
      monitorCurrentSession()  // 重新建立连接
    }
  }, 3000)
}

// ❌ 错误 - 不重连导致永久断开
onError: (error) => {
  console.error(`❌ SSE 连接失败:`, error)
  // 什么都不做,连接永久断开
}
```

### 18.6 资源管理约束

**强制要求 - 组件卸载时清理资源**:

```typescript
// ✅ 正确 - 完整清理
const stopMonitoring = () => {
  console.log('⏹️  停止实时监听')
  isMonitoring.value = false

  // 清除轮询定时器
  if (pollTimer.value) {
    clearInterval(pollTimer.value)
    pollTimer.value = null
  }

  // 关闭 SSE 连接
  if (currentSessionSSE.value) {
    currentSessionSSE.value.disconnect()
    currentSessionSSE.value = null
  }
}

onUnmounted(() => {
  stopMonitoring()
})

// ❌ 错误 - 内存泄漏
onUnmounted(() => {
  // 忘记清理定时器和SSE连接
})
```

### 18.7 性能优化约束

**强制要求 - 轮询间隔不得低于30秒**:

```typescript
// ✅ 正确 - 30秒轮询
pollTimer.value = window.setInterval(async () => {
  console.log('🔄 轮询刷新会话列表 (30s)')
  await sessionStore.fetchSessions()
  await sessionStore.fetchStats()
}, 30000)

// ❌ 错误 - 5秒轮询浪费资源
setInterval(refreshData, 5000)  // 比30秒多6倍请求

// 性能对比:
// - 5秒轮询: 12次/分钟 = 720次/小时
// - 30秒轮询: 2次/分钟 = 120次/小时
// - 节省: 83% 网络请求
```

### 18.8 生产环境检查清单

每次部署前必须验证:

- [ ] SSE连接是否支持POST请求？
- [ ] 是否监听了选中会话变化并自动切换SSE？
- [ ] 是否处理了所有SSE事件类型(status_change, manual_message)?
- [ ] 是否实现了3秒自动重连？
- [ ] 是否在组件卸载时清理了定时器和SSE连接？
- [ ] 轮询间隔是否 >= 30秒？
- [ ] 是否同时使用轮询(检测新会话) + SSE(实时消息)?

### 18.9 文件清单

**实施文件**:
- `/home/yzh/AI客服/鉴权/agent-workbench/src/composables/useAgentWorkbenchSSE.ts` (核心实现)
- `/home/yzh/AI客服/鉴权/agent-workbench/src/views/Dashboard.vue` (集成使用)

**测试文件**:
- (待补充) E2E测试验证SSE实时推送

---

**适用场景**:
- ✅ 坐席工作台实时会话列表更新
- ✅ 实时接收新消息通知
- ✅ 状态变化实时推送
- ✅ 企业生产环境并发要求

**违反后果**:
- 🟡 资源浪费(短轮询)
- 🟡 实时性差(轮询延迟)
- 🟡 内存泄漏(未清理资源)

---

## 约束19: 字段级访问控制 ⭐ 新增 (v3.1.3)

**约束编号**: 19
**约束类型**: 🔴 强制要求
**适用模块**: 后端 - 坐席认证系统
**实施时间**: v3.1.3
**文档状态**: ✅ 已完成实施

### 19.1 核心约束：坐席只能修改非敏感字段

**强制要求**：

坐席用户只能修改自己的 `name` 和 `avatar_url`，禁止修改敏感字段。

```python
# ✅ 正确 - 只允许修改非敏感字段
class UpdateProfileRequest(BaseModel):
    """修改个人资料请求 - 只允许修改非敏感字段"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    avatar_url: Optional[str] = None

@app.put("/api/agent/profile")
async def update_profile(
    request: UpdateProfileRequest,
    agent: Dict = Depends(require_agent)  # 任何登录用户都可以
):
    # 只更新允许的字段
    if request.name is not None:
        current_agent.name = request.name
    if request.avatar_url is not None:
        current_agent.avatar_url = request.avatar_url

    agent_manager.update_agent(current_agent)

# ❌ 错误 - 允许修改任意字段（权限提升漏洞！）
@app.put("/api/agent/profile")
async def update_profile(request: dict):
    for key, value in request.items():
        setattr(agent, key, value)  # 可能修改 role="admin"！
```

**禁止修改的敏感字段**：
- `role` - 角色（admin/agent）⚠️ 最危险，可能导致权限提升
- `username` - 用户名（唯一标识符）
- `max_sessions` - 最大会话数（业务限制）
- `status` - 坐席状态（业务状态机）
- `created_at` - 创建时间（审计字段）
- `last_login` - 最后登录时间（审计字段）
- `password_hash` - 密码哈希（安全字段）

### 19.2 验证规则

**必须实现的验证**：

1. **至少提供一个字段**
```python
if request.name is None and request.avatar_url is None:
    raise HTTPException(400, "NO_FIELDS_TO_UPDATE: 至少需要提供一个要修改的字段")
```

2. **字段长度验证**
```python
name: Optional[str] = Field(None, min_length=1, max_length=50)  # 1-50字符
```

3. **返回时脱敏**
```python
agent_dict = current_agent.dict()
agent_dict.pop("password_hash", None)  # 永不返回密码
return {"success": True, "agent": agent_dict}
```

### 19.3 API 接口规范

**接口**: `PUT /api/agent/profile`
**权限**: `require_agent()` - 任何登录用户
**请求体**:
```json
{
  "name": "新姓名",              // 可选，1-50字符
  "avatar_url": "/avatars/new.png"  // 可选
}
```

**响应**:
```json
{
  "success": true,
  "agent": {
    "id": "agent_123",
    "username": "agent001",  // 不可修改
    "name": "新姓名",       // ← 已更新
    "role": "agent",        // 不可修改
    "status": "online",     // 不可修改
    "max_sessions": 5,      // 不可修改
    "avatar_url": "/avatars/new.png"  // ← 已更新
  }
}
```

### 19.4 安全检查清单

**实施前检查**：
- [ ] UpdateProfileRequest 是否只包含 name 和 avatar_url？
- [ ] 是否禁止了动态字段赋值（避免 `setattr()`）？
- [ ] 是否验证了至少提供一个字段？
- [ ] 返回时是否移除了 password_hash？

**测试验证**：
- [ ] 尝试修改 role 字段是否被拒绝？
- [ ] 尝试修改 username 字段是否被拒绝？
- [ ] 尝试修改 max_sessions 字段是否被拒绝？
- [ ] 空请求是否返回 400？

### 19.5 典型攻击场景

**场景1: 权限提升攻击**
```python
# 攻击者尝试修改自己的角色为管理员
PUT /api/agent/profile
{
  "role": "admin",  // 试图提升权限
  "max_sessions": 999
}

# ✅ 正确实现：请求被忽略，只更新 name 和 avatar_url（没有这两个字段则返回400）
# ❌ 错误实现：攻击者成功成为管理员
```

**场景2: 修改其他用户账号**
```python
# ✅ 正确：通过 JWT 验证，只能修改自己的账号
agent = Depends(require_agent)  # 从 Token 获取当前用户
current_agent = agent_manager.get_agent_by_username(agent.get("username"))

# ❌ 错误：允许通过参数指定用户名
@app.put("/api/agent/profile/{username}")  # 危险！
```

### 19.6 相关文档

- `prd/03_技术方案/api_contract.md` - API 接口规范（第6节）
- `prd/04_任务拆解/admin_management_tasks.md` - ADMIN-08 任务详情
- `CLAUDE.md` - 约束19 详细说明

**违反后果**:
- 🔴 权限提升漏洞（用户可自行成为管理员）
- 🔴 业务逻辑破坏（修改 max_sessions、status）
- 🔴 审计日志失效（修改 created_at、last_login）

---

## 约束20: 密码修改安全性 ⭐ 新增 (v3.1.2)

**约束编号**: 20
**约束类型**: 🔴 强制要求
**适用模块**: 后端 - 坐席认证系统
**实施时间**: v3.1.2
**文档状态**: ✅ 已完成实施

### 20.1 三重验证机制

**强制要求**：修改密码必须通过三重验证

```python
# ✅ 正确 - 完整的三重验证
@app.post("/api/agent/change-password")
async def change_password(
    request: ChangePasswordRequest,
    agent: Dict = Depends(require_agent)
):
    current_agent = agent_manager.get_agent_by_username(agent.get("username"))

    # 验证1: 旧密码必须正确
    if not PasswordHasher.verify_password(request.old_password, current_agent.password_hash):
        raise HTTPException(400, "OLD_PASSWORD_INCORRECT: 旧密码不正确")

    # 验证2: 新密码强度要求（至少8字符，包含字母和数字）
    if not validate_password(request.new_password):
        raise HTTPException(400, "INVALID_PASSWORD: 密码必须至少8个字符，包含字母和数字")

    # 验证3: 新密码不能与旧密码相同
    if PasswordHasher.verify_password(request.new_password, current_agent.password_hash):
        raise HTTPException(400, "PASSWORD_SAME: 新密码不能与旧密码相同")

    # 通过所有验证后才更新
    current_agent.password_hash = PasswordHasher.hash_password(request.new_password)
    agent_manager.update_agent(current_agent)

# ❌ 错误 - 缺少验证
@app.post("/api/agent/change-password")
async def change_password(request: dict):
    agent.password_hash = bcrypt.hash(request["new_password"])  # 不验证旧密码！
```

### 20.2 密码强度要求

**强制规则**：

```python
def validate_password(password: str) -> bool:
    """
    密码强度验证

    要求:
    - 最少 8 个字符
    - 必须包含字母
    - 必须包含数字
    """
    if len(password) < 8:
        return False

    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)

    return has_letter and has_digit

# ✅ 正确示例
"agent123"     # 通过 - 8字符，含字母和数字
"password1"    # 通过 - 9字符，含字母和数字

# ❌ 错误示例
"pass"         # 拒绝 - 少于8字符
"12345678"     # 拒绝 - 只有数字
"abcdefgh"     # 拒绝 - 只有字母
```

### 20.3 安全注意事项

**1. 错误信息不泄露细节**
```python
# ✅ 正确 - 统一错误信息
raise HTTPException(400, "OLD_PASSWORD_INCORRECT: 旧密码不正确")

# ❌ 错误 - 泄露用户名是否存在
if not user:
    raise HTTPException(404, "用户不存在")
if not verify_password(...):
    raise HTTPException(400, "密码错误")
```

**2. Token 生命周期**
```python
# ⚠️ 注意：修改密码后，旧的 JWT Token 仍然有效（直到过期）
# 原因：JWT 是无状态的，无法主动失效
# 建议：提示用户重新登录以获取新 Token

# 未来改进：实现 Token 黑名单机制
```

**3. 密码历史记录（可选）**
```python
# 未来可扩展：记录最近3次密码，禁止重复使用
password_history: List[str] = []  # 存储最近3次密码哈希
```

### 20.4 API 接口规范

**接口**: `POST /api/agent/change-password`
**权限**: `require_agent()` - 任何登录用户
**请求体**:
```json
{
  "old_password": "agent123",
  "new_password": "newpass123"
}
```

**响应**:
```json
{
  "success": true,
  "message": "密码修改成功"
}
```

**错误响应**:
```json
{"detail": "OLD_PASSWORD_INCORRECT: 旧密码不正确"}
{"detail": "INVALID_PASSWORD: 密码必须至少8个字符，包含字母和数字"}
{"detail": "PASSWORD_SAME: 新密码不能与旧密码相同"}
```

### 20.5 安全检查清单

**实施前检查**：
- [ ] 是否验证旧密码正确性？
- [ ] 是否验证新密码强度（8字符+字母+数字）？
- [ ] 是否禁止新旧密码相同？
- [ ] 是否使用 bcrypt 加密？
- [ ] 错误信息是否统一（不泄露细节）？

**测试验证**：
- [ ] 旧密码错误是否被拒绝（400）？
- [ ] 弱密码是否被拒绝（400/422）？
- [ ] 新旧密码相同是否被拒绝（400）？
- [ ] 修改成功后能否用新密码登录？

### 20.6 相关文档

- `prd/03_技术方案/api_contract.md` - API 接口规范（第5节）
- `prd/04_任务拆解/admin_management_tasks.md` - ADMIN-07 任务详情
- `CLAUDE.md` - 约束20 详细说明

**违反后果**:
- 🔴 账号被盗（不验证旧密码）
- 🔴 弱密码攻击（不验证密码强度）
- 🔴 用户体验差（新旧密码相同无提示）

---

## 约束21: JWT 权限分级 ⭐ 新增 (v3.1.1)

**约束编号**: 21
**约束类型**: 🔴 强制要求
**适用模块**: 后端 - 权限控制
**实施时间**: v3.1.1
**文档状态**: ✅ 已完成实施

### 21.1 三级权限模型

**强制要求**：系统必须严格区分三级权限

| 权限级别 | 适用对象 | 中间件 | 典型API |
|---------|---------|-------|---------|
| **无需认证** | 用户端前端 | 无 | `/api/chat`, `/api/manual/escalate` |
| **坐席权限** | 任何登录坐席 | `require_agent()` | 修改密码、修改资料、会话查询 |
| **管理员权限** | 管理员 | `require_admin()` | 坐席CRUD、密码重置、权限管理 |

```python
# ✅ 正确 - 三级权限清晰分离

# 1. 无需认证 - 用户端 API
@app.post("/api/chat")
async def chat(request: ChatRequest):
    """用户聊天，无需登录"""
    pass

# 2. 坐席权限 - 任何登录用户（管理员+普通坐席）
@app.post("/api/agent/change-password")
async def change_password(agent: Dict = Depends(require_agent)):
    """坐席修改自己的密码"""
    pass

# 3. 管理员权限 - 仅管理员
@app.get("/api/agents")
async def get_agents(admin: Dict = Depends(require_admin)):
    """管理员查看坐席列表"""
    pass

# ❌ 错误 - 混用权限
@app.get("/api/agents")
async def get_agents(agent: Dict = Depends(require_agent)):  # 应该用 require_admin!
    # 普通坐席可以查看所有坐席列表 - 权限泄露！
    pass
```

### 21.2 JWT 中间件实现

**核心中间件**：

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_agent_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """验证 JWT Token（基础验证）"""
    token = credentials.credentials

    payload = agent_token_manager.verify_token(token)
    if not payload:
        raise HTTPException(401, detail="Token 无效或已过期")

    return payload

async def require_agent(
    agent: Dict = Depends(verify_agent_token)
) -> Dict[str, Any]:
    """要求坐席权限（管理员和普通坐席都可访问）"""
    return agent

async def require_admin(
    agent: Dict = Depends(verify_agent_token)
) -> Dict[str, Any]:
    """要求管理员权限（只有管理员可访问）"""
    if agent.get("role") != "admin":
        raise HTTPException(403, detail="需要管理员权限")
    return agent
```

### 21.3 权限检查流程

**请求处理流程**：

```
1. 用户发送请求 + Authorization Header
   ↓
2. security = HTTPBearer() 提取 Token
   ↓
3. verify_agent_token() 验证 Token 有效性
   - 无效/过期 → 401 Unauthorized
   ↓
4. require_agent() 或 require_admin() 检查角色
   - require_admin(): role != "admin" → 403 Forbidden
   - require_agent(): 任何登录用户都通过
   ↓
5. 执行业务逻辑
```

### 21.4 错误状态码规范

**强制要求**：

| 状态码 | 含义 | 触发条件 | 示例 |
|-------|------|---------|------|
| **401 Unauthorized** | 认证失败 | Token无效、过期、缺失 | `"Token 无效或已过期"` |
| **403 Forbidden** | 权限不足 | Token有效但角色不符 | `"需要管理员权限"` |

```python
# ✅ 正确 - 明确区分 401 和 403
if not payload:
    raise HTTPException(401, "Token 无效或已过期")  # 认证问题

if agent.get("role") != "admin":
    raise HTTPException(403, "需要管理员权限")  # 权限问题

# ❌ 错误 - 混淆 401 和 403
if agent.get("role") != "admin":
    raise HTTPException(401, "未授权")  # 应该用 403!
```

### 21.5 Token 生命周期

**生产环境配置**：

```python
# JWT Token 配置
ACCESS_TOKEN_EXPIRE_MINUTES = 60   # 1小时
REFRESH_TOKEN_EXPIRE_DAYS = 7      # 7天

# Token 内容
{
  "agent_id": "agent_123",
  "username": "admin",
  "role": "admin",           # ← 权限判断依据
  "iat": 1763973937,         # 签发时间
  "exp": 1763977537,         # 过期时间
  "type": "access"           # Token 类型
}
```

**Token 刷新流程**：
```python
# 1. Access Token 过期 → 返回 401
# 2. 前端使用 Refresh Token 请求新的 Access Token
POST /api/agent/refresh
{
  "refresh_token": "eyJ..."
}

# 3. 服务器验证 Refresh Token，返回新的 Access Token
{
  "success": true,
  "token": "eyJ...",  # 新的 Access Token
  "expires_in": 3600
}
```

### 21.6 API 权限分配表

**完整权限分配**：

| API 端点 | 权限要求 | 中间件 | 说明 |
|---------|---------|-------|------|
| **用户端 API** | | | |
| `POST /api/chat` | 无 | - | AI对话 |
| `POST /api/chat/stream` | 无 | - | 流式对话 |
| `POST /api/manual/escalate` | 无 | - | 用户请求人工 |
| `POST /api/manual/messages` (role=user) | 无 | - | 用户发消息 |
| **坐席工作台 API** | | | |
| `GET /api/sessions` | 坐席 | require_agent | 会话列表 |
| `GET /api/sessions/{id}` | 坐席 | require_agent | 会话详情 |
| `POST /api/sessions/{id}/takeover` | 坐席 | require_agent | 接入会话 |
| `POST /api/manual/messages` (role=agent) | 坐席 | require_agent | 坐席发消息 |
| `POST /api/sessions/{id}/release` | 坐席 | require_agent | 释放会话 |
| **坐席自助 API** | | | |
| `POST /api/agent/change-password` | 坐席 | require_agent | 修改密码 |
| `PUT /api/agent/profile` | 坐席 | require_agent | 修改资料 |
| **管理员 API** | | | |
| `GET /api/agents` | 管理员 | require_admin | 坐席列表 |
| `POST /api/agents` | 管理员 | require_admin | 创建坐席 |
| `PUT /api/agents/{username}` | 管理员 | require_admin | 修改坐席 |
| `DELETE /api/agents/{username}` | 管理员 | require_admin | 删除坐席 |
| `POST /api/agents/{username}/reset-password` | 管理员 | require_admin | 重置密码 |

### 21.7 安全检查清单

**实施前检查**：
- [ ] 所有管理员 API 是否使用 `require_admin()`？
- [ ] 所有坐席工作台 API 是否使用 `require_agent()`？
- [ ] 用户端 API 是否无需认证？
- [ ] Token 过期时间是否合理（Access: 1h, Refresh: 7d）？
- [ ] 401 和 403 错误是否正确区分？

**测试验证**：
- [ ] 无 Token 访问坐席 API 是否返回 401？
- [ ] 普通坐席访问管理员 API 是否返回 403？
- [ ] 管理员访问坐席 API 是否成功？
- [ ] Token 过期后是否返回 401？
- [ ] Refresh Token 是否能正确刷新？

### 21.8 典型攻击场景

**场景1: 权限混淆攻击**
```python
# 攻击者使用普通坐席Token访问管理员API
GET /api/agents
Authorization: Bearer <agent_token>  # role: "agent"

# ✅ 正确实现：返回 403 Forbidden
# ❌ 错误实现：返回坐席列表（权限泄露）
```

**场景2: Token 伪造攻击**
```python
# 攻击者尝试伪造 Token，修改 role 为 admin
{
  "agent_id": "agent_001",
  "role": "admin",  // 伪造
  "exp": 9999999999
}

# ✅ 正确实现：JWT 签名验证失败 → 401
# ❌ 错误实现：不验证签名，直接信任 Token
```

### 21.9 相关文档

- `prd/03_技术方案/api_contract.md` - JWT 权限中间件文档
- `prd/04_任务拆解/admin_management_tasks.md` - 权限控制任务
- `CLAUDE.md` - 约束21 详细说明

**违反后果**:
- 🔴 权限泄露（普通坐席访问管理员功能）
- 🔴 账号接管（Token 伪造）
- 🔴 审计失效（无法追溯操作者）

---
- 🟡 SSE连接断开后无法恢复(未重连)

---

## 约束22: 企业级功能开发原则 ⭐ **新增 v3.5+** (2025-11-26)

**适用范围**: 所有基于拼多多、聚水潭等企业级系统参考设计的功能

**核心原则**:
- ✅ 功能实用性优先，避免过度设计
- ✅ 渐进式开发，按P0→P1→P2→P3优先级递进
- ✅ 每个功能必须有明确的业务价值
- ✅ 保持系统简洁，避免功能堆砌

---

### 22.1 功能优先级定义

**P0 (紧急且重要)**: 立即实施，3-5天
- 严重影响用户体验或业务运转
- 示例：快捷回复、自动回复、智能提醒

**P1 (重要且常用)**: 短期实施，1-2周
- 显著提升效率，用户强需求
- 示例：会话标签、商品卡片、知识库

**P2 (重要但不紧急)**: 中期实施，1-2月
- 锦上添花，提升体验
- 示例：绩效报表、工单模板、多店铺管理

**P3 (锦上添花)**: 长期规划，2-6月
- 创新功能，差异化竞争
- 示例：智能路由、AI推荐、行为分析

---

### 22.2 参考系统使用原则

**强制要求**:
- ✅ 参考拼多多、聚水潭的**设计理念和交互逻辑**
- ✅ 根据Fiido业务场景**裁剪和适配**功能
- ❌ **禁止**盲目照搬，必须评估业务价值
- ❌ **禁止**为了功能而功能，避免臃肿

**评估标准**:
```
1. 业务匹配度: 该功能是否适合跨境电商独立站？
2. 使用频率: 坐席每天会用几次？
3. 实现成本: 开发时间 vs 收益比
4. 维护成本: 是否会增加系统复杂度？
```

**示例**:
```
✅ 采纳: 快捷回复（高频使用，实现简单）
✅ 采纳: 会话标签（提升效率，易维护）
❌ 暂缓: 智能路由（需求不明确，实现复杂）
❌ 暂缓: 行为数据分析（初期用户少，投入产出比低）
```

---

### 22.3 功能开发流程

**Step 1: 需求评审**
```
1. 明确业务场景（举具体例子）
2. 评估优先级（P0/P1/P2/P3）
3. 估算开发时间
4. 确认验收标准
```

**Step 2: 技术设计**
```
1. 数据模型设计
2. API接口设计
3. UI/UX原型
4. 性能预估
```

**Step 3: 开发实施**
```
1. 后端API开发
2. 前端UI开发
3. 单元测试
4. 集成测试
```

**Step 4: 验收上线**
```
1. 功能测试（验收标准）
2. 回归测试（不破坏现有功能）
3. 性能测试（并发、响应时间）
4. 文档更新
```

---

### 22.4 数据一致性约束

**强制要求**:
- ✅ 所有新功能数据必须支持持久化（Redis/PostgreSQL）
- ✅ 支持数据导入/导出（GDPR合规）
- ✅ 支持数据备份/恢复
- ❌ **禁止**仅内存存储（重启丢失数据）

**数据模型设计原则**:
```python
# ✅ 正确 - 清晰的数据模型
class QuickReply(BaseModel):
    id: str
    category: str
    title: str
    content: str
    variables: List[str]
    created_by: str
    created_at: float
    usage_count: int = 0

# ❌ 错误 - 字段过于模糊
class QuickReply(BaseModel):
    data: dict  # 字段不明确
    config: str  # 难以维护
```

---

### 22.5 UI/UX一致性约束

**设计系统强制遵循**:
- ✅ 使用统一的设计系统 (`design-system.scss`)
- ✅ 颜色、字体、间距、圆角统一
- ✅ 交互模式统一（悬停、点击、加载）
- ❌ **禁止**每个功能使用不同的设计风格

**示例**:
```scss
// ✅ 正确 - 使用设计系统变量
.quick-reply-btn {
  padding: $spacing-2 $spacing-4;
  background: $brand-primary;
  border-radius: $radius-md;
  transition: all $transition-base;
}

// ❌ 错误 - 硬编码样式
.quick-reply-btn {
  padding: 8px 16px;      // 应该用 $spacing-2 $spacing-4
  background: #2563EB;    // 应该用 $brand-primary
  border-radius: 8px;     // 应该用 $radius-md
}
```

---

### 22.6 性能约束

**并发性要求**:
- ✅ 支持100+并发用户
- ✅ API响应时间 P99 < 1s
- ✅ SSE连接稳定（支持10,000+连接）
- ✅ 前端列表虚拟滚动（>100条数据）

**资源限制**:
- ✅ Redis连接池：50连接
- ✅ HTTP连接池：100连接
- ✅ SSE队列长度：100条/会话
- ✅ 单文件上传：10MB
- ✅ 图片上传：5MB

---

### 22.7 安全约束

**权限控制**:
- ✅ 所有新功能API必须使用JWT认证
- ✅ 敏感操作需要管理员权限（如配置快捷回复模板）
- ✅ 数据访问遵循最小权限原则
- ❌ **禁止**未认证访问敏感数据

**数据脱敏**:
```python
# ✅ 正确 - 记录日志时脱敏
logger.info(f"客户{customer_id[:8]}***发起咨询")

# ❌ 错误 - 记录完整敏感信息
logger.info(f"客户{customer_email}发起咨询")
```

---

### 22.8 国际化约束

**适配跨境电商场景**:
- ✅ 界面多语言支持（中、英、德、法、西）
- ✅ 时区自动转换（显示客户当地时间）
- ✅ 货币自动转换（EUR、USD、GBP）
- ✅ 日期格式本地化（2025-11-26 vs 11/26/2025）

**示例**:
```typescript
// ✅ 正确 - 使用i18n
<span>{{ $t('quickReply.welcome') }}</span>

// ❌ 错误 - 硬编码中文
<span>欢迎语</span>
```

---

### 22.9 监控与日志

**强制要求**:
- ✅ 所有新功能操作记录日志
- ✅ 关键操作记录审计日志（谁、何时、做了什么）
- ✅ 性能指标监控（响应时间、错误率）
- ✅ 异常告警（错误率>5%立即告警）

**日志格式**:
```python
# ✅ 正确 - 结构化日志
logger.info(
    "quick_reply_used",
    extra={
        "agent_id": agent_id,
        "reply_id": reply_id,
        "session_name": session_name,
        "timestamp": time.time()
    }
)

# ❌ 错误 - 非结构化日志
logger.info(f"{agent_id}使用了快捷回复{reply_id}")
```

---

### 22.10 文档约束

**强制要求**:
- ✅ 每个新功能必须更新以下文档：
  - `prd/04_任务拆解/enterprise_features_tasks.md` - 任务拆解
  - `prd/03_技术方案/api_contract.md` - API文档
  - `prd/02_约束与原则/CONSTRAINTS_AND_PRINCIPLES.md` - 新增约束
  - `docs/` - 功能使用文档

**文档质量标准**:
```markdown
# 功能名称

## 业务场景
具体的使用场景描述（举例）

## 功能设计
数据模型、API接口、UI设计

## 实现方案
技术选型、架构设计、关键代码

## 验收标准
明确的验收CheckList

## 风险与注意事项
已知问题、性能瓶颈、安全隐患
```

---

### 22.11 禁止事项

**绝对禁止**:
- ❌ 为了功能而功能（无业务价值）
- ❌ 盲目照搬竞品（不评估适配性）
- ❌ 过度设计（初期就考虑所有edge case）
- ❌ 技术炫技（使用不成熟的技术）
- ❌ 忽略性能（不考虑并发和响应时间）
- ❌ 忽略安全（不验证权限）
- ❌ 忽略文档（不更新文档）
- ❌ 破坏一致性（UI风格不统一）

---

### 22.12 验收标准

**Phase 1 (v3.5.0) 验收清单**:
- [ ] 快捷回复支持5个分类
- [ ] 快捷回复支持12+动态变量
- [ ] 支持Ctrl+1-9快捷键
- [ ] 会话标签支持6个系统标签
- [ ] 会话标签支持自定义标签
- [ ] 会话置顶功能正常
- [ ] 欢迎语自动发送
- [ ] 离线提示自动发送
- [ ] 关键词自动回复（10+关键词）
- [ ] 未回复提醒（>30s）
- [ ] VIP客户弹窗提醒
- [ ] 工单SLA提醒
- [ ] 所有API使用JWT认证
- [ ] 所有操作记录审计日志
- [ ] 回归测试12/12通过
- [ ] TypeScript编译0错误
- [ ] 文档完整更新

---

### 22.13 相关文档

- `prd/01_全局指导/REFERENCE_SYSTEMS.md` - 参考系统分析
- `prd/04_任务拆解/enterprise_features_tasks.md` - 任务拆解
- `CLAUDE.md` - 约束22 详细说明

**违反后果**:
- 🟡 功能堆砌，系统臃肿
- 🟡 维护成本高，难以迭代
- 🟡 用户体验差，学习成本高
- 🔴 性能问题，无法支持高并发
- 🔴 安全隐患，数据泄露风险

---

**文档维护者**: Claude Code
**最后更新**: 2025-11-26
**版本**: v1.4 (新增约束22)
