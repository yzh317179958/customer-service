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
  animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.welcome-avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1a1a1a;
  font-weight: 700;
  font-size: 36px;
  margin-bottom: 20px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  padding: 10px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.welcome-avatar:hover {
  transform: scale(1.1) translateY(-5px);
  box-shadow: 0 8px 30px rgba(0,0,0,0.15);
}

.welcome-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.welcome-avatar:hover img {
  transform: rotate(5deg) scale(1.05);
}

.welcome-name {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 15px;
}

.welcome-message {
  font-size: 15px;
  color: #666;
  line-height: 1.6;
  max-width: 320px;
}
</style>
