import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

const FAQItem: React.FC<{ question: string; answer: string }> = ({ question, answer }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="border-b border-slate-800">
      <button 
        className="w-full py-6 flex items-center justify-between text-left focus:outline-none group"
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className="text-lg font-medium text-slate-200 group-hover:text-brand-400 transition-colors">{question}</span>
        {isOpen ? <ChevronUp className="h-5 w-5 text-brand-400" /> : <ChevronDown className="h-5 w-5 text-slate-400 group-hover:text-white" />}
      </button>
      <div 
        className={`overflow-hidden transition-all duration-300 ${isOpen ? 'max-h-48 opacity-100 pb-6' : 'max-h-0 opacity-0'}`}
      >
        <p className="text-slate-400 leading-relaxed">
          {answer}
        </p>
      </div>
    </div>
  );
};

const FAQ: React.FC = () => {
  const faqs = [
    {
      question: "Fiido 支持哪些电商平台？",
      answer: "目前 Fiido 已深度集成 Shopify 平台，支持订单查询、物流追踪等核心功能。后续将支持更多主流电商平台。"
    },
    {
      question: "AI 客服能处理哪些问题？",
      answer: "Fiido AI 客服可自动处理订单查询、物流追踪、退换货咨询、产品问答等常见问题，复杂问题自动转人工坐席。"
    },
    {
      question: "如何开始使用 Fiido？",
      answer: "选择适合的套餐后，扫码付款，添加客服微信即可开通。我们会协助您完成 Shopify 店铺绑定和 AI 配置。"
    },
    {
      question: "免费版有什么限制？",
      answer: "免费版每月 500 条会话，支持 1 个坐席和 1 个 Shopify 站点。适合初次体验，验证 AI 客服效果。"
    }
  ];

  return (
    <section id="faq" className="py-24">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-3xl md:text-4xl font-bold text-white mb-12 text-center">
          常见问题解答
        </h2>
        <div className="space-y-2">
          {faqs.map((faq, i) => (
            <FAQItem key={i} {...faq} />
          ))}
        </div>
      </div>
    </section>
  );
};

export default FAQ;