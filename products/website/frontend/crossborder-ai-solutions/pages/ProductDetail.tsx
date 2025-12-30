import React from 'react';
import { PageRoute } from '../App';
import Button from '../components/ui/Button';
import { 
  Check, ArrowLeft, Bot, Layout, Zap, Send, Sparkles, 
  ClipboardList, BookOpen, BarChart3, Search, Headphones,
  Box, MapPin, MoreHorizontal, MessageSquare, Activity,
  Layers, ChevronRight, Circle, TrendingUp, Globe
} from 'lucide-react';
import { motion } from 'framer-motion';

interface ProductDetailProps {
  id: string;
  navigate: (route: PageRoute) => void;
}

// 演示组件 1: 极致精美的移动端 AI 机器人 (优化排版与遮挡)
const AdvancedChatbotDemo = () => (
  <div className="w-full h-full flex items-center justify-center p-8 bg-gradient-to-br from-slate-50 to-indigo-50/50 relative overflow-hidden">
    {/* 灵动的背景装饰光晕 */}
    <div className="absolute -top-24 -right-24 w-64 h-64 bg-brand-500/10 blur-[100px] rounded-full"></div>
    <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-indigo-500/10 blur-[100px] rounded-full"></div>
    
    <div className="relative flex items-center justify-center w-full h-full max-w-lg">
      {/* 手机外壳：优化比例，增加高精度细节 */}
      <motion.div 
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 100 }}
        className="w-[220px] h-[460px] bg-[#0F1115] rounded-[3.2rem] border-[7px] border-[#1A1C22] shadow-[0_40px_100px_rgba(0,0,0,0.25)] relative overflow-hidden flex flex-col font-sans z-20"
      >
        {/* 顶部听筒区域 */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-20 h-5 bg-[#1A1C22] rounded-b-2xl z-30 flex items-center justify-center">
          <div className="w-6 h-1 bg-white/5 rounded-full"></div>
        </div>
        
        {/* 内部界面：毛玻璃导航 */}
        <div className="bg-white/90 backdrop-blur-xl pt-10 pb-3 px-4 border-b border-slate-100 flex items-center gap-2">
          <div className="w-7 h-7 bg-brand-600 rounded-lg flex items-center justify-center text-white shadow-lg shadow-brand-600/20">
            <Bot size={14} />
          </div>
          <div className="flex-grow">
            <div className="text-[9px] font-black text-slate-900 leading-none mb-1 tracking-tight">AI ASSISTANT</div>
            <div className="flex items-center gap-1">
              <span className="w-1 h-1 bg-success rounded-full animate-pulse"></span>
              <span className="text-[7px] font-black text-success uppercase tracking-widest">Active</span>
            </div>
          </div>
        </div>

        {/* 气泡对话区：优化间距，解决拥挤 */}
        <div className="flex-grow p-4 space-y-4 bg-[#F8FAFC] overflow-hidden">
          <motion.div 
            initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 }}
            className="flex justify-end"
          >
            <div className="bg-slate-900 text-white px-3 py-2.5 rounded-2xl rounded-tr-none text-[9px] font-medium max-w-[85%] shadow-sm leading-relaxed">
              Order #SH-2025? 👗
            </div>
          </motion.div>
          
          <div className="flex gap-2">
            <div className="w-6 h-6 bg-brand-50 rounded-lg flex items-center justify-center text-brand-600 shrink-0 border border-brand-100"><Bot size={12} /></div>
            <div className="space-y-3 flex-grow">
              <motion.div 
                initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.8 }}
                className="bg-white p-3 rounded-2xl rounded-tl-none text-[9px] text-slate-600 shadow-sm border border-slate-100 leading-snug"
              >
                Syncing with <span className="text-brand-600 font-bold">Shopify</span>...
              </motion.div>
              
              <motion.div 
                initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 1.2 }}
                className="bg-white rounded-xl overflow-hidden border border-slate-100 shadow-md"
              >
                <div className="px-3 py-2 bg-slate-50 border-b border-slate-100 flex justify-between items-center">
                  <span className="text-[7px] font-black text-slate-400">IN TRANSIT</span>
                  <Box size={10} className="text-brand-600" />
                </div>
                <div className="p-3">
                  <div className="h-1 w-full bg-slate-100 rounded-full mb-2 relative">
                    <motion.div initial={{ width: 0 }} animate={{ width: '70%' }} transition={{ duration: 1.5, delay: 1.4 }} className="h-full bg-brand-600 rounded-full" />
                  </div>
                  <div className="text-[8px] font-bold text-slate-800">NYC Hub Arrival</div>
                </div>
              </motion.div>
            </div>
          </div>
        </div>
        
        {/* 输入栏 */}
        <div className="p-3 bg-white border-t border-slate-50 flex items-center gap-2">
          <div className="flex-grow bg-slate-50 rounded-lg px-3 h-9 flex items-center text-[8px] text-slate-400">Ask follow-up...</div>
          <div className="w-9 h-9 bg-slate-900 rounded-xl flex items-center justify-center text-white"><Send size={14} /></div>
        </div>
      </motion.div>

      {/* 悬浮交互卡片：打破边框限制，提升视觉丰富度 */}
      <motion.div 
        initial={{ opacity: 0, x: 50 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 1.6, type: 'spring' }}
        className="absolute right-0 top-[15%] z-30 bg-white/95 backdrop-blur-xl p-4 rounded-2xl border border-brand-100 shadow-[0_20px_50px_rgba(79,70,229,0.15)] hidden lg:block w-44"
      >
        <div className="flex items-center gap-2 mb-3">
           <div className="p-1.5 bg-brand-50 text-brand-600 rounded-lg"><Sparkles size={14}/></div>
           <span className="text-[10px] font-black text-slate-800 uppercase tracking-tighter">AI Analysis</span>
        </div>
        <div className="space-y-2">
           <div className="flex justify-between text-[9px] font-bold">
              <span className="text-slate-400">Confidence</span>
              <span className="text-brand-600">99.8%</span>
           </div>
           <div className="h-1 w-full bg-slate-100 rounded-full overflow-hidden">
              <motion.div initial={{ width: 0 }} animate={{ width: '99.8%' }} transition={{ duration: 1, delay: 2 }} className="h-full bg-brand-500" />
           </div>
           <p className="text-[8px] text-slate-500 italic">User intent: Order Tracking</p>
        </div>
      </motion.div>

      <motion.div 
        initial={{ opacity: 0, x: -50 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 1.8, type: 'spring' }}
        className="absolute left-0 bottom-[20%] z-30 bg-slate-900 p-4 rounded-2xl shadow-2xl hidden lg:block w-48"
      >
        <div className="flex items-center gap-2 mb-2">
           <Globe size={12} className="text-brand-400" />
           <span className="text-[8px] font-black text-brand-400 uppercase tracking-widest">Real-time Translation</span>
        </div>
        <div className="text-[10px] text-slate-300 font-medium leading-relaxed">
           "Donde esta mi pedido?"<br/>
           <span className="text-white">→ "Where is my order?"</span>
        </div>
      </motion.div>
    </div>
  </div>
);

// 演示组件 2: 坐席工作台 (优化空间利用与层级感)
const AdvancedWorkbenchDemo = () => (
  <div className="w-full h-full bg-[#0F1115] p-6 flex items-center justify-center">
    <motion.div 
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className="w-full h-full bg-white rounded-2xl shadow-[0_50px_100px_rgba(0,0,0,0.4)] overflow-hidden flex flex-col font-sans"
    >
      {/* 顶部控制栏：模拟浏览器/OS感 */}
      <div className="h-11 bg-slate-50 border-b border-slate-100 flex items-center px-4 justify-between shrink-0">
        <div className="flex gap-1.5">
           <div className="w-2.5 h-2.5 rounded-full bg-slate-200"></div>
           <div className="w-2.5 h-2.5 rounded-full bg-slate-200"></div>
           <div className="w-2.5 h-2.5 rounded-full bg-slate-200"></div>
        </div>
        <div className="px-3 py-1 bg-brand-50 text-brand-600 rounded-full text-[8px] font-black tracking-widest uppercase border border-brand-100">Agent OS v2.0</div>
      </div>

      <div className="flex flex-grow overflow-hidden">
        {/* 精简侧边栏 */}
        <div className="w-14 bg-slate-900 flex flex-col items-center py-6 gap-6 shrink-0 border-r border-white/5">
          <div className="w-8 h-8 bg-brand-600 rounded-xl flex items-center justify-center text-white"><Activity size={16} /></div>
          <div className="w-8 h-8 rounded-xl flex items-center justify-center text-slate-500 hover:text-white transition-colors cursor-pointer"><MessageSquare size={16} /></div>
          <div className="w-8 h-8 rounded-xl flex items-center justify-center text-slate-500 hover:text-white transition-colors cursor-pointer mt-auto mb-4"><TrendingUp size={16} /></div>
        </div>

        {/* 聊天列表：优化间距，显得更透气 */}
        <div className="w-48 border-r border-slate-50 p-5 space-y-4 hidden lg:block bg-slate-50/50">
           <div className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Ongoing (4)</div>
           <motion.div 
             initial={{ x: -10, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: 0.5 }}
             className="p-4 bg-white rounded-xl border border-brand-200 shadow-sm shadow-brand-500/5 ring-1 ring-brand-50"
           >
              <div className="text-[10px] font-black text-slate-900 mb-1">#SH-2025 Returns</div>
              <div className="text-[8px] text-slate-400 font-medium truncate italic">"Wait for refund status..."</div>
           </motion.div>
           {[1, 2].map(i => (
             <div key={i} className="p-4 bg-white/40 rounded-xl border border-slate-100 opacity-40">
                <div className="text-[10px] font-bold text-slate-300">#SH-202{i+1} Payment</div>
             </div>
           ))}
        </div>

        {/* 核心对话空间 */}
        <div className="flex-grow flex flex-col bg-white">
          <div className="p-8 flex-grow space-y-6 overflow-hidden">
             <div className="flex gap-4">
                <div className="w-9 h-9 rounded-full overflow-hidden shrink-0 border border-slate-100"><img src="https://picsum.photos/100/100?random=5" className="w-full h-full object-cover" /></div>
                <div className="bg-slate-50 p-5 rounded-2xl rounded-tl-none text-[11px] text-slate-600 max-w-[75%] border border-slate-100 leading-relaxed font-medium">
                   Hi! I returned the product last week. When can I get my money back? 
                </div>
             </div>
             
             {/* AI Copilot 实时建议：聚焦化排版 */}
             <motion.div 
               initial={{ opacity: 0, y: 20 }}
               animate={{ opacity: 1, y: 0 }}
               transition={{ delay: 1, type: 'spring' }}
               className="ml-12"
             >
                <div className="bg-white rounded-2xl p-6 border border-brand-100 shadow-2xl shadow-brand-900/10 relative overflow-hidden group">
                  <div className="absolute top-0 right-0 p-3"><Sparkles size={14} className="text-brand-200 group-hover:text-brand-500 transition-colors" /></div>
                  <div className="flex items-center gap-2 mb-4">
                     <div className="px-2 py-1 bg-brand-600 text-white rounded text-[8px] font-black uppercase tracking-widest">Smart Reply</div>
                  </div>
                  <p className="text-[11px] font-bold text-slate-800 leading-relaxed mb-6">
                    "Package received at NYC warehouse on Jan 18. Refund is processing (estimated 3 days). Send status update?"
                  </p>
                  <div className="flex gap-3">
                     <button className="px-4 py-2 bg-brand-600 text-white rounded-lg text-[10px] font-black shadow-lg shadow-brand-600/20 hover:scale-105 transition-transform">Apply & Send</button>
                     <button className="px-4 py-2 bg-slate-50 text-slate-500 rounded-lg text-[10px] font-black hover:bg-slate-100 transition-colors">Edit Draft</button>
                  </div>
                </div>
             </motion.div>
          </div>
          
          {/* 底部回复框 */}
          <div className="p-6 bg-slate-50/50 border-t border-slate-100">
             <div className="bg-white border border-slate-200 rounded-2xl p-4 flex items-center gap-4 shadow-sm focus-within:ring-2 focus-within:ring-brand-500/10 focus-within:border-brand-300 transition-all">
                <div className="flex-grow text-[11px] text-slate-400 font-medium italic">Type your message to customer...</div>
                <div className="flex items-center gap-3">
                   <div className="p-2 text-slate-300 hover:text-brand-500 cursor-pointer transition-colors"><Circle size={14} /></div>
                   <div className="w-10 h-10 bg-slate-900 rounded-xl flex items-center justify-center text-white shadow-xl hover:bg-slate-800 transition-colors"><Send size={18} /></div>
                </div>
             </div>
          </div>
        </div>
      </div>
    </motion.div>
  </div>
);

const productData: Record<string, any> = {
  'ai-chatbot': {
    title: 'AI智能客服',
    tagline: '售前咨询与售后订单全自动化处理',
    desc: '深度集成独立站 API。不仅是 24/7 的售前引导员，更是能直接查订单、查物流、处理自助退换货申请的售后专家。',
    icon: <Bot />,
    metrics: [
      { label: '订单自动处理率', value: '92%' },
      { label: '物流同步时效', value: '秒级' },
      { label: '多语言覆盖', value: '50+' }
    ],
    highlights: [
      { title: "全链路售前售后支持", desc: "自动识别客户意图，无论是产品咨询还是退款状态查询，AI 都能精准回复并执行操作。" },
      { title: "物流轨迹实时可视化", desc: "深度集成 17Track 等主流物流商，在对话框内直接展示包裹实时运输动态与地图轨迹。" },
      { title: "Shopify 及多平台深度同步", desc: "一键同步订单数据，支持客户自助修改地址、核对商品详情及查询退款进度。" }
    ],
    preview: <AdvancedChatbotDemo />
  },
  'agent-workbench': {
    title: '坐席工作台',
    tagline: '专业级人机协作与全流程监管平台',
    desc: '跨境客服数字化的核心中枢。统一聚合全渠道咨询，集成专业工单系统、智能知识库，实现服务全过程的质量监管。',
    icon: <Layout />,
    metrics: [
      { label: '坐席人效提升', value: '300%' },
      { label: '复杂问题耗时', value: '-60%' },
      { label: '平均满意度', value: '98.5%' }
    ],
    highlights: [
      { title: "人工一键接入与渠道聚合", desc: "统一管理来自 WhatsApp, Email, Facebook 等渠道的咨询。支持在必要时一键接管 AI 对话。" },
      { title: "全流程工单流转系统", desc: "复杂售后问题一键转工单，支持多级流转、跨部门协同处理，状态实时反馈给终端客户。" },
      { title: "智能知识库与服务监管", desc: "AI 实时匹配回复建议。全方位监控坐席效率、响应时长及 CSAT 满意度指标，确保服务质量。" }
    ],
    preview: <AdvancedWorkbenchDemo />
  }
};

const ProductDetail: React.FC<ProductDetailProps> = ({ id, navigate }) => {
  const data = productData[id] || productData['ai-chatbot'];

  return (
    <div className="min-h-screen bg-white text-text-primary">
      <section className="pt-32 pb-24 bg-bg-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <button 
            onClick={() => navigate({ type: 'home' })} 
            className="flex items-center gap-2 mb-12 font-black text-[10px] text-text-muted hover:text-brand-600 transition-all uppercase tracking-widest"
          >
            <ArrowLeft size={14} /> 返回首页
          </button>
          
          <div className="flex flex-col lg:flex-row gap-20 items-center">
            <div className="flex-1 text-center lg:text-left">
              <h1 className="text-5xl lg:text-7xl font-black mb-8 tracking-tighter leading-none">
                {data.title}
              </h1>
              <p className="text-xl font-bold mb-10 text-brand-600">
                {data.tagline}
              </p>
              <div className="grid grid-cols-3 gap-8 mb-12">
                 {data.metrics.map((m: any, i: number) => (
                   <div key={i}>
                      <div className="text-3xl font-black text-text-primary">{m.value}</div>
                      <div className="text-[10px] uppercase font-black tracking-widest text-text-muted mt-1">{m.label}</div>
                   </div>
                 ))}
              </div>
              <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
                <Button size="lg" className="h-16 px-12 font-black shadow-xl shadow-brand-600/20" onClick={() => navigate({ type: 'pricing' })}>立即开始试用</Button>
                <Button size="lg" variant="secondary" className="h-16 px-12 font-bold bg-white border-bg-200" onClick={() => navigate({ type: 'pricing' })}>查看价格方案</Button>
              </div>
            </div>
            
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
              className="flex-1 w-full relative"
            >
              <div className="absolute inset-0 bg-brand-600/10 blur-[120px] rounded-full scale-75 opacity-30"></div>
              {/* 优化比例容器：使用 aspect-[4/3] 配合 overflow-visible 让悬浮组件能超出边界 */}
              <div className="relative z-10 w-full aspect-[4/3] rounded-[2.5rem] md:rounded-[3.5rem] border border-slate-200 shadow-2xl overflow-hidden group">
                {data.preview}
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      <section className="py-24 border-b border-bg-100">
        <div className="max-w-7xl mx-auto px-4">
           <h2 className="text-3xl font-black mb-20 text-center tracking-tight uppercase">产品核心能力</h2>
           <div className="grid md:grid-cols-3 gap-16">
              {data.highlights.map((h: any, i: number) => (
                <div key={i} className="group flex flex-col items-center lg:items-start text-center lg:text-left">
                   <div className="w-14 h-14 bg-brand-600 text-white rounded-[1.25rem] flex items-center justify-center mb-8 shadow-xl shadow-brand-600/20 group-hover:scale-110 transition-transform">
                      <Check size={28} />
                   </div>
                   <h3 className="text-xl font-bold mb-4">{h.title}</h3>
                   <p className="text-sm leading-relaxed text-text-secondary">{h.desc}</p>
                </div>
              ))}
           </div>
        </div>
      </section>

      <section className="py-32 bg-bg-50">
         <div className="max-w-5xl mx-auto px-4 text-center">
            <h2 className="text-4xl font-black mb-16 tracking-tight">立即开启 AI 驱动的业务增长之旅</h2>
            <div className="mt-10">
               <Button size="lg" className="h-20 px-20 text-xl font-black shadow-2xl shadow-brand-600/30" onClick={() => navigate({ type: 'pricing' })}>立即开启免费试用</Button>
            </div>
         </div>
      </section>
    </div>
  );
};

export default ProductDetail;