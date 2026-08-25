import React, { useEffect, useRef, useMemo } from 'react';
import gsap from 'gsap';
import './ScrambledText.css';

export interface ScrambledTextProps {
  radius?: number;
  duration?: number;
  speed?: number;
  scrambleChars?: string;
  className?: string;
  style?: React.CSSProperties;
  children: React.ReactNode;
  as?: 'h1' | 'h2' | 'h3' | 'h4' | 'p' | 'span' | 'div';
}

export const ScrambledText: React.FC<ScrambledTextProps> = ({
  radius = 100,
  duration = 1.2,
  speed = 0.5,
  scrambleChars = '.:!<>-_\\/[]{}—=+*^?#',
  className = '',
  style = {},
  children,
  as: Component = 'div'
}) => {
  const rootRef = useRef<HTMLElement | null>(null);
  const charsRef = useRef<(HTMLSpanElement | null)[]>([]);
  const intervalsRef = useRef<Map<number, number>>(new Map());

  // Extract raw text if children is a string
  const textContent = useMemo(() => {
    if (typeof children === 'string') return children;
    if (Array.isArray(children)) {
      return children.map(c => (typeof c === 'string' ? c : '')).join('');
    }
    return String(children || '');
  }, [children]);

  const chars = useMemo(() => textContent.split(''), [textContent]);

  useEffect(() => {
    const el = rootRef.current;
    if (!el) return;

    const charsPool = scrambleChars || '.:';

    const handleMove = (e: PointerEvent) => {
      charsRef.current.forEach((span, idx) => {
        if (!span) return;
        const rect = span.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        const dx = e.clientX - centerX;
        const dy = e.clientY - centerY;
        const dist = Math.hypot(dx, dy);

        if (dist < radius) {
          const originalChar = span.dataset.original || chars[idx] || '';
          if (!originalChar || originalChar === ' ') return;

          // Clear any active interval for this character
          if (intervalsRef.current.has(idx)) {
            window.clearInterval(intervalsRef.current.get(idx));
          }

          span.classList.add('is-scrambling');
          const scrambleDuration = Math.max(0.2, duration * (1 - dist / radius));
          const intervalMs = Math.max(20, 50 * speed);
          const endTime = performance.now() + scrambleDuration * 1000;

          // Animate character transform slightly with GSAP
          gsap.to(span, {
            y: (Math.random() - 0.5) * 2,
            duration: 0.1,
            overwrite: 'auto'
          });

          const intervalId = window.setInterval(() => {
            const now = performance.now();
            if (now >= endTime) {
              window.clearInterval(intervalId);
              intervalsRef.current.delete(idx);
              span.textContent = originalChar;
              span.classList.remove('is-scrambling');
              gsap.to(span, { y: 0, duration: 0.2, overwrite: 'auto' });
            } else {
              const randomChar = charsPool[Math.floor(Math.random() * charsPool.length)];
              span.textContent = randomChar;
            }
          }, intervalMs);

          intervalsRef.current.set(idx, intervalId);
        }
      });
    };

    el.addEventListener('pointermove', handleMove);

    const activeIntervals = intervalsRef.current;
    return () => {
      el.removeEventListener('pointermove', handleMove);
      activeIntervals.forEach(id => window.clearInterval(id));
      activeIntervals.clear();
    };
  }, [radius, duration, speed, scrambleChars, chars]);

  return React.createElement(
    Component,
    {
      ref: rootRef,
      className: `text-block select-none ${className}`,
      style
    },
    chars.map((char, index) => (
      <span
        key={index}
        ref={el => {
          charsRef.current[index] = el;
        }}
        data-original={char}
        className="scrambled-char"
      >
        {char}
      </span>
    ))
  );
};

export default ScrambledText;
