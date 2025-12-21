
import React, { useState } from 'react';
import { 
  Plus, Search, Filter, LayoutGrid, List, ArrowUpRight, Clock, AlertCircle, 
  ChevronDown, MoreHorizontal, User, Tag
} from 'lucide-react';
import { Ticket, TicketStatus } from '../types';

const TicketsView: React.FC = () => {
  const [viewMode, setViewMode] = useState<'list' | 'kanban'>('list');
  const [tickets] = useState<Ticket[]>([
    { id: 'GD-20240322-01', title: '电池充不进电，充电器红灯闪烁', customerName: 'John Doe', status: TicketStatus.OPEN, priority: '紧急', assignee: '李建国', createdAt: '2024-03-22 10:00', slaTimeRemaining: '1小时20分' },
    { id: 'GD-20240322-02', title: '车架折叠位存在异响', customerName: 'Marie Chen', status: TicketStatus.PENDING, priority: '高', assignee: '王小美', createdAt: '2024-03-22 11:30', slaTimeRemaining: '3小时45分' },
    { id: 'GD-20240321-99', title: '咨询 C11 Pro 出口认证证书', customerName: 'Adam Smith', status: TicketStatus.RESOLVED, priority: '中', assignee: '张强', createdAt: '2024-03-21 09:15', slaTimeRemaining: '-' },
  ]);

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case '紧急': return 'text-red-600 bg-red-100';
      case '高': return 'text-orange-600 bg-orange-100';
      case '中': return 'text-blue-600 bg-blue-100';
      default: return 'text-slate-600 bg-slate-100';
    }
  };

  return (
    <div className="flex flex-col h-full bg-white animate-in slide-in-from-right-4 duration-500 font-sans">
      <div className="p-8 border-b border-slate-100">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-brand font-black text-slate-800 tracking-tighter">售后工单中心</h1>
            <p className="text-[11px] text-slate-400 font-bold uppercase tracking-[0.2em] mt-2">协同追踪全球售后需求与备件流转</p>
          </div>
          <div className="flex items-center gap-4">
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
            <button className="bg-fiido text-white px-8 py-3 rounded-2xl text-[13px] font-black shadow-2xl shadow-fiido/30 flex items-center gap-2 hover:scale-[1.02] active:scale-95 transition-all">
              <Plus size={18}/> 新建工单
            </button>
          </div>
        </div>

        <div className="flex gap-4">
          <div className="relative flex-1 max-w-lg">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300" size={18}/>
            <input type="text" placeholder="搜索单号、标题、责任人..." className="w-full bg-slate-50 border border-slate-100 rounded-2xl py-3 pl-12 pr-6 text-sm outline-none focus:ring-4 focus:ring-fiido/5 focus:border-fiido transition-all font-medium"/>
          </div>
          <button className="flex items-center gap-2 px-6 py-3 border border-slate-200 rounded-2xl text-xs font-black text-slate-600 hover:bg-slate-50 transition-all">
            <Filter size={18}/> 高级筛选
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto bg-slate-50/50 p-8">
        {viewMode === 'list' ? (
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
                {tickets.map(t => (
                  <tr key={t.id} className="hover:bg-slate-50/50 transition-all group cursor-pointer">
                    <td className="px-8 py-5 font-brand font-bold text-fiido">{t.id}</td>
                    <td className="px-8 py-5">
                      <p className="font-bold text-slate-800 mb-1">{t.title}</p>
                      <p className="text-[10px] text-slate-400 font-bold">客户: {t.customerName}</p>
                    </td>
                    <td className="px-8 py-5">
                      <span className={`px-3 py-1 rounded-full text-[10px] font-black tracking-widest ${
                        t.status === TicketStatus.OPEN ? 'bg-fiido/10 text-fiido' : 'bg-green-50 text-green-600'
                      }`}>{t.status}</span>
                    </td>
                    <td className="px-8 py-5">
                      <span className={`px-3 py-1 rounded-xl font-black tracking-widest ${getPriorityColor(t.priority)}`}>{t.priority}</span>
                    </td>
                    <td className="px-8 py-5">
                       <div className="flex items-center gap-3">
                         <div className="w-8 h-8 rounded-xl bg-slate-100 flex items-center justify-center text-[10px] font-black text-slate-500 shadow-inner">{t.assignee[0]}</div>
                         <span className="font-bold text-slate-700">{t.assignee}</span>
                       </div>
                    </td>
                    <td className="px-8 py-5">
                       {t.slaTimeRemaining !== '-' ? (
                         <div className={`flex items-center gap-2 font-black ${t.priority === '紧急' ? 'text-red-500' : 'text-slate-500'}`}>
                           <Clock size={14}/> {t.slaTimeRemaining}
                         </div>
                       ) : <span className="text-slate-300">—</span>}
                    </td>
                    <td className="px-8 py-5 text-right">
                       <button className="p-3 hover:bg-white rounded-2xl opacity-0 group-hover:opacity-100 text-fiido transition-all shadow-xl"><ArrowUpRight size={18}/></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex gap-8 h-full overflow-x-auto pb-6 no-scrollbar">
             {Object.values(TicketStatus).map(status => (
                <div key={status} className="w-80 flex-shrink-0 flex flex-col gap-6">
                   <div className="flex justify-between items-center px-2">
                      <h3 className="text-xs font-black text-slate-500 flex items-center gap-2 uppercase tracking-[0.2em]">
                        {status}
                        <span className="bg-slate-200 text-slate-600 w-6 h-6 flex items-center justify-center rounded-full text-[10px] shadow-inner">{tickets.filter(x => x.status === status).length}</span>
                      </h3>
                      <button className="text-slate-300 hover:text-fiido"><MoreHorizontal size={18}/></button>
                   </div>
                   <div className="flex-1 space-y-4">
                      {tickets.filter(x => x.status === status).map(ticket => (
                        <div key={ticket.id} className="bg-white p-6 rounded-[28px] border border-slate-100 shadow-sm hover:shadow-2xl hover:-translate-y-1 transition-all cursor-grab active:cursor-grabbing group">
                           <div className="flex justify-between items-center mb-4">
                              <span className={`px-2.5 py-1 rounded-lg text-[10px] font-black tracking-widest ${getPriorityColor(ticket.priority)}`}>{ticket.priority}</span>
                              <span className="text-[9px] text-slate-300 font-brand">#{ticket.id}</span>
                           </div>
                           <h4 className="text-sm font-bold text-slate-700 leading-relaxed mb-6 group-hover:text-fiido transition-colors">{ticket.title}</h4>
                           <div className="flex justify-between items-center pt-5 border-t border-slate-50">
                              <div className="flex items-center gap-2">
                                 <User size={12} className="text-slate-300"/>
                                 <span className="text-[10px] text-slate-400 font-black">{ticket.customerName}</span>
                              </div>
                              {ticket.slaTimeRemaining !== '-' && (
                                <div className="text-[10px] text-red-500 font-black flex items-center gap-1">
                                  <AlertCircle size={12}/>{ticket.slaTimeRemaining}
                                </div>
                              )}
                           </div>
                        </div>
                      ))}
                      <button className="w-full py-4 bg-white/50 border-2 border-dashed border-slate-200 rounded-[28px] text-slate-300 text-[11px] font-black hover:border-fiido hover:text-fiido hover:bg-fiido-light/20 transition-all uppercase tracking-widest">+ 新增事项</button>
                   </div>
                </div>
             ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default TicketsView;
