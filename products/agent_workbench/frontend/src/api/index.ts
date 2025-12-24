/**
 * API 模块统一导出
 *
 * 使用方式：
 * import { authApi, sessionsApi, ticketsApi, quickRepliesApi } from './api';
 * import { apiClient } from './api';
 */

// API 客户端
export { apiClient } from './client';

// 认证 API
export { authApi } from './auth';
export type {
  AgentInfo,
  AgentStatus,
  LoginRequest,
  LoginResponse,
  UpdateProfileRequest,
  ChangePasswordRequest,
  TodayStats,
  AgentStatusPayload,
  UpdateStatusRequest,
  RefreshTokenRequest,
  RefreshTokenResponse,
} from './auth';

// 会话 API
export { sessionsApi } from './sessions';
export type {
  SessionStatus,
  SessionInfo,
  AgentBrief,
  EscalationInfo,
  MessageInfo,
  SessionStats,
  QueueItem,
  SessionListParams,
  SendMessageRequest,
  TransferRequest,
  AddNoteRequest,
  CreateTicketRequest as SessionCreateTicketRequest,
} from './sessions';

// 工单 API
export { ticketsApi } from './tickets';
export type {
  TicketStatus,
  TicketPriority,
  TicketType,
  CommentType,
  SLAStatus,
  TicketCustomerInfo,
  TicketInfo,
  TicketComment,
  TicketAttachment,
  AuditLog,
  SLADashboard,
  SLAAlert,
  SLASummary,
  TicketSLAInfo,
  CreateTicketRequest,
  ManualTicketRequest,
  UpdateTicketRequest,
  AssignTicketRequest,
  TicketFilters,
  AddCommentRequest,
  ReopenTicketRequest,
  ArchiveTicketRequest,
  BatchAssignRequest,
  BatchCloseRequest,
  BatchPriorityRequest,
  TicketListParams,
} from './tickets';

// 快捷回复 API
export { quickRepliesApi } from './quickReplies';
export type {
  QuickReplyCategory,
  QuickReply,
  VariableInfo,
  CategoriesInfo,
  QuickReplyStats,
  UseQuickReplyResult,
  CreateQuickReplyRequest,
  UpdateQuickReplyRequest,
  QuickReplyListParams,
  UseQuickReplyRequest,
} from './quickReplies';

// Shopify 订单 API
export { shopifyApi } from './shopify';
export type {
  ShopifySite,
  OrderLineItem,
  OrderAddress,
  ShopifyOrder,
  TrackingInfo,
  TrackingEvent,
} from './shopify';

// 统计数据 API
export { statsApi } from './stats';
export type {
  SessionStats as DashboardSessionStats,
  AgentTodayStats,
  SLAStats,
  SLAAlert as DashboardSLAAlert,
  SLADashboard as DashboardSLAData,
  DashboardStats,
} from './stats';
