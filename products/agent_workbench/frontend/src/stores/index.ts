/**
 * Stores 统一导出
 *
 * 使用方式：
 * import { useAuthStore, useSessionStore, useTicketStore } from './stores';
 */

// 认证 Store
export { useAuthStore, default as authStore } from './authStore';
export {
  selectIsAuthenticated,
  selectAgent,
  selectStatus,
  selectIsLoading as selectAuthIsLoading,
  selectError as selectAuthError,
  selectTodayStats,
} from './authStore';

// 会话 Store
export { useSessionStore, default as sessionStore } from './sessionStore';
export {
  selectSessions,
  selectQueue,
  selectCurrentSession,
  selectCurrentMessages,
  selectStats,
  selectIsLoading as selectSessionIsLoading,
  selectError as selectSessionError,
} from './sessionStore';

// 工单 Store
export { useTicketStore, default as ticketStore } from './ticketStore';
export {
  selectTickets,
  selectCurrentTicket,
  selectCurrentComments,
  selectFilters,
  selectSLADashboard,
  selectIsLoading as selectTicketIsLoading,
  selectError as selectTicketError,
  selectSelectedIds,
  selectViewMode,
} from './ticketStore';
