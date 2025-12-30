import React from 'react';
import { ShieldCheck, Lock, Server } from 'lucide-react';

const CompanyTrust: React.FC = () => {
  return (
    <section className="py-24 bg-white border-t border-bg-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          
          <div>
            <h2 className="text-3xl font-bold text-text-primary mb-6">安全合规，企业级信赖</h2>
            <p className="text-text-secondary text-lg mb-8 leading-relaxed">
              作为一家服务全球卖家的技术公司，我们深知数据安全的重要性。
              CrossBorderAI 严格遵循国际隐私保护标准，您的数据所有权完全归您所有。
            </p>
            
            <div className="flex flex-col gap-6">
                <div className="flex gap-4">
                    <div className="bg-green-100 p-3 rounded-xl h-fit">
                        <ShieldCheck className="w-6 h-6 text-green-600" />
                    </div>
                    <div>
                        <h3 className="font-bold text-text-primary">GDPR & CCPA 合规</h3>
                        <p className="text-sm text-text-secondary">严格遵守欧盟及美国加州的数据隐私法规，保障您在海外市场的合规经营。</p>
                    </div>
                </div>
                <div className="flex gap-4">
                    <div className="bg-brand-100 p-3 rounded-xl h-fit">
                        <Lock className="w-6 h-6 text-brand-600" />
                    </div>
                    <div>
                        <h3 className="font-bold text-text-primary">SOC 2 Type II 认证</h3>
                        <p className="text-sm text-text-secondary">通过国际权威的安全性、可用性及保密性审计。</p>
                    </div>
                </div>
                <div className="flex gap-4">
                    <div className="bg-purple-100 p-3 rounded-xl h-fit">
                        <Server className="w-6 h-6 text-purple-600" />
                    </div>
                    <div>
                        <h3 className="font-bold text-text-primary">企业级数据隔离</h3>
                        <p className="text-sm text-text-secondary">支持私有化部署 (On-Premise) 与混合云架构，数据绝不用于训练通用模型。</p>
                    </div>
                </div>
            </div>
          </div>

          <div className="bg-bg-50 rounded-3xl p-8 md:p-12 text-center border border-bg-200 relative overflow-hidden">
             <h3 className="text-xl font-bold text-text-primary mb-8 relative z-10">全球数据中心分布</h3>
             
             {/* CSS-based Abstract World Map */}
             <div className="relative w-full h-[300px] bg-white rounded-2xl shadow-sm border border-bg-200 mb-8 overflow-hidden group">
                 <div className="absolute inset-0 opacity-[0.03] bg-[linear-gradient(45deg,#000_25%,transparent_25%,transparent_75%,#000_75%,#000),linear-gradient(45deg,#000_25%,transparent_25%,transparent_75%,#000_75%,#000)] bg-[length:20px_20px] bg-[position:0_0,10px_10px]"></div>
                 
                 {/* Map Dots */}
                 <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80%] h-[60%] bg-[radial-gradient(ellipse_at_center,#e2e8f0_1px,transparent_1px)] bg-[size:10px_10px] rounded-full opacity-50"></div>

                 {/* Active Nodes */}
                 {/* US West */}
                 <div className="absolute top-[35%] left-[20%]">
                    <div className="w-3 h-3 bg-brand-500 rounded-full animate-ping absolute opacity-75"></div>
                    <div className="w-3 h-3 bg-brand-500 rounded-full relative shadow-lg shadow-brand-500/50"></div>
                    <div className="absolute top-4 left-1/2 -translate-x-1/2 text-[10px] font-bold text-brand-600 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">US West</div>
                 </div>
                 {/* US East */}
                 <div className="absolute top-[38%] left-[32%]">
                    <div className="w-2 h-2 bg-brand-400 rounded-full relative"></div>
                 </div>
                 {/* Europe */}
                 <div className="absolute top-[30%] left-[48%]">
                    <div className="w-3 h-3 bg-brand-500 rounded-full animate-ping absolute opacity-75 [animation-delay:0.3s]"></div>
                    <div className="w-3 h-3 bg-brand-500 rounded-full relative shadow-lg shadow-brand-500/50"></div>
                    <div className="absolute top-4 left-1/2 -translate-x-1/2 text-[10px] font-bold text-brand-600 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">Frankfurt</div>
                 </div>
                 {/* Singapore */}
                 <div className="absolute top-[55%] left-[75%]">
                    <div className="w-3 h-3 bg-brand-500 rounded-full animate-ping absolute opacity-75 [animation-delay:0.7s]"></div>
                    <div className="w-3 h-3 bg-brand-500 rounded-full relative shadow-lg shadow-brand-500/50"></div>
                    <div className="absolute top-4 left-1/2 -translate-x-1/2 text-[10px] font-bold text-brand-600 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">Singapore</div>
                 </div>
                 
                 {/* Connection Lines (Simulated via SVG) */}
                 <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-20">
                     <path d="M 20% 35% Q 34% 10% 48% 30%" stroke="#3b82f6" fill="none" strokeWidth="1" />
                     <path d="M 48% 30% Q 61% 60% 75% 55%" stroke="#3b82f6" fill="none" strokeWidth="1" />
                 </svg>
             </div>
             
             <div className="grid grid-cols-3 gap-4 text-center relative z-10">
                 <div>
                     <div className="text-2xl font-black text-brand-600">3</div>
                     <div className="text-xs text-text-muted font-bold uppercase">全球研发中心</div>
                 </div>
                 <div>
                     <div className="text-2xl font-black text-brand-600">99.9%</div>
                     <div className="text-xs text-text-muted font-bold uppercase">SLA 可用性</div>
                 </div>
                 <div>
                     <div className="text-2xl font-black text-brand-600">24/7</div>
                     <div className="text-xs text-text-muted font-bold uppercase">技术支持</div>
                 </div>
             </div>
          </div>

        </div>
      </div>
    </section>
  );
};

export default CompanyTrust;