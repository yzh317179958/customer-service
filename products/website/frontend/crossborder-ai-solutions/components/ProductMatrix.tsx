import React from 'react';
import { Bot, Layout, ShoppingCart, MapPin, ClipboardList, BookOpen, BarChart3, Headphones, Sparkles, Search } from 'lucide-react';
import Button from './ui/Button';
import { PageRoute } from '../App';

interface ProductMatrixProps {
  onNavigate: (route: PageRoute) => void;
}

const ProductMatrix: React.FC<ProductMatrixProps> = ({ onNavigate }) => {
  return (
    <section className="py-24 bg-bg-50 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        <div className="text-center mb-20">
          <h2 className="text-4xl md:text-5xl font-black text-text-primary mb-6 tracking-tight">
            两款核心产品，解决跨境客服所有难题
          </h2>
          <p className="text-text-secondary text-lg max-w-2xl mx-auto font-medium">
            AI 自动处理重复业务与咨询，人工在专业平台进行精细化运营与监管。
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
          
          {/* 产品1: AI智能客服 */}
          <div className="flex flex-col">
            <div className="group bg-white rounded-[2.5rem] p-10 border border-bg-200 hover:border-brand-300 transition-all duration-500 shadow-sm hover:shadow-2xl flex flex-col h-full">
              <div className="w-16 h-16 bg-brand-600 rounded-2xl flex items-center justify-center text-white mb-8 shadow-xl">
                <Bot size={32} />
              </div>
              <h3 className="text-3xl font-black mb-4">AI智能客服</h3>
              <p className="text-text-secondary mb-8 text-lg leading-relaxed font-medium">
                覆盖售前咨询到售后处理的全链路。自动识别意图，直接调用业务 API 完成任务。
              </p>
              
              <div className="space-y-4 mb-10 flex-grow">
                <div className="flex items-center gap-3 text-sm font-bold text-text-primary">
                  <div className="w-6 h-6 rounded-full bg-brand-50 flex items-center justify-center text-brand-600"><Sparkles size={12}/></div>
                  售前产品推荐与多轮咨询自动引导
                </div>
                <div className="flex items-center gap-3 text-sm font-bold text-text-primary">
                  <div className="w-6 h-6 rounded-full bg-brand-50 flex items-center justify-center text-brand-600"><Search size={12}/></div>
                  Shopify 及多平台订单状态自助查询
                </div>
                <div className="flex items-center gap-3 text-sm font-bold text-text-primary">
                  <div className="w-6 h-6 rounded-full bg-brand-50 flex items-center justify-center text-brand-600"><MapPin size={12}/></div>
                  物流轨迹可视化呈现，实时同步运输动态
                </div>
                <div className="flex items-center gap-3 text-sm font-bold text-text-primary">
                  <div className="w-6 h-6 rounded-full bg-brand-50 flex items-center justify-center text-brand-600"><ShoppingCart size={12}/></div>
                  售后改签、自助退换货申请自动受理
                </div>
              </div>

              <Button variant="primary" withArrow className="w-full h-14" onClick={() => onNavigate({ type: 'product', id: 'ai-chatbot' })}>详细了解 AI智能客服</Button>
            </div>
          </div>

          {/* 产品2: 坐席工作台 */}
          <div className="flex flex-col">
            <div className="group bg-slate-950 rounded-[2.5rem] p-10 border border-slate-800 hover:border-brand-500/50 transition-all duration-500 shadow-xl flex flex-col h-full text-white">
              <div className="w-16 h-16 bg-white/10 backdrop-blur rounded-2xl border border-white/20 flex items-center justify-center text-brand-400 mb-8 shadow-xl">
                <Layout size={32} />
              </div>
              <h3 className="text-3xl font-black mb-4">坐席工作台</h3>
              <p className="text-slate-400 mb-8 text-lg leading-relaxed font-medium">
                专业级人机协作管理平台。聚合所有渠道消息，让复杂问题的处理变得标准化、数字化。
              </p>

              <div className="space-y-4 mb-10 flex-grow">
                <div className="flex items-center gap-3 text-sm font-bold text-slate-200">
                  <div className="w-6 h-6 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-brand-400"><Headphones size={12}/></div>
                  人工一键接管 AI 会话，处理核心售后争议
                </div>
                <div className="flex items-center gap-3 text-sm font-bold text-slate-200">
                  <div className="w-6 h-6 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-brand-400"><ClipboardList size={12}/></div>
                  全流程工单处理系统，支持多级流转与协同
                </div>
                <div className="flex items-center gap-3 text-sm font-bold text-slate-200">
                  <div className="w-6 h-6 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-brand-400"><BookOpen size={12}/></div>
                  智能知识库：实时建议回复话术与操作文档
                </div>
                <div className="flex items-center gap-3 text-sm font-bold text-slate-200">
                  <div className="w-6 h-6 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-brand-400"><BarChart3 size={12}/></div>
                  全程服务监管：满意度(CSAT)与人效实时看板
                </div>
              </div>

              <Button className="w-full h-14 bg-white text-slate-900 hover:bg-slate-200" withArrow onClick={() => onNavigate({ type: 'product', id: 'agent-workbench' })}>详细了解 工作台</Button>
            </div>
          </div>

        </div>

      </div>
    </section>
  );
};

export default ProductMatrix;