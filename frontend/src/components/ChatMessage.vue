<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import type { Message } from '@/types'
import { useChatStore } from '@/stores/chatStore'

interface Props {
  message: Message
}

const props = defineProps<Props>()
const chatStore = useChatStore()

// Configure marked for rendering markdown
marked.setOptions({
  breaks: true,
  gfm: true,
})

// 判断消息类型
const isUser = computed(() => props.message.role === 'user')
const isAgent = computed(() => props.message.role === 'agent')
const isSystem = computed(() => props.message.role === 'system')
const isDivider = computed(() => (props.message as any).isDivider === true)

const formattedTime = computed(() => {
  const date = new Date(props.message.timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
})

/**
 * 将 [PRODUCT]...[/PRODUCT] 标记转换为商品卡片 HTML
 * 格式：[PRODUCT]图片URL|商品名称|数量|价格|状态|承运商|运单号|追踪链接[/PRODUCT]
 */
function transformProductCards(content: string): string {
  const productRegex = /\[PRODUCT\](.*?)\[\/PRODUCT\]/g

  return content.replace(productRegex, (match, productData) => {
    const fields = productData.split('|')
    const [
      imageUrl = '',
      name = '',
      quantity = '',
      price = '',
      status = '',
      carrier = '',
      trackingNumber = '',
      trackingUrl = ''
    ] = fields

    // 判断语言（根据状态字段 - 支持更多中文状态词）
    const isChinese = status.includes('发货') || status.includes('待') ||
                      status.includes('送达') || status.includes('运输') ||
                      status.includes('处理') || status.includes('失败')
    const trackText = isChinese ? '追踪' : 'Track'
    const qtyLabel = isChinese ? '数量' : 'Qty'
    const carrierLabel = isChinese ? '承运商' : 'Carrier'
    const trackingLabel = isChinese ? '运单号' : 'Tracking'
    const trackingTitle = isChinese ? '物流追踪' : 'Shipping Info'

    // 状态样式 - 支持多种物流状态
    // 状态判断优先级：退款状态 > 支付状态 > 已生效 > 已收货 > 运输中 > 已发货 > 待发货
    const statusLower = status.toLowerCase()

    // 退款相关状态 (最高优先级)
    const isReturned = status.includes('退货退款') ||
                       statusLower.includes('returned')
    const isRefunded = (status.includes('退款') && !status.includes('退货')) ||
                       (statusLower.includes('refund') && !statusLower.includes('returned'))
    const isCancelled = status.includes('已取消') ||
                        statusLower.includes('cancelled')

    // 支付相关状态
    const isPaymentPending = (status.includes('待支付') || status.includes('待付款')) ||
                             (statusLower.includes('payment') && statusLower.includes('pending'))
    const isVoided = status.includes('作废') ||
                     statusLower.includes('void')

    // 已生效状态 (服务类商品)
    const isActive = status.includes('已生效') ||
                     statusLower.includes('active')

    // 已收货状态 (delivery_status=success)
    const isReceived = status.includes('已收货') ||
                       statusLower.includes('received') ||
                       (statusLower.includes('success') && !statusLower.includes('active'))

    // 运输中状态
    const isInTransit = status.includes('运输中') ||
                        status.includes('派送中') ||
                        statusLower.includes('in transit') ||
                        statusLower.includes('out for delivery')

    // 已发货状态
    const isShipped = status.includes('已发货') ||
                      statusLower.includes('shipped')

    // 投递失败状态
    const isFailed = status.includes('投递失败') ||
                     statusLower.includes('delivery fail')

    // 确定状态类和图标
    let statusClass = 'pending'  // 默认待发货
    let statusIcon = '⏳'

    if (isReturned) {
      statusClass = 'returned'
      statusIcon = '↩'
    } else if (isRefunded) {
      statusClass = 'refunded'
      statusIcon = '↩'
    } else if (isCancelled) {
      statusClass = 'cancelled'
      statusIcon = '✗'
    } else if (isPaymentPending || isVoided) {
      statusClass = 'payment-pending'
      statusIcon = '⚠'
    } else if (isActive) {
      statusClass = 'active'
      statusIcon = '✓'
    } else if (isReceived) {
      statusClass = 'received'
      statusIcon = '✓'
    } else if (isInTransit) {
      statusClass = 'in-transit'
      statusIcon = '🚚'
    } else if (isShipped) {
      statusClass = 'shipped'
      statusIcon = '📦'
    } else if (isFailed) {
      statusClass = 'failed'
      statusIcon = '✗'
    }

    // 是否有物流信息
    const hasTracking = carrier || trackingNumber || trackingUrl

    // 判断是否为服务类商品（无图片的增值服务）
    const isServiceProduct = !imageUrl && (
      name.toLowerCase().includes('worry-free') ||
      name.toLowerCase().includes('purchase') ||
      name.toLowerCase().includes('warranty') ||
      name.toLowerCase().includes('protection') ||
      name.toLowerCase().includes('service')
    )

    // 服务类商品使用盾牌图标
    const serviceIcon = '🛡️'

    // 构建卡片 HTML - 物流区块单行紧凑布局
    return `
      <div class="product-card">
        <div class="product-main">
          <div class="product-image-wrapper ${isServiceProduct ? 'service-product' : ''}">
            ${imageUrl
              ? `<img class="product-img" src="${imageUrl}" alt="${name}" />`
              : (isServiceProduct
                  ? `<div class="service-icon">${serviceIcon}</div>`
                  : '<div class="no-image">📦</div>'
                )
            }
          </div>
          <div class="product-details">
            <div class="product-name">${name}</div>
            <div class="product-meta">
              <span class="product-qty">${qtyLabel}: ${quantity}</span>
              <span class="product-price">${price}</span>
            </div>
            <div class="product-status ${statusClass}">
              <span class="status-icon">${statusIcon}</span>
              <span class="status-text">${status}</span>
            </div>
          </div>
        </div>
        ${hasTracking ? `
          <div class="tracking-section">
            <span class="tracking-icon">🚚</span>
            ${carrier ? `<span class="tracking-carrier-text">${carrier}</span>` : ''}
            ${carrier && trackingNumber ? `<span class="tracking-sep">·</span>` : ''}
            ${trackingNumber ? `<span class="tracking-number">${trackingNumber}</span>` : ''}
            ${trackingUrl ? `<a href="${trackingUrl}" target="_blank" class="tracking-link"><span class="link-icon">↗</span>${trackText}</a>` : ''}
          </div>
        ` : ''}
      </div>
    `
  })
}

const renderedContent = computed(() => {
  if (isUser.value) {
    return props.message.content
  }

  // 1. 先转换商品卡片标记
  let content = props.message.content
  const hasProductCards = content.includes('[PRODUCT]')

  if (hasProductCards) {
    // 先将 [PRODUCT] 标记替换为占位符，避免被 marked 处理
    const productMatches: string[] = []
    content = content.replace(/\[PRODUCT\](.*?)\[\/PRODUCT\]/g, (match) => {
      productMatches.push(match)
      return `<!--PRODUCT_PLACEHOLDER_${productMatches.length - 1}-->`
    })

    // 2. 渲染 Markdown
    content = marked.parse(content) as string

    // 3. 将占位符替换为商品卡片 HTML
    productMatches.forEach((productMatch, index) => {
      const cardHtml = transformProductCards(productMatch)
      content = content.replace(`<!--PRODUCT_PLACEHOLDER_${index}-->`, cardHtml)
    })

    return content
  }

  // 普通 Markdown 渲染
  return marked.parse(props.message.content)
})

// 头像内容
const avatarContent = computed(() => {
  if (isUser.value) {
    return 'You'
  }
  if (isAgent.value) {
    return '👤'  // 人工客服图标
  }
  return chatStore.botConfig.name.charAt(0)
})

// 发送者名称
const senderName = computed(() => {
  if (isUser.value) {
    return 'You'
  }
  if (isAgent.value) {
    return props.message.agent_info?.name || 'Agent'
  }
  return chatStore.botConfig.name
})
</script>

<template>
  <!-- System message (包括分隔线) -->
  <div v-if="isSystem || isDivider" class="system-message">
    <div class="system-divider"></div>
    <span class="system-text">{{ message.content }}</span>
    <div class="system-divider"></div>
  </div>

  <!-- Normal message (用户、AI、人工) -->
  <div v-else class="message" :class="{ user: isUser, bot: !isUser && !isAgent, agent: isAgent }">
    <div class="message-avatar" :class="{ 'agent-avatar': isAgent }">
      <img
        v-if="!isUser && !isAgent"
        src="/fiido2.png"
        :alt="chatStore.botConfig.name"
      >
      <template v-else>{{ avatarContent }}</template>
    </div>
    <div class="message-body">
      <div class="message-header">
        <span class="message-sender" :class="{ 'agent-name': isAgent }">{{ senderName }}</span>
        <span v-if="isAgent" class="agent-badge">Live</span>
        <span class="message-time">{{ formattedTime }}</span>
      </div>
      <div class="message-content" v-if="isUser">
        {{ renderedContent }}
      </div>
      <div class="message-content" v-else v-html="renderedContent"></div>
    </div>
  </div>
</template>

<style scoped>
/* =====================================================
   Fiido Premium Message Component - Nano Banana Style
   - Clean, minimal design
   - Subtle shadows and smooth animations
   - Premium feel with elegant spacing
   ===================================================== */

/* System Message - Minimal Divider */
.system-message {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 0;
  margin: 24px 0;
}

.system-divider {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0, 0, 0, 0.08), transparent);
}

.system-text {
  color: #737373;
  font-size: 12px;
  white-space: nowrap;
  font-weight: 500;
  padding: 8px 16px;
  background: #ffffff;
  border-radius: 20px;
  letter-spacing: 0.01em;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

/* Message Base Styles */
.message {
  margin-bottom: 20px;
  display: flex;
  gap: 14px;
  animation: messageIn 0.4s cubic-bezier(0.23, 1, 0.32, 1);
}

@keyframes messageIn {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  flex-direction: row-reverse;
}

/* Avatar Styles */
.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #525252;
  font-weight: 600;
  font-size: 13px;
  flex-shrink: 0;
  overflow: hidden;
  box-shadow:
    0 4px 12px rgba(0, 0, 0, 0.06),
    0 1px 3px rgba(0, 0, 0, 0.04);
  transition: all 0.35s cubic-bezier(0.23, 1, 0.32, 1);
  padding: 6px;
}

.message-avatar:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
}

.message-avatar img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

/* User Avatar - Dark */
.message.user .message-avatar {
  background: #1a1a1a;
  color: #ffffff;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

/* Agent Avatar - Teal Gradient */
.message-avatar.agent-avatar {
  background: linear-gradient(145deg, #00c4bd 0%, #00a6a0 100%);
  color: #ffffff;
  font-size: 16px;
  box-shadow: 0 4px 16px rgba(0, 166, 160, 0.3);
}

/* Message Body */
.message-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 78%;
  min-width: 0;
}

/* Message Header */
.message-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  padding-left: 4px;
}

.message.user .message-header {
  flex-direction: row-reverse;
  padding-left: 0;
  padding-right: 4px;
}

.message-sender {
  font-weight: 500;
  color: #737373;
  letter-spacing: 0.01em;
}

.message-sender.agent-name {
  font-weight: 600;
  color: #00a6a0;
}

/* Agent Badge */
.agent-badge {
  background: linear-gradient(145deg, #00c4bd 0%, #00a6a0 100%);
  color: #ffffff;
  padding: 3px 12px;
  border-radius: 12px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.02em;
  box-shadow: 0 2px 8px rgba(0, 166, 160, 0.25);
}

.message-time {
  color: #a3a3a3;
  font-size: 11px;
  font-weight: 400;
}

/* Message Content Bubble */
.message-content {
  padding: 14px 18px;
  border-radius: 20px;
  word-wrap: break-word;
  line-height: 1.6;
  font-size: 15px;
  position: relative;
}

/* User Message - Dark */
.message.user .message-content {
  background: #1a1a1a;
  color: #ffffff;
  border-bottom-right-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

/* Bot Message - Clean White */
.message.bot .message-content {
  background: #ffffff;
  color: #1a1a1a;
  border-bottom-left-radius: 6px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

/* Agent Message - Teal Accent */
.message.agent .message-content {
  background: linear-gradient(145deg, rgba(0, 166, 160, 0.06) 0%, rgba(0, 196, 189, 0.02) 100%);
  color: #1a1a1a;
  border-bottom-left-radius: 6px;
  box-shadow: 0 2px 12px rgba(0, 166, 160, 0.08);
  border: 1px solid rgba(0, 166, 160, 0.12);
}

/* Markdown Styles */
.message-content :deep(h1),
.message-content :deep(h2),
.message-content :deep(h3) {
  margin-top: 14px;
  margin-bottom: 10px;
  font-weight: 600;
  color: inherit;
}

.message-content :deep(h3) {
  font-size: 1em;
}

.message-content :deep(p) {
  margin: 8px 0;
}

.message-content :deep(ul),
.message-content :deep(ol) {
  margin: 10px 0;
  padding-left: 22px;
}

.message-content :deep(li) {
  margin: 5px 0;
}

.message-content :deep(strong) {
  font-weight: 600;
}

.message.user .message-content :deep(strong) {
  color: #ffffff;
}

/* Links - Teal Accent */
.message-content :deep(a) {
  color: #00a6a0;
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: all 0.25s ease;
}

.message-content :deep(a:hover) {
  color: #00c4bd;
  border-bottom-color: #00c4bd;
}

.message.user .message-content :deep(a) {
  color: rgba(255, 255, 255, 0.85);
  border-bottom-color: rgba(255, 255, 255, 0.3);
}

.message.user .message-content :deep(a:hover) {
  color: #ffffff;
  border-bottom-color: #ffffff;
}

/* Code Blocks */
.message-content :deep(code) {
  background: rgba(0, 0, 0, 0.04);
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 0.9em;
  font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
}

.message.user .message-content :deep(code) {
  background: rgba(255, 255, 255, 0.12);
}

/* Product Images - Premium Style */
.message-content :deep(img) {
  max-width: 110px;
  max-height: 110px;
  width: auto;
  height: auto;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  object-fit: cover;
  display: inline-block;
  vertical-align: middle;
  margin: 8px 12px 8px 0;
  transition: all 0.35s cubic-bezier(0.23, 1, 0.32, 1);
  background: #ffffff;
}

.message-content :deep(img:hover) {
  transform: scale(1.1) translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
}

/* =====================================================
   Order Table - Premium E-commerce Style
   - 高级感、易读性、用户体验优先
   - 商品名称完整显示，无省略号
   - 物流行特殊样式突出显示
   ===================================================== */

/* Table Container */
.message-content :deep(table) {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  margin: 16px 0;
  font-size: 14px;
  border-radius: 16px;
  overflow: hidden;
  box-shadow:
    0 4px 20px rgba(0, 0, 0, 0.06),
    0 1px 3px rgba(0, 0, 0, 0.03);
  background: #ffffff;
  /* 关键：移除 table-layout: fixed，允许内容自适应 */
}

/* Table Header */
.message-content :deep(th) {
  background: linear-gradient(180deg, #f8f9fa 0%, #f3f4f6 100%);
  font-weight: 600;
  color: #374151;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 14px 16px;
  border-bottom: 2px solid #e5e7eb;
  white-space: nowrap;
}

/* Table Cells */
.message-content :deep(td) {
  padding: 16px;
  border-bottom: 1px solid #f3f4f6;
  vertical-align: middle;
  color: #1f2937;
  line-height: 1.5;
  /* 允许换行，完整显示内容 */
  word-break: break-word;
}

/* 最后一行无边框 */
.message-content :deep(tr:last-child td) {
  border-bottom: none;
}

/* 商品行悬停效果 */
.message-content :deep(tbody tr:hover td) {
  background: linear-gradient(180deg, #fafbfc 0%, #f8f9fa 100%);
}

/* ===== 列样式定义 ===== */

/* 第1列：商品名称 - 最重要，完整显示 */
.message-content :deep(th:first-child),
.message-content :deep(td:first-child) {
  min-width: 200px;
  max-width: 320px;
  text-align: left;
}

.message-content :deep(td:first-child) {
  font-weight: 500;
  color: #111827;
}

/* 商品名称加粗样式 */
.message-content :deep(td:first-child strong) {
  font-weight: 600;
  color: #111827;
  display: inline;
}

/* 第2列：数量 - 居中紧凑 */
.message-content :deep(th:nth-child(2)),
.message-content :deep(td:nth-child(2)) {
  text-align: center;
  width: 60px;
  min-width: 60px;
  color: #6b7280;
  font-weight: 500;
}

/* 第3列：价格 - 右对齐，高亮显示 */
.message-content :deep(th:nth-child(3)),
.message-content :deep(td:nth-child(3)) {
  text-align: right;
  min-width: 100px;
  white-space: nowrap;
}

.message-content :deep(td:nth-child(3)) {
  font-weight: 700;
  color: #059669;
  font-size: 15px;
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* 第4列：状态/追踪 - 居中 */
.message-content :deep(th:nth-child(4)),
.message-content :deep(td:nth-child(4)) {
  text-align: center;
  min-width: 100px;
}

.message-content :deep(td:nth-child(4)) {
  font-size: 13px;
  font-weight: 500;
}

/* ===== 商品图片样式 ===== */
.message-content :deep(table img) {
  width: 56px;
  height: 56px;
  min-width: 56px;
  object-fit: cover;
  border-radius: 10px;
  margin-right: 12px;
  vertical-align: middle;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  background: #f9fafb;
}

.message-content :deep(table img:hover) {
  transform: scale(1.08);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
}

/* ===== 物流信息行特殊样式 ===== */
/* 以 ↳ 开头的行 - 物流追踪信息 */
.message-content :deep(tr td:first-child) {
  position: relative;
}

/* 物流行整体样式 - 通过检测 ↳ 符号 */
.message-content :deep(tbody tr:has(td:first-child:not(:empty))) td {
  transition: background 0.15s ease;
}

/* ===== 状态标签样式 ===== */

/* 已发货状态 - 绿色 */
.message-content :deep(td:nth-child(4):has(✓)),
.message-content :deep(td:last-child) {
  color: #059669;
}

/* 追踪链接样式 */
.message-content :deep(table a) {
  color: #0891b2;
  text-decoration: none;
  font-weight: 600;
  padding: 6px 12px;
  background: linear-gradient(135deg, #ecfeff 0%, #e0f2fe 100%);
  border-radius: 8px;
  display: inline-block;
  transition: all 0.2s ease;
  font-size: 12px;
  border: 1px solid #cffafe;
}

.message-content :deep(table a:hover) {
  background: linear-gradient(135deg, #cffafe 0%, #bae6fd 100%);
  color: #0e7490;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(8, 145, 178, 0.2);
}

/* ===== 斑马纹效果（可选，提升可读性） ===== */
.message-content :deep(tbody tr:nth-child(4n+3) td),
.message-content :deep(tbody tr:nth-child(4n+4) td) {
  background: #fafbfc;
}

.message-content :deep(tbody tr:nth-child(4n+3):hover td),
.message-content :deep(tbody tr:nth-child(4n+4):hover td) {
  background: #f3f4f6;
}

/* =====================================================
   Product Card - Premium E-commerce Style v2
   高级感商品卡片 - 独立物流追踪区块
   ===================================================== */

/* 卡片容器 */
.message-content :deep(.product-card) {
  display: flex;
  flex-direction: column;
  margin: 12px 0;
  background: #ffffff;
  border-radius: 16px;
  box-shadow:
    0 2px 12px rgba(0, 0, 0, 0.06),
    0 1px 4px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.06);
  overflow: hidden;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.message-content :deep(.product-card:hover) {
  box-shadow:
    0 8px 28px rgba(0, 0, 0, 0.1),
    0 4px 12px rgba(0, 0, 0, 0.06);
  transform: translateY(-2px);
  border-color: rgba(0, 166, 160, 0.2);
}

/* 商品主体区域（图片+信息）*/
.message-content :deep(.product-main) {
  display: flex;
  gap: 14px;
  padding: 14px;
  align-items: flex-start;
}

/* 商品图片容器 - 纯白背景，居中显示 */
.message-content :deep(.product-image-wrapper) {
  flex: 0 0 72px;
  width: 72px;
  height: 72px;
  border-radius: 10px;
  overflow: hidden;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  box-sizing: border-box;
}

/* 商品图片 - 完全居中显示 */
.message-content :deep(.product-img) {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
  object-position: center center;
  display: block;
  margin: auto;
  transition: transform 0.3s ease;
}

.message-content :deep(.product-card:hover .product-img) {
  transform: scale(1.05);
}

.message-content :deep(.no-image) {
  font-size: 28px;
  color: #9ca3af;
}

/* 服务类商品（Worry-Free Purchase 等）- 轻柔风格 */
.message-content :deep(.product-image-wrapper.service-product) {
  background: #fafafa;
  border: 1px dashed #e5e7eb;
}

.message-content :deep(.service-icon) {
  font-size: 28px;
  opacity: 0.85;
}

/* 商品详情 */
.message-content :deep(.product-details) {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* 商品名称 - 完整显示 */
.message-content :deep(.product-name) {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
  line-height: 1.4;
  word-break: break-word;
}

/* 商品元信息（数量+价格）- 强制一行显示 */
.message-content :deep(.product-meta) {
  display: flex;
  align-items: center;
  gap: 12px;
  white-space: nowrap;
}

.message-content :deep(.product-qty) {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

.message-content :deep(.product-price) {
  font-size: 16px;
  font-weight: 700;
  color: #059669;
  font-family: -apple-system, BlinkMacSystemFont, sans-serif;
}

/* 状态标签 */
.message-content :deep(.product-status) {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  width: fit-content;
}

/* 已收货 - 绿色 */
.message-content :deep(.product-status.received) {
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  color: #059669;
}

/* 已生效 - 绿色（服务类商品） */
.message-content :deep(.product-status.active) {
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  color: #059669;
}

/* 运输中 - 蓝色 */
.message-content :deep(.product-status.in-transit) {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  color: #2563eb;
}

/* 已发货 - 青色 */
.message-content :deep(.product-status.shipped) {
  background: linear-gradient(135deg, #ecfeff 0%, #cffafe 100%);
  color: #0891b2;
}

/* 待发货/处理中 - 黄色 */
.message-content :deep(.product-status.pending) {
  background: linear-gradient(135deg, #fefce8 0%, #fef3c7 100%);
  color: #d97706;
}

/* 投递失败 - 红色 */
.message-content :deep(.product-status.failed) {
  background: linear-gradient(135deg, #fef2f2 0%, #fecaca 100%);
  color: #dc2626;
}

/* 已退款 - 灰色 */
.message-content :deep(.product-status.refunded) {
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  color: #6b7280;
}

/* 已退货退款 - 灰紫色 */
.message-content :deep(.product-status.returned) {
  background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
  color: #7c3aed;
}

/* 已取消 - 浅灰色 */
.message-content :deep(.product-status.cancelled) {
  background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
  color: #9ca3af;
}

/* 待支付/已作废 - 橙色警告 */
.message-content :deep(.product-status.payment-pending) {
  background: linear-gradient(135deg, #fff7ed 0%, #fed7aa 100%);
  color: #c2410c;
}

.message-content :deep(.product-status .status-icon) {
  font-size: 12px;
}

/* ===== 物流追踪区块 - 单行紧凑布局 ===== */
.message-content :deep(.tracking-section) {
  display: flex;
  align-items: center;
  gap: 4px;
  background: #f8fafc;
  border-top: 1px solid rgba(0, 0, 0, 0.04);
  padding: 6px 12px;
  flex-wrap: nowrap;
}

.message-content :deep(.tracking-icon) {
  font-size: 11px;
  flex-shrink: 0;
}

.message-content :deep(.tracking-carrier-text) {
  font-size: 10px;
  color: #64748b;
  font-weight: 500;
  white-space: nowrap;
}

.message-content :deep(.tracking-sep) {
  color: #cbd5e1;
  font-size: 9px;
}

/* 运单号 - 紧凑字体，完整显示 */
.message-content :deep(.tracking-number) {
  font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
  font-size: 9px;
  font-weight: 500;
  color: #64748b;
  letter-spacing: -0.02em;
  white-space: nowrap;
}

/* 追踪链接 - 迷你按钮 + 微光动效 */
.message-content :deep(.tracking-link) {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  margin-left: auto;
  font-size: 9px;
  font-weight: 500;
  color: #0891b2;
  text-decoration: none;
  padding: 2px 6px;
  background: linear-gradient(135deg, #f0fdfa 0%, #e0f7f6 100%);
  border-radius: 3px;
  border: 1px solid #99f6e4;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
  white-space: nowrap;
  position: relative;
  overflow: hidden;
}

/* 微光扫过动效 */
.message-content :deep(.tracking-link)::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.4) 50%,
    transparent 100%
  );
  animation: shimmer 3s ease-in-out infinite;
}

@keyframes shimmer {
  0% {
    left: -100%;
  }
  50%, 100% {
    left: 100%;
  }
}

.message-content :deep(.tracking-link .link-icon) {
  font-size: 8px;
  font-weight: 600;
  transition: transform 0.2s ease;
}

.message-content :deep(.tracking-link:hover) {
  background: linear-gradient(135deg, #ccfbf1 0%, #a7f3d0 100%);
  color: #0e7490;
  border-color: #5eead4;
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(20, 184, 166, 0.2);
}

.message-content :deep(.tracking-link:hover .link-icon) {
  transform: translate(1px, -1px);
}

.message-content :deep(.tracking-link:active) {
  transform: translateY(0);
  box-shadow: 0 1px 3px rgba(20, 184, 166, 0.15);
}

/* 响应式：小屏幕卡片布局 */
@media (max-width: 480px) {
  .message-content :deep(.product-main) {
    flex-direction: column;
    gap: 12px;
    padding: 14px;
    align-items: center;
    text-align: center;
  }

  .message-content :deep(.product-image-wrapper) {
    width: 100%;
    max-width: 200px;
    height: 140px;
  }

  .message-content :deep(.product-details) {
    align-items: center;
  }

  .message-content :deep(.product-meta) {
    justify-content: center;
  }

  .message-content :deep(.tracking-row) {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}

/* Responsive */
@media (max-width: 768px) {
  .message-body {
    max-width: 85%;
  }

  .message-avatar {
    width: 36px;
    height: 36px;
  }

  .message-content {
    padding: 12px 16px;
    font-size: 14px;
  }
}

/* Reduced Motion */
@media (prefers-reduced-motion: reduce) {
  .message,
  .message-avatar,
  .message-content :deep(img) {
    animation: none;
    transition: none;
  }
}
</style>
