<script setup lang="ts">
import { useChatStore } from '@/stores/chatStore'

const chatStore = useChatStore()
</script>

<template>
  <div class="welcome-screen">
    <div class="welcome-avatar">
      <img
        src="/fiido2.png"
        :alt="chatStore.botConfig.name"
      >
    </div>
    <div class="welcome-name">{{ chatStore.botConfig.name }}</div>
    <div class="welcome-message">{{ chatStore.botConfig.welcome }}</div>
  </div>
</template>

<style scoped>
.welcome-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 30px;
  text-align: center;
  animation: welcomeFadeIn 0.4s ease-out;
}

@keyframes welcomeFadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.welcome-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
  font-weight: 600;
  font-size: 24px;
  margin-bottom: 20px;
  padding: 8px;
  overflow: hidden;
}

.welcome-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.welcome-name {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 10px;
}

.welcome-message {
  font-size: 14px;
  color: #6b7280;
  line-height: 1.6;
  max-width: 280px;
}
</style>
