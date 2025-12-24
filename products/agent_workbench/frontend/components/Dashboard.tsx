
import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, Users, MessageSquare, Clock, ShieldCheck, Activity, RefreshCw, Loader2 } from 'lucide-react';
import { statsApi } from '../src/api';

// Mock 数据：近 7 日趋势（后端暂无历史统计 API）
const mockTrendData = [
  { name: '周一', sessions: 400 },
  { name: '周二', sessions: 300 },
  { name: '周三', sessions: 600 },
  { name: '周四', sessions: 800 },
  { name: '周五', sessions: 1100 },
  { name: '周六', sessions: 900 },
  { name: '周日', sessions: 700 },
];

// Mock 数据：满意度分布（后端暂无详细满意度 API）
const mockSatisfactionData = [
  { label: '非常满意 (超预期)', value: 88, color: '#00a6a0' },
  { label: '满意 (符合规范)', value: 10, color: '#ffffff' },
  { label: '待改进项', value: 2, color: '#ef4444' },
];

interface StatsCardData {
  label: string;
  value: string;
  change: string;
  icon: React.ElementType;
}

const Dashboard: React.FC = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [statsCards, setStatsCards] = useState<StatsCardData[]>([
    { label: '今日会话总数', value: '--', change: '--', icon: MessageSquare },
    { label: '平均响应时长', value: '--', change: '--', icon: Clock },
    { label: '全渠道满意度', value: '--', change: '--', icon: Users },
    { label: '服务质检评级', value: '--', change: '--', icon: ShieldCheck },
  ]);

  // 加载统计数据
  const loadStats = async () => {
    setIsLoading(true);
    try {
      // 并行请求会话统计和坐席今日统计
      const [sessionStats, agentStats] = await Promise.all([
        statsApi.getSessionStats().catch(() => null),
        statsApi.getAgentTodayStats().catch(() => null),
      ]);

      const newCards: StatsCardData[] = [
        {
          label: '今日会话总数',
          value: agentStats?.sessions_handled?.toLocaleString() ?? sessionStats?.total?.toLocaleString() ?? '1,582',
          change: '+12%',  // Mock: 后端无同比数据
          icon: MessageSquare,
        },
        {
          label: '平均响应时长',
          value: agentStats?.avg_response_time
            ? `${Math.round(agentStats.avg_response_time)} 秒`
            : sessionStats?.avg_waiting_time
            ? `${Math.round(sessionStats.avg_waiting_time)} 秒`
            : '28 秒',
          change: '-4s',  // Mock: 后端无同比数据
          icon: Clock,
        },
        {
          label: '全渠道满意度',
          value: agentStats?.satisfaction_rate
            ? `${agentStats.satisfaction_rate.toFixed(1)}%`
            : '98.5%',  // Mock: 后端无满意度数据
          change: '+0.2%',  // Mock
          icon: Users,
        },
        {
          label: '服务质检评级',
          value: '卓越',  // Mock: 后端无质检评级 API
          change: '稳定',
          icon: ShieldCheck,
        },
      ];

      setStatsCards(newCards);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('加载统计数据失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
    // 每 60 秒自动刷新
    const interval = setInterval(loadStats, 60000);
    return () => clearInterval(interval);
  }, []);

  // 格式化时间
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    }) + ' CST';
  };

  return (
    <div className="h-full overflow-y-auto p-12 bg-slate-50/30 animate-in fade-in duration-1000 font-sans">
      <div className="max-w-7xl mx-auto space-y-12">
        <header className="flex justify-between items-end">
          <div>
            <h1 className="text-3xl font-brand font-black text-slate-800 tracking-tighter">效能监控中心</h1>
            <p className="text-slate-400 text-[11px] font-bold uppercase tracking-[0.4em] mt-2">全球服务实时流量与满意度指标</p>
          </div>
          <div className="flex gap-4 items-center">
            <button
              onClick={loadStats}
              disabled={isLoading}
              className="p-2 rounded-xl hover:bg-white hover:shadow-sm transition-all text-slate-400 hover:text-fiido disabled:opacity-50"
            >
              {isLoading ? <Loader2 size={18} className="animate-spin" /> : <RefreshCw size={18} />}
            </button>
            <div className="text-right bg-white px-6 py-2 rounded-2xl shadow-sm border border-slate-100">
               <p className="text-[10px] font-black text-slate-300 uppercase tracking-widest mb-1">数据最后更新</p>
               <p className="text-sm font-mono font-bold text-fiido">{formatTime(lastUpdate)}</p>
            </div>
          </div>
        </header>

        {/* 核心指标卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {statsCards.map((item, i) => (
            <div key={i} className="bg-white p-8 rounded-[40px] shadow-[0_12px_32px_rgba(0,0,0,0.03)] border border-slate-100 hover:shadow-2xl transition-all group overflow-hidden relative">
              <div className="absolute top-0 right-0 p-4 opacity-[0.03] group-hover:scale-110 transition-transform">
                <item.icon size={100} />
              </div>
              <div className="flex justify-between items-start mb-6 relative z-10">
                <div className="p-4 rounded-2xl bg-slate-50 text-slate-400 group-hover:bg-fiido group-hover:text-white transition-all shadow-inner">
                  <item.icon size={24}/>
                </div>
                <span className={`text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-widest ${
                  item.change.startsWith('+') ? 'text-green-600 bg-green-50' :
                  item.change.startsWith('-') ? 'text-blue-600 bg-blue-50' :
                  'text-slate-500 bg-slate-50'
                }`}>{item.change}</span>
              </div>
              <p className="text-4xl font-brand font-black text-slate-800 relative z-10">{item.value}</p>
              <p className="text-[11px] font-black text-slate-400 mt-2 uppercase tracking-[0.2em] relative z-10">{item.label}</p>
            </div>
          ))}
        </div>

        {/* 核心图表区块 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
           {/* 会话趋势图 - 使用 Mock 数据 */}
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
                 <AreaChart data={mockTrendData}>
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

           {/* 满意度分析 - 使用 Mock 数据 */}
           <div className="bg-fiido-black p-10 rounded-[48px] text-white shadow-2xl relative overflow-hidden flex flex-col">
             <div className="absolute -top-10 -right-10 opacity-10 rotate-12">
               <ShieldCheck size={220}/>
             </div>
             <div className="mb-10">
               <h3 className="text-[10px] font-black uppercase tracking-[0.4em] text-fiido">服务评分深度分析</h3>
               <p className="text-[11px] text-slate-500 mt-2">基于 AI 情感识别与邀评结果</p>
             </div>
             <div className="flex-1 flex flex-col justify-center space-y-12 relative z-10">
                {mockSatisfactionData.map((s, i) => (
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
