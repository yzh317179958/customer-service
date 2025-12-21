
import React from 'react';

/**
 * 计费管理模块入口 (Iframe 容器)
 * 
 * 架构声明：
 * 1. 本页面已按照需求清空原生 UI 实现。
 * 2. 后续将通过 iframe 嵌入独立部署的计费门户产品 (products/customer-portal)。
 * 3. 这里的背景色与工作台保持一致，以确保加载时的视觉平滑。
 */
const BillingView: React.FC = () => {
  return (
    <div className="w-full h-full bg-[#f8fafc] flex flex-col items-center justify-center p-8">
      {/* 
          开发备注：
          未来此处将替换为：
          <iframe 
            src="https://billing-portal.fiido.ai/?merchant_id=..." 
            className="w-full h-full border-none"
            title="Fiido Billing Portal"
          />
      */}
      <div className="max-w-md text-center space-y-4 animate-pulse">
        <div className="w-16 h-16 bg-slate-200 rounded-2xl mx-auto mb-6"></div>
        <h3 className="text-slate-400 font-black text-sm uppercase tracking-widest">
          独立计费门户模块加载中
        </h3>
        <p className="text-slate-300 text-[11px] font-medium leading-relaxed">
          正在建立与 Fiido Billing Service 的安全连接...<br/>
          该模块为独立产品，将通过分布式架构实现动态加载。
        </p>
      </div>
    </div>
  );
};

export default BillingView;
