# 历史对话管理功能实现方案

## 需求分析

用户需求:
- 点击小加号按钮
- 弹出两个选项:
  1. **新对话** - 清除历史对话,保持当前会话
  2. **新会话** - 创建全新的会话

## Coze Workflow Chat API 说明

根据官方文档和 SDK,Workflow Chat 支持以下参数:

```python
coze.workflows.chat.stream(
    workflow_id="xxx",           # 必需: 工作流ID
    bot_id="xxx",                # 可选: Bot ID
    conversation_id="xxx",       # 可选: 会话ID (用于多轮对话)
    additional_messages=[...],   # 必需: 消息列表
)
```

### conversation_id 的作用

- **有 conversation_id**: 保留历史对话上下文,实现多轮对话
- **无 conversation_id**: 每次都是全新对话,没有上下文记忆

### session_name 的作用 (本项目已实现)

- 用于会话隔离,确保不同用户的对话互不干扰
- 在 JWT payload 和 API request payload 中都要传递

## 实现方案

### 1. 后端改动

#### 1.1 添加 Conversation管理接口

```python
# 新增数据模型
class NewConversationRequest(BaseModel):
    user_id: str  # session_id

class ConversationResponse(BaseModel):
    success: bool
    conversation_id: Optional[str] = None
    error: Optional[str] = None

# 新增API接口
@app.post("/api/conversation/create")
async def create_conversation(request: NewConversationRequest):
    """创建新的 conversation (用于多轮对话)"""
    session_id = request.user_id
    access_token = token_manager.get_access_token(session_name=session_id)

    # 使用 Coze SDK 创建 conversation
    conversation = coze_client.conversations.create()

    return ConversationResponse(
        success=True,
        conversation_id=conversation.id
    )
```

#### 1.2 修改聊天接口

```python
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None          # session_id
    conversation_id: Optional[str] = None  # 新增: conversation_id

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    session_id = request.user_id or generate_user_id()
    access_token = token_manager.get_access_token(session_name=session_id)

    payload = {
        "workflow_id": WORKFLOW_ID,
        "app_id": APP_ID,
        "session_name": session_id,
        "parameters": {"USER_INPUT": request.message},
        "additional_messages": [...]
    }

    # 如果有 conversation_id,添加到 payload
    if request.conversation_id:
        payload["conversation_id"] = request.conversation_id

    # 发送请求...
```

### 2. 前端改动

#### 2.1 Conversation ID 管理

```javascript
// 在 sessionStorage 中存储 conversation_id
let CONVERSATION_ID = sessionStorage.getItem('fiido_conversation_id');

// 创建新 conversation
async function createNewConversation() {
    const response = await fetch(`${API_BASE_URL}/api/conversation/create`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ user_id: SESSION_ID })
    });

    const data = await response.json();
    if (data.success) {
        CONVERSATION_ID = data.conversation_id;
        sessionStorage.setItem('fiido_conversation_id', CONVERSATION_ID);
        console.log('✅ 创建新 conversation:', CONVERSATION_ID);
    }
}

// 页面加载时初始化 conversation
if (!CONVERSATION_ID) {
    await createNewConversation();
}
```

#### 2.2 发送消息时携带 conversation_id

```javascript
async function sendMessage() {
    const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            message,
            user_id: SESSION_ID,
            conversation_id: CONVERSATION_ID  // 新增
        })
    });
    //...
}
```

#### 2.3 UI - 添加小加号按钮和菜单

```html
<style>
.chat-header-actions {
    display: flex;
    gap: 10px;
    align-items: center;
}

.new-chat-btn {
    background: transparent;
    border: none;
    color: #fff;
    cursor: pointer;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.3s;
    position: relative;
}

.new-chat-btn:hover {
    background: rgba(255,255,255,0.1);
}

.chat-menu {
    position: absolute;
    top: 60px;
    right: 20px;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    overflow: hidden;
    display: none;
    z-index: 1001;
}

.chat-menu.show {
    display: block;
}

.chat-menu-item {
    padding: 12px 20px;
    cursor: pointer;
    border-bottom: 1px solid #f0f0f0;
    transition: background 0.2s;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 14px;
    color: #333;
}

.chat-menu-item:last-child {
    border-bottom: none;
}

.chat-menu-item:hover {
    background: #f5f5f5;
}

.chat-menu-icon {
    width: 18px;
    height: 18px;
    fill: #666;
}
</style>

<!-- 修改聊天头部 -->
<div class="chat-header">
    <h2>Fiido 智能客服</h2>
    <div class="chat-header-actions">
        <button class="new-chat-btn" onclick="toggleChatMenu()">
            <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
            </svg>
        </button>
        <button class="chat-close" onclick="closeChat()">&times;</button>
    </div>
</div>

<!-- 聊天菜单 -->
<div class="chat-menu" id="chatMenu">
    <div class="chat-menu-item" onclick="startNewConversation()">
        <svg class="chat-menu-icon" viewBox="0 0 24 24">
            <path d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 9h12v2H6V9zm8 5H6v-2h8v2zm4-6H6V6h12v2z"/>
        </svg>
        <span>新对话</span>
    </div>
    <div class="chat-menu-item" onclick="startNewSession()">
        <svg class="chat-menu-icon" viewBox="0 0 24 24">
            <path d="M12 5V1L7 6l5 5V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z"/>
        </svg>
        <span>新会话</span>
    </div>
</div>
```

#### 2.4 JavaScript 实现

```javascript
// 切换菜单显示
function toggleChatMenu() {
    const menu = document.getElementById('chatMenu');
    menu.classList.toggle('show');
}

// 点击其他地方关闭菜单
document.addEventListener('click', (e) => {
    const menu = document.getElementById('chatMenu');
    const btn = document.querySelector('.new-chat-btn');
    if (!menu.contains(e.target) && !btn.contains(e.target)) {
        menu.classList.remove('show');
    }
});

// 新对话 - 清空历史,创建新 conversation,保持当前 session
async function startNewConversation() {
    console.log('🆕 开始新对话...');

    // 隐藏菜单
    document.getElementById('chatMenu').classList.remove('show');

    // 清空聊天记录
    const messagesDiv = document.getElementById('chatMessages');
    messagesDiv.innerHTML = '';

    // 显示欢迎屏幕
    const welcomeScreen = document.getElementById('welcomeScreen');
    if (welcomeScreen) {
        welcomeScreen.classList.remove('hidden');
        updateWelcomeScreen();
    }
    isFirstMessage = true;

    // 创建新的 conversation
    await createNewConversation();

    console.log(`✅ 新对话已创建 (Session: ${SESSION_ID}, Conversation: ${CONVERSATION_ID})`);
}

// 新会话 - 创建全新的 session 和 conversation
function startNewSession() {
    console.log('🔄 开始新会话...');

    // 隐藏菜单
    document.getElementById('chatMenu').classList.remove('show');

    // 清除所有存储
    sessionStorage.removeItem('fiido_session_id');
    sessionStorage.removeItem('fiido_conversation_id');

    // 刷新页面 (重新生成 session_id 和 conversation_id)
    window.location.reload();
}
```

## 数据流程

### 场景 1: 用户首次打开页面

```
1. 生成 SESSION_ID (session_abc123)
2. 调用 /api/conversation/create → 获取 CONVERSATION_ID (conv_xyz789)
3. 存储到 sessionStorage
4. 用户发送消息,携带 session_id 和 conversation_id
5. 保留对话历史
```

### 场景 2: 用户点击"新对话"

```
1. 保持 SESSION_ID 不变 (session_abc123)
2. 清空前端聊天记录
3. 调用 /api/conversation/create → 获取新的 CONVERSATION_ID (conv_new456)
4. 更新 sessionStorage
5. 后续对话使用新的 conversation_id
→ 结果: 清空了显示的历史,但用户身份不变 (session_name)
```

### 场景 3: 用户点击"新会话"

```
1. 清除 sessionStorage (session_id + conversation_id)
2. 刷新页面
3. 生成新的 SESSION_ID (session_def456)
4. 创建新的 CONVERSATION_ID (conv_ghi789)
→ 结果: 全新的用户会话,完全隔离
```

## 关键点

### session_name vs conversation_id

| 用途 | session_name | conversation_id |
|------|--------------|-----------------|
| **会话隔离** | ✅ 核心作用 | ❌ 无此作用 |
| **历史对话** | ❌ 无此作用 | ✅ 核心作用 |
| **在哪设置** | JWT + API payload | API payload |
| **本项目现状** | ✅ 已实现 | ❌ 未实现 |

### 两者关系

- **session_name**: 标识用户身份,确保不同用户的数据隔离
- **conversation_id**: 标识对话上下文,确保多轮对话的连贯性

**一个用户(session_name)可以有多个对话(conversation_id)**

## 实现优先级

1. ✅ **高优先级**: 添加 conversation_id 支持 (实现历史对话)
2. ✅ **高优先级**: 前端 UI (小加号按钮 + 菜单)
3. ✅ **中优先级**: 后端 conversation 管理接口
4. ⚠️ **低优先级**: 持久化存储 (可选,当前用 sessionStorage)

## 测试计划

### 测试 1: 历史对话保留

```
1. 发送: "我叫张三"
2. 发送: "我多大?" → 应该回答: "张三,你的年龄..."
3. 发送: "我叫什么?" → 应该回答: "张三"
→ 验证: 有 conversation_id 时保留上下文
```

### 测试 2: 新对话

```
1. 发送: "我叫张三"
2. 点击"新对话"
3. 发送: "我叫什么?" → 应该回答: "您还没告诉我..."
→ 验证: conversation_id 改变后,历史清空
```

### 测试 3: 新会话

```
1. 用户 A: "我叫张三"
2. 点击"新会话" (刷新页面)
3. 发送: "我叫什么?" → 应该回答: "您还没告诉我..."
→ 验证: session_name 改变后,完全隔离
```

## 下一步

1. 修改后端代码,添加 conversation 管理
2. 修改前端代码,添加 UI 和逻辑
3. 测试验证功能
4. 更新文档
