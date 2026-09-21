import React from "react";

interface StatusBadgeProps {
  status:
    | "Healthy"
    | "Degraded"
    | "Down"
    | "Operational"
    | "Critical"
    | "Connected"
    | "Disconnected"
    | "Disabled"
    | "Active"
    | "Investigating"
    | "Resolved"
    | "High"
    | "Medium"
    | "Low"
    | string;
  size?: "sm" | "md" | "lg";
  pulse?: boolean;
}

export default function StatusBadge({
  status,
  size = "md",
  pulse = false,
}: StatusBadgeProps) {
  const normalized = status.toLowerCase();

  let colorClasses = "bg-slate-800 text-slate-300 border-slate-700";
  let dotColor = "bg-slate-400";

  if (
    ["healthy", "operational", "connected", "resolved", "low"].includes(
      normalized
    )
  ) {
    colorClasses = "bg-emerald-950/60 text-emerald-400 border-emerald-800/60";
    dotColor = "bg-emerald-400";
  } else if (
    ["degraded", "investigating", "warning", "medium"].includes(normalized)
  ) {
    colorClasses = "bg-amber-950/60 text-amber-400 border-amber-800/60";
    dotColor = "bg-amber-400";
  } else if (
    ["down", "critical", "disconnected", "high", "active"].includes(normalized)
  ) {
    colorClasses = "bg-rose-950/60 text-rose-400 border-rose-800/60";
    dotColor = "bg-rose-400";
  } else if (["disabled"].includes(normalized)) {
    colorClasses = "bg-zinc-800/80 text-zinc-400 border-zinc-700";
    dotColor = "bg-zinc-500";
  }

  const sizeClasses = {
    sm: "text-[11px] px-2 py-0.5 gap-1.5",
    md: "text-xs px-2.5 py-1 gap-1.5",
    lg: "text-sm px-3 py-1.5 gap-2 font-medium",
  }[size];

  return (
    <span
      className={`inline-flex items-center rounded-full font-mono border font-medium uppercase tracking-wider ${colorClasses} ${sizeClasses}`}
    >
      <span className="relative flex h-2 w-2">
        {pulse && (
          <span
            className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${dotColor}`}
          />
        )}
        <span className={`relative inline-flex rounded-full h-2 w-2 ${dotColor}`} />
      </span>
      <span>{status}</span>
    </span>
  );
}
