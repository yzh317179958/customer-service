import React from 'react';
import { PageRoute } from '../App';
import Button from '../components/ui/Button';
import { ArrowLeft, CheckCircle } from 'lucide-react';

interface SolutionDetailProps {
  id: string;
  navigate: (route: PageRoute) => void;
}

const SolutionDetail: React.FC<SolutionDetailProps> = ({ id, navigate }) => {
  const title = id === 'shopify' ? 'Shopify 专属解决方案' : '跨境电商独立站通用方案';

  return (
    <div className="bg-white">
      <section className="bg-brand-900 text-white pt-24 pb-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <button onClick={() => navigate({ type: 'home' })} className="absolute top-24 left-8 text-brand-200 hover:text-white flex items-center">
             <ArrowLeft className="w-4 h-4 mr-2" /> 返回
          </button>
          <span className="inline-block py-1 px-3 rounded-full bg-brand-800 text-brand-200 text-sm font-medium mb-6">解决方案</span>
          <h1 className="text-4xl md:text-6xl font-bold mb-8">{title}</h1>
          <p className="text-xl text-brand-100 max-w-3xl mx-auto mb-10">
            针对 {id} 生态深度优化，无缝集成您的现有工作流。无需懂代码，一键部署 AI 增长引擎。
          </p>
          <Button size="lg" className="bg-white text-brand-900 hover:bg-brand-50" onClick={() => navigate({ type: 'pricing' })}>查看价格方案</Button>
        </div>
      </section>
      
      <section className="py-24 max-w-4xl mx-auto px-4">
         <h2 className="text-3xl font-bold mb-8">方案优势</h2>
         <div className="space-y-6">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="flex gap-4 p-6 border border-bg-200 rounded-xl">
                 <CheckCircle className="w-6 h-6 text-brand-600 flex-shrink-0" />
                 <div>
                    <h3 className="font-bold text-lg mb-2">针对性优化点 {i}</h3>
                    <p className="text-text-secondary">详细描述该解决方案如何解决特定平台的痛点，例如数据同步、插件冲突、订单回写等具体技术细节。</p>
                 </div>
              </div>
            ))}
         </div>
      </section>
    </div>
  );
};

export default SolutionDetail;