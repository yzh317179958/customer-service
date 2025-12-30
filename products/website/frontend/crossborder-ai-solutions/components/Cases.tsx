import React from 'react';
import { ArrowUpRight, TrendingUp, Users, Clock } from 'lucide-react';

const CaseCard: React.FC<{
  title: string;
  industry: string;
  stats: { label: string; value: string; icon: React.ReactNode }[];
  quote: string;
  tags: string[];
}> = ({ title, industry, stats, quote, tags }) => (
  <div className="bg-white p-8 rounded-[2.5rem] border border-bg-200 shadow-sm hover:shadow-2xl hover:-translate-y-2 transition-all duration-500 group">
    <div className="flex justify-between items-start mb-8">
      <div>
        <div className="text-[10px] font-black text-brand-600 uppercase tracking-widest mb-1">{industry}</div>
        <h3 className="font-bold text-text-primary text-xl group-hover:text-brand-600 transition-colors">{title}</h3>
      </div>
      <div className="w-12 h-12 bg-bg-50 rounded-2xl flex items-center justify-center group-hover:bg-brand-600 group-hover:text-white transition-all duration-500">
        <ArrowUpRight className="w-6 h-6" />
      </div>
    </div>
    
    <div className="grid grid-cols-2 gap-4 mb-8">
      {stats.map((stat, i) => (
        <div key={i} className="bg-bg-50 p-4 rounded-2xl border border-bg-100 group-hover:border-brand-100 transition-colors">
          <div className="text-brand-600 mb-1">{stat.icon}</div>
          <div className="text-xl font-black text-text-primary">{stat.value}</div>
          <div className="text-[10px] font-bold text-text-muted uppercase">{stat.label}</div>
        </div>
      ))}
    </div>

    <div className="flex flex-wrap gap-2 mb-6">
      {tags.map((tag, i) => (
        <span key={i} className="text-[9px] font-bold px-2 py-0.5 bg-brand-50 text-brand-700 rounded-full border border-brand-100 uppercase">
          {tag}
        </span>
      ))}
    </div>

    <blockquote className="text-text-secondary italic text-sm border-l-4 border-brand-200 pl-4 leading-relaxed line-clamp-3">
      "{quote}"
    </blockquote>
  </div>
);

const Cases: React.FC = () => {
  return (
    <section id="cases" className="py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-20">
          <h2 className="text-4xl md:text-5xl font-black text-text-primary mb-6 tracking-tight">
            实效说话，数据见证
          </h2>
          <p className="text-text-secondary text-lg">
            已有超过 500+ 领先跨境卖家通过 CrossBorderAI 实现了客服部门从成本中心到利润中心的转型。
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-20">
          <CaseCard 
            title="某全球 3C 消费电子巨头"
            industry="消费电子 | 年 GMV $50M+"
            stats={[
              { label: "节省人力", value: "72%", icon: <Users size={16}/> },
              { label: "ROI 提升", value: "3.5x", icon: <TrendingUp size={16}/> }
            ]}
            tags={["Shopify Plus", "多语言", "自动售后"]}
            quote="以前我们需要 50 人的客服团队，现在只需 10 人处理核心争议。AI 解决了一切重复劳动，这在黑五期间救了我们的命。"
          />
          <CaseCard 
            title="DTC 时尚女装品牌"
            industry="时尚服饰 | 年 GMV $20M+"
            stats={[
              { label: "询盘转化", value: "+28%", icon: <TrendingUp size={16}/> },
              { label: "夜间响应", value: "< 2s", icon: <Clock size={16}/> }
            ]}
            tags={["WhatsApp", "弃单召回", "个性化"]}
            quote="夜间（欧美白天）的流量转化一直是个痛点。AI 上线后，我们的弃单召回率提升了 3 倍，因为它能在黄金 5 分钟内完成沟通。"
          />
          <CaseCard 
            title="知名智能家居独立站"
            industry="智能家居 | 年 GMV $15M+"
            stats={[
              { label: "CSAT 评分", value: "4.9/5", icon: <Users size={16}/> },
              { label: "工单时效", value: "-60%", icon: <Clock size={16}/> }
            ]}
            tags={["统一入口", "技术支持", "全渠道"]}
            quote="原本由于响应慢导致的大量退单消失了。AI 坐席不仅快，而且能准确从 Shopify 提取订单信息，专业度超乎想象。"
          />
        </div>

        {/* Logo Cloud Placeholder */}
        <div className="bg-bg-50 rounded-[3rem] p-12 text-center border border-bg-100">
           <p className="text-xs font-bold text-text-muted uppercase tracking-widest mb-10">Trusted by fast-growing brands</p>
           <div className="flex flex-wrap justify-center items-center gap-12 md:gap-24 opacity-40 grayscale">
              {['ANKER', 'SHEIN', 'PATPAT', 'AUKEY', 'RAVPower'].map(logo => (
                <span key={logo} className="text-2xl font-black tracking-tighter text-text-primary">{logo}</span>
              ))}
           </div>
        </div>
      </div>
    </section>
  );
};

export default Cases;