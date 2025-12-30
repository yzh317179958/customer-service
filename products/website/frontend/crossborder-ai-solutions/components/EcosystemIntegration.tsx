import React from 'react';
import { Settings, PenTool, Cpu, Layers, CheckCircle2, Zap } from 'lucide-react';
import Button from './ui/Button';

const CustomizationSection: React.FC = () => {
  return (
    <section className="py-32 bg-white overflow-hidden relative border-y border-bg-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col lg:flex-row gap-16 items-center">
          
          {/* 左侧文案 */}
          <div className="lg:w-1/2">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-brand-50 border border-brand-100 text-brand-700 rounded-full text-[10px] font-black uppercase tracking-widest mb-6">
              <Settings size={12} /> Customization as a Service
            </div>
            <h2 className="text-4xl md:text-5xl font-black text-text-primary mb-8 tracking-tight leading-[1.1]">
              深度定制，<br />
              <span className="text-brand-600 text-transparent bg-clip-text bg-gradient-to-r from-brand-600 to-indigo-600">深度绑定您的业务需求</span>
            </h2>
            <p className="text-text-secondary text-lg mb-10 leading-relaxed font-medium">
              我们深知每个独立站的业务逻辑都是独特的。因此，我们的每一款产品都支持免费深度定制，确保 AI 不仅仅是一个聊天框，而是真正理解您业务流的增长引擎。
            </p>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-12">
               {[
                 { title: "私有化模型训练", desc: "基于您的历史话术进行微调" },
                 { title: "专属 API 深度集成", desc: "无缝对接您的 ERP 与系统" },
                 { title: "个性化流程定制", desc: "完美复现您的售后 SOP" },
                 { title: "全域 UI/UX 适配", desc: "保持品牌一致性的视觉呈现" }
               ].map((item, i) => (
                 <div key={i} className="flex gap-3">
                   <div className="mt-1 text-brand-600"><CheckCircle2 size={18} /></div>
                   <div>
                     <div className="font-bold text-text-primary text-sm mb-1">{item.title}</div>
                     <div className="text-xs text-text-muted">{item.desc}</div>
                   </div>
                 </div>
               ))}
            </div>

            <Button size="lg" className="h-16 px-10 shadow-xl shadow-brand-600/20" withArrow>
               开启您的定制化方案
            </Button>
          </div>

          {/* 右侧视觉：模块化定制隐喻 */}
          <div className="lg:w-1/2 relative w-full aspect-square md:aspect-auto md:h-[500px]">
            <div className="absolute inset-0 bg-slate-50 rounded-[3rem] border border-slate-200 overflow-hidden">
               {/* 背景装饰：科技网格 */}
               <div className="absolute inset-0 opacity-[0.03] bg-[linear-gradient(to_right,#000_1px,transparent_1px),linear-gradient(to_bottom,#000_1px,transparent_1px)] bg-[size:30px_30px]"></div>
               
               {/* 悬浮的定制卡片 */}
               <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-sm px-4">
                  
                  {/* 中心核心：您的业务 */}
                  <div className="relative z-20 bg-white p-8 rounded-[2rem] border-2 border-brand-600 shadow-2xl text-center group">
                     <div className="w-16 h-16 bg-brand-600 rounded-2xl flex items-center justify-center text-white mx-auto mb-4 group-hover:rotate-12 transition-transform">
                        <Cpu size={32} />
                     </div>
                     <div className="text-sm font-black text-brand-600 uppercase tracking-widest mb-1">Your Business Core</div>
                     <div className="text-xl font-black text-slate-900">核心业务大脑</div>
                  </div>

                  {/* 围绕核心的定制化组件 */}
                  <div className="absolute -top-16 -left-8 md:-left-12 bg-white/80 backdrop-blur p-4 rounded-2xl border border-slate-200 shadow-lg flex items-center gap-3 animate-[bounce_4s_infinite]">
                     <div className="p-2 bg-blue-100 text-blue-600 rounded-lg"><Layers size={16}/></div>
                     <span className="text-[10px] font-black uppercase tracking-wider text-slate-600">私有知识库</span>
                  </div>

                  <div className="absolute -bottom-12 -right-4 md:-right-8 bg-white/80 backdrop-blur p-4 rounded-2xl border border-slate-200 shadow-lg flex items-center gap-3 animate-[bounce_5s_infinite_1s]">
                     <div className="p-2 bg-green-100 text-green-600 rounded-lg"><Zap size={16}/></div>
                     <span className="text-[10px] font-black uppercase tracking-wider text-slate-600">快速处理引擎</span>
                  </div>

                  <div className="absolute top-1/4 -right-16 bg-white/80 backdrop-blur p-4 rounded-2xl border border-slate-200 shadow-lg flex items-center gap-3 animate-[bounce_6s_infinite_0.5s]">
                     <div className="p-2 bg-purple-100 text-purple-600 rounded-lg"><PenTool size={16}/></div>
                     <span className="text-[10px] font-black uppercase tracking-wider text-slate-600">定制化 UI</span>
                  </div>

                  {/* 连接线模拟 */}
                  <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-20 -z-10">
                    <line x1="20%" y1="20%" x2="50%" y2="50%" stroke="#4F46E5" strokeWidth="2" strokeDasharray="5,5" />
                    <line x1="80%" y1="80%" x2="50%" y2="50%" stroke="#4F46E5" strokeWidth="2" strokeDasharray="5,5" />
                    <line x1="85%" y1="30%" x2="50%" y2="50%" stroke="#4F46E5" strokeWidth="2" strokeDasharray="5,5" />
                  </svg>
               </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
};

export default CustomizationSection;