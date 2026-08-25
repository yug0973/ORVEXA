import React from 'react';
import {
  Globe,
  RefreshCw,
  AlertOctagon,
  FileText,
  MessageSquare
} from 'lucide-react';
import { DiscreteTabs, type TabItem } from './ui/discrete-tabs';

export type ActivePanel =
  | 'globe'
  | 'conjunctions'
  | 'reentry'
  | 'compliance';

interface SidebarProps {
  activePanel: ActivePanel;
  setActivePanel: (panel: ActivePanel) => void;
  isCopilotOpen?: boolean;
  onToggleCopilot?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activePanel,
  setActivePanel,
  isCopilotOpen = false,
  onToggleCopilot
}) => {
  const tabs: TabItem[] = [
    {
      id: 'globe',
      label: '3D Orbit Globe',
      icon: <Globe size={16} />,
      activeColor: 'text-white',
      badge: 'live'
    },
    {
      id: 'conjunctions',
      label: 'Conjunctions',
      icon: <RefreshCw size={16} />,
      activeColor: 'text-rose-400',
      badge: 'alert'
    },
    {
      id: 'reentry',
      label: 'Reentry Console',
      icon: <AlertOctagon size={16} />,
      activeColor: 'text-amber-400'
    },
    {
      id: 'compliance',
      label: 'Compliance Hub',
      icon: <FileText size={16} />,
      activeColor: 'text-emerald-400'
    }
  ];

  return (
    <div className="relative flex items-center gap-2 pointer-events-auto">
      <DiscreteTabs
        tabs={tabs}
        activeTab={activePanel}
        onTabChange={(id) => setActivePanel(id as ActivePanel)}
      />

      {onToggleCopilot && (
        <button
          onClick={onToggleCopilot}
          aria-label="AI Flight Copilot"
          title="Toggle Copilot Drawer"
          className={`relative flex items-center justify-center w-11 h-11 rounded-full transition-all duration-300 backdrop-blur-2xl border shadow-lg cursor-pointer ${
            isCopilotOpen
              ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.3)] scale-105'
              : 'bg-[#0c0d12]/90 border-white/[0.12] text-white/50 hover:text-white hover:bg-white/[0.08] hover:border-white/[0.2]'
          }`}
        >
          <MessageSquare size={16} />
          <span className="absolute top-2.5 right-2.5 h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
        </button>
      )}
    </div>
  );
};

