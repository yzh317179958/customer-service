
import React, { useState } from 'react';
import { Bell, Search, HelpCircle, ChevronDown, User, LogOut, Settings, Moon, Sun, Monitor, Globe, Command } from 'lucide-react';

interface TopbarProps {
  user: {
    name: string;
    role: string;
    status: string;
    avatar: string;
  };
  onLogout: () => void;
}

const Topbar: React.FC<TopbarProps> = ({ user, onLogout }) => {
  const [showStatusMenu, setShowStatusMenu] = useState(false);
  const [currentStatus, setCurrentStatus] = useState(user.status);

  const statuses = [
    { label: '在线', color: 'bg-green-500' },
    { label: '忙碌', color: 'bg-red-500' },
    { label: '会议中', color: 'bg-blue-500' },
    { label: '离线', color: 'bg-slate-400' }
  ];

  return (
    <header className="h-12 bg-white border-b border-slate-200 flex items-center justify-between px-4 shrink-0 z-30 shadow-sm">
      <div className="flex items-center gap-6 flex-1">
        {/* 生产级搜索框：增加快捷键提示 */}
        <div className="relative max-w-md w-full group">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-300 w-3.5 h-3.5 group-focus-within:text-fiido" />
          <input 
            type="text" 
            placeholder="搜订单、客户或知识 (Cmd+K)" 
            className="w-full bg-slate-50 border border-slate-200 rounded-md py-1.5 pl-9 pr-12 text-[12px] focus:ring-2 focus:ring-fiido/10 focus:border-fiido focus:bg-white transition-all outline-none font-medium placeholder:text-slate-300"
          />
          <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-0.5 text-[9px] font-black text-slate-300 bg-white px-1 py-0.5 rounded border border-slate-100 uppercase">
             <Command size={10}/> K
          </div>
        </div>

        <div className="hidden lg:flex items-center gap-4">
           <div className="flex items-center gap-1.5 text-slate-400 hover:text-fiido cursor-pointer transition-colors border-r border-slate-100 pr-4">
              <Globe size={13}/>
              <span className="text-[11px] font-bold uppercase tracking-wider">Node: EU-West-1</span>
           </div>
           <div className="flex items-center gap-1.5 text-slate-400">
              <Monitor size={13}/>
              <span className="text-[11px] font-bold uppercase tracking-wider">Device ID: FD-9021</span>
           </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button className="p-1.5 hover:bg-slate-50 rounded text-slate-400 relative">
          <Bell size={16} />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full border border-white"></span>
        </button>
        <button className="p-1.5 hover:bg-slate-50 rounded text-slate-400">
          <HelpCircle size={16} />
        </button>

        <div className="h-4 w-px bg-slate-200 mx-1"></div>

        <div className="relative" onMouseLeave={() => setShowStatusMenu(false)}>
          <div 
            className="flex items-center gap-2.5 cursor-pointer p-1 rounded-md transition-all hover:bg-slate-50" 
            onClick={() => setShowStatusMenu(!showStatusMenu)}
          >
            <div className="relative">
              <img src={user.avatar} className="w-7 h-7 rounded shadow-sm" alt="头像" />
              <div className={`absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 border-2 border-white rounded-full ${statuses.find(s => s.label === currentStatus)?.color || 'bg-slate-400'}`}></div>
            </div>
            <div className="text-left hidden md:block">
              <p className="text-[11px] font-black text-slate-700 leading-none">{user.name}</p>
            </div>
            <ChevronDown size={12} className="text-slate-300" />
          </div>

          {showStatusMenu && (
            <div className="absolute top-full mt-1 right-0 w-40 bg-white rounded-lg shadow-xl border border-slate-100 p-1 z-50 animate-in fade-in slide-in-from-top-1">
              {statuses.map((s) => (
                <button 
                  key={s.label}
                  onClick={() => { setCurrentStatus(s.label); setShowStatusMenu(false); }}
                  className="w-full text-left px-2.5 py-1.5 text-[11px] font-bold text-slate-600 hover:bg-fiido-light hover:text-fiido rounded flex items-center gap-2.5 transition-all"
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${s.color}`}></span>
                  {s.label}
                </button>
              ))}
              <div className="h-px bg-slate-50 my-1"></div>
              <button 
                onClick={onLogout}
                className="w-full text-left px-2.5 py-1.5 text-[11px] font-bold text-red-500 hover:bg-red-50 rounded flex items-center gap-2.5"
              >
                <LogOut size={13} /> 退出系统
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Topbar;
