import React from 'react';
import { Check } from 'lucide-react';

const Trust: React.FC = () => {
  const reasons = [
    { title: "专注跨境电商", desc: "深度理解独立站业务痛点，不是通用AI工具。" },
    { title: "定制化服务", desc: "非标准SaaS，根据您的业务定制话术和流程。" },
    { title: "快速交付", desc: "2周内完成定制和部署，快速见效。" },
    { title: "持续支持", desc: "年订阅制，提供长期技术支持和产品升级。" },
  ];

  return (
    <section className="py-24 bg-bg-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Why Us */}
        <div className="bg-white rounded-3xl p-8 md:p-12 border border-bg-200 shadow-sm mb-16">
            <h2 className="text-2xl md:text-3xl font-bold text-text-primary mb-10 text-center">为什么选择我们？</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
                {reasons.map((r, i) => (
                    <div key={i} className="flex flex-col items-start">
                        <div className="bg-green-100 p-1 rounded-full mb-3">
                            <Check className="w-5 h-5 text-green-600" />
                        </div>
                        <h3 className="font-bold text-text-primary text-lg mb-2">{r.title}</h3>
                        <p className="text-sm text-text-secondary leading-relaxed">{r.desc}</p>
                    </div>
                ))}
            </div>
        </div>

        {/* Logos */}
        <div className="text-center">
            <p className="text-sm font-semibold text-text-muted mb-8 uppercase tracking-wider">
              合作伙伴
            </p>
            <div className="flex flex-wrap justify-center gap-8 md:gap-16 opacity-50 grayscale hover:grayscale-0 transition-all duration-500">
               {["Shopify", "WooCommerce", "Magento", "BigCommerce", "Shoplazza"].map((name) => (
                   <span key={name} className="text-xl font-bold text-text-secondary">{name}</span>
               ))}
            </div>
        </div>
      </div>
    </section>
  );
};

export default Trust;