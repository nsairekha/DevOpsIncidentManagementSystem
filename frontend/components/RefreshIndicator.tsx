"use client";

import React, { useEffect, useState } from "react";
import { RefreshCw, Pause, Play } from "lucide-react";

interface RefreshIndicatorProps {
  lastUpdated: Date | null;
  onRefresh: () => void | Promise<void>;
  intervalSeconds?: number;
  isRefreshing?: boolean;
}

export default function RefreshIndicator({
  lastUpdated,
  onRefresh,
  intervalSeconds = 10,
  isRefreshing = false,
}: RefreshIndicatorProps) {
  const [secondsAgo, setSecondsAgo] = useState(0);
  const [isPaused, setIsPaused] = useState(false);

  // Tick seconds ago
  useEffect(() => {
    if (!lastUpdated) return;

    const tick = () => {
      const diff = Math.max(
        0,
        Math.floor((Date.now() - lastUpdated.getTime()) / 1000)
      );
      setSecondsAgo(diff);
    };

    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [lastUpdated]);

  // Auto-refresh timer
  useEffect(() => {
    if (isPaused) return;

    const timer = setInterval(() => {
      onRefresh();
    }, intervalSeconds * 1000);

    return () => clearInterval(timer);
  }, [onRefresh, intervalSeconds, isPaused]);

  return (
    <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-surface-subtle border border-border text-[11px] font-mono text-slate-400">
      <span className="relative flex h-2 w-2">
        {!isPaused && (
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
        )}
        <span
          className={`relative inline-flex rounded-full h-2 w-2 ${
            isPaused ? "bg-slate-500" : "bg-cyan-400"
          }`}
        />
      </span>

      <span>
        Last updated:{" "}
        <strong className="text-slate-200">
          {lastUpdated ? `${secondsAgo}s ago` : "Waiting..."}
        </strong>
      </span>

      <button
        onClick={() => onRefresh()}
        disabled={isRefreshing}
        title="Refresh now"
        className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
      >
        <RefreshCw
          className={`h-3 w-3 ${isRefreshing ? "animate-spin text-cyan-400" : ""}`}
        />
      </button>

      <button
        onClick={() => setIsPaused(!isPaused)}
        title={isPaused ? "Resume auto-refresh (10s)" : "Pause auto-refresh"}
        className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
      >
        {isPaused ? <Play className="h-3 w-3" /> : <Pause className="h-3 w-3" />}
      </button>
    </div>
  );
}
