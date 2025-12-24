
import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
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
import LoginView from './components/LoginView';
import { useAuthStore } from './src/stores';

// 占位组件：功能开发中
const ComingSoon: React.FC = () => (
  <div className="flex flex-col items-center justify-center h-full text-slate-400 bg-white">
    <h2 className="text-2xl font-bold font-brand">功能开发中</h2>
    <p className="mt-2">该模块正在全力构建，即将上线。</p>
  </div>
);

const App: React.FC = () => {
  const [isSidebarCollapsed, setSidebarCollapsed] = useState(false);

  // 从 authStore 获取认证状态
  const { isAuthenticated, agent, status, logout } = useAuthStore();

  // 构建用户信息对象
  const currentUser = agent ? {
    name: agent.name || agent.username,
    role: agent.role === 'admin' ? '管理员' : agent.role === 'supervisor' ? '主管' : '坐席',
    status: status === 'online' ? '在线' : status === 'busy' ? '忙碌' : status === 'away' ? '离开' : '离线',
    avatar: agent.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${agent.username}`
  } : {
    name: '未登录',
    role: '',
    status: '离线',
    avatar: ''
  };

  const handleLogout = async () => {
    await logout();
  };

  // 未登录时显示登录页
  if (!isAuthenticated) {
    return <LoginView />;
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-100 font-sans text-slate-900 animate-in fade-in duration-1000">
      <Sidebar
        isCollapsed={isSidebarCollapsed}
        toggleCollapse={() => setSidebarCollapsed(!isSidebarCollapsed)}
      />

      <div className="flex flex-col flex-1 min-w-0 h-full">
        <Topbar user={currentUser} onLogout={handleLogout} />
        <main className="flex-1 overflow-hidden relative">
          <Routes>
            <Route path="/" element={<Navigate to="/workspace" replace />} />
            <Route path="/workspace" element={<Workspace />} />
            <Route path="/tickets" element={<TicketsView />} />
            <Route path="/knowledge" element={<KnowledgeBase />} />
            <Route path="/monitoring" element={<Monitoring />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/audit" element={<QualityAudit />} />
            <Route path="/billing" element={<BillingView />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<ComingSoon />} />
          </Routes>
        </main>
      </div>
    </div>
  );
};

export default App;
