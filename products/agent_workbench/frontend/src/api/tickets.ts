/**
 * 工单 API 封装
 *
 * 接口：
 * - POST /tickets - 创建工单
 * - POST /tickets/manual - 手动创建工单
 * - GET /tickets - 工单列表
 * - GET /tickets/search - 搜索工单
 * - POST /tickets/filter - 高级筛选
 * - POST /tickets/export - 导出工单
 * - GET /tickets/sla-dashboard - SLA 仪表盘
 * - GET /tickets/{ticket_id} - 工单详情
 * - PATCH /tickets/{ticket_id} - 更新工单
 * - POST /tickets/{ticket_id}/assign - 分配工单
 * - POST /tickets/batch/assign - 批量分配
 * - POST /tickets/batch/close - 批量关闭
 * - POST /tickets/batch/priority - 批量更新优先级
 * - POST /tickets/{ticket_id}/comments - 添加评论
 * - GET /tickets/{ticket_id}/comments - 评论列表
 * - GET /tickets/{ticket_id}/attachments - 附件列表
 * - POST /tickets/{ticket_id}/attachments - 上传附件
 * - GET /tickets/{ticket_id}/audit-logs - 审计日志
 * - DELETE /tickets/{ticket_id}/comments/{comment_id} - 删除评论
 * - POST /tickets/{ticket_id}/reopen - 重开工单
 * - POST /tickets/{ticket_id}/archive - 归档工单
 * - POST /tickets/archive/auto - 自动归档
 * - GET /tickets/archived - 归档列表
 * - GET /tickets/sla-summary - SLA 摘要
 * - GET /tickets/sla-alerts - SLA 告警
 * - GET /tickets/{ticket_id}/sla - 工单 SLA 信息
 */

import { apiClient } from './client';

// ============ 类型定义 ============

export type TicketStatus = 'pending' | 'in_progress' | 'waiting_customer' | 'waiting_vendor' | 'resolved' | 'closed' | 'archived';
export type TicketPriority = 'low' | 'medium' | 'high' | 'urgent';
export type TicketType = 'pre_sale' | 'after_sale' | 'complaint';
export type CommentType = 'internal' | 'external' | 'system';
export type SLAStatus = 'normal' | 'warning' | 'urgent' | 'violated' | 'completed';

export interface TicketCustomerInfo {
  name?: string;
  email?: string;
  phone?: string;
  country?: string;
}

export interface TicketInfo {
  ticket_id: string;
  title: string;
  description: string;
  status: TicketStatus;
  priority: TicketPriority;
  ticket_type: TicketType;
  customer?: TicketCustomerInfo;
  session_name?: string;
  assigned_agent_id?: string;
  assigned_agent_name?: string;
  created_by?: string;
  created_by_name?: string;
  created_at: number;
  updated_at: number;
  first_response_at?: number;
  resolved_at?: number;
  closed_at?: number;
  reopened_count: number;
  metadata?: Record<string, unknown>;
}

export interface TicketComment {
  comment_id: string;
  ticket_id: string;
  content: string;
  comment_type: CommentType;
  author_id: string;
  author_name?: string;
  mentions?: string[];
  created_at: number;
}

export interface TicketAttachment {
  attachment_id: string;
  ticket_id: string;
  filename: string;
  size: number;
  content_type?: string;
  comment_type: CommentType;
  uploader_id: string;
  uploader_name?: string;
  created_at: number;
  download_url: string;
}

export interface AuditLog {
  log_id: string;
  ticket_id: string;
  event_type: string;
  operator_id: string;
  operator_name: string;
  details?: Record<string, unknown>;
  created_at: number;
}

export interface SLADashboard {
  total_open_tickets: number;
  frt_stats: Record<SLAStatus, number>;
  rt_stats: Record<SLAStatus, number>;
  alerts: SLAAlert[];
  alerts_count: number;
  summary: SLASummary;
}

export interface SLAAlert {
  ticket_id: string;
  title: string;
  priority: TicketPriority;
  status: TicketStatus;
  frt_alert: boolean;
  frt_remaining_minutes: number;
  frt_status: SLAStatus;
  rt_alert: boolean;
  rt_remaining_hours: number;
  rt_status: SLAStatus;
  assigned_agent_name?: string;
}

export interface SLASummary {
  total: number;
  on_track: number;
  at_risk: number;
  violated: number;
}

export interface TicketSLAInfo {
  ticket_id: string;
  priority: TicketPriority;
  ticket_type: TicketType;
  status: TicketStatus;
  sla: {
    frt_target_minutes: number;
    frt_remaining_seconds: number;
    frt_status: SLAStatus;
    rt_target_hours: number;
    rt_remaining_seconds: number;
    rt_status: SLAStatus;
  };
}

// ============ 请求类型 ============

export interface CreateTicketRequest {
  session_name?: string;
  title: string;
  description: string;
  ticket_type?: TicketType;
  priority?: TicketPriority;
  customer?: TicketCustomerInfo;
  assigned_agent_id?: string;
  assigned_agent_name?: string;
  metadata?: Record<string, unknown>;
}

export interface ManualTicketRequest {
  title: string;
  description: string;
  ticket_type?: TicketType;
  priority?: TicketPriority;
  customer: TicketCustomerInfo;
  assigned_agent_id?: string;
  assigned_agent_name?: string;
  metadata?: Record<string, unknown>;
}

export interface UpdateTicketRequest {
  status?: TicketStatus;
  priority?: TicketPriority;
  assigned_agent_id?: string;
  assigned_agent_name?: string;
  note?: string;
  metadata_updates?: Record<string, unknown>;
  change_reason?: string;
}

export interface AssignTicketRequest {
  agent_id: string;
  agent_name?: string;
  note?: string;
}

export interface TicketFilters {
  statuses?: TicketStatus[];
  priorities?: TicketPriority[];
  ticket_types?: TicketType[];
  assigned?: string;
  assigned_agent_ids?: string[];
  keyword?: string;
  tags?: string[];
  categories?: string[];
  created_start?: number;
  created_end?: number;
  updated_start?: number;
  updated_end?: number;
  limit?: number;
  offset?: number;
  sort_by?: string;
  sort_desc?: boolean;
}

export interface AddCommentRequest {
  content: string;
  comment_type?: CommentType;
  mentions?: string[];
}

export interface ReopenTicketRequest {
  reason: string;
  comment?: string;
}

export interface ArchiveTicketRequest {
  reason?: string;
}

export interface BatchAssignRequest {
  ticket_ids: string[];
  target_agent_id: string;
  target_agent_name?: string;
  note?: string;
}

export interface BatchCloseRequest {
  ticket_ids: string[];
  close_reason?: string;
  comment?: string;
}

export interface BatchPriorityRequest {
  ticket_ids: string[];
  priority: TicketPriority;
  reason?: string;
}

export interface TicketListParams {
  status?: TicketStatus;
  priority?: TicketPriority;
  assigned_agent_id?: string;
  limit?: number;
  offset?: number;
}

// ============ 响应类型 ============

interface ApiResponse<T> {
  success: boolean;
  data: T;
}

interface TicketListResponse {
  tickets: TicketInfo[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

interface BatchOperationResult {
  succeeded: number;
  failed: Array<{ ticket_id: string; reason: string }>;
  tickets: TicketInfo[];
}

// ============ API 函数 ============

/**
 * 创建工单
 */
export async function create(data: CreateTicketRequest): Promise<TicketInfo> {
  const response = await apiClient.post<ApiResponse<TicketInfo>>('/tickets', data);
  return response.data.data;
}

/**
 * 手动创建工单（无关联会话）
 */
export async function createManual(data: ManualTicketRequest): Promise<TicketInfo> {
  const response = await apiClient.post<ApiResponse<TicketInfo>>('/tickets/manual', data);
  return response.data.data;
}

/**
 * 获取工单列表
 */
export async function getList(params?: TicketListParams): Promise<TicketListResponse> {
  const response = await apiClient.get<ApiResponse<TicketListResponse>>('/tickets', { params });
  return response.data.data;
}

/**
 * 搜索工单
 */
export async function search(query: string, limit?: number): Promise<TicketListResponse> {
  const response = await apiClient.get<ApiResponse<TicketListResponse>>('/tickets/search', {
    params: { query, limit }
  });
  return response.data.data;
}

/**
 * 高级筛选工单
 */
export async function filter(filters: TicketFilters): Promise<TicketListResponse> {
  const response = await apiClient.post<ApiResponse<TicketListResponse>>('/tickets/filter', filters);
  return response.data.data;
}

/**
 * 导出工单（CSV）
 */
export async function exportTickets(filters?: TicketFilters): Promise<Blob> {
  const response = await apiClient.post('/tickets/export', {
    format: 'csv',
    filters
  }, {
    responseType: 'blob'
  });
  return response.data;
}

/**
 * 获取 SLA 仪表盘
 */
export async function getSLADashboard(): Promise<SLADashboard> {
  const response = await apiClient.get<ApiResponse<SLADashboard>>('/tickets/sla-dashboard');
  return response.data.data;
}

/**
 * 获取工单详情
 */
export async function getDetail(ticketId: string): Promise<TicketInfo> {
  const response = await apiClient.get<ApiResponse<TicketInfo>>(`/tickets/${ticketId}`);
  return response.data.data;
}

/**
 * 更新工单
 */
export async function update(ticketId: string, data: UpdateTicketRequest): Promise<TicketInfo> {
  const response = await apiClient.patch<ApiResponse<TicketInfo>>(`/tickets/${ticketId}`, data);
  return response.data.data;
}

/**
 * 分配工单
 */
export async function assign(ticketId: string, data: AssignTicketRequest): Promise<TicketInfo> {
  const response = await apiClient.post<ApiResponse<TicketInfo>>(`/tickets/${ticketId}/assign`, data);
  return response.data.data;
}

/**
 * 批量分配工单
 */
export async function batchAssign(data: BatchAssignRequest): Promise<BatchOperationResult> {
  const response = await apiClient.post<ApiResponse<BatchOperationResult>>('/tickets/batch/assign', data);
  return response.data.data;
}

/**
 * 批量关闭工单
 */
export async function batchClose(data: BatchCloseRequest): Promise<BatchOperationResult> {
  const response = await apiClient.post<ApiResponse<BatchOperationResult>>('/tickets/batch/close', data);
  return response.data.data;
}

/**
 * 批量更新优先级
 */
export async function batchPriority(data: BatchPriorityRequest): Promise<BatchOperationResult> {
  const response = await apiClient.post<ApiResponse<BatchOperationResult>>('/tickets/batch/priority', data);
  return response.data.data;
}

/**
 * 添加工单评论
 */
export async function addComment(ticketId: string, data: AddCommentRequest): Promise<TicketComment> {
  const response = await apiClient.post<ApiResponse<TicketComment>>(`/tickets/${ticketId}/comments`, data);
  return response.data.data;
}

/**
 * 获取工单评论列表
 */
export async function getComments(ticketId: string): Promise<TicketComment[]> {
  const response = await apiClient.get<ApiResponse<TicketComment[]>>(`/tickets/${ticketId}/comments`);
  return response.data.data;
}

/**
 * 删除工单评论
 */
export async function deleteComment(ticketId: string, commentId: string): Promise<void> {
  await apiClient.delete(`/tickets/${ticketId}/comments/${commentId}`);
}

/**
 * 获取工单附件列表
 */
export async function getAttachments(ticketId: string): Promise<TicketAttachment[]> {
  const response = await apiClient.get<ApiResponse<TicketAttachment[]>>(`/tickets/${ticketId}/attachments`);
  return response.data.data;
}

/**
 * 上传工单附件
 */
export async function uploadAttachment(
  ticketId: string,
  file: File,
  commentType: CommentType = 'internal'
): Promise<TicketAttachment> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('comment_type', commentType);

  const response = await apiClient.post<ApiResponse<TicketAttachment>>(
    `/tickets/${ticketId}/attachments`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }
  );
  return response.data.data;
}

/**
 * 获取工单审计日志
 */
export async function getAuditLogs(ticketId: string, limit?: number): Promise<AuditLog[]> {
  const response = await apiClient.get<ApiResponse<AuditLog[]>>(`/tickets/${ticketId}/audit-logs`, {
    params: { limit }
  });
  return response.data.data;
}

/**
 * 重开工单
 */
export async function reopen(ticketId: string, data: ReopenTicketRequest): Promise<TicketInfo> {
  const response = await apiClient.post<ApiResponse<TicketInfo>>(`/tickets/${ticketId}/reopen`, data);
  return response.data.data;
}

/**
 * 归档工单
 */
export async function archive(ticketId: string, data?: ArchiveTicketRequest): Promise<TicketInfo> {
  const response = await apiClient.post<ApiResponse<TicketInfo>>(`/tickets/${ticketId}/archive`, data || {});
  return response.data.data;
}

/**
 * 自动归档工单（管理员）
 */
export async function autoArchive(olderThanDays?: number): Promise<{ archived_count: number; ticket_ids: string[] }> {
  const response = await apiClient.post<ApiResponse<{ archived_count: number; ticket_ids: string[]; older_than_days: number }>>(
    '/tickets/archive/auto',
    { older_than_days: olderThanDays }
  );
  return response.data.data;
}

/**
 * 获取归档工单列表
 */
export async function getArchived(params?: {
  customer_email?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}): Promise<TicketListResponse> {
  const response = await apiClient.get<ApiResponse<TicketListResponse>>('/tickets/archived', { params });
  return response.data.data;
}

/**
 * 获取 SLA 摘要
 */
export async function getSLASummary(): Promise<SLASummary> {
  const response = await apiClient.get<ApiResponse<SLASummary>>('/tickets/sla-summary');
  return response.data.data;
}

/**
 * 获取 SLA 告警
 */
export async function getSLAAlerts(): Promise<SLAAlert[]> {
  const response = await apiClient.get<ApiResponse<SLAAlert[]>>('/tickets/sla-alerts');
  return response.data.data;
}

/**
 * 获取工单 SLA 信息
 */
export async function getTicketSLA(ticketId: string): Promise<TicketSLAInfo> {
  const response = await apiClient.get<ApiResponse<TicketSLAInfo>>(`/tickets/${ticketId}/sla`);
  return response.data.data;
}

// ============ 导出 ============

export const ticketsApi = {
  create,
  createManual,
  getList,
  search,
  filter,
  exportTickets,
  getSLADashboard,
  getDetail,
  update,
  assign,
  batchAssign,
  batchClose,
  batchPriority,
  addComment,
  getComments,
  deleteComment,
  getAttachments,
  uploadAttachment,
  getAuditLogs,
  reopen,
  archive,
  autoArchive,
  getArchived,
  getSLASummary,
  getSLAAlerts,
  getTicketSLA,
};

export default ticketsApi;
