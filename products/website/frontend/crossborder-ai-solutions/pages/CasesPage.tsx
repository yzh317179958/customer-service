import React from 'react';
import { PageRoute } from '../App';
import Button from '../components/ui/Button';
import { 
  TrendingUp, Users, Clock, Globe, Quote, 
  Bot, Layout, Send, Sparkles, MapPin, 
  Search, ShieldCheck, Activity, ChevronRight,
  Headphones, MessageSquare, MoreHorizontal,
  Circle, Zap, Box, ShoppingCart
} from 'lucide-react';
import { motion } from 'framer-motion';

interface CasesPageProps {
  navigate: (route: PageRoute) => void;
}

// 演示组件 1: 极致精美的移动端 AI 对话界面 (Fashion Case)
const DemoFashion = () => (
  <motion.div 
    initial="initial"
    whileInView="animate"
    viewport={{ once: false, amount: 0.5 }}
    className="w-full h-full bg-[#0F1115] p-6 flex items-center justify-center overflow-hidden"
  >
    <div className="w-[260px] h-[520px] bg-[#FDFDFF] rounded-[3.2rem] border-[10px] border-[#1A1C22] shadow-[0_40px_100px_rgba(0,0,0,0.5)] relative overflow-hidden flex flex-col font-sans">
      {/* 灵动岛 */}
      <div className="absolute top-2 left-1/2 -translate-x-1/2 w-20 h-6 bg-[#1A1C22] rounded-full z-30 flex items-center justify-center">
        <div className="w-6 h-1 bg-white/10 rounded-full"></div>
      </div>
      
      {/* 磨砂导航 */}
      <div className="bg-white/90 backdrop-blur-xl border-b border-slate-100 pt-10 pb-4 px-5 z-20">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 bg-brand-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-brand-600/20">
              <Bot size={18} />
            </div>
            <div>
              <div className="text-[10px] font-black text-slate-900 tracking-tight leading-none mb-1">MAISON AI</div>
              <div className="flex items-center gap-1">
                <span className="w-1 h-1 bg-success rounded-full animate-pulse"></span>
                <span className="text-[8px] font-bold text-success uppercase tracking-widest">Live</span>
              </div>
            </div>
          </div>
          <MoreHorizontal size={16} className="text-slate-300" />
        </div>
      </div>

      {/* 聊天区域 */}
      <div className="flex-grow p-4 space-y-4 bg-[#F8FAFC] overflow-hidden">
        <motion.div 
          variants={{ initial: { opacity: 0, x: 20 }, animate: { opacity: 1, x: 0 } }}
          transition={{ delay: 0.2 }}
          className="flex justify-end"
        >
          <div className="bg-slate-900 text-white px-4 py-3 rounded-2xl rounded-tr-none text-[9px] font-medium max-w-[85%] shadow-md leading-relaxed">
            Where is my order #SH-2025? It's for a wedding this Saturday. 👗
          </div>
        </motion.div>
        
        <div className="flex gap-2.5">
          <div className="w-7 h-7 bg-brand-50 rounded-lg flex items-center justify-center text-brand-600 shrink-0 border border-brand-100"><Bot size={14} /></div>
          <div className="space-y-3 flex-grow">
            <motion.div 
              variants={{ initial: { opacity: 0, x: -20 }, animate: { opacity: 1, x: 0 } }}
              transition={{ delay: 0.5 }}
              className="bg-white p-3.5 rounded-2xl rounded-tl-none text-[9px] text-slate-600 shadow-sm border border-slate-100 leading-relaxed"
            >
              Checking <span className="font-bold text-brand-600">Shopify</span> and <span className="font-bold text-slate-900">DHL</span> for you...
            </motion.div>
            
            <motion.div 
              variants={{ initial: { opacity: 0, scale: 0.95, y: 10 }, animate: { opacity: 1, scale: 1, y: 0 } }}
              transition={{ delay: 1.0, type: 'spring' }}
              className="bg-white rounded-[1.2rem] overflow-hidden border border-slate-100 shadow-[0_10px_30px_rgba(0,0,0,0.04)]"
            >
              <div className="p-3 border-b border-slate-50 bg-slate-50/50 flex justify-between items-center">
                 <div className="flex items-center gap-1.5">
                    <Box size={12} className="text-brand-600" />
                    <span className="text-[8px] font-black text-slate-800 uppercase tracking-tighter">In Transit</span>
                 </div>
                 <span className="text-[8px] font-bold text-slate-400">ETA: Jan 24</span>
              </div>
              <div className="p-3">
                <div className="flex items-center justify-between mb-3">
                   <div className="flex flex-col"><span className="text-[7px] text-slate-400 font-bold uppercase mb-0.5">Origin</span><span className="text-[9px] font-black text-slate-900">London</span></div>
                   <div className="flex-grow mx-2 flex items-center gap-0.5">
                      <div className="h-[1px] flex-grow bg-slate-100 relative">
                         <motion.div 
                           variants={{ initial: { width: 0 }, animate: { width: '75%' } }}
                           transition={{ duration: 1.5, ease: "circOut", delay: 1.2 }}
                           className="absolute top-0 left-0 h-full bg-brand-600"
                         ></motion.div>
                      </div>
                      <Zap size={8} className="text-brand-600 fill-brand-600" />
                   </div>
                   <div className="flex flex-col text-right"><span className="text-[7px] text-slate-400 font-bold uppercase mb-0.5">Dest.</span><span className="text-[9px] font-black text-slate-900">NYC</span></div>
                </div>
                <div className="flex items-center gap-1.5 px-2 py-1.5 bg-brand-50 rounded-lg">
                   <MapPin size={10} className="text-brand-600" />
                   <span className="text-[8px] font-bold text-brand-700">Arrived at NYC Sorting Facility</span>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>

      {/* 底部输入框 */}
      <div className="p-4 bg-white border-t border-slate-50 flex items-center gap-3">
        <div className="flex-grow bg-slate-50 rounded-xl px-4 h-10 flex items-center text-[9px] text-slate-400 font-medium tracking-tight">Type a message...</div>
        <div className="w-10 h-10 bg-slate-900 rounded-xl flex items-center justify-center text-white shadow-lg shadow-slate-900/10"><Send size={16} /></div>
      </div>
    </div>
  </motion.div>
);

// 演示组件 2: 极致专业的坐席工作台 (Tech Case)
const DemoHardware = () => (
  <motion.div 
    initial="initial"
    whileInView="animate"
    viewport={{ once: false, amount: 0.5 }}
    className="w-full h-full bg-[#0F1115] p-6 flex items-center justify-center overflow-hidden"
  >
    <div className="w-full h-full bg-[#FDFDFF] rounded-[2rem] shadow-[0_40px_100px_rgba(0,0,0,0.6)] border border-slate-800/20 overflow-hidden flex font-sans text-slate-900">
      {/* 侧边栏 */}
      <div className="w-16 bg-[#0F1115] flex flex-col items-center py-6 gap-6 shrink-0 border-r border-white/5">
        <div className="w-10 h-10 bg-brand-600 rounded-xl flex items-center justify-center text-white shadow-xl shadow-brand-600/20"><Headphones size={18} /></div>
        <div className="w-10 h-10 rounded-xl flex items-center justify-center text-slate-500"><MessageSquare size={16} /></div>
        <div className="w-10 h-10 rounded-xl flex items-center justify-center text-slate-500"><Activity size={16} /></div>
      </div>
      
      {/* 主工作区 */}
      <div className="flex-grow flex flex-col bg-white">
        <div className="h-16 border-b border-slate-100 flex items-center px-6 justify-between">
          <div className="flex items-center gap-3">
            <h4 className="text-[9px] font-black tracking-widest uppercase text-slate-900">Agent Co-Pilot</h4>
            <div className="px-2 py-0.5 bg-green-50 text-green-700 rounded-full text-[8px] font-black uppercase tracking-tighter border border-green-100">Live View</div>
          </div>
          <div className="flex items-center gap-4">
             <div className="text-right">
                <div className="text-[7px] font-black text-slate-400 uppercase tracking-widest">Avg CSAT</div>
                <div className="text-xs font-black">99.8%</div>
             </div>
          </div>
        </div>

        <div className="flex flex-grow overflow-hidden">
          <div className="w-48 border-r border-slate-50 p-4 space-y-2 hidden lg:block bg-[#F9FBFF]/50">
             <div className="p-3 bg-white rounded-xl border border-brand-200 shadow-sm ring-1 ring-brand-50">
                <div className="text-[9px] font-black text-slate-900 mb-1">#8291 Connectivity</div>
                <div className="text-[8px] text-slate-500 truncate">Customer reports timeout...</div>
             </div>
          </div>

          <div className="flex-grow flex flex-col relative bg-white">
            <div className="p-6 flex-grow space-y-4">
               <motion.div 
                 variants={{ initial: { opacity: 0, x: -10 }, animate: { opacity: 1, x: 0 } }}
                 transition={{ delay: 0.3 }}
                 className="flex gap-3"
               >
                  <div className="w-6 h-6 rounded-full overflow-hidden bg-slate-100"><img src="https://picsum.photos/100/100?random=5" /></div>
                  <div className="bg-slate-50 p-3.5 rounded-2xl rounded-tl-none text-[10px] text-slate-600 max-w-[80%] leading-relaxed border border-slate-100">
                     I've tried resetting the camera but it says "Connection Timeout". Help? 
                  </div>
               </motion.div>
               
               <motion.div 
                 variants={{ initial: { opacity: 0, y: 15 }, animate: { opacity: 1, y: 0 } }}
                 transition={{ delay: 0.8, type: 'spring' }}
                 className="ml-8 relative"
               >
                  <div className="absolute -left-4 top-0 bottom-0 w-0.5 bg-brand-500/20 rounded-full"></div>
                  <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-xl shadow-slate-900/5">
                    <div className="flex items-center gap-2 mb-3">
                       <Sparkles size={12} className="text-brand-600" />
                       <span className="text-[9px] font-black uppercase text-slate-900 tracking-widest">AI Logic Suggestion</span>
                    </div>
                    <p className="text-[10px] font-medium text-slate-700 leading-relaxed italic mb-4">
                      "Diagnostics show firmware v1.0.2. Guide user to Section 4.2 of the Manual for Manual Reset."
                    </p>
                    <div className="flex gap-2">
                       <button className="px-3 py-1.5 bg-brand-600 text-white rounded-lg text-[9px] font-black">Apply Suggestion</button>
                    </div>
                  </div>
               </motion.div>
            </div>
            
            <div className="p-4 bg-slate-50/50 border-t border-slate-100">
               <div className="bg-white border border-slate-200 rounded-xl p-3 flex items-center gap-3">
                  <div className="flex-grow text-[9px] text-slate-400 font-medium">Message customer...</div>
                  <div className="w-8 h-8 bg-slate-900 rounded-lg flex items-center justify-center text-white"><Send size={14} /></div>
               </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </motion.div>
);

// 演示组件 3: 极致美观的业务指标面板 (Furniture Case)
const DemoFurniture = () => (
  <motion.div 
    initial="initial"
    whileInView="animate"
    viewport={{ once: false, amount: 0.5 }}
    className="w-full h-full bg-[#0F1115] p-8 flex items-center justify-center overflow-hidden"
  >
    <div className="w-full h-full bg-[#FDFDFF] rounded-[2.5rem] shadow-[0_40px_100px_rgba(0,0,0,0.6)] border border-slate-800/10 overflow-hidden flex flex-col p-8 font-sans text-slate-900">
       <div className="flex justify-between items-start mb-8">
          <div className="flex items-center gap-3">
             <div className="w-12 h-12 bg-brand-50 rounded-2xl flex items-center justify-center text-brand-600 border border-brand-100 shadow-sm"><TrendingUp size={20} /></div>
             <div>
                <h4 className="text-sm font-[900] text-slate-900 tracking-tighter">Growth Metrics</h4>
                <div className="flex items-center gap-1.5 px-2 py-0.5 bg-brand-500/10 rounded-md mt-0.5">
                   <Zap size={8} className="text-brand-600 fill-brand-600" />
                   <span className="text-[8px] font-black text-brand-700 uppercase">Automated Analytics</span>
                </div>
             </div>
          </div>
          <div className="px-3 py-1.5 bg-slate-100 rounded-xl text-[8px] font-black text-slate-900">Real-time Dashboard</div>
       </div>

       <div className="grid grid-cols-2 gap-4 mb-8">
          <motion.div 
            variants={{ initial: { opacity: 0, y: 10 }, animate: { opacity: 1, y: 0 } }}
            transition={{ delay: 0.2 }}
            className="p-5 bg-slate-50 rounded-[1.8rem] border border-slate-100"
          >
             <div className="text-[8px] font-black text-slate-400 uppercase tracking-widest mb-2">Intent Precision</div>
             <div className="flex items-baseline gap-1.5">
                <div className="text-3xl font-[900] text-slate-900 tracking-tighter">97.8%</div>
                <div className="text-[9px] font-black text-success">+4.2%</div>
             </div>
          </motion.div>
          <motion.div 
            variants={{ initial: { opacity: 0, y: 10 }, animate: { opacity: 1, y: 0 } }}
            transition={{ delay: 0.4 }}
            className="p-5 bg-slate-50 rounded-[1.8rem] border border-slate-100"
          >
             <div className="text-[8px] font-black text-slate-400 uppercase tracking-widest mb-2">High-Intent Leads</div>
             <div className="flex items-baseline gap-1.5">
                <div className="text-3xl font-[900] text-slate-900 tracking-tighter">3,492</div>
                <div className="text-[9px] font-black text-brand-600 tracking-tighter">Verified</div>
             </div>
          </motion.div>
       </div>

       <div className="flex-grow flex flex-col">
          <div className="flex items-center justify-between mb-4">
             <div className="text-[9px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-1.5">
                <Search size={10} /> Optimization Funnel
             </div>
          </div>
          <div className="space-y-4">
             {[
               { label: "AI Initiated", value: 100, color: "bg-brand-100" },
               { label: "Need Identified", value: 88, color: "bg-brand-200" },
               { label: "Recommendation", value: 65, color: "bg-brand-400" },
               { label: "Conversion", value: 42, color: "bg-slate-900" }
             ].map((f, i) => (
               <div key={i} className="flex items-center gap-4">
                  <div className="text-[8px] font-bold text-slate-500 w-24 text-right">{f.label}</div>
                  <div className="flex-grow h-4 bg-slate-50 rounded-full overflow-hidden border border-slate-100">
                     <motion.div 
                       variants={{ initial: { width: 0 }, animate: { width: `${f.value}%` } }}
                       transition={{ duration: 1.2, delay: 0.6 + (i * 0.15), ease: "circOut" }}
                       className={`h-full ${f.color} rounded-full flex items-center justify-end px-2`}
                     >
                        <span className="text-[7px] font-black text-white/40">{f.value}%</span>
                     </motion.div>
                  </div>
               </div>
             ))}
          </div>
       </div>

       <div className="mt-auto pt-6 border-t border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
             <ShieldCheck size={12} className="text-green-600" />
             <span className="text-[8px] font-black text-slate-500 uppercase tracking-widest">GDPR Secure Analysis</span>
          </div>
          <div className="flex -space-x-2">
             {[1,2,3].map(i => (
                <div key={i} className="w-6 h-6 rounded-full border border-white overflow-hidden shadow-sm">
                   <img src={`https://picsum.photos/100/100?random=${i+10}`} className="w-full h-full object-cover" />
                </div>
             ))}
          </div>
       </div>
    </div>
  </motion.div>
);

const CasesPage: React.FC<CasesPageProps> = ({ navigate }) => {
  const successStories = [
    {
      company: "某头部快时尚 DTC 品牌",
      industry: "时尚服饰",
      results: [
        { label: "人工替代率", value: "82%" },
        { label: "订单转化率", value: "+18%" }
      ],
      description: "在黑五期间应对了超过日均 10 倍的咨询量，AI 自动处理了 90% 的物流查询，让其核心团队得以专注在高净值客户的销售转化上。",
      quote: "CrossBorderAI 的响应速度令人震惊，它不仅解决了成本问题，更重要的是它在凌晨 3 点帮我们抓住了北美市场的订单。",
      tags: ["Shopify Plus", "多语言接待", "弃单召回"],
      demoComponent: <DemoFashion />
    },
    {
      company: "知名智能家居品牌 (北美站)",
      industry: "智能硬件",
      results: [
        { label: "客户满意度", value: "4.9/5" },
        { label: "工单处理时效", value: "-65%" }
      ],
      description: "针对复杂的技术支持问题，AI 能够准确提取产品手册信息进行指引。当遇到无法解决的硬件故障时，通过坐席工作台无缝转接到国内技术团队。",
      quote: "这是我们用过最懂业务的 AI。它能准确理解客户关于‘智能配网失败’的抱怨，并给出完美的排查流程。",
      tags: ["技术支持", "人机协作", "工单流转"],
      demoComponent: <DemoHardware />
    },
    {
      company: "大型跨境家具独立站",
      industry: "家居生活",
      results: [
        { label: "月均节省成本", value: "$12,000+" },
        { label: "响应延迟", value: "< 1s" }
      ],
      description: "家具类目客单价高、决策周期长。AI 负责前期的尺码和材质咨询，高意向线索被识别后直接弹给坐席跟进，大大缩短了成单路径。",
      quote: "以前我们总是因为回消息慢丢单，现在 AI 帮我们‘守住了门’，转化率提升非常明显。",
      tags: ["高客单价", "线索挖掘", "私域运营"],
      demoComponent: <DemoFurniture />
    }
  ];

  return (
    <div className="bg-white min-h-screen pt-12">
      {/* Hero Section */}
      <section className="bg-bg-50 py-24 border-b border-bg-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-white border border-slate-200 shadow-sm rounded-full text-[10px] font-black uppercase tracking-widest text-slate-500 mb-8">
            <Sparkles size={12} className="text-brand-600 fill-brand-600" /> Customer Success Stories
          </div>
          <h1 className="text-5xl md:text-7xl font-black text-text-primary mb-8 tracking-tighter leading-none">
            实效驱动，<span className="text-brand-600 text-transparent bg-clip-text bg-gradient-to-r from-brand-600 to-indigo-600">见证增长。</span>
          </h1>
          <p className="text-xl text-text-secondary max-w-2xl mx-auto leading-relaxed font-medium">
            超越简单的“降本”，我们致力于通过 AI 为每一个独立站品牌构建可感知的增长路径与信任基石。
          </p>
        </div>
      </section>

      {/* Stats Summary - Minimalist */}
      <section className="py-16 border-b border-bg-100 bg-white">
        <div className="max-w-7xl mx-auto px-4 grid grid-cols-2 md:grid-cols-4 gap-12">
           {[
             { label: "Average Cost Reduction", value: "70%", icon: <Users /> },
             { label: "Lead Conversion Lift", value: "35%", icon: <TrendingUp /> },
             { label: "Supported Languages", value: "50+", icon: <Globe /> },
             { label: "Avg. Response Time", value: "0.8s", icon: <Clock /> }
           ].map((s, i) => (
             <div key={i} className="flex flex-col items-center md:items-start">
               <div className="text-slate-400 mb-4">{React.cloneElement(s.icon as React.ReactElement<any>, { size: 18 })}</div>
               <div className="text-4xl font-[900] text-text-primary tracking-tighter mb-1">{s.value}</div>
               <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{s.label}</div>
             </div>
           ))}
        </div>
      </section>

      {/* Case Grid */}
      <section className="py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="space-y-48">
            {successStories.map((story, idx) => (
              <div key={idx} className={`flex flex-col lg:flex-row gap-24 items-center ${idx % 2 !== 0 ? 'lg:flex-row-reverse' : ''}`}>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-6">
                     <span className="text-[10px] font-black text-brand-600 uppercase tracking-widest bg-brand-50 px-3 py-1.5 rounded-lg border border-brand-100">{story.industry} Case Study</span>
                  </div>
                  <h2 className="text-4xl font-[900] mb-8 tracking-tighter leading-none text-slate-900">{story.company}</h2>
                  <p className="text-slate-500 text-lg mb-10 leading-relaxed font-medium">
                    {story.description}
                  </p>
                  
                  <div className="grid grid-cols-2 gap-6 mb-12">
                    {story.results.map((r, i) => (
                      <div key={i} className="bg-slate-50/50 p-8 rounded-[2rem] border border-slate-100 group hover:border-brand-200 transition-colors">
                        <div className="text-4xl font-[900] text-brand-600 mb-2 tracking-tighter">{r.value}</div>
                        <div className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">{r.label}</div>
                      </div>
                    ))}
                  </div>

                  <div className="flex flex-wrap gap-2 mb-12">
                    {story.tags.map((tag, i) => (
                      <span key={i} className="text-[9px] font-black px-3 py-1.5 border border-slate-100 rounded-xl text-slate-400 uppercase tracking-widest">{tag}</span>
                    ))}
                  </div>

                  <div className="relative p-10 bg-[#0F1115] rounded-[2.5rem] shadow-2xl overflow-hidden group">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-bl-full -mr-16 -mt-16 group-hover:scale-110 transition-transform"></div>
                    <Quote className="text-white/10 mb-6" size={40} />
                    <p className="relative z-10 text-white font-medium text-lg italic leading-relaxed mb-6">
                      "{story.quote}"
                    </p>
                    <div className="flex items-center gap-4">
                       <div className="w-10 h-10 rounded-full bg-white/10 border border-white/10 flex items-center justify-center text-white font-black text-xs uppercase">CEO</div>
                       <div className="text-[10px] font-black text-white/40 uppercase tracking-widest">Head of Operations, {story.company}</div>
                    </div>
                  </div>
                </div>

                <div className="flex-1 w-full aspect-[4/3] relative">
                   <div className="absolute inset-0 bg-brand-600/20 blur-[120px] rounded-full scale-75 opacity-30"></div>
                   <div className="relative w-full h-full rounded-[3.5rem] overflow-hidden shadow-[0_50px_100px_rgba(0,0,0,0.15)] border border-slate-200 bg-slate-900 group">
                      {story.demoComponent}
                      {/* Interactive Badge */}
                      <div className="absolute top-8 left-8 flex items-center gap-2.5 px-4 py-2 bg-black/60 backdrop-blur-xl rounded-full border border-white/20 z-30 shadow-2xl">
                         <div className="w-2 h-2 bg-brand-500 rounded-full animate-pulse shadow-[0_0_10px_#6366f1]"></div>
                         <span className="text-[10px] text-white font-[800] tracking-[0.15em] uppercase">Simulated Production OS</span>
                      </div>
                   </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Bottom CTA - Premium Style */}
      <section className="py-48 text-center relative overflow-hidden bg-white">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full opacity-10 pointer-events-none">
           <div className="absolute top-[-20%] left-[-20%] w-[60%] h-[60%] bg-brand-500 blur-[150px] rounded-full"></div>
        </div>
        <div className="relative z-10 max-w-4xl mx-auto px-4">
          <h2 className="text-5xl md:text-7xl font-[900] mb-10 tracking-tighter leading-[0.9] text-slate-900">
            赋能您的品牌 <br/> 进入 <span className="text-brand-600 underline decoration-4 underline-offset-8">AI 增长时代。</span>
          </h2>
          <p className="text-xl text-slate-500 mb-16 font-medium leading-relaxed max-w-2xl mx-auto">
            与我们的顾问团队预约一次深度诊断，为您的独立站定制一套专属的 AI 自动化业务流。
          </p>
          <div className="flex flex-col sm:flex-row gap-6 justify-center items-center">
            <Button size="lg" className="h-20 px-16 text-xl font-black shadow-2xl shadow-brand-600/20" onClick={() => navigate({ type: 'pricing' })} withArrow>
              立即开启定制方案
            </Button>
            <Button size="lg" variant="secondary" className="h-20 px-12 text-lg font-bold bg-white border-slate-200">
              获取业务对标白皮书
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default CasesPage;