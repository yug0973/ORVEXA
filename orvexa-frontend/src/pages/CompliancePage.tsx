import React, { useState, useEffect, useRef, useMemo } from 'react';
import axios from 'axios';
import { API_BASE_URL, getWebSocketUrl } from '../config';

// API key for write operations — matches ORVEXA_API_KEY env var in backend
// In production, load this from an environment variable or secure store
const ORVEXA_API_KEY = import.meta.env.VITE_API_KEY ?? 'ORVEXA-dev-2026';
import { 
  FileText, 
  User, 
  Download, 
  CheckCircle, 
  RefreshCw,
  Play,
  Activity,
  Terminal as TerminalIcon,
  ShieldCheck
} from 'lucide-react';
import { Matrix, createWaveFrames } from '../components/ui/matrix';
import type { ConjunctionEvent, ConjunctionDetails } from '../types';

interface SwarmLogFrame {
  percentage: number;
  agent: string;
  log: string;
  timestamp: string;
  filing_id?: number;
}

interface CompliancePageProps {
  selectedConjunction: { id: string; satellite: string } | null;
}

export const CompliancePage: React.FC<CompliancePageProps> = ({ selectedConjunction }) => {
  const [conjunctions, setConjunctions] = useState<ConjunctionEvent[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<string>("");
  const [operatorName, setOperatorName] = useState<string>("ISRO Space Situational Awareness (SSA) Group");
  
  // Selected conjunction metadata
  const [eventDetails, setEventDetails] = useState<ConjunctionDetails | null>(null);

  // Filing outputs
  const [filingResult, setFilingResult] = useState<any>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [pastFilings, setPastFilings] = useState<any[]>([]);

  // Pipeline Live Execution Monitor States
  const [logs, setLogs] = useState<SwarmLogFrame[]>([]);
  const [isRunningPipeline, setIsRunningPipeline] = useState<boolean>(false);
  const [pipelineProgress, setPipelineProgress] = useState<number>(0);
  const [activeStep, setActiveStep] = useState<number>(-1);
  const [pipelineFilingId, setPipelineFilingId] = useState<number | null>(null);
  const terminalEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // 1. Fetch available conjunctions and past filings on load
  useEffect(() => {
    const fetchConjunctions = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/conjunctions?limit=50`);
        setConjunctions(response.data);
        
        if (selectedConjunction) {
          setSelectedEventId(selectedConjunction.id);
        } else if (response.data.length > 0) {
          setSelectedEventId(response.data[0].id);
        }
      } catch (err) {
        console.error("Error fetching conjunctions list for compliance:", err);
      }
    };

    const fetchFilings = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/compliance/filings`);
        setPastFilings(response.data);
      } catch (err) {
        console.error("Error fetching past filings:", err);
      }
    };

    fetchConjunctions();
    fetchFilings();
  }, [selectedConjunction]);

  // 2. Fetch specific conjunction details when selected
  useEffect(() => {
    if (!selectedEventId) return;

    const fetchDetails = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/conjunctions/${selectedEventId}`);
        setEventDetails(response.data);
        setErrorMsg(null);
      } catch (err) {
        console.error(`Error fetching conjunction ${selectedEventId} details:`, err);
        setErrorMsg("Failed to load conjunction telemetry.");
      }
    };

    fetchDetails();
  }, [selectedEventId]);

  // Auto-scroll terminal
  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Cleanup websocket
  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const getStepIndex = (stageName: string): number => {
    const name = stageName.toUpperCase();
    if (name.includes("INGESTION")) return 0;
    if (name.includes("SCREENING") || name.includes("MATH")) return 1;
    if (name.includes("DECAY") || name.includes("PLANNER") || name.includes("REENTRY") || name.includes("MANEUVER")) return 2;
    if (name.includes("COMPLIANCE")) return 3;
    return -1;
  };

  // Trigger Multi-Stage Pipeline via WebSocket
  const startAutomatedPipeline = () => {
    if (isRunningPipeline) return;
    
    setLogs([]);
    setPipelineProgress(0);
    setActiveStep(0);
    setPipelineFilingId(null);
    setIsRunningPipeline(true);
    
    const ws = new WebSocket(getWebSocketUrl("/api/ws/swarm/run"));
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const frame: SwarmLogFrame = JSON.parse(event.data);
        setLogs(prev => [...prev, frame]);
        setPipelineProgress(frame.percentage);
        
        if (frame.filing_id) {
          setPipelineFilingId(frame.filing_id);
        }
        
        const stepIdx = getStepIndex(frame.agent);
        if (stepIdx !== -1) {
          setActiveStep(stepIdx);
        }
      } catch (e) {
        console.error("Error parsing WebSocket pipeline log frame:", e);
      }
    };

    ws.onclose = () => {
      setIsRunningPipeline(false);
      setPipelineProgress(100);
      setActiveStep(3);
      setLogs(prev => [...prev, {
        percentage: 100,
        agent: "PIPELINE_ORCHESTRATOR",
        log: "Multi-stage automated regulatory pipeline complete. Briefing document rendered.",
        timestamp: new Date().toISOString()
      }]);
    };

    ws.onerror = (err) => {
      console.error("Pipeline socket connection error:", err);
      setIsRunningPipeline(false);
      setLogs(prev => [...prev, {
        percentage: 100,
        agent: "SYSTEM_ERROR",
        log: "Pipeline socket connection error. Check backend server connection.",
        timestamp: new Date().toISOString()
      }]);
    };
  };

  // Submit manual single-event regulatory filing
  const handleSubmitFiling = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEventId) return;

    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/compliance/file`, {
        event_id: String(selectedEventId),
        operator_name: operatorName
      }, {
        headers: { 'X-API-Key': ORVEXA_API_KEY }
      });

      setFilingResult(response.data);
      
      try {
        const updatedFilings = await axios.get(`${API_BASE_URL}/api/compliance/filings`);
        setPastFilings(updatedFilings.data);
      } catch (listErr) {
        console.warn("Could not refresh past filings list:", listErr);
      }
    } catch (err: any) {
      console.error("Error submitting compliance filing:", err);
      const detail = err.response?.data?.detail || err.message || "Failed to generate compliance brief. Please ensure backend is reachable.";
      setErrorMsg(detail);
    } finally {
      setIsSubmitting(false);
    }
  };

  const steps = [
    { label: "01. Ingestion", desc: "TLE Catalog Ephemeris Ingest", lib: "Celestrak API" },
    { label: "02. Screening", desc: "KD-Tree Proximity & Chan Pc", lib: "scipy.spatial / special" },
    { label: "03. Execution", desc: "Atmospheric Drag & RK4 Burns", lib: "RK4 Integrator, numpy" },
    { label: "04. Document", desc: "IN-SPACe / IADC PDF Brief", lib: "Llama 3.2, ReportLab" }
  ];

  const stageWave = useMemo(() => createWaveFrames(6, 26, 24), []);

  return (
    <div className="flex flex-col gap-4 w-full h-full select-none font-sans overflow-hidden">
      
      {/* ── TOP HEADER ── */}
      <div className="flex items-center justify-between pb-2.5 border-b border-white/[0.08] shrink-0 gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="p-1.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-white">
            <FileText className="h-4 w-4" />
          </div>
          <h2 className="text-xs font-bold tracking-wider text-white font-mono uppercase">
            AUTOMATED COMPLIANCE HUB
          </h2>
        </div>

        {/* Global Pipeline Trigger */}
        <div className="flex items-center gap-2 shrink-0">
          {pipelineFilingId && (
            <button
              onClick={() => window.open(`${API_BASE_URL}/api/compliance/download/${pipelineFilingId}`, '_blank')}
              className="flex items-center gap-1.5 px-3 py-1.5 border border-white/[0.12] bg-white/[0.06] hover:bg-white/[0.12] text-white rounded-xl text-xs font-semibold font-mono transition cursor-pointer"
            >
              <Download size={13} />
              <span>Download PDF</span>
            </button>
          )}

          {isRunningPipeline ? (
            <button
              onClick={() => wsRef.current?.close()}
              className="flex items-center gap-1.5 px-3.5 py-1.5 border border-rose-500/35 bg-rose-500/10 text-rose-300 rounded-xl text-xs font-semibold font-mono transition cursor-pointer"
            >
              <RefreshCw size={13} className="animate-spin" />
              <span>Cancel Pipeline</span>
            </button>
          ) : (
            <button
              onClick={startAutomatedPipeline}
              className="flex items-center gap-2 px-4 py-2 bg-white hover:bg-white/90 text-black rounded-xl text-xs font-bold font-mono transition cursor-pointer shadow-sm"
            >
              <Play size={13} className="text-black fill-black" />
              <span>Execute 6-Stage Pipeline</span>
            </button>
          )}
        </div>
      </div>

      {/* ── 4-STAGE PIPELINE PROGRESS TRACKER WITH WHITE MATRIX WAVE BACKGROUND ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5 shrink-0 font-mono">
        {steps.map((s, idx) => {
          const isCompleted = (activeStep > idx) || (!isRunningPipeline && pipelineProgress === 100);
          const isActive = isRunningPipeline && activeStep === idx;

          return (
            <div 
              key={s.label}
              className={`p-3.5 rounded-xl border transition-all duration-500 flex flex-col gap-1.5 relative overflow-hidden ${
                isActive 
                  ? 'bg-white/[0.08] border-white/40 shadow-[0_0_24px_rgba(255,255,255,0.15)] ring-1 ring-white/30' 
                  : isCompleted
                    ? 'bg-white/[0.04] border-white/20'
                    : 'bg-black/40 border-white/[0.07] opacity-60'
              }`}
            >
              {/* Digitized White LED Matrix Wave in Card Background */}
              <div className="absolute inset-0 overflow-hidden pointer-events-none flex items-center justify-center opacity-35 select-none">
                <Matrix
                  rows={6}
                  cols={26}
                  frames={stageWave}
                  size={2.4}
                  gap={1.2}
                  fps={isActive ? 22 : isCompleted ? 6 : 0}
                  autoplay={isActive || isCompleted}
                  loop={true}
                  palette={{
                    on: isActive ? '#ffffff' : isCompleted ? 'rgba(255,255,255,0.5)' : 'rgba(255,255,255,0.15)',
                    off: 'rgba(255,255,255,0.02)'
                  }}
                />
              </div>

              {/* Card Header Info */}
              <div className="relative z-10 flex items-center justify-between text-[9px] text-white/50 uppercase">
                <span className="flex items-center gap-1.5">
                  <span className="font-bold">Stage 0{idx + 1}</span>
                  {isActive && (
                    <span className="px-1.5 py-0.5 rounded-full bg-white/15 border border-white/30 text-white text-[7.5px] font-bold animate-pulse">
                      PROCESSING
                    </span>
                  )}
                  {isCompleted && (
                    <span className="px-1.5 py-0.5 rounded-full bg-white/10 border border-white/20 text-white/80 text-[7.5px] font-bold">
                      VERIFIED
                    </span>
                  )}
                </span>
                <span className={`h-2 w-2 rounded-full transition-all duration-300 ${
                  isActive 
                    ? 'bg-white shadow-[0_0_8px_#ffffff] animate-ping' 
                    : isCompleted
                      ? 'bg-white/80 shadow-[0_0_4px_#ffffff]'
                      : 'bg-white/20'
                }`} />
              </div>

              {/* Title & Description */}
              <h4 className={`relative z-10 text-xs font-bold tracking-wide transition-colors ${
                isActive ? 'text-white' : isCompleted ? 'text-white/90' : 'text-white/60'
              }`}>
                {s.label}
              </h4>
              <p className="relative z-10 text-[9.5px] text-white/50 font-mono truncate">{s.desc}</p>
              
              {/* Footer Tech Lib */}
              <div className="relative z-10 text-[8.5px] text-white/40 pt-1 border-t border-white/[0.06] truncate flex items-center justify-between">
                <span>{s.lib}</span>
                {isActive && (
                  <span className="text-white font-mono text-[8px] font-bold animate-pulse">SWARM ACTIVE</span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* ── MAIN CONTENT: TWO-COLUMN FILING & LIVE LOG ── */}
      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 gap-5 overflow-hidden">
        
        {/* LEFT COLUMN: Event Selector & Regulatory Brief Form (5 Cols) */}
        <div className="lg:col-span-5 h-full overflow-y-auto pr-1 flex flex-col gap-4">
          
          {/* Filing Generator Card */}
          <div className="p-5 rounded-2xl bg-black/30 border border-white/[0.08] flex flex-col gap-4">
            <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-emerald-400" />
                <h3 className="font-bold text-xs text-white font-mono uppercase">
                  IN-SPACe Regulatory Filing Generator
                </h3>
              </div>
              <span className="text-[9px] font-mono text-white/40">IADC 2024</span>
            </div>

            <form onSubmit={handleSubmitFiling} className="flex flex-col gap-3.5 text-xs font-mono">
              
              {/* Event Selector */}
              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] font-bold text-white/50 uppercase">Select Flagged Conjunction</label>
                <select
                  value={selectedEventId}
                  onChange={(e) => setSelectedEventId(e.target.value)}
                  className="w-full px-3 py-2 bg-black/50 border border-white/[0.1] rounded-xl text-xs text-white focus:border-white/40 focus:outline-none transition cursor-pointer"
                >
                  <option value="">-- Choose High-Risk Conjunction --</option>
                  {conjunctions.map((c) => (
                    <option key={c.id} value={String(c.id)}>
                      {c.primary_name} vs {c.secondary_name} (Pc: {c.pc.toExponential(1)})
                    </option>
                  ))}
                </select>
              </div>

              {/* Operator Name */}
              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] font-bold text-white/50 uppercase">Authorised Operator</label>
                <div className="relative">
                  <User className="absolute left-3 top-2.5 h-3.5 w-3.5 text-white/40" />
                  <input
                    type="text"
                    value={operatorName}
                    onChange={(e) => setOperatorName(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-black/50 border border-white/[0.1] rounded-xl text-xs text-white focus:border-white/40 focus:outline-none transition"
                  />
                </div>
              </div>

              {/* Event Telemetry Preview */}
              {eventDetails && (
                <div className="p-3 bg-white/[0.02] border border-white/[0.06] rounded-xl flex flex-col gap-2 text-[10px]">
                  <div className="flex justify-between">
                    <span className="text-white/40">PRIMARY:</span>
                    <span className="text-white font-bold">{eventDetails.primary?.name || eventDetails.primary_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">SECONDARY:</span>
                    <span className="text-rose-400 font-bold">{eventDetails.secondary?.name || eventDetails.secondary_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">COLLISION PROBABILITY:</span>
                    <span className="text-amber-400 font-bold">{eventDetails.pc.toExponential(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">MISS DISTANCE:</span>
                    <span className="text-white">{eventDetails.miss_distance.toFixed(3)} km</span>
                  </div>
                </div>
              )}

              {errorMsg && (
                <div className="p-2.5 bg-rose-500/10 border border-rose-500/30 text-rose-400 rounded-xl text-[10px]">
                  {errorMsg}
                </div>
              )}

              <button
                type="submit"
                disabled={isSubmitting || !selectedEventId}
                className="w-full flex items-center justify-center gap-2 py-2.5 bg-white hover:bg-white/90 disabled:bg-white/10 disabled:text-white/30 text-black font-bold text-xs rounded-xl transition cursor-pointer shadow-sm"
              >
                {isSubmitting ? (
                  <>
                    <RefreshCw size={13} className="animate-spin" />
                    Synthesizing Regulatory Brief...
                  </>
                ) : (
                  <>
                    <FileText size={13} />
                    Generate & Submit Filing to IN-SPACe
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Past Filings Register */}
          {pastFilings.length > 0 && (
            <div className="p-4 rounded-2xl bg-black/30 border border-white/[0.08] flex flex-col gap-2.5">
              <div className="text-[10px] font-mono font-bold text-white/50 uppercase">
                Archived Regulatory Filings ({pastFilings.length})
              </div>
              <div className="flex flex-col gap-1.5 max-h-40 overflow-y-auto pr-1 font-mono text-[10px]">
                {pastFilings.map((f: any) => (
                  <div key={f.id} className="p-2 bg-white/[0.02] border border-white/[0.05] rounded-lg flex items-center justify-between">
                    <div>
                      <div className="text-white font-semibold">{f.satellite_name || `NORAD ${f.norad_id}`}</div>
                      <div className="text-white/40">{new Date(f.filed_at).toLocaleDateString()} • {f.justification_type || 'CAM Plan'}</div>
                    </div>
                    <button
                      onClick={() => window.open(`${API_BASE_URL}/api/compliance/download/${f.id}`, '_blank')}
                      className="p-1.5 bg-white/[0.06] hover:bg-white/10 text-white rounded-lg transition cursor-pointer"
                      title="Download PDF"
                    >
                      <Download size={12} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>

        {/* RIGHT COLUMN: Live Multi-Stage Pipeline Execution Log & Generated Filing (7 Cols) */}
        <div className="lg:col-span-7 h-full flex flex-col gap-3 min-h-0">
          
          {/* Terminal / Live Execution Log */}
          <div className="flex-1 flex flex-col bg-[#050508] border border-white/[0.08] rounded-2xl overflow-hidden relative shadow-2xl min-h-0">
            
            {/* Terminal Header */}
            <div className="px-4 py-2 border-b border-white/[0.06] bg-[#09090d] text-white/50 font-mono text-[10px] flex items-center justify-between shrink-0">
              <div className="flex items-center gap-2">
                <TerminalIcon className="h-3.5 w-3.5 text-white/70" />
                <span className="text-white/70 font-semibold">STAGE_EXECUTION_STREAM.LOG</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1.5 font-medium">
                  <Activity size={12} />
                  Progress: {pipelineProgress}%
                </span>
                <span className={`h-1.5 w-1.5 rounded-full ${isRunningPipeline ? 'bg-emerald-400 animate-ping' : 'bg-white/30'}`} />
              </div>
            </div>

            {/* Terminal Output */}
            <div className="flex-1 overflow-y-auto p-4 font-mono text-xs text-emerald-400/90 flex flex-col gap-1.5">
              {logs.length === 0 ? (
                <div className="flex flex-col gap-1 text-white/30 mt-2 font-mono">
                  <div>// 6-Stage Automated Regulatory Compliance Engine.</div>
                  <div>// Click "Execute 6-Stage Pipeline" above to run live astrodynamics consensus & compliance generation.</div>
                  <div className="flex items-center gap-1.5 mt-3 text-white/40">
                    <span className="h-2 w-1.5 bg-emerald-400 animate-pulse" />
                    <span>Engine standby...</span>
                  </div>
                </div>
              ) : (
                <>
                  {logs.map((log, i) => (
                    <div key={i} className="flex gap-2.5 hover:bg-white/[0.02] py-0.5 px-1 rounded transition-colors group">
                      <span className="text-[10px] text-emerald-600/80 select-none shrink-0 min-w-[60px]">
                        [{new Date(log.timestamp).toLocaleTimeString()}]
                      </span>
                      <span className="font-semibold text-white/80 shrink-0 min-w-[120px]">
                        {log.agent}
                      </span>
                      <span className="text-slate-300 break-all leading-normal group-hover:text-white">
                        {log.log}
                      </span>
                    </div>
                  ))}
                  
                  {isRunningPipeline && (
                    <div className="flex gap-2.5 py-0.5 px-1 mt-1">
                      <span className="text-[10px] text-emerald-600 select-none shrink-0 min-w-[60px]" />
                      <span className="text-emerald-400 font-bold shrink-0 min-w-[120px]">EXECUTING</span>
                      <span className="flex items-center gap-1">
                        <span className="h-3 w-1.5 bg-emerald-400 animate-pulse" />
                        <span className="text-white/40 italic text-[10px]">propagating mathematical pipeline...</span>
                      </span>
                    </div>
                  )}
                </>
              )}
              <div ref={terminalEndRef} />
            </div>
          </div>

          {/* Single Event Filing Result Box (When generated via form) */}
          {filingResult && (
            <div className="p-4 rounded-xl bg-black/40 border border-white/[0.08] flex items-center justify-between shrink-0 font-mono">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <CheckCircle size={16} />
                </div>
                <div>
                  <div className="text-xs font-bold text-white flex items-center gap-2">
                    <span>Filing IN-SPACe-{filingResult.filing_id} Generated</span>
                    <span className="text-[8px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                      LLM-JUSTIFIED
                    </span>
                  </div>
                  <div className="text-[10px] text-white/50">{filingResult.maneuver_decision}</div>
                </div>
              </div>
              <button
                onClick={() => window.open(`${API_BASE_URL}/api/compliance/download/${filingResult.filing_id}`, '_blank')}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 rounded-lg text-xs font-bold transition cursor-pointer"
              >
                <Download size={12} />
                Download PDF
              </button>
            </div>
          )}

        </div>

      </div>

    </div>
  );
};
