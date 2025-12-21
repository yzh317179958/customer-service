
import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Topbar from './components/Topbar';
import Workspace from './components/Workspace';
import TicketsView from './components/TicketsView';
import Dashboard from './components/Dashboard';
import KnowledgeBase from './components/KnowledgeBase';
import Monitoring from './components/Monitoring';
import QualityAudit from './components/QualityAudit';
import Settings from './components/Settings';
import BillingView from './components/BillingView';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('workspace');
  const [isSidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [currentUser] = useState({
    name: '李建国',
    role: '高级服务主管',
    status: '在线',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Staff_Li'
  });

  const renderContent = () => {
    switch (activeTab) {
      case 'workspace':
        return <Workspace />;
      case 'tickets':
        return <TicketsView />;
      case 'dashboard':
        return <Dashboard />;
      case 'knowledge':
        return <KnowledgeBase />;
      case 'monitoring':
        return <Monitoring />;
      case 'audit':
        return <QualityAudit />;
      case 'billing':
        return <BillingView />;
      case 'settings':
        return <Settings />;
      default:
        return (
          <div className="flex flex-col items-center justify-center h-full text-slate-400 bg-white">
            <h2 className="text-2xl font-bold font-brand">功能开发中</h2>
            <p className="mt-2">该模块正在全力构建，即将上线。</p>
          </div>
        );
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-100 font-sans text-slate-900">
      <Sidebar 
        activeTab={activeTab} 
        onTabChange={setActiveTab} 
        isCollapsed={isSidebarCollapsed}
        toggleCollapse={() => setSidebarCollapsed(!isSidebarCollapsed)}
      />
      
      <div className="flex flex-col flex-1 min-w-0 h-full">
        <Topbar user={currentUser} />
        <main className="flex-1 overflow-hidden relative">
          {renderContent()}
        </main>
      </div>
    </div>
  );
};

export default App;
