// Agent 相关类型
export interface AgentInfo {
  id: string
  name: string
}

export interface LoginRequest {
  agentId: string
  agentName: string
}

// Session 相关类型
export type SessionStatus = 'bot_active' | 'pending_manual' | 'manual_live' | 'after_hours_email' | 'closed'

export interface SessionSummary {
  session_name: string
  status: SessionStatus
  user_profile?: {
    nickname?: string
    vip?: boolean
  }
  updated_at: number
  last_message_preview?: {
    role: string
    content: string
    timestamp: number
  }
  escalation?: {
    reason: string
    trigger_at: number
    waiting_seconds: number
  }
  assigned_agent?: AgentInfo | null
}

export interface SessionListResponse {
  success: boolean
  data: {
    sessions: SessionSummary[]
    total: number
    limit: number
    offset: number
    has_more: boolean
  }
}

// Message 相关类型
export interface Message {
  id: string
  role: 'user' | 'assistant' | 'agent' | 'system'
  content: string
  timestamp: number
  agent_id?: string
  agent_name?: string
}

export interface SessionDetail {
  session_name: string
  conversation_id?: string  // Coze 对话 ID
  status: SessionStatus
  history: Message[]
  escalation?: {
    reason: string
    details: string
    severity: string
    trigger_at: number
  }
  assigned_agent?: AgentInfo | null
  user_profile?: {
    nickname?: string
    vip?: boolean
  }
}

export interface SessionDetailResponse {
  success: boolean
  data: {
    session: SessionDetail
    audit_trail: any[]
  }
}

// API 请求类型
export interface TakeoverRequest {
  agent_id: string
  agent_name: string
}

export interface ReleaseRequest {
  agent_id: string
  reason: string
}

export interface ManualMessageRequest {
  session_name: string
  role: 'agent' | 'user'
  content: string
  agent_info?: {
    agent_id: string
    agent_name: string
  }
}

export interface ManualMessageResponse {
  success: boolean
  data: {
    timestamp: number
  }
}

// ====================
// 管理员功能类型定义 (v3.1.3+)
// ====================

/** 坐席角色 */
export type AgentRole = 'admin' | 'agent'

/** 坐席状态 */
export type AgentStatus = 'online' | 'offline' | 'busy'

/** 完整坐席信息 */
export interface Agent {
  id: string
  username: string
  name: string
  role: AgentRole
  status: AgentStatus
  max_sessions: number
  created_at: number
  last_login: number
  avatar_url?: string
}

/** 创建坐席请求 */
export interface CreateAgentRequest {
  username: string
  password: string
  name: string
  role: AgentRole
  max_sessions?: number
  avatar_url?: string
}

/** 修改坐席请求 */
export interface UpdateAgentRequest {
  name?: string
  role?: AgentRole
  status?: AgentStatus
  max_sessions?: number
  avatar_url?: string
}

/** 修改密码请求 */
export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}

/** 修改资料请求 */
export interface UpdateProfileRequest {
  name?: string
  avatar_url?: string
}

/** 重置密码请求 */
export interface ResetPasswordRequest {
  new_password: string
}

/** 坐席列表响应 */
export interface AgentsListResponse {
  success: boolean
  data: {
    items: Agent[]
    total: number
    page: number
    page_size: number
  }
}

/** 坐席操作响应 */
export interface AgentResponse {
  success: boolean
  agent?: Agent
  message?: string
}

// ====================
// 客户信息与业务上下文类型定义 (v3.2.0+)
// ====================

/** 来源渠道 */
export type SourceChannel = 'shopify_organic' | 'shopify_campaign' | 'amazon' | 'dealer' | 'other'

/** 客户画像 */
export interface CustomerProfile {
  customer_id: string
  name: string
  email: string
  phone: string
  country: string
  city: string
  language_preference: string  // en/de/fr/it/es
  payment_currency: string     // EUR/GBP
  source_channel: SourceChannel
  gdpr_consent: boolean
  marketing_subscribed: boolean
  vip_status?: string
  avatar_url?: string
  created_at: number
}

/** 客户画像响应 */
export interface CustomerProfileResponse {
  success: boolean
  data: CustomerProfile
}

// ====================
// 订单与设备信息类型定义 (v3.2+)
// ====================

/** 订单状态 */
export enum OrderStatus {
  PENDING = 'pending',
  PAID = 'paid',
  PROCESSING = 'processing',
  SHIPPED = 'shipped',
  IN_TRANSIT = 'in_transit',
  CUSTOMS = 'customs',
  OUT_FOR_DELIVERY = 'out_for_delivery',
  DELIVERED = 'delivered',
  CANCELLED = 'cancelled',
  REFUNDED = 'refunded'
}

/** 物流状态 */
export enum ShippingStatus {
  PENDING = 'pending',
  SHIPPED = 'shipped',
  IN_TRANSIT = 'in_transit',
  CUSTOMS_HELD = 'customs_held',
  CUSTOMS_CLEARED = 'customs_cleared',
  OUT_FOR_DELIVERY = 'out_for_delivery',
  DELIVERED = 'delivered',
  EXCEPTION = 'exception'
}

/** 物流节点 */
export interface Milestone {
  timestamp: number
  location: string
  status: string
  description: string
}

/** 物流信息 */
export interface ShippingInfo {
  tracking_number: string
  carrier: string
  status: ShippingStatus
  estimated_delivery?: number
  actual_delivery?: number
  insurance: boolean
  customs_cleared: boolean
  milestones: Milestone[]
}

/** 车辆配置 */
export interface BikeConfig {
  motor_power: string          // 电机功率 (250W/500W)
  battery_capacity: string     // 电池容量 (48V 14.5Ah)
  battery_removable: boolean   // 电池可拆卸
  max_load: string             // 最大承重 (120kg)
  brake_type: string           // 刹车类型 (液压碟刹)
  tire_size: string            // 轮胎规格 (700×40C)
  assist_modes: number         // 辅助模式数量
  firmware_version?: string    // 固件版本
}

/** 订单商品 */
export interface OrderItem {
  product_id: string
  sku: string
  product_name: string        // 产品名称 (C11 Pro)
  category: string            // 车型系列 (C/T/M/N)
  color: string
  quantity: number
  price: number
  configuration?: BikeConfig  // 车辆配置（E-bike专用）
}

/** 订单信息 */
export interface Order {
  order_id: string
  order_number: string        // 显示编号 (#1001)
  status: OrderStatus
  created_at: number
  total_amount: number
  currency: string
  vat_amount?: number
  discount_amount?: number
  shipping_fee?: number
  customs_fee?: number
  payment_method: string
  warehouse?: string
  items: OrderItem[]
  shipping?: ShippingInfo
}

/** 电池信息 */
export interface BatteryInfo {
  model: string
  serial_number: string
  capacity: string            // 容量 (48V 14.5Ah)
  removable: boolean
  cycles?: number             // 充电循环次数
  health_percent?: number     // 健康度百分比
  warranty_until?: number     // 保修期至
}

/** 电机信息 */
export interface MotorInfo {
  model: string
  power: string               // 功率 (250W/500W)
  location: string            // 位置 (中置/后轮)
  torque?: string             // 扭矩 (80Nm)
}

/** 固件信息 */
export interface FirmwareInfo {
  version: string
  release_date?: number
  update_available: boolean
  latest_version?: string
}

/** 保修信息 */
export interface WarrantyInfo {
  frame: string               // 车架保修 (2年)
  motor: string               // 电机保修 (2年)
  battery: string             // 电池保修 (1年)
  expires_at?: number         // 保修到期
  registration_status?: string // 注册状态
}

/** 设备信息 */
export interface Device {
  vin: string                 // 车辆识别码
  product_name: string        // 车型名称
  activation_date?: number    // 激活时间
  battery?: BatteryInfo       // 电池信息
  motor?: MotorInfo           // 电机信息
  firmware?: FirmwareInfo     // 固件信息
  warranty?: WarrantyInfo     // 保修信息
}

// ====================
// 对话历史类型定义 (v3.2+)
// ====================

/** 会话历史消息角色 */
export type HistoryMessageRole = 'user' | 'assistant' | 'agent' | 'system'

/** 历史消息 */
export interface HistoryMessage {
  id: string
  role: HistoryMessageRole
  content: string
  timestamp: number
  agent_id?: string           // 坐席ID（role为agent时）
  agent_name?: string         // 坐席名称（role为agent时）
  metadata?: Record<string, any>  // 附加元数据
}

/** 会话历史摘要 */
export interface ConversationSummary {
  session_name: string
  start_time: number
  end_time?: number
  message_count: number
  ai_message_count: number
  agent_message_count: number
  user_message_count: number
  status: SessionStatus
  tags?: string[]             // 会话标签
}

/** 对话历史响应 */
export interface ConversationHistoryResponse {
  success: boolean
  data: {
    session_name: string
    messages: HistoryMessage[]
    summary: ConversationSummary
  }
}
