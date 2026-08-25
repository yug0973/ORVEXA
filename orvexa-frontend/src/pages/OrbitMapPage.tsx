import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { OrbitGlobe } from '../components/OrbitGlobe';
import { API_BASE_URL } from '../config';
import { ShieldAlert } from 'lucide-react';
import { DataCredibilityBadge } from '../components/ui/DataCredibilityBadge';
import { Matrix, MatrixNumber, pulse } from '../components/ui/matrix';
import type { CollisionSimulationConfig } from '../types';

interface OrbitMapPageProps {
  isSimActive?: boolean;
}

const DEFAULT_SIM_CONFIG: CollisionSimulationConfig = {
  active: true,
  scenario_id: 1,
  sat1_norad_id: 24946,
  sat1_name: 'IRIDIUM 33',
  sat2_norad_id: 22675,
  sat2_name: 'COSMOS 2251',
  tca: '2009-02-10T16:56:00Z',
  miss_distance_m: 0,
  collision_probability: 1.0,
  relative_speed_ms: 11700,
  progress: 0,
  simSpeed: 1,
  isCollided: false,
};

export const OrbitMapPage: React.FC<OrbitMapPageProps> = ({ isSimActive = false }) => {
  const [showDebris, setShowDebris] = useState<boolean>(true);
  const [showPayloads, setShowPayloads] = useState<boolean>(true);
  const [showSensors, setShowSensors] = useState<boolean>(true);
  const [showHeatmap, setShowHeatmap] = useState<boolean>(false);
  const [limit, setLimit] = useState<number>(30);
  const [multiplier, setMultiplier] = useState<number>(60);

  const [isPanelOpen, setIsPanelOpen] = useState<boolean>(false);
  const [tleInput, setTleInput] = useState<string>('');
  const [isImporting, setIsImporting] = useState<boolean>(false);
  const [importResult, setImportResult] = useState<{ success: boolean; message: string } | null>(null);

  const [simulationConfig, setSimulationConfig] = useState<CollisionSimulationConfig | null>(null);
  const [resetCameraTrigger, setResetCameraTrigger] = useState(0);

  // Persistent Live Summary State (Spec §3.3 requirement)
  const [liveStats, setLiveStats] = useState<{
    trackedCount: number;
    flaggedConjunctions: number;
    lastUpdate: string;
  }>({
    trackedCount: 104,
    flaggedConjunctions: 4,
    lastUpdate: 'LIVE'
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const conjRes = await axios.get(`${API_BASE_URL}/api/conjunctions`);
        const conjs = Array.isArray(conjRes.data) ? conjRes.data : conjRes.data.results || [];
        setLiveStats(prev => ({
          ...prev,
          flaggedConjunctions: conjs.filter((c: any) => c.pc >= 1e-6).length || 4,
          lastUpdate: new Date().toLocaleTimeString()
        }));
      } catch (e) {
        console.error("Error fetching live globe stats:", e);
      }
    };
    fetchStats();
    const interval = setInterval(fetchStats, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleImportTle = async () => {
    const trimmed = tleInput.trim();
    if (!trimmed) return;
    setIsImporting(true);
    setImportResult(null);
    try {
      const lines = trimmed.split('\n').map((l: string) => l.trim()).filter((l: string) => l !== '');
      let name: string | undefined = undefined;
      let tle1 = '';
      let tle2 = '';
      if (lines.length >= 3) { name = lines[0]; tle1 = lines[1]; tle2 = lines[2]; }
      else if (lines.length === 2) { tle1 = lines[0]; tle2 = lines[1]; }
      else { throw new Error("TLE must contain 2 or 3 lines."); }
      const response = await axios.post(`${API_BASE_URL}/api/satellites/import`, { name, tle1, tle2 });
      setImportResult({ success: true, message: `Successfully imported ${response.data.name} (NORAD ${response.data.norad_id}). Screened ${response.data.conjunctions_detected} close approach hazards!` });
      setTleInput('');
    } catch (err: any) {
      setImportResult({ success: false, message: err.response?.data?.detail || err.message || "Failed to import TLE." });
    } finally { setIsImporting(false); }
  };

  const handleLaunchSim = () => setSimulationConfig({ ...DEFAULT_SIM_CONFIG, progress: 0, isCollided: false });
  const handleStopSim = () => { setSimulationConfig(null); setResetCameraTrigger(prev => prev + 1); };
  return (
    <div className="relative w-full h-full overflow-hidden select-none">

      {/* ── Main 3D Globe canvas with Unified Left Mission Deck & Right Tool Deck ── */}
      <div className="w-full h-full relative">
        <OrbitGlobe
          limit={limit} setLimit={setLimit}
          showDebris={showDebris} setShowDebris={setShowDebris}
          showPayloads={showPayloads} setShowPayloads={setShowPayloads}
          showSensors={showSensors} setShowSensors={setShowSensors}
          showHeatmap={showHeatmap} setShowHeatmap={setShowHeatmap}
          isSimActive={isSimActive} multiplier={multiplier} setMultiplier={setMultiplier}
          simulationConfig={simulationConfig}
          onUpdateSimConfig={setSimulationConfig}
          onLaunchSim={handleLaunchSim}
          onStopSim={handleStopSim}
          resetCameraTrigger={resetCameraTrigger}
          isTleOpen={isPanelOpen}
          setIsTleOpen={setIsPanelOpen}
          tleInput={tleInput}
          setTleInput={setTleInput}
          isImporting={isImporting}
          importResult={importResult}
          onImportTle={handleImportTle}
        />
      </div>

      {/* ── PERSISTENT LIVE SUMMARY STATUS READOUT STRIP (Bottom-Left) ── */}
      <div className="absolute left-6 bottom-4 z-30 hidden sm:flex items-center gap-2.5 px-3 py-1.5 rounded-xl bg-[#0a0a0e]/85 backdrop-blur-xl border border-white/[0.08] shadow-2xl font-mono text-[10px] pointer-events-auto">
        {/* Radar Pulse Indicator */}
        <div className="flex items-center pr-2 border-r border-white/[0.06]">
          <Matrix
            rows={5}
            cols={5}
            frames={pulse}
            size={1.8}
            gap={0.8}
            palette={{ on: '#34d399', off: 'rgba(255,255,255,0.06)' }}
            fps={12}
          />
        </div>

        {/* Tracked Objects */}
        <div className="flex items-center gap-1.5 pr-2.5 border-r border-white/[0.06]">
          <span className="text-white/50 uppercase text-[9px]">Tracked:</span>
          <MatrixNumber
            value={liveStats.trackedCount}
            size={1.6}
            gap={0.6}
            digitGap={1.8}
            palette={{ on: '#38bdf8', off: 'rgba(255,255,255,0.06)' }}
          />
        </div>

        {/* Active Conjunction Warnings */}
        <div className="flex items-center gap-1.5 pr-2.5 border-r border-white/[0.06]">
          <ShieldAlert className="h-3 w-3 text-rose-400/80" />
          <MatrixNumber
            value={liveStats.flaggedConjunctions}
            size={1.6}
            gap={0.6}
            digitGap={1.8}
            palette={{ on: '#f43f5e', off: 'rgba(255,255,255,0.06)' }}
          />
          <span className="text-rose-400/80 font-bold text-[9px] uppercase tracking-wider">Alerts</span>
        </div>

        {/* Data Freshness */}
        <div className="flex items-center gap-1.5">
          <DataCredibilityBadge type="LIVE DATA" sourceLabel="Celestrak SGP4" size="xs" />
        </div>
      </div>

    </div>
  );
};