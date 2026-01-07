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

    <!-- 遮罩层：嵌入模式下隐藏 -->
    <div v-if="!isEmbedMode" class="chat-overlay" :class="{ show: chatStore.isChatOpen }" @click="chatStore.closeChat()"></div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
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

// 向父页面发送 iframe 尺寸信息
function notifyParentIframeSize(isOpen: boolean) {
  if (!isEmbedMode.value) return

  // 检测是否在 iframe 中
  if (window.parent === window) return

  // 固定发送 460px 宽度，移动端适配由父页面嵌入代码处理
  const iframeStyle = isOpen
    ? {
        width: '460px',
        height: '100%',
        maxHeight: '100vh',
        pointerEvents: 'auto'
      }
    : {
        width: '100px',
        height: '100px',
        maxHeight: '100px',
        pointerEvents: 'auto'
      }

  window.parent.postMessage({
    type: 'fiido-chat-state',
    isOpen,
    iframeStyle
  }, '*')
}

// 监听聊天面板状态变化
watch(() => chatStore.isChatOpen, (isOpen) => {
  notifyParentIframeSize(isOpen)
})

onMounted(async () => {
  // 嵌入模式下设置透明背景
  if (isEmbedMode.value) {
    document.body.classList.add('embed-mode')
    document.documentElement.classList.add('embed-mode')

    // 初始化时通知父页面（聊天关闭状态）
    notifyParentIframeSize(false)
  }

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
</style>
