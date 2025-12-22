
export enum SessionStatus {
  BOT_ACTIVE = '机器人接待',
  PENDING_MANUAL = '等待人工',
  MANUAL_LIVE = '人工对话中',
  CLOSED = '已结束'
}

export enum TicketStatus {
  OPEN = '待处理',
  PENDING = '处理中',
  RESOLVED = '已解决',
  CLOSED = '已关闭'
}

export interface Message {
  id: string;
  sender: 'customer' | 'agent' | 'system' | 'ai';
  text: string;
  timestamp: string;
  status?: 'sent' | 'delivered' | 'read';
}

export interface Customer {
  id: string;
  name: string;
  avatar: string;
  vip: boolean;
  email: string;
  phone: string;
  channel: '官网' | '微信' | 'App' | '电话' | '邮件';
  tags: string[];
  orderId?: string;
}

export interface Session {
  id: string;
  customer: Customer;
  lastMessage: string;
  time: string;
  unreadCount: number;
  status: SessionStatus;
  priority: '紧急' | '高' | '普通' | '低';
}

export interface Ticket {
  id: string;
  title: string;
  customerName: string;
  status: TicketStatus;
  priority: '紧急' | '高' | '中' | '低';
  assignee: string;
  createdAt: string;
  slaTimeRemaining: string;
}
