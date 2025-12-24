/**
 * 话术短语库管理组件
 *
 * 功能：
 * - 快捷回复列表展示（支持分类筛选、搜索）
 * - 新增快捷回复
 * - 编辑快捷回复
 * - 删除快捷回复
 * - 支持个人/共享标识
 */

import React, { useState, useEffect } from 'react';
import {
  Search, Plus, Edit3, Trash2, X, Save,
  Zap, Hash, Loader2, MessageSquare, ArrowLeft, Check
} from 'lucide-react';
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

// 分类颜色
const CATEGORY_COLORS: Record<QuickReplyCategory, string> = {
  greeting: 'bg-green-50 text-green-600 border-green-200',
  farewell: 'bg-blue-50 text-blue-600 border-blue-200',
  apology: 'bg-orange-50 text-orange-600 border-orange-200',
  shipping: 'bg-purple-50 text-purple-600 border-purple-200',
  refund: 'bg-red-50 text-red-600 border-red-200',
  product: 'bg-cyan-50 text-cyan-600 border-cyan-200',
  technical: 'bg-slate-50 text-slate-600 border-slate-200',
  custom: 'bg-amber-50 text-amber-600 border-amber-200',
};

interface QuickReplyManagerProps {
  onBack: () => void;
}

const QuickReplyManager: React.FC<QuickReplyManagerProps> = ({ onBack }) => {
  const [replies, setReplies] = useState<QuickReply[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [activeCategory, setActiveCategory] = useState<QuickReplyCategory | 'all'>('all');
  const [error, setError] = useState<string | null>(null);

  // 编辑/新增弹窗状态
  const [showModal, setShowModal] = useState(false);
  const [editingReply, setEditingReply] = useState<QuickReply | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    category: 'custom' as QuickReplyCategory,
    shortcut_key: '',
    is_shared: false,
  });

  // 删除确认
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // 加载快捷回复列表
  const fetchReplies = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params: any = {
        include_shared: true,
        limit: 200,
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

  // 初始化加载
  useEffect(() => {
    fetchReplies();
  }, []);

  // 分类或搜索变化时重新加载
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchReplies();
    }, 300);
    return () => clearTimeout(timer);
  }, [activeCategory, searchKeyword]);

  // 打开新增弹窗
  const handleOpenCreate = () => {
    setEditingReply(null);
    setFormData({
      title: '',
      content: '',
      category: 'custom',
      shortcut_key: '',
      is_shared: false,
    });
    setShowModal(true);
  };

  // 打开编辑弹窗
  const handleOpenEdit = (reply: QuickReply) => {
    setEditingReply(reply);
    setFormData({
      title: reply.title,
      content: reply.content,
      category: reply.category,
      shortcut_key: reply.shortcut_key || '',
      is_shared: reply.is_shared || false,
    });
    setShowModal(true);
  };

  // 保存（新增或编辑）
  const handleSave = async () => {
    if (!formData.title.trim() || !formData.content.trim()) {
      alert('请填写标题和内容');
      return;
    }

    setIsSaving(true);
    try {
      if (editingReply) {
        // 编辑
        await quickRepliesApi.update(editingReply.id, {
          title: formData.title,
          content: formData.content,
          category: formData.category,
          shortcut_key: formData.shortcut_key || undefined,
          is_shared: formData.is_shared,
        });
      } else {
        // 新增
        await quickRepliesApi.create({
          title: formData.title,
          content: formData.content,
          category: formData.category,
          shortcut_key: formData.shortcut_key || undefined,
          is_shared: formData.is_shared,
        });
      }
      setShowModal(false);
      fetchReplies();
    } catch (err: any) {
      console.error('保存失败:', err);
      alert('保存失败，请重试');
    } finally {
      setIsSaving(false);
    }
  };

  // 删除
  const handleDelete = async (id: string) => {
    setIsDeleting(true);
    try {
      await quickRepliesApi.remove(id);
      setDeleteConfirm(null);
      fetchReplies();
    } catch (err: any) {
      console.error('删除失败:', err);
      alert('删除失败，请重试');
    } finally {
      setIsDeleting(false);
    }
  };

  // 分类列表
  const categories: (QuickReplyCategory | 'all')[] = [
    'all', 'greeting', 'farewell', 'apology', 'shipping', 'refund', 'product', 'technical', 'custom'
  ];

  return (
    <div className="h-full bg-slate-50/30 p-8 overflow-hidden flex flex-col">
      {/* 头部 */}
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={onBack}
          className="p-2 hover:bg-slate-200 rounded-xl text-slate-400 hover:text-slate-600 transition-colors"
        >
          <ArrowLeft size={20} />
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-black text-slate-800 flex items-center gap-3">
            <Zap size={24} className="text-fiido" />
            话术短语库
          </h1>
          <p className="text-xs text-slate-400 font-bold mt-1">管理个人及团队共享的快捷回复模板</p>
        </div>
        <button
          onClick={handleOpenCreate}
          className="px-5 py-2.5 bg-fiido text-white rounded-xl font-bold text-sm flex items-center gap-2 hover:opacity-90 transition-all shadow-lg shadow-fiido/20"
        >
          <Plus size={16} />
          新增话术
        </button>
      </div>

      {/* 搜索和筛选 */}
      <div className="flex gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            placeholder="搜索话术标题或内容..."
            className="w-full pl-11 pr-4 py-3 text-sm bg-white border border-slate-200 rounded-xl outline-none focus:border-fiido focus:ring-2 focus:ring-fiido/10 transition-all"
          />
        </div>
        <div className="flex gap-2 overflow-x-auto no-scrollbar">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-4 py-2 text-xs font-bold rounded-xl whitespace-nowrap transition-all border ${
                activeCategory === cat
                  ? 'bg-fiido text-white border-fiido'
                  : 'bg-white text-slate-500 border-slate-200 hover:border-fiido hover:text-fiido'
              }`}
            >
              {cat === 'all' ? '全部' : CATEGORY_LABELS[cat]}
            </button>
          ))}
        </div>
      </div>

      {/* 列表区域 */}
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {isLoading ? (
          <div className="flex items-center justify-center h-64 text-slate-400">
            <Loader2 size={24} className="animate-spin" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-64 text-slate-400">
            <p className="text-sm">{error}</p>
            <button
              onClick={fetchReplies}
              className="mt-3 text-sm text-fiido font-bold hover:underline"
            >
              重试
            </button>
          </div>
        ) : replies.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-slate-400">
            <MessageSquare size={48} className="mb-4 opacity-30" />
            <p className="text-sm font-bold">暂无话术</p>
            <p className="text-xs mt-1">
              {searchKeyword ? '尝试其他关键词' : '点击右上角"新增话术"创建'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {replies.map((reply) => (
              <div
                key={reply.id}
                className="bg-white rounded-2xl border border-slate-100 p-5 hover:shadow-lg hover:-translate-y-1 transition-all group"
              >
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-bold text-slate-800 truncate">{reply.title}</h3>
                    <div className="flex items-center gap-2 mt-1.5">
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${CATEGORY_COLORS[reply.category]}`}>
                        {CATEGORY_LABELS[reply.category]}
                      </span>
                      {reply.shortcut_key && (
                        <span className="text-[10px] px-2 py-0.5 bg-slate-100 text-slate-500 rounded font-mono">
                          {reply.shortcut_key}
                        </span>
                      )}
                      {reply.is_shared && (
                        <span className="text-[10px] px-2 py-0.5 bg-blue-50 text-blue-500 rounded font-bold">
                          共享
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => handleOpenEdit(reply)}
                      className="p-2 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-fiido transition-colors"
                      title="编辑"
                    >
                      <Edit3 size={14} />
                    </button>
                    <button
                      onClick={() => setDeleteConfirm(reply.id)}
                      className="p-2 hover:bg-red-50 rounded-lg text-slate-400 hover:text-red-500 transition-colors"
                      title="删除"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
                <p className="text-xs text-slate-500 leading-relaxed line-clamp-3">
                  {reply.content}
                </p>
                {reply.variables && reply.variables.length > 0 && (
                  <div className="flex items-center gap-1 mt-3 pt-3 border-t border-slate-50">
                    <Hash size={10} className="text-slate-400" />
                    <span className="text-[10px] text-slate-400">
                      变量: {reply.variables.join(', ')}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 新增/编辑弹窗 */}
      {showModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setShowModal(false)}>
          <div className="bg-white rounded-2xl w-full max-w-lg p-6 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-black text-slate-800">
                {editingReply ? '编辑话术' : '新增话术'}
              </h2>
              <button
                onClick={() => setShowModal(false)}
                className="p-1.5 hover:bg-slate-100 rounded-lg text-slate-400"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-500 mb-2">标题 *</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="如：问候语-早上好"
                  className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-fiido/20 focus:border-fiido"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 mb-2">内容 *</label>
                <textarea
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  placeholder="输入话术内容，支持变量如 {customer_name}"
                  rows={4}
                  className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-fiido/20 focus:border-fiido resize-none"
                />
                <p className="text-[10px] text-slate-400 mt-1">
                  支持变量: {'{agent_name}'} (坐席姓名), {'{customer_name}'} (客户姓名，需会话中有), {'{current_time}'} (当前时间), {'{current_date}'} (当前日期)
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 mb-2">分类</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value as QuickReplyCategory })}
                    className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-fiido/20 focus:border-fiido"
                  >
                    {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
                      <option key={key} value={key}>{label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 mb-2">快捷键</label>
                  <input
                    type="text"
                    value={formData.shortcut_key}
                    onChange={(e) => setFormData({ ...formData, shortcut_key: e.target.value })}
                    placeholder="如：/hello"
                    className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-fiido/20 focus:border-fiido"
                  />
                </div>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => setFormData({ ...formData, is_shared: !formData.is_shared })}
                  className={`w-12 h-7 rounded-full relative transition-all ${
                    formData.is_shared ? 'bg-fiido' : 'bg-slate-200'
                  }`}
                >
                  <div className={`absolute top-1 w-5 h-5 bg-white rounded-full shadow transition-all flex items-center justify-center ${
                    formData.is_shared ? 'right-1' : 'left-1'
                  }`}>
                    {formData.is_shared && <Check size={12} className="text-fiido" />}
                  </div>
                </button>
                <div>
                  <p className="text-sm font-bold text-slate-700">团队共享</p>
                  <p className="text-[10px] text-slate-400">开启后其他坐席也可使用此话术</p>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowModal(false)}
                className="px-5 py-2.5 text-sm font-bold text-slate-500 hover:bg-slate-100 rounded-xl transition-all"
              >
                取消
              </button>
              <button
                onClick={handleSave}
                disabled={isSaving || !formData.title.trim() || !formData.content.trim()}
                className="px-6 py-2.5 bg-fiido text-white text-sm font-bold rounded-xl hover:opacity-90 transition-all disabled:opacity-50 flex items-center gap-2"
              >
                {isSaving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                保存
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 删除确认弹窗 */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setDeleteConfirm(null)}>
          <div className="bg-white rounded-2xl w-full max-w-sm p-6 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-lg font-black text-slate-800 mb-2">确认删除</h2>
            <p className="text-sm text-slate-500 mb-6">删除后无法恢复，确定要删除这条话术吗？</p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-5 py-2.5 text-sm font-bold text-slate-500 hover:bg-slate-100 rounded-xl transition-all"
              >
                取消
              </button>
              <button
                onClick={() => handleDelete(deleteConfirm)}
                disabled={isDeleting}
                className="px-6 py-2.5 bg-red-500 text-white text-sm font-bold rounded-xl hover:bg-red-600 transition-all disabled:opacity-50 flex items-center gap-2"
              >
                {isDeleting && <Loader2 size={14} className="animate-spin" />}
                删除
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QuickReplyManager;
