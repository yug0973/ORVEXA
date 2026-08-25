"use client";

import { useState, useEffect, type FC, type ReactNode } from "react";
import { motion, AnimatePresence } from "motion/react";

export interface TabItem {
  id: string;
  icon: ReactNode;
  label: string;
  activeColor?: string;
  pillar?: string;
  badge?: 'live' | 'alert';
}

export interface DiscreteTabsProps {
  tabs: TabItem[];
  activeTab?: string;
  onTabChange?: (tabId: string) => void;
  defaultTab?: string;
  className?: string;
}

export const DiscreteTabs: FC<DiscreteTabsProps> = ({ 
  tabs, 
  activeTab: controlledActiveTab, 
  onTabChange, 
  defaultTab,
  className = ""
}) => {
  const [internalActiveTab, setInternalActiveTab] = useState<string>(
    controlledActiveTab || defaultTab || tabs[0]?.id
  );
  const [shine, setShine] = useState<boolean>(false);

  const activeTab = controlledActiveTab !== undefined ? controlledActiveTab : internalActiveTab;

  const handleTabClick = (tabId: string) => {
    setInternalActiveTab(tabId);
    if (onTabChange) onTabChange(tabId);
  };

  useEffect(() => {
    setShine(false);
    const timer = setTimeout(() => setShine(true), 500);
    return () => {
      clearTimeout(timer);
      setShine(false);
    };
  }, [activeTab]);

  return (
    <div className={`flex items-center justify-center gap-1.5 p-1.5 rounded-full bg-[#0c0d12]/90 backdrop-blur-2xl border border-white/[0.12] shadow-[0_12px_40px_rgba(0,0,0,0.7),inset_0_1px_1px_rgba(255,255,255,0.15)] overflow-hidden w-fit mx-auto select-none ${className}`}>
      {tabs.map((tab) => {
        const isActive = tab.id === activeTab;
        return (
          <button
            key={tab.id}
            onClick={() => handleTabClick(tab.id)}
            className="relative focus:outline-none cursor-pointer"
            type="button"
          >
            <motion.div
              layout="position"
              transition={{ type: "spring", stiffness: 260, damping: 22, mass: 0.8 }}
              className={`relative flex h-10 ${isActive ? "w-36 sm:w-40" : "w-10"} items-center justify-center rounded-full transition-colors`}
            >
              {isActive && (
                <motion.div
                  layoutId="activeBg"
                  className="absolute inset-0 rounded-full bg-white/[0.12] border border-white/[0.22] shadow-[0_0_20px_rgba(255,255,255,0.12)]"
                  transition={{ type: "spring", stiffness: 280, damping: 24 }}
                />
              )}
              <div className="relative z-10 flex items-center justify-center gap-2 px-2.5 w-full">
                <motion.div
                  animate={{ scale: isActive ? 1.05 : 1 }}
                  className={`flex h-7 w-7 items-center justify-center rounded-full shrink-0 transition-colors ${
                    isActive 
                      ? (tab.activeColor || "text-white") 
                      : "text-white/45 hover:text-white/80"
                  }`}
                >
                  {tab.icon}
                  {tab.badge && !isActive && (
                    <span className="absolute top-1 right-1 flex h-1.5 w-1.5">
                      <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                        tab.badge === 'live' ? 'bg-emerald-400' : 'bg-rose-500'
                      }`} />
                      <span className={`relative inline-flex rounded-full h-1.5 w-1.5 ${
                        tab.badge === 'live' ? 'bg-emerald-500' : 'bg-rose-500'
                      }`} />
                    </span>
                  )}
                </motion.div>

                {isActive && (
                  <motion.span
                    initial={{ width: 0, opacity: 0 }}
                    animate={{ width: "auto", opacity: 1 }}
                    exit={{ width: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className={`relative overflow-hidden whitespace-nowrap text-xs font-mono font-bold tracking-tight ${
                      tab.activeColor || "text-white"
                    }`}
                  >
                    {tab.label}
                    <AnimatePresence>
                      {shine && (
                        <motion.span
                          initial={{ left: "-120%" }}
                          animate={{ left: "120%" }}
                          transition={{ duration: 0.8, ease: "easeInOut" }}
                          className="absolute top-0 bottom-0 w-12 bg-gradient-to-r from-transparent via-white/40 to-transparent pointer-events-none"
                        />
                      )}
                    </AnimatePresence>
                  </motion.span>
                )}
              </div>
            </motion.div>
          </button>
        );
      })}
    </div>
  );
};
