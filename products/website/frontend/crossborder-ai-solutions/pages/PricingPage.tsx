import React, { useState } from 'react';
import { PageRoute } from '../App';
import Button from '../components/ui/Button';
import { PRICING_PLANS } from '../components/Pricing';
import { Check, ShieldCheck, Lock, Globe, ShoppingCart, Zap, TrendingUp } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface PricingPageProps {
  navigate: (route: PageRoute) => void;
}

const PricingPage: React.FC<PricingPageProps> = ({ navigate }) => {
  const [isYearly, setIsYearly] = useState(true);
  const [orders, setOrders] = useState(5000);
  const [showCheckout, setShowCheckout] = useState<string | null>(null);

  const calculateSavings = () => Math.floor(orders * 0.5 * 0.7);

  return (
    <div className="bg-white min-h-screen pt-24 relative selection:bg-brand-100">
      <AnimatePresence>
        {showCheckout && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="absolute inset-0 bg-slate-900/60 backdrop-blur-md"
              onClick={() => setShowCheckout(null)}
            />
            <motion.div 
              initial={{ scale: 0.9, opacity: 0, y: 20 }} animate={{ scale: 1, opacity: 1, y: 0 }} exit={{ scale: 0.9, opacity: 0, y: 20 }}
              className="relative bg-white rounded-[2.5rem] shadow-2xl w-full max-w-md overflow-hidden"
            >
              <div className="p-10">
                <div className="flex justify-between items-start mb-8">
                   <h3 className="text-2xl font-black flex items-center gap-2 tracking-tighter">
                      <ShoppingCart className="text-brand-600" size={28} /> 确认订阅
                   </h3>
                   <button onClick={() => setShowCheckout(null)} className="p-2 hover:bg-bg-100 rounded-full">✕</button>
                </div>
                <div className="space-y-4 mb-10">
                   <div className="flex justify-between p-6 bg-bg-50 rounded-2xl border border-bg-100">
                      <span className="font-bold text-text-secondary">所选方案</span>
                      <span className="text-brand-600 font-black">{showCheckout}</span>
                   </div>
                   <div className="flex justify-between p-6 bg-bg-50 rounded-2xl border border-bg-100">
                      <span className="font-bold text-text-secondary">计费周期</span>
                      <span className="text-brand-600 font-black">{isYearly ? '年度 (立省 20%)' : '月度'}</span>
                   </div>
                </div>
                <Button className="w-full h-16 text-lg font-black shadow-xl shadow-brand-600/20" onClick={() => setShowCheckout(null)}>前往安全支付</Button>
                <div className="flex justify-center gap-4 mt-8 opacity-30 grayscale scale-90">
                   <span className="font-mono text-[9px] border px-2 py-1 rounded font-bold">STRIPE</span>
                   <span className="font-mono text-[9px] border px-2 py-1 rounded font-bold">VISA</span>
                   <span className="font-mono text-[9px] border px-2 py-1 rounded font-bold">PAYPAL</span>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <section className="py-20 text-center">
         <h1 className="text-5xl lg:text-8xl font-black mb-8 tracking-tighter leading-none">简单，<span className="text-brand-600">透明。</span></h1>
         <p className="text-xl text-text-secondary mb-12 max-w-2xl mx-auto">所有方案均包含 14 天免费试用，无需信用卡。</p>
         
         <div className="flex items-center justify-center gap-4 mt-8">
            <span className={`text-sm font-black ${!isYearly ? 'text-text-primary' : 'text-text-muted'}`}>月付计划</span>
            <button onClick={() => setIsYearly(!isYearly)} className="w-16 h-8 bg-brand-600 rounded-full relative p-1 transition-colors">
               <motion.div 
                 animate={{ x: isYearly ? 32 : 0 }}
                 className="w-6 h-6 bg-white rounded-full shadow-md"
               />
            </button>
            <span className={`text-sm font-black ${isYearly ? 'text-text-primary' : 'text-text-muted'}`}>年付计划 (省 20%)</span>
         </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 grid grid-cols-1 md:grid-cols-3 gap-8 mb-32">
        {PRICING_PLANS.map((plan) => {
          const price = isYearly ? plan.priceYearly : plan.priceMonthly;
          return (
            <div key={plan.id} className={`p-10 rounded-[3rem] border-2 flex flex-col transition-all duration-500 ${plan.recommended ? 'border-brand-600 shadow-2xl scale-105 z-10 bg-slate-900 text-white' : 'border-bg-200 bg-white shadow-sm hover:border-brand-200'}`}>
              <div className="mb-8">
                <div className={`text-[10px] font-black uppercase tracking-[0.2em] mb-4 ${plan.recommended ? 'text-brand-400' : 'text-brand-600'}`}>{plan.productFocus}</div>
                <h3 className="text-3xl font-black mb-6">{plan.name}</h3>
                <div className="flex items-baseline gap-1">
                  <span className="text-2xl font-bold">¥</span>
                  <span className="text-6xl font-black tracking-tighter">{typeof price === 'number' ? price : price}</span>
                  {typeof price === 'number' && <span className="text-sm opacity-50">/月</span>}
                </div>
              </div>
              <ul className="space-y-5 mb-12 flex-grow">
                {plan.features.map((f, j) => (
                  <li key={j} className="flex items-start gap-3 text-sm font-medium">
                    <Check className={`${plan.recommended ? 'text-brand-400' : 'text-brand-600'} shrink-0 mt-0.5`} size={18}/> 
                    <span className="opacity-90">{f}</span>
                  </li>
                ))}
              </ul>
              <Button 
                variant={plan.recommended ? 'primary' : 'outline'} 
                className="w-full h-16 font-black text-base"
                onClick={() => setShowCheckout(plan.name)}
              >
                立即开启免费试用
              </Button>
            </div>
          );
        })}
      </section>

      <section className="bg-bg-50 py-32 border-y border-bg-200">
         <div className="max-w-5xl mx-auto px-4">
            <div className="text-center mb-16">
               <h2 className="text-4xl font-black tracking-tight mb-4">投入产出 ROI 预测</h2>
               <p className="text-text-secondary text-lg">基于您的业务规模，预估 AI 能为您节省的人力成本。</p>
            </div>
            <div className="bg-white rounded-[3.5rem] p-12 md:p-16 border border-bg-200 shadow-xl flex flex-col md:flex-row items-center gap-16">
               <div className="flex-1 w-full">
                  <div className="flex justify-between items-end mb-8">
                     <h3 className="text-xl font-black flex items-center gap-2"><TrendingUp className="text-brand-600" /> 月咨询量预测</h3>
                     <span className="text-brand-600 font-black text-2xl">{orders.toLocaleString()}</span>
                  </div>
                  <input 
                    type="range" min="1000" max="50000" step="1000" 
                    value={orders} onChange={(e) => setOrders(parseInt(e.target.value))}
                    className="w-full h-3 bg-brand-100 rounded-full appearance-none cursor-pointer accent-brand-600"
                  />
                  <div className="flex justify-between mt-6 text-[11px] font-black text-text-muted uppercase tracking-widest">
                     <span>1k /月</span>
                     <span>50k+ /月</span>
                  </div>
               </div>
               <div className="bg-brand-600 rounded-[3rem] p-12 text-white text-center min-w-[320px] shadow-2xl shadow-brand-600/30">
                  <div className="text-xs font-black mb-4 opacity-70 uppercase tracking-widest">预计每月节省 (人民币)</div>
                  <div className="text-7xl font-black mb-4 tracking-tighter">¥{calculateSavings().toLocaleString()}</div>
                  <p className="text-[10px] opacity-70 font-bold leading-relaxed">
                    * 基于全球平均坐席薪酬模型及 80% 自动化率测算
                  </p>
               </div>
            </div>
         </div>
      </section>

      <section className="py-24">
         <div className="max-w-7xl mx-auto px-4">
            <div className="flex flex-wrap justify-center items-center gap-12 md:gap-20 opacity-30 grayscale hover:opacity-100 transition-all duration-700">
               <div className="flex items-center gap-2 font-black text-sm"><ShieldCheck size={20}/> SOC2 Certified</div>
               <div className="flex items-center gap-2 font-black text-sm"><Lock size={20}/> GDPR Compliant</div>
               <div className="flex items-center gap-2 font-black text-sm"><Globe size={20}/> PCI DSS Compliance</div>
            </div>
         </div>
      </section>
    </div>
  );
};

export default PricingPage;