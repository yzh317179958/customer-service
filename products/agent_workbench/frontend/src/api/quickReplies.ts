/**
 * 快捷回复 API 封装
 *
 * 接口：
 * - GET /quick-replies/categories - 获取分类列表
 * - GET /quick-replies/stats - 使用统计（管理员）
 * - GET /quick-replies - 快捷回复列表
 * - POST /quick-replies - 创建快捷回复
 * - GET /quick-replies/{reply_id} - 获取快捷回复
 * - PUT /quick-replies/{reply_id} - 更新快捷回复
 * - DELETE /quick-replies/{reply_id} - 删除快捷回复
 * - POST /quick-replies/{reply_id}/use - 使用快捷回复
 */

import { apiClient } from './client';

// ============ 类型定义 ============

export type QuickReplyCategory =
  | 'greeting'      // 问候语
  | 'farewell'      // 结束语
  | 'apology'       // 道歉
  | 'shipping'      // 物流相关
  | 'refund'        // 退款相关
  | 'product'       // 产品相关
  | 'technical'     // 技术支持
  | 'custom';       // 自定义

export interface QuickReply {
  id: string;
  title: string;
  content: string;
  category: QuickReplyCategory;
  variables: string[];
  shortcut_key?: string;
  is_shared: boolean;
  created_by?: string;
  usage_count: number;
  created_at: number;
  updated_at: number;
}

export interface VariableInfo {
  name: string;
  description: string;
  example: string;
}

export interface CategoriesInfo {
  categories: Record<QuickReplyCategory, string>;
  supported_variables: VariableInfo[];
}

export interface QuickReplyStats {
  total_count: number;
  shared_count: number;
  personal_count: number;
  by_category: Record<QuickReplyCategory, number>;
  top_used: Array<{
    id: string;
    title: string;
    usage_count: number;
  }>;
}

export interface UseQuickReplyResult {
  id: string;
  title: string;
  original_content: string;
  replaced_content: string;
  variables: string[];
}

// ============ 请求类型 ============

export interface CreateQuickReplyRequest {
  title: string;
  content: string;
  category?: QuickReplyCategory;
  shortcut_key?: string;
  is_shared?: boolean;
}

export interface UpdateQuickReplyRequest {
  title?: string;
  content?: string;
  category?: QuickReplyCategory;
  shortcut_key?: string;
  is_shared?: boolean;
}

export interface QuickReplyListParams {
  category?: QuickReplyCategory;
  agent_id?: string;
  include_shared?: boolean;
  keyword?: string;
  limit?: number;
  offset?: number;
}

export interface UseQuickReplyRequest {
  session_data?: {
    session_name?: string;
    customer_name?: string;
    customer_email?: string;
  };
  agent_data?: {
    agent_name?: string;
    agent_id?: string;
  };
  shopify_data?: {
    order_number?: string;
    tracking_number?: string;
    product_name?: string;
  };
}

// ============ 响应类型 ============

interface ApiResponse<T> {
  success: boolean;
  data: T;
}

interface QuickReplyListResponse {
  items: QuickReply[];
  total: number;
  limit: number;
  offset: number;
}

// ============ API 函数 ============

/**
 * 获取快捷回复分类和支持的变量
 */
export async function getCategories(): Promise<CategoriesInfo> {
  const response = await apiClient.get<ApiResponse<CategoriesInfo>>('/quick-replies/categories');
  return response.data.data;
}

/**
 * 获取快捷回复使用统计（管理员）
 */
export async function getStats(): Promise<QuickReplyStats> {
  const response = await apiClient.get<ApiResponse<QuickReplyStats>>('/quick-replies/stats');
  return response.data.data;
}

/**
 * 获取快捷回复列表
 */
export async function getList(params?: QuickReplyListParams): Promise<QuickReplyListResponse> {
  const response = await apiClient.get<ApiResponse<QuickReplyListResponse>>('/quick-replies', { params });
  return response.data.data;
}

/**
 * 创建快捷回复
 */
export async function create(data: CreateQuickReplyRequest): Promise<QuickReply> {
  const response = await apiClient.post<ApiResponse<QuickReply>>('/quick-replies', data);
  return response.data.data;
}

/**
 * 获取快捷回复详情
 */
export async function getDetail(replyId: string): Promise<QuickReply> {
  const response = await apiClient.get<ApiResponse<QuickReply>>(`/quick-replies/${replyId}`);
  return response.data.data;
}

/**
 * 更新快捷回复
 */
export async function update(replyId: string, data: UpdateQuickReplyRequest): Promise<QuickReply> {
  const response = await apiClient.put<ApiResponse<QuickReply>>(`/quick-replies/${replyId}`, data);
  return response.data.data;
}

/**
 * 删除快捷回复
 */
export async function remove(replyId: string): Promise<void> {
  await apiClient.delete(`/quick-replies/${replyId}`);
}

/**
 * 使用快捷回复（替换变量并增加使用次数）
 */
export async function use(replyId: string, context?: UseQuickReplyRequest): Promise<UseQuickReplyResult> {
  const response = await apiClient.post<ApiResponse<UseQuickReplyResult>>(
    `/quick-replies/${replyId}/use`,
    context || {}
  );
  return response.data.data;
}

// ============ 导出 ============

export const quickRepliesApi = {
  getCategories,
  getStats,
  getList,
  create,
  getDetail,
  update,
  remove,
  use,
};

export default quickRepliesApi;
