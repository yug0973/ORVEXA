"use client";

import { useEffect, useRef, useCallback } from "react";
import { useState } from "react";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import {
    ShieldAlert,
    Satellite,
    SunMedium,
    TrendingDown,
    Crosshair,
    ArrowUp,
    Terminal,
} from "lucide-react";

interface UseAutoResizeTextareaProps {
    minHeight: number;
    maxHeight?: number;
}

function useAutoResizeTextarea({
    minHeight,
    maxHeight,
}: UseAutoResizeTextareaProps) {
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const adjustHeight = useCallback(
        (reset?: boolean) => {
            const textarea = textareaRef.current;
            if (!textarea) return;

            if (reset) {
                textarea.style.height = `${minHeight}px`;
                return;
            }

            textarea.style.height = `${minHeight}px`;
            const newHeight = Math.max(
                minHeight,
                Math.min(
                    textarea.scrollHeight,
                    maxHeight ?? Number.POSITIVE_INFINITY
                )
            );
            textarea.style.height = `${newHeight}px`;
        },
        [minHeight, maxHeight]
    );

    useEffect(() => {
        const textarea = textareaRef.current;
        if (textarea) {
            textarea.style.height = `${minHeight}px`;
        }
    }, [minHeight]);

    useEffect(() => {
        const handleResize = () => adjustHeight();
        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, [adjustHeight]);

    return { textareaRef, adjustHeight };
}

export interface VercelV0ChatProps {
    onSubmit?: (message: string) => void;
    disabled?: boolean;
    placeholder?: string;
}

export function VercelV0Chat({ 
    onSubmit, 
    disabled,
    placeholder = "Transmit telemetry query or command (e.g. ISS conjunctions, solar flux, deorbit ETA)..." 
}: VercelV0ChatProps) {
    const [value, setValue] = useState("");
    const { textareaRef, adjustHeight } = useAutoResizeTextarea({
        minHeight: 48,
        maxHeight: 140,
    });

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            if (value.trim() && !disabled) {
                onSubmit?.(value);
                setValue("");
                adjustHeight(true);
            }
        }
    };

    const handleSubmit = () => {
        if (value.trim() && !disabled) {
            onSubmit?.(value);
            setValue("");
            adjustHeight(true);
        }
    };

    const handleActionClick = (prompt: string) => {
        if (!disabled) {
            onSubmit?.(prompt);
        }
    };

    const quickActions = [
        {
            icon: <ShieldAlert className="w-3 h-3 text-rose-400" />,
            label: "Conjunction Risks",
            prompt: "List all high-risk conjunction events with Pc exceeding 1e-4",
        },
        {
            icon: <Satellite className="w-3 h-3 text-white/70" />,
            label: "ISS Telemetry",
            prompt: "What is the orbital state and active conjunction status of ISS (ZARYA)?",
        },
        {
            icon: <SunMedium className="w-3 h-3 text-amber-400" />,
            label: "Space Weather",
            prompt: "Summarize current NOAA solar radio flux (F10.7) and geomagnetic Ap indices",
        },
        {
            icon: <TrendingDown className="w-3 h-3 text-cyan-300" />,
            label: "Atmospheric Drag",
            prompt: "Analyze current thermospheric drag multiplier and decay rates for LEO payloads",
        },
        {
            icon: <Crosshair className="w-3 h-3 text-emerald-400" />,
            label: "Avoidance Burns",
            prompt: "What is the recommended maneuver burn strategy for critical encounter geometry?",
        },
    ];

    return (
        <div className="flex flex-col items-center w-full mx-auto gap-2.5">
            {/* Quick Action Chips */}
            <div className="flex items-center justify-start flex-wrap gap-1.5 w-full">
                {quickActions.map((action, idx) => (
                    <button
                        key={idx}
                        type="button"
                        disabled={disabled}
                        onClick={() => handleActionClick(action.prompt)}
                        className="flex items-center gap-1.5 px-2.5 py-1 bg-white/[0.02] hover:bg-white/[0.06] rounded-lg border border-white/[0.07] hover:border-white/[0.14] text-white/70 hover:text-white transition-all text-[10px] font-mono disabled:opacity-40 cursor-pointer"
                    >
                        {action.icon}
                        <span>{action.label}</span>
                    </button>
                ))}
            </div>

            {/* Input Box */}
            <div className="w-full">
                <div className="relative bg-black/60 rounded-2xl border border-white/[0.09] focus-within:border-white/30 transition-all shadow-xl">
                    <div className="overflow-y-auto">
                        <Textarea
                            ref={textareaRef}
                            value={value}
                            disabled={disabled}
                            onChange={(e) => {
                                setValue(e.target.value);
                                adjustHeight();
                            }}
                            onKeyDown={handleKeyDown}
                            placeholder={disabled ? "Synthesizing astrodynamics telemetry..." : placeholder}
                            className={cn(
                                "w-full px-3.5 py-3",
                                "resize-none",
                                "bg-transparent",
                                "border-none",
                                "text-white text-xs font-mono",
                                "focus:outline-none",
                                "focus-visible:ring-0 focus-visible:ring-offset-0",
                                "placeholder:text-white/30 placeholder:text-xs placeholder:font-mono",
                                "min-h-[48px]"
                            )}
                            style={{
                                overflow: "hidden",
                            }}
                        />
                    </div>

                    <div className="flex items-center justify-between px-3 py-1.5 border-t border-white/[0.05]">
                        <div className="flex items-center gap-2 text-[9.5px] font-mono text-white/40">
                            <Terminal className="w-3 h-3 text-white/30" />
                            <span>↵ Transmit • Shift+↵ Line</span>
                        </div>

                        <div className="flex items-center gap-2">
                            <button
                                type="button"
                                onClick={handleSubmit}
                                disabled={disabled || !value.trim()}
                                className={cn(
                                    "px-3 py-1.5 rounded-xl text-xs font-mono font-bold transition-all flex items-center gap-1.5",
                                    value.trim() && !disabled
                                        ? "bg-white hover:bg-white/90 text-black shadow-sm cursor-pointer"
                                        : "bg-white/[0.04] text-white/20 border border-white/[0.04] cursor-not-allowed"
                                )}
                            >
                                <ArrowUp className="w-3.5 h-3.5" />
                                <span>Transmit</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}


