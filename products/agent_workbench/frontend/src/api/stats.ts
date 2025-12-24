/**
 * 统计数据 API 封装
 *
 * 提供效能报表所需的各类统计数据
 */

import { apiClient } from './client';

// ============================================================================
// 类型定义
// ============================================================================

// 会话统计
export interface SessionStats {
  total: number;
  pending: number;
  active: number;
  completed: number;
  avg_waiting_time: number;  // 秒
  max_waiting_time: number;  // 秒
  avg_service_time: number;  // 秒
  active_agents: number;
}

// 坐席今日统计
export interface AgentTodayStats {
  sessions_handled: number;
  messages_sent: number;
  avg_response_time: number;  // 秒
  satisfaction_rate: number;  // 0-100
  tickets_created: number;
  current_sessions: number;
  max_sessions: number;
}

// SLA 状态统计
export interface SLAStats {
  normal: number;
  warning: number;
  urgent: number;
  violated: number;
  completed: number;
}

// SLA 告警
export interface SLAAlert {
  ticket_id: string;
  title: string;
  priority: string;
  status: string;
  frt_alert: boolean;
  frt_remaining_minutes: number;
  frt_status: string;
  rt_alert: boolean;
  rt_remaining_hours: number;
  rt_status: string;
  assigned_agent_name?: string;
}

// SLA 仪表盘数据
export interface SLADashboard {
  frt_stats: SLAStats;
  rt_stats: SLAStats;
  alerts: SLAAlert[];
  total_active_tickets: number;
}

// 效能报表汇总
export interface DashboardStats {
  sessions: SessionStats;
  agent: AgentTodayStats;
  sla: SLADashboard;
}

// API 响应
interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: string;
}

// ============================================================================
// API 函数
// ============================================================================

/**
 * 获取会话统计
 */
export async function getSessionStats(): Promise<SessionStats> {
  const response = await apiClient.get<ApiResponse<SessionStats>>('/sessions/stats');
  return response.data.data;
}

/**
 * 获取坐席今日统计
 */
export async function getAgentTodayStats(): Promise<AgentTodayStats> {
  const response = await apiClient.get<ApiResponse<AgentTodayStats>>('/agent/stats/today');
  return response.data.data;
}

/**
 * 获取 SLA 仪表盘数据
 */
export async function getSLADashboard(): Promise<SLADashboard> {
  const response = await apiClient.get<ApiResponse<SLADashboard>>('/tickets/sla-dashboard');
  return response.data.data;
}

/**
 * 获取效能报表汇总数据
 * 并行请求所有统计接口
 */
export async function getDashboardStats(): Promise<DashboardStats> {
  const [sessions, agent, sla] = await Promise.all([
    getSessionStats(),
    getAgentTodayStats(),
    getSLADashboard(),
  ]);

  return { sessions, agent, sla };
}

// 导出所有函数
export const statsApi = {
  getSessionStats,
  getAgentTodayStats,
  getSLADashboard,
  getDashboardStats,
};

export default statsApi;
