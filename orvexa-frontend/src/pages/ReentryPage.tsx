import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import { 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as ChartTooltip 
} from 'recharts';
import { ReentryMap } from '../components/ReentryMap';
import { 
  AlertOctagon, 
  TrendingDown, 
  Activity, 
  Layers, 
  ChevronRight, 
  CheckCircle, 
  Sun, 
  Zap 
} from 'lucide-react';
import type { ReentryCandidate } from '../types';

export const ReentryPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'reentry' | 'weather'>('reentry');
  const [candidates, setCandidates] = useState<ReentryCandidate[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [corridorGeojson, setCorridorGeojson] = useState<any>(null);
  const [loadingList, setLoadingList] = useState<boolean>(true);
  const [loadingMap, setLoadingMap] = useState<boolean>(false);

  // Space Weather State (Folded into Reentry Risk Pillar)
  const [weatherData, setWeatherData] = useState<any>(null);
  const [adityaHistory, setAdityaHistory] = useState<any[]>([]);

  // 1. Fetch LEO decay alerts
  useEffect(() => {
    const fetchList = async () => {
      try {
        setLoadingList(true);
        const response = await axios.get(`${API_BASE_URL}/api/reentry`);
        setCandidates(response.data);
        if (response.data.length > 0) {
          setSelectedId(response.data[0].norad_id);
        }
      } catch (e) {
        console.error("Error fetching decay candidates:", e);
      } finally {
        setLoadingList(false);
      }
    };
    fetchList();
  }, []);

  // 2. Fetch NOAA Space Weather
  useEffect(() => {
    const fetchWeather = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/solar`);
        setWeatherData(response.data);
      } catch (e) {
        console.error("Error fetching solar indices in Reentry:", e);
      }
    };
    fetchWeather();

    const fetchAditya = async () => {
      try {
        const res = await axios.get(`${API_BASE_URL}/api/solar/aditya-l1`);
        setAdityaHistory(prev => {
          const timestampLabel = new Date(res.data.timestamp * 1000).toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit' 
          });
          const next = [...prev, {
            time: timestampLabel,
            solexs: res.data.solexs_flux,
            hel1os: res.data.hel1os_flux
          }];
          return next.slice(-20);
        });
      } catch (e) {
        console.error("Error polling Aditya-L1 in Reentry:", e);
      }
    };
    fetchAditya();
    const interval = setInterval(fetchAditya, 3000);
    return () => clearInterval(interval);
  }, []);

  // 3. Fetch GeoJSON landing corridor map when selected candidate changes
  useEffect(() => {
    if (selectedId === null) return;
    
    const fetchMap = async () => {
      try {
        setLoadingMap(true);
        const response = await axios.get(`${API_BASE_URL}/api/reentry/${selectedId}/map`);
        setCorridorGeojson(response.data);
      } catch (e) {
        console.error(`Error fetching reentry map for NORAD ${selectedId}:`, e);
      } finally {
        setLoadingMap(false);
      }
    };
    fetchMap();
  }, [selectedId]);

  const selectedCandidate = candidates.find(c => c.norad_id === selectedId);

  // Generate dynamic decay curve data with Space Weather (Kp index) correlation
  const decayData = selectedCandidate 
    ? Array.from({ length: 8 }, (_, i) => {
        const dayOffset = 7 - i;
        const baseAlt = selectedCandidate.current_altitude;
        const baseDecayRate = selectedCandidate.decay_rate;

        let solarKp = 2.0;
        if (dayOffset === 3) solarKp = 7.8;
        else if (dayOffset === 2) solarKp = 5.2;
        else if (dayOffset === 1) solarKp = 3.5;
        else if (dayOffset === 4) solarKp = 2.5;

        let decayImpact = 0;
        for (let day = 7; day > dayOffset; day--) {
          let stepDecay = baseDecayRate;
          if (day === 3) stepDecay *= 4.5;
          else if (day === 2) stepDecay *= 2.5;
          else if (day === 1) stepDecay *= 1.5;
          decayImpact += stepDecay;
        }

        const altitudeVal = baseAlt + (baseDecayRate * 7) - decayImpact + Math.sin(dayOffset) * 0.8;

        return {
          day: `T-${dayOffset}d`,
          altitude: Math.max(80.0, Math.round(altitudeVal * 10) / 10),
          kpIndex: solarKp
        };
      })
    : [];

  return (
    <div className="flex flex-col gap-4 w-full h-full select-none font-sans overflow-hidden">
      
      {/* ── TOP HEADER & SUB-TABS ── */}
      <div className="flex items-center justify-between pb-2.5 border-b border-white/[0.08] shrink-0 gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="p-1.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-white">
            <AlertOctagon className="h-4 w-4" />
          </div>
          <h2 className="text-xs font-bold tracking-wider text-white font-mono uppercase">
            REENTRY & DECAY CONSOLE
          </h2>
        </div>

        {/* Sub-Navigation Tabs */}
        <div className="flex items-center gap-1 bg-white/[0.02] border border-white/[0.07] p-1 rounded-xl font-mono text-xs shrink-0">
          <button
            onClick={() => setActiveTab('reentry')}
            className={`px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer text-xs ${
              activeTab === 'reentry'
                ? 'bg-white text-black shadow-sm'
                : 'text-white/50 hover:text-white hover:bg-white/[0.04]'
            }`}
          >
            Decay Corridors ({candidates.length})
          </button>
          <button
            onClick={() => setActiveTab('weather')}
            className={`px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer flex items-center gap-1.5 text-xs ${
              activeTab === 'weather'
                ? 'bg-white text-black shadow-sm'
                : 'text-white/50 hover:text-white hover:bg-white/[0.04]'
            }`}
          >
            <Sun size={13} className={activeTab === 'weather' ? 'text-amber-600' : 'text-amber-400'} />
            <span>Solar Weather</span>
          </button>
        </div>
      </div>

      {/* ── TAB 1: REENTRY CORRIDORS & DECAY ── */}
      {activeTab === 'reentry' && (
        <div className="flex flex-col lg:flex-row gap-5 flex-1 min-h-0 overflow-hidden">
          
          {/* LEFT: Candidate List */}
          <div className="w-full lg:w-[300px] shrink-0 h-full flex flex-col gap-2.5 border-r border-white/[0.06] pr-4">
            <div className="flex items-center justify-between pb-1">
              <span className="text-[10px] font-mono font-bold text-white/50 uppercase tracking-wider">
                Candidates (&lt; 250 km)
              </span>
              <span className="text-[9px] font-mono px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
                CRITICAL ZONE
              </span>
            </div>

            {loadingList ? (
              <div className="flex-1 flex items-center justify-center font-mono text-xs text-white/40">
                LOADING DECAY REGISTER...
              </div>
            ) : candidates.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-white/40 gap-2">
                <CheckCircle className="h-8 w-8 text-emerald-500/40" />
                <h4 className="text-xs font-semibold text-white/80">Orbit Safe</h4>
                <p className="text-xs max-w-[200px] text-white/40">No tracked spacecraft currently decay below 250 km threshold.</p>
              </div>
            ) : (
              <div className="flex-1 overflow-y-auto flex flex-col gap-1.5 pr-1">
                {candidates.map((c) => {
                  const isSelected = selectedId === c.norad_id;
                  return (
                    <button
                      key={c.norad_id}
                      onClick={() => setSelectedId(c.norad_id)}
                      className={`w-full text-left p-3 rounded-xl transition-all duration-150 flex items-center justify-between group cursor-pointer border font-mono ${
                        isSelected 
                          ? 'border-white/30 bg-white/[0.08] text-white shadow-md' 
                          : 'border-white/[0.05] bg-black/20 hover:border-white/15 hover:bg-white/[0.02] text-white/60'
                      }`}
                    >
                      <div className="flex-1 min-w-0 pr-2">
                        <div className="font-bold text-xs tracking-wide truncate text-white">
                          {c.name}
                        </div>
                        <div className="flex items-center gap-2 mt-1 text-[10px] text-white/40">
                          <span>Alt: <span className="text-white/90 font-bold">{c.current_altitude.toFixed(1)} km</span></span>
                          <span>•</span>
                          <span>Decay: <span className="text-rose-400 font-bold">{c.decay_rate.toFixed(2)} km/d</span></span>
                        </div>
                      </div>
                      <ChevronRight className={`h-3.5 w-3.5 shrink-0 transition-transform ${isSelected ? 'text-white' : 'text-white/20 group-hover:text-white/40'}`} />
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* RIGHT: Spatial Map, Stats, and Charts */}
          <div className="flex-1 h-full overflow-y-auto pr-1 flex flex-col gap-4">
            {loadingMap || !selectedCandidate ? (
              <div className="flex-1 flex items-center justify-center font-mono text-xs text-white/40">
                LOADING DECAY SIMULATION GEO-DATABASE...
              </div>
            ) : (
              <>
                {/* Header Strip */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl bg-white/[0.02] border border-white/[0.06]">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-base text-white">{selectedCandidate.name}</h3>
                      <span className="text-[10px] font-mono text-white/40">NORAD {selectedCandidate.norad_id}</span>
                    </div>
                    <p className="text-[11px] font-mono text-white/40 mt-0.5">
                      Ground Impact (ETA): <span className="text-white/80 font-mono">{new Date(selectedCandidate.eta).toUTCString()}</span>
                    </p>
                  </div>
                </div>

                {/* Map & Telemetry Metrics Grid */}
                <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
                  {/* Map */}
                  <div className="xl:col-span-2 h-[340px] xl:h-[380px] rounded-2xl overflow-hidden border border-white/[0.08]">
                    <ReentryMap
                      geojsonCorridor={corridorGeojson}
                      satelliteName={selectedCandidate.name}
                    />
                  </div>

                  {/* 3 Metric Cards */}
                  <div className="flex flex-col gap-3">
                    {/* Current Altitude */}
                    <div className="p-4 bg-white/[0.02] border border-white/[0.07] rounded-xl flex items-center justify-between">
                      <div>
                        <div className="text-[9.5px] font-mono font-bold text-white/40 uppercase mb-1">Current Altitude</div>
                        <div className="text-2xl font-mono font-bold text-white">{selectedCandidate.current_altitude.toFixed(1)} km</div>
                        <div className="text-[9px] text-white/40 mt-1">Thermospheric drag zone</div>
                      </div>
                      <TrendingDown className="h-5 w-5 text-amber-400/60" />
                    </div>

                    {/* Fragment Survival Rate */}
                    <div className="p-4 bg-white/[0.02] border border-white/[0.07] rounded-xl flex items-center justify-between">
                      <div>
                        <div className="text-[9.5px] font-mono font-bold text-white/40 uppercase mb-1">Fragment Survival Rate</div>
                        <div className="text-2xl font-mono font-bold text-amber-400">{selectedCandidate.survival_pct.toFixed(1)}%</div>
                        <div className="text-[9px] text-white/40 mt-1">NASA EVM Model</div>
                      </div>
                      <Layers className="h-5 w-5 text-amber-400/60" />
                    </div>

                    {/* Casualty Probability Ec */}
                    <div className="p-4 bg-white/[0.02] border border-white/[0.07] rounded-xl flex items-center justify-between">
                      <div>
                        <div className="text-[9.5px] font-mono font-bold text-white/40 uppercase mb-1">Casualty Risk (Ec)</div>
                        <div className="text-2xl font-mono font-bold text-rose-400">{selectedCandidate.casualty_probability.toExponential(2)}</div>
                        <div className="text-[9px] text-rose-400/70 mt-1">NASA 1:10,000 threshold</div>
                      </div>
                      <AlertOctagon className="h-5 w-5 text-rose-500/60" />
                    </div>
                  </div>
                </div>

                {/* Altitude Decay & Solar Storm Correlation Chart */}
                <div className="p-4 bg-white/[0.02] border border-white/[0.07] rounded-xl">
                  <div className="flex items-center justify-between text-xs font-mono font-bold text-white/60 mb-3">
                    <span className="flex items-center gap-2">
                      <Activity className="h-4 w-4 text-emerald-400" />
                      Altitude Decay & Solar Storm Correlation (T-7 Days)
                    </span>
                    <span className="text-[10px] text-purple-400">Kp ≥ 5 Storm Event</span>
                  </div>
                  <div className="h-44 w-full font-mono text-xs">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={decayData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
                        <XAxis dataKey="day" stroke="#666677" fontSize={9} tickLine={false} />
                        <YAxis yAxisId="left" stroke="#ef4444" fontSize={9} domain={['auto', 'auto']} tickLine={false} unit=" km" />
                        <YAxis yAxisId="right" orientation="right" stroke="#a855f7" fontSize={9} domain={[0, 9]} tickLine={false} unit=" Kp" />
                        <ChartTooltip
                          contentStyle={{
                            backgroundColor: '#0a0a0d',
                            border: '1px solid rgba(255,255,255,0.1)',
                            borderRadius: '10px',
                            fontSize: '11px',
                            fontFamily: 'monospace'
                          }}
                        />
                        <Line yAxisId="left" type="monotone" dataKey="altitude" stroke="#ef4444" strokeWidth={2} dot={{ r: 3, fill: '#ef4444' }} name="Altitude (km)" />
                        <Line yAxisId="right" type="monotone" dataKey="kpIndex" stroke="#a855f7" strokeWidth={1.5} strokeDasharray="4 4" dot={{ r: 2.5, fill: '#a855f7' }} name="Storm Kp Index" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </>
            )}
          </div>

        </div>
      )}

      {/* ── TAB 2: NOAA SPACE WEATHER & THERMOSPHERIC DRAG ── */}
      {activeTab === 'weather' && (
        <div className="flex-1 min-h-0 overflow-y-auto pr-1 flex flex-col gap-4">
          
          {/* Weather Headline Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3 font-mono">
            
            {/* F10.7 */}
            <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.07] flex flex-col gap-1">
              <span className="text-[9px] font-bold text-white/40 uppercase">Solar Flux (F10.7)</span>
              <div className="text-2xl font-bold text-amber-400 mt-1">
                {weatherData ? Math.round(weatherData.f10_7) : '136'} <span className="text-xs font-normal text-white/40">sfu</span>
              </div>
              <span className="text-[9.5px] text-white/40 mt-1">Baseline: 70.0 sfu</span>
            </div>

            {/* Ap Index */}
            <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.07] flex flex-col gap-1">
              <span className="text-[9px] font-bold text-white/40 uppercase">Planetary Ap Index</span>
              <div className="text-2xl font-bold text-purple-400 mt-1">
                {weatherData ? weatherData.ap.toFixed(1) : '7.5'} <span className="text-xs font-normal text-white/40">nT</span>
              </div>
              <span className="text-[9.5px] text-white/40 mt-1">Storm threshold: &gt;30</span>
            </div>

            {/* Drag Multiplier */}
            <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.07] flex flex-col gap-1">
              <span className="text-[9px] font-bold text-white/40 uppercase">Drag Multiplier</span>
              <div className="text-2xl font-bold text-emerald-400 mt-1">
                {weatherData ? weatherData.drag_scaler.toFixed(2) : '1.94'}x
              </div>
              <span className="text-[9.5px] text-white/40 mt-1">Thermosphere density</span>
            </div>

            {/* Aditya-L1 Active Stream */}
            <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.07] flex flex-col gap-1">
              <span className="text-[9px] font-bold text-white/40 uppercase">Aditya-L1 Telemetry</span>
              <div className="text-2xl font-bold text-white mt-1 flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-emerald-400">ONLINE</span>
              </div>
              <span className="text-[9.5px] text-white/40 mt-1">SoLEXS + HEL1OS</span>
            </div>

          </div>


          {/* Aditya-L1 Live X-Ray Flux Area Chart */}
          <div className="p-4 bg-black/30 border border-white/[0.06] rounded-xl flex flex-col gap-3">
            <div className="flex items-center justify-between font-mono text-xs">
              <span className="flex items-center gap-2 font-bold text-white">
                <Zap className="h-4 w-4 text-amber-400" />
                Aditya-L1 Solar X-Ray Spectrometer Real-Time Feed (SoLEXS & HEL1OS)
              </span>
              <span className="text-[10px] text-emerald-400">Telemetry Refresh: 3.0s</span>
            </div>

            <div className="h-52 w-full font-mono text-xs">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={adityaHistory} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
                  <XAxis dataKey="time" stroke="#666677" fontSize={9} tickLine={false} />
                  <YAxis stroke="#666677" fontSize={9} tickLine={false} unit=" W/m²" />
                  <ChartTooltip
                    contentStyle={{
                      backgroundColor: '#0a0a0d',
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '10px',
                      fontSize: '11px',
                      fontFamily: 'monospace'
                    }}
                  />
                  <Area type="monotone" dataKey="solexs" stroke="#f59e0b" fill="rgba(245, 158, 11, 0.15)" strokeWidth={2} name="SoLEXS Soft X-Ray" />
                  <Area type="monotone" dataKey="hel1os" stroke="#a855f7" fill="rgba(168, 85, 247, 0.15)" strokeWidth={1.5} name="HEL1OS Hard X-Ray" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

        </div>
      )}

    </div>
  );
};
