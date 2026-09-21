import React from "react";
import { AlertTriangle, Database, RefreshCw } from "lucide-react";

interface LoadingStateProps {
  message?: string;
  type?: "cards" | "table" | "chart" | "full";
}

export function LoadingState({
  message = "Loading telemetry data...",
  type = "cards",
}: LoadingStateProps) {
  if (type === "full") {
    return (
      <div className="flex flex-col items-center justify-center min-h-[360px] p-8 text-center space-y-4">
        <div className="relative">
          <div className="w-12 h-12 rounded-full border-2 border-slate-700 border-t-cyan-500 animate-spin" />
        </div>
        <p className="text-sm font-mono text-slate-400">{message}</p>
      </div>
    );
  }

  if (type === "cards") {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-pulse">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div
            key={i}
            className="h-28 rounded-lg bg-surface border border-border/50 p-4 space-y-3"
          >
            <div className="h-3 bg-slate-800 rounded w-1/3" />
            <div className="h-7 bg-slate-700/60 rounded w-1/2" />
            <div className="h-2 bg-slate-800 rounded w-2/3" />
          </div>
        ))}
      </div>
    );
  }

  if (type === "table") {
    return (
      <div className="border border-border rounded-lg bg-surface p-4 space-y-3 animate-pulse">
        <div className="h-8 bg-slate-800 rounded w-full" />
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-10 bg-slate-800/40 rounded w-full" />
        ))}
      </div>
    );
  }

  return (
    <div className="h-64 rounded-lg bg-surface border border-border/50 p-4 flex items-center justify-center animate-pulse">
      <div className="text-xs font-mono text-slate-500">Loading chart data...</div>
    </div>
  );
}

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorState({
  title = "Failed to fetch telemetry",
  message,
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="rounded-lg border border-rose-900/60 bg-rose-950/20 p-5 text-left space-y-3">
      <div className="flex items-start gap-3">
        <AlertTriangle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <h4 className="text-sm font-semibold text-rose-300">{title}</h4>
          <p className="text-xs text-rose-400/80 font-mono break-all">{message}</p>
        </div>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-rose-900/40 hover:bg-rose-900/70 text-rose-200 border border-rose-700/50 transition-colors"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Retry Connection
        </button>
      )}
    </div>
  );
}

interface EmptyStateProps {
  title?: string;
  message?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({
  title = "No data available",
  message = "No active records detected for the selected period.",
  actionLabel,
  onAction,
}: EmptyStateProps) {
  return (
    <div className="rounded-lg border border-border bg-surface/50 p-8 text-center space-y-3">
      <div className="inline-flex p-3 rounded-full bg-slate-800/60 border border-slate-700">
        <Database className="h-6 w-6 text-slate-400" />
      </div>
      <h4 className="text-sm font-medium text-slate-200">{title}</h4>
      <p className="text-xs text-slate-400 max-w-sm mx-auto">{message}</p>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 transition-colors"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}

export default LoadingState;
