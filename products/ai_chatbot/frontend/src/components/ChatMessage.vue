<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { marked } from 'marked'
import type { Message } from '@/types'
import { useChatStore } from '@/stores/chatStore'

interface Props {
  message: Message
}

const props = defineProps<Props>()
const chatStore = useChatStore()

// ============ 物流时间线状态管理 ============

interface TrackingEvent {
  timestamp: string | null
  status: string | null
  status_zh: string | null
  location: string | null
  description: string | null
}

interface TrackingData {
  tracking_number: string
  current_status: string
  current_status_zh: string
  is_delivered: boolean
  is_exception: boolean
  is_pending: boolean
  events: TrackingEvent[]
  loading: boolean
  error: string | null
  message: string | null        // 友好提示信息
  tracking_url: string | null   // 承运商官网链接
}

// 存储每个运单的时间线数据和展开状态
const trackingDataMap = ref<Map<string, TrackingData>>(new Map())
const expandedTrackings = ref<Set<string>>(new Set())

// 记录已自动弹出过承运商官网的运单（防止重复弹出）
const autoPopupTriggered = ref<Set<string>>(new Set())

// 统一 API Base：本地可配置 VITE_API_BASE，生产可留空走同域 /api
const API_BASE = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')

// 获取物流轨迹 API
async function fetchTrackingData(
  trackingNumber: string,
  carrier?: string,
  orderNumber?: string,
  options?: { force?: boolean }
): Promise<void> {
  const existing = trackingDataMap.value.get(trackingNumber)
  if (existing && !options?.force && !existing.error && !existing.is_pending) return

  // 设置加载状态
  trackingDataMap.value.set(trackingNumber, {
    tracking_number: existing?.tracking_number ?? trackingNumber,
    current_status: existing?.current_status ?? '',
    current_status_zh: existing?.current_status_zh ?? '',
    is_delivered: existing?.is_delivered ?? false,
    is_exception: existing?.is_exception ?? false,
    is_pending: existing?.is_pending ?? false,
    events: existing?.events ?? [],
    loading: true,
    error: null,
    message: existing?.message ?? null,
    tracking_url: existing?.tracking_url ?? null
  })

  try {
    // 构建查询参数
    const params = new URLSearchParams()
    if (carrier) params.set('carrier', carrier)
    if (orderNumber) params.set('order_number', orderNumber)
    if (options?.force) params.set('refresh', '1')
    const query = params.toString() ? `?${params.toString()}` : ''
    const url = `${API_BASE}/api/tracking/${encodeURIComponent(trackingNumber)}${query}`
    const response = await fetch(url)

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const data = await response.json()

    trackingDataMap.value.set(trackingNumber, {
      tracking_number: data.tracking_number,
      current_status: data.current_status || '',
      current_status_zh: data.current_status_zh || '',
      is_delivered: data.is_delivered || false,
      is_exception: data.is_exception || false,
      is_pending: data.is_pending || false,
      events: data.events || [],
      loading: false,
      error: null,
      message: data.message || null,
      tracking_url: data.tracking_url || null
    })
  } catch (error) {
    trackingDataMap.value.set(trackingNumber, {
      tracking_number: trackingNumber,
      current_status: '',
      current_status_zh: '',
      is_delivered: false,
      is_exception: false,
      is_pending: false,
      events: [],
      loading: false,
      error: error instanceof Error ? error.message : 'Failed to load',
      message: null,
      tracking_url: null
    })
  }
}

/**
 * 打开承运商官网弹出窗口
 * 使用定制大小的弹出窗口，用户无需离开当前聊天界面
 */
function openCarrierPopup(url: string, trackingNumber: string): void {
  // 防止重复弹出
  if (autoPopupTriggered.value.has(trackingNumber)) {
    return
  }
  autoPopupTriggered.value.add(trackingNumber)

  // 计算窗口位置（屏幕右侧）
  const width = 500
  const height = 700
  const left = window.screenX + window.outerWidth - width - 50
  const top = window.screenY + 100

  // 打开定制大小的弹出窗口
  window.open(
    url,
    `carrier_tracking_${trackingNumber}`,
    `width=${width},height=${height},left=${left},top=${top},scrollbars=yes,resizable=yes`
  )
}

/**
 * 预加载物流数据 - 在订单卡片渲染时调用
 * 静默加载，不显示 loading 状态，用户点击时直接展示
 */
function prefetchTrackingData(
  trackingNumber: string,
  carrier?: string,
  orderNumber?: string,
  shipmentStatus?: string
): void {
  // 如果已有数据且不是错误/pending 状态，跳过
  const existing = trackingDataMap.value.get(trackingNumber)
  if (existing && !existing.error && !existing.is_pending && existing.events.length > 0) {
    return
  }

  // 静默预加载（不设置 loading 状态，避免 UI 闪烁）
  const params = new URLSearchParams()
  if (carrier) params.set('carrier', carrier)
  if (orderNumber) params.set('order_number', orderNumber)
  if (shipmentStatus) {
    params.set('shipment_status', shipmentStatus)
  }
  const query = params.toString() ? `?${params.toString()}` : ''
  const url = `${API_BASE}/api/tracking/${encodeURIComponent(trackingNumber)}${query}`

  // 使用 fetch 静默请求，不阻塞 UI
  fetch(url)
    .then(response => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      return response.json()
    })
    .then(data => {
      trackingDataMap.value.set(trackingNumber, {
        tracking_number: data.tracking_number,
        current_status: data.current_status || '',
        current_status_zh: data.current_status_zh || '',
        is_delivered: data.is_delivered || false,
        is_exception: data.is_exception || false,
        is_pending: data.is_pending || false,
        events: data.events || [],
        loading: false,
        error: null,
        message: data.message || null,
        tracking_url: data.tracking_url || null
      })
    })
    .catch(() => {
      // 预加载失败静默处理，用户点击时会重试
    })
}

// 切换时间线展开/收起
function toggleTracking(trackingNumber: string, carrier?: string, orderNumber?: string, shipmentStatus?: string): void {
  if (expandedTrackings.value.has(trackingNumber)) {
    expandedTrackings.value.delete(trackingNumber)
    updateTimelineDOM(trackingNumber, false)
  } else {
    expandedTrackings.value.add(trackingNumber)
    const existing = trackingDataMap.value.get(trackingNumber)

    // 判断是否有有效的轨迹数据（必须有 events 才算有效）
    const hasValidTrackingData = existing &&
      !existing.loading &&
      !existing.error &&
      existing.events.length > 0

    if (hasValidTrackingData) {
      // 有有效轨迹数据，直接展示，无需弹出官网
      updateTimelineDOM(trackingNumber, true)
    } else {
      // 没有有效数据，需要请求 API
      // 先显示加载状态
      updateTimelineDOM(trackingNumber, true)

      // 请求数据，完成后再决定是否弹出官网
      const force = !!existing && (existing.error !== null || existing.is_pending)
      fetchTrackingData(trackingNumber, carrier, orderNumber, { force }).then(() => {
        // API 请求完成后更新 DOM
        updateTimelineDOM(trackingNumber, true)

        // 检查返回的数据，确定是否需要弹出官网
        const data = trackingDataMap.value.get(trackingNumber)
        if (data && !data.loading && !data.error) {
          // 只有在 17track 确实没有轨迹事件时才弹出官网
          // is_pending 表示后台正在注册，可能稍后会有数据，也弹出让用户先看官网
          // events.length === 0 表示确实没有轨迹
          const noTrackingEvents = data.events.length === 0
          if (noTrackingEvents && data.tracking_url) {
            openCarrierPopup(data.tracking_url, trackingNumber)
          }
        }
      })
    }
  }
  // 触发响应式更新
  expandedTrackings.value = new Set(expandedTrackings.value)
}

// 格式化时间戳
function formatTimestamp(timestamp: string | null): string {
  if (!timestamp) return ''
  try {
    const date = new Date(timestamp)
    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return timestamp
  }
}

// 更新时间线 DOM
function updateTimelineDOM(trackingNumber: string, expanded: boolean): void {
  const containers = document.querySelectorAll(
    `.tracking-timeline-container[data-tracking="${trackingNumber}"]`
  )
  const buttons = document.querySelectorAll(
    `.tracking-expand-btn[data-tracking="${trackingNumber}"]`
  )

  containers.forEach(container => {
    if (!expanded) {
      container.innerHTML = ''
      container.classList.remove('expanded')
    } else {
      container.classList.add('expanded')
      const data = trackingDataMap.value.get(trackingNumber)

      if (!data || data.loading) {
        container.innerHTML = `
          <div class="tracking-timeline loading">
            <div class="timeline-loading">
              <span class="loading-spinner"></span>
              <span>Loading...</span>
            </div>
          </div>
        `
      } else if (data.error) {
        container.innerHTML = `
          <div class="tracking-timeline error">
            <div class="timeline-error">
              <span class="error-icon">⚠️</span>
              <span>No tracking info</span>
            </div>
          </div>
        `
      } else if (data.is_pending) {
        // 运单正在追踪中（后台注册中），显示友好提示
        const pendingMessage = data.message || 'Fetching tracking info, please refresh in 1-2 minutes.'
        const trackUrl = data.tracking_url

        // 从 URL 中提取承运商名称用于显示
        const carrierName = trackUrl?.includes('ups.com') ? 'UPS'
          : trackUrl?.includes('fedex.com') ? 'FedEx'
          : trackUrl?.includes('dhl.com') ? 'DHL'
          : trackUrl?.includes('usps.com') ? 'USPS'
          : 'carrier'

        container.innerHTML = `
          <div class="tracking-timeline pending">
            <div class="timeline-pending">
              <span class="pending-icon">📦</span>
              <span class="pending-message">${pendingMessage}</span>
            </div>
            ${trackUrl ? `<div class="carrier-opened-hint">🔍 Real-time tracking opened in ${carrierName} website</div>` : ''}
          </div>
        `
      } else if (data.events.length === 0) {
        // 轨迹为空，显示友好提示
        const emptyMessage = data.message || 'No tracking events available.'
        const trackUrl = data.tracking_url

        // 从 URL 中提取承运商名称用于显示
        const carrierName = trackUrl?.includes('ups.com') ? 'UPS'
          : trackUrl?.includes('fedex.com') ? 'FedEx'
          : trackUrl?.includes('dhl.com') ? 'DHL'
          : trackUrl?.includes('usps.com') ? 'USPS'
          : 'carrier'

        container.innerHTML = `
          <div class="tracking-timeline empty">
            <div class="timeline-empty">
              <span class="empty-icon">📦</span>
              <span class="empty-message">${emptyMessage}</span>
            </div>
            ${trackUrl ? `<div class="carrier-opened-hint">🔍 Real-time tracking opened in ${carrierName} website</div>` : ''}
          </div>
        `
      } else {
        const eventsHtml = data.events.map((event, index) => `
          <div class="timeline-item ${index === 0 ? 'latest' : ''}">
            <div class="timeline-dot ${index === 0 ? 'active' : ''}"></div>
            <div class="timeline-content">
              <div class="timeline-time">${formatTimestamp(event.timestamp)}</div>
              <div class="timeline-status">${event.status || event.status_zh || event.description || ''}</div>
              ${event.location ? `<div class="timeline-location">📍 ${event.location}</div>` : ''}
            </div>
          </div>
        `).join('')

        container.innerHTML = `
          <div class="tracking-timeline">
            <div class="timeline-header">
              <span class="timeline-status-badge ${data.is_delivered ? 'delivered' : data.is_exception ? 'exception' : 'in-transit'}">
                ${data.current_status || data.current_status_zh || 'In Transit'}
              </span>
              <span class="timeline-count">${data.events.length} events</span>
            </div>
            <div class="timeline-events">
              ${eventsHtml}
            </div>
          </div>
        `
      }
    }
  })

  // 更新按钮状态
  buttons.forEach(btn => {
    const button = btn as HTMLElement
    const expandText = button.dataset.expand || 'Track Details'
    const collapseText = button.dataset.collapse || 'Collapse'
    const icon = button.querySelector('.expand-icon')
    const text = button.querySelector('.expand-text')

    if (icon) icon.textContent = expanded ? '▲' : '▼'
    if (text) text.textContent = expanded ? collapseText : expandText
    button.classList.toggle('expanded', expanded)
  })
}

// 事件委托处理点击
function handleTrackingClick(event: Event): void {
  const target = event.target as HTMLElement
  const button = target.closest('.tracking-expand-btn') as HTMLElement

  if (button) {
    const trackingNumber = button.dataset.tracking
    const carrier = button.dataset.carrier
    const orderNumber = button.dataset.order
    if (trackingNumber) {
      toggleTracking(trackingNumber, carrier, orderNumber)
    }
  }
}

// 挂载/卸载事件监听
onMounted(() => {
  document.addEventListener('click', handleTrackingClick)
  document.addEventListener('click', handleImageClick)
})

onUnmounted(() => {
  document.removeEventListener('click', handleTrackingClick)
  document.removeEventListener('click', handleImageClick)
})

// ============ 图片预览功能 ============
const zoomedImageUrl = ref<string | null>(null)

function handleImageClick(e: MouseEvent) {
  const target = e.target as HTMLElement
  // 检查是否点击了消息内容中的图片
  if (target.tagName === 'IMG' && target.closest('.message-content')) {
    const imgSrc = (target as HTMLImageElement).src
    // 排除产品图片和头像等小图
    if (imgSrc && !target.classList.contains('product-img')) {
      zoomedImageUrl.value = imgSrc
    }
  }
}

function closeImagePreview() {
  zoomedImageUrl.value = null
}

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
 * 从消息内容中提取订单号
 * 匹配格式：订单 UK22080、Order #UK22080、订单号：UK22080 等
 */
function extractOrderNumber(content: string): string | null {
  // 匹配常见订单号格式
  const patterns = [
    /订单\s*[#：:]*\s*([A-Z]{2}\d+)/i,         // 订单 UK22080、订单：UK22080
    /Order\s*[#：:]*\s*([A-Z]{2}\d+)/i,        // Order #UK22080、Order UK22080
    /订单号\s*[：:]*\s*([A-Z]{2}\d+)/i,        // 订单号：UK22080
    /Order\s*Number\s*[：:]*\s*([A-Z]{2}\d+)/i // Order Number: UK22080
  ]

  for (const pattern of patterns) {
    const match = content.match(pattern)
    if (match && match[1]) {
      return match[1]
    }
  }
  return null
}

function extractLatestOrderNumberFromChat(): string | null {
  const messages = chatStore.messages
  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i]
    if (!msg?.content) continue
    const orderNumber = extractOrderNumber(String(msg.content))
    if (orderNumber) return orderNumber
  }
  return null
}

/**
 * 将 [PRODUCT]...[/PRODUCT] 标记转换为商品卡片 HTML
 * 格式：[PRODUCT]图片URL|商品名称|数量|价格|状态|承运商|运单号|追踪链接[/PRODUCT]
 */
function transformProductCards(content: string, orderNumber?: string | null): string {
  const productRegex = /\[PRODUCT\](.*?)\[\/PRODUCT\]/g

  return content.replace(productRegex, (match, productData) => {
    let fields = productData.split('|')

    // 服务类商品关键词（用于检测字段错位）
    const serviceKeywords = ['worry-free', 'warranty', 'protection', 'insurance', 'service', 'purchase', 'seel']

    // 检测字段错位：如果第一个字段包含服务类商品关键词（而非 URL），则说明缺少 imageUrl 字段
    // 正常格式: [PRODUCT]ImageURL|ProductName|Qty|Price|Status|Carrier|TrackingNumber|TrackingURL[/PRODUCT]
    // 错误格式: [PRODUCT]ProductName|Qty|Price|Status|...[/PRODUCT] (缺少 ImageURL)
    const firstField = (fields[0] || '').toLowerCase()
    const isFirstFieldUrl = firstField.startsWith('http') || firstField.startsWith('/') || firstField === ''
    const isFirstFieldServiceProduct = serviceKeywords.some(kw => firstField.includes(kw))

    if (!isFirstFieldUrl && isFirstFieldServiceProduct) {
      // 检测到字段错位，在开头插入空的 imageUrl 字段
      fields = ['', ...fields]
    }

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
                       status.includes('已送达') ||
                       statusLower.includes('received') ||
                       statusLower.includes('delivered') ||
                       (statusLower.includes('success') && !statusLower.includes('active'))

    // 运输中状态 - 支持 in_transit 和 in transit 两种格式
    const isInTransit = status.includes('运输中') ||
                        status.includes('派送中') ||
                        statusLower.includes('in_transit') ||
                        statusLower.includes('in transit') ||
                        statusLower.includes('out_for_delivery') ||
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

    // 服务类商品使用盾牌 SVG 图标（避免 emoji 在某些设备上显示异常）
    const serviceIcon = `<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="#00a6a0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg>`

    // 物流展开按钮文字
    const expandText = isChinese ? '查看物流' : 'Track Details'
    const collapseText = isChinese ? '收起' : 'Collapse'
    const loadingText = isChinese ? '加载中...' : 'Loading...'

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
            <div class="tracking-info">
              <span class="tracking-icon">🚚</span>
              ${carrier ? `<span class="tracking-carrier-text">${carrier}</span>` : ''}
              ${carrier && trackingNumber ? `<span class="tracking-sep">·</span>` : ''}
              ${trackingNumber ? `<span class="tracking-number">${trackingNumber}</span>` : ''}
            </div>
            <div class="tracking-actions">
              ${trackingNumber ? `<button class="tracking-expand-btn" data-tracking="${trackingNumber}" data-carrier="${carrier}" data-order="${orderNumber || ''}" data-expand="${expandText}" data-collapse="${collapseText}" data-loading="${loadingText}"><span class="expand-icon">▼</span><span class="expand-text">${expandText}</span></button>` : ''}
            </div>
          </div>
          ${trackingNumber ? `<div class="tracking-timeline-container" data-tracking="${trackingNumber}" data-carrier="${carrier}"></div>` : ''}
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
    // 提取订单号用于物流查询
    const orderNumber = extractOrderNumber(content) || extractLatestOrderNumberFromChat()

    // 先将 [PRODUCT] 标记替换为占位符，避免被 marked 处理
    const productMatches: string[] = []
    content = content.replace(/\[PRODUCT\](.*?)\[\/PRODUCT\]/g, (match) => {
      productMatches.push(match)
      return `<!--PRODUCT_PLACEHOLDER_${productMatches.length - 1}-->`
    })

    // 2. 渲染 Markdown
    content = marked.parse(content) as string

    // 3. 将占位符替换为商品卡片 HTML，传递订单号
    productMatches.forEach((productMatch, index) => {
      const cardHtml = transformProductCards(productMatch, orderNumber)
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

const isTyping = computed(() => props.message.role === 'assistant' && props.message.isTyping === true)

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

/**
 * 从消息内容中提取所有运单信息并预加载
 * 在消息渲染后自动调用，静默加载物流数据
 */
function prefetchAllTrackingInMessage(): void {
  const content = props.message.content
  if (!content || isUser.value) return

  // 提取所有 [PRODUCT] 标记中的运单号
  const productRegex = /\[PRODUCT\](.*?)\[\/PRODUCT\]/g
  let match: RegExpExecArray | null

  // 提取订单号用于物流查询
  const orderNumber = extractOrderNumber(content) || extractLatestOrderNumberFromChat()

  while ((match = productRegex.exec(content)) !== null) {
    const productData = match[1]
    if (!productData) continue
    const fields = productData.split('|')
    // 字段顺序：图片URL|商品名称|数量|价格|状态|承运商|运单号|追踪链接
    const [, , , , status, carrier, trackingNumber] = fields

    if (trackingNumber && trackingNumber.trim()) {
      // 静默预加载该运单的物流数据
      prefetchTrackingData(
        trackingNumber.trim(),
        carrier?.trim(),
        orderNumber || undefined,
        status?.trim()
      )
    }
  }
}

// 消息渲染后自动预加载物流数据
watch(
  () => props.message.content,
  () => {
    nextTick(() => {
      prefetchAllTrackingInMessage()
    })
  },
  { immediate: true }
)
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
      <div v-else-if="isTyping" class="message-content typing-indicator" aria-label="typing">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
      <div class="message-content" v-else v-html="renderedContent"></div>
    </div>
  </div>

  <!-- 图片预览弹窗 -->
  <Teleport to="body">
    <div v-if="zoomedImageUrl" class="image-preview-overlay" @click="closeImagePreview">
      <div class="image-preview-container" @click.stop>
        <img :src="zoomedImageUrl" alt="Preview" class="image-preview-img" />
        <button class="image-preview-close" @click="closeImagePreview">×</button>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
/* =====================================================
   Fiido Premium Message Component - 统一坐席工作台风格
   - 品牌色: #00a6a0 (fiido)
   - 配色系统: slate 灰色系 + fiido 青绿色
   - 与坐席工作台 UI 保持一致
   ===================================================== */

/* CSS 变量定义 - 与坐席工作台保持一致 */
:root {
  --fiido: #00a6a0;
  --fiido-dark: #008b86;
  --fiido-light: #f0f9f9;
  --fiido-black: #0f172a;
  --fiido-slate: #1e293b;
}

/* System Message - 统一风格 */
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
  color: #64748b;
  font-size: 12px;
  white-space: nowrap;
  font-weight: 500;
  padding: 8px 16px;
  background: #f8fafc;
  border-radius: 20px;
  letter-spacing: 0.01em;
  border: 1px solid #e2e8f0;
}

/* Message Base Styles */
.message {
  margin-bottom: 20px;
  display: flex;
  gap: 14px;
  animation: messageIn 0.4s cubic-bezier(0.23, 1, 0.32, 1);
}

/* Agent Message - Special Entrance Animation */
.message.agent {
  animation: agentMessageIn 0.5s cubic-bezier(0.23, 1, 0.32, 1);
}

@keyframes agentMessageIn {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
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

/* Avatar Styles - 统一风格 */
.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  font-weight: 600;
  font-size: 13px;
  flex-shrink: 0;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.35s cubic-bezier(0.23, 1, 0.32, 1);
  padding: 6px;
  border: 1px solid #e2e8f0;
}

.message-avatar:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.message-avatar img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

/* User Avatar - 深色主题 */
.message.user .message-avatar {
  background: var(--fiido-black, #0f172a);
  color: #ffffff;
  border-color: transparent;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.2);
}

/* Agent Avatar - 简洁样式（与用户头像格式一致，只是颜色不同） */
.message-avatar.agent-avatar {
  background: var(--fiido, #00a6a0);
  color: #ffffff;
  font-size: 15px;
  border-color: transparent;
  box-shadow: 0 2px 8px rgba(0, 166, 160, 0.2);
}

/* Message Body */
.message-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 78%;
  min-width: 0;
}

/* Message Header - 统一风格 */
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
  color: #64748b;
  letter-spacing: 0.01em;
}

.message-sender.agent-name {
  font-weight: 700;
  color: var(--fiido-slate, #1e293b);
  background: linear-gradient(135deg, var(--fiido, #00a6a0) 0%, #00c4bd 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Agent Badge - Premium Glassmorphism Style */
.agent-badge {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #ffffff;
  padding: 3px 10px;
  border-radius: 10px;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  box-shadow:
    0 2px 8px rgba(16, 185, 129, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  position: relative;
  overflow: hidden;
  animation: badgePulse 2s ease-in-out infinite;
}

/* Live Badge Dot Animation */
.agent-badge::before {
  content: '';
  display: inline-block;
  width: 5px;
  height: 5px;
  background: #ffffff;
  border-radius: 50%;
  margin-right: 5px;
  animation: liveDot 1.5s ease-in-out infinite;
}

@keyframes badgePulse {
  0%, 100% {
    box-shadow:
      0 2px 8px rgba(16, 185, 129, 0.35),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
  }
  50% {
    box-shadow:
      0 2px 12px rgba(16, 185, 129, 0.5),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
  }
}

@keyframes liveDot {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(0.8);
  }
}

.message-time {
  color: #94a3b8;
  font-size: 11px;
  font-weight: 400;
}

/* Message Content Bubble - 统一风格 */
.message-content {
  padding: 12px 16px;
  border-radius: 16px;
  word-wrap: break-word;
  line-height: 1.6;
  font-size: 13px;
  position: relative;
  width: fit-content;
  max-width: 100%;
}

/* User Message - 深色主题 */
.message.user .message-content {
  background: var(--fiido-black, #0f172a);
  color: #ffffff;
  border-bottom-right-radius: 4px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.15);
}

/* Bot Message - 白色卡片 */
.message.bot .message-content {
  background: #ffffff;
  color: var(--fiido-slate, #1e293b);
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid #e2e8f0;
}

/* Agent Message - 白色气泡（与用户黑色气泡对比，格式一致） */
.message.agent .message-content {
  background: #ffffff;
  color: var(--fiido-slate, #1e293b);
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
}

/* Agent Message Accent Line - 移除过度装饰 */
.message.agent .message-content::before {
  display: none;
}

/* Agent Message Subtle Glow - 移除过度装饰 */
.message.agent .message-content::after {
  display: none;
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
  margin: 0;
}

/* Typing Indicator - 合并到 bot 占位气泡 */
.typing-indicator {
  display: flex;
  gap: 6px;
  width: fit-content;
}

.typing-dot {
  width: 8px;
  height: 8px;
  background: var(--fiido, #00a6a0);
  border-radius: 50%;
  animation: typingBounce 1.6s infinite;
}

.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typingBounce {
  0%, 60%, 100% {
    opacity: 0.5;
    transform: translateY(0);
  }
  30% {
    opacity: 1;
    transform: translateY(-6px);
  }
}

.message-content :deep(p + p) {
  margin-top: 8px;
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

/* Agent Message Links - 与 Bot 消息链接样式一致 */
.message.agent .message-content :deep(a) {
  color: #00a6a0;
  border-bottom-color: rgba(0, 166, 160, 0.3);
}

.message.agent .message-content :deep(a:hover) {
  color: #00c4bd;
  border-bottom-color: #00c4bd;
}

/* Agent Message Strong Text - 深色文本 */
.message.agent .message-content :deep(strong) {
  color: var(--fiido-slate, #1e293b);
  font-weight: 600;
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

/* Agent Message Code Blocks - 与 Bot 消息代码块样式一致 */
.message.agent .message-content :deep(code) {
  background: rgba(0, 0, 0, 0.04);
  color: var(--fiido-slate, #1e293b);
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

/* ===== 物流追踪区块 - 自适应两行布局 ===== */
.message-content :deep(.tracking-section) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  background: #f8fafc;
  border-top: 1px solid rgba(0, 0, 0, 0.04);
  padding: 8px 12px;
  flex-wrap: wrap;
}

/* 物流信息区域（承运商+运单号）*/
.message-content :deep(.tracking-info) {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
  min-width: 0;
  flex-wrap: wrap;
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

/* 运单号 - 允许换行显示长运单号 */
.message-content :deep(.tracking-number) {
  font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
  font-size: 9px;
  font-weight: 500;
  color: #64748b;
  letter-spacing: -0.02em;
  word-break: break-all;
}

/* 响应式：小屏幕卡片布局 - 仅在非嵌入模式下生效 */
@media (max-width: 480px) {
  html:not(.embed-mode) .message-content :deep(.product-main) {
    flex-direction: column;
    gap: 12px;
    padding: 14px;
    align-items: center;
    text-align: center;
  }

  html:not(.embed-mode) .message-content :deep(.product-image-wrapper) {
    width: 100%;
    max-width: 200px;
    height: 140px;
  }

  html:not(.embed-mode) .message-content :deep(.product-details) {
    align-items: center;
  }

  html:not(.embed-mode) .message-content :deep(.product-meta) {
    justify-content: center;
  }

  html:not(.embed-mode) .message-content :deep(.tracking-row) {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}

/* Responsive - 仅在非嵌入模式下生效 */
@media (max-width: 768px) {
  html:not(.embed-mode) .message-body {
    max-width: 85%;
  }

  html:not(.embed-mode) .message-avatar {
    width: 36px;
    height: 36px;
  }

  html:not(.embed-mode) .message-content {
    padding: 12px 16px;
    font-size: 14px;
  }
}

/* Reduced Motion */
@media (prefers-reduced-motion: reduce) {
  .message,
  .message.agent,
  .message-avatar,
  .message-content :deep(img),
  .agent-badge {
    animation: none;
    transition: none;
  }
}

/* =====================================================
   物流时间线 - 可折叠展示
   ===================================================== */

/* 物流操作区 - 按钮组 */
.message-content :deep(.tracking-actions) {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

/* 展开按钮 */
.message-content :deep(.tracking-expand-btn) {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 9px;
  font-weight: 500;
  color: #0891b2;
  padding: 3px 8px;
  background: linear-gradient(135deg, #f0fdfa 0%, #e0f7f6 100%);
  border-radius: 4px;
  border: 1px solid #99f6e4;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
}

.message-content :deep(.tracking-expand-btn:hover) {
  background: linear-gradient(135deg, #ccfbf1 0%, #a7f3d0 100%);
  color: #0e7490;
  border-color: #5eead4;
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(20, 184, 166, 0.2);
}

.message-content :deep(.tracking-expand-btn.expanded) {
  background: linear-gradient(135deg, #0891b2 0%, #0e7490 100%);
  color: #ffffff;
  border-color: #0891b2;
}

.message-content :deep(.tracking-expand-btn .expand-icon) {
  font-size: 8px;
  transition: transform 0.3s ease;
}

.message-content :deep(.tracking-expand-btn.expanded .expand-icon) {
  transform: rotate(180deg);
}

/* 时间线容器 */
.message-content :deep(.tracking-timeline-container) {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.message-content :deep(.tracking-timeline-container.expanded) {
  max-height: 500px;
}

/* 时间线主体 */
.message-content :deep(.tracking-timeline) {
  background: #f8fafc;
  border-top: 1px solid rgba(0, 0, 0, 0.04);
  padding: 12px;
}

/* 时间线头部 */
.message-content :deep(.timeline-header) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px dashed #e2e8f0;
}

.message-content :deep(.timeline-status-badge) {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
}

.message-content :deep(.timeline-status-badge.in-transit) {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  color: #2563eb;
}

.message-content :deep(.timeline-status-badge.delivered) {
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  color: #059669;
}

.message-content :deep(.timeline-status-badge.exception) {
  background: linear-gradient(135deg, #fef2f2 0%, #fecaca 100%);
  color: #dc2626;
}

.message-content :deep(.timeline-count) {
  font-size: 10px;
  color: #94a3b8;
}

/* 时间线事件列表 */
.message-content :deep(.timeline-events) {
  display: flex;
  flex-direction: column;
  gap: 0;
  max-height: 300px;
  overflow-y: auto;
}

/* 时间线项目 */
.message-content :deep(.timeline-item) {
  display: flex;
  gap: 12px;
  padding: 8px 0;
  position: relative;
}

.message-content :deep(.timeline-item:not(:last-child)::before) {
  content: '';
  position: absolute;
  left: 5px;
  top: 20px;
  bottom: -8px;
  width: 2px;
  background: #e2e8f0;
}

/* 时间线圆点 */
.message-content :deep(.timeline-dot) {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #e2e8f0;
  flex-shrink: 0;
  margin-top: 2px;
  position: relative;
  z-index: 1;
}

.message-content :deep(.timeline-dot.active) {
  background: linear-gradient(135deg, #00a6a0 0%, #00c4bd 100%);
  box-shadow: 0 0 0 3px rgba(0, 166, 160, 0.2);
}

/* 时间线内容 */
.message-content :deep(.timeline-content) {
  flex: 1;
  min-width: 0;
}

.message-content :deep(.timeline-time) {
  font-size: 10px;
  color: #94a3b8;
  margin-bottom: 2px;
}

.message-content :deep(.timeline-status) {
  font-size: 12px;
  color: #334155;
  font-weight: 500;
  line-height: 1.4;
}

.message-content :deep(.timeline-item.latest .timeline-status) {
  color: #0f172a;
  font-weight: 600;
}

.message-content :deep(.timeline-location) {
  font-size: 10px;
  color: #64748b;
  margin-top: 2px;
}

/* 加载状态 */
.message-content :deep(.timeline-loading) {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  color: #64748b;
  font-size: 12px;
}

.message-content :deep(.loading-spinner) {
  width: 14px;
  height: 14px;
  border: 2px solid #e2e8f0;
  border-top-color: #00a6a0;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 错误/空状态/追踪中状态 */
.message-content :deep(.timeline-error),
.message-content :deep(.timeline-empty),
.message-content :deep(.timeline-pending) {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  color: #94a3b8;
  font-size: 12px;
}

.message-content :deep(.timeline-empty > div),
.message-content :deep(.timeline-pending > div) {
  display: flex;
  align-items: center;
  gap: 8px;
}

.message-content :deep(.timeline-pending) {
  color: #60a5fa;
  background: rgba(59, 130, 246, 0.05);
  border-radius: 8px;
}

.message-content :deep(.error-icon),
.message-content :deep(.empty-icon),
.message-content :deep(.pending-icon) {
  font-size: 16px;
}

/* 友好提示消息样式 */
.message-content :deep(.pending-message),
.message-content :deep(.empty-message) {
  line-height: 1.5;
  text-align: center;
}

/* 承运商官网已打开提示 - 简洁样式 */
.message-content :deep(.carrier-opened-hint) {
  margin-top: 10px;
  padding: 8px 12px;
  font-size: 11px;
  font-weight: 500;
  color: #059669;
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  border-radius: 6px;
  border: 1px solid #a7f3d0;
  text-align: center;
}

/* 时间线滚动条美化 */
.message-content :deep(.timeline-events::-webkit-scrollbar) {
  width: 4px;
}

.message-content :deep(.timeline-events::-webkit-scrollbar-track) {
  background: #f1f5f9;
  border-radius: 2px;
}

.message-content :deep(.timeline-events::-webkit-scrollbar-thumb) {
  background: #cbd5e1;
  border-radius: 2px;
}

.message-content :deep(.timeline-events::-webkit-scrollbar-thumb:hover) {
  background: #94a3b8;
}

/* =====================================================
   图片预览弹窗样式
   ===================================================== */
.image-preview-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  cursor: pointer;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.image-preview-container {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
  cursor: default;
  animation: zoomIn 0.25s ease-out;
}

@keyframes zoomIn {
  from {
    transform: scale(0.9);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

.image-preview-img {
  max-width: 90vw;
  max-height: 90vh;
  object-fit: contain;
  border-radius: 12px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.image-preview-close {
  position: absolute;
  top: -40px;
  right: 0;
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.15);
  border: none;
  border-radius: 50%;
  color: white;
  font-size: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.image-preview-close:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: scale(1.1);
}

/* 让消息内容中的图片显示可点击的样式 */
.message-content :deep(img) {
  cursor: pointer;
}
</style>
