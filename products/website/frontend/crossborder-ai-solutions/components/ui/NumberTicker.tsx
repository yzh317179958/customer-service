import React, { useEffect, useState, useRef } from 'react';
import { useInView } from 'framer-motion'; // Assuming framer-motion might not be installed, we'll use a simple IntersectionObserver approach

interface NumberTickerProps {
  value: number;
  duration?: number;
  suffix?: string;
  className?: string;
}

const NumberTicker: React.FC<NumberTickerProps> = ({ value, duration = 2000, suffix = '', className }) => {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const [hasAnimated, setHasAnimated] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated) {
          setHasAnimated(true);
        }
      },
      { threshold: 0.1 }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => observer.disconnect();
  }, [hasAnimated]);

  useEffect(() => {
    if (!hasAnimated) return;

    let startTime: number | null = null;
    const animate = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const progress = timestamp - startTime;
      const percentage = Math.min(progress / duration, 1);
      
      // Easing function (easeOutExpo)
      const ease = (x: number) => (x === 1 ? 1 : 1 - Math.pow(2, -10 * x));
      
      setCount(Math.floor(ease(percentage) * value));

      if (progress < duration) {
        requestAnimationFrame(animate);
      } else {
        setCount(value);
      }
    };

    requestAnimationFrame(animate);
  }, [value, duration, hasAnimated]);

  return (
    <span ref={ref} className={className}>
      {count}{suffix}
    </span>
  );
};

export default NumberTicker;