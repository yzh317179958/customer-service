import React, { useMemo, useState } from 'react';
import { ExternalLink, ShoppingBag, Truck, ZoomIn } from 'lucide-react';

type ProductCardData = {
  imageUrl: string;
  name: string;
  quantity: string;
  price: string;
  status: string;
  carrier: string;
  trackingNumber: string;
  trackingUrl: string;
};

const PRODUCT_CARD_REGEX = /\[PRODUCT\]([\s\S]*?)\[\/PRODUCT\]/g;

const sanitizeHttpUrl = (rawUrl: string): string => {
  const url = (rawUrl || '').trim();
  if (!url) return '';

  try {
    const parsed = new URL(url);
    const protocol = parsed.protocol.toLowerCase();
    if (protocol !== 'http:' && protocol !== 'https:') {
      return '';
    }
    return parsed.toString();
  } catch {
    return '';
  }
};

const parseProductCardData = (raw: string): ProductCardData => {
  const fields = raw.split('|');
  const get = (index: number) => (fields[index] || '').trim();

  return {
    imageUrl: sanitizeHttpUrl(get(0)),
    name: get(1),
    quantity: get(2),
    price: get(3),
    status: get(4),
    carrier: get(5),
    trackingNumber: get(6),
    trackingUrl: sanitizeHttpUrl(fields.slice(7).join('|').trim()),
  };
};

const getStatusBadgeClass = (status: string) => {
  const s = (status || '').toLowerCase();
  if (status.includes('已取消') || s.includes('cancel')) return 'bg-rose-50 text-rose-600 border-rose-100';
  if (status.includes('退货') || status.includes('退款') || s.includes('refund') || s.includes('return')) return 'bg-rose-50 text-rose-600 border-rose-100';
  if (status.includes('已收货') || status.includes('已送达') || s.includes('delivered') || s.includes('received')) return 'bg-emerald-50 text-emerald-600 border-emerald-100';
  if (status.includes('运输') || status.includes('派送') || s.includes('in_transit') || s.includes('out_for_delivery')) return 'bg-blue-50 text-blue-600 border-blue-100';
  if (status.includes('已发货') || s.includes('shipped')) return 'bg-amber-50 text-amber-700 border-amber-100';
  return 'bg-slate-50 text-slate-600 border-slate-200';
};

const ProductCard: React.FC<{ data: ProductCardData }> = ({ data }) => {
  const [imageError, setImageError] = useState(false);
  const hasTracking = Boolean(data.carrier || data.trackingNumber || data.trackingUrl);
  const showImage = Boolean(data.imageUrl) && !imageError;

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
      <div className="flex gap-3 p-3">
        {showImage ? (
          <img
            src={data.imageUrl}
            alt={data.name || '商品'}
            className="w-14 h-14 rounded-lg object-cover border border-slate-200 bg-slate-50 shrink-0"
            onError={() => setImageError(true)}
          />
        ) : (
          <div className="w-14 h-14 rounded-lg border border-slate-200 bg-slate-50 flex items-center justify-center shrink-0">
            <ShoppingBag size={18} className="text-slate-400" />
          </div>
        )}

        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <div className="text-[12px] font-black text-slate-800 truncate">{data.name || '商品'}</div>
              <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-[10px] text-slate-500 font-bold">
                {data.quantity && <span>数量: {data.quantity}</span>}
                {data.price && <span>价格: {data.price}</span>}
              </div>
            </div>
            {data.status && (
              <span className={`shrink-0 text-[10px] px-2 py-0.5 rounded-lg font-black border ${getStatusBadgeClass(data.status)}`}>
                {data.status}
              </span>
            )}
          </div>

          {hasTracking && (
            <div className="mt-2 flex items-center gap-2 text-[10px] text-slate-600 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-2">
              <Truck size={12} className="text-slate-400 shrink-0" />
              <div className="min-w-0 flex-1 flex items-center gap-2">
                {data.carrier && <span className="font-black truncate">{data.carrier}</span>}
                {data.trackingNumber && <span className="font-mono text-slate-700 truncate">{data.trackingNumber}</span>}
              </div>
              {data.trackingUrl && (
                <a
                  href={data.trackingUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="shrink-0 text-fiido font-black hover:underline inline-flex items-center gap-1"
                >
                  查看 <ExternalLink size={12} />
                </a>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Markdown 图片正则: ![alt](url)
const MARKDOWN_IMAGE_REGEX = /!\[([^\]]*)\]\(([^)]+)\)/g;

// 渲染 Markdown 图片
const ImagePreview: React.FC<{ src: string; alt: string }> = ({ src, alt }) => {
  const [error, setError] = useState(false);
  const [isZoomed, setIsZoomed] = useState(false);

  if (error) {
    return (
      <div className="inline-flex items-center gap-2 px-3 py-2 bg-slate-100 rounded-lg text-slate-500 text-[11px]">
        <ShoppingBag size={14} />
        <span>图片加载失败</span>
      </div>
    );
  }

  return (
    <>
      <div className="relative inline-block group">
        <img
          src={src}
          alt={alt || 'image'}
          className="max-w-[240px] max-h-[180px] rounded-lg border border-slate-200 cursor-pointer hover:opacity-90 transition-all"
          onError={() => setError(true)}
          onClick={() => setIsZoomed(true)}
        />
        <div
          className="absolute inset-0 bg-black/0 group-hover:bg-black/10 rounded-lg transition-all flex items-center justify-center opacity-0 group-hover:opacity-100 cursor-pointer"
          onClick={() => setIsZoomed(true)}
        >
          <ZoomIn size={20} className="text-white drop-shadow-lg" />
        </div>
      </div>

      {/* 图片放大预览 */}
      {isZoomed && (
        <div
          className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 cursor-pointer"
          onClick={() => setIsZoomed(false)}
        >
          <img
            src={src}
            alt={alt || 'image'}
            className="max-w-[90vw] max-h-[90vh] rounded-lg shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          />
          <button
            onClick={() => setIsZoomed(false)}
            className="absolute top-4 right-4 text-white text-2xl hover:opacity-80"
          >
            ×
          </button>
        </div>
      )}
    </>
  );
};

// 渲染带图片支持的消息内容
const renderMessageWithImages = (content: string): React.ReactNode => {
  // 检查是否包含 Markdown 图片
  if (!content.includes('![')) {
    return content;
  }

  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let partIndex = 0;

  MARKDOWN_IMAGE_REGEX.lastIndex = 0;
  while ((match = MARKDOWN_IMAGE_REGEX.exec(content)) !== null) {
    const startIndex = match.index;
    const endIndex = match.index + match[0].length;

    // 添加图片前的文本
    if (startIndex > lastIndex) {
      const text = content.slice(lastIndex, startIndex);
      if (text.trim()) {
        parts.push(
          <span key={`t-${partIndex}`} className="whitespace-pre-wrap">
            {text}
          </span>
        );
        partIndex += 1;
      }
    }

    // 添加图片
    const alt = match[1] || '';
    const src = match[2] || '';
    parts.push(
      <div key={`img-${partIndex}`} className="my-2">
        <ImagePreview src={src} alt={alt} />
      </div>
    );
    partIndex += 1;

    lastIndex = endIndex;
  }

  // 添加剩余文本
  if (lastIndex < content.length) {
    const text = content.slice(lastIndex);
    if (text.trim()) {
      parts.push(
        <span key={`t-${partIndex}`} className="whitespace-pre-wrap">
          {text}
        </span>
      );
    }
  }

  return <div className="space-y-1">{parts}</div>;
};

const renderProductCardMessage = (content: string): React.ReactNode => {
  // 先检查是否有商品卡片
  if (!content || !content.includes('[PRODUCT]')) {
    // 没有商品卡片，检查是否有图片
    return renderMessageWithImages(content);
  }

  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let partIndex = 0;

  PRODUCT_CARD_REGEX.lastIndex = 0;
  while ((match = PRODUCT_CARD_REGEX.exec(content)) !== null) {
    const startIndex = match.index;
    const endIndex = match.index + match[0].length;

    if (startIndex > lastIndex) {
      const text = content.slice(lastIndex, startIndex);
      if (text.trim()) {
        parts.push(
          <div key={`t-${partIndex}`} className="whitespace-pre-wrap">
            {text}
          </div>
        );
        partIndex += 1;
      }
    }

    const raw = match[1] || '';
    parts.push(<ProductCard key={`p-${partIndex}`} data={parseProductCardData(raw)} />);
    partIndex += 1;

    lastIndex = endIndex;
  }

  if (lastIndex < content.length) {
    const text = content.slice(lastIndex);
    if (text.trim()) {
      parts.push(
        <div key={`t-${partIndex}`} className="whitespace-pre-wrap">
          {text}
        </div>
      );
    }
  }

  return <div className="space-y-2">{parts}</div>;
};

const MessageContent: React.FC<{ content: string }> = ({ content }) => {
  const rendered = useMemo(() => renderProductCardMessage(content), [content]);
  return <>{rendered}</>;
};

export default MessageContent;

