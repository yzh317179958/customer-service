import React from 'react';
import { XCircle, CheckCircle } from 'lucide-react';

const PainPoints: React.FC = () => {
  return (
    <section className="py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-text-primary mb-4">您的跨境电商是否面临这些痛点？</h2>
          <p className="text-text-secondary">传统客服模式成本高、效率低，严重制约业务增长</p>
        </div>

        <div className="grid md:grid-cols-2 gap-12 items-center relative">
          
          {/* Pain Points (Left) */}
          <div className="space-y-6">
            <div className="p-6 rounded-2xl bg-red-50/50 border border-red-100 transition-transform hover:-translate-y-1">
              <div className="flex gap-4">
                <XCircle className="w-6 h-6 text-red-500 shrink-0" />
                <div>
                  <h3 className="font-bold text-text-primary mb-1">客服成本高昂</h3>
                  <p className="text-sm text-text-secondary">一个客服年薪6-8万，多语言团队成本更高，管理难度大。</p>
                </div>
              </div>
            </div>
            <div className="p-6 rounded-2xl bg-red-50/50 border border-red-100 transition-transform hover:-translate-y-1">
              <div className="flex gap-4">
                <XCircle className="w-6 h-6 text-red-500 shrink-0" />
                <div>
                  <h3 className="font-bold text-text-primary mb-1">时差问题严重</h3>
                  <p className="text-sm text-text-secondary">海外客户咨询时国内已下班，错失订单，响应不及时导致退单。</p>
                </div>
              </div>
            </div>
            <div className="p-6 rounded-2xl bg-red-50/50 border border-red-100 transition-transform hover:-translate-y-1">
              <div className="flex gap-4">
                <XCircle className="w-6 h-6 text-red-500 shrink-0" />
                <div>
                  <h3 className="font-bold text-text-primary mb-1">重复问题多，效率低</h3>
                  <p className="text-sm text-text-secondary">80%是订单查询、物流等重复问题，人工回复效率低下。</p>
                </div>
              </div>
            </div>
          </div>

          {/* VS Badge */}
          <div className="hidden md:flex absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-12 h-12 bg-white rounded-full border border-bg-200 items-center justify-center font-bold text-brand-500 shadow-lg z-10">
            VS
          </div>

          {/* Solution (Right) */}
          <div className="space-y-6">
             <div className="p-6 rounded-2xl bg-brand-50/50 border border-brand-100 shadow-sm transition-transform hover:-translate-y-1">
              <div className="flex gap-4">
                <CheckCircle className="w-6 h-6 text-brand-600 shrink-0" />
                <div>
                  <h3 className="font-bold text-text-primary mb-1">降低60-80%成本</h3>
                  <p className="text-sm text-text-secondary">AI处理大部分咨询，大幅减少人力需求，仅需少量人工处理复杂问题。</p>
                </div>
              </div>
            </div>
            <div className="p-6 rounded-2xl bg-brand-50/50 border border-brand-100 shadow-sm transition-transform hover:-translate-y-1">
              <div className="flex gap-4">
                <CheckCircle className="w-6 h-6 text-brand-600 shrink-0" />
                <div>
                  <h3 className="font-bold text-text-primary mb-1">24/7全天候智能响应</h3>
                  <p className="text-sm text-text-secondary">无论客户何时咨询，秒级响应，不错过任何一个销售机会。</p>
                </div>
              </div>
            </div>
            <div className="p-6 rounded-2xl bg-brand-50/50 border border-brand-100 shadow-sm transition-transform hover:-translate-y-1">
              <div className="flex gap-4">
                <CheckCircle className="w-6 h-6 text-brand-600 shrink-0" />
                <div>
                  <h3 className="font-bold text-text-primary mb-1">多语言 & 智能处理</h3>
                  <p className="text-sm text-text-secondary">支持英/西/法/德/日等语言自动识别，AI自动处理订单查询。</p>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
};

export default PainPoints;