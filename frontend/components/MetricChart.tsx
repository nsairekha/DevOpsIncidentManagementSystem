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
        <div className="rounded-lg border border-slate-200 bg-white p-2.5 shadow-lg text-xs">
          <p className="text-slate-500 font-medium mb-1 border-b border-slate-200 pb-1">
            Time: <span className="font-mono">{label}</span>
          </p>
          {payload.map((entry: any, index: number) => (
            <div
              key={`item-${index}`}
              className="flex items-center justify-between gap-4 py-0.5"
            >
              <span className="flex items-center gap-1.5 text-slate-500">
                <span
                  className="inline-block w-2 h-2 rounded-full"
                  style={{ backgroundColor: entry.color }}
                />
                {entry.name}:
              </span>
              <span className="font-semibold text-slate-900">
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
    <div className="rounded-xl bg-white border border-slate-200 shadow-sm p-5 flex flex-col justify-between">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="text-sm font-semibold text-slate-900 tracking-tight">
            {title}
          </h4>
          {subtitle && (
            <p className="text-[11px] text-slate-500">{subtitle}</p>
          )}
        </div>
        {unit && (
          <span className="text-[11px] px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-500">
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
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#E5E7EB"
                vertical={false}
              />
              <XAxis
                dataKey={xAxisKey}
                stroke="#E5E7EB"
                tick={{ fill: "#6B7280", fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: "#E5E7EB" }}
              />
              <YAxis
                stroke="#E5E7EB"
                tick={{ fill: "#6B7280", fontSize: 11 }}
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
                  fill={s.color}
                  fillOpacity={0.1}
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
                stroke="#E5E7EB"
                vertical={false}
              />
              <XAxis
                dataKey={xAxisKey}
                stroke="#E5E7EB"
                tick={{ fill: "#6B7280", fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: "#E5E7EB" }}
              />
              <YAxis
                stroke="#E5E7EB"
                tick={{ fill: "#6B7280", fontSize: 11 }}
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
                  activeDot={{ r: 4, stroke: "#FFFFFF", strokeWidth: 2 }}
                />
              ))}
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}
