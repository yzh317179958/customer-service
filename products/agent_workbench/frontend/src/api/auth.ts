/**
 * 认证 API 封装
 *
 * 接口：
 * - POST /agent/login - 登录
 * - POST /agent/logout - 登出
 * - POST /agent/refresh - 刷新 Token
 * - GET /agent/profile - 获取个人信息
 * - PUT /agent/profile - 更新个人信息
 * - GET /agent/status - 获取状态
 * - PUT /agent/status - 更新状态
 * - POST /agent/change-password - 修改密码
 * - POST /agent/heartbeat - 心跳
 * - GET /agent/stats/today - 今日统计
 */

import { apiClient, setToken, setRefreshToken, clearTokens } from './client';

// ============ 类型定义 ============

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  refresh_token: string;
  expires_in: number;
  agent: AgentInfo;
}

export interface AgentInfo {
  id: string;
  username: string;
  name: string;
  email?: string;
  avatar_url?: string;
  role: 'agent' | 'admin' | 'supervisor';
  status: AgentStatus;
  status_note?: string;
  max_sessions: number;
  skills?: string[];
  created_at?: number;
}

export type AgentStatus = 'online' | 'busy' | 'away' | 'offline';

export interface AgentStatusPayload {
  status: AgentStatus;
  status_note?: string;
  current_sessions: number;
  max_sessions: number;
  today_stats: TodayStats;
}

export interface TodayStats {
  sessions_handled: number;
  messages_sent: number;
  avg_response_time: number;
  satisfaction_score: number;
}

export interface UpdateStatusRequest {
  status: AgentStatus;
  status_note?: string;
}

export interface UpdateProfileRequest {
  name?: string;
  avatar_url?: string;
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RefreshTokenResponse {
  token: string;
  expires_in: number;
}

// ============ API 函数 ============

/**
 * 坐席登录
 */
export async function login(data: LoginRequest): Promise<LoginResponse> {
  const response = await apiClient.post<LoginResponse>('/agent/login', data);

  // 自动存储 Token
  if (response.data.token) {
    setToken(response.data.token);
  }
  if (response.data.refresh_token) {
    setRefreshToken(response.data.refresh_token);
  }

  return response.data;
}

/**
 * 坐席登出
 */
export async function logout(username: string): Promise<void> {
  await apiClient.post('/agent/logout', null, {
    params: { username }
  });
  clearTokens();
}

/**
 * 刷新 Token
 */
export async function refreshToken(data: RefreshTokenRequest): Promise<RefreshTokenResponse> {
  const response = await apiClient.post<RefreshTokenResponse>('/agent/refresh', data);

  // 更新 Token
  if (response.data.token) {
    setToken(response.data.token);
  }

  return response.data;
}

/**
 * 获取坐席个人信息
 */
export async function getProfile(username: string): Promise<{ agent: AgentInfo }> {
  const response = await apiClient.get<{ agent: AgentInfo }>('/agent/profile', {
    params: { username }
  });
  return response.data;
}

/**
 * 更新坐席个人信息
 */
export async function updateProfile(data: UpdateProfileRequest): Promise<{ agent: AgentInfo }> {
  const response = await apiClient.put<{ agent: AgentInfo }>('/agent/profile', data);
  return response.data;
}

/**
 * 获取坐席状态
 */
export async function getStatus(): Promise<AgentStatusPayload> {
  const response = await apiClient.get<AgentStatusPayload>('/agent/status');
  return response.data;
}

/**
 * 更新坐席状态
 */
export async function updateStatus(data: UpdateStatusRequest): Promise<AgentStatusPayload> {
  const response = await apiClient.put<AgentStatusPayload>('/agent/status', data);
  return response.data;
}

/**
 * 修改密码
 */
export async function changePassword(data: ChangePasswordRequest): Promise<{ message: string }> {
  const response = await apiClient.post<{ message: string }>('/agent/change-password', data);
  return response.data;
}

/**
 * 心跳（保持在线状态）
 */
export async function heartbeat(): Promise<{ last_active_at: number }> {
  const response = await apiClient.post<{ last_active_at: number }>('/agent/heartbeat');
  return response.data;
}

/**
 * 获取今日统计
 */
export async function getTodayStats(): Promise<TodayStats & { current_sessions: number; max_sessions: number }> {
  const response = await apiClient.get('/agent/stats/today');
  return response.data;
}

// ============ 导出 ============

export const authApi = {
  login,
  logout,
  refreshToken,
  getProfile,
  updateProfile,
  getStatus,
  updateStatus,
  changePassword,
  heartbeat,
  getTodayStats,
};

export default authApi;
