/**
 * 会话 API 封装
 *
 * 接口：
 * - GET /sessions - 会话列表
 * - GET /sessions/stats - 会话统计
 * - GET /sessions/queue - 待接入队列
 * - GET /sessions/{session_name} - 会话详情
 * - POST /sessions/{session_name}/takeover - 接管会话
 * - POST /sessions/{session_name}/release - 释放会话
 * - POST /sessions/{session_name}/transfer - 转接会话
 * - POST /sessions/{session_name}/messages - 发送消息
 * - POST /sessions/{session_name}/notes - 添加备注
 * - POST /sessions/{session_name}/ticket - 创建工单
 * - GET /sessions/{session_name}/events - SSE 事件流
 */

import { apiClient } from './client';

// ============ 类型定义 ============

export type SessionStatus = 'bot_active' | 'pending_manual' | 'manual_live' | 'closed';

export interface SessionInfo {
  session_name: string;
  status: SessionStatus;
  customer_id?: string;
  customer_name?: string;
  customer_email?: string;
  customer_avatar?: string;
  channel?: string;
  tags?: string[];
  assigned_agent?: AgentBrief;
  escalation?: EscalationInfo;
  created_at: number;
  updated_at: number;
  last_message?: MessageInfo;
  unread_count?: number;
}

export interface AgentBrief {
  id: string;
  name: string;
  avatar_url?: string;
}

export interface EscalationInfo {
  reason: string;
  details?: string;
  severity?: 'low' | 'medium' | 'high';
  escalated_at?: number;
}

export interface MessageInfo {
  id?: string;
  role: 'user' | 'assistant' | 'agent' | 'system';
  content: string;
  timestamp: number;
  agent_id?: string;
  agent_name?: string;
  message_type?: 'text' | 'image' | 'file';
}

export interface SessionStats {
  total: number;
  pending_manual: number;
  manual_live: number;
  bot_active: number;
  closed_today: number;
}

export interface QueueItem {
  session_name: string;
  customer_name?: string;
  customer_email?: string;
  channel?: string;
  tags?: string[];
  escalation_reason?: string;
  wait_time: number;
  created_at: number;
}

export interface SessionListParams {
  status?: SessionStatus;
  agent_id?: string;
  page?: number;
  page_size?: number;
}

export interface SendMessageRequest {
  content: string;
  message_type?: 'text' | 'image' | 'file';
}

export interface TransferRequest {
  target_agent_id: string;
  reason?: string;
}

export interface AddNoteRequest {
  content: string;
}

export interface CreateTicketRequest {
  title?: string;
  description?: string;
  ticket_type?: 'complaint' | 'after_sale' | 'inquiry' | 'suggestion';
  priority?: 'low' | 'medium' | 'high' | 'urgent';
}

export interface TakeoverRequest {
  agent_id: string;
  agent_name: string;
}

export interface ReleaseRequest {
  agent_id: string;
  reason?: string;
}

// ============ API 函数 ============

/**
 * 获取会话列表
 */
export async function getList(params?: SessionListParams): Promise<{ sessions: SessionInfo[]; total: number }> {
  const response = await apiClient.get('/sessions', { params });
  return response.data;
}

/**
 * 获取会话统计
 */
export async function getStats(): Promise<SessionStats> {
  const response = await apiClient.get<SessionStats>('/sessions/stats');
  return response.data;
}

/**
 * 获取待接入队列
 */
export async function getQueue(): Promise<{ queue: QueueItem[]; total: number }> {
  const response = await apiClient.get('/sessions/queue');
  return response.data;
}

/**
 * 获取会话详情
 */
export async function getSession(sessionName: string): Promise<SessionInfo> {
  const response = await apiClient.get(`/sessions/${sessionName}`);
  // 适配后端返回格式: { success, data: { session, audit_trail } }
  const result = (response.data as any).data?.session || response.data;
  return result;
}

/**
 * 接管会话
 */
export async function takeover(sessionName: string, data: TakeoverRequest): Promise<SessionInfo> {
  const response = await apiClient.post(`/sessions/${sessionName}/takeover`, data);
  // 适配后端返回格式: { success, data: SessionState }
  const result = (response.data as any).data || response.data;
  return result;
}

/**
 * 释放会话
 */
export async function release(sessionName: string, data: ReleaseRequest): Promise<{ message: string }> {
  const response = await apiClient.post(`/sessions/${sessionName}/release`, data);
  return response.data;
}

/**
 * 转接会话
 */
export async function transfer(sessionName: string, data: TransferRequest): Promise<{ message: string }> {
  const response = await apiClient.post(`/sessions/${sessionName}/transfer`, data);
  return response.data;
}

/**
 * 发送消息
 */
export async function sendMessage(sessionName: string, data: SendMessageRequest): Promise<MessageInfo> {
  const response = await apiClient.post(`/sessions/${sessionName}/messages`, data);
  // 适配后端返回格式: { success, data: { message, session_name } }
  const result = (response.data as any).data?.message || response.data;
  return result;
}

/**
 * 添加备注
 */
export async function addNote(sessionName: string, data: AddNoteRequest): Promise<{ message: string }> {
  const response = await apiClient.post(`/sessions/${sessionName}/notes`, data);
  return response.data;
}

/**
 * 从会话创建工单
 */
export async function createTicket(sessionName: string, data: CreateTicketRequest): Promise<{ ticket_id: string }> {
  const response = await apiClient.post(`/sessions/${sessionName}/ticket`, data);
  return response.data;
}

/**
 * 上传聊天图片
 */
export async function uploadChatImage(file: File): Promise<{ success: boolean; image_url: string; filename: string; markdown: string }> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<{ success: boolean; image_url: string; filename: string; markdown: string }>(
    '/sessions/upload/image',
    formData
  );
  return response.data;
}

/**
 * 订阅会话 SSE 事件流
 * 返回 EventSource 实例，调用方需要自行管理生命周期
 */
export function subscribeEvents(sessionName: string, onMessage: (event: MessageEvent) => void, onError?: (event: Event) => void): EventSource {
  const token = localStorage.getItem('agent_token');
  const url = `${apiClient.defaults.baseURL}/sessions/${sessionName}/events?token=${token}`;

  const eventSource = new EventSource(url);

  eventSource.onmessage = onMessage;

  if (onError) {
    eventSource.onerror = onError;
  }

  return eventSource;
}

// ============ 导出 ============

export const sessionsApi = {
  getList,
  getStats,
  getQueue,
  getSession,
  takeover,
  release,
  transfer,
  sendMessage,
  addNote,
  createTicket,
  uploadChatImage,
  subscribeEvents,
};

export default sessionsApi;
