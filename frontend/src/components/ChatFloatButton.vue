<script setup lang="ts">
import { ref } from 'vue'
import { useChatStore } from '@/stores/chatStore'

const chatStore = useChatStore()
const showTooltip = ref(false)

const handleClick = () => {
  chatStore.openChat()
}
</script>

<template>
  <div
    class="chat-float-button"
    @click="handleClick"
    @mouseenter="showTooltip = true"
    @mouseleave="showTooltip = false"
  >
    <span class="chat-tooltip" :class="{ show: showTooltip }">要帮忙?</span>
    <svg viewBox="0 0 24 24">
      <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
      <circle cx="12" cy="11" r="1"/>
      <circle cx="8" cy="11" r="1"/>
      <circle cx="16" cy="11" r="1"/>
    </svg>
    <span class="chat-badge">1</span>
  </div>
</template>

<style scoped>
.chat-float-button {
  position: fixed;
  bottom: 30px;
  right: 30px;
  width: 60px;
  height: 60px;
  background: #1a1a1a;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 999;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  }
  50% {
    box-shadow: 0 4px 20px rgba(26,26,26,0.4);
  }
}

.chat-float-button:hover {
  transform: scale(1.15) translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.3);
  background: #333;
  animation: none;
}

.chat-float-button svg {
  width: 28px;
  height: 28px;
  fill: #fff;
}

.chat-tooltip {
  position: absolute;
  right: 75px;
  top: 50%;
  transform: translateY(-50%) translateX(10px);
  background: #1a1a1a;
  color: #fff;
  padding: 10px 18px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  box-shadow: 0 4px 16px rgba(0,0,0,0.2);
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
}

.chat-tooltip.show {
  opacity: 1;
  visibility: visible;
  transform: translateY(-50%) translateX(0);
}

.chat-tooltip::after {
  content: '';
  position: absolute;
  right: -6px;
  top: 50%;
  transform: translateY(-50%);
  width: 0;
  height: 0;
  border-left: 6px solid #1a1a1a;
  border-top: 6px solid transparent;
  border-bottom: 6px solid transparent;
}

.chat-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: #d32f2f;
  color: #fff;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  border: 2px solid #fff;
}

/* Responsive */
@media (max-width: 768px) {
  .chat-float-button {
    bottom: 20px;
    right: 20px;
    width: 56px;
    height: 56px;
  }
}
</style>
