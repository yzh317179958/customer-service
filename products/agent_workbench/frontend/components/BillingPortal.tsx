
import React, { useState } from 'react';
import { 
  CreditCard, Zap, ShieldCheck, Download, Sparkles, TrendingUp, 
  Users, Check, ArrowRight, UserPlus, Bot, BarChart3, 
  PenTool, ShoppingCart, Layout, MessageSquare, PlusCircle,
  HelpCircle, Settings2, Rocket, History, Globe, ShieldAlert
} from 'lucide-react';

const BillingPortal: React.FC = () => {
  const [activePlan, setActivePlan] = useState('pro');

  // 核心组合产品（已上线）
  const coreBundles = [
    { 
      id: 'basic', 
      name: '创业版 (Starter)', 
      price: '2,388', 
      desc: '适合初创独立站，解决基础接待。',
      features: ['2个标准坐席', '基础 AI 对话引擎', '全渠道消息集成', '标准工单系统']
    },
    { 
      id: 'pro', 
      name: '数字化坐席版 (Growth)', 
      price: '5,999', 
      isPopular: true,
      desc: '深度 AI 介入，全面替代重复性人工。',
      features: ['5个标准坐席', 'Gemini Pro 级对话能力', '中英母语级逻辑注入', '智能工单流转系统', '7*24h 全自动化值班']
    },
    { 
      id: 'enterprise', 
      name: '旗舰全托管版 (Scale)', 
      price: '12,800', 
      desc: '品牌化定制，深度嵌入业务流程。',
      features: ['10个标准坐席', '专属私有化模型调优', 'ERP/Shopify API 深度联动', '高级数据看板定制', '专家 1对1 实施服务']
    },
  ];

  // 增值方案货架（蓝图/待开发）
  const addonSolutions = [
    {
      id: 'analytics',
      name: 'AI 数据洞察助手',
      status: 'pre_order', // 预购
      icon: BarChart3,
      desc: '从海量对话中提取用户痛点，自动生成爆款策略与周报。',
      customLevel: '深度业务定制',
      price: '¥1,999/年'
    },
    {
      id: 'marketing',
      name: 'AI 跨境营销生成器',
      status: 'planned', // 规划中
      icon: PenTool,
      desc: '根据品牌调性，自动生成符合海外审美的商品详情与社交媒体推文。',
      customLevel: '品牌语料定制',
      price: '预约定制'
    },
    {
      id: 'logistics',
      name: '物流预警与异常监控',
      status: 'active', // 已集成在核心包或可单独买
      icon: Globe,
      desc: '主动追踪全球包裹状态，异常时 AI 自动联系客户安抚，降低纠纷。',
      customLevel: '物流接口对接',
      price: '包含在专业版/旗舰版中'
    },
    {
      id: 'recommend',
      name: '智能商品推荐引擎',
      status: 'planned',
      icon: ShoppingCart,
      desc: '对话中实时分析用户意图，精准推荐关联 SKU，提升客单价。',
      customLevel: 'SKU 逻辑训练',
      price: '预约定制'
    }
  ];

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 font-sans p-6 lg:p-10 animate-in fade-in duration-700">
      <div className="max-w-7xl mx-auto space-y-10">
        
        {/* Portal Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
           <div>
              <div className="flex items-center gap-3 mb-2">
                 <div className="w-8 h-8 bg-fiido rounded-lg flex items-center justify-center text-white shadow-lg">
                    <CreditCard size={18}/>
                 </div>
                 <h1 className="text-2xl font-black tracking-tight text-slate-900">Fiido 平台订阅与方案中心</h1>
              </div>
              <p className="text-slate-400 text-sm font-medium">管理您的数字化资产、AI 算力以及业务定制方案</p>
           </div>
           <div className="flex gap-3">
              <button className="px-5 py-2.5 bg-white border border-slate-200 rounded-xl text-xs font-black text-slate-600 hover:bg-slate-50 transition-all flex items-center gap-2">
                 <History size={16}/> 消费明细
              </button>
              <button className="px-5 py-2.5 bg-fiido text-white rounded-xl text-xs font-black hover:opacity-90 transition-all shadow-lg shadow-fiido/20 flex items-center gap-2">
                 <Rocket size={16}/> 极速扩容
              </button>
           </div>
        </div>

        {/* ROI & Status Dashboard */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
           <div className="lg:col-span-2 bg-slate-900 rounded-[32px] p-8 text-white relative overflow-hidden shadow-2xl">
              <div className="absolute right-0 top-0 p-10 opacity-5 pointer-events-none">
                 <Sparkles size={180}/>
              </div>
              <div className="relative z-10 flex flex-col md:flex-row justify-between gap-8 h-full">
                 <div className="space-y-6">
                    <div className="inline-flex items-center gap-2 px-3 py-1 bg-fiido/20 text-fiido rounded-full text-[10px] font-black uppercase tracking-widest border border-fiido/30">
                       <TrendingUp size={12}/> 实时效能分析
                    </div>
                    <h2 className="text-3xl font-bold leading-tight">本月 AI 已为您节省约 <span className="text-fiido text-4xl font-brand font-black">¥4,800</span></h2>
                    <p className="text-slate-400 text-sm max-w-md">基于当前会话量，AI 客服已自动完成了 78% 的重复咨询，相当于 1.1 个全职人力成本。</p>
                    <div className="pt-4">
                       <button className="text-[11px] font-black text-fiido hover:underline flex items-center gap-1 uppercase tracking-widest">
                          查看详细投资回报率报告 <ArrowRight size={14}/>
                       </button>
                    </div>
                 </div>
                 <div className="w-full md:w-64 bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm space-y-4">
                    <div className="flex justify-between items-center text-[10px] font-black text-slate-500 uppercase tracking-widest">
                       当前算力余量
                       <Zap size={14} className="text-fiido"/>
                    </div>
                    <div className="space-y-2">
                       <div className="flex justify-between items-end">
                          <span className="text-xl font-brand font-black">7,420</span>
                          <span className="text-[10px] text-slate-500 font-bold mb-1">/ 10,000 点</span>
                       </div>
                       <div className="w-full bg-white/10 h-2 rounded-full overflow-hidden">
                          <div className="bg-fiido h-full w-[74%] shadow-[0_0_12px_#00a6a0]"></div>
                       </div>
                    </div>
                    <div className="pt-2 flex justify-between items-center text-[10px] font-bold text-slate-400">
                       <span>重置日期: 04-20</span>
                       <button className="text-fiido">自动续费: ON</button>
                    </div>
                 </div>
              </div>
           </div>
           
           <div className="bg-white border border-slate-200 rounded-[32px] p-8 shadow-sm flex flex-col justify-between">
              <div>
                <h3 className="text-sm font-black text-slate-800 uppercase tracking-widest mb-4">当前订阅</h3>
                <div className="flex items-baseline gap-2 mb-2">
                   <span className="text-3xl font-brand font-black text-slate-900">专业版</span>
                   <span className="text-xs font-bold text-slate-400">Annual</span>
                </div>
                <p className="text-xs text-slate-500 font-medium">到期时间：2026年3月22日</p>
              </div>
              <div className="space-y-3 mt-8">
                 <div className="flex items-center gap-2 text-[11px] font-bold text-slate-600">
                    <Check size={14} className="text-emerald-500"/> 已激活 5 个坐席
                 </div>
                 <div className="flex items-center gap-2 text-[11px] font-bold text-slate-600">
                    <Check size={14} className="text-emerald-500"/> 物流通知方案已上线
                 </div>
                 <button className="w-full mt-4 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-[11px] font-black uppercase tracking-widest transition-all">
                    管理订阅
                 </button>
              </div>
           </div>
        </div>

        {/* Solution Shelf: The Core Pricing */}
        <div className="space-y-8">
           <div className="text-center space-y-2">
              <h3 className="text-2xl font-black text-slate-900">选择您的数字化底座</h3>
              <p className="text-slate-400 text-sm font-medium">核心产品已深度集成，选择最适合您当前规模的方案</p>
           </div>
           
           <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {coreBundles.map((plan) => (
                <div 
                  key={plan.id}
                  onClick={() => setActivePlan(plan.id)}
                  className={`bg-white rounded-[40px] p-8 border-2 transition-all cursor-pointer relative flex flex-col ${
                    activePlan === plan.id 
                    ? 'border-fiido shadow-2xl scale-[1.02]' 
                    : 'border-transparent shadow-sm hover:border-slate-200'
                  }`}
                >
                   {plan.isPopular && (
                     <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1.5 bg-fiido text-white rounded-full text-[10px] font-black uppercase tracking-widest shadow-lg">
                        最有价值方案
                     </div>
                   )}
                   
                   <h4 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-6">{plan.name}</h4>
                   
                   <div className="flex items-baseline gap-1 mb-4">
                      <span className="text-sm font-black text-slate-400">¥</span>
                      <span className="text-5xl font-brand font-black text-slate-900 tracking-tighter">{plan.price}</span>
                      <span className="text-xs font-bold text-slate-400 ml-1">/ 年</span>
                   </div>
                   
                   <p className="text-xs text-slate-500 mb-8 font-medium">{plan.desc}</p>
                   
                   <div className="space-y-4 mb-10 flex-1">
                      {plan.features.map((feat, i) => (
                        <div key={i} className="flex items-center gap-3 text-[12px] font-bold text-slate-700">
                           <div className="w-1.5 h-1.5 bg-fiido rounded-full"></div>
                           {feat}
                        </div>
                      ))}
                   </div>
                   
                   <button className={`w-full py-4 rounded-2xl text-[12px] font-black uppercase tracking-widest transition-all ${
                     activePlan === plan.id 
                     ? 'bg-fiido text-white shadow-lg shadow-fiido/20' 
                     : 'bg-slate-50 text-slate-500 hover:bg-slate-100'
                   }`}>
                     {activePlan === plan.id ? '当前选择' : '立即升级'}
                   </button>
                </div>
              ))}
           </div>
        </div>

        {/* The Add-on Shelf: Functional Expansion */}
        <div className="space-y-8 pt-10">
           <div className="flex justify-between items-end">
              <div>
                 <h3 className="text-xl font-black text-slate-900 uppercase tracking-tight">AI 业务增强方案货架</h3>
                 <p className="text-slate-400 text-sm font-medium mt-1">根据您的业务逻辑量身定制，点击开启专家实施</p>
              </div>
              <div className="flex items-center gap-2 text-fiido text-[10px] font-black uppercase tracking-widest bg-fiido/5 px-3 py-1.5 rounded-full">
                 <ShieldCheck size={14}/> 100% 专家人工调优确保落地
              </div>
           </div>
           
           <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {addonSolutions.map((item) => (
                <div 
                  key={item.id}
                  className="bg-white rounded-[32px] p-6 border border-slate-100 shadow-sm hover:shadow-xl transition-all group flex flex-col"
                >
                   <div className="flex justify-between items-start mb-6">
                      <div className="p-3.5 bg-slate-50 rounded-2xl text-slate-400 group-hover:bg-fiido group-hover:text-white transition-all shadow-inner">
                         <item.icon size={22}/>
                      </div>
                      <span className={`px-2 py-1 rounded-lg text-[8px] font-black uppercase tracking-widest ${
                        item.status === 'active' ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-100 text-slate-400'
                      }`}>
                        {item.status === 'active' ? '已激活' : item.status === 'pre_order' ? '可预约' : '规划中'}
                      </span>
                   </div>
                   
                   <h4 className="text-[15px] font-bold text-slate-800 mb-2">{item.name}</h4>
                   <p className="text-[11px] text-slate-400 leading-relaxed font-medium mb-4">{item.desc}</p>
                   
                   <div className="mt-auto space-y-4">
                      <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                         <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">实施程度</p>
                         <p className="text-[11px] font-bold text-slate-700">{item.customLevel}</p>
                      </div>
                      <div className="text-[10px] font-black text-fiido uppercase tracking-widest text-center">{item.price}</div>
                      <button 
                        disabled={item.status === 'planned'}
                        className={`w-full py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
                          item.status === 'active' 
                          ? 'border border-emerald-200 text-emerald-600' 
                          : item.status === 'pre_order'
                          ? 'bg-fiido-black text-white hover:opacity-90'
                          : 'bg-slate-50 text-slate-300 cursor-not-allowed'
                        }`}
                      >
                        {item.status === 'active' ? '管理方案' : item.status === 'pre_order' ? '开启专家定制' : '即将上线'}
                      </button>
                   </div>
                </div>
              ))}
           </div>
        </div>

        {/* Footer Info */}
        <div className="bg-white rounded-[40px] p-10 border border-slate-200 shadow-sm flex flex-col md:flex-row items-center gap-10">
           <div className="w-20 h-20 bg-fiido-light rounded-[32px] flex items-center justify-center text-fiido shrink-0">
              <HelpCircle size={40}/>
           </div>
           <div className="flex-1 space-y-2">
              <h4 className="text-lg font-black text-slate-800">需要更深度的定制化业务集成？</h4>
              <p className="text-sm text-slate-400 font-medium leading-relaxed max-w-2xl">
                 Fiido 的 AI 工程师团队支持深度对接您的 ERP 系统、物流 API 以及私有知识库。
                 我们可以为您单独训练符合品牌调性的回复逻辑。
              </p>
           </div>
           <button className="px-10 py-5 bg-fiido-black text-white rounded-[24px] text-[13px] font-black uppercase tracking-widest hover:bg-slate-800 transition-all shadow-xl shrink-0">
              联系专家支持
           </button>
        </div>

      </div>
    </div>
  );
};

export default BillingPortal;
