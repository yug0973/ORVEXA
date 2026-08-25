import React, { useEffect, useRef } from 'react';
import './SpaceBackground.css';

interface Star {
  x: number;
  y: number;
  z: number; // depth layer: 0 (far) to 1 (near)
  radius: number;
  color: string;
  baseAlpha: number;
  twinkleSpeed: number;
  twinklePhase: number;
  hasSpikes?: boolean;
}

export const SpaceBackground: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d', { alpha: false });
    if (!ctx) return;

    let animationFrameId: number;
    let width = 0;
    let height = 0;
    let dpr = Math.min(window.devicePixelRatio || 1, 2);

    // Load authentic high-resolution photographic Milky Way galaxy
    const galaxyImg = new Image();
    galaxyImg.src = '/assets/milky_way_galaxy.jpg';
    let galaxyLoaded = false;
    galaxyImg.onload = () => {
      galaxyLoaded = true;
    };

    // Realistic stellar colors (pure white, cold diamond blue, warm stellar gold - NO purple)
    const starColors = [
      'rgba(255, 255, 255, ', // Pure Stellar White
      'rgba(230, 242, 255, ', // Cool Blue-White (Type B)
      'rgba(210, 235, 255, ', // Diamond Blue (Type O)
      'rgba(255, 250, 235, ', // Warm Sunlight (Type G)
      'rgba(255, 230, 200, ', // Soft Warm Gold (Type K)
    ];

    let stars: Star[] = [];

    const initScene = () => {
      width = canvas.parentElement?.clientWidth || window.innerWidth;
      height = canvas.parentElement?.clientHeight || window.innerHeight;

      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;

      // Generate 1,800+ realistic micro-pinpoint stars
      const numStars = Math.floor(Math.max(width, height) * 1.4);
      stars = [];

      for (let i = 0; i < numStars; i++) {
        const x = Math.random() * width;
        const y = Math.random() * height;
        const z = Math.random(); // 0 = distant background, 1 = foreground

        const sizeRand = Math.random();
        let radius = 0.4 + Math.random() * 0.45; // Default micro-pinpoint star
        let baseAlpha = 0.35 + Math.random() * 0.55;
        let hasSpikes = false;

        // Realistic stellar magnitude distribution
        if (sizeRand > 0.988) {
          // Rare bright navigation star with optical spikes
          radius = 1.4 + Math.random() * 0.7;
          baseAlpha = 0.9 + Math.random() * 0.1;
          hasSpikes = true;
        } else if (sizeRand > 0.88) {
          // Medium field star
          radius = 0.8 + Math.random() * 0.4;
          baseAlpha = 0.6 + Math.random() * 0.3;
        } else {
          // Deep cosmic star dust (crisp micro subpixel)
          radius = 0.35 + Math.random() * 0.35;
          baseAlpha = 0.2 + Math.random() * 0.45;
        }

        const colorBase = starColors[Math.floor(Math.random() * starColors.length)];

        stars.push({
          x,
          y,
          z,
          radius,
          color: colorBase,
          baseAlpha,
          twinkleSpeed: 0.6 + Math.random() * 2.0,
          twinklePhase: Math.random() * Math.PI * 2,
          hasSpikes
        });
      }
    };

    initScene();

    const handleResize = () => {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      initScene();
    };

    window.addEventListener('resize', handleResize);

    // Animation Loop (Continuous smooth cosmic motion)
    let lastTime = performance.now();
    let galaxyOffsetX = 0;
    let galaxyOffsetY = 0;

    const render = (currentTime: number) => {
      const delta = Math.min((currentTime - lastTime) / 1000, 0.1);
      lastTime = currentTime;

      const timeSec = currentTime * 0.001;

      // Slow cosmic motion: galaxy and stars drift continuously across space
      const driftSpeed = 3.2; // pixels per second
      const driftAngle = -0.45; // diagonal drift direction
      const driftX = Math.cos(driftAngle) * driftSpeed * delta;
      const driftY = Math.sin(driftAngle) * driftSpeed * delta;

      galaxyOffsetX = (galaxyOffsetX - driftX * 0.25) % (width * 0.3);
      galaxyOffsetY = (galaxyOffsetY - driftY * 0.25) % (height * 0.3);

      ctx.save();
      ctx.scale(dpr, dpr);

      // 1. True 100% Pitch-Black Deep Space Void Base (NO purple/indigo wash)
      ctx.fillStyle = '#000000';
      ctx.fillRect(0, 0, width, height);

      // 2. Draw Real Photographic Milky Way Galaxy with Soft Cosmic Blend
      if (galaxyLoaded && galaxyImg.naturalWidth > 0) {
        ctx.save();

        // Position galaxy diagonally across viewport
        const gScale = Math.max(width / galaxyImg.naturalWidth, height / galaxyImg.naturalHeight) * 1.5;
        const gw = galaxyImg.naturalWidth * gScale;
        const gh = galaxyImg.naturalHeight * gScale;

        const gcx = width * 0.5 + galaxyOffsetX;
        const gcy = height * 0.5 + galaxyOffsetY;

        ctx.translate(gcx, gcy);
        // Subtle slow galactic rotation
        ctx.rotate(-0.38 + Math.sin(timeSec * 0.01) * 0.01);

        // Render real photographic galaxy
        ctx.globalAlpha = 0.85;
        ctx.drawImage(galaxyImg, -gw / 2, -gh / 2, gw, gh);

        ctx.restore();
      }

      // 3. Draw Dynamic Starfield with Multi-Layer Parallax Motion
      for (let i = 0; i < stars.length; i++) {
        const star = stars[i];

        // Cosmic motion: foreground stars move faster than background stars
        star.x -= driftX * (0.4 + star.z * 0.8);
        star.y -= driftY * (0.4 + star.z * 0.8);

        // Seamless infinite boundary wrapping
        if (star.x < -15) star.x += width + 30;
        if (star.x > width + 15) star.x -= width + 30;
        if (star.y < -15) star.y += height + 30;
        if (star.y > height + 15) star.y -= height + 30;

        // Real stellar scintillation / twinkling
        const twinkle = Math.sin(timeSec * star.twinkleSpeed + star.twinklePhase);
        const currentAlpha = Math.max(0.12, Math.min(1.0, star.baseAlpha * (0.8 + 0.2 * twinkle)));

        ctx.fillStyle = `${star.color}${currentAlpha.toFixed(3)})`;

        // Crisp pinpoint star rendering
        ctx.beginPath();
        ctx.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
        ctx.fill();

        // Optical diffraction spikes & subtle natural glow on bright stars
        if (star.hasSpikes) {
          const glowRadius = star.radius * 3.5;
          const glowGrad = ctx.createRadialGradient(star.x, star.y, 0, star.x, star.y, glowRadius);
          glowGrad.addColorStop(0, `${star.color}${(currentAlpha * 0.4).toFixed(3)})`);
          glowGrad.addColorStop(0.6, `${star.color}${(currentAlpha * 0.1).toFixed(3)})`);
          glowGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');

          ctx.fillStyle = glowGrad;
          ctx.beginPath();
          ctx.arc(star.x, star.y, glowRadius, 0, Math.PI * 2);
          ctx.fill();

          // Delicate 4-point cross spike
          ctx.strokeStyle = `${star.color}${(currentAlpha * 0.35).toFixed(3)})`;
          ctx.lineWidth = 0.6;
          const spikeLen = star.radius * 4.2;

          ctx.beginPath();
          ctx.moveTo(star.x - spikeLen, star.y);
          ctx.lineTo(star.x + spikeLen, star.y);
          ctx.moveTo(star.x, star.y - spikeLen);
          ctx.lineTo(star.x, star.y + spikeLen);
          ctx.stroke();
        }
      }

      ctx.restore();
      animationFrameId = requestAnimationFrame(render);
    };

    animationFrameId = requestAnimationFrame(render);

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div className="space-canvas-wrapper">
      <canvas ref={canvasRef} className="space-canvas" />
      <div className="space-vignette" />
    </div>
  );
};

export default SpaceBackground;
