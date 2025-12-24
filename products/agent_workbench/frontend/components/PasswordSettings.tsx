/**
 * 密码修改页面
 *
 * 功能：
 * - 输入旧密码
 * - 输入新密码（需确认）
 * - 密码强度校验
 */

import React, { useState } from 'react';
import { ArrowLeft, Lock, Eye, EyeOff, Loader2, Check, AlertCircle, ShieldCheck } from 'lucide-react';
import { authApi } from '../src/api';

interface PasswordSettingsProps {
  onBack: () => void;
}

const PasswordSettings: React.FC<PasswordSettingsProps> = ({ onBack }) => {
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showOldPassword, setShowOldPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // 密码强度检测
  const getPasswordStrength = (password: string): { level: number; text: string; color: string } => {
    if (!password) return { level: 0, text: '', color: '' };

    let score = 0;
    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    if (/[a-z]/.test(password)) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^a-zA-Z0-9]/.test(password)) score++;

    if (score <= 2) return { level: 1, text: '弱', color: 'bg-red-500' };
    if (score <= 4) return { level: 2, text: '中等', color: 'bg-yellow-500' };
    return { level: 3, text: '强', color: 'bg-green-500' };
  };

  const passwordStrength = getPasswordStrength(newPassword);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // 表单验证
    if (!oldPassword) {
      setMessage({ type: 'error', text: '请输入当前密码' });
      return;
    }

    if (!newPassword) {
      setMessage({ type: 'error', text: '请输入新密码' });
      return;
    }

    if (newPassword.length < 8) {
      setMessage({ type: 'error', text: '新密码长度至少为 8 位' });
      return;
    }

    if (newPassword !== confirmPassword) {
      setMessage({ type: 'error', text: '两次输入的新密码不一致' });
      return;
    }

    if (oldPassword === newPassword) {
      setMessage({ type: 'error', text: '新密码不能与当前密码相同' });
      return;
    }

    setIsLoading(true);
    setMessage(null);

    try {
      await authApi.changePassword({
        old_password: oldPassword,
        new_password: newPassword,
      });

      setMessage({ type: 'success', text: '密码修改成功' });

      // 清空表单
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error: any) {
      console.error('修改密码失败:', error);
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || '修改失败，请检查当前密码是否正确',
      });
    } finally {
      setIsLoading(false);
    }
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
          <h1 className="text-2xl font-brand font-black text-slate-800 tracking-tighter">修改密码</h1>
          <p className="text-slate-400 text-xs font-bold mt-2">定期修改密码可以提高账户安全性</p>
        </header>

        {/* 表单 */}
        <form onSubmit={handleSubmit} className="space-y-8">
          {/* 安全提示 */}
          <div className="bg-fiido/5 border border-fiido/20 p-6 rounded-2xl flex items-start gap-4">
            <ShieldCheck size={24} className="text-fiido flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-bold text-slate-800 mb-1">密码安全建议</h4>
              <ul className="text-xs text-slate-500 space-y-1">
                <li>• 密码长度至少 8 位</li>
                <li>• 建议包含大小写字母、数字和特殊字符</li>
                <li>• 不要使用容易猜测的密码（如生日、电话号码）</li>
                <li>• 定期更换密码，不要重复使用旧密码</li>
              </ul>
            </div>
          </div>

          {/* 密码输入 */}
          <div className="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm space-y-6">
            <h3 className="text-sm font-bold text-slate-800">密码设置</h3>

            {/* 当前密码 */}
            <div>
              <label className="block text-xs font-bold text-slate-500 mb-2">当前密码 *</label>
              <div className="relative">
                <Lock size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type={showOldPassword ? 'text' : 'password'}
                  value={oldPassword}
                  onChange={(e) => setOldPassword(e.target.value)}
                  placeholder="请输入当前密码"
                  className="w-full pl-12 pr-12 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:border-fiido focus:ring-2 focus:ring-fiido/10 transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowOldPassword(!showOldPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showOldPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            {/* 新密码 */}
            <div>
              <label className="block text-xs font-bold text-slate-500 mb-2">新密码 *</label>
              <div className="relative">
                <Lock size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type={showNewPassword ? 'text' : 'password'}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="请输入新密码（至少 8 位）"
                  className="w-full pl-12 pr-12 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:border-fiido focus:ring-2 focus:ring-fiido/10 transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showNewPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {/* 密码强度指示器 */}
              {newPassword && (
                <div className="mt-3 flex items-center gap-3">
                  <div className="flex-1 flex gap-1">
                    <div className={`h-1.5 flex-1 rounded-full transition-all ${passwordStrength.level >= 1 ? passwordStrength.color : 'bg-slate-200'}`} />
                    <div className={`h-1.5 flex-1 rounded-full transition-all ${passwordStrength.level >= 2 ? passwordStrength.color : 'bg-slate-200'}`} />
                    <div className={`h-1.5 flex-1 rounded-full transition-all ${passwordStrength.level >= 3 ? passwordStrength.color : 'bg-slate-200'}`} />
                  </div>
                  <span className={`text-xs font-bold ${
                    passwordStrength.level === 1 ? 'text-red-500' :
                    passwordStrength.level === 2 ? 'text-yellow-500' :
                    'text-green-500'
                  }`}>
                    密码强度：{passwordStrength.text}
                  </span>
                </div>
              )}
            </div>

            {/* 确认新密码 */}
            <div>
              <label className="block text-xs font-bold text-slate-500 mb-2">确认新密码 *</label>
              <div className="relative">
                <Lock size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="请再次输入新密码"
                  className={`w-full pl-12 pr-12 py-3 bg-slate-50 border rounded-xl text-sm outline-none focus:ring-2 focus:ring-fiido/10 transition-all ${
                    confirmPassword && confirmPassword !== newPassword
                      ? 'border-red-300 focus:border-red-400'
                      : 'border-slate-200 focus:border-fiido'
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {confirmPassword && confirmPassword !== newPassword && (
                <p className="text-xs text-red-500 mt-2">两次输入的密码不一致</p>
              )}
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
              disabled={isLoading || !oldPassword || !newPassword || !confirmPassword || newPassword !== confirmPassword}
              className="px-8 py-3 bg-fiido text-white rounded-xl font-bold text-sm hover:opacity-90 disabled:opacity-50 flex items-center gap-2 transition-all"
            >
              {isLoading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  修改中...
                </>
              ) : (
                '确认修改'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PasswordSettings;
