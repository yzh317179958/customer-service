/**
 * 快捷回复 API 客户端
 *
 * 功能：
 * - 获取快捷回复列表（支持分类筛选）
 * - 创建快捷回复（管理员）
 * - 更新快捷回复（管理员）
 * - 删除快捷回复（管理员）
 * - 使用快捷回复（追踪使用次数）
 */

import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

// 快捷回复分类
export enum QuickReplyCategory {
  PRE_SALES = 'pre_sales',
  AFTER_SALES = 'after_sales',
  LOGISTICS = 'logistics',
  TECHNICAL = 'technical',
  POLICY = 'policy'
}

// 快捷回复数据结构
export interface QuickReply {
  id: string
  category: QuickReplyCategory
  title: string
  content: string
  variables: string[]  // 如 ["{customer_name}", "{agent_name}"]
  shortcut?: string    // 快捷键 如 "Ctrl+1"
  is_shared: boolean   // 是否共享
  created_by: string   // 创建者 agent_id
  usage_count: number
  created_at: number
  updated_at?: number | null
}

// 分类元数据
export interface CategoryMetadata {
  key: string
  label: string
  icon: string
  color: string
}

// 支持的变量
export type SupportedVariables = Record<string, string>

// API 响应结构
export interface QuickRepliesResponse {
  success: boolean
  data: {
    items: QuickReply[]
    total: number
    categories: CategoryMetadata[]
    variables: SupportedVariables
  }
}

export interface QuickReplyResponse {
  success: boolean
  data: QuickReply
}

export interface UseQuickReplyResponse {
  success: boolean
  data: {
    id: string
    usage_count: number
  }
}

export interface DeleteQuickReplyResponse {
  success: boolean
  message: string
}

// 创建/更新快捷回复的请求数据
export interface CreateQuickReplyRequest {
  category: QuickReplyCategory
  title: string
  content: string
  shortcut?: string
  is_shared: boolean
}

export interface UpdateQuickReplyRequest {
  title?: string
  content?: string
  shortcut?: string
  is_shared?: boolean
}

/**
 * 获取认证 token
 */
const getAuthHeader = () => {
  const token = localStorage.getItem('access_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

/**
 * 获取快捷回复列表
 */
export const getQuickReplies = async (
  category?: QuickReplyCategory
): Promise<QuickRepliesResponse> => {
  const params = category ? { category } : {}
  const response = await axios.get<QuickRepliesResponse>(
    `${API_BASE}/api/quick-replies`,
    {
      headers: getAuthHeader(),
      params
    }
  )
  return response.data
}

/**
 * 创建快捷回复（仅管理员）
 */
export const createQuickReply = async (
  data: CreateQuickReplyRequest
): Promise<QuickReplyResponse> => {
  const response = await axios.post<QuickReplyResponse>(
    `${API_BASE}/api/quick-replies`,
    data,
    { headers: getAuthHeader() }
  )
  return response.data
}

/**
 * 更新快捷回复（仅管理员）
 */
export const updateQuickReply = async (
  id: string,
  data: UpdateQuickReplyRequest
): Promise<QuickReplyResponse> => {
  const response = await axios.put<QuickReplyResponse>(
    `${API_BASE}/api/quick-replies/${id}`,
    data,
    { headers: getAuthHeader() }
  )
  return response.data
}

/**
 * 删除快捷回复（仅管理员）
 */
export const deleteQuickReply = async (
  id: string
): Promise<DeleteQuickReplyResponse> => {
  const response = await axios.delete<DeleteQuickReplyResponse>(
    `${API_BASE}/api/quick-replies/${id}`,
    { headers: getAuthHeader() }
  )
  return response.data
}

/**
 * 使用快捷回复（追踪使用次数）
 */
export const useQuickReply = async (
  id: string
): Promise<UseQuickReplyResponse> => {
  const response = await axios.post<UseQuickReplyResponse>(
    `${API_BASE}/api/quick-replies/${id}/use`,
    {},
    { headers: getAuthHeader() }
  )
  return response.data
}

/**
 * 变量替换工具函数
 *
 * @param content - 包含变量的内容模板
 * @param variables - 变量值映射 { customer_name: "张三", agent_name: "李四" }
 * @returns 替换后的内容
 */
export const replaceVariables = (
  content: string,
  variables: Record<string, string>
): string => {
  let result = content

  Object.keys(variables).forEach(key => {
    const placeholder = `{${key}}`
    const value = variables[key] || placeholder  // 如果值不存在，保留占位符
    result = result.replace(new RegExp(placeholder.replace(/[{}]/g, '\\$&'), 'g'), value)
  })

  return result
}
