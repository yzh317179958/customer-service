import React from 'react';

const Testimonials: React.FC = () => {
  const testimonials = [
    {
      quote: "NovaStream 彻底改变了我们处理 ETL 管道的方式。以前需要几天的工作，现在只需几分钟就能完成。",
      author: "Sarah Jenkins",
      role: "VP of Engineering at TechFlow",
      image: "https://picsum.photos/100/100?random=1"
    },
    {
      quote: "可观测性功能简直是游戏规则改变者。我们在部署数小时内就发现了一个严重的数据泄露隐患。",
      author: "Michael Chen",
      role: "CTO at DataSphere",
      image: "https://picsum.photos/100/100?random=2"
    },
    {
      quote: "终于有一款尊重开发者体验的工具了。CLI 非常直观，API 坚如磐石，文档也极其详细。",
      author: "Elena Rodriguez",
      role: "Lead Architect at CloudScale",
      image: "https://picsum.photos/100/100?random=3"
    }
  ];

  return (
    <section className="py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-3xl md:text-5xl font-bold text-center text-white mb-16">
          深受开发者喜爱
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {testimonials.map((t, idx) => (
            <div key={idx} className="bg-slate-900 border border-slate-800 p-8 rounded-2xl flex flex-col justify-between hover:border-brand-500/30 transition-colors hover:shadow-lg hover:shadow-brand-500/5 group">
              <div>
                <div className="flex text-brand-400 mb-4 group-hover:scale-105 transition-transform origin-left">
                  {[...Array(5)].map((_, i) => (
                    <svg key={i} className="w-5 h-5 fill-current" viewBox="0 0 20 20">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  ))}
                </div>
                <p className="text-slate-300 text-lg mb-6 leading-relaxed">"{t.quote}"</p>
              </div>
              <div className="flex items-center gap-4">
                <img src={t.image} alt={t.author} className="w-12 h-12 rounded-full border border-slate-700 grayscale group-hover:grayscale-0 transition-all" />
                <div>
                  <div className="text-white font-medium">{t.author}</div>
                  <div className="text-slate-500 text-sm">{t.role}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Testimonials;