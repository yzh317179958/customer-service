import React from 'react';
import { Bot, Github, Twitter, Linkedin, ShieldCheck, Globe } from 'lucide-react';
import { PageRoute } from '../App';

interface FooterProps {
  onNavigate: (route: PageRoute) => void;
}

const Footer: React.FC<FooterProps> = ({ onNavigate }) => {
  const linkClass = "hover:text-brand-600 transition-colors cursor-pointer";

  return (
    <footer className="bg-white border-t border-bg-200 pt-20 pb-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-12 mb-20">
          
          <div className="col-span-2">
            <div className="flex items-center gap-2 mb-6 cursor-pointer group" onClick={() => onNavigate({ type: 'home' })}>
              <div className="p-2 bg-brand-600 rounded-lg text-white">
                <Bot className="h-6 w-6" />
              </div>
              <span className="text-2xl font-black text-text-primary tracking-tighter">Fiido</span>
            </div>
            <p className="text-text-secondary text-base leading-relaxed mb-8 max-w-sm">
              专为跨境独立站卖家打造的 AI 智能客服系统。7x24h 智能接待，让每一句沟通都产生价值。
            </p>
            <div className="flex gap-4">
              <a href="#" className="p-2 rounded-full border border-bg-200 text-text-muted hover:text-brand-600 hover:border-brand-600 transition-all"><Twitter className="h-5 w-5" /></a>
              <a href="#" className="p-2 rounded-full border border-bg-200 text-text-muted hover:text-brand-600 hover:border-brand-600 transition-all"><Linkedin className="h-5 w-5" /></a>
              <a href="#" className="p-2 rounded-full border border-bg-200 text-text-muted hover:text-brand-600 hover:border-brand-600 transition-all"><Github className="h-5 w-5" /></a>
            </div>
          </div>

          <div>
            <h4 className="text-text-primary font-black uppercase tracking-widest text-xs mb-6">核心产品</h4>
            <ul className="space-y-4 text-sm text-text-secondary font-medium">
              <li onClick={() => onNavigate({ type: 'product', id: 'ai-chatbot' })} className={linkClass}>AI 智能客服</li>
              <li onClick={() => onNavigate({ type: 'product', id: 'agent-workbench' })} className={linkClass}>坐席工作台</li>
              <li onClick={() => onNavigate({ type: 'cases' })} className={linkClass}>客户案例</li>
              <li onClick={() => onNavigate({ type: 'roadmap' })} className={linkClass}>路线图</li>
            </ul>
          </div>

          <div>
            <h4 className="text-text-primary font-black uppercase tracking-widest text-xs mb-6">解决方案</h4>
            <ul className="space-y-4 text-sm text-text-secondary font-medium">
              <li onClick={() => onNavigate({ type: 'solution', id: 'shopify' })} className={linkClass}>Shopify 增长方案</li>
              <li onClick={() => onNavigate({ type: 'solution', id: 'brand-overseas' })} className={linkClass}>品牌出海</li>
              <li onClick={() => onNavigate({ type: 'solution', id: 'custom' })} className={linkClass}>定制集成方案</li>
            </ul>
          </div>

          <div>
            <h4 className="text-text-primary font-black uppercase tracking-widest text-xs mb-6">关于</h4>
            <ul className="space-y-4 text-sm text-text-secondary font-medium">
              <li className={linkClass}>关于我们</li>
              <li className={linkClass}>服务协议</li>
              <li onClick={() => onNavigate({ type: 'pricing' })} className={linkClass}>价格说明</li>
            </ul>
          </div>

        </div>

        <div className="pt-10 border-t border-bg-100 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex flex-col md:flex-row items-center gap-4 text-sm text-text-muted">
            <p>&copy; {new Date().getFullYear()} Fiido. All rights reserved.</p>
          </div>
          <div className="text-xs font-black text-brand-600 uppercase tracking-widest">
            AI 智能客服 · 让服务更简单
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;