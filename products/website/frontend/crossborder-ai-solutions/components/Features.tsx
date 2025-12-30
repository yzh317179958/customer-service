import React from 'react';
import { MessageSquare, Globe, UserCheck, PieChart, Share2, Settings } from 'lucide-react';

const Features: React.FC = () => {
  const features = [
    {
      title: "智能对话引擎",
      desc: "基于先进AI技术，支持多轮对话，上下文理解，自然流畅。",
      icon: <MessageSquare />
    },
    {
      title: "多语言支持",
      desc: "支持英/西/法/德/日等语言，自动识别，翻译准确率>95%。",
      icon: <Globe />
    },
    {
      title: "智能转人工",
      desc: "关键词触发，意图识别，复杂问题自动平滑转接人工客服。",
      icon: <UserCheck />
    },
    {
      title: "数据统计分析",
      desc: "对话量实时统计，问题类型分析，AI解决率自动报告。",
      icon: <PieChart />
    },
    {
      title: "多渠道接入",
      desc: "支持独立站、WhatsApp、Messenger、邮件自动回复。",
      icon: <Share2 />
    },
    {
      title: "定制化配置",
      desc: "话术库自定义，转人工规则配置，完全贴合您的业务流程。",
      icon: <Settings />
    }
  ];

  return (
    <section className="py-24 bg-white relative overflow-hidden">
      {/* Background Decor */}
      <div className="absolute top-0 left-0 w-full h-full bg-[linear-gradient(to_right,#f0f0f0_1px,transparent_1px),linear-gradient(to_bottom,#f0f0f0_1px,transparent_1px)] bg-[size:32px_32px] opacity-60"></div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl font-bold text-text-primary mb-6">核心功能展示</h2>
          <p className="text-lg text-text-secondary">
            专为跨境电商场景优化的六大核心能力
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((f, i) => (
            <div key={i} className="group p-8 bg-white border border-bg-200 rounded-2xl hover:border-brand-200 hover:shadow-lg transition-all duration-300">
              <div className="w-12 h-12 bg-brand-50 rounded-xl flex items-center justify-center text-brand-600 mb-6 group-hover:scale-110 transition-transform">
                {React.cloneElement(f.icon as React.ReactElement<{ className?: string }>, { className: "w-6 h-6" })}
              </div>
              <h3 className="text-xl font-bold text-text-primary mb-3">{f.title}</h3>
              <p className="text-text-secondary leading-relaxed">
                {f.desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features;