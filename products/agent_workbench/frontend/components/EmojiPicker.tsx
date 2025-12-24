/**
 * 表情选择器组件
 *
 * 功能：
 * - 提供欧洲用户常用的表情符号
 * - 分类展示（表情、手势、物品等）
 * - 点击插入到输入框
 * - 点击外部自动关闭
 */

import React, { useState, useEffect, useRef } from 'react';

interface EmojiPickerProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (emoji: string) => void;
}

// 欧洲用户常用表情 - 参考 WhatsApp/Telegram
const EMOJI_CATEGORIES = {
  'Smileys': [
    '😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂',
    '🙂', '😊', '😇', '🥰', '😍', '🤩', '😘', '😗',
    '😚', '😙', '🥲', '😋', '😛', '😜', '🤪', '😝',
    '🤗', '🤭', '🫢', '🤫', '🤔', '🫡', '🤐', '🤨',
    '😐', '😑', '😶', '🫥', '😏', '😒', '🙄', '😬',
    '😮‍💨', '🤥', '🫠', '😌', '😔', '😪', '🤤', '😴',
    '😷', '🤒', '🤕', '🤢', '🤮', '🤧', '🥵', '🥶',
  ],
  'Gestures': [
    '👍', '👎', '👌', '🤌', '🤏', '✌️', '🤞', '🫰',
    '🤟', '🤘', '🤙', '👈', '👉', '👆', '👇', '☝️',
    '🫵', '👋', '🤚', '🖐️', '✋', '🖖', '🫱', '🫲',
    '👏', '🙌', '🫶', '👐', '🤲', '🤝', '🙏', '✍️',
    '💪', '🦾', '🫂', '🙆', '🙅', '🤷', '🤦', '💁',
  ],
  'Objects': [
    '❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍',
    '💯', '💢', '💥', '💫', '💦', '💨', '🕳️', '💬',
    '👁️‍🗨️', '🗨️', '🗯️', '💭', '💤', '🔥', '✨', '🌟',
    '⭐', '🌈', '☀️', '🌤️', '⛅', '🌥️', '☁️', '🌧️',
    '📦', '📧', '📩', '📨', '✉️', '📝', '📋', '📊',
    '🔔', '🔕', '📢', '📣', '⏰', '⏱️', '🔒', '🔓',
  ],
  'Symbols': [
    '✅', '❌', '❓', '❗', '‼️', '⁉️', '💡', '🔍',
    '🔎', '🔗', '📌', '📍', '🏷️', '💰', '💵', '💶',
    '🎁', '🎉', '🎊', '🎈', '🏆', '🥇', '🥈', '🥉',
    '⚠️', '🚫', '⛔', '🔴', '🟠', '🟡', '🟢', '🔵',
    '➡️', '⬅️', '⬆️', '⬇️', '↗️', '↘️', '↙️', '↖️',
  ],
};

const EmojiPicker: React.FC<EmojiPickerProps> = ({ isOpen, onClose, onSelect }) => {
  const [activeCategory, setActiveCategory] = useState<keyof typeof EMOJI_CATEGORIES>('Smileys');
  const pickerRef = useRef<HTMLDivElement>(null);

  // 点击外部关闭
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (pickerRef.current && !pickerRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    // 延迟添加监听，避免打开时立即触发关闭
    const timer = setTimeout(() => {
      document.addEventListener('click', handleClickOutside);
    }, 0);

    return () => {
      clearTimeout(timer);
      document.removeEventListener('click', handleClickOutside);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleEmojiClick = (emoji: string) => {
    onSelect(emoji);
  };

  const categoryIcons: Record<keyof typeof EMOJI_CATEGORIES, string> = {
    'Smileys': '😀',
    'Gestures': '👋',
    'Objects': '❤️',
    'Symbols': '✅',
  };

  return (
    <div
      ref={pickerRef}
      className="absolute bottom-full left-0 mb-2 bg-white rounded-2xl shadow-xl border border-slate-200 w-[320px] overflow-hidden z-50 animate-in fade-in slide-in-from-bottom-2 duration-200"
    >
      {/* Category Tabs */}
      <div className="flex border-b border-slate-100 bg-slate-50/50">
        {(Object.keys(EMOJI_CATEGORIES) as Array<keyof typeof EMOJI_CATEGORIES>).map((category) => (
          <button
            key={category}
            onClick={() => setActiveCategory(category)}
            className={`flex-1 py-2.5 text-lg transition-all ${
              activeCategory === category
                ? 'bg-white border-b-2 border-fiido'
                : 'hover:bg-slate-100'
            }`}
            title={category}
          >
            {categoryIcons[category]}
          </button>
        ))}
      </div>

      {/* Emoji Grid */}
      <div className="p-3 max-h-[240px] overflow-y-auto custom-scrollbar">
        <div className="grid grid-cols-8 gap-1">
          {EMOJI_CATEGORIES[activeCategory].map((emoji, index) => (
            <button
              key={index}
              onClick={() => handleEmojiClick(emoji)}
              className="w-8 h-8 flex items-center justify-center text-xl hover:bg-slate-100 rounded-lg transition-all hover:scale-110 active:scale-95"
            >
              {emoji}
            </button>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="px-3 py-2 border-t border-slate-100 bg-slate-50/50 flex justify-between items-center">
        <span className="text-[10px] text-slate-400 font-bold uppercase">{activeCategory}</span>
        <button
          onClick={onClose}
          className="text-[10px] text-slate-400 hover:text-slate-600 font-bold"
        >
          Close
        </button>
      </div>
    </div>
  );
};

export default EmojiPicker;
