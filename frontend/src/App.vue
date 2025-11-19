<template>
  <div id="app">
    <AppHeader />
    <HeroSection />
    <ProductsSection />
    <AppFooter />
    <ChatFloatButton />
    <ChatPanel />
    <div class="chat-overlay" :class="{ show: chatStore.isChatOpen }" @click="chatStore.closeChat()"></div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useChatStore } from './stores/chatStore'
import { loadBotConfig } from './api/chat'
import AppHeader from './components/AppHeader.vue'
import HeroSection from './components/HeroSection.vue'
import ProductsSection from './components/ProductsSection.vue'
import AppFooter from './components/AppFooter.vue'
import ChatFloatButton from './components/ChatFloatButton.vue'
import ChatPanel from './components/ChatPanel.vue'

const chatStore = useChatStore()

onMounted(async () => {
  // 加载 Bot 配置
  const result = await loadBotConfig()
  if (result.success && result.bot) {
    chatStore.setBotConfig(result.bot)
  }
})
</script>

<style scoped>
.chat-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s;
  z-index: 999;
}

.chat-overlay.show {
  opacity: 1;
  visibility: visible;
}
</style>
