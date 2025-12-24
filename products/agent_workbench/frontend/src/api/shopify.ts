/**
 * Shopify 订单 API 封装
 *
 * 提供多站点订单查询、物流追踪等功能
 */

import { apiClient } from './client';

// ============================================================================
// 类型定义
// ============================================================================

// 站点信息
export interface ShopifySite {
  code: string;
  name: string;
  domain: string;
  currency: string;
}

// 订单商品
export interface OrderLineItem {
  id: string;
  title: string;
  variant_title?: string;
  quantity: number;
  price: string;
  sku?: string;
  image_url?: string;
}

// 订单地址
export interface OrderAddress {
  name?: string;
  address1?: string;
  address2?: string;
  city?: string;
  province?: string;
  country?: string;
  zip?: string;
  phone?: string;
}

// 订单信息
export interface ShopifyOrder {
  id: string;
  /**
   * 后端常见字段名是 order_id（尤其是 global-search 返回）。
   * 前端统一使用 id；order_id 仅用于兼容/调试。
   */
  order_id?: string;
  order_number: string;
  name: string;  // 如 #UK22080
  email: string;
  phone?: string;
  created_at: string;
  updated_at: string;
  financial_status: string;  // paid, pending, refunded 等
  fulfillment_status?: string;  // fulfilled, partial, null
  total_price: string;
  subtotal_price: string;
  total_tax: string;
  total_discounts: string;
  currency: string;
  line_items: OrderLineItem[];
  shipping_address?: OrderAddress;
  billing_address?: OrderAddress;
  note?: string;
  tags?: string;
  site_code?: string;  // 站点代码
}

type ShopifyOrderApi = Omit<ShopifyOrder, 'id'> & {
  id?: string;
  order_id?: string;
};

function normalizeOrder(order: ShopifyOrderApi): ShopifyOrder {
  const id = order.id ?? order.order_id;
  if (!id) {
    // 保持调用方可用：若后端缺少 id/order_id，则抛出明确错误，便于定位数据源问题
    throw new Error('ShopifyOrder missing id/order_id');
  }
  return {
    ...(order as Omit<ShopifyOrder, 'id'>),
    id: String(id),
    order_id: order.order_id ? String(order.order_id) : undefined,
  };
}

// 物流信息
export interface TrackingInfo {
  tracking_number?: string;
  tracking_company?: string;
  tracking_url?: string;
  fulfillment_status?: string;
  shipment_status?: string;
  estimated_delivery?: string;
  events?: TrackingEvent[];
}

export interface TrackingEvent {
  timestamp: string;
  description: string;
  description_zh?: string | null;
  location?: string;
}

// API 响应
export interface ShopifyResponse<T> {
  success: boolean;
  data: T;
  error?: string;
}

// ============================================================================
// API 函数
// ============================================================================

/**
 * 获取已配置的站点列表
 */
export async function getSites(): Promise<ShopifySite[]> {
  const response = await apiClient.get<ShopifyResponse<{ sites: ShopifySite[]; total: number }>>('/shopify/sites');
  return response.data.data.sites;
}

/**
 * 按邮箱查询指定站点的订单
 */
export async function getOrdersByEmail(
  site: string,
  email: string,
  options?: { limit?: number; status?: 'open' | 'closed' | 'cancelled' | 'any' }
): Promise<{ orders: ShopifyOrder[]; total: number }> {
  const params = {
    email,
    limit: options?.limit || 10,
    status: options?.status || 'any',
  };
  const response = await apiClient.get<ShopifyResponse<{ orders: ShopifyOrderApi[]; total: number }>>(
    `/shopify/${site}/orders`,
    { params }
  );
  return {
    orders: (response.data.data.orders || []).map(normalizeOrder),
    total: response.data.data.total,
  };
}

/**
 * 按订单号搜索指定站点的订单
 */
export async function searchOrder(
  site: string,
  query: string
): Promise<{ order: ShopifyOrder | null; query: string; site_code: string; message?: string }> {
  const response = await apiClient.get<ShopifyResponse<{ order: ShopifyOrderApi | null; query: string; site_code: string; message?: string }>>(
    `/shopify/${site}/orders/search`,
    { params: { q: query } }
  );
  return {
    ...response.data.data,
    order: response.data.data.order ? normalizeOrder(response.data.data.order) : null,
  };
}

/**
 * 跨站点搜索订单（根据订单号前缀自动检测站点）
 */
export async function searchOrderGlobal(
  query: string
): Promise<{ order: ShopifyOrder | null; query: string; site_code?: string; message?: string }> {
  const response = await apiClient.get<ShopifyResponse<{ order: ShopifyOrderApi | null; query: string; site_code?: string; message?: string }>>(
    '/shopify/orders/global-search',
    { params: { q: query } }
  );
  return {
    ...response.data.data,
    order: response.data.data.order ? normalizeOrder(response.data.data.order) : null,
  };
}

/**
 * 跨站点按邮箱搜索订单
 */
export async function searchOrdersByEmailGlobal(
  email: string,
  limit: number = 10
): Promise<{
  orders: ShopifyOrder[];
  total: number;
  sites_searched: string[];
  sites_with_orders: string[];
}> {
  const response = await apiClient.get<ShopifyResponse<{
    orders: ShopifyOrderApi[];
    total: number;
    sites_searched: string[];
    sites_with_orders: string[];
  }>>(
    '/shopify/orders/global-email-search',
    { params: { email, limit } }
  );
  return {
    ...response.data.data,
    orders: (response.data.data.orders || []).map(normalizeOrder),
  };
}

/**
 * 获取订单详情
 */
export async function getOrderDetail(
  site: string,
  orderId: string
): Promise<{ order: ShopifyOrder | null; message?: string }> {
  const response = await apiClient.get<ShopifyResponse<{ order: ShopifyOrderApi | null; message?: string }>>(
    `/shopify/${site}/orders/${orderId}`
  );
  return {
    ...response.data.data,
    order: response.data.data.order ? normalizeOrder(response.data.data.order) : null,
  };
}

/**
 * 获取订单物流信息
 */
export async function getOrderTracking(
  site: string,
  orderId: string
): Promise<{ tracking: TrackingInfo | null; order_id: string; site_code: string; message?: string }> {
  const response = await apiClient.get<ShopifyResponse<{ tracking: TrackingInfo | null; order_id: string; site_code: string; message?: string }>>(
    `/shopify/${site}/orders/${orderId}/tracking`
  );
  return response.data.data;
}

/**
 * 全站点物流查询（自动遍历所有站点）
 */
export async function getTrackingGlobal(
  orderId: string
): Promise<{ tracking: TrackingInfo | null; order_id: string; site_code?: string; message?: string }> {
  const response = await apiClient.get<ShopifyResponse<{ tracking: TrackingInfo | null; order_id: string; site_code?: string; message?: string }>>(
    '/shopify/tracking',
    { params: { order_id: orderId } }
  );
  return response.data.data;
}

/**
 * 站点健康检查
 */
export async function checkSiteHealth(site: string): Promise<{
  site_code: string;
  status: string;
  message?: string;
}> {
  const response = await apiClient.get<ShopifyResponse<{
    site_code: string;
    status: string;
    message?: string;
  }>>(`/shopify/${site}/health`);
  return response.data.data;
}

/**
 * 全站点健康检查
 */
export async function checkAllSitesHealth(): Promise<{
  sites: Record<string, { api: { status: string } }>;
  summary: { total: number; healthy: number; unhealthy: number };
}> {
  const response = await apiClient.get<ShopifyResponse<{
    sites: Record<string, { api: { status: string } }>;
    summary: { total: number; healthy: number; unhealthy: number };
  }>>('/shopify/health/all');
  return response.data.data;
}

// 导出所有函数
export const shopifyApi = {
  getSites,
  getOrdersByEmail,
  searchOrder,
  searchOrderGlobal,
  searchOrdersByEmailGlobal,
  getOrderDetail,
  getOrderTracking,
  getTrackingGlobal,
  checkSiteHealth,
  checkAllSitesHealth,
};

export default shopifyApi;
