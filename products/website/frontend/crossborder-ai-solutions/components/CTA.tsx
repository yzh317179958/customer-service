import React from 'react';
import Button from './ui/Button';
import { MessageCircle, Mail, TrendingUp, Clock, Zap, ShieldCheck, Sparkles } from 'lucide-react';

const CTA: React.FC = () => {
  return (
    <section className="py-24 bg-white relative overflow-hidden">
      {/* 极简背景装饰 */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full opacity-30 pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-brand-100/40 blur-[120px] rounded-full"></div>
        <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-indigo-100/40 blur-[120px] rounded-full"></div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        
        {/* 高感亮色卡片 */}
        <div className="relative bg-bg-50/50 backdrop-blur-xl rounded-[4rem] p-10 md:p-24 overflow-hidden shadow-[0_30px_80px_-20px_rgba(79,70,229,0.06)] border border-bg-100">
          
          <div className="relative z-10 flex flex-col items-center text-center">
            {/* 顶层小标签 */}
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-brand-100 rounded-full text-brand-600 text-[10px] font-black uppercase tracking-[0.25em] mb-12 shadow-sm">
              <Sparkles size={12} className="fill-current" /> Empowering Brand AI Evolution
            </div>

            <h2 className="text-3xl lg:text-5xl font-black text-text-primary mb-10 tracking-tighter leading-tight max-w-6xl whitespace-nowrap">
              AI 深度打通经营全链路：赋能品牌 <span className="text-brand-600">AI 化转型</span> 与业务深度绑定的 <span className="text-brand-600">智能增长方案</span>
            </h2>

            <p className="text-text-secondary text-lg md:text-xl mb-16 max-w-3xl leading-relaxed font-medium">
              不再只是处理对话。我们用 AI 渗透每一个业务微小细节，将独立站从“劳动密集型”转变为“智能增长型”，实现品牌溢价与经营效率的双重跃迁。
            </p>

            {/* 业务深度绑定指标展示 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full max-w-5xl mb-16">
               {[
                 { label: "全细节自动化率", value: "95%+", icon: <Zap size={20}/>, color: "text-brand-600", bg: "bg-brand-50" },
                 { label: "品牌资产沉淀", value: "100%", icon: <ShieldCheck size={20}/>, color: "text-blue-600", bg: "bg-blue-50" },
                 { label: "业务转化闭环", value: "实时驱动", icon: <TrendingUp size={20}/>, color: "text-green-600", bg: "bg-green-50" }
               ].map((item, i) => (
                 <div key={i} className="bg-white border border-bg-200/60 rounded-[2.5rem] p-8 flex flex-col items-center group hover:border-brand-300 transition-all duration-500 hover:shadow-xl">
                    <div className={`${item.bg} ${item.color} p-4 rounded-2xl mb-5 group-hover:scale-110 transition-transform`}>{item.icon}</div>
                    <div className="text-3xl font-black text-text-primary">{item.value}</div>
                    <div className="text-[10px] font-bold text-text-muted uppercase tracking-[0.15em] mt-3">{item.label}</div>
                 </div>
               ))}
            </div>
            
            <div className="flex flex-col sm:flex-row gap-6 justify-center w-full sm:w-auto">
              <Button size="lg" className="h-16 px-14 text-lg font-black shadow-2xl shadow-brand-600/20">立即开启 AI 转型诊断</Button>
              <Button size="lg" variant="secondary" className="h-16 px-12 text-lg font-bold bg-white border-bg-200">
                获取深度绑定方案
              </Button>
            </div>
          </div>
        </div>

        {/* 底部联系渠道 */}
        <div className="mt-16 flex flex-wrap justify-center gap-12 md:gap-20">
            {[
              { title: "微信咨询", icon: <MessageCircle /> },
              { title: "WhatsApp", icon: <MessageCircle /> },
              { title: "E-mail", icon: <Mail /> }
            ].map((channel, i) => (
              <div key={i} className="flex items-center gap-4 group cursor-pointer">
                  <div className="w-12 h-12 bg-white border border-bg-100 rounded-2xl flex items-center justify-center text-text-muted group-hover:bg-brand-600 group-hover:text-white transition-all duration-300">
                      {React.cloneElement(channel.icon as React.ReactElement<any>, { size: 20 })}
                  </div>
                  <span className="font-black text-text-primary text-xs uppercase tracking-widest">{channel.title}</span>
              </div>
            ))}
        </div>

      </div>
    </section>
  );
};

export default CTA;