
import React, { useState, useEffect } from 'react';
import {
  Plus, Search, Filter, LayoutGrid, List, ArrowUpRight, Clock, AlertCircle,
  MoreHorizontal, User, RefreshCw, Loader2, X, Edit3
} from 'lucide-react';
import { useTicketStore } from '../src/stores';
import { TicketStatus, TicketPriority, TicketType, TicketInfo } from '../src/api';

// 状态显示名称映射
const statusLabels: Record<TicketStatus, string> = {
  pending: '待处理',
  in_progress: '处理中',
  waiting_customer: '等待客户',
  waiting_vendor: '等待供应商',
  resolved: '已解决',
  closed: '已关闭',
  archived: '已归档',
};

// 优先级显示名称映射
const priorityLabels: Record<TicketPriority, string> = {
  urgent: '紧急',
  high: '高',
  medium: '中',
  low: '低',
};

// 工单类型显示名称映射
const typeLabels: Record<TicketType, string> = {
  pre_sale: '售前咨询',
  after_sale: '售后服务',
  complaint: '投诉建议',
};

// 看板视图的状态列表
const kanbanStatuses: TicketStatus[] = ['pending', 'in_progress', 'waiting_customer', 'resolved', 'closed'];

const TicketsView: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [createForm, setCreateForm] = useState({
    title: '',
    description: '',
    ticket_type: 'after_sale' as TicketType,
    priority: 'medium' as TicketPriority,
    customer_name: '',
    customer_email: '',
  });

  // 编辑弹窗状态
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingTicket, setEditingTicket] = useState<TicketInfo | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const [editForm, setEditForm] = useState({
    status: 'pending' as TicketStatus,
    priority: 'medium' as TicketPriority,
    assigned_agent_name: '',
  });

  // 从 ticketStore 获取状态和方法
  const {
    tickets,
    total,
    isLoading,
    error,
    viewMode,
    fetchTickets,
    searchTickets,
    setViewMode,
    refreshTickets,
    clearError,
    createTicket,
    updateTicket,
  } = useTicketStore();

  // 初始化加载工单列表
  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  // 搜索防抖
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchQuery.trim()) {
        searchTickets(searchQuery.trim());
      } else {
        refreshTickets();
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery, searchTickets, refreshTickets]);

  const getPriorityColor = (priority: TicketPriority) => {
    switch (priority) {
      case 'urgent': return 'text-red-600 bg-red-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'medium': return 'text-blue-600 bg-blue-100';
      default: return 'text-slate-600 bg-slate-100';
    }
  };

  const getStatusColor = (status: TicketStatus) => {
    switch (status) {
      case 'pending': return 'bg-fiido/10 text-fiido';
      case 'in_progress': return 'bg-blue-50 text-blue-600';
      case 'waiting_customer': return 'bg-amber-50 text-amber-600';
      case 'waiting_vendor': return 'bg-purple-50 text-purple-600';
      case 'resolved': return 'bg-green-50 text-green-600';
      case 'closed': return 'bg-slate-100 text-slate-500';
      case 'archived': return 'bg-slate-50 text-slate-400';
      default: return 'bg-slate-100 text-slate-500';
    }
  };

  // 格式化时间戳
  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // 计算 SLA 倒计时（简化版，后续可接入真实 SLA 数据）
  const getSLARemaining = (createdAt: number, priority: TicketPriority) => {
    const slaHours: Record<TicketPriority, number> = {
      urgent: 2,
      high: 8,
      medium: 24,
      low: 72,
    };
    const deadline = createdAt + slaHours[priority] * 3600;
    const remaining = deadline - Date.now() / 1000;

    if (remaining <= 0) return { text: '已超时', isOverdue: true };

    const hours = Math.floor(remaining / 3600);
    const minutes = Math.floor((remaining % 3600) / 60);

    if (hours > 24) {
      const days = Math.floor(hours / 24);
      return { text: `${days}天`, isOverdue: false };
    }
    return { text: `${hours}小时${minutes}分`, isOverdue: remaining < 3600 };
  };

  // 处理创建工单
  const handleCreateTicket = async () => {
    if (!createForm.title.trim()) {
      alert('请输入工单标题');
      return;
    }
    setIsCreating(true);
    try {
      const success = await createTicket({
        title: createForm.title,
        description: createForm.description,
        ticket_type: createForm.ticket_type,
        priority: createForm.priority,
        customer: {
          name: createForm.customer_name || undefined,
          email: createForm.customer_email || undefined,
        },
      });
      if (success) {
        setShowCreateModal(false);
        setCreateForm({
          title: '',
          description: '',
          ticket_type: 'after_sale',
          priority: 'medium',
          customer_name: '',
          customer_email: '',
        });
      }
    } finally {
      setIsCreating(false);
    }
  };

  // 打开编辑弹窗
  const handleOpenEdit = (ticket: TicketInfo) => {
    setEditingTicket(ticket);
    setEditForm({
      status: ticket.status,
      priority: ticket.priority,
      assigned_agent_name: ticket.assigned_agent_name || '',
    });
    setShowEditModal(true);
  };

  // 处理更新工单
  const handleUpdateTicket = async () => {
    if (!editingTicket) return;

    setIsUpdating(true);
    try {
      const success = await updateTicket(editingTicket.ticket_id, {
        status: editForm.status,
        priority: editForm.priority,
        assigned_agent_name: editForm.assigned_agent_name || undefined,
      });
      if (success) {
        setShowEditModal(false);
        setEditingTicket(null);
      }
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white animate-in slide-in-from-right-4 duration-500 font-sans">
      <div className="p-8 border-b border-slate-100">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-brand font-black text-slate-800 tracking-tighter">售后工单中心</h1>
            <p className="text-[11px] text-slate-400 font-bold uppercase tracking-[0.2em] mt-2">
              共 {total} 条工单
            </p>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => refreshTickets()}
              className="p-2 hover:bg-slate-100 rounded-xl text-slate-400 hover:text-slate-600 transition-all"
              disabled={isLoading}
            >
              <RefreshCw size={20} className={isLoading ? 'animate-spin' : ''} />
            </button>
            <div className="bg-slate-100 p-1.5 rounded-2xl flex shadow-inner">
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded-xl transition-all ${viewMode === 'list' ? 'bg-white shadow-xl text-fiido' : 'text-slate-400 hover:text-slate-600'}`}
              >
                <List size={20}/>
              </button>
              <button
                onClick={() => setViewMode('kanban')}
                className={`p-2 rounded-xl transition-all ${viewMode === 'kanban' ? 'bg-white shadow-xl text-fiido' : 'text-slate-400 hover:text-slate-600'}`}
              >
                <LayoutGrid size={20}/>
              </button>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-fiido text-white px-8 py-3 rounded-2xl text-[13px] font-black shadow-2xl shadow-fiido/30 flex items-center gap-2 hover:scale-[1.02] active:scale-95 transition-all"
            >
              <Plus size={18}/> 新建工单
            </button>
          </div>
        </div>

        <div className="flex gap-4">
          <div className="relative flex-1 max-w-lg">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300" size={18}/>
            <input
              type="text"
              placeholder="搜索单号、标题、责任人..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-50 border border-slate-100 rounded-2xl py-3 pl-12 pr-6 text-sm outline-none focus:ring-4 focus:ring-fiido/5 focus:border-fiido transition-all font-medium"
            />
          </div>
          <button className="flex items-center gap-2 px-6 py-3 border border-slate-200 rounded-2xl text-xs font-black text-slate-600 hover:bg-slate-50 transition-all">
            <Filter size={18}/> 高级筛选
          </button>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-100 rounded-xl text-red-600 text-sm flex items-center justify-between">
            <span>{error}</span>
            <button onClick={clearError} className="text-red-400 hover:text-red-600">×</button>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-auto bg-slate-50/50 p-8">
        {isLoading && tickets.length === 0 ? (
          <div className="flex items-center justify-center h-64 text-slate-400">
            <Loader2 size={32} className="animate-spin" />
          </div>
        ) : tickets.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-slate-400">
            <AlertCircle size={48} className="mb-4 opacity-30" />
            <p className="text-[14px] font-bold">暂无工单</p>
            <p className="text-[12px] mt-1">点击"新建工单"创建第一个工单</p>
          </div>
        ) : viewMode === 'list' ? (
          <div className="bg-white rounded-[32px] border border-slate-100 overflow-hidden shadow-2xl shadow-slate-200/50">
            <table className="w-full text-left text-[12px]">
              <thead className="bg-slate-50/80 border-b border-slate-100">
                <tr>
                  <th className="px-8 py-5 font-black text-slate-400 uppercase tracking-widest">工单编号</th>
                  <th className="px-8 py-5 font-black text-slate-400 uppercase tracking-widest">工单标题</th>
                  <th className="px-8 py-5 font-black text-slate-400 uppercase tracking-widest">当前状态</th>
                  <th className="px-8 py-5 font-black text-slate-400 uppercase tracking-widest">优先级</th>
                  <th className="px-8 py-5 font-black text-slate-400 uppercase tracking-widest">受理人</th>
                  <th className="px-8 py-5 font-black text-slate-400 uppercase tracking-widest">SLA 倒计时</th>
                  <th className="px-8 py-5"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {tickets.map(t => {
                  const sla = getSLARemaining(t.created_at, t.priority);
                  return (
                    <tr
                      key={t.ticket_id}
                      className="hover:bg-slate-50/50 transition-all group cursor-pointer"
                      onClick={() => handleOpenEdit(t)}
                    >
                      <td className="px-8 py-5 font-brand font-bold text-fiido">{t.ticket_id}</td>
                      <td className="px-8 py-5">
                        <p className="font-bold text-slate-800 mb-1">{t.title}</p>
                        <p className="text-[10px] text-slate-400 font-bold">客户: {t.customer?.name || '-'}</p>
                      </td>
                      <td className="px-8 py-5">
                        <span className={`px-3 py-1 rounded-full text-[10px] font-black tracking-widest ${getStatusColor(t.status)}`}>
                          {statusLabels[t.status] || t.status}
                        </span>
                      </td>
                      <td className="px-8 py-5">
                        <span className={`px-3 py-1 rounded-xl font-black tracking-widest ${getPriorityColor(t.priority)}`}>
                          {priorityLabels[t.priority] || t.priority}
                        </span>
                      </td>
                      <td className="px-8 py-5">
                        {t.assigned_agent_name ? (
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-xl bg-slate-100 flex items-center justify-center text-[10px] font-black text-slate-500 shadow-inner">
                              {t.assigned_agent_name[0]}
                            </div>
                            <span className="font-bold text-slate-700">{t.assigned_agent_name}</span>
                          </div>
                        ) : (
                          <span className="text-slate-300">未分配</span>
                        )}
                      </td>
                      <td className="px-8 py-5">
                        {t.status !== 'closed' && t.status !== 'resolved' && t.status !== 'archived' ? (
                          <div className={`flex items-center gap-2 font-black ${sla.isOverdue ? 'text-red-500' : 'text-slate-500'}`}>
                            <Clock size={14}/> {sla.text}
                          </div>
                        ) : <span className="text-slate-300">—</span>}
                      </td>
                      <td className="px-8 py-5 text-right">
                        <button
                          onClick={(e) => { e.stopPropagation(); handleOpenEdit(t); }}
                          className="p-3 hover:bg-white rounded-2xl opacity-0 group-hover:opacity-100 text-fiido transition-all shadow-xl"
                        >
                          <Edit3 size={18}/>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex gap-8 h-full overflow-x-auto pb-6 no-scrollbar">
            {kanbanStatuses.map(status => {
              const statusTickets = tickets.filter(x => x.status === status);
              return (
                <div key={status} className="w-80 flex-shrink-0 flex flex-col gap-6">
                  <div className="flex justify-between items-center px-2">
                    <h3 className="text-xs font-black text-slate-500 flex items-center gap-2 uppercase tracking-[0.2em]">
                      {statusLabels[status] || status}
                      <span className="bg-slate-200 text-slate-600 w-6 h-6 flex items-center justify-center rounded-full text-[10px] shadow-inner">
                        {statusTickets.length}
                      </span>
                    </h3>
                    <button className="text-slate-300 hover:text-fiido"><MoreHorizontal size={18}/></button>
                  </div>
                  <div className="flex-1 space-y-4">
                    {statusTickets.map(ticket => {
                      const sla = getSLARemaining(ticket.created_at, ticket.priority);
                      return (
                        <div
                          key={ticket.ticket_id}
                          className="bg-white p-6 rounded-[28px] border border-slate-100 shadow-sm hover:shadow-2xl hover:-translate-y-1 transition-all cursor-pointer group"
                          onClick={() => handleOpenEdit(ticket)}
                        >
                          <div className="flex justify-between items-center mb-4">
                            <span className={`px-2.5 py-1 rounded-lg text-[10px] font-black tracking-widest ${getPriorityColor(ticket.priority)}`}>
                              {priorityLabels[ticket.priority] || ticket.priority}
                            </span>
                            <span className="text-[9px] text-slate-300 font-brand">#{ticket.ticket_id}</span>
                          </div>
                          <h4 className="text-sm font-bold text-slate-700 leading-relaxed mb-6 group-hover:text-fiido transition-colors">
                            {ticket.title}
                          </h4>
                          <div className="flex justify-between items-center pt-5 border-t border-slate-50">
                            <div className="flex items-center gap-2">
                              <User size={12} className="text-slate-300"/>
                              <span className="text-[10px] text-slate-400 font-black">{ticket.customer?.name || '-'}</span>
                            </div>
                            {status !== 'closed' && status !== 'resolved' && (
                              <div className={`text-[10px] font-black flex items-center gap-1 ${sla.isOverdue ? 'text-red-500' : 'text-slate-400'}`}>
                                <AlertCircle size={12}/>{sla.text}
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                    <button className="w-full py-4 bg-white/50 border-2 border-dashed border-slate-200 rounded-[28px] text-slate-300 text-[11px] font-black hover:border-fiido hover:text-fiido hover:bg-fiido-light/20 transition-all uppercase tracking-widest">
                      + 新增事项
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 新建工单弹窗 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setShowCreateModal(false)}>
          <div className="bg-white rounded-3xl w-full max-w-lg p-8 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-brand font-black text-slate-800">新建工单</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-2 hover:bg-slate-100 rounded-xl text-slate-400"
              >
                <X size={20}/>
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-500 mb-2">工单标题 *</label>
                <input
                  type="text"
                  value={createForm.title}
                  onChange={(e) => setCreateForm({...createForm, title: e.target.value})}
                  placeholder="请输入工单标题"
                  className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-fiido/20 focus:border-fiido"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 mb-2">问题描述</label>
                <textarea
                  value={createForm.description}
                  onChange={(e) => setCreateForm({...createForm, description: e.target.value})}
                  placeholder="请描述客户问题..."
                  rows={3}
                  className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-fiido/20 focus:border-fiido resize-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 mb-2">工单类型</label>
                  <select
                    value={createForm.ticket_type}
                    onChange={(e) => setCreateForm({...createForm, ticket_type: e.target.value as TicketType})}
                    className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-fiido/20 focus:border-fiido"
                  >
                    {Object.entries(typeLabels).map(([value, label]) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 mb-2">优先级</label>
                  <select
                    value={createForm.priority}
                    onChange={(e) => setCreateForm({...createForm, priority: e.target.value as TicketPriority})}
                    className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-fiido/20 focus:border-fiido"
                  >
                    {Object.entries(priorityLabels).map(([value, label]) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 mb-2">客户姓名</label>
                  <input
                    type="text"
                    value={createForm.customer_name}
                    onChange={(e) => setCreateForm({...createForm, customer_name: e.target.value})}
                    placeholder="可选"
                    className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-fiido/20 focus:border-fiido"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 mb-2">客户邮箱</label>
                  <input
                    type="email"
                    value={createForm.customer_email}
                    onChange={(e) => setCreateForm({...createForm, customer_email: e.target.value})}
                    placeholder="可选"
                    className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-fiido/20 focus:border-fiido"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-8">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-6 py-3 text-sm font-bold text-slate-500 hover:bg-slate-100 rounded-xl transition-all"
              >
                取消
              </button>
              <button
                onClick={handleCreateTicket}
                disabled={isCreating}
                className="px-8 py-3 bg-fiido text-white text-sm font-bold rounded-xl hover:scale-[1.02] active:scale-95 transition-all disabled:opacity-50 flex items-center gap-2"
              >
                {isCreating && <Loader2 size={16} className="animate-spin"/>}
                创建工单
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 编辑工单弹窗 */}
      {showEditModal && editingTicket && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setShowEditModal(false)}>
          <div className="bg-white rounded-3xl w-full max-w-lg p-8 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-brand font-black text-slate-800">编辑工单</h2>
                <p className="text-xs text-slate-400 mt-1">#{editingTicket.ticket_id}</p>
              </div>
              <button
                onClick={() => setShowEditModal(false)}
                className="p-2 hover:bg-slate-100 rounded-xl text-slate-400"
              >
                <X size={20}/>
              </button>
            </div>

            {/* 工单信息（只读） */}
            <div className="mb-6 p-4 bg-slate-50 rounded-2xl">
              <h3 className="font-bold text-slate-800 mb-2">{editingTicket.title}</h3>
              <p className="text-sm text-slate-500 mb-3">{editingTicket.description || '无描述'}</p>
              <div className="flex gap-4 text-xs text-slate-400">
                <span>类型: {typeLabels[editingTicket.ticket_type] || editingTicket.ticket_type}</span>
                <span>客户: {editingTicket.customer?.name || '-'}</span>
              </div>
            </div>

            {/* 可编辑字段 */}
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-500 mb-2">工单状态</label>
                <select
                  value={editForm.status}
                  onChange={(e) => setEditForm({...editForm, status: e.target.value as TicketStatus})}
                  className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-fiido/20 focus:border-fiido"
                >
                  {Object.entries(statusLabels).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 mb-2">优先级</label>
                <select
                  value={editForm.priority}
                  onChange={(e) => setEditForm({...editForm, priority: e.target.value as TicketPriority})}
                  className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-fiido/20 focus:border-fiido"
                >
                  {Object.entries(priorityLabels).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 mb-2">受理人</label>
                <input
                  type="text"
                  value={editForm.assigned_agent_name}
                  onChange={(e) => setEditForm({...editForm, assigned_agent_name: e.target.value})}
                  placeholder="输入受理人姓名"
                  className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-fiido/20 focus:border-fiido"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-8">
              <button
                onClick={() => setShowEditModal(false)}
                className="px-6 py-3 text-sm font-bold text-slate-500 hover:bg-slate-100 rounded-xl transition-all"
              >
                取消
              </button>
              <button
                onClick={handleUpdateTicket}
                disabled={isUpdating}
                className="px-8 py-3 bg-fiido text-white text-sm font-bold rounded-xl hover:scale-[1.02] active:scale-95 transition-all disabled:opacity-50 flex items-center gap-2"
              >
                {isUpdating && <Loader2 size={16} className="animate-spin"/>}
                保存修改
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TicketsView;
