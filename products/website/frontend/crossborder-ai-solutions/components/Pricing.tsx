import React, { useState } from 'react';
import { Check, Zap, Bot, BarChart, Sparkles } from 'lucide-react';
import Button from './ui/Button';

export const PRICING_PLANS = [
  {
    id: "free",
    name: "免费版",
    productFocus: "快速体验",
    icon: <Bot className="w-6 h-6" />,
    priceMonthly: 0,
    priceYearly: 0,
    desc: "适合初次体验。快速验证 AI 客服效果，零成本起步。",
    features: [
      "500 条会话/月",
      "1 个坐席",
      "1 个 Shopify 站点",
      "AI 智能客服",
      "订单 & 物流查询",
      "社群支持"
    ],
    recommended: false
  },
  {
    id: "basic",
    name: "基础版",
    productFocus: "小型团队首选",
    icon: <Zap className="w-6 h-6" />,
    priceMonthly: 199,
    priceYearly: 166,
    recommended: true,
    desc: "适合成长期卖家。完整的客服工作台，提升团队效率。",
    features: [
      "3000 条会话/月",
      "3 个坐席",
      "3 个 Shopify 站点",
      "AI 智能客服 + 坐席工作台",
      "工单管理系统",
      "快捷回复 (50条)",
      "微信 1v1 支持"
    ]
  },
  {
    id: "pro",
    name: "专业版",
    productFocus: "规模化运营",
    icon: <BarChart className="w-6 h-6" />,
    priceMonthly: 499,
    priceYearly: 416,
    desc: "适合多站点卖家。全功能解锁，专属服务支持。",
    features: [
      "10000 条会话/月",
      "10 个坐席",
      "9 个 Shopify 站点",
      "全部功能解锁",
      "工单 SLA 管理",
      "快捷回复 (无限)",
      "1v1 专属客户经理"
    ],
    recommended: false
  }
];

const PricingCard: React.FC<{
  plan: typeof PRICING_PLANS[0];
  period: 'monthly' | 'yearly';
}> = ({ plan, period }) => {
  const price = period === 'monthly' ? plan.priceMonthly : plan.priceYearly;
  
  return (
    <div className={`relative p-8 md:p-10 rounded-[3.5rem] flex flex-col h-full transition-all duration-700 border-2
      ${plan.recommended 
        ? 'bg-white text-text-primary shadow-[0_40px_100px_-20px_rgba(79,70,229,0.12)] border-brand-600 scale-105 z-10' 
        : 'bg-white text-text-primary border-bg-200 hover:border-brand-200 shadow-sm'
      }
    `}>
      {plan.recommended && (
        <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1.5 bg-brand-600 text-white text-[10px] font-black uppercase tracking-widest rounded-full shadow-lg flex items-center gap-2">
          <Sparkles size={10} /> Brand Choice
        </div>
      )}
      
      <div className="mb-10">
        <div className={`w-12 h-12 rounded-2xl flex items-center justify-center mb-6 ${plan.recommended ? 'bg-brand-600 text-white' : 'bg-brand-50 text-brand-600'} shadow-md`}>
            {plan.icon}
        </div>
        <div className="text-[10px] font-black uppercase tracking-[0.2em] mb-2 text-brand-600">
            {plan.productFocus}
        </div>
        <h3 className="text-2xl font-black mb-3">{plan.name}</h3>
        <p className="text-xs leading-relaxed text-text-secondary font-medium h-12">{plan.desc}</p>
        
        <div className="mt-8 flex items-baseline gap-1">
          {typeof price === 'number' ? (
            <>
              <span className="text-2xl font-bold">¥</span>
              <span className="text-6xl font-black tracking-tighter">{price}</span>
              <span className="text-sm text-text-muted font-bold ml-1">/月</span>
            </>
          ) : (
            <span className="text-4xl font-black text-text-primary">{price}</span>
          )}
        </div>
      </div>

      <ul className="space-y-4 mb-12 flex-grow">
        {plan.features.map((feat, i) => (
          <li key={i} className="flex items-start gap-3 text-sm font-medium">
            <Check className="h-4 w-4 shrink-0 mt-0.5 text-brand-600" />
            <span className="text-text-secondary">{feat}</span>
          </li>
        ))}
      </ul>

      <Button 
        variant={plan.recommended ? 'primary' : 'secondary'} 
        className={`w-full h-16 font-black shadow-lg ${plan.recommended ? 'shadow-brand-600/30' : ''}`}
        withArrow={plan.recommended}
      >
        {typeof price === 'string' ? '咨询深度绑定方案' : '开启 14 天免费 AI 转型之旅'}
      </Button>
    </div>
  );
};

const Pricing: React.FC = () => {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('yearly');

  return (
    <section id="pricing" className="py-32 bg-bg-50 relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center max-w-3xl mx-auto mb-24">
          <h2 className="text-4xl md:text-5xl font-black text-text-primary mb-8 tracking-tight">业务驱动的透明定价</h2>
          <p className="text-text-secondary text-lg mb-10 font-medium">所有的增长引擎都支持深度业务逻辑绑定，确保 AI 为您的品牌量身定制。</p>
          
          <div className="inline-flex bg-white p-1.5 rounded-full border border-bg-200 shadow-sm relative">
            <button 
              onClick={() => setBillingCycle('monthly')}
              className={`relative z-10 px-10 py-3 rounded-full text-sm font-black transition-all ${billingCycle === 'monthly' ? 'bg-brand-600 text-white shadow-md' : 'text-text-muted hover:text-text-primary'}`}
            >
              按月支付
            </button>
            <button 
              onClick={() => setBillingCycle('yearly')}
              className={`relative z-10 px-10 py-3 rounded-full text-sm font-black transition-all flex items-center gap-2 ${billingCycle === 'yearly' ? 'bg-brand-600 text-white shadow-md' : 'text-text-muted hover:text-text-primary'}`}
            >
              按年支付 <span className="text-[9px] px-1.5 py-0.5 bg-brand-100 text-brand-700 rounded-md font-bold">-20%</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-stretch max-w-6xl mx-auto">
          {PRICING_PLANS.map(plan => (
            <PricingCard key={plan.id} plan={plan} period={billingCycle} />
          ))}
        </div>
        
        <div className="mt-20 text-center">
           <p className="text-sm font-bold text-text-muted flex items-center justify-center gap-2">
              <Sparkles size={14} className="text-brand-600" />
              所有方案均提供免费的品牌转型对标诊断与数据迁移服务
           </p>
        </div>
      </div>
    </section>
  );
};

export default Pricing;