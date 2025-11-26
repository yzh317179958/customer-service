<script setup lang="ts">
import { computed } from 'vue'
import type { Device } from '@/types'

const props = defineProps<{
  devices: Device[]
  loading?: boolean
}>()

// 格式化日期
const formatDate = (timestamp: number): string => {
  return new Date(timestamp * 1000).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

// 电池健康度颜色
const getBatteryHealthColor = (health: number): string => {
  if (health >= 80) return '#10B981'  // 绿色
  if (health >= 50) return '#F59E0B'  // 橙色
  return '#EF4444'  // 红色
}

// 固件更新状态
const getFirmwareStatus = (updateAvailable: boolean): { label: string; color: string } => {
  if (updateAvailable) {
    return { label: '有更新', color: '#F59E0B' }
  }
  return { label: '最新', color: '#10B981' }
}

// 保修状态
const getWarrantyStatus = (expiresAt?: number): { label: string; color: string } => {
  if (!expiresAt) {
    return { label: '未注册', color: '#9CA3AF' }
  }

  const now = Date.now() / 1000
  const daysRemaining = Math.floor((expiresAt - now) / 86400)

  if (daysRemaining < 0) {
    return { label: '已过期', color: '#EF4444' }
  }
  if (daysRemaining < 30) {
    return { label: `剩余${daysRemaining}天`, color: '#F59E0B' }
  }
  return { label: '有效', color: '#10B981' }
}
</script>

<template>
  <div class="device-info">
    <!-- Loading 状态 -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>加载设备信息...</span>
    </div>

    <!-- 无设备 -->
    <div v-else-if="!devices || devices.length === 0" class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect>
        <line x1="12" y1="18" x2="12.01" y2="18"></line>
      </svg>
      <p>暂无设备记录</p>
    </div>

    <!-- 设备列表 -->
    <div v-else class="devices-container">
      <div v-for="device in devices" :key="device.vin" class="device-card">
        <!-- 设备头部 -->
        <div class="device-header">
          <div class="device-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
            </svg>
            <div>
              <div class="device-name">{{ device.product_name }}</div>
              <div class="device-vin">VIN: {{ device.vin }}</div>
            </div>
          </div>
          <div v-if="device.activation_date" class="activation-date">
            激活于 {{ formatDate(device.activation_date) }}
          </div>
        </div>

        <!-- 电池信息 -->
        <div v-if="device.battery" class="section">
          <div class="section-header">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="1" y="6" width="18" height="12" rx="2" ry="2"></rect>
              <line x1="23" y1="13" x2="23" y2="11"></line>
            </svg>
            <span class="section-title">电池信息</span>
          </div>
          <div class="section-content">
            <div class="info-row">
              <span class="label">型号</span>
              <span class="value">{{ device.battery.model }}</span>
            </div>
            <div class="info-row">
              <span class="label">容量</span>
              <span class="value">{{ device.battery.capacity }}</span>
            </div>
            <div class="info-row">
              <span class="label">可拆卸</span>
              <span class="value">{{ device.battery.removable ? '是' : '否' }}</span>
            </div>
            <div class="info-row">
              <span class="label">序列号</span>
              <span class="value monospace">{{ device.battery.serial_number }}</span>
            </div>
            <div v-if="device.battery.cycles !== undefined" class="info-row">
              <span class="label">充电次数</span>
              <span class="value">{{ device.battery.cycles }} 次</span>
            </div>
            <div v-if="device.battery.health_percent !== undefined" class="info-row">
              <span class="label">健康度</span>
              <div class="battery-health">
                <div class="health-bar-bg">
                  <div
                    class="health-bar-fill"
                    :style="{
                      width: `${device.battery.health_percent}%`,
                      backgroundColor: getBatteryHealthColor(device.battery.health_percent)
                    }"
                  ></div>
                </div>
                <span
                  class="health-percent"
                  :style="{ color: getBatteryHealthColor(device.battery.health_percent) }"
                >
                  {{ device.battery.health_percent }}%
                </span>
              </div>
            </div>
            <div v-if="device.battery.warranty_until" class="info-row">
              <span class="label">保修期至</span>
              <span class="value">{{ formatDate(device.battery.warranty_until) }}</span>
            </div>
          </div>
        </div>

        <!-- 电机信息 -->
        <div v-if="device.motor" class="section">
          <div class="section-header">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <polygon points="10 8 16 12 10 16 10 8"></polygon>
            </svg>
            <span class="section-title">电机信息</span>
          </div>
          <div class="section-content">
            <div class="info-row">
              <span class="label">型号</span>
              <span class="value">{{ device.motor.model }}</span>
            </div>
            <div class="info-row">
              <span class="label">功率</span>
              <span class="value">{{ device.motor.power }}</span>
            </div>
            <div class="info-row">
              <span class="label">位置</span>
              <span class="value">{{ device.motor.location }}</span>
            </div>
            <div v-if="device.motor.torque" class="info-row">
              <span class="label">扭矩</span>
              <span class="value">{{ device.motor.torque }}</span>
            </div>
          </div>
        </div>

        <!-- 固件信息 -->
        <div v-if="device.firmware" class="section">
          <div class="section-header">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
              <polyline points="13 2 13 9 20 9"></polyline>
            </svg>
            <span class="section-title">固件信息</span>
            <span
              class="status-badge"
              :style="{ backgroundColor: getFirmwareStatus(device.firmware.update_available).color }"
            >
              {{ getFirmwareStatus(device.firmware.update_available).label }}
            </span>
          </div>
          <div class="section-content">
            <div class="info-row">
              <span class="label">当前版本</span>
              <span class="value monospace">{{ device.firmware.version }}</span>
            </div>
            <div v-if="device.firmware.release_date" class="info-row">
              <span class="label">发布日期</span>
              <span class="value">{{ formatDate(device.firmware.release_date) }}</span>
            </div>
            <div v-if="device.firmware.update_available && device.firmware.latest_version" class="info-row highlight">
              <span class="label">最新版本</span>
              <span class="value monospace">{{ device.firmware.latest_version }}</span>
            </div>
          </div>
        </div>

        <!-- 保修信息 -->
        <div v-if="device.warranty" class="section">
          <div class="section-header">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
            </svg>
            <span class="section-title">保修信息</span>
            <span
              class="status-badge"
              :style="{ backgroundColor: getWarrantyStatus(device.warranty.expires_at).color }"
            >
              {{ getWarrantyStatus(device.warranty.expires_at).label }}
            </span>
          </div>
          <div class="section-content">
            <div class="info-row">
              <span class="label">车架</span>
              <span class="value">{{ device.warranty.frame }}</span>
            </div>
            <div class="info-row">
              <span class="label">电机</span>
              <span class="value">{{ device.warranty.motor }}</span>
            </div>
            <div class="info-row">
              <span class="label">电池</span>
              <span class="value">{{ device.warranty.battery }}</span>
            </div>
            <div v-if="device.warranty.expires_at" class="info-row">
              <span class="label">到期日期</span>
              <span class="value">{{ formatDate(device.warranty.expires_at) }}</span>
            </div>
            <div v-if="device.warranty.registration_status" class="info-row">
              <span class="label">注册状态</span>
              <span class="value">{{ device.warranty.registration_status }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.device-info {
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

.devices-container {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.device-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.device-header {
  padding: 14px 16px;
  background: #f7fafc;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.device-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.device-title svg {
  color: #4ECDC4;
  flex-shrink: 0;
}

.device-name {
  font-size: 15px;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 4px;
}

.device-vin {
  font-size: 11px;
  font-family: monospace;
  color: #718096;
}

.activation-date {
  font-size: 11px;
  color: #718096;
}

.section {
  border-bottom: 1px solid #f0f0f0;
}

.section:last-child {
  border-bottom: none;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fafafa;
}

.section-header svg {
  color: #4ECDC4;
  flex-shrink: 0;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #2d3748;
  flex: 1;
}

.status-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  color: white;
}

.section-content {
  padding: 12px 16px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  font-size: 13px;
}

.info-row:not(:last-child) {
  border-bottom: 1px solid #f7fafc;
}

.label {
  color: #718096;
  flex-shrink: 0;
}

.value {
  color: #2d3748;
  font-weight: 500;
  text-align: right;
}

.value.monospace {
  font-family: monospace;
  font-size: 12px;
}

.battery-health {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  justify-content: flex-end;
}

.health-bar-bg {
  width: 100px;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.health-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease, background-color 0.3s ease;
}

.health-percent {
  font-weight: 600;
  font-size: 12px;
  min-width: 40px;
  text-align: right;
}

.info-row.highlight {
  background: #fef3c7;
  margin: 0 -16px;
  padding: 8px 16px;
}
</style>
