import React from 'react';
import './StarfieldBackground.css';

export const StarfieldBackground: React.FC = () => {
  return (
    <div className="absolute inset-0 overflow-hidden bg-[#000000] -z-10 pointer-events-none">
      <div className="stars-container absolute inset-0">
        {/* Layer 1: Slow moving tiny stars */}
        <div className="star-layer star-layer-1"></div>
        {/* Layer 2: Medium moving small stars */}
        <div className="star-layer star-layer-2"></div>
        {/* Layer 3: Fast moving larger stars */}
        <div className="star-layer star-layer-3"></div>
      </div>
      
      {/* Subtle monochrome vignette behind earth */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[60vh] h-[60vh] bg-white/[0.02] blur-[100px] rounded-full pointer-events-none"></div>
    </div>
  );
};

export default StarfieldBackground;
