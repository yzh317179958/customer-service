import React from 'react';
import { X, MessageCircle, CheckCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import Button from './ui/Button';

interface PaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  planName: string;
  price: number;
  isYearly: boolean;
}

const PaymentModal: React.FC<PaymentModalProps> = ({ isOpen, onClose, planName, price, isYearly }) => {
  const totalPrice = isYearly ? price * 12 : price;
  const period = isYearly ? '年' : '月';

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-slate-900/60 backdrop-blur-md"
            onClick={onClose}
          />
          <motion.div
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            className="relative bg-white rounded-[2rem] shadow-2xl w-full max-w-lg overflow-hidden"
          >
            {/* Header */}
            <div className="p-8 border-b border-bg-100">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-2xl font-black tracking-tight mb-2">订阅 {planName}</h3>
                  <p className="text-text-secondary text-sm">
                    ¥{totalPrice}/{period} · {isYearly ? '年付立省20%' : '按月计费'}
                  </p>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-bg-100 rounded-full transition-colors"
                >
                  <X size={20} />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-8">
              {/* QR Code Section */}
              <div className="text-center mb-8">
                <div className="inline-flex items-center justify-center w-48 h-48 bg-white rounded-2xl border border-bg-200 mb-4 overflow-hidden">
                  <img src="/payment-qr.jpg" alt="收款码" className="w-full h-full object-contain" />
                </div>
                <p className="text-sm text-text-secondary">
                  微信/支付宝扫码支付 <span className="font-bold text-brand-600">¥{totalPrice}</span>
                </p>
              </div>

              {/* Steps */}
              <div className="bg-bg-50 rounded-xl p-6 mb-6">
                <h4 className="font-bold text-sm mb-4 flex items-center gap-2">
                  <CheckCircle size={16} className="text-brand-600" /> 开通流程
                </h4>
                <ol className="space-y-3 text-sm text-text-secondary">
                  <li className="flex gap-3">
                    <span className="w-5 h-5 rounded-full bg-brand-600 text-white text-xs flex items-center justify-center shrink-0">1</span>
                    <span>扫码支付 ¥{totalPrice}</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="w-5 h-5 rounded-full bg-brand-600 text-white text-xs flex items-center justify-center shrink-0">2</span>
                    <span>添加客服微信，发送支付截图</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="w-5 h-5 rounded-full bg-brand-600 text-white text-xs flex items-center justify-center shrink-0">3</span>
                    <span>客服为您开通服务（通常 10 分钟内）</span>
                  </li>
                </ol>
              </div>

              {/* WeChat Contact */}
              <div className="flex items-center gap-4 p-4 bg-green-50 rounded-xl border border-green-100">
                <div className="w-12 h-12 bg-green-500 rounded-xl flex items-center justify-center">
                  <MessageCircle size={24} className="text-white" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-bold text-green-800">客服微信</p>
                  <p className="text-lg font-black text-green-600 tracking-wide">yzh317179958</p>
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  className="bg-white border-green-200 hover:bg-green-50"
                  onClick={() => navigator.clipboard.writeText('yzh317179958')}
                >
                  复制
                </Button>
              </div>
            </div>

            {/* Footer */}
            <div className="p-6 bg-bg-50 border-t border-bg-100">
              <p className="text-xs text-text-muted text-center">
                支付遇到问题？添加客服微信咨询
              </p>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default PaymentModal;
