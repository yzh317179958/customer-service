
import React, { useState, useEffect, useRef } from 'react';
import {
  Search, Filter, Send, Image, Paperclip,
  Smile, Sparkles, Bot, Star, Phone,
  Video, MoreVertical, CheckCheck, Clock,
  Bike, Zap, MapPin, Gauge, ShoppingBag,
  History, MessageCircle, AlertCircle, ChevronRight,
  UserCheck, ShieldAlert, Monitor, Plus, Edit3,
  ExternalLink, RefreshCw, Truck, ClipboardList, ChevronDown,
  ChevronUp, UserPlus, Hash, Calendar, Layers, Info, Settings2,
  Box, CreditCard, Activity, HelpCircle, Tag, TrendingUp, Loader2
} from 'lucide-react';
import { useSessionStore } from '../src/stores';
import { sessionsApi } from '../src/api';

const Workspace: React.FC = () => {
  const [inputText, setInputText] = useState('');
  const [aiSuggestions, setAiSuggestions] = useState<string[]>([]);
  const [rightPanelTab, setRightPanelTab] = useState<'info' | 'order' | 'roi'>('info');

  // 创建工单弹窗状态
  const [showTicketModal, setShowTicketModal] = useState(false);
  const [isCreatingTicket, setIsCreatingTicket] = useState(false);
  const [ticketForm, setTicketForm] = useState({
    title: '',
    description: '',
    ticket_type: 'after_sale' as 'after_sale' | 'pre_sale' | 'complaint',
    priority: 'medium' as 'low' | 'medium' | 'high' | 'urgent',
  });

  // 从 sessionStore 获取状态和方法
  const {
    sessions,
    queue,
    currentSession,
    currentMessages,
    isLoading,
    isLoadingMessages,
    error,
    fetchSessions,
    fetchQueue,
    selectSession,
    takeover,
    release,
    sendMessage,
    clearError,
  } = useSessionStore();

  const scrollRef = useRef<HTMLDivElement>(null);

  // 初始化加载会话列表和队列
  useEffect(() => {
    fetchSessions();
    fetchQueue();
  }, [fetchSessions, fetchQueue]);

  // 自动刷新待接入队列（每 5 秒）
  useEffect(() => {
    const interval = setInterval(() => {
      fetchQueue();
    }, 5000);

    return () => clearInterval(interval);
  }, [fetchQueue]);

  // 消息列表滚动到底部
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [currentMessages]);

  // AI 建议功能（Mock 数据，后续接入真实 AI 服务）
  const fetchAiSuggestions = async (text: string) => {
    // Mock AI 建议
    setAiSuggestions([
      "请确认三块电池是否均已充满？",
      "建议检查胎压，这会显著影响里程。",
      "我们提供远程 BMS 诊断，是否现在开启？"
    ]);
  };

  // 发送消息
  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    const success = await sendMessage(inputText.trim());
    if (success) {
      setInputText('');
      fetchAiSuggestions(inputText);
    }
  };

  // 接管会话
  const handleTakeover = async (sessionName: string) => {
    await takeover(sessionName);
  };

  // 释放/结束会话
  const handleRelease = async () => {
    if (currentSession) {
      await release(currentSession.session_name);
    }
  };

  // 打开创建工单弹窗
  const handleOpenTicketModal = () => {
    if (!currentSession) return;

    // 预填充工单信息
    const lastUserMessage = currentMessages
      .filter(m => m.role === 'user')
      .pop();

    setTicketForm({
      title: `${currentSession.customer_name || '访客'}的工单`,
      description: lastUserMessage?.content || '',
      ticket_type: 'after_sale',
      priority: 'medium',
    });
    setShowTicketModal(true);
  };

  // 创建工单
  const handleCreateTicket = async () => {
    if (!currentSession || !ticketForm.title.trim()) return;

    setIsCreatingTicket(true);
    try {
      await sessionsApi.createTicket(currentSession.session_name, {
        title: ticketForm.title,
        description: ticketForm.description,
        ticket_type: ticketForm.ticket_type,
        priority: ticketForm.priority,
      });
      setShowTicketModal(false);
      alert('工单创建成功！');
    } catch (error) {
      console.error('创建工单失败:', error);
      alert('创建工单失败，请重试');
    } finally {
      setIsCreatingTicket(false);
    }
  };

  // 选择会话
  const handleSelectSession = async (sessionName: string) => {
    await selectSession(sessionName);
  };

  // 格式化时间戳
  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
  };

  // 格式化等待时间
  const formatWaitTime = (seconds: number) => {
    if (seconds < 60) return `${seconds}秒`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`;
    return `${Math.floor(seconds / 3600)}小时`;
  };

  return (
    <div className="flex h-full w-full bg-[#f8fafc] overflow-hidden">
      {/* 左侧会话列表 */}
      <div className="w-[280px] border-r border-slate-200 bg-white flex flex-col shrink-0">
        {/* 待接入队列 */}
        {queue.length > 0 && (
          <div className="border-b border-slate-200">
            <div className="h-10 flex items-center px-4 bg-fiido-light border-b border-fiido/10">
              <span className="text-[11px] font-black text-fiido uppercase tracking-widest flex items-center gap-2">
                <Clock size={12} className="animate-pulse" />
                待接入 ({queue.length})
              </span>
            </div>
            <div className="max-h-[200px] overflow-y-auto">
              {queue.map(item => {
                // 适配后端返回格式
                const customerName = (item as any).user_profile?.nickname || item.customer_name || '访客';
                const waitTime = (item as any).wait_time_seconds || item.wait_time || 0;
                const reason = item.escalation_reason || (item as any).last_message || '请求人工服务';

                return (
                <div key={item.session_name} className="p-3 border-b border-slate-50 hover:bg-slate-50 cursor-pointer group">
                  <div className="flex justify-between items-start">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[12px] font-bold truncate">{customerName}</span>
                        {item.channel && (
                          <span className="text-[9px] px-1.5 py-0.5 bg-slate-100 text-slate-500 rounded font-bold">{item.channel}</span>
                        )}
                        {(item as any).is_vip && (
                          <span className="text-[9px] px-1.5 py-0.5 bg-amber-100 text-amber-600 rounded font-bold">VIP</span>
                        )}
                      </div>
                      <p className="text-[10px] text-slate-500 truncate mt-1">{reason}</p>
                      <p className="text-[9px] text-fiido font-bold mt-1">等待 {formatWaitTime(waitTime)}</p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleTakeover(item.session_name);
                      }}
                      className="px-3 py-1.5 bg-fiido text-white text-[10px] font-bold rounded-lg hover:bg-fiido-dark transition-all shadow-sm"
                    >
                      接管
                    </button>
                  </div>
                </div>
              )})}
            </div>
          </div>
        )}

        {/* 我的会话 */}
        <div className="h-12 flex items-center px-4 border-b border-slate-100 bg-slate-50/50">
          <span className="text-[11px] font-black text-slate-400 uppercase tracking-widest">我的会话 ({sessions.length})</span>
          <button
            onClick={() => { fetchSessions(); fetchQueue(); }}
            className="ml-auto p-1 hover:bg-slate-200 rounded text-slate-400 hover:text-slate-600"
          >
            <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {isLoading && sessions.length === 0 ? (
            <div className="flex items-center justify-center h-32 text-slate-400">
              <Loader2 size={20} className="animate-spin" />
            </div>
          ) : sessions.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-32 text-slate-400">
              <MessageCircle size={24} className="mb-2 opacity-50" />
              <p className="text-[11px] font-bold">暂无会话</p>
            </div>
          ) : (
            sessions.map(s => (
              <div
                key={s.session_name}
                onClick={() => handleSelectSession(s.session_name)}
                className={`p-3 border-b border-slate-50 cursor-pointer relative transition-all ${
                  currentSession?.session_name === s.session_name
                    ? 'bg-fiido-light'
                    : 'hover:bg-slate-50'
                }`}
              >
                {currentSession?.session_name === s.session_name && (
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-fiido"></div>
                )}
                <div className="flex gap-3">
                  <img
                    src={s.customer_avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${s.customer_name || s.session_name}`}
                    className="w-10 h-10 rounded-lg"
                    alt=""
                  />
                  <div className="min-w-0 flex-1">
                    <div className="flex justify-between items-center">
                      <span className="text-[12px] font-bold truncate">{s.customer_name || '访客'}</span>
                      <span className="text-[10px] text-slate-400">{formatTime(s.updated_at)}</span>
                    </div>
                    <p className="text-[11px] text-slate-500 truncate mt-0.5">
                      {s.last_message?.content || '暂无消息'}
                    </p>
                    {s.unread_count && s.unread_count > 0 && (
                      <span className="absolute right-3 top-3 w-5 h-5 bg-fiido text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                        {s.unread_count}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* 主对话区 */}
      <div className="flex-1 flex flex-col min-w-0 bg-white shadow-inner">
        {currentSession ? (
          <>
            {/* 对话头部 */}
            <div className="h-12 border-b border-slate-200 flex items-center justify-between px-6 bg-white z-10">
              <div className="flex items-center gap-3">
                <span className="text-[13px] font-bold text-slate-800">{currentSession.customer_name || '访客'}</span>
                {currentSession.channel && (
                  <span className="text-[10px] px-2 py-0.5 bg-slate-100 text-slate-500 rounded font-bold">{currentSession.channel}</span>
                )}
                <div className="flex items-center gap-1.5 px-2 py-0.5 bg-fiido/5 border border-fiido/10 rounded text-fiido text-[10px] font-black">
                  <span className="w-1.5 h-1.5 bg-fiido rounded-full animate-pulse"></span>
                  {currentSession.status === 'manual_live' ? '服务中' : currentSession.status}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button className="text-[11px] font-black text-slate-400 hover:text-fiido uppercase border border-slate-100 px-3 py-1 rounded">知识库匹配</button>
                <button
                  onClick={handleRelease}
                  className="bg-fiido text-white px-4 py-1.5 rounded text-[11px] font-black hover:opacity-90 shadow-sm"
                >
                  结束会话
                </button>
              </div>
            </div>

            {/* 消息列表 */}
            <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6 bg-[#fcfdfe] custom-scrollbar">
              {isLoadingMessages ? (
                <div className="flex items-center justify-center h-32 text-slate-400">
                  <Loader2 size={20} className="animate-spin" />
                </div>
              ) : currentMessages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-32 text-slate-400">
                  <MessageCircle size={24} className="mb-2 opacity-50" />
                  <p className="text-[11px] font-bold">暂无消息</p>
                </div>
              ) : (
                currentMessages.map((m, index) => (
                  <div key={m.id || index} className={`flex ${m.role === 'agent' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] flex gap-3 ${m.role === 'agent' ? 'flex-row-reverse' : ''}`}>
                      <img
                        src={m.role === 'agent'
                          ? 'https://api.dicebear.com/7.x/avataaars/svg?seed=Agent'
                          : currentSession.customer_avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${currentSession.customer_name}`
                        }
                        className="w-8 h-8 rounded shadow-sm shrink-0"
                        alt=""
                      />
                      <div className={`p-3 rounded-2xl text-[12px] leading-relaxed shadow-sm ${
                        m.role === 'agent'
                          ? 'bg-fiido-black text-white rounded-tr-none'
                          : m.role === 'assistant'
                            ? 'bg-blue-50 border border-blue-100 text-slate-700 rounded-tl-none'
                            : 'bg-white border border-slate-200 text-slate-700 rounded-tl-none font-medium'
                      }`}>
                        {m.role === 'assistant' && (
                          <div className="flex items-center gap-1 mb-1 text-[10px] text-blue-500 font-bold">
                            <Bot size={12} /> AI 助手
                          </div>
                        )}
                        {m.content}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* 输入区域 */}
            <div className="p-4 border-t border-slate-100 bg-white">
              {aiSuggestions.length > 0 && (
                <div className="flex gap-2 mb-3 overflow-x-auto no-scrollbar py-1">
                  <span className="bg-slate-50 text-slate-400 px-2 py-1 rounded text-[9px] font-black uppercase flex items-center gap-1 shrink-0 border border-slate-200">
                    <Bot size={12}/> AI 灵感
                  </span>
                  {aiSuggestions.map((s, i) => (
                    <button
                      key={i}
                      onClick={() => setInputText(s)}
                      className="whitespace-nowrap bg-white border border-slate-200 px-3 py-1 rounded text-[10px] font-bold text-slate-600 hover:border-fiido hover:text-fiido transition-all shadow-sm"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
              <div className="bg-slate-50 rounded-xl border border-slate-200 focus-within:border-fiido transition-all">
                <textarea
                  value={inputText}
                  onChange={e => setInputText(e.target.value)}
                  placeholder="在此输入回复... (Shift+Enter 换行)"
                  className="w-full bg-transparent p-3 text-[12px] h-20 outline-none resize-none font-medium"
                  onKeyDown={e => { if(e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage(); }}}
                />
                <div className="flex items-center justify-between p-3 border-t border-slate-100/50">
                  <div className="flex gap-3 text-slate-400">
                    <Smile size={16} className="cursor-pointer hover:text-fiido"/>
                    <Image size={16} className="cursor-pointer hover:text-fiido"/>
                    <Paperclip size={16} className="cursor-pointer hover:text-fiido"/>
                    <Monitor size={16} className="cursor-pointer hover:text-fiido"/>
                  </div>
                  <button
                    onClick={handleSendMessage}
                    disabled={!inputText.trim()}
                    className="bg-fiido text-white px-4 py-1.5 rounded font-black text-[11px] flex items-center gap-2 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    发送 <Send size={12}/>
                  </button>
                </div>
              </div>
            </div>
          </>
        ) : (
          /* 未选中会话时的占位 */
          <div className="flex-1 flex flex-col items-center justify-center text-slate-400">
            <MessageCircle size={48} className="mb-4 opacity-30" />
            <p className="text-[14px] font-bold">选择一个会话开始服务</p>
            <p className="text-[12px] mt-1">或从待接入队列中接管会话</p>
          </div>
        )}
      </div>

      {/* 右侧业务台 */}
      {currentSession && (
        <div className="w-[340px] border-l border-slate-200 bg-white flex flex-col shrink-0 overflow-hidden">
          <div className="p-4 border-b border-slate-50 flex items-center gap-4">
            <div className="flex-1">
              <h4 className="text-[13px] font-black text-slate-800">业务洞察</h4>
              <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-0.5">Business Intelligence</p>
            </div>
            <button className="p-2 hover:bg-slate-100 rounded text-slate-400"><Settings2 size={16}/></button>
          </div>

          <div className="flex border-b border-slate-100 bg-slate-50/30">
            {['info', 'order', 'roi'].map(t => (
              <button
                key={t}
                onClick={() => setRightPanelTab(t as any)}
                className={`flex-1 py-3 text-[10px] font-black uppercase tracking-tighter transition-all border-b-2 ${rightPanelTab === t ? 'text-fiido border-fiido bg-white' : 'text-slate-400 border-transparent hover:text-slate-600'}`}
              >
                {t === 'info' ? '客户档案' : t === 'order' ? '订单集成' : 'AI 价值收益'}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
            {rightPanelTab === 'info' && (
              <div className="space-y-4 animate-in fade-in duration-300">
                <div className="bg-white border border-slate-100 rounded-xl p-4 shadow-sm space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-[11px] font-bold text-slate-400">标签分类</span>
                    <button className="text-[10px] text-fiido font-black">+ 快速打标</button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {(currentSession.tags || []).map(tag => (
                      <span key={tag} className="px-2 py-0.5 bg-fiido-light text-fiido rounded text-[10px] font-bold border border-fiido/10">{tag}</span>
                    ))}
                    {(!currentSession.tags || currentSession.tags.length === 0) && (
                      <span className="text-[10px] text-slate-400">暂无标签</span>
                    )}
                  </div>
                </div>

                {/* 客户信息 */}
                <div className="bg-white border border-slate-100 rounded-xl p-4 shadow-sm space-y-3">
                  <div className="text-[11px] font-bold text-slate-400">客户信息</div>
                  <div className="space-y-2 text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-slate-500">邮箱</span>
                      <span className="font-bold text-slate-700">{currentSession.customer_email || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">渠道</span>
                      <span className="font-bold text-slate-700">{currentSession.channel || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">创建时间</span>
                      <span className="font-bold text-slate-700">{formatTime(currentSession.created_at)}</span>
                    </div>
                  </div>
                </div>

                {/* 转人工原因 */}
                {currentSession.escalation && (
                  <div className="bg-fiido-light border border-fiido/20 rounded-xl p-4 shadow-sm">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertCircle size={14} className="text-fiido" />
                      <span className="text-[11px] font-bold text-fiido">转人工原因</span>
                    </div>
                    <p className="text-[11px] text-fiido-dark">{currentSession.escalation.reason}</p>
                    {currentSession.escalation.details && (
                      <p className="text-[10px] text-fiido mt-1">{currentSession.escalation.details}</p>
                    )}
                  </div>
                )}

                <div className="bg-slate-900 rounded-xl p-4 text-white shadow-xl relative overflow-hidden group">
                  <div className="absolute right-0 bottom-0 opacity-5 group-hover:scale-110 transition-transform"><Sparkles size={60}/></div>
                  <div className="flex items-center gap-2 mb-2"><Sparkles size={14} className="text-fiido"/><span className="text-[10px] font-black text-fiido uppercase tracking-widest">AI 坐席建议</span></div>
                  <p className="text-[11px] font-medium leading-relaxed text-slate-300">系统正在分析客户意图，稍后为您提供智能建议。</p>
                  <button className="w-full mt-4 py-2 bg-fiido text-white rounded font-black text-[10px] uppercase shadow-lg shadow-fiido/20">获取 AI 建议</button>
                </div>
              </div>
            )}

            {rightPanelTab === 'order' && (
              <div className="space-y-3 animate-in fade-in duration-300">
                <div className="flex flex-col items-center justify-center py-8 text-slate-400">
                  <ShoppingBag size={32} className="mb-3 opacity-30" />
                  <p className="text-[11px] font-bold">暂无关联订单</p>
                  <p className="text-[10px] mt-1">可通过邮箱查询客户订单</p>
                </div>
                <button className="w-full py-2.5 border border-dashed border-slate-200 rounded-xl text-[10px] font-black text-slate-400 hover:border-fiido hover:text-fiido transition-all uppercase tracking-widest">
                  + 查询 Shopify 订单
                </button>
              </div>
            )}

            {rightPanelTab === 'roi' && (
              <div className="space-y-4 animate-in fade-in duration-300">
                <div className="bg-[#1e293b] rounded-xl p-5 text-white shadow-xl">
                  <div className="flex items-center gap-2 mb-6"><TrendingUp size={16} className="text-emerald-400"/><span className="text-[10px] font-black uppercase tracking-widest">AI 数字化降本看板</span></div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <p className="text-[9px] text-slate-500 font-black uppercase">本月节省人工</p>
                      <p className="text-2xl font-black text-white">--<span className="text-xs ml-0.5 text-slate-500">h</span></p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-[9px] text-slate-500 font-black uppercase">响应时效优化</p>
                      <p className="text-2xl font-black text-emerald-400">--<span className="text-xs ml-0.5 text-emerald-500/50">%</span></p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="p-4 border-t border-slate-100 bg-white grid grid-cols-2 gap-2">
            <button
              onClick={handleOpenTicketModal}
              className="py-2.5 bg-fiido-black text-white text-[11px] font-black rounded-lg flex items-center justify-center gap-2 hover:bg-slate-800 transition-all active:scale-95 shadow-lg"
            >
              <Edit3 size={14}/> 创建工单
            </button>
            <button className="py-2.5 bg-slate-100 text-slate-600 text-[11px] font-black rounded-lg flex items-center justify-center gap-2 hover:bg-slate-200 transition-all border border-slate-200"><History size={14}/> 服务历史</button>
          </div>
        </div>
      )}

      {/* 创建工单弹窗 */}
      {showTicketModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setShowTicketModal(false)}>
          <div className="bg-white rounded-2xl w-full max-w-md p-6 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-black text-slate-800">从会话创建工单</h2>
              <button
                onClick={() => setShowTicketModal(false)}
                className="p-1.5 hover:bg-slate-100 rounded-lg text-slate-400"
              >
                ×
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-500 mb-2">工单标题 *</label>
                <input
                  type="text"
                  value={ticketForm.title}
                  onChange={(e) => setTicketForm({...ticketForm, title: e.target.value})}
                  placeholder="请输入工单标题"
                  className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-fiido/20 focus:border-fiido"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 mb-2">问题描述</label>
                <textarea
                  value={ticketForm.description}
                  onChange={(e) => setTicketForm({...ticketForm, description: e.target.value})}
                  placeholder="请描述客户问题..."
                  rows={3}
                  className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-fiido/20 focus:border-fiido resize-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 mb-2">工单类型</label>
                  <select
                    value={ticketForm.ticket_type}
                    onChange={(e) => setTicketForm({...ticketForm, ticket_type: e.target.value as any})}
                    className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-fiido/20 focus:border-fiido"
                  >
                    <option value="pre_sale">售前咨询</option>
                    <option value="after_sale">售后服务</option>
                    <option value="complaint">投诉建议</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 mb-2">优先级</label>
                  <select
                    value={ticketForm.priority}
                    onChange={(e) => setTicketForm({...ticketForm, priority: e.target.value as any})}
                    className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-fiido/20 focus:border-fiido"
                  >
                    <option value="low">低</option>
                    <option value="medium">中</option>
                    <option value="high">高</option>
                    <option value="urgent">紧急</option>
                  </select>
                </div>
              </div>

              {/* 会话信息 */}
              {currentSession && (
                <div className="p-3 bg-slate-50 rounded-xl text-xs text-slate-500">
                  <p>关联会话: {currentSession.session_name}</p>
                  <p>客户: {currentSession.customer_name || '访客'}</p>
                </div>
              )}
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowTicketModal(false)}
                className="px-5 py-2.5 text-sm font-bold text-slate-500 hover:bg-slate-100 rounded-xl transition-all"
              >
                取消
              </button>
              <button
                onClick={handleCreateTicket}
                disabled={isCreatingTicket || !ticketForm.title.trim()}
                className="px-6 py-2.5 bg-fiido text-white text-sm font-bold rounded-xl hover:scale-[1.02] active:scale-95 transition-all disabled:opacity-50 flex items-center gap-2"
              >
                {isCreatingTicket && <Loader2 size={14} className="animate-spin"/>}
                创建工单
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Workspace;
