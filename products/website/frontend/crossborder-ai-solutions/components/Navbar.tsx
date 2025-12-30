import React, { useState, useEffect } from 'react';
import { Bot, Menu, X, Sparkles } from 'lucide-react';
import Button from './ui/Button';
import { PageRoute } from '../App';
import { motion, AnimatePresence } from 'framer-motion';

interface NavbarProps {
  onNavigate: (route: PageRoute) => void;
  currentRoute: PageRoute;
}

const Navbar: React.FC<NavbarProps> = ({ onNavigate, currentRoute }) => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 10);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks: { name: string; route: PageRoute }[] = [
    { name: 'AI智能客服', route: { type: 'product', id: 'ai-chatbot' } },
    { name: '坐席工作台', route: { type: 'product', id: 'agent-workbench' } },
    { name: '客户案例', route: { type: 'cases' } },
    { name: '价格方案', route: { type: 'pricing' } },
  ];

  const handleNavClick = (route: PageRoute) => {
    onNavigate(route);
    setMobileMenuOpen(false);
  };

  const checkActive = (linkRoute: PageRoute) => {
    if (linkRoute.type !== currentRoute.type) return false;
    if (linkRoute.type === 'product' && currentRoute.type === 'product') {
      return linkRoute.id === currentRoute.id;
    }
    return true;
  };

  return (
    <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
      isScrolled ? 'bg-white/95 backdrop-blur-md border-b border-bg-200 py-3 shadow-sm' : 'bg-transparent py-6'
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          
          <div className="flex items-center gap-2 cursor-pointer group" onClick={() => handleNavClick({ type: 'home' })}>
            <div className="p-2 bg-brand-600 rounded-xl text-white shadow-lg group-hover:scale-110 transition-all">
              <Bot size={24} />
            </div>
            <div className="flex flex-col">
              <span className="text-xl font-black tracking-tighter leading-none text-text-primary">Fiido</span>
              <span className="text-[8px] font-black text-brand-600 tracking-[0.3em] uppercase mt-1">AI 智能客服</span>
            </div>
          </div>

          <nav className="hidden lg:flex items-center gap-10">
            {navLinks.map((link, idx) => (
              <button 
                key={idx}
                className={`relative text-sm font-black transition-colors py-2 ${
                  checkActive(link.route) ? 'text-brand-600' : 'text-text-secondary hover:text-brand-600'
                }`}
                onClick={() => handleNavClick(link.route)}
              >
                {link.name}
                {checkActive(link.route) && (
                  <motion.div 
                    layoutId="nav-active" 
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-brand-600 rounded-full"
                    transition={{ type: "spring", stiffness: 400, damping: 30 }}
                  />
                )}
              </button>
            ))}
          </nav>

          <div className="hidden lg:flex items-center gap-6">
            <button className="text-xs font-black text-text-muted hover:text-text-primary transition-colors uppercase tracking-widest">登录</button>
            <Button size="sm" className="px-6 h-10 font-black shadow-lg shadow-brand-600/20" onClick={() => handleNavClick({ type: 'pricing' })}>
               免费开始
            </Button>
          </div>

          <button className="lg:hidden p-2 text-text-primary" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
            {mobileMenuOpen ? <X /> : <Menu />}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="lg:hidden fixed inset-0 top-[72px] bg-white z-[60] p-8 flex flex-col gap-8 shadow-2xl"
          >
             {navLinks.map((link, idx) => (
                <button 
                  key={idx} 
                  className={`text-3xl font-black text-left tracking-tighter ${checkActive(link.route) ? 'text-brand-600' : 'text-text-primary'}`}
                  onClick={() => handleNavClick(link.route)}
                >
                  {link.name}
                </button>
             ))}
             <div className="mt-auto pt-8 border-t border-bg-100 flex flex-col gap-4">
                <Button className="w-full h-14 text-lg font-black" onClick={() => handleNavClick({ type: 'pricing' })}>免费开始</Button>
                <button className="w-full h-14 text-text-secondary font-bold">登录账号</button>
             </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
};

export default Navbar;