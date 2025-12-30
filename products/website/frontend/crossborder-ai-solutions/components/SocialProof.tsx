import React from 'react';

const SocialProof: React.FC = () => {
  const logos = [
    "Acme Corp", "GlobalBank", "Nebula", "Tesseract", "Oasis", "Vertex"
  ];

  return (
    <section className="py-12 border-y border-slate-900 bg-slate-950/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <p className="text-center text-sm font-semibold text-slate-500 mb-8 uppercase tracking-wider">
          深受全球顶尖技术团队信赖
        </p>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-8 items-center justify-items-center opacity-60 grayscale hover:grayscale-0 transition-all duration-500">
          {/* Placeholder for Logos - Using text for prototype, normally SVGs */}
          {logos.map((logo, index) => (
            <div key={index} className="text-xl font-bold text-slate-400 flex items-center gap-2 hover:text-white transition-colors cursor-default">
              <div className="h-6 w-6 rounded bg-slate-800"></div>
              {logo}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default SocialProof;