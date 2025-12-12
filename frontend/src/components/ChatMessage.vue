<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import type { Message } from '@/types'
import { useChatStore } from '@/stores/chatStore'

interface Props {
  message: Message
}

const props = defineProps<Props>()
const chatStore = useChatStore()

// Configure marked for rendering markdown
marked.setOptions({
  breaks: true,
  gfm: true,
})

// 判断消息类型
const isUser = computed(() => props.message.role === 'user')
const isAgent = computed(() => props.message.role === 'agent')
const isSystem = computed(() => props.message.role === 'system')
const isDivider = computed(() => (props.message as any).isDivider === true)

const formattedTime = computed(() => {
  const date = new Date(props.message.timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
})

const renderedContent = computed(() => {
  if (isUser.value) {
    return props.message.content
  }
  // Render markdown for bot and agent messages
  return marked.parse(props.message.content)
})

// 头像内容
const avatarContent = computed(() => {
  if (isUser.value) {
    return 'You'
  }
  if (isAgent.value) {
    return '👤'  // 人工客服图标
  }
  return chatStore.botConfig.name.charAt(0)
})

// 发送者名称
const senderName = computed(() => {
  if (isUser.value) {
    return 'You'
  }
  if (isAgent.value) {
    return props.message.agent_info?.name || 'Agent'
  }
  return chatStore.botConfig.name
})
</script>

<template>
  <!-- System message (包括分隔线) -->
  <div v-if="isSystem || isDivider" class="system-message">
    <div class="system-divider"></div>
    <span class="system-text">{{ message.content }}</span>
    <div class="system-divider"></div>
  </div>

  <!-- Normal message (用户、AI、人工) -->
  <div v-else class="message" :class="{ user: isUser, bot: !isUser && !isAgent, agent: isAgent }">
    <div class="message-avatar" :class="{ 'agent-avatar': isAgent }">
      <img
        v-if="!isUser && !isAgent"
        src="/fiido2.png"
        :alt="chatStore.botConfig.name"
      >
      <template v-else>{{ avatarContent }}</template>
    </div>
    <div class="message-body">
      <div class="message-header">
        <span class="message-sender" :class="{ 'agent-name': isAgent }">{{ senderName }}</span>
        <span v-if="isAgent" class="agent-badge">Live</span>
        <span class="message-time">{{ formattedTime }}</span>
      </div>
      <div class="message-content" v-if="isUser">
        {{ renderedContent }}
      </div>
      <div class="message-content" v-else v-html="renderedContent"></div>
    </div>
  </div>
</template>

<style scoped>
/* =====================================================
   Fiido Premium Message Component - Nano Banana Style
   - Clean, minimal design
   - Subtle shadows and smooth animations
   - Premium feel with elegant spacing
   ===================================================== */

/* System Message - Minimal Divider */
.system-message {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 0;
  margin: 24px 0;
}

.system-divider {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0, 0, 0, 0.08), transparent);
}

.system-text {
  color: #737373;
  font-size: 12px;
  white-space: nowrap;
  font-weight: 500;
  padding: 8px 16px;
  background: #ffffff;
  border-radius: 20px;
  letter-spacing: 0.01em;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

/* Message Base Styles */
.message {
  margin-bottom: 20px;
  display: flex;
  gap: 14px;
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

.message.user {
  flex-direction: row-reverse;
}

/* Avatar Styles */
.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #525252;
  font-weight: 600;
  font-size: 13px;
  flex-shrink: 0;
  overflow: hidden;
  box-shadow:
    0 4px 12px rgba(0, 0, 0, 0.06),
    0 1px 3px rgba(0, 0, 0, 0.04);
  transition: all 0.35s cubic-bezier(0.23, 1, 0.32, 1);
  padding: 6px;
}

.message-avatar:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
}

.message-avatar img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

/* User Avatar - Dark */
.message.user .message-avatar {
  background: #1a1a1a;
  color: #ffffff;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

/* Agent Avatar - Teal Gradient */
.message-avatar.agent-avatar {
  background: linear-gradient(145deg, #00c4bd 0%, #00a6a0 100%);
  color: #ffffff;
  font-size: 16px;
  box-shadow: 0 4px 16px rgba(0, 166, 160, 0.3);
}

/* Message Body */
.message-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 78%;
  min-width: 0;
}

/* Message Header */
.message-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  padding-left: 4px;
}

.message.user .message-header {
  flex-direction: row-reverse;
  padding-left: 0;
  padding-right: 4px;
}

.message-sender {
  font-weight: 500;
  color: #737373;
  letter-spacing: 0.01em;
}

.message-sender.agent-name {
  font-weight: 600;
  color: #00a6a0;
}

/* Agent Badge */
.agent-badge {
  background: linear-gradient(145deg, #00c4bd 0%, #00a6a0 100%);
  color: #ffffff;
  padding: 3px 12px;
  border-radius: 12px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.02em;
  box-shadow: 0 2px 8px rgba(0, 166, 160, 0.25);
}

.message-time {
  color: #a3a3a3;
  font-size: 11px;
  font-weight: 400;
}

/* Message Content Bubble */
.message-content {
  padding: 14px 18px;
  border-radius: 20px;
  word-wrap: break-word;
  line-height: 1.6;
  font-size: 15px;
  position: relative;
}

/* User Message - Dark */
.message.user .message-content {
  background: #1a1a1a;
  color: #ffffff;
  border-bottom-right-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

/* Bot Message - Clean White */
.message.bot .message-content {
  background: #ffffff;
  color: #1a1a1a;
  border-bottom-left-radius: 6px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

/* Agent Message - Teal Accent */
.message.agent .message-content {
  background: linear-gradient(145deg, rgba(0, 166, 160, 0.06) 0%, rgba(0, 196, 189, 0.02) 100%);
  color: #1a1a1a;
  border-bottom-left-radius: 6px;
  box-shadow: 0 2px 12px rgba(0, 166, 160, 0.08);
  border: 1px solid rgba(0, 166, 160, 0.12);
}

/* Markdown Styles */
.message-content :deep(h1),
.message-content :deep(h2),
.message-content :deep(h3) {
  margin-top: 14px;
  margin-bottom: 10px;
  font-weight: 600;
  color: inherit;
}

.message-content :deep(h3) {
  font-size: 1em;
}

.message-content :deep(p) {
  margin: 8px 0;
}

.message-content :deep(ul),
.message-content :deep(ol) {
  margin: 10px 0;
  padding-left: 22px;
}

.message-content :deep(li) {
  margin: 5px 0;
}

.message-content :deep(strong) {
  font-weight: 600;
}

.message.user .message-content :deep(strong) {
  color: #ffffff;
}

/* Links - Teal Accent */
.message-content :deep(a) {
  color: #00a6a0;
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: all 0.25s ease;
}

.message-content :deep(a:hover) {
  color: #00c4bd;
  border-bottom-color: #00c4bd;
}

.message.user .message-content :deep(a) {
  color: rgba(255, 255, 255, 0.85);
  border-bottom-color: rgba(255, 255, 255, 0.3);
}

.message.user .message-content :deep(a:hover) {
  color: #ffffff;
  border-bottom-color: #ffffff;
}

/* Code Blocks */
.message-content :deep(code) {
  background: rgba(0, 0, 0, 0.04);
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 0.9em;
  font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
}

.message.user .message-content :deep(code) {
  background: rgba(255, 255, 255, 0.12);
}

/* Product Images - Premium Style */
.message-content :deep(img) {
  max-width: 110px;
  max-height: 110px;
  width: auto;
  height: auto;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  object-fit: cover;
  display: inline-block;
  vertical-align: middle;
  margin: 8px 12px 8px 0;
  transition: all 0.35s cubic-bezier(0.23, 1, 0.32, 1);
  background: #ffffff;
}

.message-content :deep(img:hover) {
  transform: scale(1.1) translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
}

/* Table Images */
.message-content :deep(table img) {
  max-width: 65px;
  max-height: 65px;
  margin: 5px 0;
  border-radius: 10px;
}

/* Table Styles - Clean & Modern */
.message-content :deep(table) {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  margin: 14px 0;
  font-size: 13px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  table-layout: fixed;
}

.message-content :deep(th),
.message-content :deep(td) {
  padding: 10px 6px;
  text-align: left;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  vertical-align: middle;
  word-wrap: break-word;
}

.message-content :deep(th) {
  background: #fafafa;
  font-weight: 600;
  color: #525252;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.message-content :deep(td) {
  background: #ffffff;
  color: #1a1a1a;
}

/* 商品列 - 占据更多空间 */
.message-content :deep(th:first-child),
.message-content :deep(td:first-child) {
  width: 42%;
}

/* 数量列 - 紧凑 */
.message-content :deep(th:nth-child(2)),
.message-content :deep(td:nth-child(2)) {
  width: 10%;
  text-align: center;
  color: #525252;
}

/* 价格列 - 防止换行 */
.message-content :deep(th:nth-child(3)),
.message-content :deep(td:nth-child(3)) {
  width: 24%;
  text-align: right;
  font-weight: 600;
  color: #00a6a0;
  white-space: nowrap;
}

/* 状态列 - 足够宽度显示文字 */
.message-content :deep(th:nth-child(4)),
.message-content :deep(td:nth-child(4)) {
  width: 24%;
  text-align: center;
  white-space: nowrap;
  font-size: 12px;
}

.message-content :deep(tr:last-child td) {
  border-bottom: none;
}

.message-content :deep(tr:hover td) {
  background: #fafafa;
}

/* Responsive */
@media (max-width: 768px) {
  .message-body {
    max-width: 85%;
  }

  .message-avatar {
    width: 36px;
    height: 36px;
  }

  .message-content {
    padding: 12px 16px;
    font-size: 14px;
  }
}

/* Reduced Motion */
@media (prefers-reduced-motion: reduce) {
  .message,
  .message-avatar,
  .message-content :deep(img) {
    animation: none;
    transition: none;
  }
}
</style>
