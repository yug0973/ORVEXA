// CollisionSimulationPanel.tsx
// Orbital Collision Physics Reconstruction Engine

import { useState, useEffect, useCallback } from 'react';
import type { CollisionSimulationConfig, ReplayCameraMode } from '../types';
import { DataCredibilityBadge } from './ui/DataCredibilityBadge';
import { History, Play, Pause, RotateCcw, ShieldAlert } from 'lucide-react';

const SCENARIOS = [
  {
    id: 1 as const,
    label: '2009: Iridium 33 × Cosmos 2251',
    subtitle: 'First accidental hypervelocity satellite collision',
    year: 2009,
    sat1_norad_id: 24946,
    sat1_name: 'IRIDIUM 33',
    sat2_norad_id: 22675,
    sat2_name: 'COSMOS 2251',
    relative_speed_ms: 11700,
    altitude_km: 789,
    region: 'Taymyr Peninsula, Siberia',
    fragments: 2300,
    takeaway: 'Over 2,300 catalogued fragments were generated. Today, >1,000 trackable pieces remain in LEO, continuously triggering emergency conjunction screenings for active payloads.'
  },
  {
    id: 2 as const,
    label: '2007: Fengyun-1C ASAT Strike',
    subtitle: 'Kinetic anti-satellite intercept test',
    year: 2007,
    sat1_norad_id: 25730,
    sat1_name: 'FENGYUN-1C',
    sat2_norad_id: 29507,
    sat2_name: 'SC-19 KINETIC KV',
    relative_speed_ms: 9000,
    altitude_km: 865,
    region: 'Xichang / Central Asia',
    fragments: 3500,
    takeaway: 'Over 3,500 trackable fragments dispersed across 200–3,850 km altitude, permanently increasing LEO collision background flux by ~30% and threatening the ISS orbit.'
  }
];

function formatEnergy(joules: number): string {
  if (joules >= 1e15) return `${(joules / 1e15).toFixed(2)} PJ`;
  if (joules >= 1e12) return `${(joules / 1e12).toFixed(2)} TJ`;
  if (joules >= 1e9) return `${(joules / 1e9).toFixed(2)} GJ`;
  return `${(joules / 1e6).toFixed(1)} MJ`;
}

interface CollisionSimulationPanelProps {
  config: CollisionSimulationConfig;
  onUpdateConfig: (newConfig: CollisionSimulationConfig) => void;
  onStop: () => void;
  onCameraMode?: (mode: ReplayCameraMode) => void;
}

export function CollisionSimulationPanel({
  config,
  onUpdateConfig,
  onStop,
  onCameraMode,
}: CollisionSimulationPanelProps) {
  const [isPlaying, setIsPlaying] = useState(true);
  const [cameraMode, setCameraMode] = useState<ReplayCameraMode>('orbit');

  const currentScenario = SCENARIOS.find((s) => s.id === config.scenario_id) ?? SCENARIOS[0];

  const sat1Mass = currentScenario.id === 1 ? 560 : 750;
  const sat2Mass = currentScenario.id === 1 ? 900 : 120;
  const reducedMass = (sat1Mass * sat2Mass) / (sat1Mass + sat2Mass);
  const kineticEnergyJ = 0.5 * reducedMass * config.relative_speed_ms ** 2;

  const totalFragments = currentScenario.fragments;
  const fragmentCount = config.isCollided
    ? Math.round(Math.min(totalFragments, (config.progress - 0.5) * 2 * totalFragments))
    : 0;

  const phase = config.progress < 0.5 ? 1 : config.progress < 0.58 ? 2 : 3;
  const phaseLabel =
    phase === 1 ? 'STAGE 01: ORBITAL CONVERGENCE' : phase === 2 ? 'STAGE 02: HYPERVELOCITY IMPACT' : 'STAGE 03: DEBRIS EXPANSION';

  // Animation Loop with Auto-Camera Staging Transitions (Approach -> Impact -> Dispersal)
  useEffect(() => {
    if (!isPlaying) return;
    let animId: number;
    let lastTime = performance.now();

    const loop = (currentTime: number) => {
      const deltaMs = currentTime - lastTime;
      if (deltaMs >= 11) {
        lastTime = currentTime;
        const nextProgress = config.progress >= 1 ? 0 : config.progress + 0.00045 * config.simSpeed;
        const nextPhase: 1 | 2 | 3 = nextProgress < 0.5 ? 1 : nextProgress < 0.58 ? 2 : 3;
        
        // Auto camera transition
        let nextCam: ReplayCameraMode = cameraMode;
        if (nextPhase === 1 && cameraMode !== 'approach') {
          nextCam = 'approach';
        } else if (nextPhase === 2 && cameraMode !== 'impact') {
          nextCam = 'impact';
        } else if (nextPhase === 3 && cameraMode !== 'orbit') {
          nextCam = 'orbit';
        }

        onUpdateConfig({
          ...config,
          progress: nextProgress,
          isCollided: nextProgress >= 0.5,
          phase: nextPhase,
          camera_mode: nextCam
        });

        if (nextCam !== cameraMode) {
          setCameraMode(nextCam);
          onCameraMode?.(nextCam);
        }
      }
      animId = requestAnimationFrame(loop);
    };

    animId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animId);
  }, [isPlaying, config, cameraMode, onUpdateConfig, onCameraMode]);

  const handleCameraMode = useCallback(
    (mode: ReplayCameraMode) => {
      setCameraMode(mode);
      onUpdateConfig({ ...config, camera_mode: mode });
      onCameraMode?.(mode);
    },
    [config, onUpdateConfig, onCameraMode]
  );

  const scrubberTrackBackground = (() => {
    const pct = config.progress * 100;
    if (config.progress < 0.5) {
      return `linear-gradient(to right, #10B981 ${pct}%, #22252C ${pct}%)`;
    } else if (config.progress < 0.58) {
      return `linear-gradient(to right, #10B981 50%, #ffffff ${pct}%, #22252C ${pct}%)`;
    }
    return `linear-gradient(to right, #10B981 50%, #f43f5e 58%, #f59e0b ${pct}%, #22252C ${pct}%)`;
  })();

  return (
    <div className="w-80 md:w-96 bg-[#0a0a0d]/95 backdrop-blur-2xl border border-white/[0.12] rounded-2xl p-4 shadow-[0_20px_50px_rgba(0,0,0,0.8)] space-y-3.5 select-none font-sans text-xs text-white">
      
      {/* Header with Credibility Badge */}
      <div className="flex items-center justify-between pb-2.5 border-b border-white/[0.08]">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20">
            <History size={14} />
          </div>
          <div>
            <div className="font-mono font-bold text-xs text-white uppercase tracking-wider">
              Collision Replay
            </div>
            <div className="text-[9px] text-white/40 font-mono">Energetics Reconstruction</div>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <DataCredibilityBadge type="HISTORICAL RECONSTRUCTION" />
          <button
            onClick={onStop}
            className="p-1 text-white/40 hover:text-white rounded-lg hover:bg-white/[0.08] transition cursor-pointer"
            title="Exit Replay"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Scenario Selector (Exactly 2 real historical scenarios as per spec §2.4) */}
      <div className="space-y-1.5">
        <label className="text-[9px] font-mono font-bold text-white/40 uppercase tracking-wider">
          Historical Incident Scenario (2 Benchmarks)
        </label>
        <div className="grid grid-cols-2 gap-1.5">
          {SCENARIOS.map((s) => (
            <button
              key={s.id}
              onClick={() => {
                onUpdateConfig({
                  ...config,
                  scenario_id: s.id,
                  sat1_name: s.sat1_name,
                  sat1_norad_id: s.sat1_norad_id,
                  sat2_name: s.sat2_name,
                  sat2_norad_id: s.sat2_norad_id,
                  relative_speed_ms: s.relative_speed_ms,
                  progress: 0,
                  isCollided: false,
                  phase: 1,
                });
              }}
              className={`p-2 rounded-xl text-left border transition-all cursor-pointer font-mono ${
                config.scenario_id === s.id
                  ? 'bg-white/[0.12] border-white/40 text-white shadow-md'
                  : 'bg-black/30 border-white/[0.06] text-white/50 hover:bg-white/[0.04] hover:text-white'
              }`}
            >
              <div className="font-bold text-[10px] truncate text-white">{s.label}</div>
              <div className="text-[8.5px] text-white/40 truncate">{s.region}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Playback Controls & Timeline Scrubber */}
      <div className="p-3 bg-black/40 border border-white/[0.06] rounded-xl space-y-2.5">
        <div className="flex items-center justify-between font-mono text-[10px]">
          <span className="font-bold text-emerald-400">{phaseLabel}</span>
          <span className="text-white/60">{(config.progress * 100).toFixed(0)}%</span>
        </div>

        {/* Scrubber Input */}
        <input
          type="range"
          min="0"
          max="1"
          step="0.001"
          value={config.progress}
          onChange={(e) => {
            const nextProgress = parseFloat(e.target.value);
            onUpdateConfig({
              ...config,
              progress: nextProgress,
              isCollided: nextProgress >= 0.5,
              phase: nextProgress < 0.5 ? 1 : nextProgress < 0.58 ? 2 : 3,
            });
          }}
          className="w-full h-1.5 rounded-lg appearance-none cursor-pointer accent-white"
          style={{ background: scrubberTrackBackground }}
        />

        {/* Buttons */}
        <div className="flex items-center justify-between pt-1">
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="p-2 rounded-lg bg-white text-black hover:bg-white/90 transition cursor-pointer font-bold"
            >
              {isPlaying ? <Pause size={12} /> : <Play size={12} className="fill-black" />}
            </button>
            <button
              onClick={() => {
                onUpdateConfig({ ...config, progress: 0, isCollided: false, phase: 1 });
              }}
              className="p-2 rounded-lg bg-white/[0.06] hover:bg-white/[0.12] text-white/80 transition cursor-pointer"
              title="Reset Simulation"
            >
              <RotateCcw size={12} />
            </button>
          </div>

          {/* Speed Multiplier */}
          <div className="flex items-center gap-1 font-mono text-[9px]">
            {[1, 2, 5].map((spd) => (
              <button
                key={spd}
                onClick={() => onUpdateConfig({ ...config, simSpeed: spd })}
                className={`px-2 py-1 rounded-md border font-bold transition cursor-pointer ${
                  config.simSpeed === spd
                    ? 'bg-white/20 border-white/40 text-white'
                    : 'bg-transparent border-white/[0.06] text-white/40 hover:text-white'
                }`}
              >
                {spd}x
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Camera Angle Staging Controls */}
      <div className="space-y-1.5 font-mono">
        <div className="flex items-center justify-between text-[9px] text-white/40 uppercase">
          <span>Camera Staging</span>
          <span className="text-emerald-400">Auto-transition active</span>
        </div>
        <div className="grid grid-cols-4 gap-1">
          {(['approach', 'impact', 'orbit', 'follow'] as ReplayCameraMode[]).map((mode) => (
            <button
              key={mode}
              onClick={() => handleCameraMode(mode)}
              className={`py-1 text-[9px] font-bold rounded-lg border uppercase transition cursor-pointer ${
                cameraMode === mode
                  ? 'bg-white/20 border-white/40 text-white'
                  : 'bg-black/20 border-white/[0.06] text-white/40 hover:text-white'
              }`}
            >
              {mode}
            </button>
          ))}
        </div>
      </div>

      {/* Telemetry Output Metrics */}
      <div className="p-3 bg-black/40 border border-white/[0.06] rounded-xl space-y-2 font-mono text-[10px]">
        <div className="flex justify-between items-center text-white/40 uppercase pb-1 border-b border-white/[0.04]">
          <span>Encounter Altitude:</span>
          <span className="text-white font-bold">{currentScenario.altitude_km} km</span>
        </div>
        <div className="flex justify-between items-center text-white/40 uppercase pb-1 border-b border-white/[0.04]">
          <span>Closing Velocity:</span>
          <span className="text-amber-400 font-bold">{(config.relative_speed_ms / 1000).toFixed(2)} km/s</span>
        </div>
        <div className="flex justify-between items-center text-white/40 uppercase pb-1 border-b border-white/[0.04]">
          <span>Impact Kinetic Energy:</span>
          <span className="text-white font-bold">{formatEnergy(kineticEnergyJ)}</span>
        </div>
        <div className="flex justify-between items-center text-white/40 uppercase">
          <span>Debris Fragments:</span>
          <span className="text-rose-400 font-bold">{fragmentCount.toLocaleString()} / {totalFragments.toLocaleString()}</span>
        </div>
      </div>

      {/* Real-World Present-Day Takeaway Note Box (Spec §2.4 requirement) */}
      <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/25 text-amber-200/90 text-[10px] space-y-1">
        <div className="flex items-center gap-1.5 font-bold text-[9px] font-mono text-amber-300 uppercase">
          <ShieldAlert size={12} />
          Present-Day Orbital Safety Takeaway
        </div>
        <p className="leading-relaxed text-amber-100/80">
          {currentScenario.takeaway}
        </p>
      </div>

    </div>
  );
}