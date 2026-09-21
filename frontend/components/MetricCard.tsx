import React from "react";
import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  change?: string;
  trend?: "up" | "down" | "neutral";
  trendGood?: boolean; // is up good or bad? (e.g. error rate up is bad, availability up is good)
  description?: string;
  status?: "normal" | "warning" | "critical";
  icon?: React.ReactNode;
}

export default function MetricCard({
  title,
  value,
  unit,
  change,
  trend,
  trendGood = true,
  description,
  status = "normal",
  icon,
}: MetricCardProps) {
  // Border and accent based on status
  let statusBorder = "border-border hover:border-slate-700";
  let statusGlow = "";

  if (status === "warning") {
    statusBorder = "border-amber-800/60 hover:border-amber-700/80";
    statusGlow = "shadow-[0_0_15px_-3px_rgba(245,158,11,0.15)]";
  } else if (status === "critical") {
    statusBorder = "border-rose-800/70 hover:border-rose-700";
    statusGlow = "shadow-[0_0_15px_-3px_rgba(239,68,68,0.2)]";
  }

  // Trend color
  let trendColor = "text-slate-400";
  if (trend === "up") {
    trendColor = trendGood ? "text-emerald-400" : "text-rose-400";
  } else if (trend === "down") {
    trendColor = trendGood ? "text-rose-400" : "text-emerald-400";
  }

  return (
    <div
      className={`rounded-lg bg-surface p-4 border transition-all duration-200 ${statusBorder} ${statusGlow} flex flex-col justify-between`}
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
          {title}
        </span>
        {icon && <span className="text-slate-500">{icon}</span>}
      </div>

      <div className="flex items-baseline gap-1.5 my-1">
        <span className="text-2xl font-bold font-mono tracking-tight text-white">
          {value}
        </span>
        {unit && (
          <span className="text-xs font-mono text-slate-400 uppercase font-medium">
            {unit}
          </span>
        )}
      </div>

      <div className="mt-2 pt-2 border-t border-border/40 flex items-center justify-between text-xs">
        {change ? (
          <div className={`flex items-center gap-1 font-mono font-medium ${trendColor}`}>
            {trend === "up" && <ArrowUpRight className="h-3.5 w-3.5" />}
            {trend === "down" && <ArrowDownRight className="h-3.5 w-3.5" />}
            {trend === "neutral" && <Minus className="h-3.5 w-3.5" />}
            <span>{change}</span>
          </div>
        ) : (
          <span className="text-slate-500 text-[11px]">Real-time telemetry</span>
        )}

        {description && (
          <span className="text-[11px] text-slate-400 font-mono">
            {description}
          </span>
        )}
      </div>
    </div>
  );
}
