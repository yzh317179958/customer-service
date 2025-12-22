/**
 * 工单状态 Store
 *
 * 管理：
 * - 工单列表
 * - 当前选中工单
 * - 工单筛选
 * - SLA 仪表盘
 * - 批量操作
 */

import { create } from 'zustand';
import {
  ticketsApi,
  TicketInfo,
  TicketStatus,
  TicketPriority,
  TicketFilters,
  TicketComment,
  SLADashboard,
  SLASummary,
} from '../api';

// ============ 类型定义 ============

interface TicketState {
  // 列表数据
  tickets: TicketInfo[];
  total: number;
  hasMore: boolean;

  // 当前选中
  currentTicket: TicketInfo | null;
  currentComments: TicketComment[];

  // SLA
  slaDashboard: SLADashboard | null;
  slaSummary: SLASummary | null;

  // 加载状态
  isLoading: boolean;
  isLoadingDetail: boolean;
  error: string | null;

  // 筛选条件
  filters: TicketFilters;

  // 视图模式
  viewMode: 'list' | 'kanban';

  // 批量选中
  selectedIds: string[];
}

interface TicketActions {
  // 列表操作
  fetchTickets: (append?: boolean) => Promise<void>;
  searchTickets: (query: string) => Promise<void>;
  refreshTickets: () => Promise<void>;

  // 工单操作
  selectTicket: (ticketId: string) => Promise<void>;
  clearCurrentTicket: () => void;
  createTicket: (data: Parameters<typeof ticketsApi.create>[0]) => Promise<TicketInfo | null>;
  updateTicket: (ticketId: string, data: Parameters<typeof ticketsApi.update>[1]) => Promise<boolean>;
  assignTicket: (ticketId: string, agentId: string, agentName?: string) => Promise<boolean>;

  // 批量操作
  batchAssign: (agentId: string, agentName?: string, note?: string) => Promise<boolean>;
  batchClose: (reason?: string) => Promise<boolean>;
  batchPriority: (priority: TicketPriority, reason?: string) => Promise<boolean>;

  // 评论操作
  fetchComments: (ticketId: string) => Promise<void>;
  addComment: (ticketId: string, content: string, commentType?: 'internal' | 'external') => Promise<boolean>;

  // SLA
  fetchSLADashboard: () => Promise<void>;
  fetchSLASummary: () => Promise<void>;

  // 筛选
  setFilters: (filters: Partial<TicketFilters>) => void;
  clearFilters: () => void;

  // 视图
  setViewMode: (mode: 'list' | 'kanban') => void;

  // 批量选择
  toggleSelect: (ticketId: string) => void;
  selectAll: () => void;
  clearSelection: () => void;

  // 工具方法
  updateTicketInList: (ticket: TicketInfo) => void;
  removeTicketFromList: (ticketId: string) => void;
  clearError: () => void;
  reset: () => void;
}

type TicketStore = TicketState & TicketActions;

// ============ 初始状态 ============

const defaultFilters: TicketFilters = {
  limit: 50,
  offset: 0,
  sort_by: 'updated_at',
  sort_desc: true,
};

const initialState: TicketState = {
  tickets: [],
  total: 0,
  hasMore: false,
  currentTicket: null,
  currentComments: [],
  slaDashboard: null,
  slaSummary: null,
  isLoading: false,
  isLoadingDetail: false,
  error: null,
  filters: { ...defaultFilters },
  viewMode: 'list',
  selectedIds: [],
};

// ============ Store 实现 ============

export const useTicketStore = create<TicketStore>((set, get) => ({
  ...initialState,

  /**
   * 获取工单列表
   */
  fetchTickets: async (append = false): Promise<void> => {
    const { filters, tickets } = get();

    set({ isLoading: true, error: null });

    try {
      const response = await ticketsApi.filter({
        ...filters,
        offset: append ? tickets.length : 0,
      });

      set({
        tickets: append ? [...tickets, ...response.tickets] : response.tickets,
        total: response.total,
        hasMore: response.has_more,
        isLoading: false,
        filters: {
          ...filters,
          offset: append ? tickets.length : 0,
        },
      });
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : '获取工单列表失败';
      set({ isLoading: false, error: message });
    }
  },

  /**
   * 搜索工单
   */
  searchTickets: async (query: string): Promise<void> => {
    set({ isLoading: true, error: null });

    try {
      const response = await ticketsApi.search(query);
      set({
        tickets: response.tickets,
        total: response.total,
        hasMore: response.has_more,
        isLoading: false,
      });
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : '搜索工单失败';
      set({ isLoading: false, error: message });
    }
  },

  /**
   * 刷新工单列表
   */
  refreshTickets: async (): Promise<void> => {
    set({ filters: { ...get().filters, offset: 0 } });
    await get().fetchTickets(false);
  },

  /**
   * 选中工单
   */
  selectTicket: async (ticketId: string): Promise<void> => {
    set({ isLoadingDetail: true, error: null });

    try {
      const ticket = await ticketsApi.getDetail(ticketId);
      set({
        currentTicket: ticket,
        isLoadingDetail: false,
      });

      // 获取评论
      get().fetchComments(ticketId);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : '获取工单详情失败';
      set({ isLoadingDetail: false, error: message });
    }
  },

  /**
   * 清除当前工单
   */
  clearCurrentTicket: (): void => {
    set({
      currentTicket: null,
      currentComments: [],
    });
  },

  /**
   * 创建工单
   */
  createTicket: async (data): Promise<TicketInfo | null> => {
    set({ isLoading: true, error: null });

    try {
      const ticket = await ticketsApi.create(data);

      // 添加到列表头部
      set((state) => ({
        tickets: [ticket, ...state.tickets],
        total: state.total + 1,
        isLoading: false,
      }));

      return ticket;
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : '创建工单失败';
      set({ isLoading: false, error: message });
      return null;
    }
  },

  /**
   * 更新工单
   */
  updateTicket: async (ticketId, data): Promise<boolean> => {
    set({ isLoading: true, error: null });

    try {
      const ticket = await ticketsApi.update(ticketId, data);

      // 更新列表和当前选中
      get().updateTicketInList(ticket);
      if (get().currentTicket?.ticket_id === ticketId) {
        set({ currentTicket: ticket });
      }

      set({ isLoading: false });
      return true;
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : '更新工单失败';
      set({ isLoading: false, error: message });
      return false;
    }
  },

  /**
   * 分配工单
   */
  assignTicket: async (ticketId, agentId, agentName): Promise<boolean> => {
    set({ isLoading: true, error: null });

    try {
      const ticket = await ticketsApi.assign(ticketId, {
        agent_id: agentId,
        agent_name: agentName,
      });

      get().updateTicketInList(ticket);
      if (get().currentTicket?.ticket_id === ticketId) {
        set({ currentTicket: ticket });
      }

      set({ isLoading: false });
      return true;
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : '分配工单失败';
      set({ isLoading: false, error: message });
      return false;
    }
  },

  /**
   * 批量分配
   */
  batchAssign: async (agentId, agentName, note): Promise<boolean> => {
    const { selectedIds } = get();
    if (selectedIds.length === 0) return false;

    set({ isLoading: true, error: null });

    try {
      const result = await ticketsApi.batchAssign({
        ticket_ids: selectedIds,
        target_agent_id: agentId,
        target_agent_name: agentName,
        note,
      });

      // 更新列表中的工单
      result.tickets.forEach((ticket) => {
        get().updateTicketInList(ticket);
      });

      set({ isLoading: false, selectedIds: [] });
      return true;
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : '批量分配失败';
      set({ isLoading: false, error: message });
      return false;
    }
  },

  /**
   * 批量关闭
   */
  batchClose: async (reason): Promise<boolean> => {
    const { selectedIds } = get();
    if (selectedIds.length === 0) return false;

    set({ isLoading: true, error: null });

    try {
      const result = await ticketsApi.batchClose({
        ticket_ids: selectedIds,
        close_reason: reason,
      });

      // 更新列表中的工单
      result.tickets.forEach((ticket) => {
        get().updateTicketInList(ticket);
      });

      set({ isLoading: false, selectedIds: [] });
      return true;
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : '批量关闭失败';
      set({ isLoading: false, error: message });
      return false;
    }
  },

  /**
   * 批量更新优先级
   */
  batchPriority: async (priority, reason): Promise<boolean> => {
    const { selectedIds } = get();
    if (selectedIds.length === 0) return false;

    set({ isLoading: true, error: null });

    try {
      const result = await ticketsApi.batchPriority({
        ticket_ids: selectedIds,
        priority,
        reason,
      });

      // 更新列表中的工单
      result.tickets.forEach((ticket) => {
        get().updateTicketInList(ticket);
      });

      set({ isLoading: false, selectedIds: [] });
      return true;
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : '批量更新优先级失败';
      set({ isLoading: false, error: message });
      return false;
    }
  },

  /**
   * 获取评论
   */
  fetchComments: async (ticketId: string): Promise<void> => {
    try {
      const comments = await ticketsApi.getComments(ticketId);
      set({ currentComments: comments });
    } catch (error) {
      console.error('Fetch comments failed:', error);
    }
  },

  /**
   * 添加评论
   */
  addComment: async (ticketId, content, commentType = 'internal'): Promise<boolean> => {
    try {
      const comment = await ticketsApi.addComment(ticketId, {
        content,
        comment_type: commentType,
      });

      set((state) => ({
        currentComments: [...state.currentComments, comment],
      }));

      return true;
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : '添加评论失败';
      set({ error: message });
      return false;
    }
  },

  /**
   * 获取 SLA 仪表盘
   */
  fetchSLADashboard: async (): Promise<void> => {
    try {
      const dashboard = await ticketsApi.getSLADashboard();
      set({ slaDashboard: dashboard });
    } catch (error) {
      console.error('Fetch SLA dashboard failed:', error);
    }
  },

  /**
   * 获取 SLA 摘要
   */
  fetchSLASummary: async (): Promise<void> => {
    try {
      const summary = await ticketsApi.getSLASummary();
      set({ slaSummary: summary });
    } catch (error) {
      console.error('Fetch SLA summary failed:', error);
    }
  },

  /**
   * 设置筛选条件
   */
  setFilters: (newFilters: Partial<TicketFilters>): void => {
    set((state) => ({
      filters: {
        ...state.filters,
        ...newFilters,
        offset: 0, // 重置分页
      },
    }));
    get().fetchTickets(false);
  },

  /**
   * 清除筛选条件
   */
  clearFilters: (): void => {
    set({ filters: { ...defaultFilters } });
    get().fetchTickets(false);
  },

  /**
   * 设置视图模式
   */
  setViewMode: (mode: 'list' | 'kanban'): void => {
    set({ viewMode: mode });
  },

  /**
   * 切换选择
   */
  toggleSelect: (ticketId: string): void => {
    set((state) => ({
      selectedIds: state.selectedIds.includes(ticketId)
        ? state.selectedIds.filter((id) => id !== ticketId)
        : [...state.selectedIds, ticketId],
    }));
  },

  /**
   * 全选
   */
  selectAll: (): void => {
    set((state) => ({
      selectedIds: state.tickets.map((t) => t.ticket_id),
    }));
  },

  /**
   * 清除选择
   */
  clearSelection: (): void => {
    set({ selectedIds: [] });
  },

  /**
   * 更新列表中的工单
   */
  updateTicketInList: (ticket: TicketInfo): void => {
    set((state) => ({
      tickets: state.tickets.map((t) =>
        t.ticket_id === ticket.ticket_id ? ticket : t
      ),
    }));
  },

  /**
   * 从列表移除工单
   */
  removeTicketFromList: (ticketId: string): void => {
    set((state) => ({
      tickets: state.tickets.filter((t) => t.ticket_id !== ticketId),
      total: state.total - 1,
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
    set(initialState);
  },
}));

// ============ 选择器 ============

export const selectTickets = (state: TicketStore) => state.tickets;
export const selectCurrentTicket = (state: TicketStore) => state.currentTicket;
export const selectCurrentComments = (state: TicketStore) => state.currentComments;
export const selectFilters = (state: TicketStore) => state.filters;
export const selectSLADashboard = (state: TicketStore) => state.slaDashboard;
export const selectIsLoading = (state: TicketStore) => state.isLoading;
export const selectError = (state: TicketStore) => state.error;
export const selectSelectedIds = (state: TicketStore) => state.selectedIds;
export const selectViewMode = (state: TicketStore) => state.viewMode;

export default useTicketStore;
