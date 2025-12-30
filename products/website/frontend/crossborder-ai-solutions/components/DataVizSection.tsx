import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, Radio } from 'lucide-react';

const data = [
  { time: '00:00', throughput: 2400 },
  { time: '04:00', throughput: 1398 },
  { time: '08:00', throughput: 9800 },
  { time: '12:00', throughput: 3908 },
  { time: '16:00', throughput: 4800 },
  { time: '20:00', throughput: 3800 },
  { time: '24:00', throughput: 4300 },
];

const DataVizSection: React.FC = () => {
  return (
    <section className="py-24 bg-slate-900/30 border-y border-slate-900 overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="lg:grid lg:grid-cols-2 lg:gap-16 items-center">
          
          <div className="mb-12 lg:mb-0 order-last lg:order-first">
             <div className="relative group">
               {/* Window Chrome */}
              <div className="rounded-xl border border-slate-700 bg-slate-950 shadow-2xl overflow-hidden relative z-10">
                <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/90 backdrop-blur-md">
                  <div className="flex items-center gap-2">
                    <div className="h-3 w-3 rounded-full bg-rose-500"></div>
                    <div className="h-3 w-3 rounded-full bg-amber-500"></div>
                    <div className="h-3 w-3 rounded-full bg-emerald-500"></div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-brand-500/10 border border-brand-500/20">
                      <div className="w-1.5 h-1.5 rounded-full bg-brand-500 animate-pulse"></div>
                      <span className="text-[10px] text-brand-400 font-mono font-medium">AI MONITORING</span>
                    </div>
                  </div>
                </div>
                
                {/* Chart Content */}
                <div className="p-6 h-[350px] w-full bg-slate-950/50 relative">
                  {/* Scanning Effect Overlay */}
                  <div className="absolute inset-0 pointer-events-none z-20 overflow-hidden">
                    <div className="w-full h-[2px] bg-brand-500/50 shadow-[0_0_15px_rgba(14,165,233,0.5)] animate-scan"></div>
                  </div>

                  <div className="flex justify-between items-end mb-4">
                     <div>
                        <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">实时吞吐量 (Events/sec)</h4>
                        <div className="text-2xl font-mono text-white mt-1">9,842 <span className="text-emerald-500 text-sm">▲ 12%</span></div>
                     </div>
                     <div className="text-xs text-brand-500 font-mono animate-pulse">Processing...</div>
                  </div>

                  <ResponsiveContainer width="100%" height="80%">
                    <AreaChart data={data}>
                      <defs>
                        <linearGradient id="colorThroughput" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                      <XAxis dataKey="time" stroke="#64748b" tick={{fontSize: 12}} tickLine={false} axisLine={false} />
                      <YAxis stroke="#64748b" tick={{fontSize: 12}} tickLine={false} axisLine={false} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f8fafc', borderRadius: '8px' }}
                        itemStyle={{ color: '#38bdf8' }}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="throughput" 
                        stroke="#0ea5e9" 
                        strokeWidth={2}
                        fillOpacity={1} 
                        fill="url(#colorThroughput)" 
                        isAnimationActive={true}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
              
              {/* Backglow */}
              <div className="absolute -inset-1 bg-gradient-to-r from-brand-500 to-purple-600 rounded-xl blur opacity-20 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
            </div>
          </div>

          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 text-xs font-medium text-brand-400 mb-6 border border-brand-500/20">
              <Activity className="w-3 h-3" /> 智能监控引擎
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
              实时洞察，<br />
              <span className="text-brand-400">毫厘不差。</span>
            </h2>
            <p className="text-slate-400 text-lg mb-8">
              获得前所未有的数据基础设施可见性。通过我们的智能仪表盘，以极其精细的粒度监控吞吐量、延迟和错误率。
            </p>
            <ul className="space-y-4">
              {[
                {text: '亚毫秒级延迟追踪', icon: <Radio className="w-4 h-4 text-brand-500" />},
                {text: 'AI 驱动的历史吞吐量分析', icon: <Activity className="w-4 h-4 text-brand-500" />},
                {text: '自定义智能告警阈值', icon: <Radio className="w-4 h-4 text-brand-500" />}
              ].map((item, i) => (
                <li key={i} className="flex items-center text-slate-300 group cursor-default">
                  <div className="mr-3 p-2 rounded-lg bg-slate-800 group-hover:bg-brand-500/20 transition-colors">
                    {item.icon}
                  </div>
                  {item.text}
                </li>
              ))}
            </ul>
          </div>

        </div>
      </div>
    </section>
  );
};

export default DataVizSection;