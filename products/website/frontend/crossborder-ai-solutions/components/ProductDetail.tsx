import React from 'react';
import { PageRoute } from '../App';
import Button from '../components/ui/Button';
import { Check, ArrowLeft, Bot, Layout, BarChart, PenTool } from 'lucide-react';

interface ProductDetailProps {
  id: string;
  navigate: (route: PageRoute) => void;
}

// Mock Data for Prototype
const productData: Record<string, any> = {
  'ai-customer-service': {
    title: 'AI智能客服',
    subtitle: '降低60%客服成本，24/7多语言智能响应',
    icon: <Bot className="w-12 h-12" />,
    features: [
      { title: '智能对话引擎', desc: '基于GPT-4技术，理解上下文，处理复杂咨询。' },
      { title: '多语言自动切换', desc: '识别客户语言并自动切换，消除沟通障碍。' },
      { title: '意图识别转人工', desc: '精准识别销售线索或愤怒情绪，平滑转接。' }
    ],
    // Updated metrics for realism
    stats: ['60% 成本降低', '毫秒级 响应', '24/7 全天候']
  },
  'workbench': {
    title: '客服坐席工作台',
    subtitle: '人机协同更高效，统一管理所有渠道对话',
    icon: <Layout className="w-12 h-12" />,
    features: [
      { title: '全渠道聚合', desc: 'WhatsApp, Email, LiveChat 统一界面管理。' },
      { title: 'AI 辅助回复', desc: 'AI 实时建议回复话术，点击即可发送。' },
      { title: '客户画像侧边栏', desc: '对话时实时展示客户订单、历史行为数据。' }
    ],
    stats: ['3倍 效率提升', '100% 数据留存', '统一 管理视图']
  }
  // Add others or fallback
};

const ProductDetail: React.FC<ProductDetailProps> = ({ id, navigate }) => {
  const data = productData[id] || productData['ai-customer-service']; // Fallback

  return (
    <div className="bg-white">
      {/* Product Hero */}
      <section className="bg-bg-50 pt-16 pb-24 border-b border-bg-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <button onClick={() => navigate({ type: 'home' })} className="flex items-center text-text-muted hover:text-brand-600 mb-8 transition-colors">
            <ArrowLeft className="w-4 h-4 mr-2" /> 返回首页
          </button>
          
          <div className="flex flex-col md:flex-row items-center gap-12">
            <div className="flex-1">
              <div className="bg-brand-100 p-4 rounded-2xl w-fit text-brand-600 mb-6">{data.icon}</div>
              <h1 className="text-4xl md:text-5xl font-bold text-text-primary mb-6">{data.title}</h1>
              <p className="text-xl text-text-secondary mb-8">{data.subtitle}</p>
              <div className="flex gap-4">
                <Button size="lg">立即试用</Button>
                <Button size="lg" variant="outline">预约演示</Button>
              </div>
            </div>
            {/* Abstract Visual Placeholder */}
            <div className="flex-1 h-[400px] w-full bg-gradient-to-br from-bg-100 to-bg-200 rounded-3xl border border-bg-200 flex items-center justify-center relative overflow-hidden">
               <div className="absolute inset-0 bg-grid-slate-200 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))]"></div>
               <span className="text-text-muted font-mono text-sm relative z-10">Product UI Placeholder for {data.title}</span>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">核心功能亮点</h2>
            <p className="text-text-secondary">专为跨境电商场景深度定制</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {data.features.map((f: any, i: number) => (
              <div key={i} className="p-8 rounded-2xl border border-bg-200 hover:border-brand-200 hover:shadow-lg transition-all">
                <h3 className="text-xl font-bold mb-4">{f.title}</h3>
                <p className="text-text-secondary leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="py-16 bg-brand-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
           <div className="grid grid-cols-3 gap-8 text-center divide-x divide-white/20">
              {data.stats.map((s: string, i: number) => (
                <div key={i} className="font-bold text-2xl md:text-3xl">{s}</div>
              ))}
           </div>
        </div>
      </section>

      {/* Placeholder for "How it works" */}
      <section className="py-24 bg-bg-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
           <h2 className="text-3xl font-bold mb-12">工作流程</h2>
           <div className="h-64 border-2 border-dashed border-bg-200 rounded-3xl flex items-center justify-center">
              <span className="text-text-muted">Workflow Diagram Placeholder</span>
           </div>
        </div>
      </section>
    </div>
  );
};

export default ProductDetail;