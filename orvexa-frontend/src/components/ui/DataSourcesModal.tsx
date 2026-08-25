import React from 'react';
import { ShieldCheck, Database, Sun, Calculator, Brain, X, CheckCircle2 } from 'lucide-react';
import { DataCredibilityBadge } from './DataCredibilityBadge';

interface DataSourcesModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DataSourcesModal: React.FC<DataSourcesModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="w-full max-w-2xl bg-[#0d0e14] border border-white/[0.14] rounded-2xl shadow-[0_25px_60px_rgba(0,0,0,0.9)] overflow-hidden flex flex-col font-sans max-h-[85vh]">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-white/[0.08] flex items-center justify-between bg-black/40">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white font-mono tracking-wide uppercase">
                Data Sources & Astrodynamics Integrity
              </h2>
              <p className="text-[11px] text-white/50">
                Official transparency statement of feeds, mathematical models, and AI engines.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-white/40 hover:text-white hover:bg-white/[0.06] transition cursor-pointer"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-4 text-xs">
          
          {/* Feed 1: Celestrak / Space-Track */}
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.07] flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-semibold text-white font-mono">
                <Database className="h-4 w-4 text-emerald-400" />
                <span>1. Satellite Orbital Ephemeris & TLE Catalog</span>
              </div>
              <DataCredibilityBadge type="LIVE DATA" sourceLabel="Celestrak" />
            </div>
            <p className="text-white/70 leading-relaxed text-[11.5px]">
              Active payloads, rocket bodies, and debris objects are ingested live via CelesTrak SGP4 Two-Line Element (TLE) ephemeris sets. State vectors are propagated using standardized SGP4 astrodynamics algorithms.
            </p>
          </div>

          {/* Feed 2: NOAA Space Weather */}
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.07] flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-semibold text-white font-mono">
                <Sun className="h-4 w-4 text-amber-400" />
                <span>2. Space Weather & Solar Flux Feeds</span>
              </div>
              <DataCredibilityBadge type="LIVE DATA" sourceLabel="NOAA SWPC / Aditya-L1" />
            </div>
            <p className="text-white/70 leading-relaxed text-[11.5px]">
              10.7 cm Solar Radio Flux (F10.7) and Planetary Geomagnetic Ap/Kp indices are streamed directly from NOAA Space Weather Prediction Center (SWPC) JSON endpoints, scaling Jacchia-Roberts/NRLMSISE-00 atmospheric density calculations.
            </p>
          </div>

          {/* Model 3: Collision Probability & B-Plane */}
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.07] flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-semibold text-white font-mono">
                <Calculator className="h-4 w-4 text-amber-400" />
                <span>3. Collision Screening (Pc) & B-Plane Geometry</span>
              </div>
              <DataCredibilityBadge type="ESTIMATED" sourceLabel="Chan Rician Series" />
            </div>
            <p className="text-white/70 leading-relaxed text-[11.5px]">
              Collision probabilities are computed using <strong>Ken Chan's analytical Rician series</strong> for 3D positional covariance ellipsoids projected onto the 2D B-Plane encounter coordinate system (K-Chan formulation). Standardized position uncertainties are assigned by object classification.
            </p>
          </div>

          {/* Model 4: Historical Replay */}
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.07] flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-semibold text-white font-mono">
                <ShieldCheck className="h-4 w-4 text-sky-400" />
                <span>4. Historical Conjunction Reconstructions</span>
              </div>
              <DataCredibilityBadge type="HISTORICAL RECONSTRUCTION" sourceLabel="NASA EVM Debris Energetics" />
            </div>
            <p className="text-white/70 leading-relaxed text-[11.5px]">
              Reconstructions of historical incidents (2009 Iridium-33 vs Cosmos-2251; 2007 Fengyun-1C) utilize actual catalogued encounter velocities and collision kinetic energy to compute debris fragmentation spreads.
            </p>
          </div>

          {/* Model 5: LLM Compliance */}
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.07] flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-semibold text-white font-mono">
                <Brain className="h-4 w-4 text-emerald-400" />
                <span>5. 6-Stage Compliance Pipeline & IN-SPACe Filings</span>
              </div>
              <DataCredibilityBadge type="LIVE DATA" sourceLabel="Local Llama 3.2 / Fallback" />
            </div>
            <p className="text-white/70 leading-relaxed text-[11.5px]">
              Compliance filings align strictly with IADC Space Debris Mitigation Guidelines and IN-SPACe 2024 Authorisation Norms. Generated justifications are produced by an air-gapped local LLM with rule-based deterministic fallback.
            </p>
          </div>

        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 border-t border-white/[0.08] bg-black/40 flex items-center justify-between">
          <div className="flex items-center gap-2 text-[10px] font-mono text-white/50">
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
            Zero synthetic data in core tracking telemetry
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-white text-black font-semibold text-xs hover:bg-white/90 transition cursor-pointer"
          >
            Close Overview
          </button>
        </div>

      </div>
    </div>
  );
};
