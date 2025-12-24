import React, { useState } from 'react';
import { User, Bell, Shield, Globe, Keyboard, Database, ChevronRight, Check, Settings as SettingsIcon } from 'lucide-react';
import QuickReplyManager from './QuickReplyManager';
import ProfileSettings from './ProfileSettings';
import PasswordSettings from './PasswordSettings';

const Settings: React.FC = () => {
  const [activeSection, setActiveSection] = useState<string | null>(null);

  // 子页面路由
  if (activeSection === '话术短语库') {
    return <QuickReplyManager onBack={() => setActiveSection(null)} />;
  }

  if (activeSection === '个人配置') {
    return <ProfileSettings onBack={() => setActiveSection(null)} />;
  }

  if (activeSection === '账号与合规') {
    return <PasswordSettings onBack={() => setActiveSection(null)} />;
  }

  const sections = [
    { title: '个人配置', icon: User, desc: '修改头像、显示名称等个人信息', clickable: true },
    { title: '通知与提醒', icon: Bell, desc: '配置声音告警、弹窗及外部 IM 推送逻辑', clickable: false },
    { title: '账号与合规', icon: Shield, desc: '修改密码、动态令牌验证及系统操作审计', clickable: true },
    { title: '话术短语库', icon: Keyboard, desc: '管理个人及团队共享的快捷回复模版', clickable: true },
    { title: '语言与时区', icon: Globe, desc: '切换后台语言（默认中文）及各地区时区显示', clickable: false },
    { title: '外部集成', icon: Database, desc: '绑定 ERP 系统、物流 API 及售后备件库', clickable: false },
  ];

  return (
    <div className="h-full bg-slate-50/30 p-12 overflow-y-auto font-sans">
      <div className="max-w-5xl mx-auto space-y-12">
        <header>
          <h1 className="text-3xl font-brand font-black text-slate-800 tracking-tighter uppercase">系统配置中心</h1>
          <p className="text-slate-400 text-xs font-bold uppercase tracking-[0.4em] mt-2">个性化您的工作台并优化服务流程</p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
           {sections.map((s, i) => (
             <div
               key={i}
               onClick={() => s.clickable && setActiveSection(s.title)}
               className={`bg-white p-8 rounded-[48px] border border-slate-100 shadow-[0_12px_32px_rgba(0,0,0,0.02)] hover:shadow-2xl hover:-translate-y-2 transition-all flex gap-6 group ${
                 s.clickable ? 'cursor-pointer' : 'cursor-default opacity-60'
               }`}
             >
                <div className="bg-slate-50 p-4 rounded-[28px] text-slate-400 group-hover:bg-fiido group-hover:text-white transition-all shadow-inner h-fit">
                  <s.icon size={28}/>
                </div>
                <div className="flex-1">
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="font-bold text-slate-800 text-base">{s.title}</h4>
                    <ChevronRight size={16} className="text-slate-200 group-hover:text-fiido transition-colors"/>
                  </div>
                  <p className="text-[12px] text-slate-400 leading-relaxed font-bold">{s.desc}</p>
                </div>
             </div>
           ))}
        </div>

        <div className="bg-fiido-black p-10 rounded-[48px] text-white shadow-2xl relative overflow-hidden group">
           <div className="absolute -right-12 -bottom-12 p-12 opacity-5 pointer-events-none group-hover:rotate-6 transition-transform duration-700">
              {/* Fix: Replaced recursive Settings component call with SettingsIcon from lucide-react */}
              <SettingsIcon size={300} />
           </div>
           <h3 className="font-brand font-black text-fiido mb-10 text-xs uppercase tracking-[0.3em]">界面交互首选项</h3>
           <div className="space-y-10 relative z-10">
              <div className="flex items-center justify-between">
                 <div>
                    <p className="text-sm font-bold text-white mb-1">视觉深色模式</p>
                    <p className="text-[11px] text-slate-500 font-bold">在低光环境下提供更舒适的坐席操作体验</p>
                 </div>
                 <div className="w-14 h-8 bg-white/5 rounded-full relative cursor-pointer border border-white/10 transition-all">
                    <div className="absolute left-1 top-1 w-6 h-6 bg-slate-600 rounded-full shadow-lg"></div>
                 </div>
              </div>
              <div className="h-px bg-white/5"></div>
              <div className="flex items-center justify-between">
                 <div>
                    <p className="text-sm font-bold text-white mb-1">实时 AI 语音转写</p>
                    <p className="text-[11px] text-slate-500 font-bold">自动将 VoIP 通话实时转录为中英双语文字</p>
                 </div>
                 <div className="w-14 h-8 bg-fiido rounded-full relative cursor-pointer shadow-[0_0_15px_rgba(0,166,160,0.5)] transition-all">
                    <div className="absolute right-1 top-1 w-6 h-6 bg-white rounded-full shadow-lg flex items-center justify-center">
                       <Check size={14} className="text-fiido" />
                    </div>
                 </div>
              </div>
              <div className="h-px bg-white/5"></div>
              <div className="flex items-center justify-between">
                 <div>
                    <p className="text-sm font-bold text-white mb-1">全球 CDN 加速</p>
                    <p className="text-[11px] text-slate-500 font-bold">针对欧美地区会话延迟进行深度优化</p>
                 </div>
                 <div className="w-14 h-8 bg-fiido rounded-full relative cursor-pointer shadow-[0_0_15px_rgba(0,166,160,0.5)] transition-all">
                    <div className="absolute right-1 top-1 w-6 h-6 bg-white rounded-full shadow-lg flex items-center justify-center">
                       <Check size={14} className="text-fiido" />
                    </div>
                 </div>
              </div>
           </div>
           <div className="mt-12 flex justify-end">
              <button className="px-10 py-4 bg-white text-fiido-black rounded-2xl font-black text-[12px] uppercase tracking-widest hover:bg-slate-50 transition-all">保存全局配置</button>
           </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;