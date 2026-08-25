import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import { BPlanePlotter } from '../components/BPlanePlotter';
import { 
  AlertTriangle, 
  ShieldAlert, 
  ChevronRight, 
  FileText, 
  CheckCircle, 
  Navigation, 
  Activity, 
  Search, 
  RotateCcw, 
  Globe, 
  Radio, 
  ShieldCheck
} from 'lucide-react';
import type { ConjunctionEvent, ConjunctionDetails } from '../types';
import { Matrix } from '../components/ui/matrix';

interface TcaCountdownProps {
  tcaString: string;
}

const TcaCountdown: React.FC<TcaCountdownProps> = ({ tcaString }) => {
  const [timeLeft, setTimeLeft] = useState<string>("Calculating...");
  const [isUrgent, setIsUrgent] = useState<boolean>(false);
  const [isPassed, setIsPassed] = useState<boolean>(false);

  useEffect(() => {
    const tcaEpoch = new Date(tcaString).getTime();

    const updateCountdown = () => {
      const now = Date.now();
      const diff = tcaEpoch - now;

      if (diff <= 0) {
        const elapsed = Math.abs(diff);
        const hours = Math.floor(elapsed / 3600000);
        const mins = Math.floor((elapsed % 3600000) / 60000);
        const secs = Math.floor((elapsed % 60000) / 1000);
        setTimeLeft(`PASSED (+${hours}h ${mins}m ${secs}s)`);
        setIsUrgent(false);
        setIsPassed(true);
        return;
      }

      setIsPassed(false);
      const hours = Math.floor(diff / 3600000);
      const mins = Math.floor((diff % 3600000) / 60000);
      const secs = Math.floor((diff % 60000) / 1000);
      const ms = Math.floor((diff % 1000) / 10);

      const formatted = `${hours.toString().padStart(2, '0')}h ${mins.toString().padStart(2, '0')}m ${secs.toString().padStart(2, '0')}s .${ms.toString().padStart(2, '0')}`;
      setTimeLeft(formatted);
      setIsUrgent(diff < 6 * 3600000);
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 40);
    return () => clearInterval(interval);
  }, [tcaString]);

  return (
    <div className="flex flex-col">
      <div className="flex items-center gap-1.5 mb-1">
        <span className={`h-1.5 w-1.5 rounded-full ${isUrgent ? 'bg-rose-500 animate-ping' : isPassed ? 'bg-white/30' : 'bg-white animate-pulse'}`} />
        <span className="text-[10px] font-mono font-bold tracking-wider text-white/40 uppercase">
          TCA Countdown
        </span>
      </div>
      <div className={`text-xl font-mono font-bold tracking-wider ${isUrgent ? 'text-rose-400' : 'text-white'}`}>
        {timeLeft}
      </div>
      <span className="text-[9px] font-mono text-white/30 mt-0.5">
        {isPassed ? 'Encounter epoch elapsed' : isUrgent ? 'Critical encounter window' : 'Approaching TCA epoch'}
      </span>
    </div>
  );
};

const computeChanPc = (
  cov: number[][] | undefined,
  r_B: [number, number],
  hbr: number = 15.0
): number => {
  const matrix = cov || [[0.18, 0.04], [0.04, 0.08]];
  const [[cxx, cxy], [, cyy]] = matrix;
  
  const mean = (cxx + cyy) / 2.0;
  const diff = (cxx - cyy) / 2.0;
  const term = Math.sqrt(diff * diff + cxy * cxy);
  const s1_sq = Math.max(0.001, mean + term);
  const s2_sq = Math.max(0.001, mean - term);
  
  const [x, y] = r_B;
  const u = (x * x) / (2.0 * s1_sq) + (y * y) / (2.0 * s2_sq);
  const R_eff = hbr / 1000.0;
  const v = (R_eff * R_eff) / (2.0 * Math.sqrt(s1_sq * s2_sq));
  
  const pc = Math.exp(-u) * (1.0 - Math.exp(-v));
  return Math.min(1.0, Math.max(0.0, pc));
};

interface ConjunctionPageProps {
  onInitiateFiling: (eventId: string, satelliteName: string) => void;
}

export const ConjunctionPage: React.FC<ConjunctionPageProps> = ({ onInitiateFiling }) => {
  const [conjunctions, setConjunctions] = useState<ConjunctionEvent[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [details, setDetails] = useState<ConjunctionDetails | null>(null);
  const [loadingList, setLoadingList] = useState<boolean>(true);
  const [loadingDetails, setLoadingDetails] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [threatFilter, setThreatFilter] = useState<'all' | 'critical' | 'warning' | 'nominal'>('all');

  // Interactive Maneuver Delta-V Thrust Burn Slider States
  const [radialBurn, setRadialBurn] = useState<number>(0);
  const [inTrackBurn, setInTrackBurn] = useState<number>(0);
  const [crossTrackBurn, setCrossTrackBurn] = useState<number>(0);

  const x_base = details?.relative_vectors?.cross_track || 0;
  const y_base = details?.relative_vectors?.radial || 0;
  const radialNew = y_base + (8.0 * radialBurn) + (18.0 * inTrackBurn);
  const crossTrackNew = x_base + (12.0 * crossTrackBurn);
  const newMissDistance = Math.sqrt(radialNew * radialNew + crossTrackNew * crossTrackNew);
  const newPc = details ? computeChanPc(details.covariance_matrix?.p_cov, [crossTrackNew, radialNew], 15.0) : 0;

  const counts = useMemo(() => {
    return {
      all: conjunctions.length,
      critical: conjunctions.filter(c => c.pc >= 1e-4).length,
      warning: conjunctions.filter(c => c.pc >= 1e-6 && c.pc < 1e-4).length,
      nominal: conjunctions.filter(c => c.pc < 1e-6).length,
    };
  }, [conjunctions]);

  const filteredConjunctions = useMemo(() => {
    return conjunctions.filter(conj => {
      const matchesSearch = 
        conj.primary_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        conj.secondary_name.toLowerCase().includes(searchQuery.toLowerCase());
      
      let matchesThreat = true;
      if (threatFilter === 'critical') {
        matchesThreat = conj.pc >= 1e-4;
      } else if (threatFilter === 'warning') {
        matchesThreat = conj.pc >= 1e-6 && conj.pc < 1e-4;
      } else if (threatFilter === 'nominal') {
        matchesThreat = conj.pc < 1e-6;
      }
      
      return matchesSearch && matchesThreat;
    });
  }, [conjunctions, searchQuery, threatFilter]);

  // 1. Fetch active conjunctions list
  useEffect(() => {
    const fetchList = async () => {
      try {
        setLoadingList(true);
        const response = await axios.get(`${API_BASE_URL}/api/conjunctions`);
        const data = Array.isArray(response.data) ? response.data : response.data.results || [];
        setConjunctions(data);
        if (data.length > 0) {
          setSelectedId(String(data[0].id));
        }
      } catch (e) {
        console.error("Error fetching conjunctions list:", e);
      } finally {
        setLoadingList(false);
      }
    };
    fetchList();
  }, []);

  // 2. Fetch specific conjunction details when selection changes
  useEffect(() => {
    if (selectedId === null) return;
    
    const fetchDetails = async () => {
      try {
        setLoadingDetails(true);
        const response = await axios.get(`${API_BASE_URL}/api/conjunctions/${selectedId}`);
        setDetails(response.data);
        // Reset burns on new selection
        setRadialBurn(0);
        setInTrackBurn(0);
        setCrossTrackBurn(0);
      } catch (e) {
        console.error(`Error fetching conjunction details for ID ${selectedId}:`, e);
      } finally {
        setLoadingDetails(false);
      }
    };
    fetchDetails();
  }, [selectedId]);

  const getThreatBadge = (pc: number) => {
    if (pc >= 1e-4) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[9px] font-mono font-bold uppercase tracking-wider bg-rose-500/[0.12] text-rose-300 border border-rose-500/30 shadow-[0_0_10px_rgba(244,63,94,0.15)] shrink-0 whitespace-nowrap">
          <ShieldAlert className="h-3 w-3 text-rose-400" />
          Critical Hazard
        </span>
      );
    } else if (pc >= 1e-6) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[9px] font-mono font-bold uppercase tracking-wider bg-amber-500/[0.12] text-amber-300 border border-amber-500/30 shadow-[0_0_10px_rgba(245,158,11,0.15)] shrink-0 whitespace-nowrap">
          <AlertTriangle className="h-3 w-3 text-amber-400" />
          Elevated Warning
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[9px] font-mono font-semibold uppercase tracking-wider bg-emerald-500/[0.08] text-emerald-300 border border-emerald-500/25 shrink-0 whitespace-nowrap">
          <ShieldCheck className="h-3 w-3 text-emerald-400" />
          Nominal Risk
        </span>
      );
    }
  };

  return (
    <div className="w-full h-full flex flex-col lg:flex-row gap-5 overflow-hidden select-none font-sans">
      
      {/* ── LEFT PANE: CONJUNCTION FEED LIST ───────────────────────── */}
      <div className="w-full lg:w-[340px] shrink-0 h-full flex flex-col gap-3 pb-2 border-r border-white/[0.07] pr-4">
        {/* Directory Title */}
        <div className="flex items-center gap-2 pb-2.5 border-b border-white/[0.07]">
          <Activity className="h-4 w-4 text-white/70" />
          <h3 className="font-bold text-xs font-mono tracking-wider text-white uppercase">
            CONJUNCTIONS
          </h3>
        </div>

        {/* Minimal Search Input */}
        <div className="relative">
          <input
            type="text"
            placeholder="Search payload or NORAD..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-7 py-2 bg-black/40 border border-white/[0.08] hover:border-white/[0.14] rounded-xl text-xs text-white placeholder-white/30 focus:border-white/30 focus:outline-none transition-all font-mono"
          />
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-white/30" />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2.5 top-2 text-xs text-white/40 hover:text-white transition-colors cursor-pointer"
            >
              ×
            </button>
          )}
        </div>

        {/* Tab Filters */}
        <div className="flex items-center gap-1 border-b border-white/[0.06] pb-2 font-mono text-[9px]">
          {(['all', 'critical', 'warning', 'nominal'] as const).map((filterKey) => {
            const isActive = threatFilter === filterKey;
            const count = counts[filterKey];
            return (
              <button
                key={filterKey}
                onClick={() => setThreatFilter(filterKey)}
                className={`py-1 px-2 rounded font-bold uppercase transition-all cursor-pointer ${
                  isActive
                    ? 'bg-white text-black shadow-sm'
                    : 'text-white/40 hover:text-white/80'
                }`}
              >
                {filterKey} <span className="opacity-60 text-[8px]">({count})</span>
              </button>
            );
          })}
        </div>

        {/* Conjunctions List */}
        <div className="flex-1 overflow-y-auto flex flex-col gap-1 pr-1 custom-scrollbar">
          {loadingList ? (
            <div className="flex flex-col items-center justify-center py-24 gap-2 text-xs font-mono text-white/40">
              <Radio className="h-4 w-4 animate-spin text-white/60" />
              <span>Scanning catalog...</span>
            </div>
          ) : filteredConjunctions.length === 0 ? (
            <div className="text-center py-20 font-mono text-xs text-white/30 flex flex-col items-center gap-2">
              <CheckCircle className="h-5 w-5 text-white/20" />
              <span>No matching encounters detected.</span>
            </div>
          ) : (
            filteredConjunctions.map((conj) => {
              const isSelected = selectedId === String(conj.id);
              const isCritical = conj.pc >= 1e-4;
              const isWarn = conj.pc >= 1e-6 && conj.pc < 1e-4;
              return (
                <button
                  key={conj.id}
                  onClick={() => setSelectedId(String(conj.id))}
                  className={`w-full flex items-center justify-between p-2.5 text-left font-mono transition-all duration-150 group cursor-pointer border-l-2 ${
                    isSelected
                      ? 'border-white bg-white/[0.06] text-white pl-3'
                      : 'border-transparent hover:border-white/30 hover:bg-white/[0.02] text-white/60 pl-2.5'
                  }`}
                >
                  <div className="flex flex-col min-w-0 pr-2">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-white truncate">
                      <span className="truncate">{conj.primary_name}</span>
                      <span className="text-white/30 font-normal text-[10px]">⚔️</span>
                      <span className="truncate text-white/70">{conj.secondary_name}</span>
                    </div>

                    <div className="flex items-center gap-3 mt-1 text-[10px] text-white/40 font-mono">
                      <span>Miss: <span className="text-white/80 font-medium">{conj.miss_distance.toFixed(3)} km</span></span>
                      <span>•</span>
                      <span>Pc: <span className={isCritical ? 'text-rose-400 font-bold' : isWarn ? 'text-amber-400 font-bold' : 'text-white/70'}>{conj.pc.toExponential(2)}</span></span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <Matrix
                      rows={5}
                      cols={3}
                      mode="vu"
                      levels={[
                        isCritical ? 1.0 : isWarn ? 0.6 : 0.25,
                        isCritical ? 0.85 : isWarn ? 0.5 : 0.2,
                        isCritical ? 1.0 : isWarn ? 0.6 : 0.25
                      ]}
                      size={2}
                      gap={1}
                      palette={{
                        on: isCritical ? '#f43f5e' : isWarn ? '#fbbf24' : '#34d399',
                        off: 'rgba(255,255,255,0.06)'
                      }}
                    />
                    <ChevronRight className={`h-3.5 w-3.5 shrink-0 transition-transform ${isSelected ? 'text-white' : 'text-white/20 group-hover:text-white/40'}`} />
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* ── RIGHT PANE: ENCOUNTER WORKSPACE & B-PLANE ──────────────── */}
      <div className="flex-1 h-full overflow-y-auto pr-2 custom-scrollbar flex flex-col gap-5">
        {loadingDetails ? (
          <div className="flex-1 flex flex-col items-center justify-center py-40 gap-3 text-xs font-mono text-white/40">
            <Radio className="h-6 w-6 animate-spin text-white/60" />
            <span>Propagating encounter geometry...</span>
          </div>
        ) : !details ? (
          <div className="flex-1 flex flex-col items-center justify-center text-white/40 gap-2 font-mono py-32">
            <AlertTriangle className="h-8 w-8 opacity-40 text-amber-400" />
            <p className="text-xs">Select a conjunction event to view B-Plane analysis & maneuver burn simulator.</p>
          </div>
        ) : (
          <div className="flex flex-col gap-5">
            
            {/* Header Telemetry Row */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-3 border-b border-white/[0.08]">
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-3">
                  <h2 className="text-lg font-mono font-bold tracking-tight text-white flex items-center gap-2">
                    <span>{details.primary.name}</span>
                    <span className="text-white/30 text-xs font-normal">VS</span>
                    <span className="text-white/80">{details.secondary.name}</span>
                  </h2>
                  {getThreatBadge(details.pc)}
                </div>
                <p className="text-[11px] font-mono text-white/40">
                  TCA: <span className="text-white/80">{new Date(details.tca).toUTCString()}</span>
                </p>
              </div>

              <div className="flex items-center gap-2.5 shrink-0">
                <button
                  onClick={() => onInitiateFiling(String(details.id), details.primary.name)}
                  className="flex items-center gap-2 px-3.5 py-2 bg-white hover:bg-white/90 text-black font-mono font-bold text-xs rounded-xl transition cursor-pointer shadow-sm"
                >
                  <FileText size={13} />
                  Initiate IN-SPACe Filing
                </button>
              </div>
            </div>

            {/* Top 4 Telemetry Insets */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono">
              {/* TCA Countdown */}
              <div className="p-3.5 rounded-xl bg-black/30 border border-white/[0.06] flex flex-col justify-between">
                <TcaCountdown tcaString={details.tca} />
              </div>

              {/* Collision Probability Pc */}
              <div className="p-3.5 rounded-xl bg-black/30 border border-white/[0.06] flex flex-col justify-between">
                <div className="text-[10px] font-bold text-white/40 uppercase">COLLISION PROBABILITY</div>
                <div className={`text-xl font-bold mt-1 ${details.pc >= 1e-4 ? 'text-rose-400' : 'text-amber-400'}`}>
                  {details.pc.toExponential(4)}
                </div>
                <span className="text-[9px] text-white/30 mt-0.5">Pc Value</span>
              </div>

              {/* Miss Distance */}
              <div className="p-3.5 rounded-xl bg-black/30 border border-white/[0.06] flex flex-col justify-between">
                <div className="text-[10px] font-bold text-white/40 uppercase">MISS DISTANCE</div>
                <div className="text-xl font-bold text-white mt-1">
                  {details.miss_distance.toFixed(3)} <span className="text-xs font-normal text-white/40">km</span>
                </div>
                <span className="text-[9px] text-white/30 mt-0.5">Separation</span>
              </div>

              {/* Relative Speed */}
              <div className="p-3.5 rounded-xl bg-black/30 border border-white/[0.06] flex flex-col justify-between">
                <div className="text-[10px] font-bold text-white/40 uppercase">CLOSING RATE</div>
                <div className="text-xl font-bold text-white mt-1">
                  11.70 <span className="text-xs font-normal text-white/40">km/s</span>
                </div>
                <span className="text-[9px] text-white/30 mt-0.5">Relative Vector</span>
              </div>
            </div>

            {/* Main Encounter Workspace: 2-Columns */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
              
              {/* LEFT COLUMN: Real-Time Delta-V Thrust Burn Simulator */}
              <div className="flex flex-col gap-4 p-5 rounded-2xl bg-black/30 border border-white/[0.08]">
                <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
                  <div className="flex items-center gap-2">
                    <Navigation className="h-4 w-4 text-white/70" />
                    <h3 className="text-xs font-mono font-bold text-white uppercase">
                      Delta-V Maneuver Simulator
                    </h3>
                  </div>
                  <span className="text-[9px] font-mono text-white/40">HCW / RIC Frame</span>
                </div>

                {/* 3-Axis Burn Sliders */}
                <div className="flex flex-col gap-3.5 font-mono text-xs">
                  
                  {/* Radial Burn */}
                  <div className="flex flex-col gap-1.5">
                    <div className="flex justify-between items-center text-[10px]">
                      <span className="text-white/50">RADIAL THRUST (ΔVr)</span>
                      <span className={`font-bold ${radialBurn !== 0 ? 'text-white' : 'text-white/30'}`}>
                        {radialBurn > 0 ? `+${radialBurn.toFixed(2)}` : radialBurn.toFixed(2)} m/s
                      </span>
                    </div>
                    <input 
                      type="range" 
                      min="-2.0" 
                      max="2.0" 
                      step="0.05" 
                      value={radialBurn}
                      onChange={(e) => setRadialBurn(parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-black/60 rounded-lg appearance-none cursor-pointer accent-white"
                    />
                  </div>

                  {/* In-Track Burn */}
                  <div className="flex flex-col gap-1.5">
                    <div className="flex justify-between items-center text-[10px]">
                      <span className="text-white/50">IN-TRACK THRUST (ΔVt)</span>
                      <span className={`font-bold ${inTrackBurn !== 0 ? 'text-white' : 'text-white/30'}`}>
                        {inTrackBurn > 0 ? `+${inTrackBurn.toFixed(2)}` : inTrackBurn.toFixed(2)} m/s
                      </span>
                    </div>
                    <input 
                      type="range" 
                      min="-2.0" 
                      max="2.0" 
                      step="0.05" 
                      value={inTrackBurn}
                      onChange={(e) => setInTrackBurn(parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-black/60 rounded-lg appearance-none cursor-pointer accent-white"
                    />
                  </div>

                  {/* Cross-Track Burn */}
                  <div className="flex flex-col gap-1.5">
                    <div className="flex justify-between items-center text-[10px]">
                      <span className="text-white/50">CROSS-TRACK THRUST (ΔVn)</span>
                      <span className={`font-bold ${crossTrackBurn !== 0 ? 'text-white' : 'text-white/30'}`}>
                        {crossTrackBurn > 0 ? `+${crossTrackBurn.toFixed(2)}` : crossTrackBurn.toFixed(2)} m/s
                      </span>
                    </div>
                    <input 
                      type="range" 
                      min="-2.0" 
                      max="2.0" 
                      step="0.05" 
                      value={crossTrackBurn}
                      onChange={(e) => setCrossTrackBurn(parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-black/60 rounded-lg appearance-none cursor-pointer accent-white"
                    />
                  </div>

                </div>

                {/* Post-Burn Summary Readout */}
                <div className="p-3 bg-white/[0.02] border border-white/[0.06] rounded-xl flex items-center justify-between font-mono">
                  <div>
                    <span className="text-white/40 block text-[9px] uppercase">Post-Burn Miss Distance</span>
                    <span className="text-white font-bold text-sm">{newMissDistance.toFixed(3)} km</span>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <span className="text-white/40 block text-[9px] uppercase">Recalculated Pc</span>
                      <span className={`font-bold text-sm ${newPc < 1e-6 ? 'text-emerald-400' : 'text-amber-400'}`}>
                        {newPc.toExponential(4)}
                      </span>
                    </div>

                    <button
                      type="button"
                      onClick={() => {
                        setRadialBurn(0);
                        setInTrackBurn(0);
                        setCrossTrackBurn(0);
                      }}
                      className="p-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-white/60 hover:text-white transition cursor-pointer"
                      title="Reset burn sliders"
                    >
                      <RotateCcw size={13} />
                    </button>
                  </div>
                </div>

                {/* Apply CTA */}
                <button
                  onClick={() => onInitiateFiling(String(details.id), details.primary.name)}
                  className="w-full py-2.5 bg-white hover:bg-white/90 text-black font-mono font-bold text-xs rounded-xl transition shadow-sm cursor-pointer flex items-center justify-center gap-2"
                >
                  <FileText size={13} />
                  Accept Maneuver & Submit IN-SPACe Filing
                </button>
              </div>

              {/* RIGHT COLUMN: 2D B-PLANE PLOTTER & EPHEMERIS MATRIX */}
              <div className="flex flex-col gap-4">
                
                {/* 2D B-Plane Plotter */}
                <div className="p-5 rounded-2xl bg-black/30 border border-white/[0.08] flex flex-col gap-3">
                  <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
                    <div className="flex items-center gap-2">
                      <Activity className="h-4 w-4 text-white/70" />
                      <h3 className="text-xs font-mono font-bold text-white uppercase">
                        2D B-Plane Encounter Plot
                      </h3>
                    </div>
                    <span className="text-[9px] font-mono text-white/40">1σ & 3σ Covariance</span>
                  </div>

                  <BPlanePlotter
                    covarianceMatrix={details.covariance_matrix?.p_cov}
                    missDistanceVector={[crossTrackNew, radialNew]}
                    hbr={15.0}
                  />
                </div>

                {/* Satellite Ephemeris Matrix */}
                <div className="p-4 rounded-xl bg-black/30 border border-white/[0.06] font-mono text-xs flex flex-col gap-2.5">
                  <div className="text-[10px] font-bold text-white/50 uppercase flex items-center gap-1.5 pb-1 border-b border-white/[0.04]">
                    <Globe size={13} className="text-white/60" />
                    Encounter Object Registry
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="flex flex-col gap-0.5">
                      <span className="text-[9px] text-white/40 uppercase">Primary Payload</span>
                      <span className="text-white font-bold truncate">{details.primary.name}</span>
                      <span className="text-[10px] text-white/40">NORAD #{details.primary.norad_id} • {details.primary.operator || 'Unknown'}</span>
                    </div>

                    <div className="flex flex-col gap-0.5">
                      <span className="text-[9px] text-rose-400 uppercase">Secondary Object</span>
                      <span className="text-white font-bold truncate">{details.secondary.name}</span>
                      <span className="text-[10px] text-white/40">NORAD #{details.secondary.norad_id} • {details.secondary.operator || 'Debris'}</span>
                    </div>
                  </div>
                </div>

              </div>

            </div>

          </div>
        )}
      </div>



    </div>
  );
};

export default ConjunctionPage;

