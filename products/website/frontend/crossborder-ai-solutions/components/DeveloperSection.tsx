import React from 'react';
import { Terminal, Copy, Check, ArrowRight } from 'lucide-react';
import Button from './ui/Button';

const DeveloperSection: React.FC = () => {
  return (
    <section className="py-24 bg-slate-900 text-white overflow-hidden relative border-y border-slate-800">
      {/* High-Tech Animated Cyber Grid Background */}
      <div className="absolute inset-0 z-0 opacity-20 pointer-events-none">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>
        <div className="absolute left-0 right-0 top-0 -z-10 m-auto h-[310px] w-[310px] rounded-full bg-brand-500 opacity-20 blur-[100px]"></div>
      </div>
      
      {/* Moving Scanline Overlay */}
      <div className="absolute inset-0 z-0 pointer-events-none bg-gradient-to-b from-transparent via-brand-500/5 to-transparent animate-[scan_3s_ease-in-out_infinite] h-[200%] w-full -translate-y-[50%]"></div>
      
      <style>{`
        @keyframes scan {
          0% { transform: translateY(-50%); }
          100% { transform: translateY(0%); }
        }
      `}</style>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          
          {/* Left: Content */}
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-400 text-xs font-bold uppercase tracking-wider mb-6">
              <Terminal className="w-3 h-3" /> API First Architecture
            </div>
            <h2 className="text-3xl md:text-4xl font-bold mb-6">
              以 API 为先的架构<br/>
              <span className="text-slate-400">构建您的专属工作流</span>
            </h2>
            <p className="text-slate-400 text-lg mb-8 leading-relaxed">
              我们开放了 CrossBorderAI 的核心能力。您可以轻松读取对话分析数据、触发自定义营销动作，或将 AI 坐席无缝嵌入到您自研的 ERP 或工单系统中。
            </p>
            
            <div className="space-y-4 mb-10">
              <div className="flex items-start gap-3">
                <div className="w-5 h-5 rounded-full bg-brand-500/20 flex items-center justify-center mt-1"><Check className="w-3 h-3 text-brand-400" /></div>
                <div>
                  <div className="font-bold text-sm">完善的开发者文档</div>
                  <div className="text-xs text-slate-500">符合 OpenAPI 3.0 标准，提供 Python/Node.js SDK。</div>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-5 h-5 rounded-full bg-brand-500/20 flex items-center justify-center mt-1"><Check className="w-3 h-3 text-brand-400" /></div>
                <div>
                  <div className="font-bold text-sm">Webhooks 实时推送</div>
                  <div className="text-xs text-slate-500">支持订单状态变更、高意向客户识别等事件订阅。</div>
                </div>
              </div>
            </div>

            <div className="flex gap-4">
              <Button className="bg-brand-600 text-white hover:bg-brand-500 border border-transparent shadow-lg shadow-brand-900/50">
                阅读开发者文档
              </Button>
              <Button className="bg-white/5 text-white border border-white/20 hover:bg-white/10 backdrop-blur-sm">
                获取 API Key <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>

          {/* Right: Code Block */}
          <div className="bg-slate-950 rounded-2xl border border-slate-800 shadow-2xl overflow-hidden relative group transform hover:scale-[1.01] transition-transform duration-500">
            {/* Terminal Glow */}
            <div className="absolute -inset-1 bg-gradient-to-r from-brand-500 to-purple-600 rounded-2xl opacity-20 blur-lg group-hover:opacity-30 transition duration-500"></div>
            
            <div className="relative bg-slate-950 rounded-2xl overflow-hidden">
                <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/50">
                <div className="flex gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/50"></div>
                    <div className="w-3 h-3 rounded-full bg-amber-500/20 border border-amber-500/50"></div>
                    <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/50"></div>
                </div>
                <div className="text-xs font-mono text-slate-500">POST /v1/analysis/order</div>
                <Copy className="w-4 h-4 text-slate-600 cursor-pointer hover:text-white transition-colors" />
                </div>
                <div className="p-6 overflow-x-auto">
                <pre className="font-mono text-sm leading-relaxed">
                    <code className="language-json">
    <span className="text-purple-400">curl</span> -X POST https://api.crossborder.ai/v1/analyze \<br/>
    -H <span className="text-green-400">"Authorization: Bearer sk_live_..."</span> \<br/>
    -d <span className="text-amber-300">
      {`'{
        "platform": "shopify",
        "order_id": "#1024",
        "customer_message": "Can I return this? It fits small."
      }'`}
    </span>
                    </code>
                </pre>
                <div className="mt-4 pt-4 border-t border-slate-800">
                    <div className="text-xs font-bold text-slate-500 mb-2 uppercase flex items-center gap-2">
                         Response (200 OK)
                         <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                    </div>
                    <pre className="font-mono text-sm text-green-400">
    {`{
    "intent": "return_request",
    "reason": "fit_issue",
    "sentiment": "neutral",
    "suggested_action": {
        "type": "offer_exchange",
        "coupon": "EXCHANGE_FREE_SHIP"
    }
    }`}
                    </pre>
                </div>
                </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
};

export default DeveloperSection;