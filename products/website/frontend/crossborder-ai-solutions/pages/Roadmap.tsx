import React from 'react';
import { PageRoute } from '../App';
import { Flag, ArrowRight } from 'lucide-react';

interface RoadmapProps {
  navigate: (route: PageRoute) => void;
}

const Roadmap: React.FC<RoadmapProps> = ({ navigate }) => {
  return (
    <div className="bg-bg-50 py-16">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold text-text-primary mb-6">我们的愿景与路线图</h1>
          <p className="text-xl text-text-secondary">打造跨境电商 AI 操作系统，让每一个独立站都能享受 AI 红利。</p>
        </div>

        <div className="space-y-12 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-brand-200 before:to-transparent">
          
          {/* Phase 1 */}
          <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
            <div className="flex items-center justify-center w-10 h-10 rounded-full border border-white bg-brand-600 text-white shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
              <Flag className="w-5 h-5" />
            </div>
            <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-white p-6 rounded-2xl shadow-sm border border-bg-200">
              <div className="flex justify-between items-center mb-2">
                 <span className="font-bold text-brand-600 text-sm">Phase 1: 基础设施</span>
                 <span className="text-xs font-mono text-bg-300">已完成</span>
              </div>
              <h3 className="font-bold text-lg mb-2">智能交互层</h3>
              <p className="text-text-secondary text-sm">构建AI客服与坐席工作台，解决最基础的沟通效率问题，沉淀对话数据。</p>
            </div>
          </div>

          {/* Phase 2 */}
          <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group">
            <div className="flex items-center justify-center w-10 h-10 rounded-full border border-white bg-brand-400 text-white shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
              <span className="font-bold text-sm">02</span>
            </div>
             <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-white p-6 rounded-2xl shadow-sm border border-bg-200">
              <div className="flex justify-between items-center mb-2">
                 <span className="font-bold text-amber-600 text-sm">Phase 2: 增长引擎</span>
                 <span className="text-xs font-mono text-amber-600 bg-amber-50 px-2 py-0.5 rounded">进行中</span>
              </div>
              <h3 className="font-bold text-lg mb-2">数据洞察与营销层</h3>
              <p className="text-text-secondary text-sm">上线AI分析助手与内容生成器，将对话数据转化为营销策略，主动出击获取流量。</p>
            </div>
          </div>

          {/* Phase 3 */}
          <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group">
            <div className="flex items-center justify-center w-10 h-10 rounded-full border border-white bg-bg-200 text-text-muted shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
               <span className="font-bold text-sm">03</span>
            </div>
             <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-white p-6 rounded-2xl shadow-sm border border-bg-200 opacity-75">
              <div className="flex justify-between items-center mb-2">
                 <span className="font-bold text-text-muted text-sm">Phase 3: 商业闭环</span>
                 <span className="text-xs font-mono text-text-muted">2026 Q1</span>
              </div>
              <h3 className="font-bold text-lg mb-2">全链路生态层</h3>
              <p className="text-text-secondary text-sm">打通供应链、风控与个性化推荐，形成完全自动化的商业闭环系统。</p>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default Roadmap;