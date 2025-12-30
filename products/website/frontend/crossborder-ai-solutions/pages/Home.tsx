import React from 'react';
import Hero from '../components/Hero';
import ProductMatrix from '../components/ProductMatrix';
import CustomizationSection from '../components/EcosystemIntegration';
import Cases from '../components/Cases';
import Pricing from '../components/Pricing';
import CTA from '../components/CTA';

const Home: React.FC<{ navigate: any }> = ({ navigate }) => {
  return (
    <div className="flex flex-col">
      {/* 1. 核心价值：快速了解产品定位 */}
      <Hero />
      
      {/* 2. 产品矩阵：AI智能客服 与 坐席工作台 的功能详述 */}
      <ProductMatrix onNavigate={navigate} />
      
      {/* 3. 核心能力：深度定制化展示 */}
      <CustomizationSection />
      
      {/* 4. 信任背书：真实客户案例 */}
      <Cases />
      
      {/* 5. 商业转化：定价方案 */}
      <Pricing />
      
      {/* 6. 行动号召 */}
      <CTA />
    </div>
  );
};

export default Home;