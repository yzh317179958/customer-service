import React from 'react';
import SpotlightCard from './ui/SpotlightCard';
import { ArrowRight, BookOpen, FileText, Video } from 'lucide-react';

const ResourcesSection: React.FC = () => {
  const resources = [
    {
      type: "行业白皮书",
      icon: <FileText className="w-4 h-4" />,
      title: "2025 跨境电商独立站 AI 应用趋势报告",
      desc: "深入分析 500+ 头部 DTC 品牌的 AI 落地实践，揭示未来增长机会。",
      date: "2025-05-12",
      bgClass: "from-blue-50 to-indigo-50"
    },
    {
      type: "最佳实践",
      icon: <BookOpen className="w-4 h-4" />,
      title: "如何利用 AI 将弃单召回率提升 300%",
      desc: "实战案例解析：通过个性化 WhatsApp 营销召回高意向客户的完整SOP。",
      date: "2025-06-01",
      bgClass: "from-purple-50 to-pink-50"
    },
    {
      type: "视频教程",
      icon: <Video className="w-4 h-4" />,
      title: "5分钟搭建您的第一个 AI 客服坐席",
      desc: "手把手教您如何配置知识库、设置转人工规则并上线。",
      date: "2025-06-15",
      bgClass: "from-amber-50 to-orange-50"
    }
  ];

  return (
    <section className="py-24 bg-bg-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-end mb-12">
          <div>
            <h2 className="text-3xl font-bold text-text-primary mb-2">资源中心</h2>
            <p className="text-text-secondary">跨境出海实战干货，助您少走弯路</p>
          </div>
          <a href="#" className="hidden md:flex items-center font-bold text-brand-600 hover:underline">
            查看更多内容 <ArrowRight className="w-4 h-4 ml-1" />
          </a>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {resources.map((item, i) => (
            <SpotlightCard key={i} className="bg-white rounded-2xl border border-bg-200 shadow-sm flex flex-col h-full group cursor-pointer hover:border-brand-200 hover:shadow-lg transition-all">
              <div className={`h-48 w-full relative overflow-hidden bg-gradient-to-br ${item.bgClass}`}>
                {/* SVG Pattern Overlay */}
                <svg className="absolute inset-0 w-full h-full opacity-30" width="100%" height="100%">
                    <defs>
                        <pattern id={`pattern-${i}`} x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
                            <path d="M0 40L40 0H20L0 20M40 40V20L20 40" stroke="currentColor" strokeWidth="1" fill="none" className="text-brand-200"/>
                        </pattern>
                    </defs>
                    <rect width="100%" height="100%" fill={`url(#pattern-${i})`} />
                </svg>
                
                <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur px-3 py-1.5 rounded-full text-xs font-bold text-text-primary flex items-center gap-2 shadow-sm border border-white/50">
                  {item.icon} {item.type}
                </div>
              </div>
              <div className="p-6 flex flex-col flex-grow">
                <div className="text-xs text-text-muted mb-3 flex items-center gap-2">
                    <span className="w-1.5 h-1.5 bg-brand-400 rounded-full"></span>
                    {item.date}
                </div>
                <h3 className="text-lg font-bold text-text-primary mb-3 group-hover:text-brand-600 transition-colors line-clamp-2">
                  {item.title}
                </h3>
                <p className="text-sm text-text-secondary leading-relaxed line-clamp-3 mb-4 flex-grow">
                  {item.desc}
                </p>
                <div className="text-brand-600 text-sm font-bold flex items-center mt-auto">
                  阅读全文 <ArrowRight className="w-4 h-4 ml-1 transition-transform group-hover:translate-x-1" />
                </div>
              </div>
            </SpotlightCard>
          ))}
        </div>
        
        <div className="mt-8 text-center md:hidden">
            <a href="#" className="inline-flex items-center font-bold text-brand-600 hover:underline">
                查看更多内容 <ArrowRight className="w-4 h-4 ml-1" />
            </a>
        </div>
      </div>
    </section>
  );
};

export default ResourcesSection;