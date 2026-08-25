import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import { VercelV0Chat } from '../components/ui/v0-ai-chat';
import { Terminal, User, Trash2 } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export const CopilotPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "ORVEXA Astrodynamics Terminal online. Query conjunction geometries, B-Plane collision risks, deorbit compliance, or thermospheric drag regimes."
    }
  ]);
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<'online' | 'fallback'>('online');
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of conversation
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (query: string) => {
    if (!query.trim()) return;

    const userMessage: Message = { role: 'user', content: query };
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/copilot/chat`, {
        query: query
      });

      setMode(response.data.mode || 'online');
      const botMessage: Message = {
        role: 'assistant',
        content: response.data.response || "No response received from astrodynamics intelligence engine."
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (err: any) {
      console.error("Copilot request error:", err);
      const errorMsg: Message = {
        role: 'assistant',
        content: "Telemetry query failure. Ensure backend astrodynamics daemon is operational."
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearChat = () => {
    setMessages([
      {
        role: 'assistant',
        content: "Terminal session reset. Standing by for telemetry query."
      }
    ]);
  };

  return (
    <div className="flex flex-col gap-3 w-full h-full select-none font-sans overflow-hidden relative">
      
      {/* 1. HEADER SECTION */}
      <div className="p-3.5 px-4 rounded-xl border border-white/[0.08] flex items-center justify-between shrink-0 bg-black/40 backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-xl bg-white/[0.05] border border-white/[0.1] flex items-center justify-center text-white">
            <Terminal className="h-4 w-4 text-white/80" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-bold text-white tracking-wider uppercase font-mono">
                FLIGHT COPILOT TERMINAL
              </h3>
              <span className="text-[8.5px] font-mono px-1.5 py-0.2 rounded bg-white/[0.06] text-white/60 border border-white/[0.08]">
                AIR-GAPPED
              </span>
            </div>
            <div className="text-[9.5px] text-white/40 font-mono mt-0.5 flex items-center gap-1.5">
              <span className={`h-1.5 w-1.5 rounded-full ${mode === 'online' ? 'bg-emerald-400' : 'bg-amber-400'}`} />
              <span>{mode === 'online' ? 'Local Llama 3.2 • Offline Active' : 'Offline Rule Engine'}</span>
            </div>
          </div>
        </div>

        <button 
          onClick={handleClearChat}
          className="p-1.5 rounded-lg border border-white/[0.08] hover:border-white/20 bg-white/[0.02] hover:bg-white/[0.06] text-white/40 hover:text-white transition cursor-pointer"
          title="Reset Terminal Log"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* 2. CHAT CANVAS */}
      <div className="flex-1 rounded-2xl border border-white/[0.08] p-4 overflow-y-auto flex flex-col gap-3 relative min-h-0 bg-black/40 backdrop-blur-xl font-mono custom-scrollbar">
        {messages.map((msg, idx) => {
          const isAssistant = msg.role === 'assistant';
          
          return (
            <div 
              key={idx} 
              className={`flex gap-2.5 max-w-[85%] ${isAssistant ? 'self-start' : 'self-end flex-row-reverse'}`}
            >
              {/* Avatar Icon */}
              <div className={`h-6 w-6 rounded-lg shrink-0 border flex items-center justify-center text-[9px] font-bold font-mono
                ${isAssistant 
                  ? 'bg-white/[0.04] border-white/[0.1] text-white/70'
                  : 'bg-white text-black border-white'
                }`}
              >
                {isAssistant ? 'OG' : <User size={11} />}
              </div>

              {/* Chat Bubble */}
              <div className={`p-3 rounded-xl text-xs font-mono leading-relaxed border relative
                ${isAssistant 
                  ? 'bg-white/[0.02] border-white/[0.07] text-white/90 rounded-tl-none'
                  : 'bg-white text-black border-white font-medium rounded-tr-none shadow-sm'
                }`}
              >
                <div className="whitespace-pre-line space-y-1">
                  {msg.content.split('\n').map((line, lidx) => {
                    if (line.startsWith('###')) {
                      return <h4 key={lidx} className="text-white font-bold text-xs mt-2 mb-1 uppercase tracking-wider">{line.replace('###', '').trim()}</h4>;
                    }
                    if (line.startsWith('**') && line.endsWith('**')) {
                      return <strong key={lidx} className="text-white block mt-1 font-bold">{line.replace(/\*\*/g, '')}</strong>;
                    }
                    if (line.startsWith('- ')) {
                      return (
                        <div key={lidx} className="pl-3 relative flex items-start gap-1.5 text-white/80">
                          <span className="text-white/40">•</span>
                          <span>{line.substring(2)}</span>
                        </div>
                      );
                    }
                    return <p key={lidx}>{line}</p>;
                  })}
                </div>
              </div>
            </div>
          );
        })}

        {/* Loading Indicator */}
        {loading && (
          <div className="flex gap-2.5 self-start items-center max-w-[80%]">
            <div className="h-6 w-6 rounded-lg bg-white/[0.04] border border-white/[0.1] text-white/70 flex items-center justify-center text-[9px] font-bold font-mono">
              OG
            </div>
            <div className="bg-white/[0.02] border border-white/[0.07] text-white/50 px-3 py-2 rounded-xl text-xs font-mono flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-white/70 animate-pulse" />
              <span>Synthesizing orbital vectors...</span>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* 3. INPUT PANEL & SUGGESTIONS */}
      <div className="shrink-0">
        <VercelV0Chat onSubmit={handleSend} disabled={loading} />
      </div>

    </div>
  );
};