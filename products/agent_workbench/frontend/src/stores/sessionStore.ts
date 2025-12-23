/**
 * 会话状态 Store
 *
 * 管理：
 * - 会话列表
 * - 待接入队列
 * - 当前选中会话
 * - 会话统计
 * - SSE 事件订阅
 */

import { create } from 'zustand';
import {
  sessionsApi,
  SessionInfo,
  SessionStats,
  QueueItem,
  MessageInfo,
  SessionStatus,
} from '../api';
import { useAuthStore } from './authStore';

// ============ 类型定义 ============

interface SessionState {
  // 列表数据
  sessions: SessionInfo[];
  queue: QueueItem[];
  total: number;
  queueTotal: number;

  // 当前选中
  currentSession: SessionInfo | null;
  currentMessages: MessageInfo[];

  // 统计
  stats: SessionStats | null;

  // 加载状态
  isLoading: boolean;
  isLoadingMessages: boolean;
  error: string | null;

  // SSE
  eventSource: EventSource | null;

  // 筛选
  statusFilter: SessionStatus | null;
}

interface SessionActions {
  // 列表操作
  fetchSessions: (status?: SessionStatus) => Promise<void>;
  fetchQueue: () => Promise<void>;
  fetchStats: () => Promise<void>;

  // 会话操作
  selectSession: (sessionName: string) => Promise<void>;
  clearCurrentSession: () => void;
  takeover: (sessionName: string) => Promise<boolean>;
  release: (sessionName: string) => Promise<boolean>;
  transfer: (sessionName: string, targetAgentId: string, reason?: string) => Promise<boolean>;

  // 消息操作
  sendMessage: (content: string, messageType?: 'text' | 'image' | 'file') => Promise<boolean>;
  addNote: (content: string) => Promise<boolean>;

  // SSE 订阅
  subscribeToSession: (sessionName: string) => void;
  unsubscribeFromSession: () => void;

  // 工具方法
  setStatusFilter: (status: SessionStatus | null) => void;
  updateSessionInList: (session: SessionInfo) => void;
  addMessageToCurrentSession: (message: MessageInfo) => void;
  clearError: () => void;
  reset: () => void;
}

type SessionStore = SessionState & SessionActions;

// ============ 初始状态 ============

const initialState: SessionState = {
  sessions: [],
  queue: [],
  total: 0,
  queueTotal: 0,
  currentSession: null,
  currentMessages: [],
  stats: null,
  isLoading: false,
  isLoadingMessages: false,
  error: null,
  eventSource: null,
  statusFilter: null,
};

// ============ Store 实现 ============

export const useSessionStore = create<SessionStore>((set, get) => ({
  ...initialState,

  /**
   * 获取会话列表
   */
  fetchSessions: async (status?: SessionStatus): Promise<void> => {
    set({ isLoading: true, error: null });

    try {
      const response = await sessionsApi.getList({
        status: status || get().statusFilter || undefined,
      });

      // 适配后端返回格式: { success, data: { items, total, page, page_size } }
      const data = (response as any).data || response;
      const sessions = data.items || data.sessions || [];
      const total = data.total || 0;

      set({
        sessions,
        total,
        isLoading: false,
      });
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : '获取会话列表失败';
      set({ isLoading: false, error: message });
    }
  },

  /**
   * 获取待接入队列
   */
  fetchQueue: async (): Promise<void> => {
    try {
      const response = await sessionsApi.getQueue();

      // 适配后端返回格式: { success, data: { queue, total_count, ... } }
      const data = (response as any).data || response;
      const queue = data.queue || [];
      const total = data.total_count || data.total || 0;

      set({
        queue,
        queueTotal: total,
      });
    } catch (error: unknown) {
      console.error('Fetch queue failed:', error);
    }
  },

  /**
   * 获取会话统计
   */
  fetchStats: async (): Promise<void> => {
    try {
      const stats = await sessionsApi.getStats();
      set({ stats });
    } catch (error: unknown) {
      console.error('Fetch stats failed:', error);
    }
  },

  /**
   * 选中会话
   */
  selectSession: async (sessionName: string): Promise<void> => {
    set({ isLoadingMessages: true, error: null });

    try {
      const session = await sessionsApi.getSession(sessionName);
      set({
        currentSession: session,
        currentMessages: [], // 消息从 SSE 获取
        isLoadingMessages: false,
      });

      // 订阅 SSE 事件
      get().subscribeToSession(sessionName);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : '获取会话详情失败';
      set({ isLoadingMessages: false, error: message });
    }
  },

  /**
   * 清除当前会话
   */
  clearCurrentSession: (): void => {
    get().unsubscribeFromSession();
    set({
      currentSession: null,
      currentMessages: [],
    });
  },

  /**
   * 接管会话
   */
  takeover: async (sessionName: string): Promise<boolean> => {
    set({ isLoading: true, error: null });

    // 从 authStore 获取当前坐席信息
    const agent = useAuthStore.getState().agent;
    if (!agent) {
      set({ isLoading: false, error: '未登录，请先登录' });
      return false;
    }

    try {
      const session = await sessionsApi.takeover(sessionName, {
        agent_id: agent.id,
        agent_name: agent.name,
      });

      // 更新列表中的会话状态
      get().updateSessionInList(session);

      // 从队列中移除
      set((state) => ({
        queue: state.queue.filter((q) => q.session_name !== sessionName),
        queueTotal: state.queueTotal - 1,
        isLoading: false,
      }));

      // 选中该会话
      await get().selectSession(sessionName);

      return true;
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : '接管会话失败';
      set({ isLoading: false, error: message });
      return false;
    }
  },

  /**
   * 释放会话
   */
  release: async (sessionName: string): Promise<boolean> => {
    set({ isLoading: true, error: null });

    // 从 authStore 获取当前坐席信息
    const agent = useAuthStore.getState().agent;
    if (!agent) {
      set({ isLoading: false, error: '未登录，请先登录' });
      return false;
    }

    try {
      await sessionsApi.release(sessionName, {
        agent_id: agent.id,
        reason: 'resolved',
      });

      // 从列表移除或更新状态
      set((state) => ({
        sessions: state.sessions.filter((s) => s.session_name !== sessionName),
        total: state.total - 1,
        isLoading: false,
      }));

      // 如果是当前会话，清除选中
      if (get().currentSession?.session_name === sessionName) {
        get().clearCurrentSession();
      }

      return true;
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : '释放会话失败';
      set({ isLoading: false, error: message });
      return false;
    }
  },

  /**
   * 转接会话
   */
  transfer: async (sessionName: string, targetAgentId: string, reason?: string): Promise<boolean> => {
    set({ isLoading: true, error: null });

    try {
      await sessionsApi.transfer(sessionName, {
        target_agent_id: targetAgentId,
        reason,
      });

      // 从列表移除
      set((state) => ({
        sessions: state.sessions.filter((s) => s.session_name !== sessionName),
        total: state.total - 1,
        isLoading: false,
      }));

      // 如果是当前会话，清除选中
      if (get().currentSession?.session_name === sessionName) {
        get().clearCurrentSession();
      }

      return true;
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : '转接会话失败';
      set({ isLoading: false, error: message });
      return false;
    }
  },

  /**
   * 发送消息
   */
  sendMessage: async (content: string, messageType: 'text' | 'image' | 'file' = 'text'): Promise<boolean> => {
    const { currentSession } = get();
    if (!currentSession) return false;

    try {
      const message = await sessionsApi.sendMessage(currentSession.session_name, {
        content,
        message_type: messageType,
      });

      // 添加到消息列表
      get().addMessageToCurrentSession(message);

      return true;
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : '发送消息失败';
      set({ error: message });
      return false;
    }
  },

  /**
   * 添加备注
   */
  addNote: async (content: string): Promise<boolean> => {
    const { currentSession } = get();
    if (!currentSession) return false;

    try {
      await sessionsApi.addNote(currentSession.session_name, { content });
      return true;
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : '添加备注失败';
      set({ error: message });
      return false;
    }
  },

  /**
   * 订阅会话 SSE 事件
   */
  subscribeToSession: (sessionName: string): void => {
    // 先取消之前的订阅
    get().unsubscribeFromSession();

    const eventSource = sessionsApi.subscribeEvents(
      sessionName,
      (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);

          switch (data.type) {
            case 'message':
              get().addMessageToCurrentSession(data.message);
              break;
            case 'manual_message':
              // 处理人工消息（来自 AI 客服用户或坐席）
              get().addMessageToCurrentSession({
                role: data.role,
                content: data.content,
                timestamp: data.timestamp,
                agent_id: data.agent_id,
                agent_name: data.agent_name,
                message_type: data.message_type,
              });
              break;
            case 'session_update':
              if (data.session) {
                set({ currentSession: data.session });
                get().updateSessionInList(data.session);
              }
              break;
            case 'status_change':
              // 处理会话状态变化，刷新会话列表
              console.log('Session status changed:', data.status);
              get().refreshSessions();
              break;
            case 'history':
              // 初始消息历史
              if (Array.isArray(data.messages)) {
                set({ currentMessages: data.messages });
              }
              break;
            case 'connected':
            case 'heartbeat':
              // 连接和心跳事件，忽略
              break;
            default:
              console.log('Unknown SSE event:', data.type);
          }
        } catch (error) {
          console.error('Parse SSE event failed:', error);
        }
      },
      (error: Event) => {
        console.error('SSE error:', error);
        // 可以尝试重连
      }
    );

    set({ eventSource });
  },

  /**
   * 取消 SSE 订阅
   */
  unsubscribeFromSession: (): void => {
    const { eventSource } = get();
    if (eventSource) {
      eventSource.close();
      set({ eventSource: null });
    }
  },

  /**
   * 设置状态筛选
   */
  setStatusFilter: (status: SessionStatus | null): void => {
    set({ statusFilter: status });
    get().fetchSessions(status || undefined);
  },

  /**
   * 更新列表中的会话
   */
  updateSessionInList: (session: SessionInfo): void => {
    set((state) => ({
      sessions: state.sessions.map((s) =>
        s.session_name === session.session_name ? session : s
      ),
    }));
  },

  /**
   * 添加消息到当前会话
   */
  addMessageToCurrentSession: (message: MessageInfo): void => {
    set((state) => ({
      currentMessages: [...state.currentMessages, message],
    }));
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
    get().unsubscribeFromSession();
    set(initialState);
  },
}));

// ============ 选择器 ============

export const selectSessions = (state: SessionStore) => state.sessions;
export const selectQueue = (state: SessionStore) => state.queue;
export const selectCurrentSession = (state: SessionStore) => state.currentSession;
export const selectCurrentMessages = (state: SessionStore) => state.currentMessages;
export const selectStats = (state: SessionStore) => state.stats;
export const selectIsLoading = (state: SessionStore) => state.isLoading;
export const selectError = (state: SessionStore) => state.error;

export default useSessionStore;
