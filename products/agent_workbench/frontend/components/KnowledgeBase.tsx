
import React, { useState } from 'react';
import { Search, Folder, FileText, ChevronRight, Plus, Eye, Sparkles, Bike, Zap, Battery, ShieldCheck, Download, ExternalLink } from 'lucide-react';

const KnowledgeBase: React.FC = () => {
  const [activeCategory, setActiveCategory] = useState('全部');
  
  const categories = [
    { name: '全部', icon: Folder },
    { name: '产品手册', icon: FileText },
    { name: '技术支持', icon: Zap },
    { name: '组装指南', icon: Bike },
    { name: '电池保养', icon: Battery },
    { name: '合规政策', icon: ShieldCheck },
  ];

  const articles = [
    { title: 'Fiido Titan: 三电池系统安装与续航优化指南', category: '技术支持', updated: '1小时前', views: '1.2w', hot: true, icon: Battery },
    { title: 'C11 Pro Mivice S200 力矩传感器校准教程', category: '产品手册', updated: '5小时前', views: '4.2k', hot: false, icon: Zap },
    { title: 'Fiido X 镁合金车架日常维护注意事项', category: '技术支持', updated: '昨天', views: '1.8k', hot: true, icon: Bike },
    { title: '2025年欧盟/美国电动自行车道路法规指南', category: '合规政策', updated: '3天前', views: '8.5k', hot: false, icon: ShieldCheck },
    { title: '冬季低温环境下电池性能保障建议', category: '电池保养', updated: '1周前', views: '5.1k', hot: true, icon: Battery },
  ];

  return (
    <div className="h-full flex flex-col bg-white animate-in zoom-in-95 duration-700 font-sans">
      <div className="p-16 border-b border-slate-100 bg-slate-50/50 relative overflow-hidden shrink-0">
        <div className="absolute top-0 right-0 p-24 opacity-[0.02] pointer-events-none">
           <Bike size={500} />
        </div>
        <div className="max-w-4xl mx-auto text-center mb-12 relative z-10">
          <h1 className="text-4xl font-brand font-black text-slate-800 mb-4 tracking-tighter uppercase">知识赋能中心</h1>
          <p className="text-slate-400 text-xs font-bold uppercase tracking-[0.4em]">Make innovative e-mobility accessible to all</p>
        </div>
        
        <div className="max-w-2xl mx-auto relative group z-10">
          <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-slate-300 w-6 h-6 group-focus-within:text-fiido transition-colors" />
          <input 
            type="text" 
            placeholder="搜手册、错误码 (如 E001)、组装视频或话术模版..." 
            className="w-full bg-white border border-slate-200 rounded-[32px] py-6 pl-16 pr-8 text-base shadow-2xl shadow-slate-200/40 outline-none focus:border-fiido focus:ring-8 focus:ring-fiido/5 transition-all font-bold placeholder:text-slate-300"
          />
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* 左侧导航树 */}
        <div className="w-72 border-r border-slate-100 p-8 space-y-2 overflow-y-auto custom-scrollbar bg-white shrink-0">
          <h3 className="text-[10px] font-black text-slate-300 uppercase tracking-[0.2em] mb-8">内容分类</h3>
          {categories.map(cat => (
            <button
              key={cat.name}
              onClick={() => setActiveCategory(cat.name)}
              className={`w-full flex items-center justify-between p-4 rounded-2xl text-[12px] font-black transition-all ${
                activeCategory === cat.name ? 'bg-fiido text-white shadow-xl shadow-fiido/30' : 'text-slate-500 hover:bg-slate-50'
              }`}
            >
              <div className="flex items-center gap-3">
                <cat.icon size={16} className={activeCategory === cat.name ? 'text-white' : 'text-slate-300'} />
                {cat.name}
              </div>
              <ChevronRight size={14} className={activeCategory === cat.name ? 'text-white/50' : 'text-slate-200'} />
            </button>
          ))}
          <div className="pt-12">
            <button className="w-full flex items-center justify-center gap-2 py-4 bg-fiido-black text-white rounded-[24px] text-[11px] font-black uppercase tracking-widest hover:bg-slate-800 transition-all shadow-xl">
              <Plus size={18} /> 上传新文档
            </button>
          </div>
        </div>

        {/* 右侧内容列表 */}
        <div className="flex-1 bg-slate-50/30 p-12 overflow-y-auto custom-scrollbar">
           <div className="flex items-center justify-between mb-10">
              <div className="flex items-center gap-3 text-fiido">
                <div className="p-2.5 bg-fiido/10 rounded-2xl"><Sparkles size={22}/></div>
                <span className="text-sm font-black uppercase tracking-widest">AI 智能推荐建议</span>
              </div>
              <div className="flex gap-4">
                 <button className="text-[11px] font-black text-slate-400 hover:text-fiido uppercase tracking-widest transition-all">最新更新</button>
                 <button className="text-[11px] font-black text-fiido uppercase tracking-widest transition-all">最热门文章</button>
              </div>
           </div>
           
           <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
             {articles.map((art, i) => (
               <div key={i} className="bg-white p-8 rounded-[40px] border border-slate-100 shadow-sm hover:shadow-2xl hover:-translate-y-2 transition-all cursor-pointer group flex flex-col h-full">
                 <div className="flex justify-between items-start mb-8">
                   <div className="bg-slate-50 p-4 rounded-[28px] text-slate-400 group-hover:bg-fiido group-hover:text-white transition-all shadow-inner">
                     <art.icon size={32} />
                   </div>
                   <div className="flex gap-2">
                     <button className="p-3 bg-slate-50 hover:bg-fiido-light rounded-2xl text-slate-300 hover:text-fiido transition-all"><Download size={18}/></button>
                     <button className="p-3 bg-slate-50 hover:bg-fiido-light rounded-2xl text-slate-300 hover:text-fiido transition-all"><ExternalLink size={18}/></button>
                   </div>
                 </div>
                 <h4 className="text-[18px] font-bold text-slate-800 mb-6 group-hover:text-fiido transition-colors leading-snug">{art.title}</h4>
                 <div className="mt-auto flex items-center gap-6 text-[10px] text-slate-400 font-bold uppercase tracking-widest border-t border-slate-50 pt-6">
                   <span className="flex items-center gap-2">更新于: {art.updated}</span>
                   <span className="flex items-center gap-2 font-brand font-black"><Eye size={12} className="text-slate-300"/> {art.views} 次阅读</span>
                   {art.hot && (
                     <span className="ml-auto text-[9px] font-black text-white bg-red-500 px-3 py-1.5 rounded-full uppercase tracking-[0.2em] shadow-lg shadow-red-200 animate-pulse">热点文章</span>
                   )}
                 </div>
               </div>
             ))}
           </div>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeBase;
