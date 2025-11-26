<script setup lang="ts">
import { ref, computed } from 'vue'
import type { HistoryMessage, ConversationSummary } from '@/types'

const props = defineProps<{
  messages: HistoryMessage[]
  summary?: ConversationSummary
  loading?: boolean
}>()

// 消息角色配置
const roleConfig = {
  user: { label: '用户', color: '#3B82F6', icon: '👤' },
  assistant: { label: 'AI', color: '#8B5CF6', icon: '🤖' },
  agent: { label: '坐席', color: '#10B981', icon: '👨‍💼' },
  system: { label: '系统', color: '#9CA3AF', icon: 'ℹ️' }
}

// 格式化时间
const formatTime = (timestamp: number): string => {
  const date = new Date(timestamp * 1000)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  // 小于1分钟显示"刚刚"
  if (diff < 60000) {
    return '刚刚'
  }

  // 小于1小时显示"X分钟前"
  if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`
  }

  // 小于24小时显示"X小时前"
  if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`
  }

  // 今年显示"MM-DD HH:mm"
  if (date.getFullYear() === now.getFullYear()) {
    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // 超过一年显示"YYYY-MM-DD HH:mm"
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 格式化完整时间
const formatFullTime = (timestamp: number): string => {
  return new Date(timestamp * 1000).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 格式化时长
const formatDuration = (seconds: number): string => {
  if (seconds < 60) {
    return `${seconds}秒`
  }
  if (seconds < 3600) {
    return `${Math.floor(seconds / 60)}分钟`
  }
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return minutes > 0 ? `${hours}小时${minutes}分钟` : `${hours}小时`
}

// 获取角色配置
const getRoleConfig = (role: string) => {
  return roleConfig[role as keyof typeof roleConfig] || { label: role, color: '#9CA3AF', icon: '?' }
}

// 展开/收起状态
const expandedMessageId = ref<string | null>(null)

const toggleMessage = (messageId: string) => {
  expandedMessageId.value = expandedMessageId.value === messageId ? null : messageId
}

// 判断消息是否过长需要展开
const isLongMessage = (content: string): boolean => {
  return content.length > 200
}

// 截取消息预览
const getMessagePreview = (content: string): string => {
  if (content.length <= 200) return content
  return content.substring(0, 200) + '...'
}
</script>

<template>
  <div class="conversation-history">
    <!-- Loading 状态 -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>加载对话历史...</span>
    </div>

    <!-- 无消息 -->
    <div v-else-if="!messages || messages.length === 0" class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
      </svg>
      <p>暂无对话记录</p>
    </div>

    <!-- 对话历史 -->
    <div v-else class="history-container">
      <!-- 会话摘要 -->
      <div v-if="summary" class="summary-card">
        <div class="summary-header">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 11H3v2h6v-2zm0-4H3v2h6V7zm0 8H3v2h6v-2zm8-4h-6v2h6v-2zm0-4h-6v2h6V7zm0 8h-6v2h6v-2z"></path>
          </svg>
          <span class="summary-title">会话统计</span>
        </div>
        <div class="summary-stats">
          <div class="stat-item">
            <span class="stat-label">总消息</span>
            <span class="stat-value">{{ summary.message_count }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">用户</span>
            <span class="stat-value user">{{ summary.user_message_count }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">AI</span>
            <span class="stat-value ai">{{ summary.ai_message_count }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">坐席</span>
            <span class="stat-value agent">{{ summary.agent_message_count }}</span>
          </div>
        </div>
        <div v-if="summary.start_time" class="summary-info">
          <div class="info-row">
            <span class="info-label">开始时间</span>
            <span class="info-value">{{ formatFullTime(summary.start_time) }}</span>
          </div>
          <div v-if="summary.end_time" class="info-row">
            <span class="info-label">结束时间</span>
            <span class="info-value">{{ formatFullTime(summary.end_time) }}</span>
          </div>
          <div v-if="summary.end_time" class="info-row">
            <span class="info-label">会话时长</span>
            <span class="info-value">{{ formatDuration(summary.end_time - summary.start_time) }}</span>
          </div>
        </div>
        <div v-if="summary.tags && summary.tags.length > 0" class="summary-tags">
          <span v-for="tag in summary.tags" :key="tag" class="tag">{{ tag }}</span>
        </div>
      </div>

      <!-- 消息时间线 -->
      <div class="messages-timeline">
        <div
          v-for="message in messages"
          :key="message.id"
          class="message-item"
          :class="[`role-${message.role}`, { expanded: expandedMessageId === message.id }]"
        >
          <!-- 消息头部 -->
          <div class="message-header">
            <div class="message-role">
              <span class="role-icon">{{ getRoleConfig(message.role).icon }}</span>
              <span class="role-label" :style="{ color: getRoleConfig(message.role).color }">
                {{ getRoleConfig(message.role).label }}
              </span>
              <span v-if="message.agent_name" class="agent-name">
                {{ message.agent_name }}
              </span>
            </div>
            <div class="message-time" :title="formatFullTime(message.timestamp)">
              {{ formatTime(message.timestamp) }}
            </div>
          </div>

          <!-- 消息内容 -->
          <div class="message-content">
            <div
              v-if="isLongMessage(message.content) && expandedMessageId !== message.id"
              class="message-text preview"
            >
              {{ getMessagePreview(message.content) }}
            </div>
            <div v-else class="message-text">
              {{ message.content }}
            </div>

            <!-- 展开/收起按钮 -->
            <button
              v-if="isLongMessage(message.content)"
              class="toggle-btn"
              @click="toggleMessage(message.id)"
            >
              {{ expandedMessageId === message.id ? '收起' : '展开全部' }}
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                :class="{ rotated: expandedMessageId === message.id }"
              >
                <polyline points="6 9 12 15 18 9"></polyline>
              </svg>
            </button>
          </div>

          <!-- 元数据 -->
          <div v-if="message.metadata && Object.keys(message.metadata).length > 0" class="message-metadata">
            <details class="metadata-details">
              <summary>元数据</summary>
              <pre>{{ JSON.stringify(message.metadata, null, 2) }}</pre>
            </details>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.conversation-history {
  height: 100%;
  overflow-y: auto;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: #a0aec0;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e2e8f0;
  border-top-color: #4ECDC4;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state svg {
  margin-bottom: 16px;
  color: #cbd5e0;
}

.history-container {
  padding: 16px;
}

/* 会话摘要 */
.summary-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  padding: 16px;
  margin-bottom: 16px;
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.summary-header svg {
  color: #4ECDC4;
}

.summary-title {
  font-size: 13px;
  font-weight: 600;
  color: #2d3748;
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e2e8f0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-label {
  font-size: 11px;
  color: #718096;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #2d3748;
}

.stat-value.user { color: #3B82F6; }
.stat-value.ai { color: #8B5CF6; }
.stat-value.agent { color: #10B981; }

.summary-info {
  margin-bottom: 12px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  font-size: 12px;
}

.info-label {
  color: #718096;
}

.info-value {
  color: #2d3748;
  font-weight: 500;
}

.summary-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  padding: 4px 10px;
  background: #e2e8f0;
  border-radius: 12px;
  font-size: 11px;
  color: #4a5568;
}

/* 消息时间线 */
.messages-timeline {
  position: relative;
  padding-left: 20px;
}

.messages-timeline::before {
  content: '';
  position: absolute;
  left: 6px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: linear-gradient(to bottom, #e2e8f0 0%, #e2e8f0 100%);
}

.message-item {
  position: relative;
  margin-bottom: 16px;
  background: white;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  transition: all 0.2s ease;
}

.message-item::before {
  content: '';
  position: absolute;
  left: -18px;
  top: 14px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #cbd5e0;
  border: 2px solid white;
  z-index: 1;
}

.message-item.role-user::before { background: #3B82F6; }
.message-item.role-assistant::before { background: #8B5CF6; }
.message-item.role-agent::before { background: #10B981; }
.message-item.role-system::before { background: #9CA3AF; }

.message-item:hover {
  border-color: #cbd5e0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}

.message-role {
  display: flex;
  align-items: center;
  gap: 8px;
}

.role-icon {
  font-size: 14px;
}

.role-label {
  font-size: 12px;
  font-weight: 600;
}

.agent-name {
  font-size: 11px;
  color: #718096;
  padding: 2px 8px;
  background: #e2e8f0;
  border-radius: 8px;
}

.message-time {
  font-size: 11px;
  color: #a0aec0;
}

.message-content {
  padding: 12px;
}

.message-text {
  font-size: 13px;
  color: #2d3748;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.message-text.preview {
  position: relative;
}

.toggle-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  padding: 4px 10px;
  background: #f7fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 11px;
  color: #4a5568;
  cursor: pointer;
  transition: all 0.2s ease;
}

.toggle-btn:hover {
  background: #edf2f7;
  border-color: #cbd5e0;
}

.toggle-btn svg {
  transition: transform 0.2s ease;
}

.toggle-btn svg.rotated {
  transform: rotate(180deg);
}

.message-metadata {
  padding: 0 12px 12px;
}

.metadata-details {
  font-size: 11px;
}

.metadata-details summary {
  color: #718096;
  cursor: pointer;
  user-select: none;
  padding: 4px 0;
}

.metadata-details summary:hover {
  color: #4a5568;
}

.metadata-details pre {
  margin-top: 8px;
  padding: 8px;
  background: #f7fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 10px;
  color: #4a5568;
  overflow-x: auto;
}
</style>
