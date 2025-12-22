/**
 * 认证状态 Store
 *
 * 管理：
 * - 登录状态 (isAuthenticated)
 * - 坐席信息 (agent)
 * - Token 存储
 * - 登录/登出操作
 * - 状态更新
 * - 心跳保活
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import {
  authApi,
  AgentInfo,
  AgentStatus,
  LoginRequest,
  TodayStats,
} from '../api';

// ============ 类型定义 ============

interface AuthState {
  // 状态
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // 坐席信息
  agent: AgentInfo | null;
  status: AgentStatus;
  statusNote: string;

  // 统计
  currentSessions: number;
  maxSessions: number;
  todayStats: TodayStats | null;

  // 心跳
  heartbeatInterval: number | null;
}

interface AuthActions {
  // 认证操作
  login: (data: LoginRequest) => Promise<boolean>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<boolean>;

  // 状态操作
  setStatus: (status: AgentStatus, note?: string) => Promise<void>;
  fetchProfile: () => Promise<void>;
  fetchStatus: () => Promise<void>;
  fetchTodayStats: () => Promise<void>;

  // 心跳
  startHeartbeat: () => void;
  stopHeartbeat: () => void;

  // 工具方法
  clearError: () => void;
  reset: () => void;
}

type AuthStore = AuthState & AuthActions;

// ============ 初始状态 ============

const initialState: AuthState = {
  isAuthenticated: false,
  isLoading: false,
  error: null,
  agent: null,
  status: 'offline',
  statusNote: '',
  currentSessions: 0,
  maxSessions: 10,
  todayStats: null,
  heartbeatInterval: null,
};

// ============ Store 实现 ============

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      ...initialState,

      /**
       * 登录
       */
      login: async (data: LoginRequest): Promise<boolean> => {
        set({ isLoading: true, error: null });

        try {
          const response = await authApi.login(data);

          set({
            isAuthenticated: true,
            isLoading: false,
            agent: response.agent,
            status: response.agent.status,
            statusNote: response.agent.status_note || '',
            error: null,
          });

          // 登录成功后启动心跳
          get().startHeartbeat();

          // 获取今日统计
          get().fetchTodayStats();

          return true;
        } catch (error: unknown) {
          const message = error instanceof Error ? error.message : '登录失败';
          set({
            isLoading: false,
            error: message,
            isAuthenticated: false,
          });
          return false;
        }
      },

      /**
       * 登出
       */
      logout: async (): Promise<void> => {
        const { agent, stopHeartbeat } = get();

        // 停止心跳
        stopHeartbeat();

        try {
          if (agent?.username) {
            await authApi.logout(agent.username);
          }
        } catch (error) {
          // 忽略登出错误，继续清理状态
          console.warn('Logout API failed:', error);
        }

        // 重置状态
        set({
          ...initialState,
          isAuthenticated: false,
        });
      },

      /**
       * 刷新 Token
       */
      refreshToken: async (): Promise<boolean> => {
        const refreshToken = localStorage.getItem('agent_refresh_token');
        if (!refreshToken) {
          return false;
        }

        try {
          await authApi.refreshToken({ refresh_token: refreshToken });
          return true;
        } catch (error) {
          console.error('Token refresh failed:', error);
          // 刷新失败，执行登出
          get().logout();
          return false;
        }
      },

      /**
       * 更新坐席状态
       */
      setStatus: async (status: AgentStatus, note?: string): Promise<void> => {
        set({ isLoading: true });

        try {
          const response = await authApi.updateStatus({
            status,
            status_note: note,
          });

          set({
            isLoading: false,
            status: response.status,
            statusNote: response.status_note || '',
            currentSessions: response.current_sessions,
            maxSessions: response.max_sessions,
            todayStats: response.today_stats,
          });
        } catch (error: unknown) {
          const message = error instanceof Error ? error.message : '状态更新失败';
          set({ isLoading: false, error: message });
        }
      },

      /**
       * 获取坐席信息
       */
      fetchProfile: async (): Promise<void> => {
        const { agent } = get();
        if (!agent?.username) return;

        try {
          const response = await authApi.getProfile(agent.username);
          set({
            agent: response.agent,
            status: response.agent.status,
            statusNote: response.agent.status_note || '',
          });
        } catch (error) {
          console.error('Fetch profile failed:', error);
        }
      },

      /**
       * 获取坐席状态
       */
      fetchStatus: async (): Promise<void> => {
        try {
          const response = await authApi.getStatus();
          set({
            status: response.status,
            statusNote: response.status_note || '',
            currentSessions: response.current_sessions,
            maxSessions: response.max_sessions,
            todayStats: response.today_stats,
          });
        } catch (error) {
          console.error('Fetch status failed:', error);
        }
      },

      /**
       * 获取今日统计
       */
      fetchTodayStats: async (): Promise<void> => {
        try {
          const response = await authApi.getTodayStats();
          set({
            currentSessions: response.current_sessions,
            maxSessions: response.max_sessions,
            todayStats: {
              sessions_handled: response.sessions_handled,
              messages_sent: response.messages_sent,
              avg_response_time: response.avg_response_time,
              satisfaction_score: response.satisfaction_score,
            },
          });
        } catch (error) {
          console.error('Fetch today stats failed:', error);
        }
      },

      /**
       * 启动心跳
       */
      startHeartbeat: (): void => {
        const { heartbeatInterval } = get();

        // 避免重复启动
        if (heartbeatInterval) return;

        const interval = window.setInterval(async () => {
          try {
            await authApi.heartbeat();
          } catch (error) {
            console.warn('Heartbeat failed:', error);
          }
        }, 30000); // 30秒一次

        set({ heartbeatInterval: interval });
      },

      /**
       * 停止心跳
       */
      stopHeartbeat: (): void => {
        const { heartbeatInterval } = get();
        if (heartbeatInterval) {
          window.clearInterval(heartbeatInterval);
          set({ heartbeatInterval: null });
        }
      },

      /**
       * 清除错误
       */
      clearError: (): void => {
        set({ error: null });
      },

      /**
       * 重置状态
       */
      reset: (): void => {
        get().stopHeartbeat();
        set(initialState);
      },
    }),
    {
      name: 'auth-storage',
      // 只持久化关键状态
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        agent: state.agent,
        status: state.status,
        statusNote: state.statusNote,
      }),
    }
  )
);

// ============ 监听登出事件 ============

// 监听 401 事件，自动登出
if (typeof window !== 'undefined') {
  window.addEventListener('auth:logout', () => {
    useAuthStore.getState().logout();
  });
}

// ============ 选择器 ============

export const selectIsAuthenticated = (state: AuthStore) => state.isAuthenticated;
export const selectAgent = (state: AuthStore) => state.agent;
export const selectStatus = (state: AuthStore) => state.status;
export const selectIsLoading = (state: AuthStore) => state.isLoading;
export const selectError = (state: AuthStore) => state.error;
export const selectTodayStats = (state: AuthStore) => state.todayStats;

export default useAuthStore;
