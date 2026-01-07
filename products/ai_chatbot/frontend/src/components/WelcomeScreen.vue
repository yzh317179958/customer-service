<script setup lang="ts">
import { useChatStore, type UserIntent } from '@/stores/chatStore'

const chatStore = useChatStore()

// 快捷问题列表 - 三个业务分支 + 联系客服
// v7.8.0: 简化为 presale（售前）、tracking（物流）、after_sale（售后）三大分支
const quickQuestions = [
  {
    icon: import.meta.env.BASE_URL + 'icons/icon-product-help.png',
    text: 'Pre-sales inquiry',
    intent: 'presale' as UserIntent,
    // 售前咨询（购车相关）
    guideReply: 'Welcome! I\'m here to help you find the perfect Fiido e-bike. What would you like to know? You can ask about:\n\n• Product features & specifications\n• Price & promotions\n• Which model suits your needs\n• Availability & shipping'
  },
  {
    icon: import.meta.env.BASE_URL + 'icons/icon-order-status.png',
    text: "Where's my package?",
    intent: 'tracking' as UserIntent,
    // 物流查询
    guideReply: 'I\'d be happy to help track your order! Please provide your **order number** (e.g., UK22080, NL16479). You can find it in your order confirmation email.'
  },
  {
    icon: import.meta.env.BASE_URL + 'icons/icon-return.png',
    text: 'After-sales support',
    intent: 'after_sale' as UserIntent,
    // 售后问题（退换货、维修、投诉等）
    guideReply: 'I\'m here to help with any after-sales issues. Please describe your problem, such as:\n\n• Returns & refunds\n• Product repairs\n• Warranty claims\n• Other issues\n\nIf you have an order number, please provide it for faster assistance.'
  },
  {
    icon: import.meta.env.BASE_URL + 'icons/icon-contact-us.png',
    text: 'Contact support team',
    intent: 'contact_agent' as UserIntent,
    // 联系售后团队
    guideReply: 'I\'ll connect you with our support team. Before I do, could you briefly describe your issue so we can direct you to the right specialist?'
  }
]

// 客服主图标路径
const avatarSrc = import.meta.env.BASE_URL + 'customer-service.jpg'

const emit = defineEmits<{
  (e: 'quick-question', data: { text: string, guideReply: string, intent: UserIntent }): void
}>()

const handleQuickQuestion = (item: typeof quickQuestions[0]) => {
  emit('quick-question', { text: item.text, guideReply: item.guideReply, intent: item.intent })
}
</script>

<template>
  <div class="welcome-screen">
    <!-- Logo - 居中 -->
    <div class="welcome-avatar">
      <img
        :src="avatarSrc"
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
          <img class="quick-icon" :src="item.icon" :alt="item.text" />
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
  object-fit: cover;
  border-radius: 50%;
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
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  object-fit: contain;
}

.quick-text {
  font-size: 13px;
  font-weight: 500;
  color: #525252;
}

.quick-btn:hover .quick-text {
  color: #00a6a0;
}

/* Responsive - 仅在非嵌入模式下生效 */
@media (max-width: 768px) {
  html:not(.embed-mode) .welcome-screen {
    padding: 20px 16px;
  }

  html:not(.embed-mode) .welcome-avatar {
    width: 48px;
    height: 48px;
  }

  html:not(.embed-mode) .quick-questions {
    max-width: 100%;
  }

  html:not(.embed-mode) .quick-btn {
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
