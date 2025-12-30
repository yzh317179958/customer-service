import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Home from './pages/Home';
import ProductDetail from './pages/ProductDetail';
import CasesPage from './pages/CasesPage';
import PricingPage from './pages/PricingPage';
import SolutionDetail from './pages/SolutionDetail';
import Roadmap from './pages/Roadmap';

export type PageRoute = 
  | { type: 'home' }
  | { type: 'product'; id: string }
  | { type: 'cases' }
  | { type: 'pricing' }
  | { type: 'solution'; id: string }
  | { type: 'roadmap' };

const App: React.FC = () => {
  const [route, setRoute] = useState<PageRoute>({ type: 'home' });

  const navigate = (newRoute: PageRoute) => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setRoute(newRoute);
  };

  const renderPage = () => {
    switch (route.type) {
      case 'home':
        return <Home navigate={navigate} />;
      case 'product':
        return <ProductDetail id={route.id} navigate={navigate} />;
      case 'cases':
        return <CasesPage navigate={navigate} />;
      case 'pricing':
        return <PricingPage navigate={navigate} />;
      case 'solution':
        return <SolutionDetail id={route.id} navigate={navigate} />;
      case 'roadmap':
        return <Roadmap navigate={navigate} />;
      default:
        return <Home navigate={navigate} />;
    }
  };

  return (
    <div className="min-h-screen flex flex-col overflow-x-hidden bg-bg-50 font-sans text-text-primary selection:bg-brand-500/30 selection:text-brand-900">
      <Navbar onNavigate={navigate} currentRoute={route} />
      
      <main className="flex-grow relative z-10">
        <AnimatePresence mode="wait">
          <motion.div
            key={JSON.stringify(route)}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
          >
            {renderPage()}
          </motion.div>
        </AnimatePresence>
      </main>

      <Footer onNavigate={navigate} />
    </div>
  );
};

export default App;