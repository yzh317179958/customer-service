import React, { useMemo, useState } from 'react';
import { ExternalLink, ShoppingBag, Truck } from 'lucide-react';

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

const renderProductCardMessage = (content: string): React.ReactNode => {
  if (!content || !content.includes('[PRODUCT]')) {
    return content;
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

