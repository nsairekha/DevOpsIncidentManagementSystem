"use client";

import React from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface SeriesConfig {
  key: string;
  name: string;
  color: string;
  strokeWidth?: number;
  strokeDasharray?: string;
  type?: "line" | "area";
}

interface MetricChartProps {
  title: string;
  subtitle?: string;
  data: any[];
  xAxisKey?: string;
  series: SeriesConfig[];
  unit?: string;
  height?: number;
  chartType?: "line" | "area";
  showLegend?: boolean;
}

export default function MetricChart({
  title,
  subtitle,
  data,
  xAxisKey = "time",
  series,
  unit = "",
  height = 240,
  chartType = "area",
  showLegend = false,
}: MetricChartProps) {
  const customTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="rounded-md border border-border bg-slate-900/95 p-2.5 shadow-xl backdrop-blur-sm text-xs font-mono">
          <p className="text-slate-400 font-semibold mb-1 border-b border-border/60 pb-1">
            Time: {label}
          </p>
          {payload.map((entry: any, index: number) => (
            <div
              key={`item-${index}`}
              className="flex items-center justify-between gap-4 py-0.5"
            >
              <span className="flex items-center gap-1.5" style={{ color: entry.color }}>
                <span
                  className="inline-block w-2 h-2 rounded-full"
                  style={{ backgroundColor: entry.color }}
                />
                {entry.name}:
              </span>
              <span className="font-bold text-white">
                {typeof entry.value === "number"
                  ? entry.value.toFixed(2)
                  : entry.value}{" "}
                {unit}
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="rounded-lg bg-surface border border-border p-4 flex flex-col justify-between">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="text-sm font-semibold text-slate-200 tracking-tight">
            {title}
          </h4>
          {subtitle && (
            <p className="text-[11px] font-mono text-slate-400">{subtitle}</p>
          )}
        </div>
        {unit && (
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-surface-subtle border border-border/70 text-slate-400">
            {unit}
          </span>
        )}
      </div>

      <div style={{ width: "100%", height }}>
        <ResponsiveContainer width="100%" height="100%">
          {chartType === "area" ? (
            <AreaChart
              data={data}
              margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
            >
              <defs>
                {series.map((s) => (
                  <linearGradient
                    key={s.key}
                    id={`grad-${s.key}`}
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop offset="5%" stopColor={s.color} stopOpacity={0.35} />
                    <stop offset="95%" stopColor={s.color} stopOpacity={0.0} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#1e293b"
                vertical={false}
              />
              <XAxis
                dataKey={xAxisKey}
                stroke="#475569"
                tick={{ fill: "#64748b", fontSize: 11, fontFamily: "monospace" }}
                tickLine={false}
                axisLine={{ stroke: "#1e293b" }}
              />
              <YAxis
                stroke="#475569"
                tick={{ fill: "#64748b", fontSize: 11, fontFamily: "monospace" }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(val) =>
                  val >= 1000 ? `${(val / 1000).toFixed(1)}k` : val
                }
              />
              <Tooltip content={customTooltip} />
              {showLegend && (
                <Legend
                  wrapperStyle={{
                    fontSize: "11px",
                    fontFamily: "monospace",
                    paddingTop: "6px",
                  }}
                />
              )}
              {series.map((s) => (
                <Area
                  key={s.key}
                  type="monotone"
                  dataKey={s.key}
                  name={s.name}
                  stroke={s.color}
                  strokeWidth={s.strokeWidth || 2}
                  fillOpacity={1}
                  fill={`url(#grad-${s.key})`}
                />
              ))}
            </AreaChart>
          ) : (
            <LineChart
              data={data}
              margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#1e293b"
                vertical={false}
              />
              <XAxis
                dataKey={xAxisKey}
                stroke="#475569"
                tick={{ fill: "#64748b", fontSize: 11, fontFamily: "monospace" }}
                tickLine={false}
                axisLine={{ stroke: "#1e293b" }}
              />
              <YAxis
                stroke="#475569"
                tick={{ fill: "#64748b", fontSize: 11, fontFamily: "monospace" }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(val) =>
                  val >= 1000 ? `${(val / 1000).toFixed(1)}k` : val
                }
              />
              <Tooltip content={customTooltip} />
              {showLegend && (
                <Legend
                  wrapperStyle={{
                    fontSize: "11px",
                    fontFamily: "monospace",
                    paddingTop: "6px",
                  }}
                />
              )}
              {series.map((s) => (
                <Line
                  key={s.key}
                  type="monotone"
                  dataKey={s.key}
                  name={s.name}
                  stroke={s.color}
                  strokeWidth={s.strokeWidth || 2}
                  strokeDasharray={s.strokeDasharray}
                  dot={false}
                  activeDot={{ r: 4, stroke: "#0f172a", strokeWidth: 2 }}
                />
              ))}
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}
