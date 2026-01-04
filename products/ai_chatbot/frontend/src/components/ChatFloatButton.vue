<script setup lang="ts">
import { ref } from 'vue'
import { useChatStore } from '@/stores/chatStore'

const chatStore = useChatStore()
const showTooltip = ref(false)
const isHovered = ref(false)
const isPressed = ref(false)

// 悬浮按钮图标路径
const floatIconSrc = import.meta.env.BASE_URL + 'customer-service.jpg'

const handleClick = () => {
  chatStore.openChat()
}

const handleMouseDown = () => {
  isPressed.value = true
}

const handleMouseUp = () => {
  isPressed.value = false
}
</script>

<template>
  <div
    class="chat-float-button"
    :class="{ hovered: isHovered, pressed: isPressed }"
    @click="handleClick"
    @mouseenter="showTooltip = true; isHovered = true"
    @mouseleave="showTooltip = false; isHovered = false; isPressed = false"
    @mousedown="handleMouseDown"
    @mouseup="handleMouseUp"
  >
    <!-- Tooltip -->
    <span class="chat-tooltip" :class="{ show: showTooltip }">
      <span class="tooltip-text">Need help?</span>
    </span>

    <!-- Main Button -->
    <div class="button-inner">
      <div class="icon-wrapper">
        <img :src="floatIconSrc" alt="Fiido" class="fiido-logo" />
      </div>
    </div>

    <!-- Ripple Effect -->
    <div class="ripple-ring"></div>
  </div>
</template>

<style scoped>
/* =====================================================
   Fiido Premium Float Button - Nano Banana Style
   - Smooth animations
   - Subtle shadows
   - Premium feel
   ===================================================== */

.chat-float-button {
  position: fixed;
  bottom: 28px;
  right: 28px;
  width: 52px;
  height: 52px;
  background: #ffffff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow:
    0 4px 20px rgba(0, 0, 0, 0.1),
    0 2px 6px rgba(0, 0, 0, 0.06);
  transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
  z-index: 999;
}

/* Subtle gradient overlay on hover */
.chat-float-button::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: linear-gradient(145deg, rgba(0, 166, 160, 0.08) 0%, rgba(0, 196, 189, 0.04) 100%);
  opacity: 0;
  transition: opacity 0.4s ease;
}

/* Outer glow ring */
.chat-float-button::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  background: transparent;
  border: 2px solid transparent;
  transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
}

/* Hover state - premium lift effect */
.chat-float-button:hover {
  transform: translateY(-6px) scale(1.08);
  box-shadow:
    0 16px 40px rgba(0, 166, 160, 0.2),
    0 8px 20px rgba(0, 0, 0, 0.1),
    0 0 0 1px rgba(0, 166, 160, 0.1);
}

.chat-float-button:hover::before {
  opacity: 1;
}

.chat-float-button:hover::after {
  border-color: rgba(0, 166, 160, 0.3);
  animation: ringPulse 2s ease-in-out infinite;
}

@keyframes ringPulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.5;
  }
}

/* Pressed state */
.chat-float-button.pressed {
  transform: translateY(-2px) scale(1.02);
  box-shadow:
    0 6px 16px rgba(0, 0, 0, 0.12),
    0 2px 6px rgba(0, 0, 0, 0.08);
  transition-duration: 0.15s;
}

/* Button Inner */
.button-inner {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  position: relative;
  z-index: 2;
}

.icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: transparent;
  transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1);
}

/* Fiido Logo */
.fiido-logo {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
  transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1);
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.08));
}

.chat-float-button:hover .fiido-logo {
  transform: scale(1.12) rotate(3deg);
  filter: drop-shadow(0 4px 8px rgba(0, 166, 160, 0.2));
}

.chat-float-button.pressed .fiido-logo {
  transform: scale(1.05) rotate(0deg);
}

/* Tooltip - Premium style */
.chat-tooltip {
  position: absolute;
  right: 64px;
  top: 50%;
  transform: translateY(-50%) translateX(12px);
  background: #ffffff;
  padding: 10px 16px;
  border-radius: 10px;
  box-shadow:
    0 4px 16px rgba(0, 0, 0, 0.1),
    0 2px 6px rgba(0, 0, 0, 0.05);
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1);
  pointer-events: none;
  white-space: nowrap;
}

.chat-tooltip::after {
  content: '';
  position: absolute;
  right: -8px;
  top: 50%;
  transform: translateY(-50%);
  width: 0;
  height: 0;
  border-left: 8px solid #ffffff;
  border-top: 8px solid transparent;
  border-bottom: 8px solid transparent;
  filter: drop-shadow(2px 0 4px rgba(0, 0, 0, 0.06));
}

.chat-tooltip.show {
  opacity: 1;
  visibility: visible;
  transform: translateY(-50%) translateX(0);
}

.tooltip-text {
  color: #1a1a1a;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.01em;
}

/* Ripple Ring - Breathing animation to attract attention */
.ripple-ring {
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  border: 2px solid rgba(0, 166, 160, 0.4);
  animation: breathe 3s ease-in-out infinite;
  pointer-events: none;
}

@keyframes breathe {
  0%, 100% {
    transform: scale(1);
    opacity: 0.6;
    border-color: rgba(0, 166, 160, 0.4);
  }
  50% {
    transform: scale(1.15);
    opacity: 0.2;
    border-color: rgba(0, 166, 160, 0.3);
  }
}

.chat-float-button:hover .ripple-ring {
  animation: none;
  opacity: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .chat-float-button {
    bottom: 20px;
    right: 20px;
    width: 56px;
    height: 56px;
  }

  /* 图片保持填满按钮，不固定尺寸 */
  .fiido-logo {
    width: 100%;
    height: 100%;
  }

  .chat-tooltip {
    display: none;
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .chat-float-button,
  .chat-tooltip,
  .ripple-ring,
  .chat-badge,
  .fiido-logo {
    animation: none;
    transition: none;
  }
}
</style>
