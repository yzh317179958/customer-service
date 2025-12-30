import React, { useState } from 'react';
import { Globe, Cpu, Zap, MapPin, ClipboardCheck, BarChart3 } from 'lucide-react';

const PlatformArchitecture: React.FC = () => {
  const [activeStage, setActiveStage] = useState<number | null>(null);

  const ConnectionLine = ({ isActive }: { isActive: boolean }) => (
    <div className="hidden md:flex flex-1 h-px bg-bg-200 relative mx-4 self-center">
      <div className={`absolute inset-0 bg-gradient-to-r from-brand-300 to-brand-500 transition-all duration-700 ${isActive ? 'w-full opacity-100' : 'w-0 opacity-0'}`}></div>
      {isActive && (
         <div className="absolute top-1/2 -translate-y-1/2 w-2 h-2 bg-brand-600 rounded-full shadow-[0_0_10px_rgba(37,99,235,0.8)] animate-[moveRight_1s_infinite_linear]"></div>
      )}
    </div>
  );

  return (
    <section className="py-24 bg-white relative overflow-hidden">
      <style>{`
        @keyframes moveRight {
          0% { left: 0%; opacity: 0; }
          100% { left: 100%; opacity: 0; }
        }
      `}</style>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center mb-20">
          <span className="text-brand-600 font-bold tracking-wider uppercase text-xs bg-brand-50 px-3 py-1 rounded-full border border-brand-100">Operation Architecture</span>
          <h2 className="text-3xl md:text-4xl font-black text-text-primary mt-4 mb-4 uppercase tracking-tight">业务闭环：从对话到决策</h2>
          <p className="text-text-secondary max-w-2xl mx-auto text-lg leading-relaxed">
            打通全渠道流量入口，通过智能 OS 实现订单自动同步与坐席精细化管理。
          </p>
        </div>

        <div className="flex flex-col md:flex-row justify-between gap-6 relative">
            
            {/* Stage 1: Connect */}
            <div 
              className={`flex-1 rounded-2xl p-8 border transition-all duration-500 relative
                ${activeStage === 1 ? 'border-brand-400 shadow-xl bg-brand-50/30 scale-105' : 'border-bg-200 bg-bg-50 hover:border-brand-200'}
              `}
              onMouseEnter={() => setActiveStage(1)}
              onMouseLeave={() => setActiveStage(null)}
            >
              <div className="w-14 h-14 bg-white rounded-xl shadow-sm border border-bg-100 flex items-center justify-center text-blue-600 mb-6 transition-all duration-300">
                <Globe className="w-7 h-7" />
              </div>
              <h3 className="text-xl font-bold text-text-primary mb-3 uppercase tracking-tighter">全渠道入口</h3>
              <p className="text-xs text-text-secondary leading-relaxed mb-4">
                集成 Shopify, WhatsApp, FB 等所有渠道。AI 实时获取订单意图。
              </p>
            </div>

            <ConnectionLine isActive={activeStage === 1 || activeStage === 2} />

            {/* Stage 2: OS Core */}
            <div 
              className={`flex-1 rounded-2xl p-8 border-2 transition-all duration-500 relative transform md:-translate-y-8
                ${activeStage === 2 ? 'border-purple-500 shadow-2xl bg-purple-50/50 scale-110 z-10' : 'border-purple-200 bg-white hover:border-purple-400'}
              `}
              onMouseEnter={() => setActiveStage(2)}
              onMouseLeave={() => setActiveStage(null)}
            >
              <div className="w-14 h-14 bg-purple-600 rounded-xl shadow-lg border border-purple-400 flex items-center justify-center text-white mb-6">
                <Cpu className="w-7 h-7" />
              </div>
              <h3 className="text-xl font-bold text-text-primary mb-3 uppercase tracking-tighter">智能业务中心</h3>
              <p className="text-xs text-text-secondary leading-relaxed mb-4">
                API 深度读取 Shopify 数据。<b>自动处理物流查询</b>与<b>工单生命周期</b>管理。
              </p>
              <div className="flex gap-2 mt-auto pt-4 border-t border-bg-200">
                 <div className="flex items-center gap-1 text-[8px] font-black text-purple-600"><MapPin size={8}/> TRACK_SYNC</div>
                 <div className="flex items-center gap-1 text-[8px] font-black text-purple-600"><ClipboardCheck size={8}/> TICKET_FLOW</div>
              </div>
            </div>

            <ConnectionLine isActive={activeStage === 2 || activeStage === 3} />

            {/* Stage 3: Dashboard */}
            <div 
              className={`flex-1 rounded-2xl p-8 border transition-all duration-500 relative
                ${activeStage === 3 ? 'border-amber-400 shadow-xl bg-amber-50/30 scale-105' : 'border-bg-200 bg-bg-50 hover:border-amber-200'}
              `}
              onMouseEnter={() => setActiveStage(3)}
              onMouseLeave={() => setActiveStage(null)}
            >
              <div className="w-14 h-14 bg-white rounded-xl shadow-sm border border-bg-100 flex items-center justify-center text-amber-600 mb-6">
                <BarChart3 className="w-7 h-7" />
              </div>
              <h3 className="text-xl font-bold text-text-primary mb-3 uppercase tracking-tighter">指标监控看板</h3>
              <p className="text-xs text-text-secondary leading-relaxed mb-4">
                透视转化率与坐席效率。AI 自动生成业务分析简报，驱动增长决策。
              </p>
            </div>

        </div>
        
        <div className="mt-12 text-center opacity-40 text-[10px] font-mono tracking-widest uppercase">
           Secure Real-time API Bridge: Shopify • AfterShip • PayPal • 17Track
        </div>
      </div>
    </section>
  );
};

export default PlatformArchitecture;