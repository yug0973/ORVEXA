import { useState, useEffect } from 'react';

interface EntryPortalProps {
  onEnter: () => void;
}

export function EntryPortal({ onEnter }: EntryPortalProps) {
  const [isOpening, setIsOpening] = useState(false);

  const handleInitiate = () => {
    if (isOpening) return;
    setIsOpening(true);
    // Smooth gate opening transition before unmounting
    setTimeout(() => {
      onEnter();
    }, 1200);
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.key === 'Enter' || e.code === 'Space') && !isOpening) {
        e.preventDefault();
        handleInitiate();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpening]);

  return (
    <div 
      onClick={handleInitiate}
      className={`fixed inset-0 z-[9999] flex flex-col cursor-pointer select-none ${
        isOpening ? 'pointer-events-none' : 'pointer-events-auto'
      }`}
    >
      {/* Top Gate */}
      <div 
        className="flex-1 bg-black w-full transition-transform duration-[1200ms] ease-[cubic-bezier(0.645,0.045,0.355,1)]"
        style={{ transform: isOpening ? 'translateY(-100%)' : 'translateY(0)' }}
      />
      
      {/* Bottom Gate */}
      <div 
        className="flex-1 bg-black w-full transition-transform duration-[1200ms] ease-[cubic-bezier(0.645,0.045,0.355,1)]"
        style={{ transform: isOpening ? 'translateY(100%)' : 'translateY(0)' }}
      />

      {/* Center content (fades and zooms out cleanly when opening) */}
      <div 
        className={`absolute inset-0 flex flex-col items-center justify-center pointer-events-none transition-all duration-1000 ease-in-out ${
          isOpening ? 'opacity-0 scale-150 blur-xl' : 'opacity-100 scale-100 blur-0'
        }`}
      >
        <h1 
          className="text-5xl md:text-7xl font-bold tracking-[0.3em] text-white font-mono uppercase"
          style={{ textShadow: '0 0 40px rgba(255,255,255,0.6), 0 0 80px rgba(255,255,255,0.2)' }}
        >
          ORVEXA
        </h1>
        <div className="mt-16 text-[10px] md:text-xs text-white/40 tracking-[0.4em] font-mono animate-pulse uppercase">
          PRESS ENTER OR CLICK TO INITIATE
        </div>
      </div>

      {/* Glowing split line in the middle */}
      <div 
        className={`absolute top-1/2 left-0 w-full h-[1px] bg-white/20 transition-all duration-[800ms] ease-out -translate-y-1/2 ${
          isOpening ? 'opacity-0 scale-x-0' : 'opacity-100 scale-x-100'
        }`}
        style={{ boxShadow: '0 0 15px rgba(255,255,255,0.4), 0 0 30px rgba(255,255,255,0.2)' }}
      />
    </div>
  );
}
