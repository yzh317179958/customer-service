
import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  MessageSquare,
  Ticket,
  BookOpen,
  Activity,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Bike,
  CreditCard,
  Sparkles
} from 'lucide-react';

interface SidebarProps {
  isCollapsed: boolean;
  toggleCollapse: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, toggleCollapse }) => {
  const navigate = useNavigate();

  const navItems = [
    { path: '/workspace', icon: MessageSquare, label: '会话工作台' },
    { path: '/tickets', icon: Ticket, label: '工单中心' },
    { path: '/knowledge', icon: BookOpen, label: '知识文档' },
    { path: '/monitoring', icon: Activity, label: '实时大屏' },
    { path: '/dashboard', icon: BarChart3, label: '效能报表' },
    { path: '/audit', icon: ShieldCheck, label: '智能质检' },
    { path: '/billing', icon: CreditCard, label: '计费管理' },
    { path: '/settings', icon: Settings, label: '系统设置' },
  ];

  return (
    <aside className={`bg-fiido-black text-white flex flex-col transition-all duration-300 ease-in-out z-40 shadow-2xl shrink-0 ${isCollapsed ? 'w-16' : 'w-60'}`}>
      <div className="p-4 flex items-center h-14 border-b border-white/5 shrink-0">
        <div className="bg-fiido p-1.5 rounded-lg mr-3 flex-shrink-0 shadow-[0_0_15px_rgba(0,166,160,0.3)]">
          <Bike className="w-5 h-5 text-white" />
        </div>
        {!isCollapsed && (
          <div className="flex flex-col overflow-hidden">
            <span className="font-brand font-black text-base tracking-tighter leading-none whitespace-nowrap">FIIDO CRM</span>
            <span className="text-[8px] font-bold text-fiido tracking-[0.2em] uppercase opacity-60 mt-0.5 whitespace-nowrap">Smart AI SaaS</span>
          </div>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto custom-scrollbar py-4 px-2.5 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `w-full flex items-center gap-3.5 p-3 rounded-xl transition-all group relative ${
                isActive
                  ? 'bg-fiido text-white shadow-lg shadow-fiido/20 font-bold'
                  : 'hover:bg-white/5 text-slate-400 hover:text-white'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <item.icon className={`w-5 h-5 flex-shrink-0 ${isActive ? 'text-white' : 'group-hover:text-fiido'}`} />
                {!isCollapsed && <span className="text-[13px] tracking-wide whitespace-nowrap">{item.label}</span>}
                {isActive && (
                  <div className="absolute right-0 w-1 h-5 bg-white rounded-l-full"></div>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {!isCollapsed && (
        <div className="px-4 py-4 m-2 bg-gradient-to-br from-slate-800 to-black rounded-2xl border border-white/5">
           <div className="flex items-center gap-2 mb-2">
             <Sparkles size={12} className="text-fiido" />
             <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest">AI 接待额度</span>
           </div>
           <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden mb-2">
             <div className="bg-fiido h-full w-3/4 shadow-[0_0_8px_#00a6a0]"></div>
           </div>
           <div className="flex justify-between items-center text-[9px] font-bold text-slate-500">
              <span>本月已用 7.5k / 10k</span>
              <button onClick={() => navigate('/billing')} className="text-fiido hover:underline">加油包</button>
           </div>
        </div>
      )}

      <div className="p-3 border-t border-white/5 bg-black/10">
        <button
          onClick={toggleCollapse}
          className="w-full flex items-center justify-center p-2 rounded-xl hover:bg-white/5 transition-colors text-slate-500 hover:text-fiido"
        >
          {isCollapsed ? <ChevronRight size={20} /> : <div className="flex items-center gap-2 font-bold text-[10px] uppercase tracking-widest text-slate-500 hover:text-fiido"><ChevronLeft size={16} /> 收起面板</div>}
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
