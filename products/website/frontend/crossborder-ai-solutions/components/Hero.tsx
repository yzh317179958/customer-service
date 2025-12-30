import React from 'react';
import Button from './ui/Button';
import ParticleBackground from './ui/ParticleBackground';
import { ShoppingBag, MapPin, Zap, Globe, Sparkles } from 'lucide-react';

const Hero: React.FC = () => {
  return (
    <section className="relative pt-24 pb-16 lg:pt-40 lg:pb-32 overflow-hidden bg-white">
      <ParticleBackground />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
        {/* 核心卖点标签 */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-brand-50 border border-brand-100 text-brand-700 text-[10px] font-black mb-8 animate-fade-in-up uppercase tracking-[0.2em]">
          <Sparkles size={12} className="fill-current" /> 全球领先的跨境独立站客服操作系统
        </div>

        {/* 升级后的主标题：具有高度且涵盖两款产品定位 */}
        <h1 className="text-5xl lg:text-7xl font-black text-text-primary mb-8 tracking-tighter leading-[1.1] animate-fade-in-up">
          跨境独立站全场景 <br/>
          <span className="text-brand-600">AI 智能增长引擎</span>
        </h1>

        {/* 核心价值金句 - 严格执行用户要求 */}
        <p className="text-lg md:text-xl text-text-secondary mb-12 leading-relaxed max-w-3xl mx-auto animate-fade-in-up [animation-delay:100ms]">
          通过 <span className="text-text-primary font-bold">AI智能客服</span> 实现售前售后咨询与订单自动化处理，利用 <span className="text-text-primary font-bold">坐席工作台</span> 统一管理工单与人工介入。让您的独立站拥有全天候业务专家。
        </p>

        {/* 快速决策入口 */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-20 animate-fade-in-up [animation-delay:200ms]">
          <Button size="lg" className="h-16 px-12 text-lg font-black shadow-2xl shadow-brand-600/30">立即开启免费试用</Button>
          <Button size="lg" variant="secondary" className="h-16 px-10 text-lg font-bold bg-white border-bg-200">
            预约演示
          </Button>
        </div>

        {/* 关键指标数据 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 py-8 border-y border-bg-100 animate-fade-in-up [animation-delay:300ms]">
          {[
            { label: "订单处理自动化", value: "90%+", icon: <ShoppingBag size={14}/> },
            { label: "物流查询时效", value: "实时", icon: <MapPin size={14}/> },
            { label: "人工接入效率", value: "提升300%", icon: <Zap size={14}/> },
            { label: "支持语种数量", value: "50+", icon: <Globe size={14}/> }
          ].map((stat, i) => (
            <div key={i} className="flex flex-col items-center gap-1">
              <div className="text-2xl font-black text-brand-600">{stat.value}</div>
              <div className="text-[10px] font-bold text-text-muted uppercase tracking-widest">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Hero;