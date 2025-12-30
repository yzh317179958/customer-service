import React from 'react';
import { Play, Zap } from 'lucide-react';

interface VideoPlayerProps {
  poster?: string;
  title?: string;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({ poster, title = "产品演示" }) => {
  return (
    <div className="relative group cursor-pointer aspect-video w-full rounded-3xl overflow-hidden bg-slate-900 border border-bg-200 shadow-2xl">
      {/* 视频封面图占位 */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-800 to-slate-950 flex items-center justify-center">
        <div className="absolute inset-0 opacity-20 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')]"></div>
        <div className="text-center relative z-10">
          <div className="w-20 h-20 bg-brand-600 rounded-full flex items-center justify-center text-white mx-auto mb-4 shadow-xl shadow-brand-600/40 group-hover:scale-110 transition-transform duration-500">
            <Play size={32} fill="currentColor" />
          </div>
          <p className="text-white/60 font-bold uppercase tracking-widest text-xs">{title} (3:00)</p>
        </div>
      </div>
      
      {/* 悬浮装饰 */}
      <div className="absolute top-4 left-4">
        <div className="flex items-center gap-2 px-3 py-1 bg-black/40 backdrop-blur-md rounded-full border border-white/10">
          <Zap className="w-3 h-3 text-brand-400 fill-current" />
          <span className="text-[10px] text-white font-bold tracking-tight">AI PREVIEW</span>
        </div>
      </div>
    </div>
  );
};

export default VideoPlayer;