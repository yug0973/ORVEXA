import { useState, Suspense, lazy, useEffect } from 'react';
import axios from 'axios';
import { AlertOctagon } from 'lucide-react';
import { Topbar } from './components/Topbar';
import { Sidebar } from './components/Sidebar';
import { EntryPortal } from './components/EntryPortal';
import { CopilotDrawer } from './components/CopilotDrawer';
import type { ActivePanel } from './components/Sidebar';
import { API_BASE_URL, getWebSocketUrl } from './config';

// Exactly 4 Core Pillars of ORVEXA Space Situational Awareness
const OrbitMapPage = lazy(() => import('./pages/OrbitMapPage').then(m => ({ default: m.OrbitMapPage })));
const ConjunctionPage = lazy(() => import('./pages/ConjunctionPage').then(m => ({ default: m.ConjunctionPage })));
const ReentryPage = lazy(() => import('./pages/ReentryPage').then(m => ({ default: m.ReentryPage })));
const CompliancePage = lazy(() => import('./pages/CompliancePage').then(m => ({ default: m.CompliancePage })));

function App() {
  const [activePanel, setActivePanel] = useState<ActivePanel>('globe');
  const [selectedConjunction, setSelectedConjunction] = useState<{ id: string; satellite: string } | null>(null);
  const [solarAlert, setSolarAlert] = useState<{ type: 'geomagnetic' | 'flux'; val: number; scaler: number } | null>(null);
  const [solarMetrics, setSolarMetrics] = useState<{ ap: number; f10_7: number; drag_scaler: number } | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'info' | 'warning' | 'success' } | null>(null);
  const [hasEntered, setHasEntered] = useState(false);
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);

  useEffect(() => {
    const checkSolarWeather = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/solar`);
        const { ap, f10_7, drag_scaler } = response.data;
        setSolarMetrics({ ap, f10_7, drag_scaler });
        if (ap >= 20.0) {
          setSolarAlert({ type: 'geomagnetic', val: ap, scaler: drag_scaler });
        } else if (f10_7 >= 140.0) {
          setSolarAlert({ type: 'flux', val: f10_7, scaler: drag_scaler });
        }
      } catch (e) {
        console.error("Error loading space weather warnings:", e);
      }
    };
    checkSolarWeather();
  }, []);

  // WebSocket Alerts Connection
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: any = null;

    const connectWS = () => {
      try {
        const wsUrl = getWebSocketUrl('/api/ws/alerts');
        ws = new WebSocket(wsUrl);

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.event === 'solar_storm_rescreen') {
              setToast({ message: data.toast, type: 'warning' });
            } else if (data.event === 'solar_storm_cleared') {
              setToast({ message: data.toast, type: 'success' });
            }
          } catch (e) {
            console.error("Error parsing WebSocket alert message:", e);
          }
        };

        ws.onclose = () => {
          reconnectTimeout = setTimeout(connectWS, 3000);
        };
      } catch (err) {
        console.error("WebSocket connection error:", err);
      }
    };

    connectWS();

    return () => {
      if (ws) ws.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, []);

  // Auto-dismiss toast
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 6000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  const handleInitiateFiling = (eventId: string, satelliteName: string) => {
    setSelectedConjunction({ id: eventId, satellite: satelliteName });
    setActivePanel('compliance');
  };

  const toggleSolarSimulation = async () => {
    if (solarAlert) {
      try {
        await axios.post(`${API_BASE_URL}/api/solar/clear-flare`);
        setSolarAlert(null);
        const response = await axios.get(`${API_BASE_URL}/api/solar`);
        const { ap, f10_7, drag_scaler } = response.data;
        setSolarMetrics({ ap, f10_7, drag_scaler });
      } catch (err) {
        console.error("Error clearing solar simulation:", err);
      }
    } else {
      try {
        await axios.post(`${API_BASE_URL}/api/solar/trigger-flare/X`);
        setSolarAlert({ type: 'geomagnetic', val: 54.2, scaler: 3.06 });
        const response = await axios.get(`${API_BASE_URL}/api/solar`);
        const { ap, f10_7, drag_scaler } = response.data;
        setSolarMetrics({ ap, f10_7, drag_scaler });
      } catch (err) {
        console.error("Error triggering solar simulation:", err);
      }
    }
  };

  // Render exactly the 4 SSA Pillars
  const renderPanelContent = () => {
    switch (activePanel) {
      case 'globe':
        return <OrbitMapPage isSimActive={!!solarAlert} />;
        
      case 'conjunctions':
        return <ConjunctionPage onInitiateFiling={handleInitiateFiling} />;
        
      case 'reentry':
        return <ReentryPage />;
        
      case 'compliance':
        return <CompliancePage selectedConjunction={selectedConjunction} />;
        
      default:
        return <OrbitMapPage isSimActive={!!solarAlert} />;
    }
  };

  return (
    <div className="h-screen w-screen overflow-hidden relative" style={{ background: '#0a0a0a', color: '#ffffff' }}>
      
      {!hasEntered && (
        <EntryPortal 
          onEnter={() => setHasEntered(true)} 
        />
      )}

      {/* 1. Main Background Canvas (Globe) or Content Area */}
      <main 
        className={`absolute inset-0 z-0 ${
          activePanel === 'globe' 
            ? 'overflow-hidden flex' 
            : 'overflow-hidden pt-[64px] pb-[60px] px-3 sm:px-6 flex flex-col w-full h-full'
        }`}
      >
        <Suspense fallback={
          <div className="w-full h-full flex flex-col items-center justify-center gap-3 font-mono text-xs text-white/50">
            <span className="animate-pulse">LOADING ORVEXA CORE...</span>
          </div>
        }>
          {renderPanelContent()}
        </Suspense>
      </main>

      {/* 2. Floating Top Header Area */}
      <div className="absolute top-0 left-0 right-0 z-40 pointer-events-none flex flex-col">
        <div className="pointer-events-auto">
          <Topbar 
            onToggleSim={toggleSolarSimulation} 
            isSimActive={!!solarAlert} 
            solarMetrics={solarMetrics}
            trackedCount={104}
            onToggleCopilot={() => setIsCopilotOpen(!isCopilotOpen)}
            isCopilotOpen={isCopilotOpen}
          />
        </div>

        {/* Space weather warning banner */}
        {solarAlert && (
          <div className="pointer-events-auto mx-auto mt-4 max-w-3xl w-full" style={{
            padding: '8px 14px',
            borderRadius: 8,
            border: '1px solid rgba(239,68,68,0.25)',
            background: 'rgba(239,68,68,0.08)',
            color: '#ef4444',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 10,
            letterSpacing: '0.04em',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 12,
            backdropFilter: 'blur(16px)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <AlertOctagon size={12} style={{ flexShrink: 0 }} />
              <span>
                {solarAlert.type === 'geomagnetic'
                  ? `⚠ GEOMAGNETIC STORM ACTIVE — Ap: ${solarAlert.val.toFixed(1)} — Thermosphere density ×${solarAlert.scaler.toFixed(2)}. LEO decay rates elevated.`
                  : `⚠ SOLAR FLUX ALERT — F10.7: ${solarAlert.val.toFixed(1)} sfu — Enhanced drag profile active.`
                }
              </span>
            </div>
            <button
              onClick={() => setSolarAlert(null)}
              style={{ background: 'none', border: 'none', color: '#999', cursor: 'pointer', fontSize: 16, lineHeight: 1 }}
            >×</button>
          </div>
        )}
      </div>

      {/* 3. Floating Bottom Navigation (Sidebar) */}
      <div className="absolute bottom-2.5 left-0 right-0 z-40 pointer-events-none flex justify-center">
        <div className="pointer-events-auto">
          <Sidebar 
            activePanel={activePanel} 
            setActivePanel={setActivePanel} 
            isCopilotOpen={isCopilotOpen}
            onToggleCopilot={() => setIsCopilotOpen(!isCopilotOpen)}
          />
        </div>
      </div>

      {/* 4. AI Astrometry Copilot Slide-out Drawer */}
      <CopilotDrawer
        isOpen={isCopilotOpen}
        onClose={() => setIsCopilotOpen(false)}
      />

      {/* Premium Toast Notification Pop-up */}
      {toast && (
        <div className={`fixed bottom-24 right-6 z-[100] px-5 py-4 rounded-xl shadow-2xl flex items-center gap-3 border font-mono text-[11px] animate-slide-in glassmorphism max-w-sm
          ${toast.type === 'warning' 
            ? 'border-orange-500/35 bg-orange-950/20 text-orange-400' 
            : 'border-emerald-500/35 bg-emerald-950/20 text-emerald-400'
          }`}
        >
          <span className={`h-2 w-2 rounded-full shrink-0 ${toast.type === 'warning' ? 'bg-orange-500 animate-ping' : 'bg-emerald-500 animate-pulse'}`} />
          <div className="flex-1">
            <div className="font-bold uppercase tracking-wider mb-0.5">
              {toast.type === 'warning' ? "Solar Activity Alert" : "Weather Cleared"}
            </div>
            <div className="text-slate-300 font-sans leading-relaxed text-xs">{toast.message}</div>
          </div>
          <button 
            onClick={() => setToast(null)}
            className="text-slate-500 hover:text-slate-300 font-sans font-bold text-sm shrink-0 pl-2 self-start cursor-pointer"
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
