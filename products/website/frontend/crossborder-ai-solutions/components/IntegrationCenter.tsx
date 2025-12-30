
import React, { useState } from 'react';
import { ShoppingCart, MessageCircle, Database, Plug, Link as LinkIcon, Search, RefreshCw, Globe, CreditCard, Share2, Layers } from 'lucide-react';
import Button from './ui/Button';

// Mock Data
const allApps = [
  { id: 1, name: "Shopify", category: "store", icon: <ShoppingCart />, color: "bg-[#95BF47]" },
  { id: 2, name: "WooCommerce", category: "store", icon: <Layers />, color: "bg-[#96588a]" },
  { id: 3, name: "WhatsApp", category: "social", icon: <MessageCircle />, color: "bg-[#25D366]" },
  { id: 4, name: "Messenger", category: "social", icon: <Share2 />, color: "bg-[#00B2FF]" },
  { id: 5, name: "Salesforce", category: "tool", icon: <Database />, color: "bg-[#00A1E0]" },
  { id: 6, name: "Stripe", category: "tool", icon: <CreditCard />, color: "bg-[#635BFF]" },
  { id: 7, name: "Magento", category: "store", icon: <ShoppingCart />, color: "bg-[#EE672F]" },
  { id: 8, name: "Zendesk", category: "tool", icon: <MessageCircle />, color: "bg-[#03363D]" },
];

const OrbitIcon = ({ delay, radius, icon, color, reverse = false }: { delay: number, radius: number, icon: React.ReactNode, color: string, reverse?: boolean }) => {
  const animationName = reverse ? 'orbit-ccw' : 'orbit-cw';
  const childAnimationName = reverse ? 'orbit-cw' : 'orbit-ccw';

  return (
    <div
      className="absolute top-1/2 left-1/2"
      style={{ 
        width: radius * 2, 
        height: radius * 2,
        transform: 'translate(-50%, -50%)',
        animation: `${animationName} 40s linear infinite`
      }}
    >
      <div
        className={`absolute top-0 left-1/2 w-12 h-12 rounded-2xl ${color} text-white flex items-center justify-center shadow-lg border-2 border-white z-10`}
        style={{
            transform: 'translate(-50%, -50%)',
            animation: `${childAnimationName} 40s linear infinite`
        }}
      >
        {React.cloneElement(icon as React.ReactElement<any>, { size: 20 })}
      </div>
    </div>
  );
};

const IntegrationCenter: React.FC = () => {
  const [filter, setFilter] = useState<'all' | 'store' | 'social' | 'tool'>('all');
  
  return (
    <section className="py-24 bg-white relative overflow-hidden">
      <style>{`
        @keyframes orbit-cw {
            from { transform: translate(-50%, -50%) rotate(0deg); }
            to { transform: translate(-50%, -50%) rotate(360deg); }
        }
        @keyframes orbit-ccw {
            from { transform: translate(-50%, -50%) rotate(0deg); }
            to { transform: translate(-50%, -50%) rotate(-360deg); }
        }
      `}</style>

      {/* Background Grid Pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#f0f0f0_1px,transparent_1px),linear-gradient(to_bottom,#f0f0f0_1px,transparent_1px)] bg-[size:40px_40px] opacity-70"></div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        
        {/* Header Section */}
        <div className="flex flex-col md:flex-row justify-between items-end mb-16 gap-8 text-center md:text-left">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-brand-50 border border-brand-100 text-brand-700 rounded-full text-xs font-bold uppercase tracking-wider mb-4">
              <LinkIcon className="w-3 h-3" /> Integration Hub
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-text-primary mb-4">
              连接您的跨境全生态
            </h2>
            <p className="text-text-secondary text-lg max-w-xl">
              像安装手机 App 一样简单。一键连接 50+ 主流平台，让数据在 CrossBorderAI 与您的业务系统之间自由流动。
            </p>
          </div>
          
          <div className="flex flex-col gap-4 items-center md:items-end w-full md:w-auto">
             <Button variant="primary" withArrow className="shadow-lg shadow-brand-500/20">查看 API 文档</Button>
             <p className="text-xs text-text-muted flex items-center gap-2">
                <span className="flex h-2 w-2 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                </span>
                系统运行正常 • 99.9% Uptime
             </p>
          </div>
        </div>

        {/* Dynamic Visualization Area */}
        <div className="relative h-[500px] w-full bg-bg-50/50 rounded-3xl border border-bg-200 overflow-hidden mb-12 flex items-center justify-center">
            
            {/* Center Core */}
            <div className="relative z-20 flex flex-col items-center justify-center">
                <div className="w-32 h-32 bg-white rounded-full shadow-[0_0_40px_rgba(37,99,235,0.2)] border-4 border-brand-50 flex flex-col items-center justify-center relative z-20">
                    <div className="w-16 h-16 bg-brand-600 rounded-xl flex items-center justify-center text-white mb-1 shadow-inner">
                         <Plug className="w-8 h-8" />
                    </div>
                    <div className="text-[10px] font-bold text-brand-600 uppercase">Hub</div>
                </div>
                {/* Pulse Waves */}
                <div className="absolute inset-0 rounded-full border border-brand-200 animate-[ping_3s_linear_infinite] opacity-30"></div>
                <div className="absolute inset-[-20px] rounded-full border border-brand-100 animate-[ping_3s_linear_infinite_1s] opacity-20"></div>
            </div>

            {/* Orbit Rings */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[300px] h-[300px] border border-dashed border-bg-300 rounded-full opacity-50"></div>
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] border border-bg-200 rounded-full opacity-40"></div>

            {/* Orbiting Icons - Inner Ring */}
            <OrbitIcon delay={0} radius={150} icon={allApps[0].icon} color={allApps[0].color} />
            <div className="absolute top-1/2 left-1/2 w-[300px] h-[300px]" style={{ transform: 'translate(-50%, -50%) rotate(120deg)' }}>
                <OrbitIcon delay={0} radius={150} icon={allApps[1].icon} color={allApps[1].color} />
            </div>
            <div className="absolute top-1/2 left-1/2 w-[300px] h-[300px]" style={{ transform: 'translate(-50%, -50%) rotate(240deg)' }}>
                <OrbitIcon delay={0} radius={150} icon={allApps[2].icon} color={allApps[2].color} />
            </div>

             {/* Orbiting Icons - Outer Ring (Reverse) */}
             <div className="absolute top-1/2 left-1/2 w-[500px] h-[500px]" style={{ transform: 'translate(-50%, -50%) rotate(45deg)' }}>
                <OrbitIcon delay={0} radius={250} icon={allApps[3].icon} color={allApps[3].color} reverse />
            </div>
            <div className="absolute top-1/2 left-1/2 w-[500px] h-[500px]" style={{ transform: 'translate(-50%, -50%) rotate(135deg)' }}>
                <OrbitIcon delay={0} radius={250} icon={allApps[4].icon} color={allApps[4].color} reverse />
            </div>
            <div className="absolute top-1/2 left-1/2 w-[500px] h-[500px]" style={{ transform: 'translate(-50%, -50%) rotate(225deg)' }}>
                <OrbitIcon delay={0} radius={250} icon={allApps[5].icon} color={allApps[5].color} reverse />
            </div>
            <div className="absolute top-1/2 left-1/2 w-[500px] h-[500px]" style={{ transform: 'translate(-50%, -50%) rotate(315deg)' }}>
                <OrbitIcon delay={0} radius={250} icon={allApps[6].icon} color={allApps[6].color} reverse />
            </div>
        </div>

        {/* App Grid Filter */}
        <div className="bg-white rounded-2xl border border-bg-200 p-6 shadow-sm">
             <div className="flex flex-col md:flex-row justify-between items-center gap-4 mb-6">
                 <div className="flex p-1 bg-bg-100 rounded-lg overflow-hidden w-full md:w-auto">
                     {['all', 'store', 'social', 'tool'].map((t) => (
                        <button 
                          key={t}
                          onClick={() => setFilter(t as any)}
                          className={`flex-1 md:flex-none px-4 py-1.5 text-sm font-medium rounded-md transition-all ${filter === t ? 'bg-white text-text-primary shadow-sm' : 'text-text-muted hover:text-text-secondary'}`}
                        >
                          {t === 'all' ? '全部' : t === 'store' ? '电商' : t === 'social' ? '社交' : '工具'}
                        </button>
                     ))}
                  </div>
                  <div className="relative w-full md:w-64">
                     <Search className="w-4 h-4 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
                     <input 
                        type="text" 
                        placeholder="搜索集成..." 
                        className="w-full bg-bg-50 border border-bg-200 rounded-lg pl-9 pr-4 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
                        disabled
                     />
                  </div>
             </div>
             
             <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                 {allApps.filter(a => filter === 'all' || a.category === filter).map(app => (
                     <div key={app.id} className="flex flex-col items-center justify-center p-4 rounded-xl border border-bg-100 hover:border-brand-200 hover:bg-brand-50/20 hover:shadow-sm transition-all cursor-pointer group">
                         <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-white mb-2 shadow-sm ${app.color} group-hover:scale-110 transition-transform`}>
                             {React.cloneElement(app.icon as React.ReactElement<any>, { size: 20 })}
                         </div>
                         <span className="text-xs font-bold text-text-secondary">{app.name}</span>
                     </div>
                 ))}
                 <div className="flex flex-col items-center justify-center p-4 rounded-xl border border-dashed border-bg-300 text-text-muted cursor-pointer hover:border-brand-300 hover:text-brand-600 transition-all">
                     <Plug className="w-6 h-6 mb-2" />
                     <span className="text-xs font-bold">Request App</span>
                 </div>
             </div>
        </div>

      </div>
    </section>
  );
};

export default IntegrationCenter;
