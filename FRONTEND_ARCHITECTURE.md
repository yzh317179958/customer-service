# Fiido 智能客服系统 - 前后端分离架构

## 项目架构

```
fiido-customer-service/
├── backend.py                  # FastAPI 后端 (端口 8000)
├── src/                        # 后端源码
│   ├── jwt_signer.py
│   └── oauth_token_manager.py
├── frontend/                   # Vue 3 前端 (端口 5173)
│   ├── src/
│   │   ├── components/         # Vue 组件
│   │   │   ├── ChatPanel.vue   # 聊天面板主组件
│   │   │   ├── ChatMessage.vue # 消息组件
│   │   │   ├── ChatInput.vue   # 输入框组件
│   │   │   └── ChatMenu.vue    # 历史对话菜单
│   │   ├── composables/        # Vue Composables
│   │   │   ├── useChat.ts      # 聊天逻辑
│   │   │   ├── useConversation.ts # Conversation 管理
│   │   │   └── useSession.ts   # Session 管理
│   │   ├── stores/             # Pinia Stores
│   │   │   └── chatStore.ts    # 聊天状态管理
│   │   ├── api/                # API 调用
│   │   │   └── chat.ts         # 聊天 API
│   │   ├── types/              # TypeScript 类型
│   │   │   └── chat.ts         # 聊天相关类型
│   │   └── App.vue             # 主应用
│   ├── package.json
│   └── vite.config.ts
├── tests/                      # 测试脚本
├── docs/                       # 文档
└── README.md
```

## 技术栈

### 后端
- **框架**: FastAPI
- **鉴权**: OAuth JWT
- **AI平台**: Coze Workflow Chat API
- **会话隔离**: session_name (JWT + API payload)
- **历史对话**: conversation_id

### 前端
- **框架**: Vue 3 + TypeScript
- **状态管理**: Pinia
- **路由**: Vue Router
- **构建工具**: Vite
- **HTTP客户端**: Fetch API
- **样式**: CSS3 (可选 Tailwind CSS)

## 核心功能实现

### 1. 历史对话管理

#### 数据流程

```
用户首次访问
    ↓
生成 SESSION_ID (sessionStorage)
    ↓
创建 CONVERSATION_ID (调用后端 API)
    ↓
发送消息 (携带 session_id + conversation_id)
    ↓
保留历史对话上下文
```

#### 用户操作

1. **新对话** (点击加号菜单)
   - 清空前端聊天记录显示
   - 创建新的 conversation_id
   - 保持 session_id 不变
   - 结果: 清空历史,开始新话题

2. **新会话** (点击加号菜单)
   - 清空 sessionStorage
   - 生成新的 session_id
   - 创建新的 conversation_id
   - 结果: 完全隔离的新用户身份

### 2. 前端核心组件

#### ChatPanel.vue (主组件)
```vue
<template>
  <div class="chat-panel">
    <ChatHeader
      @new-conversation="handleNewConversation"
      @new-session="handleNewSession"
    />
    <ChatMessages :messages="messages" />
    <ChatInput @send="handleSend" :disabled="isLoading" />
  </div>
</template>

<script setup lang="ts">
import { useChatStore } from '@/stores/chatStore'
import { useConversation } from '@/composables/useConversation'

const chatStore = useChatStore()
const { createConversation } = useConversation()

const handleNewConversation = async () => {
  // 清空消息
  chatStore.clearMessages()
  // 创建新 conversation
  await createConversation()
}

const handleNewSession = () => {
  // 清空所有存储
  sessionStorage.clear()
  // 刷新页面
  window.location.reload()
}
</script>
```

#### useConversation.ts (Composable)
```typescript
import { ref } from 'vue'
import { createNewConversation } from '@/api/chat'

export function useConversation() {
  const conversationId = ref<string | null>(
    sessionStorage.getItem('conversation_id')
  )

  const createConversation = async (sessionId: string) => {
    const response = await createNewConversation(sessionId)
    if (response.success && response.conversation_id) {
      conversationId.value = response.conversation_id
      sessionStorage.setItem('conversation_id', response.conversation_id)
      console.log('✅ 创建新 Conversation:', response.conversation_id)
    }
  }

  return {
    conversationId,
    createConversation
  }
}
```

#### chatStore.ts (Pinia Store)
```typescript
import { defineStore } from 'pinia'
import type { Message } from '@/types/chat'

export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: [] as Message[],
    isLoading: false,
    sessionId: sessionStorage.getItem('session_id') || '',
    conversationId: sessionStorage.getItem('conversation_id') || ''
  }),

  actions: {
    addMessage(message: Message) {
      this.messages.push(message)
    },

    clearMessages() {
      this.messages = []
    },

    setConversationId(id: string) {
      this.conversationId = id
      sessionStorage.setItem('conversation_id', id)
    }
  }
})
```

### 3. API 调用

#### chat.ts
```typescript
const API_BASE = 'http://localhost:8000'

export interface ChatRequest {
  message: string
  user_id: string
  conversation_id?: string
}

export interface ConversationResponse {
  success: boolean
  conversation_id?: string
  error?: string
}

// 创建新 Conversation
export async function createNewConversation(
  sessionId: string
): Promise<ConversationResponse> {
  const response = await fetch(`${API_BASE}/api/conversation/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: sessionId })
  })
  return response.json()
}

// 流式聊天
export async function sendChatStream(
  request: ChatRequest,
  onMessage: (content: string) => void,
  onComplete: () => void,
  onError: (error: string) => void
) {
  try {
    const response = await fetch(`${API_BASE}/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    while (reader) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === 'message') {
              onMessage(data.content)
            } else if (data.type === 'done') {
              onComplete()
            } else if (data.type === 'error') {
              onError(data.content)
            }
          } catch (e) {
            console.error('解析错误:', e)
          }
        }
      }
    }
  } catch (error) {
    onError(error instanceof Error ? error.message : '连接失败')
  }
}
```

## 部署说明

### 开发环境

#### 启动后端
```bash
cd /home/yzh/AI客服/鉴权
python3 backend.py
# 运行在 http://localhost:8000
```

#### 启动前端
```bash
cd /home/yzh/AI客服/鉴权/frontend
npm run dev
# 运行在 http://localhost:5173
```

### 生产环境

#### 构建前端
```bash
cd frontend
npm run build
# 输出到 frontend/dist/
```

#### 配置后端提供前端静态文件
```python
# backend.py
from fastapi.staticfiles import StaticFiles

# 挂载前端构建文件
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
```

#### 单端口部署
```bash
# 后端提供前端 + API
python3 backend.py
# 访问 http://localhost:8000
```

## 下一步计划

1. ✅ 后端 conversation 管理已实现
2. 🔄 创建 Vue 3 前端组件
3. ⏳ 实现历史对话UI
4. ⏳ 前后端联调测试
5. ⏳ 生产构建和部署

## 优势

### 相比单HTML文件

| 方面 | 单HTML | Vue 3 分离 |
|------|--------|-----------|
| **代码组织** | ❌ 混在一起 | ✅ 分层清晰 |
| **类型安全** | ❌ 无类型 | ✅ TypeScript |
| **状态管理** | ❌ 手动管理 | ✅ Pinia 自动 |
| **代码复用** | ❌ 复制粘贴 | ✅ 组件化 |
| **开发体验** | ❌ 无热重载 | ✅ HMR |
| **可维护性** | ❌ 难维护 | ✅ 易维护 |
| **可测试性** | ❌ 难测试 | ✅ 易测试 |

### 技术特性

- ✅ 响应式状态管理 (Pinia)
- ✅ 类型安全 (TypeScript)
- ✅ 组件化开发
- ✅ 热模块替换 (HMR)
- ✅ 自动依赖追踪
- ✅ 生产优化构建

---

**文档更新**: 2025-11-19
**架构**: 前后端分离 (FastAPI + Vue 3)
