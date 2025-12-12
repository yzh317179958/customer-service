<script setup lang="ts">
import { ref } from 'vue'
import { useChatStore } from '@/stores/chatStore'

const chatStore = useChatStore()
const showTooltip = ref(false)
const isHovered = ref(false)
const isPressed = ref(false)

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
      <!-- Fiido Logo -->
      <div class="icon-wrapper">
        <img src="/fiido2.png" alt="Fiido" class="fiido-logo" />
      </div>
    </div>

    <!-- Notification Badge -->
    <span class="chat-badge">
      <span class="badge-inner">1</span>
    </span>

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
  width: 64px;
  height: 64px;
  background: #ffffff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow:
    0 4px 24px rgba(0, 0, 0, 0.12),
    0 2px 8px rgba(0, 0, 0, 0.08),
    0 0 0 1px rgba(0, 0, 0, 0.04);
  transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
  z-index: 999;
  overflow: hidden;
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
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: transparent;
  transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
}

/* Fiido Logo */
.fiido-logo {
  width: 36px;
  height: 36px;
  object-fit: contain;
  transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
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
  right: 76px;
  top: 50%;
  transform: translateY(-50%) translateX(12px);
  background: #ffffff;
  padding: 12px 20px;
  border-radius: 12px;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.12),
    0 2px 8px rgba(0, 0, 0, 0.06),
    0 0 0 1px rgba(0, 0, 0, 0.04);
  opacity: 0;
  visibility: hidden;
  transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
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

/* Badge - Teal accent */
.chat-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  width: 22px;
  height: 22px;
  background: linear-gradient(145deg, #00c4bd 0%, #00a6a0 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 4px 12px rgba(0, 166, 160, 0.4),
    0 2px 4px rgba(0, 0, 0, 0.1);
  border: 3px solid #ffffff;
  animation: badgePop 0.5s cubic-bezier(0.23, 1, 0.32, 1);
  z-index: 3;
}

@keyframes badgePop {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.badge-inner {
  color: #ffffff;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
}

/* Ripple Ring - Subtle breathing */
.ripple-ring {
  position: absolute;
  inset: -2px;
  border-radius: 50%;
  border: 2px solid rgba(0, 166, 160, 0.25);
  animation: ripple 4s ease-out infinite;
  pointer-events: none;
}

@keyframes ripple {
  0% {
    transform: scale(1);
    opacity: 0.5;
  }
  50% {
    opacity: 0.3;
  }
  100% {
    transform: scale(1.5);
    opacity: 0;
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

  .fiido-logo {
    width: 32px;
    height: 32px;
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
