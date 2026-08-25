import React, { useState, useEffect } from 'react';
import {
  Shield,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Flame,
  Info,
  MessageSquare,
  Activity
} from 'lucide-react';
import { DataSourcesModal } from './ui/DataSourcesModal';

import { Matrix, MatrixText, MatrixNumber, wave } from './ui/matrix';

interface TopbarProps {
  criticalAlerts?: string[];
  onToggleSim?: () => void;
  isSimActive?: boolean;
  solarMetrics?: { ap: number; f10_7: number; drag_scaler: number } | null;
  trackedCount?: number;
  onToggleCopilot?: () => void;
  isCopilotOpen?: boolean;
}

export const Topbar: React.FC<TopbarProps> = ({
  criticalAlerts = [
    "ISS vs COSMOS 2251: Critical conjunction (Pc 2.3e-4) in T-18h",
    "Severe CME: Solar flux spike >220 sfu detected",
    "CALSPHERE 1: Orbit decay below 130 km threshold"
  ],
  onToggleSim,
  isSimActive = false,
  solarMetrics,
  trackedCount = 104,
  onToggleCopilot,
  isCopilotOpen = false
}) => {
  const [istTime, setIstTime] = useState('');
  const [activeAlertIndex, setActiveAlertIndex] = useState(0);
  const [showDataSources, setShowDataSources] = useState(false);

  // Live IST Clock (Indian Standard Time, UTC+5:30)
  useEffect(() => {
    const tick = () => {
      const d = new Date();
      const options: Intl.DateTimeFormatOptions = {
        timeZone: 'Asia/Kolkata',
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      };
      setIstTime(new Intl.DateTimeFormat('en-GB', options).format(d));
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  // Alert cycling
  useEffect(() => {
    if (criticalAlerts.length <= 1) return;
    const interval = setInterval(() => {
      setActiveAlertIndex(prev => (prev + 1) % criticalAlerts.length);
    }, 6000);
    return () => clearInterval(interval);
  }, [criticalAlerts]);

  const dragVal = solarMetrics?.drag_scaler ?? 1.94;

  return (
    <>
      <header className="w-full sticky top-0 z-50 px-4 sm:px-6 py-3 flex items-center justify-between gap-4 bg-transparent border-none pointer-events-none select-none">
        
        {/* ── LEFT: Clean Brand + Live IST Clock Capsule ──────── */}
        <div className="flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-[#0c0d12]/85 backdrop-blur-2xl border border-white/[0.12] shadow-xl pointer-events-auto shrink-0">
          <div className="h-6 w-6 rounded-lg bg-white/[0.08] border border-white/[0.14] flex items-center justify-center text-white shadow-inner">
            <Shield className="h-3.5 w-3.5" />
          </div>

          <MatrixText
            text="ORVEXA"
            size={1.6}
            gap={0.5}
            charGap={1.8}
            palette={{ on: '#ffffff', off: 'rgba(255,255,255,0.06)' }}
          />

          <div className="hidden sm:flex items-center gap-1.5 pl-2.5 ml-1 border-l border-white/[0.1] font-mono text-[10px] text-white/70">
            <div className="flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-400">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <MatrixText
                text="LIVE"
                size={1.2}
                gap={0.4}
                charGap={1.2}
                palette={{ on: '#34d399', off: 'rgba(52,211,153,0.1)' }}
              />
            </div>
            <MatrixNumber
              value={istTime}
              size={1.5}
              gap={0.5}
              digitGap={1.5}
              palette={{ on: '#ffffff', off: 'rgba(255,255,255,0.06)' }}
              className="pl-0.5"
            />
            <span className="text-[8px] font-bold text-white/50">IST</span>
          </div>
        </div>

        {/* ── CENTER: Clean Alert Ticker Capsule ── */}
        <div className="hidden md:flex flex-1 max-w-md items-center justify-between gap-2.5 px-3.5 py-1.5 rounded-full bg-[#0c0d12]/85 backdrop-blur-2xl border border-white/[0.12] shadow-xl pointer-events-auto">
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-rose-500/15 border border-rose-500/30 text-rose-400 font-mono text-[8.5px] font-bold tracking-wider shrink-0">
              <AlertTriangle className="h-2.5 w-2.5" />
              ALERT {activeAlertIndex + 1}/{criticalAlerts.length}
            </span>
            
            <span
              key={activeAlertIndex}
              className="text-[10.5px] font-mono text-white/80 truncate"
              title={criticalAlerts[activeAlertIndex]}
            >
              {criticalAlerts[activeAlertIndex]}
            </span>
          </div>

          <div className="flex items-center gap-0.5 shrink-0">
            <button
              onClick={() => setActiveAlertIndex(prev => (prev - 1 + criticalAlerts.length) % criticalAlerts.length)}
              className="p-1 text-white/40 hover:text-white transition-colors cursor-pointer"
            >
              <ChevronLeft className="h-3 w-3" />
            </button>
            <button
              onClick={() => setActiveAlertIndex(prev => (prev + 1) % criticalAlerts.length)}
              className="p-1 text-white/40 hover:text-white transition-colors cursor-pointer"
            >
              <ChevronRight className="h-3 w-3" />
            </button>
          </div>
        </div>

        {/* ── RIGHT: Minimal Floating Telemetry + Action Capsules ────────── */}
        <div className="flex items-center gap-2 shrink-0 font-mono text-[10px] pointer-events-auto">
          
          {/* Live Telemetry Radar / Solar Wave Matrix */}
          <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#0c0d12]/85 backdrop-blur-2xl border border-white/[0.12] shadow-xl">
            <Matrix
              rows={5}
              cols={7}
              frames={wave}
              size={2}
              gap={0.8}
              palette={{ on: '#38bdf8', off: 'rgba(255,255,255,0.06)' }}
              fps={18}
            />
            <MatrixText
              text="RADAR"
              size={1.3}
              gap={0.4}
              charGap={1.3}
              palette={{ on: '#38bdf8', off: 'rgba(56,189,248,0.1)' }}
            />
          </div>

          {/* Tracked Count & Drag Pill */}
          <div className="hidden sm:flex items-center rounded-full bg-[#0c0d12]/85 backdrop-blur-2xl border border-white/[0.12] shadow-xl px-3 py-1.5 gap-2 text-white/80">
            <span className="flex items-center gap-1.5 text-cyan-300 font-bold">
              <MatrixNumber
                value={trackedCount}
                size={1.5}
                gap={0.5}
                digitGap={1.5}
                palette={{ on: '#38bdf8', off: 'rgba(56,189,248,0.1)' }}
              />
              <span className="text-[9px]">SATS</span>
            </span>
            <span className="text-white/20">•</span>
            <span className="flex items-center gap-1 text-emerald-400 font-bold">
              <Flame className="h-3 w-3" />
              {dragVal.toFixed(1)}x Drag
            </span>
          </div>

          {/* Info Button */}
          <button
            onClick={() => setShowDataSources(true)}
            className="p-2 rounded-full bg-[#0c0d12]/85 backdrop-blur-2xl border border-white/[0.12] shadow-xl hover:bg-white/[0.08] text-white/50 hover:text-white transition-all cursor-pointer"
            title="Data Sources"
          >
            <Info size={12} />
          </button>

          {/* AI Copilot Button */}
          {onToggleCopilot && (
            <button
              onClick={onToggleCopilot}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full font-bold tracking-wider transition-all cursor-pointer backdrop-blur-2xl shadow-xl ${
                isCopilotOpen
                  ? 'bg-emerald-500/20 border border-emerald-500/50 text-emerald-300 shadow-[0_0_12px_rgba(16,185,129,0.3)]'
                  : 'bg-[#0c0d12]/85 border border-white/[0.12] hover:bg-white/[0.08] text-white/80 hover:text-white'
              }`}
            >
              <MessageSquare className="h-3 w-3 text-emerald-400" />
              <span className="hidden sm:inline">COPILOT</span>
            </button>
          )}

          {/* Sim Flare Button */}
          {onToggleSim && (
            <button
              onClick={onToggleSim}
              className={`flex items-center gap-1 p-2 rounded-full border transition-all cursor-pointer backdrop-blur-2xl shadow-xl ${
                isSimActive
                  ? 'bg-rose-500/20 border border-rose-500/50 text-rose-300 shadow-[0_0_10px_rgba(244,63,94,0.25)] animate-pulse'
                  : 'bg-[#0c0d12]/85 border border-white/[0.12] text-white/50 hover:text-white'
              }`}
              title={isSimActive ? 'Clear Flare Sim' : 'Trigger Solar Flare Sim'}
            >
              <Activity className="h-3 w-3" />
            </button>
          )}

        </div>
      </header>

      {/* Data Sources Transparency Modal */}
      <DataSourcesModal
        isOpen={showDataSources}
        onClose={() => setShowDataSources(false)}
      />
    </>
  );
};


