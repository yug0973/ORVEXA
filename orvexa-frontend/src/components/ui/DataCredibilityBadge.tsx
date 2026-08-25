import React, { useState } from 'react';
import { ShieldCheck, Calculator, History, Sparkles, Info } from 'lucide-react';

export type CredibilityType = 'LIVE DATA' | 'ESTIMATED' | 'HISTORICAL RECONSTRUCTION' | 'DEMO SIMULATION';

interface DataCredibilityBadgeProps {
  type: CredibilityType;
  className?: string;
  sourceLabel?: string;
  showIcon?: boolean;
  size?: 'xs' | 'sm' | 'md';
}

const BADGE_CONFIGS: Record<CredibilityType, {
  label: string;
  dotColor: string;
  style: string;
  icon: React.ComponentType<any>;
  description: string;
}> = {
  'LIVE DATA': {
    label: 'LIVE',
    dotColor: 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]',
    style: 'bg-emerald-500/[0.08] text-emerald-300 border-emerald-500/25 hover:border-emerald-500/40 hover:bg-emerald-500/[0.12]',
    icon: ShieldCheck,
    description: 'Directly ingested from verified external telemetry (CelesTrak / Space-Track SGP4 TLEs or NOAA SWPC solar feeds).'
  },
  'ESTIMATED': {
    label: 'ESTIMATED',
    dotColor: 'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.8)]',
    style: 'bg-amber-500/[0.08] text-amber-300 border-amber-500/25 hover:border-amber-500/40 hover:bg-amber-500/[0.12]',
    icon: Calculator,
    description: 'Propagated via SGP4 astrodynamics, Chan analytical Rician series, or RK4 atmospheric decay with standardized covariance.'
  },
  'HISTORICAL RECONSTRUCTION': {
    label: 'HISTORICAL',
    dotColor: 'bg-sky-400 shadow-[0_0_8px_rgba(56,189,248,0.8)]',
    style: 'bg-sky-500/[0.08] text-sky-300 border-sky-500/25 hover:border-sky-500/40 hover:bg-sky-500/[0.12]',
    icon: History,
    description: 'Parametric physics reconstruction modeled from verified historical collision energetics.'
  },
  'DEMO SIMULATION': {
    label: 'SIMULATION',
    dotColor: 'bg-indigo-400 shadow-[0_0_8px_rgba(129,140,248,0.8)]',
    style: 'bg-indigo-500/[0.08] text-indigo-300 border-indigo-500/25 hover:border-indigo-500/40 hover:bg-indigo-500/[0.12]',
    icon: Sparkles,
    description: 'Parametric simulation generated for operational stress testing and mission rehearsal.'
  }
};

export const DataCredibilityBadge: React.FC<DataCredibilityBadgeProps> = ({
  type,
  className = '',
  sourceLabel,
  showIcon = true,
  size = 'xs'
}) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const cfg = BADGE_CONFIGS[type] || BADGE_CONFIGS['ESTIMATED'];
  const Icon = cfg.icon;

  const sizeClasses = {
    xs: 'text-[8.5px] px-2 py-0.5 gap-1.5',
    sm: 'text-[9.5px] px-2.5 py-0.5 gap-1.5',
    md: 'text-[10.5px] px-3 py-1 gap-2'
  }[size];

  return (
    <div className="relative inline-flex items-center shrink-0">
      <span
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onClick={() => setShowTooltip(!showTooltip)}
        className={`inline-flex items-center font-mono font-semibold tracking-wider rounded-full border backdrop-blur-md transition-all duration-200 select-none cursor-help shrink-0 whitespace-nowrap ${cfg.style} ${sizeClasses} ${className}`}
        title={`${cfg.label}: ${cfg.description}`}
      >
        <span className={`h-1.5 w-1.5 rounded-full ${cfg.dotColor} shrink-0 animate-pulse`} />
        {showIcon && <Icon className="h-2.5 w-2.5 shrink-0 opacity-70" />}
        <span className="shrink-0">{cfg.label}</span>
        {sourceLabel && (
          <span className="opacity-60 font-mono font-normal tracking-normal border-l border-current/25 pl-1.5 ml-0.5 shrink-0 truncate max-w-[130px]">
            {sourceLabel}
          </span>
        )}
      </span>

      {/* Floating Info Tooltip */}
      {showTooltip && (
        <div className="absolute bottom-full right-0 mb-2 w-64 p-3 rounded-xl bg-[#0d0d12]/95 backdrop-blur-2xl border border-white/[0.12] shadow-2xl text-[10px] font-sans text-white/90 z-50 pointer-events-none animate-in fade-in zoom-in-95 duration-150 leading-relaxed">
          <div className="flex items-center gap-1.5 font-mono font-bold text-[9px] text-white/70 uppercase mb-1.5 border-b border-white/[0.08] pb-1">
            <Info className="h-3 w-3 text-white/60" />
            <span>Astrometry Credibility Note</span>
          </div>
          <p className="text-white/80 font-normal leading-normal">{cfg.description}</p>
        </div>
      )}
    </div>
  );
};

