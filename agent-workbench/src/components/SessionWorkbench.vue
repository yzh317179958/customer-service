<template>
  <div class="session-workbench">
    <!-- 会话列表区域 -->
    <div class="session-list-panel">
      <!-- 统计卡片 -->
      <div class="stats-cards">
        <div class="stat-card stat-pending" @click="handleFilterChange('pending_manual')">
          <div class="stat-value">{{ sessionStore.pendingCount }}</div>
          <div class="stat-label">待接入</div>
        </div>
        <div class="stat-card stat-active" @click="handleFilterChange('manual_live')">
          <div class="stat-value">{{ sessionStore.manualLiveCount }}</div>
          <div class="stat-label">服务中</div>
        </div>
        <div class="stat-card stat-total" @click="handleFilterChange('all')">
          <div class="stat-value">{{ sessionStore.stats.total_sessions }}</div>
          <div class="stat-label">全部</div>
        </div>
      </div>

      <!-- 筛选标签 -->
      <div class="filter-tabs">
        <button
          v-for="filter in filters"
          :key="filter.value"
          class="filter-tab"
          :class="{ active: currentFilter === filter.value }"
          @click="handleFilterChange(filter.value)"
        >
          {{ filter.label }}
        </button>
      </div>

      <!-- 搜索框 -->
      <div class="search-wrapper">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索用户、会话ID..."
          :prefix-icon="Search"
          clearable
        />
      </div>

      <!-- 会话列表 -->
      <div class="session-list" v-loading="sessionStore.isLoading">
        <div
          v-for="session in filteredSessions"
          :key="session.session_name"
          class="session-item"
          :class="{ active: sessionStore.currentSessionName === session.session_name }"
          @click="handleSelectSession(session.session_name)"
        >
          <div class="session-avatar">
            {{ session.user_profile?.nickname?.charAt(0) || 'U' }}
          </div>
          <div class="session-content">
            <div class="session-header">
              <span class="session-user">{{ session.user_profile?.nickname || session.session_name }}</span>
              <span class="session-time">{{ formatTime(session.updated_at) }}</span>
            </div>
            <div class="session-preview">
              {{ session.last_message_preview?.content || '暂无消息' }}
            </div>
            <div class="session-footer">
              <el-tag :type="getStatusType(session.status)" size="small">
                {{ getStatusLabel(session.status) }}
              </el-tag>
              <span v-if="session.assigned_agent" class="session-agent">
                {{ session.assigned_agent.name }}
              </span>
            </div>
          </div>
          <button
            v-if="session.status === 'pending_manual'"
            class="takeover-btn"
            @click.stop="handleTakeover(session.session_name)"
          >
            接入
          </button>
        </div>

        <div v-if="filteredSessions.length === 0" class="empty-state">
          <MessageSquareOff />
          <p>暂无会话</p>
        </div>
      </div>
    </div>

    <!-- 聊天区域 -->
    <div class="chat-panel">
      <div v-if="!sessionStore.currentSession" class="empty-chat">
        <MessageSquare />
        <p>选择一个会话开始服务</p>
      </div>

      <div v-else class="chat-container">
        <!-- 聊天头部 -->
        <div class="chat-header">
          <div class="chat-user-info">
            <div class="chat-avatar">
              {{ sessionStore.currentSession.user_profile?.nickname?.charAt(0) || 'U' }}
            </div>
            <div>
              <div class="chat-user-name">
                {{ sessionStore.currentSession.user_profile?.nickname || sessionStore.currentSession.session_name }}
              </div>
              <div class="chat-session-id">{{ sessionStore.currentSession.session_name }}</div>
            </div>
          </div>

          <div class="chat-actions">
            <button
              v-if="sessionStore.currentSession.status === 'pending_manual'"
              class="action-btn primary"
              @click="handleTakeover(sessionStore.currentSession.session_name)"
            >
              接入会话
            </button>
            <button
              v-if="sessionStore.currentSession.status === 'manual_live'"
              class="action-btn"
              @click="openTransferDialog"
            >
              转接
            </button>
            <button
              v-if="sessionStore.currentSession.status === 'manual_live'"
              class="action-btn danger"
              @click="handleRelease"
            >
              结束服务
            </button>
          </div>
        </div>

        <!-- 聊天历史 -->
        <div ref="chatHistoryRef" class="chat-history">
          <div
            v-for="message in sessionStore.currentSession.history"
            :key="message.id"
            class="message"
            :class="message.role"
          >
            <div v-if="message.role === 'system'" class="system-message">
              {{ message.content }}
            </div>
            <template v-else>
              <div class="message-avatar">
                {{ message.role === 'user' ? 'U' : message.role === 'agent' ? 'A' : 'AI' }}
              </div>
              <div class="message-body">
                <div class="message-meta">
                  <span class="message-sender">
                    {{ message.role === 'user' ? '用户' : message.role === 'agent' ? message.agent_name || '客服' : 'AI' }}
                  </span>
                  <span class="message-time">
                    {{ formatMessageTime(message.timestamp) }}
                  </span>
                </div>
                <div class="message-content">{{ message.content }}</div>
              </div>
            </template>
          </div>
        </div>

        <!-- 聊天输入区 -->
        <div v-if="sessionStore.currentSession.status === 'manual_live'" class="chat-input-area">
          <div class="input-toolbar">
            <button class="toolbar-btn" @click="showQuickReplies = !showQuickReplies">
              <Zap />
              快捷短语
            </button>
          </div>

          <!-- 快捷回复面板 -->
          <div v-if="showQuickReplies" class="quick-replies-panel">
            <QuickReplies
              :session-name="sessionStore.currentSession.session_name"
              :customer-name="customerProfile?.name || customerProfile?.email || '客户'"
              :agent-name="agentStore.agent?.name || '客服'"
              @select="handleQuickReplySelect"
            />
          </div>

          <div class="input-wrapper">
            <textarea
              v-model="messageInput"
              class="message-input"
              placeholder="输入消息... (Enter发送, Shift+Enter换行)"
              rows="3"
              @keydown="handleKeyPress"
            ></textarea>
            <button
              class="send-btn"
              :disabled="!messageInput.trim() || isSending"
              @click="handleSendMessage"
            >
              <Send v-if="!isSending" />
              <Loader2 v-else class="spinning" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 客户信息侧边栏 -->
    <div v-if="sessionStore.currentSession" class="customer-panel">
      <div class="customer-tabs-header">
        <button
          v-for="tab in customerTabs"
          :key="tab.key"
          class="customer-tab"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>
      <div class="customer-tabs-content">
        <CustomerProfile
          v-if="activeTab === 'profile'"
          :customer="customerProfile"
          :loading="loadingCustomer"
        />
        <OrderList
          v-else-if="activeTab === 'orders'"
          :orders="customerOrders"
          :loading="loadingOrders"
        />
        <DeviceInfo
          v-else-if="activeTab === 'devices'"
          :devices="customerDevices"
          :loading="loadingDevices"
        />
        <ConversationHistory
          v-else-if="activeTab === 'history'"
          :messages="conversationHistory"
          :summary="conversationSummary"
          :loading="loadingHistory"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useAgentStore } from '@/stores/agentStore'
import { useSessionStore } from '@/stores/sessionStore'
import { useAgentWorkbenchSSE } from '@/composables/useAgentWorkbenchSSE'
import {
  Search,
  MessageSquare,
  MessageSquareOff,
  Zap,
  Send,
  Loader2
} from 'lucide-vue-next'
import CustomerProfile from '@/components/customer/CustomerProfile.vue'
import OrderList from '@/components/customer/OrderList.vue'
import DeviceInfo from '@/components/customer/DeviceInfo.vue'
import ConversationHistory from '@/components/customer/ConversationHistory.vue'
import QuickReplies from '@/components/QuickReplies.vue'
import type { SessionStatus } from '@/types'
import axios from 'axios'

const agentStore = useAgentStore()
const sessionStore = useSessionStore()
const { startMonitoring, stopMonitoring } = useAgentWorkbenchSSE()

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

// 筛选状态
const currentFilter = ref<SessionStatus | 'all'>('pending_manual')
const searchKeyword = ref('')

// 筛选选项
const filters = [
  { label: '待接入', value: 'pending_manual' },
  { label: '服务中', value: 'manual_live' },
  { label: '全部', value: 'all' }
]

// 过滤后的会话列表
const filteredSessions = computed(() => {
  if (!searchKeyword.value.trim()) {
    return sessionStore.sessions
  }

  const keyword = searchKeyword.value.toLowerCase().trim()
  return sessionStore.sessions.filter(session => {
    return (
      session.session_name.toLowerCase().includes(keyword) ||
      session.user_profile?.nickname?.toLowerCase().includes(keyword) ||
      session.last_message_preview?.content.toLowerCase().includes(keyword)
    )
  })
})

// 聊天相关
const messageInput = ref('')
const isSending = ref(false)
const chatHistoryRef = ref<HTMLElement | null>(null)
const showQuickReplies = ref(false)

// 客户信息相关
const activeTab = ref('profile')
const customerTabs = [
  { key: 'profile', label: '客户' },
  { key: 'orders', label: '订单' },
  { key: 'devices', label: '设备' },
  { key: 'history', label: '历史' }
]
const customerProfile = ref(null)
const loadingCustomer = ref(false)
const customerOrders = ref([])
const loadingOrders = ref(false)
const customerDevices = ref([])
const loadingDevices = ref(false)
const conversationHistory = ref([])
const conversationSummary = ref(undefined)
const loadingHistory = ref(false)

// 处理筛选变化
const handleFilterChange = async (filter: SessionStatus | 'all') => {
  currentFilter.value = filter
  if (filter === 'all') {
    await sessionStore.fetchSessions()
  } else {
    await sessionStore.setFilter(filter)
  }
}

// 选择会话
const handleSelectSession = async (sessionName: string) => {
  await sessionStore.fetchSessionDetail(sessionName)
  fetchCustomerProfile(sessionName)
}

// 接入会话
const handleTakeover = async (sessionName: string) => {
  try {
    await sessionStore.takeoverSession(
      sessionName,
      agentStore.agentId,
      agentStore.agentName
    )
    await sessionStore.fetchSessionDetail(sessionName)
  } catch (err: any) {
    console.error('接入失败:', err)
  }
}

// 发送消息
const handleSendMessage = async () => {
  if (!messageInput.value.trim() || isSending.value || !sessionStore.currentSession) return

  const content = messageInput.value.trim()
  messageInput.value = ''
  isSending.value = true

  try {
    await sessionStore.sendMessage(
      sessionStore.currentSession.session_name,
      content,
      agentStore.agentId,
      agentStore.agentName
    )
    await scrollToBottom()
  } catch (err: any) {
    console.error('发送失败:', err)
  } finally {
    isSending.value = false
  }
}

/**
 * 处理快捷回复选择
 */
const handleQuickReplySelect = (content: string) => {
  // 将快捷回复内容填充到输入框
  messageInput.value = content

  // 关闭快捷回复面板
  showQuickReplies.value = false

  // 可选：自动发送（如果需要的话）
  // await handleSendMessage()
}

// 处理键盘事件
const handleKeyPress = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSendMessage()
  }
}

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (chatHistoryRef.value) {
    chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight
  }
}

// 释放会话
const handleRelease = async () => {
  if (!sessionStore.currentSession) return
  if (!confirm('确定要结束本次服务吗？')) return

  try {
    await sessionStore.releaseSession(
      sessionStore.currentSession.session_name,
      agentStore.agentId,
      'resolved'
    )
    sessionStore.clearCurrentSession()
  } catch (err: any) {
    console.error('释放失败:', err)
  }
}

// 打开转接对话框
const openTransferDialog = () => {
  // TODO: 实现转接对话框
  console.log('打开转接对话框')
}

// 获取客户画像
const fetchCustomerProfile = async (customerId: string) => {
  try {
    loadingCustomer.value = true
    const token = localStorage.getItem('access_token')
    const response = await axios.get(
      `${API_BASE}/api/customers/${customerId}/profile`,
      { headers: { Authorization: `Bearer ${token}` } }
    )
    if (response.data.success) {
      customerProfile.value = response.data.data
    }
  } catch (error) {
    console.error('获取客户信息失败:', error)
  } finally {
    loadingCustomer.value = false
  }
}

// 格式化时间
const formatTime = (timestamp: number) => {
  const date = new Date(timestamp * 1000)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`

  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  return `${month}-${day} ${hour}:${minute}`
}

const formatMessageTime = (timestamp: number) => {
  const date = new Date(timestamp * 1000)
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  return `${hour}:${minute}`
}

// 获取状态类型
const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    pending_manual: 'warning',
    manual_live: 'primary',
    bot_active: 'success'
  }
  return types[status] || 'info'
}

// 获取状态标签
const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    pending_manual: '待接入',
    manual_live: '服务中',
    bot_active: 'AI服务'
  }
  return labels[status] || status
}

// 监听当前会话变化
watch(() => sessionStore.currentSessionName, (newSession) => {
  if (newSession) {
    fetchCustomerProfile(newSession)
  } else {
    customerProfile.value = null
    customerOrders.value = []
    customerDevices.value = []
    conversationHistory.value = []
  }
})

onMounted(async () => {
  await startMonitoring()
})

onUnmounted(() => {
  stopMonitoring()
})
</script>

<style scoped lang="scss">
@import '@/styles/design-system.scss';

.session-workbench {
  display: flex;
  height: 100%;
  gap: 1px;
  background: $border-light;
}

// ========== 会话列表面板 ==========
.session-list-panel {
  width: $session-list-width;
  background: $bg-primary;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: $spacing-2;
  padding: $spacing-4;
  border-bottom: 1px solid $border-light;
}

.stat-card {
  padding: $spacing-3;
  border-radius: $radius-md;
  cursor: pointer;
  transition: all $transition-base;
  text-align: center;

  &:hover {
    transform: translateY(-2px);
    box-shadow: $shadow-md;
  }

  .stat-value {
    font-size: $font-size-2xl;
    font-weight: $font-weight-bold;
    margin-bottom: $spacing-1;
  }

  .stat-label {
    font-size: $font-size-xs;
    color: $text-secondary;
    font-weight: $font-weight-medium;
  }

  &.stat-pending {
    background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%);
    .stat-value { color: #EA580C; }
  }

  &.stat-active {
    background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
    .stat-value { color: #2563EB; }
  }

  &.stat-total {
    background: linear-gradient(135deg, #F9FAFB 0%, #F3F4F6 100%);
    .stat-value { color: #374151; }
  }
}

.filter-tabs {
  display: flex;
  padding: $spacing-2 $spacing-4;
  gap: $spacing-2;
  border-bottom: 1px solid $border-light;
}

.filter-tab {
  @include button-reset;
  flex: 1;
  padding: $spacing-2;
  border-radius: $radius-base;
  font-size: $font-size-sm;
  font-weight: $font-weight-medium;
  color: $text-secondary;
  background: transparent;
  transition: all $transition-base;

  &:hover {
    background: $bg-tertiary;
    color: $text-primary;
  }

  &.active {
    background: $brand-primary;
    color: $text-white;
  }
}

.search-wrapper {
  padding: $spacing-4;
  border-bottom: 1px solid $border-light;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: $spacing-2;
}

.session-item {
  display: flex;
  gap: $spacing-3;
  padding: $spacing-3;
  border-radius: $radius-md;
  cursor: pointer;
  transition: all $transition-base;
  position: relative;
  margin-bottom: $spacing-1;

  &:hover {
    background: $bg-secondary;
  }

  &.active {
    background: $bg-info-light;
    border-left: 3px solid $brand-primary;
  }

  .session-avatar {
    width: 40px;
    height: 40px;
    border-radius: $radius-full;
    background: linear-gradient(135deg, $brand-primary 0%, $brand-primary-light 100%);
    color: $text-white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: $font-weight-bold;
    font-size: $font-size-base;
    flex-shrink: 0;
  }

  .session-content {
    flex: 1;
    min-width: 0;
  }

  .session-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $spacing-1;
  }

  .session-user {
    font-size: $font-size-sm;
    font-weight: $font-weight-semibold;
    color: $text-primary;
    @include text-ellipsis;
  }

  .session-time {
    font-size: $font-size-xs;
    color: $text-tertiary;
    flex-shrink: 0;
    margin-left: $spacing-2;
  }

  .session-preview {
    font-size: $font-size-sm;
    color: $text-secondary;
    margin-bottom: $spacing-2;
    @include text-ellipsis;
  }

  .session-footer {
    display: flex;
    align-items: center;
    gap: $spacing-2;

    .session-agent {
      font-size: $font-size-xs;
      color: $text-tertiary;
    }
  }

  .takeover-btn {
    @include button-reset;
    padding: $spacing-1 $spacing-3;
    background: $brand-primary;
    color: $text-white;
    border-radius: $radius-base;
    font-size: $font-size-xs;
    font-weight: $font-weight-medium;
    align-self: flex-start;
    transition: all $transition-base;

    &:hover {
      background: $brand-primary-dark;
    }
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: $spacing-10;
  color: $text-tertiary;

  svg {
    width: 48px;
    height: 48px;
    margin-bottom: $spacing-4;
  }

  p {
    font-size: $font-size-sm;
  }
}

// ========== 聊天面板 ==========
.chat-panel {
  flex: 1;
  background: $bg-primary;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.empty-chat {
  @include flex-center;
  flex-direction: column;
  height: 100%;
  color: $text-tertiary;

  svg {
    width: 64px;
    height: 64px;
    margin-bottom: $spacing-4;
  }

  p {
    font-size: $font-size-base;
  }
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-header {
  padding: $spacing-4 $spacing-6;
  border-bottom: 1px solid $border-light;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.chat-user-info {
  display: flex;
  align-items: center;
  gap: $spacing-3;

  .chat-avatar {
    width: 40px;
    height: 40px;
    border-radius: $radius-full;
    background: linear-gradient(135deg, $brand-primary 0%, $brand-primary-light 100%);
    color: $text-white;
    @include flex-center;
    font-weight: $font-weight-bold;
    font-size: $font-size-base;
  }

  .chat-user-name {
    font-size: $font-size-base;
    font-weight: $font-weight-semibold;
    color: $text-primary;
  }

  .chat-session-id {
    font-size: $font-size-xs;
    color: $text-tertiary;
    font-family: $font-family-mono;
  }
}

.chat-actions {
  display: flex;
  gap: $spacing-2;
}

.action-btn {
  @include button-reset;
  padding: $spacing-2 $spacing-4;
  border-radius: $radius-base;
  font-size: $font-size-sm;
  font-weight: $font-weight-medium;
  border: 1px solid $border-medium;
  background: $bg-primary;
  color: $text-primary;
  transition: all $transition-base;

  &:hover {
    background: $bg-secondary;
    border-color: $border-dark;
  }

  &.primary {
    background: $brand-primary;
    color: $text-white;
    border-color: $brand-primary;

    &:hover {
      background: $brand-primary-dark;
    }
  }

  &.danger {
    color: $color-error;
    border-color: $color-error;

    &:hover {
      background: $color-error-light;
    }
  }
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: $spacing-6;
}

.message {
  display: flex;
  gap: $spacing-3;
  margin-bottom: $spacing-4;

  &.user {
    flex-direction: row-reverse;
  }

  &.system {
    justify-content: center;
  }

  .system-message {
    padding: $spacing-2 $spacing-4;
    background: $bg-tertiary;
    border-radius: $radius-full;
    font-size: $font-size-xs;
    color: $text-secondary;
  }

  .message-avatar {
    width: 32px;
    height: 32px;
    border-radius: $radius-full;
    @include flex-center;
    font-weight: $font-weight-bold;
    font-size: $font-size-xs;
    flex-shrink: 0;
  }

  &.user .message-avatar {
    background: $neutral-200;
    color: $text-primary;
  }

  &.assistant .message-avatar {
    background: linear-gradient(135deg, $color-success 0%, #34D399 100%);
    color: $text-white;
  }

  &.agent .message-avatar {
    background: linear-gradient(135deg, $brand-primary 0%, $brand-primary-light 100%);
    color: $text-white;
  }

  .message-body {
    max-width: 70%;
  }

  .message-meta {
    display: flex;
    align-items: center;
    gap: $spacing-2;
    margin-bottom: $spacing-1;
  }

  .message-sender {
    font-size: $font-size-xs;
    font-weight: $font-weight-semibold;
    color: $text-secondary;
  }

  .message-time {
    font-size: $font-size-xs;
    color: $text-tertiary;
  }

  .message-content {
    padding: $spacing-3 $spacing-4;
    border-radius: $radius-md;
    font-size: $font-size-sm;
    line-height: $line-height-relaxed;
    word-wrap: break-word;
  }

  &.user .message-content {
    background: $brand-primary;
    color: $text-white;
  }

  &.assistant .message-content {
    background: $bg-secondary;
    color: $text-primary;
  }

  &.agent .message-content {
    background: $bg-info-light;
    color: $text-primary;
    border-left: 3px solid $brand-primary;
  }
}

.chat-input-area {
  padding: $spacing-4 $spacing-6;
  border-top: 1px solid $border-light;
  flex-shrink: 0;
}

.input-toolbar {
  margin-bottom: $spacing-2;
}

.quick-replies-panel {
  margin-bottom: $spacing-3;
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.toolbar-btn {
  @include button-reset;
  padding: $spacing-1 $spacing-3;
  border-radius: $radius-base;
  font-size: $font-size-xs;
  font-weight: $font-weight-medium;
  color: $text-secondary;
  background: $bg-secondary;
  transition: all $transition-base;
  display: inline-flex;
  align-items: center;
  gap: $spacing-1;

  svg {
    width: 14px;
    height: 14px;
  }

  &:hover {
    background: $bg-tertiary;
    color: $text-primary;
  }
}

.input-wrapper {
  display: flex;
  gap: $spacing-3;
  align-items: flex-end;

  .message-input {
    flex: 1;
    padding: $spacing-3 $spacing-4;
    border: 1px solid $border-medium;
    border-radius: $radius-md;
    font-size: $font-size-sm;
    font-family: $font-family-base;
    resize: none;
    transition: all $transition-base;

    &:focus {
      outline: none;
      border-color: $brand-primary;
      box-shadow: 0 0 0 3px rgba($brand-primary, 0.1);
    }
  }

  .send-btn {
    @include button-reset;
    width: 40px;
    height: 40px;
    border-radius: $radius-md;
    background: $brand-primary;
    color: $text-white;
    @include flex-center;
    transition: all $transition-base;

    &:hover:not(:disabled) {
      background: $brand-primary-dark;
      transform: translateY(-2px);
      box-shadow: $shadow-md;
    }

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    svg {
      width: 20px;
      height: 20px;

      &.spinning {
        animation: spin 1s linear infinite;
      }
    }
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

// ========== 客户信息面板 ==========
.customer-panel {
  width: $customer-info-width;
  background: $bg-primary;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.customer-tabs-header {
  display: flex;
  border-bottom: 1px solid $border-light;
  padding: 0 $spacing-4;
}

.customer-tab {
  @include button-reset;
  flex: 1;
  padding: $spacing-3 $spacing-4;
  font-size: $font-size-sm;
  font-weight: $font-weight-medium;
  color: $text-secondary;
  border-bottom: 2px solid transparent;
  transition: all $transition-base;

  &:hover {
    color: $text-primary;
    background: $bg-secondary;
  }

  &.active {
    color: $brand-primary;
    border-bottom-color: $brand-primary;
  }
}

.customer-tabs-content {
  flex: 1;
  overflow-y: auto;
  padding: $spacing-4;
}
</style>
