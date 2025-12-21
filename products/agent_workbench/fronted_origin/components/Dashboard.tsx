
import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';
import { TrendingUp, Users, MessageSquare, Clock, ShieldCheck, Bike, Activity, Zap } from 'lucide-react';

const data = [
  { name: '周一', sessions: 400, satisfaction: 98, load: 45 },
  { name: '周二', sessions: 300, satisfaction: 95, load: 52 },
  { name: '周三', sessions: 600, satisfaction: 92, load: 78 },
  { name: '周四', sessions: 800, satisfaction: 96, load: 88 },
  { name: '周五', sessions: 1100, satisfaction: 99, load: 95 },
  { name: '周六', sessions: 900, satisfaction: 97, load: 70 },
  { name: '周日', sessions: 700, satisfaction: 98, load: 60 },
];

const Dashboard: React.FC = () => {
  return (
    <div className="h-full overflow-y-auto p-12 bg-slate-50/30 animate-in fade-in duration-1000 font-sans">
      <div className="max-w-7xl mx-auto space-y-12">
        <header className="flex justify-between items-end">
          <div>
            <h1 className="text-3xl font-brand font-black text-slate-800 tracking-tighter">效能监控中心</h1>
            <p className="text-slate-400 text-[11px] font-bold uppercase tracking-[0.4em] mt-2">全球服务实时流量与满意度指标</p>
          </div>
          <div className="flex gap-4">
            <div className="text-right bg-white px-6 py-2 rounded-2xl shadow-sm border border-slate-100">
               <p className="text-[10px] font-black text-slate-300 uppercase tracking-widest mb-1">数据最后更新</p>
               <p className="text-sm font-mono font-bold text-fiido">15:30:00 CST</p>
            </div>
          </div>
        </header>

        {/* 核心指标卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {[
            { label: '今日会话总数', value: '1,582', change: '+12%', icon: MessageSquare, color: 'fiido' },
            { label: '平均响应时长', value: '28 秒', change: '-4s', icon: Clock, color: 'emerald' },
            { label: '全渠道满意度', value: '98.5%', change: '+0.2%', icon: Users, color: 'fiido' },
            { label: '服务质检评级', value: '卓越', change: '稳定', icon: ShieldCheck, color: 'indigo' },
          ].map((item, i) => (
            <div key={i} className="bg-white p-8 rounded-[40px] shadow-[0_12px_32px_rgba(0,0,0,0.03)] border border-slate-100 hover:shadow-2xl transition-all group overflow-hidden relative">
              <div className="absolute top-0 right-0 p-4 opacity-[0.03] group-hover:scale-110 transition-transform">
                <item.icon size={100} />
              </div>
              <div className="flex justify-between items-start mb-6 relative z-10">
                <div className="p-4 rounded-2xl bg-slate-50 text-slate-400 group-hover:bg-fiido group-hover:text-white transition-all shadow-inner">
                  <item.icon size={24}/>
                </div>
                <span className={`text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-widest ${item.change.startsWith('+') ? 'text-green-600 bg-green-50' : 'text-blue-600 bg-blue-50'}`}>{item.change}</span>
              </div>
              <p className="text-4xl font-brand font-black text-slate-800 relative z-10">{item.value}</p>
              <p className="text-[11px] font-black text-slate-400 mt-2 uppercase tracking-[0.2em] relative z-10">{item.label}</p>
            </div>
          ))}
        </div>

        {/* 核心图表区块 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
           {/* 会话趋势图 */}
           <div className="lg:col-span-2 bg-white p-10 rounded-[48px] border border-slate-100 shadow-[0_12px_48px_rgba(0,0,0,0.02)] relative overflow-hidden">
             <div className="absolute top-0 right-0 p-8 opacity-[0.02]">
               <Activity size={180}/>
             </div>
             <div className="flex justify-between items-center mb-10">
               <h3 className="text-xs font-black text-slate-800 uppercase tracking-[0.3em] flex items-center gap-3">
                 <TrendingUp size={16} className="text-fiido"/> 会话流量趋势 (近 7 日)
               </h3>
               <div className="flex gap-2">
                  <span className="flex items-center gap-2 text-[10px] font-bold text-slate-400"><span className="w-2 h-2 rounded-full bg-fiido"></span> 会话量</span>
               </div>
             </div>
             <div className="h-[380px]">
               <ResponsiveContainer width="100%" height="100%">
                 <AreaChart data={data}>
                   <defs>
                     <linearGradient id="colorTrend" x1="0" y1="0" x2="0" y2="1">
                       <stop offset="5%" stopColor="#00a6a0" stopOpacity={0.2}/>
                       <stop offset="95%" stopColor="#00a6a0" stopOpacity={0}/>
                     </linearGradient>
                   </defs>
                   <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                   <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fontSize: 11, fill: '#94a3b8', fontWeight: 'bold'}} dy={10} />
                   <YAxis axisLine={false} tickLine={false} tick={{fontSize: 11, fill: '#94a3b8', fontWeight: 'bold'}} />
                   <Tooltip 
                     contentStyle={{ borderRadius: '24px', border: 'none', boxShadow: '0 24px 48px rgba(15,23,42,0.12)', fontFamily: 'Noto Sans SC' }}
                     cursor={{ stroke: '#00a6a0', strokeWidth: 2, strokeDasharray: '5 5' }}
                   />
                   <Area type="monotone" dataKey="sessions" stroke="#00a6a0" strokeWidth={5} fillOpacity={1} fill="url(#colorTrend)" animationDuration={1500} />
                 </AreaChart>
               </ResponsiveContainer>
             </div>
           </div>

           {/* 满意度极化柱状图 */}
           <div className="bg-fiido-black p-10 rounded-[48px] text-white shadow-2xl relative overflow-hidden flex flex-col">
             <div className="absolute -top-10 -right-10 opacity-10 rotate-12">
               <ShieldCheck size={220}/>
             </div>
             <div className="mb-10">
               <h3 className="text-[10px] font-black uppercase tracking-[0.4em] text-fiido">服务评分深度分析</h3>
               <p className="text-[11px] text-slate-500 mt-2">基于 AI 情感识别与邀评结果</p>
             </div>
             <div className="flex-1 flex flex-col justify-center space-y-12 relative z-10">
                {[
                  { label: '非常满意 (超预期)', value: 88, color: '#00a6a0' },
                  { label: '满意 (符合规范)', value: 10, color: '#ffffff' },
                  { label: '待改进项', value: 2, color: '#ef4444' },
                ].map((s, i) => (
                  <div key={i} className="space-y-4">
                     <div className="flex justify-between items-end">
                        <span className="text-[11px] font-bold uppercase tracking-widest text-slate-400">{s.label}</span>
                        <span className="text-3xl font-brand font-black">{s.value}<span className="text-xs ml-1">%</span></span>
                     </div>
                     <div className="w-full bg-white/5 h-2.5 rounded-full overflow-hidden shadow-inner">
                        <div className="h-full rounded-full transition-all duration-[2s] ease-out shadow-[0_0_20px_rgba(0,166,160,0.6)]" style={{ width: `${s.value}%`, backgroundColor: s.color }}></div>
                     </div>
                  </div>
                ))}
             </div>
             <button className="mt-12 w-full py-5 bg-white/5 border border-white/10 hover:bg-fiido hover:border-fiido transition-all rounded-[28px] text-[11px] font-black uppercase tracking-widest text-slate-300 hover:text-white">导出满意度报告</button>
           </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
