<script setup lang="ts">
import { computed } from 'vue'
import type { Order, OrderStatus, ShippingStatus } from '@/types'

const props = defineProps<{
  orders: Order[]
  loading?: boolean
}>()

// 订单状态显示配置
const orderStatusConfig: Record<OrderStatus, { label: string; color: string; icon: string }> = {
  pending: { label: '待处理', color: '#9CA3AF', icon: '⏳' },
  paid: { label: '已支付', color: '#10B981', icon: '✓' },
  processing: { label: '处理中', color: '#3B82F6', icon: '⚙️' },
  shipped: { label: '已发货', color: '#6366F1', icon: '📦' },
  in_transit: { label: '运输中', color: '#8B5CF6', icon: '🚚' },
  customs: { label: '清关中', color: '#EC4899', icon: '🛃' },
  out_for_delivery: { label: '配送中', color: '#F59E0B', icon: '🚴' },
  delivered: { label: '已送达', color: '#10B981', icon: '✅' },
  cancelled: { label: '已取消', color: '#EF4444', icon: '❌' },
  refunded: { label: '已退款', color: '#F97316', icon: '↩️' }
}

// 物流状态显示配置
const shippingStatusConfig: Record<ShippingStatus, { label: string; color: string }> = {
  pending: { label: '待发货', color: '#9CA3AF' },
  shipped: { label: '已发货', color: '#3B82F6' },
  in_transit: { label: '运输中', color: '#8B5CF6' },
  customs_held: { label: '海关扣留', color: '#EF4444' },
  customs_cleared: { label: '已清关', color: '#10B981' },
  out_for_delivery: { label: '配送中', color: '#F59E0B' },
  delivered: { label: '已送达', color: '#10B981' },
  exception: { label: '异常', color: '#DC2626' }
}

// 格式化金额
const formatAmount = (amount: number, currency: string): string => {
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: currency || 'EUR'
  }).format(amount)
}

// 格式化日期
const formatDate = (timestamp: number): string => {
  return new Date(timestamp * 1000).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

// 格式化日期时间
const formatDateTime = (timestamp: number): string => {
  return new Date(timestamp * 1000).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 获取订单状态配置
const getOrderStatusConfig = (status: OrderStatus) => {
  return orderStatusConfig[status] || { label: status, color: '#9CA3AF', icon: '?' }
}

// 获取物流状态配置
const getShippingStatusConfig = (status: ShippingStatus) => {
  return shippingStatusConfig[status] || { label: status, color: '#9CA3AF' }
}
</script>

<template>
  <div class="order-list">
    <!-- Loading 状态 -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>加载订单信息...</span>
    </div>

    <!-- 无订单 -->
    <div v-else-if="!orders || orders.length === 0" class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="9" cy="21" r="1"></circle>
        <circle cx="20" cy="21" r="1"></circle>
        <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
      </svg>
      <p>暂无订单记录</p>
    </div>

    <!-- 订单列表 -->
    <div v-else class="orders-container">
      <div v-for="order in orders" :key="order.order_id" class="order-card">
        <!-- 订单头部 -->
        <div class="order-header">
          <div class="order-title">
            <span class="order-number">{{ order.order_number }}</span>
            <span class="order-date">{{ formatDate(order.created_at) }}</span>
          </div>
          <div class="order-status" :style="{ backgroundColor: getOrderStatusConfig(order.status).color }">
            <span class="status-icon">{{ getOrderStatusConfig(order.status).icon }}</span>
            <span>{{ getOrderStatusConfig(order.status).label }}</span>
          </div>
        </div>

        <!-- 订单商品 -->
        <div class="order-items">
          <div v-for="item in order.items" :key="item.product_id" class="order-item">
            <div class="item-info">
              <div class="item-name">{{ item.product_name }}</div>
              <div class="item-details">
                <span class="item-sku">SKU: {{ item.sku }}</span>
                <span class="item-color">{{ item.color }}</span>
                <span class="item-qty">x{{ item.quantity }}</span>
              </div>
            </div>
            <div class="item-price">{{ formatAmount(item.price, order.currency) }}</div>
          </div>
        </div>

        <!-- 订单金额 -->
        <div class="order-amounts">
          <div class="amount-row">
            <span class="amount-label">小计</span>
            <span class="amount-value">{{ formatAmount(order.total_amount - (order.shipping_fee || 0) - (order.customs_fee || 0), order.currency) }}</span>
          </div>
          <div v-if="order.discount_amount && order.discount_amount > 0" class="amount-row discount">
            <span class="amount-label">折扣</span>
            <span class="amount-value">-{{ formatAmount(order.discount_amount, order.currency) }}</span>
          </div>
          <div v-if="order.vat_amount && order.vat_amount > 0" class="amount-row">
            <span class="amount-label">VAT</span>
            <span class="amount-value">{{ formatAmount(order.vat_amount, order.currency) }}</span>
          </div>
          <div v-if="order.shipping_fee && order.shipping_fee > 0" class="amount-row">
            <span class="amount-label">运费</span>
            <span class="amount-value">{{ formatAmount(order.shipping_fee, order.currency) }}</span>
          </div>
          <div v-if="order.customs_fee && order.customs_fee > 0" class="amount-row">
            <span class="amount-label">关税</span>
            <span class="amount-value">{{ formatAmount(order.customs_fee, order.currency) }}</span>
          </div>
          <div class="amount-row total">
            <span class="amount-label">总计</span>
            <span class="amount-value">{{ formatAmount(order.total_amount, order.currency) }}</span>
          </div>
        </div>

        <!-- 物流信息 -->
        <div v-if="order.shipping" class="shipping-info">
          <div class="shipping-header">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="1" y="3" width="15" height="13"></rect>
              <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"></polygon>
              <circle cx="5.5" cy="18.5" r="2.5"></circle>
              <circle cx="18.5" cy="18.5" r="2.5"></circle>
            </svg>
            <span class="shipping-title">物流追踪</span>
            <span
              class="shipping-status"
              :style="{ color: getShippingStatusConfig(order.shipping.status).color }"
            >
              {{ getShippingStatusConfig(order.shipping.status).label }}
            </span>
          </div>

          <div class="shipping-details">
            <div class="shipping-row">
              <span class="shipping-label">承运商</span>
              <span class="shipping-value">{{ order.shipping.carrier }}</span>
            </div>
            <div class="shipping-row">
              <span class="shipping-label">追踪号</span>
              <span class="shipping-value tracking">{{ order.shipping.tracking_number }}</span>
            </div>
            <div v-if="order.shipping.estimated_delivery" class="shipping-row">
              <span class="shipping-label">预计送达</span>
              <span class="shipping-value">{{ formatDate(order.shipping.estimated_delivery) }}</span>
            </div>
          </div>

          <!-- 物流里程碑 -->
          <div v-if="order.shipping.milestones && order.shipping.milestones.length > 0" class="milestones">
            <div class="milestone-title">物流轨迹</div>
            <div class="milestone-list">
              <div
                v-for="(milestone, index) in order.shipping.milestones.slice(0, 3)"
                :key="index"
                class="milestone-item"
                :class="{ latest: index === 0 }"
              >
                <div class="milestone-dot"></div>
                <div class="milestone-content">
                  <div class="milestone-time">{{ formatDateTime(milestone.timestamp) }}</div>
                  <div class="milestone-location">{{ milestone.location }}</div>
                  <div class="milestone-desc">{{ milestone.description }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 订单底部信息 -->
        <div class="order-footer">
          <div class="footer-item">
            <span class="footer-label">支付方式</span>
            <span class="footer-value">{{ order.payment_method }}</span>
          </div>
          <div v-if="order.warehouse" class="footer-item">
            <span class="footer-label">发货仓</span>
            <span class="footer-value">{{ order.warehouse }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.order-list {
  height: 100%;
  overflow-y: auto;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: #a0aec0;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e2e8f0;
  border-top-color: #4ECDC4;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state svg {
  margin-bottom: 16px;
  color: #cbd5e0;
}

.orders-container {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.order-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: #f7fafc;
  border-bottom: 1px solid #e2e8f0;
}

.order-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.order-number {
  font-size: 15px;
  font-weight: 600;
  color: #2d3748;
}

.order-date {
  font-size: 12px;
  color: #718096;
}

.order-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
  color: white;
}

.status-icon {
  font-size: 14px;
}

.order-items {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.order-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
}

.order-item:not(:last-child) {
  border-bottom: 1px solid #f7fafc;
}

.item-info {
  flex: 1;
}

.item-name {
  font-size: 14px;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 6px;
}

.item-details {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #718096;
}

.item-sku {
  font-family: monospace;
}

.item-price {
  font-size: 14px;
  font-weight: 600;
  color: #2d3748;
}

.order-amounts {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.amount-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  font-size: 13px;
}

.amount-row.discount .amount-value {
  color: #10B981;
}

.amount-row.total {
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px solid #e2e8f0;
  font-size: 15px;
  font-weight: 700;
}

.amount-label {
  color: #718096;
}

.amount-value {
  color: #2d3748;
  font-weight: 600;
}

.shipping-info {
  padding: 16px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}

.shipping-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.shipping-header svg {
  color: #4ECDC4;
}

.shipping-title {
  font-size: 13px;
  font-weight: 600;
  color: #2d3748;
}

.shipping-status {
  margin-left: auto;
  font-size: 12px;
  font-weight: 600;
}

.shipping-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.shipping-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.shipping-label {
  color: #718096;
}

.shipping-value {
  color: #2d3748;
  font-weight: 500;
}

.shipping-value.tracking {
  font-family: monospace;
  font-size: 11px;
}

.milestones {
  margin-top: 16px;
}

.milestone-title {
  font-size: 12px;
  font-weight: 600;
  color: #718096;
  margin-bottom: 12px;
}

.milestone-list {
  position: relative;
  padding-left: 20px;
}

.milestone-list::before {
  content: '';
  position: absolute;
  left: 6px;
  top: 8px;
  bottom: 8px;
  width: 2px;
  background: #e2e8f0;
}

.milestone-item {
  position: relative;
  padding-bottom: 16px;
}

.milestone-item:last-child {
  padding-bottom: 0;
}

.milestone-dot {
  position: absolute;
  left: -18px;
  top: 4px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #cbd5e0;
  border: 2px solid white;
}

.milestone-item.latest .milestone-dot {
  background: #4ECDC4;
  box-shadow: 0 0 0 4px rgba(78, 205, 196, 0.2);
}

.milestone-content {
  font-size: 12px;
}

.milestone-time {
  color: #718096;
  margin-bottom: 2px;
}

.milestone-location {
  color: #2d3748;
  font-weight: 600;
  margin-bottom: 2px;
}

.milestone-desc {
  color: #718096;
}

.order-footer {
  display: flex;
  gap: 24px;
  padding: 12px 16px;
  background: #f7fafc;
}

.footer-item {
  display: flex;
  gap: 8px;
  font-size: 12px;
}

.footer-label {
  color: #718096;
}

.footer-value {
  color: #2d3748;
  font-weight: 500;
}
</style>
