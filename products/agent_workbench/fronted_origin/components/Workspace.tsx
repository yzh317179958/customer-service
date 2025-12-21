
import React, { useState, useEffect, useRef } from 'react';
import { 
  Search, Filter, Send, Image, Paperclip, 
  Smile, Sparkles, Bot, Star, Phone, 
  Video, MoreVertical, CheckCheck, Clock,
  Bike, Zap, MapPin, Gauge, ShoppingBag, 
  History, MessageCircle, AlertCircle, ChevronRight,
  UserCheck, ShieldAlert, Monitor, Plus, Edit3, 
  ExternalLink, RefreshCw, Truck, ClipboardList, ChevronDown,
  ChevronUp, UserPlus, Hash, Calendar, Layers, Info, Settings2,
  Box, CreditCard, Activity, HelpCircle, Tag, TrendingUp
} from 'lucide-react';
import { Session, Message, SessionStatus } from '../types';
import { GoogleGenAI } from "@google/genai";

const Workspace: React.FC = () => {
  const [activeSessionId, setActiveSessionId] = useState<string>('1');
  const [inputText, setInputText] = useState('');
  const [aiSuggestions, setAiSuggestions] = useState<string[]>([]);
  const [rightPanelTab, setRightPanelTab] = useState<'info' | 'order' | 'roi'>('info');
  
  // 模拟数据
  const [sessions] = useState<Session[]>([
    {
      id: '1',
      customer: { id: 'c1', name: 'John Doe', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=John', vip: true, email: 'john@eu-bike.com', phone: '+44 7700 900077', channel: '官网', tags: ['Titan旗舰', '续航反馈', '英国站'], orderId: 'FIIDO-T-9821' },
      lastMessage: '三电池系统续航不如预期...',
      time: '10:45',
      unreadCount: 1,
      status: SessionStatus.MANUAL_LIVE,
      priority: '紧急'
    }
  ]);

  const [messages, setMessages] = useState<Message[]>([
    { id: 'm1', sender: 'customer', text: '你好，我的 Titan 刚收到。我加装了三电池系统，但感觉续航没达到 248 英里。', timestamp: '10:30' },
    { id: 'm2', sender: 'agent', text: '你好 John，祝贺你收到 Titan！续航受环境影响较大，我这就为您接入后台数据进行分析。', timestamp: '10:32', status: 'read' }
  ]);

  const activeSession = sessions[0];
  const scrollRef = useRef<HTMLDivElement>(null);

  const fetchAiSuggestions = async (text: string) => {
    try {
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      const response = await ai.models.generateContent({
        model: 'gemini-3-flash-preview',
        contents: `你是一名出海品牌的专家客服。针对用户反馈"${text}"，给出3个专业的回复方案，要求：1.包含同情心 2.引导检查具体参数 3.语言地道。`,
        config: { responseMimeType: "application/json" }
      });
      const resultText = response.text;
      if (resultText) setAiSuggestions(JSON.parse(resultText.trim()));
    } catch {
      setAiSuggestions(["请确认三块电池是否均已充满？","建议检查胎压，这会显著影响里程。","我们提供远程 BMS 诊断，是否现在开启？"]);
    }
  };

  const handleSendMessage = () => {
    if (!inputText.trim()) return;
    setMessages([...messages, { id: Date.now().toString(), sender: 'agent', text: inputText, timestamp: '10:46', status: 'sent' }]);
    setInputText('');
    fetchAiSuggestions(inputText);
  };

  return (
    <div className="flex h-full w-full bg-[#f8fafc] overflow-hidden">
      {/* 左侧会话列表 */}
      <div className="w-[280px] border-r border-slate-200 bg-white flex flex-col shrink-0">
        <div className="h-12 flex items-center px-4 border-b border-slate-100 bg-slate-50/50">
          <span className="text-[11px] font-black text-slate-400 uppercase tracking-widest">服务队列 (1)</span>
        </div>
        <div className="flex-1 overflow-y-auto">
          {sessions.map(s => (
            <div key={s.id} className="p-3 border-b border-slate-50 bg-fiido-light cursor-pointer relative">
               <div className="absolute left-0 top-0 bottom-0 w-1 bg-fiido"></div>
               <div className="flex gap-3">
                  <img src={s.customer.avatar} className="w-10 h-10 rounded-lg" alt=""/>
                  <div className="min-w-0 flex-1">
                    <div className="flex justify-between items-center"><span className="text-[12px] font-bold truncate">{s.customer.name}</span><span className="text-[10px] text-slate-400">10:45</span></div>
                    <p className="text-[11px] text-slate-500 truncate mt-0.5">{s.lastMessage}</p>
                  </div>
               </div>
            </div>
          ))}
        </div>
      </div>

      {/* 主对话区 */}
      <div className="flex-1 flex flex-col min-w-0 bg-white shadow-inner">
        <div className="h-12 border-b border-slate-200 flex items-center justify-between px-6 bg-white z-10">
          <div className="flex items-center gap-3">
             <span className="text-[13px] font-bold text-slate-800">{activeSession.customer.name}</span>
             <div className="flex items-center gap-1.5 px-2 py-0.5 bg-fiido/5 border border-fiido/10 rounded text-fiido text-[10px] font-black">
                <span className="w-1.5 h-1.5 bg-fiido rounded-full animate-pulse"></span> SLA: 04:30
             </div>
          </div>
          <div className="flex items-center gap-2">
             <button className="text-[11px] font-black text-slate-400 hover:text-fiido uppercase border border-slate-100 px-3 py-1 rounded">知识库匹配</button>
             <button className="bg-fiido text-white px-4 py-1.5 rounded text-[11px] font-black hover:opacity-90 shadow-sm">结束会话</button>
          </div>
        </div>

        <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6 bg-[#fcfdfe] custom-scrollbar">
           {messages.map(m => (
             <div key={m.id} className={`flex ${m.sender === 'agent' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] flex gap-3 ${m.sender === 'agent' ? 'flex-row-reverse' : ''}`}>
                   <img src={m.sender === 'agent' ? 'https://api.dicebear.com/7.x/avataaars/svg?seed=Agent' : activeSession.customer.avatar} className="w-8 h-8 rounded shadow-sm shrink-0" alt=""/>
                   <div className={`p-3 rounded-2xl text-[12px] leading-relaxed shadow-sm ${m.sender === 'agent' ? 'bg-fiido-black text-white rounded-tr-none' : 'bg-white border border-slate-200 text-slate-700 rounded-tl-none font-medium'}`}>
                      {m.text}
                   </div>
                </div>
             </div>
           ))}
        </div>

        <div className="p-4 border-t border-slate-100 bg-white">
           <div className="flex gap-2 mb-3 overflow-x-auto no-scrollbar py-1">
              <span className="bg-slate-50 text-slate-400 px-2 py-1 rounded text-[9px] font-black uppercase flex items-center gap-1 shrink-0 border border-slate-200"><Bot size={12}/> AI 灵感</span>
              {aiSuggestions.map((s, i) => (
                <button key={i} onClick={() => setInputText(s)} className="whitespace-nowrap bg-white border border-slate-200 px-3 py-1 rounded text-[10px] font-bold text-slate-600 hover:border-fiido hover:text-fiido transition-all shadow-sm">{s}</button>
              ))}
           </div>
           <div className="bg-slate-50 rounded-xl border border-slate-200 focus-within:border-fiido transition-all">
              <textarea 
                value={inputText}
                onChange={e => setInputText(e.target.value)}
                placeholder="在此输入回复... (Shift+Enter 换行)"
                className="w-full bg-transparent p-3 text-[12px] h-20 outline-none resize-none font-medium"
                onKeyDown={e => { if(e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage(); }}}
              />
              <div className="flex items-center justify-between p-3 border-t border-slate-100/50">
                 <div className="flex gap-3 text-slate-400"><Smile size={16}/><Image size={16}/><Paperclip size={16}/><Monitor size={16}/></div>
                 <button onClick={handleSendMessage} className="bg-fiido text-white px-4 py-1.5 rounded font-black text-[11px] flex items-center gap-2 hover:opacity-90">发送 <Send size={12}/></button>
              </div>
           </div>
        </div>
      </div>

      {/* 右侧业务台：针对中小卖家优化的 ROI 面板 */}
      <div className="w-[340px] border-l border-slate-200 bg-white flex flex-col shrink-0 overflow-hidden">
        <div className="p-4 border-b border-slate-50 flex items-center gap-4">
           <div className="flex-1">
             <h4 className="text-[13px] font-black text-slate-800">业务洞察</h4>
             <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-0.5">Business Intelligence</p>
           </div>
           <button className="p-2 hover:bg-slate-100 rounded text-slate-400"><Settings2 size={16}/></button>
        </div>

        <div className="flex border-b border-slate-100 bg-slate-50/30">
           {['info', 'order', 'roi'].map(t => (
             <button 
               key={t}
               onClick={() => setRightPanelTab(t as any)}
               className={`flex-1 py-3 text-[10px] font-black uppercase tracking-tighter transition-all border-b-2 ${rightPanelTab === t ? 'text-fiido border-fiido bg-white' : 'text-slate-400 border-transparent hover:text-slate-600'}`}
             >
               {t === 'info' ? '客户档案' : t === 'order' ? '订单集成' : 'AI 价值收益'}
             </button>
           ))}
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
           {rightPanelTab === 'info' && (
             <div className="space-y-4 animate-in fade-in duration-300">
                <div className="bg-white border border-slate-100 rounded-xl p-4 shadow-sm space-y-3">
                   <div className="flex justify-between items-center"><span className="text-[11px] font-bold text-slate-400">标签分类</span><button className="text-[10px] text-fiido font-black">+ 快速打标</button></div>
                   <div className="flex flex-wrap gap-2">
                     {activeSession.customer.tags.map(tag => (
                       <span key={tag} className="px-2 py-0.5 bg-fiido-light text-fiido rounded text-[10px] font-bold border border-fiido/10">{tag}</span>
                     ))}
                   </div>
                </div>
                <div className="bg-slate-900 rounded-xl p-4 text-white shadow-xl relative overflow-hidden group">
                   <div className="absolute right-0 bottom-0 opacity-5 group-hover:scale-110 transition-transform"><Sparkles size={60}/></div>
                   <div className="flex items-center gap-2 mb-2"><Sparkles size={14} className="text-fiido"/><span className="text-[10px] font-black text-fiido uppercase tracking-widest">AI 坐席建议</span></div>
                   <p className="text-[11px] font-medium leading-relaxed text-slate-300">该用户近期在伦敦搜索过“冬季保养”，系统已自动匹配“低温续航优化指南”。</p>
                   <button className="w-full mt-4 py-2 bg-fiido text-white rounded font-black text-[10px] uppercase shadow-lg shadow-fiido/20">一键推送保养建议</button>
                </div>
             </div>
           )}

           {rightPanelTab === 'order' && (
             <div className="space-y-3 animate-in fade-in duration-300">
                <div className="border-2 border-fiido/20 rounded-xl p-4 bg-white relative overflow-hidden">
                   <div className="absolute top-0 right-0 px-2 py-0.5 bg-fiido text-white text-[8px] font-black uppercase rounded-bl">已支付</div>
                   <span className="text-[9px] font-mono text-slate-400 font-bold tracking-tighter">#ORD-T-9821</span>
                   <h5 className="text-[12px] font-bold text-slate-800 mt-1">Fiido Titan (三电池版)</h5>
                   <div className="flex justify-between items-end mt-4">
                      <div className="text-[9px] text-slate-500 flex items-center gap-1.5 font-bold"><Truck size={12}/> DHL: 9021-3921</div>
                      <span className="text-[13px] font-black text-slate-800">$1,499.00</span>
                   </div>
                </div>
                <button className="w-full py-2.5 border border-dashed border-slate-200 rounded-xl text-[10px] font-black text-slate-400 hover:border-fiido hover:text-fiido transition-all uppercase tracking-widest">+ 关联三方 ERP 订单</button>
             </div>
           )}

           {rightPanelTab === 'roi' && (
             <div className="space-y-4 animate-in fade-in duration-300">
                <div className="bg-[#1e293b] rounded-xl p-5 text-white shadow-xl">
                   <div className="flex items-center gap-2 mb-6"><TrendingUp size={16} className="text-emerald-400"/><span className="text-[10px] font-black uppercase tracking-widest">AI 数字化降本看板</span></div>
                   <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-1">
                        <p className="text-[9px] text-slate-500 font-black uppercase">本月节省人工</p>
                        <p className="text-2xl font-black text-white">124<span className="text-xs ml-0.5 text-slate-500">h</span></p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-[9px] text-slate-500 font-black uppercase">响应时效优化</p>
                        <p className="text-2xl font-black text-emerald-400">85<span className="text-xs ml-0.5 text-emerald-500/50">%</span></p>
                      </div>
                   </div>
                   <div className="mt-8 pt-4 border-t border-white/5">
                      <p className="text-[9px] text-slate-500 font-black uppercase mb-2">预估减少人力开支</p>
                      <p className="text-xl font-black text-white">$1,280.00 <span className="text-[10px] font-medium text-slate-500 ml-1">USD/月</span></p>
                   </div>
                </div>
                <div className="p-4 bg-white border border-slate-100 rounded-xl space-y-2">
                   <h5 className="text-[11px] font-black text-slate-800 uppercase tracking-widest">智能知识库库覆盖率</h5>
                   <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden shadow-inner">
                      <div className="h-full bg-fiido shadow-[0_0_8px_#00a6a0]" style={{width: '72%'}}></div>
                   </div>
                   <p className="text-[10px] text-slate-400 font-bold">已覆盖 72% 的高频售后问题。建议继续完善“电池冬季养护”类目。</p>
                </div>
             </div>
           )}
        </div>

        <div className="p-4 border-t border-slate-100 bg-white grid grid-cols-2 gap-2">
           <button className="py-2.5 bg-fiido-black text-white text-[11px] font-black rounded-lg flex items-center justify-center gap-2 hover:bg-slate-800 transition-all active:scale-95 shadow-lg"><Edit3 size={14}/> 快速下单</button>
           <button className="py-2.5 bg-slate-100 text-slate-600 text-[11px] font-black rounded-lg flex items-center justify-center gap-2 hover:bg-slate-200 transition-all border border-slate-200"><History size={14}/> 服务历史</button>
        </div>
      </div>
    </div>
  );
};

export default Workspace;
