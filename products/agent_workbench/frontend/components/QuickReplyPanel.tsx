/**
 * 快捷回复面板组件
 *
 * 功能：
 * - 展示快捷回复列表（支持分类筛选）
 * - 关键词搜索
 * - 点击快捷回复插入到输入框
 * - 支持变量替换
 */

import React, { useState, useEffect, useRef } from 'react';
import { Search, Zap, X, Hash, Loader2, MessageSquare } from 'lucide-react';
import { quickRepliesApi, QuickReply, QuickReplyCategory } from '../src/api';

// 分类标签中文映射
const CATEGORY_LABELS: Record<QuickReplyCategory, string> = {
  greeting: '问候语',
  farewell: '结束语',
  apology: '道歉',
  shipping: '物流',
  refund: '退款',
  product: '产品',
  technical: '技术',
  custom: '自定义',
};

interface QuickReplyPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (content: string) => void;
  sessionContext?: {
    session_name?: string;
    customer_name?: string;
    customer_email?: string;
  };
  agentContext?: {
    agent_name?: string;
    agent_id?: string;
  };
}

const QuickReplyPanel: React.FC<QuickReplyPanelProps> = ({
  isOpen,
  onClose,
  onSelect,
  sessionContext,
  agentContext,
}) => {
  const [replies, setReplies] = useState<QuickReply[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [activeCategory, setActiveCategory] = useState<QuickReplyCategory | 'all'>('all');
  const [error, setError] = useState<string | null>(null);

  const panelRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // 加载快捷回复列表
  const fetchReplies = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params: any = {
        include_shared: true,
        limit: 100,
      };
      if (activeCategory !== 'all') {
        params.category = activeCategory;
      }
      if (searchKeyword.trim()) {
        params.keyword = searchKeyword.trim();
      }
      const result = await quickRepliesApi.getList(params);
      setReplies(result.items || []);
    } catch (err: any) {
      console.error('加载快捷回复失败:', err);
      setError('加载失败，请重试');
      setReplies([]);
    } finally {
      setIsLoading(false);
    }
  };

  // 打开面板时加载数据并聚焦搜索框
  useEffect(() => {
    if (isOpen) {
      fetchReplies();
      // 延迟聚焦搜索框
      setTimeout(() => {
        searchInputRef.current?.focus();
      }, 100);
    }
  }, [isOpen]);

  // 分类或搜索变化时重新加载
  useEffect(() => {
    if (isOpen) {
      const timer = setTimeout(() => {
        fetchReplies();
      }, 300); // 防抖
      return () => clearTimeout(timer);
    }
  }, [activeCategory, searchKeyword]);

  // 点击外部关闭
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  // ESC 键关闭
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  // 选择快捷回复（调用 use API 进行变量替换）
  const handleSelectReply = async (reply: QuickReply) => {
    try {
      // 调用 use API 进行变量替换
      const result = await quickRepliesApi.use(reply.id, {
        session_data: sessionContext,
        agent_data: agentContext,
      });
      onSelect(result.replaced_content);
      onClose();
    } catch (err: any) {
      console.error('使用快捷回复失败:', err);
      // 降级：直接使用原始内容
      onSelect(reply.content);
      onClose();
    }
  };

  if (!isOpen) return null;

  // 可用分类列表
  const categories: (QuickReplyCategory | 'all')[] = [
    'all', 'greeting', 'farewell', 'shipping', 'refund', 'product', 'technical', 'custom'
  ];

  return (
    <div
      ref={panelRef}
      className="absolute bottom-full left-0 right-0 mb-2 bg-white rounded-xl shadow-2xl border border-slate-200 overflow-hidden z-50 animate-in fade-in slide-in-from-bottom-2 duration-200"
      style={{ maxHeight: '400px' }}
    >
      {/* 头部 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 bg-slate-50/50">
        <div className="flex items-center gap-2">
          <Zap size={16} className="text-fiido" />
          <span className="text-[12px] font-black text-slate-700 uppercase tracking-wider">快捷回复</span>
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-slate-200 rounded text-slate-400 hover:text-slate-600 transition-colors"
        >
          <X size={16} />
        </button>
      </div>

      {/* 搜索框 */}
      <div className="px-4 py-2 border-b border-slate-100">
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            ref={searchInputRef}
            type="text"
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            placeholder="搜索快捷回复..."
            className="w-full pl-9 pr-4 py-2 text-[12px] bg-slate-50 border border-slate-200 rounded-lg outline-none focus:border-fiido focus:ring-2 focus:ring-fiido/10 transition-all"
          />
        </div>
      </div>

      {/* 分类 Tab */}
      <div className="flex gap-1 px-4 py-2 border-b border-slate-100 overflow-x-auto no-scrollbar">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`px-3 py-1 text-[10px] font-bold rounded-full whitespace-nowrap transition-all ${
              activeCategory === cat
                ? 'bg-fiido text-white'
                : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
            }`}
          >
            {cat === 'all' ? '全部' : CATEGORY_LABELS[cat]}
          </button>
        ))}
      </div>

      {/* 列表区域 */}
      <div className="overflow-y-auto custom-scrollbar" style={{ maxHeight: '260px' }}>
        {isLoading ? (
          <div className="flex items-center justify-center py-8 text-slate-400">
            <Loader2 size={20} className="animate-spin" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-8 text-slate-400">
            <p className="text-[11px]">{error}</p>
            <button
              onClick={fetchReplies}
              className="mt-2 text-[10px] text-fiido font-bold hover:underline"
            >
              重试
            </button>
          </div>
        ) : replies.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-slate-400">
            <MessageSquare size={24} className="mb-2 opacity-50" />
            <p className="text-[11px] font-bold">暂无快捷回复</p>
            <p className="text-[10px] mt-1">
              {searchKeyword ? '尝试其他关键词' : '可在设置中添加快捷回复'}
            </p>
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {replies.map((reply) => (
              <button
                key={reply.id}
                onClick={() => handleSelectReply(reply)}
                className="w-full text-left p-3 rounded-lg hover:bg-fiido-light border border-transparent hover:border-fiido/10 transition-all group"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] font-bold text-slate-700 group-hover:text-fiido-dark truncate">
                        {reply.title}
                      </span>
                      {reply.shortcut_key && (
                        <span className="text-[9px] px-1.5 py-0.5 bg-slate-100 text-slate-500 rounded font-mono">
                          {reply.shortcut_key}
                        </span>
                      )}
                      {reply.is_shared && (
                        <span className="text-[9px] px-1.5 py-0.5 bg-blue-50 text-blue-500 rounded font-bold">
                          共享
                        </span>
                      )}
                    </div>
                    <p className="text-[10px] text-slate-500 mt-1 line-clamp-2">
                      {reply.content}
                    </p>
                  </div>
                  <span className="text-[9px] px-1.5 py-0.5 bg-slate-50 text-slate-400 rounded shrink-0">
                    {CATEGORY_LABELS[reply.category]}
                  </span>
                </div>
                {reply.variables && reply.variables.length > 0 && (
                  <div className="flex items-center gap-1 mt-2">
                    <Hash size={10} className="text-slate-400" />
                    <span className="text-[9px] text-slate-400">
                      变量: {reply.variables.join(', ')}
                    </span>
                  </div>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* 底部提示 */}
      <div className="px-4 py-2 border-t border-slate-100 bg-slate-50/50">
        <p className="text-[9px] text-slate-400 text-center">
          点击快捷回复插入到输入框 • ESC 关闭
        </p>
      </div>
    </div>
  );
};

export default QuickReplyPanel;
