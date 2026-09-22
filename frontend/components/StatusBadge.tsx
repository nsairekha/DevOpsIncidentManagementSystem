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

  let colorClasses = "bg-slate-100 text-slate-600 border-slate-200";
  let dotColor = "bg-slate-400";

  if (
    ["healthy", "operational", "connected", "resolved", "low"].includes(
      normalized
    )
  ) {
    colorClasses = "bg-emerald-50 text-emerald-700 border-emerald-200";
    dotColor = "bg-emerald-500";
  } else if (
    ["degraded", "investigating", "warning", "medium"].includes(normalized)
  ) {
    colorClasses = "bg-amber-50 text-amber-700 border-amber-200";
    dotColor = "bg-amber-500";
  } else if (
    ["down", "critical", "disconnected", "high", "active"].includes(normalized)
  ) {
    colorClasses = "bg-rose-50 text-rose-700 border-rose-200";
    dotColor = "bg-rose-500";
  } else if (["disabled"].includes(normalized)) {
    colorClasses = "bg-slate-100 text-slate-500 border-slate-200";
    dotColor = "bg-slate-400";
  }

  const sizeClasses = {
    sm: "text-[11px] px-2 py-0.5 gap-1.5",
    md: "text-xs px-2.5 py-1 gap-1.5",
    lg: "text-sm px-3 py-1.5 gap-2",
  }[size];

  return (
    <span
      className={`inline-flex items-center rounded-full border font-medium ${colorClasses} ${sizeClasses}`}
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
