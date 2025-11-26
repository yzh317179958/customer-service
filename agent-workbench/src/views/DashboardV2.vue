<template>
  <div class="dashboard-v2">
    <!-- 侧边导航栏 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <img v-if="!sidebarCollapsed" src="/fiido2.png" alt="Fiido" class="logo" />
        <img v-else src="/fiido2.png" alt="F" class="logo-icon" />
      </div>

      <nav class="sidebar-nav">
        <div
          v-for="item in navItems"
          :key="item.key"
          class="nav-item"
          :class="{ active: currentView === item.key }"
          @click="currentView = item.key"
        >
          <component :is="item.icon" class="nav-icon" />
          <span v-if="!sidebarCollapsed" class="nav-label">{{ item.label }}</span>
          <span v-if="!sidebarCollapsed && item.badge" class="nav-badge">{{ item.badge }}</span>
        </div>
      </nav>

      <div class="sidebar-footer">
        <div class="agent-profile" :class="{ collapsed: sidebarCollapsed }">
          <div class="agent-avatar">{{ agentStore.agentName?.charAt(0) || 'A' }}</div>
          <div v-if="!sidebarCollapsed" class="agent-info">
            <div class="agent-name">{{ agentStore.agentName }}</div>
            <div class="agent-status">
              <span class="status-dot"></span>
              <span>在线</span>
            </div>
          </div>
        </div>
        <button class="collapse-btn" @click="sidebarCollapsed = !sidebarCollapsed">
          <ChevronLeft v-if="!sidebarCollapsed" />
          <ChevronRight v-else />
        </button>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <!-- 顶部栏 -->
      <header class="top-bar">
        <div class="top-bar-left">
          <h1 class="page-title">{{ currentPageTitle }}</h1>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>工作台</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentPageTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="top-bar-right">
          <!-- 搜索框 -->
          <div class="search-box">
            <el-input
              v-model="globalSearch"
              placeholder="搜索会话、工单、客户..."
              :prefix-icon="Search"
              clearable
            />
          </div>

          <!-- 通知 -->
          <el-badge :value="notificationCount" class="notification-badge">
            <button class="icon-btn">
              <Bell />
            </button>
          </el-badge>

          <!-- 设置 -->
          <el-dropdown trigger="click">
            <button class="icon-btn">
              <Settings />
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-if="agentStore.agentRole === 'admin'" @click="router.push('/admin/agents')">
                  <UserCog /> 坐席管理
                </el-dropdown-item>
                <el-dropdown-item @click="handleLogout">
                  <LogOut /> 退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- 内容视图 -->
      <div class="content-view">
        <!-- 会话工作台 -->
        <div v-if="currentView === 'sessions'" class="view-sessions">
          <SessionWorkbench />
        </div>

        <!-- 工单管理 -->
        <div v-else-if="currentView === 'tickets'" class="view-tickets">
          <div class="tickets-placeholder">
            <FileText />
            <p>工单管理功能</p>
            <small>UI重构中...</small>
            <el-button type="primary" @click="router.push('/tickets')" style="margin-top: 16px;">
              查看当前工单列表
            </el-button>
          </div>
        </div>

        <!-- 数据统计 -->
        <div v-else-if="currentView === 'statistics'" class="view-statistics">
          <StatisticsDashboard />
        </div>

        <!-- 知识库 -->
        <div v-else-if="currentView === 'knowledge'" class="view-knowledge">
          <KnowledgeBase />
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAgentStore } from '@/stores/agentStore'
import { useSessionStore } from '@/stores/sessionStore'
import {
  MessageSquare,
  FileText,
  BarChart3,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Search,
  Bell,
  Settings,
  UserCog,
  LogOut
} from 'lucide-vue-next'
import SessionWorkbench from '@/components/SessionWorkbench.vue'
import StatisticsDashboard from '@/components/StatisticsDashboard.vue'
import KnowledgeBase from '@/components/KnowledgeBase.vue'

const router = useRouter()
const agentStore = useAgentStore()
const sessionStore = useSessionStore()

// 侧边栏状态
const sidebarCollapsed = ref(false)

// 当前视图
const currentView = ref('sessions')

// 全局搜索
const globalSearch = ref('')

// 通知数量
const notificationCount = computed(() => sessionStore.pendingCount)

// 导航项
const navItems = [
  {
    key: 'sessions',
    label: '会话工作台',
    icon: MessageSquare,
    badge: computed(() => sessionStore.pendingCount > 0 ? sessionStore.pendingCount : null)
  },
  {
    key: 'tickets',
    label: '工单管理',
    icon: FileText,
    badge: null
  },
  {
    key: 'statistics',
    label: '数据统计',
    icon: BarChart3,
    badge: null
  },
  {
    key: 'knowledge',
    label: '知识库',
    icon: BookOpen,
    badge: null
  }
]

// 当前页面标题
const currentPageTitle = computed(() => {
  const item = navItems.find(i => i.key === currentView.value)
  return item?.label || '工作台'
})

// 退出登录
const handleLogout = () => {
  if (confirm('确定要退出登录吗？')) {
    agentStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped lang="scss">
@import '@/styles/design-system.scss';

.dashboard-v2 {
  display: flex;
  height: 100vh;
  background: $bg-secondary;
}

// ========== 侧边栏 ==========
.sidebar {
  width: $sidebar-width;
  height: 100%;
  background: $bg-sidebar;
  display: flex;
  flex-direction: column;
  transition: width $transition-base;
  flex-shrink: 0;

  &.collapsed {
    width: $sidebar-collapsed-width;
  }
}

.sidebar-header {
  height: $header-height;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: $spacing-4;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);

  .logo {
    height: 32px;
    width: auto;
    filter: brightness(0) invert(1);
  }

  .logo-icon {
    height: 32px;
    width: 32px;
    filter: brightness(0) invert(1);
  }
}

.sidebar-nav {
  flex: 1;
  padding: $spacing-4 $spacing-2;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: $spacing-3;
  padding: $spacing-3 $spacing-4;
  margin-bottom: $spacing-1;
  border-radius: $radius-md;
  color: $text-dark-secondary;
  cursor: pointer;
  transition: all $transition-base;
  position: relative;

  &:hover {
    background: $bg-dark-hover;
    color: $text-white;
  }

  &.active {
    background: $brand-primary;
    color: $text-white;

    .nav-icon {
      color: $text-white;
    }
  }

  .nav-icon {
    width: 20px;
    height: 20px;
    flex-shrink: 0;
    color: $text-dark-secondary;
    transition: color $transition-base;
  }

  .nav-label {
    flex: 1;
    font-size: $font-size-sm;
    font-weight: $font-weight-medium;
  }

  .nav-badge {
    min-width: 20px;
    height: 20px;
    padding: 0 $spacing-1;
    background: $color-error;
    color: $text-white;
    border-radius: $radius-full;
    font-size: $font-size-xs;
    font-weight: $font-weight-bold;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .collapsed & {
    justify-content: center;
    padding: $spacing-3;
  }
}

.sidebar-footer {
  padding: $spacing-4;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.agent-profile {
  display: flex;
  align-items: center;
  gap: $spacing-3;
  padding: $spacing-3;
  background: $bg-dark-hover;
  border-radius: $radius-md;
  margin-bottom: $spacing-2;

  &.collapsed {
    justify-content: center;
  }

  .agent-avatar {
    width: 36px;
    height: 36px;
    border-radius: $radius-full;
    background: $brand-primary;
    color: $text-white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: $font-weight-bold;
    font-size: $font-size-base;
    flex-shrink: 0;
  }

  .agent-info {
    flex: 1;
    min-width: 0;
  }

  .agent-name {
    font-size: $font-size-sm;
    font-weight: $font-weight-semibold;
    color: $text-white;
    @include text-ellipsis;
  }

  .agent-status {
    display: flex;
    align-items: center;
    gap: $spacing-1;
    font-size: $font-size-xs;
    color: $text-dark-secondary;
    margin-top: 2px;

    .status-dot {
      width: 6px;
      height: 6px;
      border-radius: $radius-full;
      background: $color-success;
      animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.collapse-btn {
  @include button-reset;
  width: 100%;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: $text-dark-secondary;
  background: transparent;
  border-radius: $radius-md;
  transition: all $transition-base;

  &:hover {
    background: $bg-dark-hover;
    color: $text-white;
  }

  svg {
    width: 20px;
    height: 20px;
  }
}

// ========== 主内容区 ==========
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.top-bar {
  height: $header-height;
  background: $bg-primary;
  border-bottom: 1px solid $border-light;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 $spacing-6;
  flex-shrink: 0;
}

.top-bar-left {
  display: flex;
  align-items: center;
  gap: $spacing-4;

  .page-title {
    font-size: $font-size-xl;
    font-weight: $font-weight-bold;
    color: $text-primary;
    margin: 0;
  }

  .el-breadcrumb {
    font-size: $font-size-sm;
  }
}

.top-bar-right {
  display: flex;
  align-items: center;
  gap: $spacing-3;

  .search-box {
    width: 320px;

    .el-input {
      --el-input-border-radius: #{$radius-md};
    }
  }

  .icon-btn {
    @include button-reset;
    width: 36px;
    height: 36px;
    border-radius: $radius-md;
    display: flex;
    align-items: center;
    justify-content: center;
    color: $text-secondary;
    transition: all $transition-base;

    &:hover {
      background: $bg-tertiary;
      color: $text-primary;
    }

    svg {
      width: 20px;
      height: 20px;
    }
  }

  .notification-badge {
    :deep(.el-badge__content) {
      background: $color-error;
      border: none;
    }
  }
}

.content-view {
  flex: 1;
  overflow: hidden;
  padding: $spacing-6;
}

.view-sessions,
.view-tickets,
.view-statistics,
.view-knowledge {
  height: 100%;
  background: $bg-primary;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
  overflow: hidden;
}

.tickets-placeholder {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: $text-tertiary;

  svg {
    width: 64px;
    height: 64px;
    margin-bottom: $spacing-4;
  }

  p {
    font-size: $font-size-lg;
    font-weight: $font-weight-semibold;
    margin-bottom: $spacing-2;
  }

  small {
    font-size: $font-size-sm;
  }
}
</style>
