/**
 * 个人配置页面
 *
 * 功能：
 * - 查看/修改头像（支持本地上传）
 * - 修改显示名称
 * - 修改最大接单数
 */

import React, { useState, useEffect, useRef } from 'react';
import { ArrowLeft, User, Camera, Loader2, Check, AlertCircle, Upload } from 'lucide-react';
import { authApi } from '../src/api';
import { useAuthStore } from '../src/stores';

interface ProfileSettingsProps {
  onBack: () => void;
}

const ProfileSettings: React.FC<ProfileSettingsProps> = ({ onBack }) => {
  const { agent, fetchProfile } = useAuthStore();

  const [name, setName] = useState(agent?.name || '');
  const [avatarUrl, setAvatarUrl] = useState(agent?.avatar_url || '');
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (agent) {
      setName(agent.name || '');
      setAvatarUrl(agent.avatar_url || '');
    }
  }, [agent]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) {
      setMessage({ type: 'error', text: '显示名称不能为空' });
      return;
    }

    setIsLoading(true);
    setMessage(null);

    try {
      await authApi.updateProfile({
        name: name.trim(),
        avatar_url: avatarUrl.trim() || undefined,
      });

      // 刷新用户信息
      await fetchProfile();

      setMessage({ type: 'success', text: '个人信息已更新' });
    } catch (error: any) {
      console.error('更新个人信息失败:', error);
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || '更新失败，请重试',
      });
    } finally {
      setIsLoading(false);
    }
  };

  // 处理文件上传
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // 验证文件类型
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      setMessage({ type: 'error', text: '请选择 JPG、PNG、GIF 或 WebP 格式的图片' });
      return;
    }

    // 验证文件大小（2MB）
    if (file.size > 2 * 1024 * 1024) {
      setMessage({ type: 'error', text: '图片大小不能超过 2MB' });
      return;
    }

    setIsUploading(true);
    setMessage(null);

    try {
      const result = await authApi.uploadAvatar(file);
      setAvatarUrl(result.avatar_url);

      // 刷新用户信息
      await fetchProfile();

      setMessage({ type: 'success', text: '头像上传成功' });
    } catch (error: any) {
      console.error('上传头像失败:', error);
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || '上传失败，请重试',
      });
    } finally {
      setIsUploading(false);
      // 清空文件输入，允许重复选择同一文件
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // 触发文件选择
  const handleAvatarClick = () => {
    fileInputRef.current?.click();
  };

  // 生成默认头像 URL
  const getAvatarSrc = () => {
    if (avatarUrl) return avatarUrl;
    return `https://api.dicebear.com/7.x/avataaars/svg?seed=${agent?.username || 'default'}`;
  };

  return (
    <div className="h-full bg-slate-50/30 p-12 overflow-y-auto font-sans">
      <div className="max-w-2xl mx-auto space-y-8">
        {/* 返回按钮 */}
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-slate-400 hover:text-fiido transition-colors text-sm font-bold"
        >
          <ArrowLeft size={18} />
          返回设置
        </button>

        {/* 标题 */}
        <header>
          <h1 className="text-2xl font-brand font-black text-slate-800 tracking-tighter">个人配置</h1>
          <p className="text-slate-400 text-xs font-bold mt-2">修改头像、显示名称等个人信息</p>
        </header>

        {/* 表单 */}
        <form onSubmit={handleSubmit} className="space-y-8">
          {/* 头像 */}
          <div className="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm">
            <h3 className="text-sm font-bold text-slate-800 mb-6">头像设置</h3>
            <div className="flex items-center gap-6">
              {/* 头像预览和上传 */}
              <div
                className="relative group cursor-pointer"
                onClick={handleAvatarClick}
              >
                <img
                  src={getAvatarSrc()}
                  alt="头像"
                  className="w-24 h-24 rounded-2xl object-cover border-4 border-slate-100"
                />
                <div className="absolute inset-0 bg-black/50 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  {isUploading ? (
                    <Loader2 size={24} className="text-white animate-spin" />
                  ) : (
                    <Camera size={24} className="text-white" />
                  )}
                </div>
                {/* 隐藏的文件输入 */}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/gif,image/webp"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-3">
                  <button
                    type="button"
                    onClick={handleAvatarClick}
                    disabled={isUploading}
                    className="px-4 py-2 bg-fiido text-white rounded-lg text-xs font-bold hover:opacity-90 disabled:opacity-50 flex items-center gap-2 transition-all"
                  >
                    {isUploading ? (
                      <>
                        <Loader2 size={14} className="animate-spin" />
                        上传中...
                      </>
                    ) : (
                      <>
                        <Upload size={14} />
                        上传图片
                      </>
                    )}
                  </button>
                  <span className="text-[10px] text-slate-400">支持 JPG、PNG、GIF、WebP，最大 2MB</span>
                </div>
                <label className="block text-xs font-bold text-slate-500 mb-2">或输入头像 URL</label>
                <input
                  type="text"
                  value={avatarUrl}
                  onChange={(e) => setAvatarUrl(e.target.value)}
                  placeholder="https://example.com/avatar.jpg"
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:border-fiido focus:ring-2 focus:ring-fiido/10 transition-all"
                />
                <p className="text-[10px] text-slate-400 mt-2">留空将使用默认头像</p>
              </div>
            </div>
          </div>

          {/* 基本信息 */}
          <div className="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm space-y-6">
            <h3 className="text-sm font-bold text-slate-800">基本信息</h3>

            {/* 用户名（只读） */}
            <div>
              <label className="block text-xs font-bold text-slate-500 mb-2">用户名</label>
              <input
                type="text"
                value={agent?.username || ''}
                disabled
                className="w-full px-4 py-3 bg-slate-100 border border-slate-200 rounded-xl text-sm text-slate-500 cursor-not-allowed"
              />
              <p className="text-[10px] text-slate-400 mt-2">用户名不可修改</p>
            </div>

            {/* 显示名称 */}
            <div>
              <label className="block text-xs font-bold text-slate-500 mb-2">显示名称 *</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="请输入显示名称"
                maxLength={50}
                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:border-fiido focus:ring-2 focus:ring-fiido/10 transition-all"
              />
            </div>

            {/* 角色（只读） */}
            <div>
              <label className="block text-xs font-bold text-slate-500 mb-2">角色</label>
              <input
                type="text"
                value={agent?.role === 'admin' ? '管理员' : agent?.role === 'supervisor' ? '主管' : '坐席'}
                disabled
                className="w-full px-4 py-3 bg-slate-100 border border-slate-200 rounded-xl text-sm text-slate-500 cursor-not-allowed"
              />
            </div>
          </div>

          {/* 提示消息 */}
          {message && (
            <div
              className={`flex items-center gap-3 p-4 rounded-xl ${
                message.type === 'success'
                  ? 'bg-green-50 text-green-600 border border-green-200'
                  : 'bg-red-50 text-red-600 border border-red-200'
              }`}
            >
              {message.type === 'success' ? <Check size={18} /> : <AlertCircle size={18} />}
              <span className="text-sm font-bold">{message.text}</span>
            </div>
          )}

          {/* 提交按钮 */}
          <div className="flex justify-end gap-4">
            <button
              type="button"
              onClick={onBack}
              className="px-6 py-3 text-slate-500 hover:text-slate-700 font-bold text-sm transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-8 py-3 bg-fiido text-white rounded-xl font-bold text-sm hover:opacity-90 disabled:opacity-50 flex items-center gap-2 transition-all"
            >
              {isLoading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  保存中...
                </>
              ) : (
                '保存修改'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProfileSettings;
