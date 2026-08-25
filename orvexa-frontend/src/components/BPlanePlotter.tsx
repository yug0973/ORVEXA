import React from 'react';
import { Crosshair } from 'lucide-react';

interface BPlanePlotterProps {
  covarianceMatrix?: number[][]; // 2x2 matrix
  missDistanceVector: [number, number]; // [x, y] offsets in km
  hbr?: number; // Hard-body radius in meters
}

export const BPlanePlotter: React.FC<BPlanePlotterProps> = ({
  covarianceMatrix = [[0.18, 0.04], [0.04, 0.08]], // Default realistic 2x2 covariance in km^2
  missDistanceVector,
  hbr = 15.0 // Default 15 meters hard body radius
}) => {
  // 1. Solve eigenvalues and rotation angle for the 2D projected covariance matrix
  const [[cxx, cxy], [, cyy]] = covarianceMatrix;
  
  const mean = (cxx + cyy) / 2.0;
  const diff = (cxx - cyy) / 2.0;
  const term = Math.sqrt(diff * diff + cxy * cxy);
  
  const lambda1 = mean + term; // Eigenvalue 1 (semi-major axis squared)
  const lambda2 = mean - term; // Eigenvalue 2 (semi-minor axis squared)

  // Calculate 1-sigma standard deviation lengths in km
  const a1 = Math.sqrt(Math.max(0, lambda1));
  const b1 = Math.sqrt(Math.max(0, lambda2));

  // Calculate rotation angle in degrees
  let rotationAngle = 0;
  if (cxy !== 0) {
    rotationAngle = 0.5 * Math.atan2(2 * cxy, cxx - cyy) * (180.0 / Math.PI);
  } else if (cxx < cyy) {
    rotationAngle = 90;
  }

  // 2. Setup dynamic auto-scaling logic so elements fit beautifully
  const [xOffset, yOffset] = missDistanceVector;
  const missDistance = Math.sqrt(xOffset * xOffset + yOffset * yOffset);
  
  // Calculate viewport boundaries based on the 3-sigma ellipse size and miss offset
  const maxAxis3Sigma = 3.0 * a1;
  const maxVal = Math.max(missDistance, maxAxis3Sigma, 0.1); // minimum bounding scale
  
  const marginMultiplier = 1.35;
  const scale = 175.0 / (maxVal * marginMultiplier); // px per km

  // Convert HBR from meters to km and then scale to pixels
  const hbrKm = hbr / 1000.0;
  const hbrPx = Math.max(5, hbrKm * scale);

  // Offset point coordinates in pixels (flip Y coordinate for SVG standard viewport)
  const xOffsetPx = xOffset * scale;
  const yOffsetPx = -yOffset * scale;

  // Generate grid concentric range rings
  const gridRings = [0.25, 0.5, 0.75, 1.0].map(pct => maxVal * marginMultiplier * pct);

  return (
    <div className="relative w-full flex flex-col group">
      {/* Top Header & Tactical Status */}
      <div className="flex items-center justify-between pb-2 mb-2 border-b border-white/[0.06]">
        <div className="flex items-center gap-2">
          <Crosshair className="h-3.5 w-3.5 text-white/70" />
          <h4 className="text-[11px] font-bold font-mono tracking-wider text-white uppercase">
            B-Plane Encounter Geometry
          </h4>
        </div>
        <div className="flex items-center gap-1.5 text-[9px] font-mono text-white/50">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
          2D Relative Plane
        </div>
      </div>

      {/* SVG Plot Container */}
      <div className="relative w-full aspect-square max-w-[340px] mx-auto flex items-center justify-center my-1">
        <svg 
          viewBox="-200 -200 400 400" 
          className="w-full h-full bg-black/40 border border-white/[0.04] rounded-xl shadow-inner select-none"
        >
          <defs>
            {/* Monochrome Radar Glow */}
            <radialGradient id="monoRadarGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="rgba(255, 255, 255, 0.03)" />
              <stop offset="60%" stopColor="rgba(255, 255, 255, 0.01)" />
              <stop offset="100%" stopColor="rgba(0, 0, 0, 0)" />
            </radialGradient>
          </defs>

          {/* Central Radar Glow */}
          <circle cx="0" cy="0" r="195" fill="url(#monoRadarGlow)" />

          {/* Tactical Axis Grid Lines & Concentric Rings */}
          <line x1="-195" y1="0" x2="195" y2="0" stroke="rgba(255, 255, 255, 0.1)" strokeWidth="1" strokeDasharray="3,3" />
          <line x1="0" y1="-195" x2="0" y2="195" stroke="rgba(255, 255, 255, 0.1)" strokeWidth="1" strokeDasharray="3,3" />
          
          {/* 45-degree tactical diagonals */}
          <line x1="-138" y1="-138" x2="138" y2="138" stroke="rgba(255, 255, 255, 0.04)" strokeWidth="0.75" strokeDasharray="2,4" />
          <line x1="-138" y1="138" x2="138" y2="-138" stroke="rgba(255, 255, 255, 0.04)" strokeWidth="0.75" strokeDasharray="2,4" />

          {/* Concentric Distance Rings */}
          {gridRings.map((r, i) => (
            <g key={i}>
              <circle
                cx="0"
                cy="0"
                r={r * scale}
                fill="none"
                stroke="rgba(255, 255, 255, 0.06)"
                strokeWidth="0.8"
                strokeDasharray="2,2"
              />
              <text
                x="5"
                y={-r * scale + 10}
                fill="rgba(255, 255, 255, 0.35)"
                fontSize="7"
                fontFamily="monospace"
                fontWeight="bold"
              >
                {r.toFixed(2)} km
              </text>
            </g>
          ))}

          {/* Uncertainty Covariance Ellipses (1-sigma, 2-sigma, 3-sigma) */}
          {/* 3-sigma (Red Outer Danger Zone) */}
          <ellipse
            cx="0"
            cy="0"
            rx={3 * a1 * scale}
            ry={3 * b1 * scale}
            transform={`rotate(${-rotationAngle})`}
            fill="rgba(244, 63, 94, 0.03)"
            stroke="rgba(244, 63, 94, 0.35)"
            strokeWidth="1.2"
            strokeDasharray="4,4"
          />

          {/* 2-sigma (Amber Transition Zone) */}
          <ellipse
            cx="0"
            cy="0"
            rx={2 * a1 * scale}
            ry={2 * b1 * scale}
            transform={`rotate(${-rotationAngle})`}
            fill="rgba(251, 191, 36, 0.04)"
            stroke="rgba(251, 191, 36, 0.5)"
            strokeWidth="1.2"
          />

          {/* 1-sigma (Monochrome Core Area) */}
          <ellipse
            cx="0"
            cy="0"
            rx={a1 * scale}
            ry={b1 * scale}
            transform={`rotate(${-rotationAngle})`}
            fill="rgba(255, 255, 255, 0.06)"
            stroke="rgba(255, 255, 255, 0.6)"
            strokeWidth="1.5"
          />

          {/* Primary Satellite (Origin Center Point + Hard-Body Radius) */}
          <circle
            cx="0"
            cy="0"
            r={hbrPx}
            fill="rgba(255, 255, 255, 0.15)"
            stroke="#ffffff"
            strokeWidth="1.2"
          />
          {/* Center Point */}
          <circle cx="0" cy="0" r="3" fill="#ffffff" />

          {/* Relative Vector from Origin to Secondary */}
          <line
            x1="0"
            y1="0"
            x2={xOffsetPx}
            y2={yOffsetPx}
            stroke="rgba(244, 63, 94, 0.5)"
            strokeWidth="1.2"
            strokeDasharray="3,3"
          />

          {/* Secondary Satellite Offset Target Point */}
          <g>
            <circle
              cx={xOffsetPx}
              cy={yOffsetPx}
              r="7"
              fill="rgba(244, 63, 94, 0.2)"
              stroke="#f43f5e"
              strokeWidth="1.2"
            />
            <circle
              cx={xOffsetPx}
              cy={yOffsetPx}
              r="3"
              fill="#f43f5e"
            />
            <circle
              cx={xOffsetPx}
              cy={yOffsetPx}
              r="1.5"
              fill="#ffffff"
            />
          </g>
        </svg>

        {/* Floating Legends */}
        <div className="absolute top-2 right-2 flex flex-col gap-1 font-mono text-[8.5px] text-white/70 bg-black/70 backdrop-blur-md px-2 py-1 rounded border border-white/[0.06]">
          <div className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-white"></span>
            <span>Primary (HBR)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-rose-500"></span>
            <span>Secondary</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-1 w-2 rounded bg-amber-400"></span>
            <span>2σ Boundary</span>
          </div>
        </div>
      </div>

      {/* Plot Technical Telemetry Breakdown */}
      <div className="grid grid-cols-3 gap-2 pt-2 border-t border-white/[0.04] font-mono text-[9.5px]">
        <div>
          <span className="text-white/30 block text-[8.5px]">COV ROTATION</span>
          <span className="text-white font-medium">{rotationAngle.toFixed(1)}°</span>
        </div>
        <div>
          <span className="text-white/30 block text-[8.5px]">1σ MAJOR AXIS</span>
          <span className="text-white font-medium">{(a1 * 1000).toFixed(0)} m</span>
        </div>
        <div>
          <span className="text-white/30 block text-[8.5px]">1σ MINOR AXIS</span>
          <span className="text-white font-medium">{(b1 * 1000).toFixed(0)} m</span>
        </div>
      </div>
    </div>
  );
};

export default BPlanePlotter;
