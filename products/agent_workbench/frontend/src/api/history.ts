/**
 * Chat history API (Step 8)
 *
 * Endpoints (agent_workbench backend):
 * - GET /history/sessions
 * - GET /history/sessions/{session_name}
 * - GET /history/search
 * - GET /history/statistics
 * - GET /history/export (CSV)
 */

import { apiClient } from './client';

export type HistoryRole = 'user' | 'assistant' | 'agent';

export interface HistorySessionMeta {
  display_name: string | null;
  note: string | null;
  tags: any;
  updated_by: string | null;
  updated_at: number;
}

export interface HistorySessionSummary {
  session_name: string;
  meta?: HistorySessionMeta | null;
  last_message_preview?: string;
  message_count: number;
  first_message_at: number;
  last_message_at: number;
  conversation_count: number;
}

export interface HistoryMessageItem {
  id: number;
  message_id: string;
  session_name: string;
  conversation_id: string | null;
  role: HistoryRole;
  content: string;
  agent_id: string | null;
  agent_name: string | null;
  response_time_ms: number | null;
  created_at: number;
}

export interface HistorySessionsResponse {
  items: HistorySessionSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface HistorySessionDetailResponse {
  session_name: string;
  total: number;
  items: HistoryMessageItem[];
  order?: 'asc' | 'desc';
}

export interface HistorySearchItem extends HistoryMessageItem {
  rank: number;
}

export interface HistorySearchResponse {
  items: HistorySearchItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface HistoryStatisticsResponse {
  total_messages: number;
  total_sessions: number;
  by_role: Record<HistoryRole, number>;
  avg_response_time_ms: number;
}

export interface HistoryListParams {
  page?: number;
  page_size?: number;
  start_time?: number;
  end_time?: number;
}

export interface HistoryDetailParams {
  limit?: number;
  offset?: number;
}

export interface HistorySearchParams {
  q: string;
  start_time?: number;
  end_time?: number;
  role?: HistoryRole;
  session_name?: string;
  page?: number;
  page_size?: number;
}

export interface HistoryExportParams {
  session_name: string;
  start_time?: number;
  end_time?: number;
}

export interface HistorySearchSessionsResponse {
  items: Array<{
    session_name: string;
    meta?: HistorySessionMeta | null;
    match_count: number;
    last_match_at: number;
    last_match_preview: string;
  }>;
  total: number;
  page: number;
  page_size: number;
}

export interface HistorySessionMetaResponse {
  session_name: string;
  meta: HistorySessionMeta | null;
}

export interface HistoryUpdateSessionMetaRequest {
  display_name?: string | null;
  note?: string | null;
  tags?: any;
}

export interface ExportJobCreateRequest {
  start_time: number;
  end_time: number;
  q?: string | null;
  role?: HistoryRole | null;
  session_name?: string | null;
}

export interface ExportJobItem {
  job_id: string;
  created_by: string;
  status: 'pending' | 'running' | 'done' | 'failed';
  request: any;
  row_count: number | null;
  file_path: string | null;
  error: string | null;
  created_at: number;
  updated_at: number;
  finished_at: number | null;
}

export interface ExportJobListResponse {
  items: ExportJobItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface ExportJobCreateResponse {
  job_id: string;
  status: 'pending';
  created_by: string;
}

export interface HistoryTranslateRequest {
  text: string;
}

export interface HistoryTranslateResponse {
  translated_text: string;
}

export async function listSessions(params?: HistoryListParams): Promise<HistorySessionsResponse> {
  const response = await apiClient.get<HistorySessionsResponse>('/history/sessions', { params });
  return response.data;
}

export async function searchSessions(params: { q: string; start_time?: number; end_time?: number; page?: number; page_size?: number }): Promise<HistorySearchSessionsResponse> {
  const response = await apiClient.get<HistorySearchSessionsResponse>('/history/sessions/search', { params });
  return response.data;
}

export async function getSessionDetail(
  sessionName: string,
  params?: HistoryDetailParams & { order?: 'asc' | 'desc' }
): Promise<HistorySessionDetailResponse> {
  const response = await apiClient.get<HistorySessionDetailResponse>(`/history/sessions/${encodeURIComponent(sessionName)}`, { params });
  return response.data;
}

export async function getSessionMeta(sessionName: string): Promise<HistorySessionMetaResponse> {
  const response = await apiClient.get<HistorySessionMetaResponse>(`/history/sessions/${encodeURIComponent(sessionName)}/meta`);
  return response.data;
}

export async function updateSessionMeta(sessionName: string, payload: HistoryUpdateSessionMetaRequest): Promise<HistorySessionMetaResponse> {
  const response = await apiClient.put<HistorySessionMetaResponse>(`/history/sessions/${encodeURIComponent(sessionName)}/meta`, payload);
  return response.data;
}

export async function searchMessages(params: HistorySearchParams): Promise<HistorySearchResponse> {
  const response = await apiClient.get<HistorySearchResponse>('/history/search', { params });
  return response.data;
}

export async function getStatistics(params?: { start_time?: number; end_time?: number }): Promise<HistoryStatisticsResponse> {
  const response = await apiClient.get<HistoryStatisticsResponse>('/history/statistics', { params });
  return response.data;
}

export async function exportMessagesCsv(params: HistoryExportParams): Promise<Blob> {
  const response = await apiClient.get('/history/export', {
    params,
    responseType: 'blob',
  });
  return response.data as Blob;
}

export async function createExportJob(payload: ExportJobCreateRequest): Promise<ExportJobCreateResponse> {
  const response = await apiClient.post<ExportJobCreateResponse>('/history/export-jobs', payload);
  return response.data;
}

export async function listExportJobs(params?: { limit?: number; offset?: number }): Promise<ExportJobListResponse> {
  const response = await apiClient.get<ExportJobListResponse>('/history/export-jobs', { params });
  return response.data;
}

export function getExportJobDownloadUrl(jobId: string): string {
  const base = apiClient.defaults.baseURL || '/api';
  return `${base}/history/export-jobs/${encodeURIComponent(jobId)}/download`;
}

export async function downloadExportJobCsv(jobId: string): Promise<Blob> {
  const response = await apiClient.get(`/history/export-jobs/${encodeURIComponent(jobId)}/download`, {
    responseType: 'blob',
  });
  return response.data as Blob;
}

export async function translateToZh(payload: HistoryTranslateRequest): Promise<HistoryTranslateResponse> {
  const response = await apiClient.post<HistoryTranslateResponse>('/history/translate', payload);
  return response.data;
}

export const historyApi = {
  listSessions,
  searchSessions,
  getSessionDetail,
  getSessionMeta,
  updateSessionMeta,
  searchMessages,
  getStatistics,
  exportMessagesCsv,
  createExportJob,
  listExportJobs,
  getExportJobDownloadUrl,
  downloadExportJobCsv,
  translateToZh,
};

export default historyApi;
