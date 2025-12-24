/**
 * 订单面板组件
 *
 * 功能：
 * - 通过邮箱或订单号查询客户订单（跨站点）
 * - 订单列表展示
 * - 订单详情查看
 * - 物流信息查询
 */

import React, { useState, useEffect } from 'react';
import {
  Search, ShoppingBag, Package, Truck, ChevronDown, ChevronUp,
  ExternalLink, Loader2, RefreshCw, Globe, Clock, CreditCard,
  MapPin, Phone, Mail, Tag, Box, CheckCircle, XCircle, AlertCircle,
  Link2
} from 'lucide-react';
import { shopifyApi, ShopifyOrder, TrackingInfo } from '../src/api';

// 订单状态颜色
const STATUS_COLORS: Record<string, string> = {
  paid: 'bg-green-50 text-green-600 border-green-200',
  pending: 'bg-yellow-50 text-yellow-600 border-yellow-200',
  refunded: 'bg-red-50 text-red-600 border-red-200',
  partially_refunded: 'bg-orange-50 text-orange-600 border-orange-200',
  voided: 'bg-slate-50 text-slate-600 border-slate-200',
};

// 物流状态颜色
const FULFILLMENT_COLORS: Record<string, string> = {
  fulfilled: 'bg-green-50 text-green-600',
  partial: 'bg-yellow-50 text-yellow-600',
  unfulfilled: 'bg-slate-50 text-slate-500',
};

// 物流状态文本
const FULFILLMENT_TEXT: Record<string, string> = {
  fulfilled: '已发货',
  partial: '部分发货',
  unfulfilled: '未发货',
};

interface OrderPanelProps {
  customerEmail?: string;
  onOrderSelect?: (order: ShopifyOrder) => void;
}

const OrderPanel: React.FC<OrderPanelProps> = ({
  customerEmail,
  onOrderSelect,
}) => {
  const [searchQuery, setSearchQuery] = useState(customerEmail || '');
  const [searchType, setSearchType] = useState<'email' | 'order'>('email');
  const [orders, setOrders] = useState<ShopifyOrder[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  // 展开的订单ID
  const [expandedOrderId, setExpandedOrderId] = useState<string | null>(null);

  // 物流信息
  const [trackingInfo, setTrackingInfo] = useState<Record<string, TrackingInfo | null>>({});
  const [loadingTracking, setLoadingTracking] = useState<string | null>(null);

  // 当客户邮箱变化时更新搜索框
  useEffect(() => {
    if (customerEmail && customerEmail !== searchQuery) {
      setSearchQuery(customerEmail);
      setSearchType('email');
      // 自动搜索
      handleSearch(customerEmail, 'email');
    }
  }, [customerEmail]);

  // 自动检测搜索类型
  const detectSearchType = (query: string): 'email' | 'order' => {
    if (query.includes('@')) {
      return 'email';
    }
    return 'order';
  };

  // 输入变化时自动切换类型
  const handleInputChange = (value: string) => {
    setSearchQuery(value);
    setSearchType(detectSearchType(value));
  };

  // 搜索订单
  const handleSearch = async (query?: string, type?: 'email' | 'order') => {
    const targetQuery = query || searchQuery;
    const targetType = type || searchType;

    if (!targetQuery.trim()) {
      setError('请输入邮箱或订单号');
      return;
    }

    // 验证
    if (targetType === 'email' && !targetQuery.includes('@')) {
      setError('请输入有效的邮箱地址');
      return;
    }

    if (targetType === 'order' && targetQuery.length < 3) {
      setError('订单号至少需要3个字符');
      return;
    }

    setIsLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      if (targetType === 'email') {
        // 按邮箱搜索
        const result = await shopifyApi.searchOrdersByEmailGlobal(targetQuery, 20);
        setOrders(result.orders || []);
        if (result.orders.length === 0) {
          setError('未找到该邮箱的订单');
        }
      } else {
        // 按订单号搜索
        const result = await shopifyApi.searchOrderGlobal(targetQuery);
        if (result.order) {
          setOrders([result.order]);
        } else {
          setOrders([]);
          setError(result.message || '未找到该订单');
        }
      }
    } catch (err: any) {
      console.error('搜索订单失败:', err);
      setError('查询失败，请重试');
      setOrders([]);
    } finally {
      setIsLoading(false);
    }
  };

  // 获取物流信息
  const handleGetTracking = async (order: ShopifyOrder) => {
    if (!order.id || !order.site_code) return;

    setLoadingTracking(order.id);
    try {
      const result = await shopifyApi.getOrderTracking(order.site_code, order.id);
      setTrackingInfo(prev => ({ ...prev, [order.id]: result.tracking }));
    } catch (err) {
      console.error('获取物流信息失败:', err);
      setTrackingInfo(prev => ({ ...prev, [order.id]: null }));
    } finally {
      setLoadingTracking(null);
    }
  };

  // 切换订单展开
  const toggleExpand = (orderId: string) => {
    if (expandedOrderId === orderId) {
      setExpandedOrderId(null);
    } else {
      setExpandedOrderId(orderId);
      // 如果还没有物流信息，自动获取
      const order = orders.find(o => o.id === orderId);
      const existing = trackingInfo[orderId];
      const hasEvents = (existing?.events?.length || 0) > 0;
      if (order && (!existing || !hasEvents)) {
        handleGetTracking(order);
      }
    }
  };

  // 格式化时间
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
  };

  // 格式化金额
  const formatPrice = (price: string, currency: string) => {
    return `${currency} ${parseFloat(price).toFixed(2)}`;
  };

  return (
    <div className="space-y-4 animate-in fade-in duration-300">
      {/* 搜索框 */}
      <div className="space-y-2">
        <div className="relative">
          {searchType === 'email' ? (
            <Mail size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          ) : (
            <Package size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          )}
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => handleInputChange(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="输入邮箱或订单号查询..."
            className="w-full pl-9 pr-20 py-2.5 text-[11px] bg-white border border-slate-200 rounded-xl outline-none focus:border-fiido focus:ring-2 focus:ring-fiido/10 transition-all"
          />
          <button
            onClick={() => handleSearch()}
            disabled={isLoading}
            className="absolute right-1.5 top-1/2 -translate-y-1/2 px-3 py-1.5 bg-fiido text-white text-[10px] font-bold rounded-lg hover:opacity-90 disabled:opacity-50 flex items-center gap-1"
          >
            {isLoading ? <Loader2 size={12} className="animate-spin" /> : <Search size={12} />}
            查询
          </button>
        </div>
        {/* 搜索类型提示 */}
        <div className="flex items-center gap-2 px-1">
          <span className={`text-[9px] px-2 py-0.5 rounded-full font-bold ${
            searchType === 'email'
              ? 'bg-blue-50 text-blue-600'
              : 'bg-purple-50 text-purple-600'
          }`}>
            {searchType === 'email' ? '按邮箱查询' : '按订单号查询'}
          </span>
          <span className="text-[9px] text-slate-400">
            {searchType === 'email' ? '跨站点搜索客户所有订单' : '自动识别站点'}
          </span>
        </div>
      </div>

      {/* 结果区域 */}
      {isLoading ? (
        <div className="flex items-center justify-center py-8 text-slate-400">
          <Loader2 size={20} className="animate-spin" />
        </div>
      ) : error && hasSearched ? (
        <div className="flex flex-col items-center justify-center py-8 text-slate-400">
          <ShoppingBag size={32} className="mb-3 opacity-30" />
          <p className="text-[11px] font-bold">{error}</p>
          <button
            onClick={() => handleSearch()}
            className="mt-2 text-[10px] text-fiido font-bold hover:underline"
          >
            重试
          </button>
        </div>
      ) : orders.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-8 text-slate-400">
          <ShoppingBag size={32} className="mb-3 opacity-30" />
          <p className="text-[11px] font-bold">
            {hasSearched ? '未找到订单' : '查询客户订单'}
          </p>
          <p className="text-[10px] mt-1">支持邮箱或订单号查询</p>
        </div>
      ) : (
        <div className="space-y-2">
          {/* 结果统计 */}
          <div className="flex items-center justify-between text-[10px] text-slate-400 px-1">
            <span>找到 {orders.length} 个订单</span>
            <button
              onClick={() => handleSearch()}
              className="flex items-center gap-1 hover:text-fiido"
            >
              <RefreshCw size={10} /> 刷新
            </button>
          </div>

          {/* 订单列表 */}
          {orders.map((order) => (
            <div
              key={order.id}
              className="bg-white rounded-xl border border-slate-100 overflow-hidden hover:shadow-md transition-all"
            >
              {/* 订单头部 */}
              <div
                onClick={() => toggleExpand(order.id)}
                className="p-3 cursor-pointer hover:bg-slate-50 transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] font-bold text-slate-800">{order.name}</span>
                      {order.site_code && (
                        <span className="text-[9px] px-1.5 py-0.5 bg-slate-100 text-slate-500 rounded font-bold uppercase">
                          {order.site_code}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`text-[9px] px-1.5 py-0.5 rounded border font-bold ${STATUS_COLORS[order.financial_status] || STATUS_COLORS.pending}`}>
                        {order.financial_status === 'paid' ? '已支付' : order.financial_status}
                      </span>
                      {order.fulfillment_status && (
                        <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold ${FULFILLMENT_COLORS[order.fulfillment_status] || FULFILLMENT_COLORS.unfulfilled}`}>
                          {FULFILLMENT_TEXT[order.fulfillment_status] || order.fulfillment_status}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-[11px] font-bold text-slate-800">
                      {formatPrice(order.total_price, order.currency)}
                    </p>
                    <p className="text-[9px] text-slate-400 mt-0.5">
                      {formatDate(order.created_at)}
                    </p>
                  </div>
                  <div className="ml-1 text-slate-400">
                    {expandedOrderId === order.id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </div>
                </div>
              </div>

              {/* 订单详情（展开时显示） */}
              {expandedOrderId === order.id && (
                <div className="px-3 pb-3 border-t border-slate-50 bg-slate-50/50">
                  {/* 商品列表 */}
                  <div className="py-2 space-y-2">
                    <p className="text-[10px] font-bold text-slate-500 uppercase">商品明细</p>
                    {order.line_items.map((item, idx) => (
                      <div key={idx} className="flex items-center gap-2 bg-white rounded-lg p-2">
                        {item.image_url ? (
                          <img src={item.image_url} alt="" className="w-10 h-10 rounded object-cover" />
                        ) : (
                          <div className="w-10 h-10 rounded bg-slate-100 flex items-center justify-center">
                            <Box size={16} className="text-slate-300" />
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="text-[10px] font-bold text-slate-700 truncate">{item.title}</p>
                          {item.variant_title && (
                            <p className="text-[9px] text-slate-400">{item.variant_title}</p>
                          )}
                        </div>
                        <div className="text-right shrink-0">
                          <p className="text-[10px] font-bold text-slate-600">x{item.quantity}</p>
                          <p className="text-[9px] text-slate-400">{order.currency} {item.price}</p>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* 收货地址 */}
                  {order.shipping_address && (
                    <div className="py-2 border-t border-slate-100">
                      <p className="text-[10px] font-bold text-slate-500 uppercase mb-1">收货地址</p>
                      <div className="flex items-start gap-1.5 text-[10px] text-slate-600">
                        <MapPin size={12} className="shrink-0 mt-0.5 text-slate-400" />
                        <div>
                          <p>{order.shipping_address.name}</p>
                          <p>{order.shipping_address.address1}</p>
                          {order.shipping_address.address2 && <p>{order.shipping_address.address2}</p>}
                          <p>
                            {order.shipping_address.city}, {order.shipping_address.province} {order.shipping_address.zip}
                          </p>
                          <p>{order.shipping_address.country}</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* 物流信息 */}
                  {order.fulfillment_status && (
                    <div className="py-2 border-t border-slate-100">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-[10px] font-bold text-slate-500 uppercase">物流信息</p>
                        {loadingTracking === order.id && (
                          <Loader2 size={12} className="animate-spin text-slate-400" />
                        )}
                      </div>
                      {trackingInfo[order.id] ? (
                        <div className="space-y-2">
                          <div className="flex items-center gap-2 bg-white rounded-lg p-2">
                            <Truck size={14} className="text-fiido shrink-0" />
                            <div className="flex-1">
                              <p className="text-[10px] font-bold text-slate-700">
                                {trackingInfo[order.id]?.tracking_company || '物流公司'}
                              </p>
                              <p className="text-[9px] text-slate-500">
                                {trackingInfo[order.id]?.tracking_number || '暂无单号'}
                              </p>
                            </div>
                            {trackingInfo[order.id]?.tracking_url && (
                              <a
                                href={trackingInfo[order.id]?.tracking_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-fiido hover:underline"
                              >
                                <ExternalLink size={12} />
                              </a>
                            )}
                          </div>
                          {/* 物流轨迹 */}
                          {trackingInfo[order.id]?.events && trackingInfo[order.id]!.events!.length > 0 ? (
                            <div className="space-y-1 pl-2 max-h-40 overflow-y-auto">
                              {trackingInfo[order.id]!.events!.map((event, idx) => (
                                <div key={idx} className="flex items-start gap-2 text-[9px]">
                                  <div className="w-1.5 h-1.5 rounded-full bg-fiido shrink-0 mt-1" />
                                  <div>
                                    <p className="text-slate-600">{event.description}</p>
                                    <p className="text-slate-400">{event.timestamp}{event.location ? ` · ${event.location}` : ''}</p>
                                  </div>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <div className="text-[10px] text-slate-400 text-center py-2">
                              {loadingTracking === order.id ? '加载中...' : '暂无物流轨迹'}
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="text-[10px] text-slate-400 text-center py-2">
                          {loadingTracking === order.id ? '加载中...' : '暂无物流信息'}
                        </div>
                      )}
                    </div>
                  )}

                  {/* 关联此订单按钮 */}
                  <div className="pt-2 border-t border-slate-100">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onOrderSelect?.(order);
                      }}
                      className="w-full py-2 bg-fiido/10 text-fiido text-[10px] font-bold rounded-lg hover:bg-fiido/20 transition-all flex items-center justify-center gap-1"
                    >
                      <Link2 size={12} />
                      关联此订单
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default OrderPanel;
