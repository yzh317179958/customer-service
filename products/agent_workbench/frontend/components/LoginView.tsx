
import React, { useState } from 'react';
import {
  Bike,
  Lock,
  Mail,
  ArrowRight,
  ShieldCheck,
  Globe,
  AlertCircle,
  Fingerprint
} from 'lucide-react';
import { useAuthStore } from '../src/stores';

const LoginView: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  // 从 authStore 获取状态和方法
  const { login, isLoading, error, clearError } = useAuthStore();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    if (!username.trim() || !password.trim()) {
      return;
    }

    await login({ username: username.trim(), password });
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-[#f0f4f8] relative overflow-hidden font-sans">
      {/* 装饰性背景元素 */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-fiido/5 rounded-full blur-[120px] animate-pulse"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-fiido/10 rounded-full blur-[120px] animate-pulse"></div>

      <div className="max-w-6xl w-full grid grid-cols-1 lg:grid-cols-2 gap-0 bg-white rounded-[48px] shadow-2xl overflow-hidden relative z-10 m-6">

        {/* 左侧：品牌展示区 */}
        <div className="hidden lg:flex flex-col justify-between p-16 bg-fiido-black text-white relative">
           <div className="absolute inset-0 opacity-10 pointer-events-none overflow-hidden">
              <Bike size={600} className="absolute -bottom-20 -left-20 rotate-12" />
           </div>

           <div className="relative z-10">
              <div className="flex items-center gap-3 mb-12">
                 <div className="bg-fiido p-2 rounded-xl">
                    <Bike size={24} className="text-white" />
                 </div>
                 <span className="text-xl font-brand font-black tracking-tighter uppercase">Fiido Intelligence</span>
              </div>

              <div className="space-y-6">
                 <h1 className="text-5xl font-black leading-tight tracking-tighter">
                    驱动全球<br/>
                    <span className="text-fiido">智能服务</span> 生态
                 </h1>
                 <p className="text-slate-400 text-lg max-w-sm leading-relaxed">
                    专为出海品牌打造的次世代 AI 坐席工作台，将每一场对话转化为品牌增长。
                 </p>
              </div>
           </div>

           <div className="relative z-10 grid grid-cols-2 gap-8">
              <div className="space-y-2">
                 <div className="flex items-center gap-2 text-fiido font-black text-[10px] uppercase tracking-widest">
                    <ShieldCheck size={14}/> 生产级安全
                 </div>
                 <p className="text-xs text-slate-500">端到端数据加密与多重身份验证</p>
              </div>
              <div className="space-y-2">
                 <div className="flex items-center gap-2 text-fiido font-black text-[10px] uppercase tracking-widest">
                    <Globe size={14}/> 全球加速
                 </div>
                 <p className="text-xs text-slate-500">跨地区毫秒级响应，稳定连接全球客户</p>
              </div>
           </div>
        </div>

        {/* 右侧：登录表单区 */}
        <div className="p-12 lg:p-20 flex flex-col justify-center">
           <div className="mb-12">
              <h2 className="text-3xl font-black text-slate-800 tracking-tight mb-2">欢迎回来</h2>
              <p className="text-slate-400 font-bold text-xs uppercase tracking-[0.2em]">请使用您的 Fiido 账号登录系统</p>
           </div>

           {/* 错误提示 */}
           {error && (
             <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-2xl flex items-center gap-3">
               <AlertCircle size={18} className="text-red-500 flex-shrink-0" />
               <span className="text-sm font-bold text-red-600">{error}</span>
             </div>
           )}

           <form onSubmit={handleLogin} className="space-y-6">
              <div className="space-y-2">
                 <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">用户名 / 员工 ID</label>
                 <div className="relative group">
                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300 group-focus-within:text-fiido transition-colors" size={18} />
                    <input
                       type="text"
                       value={username}
                       onChange={(e) => setUsername(e.target.value)}
                       required
                       placeholder="请输入用户名"
                       className="w-full bg-slate-50 border border-slate-200 rounded-2xl py-4 pl-12 pr-6 text-sm font-bold outline-none focus:bg-white focus:border-fiido focus:ring-4 focus:ring-fiido/5 transition-all"
                    />
                 </div>
              </div>

              <div className="space-y-2">
                 <div className="flex justify-between items-center px-1">
                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">安全密码</label>
                    <button type="button" className="text-[10px] font-black text-fiido uppercase tracking-widest hover:underline">忘记密码?</button>
                 </div>
                 <div className="relative group">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300 group-focus-within:text-fiido transition-colors" size={18} />
                    <input
                       type="password"
                       value={password}
                       onChange={(e) => setPassword(e.target.value)}
                       required
                       placeholder="请输入您的密码"
                       className="w-full bg-slate-50 border border-slate-200 rounded-2xl py-4 pl-12 pr-6 text-sm font-bold outline-none focus:bg-white focus:border-fiido focus:ring-4 focus:ring-fiido/5 transition-all"
                    />
                 </div>
              </div>

              <div className="flex items-center gap-3 px-1 py-2">
                 <input type="checkbox" id="remember" className="w-4 h-4 rounded border-slate-300 text-fiido focus:ring-fiido cursor-pointer" defaultChecked />
                 <label htmlFor="remember" className="text-xs font-bold text-slate-500 cursor-pointer">在此设备上保持登录</label>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className={`w-full py-4 rounded-2xl bg-fiido text-white text-[13px] font-black uppercase tracking-widest shadow-xl shadow-fiido/20 flex items-center justify-center gap-2 transition-all hover:scale-[1.01] active:scale-95 ${isLoading ? 'opacity-80 cursor-wait' : 'hover:opacity-90'}`}
              >
                {isLoading ? (
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                ) : (
                  <>登录 Fiido 工作台 <ArrowRight size={18} /></>
                )}
              </button>
           </form>

           <div className="mt-12 space-y-6">
              <div className="relative">
                 <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-slate-100"></div></div>
                 <div className="relative flex justify-center text-[10px] font-black uppercase tracking-widest"><span className="bg-white px-4 text-slate-300">或使用快速访问</span></div>
              </div>

              <div className="grid grid-cols-1 gap-4">
                 <button className="flex items-center justify-center gap-3 py-3 px-6 bg-white border border-slate-200 rounded-2xl text-[11px] font-black text-slate-600 hover:bg-slate-50 hover:border-slate-300 transition-all">
                    <Fingerprint size={16} className="text-fiido" /> 专家模式 SSO 快速登录
                 </button>
              </div>
           </div>

           <div className="mt-12 flex items-center justify-center gap-6 text-[10px] font-black text-slate-300 uppercase tracking-widest">
              <span className="hover:text-fiido cursor-pointer transition-colors">隐私条款</span>
              <span className="w-1 h-1 bg-slate-200 rounded-full"></span>
              <span className="hover:text-fiido cursor-pointer transition-colors">SOP 帮助手册</span>
              <span className="w-1 h-1 bg-slate-200 rounded-full"></span>
              <span className="hover:text-fiido cursor-pointer transition-colors">系统状态: 正常</span>
           </div>
        </div>
      </div>

      <div className="absolute bottom-8 text-center w-full">
         <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.4em]">© 2024 Fiido Intelligent Technology Co., Ltd.</p>
      </div>
    </div>
  );
};

export default LoginView;
