<template>
  <div id="app" :class="{ 'embed-mode': isEmbedMode }">
    <!-- 非嵌入模式：显示完整页面 -->
    <template v-if="!isEmbedMode">
      <AppHeader />
      <HeroSection />
      <ProductsSection />
      <AppFooter />
    </template>

    <!-- 核心聊天组件（始终显示） -->
    <ChatFloatButton />
    <ChatPanel />
    <div class="chat-overlay" :class="{ show: chatStore.isChatOpen }" @click="chatStore.closeChat()"></div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useChatStore } from './stores/chatStore'
import { loadBotConfig } from './api/chat'
import AppHeader from './components/AppHeader.vue'
import HeroSection from './components/HeroSection.vue'
import ProductsSection from './components/ProductsSection.vue'
import AppFooter from './components/AppFooter.vue'
import ChatFloatButton from './components/ChatFloatButton.vue'
import ChatPanel from './components/ChatPanel.vue'

const chatStore = useChatStore()

// 检测是否为嵌入模式（URL 带 ?embed 或 ?embed=true）
const isEmbedMode = ref(new URLSearchParams(window.location.search).has('embed'))

onMounted(async () => {
  // 加载 Bot 配置
  const result = await loadBotConfig()
  if (result.success && result.bot) {
    chatStore.setBotConfig(result.bot)
  }

  // 嵌入模式下设置透明背景（不自动打开聊天，让用户点击按钮打开）
  if (isEmbedMode.value) {
    document.body.classList.add('embed-mode')
    document.documentElement.classList.add('embed-mode')
    // 不自动打开聊天，只显示悬浮按钮
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
  background: rgba(0, 0, 0, 0.2);
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s;
  z-index: 999;
}

.chat-overlay.show {
  opacity: 1;
  visibility: visible;
}

/* 嵌入模式样式：透明背景，只显示聊天组件 */
#app.embed-mode {
  background: transparent;
  min-height: auto;
}

#app.embed-mode .chat-overlay {
  display: none;
}
</style>
