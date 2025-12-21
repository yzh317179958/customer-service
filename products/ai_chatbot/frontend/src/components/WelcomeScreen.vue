<script setup lang="ts">
import { useChatStore } from '@/stores/chatStore'

const chatStore = useChatStore()

// 快捷问题列表 - 包含引导回复
const quickQuestions = [
  {
    icon: '🚚',
    text: 'Order status',
    // 本地引导回复，不调用API
    guideReply: 'To help you check your order status, please provide your **order number** (e.g., #12345 or FD-XXXXX). You can find it in your order confirmation email.'
  },
  {
    icon: '🔧',
    text: 'Product help',
    guideReply: 'I\'d be happy to help with your Fiido e-bike! Please describe the issue you\'re experiencing, or let me know which product model you have (e.g., D11, X3, etc.).'
  },
  {
    icon: '↩️',
    text: 'Returns',
    guideReply: 'For returns or refunds, please provide your **order number** and briefly describe the reason for return. Our team will assist you promptly.'
  },
  {
    icon: '📞',
    text: 'Contact us',
    guideReply: 'I can connect you with our support team. Before I do, could you briefly describe your issue so we can direct you to the right specialist?'
  }
]

const emit = defineEmits<{
  (e: 'quick-question', data: { text: string, guideReply: string }): void
}>()

const handleQuickQuestion = (item: typeof quickQuestions[0]) => {
  emit('quick-question', { text: item.text, guideReply: item.guideReply })
}
</script>

<template>
  <div class="welcome-screen">
    <!-- Logo - 居中 -->
    <div class="welcome-avatar">
      <img
        src="/fiido2.png"
        :alt="chatStore.botConfig.name"
      >
    </div>

    <!-- Welcome Message -->
    <div class="welcome-message">
      <p class="greeting">Hi there!</p>
      <p class="description">How can I help you today?</p>
    </div>

    <!-- Quick Questions - 垂直列表但更紧凑 -->
    <div class="quick-questions">
      <div class="quick-buttons">
        <button
          v-for="(item, index) in quickQuestions"
          :key="index"
          class="quick-btn"
          @click="handleQuickQuestion(item)"
        >
          <span class="quick-icon">{{ item.icon }}</span>
          <span class="quick-text">{{ item.text }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* =====================================================
   Fiido Welcome Screen - Compact & Elegant
   ===================================================== */

/* Welcome Screen Container - 居中紧凑布局 */
.welcome-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 20px;
  text-align: center;
  animation: welcomeIn 0.5s cubic-bezier(0.23, 1, 0.32, 1);
}

@keyframes welcomeIn {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Avatar - 精致尺寸 */
.welcome-avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
  padding: 8px;
  overflow: hidden;
  box-shadow:
    0 4px 16px rgba(0, 0, 0, 0.06),
    0 2px 4px rgba(0, 0, 0, 0.04);
  transition: all 0.35s cubic-bezier(0.23, 1, 0.32, 1);
}

.welcome-avatar:hover {
  transform: scale(1.08);
  box-shadow: 0 8px 24px rgba(0, 166, 160, 0.12);
}

.welcome-avatar img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

/* Welcome Message - 紧凑 */
.welcome-message {
  margin-bottom: 16px;
}

.greeting {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 4px 0;
}

.description {
  font-size: 13px;
  color: #737373;
  margin: 0;
  line-height: 1.4;
}

/* Quick Questions - 紧凑列表 */
.quick-questions {
  width: 100%;
  max-width: 280px;
}

.quick-buttons {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* Quick Button - 精致小巧 */
.quick-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 14px;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.23, 1, 0.32, 1);
  text-align: left;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
}

.quick-btn:hover {
  border-color: rgba(0, 166, 160, 0.25);
  background: linear-gradient(145deg, rgba(0, 166, 160, 0.03) 0%, transparent 100%);
  transform: translateX(3px);
  box-shadow: 0 4px 12px rgba(0, 166, 160, 0.08);
}

.quick-btn:active {
  transform: translateX(3px) scale(0.98);
  transition-duration: 0.1s;
}

.quick-icon {
  font-size: 15px;
  flex-shrink: 0;
}

.quick-text {
  font-size: 13px;
  font-weight: 500;
  color: #525252;
}

.quick-btn:hover .quick-text {
  color: #00a6a0;
}

/* Responsive */
@media (max-width: 768px) {
  .welcome-screen {
    padding: 20px 16px;
  }

  .welcome-avatar {
    width: 48px;
    height: 48px;
  }

  .quick-questions {
    max-width: 100%;
  }

  .quick-btn {
    padding: 9px 12px;
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .welcome-screen,
  .welcome-avatar,
  .quick-btn {
    animation: none;
    transition: none;
  }
}
</style>
