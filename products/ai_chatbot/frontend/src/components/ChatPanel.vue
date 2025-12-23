<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useChatStore } from '@/stores/chatStore'
import { clearConversationHistory } from '@/api/chat'
import ChatMessage from './ChatMessage.vue'
import WelcomeScreen from './WelcomeScreen.vue'

const chatStore = useChatStore()
const chatInput = ref('')
const chatMessagesRef = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLInputElement | null>(null)
const showMenu = ref(false)
let statusPollInterval: number | null = null

// 生产环境使用相对路径（通过nginx代理），本地开发使用8000端口
const API_BASE_URL = computed(() => {
  const hostname = window.location.hostname
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:8000'
  }
  // 生产环境使用同域名，通过 nginx 代理 /api
  return ''
})

// 🔴 P0-9.5: 输入框禁用逻辑
const isInputDisabled = computed(() => {
  return chatStore.isLoading || chatStore.sessionStatus === 'closed'
})

// 🔴 P0-9.6: 动态 placeholder
const inputPlaceholder = computed(() => {
  switch (chatStore.sessionStatus) {
    case 'bot_active':
      return 'Type your message...'
    case 'pending_manual':
      return 'Waiting for agent...'
    case 'manual_live':
      return 'Message agent...'
    case 'after_hours_email':
      return 'Leave a message'
    case 'closed':
      return 'Session closed'
    default:
      return 'Type a message...'
  }
})

// Auto-scroll to bottom (智能滚动：只有用户在底部附近时才自动滚动)
const scrollToBottom = (force = false) => {
  nextTick(() => {
    if (!chatMessagesRef.value) return
    const el = chatMessagesRef.value
    // 检测用户是否在底部附近（100px 容差）
    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 100
    // 强制滚动或用户在底部附近时才滚动
    if (force || isNearBottom) {
      el.scrollTop = el.scrollHeight
    }
  })
}

// Watch messages for auto-scroll
watch(() => chatStore.messages.length, () => {
  scrollToBottom()
})

// Watch chat open state to focus input
watch(() => chatStore.isChatOpen, (isOpen) => {
  if (isOpen) {
    nextTick(() => {
      inputRef.value?.focus()
    })
  }
})

const handleClose = () => {
  chatStore.closeChat()
  showMenu.value = false
}

const toggleMenu = () => {
  showMenu.value = !showMenu.value
}

const closeMenu = () => {
  showMenu.value = false
}

const handleNewConversation = async () => {
  closeMenu()

  if (!confirm('Start a new conversation? Current chat history will be cleared.')) {
    return
  }

  try {
    console.log('🆕 创建新对话...')

    const response = await fetch(`${API_BASE_URL.value}/api/conversation/new`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: chatStore.sessionId })
    })

    const data = await response.json()

    if (data.success && data.conversation_id) {
      chatStore.setConversationId(data.conversation_id)
      chatStore.clearMessages()
      console.log('✅ 新对话已创建:', data.conversation_id)
    } else {
      console.error('创建新对话失败:', data)
    }
  } catch (error) {
    console.error('创建新对话异常:', error)
  }
}

const handleClearConversation = () => {
  closeMenu()

  // 添加分隔线消息
  chatStore.addMessage({
    id: `divider-${Date.now()}`,
    content: '--- Previous conversation ---',
    role: 'system',
    timestamp: new Date(),
    sender: 'System',
    isDivider: true
  })
  console.log('🗑️  已添加历史对话分隔线')
}

const handleNewSession = async () => {
  closeMenu()

  // 立即清空界面，无需等待
  chatStore.clearMessages()
  console.log('🔄 创建新会话...')

  // 异步调用后端创建新会话，不阻塞UI
  try {
    const response = await fetch(`${API_BASE_URL.value}/api/conversation/new`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: chatStore.sessionId })
    })

    const data = await response.json()

    if (data.success && data.conversation_id) {
      chatStore.setConversationId(data.conversation_id)
      console.log('✅ 新会话已创建, Conversation ID:', data.conversation_id)
    } else {
      console.error('⚠️  创建新会话失败:', data)
    }
  } catch (error) {
    console.error('❌ 创建新会话异常:', error)
  }
}

const handleEscalateToManual = async () => {
  closeMenu()

  if (!chatStore.canEscalate) {
    console.warn('⚠️  当前状态不允许转人工')
    return
  }

  if (!confirm('Connect to a live agent?')) {
    return
  }

  try {
    console.log('🚀 发起转人工请求...')
    const success = await chatStore.escalateToManual('manual')

    if (success) {
      console.log('✅ 转人工成功')
      alert('Connecting you to a live agent...')

      // 添加系统消息提示
      chatStore.addMessage({
        id: `system-${Date.now()}`,
        content: 'Connecting you to a live agent, please wait...',
        role: 'system',
        timestamp: new Date(),
        sender: 'System'
      })
    } else {
      alert('Failed to connect. Please try again.')
      console.error('❌ 转人工失败')
    }
  } catch (error) {
    alert('Request failed: ' + (error as Error).message)
    console.error('❌ 转人工异常:', error)
  }
}

// 处理快捷问题点击 - 本地引导回复，不调用API
const handleQuickQuestion = (data: { text: string, guideReply: string }) => {
  // 1. 添加用户点击的问题作为用户消息
  chatStore.addMessage({
    id: Date.now().toString(),
    content: data.text,
    role: 'user',
    timestamp: new Date(),
    sender: 'You'
  })

  // 2. 本地直接回复引导语，不调用API
  setTimeout(() => {
    chatStore.addMessage({
      id: (Date.now() + 1).toString(),
      content: data.guideReply,
      role: 'assistant',
      timestamp: new Date(),
      sender: chatStore.botConfig.name
    })
    // 快捷问题回复后强制滚动
    scrollToBottom(true)
  }, 300) // 短暂延迟模拟回复

  // 3. 标记已经不是首条消息（隐藏欢迎界面）
  chatStore.setFirstMessage(false)
}

const sendMessage = async () => {
  if (chatStore.isLoading || !chatInput.value.trim()) return

  const message = chatInput.value.trim()
  chatInput.value = ''

  // 🔴 P0-9.1: 根据状态判断发送方式
  const status = chatStore.sessionStatus

  // Add user message
  const localMessageId = Date.now().toString()
  chatStore.addMessage({
    id: localMessageId,
    content: message,
    role: 'user',
    timestamp: new Date(),
    sender: 'You'
  })

  // 用户发送消息后强制滚动到底部
  scrollToBottom(true)

  chatStore.setLoading(true)

  // ✅ 关键修复：AI 模式下先立刻插入占位气泡，避免等待网络返回才出现气泡
  const botPlaceholder =
    status === 'bot_active'
      ? {
          id: (Date.now() + 1).toString(),
          content: '',
          role: 'assistant' as const,
          timestamp: new Date(),
          sender: chatStore.botConfig.name,
          isTyping: true
        }
      : null

  if (botPlaceholder) {
    chatStore.addMessage(botPlaceholder)
    scrollToBottom(true)
  }

  try {
    // 🔴 P0-9.2: pending_manual状态 - 禁止发送
    if (status === 'pending_manual') {
      chatStore.addMessage({
        id: `system-${Date.now()}`,
        content: 'Connecting you to a live agent, please wait...',
        role: 'system',
        timestamp: new Date(),
        sender: 'System'
      })
      chatStore.setLoading(false)
      return
    }

    // 🔴 P0-9.3: manual_live状态 - 调用人工消息接口
    if (status === 'manual_live') {
      const response = await fetch(`${API_BASE_URL.value}/api/manual/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_name: chatStore.sessionId,
          role: 'user',
          content: message
        })
      })

      const data = await response.json()

      if (!data.success) {
        throw new Error(data.error || '发送失败')
      }

      // ✅ 关键修复：对齐本地消息时间戳到后端写入时间，避免轮询同步时再次追加同一条消息
      const backendTimestamp = data?.data?.timestamp
      if (typeof backendTimestamp === 'number') {
        const localMessage = chatStore.messages.find(m => m.id === localMessageId)
        if (localMessage) {
          localMessage.timestamp = new Date(backendTimestamp * 1000)
        }
      }

      console.log('✅ 人工模式消息已发送')
      chatStore.setLoading(false)
      return
    }

    // 🔴 P0-9.4: bot_active状态 - 调用AI接口（现有逻辑）
    const requestBody: any = {
      message,
      user_id: chatStore.sessionId
    }

    if (chatStore.conversationId) {
      requestBody.conversation_id = chatStore.conversationId
      console.log('💬 使用 Conversation ID:', chatStore.conversationId)
    }

    const response = await fetch(`${API_BASE_URL.value}/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    })

    if (!response.ok) {
      if (botPlaceholder) {
        botPlaceholder.content = `Sorry, an error occurred (HTTP ${response.status}).`
        botPlaceholder.isTyping = false
      }
      throw new Error(`HTTP ${response.status}`)
    }

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    if (!reader) throw new Error('No reader available')

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))

            // 🔴 P0-8.1: AI消息（现有逻辑）
            if (data.type === 'message') {
              chatStore.updateLastMessage(data.content)
              scrollToBottom()
            }

            // 🔴 P0-8.2: 错误消息（现有逻辑）
            else if (data.type === 'error') {
              chatStore.updateLastMessage('Sorry, an error occurred: ' + data.content)

              // 如果是人工接管错误
              if (data.content === 'MANUAL_IN_PROGRESS') {
                chatStore.updateSessionStatus('manual_live')
              }
            }

            // 🔴 P0-8.3: 人工消息（新增）
            else if (data.type === 'manual_message') {
              if (data.role === 'agent') {
                // 坐席消息
                chatStore.addMessage({
                  id: Date.now().toString(),
                  content: data.content,
                  role: 'agent',
                  timestamp: new Date(data.timestamp * 1000),
                  agent_info: {
                    id: data.agent_id,
                    name: data.agent_name
                  }
                })
              } else if (data.role === 'system') {
                // 系统消息
                chatStore.addMessage({
                  id: `system-${Date.now()}`,
                  content: data.content,
                  role: 'system',
                  timestamp: new Date(data.timestamp * 1000),
                  sender: 'System'
                })
              }
              scrollToBottom()
              console.log('📨 收到人工消息:', data.role, data.content)
            }

            // 🔴 P0-8.4: 状态变化（新增）
            else if (data.type === 'status_change') {
              chatStore.updateSessionStatus(data.status)

              // 如果转为人工模式，保存坐席信息
              if (data.status === 'manual_live' && data.agent_info) {
                chatStore.setAgentInfo({
                  id: data.agent_info.agent_id,
                  name: data.agent_info.agent_name
                })
              }

              console.log('📊 SSE状态变化:', data.status)
            }
          } catch (e) {
            console.error('解析错误:', e)
          }
        }
      }
    }
  } catch (error) {
    console.error('Error:', error)
    // 优先复用 bot 占位气泡展示错误，避免多出一条系统气泡
    const last = chatStore.messages[chatStore.messages.length - 1]
    if (status === 'bot_active' && last?.role === 'assistant' && (last as any).isTyping) {
      ;(last as any).isTyping = false
      last.content = last.content || 'Sorry, failed to send. Please try again.'
    } else {
      chatStore.addMessage({
        id: `system-${Date.now()}`,
        content: 'Sorry, failed to send. Please try again.',
        role: 'system',
        timestamp: new Date(),
        sender: 'System'
      })
    }
  } finally {
    chatStore.setLoading(false)
    inputRef.value?.focus()
  }
}

const handleKeyPress = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

// Initialize conversation on mount
const initializeConversation = async () => {
  try {
    console.log('🔄 初始化会话...')

    const response = await fetch(`${API_BASE_URL.value}/api/conversation/new`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: chatStore.sessionId })
    })

    const data = await response.json()

    if (data.success && data.conversation_id) {
      chatStore.setConversationId(data.conversation_id)
      console.log('✅ 会话初始化成功, Conversation ID:', data.conversation_id)
    } else {
      console.error('⚠️  会话初始化失败:', data)
    }
  } catch (error) {
    console.error('❌ 会话初始化异常:', error)
  }
}

// 🔴 P1-2: 加载会话历史（用户打开页面时回填历史消息）
const loadSessionHistory = async () => {
  try {
    console.log('📚 加载会话历史...')

    const response = await fetch(`${API_BASE_URL.value}/api/sessions/${chatStore.sessionId}`)

    // 404 表示新会话，无历史记录
    if (response.status === 404) {
      console.log('ℹ️  新会话，无历史记录')
      return
    }

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const data = await response.json()

    if (data.success && data.data.session) {
      const session = data.data.session

      // 1. 恢复会话状态
      if (session.status && session.status !== chatStore.sessionStatus) {
        chatStore.updateSessionStatus(session.status)
        console.log('✅ 恢复会话状态:', session.status)
      }

      // 2. 恢复升级信息
      if (session.escalation) {
        chatStore.setEscalationInfo({
          reason: session.escalation.reason,
          details: session.escalation.details || '',
          severity: session.escalation.severity || 'medium',
          trigger_at: session.escalation.trigger_at
        })
        console.log('✅ 恢复升级信息:', session.escalation.reason)
      }

      // 3. 恢复坐席信息
      if (session.assigned_agent) {
        chatStore.setAgentInfo({
          id: session.assigned_agent.id,
          name: session.assigned_agent.name
        })
        console.log('✅ 恢复坐席信息:', session.assigned_agent.name)
      }

      // 4. 恢复历史消息
      if (session.history && session.history.length > 0) {
        console.log(`📨 加载 ${session.history.length} 条历史消息`)

        // 按时间戳排序
        const sortedHistory = [...session.history].sort((a: any, b: any) =>
          a.timestamp - b.timestamp
        )

        // 添加历史消息到前端
        sortedHistory.forEach((msg: any) => {
          // 检查是否已存在（避免重复）
          const exists = chatStore.messages.some(m => {
            const sameRole = m.role === msg.role
            const sameContent = m.content === msg.content
            const sameAgentId = (m.agent_info?.id || null) === (msg.agent_id || null)
            const closeTime = Math.abs(m.timestamp.getTime() / 1000 - msg.timestamp) < 3
            return sameRole && sameContent && sameAgentId && closeTime
          })

          if (!exists) {
            let sender = 'System'
            if (msg.role === 'user') {
              sender = 'You'
            } else if (msg.role === 'assistant') {
              sender = chatStore.botConfig.name
            } else if (msg.role === 'agent') {
              sender = msg.agent_name || 'Agent'
            }

            chatStore.addMessage({
              id: `history-${msg.role}-${msg.timestamp}`,
              content: msg.content,
              role: msg.role,
              timestamp: new Date(msg.timestamp * 1000),
              sender: sender,
              agent_info: msg.agent_id ? {
                id: msg.agent_id,
                name: msg.agent_name || 'Agent'
              } : undefined
            })
          }
        })

        console.log('✅ 历史消息加载完成')
        // 加载历史后强制滚动到底部
        scrollToBottom(true)
      }

      // 5. 如果是人工模式，启动轮询
      if (session.status === 'pending_manual' || session.status === 'manual_live') {
        startStatusPolling()
      }
    }
  } catch (error) {
    console.error('⚠️  加载历史失败:', error)
  }
}

// Handle product inquiry from other components
onMounted(async () => {
  window.addEventListener('ask-product', ((e: CustomEvent) => {
    chatInput.value = `Tell me about the ${e.detail}`
    sendMessage()
  }) as EventListener)

  // Load bot config
  loadBotConfig()

  // Initialize conversation immediately
  await initializeConversation()

  // 🔴 P1-2: 加载历史消息
  await loadSessionHistory()
})

const loadBotConfig = async () => {
  try {
    const response = await fetch(`${API_BASE_URL.value}/api/bot/info`)
    const data = await response.json()

    if (data.success && data.bot) {
      chatStore.setBotConfig({
        name: data.bot.name || 'Fiido Support',
        icon_url: data.bot.icon_url || '',
        description: data.bot.description || '',
        welcome: data.bot.welcome || 'Hello! I\'m Fiido\'s AI assistant. How can I help you today?'
      })
      console.log('✅ Bot 配置加载成功:', chatStore.botConfig)
    }
  } catch (error) {
    console.error('⚠️  Bot 配置加载失败,使用默认配置:', error)
  }
}

// 🔴 新增: 轮询会话状态
const pollSessionStatus = async () => {
  try {
    const response = await fetch(`${API_BASE_URL.value}/api/sessions/${chatStore.sessionId}`)

    if (response.status === 404) {
      // 会话不存在，这是正常情况（新会话）
      return
    }

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const data = await response.json()

    if (data.success && data.data.session) {
      const session = data.data.session
      const newStatus = session.status

      // 只在状态真正变化时更新
      if (newStatus !== chatStore.sessionStatus) {
        console.log(`🔄 状态轮询: ${chatStore.sessionStatus} → ${newStatus}`)
        chatStore.updateSessionStatus(newStatus)

        // 如果转为 manual_live，保存坐席信息
        if (newStatus === 'manual_live' && session.assigned_agent) {
          chatStore.setAgentInfo({
            id: session.assigned_agent.id,
            name: session.assigned_agent.name
          })
        }
      }

      // 🔴 新增: 同步历史消息（检查是否有新消息）
      if (session.history && session.history.length > 0) {
        // 获取后端最后一条消息
        const lastBackendMessage = session.history[session.history.length - 1]
        const lastBackendTimestamp = lastBackendMessage.timestamp

        // 获取前端最后一条消息
        const frontendMessages = chatStore.messages
        const lastFrontendMessage = frontendMessages.length > 0
          ? frontendMessages[frontendMessages.length - 1]
          : null

        const lastFrontendTimestamp = lastFrontendMessage
          ? lastFrontendMessage.timestamp.getTime() / 1000
          : 0

        // 如果后端有新消息（时间戳更新）
        if (lastBackendTimestamp > lastFrontendTimestamp) {
          console.log('📨 检测到新消息，同步历史')

          // 找出所有新消息（时间戳大于前端最后一条消息）
          const newMessages = session.history.filter((msg: any) =>
            msg.timestamp > lastFrontendTimestamp
          )

          // 添加新消息到前端
          newMessages.forEach((msg: any) => {
            // 检查是否已存在（避免重复）
            const exists = chatStore.messages.some(m => {
              const sameRole = m.role === msg.role
              const sameContent = m.content === msg.content
              const sameAgentId = (m.agent_info?.id || null) === (msg.agent_id || null)
              const closeTime = Math.abs(m.timestamp.getTime() / 1000 - msg.timestamp) < 3
              return sameRole && sameContent && sameAgentId && closeTime
            })

            if (!exists) {
              chatStore.addMessage({
                id: `${msg.role}-${msg.timestamp}`,
                content: msg.content,
                role: msg.role,
                timestamp: new Date(msg.timestamp * 1000),
                sender: msg.role === 'agent' ? (msg.agent_name || 'Agent') :
                        msg.role === 'user' ? 'You' : 'System',
                agent_info: msg.agent_id ? {
                  id: msg.agent_id,
                  name: msg.agent_name || 'Agent'
                } : undefined
              })
              console.log(`✅ 添加新消息: ${msg.role} - ${msg.content.substring(0, 20)}...`)
            }
          })

          scrollToBottom()
        }
      }
    }
  } catch (error) {
    console.error('⚠️  状态轮询失败:', error)
  }
}

// 启动状态轮询（仅在 pending_manual 或 manual_live 状态下）
const startStatusPolling = () => {
  if (statusPollInterval !== null) {
    return // 已经在轮询
  }

  console.log('🔄 启动状态轮询')
  statusPollInterval = window.setInterval(() => {
    const status = chatStore.sessionStatus
    if (status === 'pending_manual' || status === 'manual_live') {
      pollSessionStatus()
    } else if (status === 'bot_active' || status === 'closed') {
      // 恢复到稳定状态，停止轮询
      stopStatusPolling()
    }
  }, 2000) // 每2秒轮询一次
}

// 停止状态轮询
const stopStatusPolling = () => {
  if (statusPollInterval !== null) {
    console.log('⏸️  停止状态轮询')
    clearInterval(statusPollInterval)
    statusPollInterval = null
  }
}

// 监听状态变化，自动启动/停止轮询
watch(() => chatStore.sessionStatus, (newStatus) => {
  if (newStatus === 'pending_manual' || newStatus === 'manual_live') {
    startStatusPolling()
  } else if (newStatus === 'bot_active' || newStatus === 'closed') {
    stopStatusPolling()
  }
})

// Close menu when clicking outside
const handleClickOutside = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  // 如果点击的不是菜单容器内的元素，则关闭菜单
  if (!target.closest('.floating-menu-container')) {
    if (showMenu.value) {
      closeMenu()
    }
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

// 组件卸载时清理轮询
onUnmounted(() => {
  stopStatusPolling()
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div>
    <!-- Overlay -->
    <div
      class="chat-overlay"
      :class="{ show: chatStore.isChatOpen }"
      @click="handleClose"
    ></div>

    <!-- Chat Panel -->
    <div class="chat-panel" :class="{ open: chatStore.isChatOpen }">
      <div class="chat-header">
        <div class="header-left">
          <div class="status-dot" :class="chatStore.statusColorClass"></div>
          <h2>{{ chatStore.botConfig.name }}</h2>
        </div>
        <div class="header-right">
          <span class="status-label">{{ chatStore.statusText }}</span>
          <button class="chat-close" @click="handleClose">&times;</button>
        </div>
      </div>

      <!-- Messages Area -->
      <div class="chat-messages" ref="chatMessagesRef">
        <WelcomeScreen
          v-if="chatStore.isFirstMessage && chatStore.messages.length === 0"
          @quick-question="handleQuickQuestion"
        />
        <ChatMessage
          v-for="message in chatStore.messages"
          :key="message.id"
          :message="message"
        />
      </div>

      <!-- Input Area -->
      <div class="chat-input-area">
        <div class="chat-input-wrapper">
          <!-- Floating Action Menu -->
          <div class="floating-menu-container" @click.stop>
            <!-- Main Bubble Button -->
            <button class="main-bubble" @click="toggleMenu" :class="{ active: showMenu }">
              <svg v-if="!showMenu" class="plus-icon" viewBox="0 0 24 24">
                <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
              </svg>
              <svg v-else class="close-icon" viewBox="0 0 24 24">
                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
              </svg>
            </button>

            <!-- Sub Bubbles -->
            <transition name="bubble">
              <div v-if="showMenu" class="sub-bubbles">
                <button
                  class="sub-bubble"
                  @click="handleEscalateToManual"
                  title="Talk to agent"
                  :disabled="!chatStore.canEscalate"
                  :class="{ disabled: !chatStore.canEscalate }"
                >
                  <span class="bubble-text">Live Agent</span>
                </button>
                <button class="sub-bubble" @click="handleNewSession" title="New chat">
                  <span class="bubble-text">New Chat</span>
                </button>
              </div>
            </transition>
          </div>

          <input
            ref="inputRef"
            v-model="chatInput"
            type="text"
            class="chat-input"
            :placeholder="inputPlaceholder"
            @keypress="handleKeyPress"
            :disabled="isInputDisabled"
          >
          <button
            class="chat-send"
            @click="sendMessage"
            :disabled="isInputDisabled || !chatInput.trim()"
          >
            <svg viewBox="0 0 24 24">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          </button>
        </div>

        <!-- Waiting tip -->
        <div v-if="chatStore.sessionStatus === 'pending_manual'" class="waiting-tip">
          <span class="tip-icon">⏳</span>
          <span>Connecting you to a live agent...</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* =====================================================
   Fiido Premium Chat Panel - 统一坐席工作台风格
   - 品牌色: #00a6a0 (fiido)
   - 配色系统: slate 灰色系 + fiido 青绿色
   - 与坐席工作台 UI 保持一致
   ===================================================== */

/* CSS 变量定义 - 与坐席工作台保持一致 */
:root {
  --fiido: #00a6a0;
  --fiido-dark: #008b86;
  --fiido-light: #f0f9f9;
  --fiido-black: #0f172a;
  --fiido-slate: #1e293b;
}

/* Overlay - transparent, not blocking main content */
.chat-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: transparent;
  opacity: 0;
  visibility: hidden;
  transition: all 0.4s ease-out;
  z-index: 999;
  pointer-events: none;
}

.chat-overlay.show {
  opacity: 1;
  visibility: visible;
  pointer-events: auto;
}

/* Chat Panel - Premium Slide-in */
.chat-panel {
  position: fixed;
  top: 0;
  right: -460px;
  width: 440px;
  height: 100vh;
  background: #ffffff;
  box-shadow:
    -12px 0 60px rgba(0, 0, 0, 0.1),
    -4px 0 16px rgba(0, 0, 0, 0.04),
    0 0 0 1px rgba(0, 0, 0, 0.02);
  transition: right 0.5s cubic-bezier(0.23, 1, 0.32, 1);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 20px 0 0 20px;
}

.chat-panel.open {
  right: 0;
}

/* Header - Clean & Premium with integrated status */
.chat-header {
  background: #ffffff;
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  border-bottom: 1px solid #e2e8f0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-left .status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: statusPulse 2.5s ease-in-out infinite;
  flex-shrink: 0;
}

/* 状态点颜色 - 使用 fiido 品牌色系 */
.header-left .status-dot.status-ai {
  background: var(--fiido, #00a6a0);
  box-shadow: 0 0 6px rgba(0, 166, 160, 0.5);
}

.header-left .status-dot.status-pending {
  background: var(--fiido, #00a6a0);
  box-shadow: 0 0 6px rgba(0, 166, 160, 0.5);
  animation: statusPulse 1.5s ease-in-out infinite;
}

.header-left .status-dot.status-manual {
  background: var(--fiido, #00a6a0);
  box-shadow: 0 0 6px rgba(0, 166, 160, 0.5);
}

.header-left .status-dot.status-closed {
  background: #94a3b8;
  box-shadow: 0 0 6px rgba(148, 163, 184, 0.5);
}

.chat-header h2 {
  font-size: 15px;
  font-weight: 600;
  margin: 0;
  color: var(--fiido-slate, #1e293b);
  letter-spacing: -0.01em;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
  padding: 4px 10px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

@keyframes statusPulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(0.9); }
}

.chat-close {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  color: #64748b;
  font-size: 18px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1);
}

.chat-close:hover {
  background: var(--fiido-black, #0f172a);
  color: #ffffff;
  border-color: transparent;
  transform: rotate(90deg);
}

.chat-close:active {
  transform: rotate(90deg) scale(0.92);
}

/* Messages Area - 统一 slate 色系 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: #f8fafc;
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.2);
}

/* Message Styles */
.message {
  margin-bottom: 20px;
  display: flex;
  gap: 12px;
  animation: messageIn 0.4s cubic-bezier(0.23, 1, 0.32, 1);
}

@keyframes messageIn {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.bot {
  flex-direction: row;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--fiido-slate, #1e293b);
  font-weight: 600;
  font-size: 13px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 6px;
  overflow: hidden;
  transition: all 0.35s cubic-bezier(0.23, 1, 0.32, 1);
  border: 1px solid #e2e8f0;
}

.message-avatar:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.message-avatar img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.message-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 78%;
}

/* Input Area - 统一 fiido 风格 */
.chat-input-area {
  padding: 20px 24px 24px;
  background: #ffffff;
  border-top: 1px solid #e2e8f0;
}

.chat-input-wrapper {
  display: flex;
  gap: 12px;
  align-items: center;
  position: relative;
}

/* Floating Action Menu */
.floating-menu-container {
  position: relative;
  display: flex;
  align-items: center;
}

.main-bubble {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  background: var(--fiido-black, #0f172a);
  border: none;
  box-shadow:
    0 4px 16px rgba(15, 23, 42, 0.15),
    0 2px 6px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
  flex-shrink: 0;
  position: relative;
  overflow: hidden;
}

.main-bubble::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--fiido, #00a6a0);
  border-radius: 50%;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.main-bubble:hover {
  transform: translateY(-3px) scale(1.05);
  box-shadow:
    0 8px 24px rgba(0, 166, 160, 0.25),
    0 4px 8px rgba(0, 0, 0, 0.1);
}

.main-bubble:hover::before {
  opacity: 1;
}

.main-bubble:active {
  transform: translateY(-1px) scale(1);
  transition-duration: 0.1s;
}

.main-bubble.active {
  transform: rotate(45deg);
  background: #64748b;
}

.main-bubble svg {
  width: 20px;
  height: 20px;
  fill: #ffffff;
  position: relative;
  z-index: 1;
  transition: transform 0.3s ease;
}

/* Sub Bubbles */
.sub-bubbles {
  position: absolute;
  left: 0;
  bottom: 60px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  animation: bubblesIn 0.35s cubic-bezier(0.23, 1, 0.32, 1);
  z-index: 5;
}

@keyframes bubblesIn {
  from {
    opacity: 0;
    transform: translateY(12px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.bubble-enter-active,
.bubble-leave-active {
  transition: all 0.35s cubic-bezier(0.23, 1, 0.32, 1);
}

.bubble-enter-from,
.bubble-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(0.95);
}

.sub-bubble {
  height: 42px;
  padding: 0 20px;
  border-radius: 21px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1);
  white-space: nowrap;
  position: relative;
  overflow: hidden;
}

.sub-bubble::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--fiido-black, #0f172a);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.sub-bubble:hover {
  transform: translateX(6px);
  border-color: transparent;
  box-shadow:
    0 8px 24px rgba(0, 0, 0, 0.1),
    0 2px 8px rgba(0, 0, 0, 0.04);
}

.sub-bubble:hover::before {
  opacity: 1;
}

.sub-bubble:hover .bubble-text {
  color: #ffffff;
  position: relative;
  z-index: 1;
}

.sub-bubble:active {
  transform: translateX(6px) scale(0.98);
}

.sub-bubble.disabled {
  background: #f8fafc;
  border-color: #e2e8f0;
  cursor: not-allowed;
  opacity: 0.5;
  box-shadow: none;
}

.sub-bubble.disabled:hover {
  transform: none;
  box-shadow: none;
}

.sub-bubble.disabled:hover::before {
  opacity: 0;
}

.sub-bubble.disabled .bubble-text {
  color: #94a3b8;
}

.sub-bubble.disabled:hover .bubble-text {
  color: #94a3b8;
}

.bubble-text {
  font-size: 14px;
  font-weight: 500;
  color: #64748b;
  transition: color 0.3s ease;
  position: relative;
  z-index: 1;
  letter-spacing: -0.01em;
}

/* Input Field - 统一 fiido 风格 */
.chat-input {
  flex: 1;
  padding: 14px 20px;
  border: 1px solid #e2e8f0;
  border-radius: 24px;
  font-family: inherit;
  font-size: 15px;
  outline: none;
  color: var(--fiido-slate, #1e293b);
  background: #f8fafc;
  transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1);
}

.chat-input::placeholder {
  color: #94a3b8;
}

.chat-input:hover {
  border-color: #cbd5e1;
  background: #ffffff;
}

.chat-input:focus {
  border-color: var(--fiido, #00a6a0);
  background: #ffffff;
  box-shadow: 0 0 0 4px rgba(0, 166, 160, 0.1);
}

/* Send Button - 统一 fiido 风格 */
.chat-send {
  background: var(--fiido-black, #0f172a);
  color: #ffffff;
  border: none;
  width: 46px;
  height: 46px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1);
  flex-shrink: 0;
  box-shadow:
    0 2px 8px rgba(15, 23, 42, 0.15),
    0 2px 6px rgba(0, 0, 0, 0.08);
  position: relative;
  overflow: hidden;
}

.chat-send::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--fiido, #00a6a0);
  border-radius: 50%;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.chat-send:hover:not(:disabled) {
  transform: translateY(-3px) scale(1.05);
  box-shadow:
    0 8px 24px rgba(0, 166, 160, 0.3),
    0 4px 8px rgba(0, 0, 0, 0.1);
}

.chat-send:hover:not(:disabled)::before {
  opacity: 1;
}

.chat-send:active:not(:disabled) {
  transform: translateY(-1px) scale(1);
}

.chat-send:disabled {
  background: #e2e8f0;
  cursor: not-allowed;
  opacity: 0.5;
  box-shadow: none;
}

.chat-send svg {
  width: 18px;
  height: 18px;
  fill: #ffffff;
  position: relative;
  z-index: 1;
  transition: transform 0.25s ease;
}

.chat-send:hover:not(:disabled) svg {
  transform: translateX(2px);
}

/* Waiting Tip - 统一 fiido 风格 */
.waiting-tip {
  padding: 14px 18px;
  background: var(--fiido-light, #f0f9f9);
  border: 1px solid rgba(0, 166, 160, 0.2);
  border-radius: 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: var(--fiido, #00a6a0);
  font-weight: 500;
  margin-top: 14px;
  animation: messageIn 0.35s ease;
}

.tip-icon {
  font-size: 18px;
  animation: tipPulse 2s ease-in-out infinite;
}

@keyframes tipPulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
}

/* Responsive */
@media (max-width: 768px) {
  .chat-panel {
    width: 100%;
    right: -100%;
    border-radius: 0;
  }

  .chat-header {
    padding: 18px 20px;
  }

  .chat-messages {
    padding: 20px;
  }

  .chat-input-area {
    padding: 16px 18px 20px;
  }
}

/* Reduced Motion */
@media (prefers-reduced-motion: reduce) {
  .chat-panel,
  .chat-overlay,
  .message,
  .main-bubble,
  .sub-bubble,
  .chat-send,
  .typing-dot {
    animation: none;
    transition: none;
  }
}
</style>
