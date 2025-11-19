import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Message, BotConfig } from '@/types'

export const useChatStore = defineStore('chat', () => {
  // State
  const messages = ref<Message[]>([])
  const isLoading = ref(false)
  const sessionId = ref(sessionStorage.getItem('fiido_session_id') || generateSessionId())
  const conversationId = ref(sessionStorage.getItem('fiido_conversation_id') || '')
  const isChatOpen = ref(false)
  const isFirstMessage = ref(true)

  const botConfig = ref<BotConfig>({
    name: 'Fiido 客服',
    icon_url: '',
    description: 'Fiido 智能客服助手',
    welcome: '您好！我是Fiido智能客服助手,很高兴为您服务。请问有什么可以帮助您的？'
  })

  // Computed
  const hasMessages = computed(() => messages.value.length > 0)
  const lastMessage = computed(() => messages.value[messages.value.length - 1])

  // Actions
  function generateSessionId(): string {
    const id = `session_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`
    sessionStorage.setItem('fiido_session_id', id)
    console.log('🆕 生成新会话 ID:', id)
    return id
  }

  function addMessage(message: Message) {
    messages.value.push(message)
    if (isFirstMessage.value) {
      isFirstMessage.value = false
    }
  }

  function updateLastMessage(content: string) {
    const last = messages.value[messages.value.length - 1]
    if (last && last.role === 'assistant') {
      last.content += content
    }
  }

  function clearMessages() {
    messages.value = []
    isFirstMessage.value = true
    console.log('🗑️  清空聊天记录')
  }

  function setConversationId(id: string) {
    conversationId.value = id
    sessionStorage.setItem('fiido_conversation_id', id)
    console.log('💬 设置 Conversation ID:', id)
  }

  function setBotConfig(config: Partial<BotConfig>) {
    botConfig.value = { ...botConfig.value, ...config }
  }

  function setLoading(loading: boolean) {
    isLoading.value = loading
  }

  function toggleChat() {
    isChatOpen.value = !isChatOpen.value
  }

  function openChat() {
    isChatOpen.value = true
  }

  function closeChat() {
    isChatOpen.value = false
  }

  return {
    messages,
    isLoading,
    sessionId,
    conversationId,
    botConfig,
    isChatOpen,
    isFirstMessage,
    hasMessages,
    lastMessage,
    addMessage,
    updateLastMessage,
    clearMessages,
    setConversationId,
    setBotConfig,
    setLoading,
    toggleChat,
    openChat,
    closeChat,
    generateSessionId
  }
})
