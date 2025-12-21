
import React from 'react';
import { ShieldCheck, CheckCircle, AlertCircle, Search, Filter, Sparkles, TrendingUp, UserCheck, MessageSquare } from 'lucide-react';

const QualityAudit: React.FC = () => {
  const auditRecords = [
    { id: 'QA-001', agent: '李建国', customer: 'John Doe', score: 98, date: '2024-03-22', status: '合格', type: 'Titan续航疑虑回复' },
    { id: 'QA-002', agent: '王小美', customer: 'Marie Chen', score: 92, date: '2024-03-22', status: '合格', type: '物流发货查询' },
    { id: 'QA-003', agent: '张强', customer: 'Adam Smith', score: 75, date: '2024-03-21', status: '不合格', type: '退换货政策解答' },
  ];

  return (
    <div className="h-full bg-slate-50/30 p-12 overflow-y-auto font-sans">
      <div className="max-w-6xl mx-auto space-y-12">
        <div className="flex justify-between items-end">
          <div>
            <h1 className="text-3xl font-brand font-black text-slate-800 tracking-tighter">AI 智能质检大盘</h1>
            <p className="text-slate-400 text-xs font-bold uppercase tracking-[0.2em] mt-2">基于 NLP 深度识别会话违规、情绪及话术规范</p>
          </div>
          <button className="bg-fiido-black text-white px-8 py-3.5 rounded-[24px] text-[13px] font-black shadow-2xl shadow-fiido-black/10 hover:bg-slate-800 transition-all flex items-center gap-2">
            <Sparkles size={18}/> 执行全量 AI 抽检
          </button>
        </div>

        {/* 质检概览卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
           <div className="bg-white p-8 rounded-[48px] border border-slate-100 shadow-[0_12px_32px_rgba(0,0,0,0.02)] relative overflow-hidden group">
             <div className="absolute -right-6 -bottom-6 opacity-[0.03] group-hover:scale-110 transition-transform"><TrendingUp size={150}/></div>
             <ShieldCheck size={28} className="text-fiido mb-6"/>
             <p className="text-4xl font-brand font-black text-slate-800">99.1%</p>
             <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mt-2">本月全量合格率</p>
           </div>
           <div className="bg-white p-8 rounded-[48px] border border-slate-100 shadow-[0_12px_32px_rgba(0,0,0,0.02)] relative overflow-hidden group">
             <div className="absolute -right-6 -bottom-6 opacity-[0.03] group-hover:scale-110 transition-transform"><MessageSquare size={150}/></div>
             <CheckCircle size={28} className="text-green-500 mb-6"/>
             <p className="text-4xl font-brand font-black text-slate-800">1,204</p>
             <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mt-2">本月已质检会话数</p>
           </div>
           <div className="bg-white p-8 rounded-[48px] border border-slate-100 shadow-[0_12px_32px_rgba(0,0,0,0.02)] relative overflow-hidden group">
             <div className="absolute -right-6 -bottom-6 opacity-[0.03] group-hover:scale-110 transition-transform"><UserCheck size={150}/></div>
             <AlertCircle size={28} className="text-red-500 mb-6"/>
             <p className="text-4xl font-brand font-black text-slate-800">12</p>
             <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mt-2">待人工复核违规</p>
           </div>
        </div>

        {/* 质检记录列表 */}
        <div className="bg-white rounded-[48px] border border-slate-100 shadow-[0_24px_64px_rgba(0,0,0,0.03)] overflow-hidden">
           <div className="p-8 border-b border-slate-50 flex justify-between items-center bg-slate-50/50">
             <h3 className="font-brand font-black text-slate-800 uppercase tracking-widest text-[13px]">实时质检流水</h3>
             <div className="flex gap-3">
               <div className="relative">
                 <Search size={14} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300"/>
                 <input type="text" placeholder="搜座席、关键词..." className="bg-white border border-slate-100 rounded-2xl py-2 pl-10 pr-4 text-[12px] font-bold outline-none focus:ring-4 focus:ring-fiido/5 focus:border-fiido transition-all"/>
               </div>
               <button className="p-2.5 bg-white border border-slate-100 rounded-2xl text-slate-400 shadow-sm hover:text-fiido transition-all"><Filter size={18}/></button>
             </div>
           </div>
           <div className="divide-y divide-slate-50">
             {auditRecords.map(r => (
               <div key={r.id} className="p-8 flex items-center justify-between hover:bg-slate-50 transition-all cursor-pointer group">
                 <div className="flex gap-8 items-center">
                    <div className={`w-16 h-16 rounded-[24px] flex flex-col items-center justify-center shadow-inner group-hover:shadow-lg transition-all ${r.score >= 90 ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'}`}>
                      <span className="text-xl font-brand font-black">{r.score}</span>
                      <span className="text-[8px] font-black uppercase tracking-widest">分</span>
                    </div>
                    <div>
                      <div className="flex items-center gap-3 mb-2">
                         <span className="text-base font-bold text-slate-800">[{r.agent}] 的服务会话</span>
                         <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest">{r.id}</span>
                      </div>
                      <p className="text-[11px] text-slate-400 font-bold uppercase tracking-widest">
                        场景：{r.type} • 客户：{r.customer} • 抽检日期：{r.date}
                      </p>
                    </div>
                 </div>
                 <div className="flex items-center gap-4">
                    <span className={`px-4 py-1 rounded-full text-[10px] font-black tracking-widest ${r.status === '合格' ? 'bg-fiido/10 text-fiido' : 'bg-red-50 text-red-500'}`}>{r.status}</span>
                    <button className="px-6 py-2.5 border border-slate-200 rounded-2xl text-[11px] font-black text-slate-500 hover:border-fiido hover:text-fiido hover:bg-fiido-light/30 transition-all">查看录音/回放</button>
                 </div>
               </div>
             ))}
           </div>
           <button className="w-full py-6 text-[11px] font-black text-slate-300 uppercase tracking-[0.3em] hover:text-fiido hover:bg-slate-50 transition-all">
             加载更多质检历史
           </button>
        </div>
      </div>
    </div>
  );
};

export default QualityAudit;
