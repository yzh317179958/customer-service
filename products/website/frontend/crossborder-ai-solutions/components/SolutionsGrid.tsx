import React from 'react';
import { ArrowRight, ShoppingBag, Globe, Zap, Users } from 'lucide-react';
import SpotlightCard from './ui/SpotlightCard';

const SolutionCard: React.FC<{
  icon: React.ReactNode;
  title: string;
  desc: string;
  tags: string[];
  colorClass: string;
}> = ({ icon, title, desc, tags, colorClass }) => (
  <SpotlightCard className="group bg-white rounded-2xl p-8 border border-bg-200 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 h-full">
    <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${colorClass} opacity-10 rounded-bl-[100px] -mr-8 -mt-8 transition-transform group-hover:scale-150 pointer-events-none`}></div>
    
    <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-6 ${colorClass.replace('from-', 'bg-').replace('to-', 'text-white')} text-white shadow-md relative z-10`}>
      {icon}
    </div>
    
    <h3 className="text-xl font-bold text-text-primary mb-3 relative z-10">{title}</h3>
    <p className="text-text-secondary text-sm leading-relaxed mb-6 relative z-10">{desc}</p>
    
    <div className="flex flex-wrap gap-2 mb-6 relative z-10">
      {tags.map((tag, i) => (
        <span key={i} className="text-[10px] font-medium px-2 py-1 bg-bg-50 text-text-muted rounded border border-bg-100">
          {tag}
        </span>
      ))}
    </div>
    
    <div className="flex items-center text-brand-600 font-bold text-sm cursor-pointer group-hover:gap-2 transition-all mt-auto relative z-10">
      查看方案 <ArrowRight className="w-4 h-4 ml-1" />
    </div>
  </SpotlightCard>
);

const SolutionsGrid: React.FC = () => {
  return (
    <section className="py-24 bg-bg-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-text-primary mb-4">全场景解决方案</h2>
          <p className="text-text-secondary">无论您的业务规模如何，我们都有匹配的增长引擎</p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <SolutionCard 
            icon={<ShoppingBag className="w-6 h-6" />}
            title="DTC 品牌出海"
            desc="为追求品牌调性的独立站卖家打造。提供符合欧美本地化审美的AI接待与私域运营方案。"
            tags={['Shopify', '品牌调性', '复购率']}
            colorClass="from-purple-500 to-indigo-600"
          />
          <SolutionCard 
            icon={<Globe className="w-6 h-6" />}
            title="B2B 外贸工厂"
            desc="针对长周期、高客单价的询盘场景。AI 自动跟进线索，清洗无效询盘，加速成单。"
            tags={['询盘清洗', '邮件跟进', 'CRM集成']}
            colorClass="from-blue-500 to-cyan-600"
          />
          <SolutionCard 
            icon={<Zap className="w-6 h-6" />}
            title="爆品站群模式"
            desc="应对高并发流量。AI 0秒响应海量咨询，自动处理退换货，极致降低人工成本。"
            tags={['高并发', '自动售后', '多店管理']}
            colorClass="from-amber-500 to-orange-600"
          />
          <SolutionCard 
            icon={<Users className="w-6 h-6" />}
            title="客户服务外包"
            desc="为服务商提供技术底座。一个工作台管理数百个客户，AI 辅助人工提升人效 300%。"
            tags={['多租户', '绩效管理', '质检']}
            colorClass="from-emerald-500 to-green-600"
          />
        </div>
      </div>
    </section>
  );
};

export default SolutionsGrid;