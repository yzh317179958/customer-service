
import React from 'react';
import { Activity, Users, Zap, Clock, ShieldAlert, Monitor, ChevronRight, Globe, Battery } from 'lucide-react';

const Monitoring: React.FC = () => {
  return (
    <div className="h-full overflow-y-auto bg-fiido-black text-white p-12 custom-scrollbar font-sans">
      <div className="max-w-7xl mx-auto space-y-12">
        <header className="flex justify-between items-end">
          <div>
            <div className="flex items-center gap-3 text-fiido mb-3 font-black text-xs uppercase tracking-[0.3em]">
              <span className="w-2.5 h-2.5 bg-fiido rounded-full animate-ping shadow-[0_0_12px_#00a6a0]"></span>
              系统链路状态：全量运行中
            </div>
            <h1 className="text-4xl font-brand font-black tracking-tighter">全球实时服务看板</h1>
          </div>
          <div className="text-right bg-white/5 border border-white/10 px-6 py-3 rounded-2xl backdrop-blur-xl">
             <p className="text-[10px] text-slate-500 font-black uppercase tracking-widest mb-1">CST 实时同步</p>
             <p className="text-sm font-mono font-bold text-fiido">15:31:05</p>
          </div>
        </header>

        {/* 核心集群指标 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {[
            { label: '系统并发负载', value: '28.4%', icon: Zap, color: 'blue' },
            { label: '全球实时排队', value: '14 人', icon: Users, color: 'amber' },
            { label: '坐席活跃率', value: '42/50', icon: Monitor, color: 'emerald' },
            { label: 'SLA 告警事件', value: '0', icon: ShieldAlert, color: 'red' },
          ].map((stat, i) => (
            <div key={i} className="bg-white/5 border border-white/10 p-8 rounded-[40px] backdrop-blur-3xl hover:bg-white/10 transition-all border-b-4 border-b-transparent hover:border-b-fiido group">
              <div className="flex items-center gap-4 mb-8">
                 <div className={`p-3 rounded-2xl bg-white/5 text-slate-400 group-hover:text-fiido transition-colors`}>
                   <stat.icon size={24} />
                 </div>
                 <span className="text-[11px] font-black text-slate-400 uppercase tracking-widest">{stat.label}</span>
              </div>
              <p className="text-4xl font-brand font-black text-white">{stat.value}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
           {/* 流量分布图 */}
           <div className="lg:col-span-2 bg-white/5 border border-white/10 p-10 rounded-[48px] backdrop-blur-md relative overflow-hidden group">
              <Globe className="absolute -right-12 -bottom-12 w-64 h-64 text-white/5 group-hover:scale-110 transition-transform duration-[2s]" />
              <h3 className="text-[11px] font-black text-slate-400 mb-10 uppercase tracking-[0.3em] flex items-center gap-3">
                <Activity size={18} className="text-fiido"/> 全渠道实时流量矩阵
              </h3>
              <div className="space-y-8 relative z-10">
                 {[
                   { name: 'Fiido App (iOS/Android)', load: 88, users: 1202, trend: '上升' },
                   { name: 'Fiido Global (网页版)', load: 56, users: 840, trend: '稳定' },
                   { name: '微信小程序 (亚太区)', load: 74, users: 2100, trend: '上升' },
                   { name: '电话/呼叫中心', load: 32, users: 156, trend: '下降' },
                 ].map((c, i) => (
                   <div key={i} className="space-y-4">
                      <div className="flex justify-between items-end font-bold text-xs uppercase tracking-widest">
                        <span className="text-slate-300">{c.name}</span>
                        <div className="flex gap-4">
                           <span className="text-slate-500 font-mono">{c.users} 在线</span>
                           <span className={c.trend === '上升' ? 'text-green-500' : c.trend === '下降' ? 'text-red-500' : 'text-fiido'}>{c.load}% {c.trend}</span>
                        </div>
                      </div>
                      <div className="w-full bg-white/5 h-2.5 rounded-full overflow-hidden shadow-inner">
                        <div className="h-full bg-fiido rounded-full shadow-[0_0_12px_#00a6a0] transition-all duration-[1.5s]" style={{ width: `${c.load}%` }}></div>
                      </div>
                   </div>
                 ))}
              </div>
           </div>

           {/* 团队健康度看板 */}
           <div className="bg-white/5 border border-white/10 p-10 rounded-[48px] backdrop-blur-md">
              <h3 className="text-[11px] font-black text-slate-400 mb-10 uppercase tracking-[0.3em] flex items-center gap-3">
                <Clock size={18} className="text-fiido"/> 座席服务健康度
              </h3>
              <div className="space-y-6">
                 {[
                   { name: '李建国', status: '服务中', time: '12m', load: '高' },
                   { name: '王小美', status: '在线', time: '4h', load: '低' },
                   { name: '张强', status: '小休', time: '15m', load: '-' },
                   { name: 'Adam Smith', status: '服务中', time: '2m', load: '中' },
                   { name: '陈丹丹', status: '在线', time: '1h', load: '低' },
                 ].map((a, i) => (
                   <div key={i} className="flex justify-between items-center border-b border-white/5 pb-4 last:border-0 last:pb-0 group">
                      <div className="flex items-center gap-4">
                         <div className={`w-2.5 h-2.5 rounded-full ${a.status === '在线' ? 'bg-green-500' : a.status === '服务中' ? 'bg-fiido' : 'bg-amber-500'} shadow-[0_0_10px_currentColor]`}></div>
                         <div>
                            <p className="text-sm font-bold text-white group-hover:text-fiido transition-colors">{a.name}</p>
                            <p className="text-[9px] text-slate-500 font-black uppercase tracking-widest mt-1">负载: {a.load}</p>
                         </div>
                      </div>
                      <div className="text-right">
                         <p className="text-[10px] text-slate-400 font-black uppercase tracking-widest mb-1">{a.status}</p>
                         <p className="text-xs font-mono font-bold text-fiido">{a.time}</p>
                      </div>
                   </div>
                 ))}
                 <button className="w-full mt-10 py-5 bg-fiido text-white rounded-[28px] text-[11px] font-black uppercase tracking-[0.2em] shadow-xl shadow-fiido/20 hover:scale-[1.02] active:scale-95 transition-all">
                   进入团队管理台
                 </button>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
};

export default Monitoring;
