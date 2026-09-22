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
  // Border based on status
  let statusBorder = "border-slate-200";
  if (status === "warning") {
    statusBorder = "border-amber-300";
  } else if (status === "critical") {
    statusBorder = "border-rose-300";
  }

  // Trend color
  let trendColor = "text-slate-400";
  if (trend === "up") {
    trendColor = trendGood ? "text-emerald-600" : "text-rose-600";
  } else if (trend === "down") {
    trendColor = trendGood ? "text-rose-600" : "text-emerald-600";
  }

  return (
    <div
      className={`rounded-xl bg-white p-5 border ${statusBorder} shadow-sm hover:shadow transition flex flex-col justify-between`}
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-[13px] font-medium text-slate-500">
          {title}
        </span>
        {icon && (
          <span className="p-2 rounded-lg bg-slate-100 text-slate-500">
            {icon}
          </span>
        )}
      </div>

      <div className="flex items-baseline gap-1.5 my-1">
        <span className="text-2xl font-semibold tracking-tight text-slate-900">
          {value}
        </span>
        {unit && (
          <span className="text-sm text-slate-400 font-medium">
            {unit}
          </span>
        )}
      </div>

      <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
        {change ? (
          <div className={`flex items-center gap-1 font-medium ${trendColor}`}>
            {trend === "up" && <ArrowUpRight className="h-3.5 w-3.5" />}
            {trend === "down" && <ArrowDownRight className="h-3.5 w-3.5" />}
            {trend === "neutral" && <Minus className="h-3.5 w-3.5" />}
            <span>{change}</span>
          </div>
        ) : (
          <span className="text-slate-500 text-[11px]">Real-time telemetry</span>
        )}

        {description && (
          <span className="text-[11px] text-slate-500">
            {description}
          </span>
        )}
      </div>
    </div>
  );
}
