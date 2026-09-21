"use client";

import React, { useState } from "react";
import { AlertCircle, Search, TrendingUp } from "lucide-react";
import StatusBadge from "./StatusBadge";
import { AnomalyRecord } from "../lib/types";

interface AnomalyTableProps {
  anomalies: AnomalyRecord[];
  isDemo?: boolean;
  title?: string;
  limit?: number;
}

export default function AnomalyTable({
  anomalies,
  isDemo = false,
  title = "Recent Telemetry Anomalies",
  limit,
}: AnomalyTableProps) {
  const [serviceFilter, setServiceFilter] = useState<string>("ALL");
  const [search, setSearch] = useState<string>("");

  const filtered = anomalies.filter((a) => {
    if (serviceFilter !== "ALL" && a.service !== serviceFilter) {
      return false;
    }
    if (
      search &&
      !a.metric.toLowerCase().includes(search.toLowerCase()) &&
      !a.service.toLowerCase().includes(search.toLowerCase()) &&
      !a.anomalyType.toLowerCase().includes(search.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  const displayList = limit ? filtered.slice(0, limit) : filtered;

  return (
    <div className="rounded-lg bg-surface border border-border p-5 flex flex-col justify-between">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-md bg-amber-950/60 text-amber-400 border border-amber-800/40">
            <TrendingUp className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-slate-200 tracking-tight">
                {title}
              </h3>
              {isDemo && (
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-950/50 text-amber-400 border border-amber-800/50">
                  Demo Fallback
                </span>
              )}
            </div>
            <p className="text-[11px] font-mono text-slate-400">
              AI baseline deviations detected via Z-score & IQR models
            </p>
          </div>
        </div>

        {/* Filter inputs */}
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search anomalies..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8 pr-3 py-1.5 bg-surface-subtle border border-border rounded text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 w-36 sm:w-44"
            />
          </div>

          <select
            value={serviceFilter}
            onChange={(e) => setServiceFilter(e.target.value)}
            className="bg-surface-subtle border border-border rounded px-2 py-1.5 text-xs font-mono text-slate-300 focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Services</option>
            <option value="User Service">User Service</option>
            <option value="Order Service">Order Service</option>
            <option value="Payment Service">Payment Service</option>
            <option value="Notification Service">Notification Service</option>
          </select>
        </div>
      </div>

      {/* Table with horizontal scroll */}
      <div className="overflow-x-auto border border-border/80 rounded-md bg-surface-subtle">
        <table className="w-full text-left text-xs border-collapse min-w-[700px]">
          <thead>
            <tr className="border-b border-border bg-slate-900/60 font-mono text-[11px] text-slate-400">
              <th className="py-2.5 px-3 font-semibold">Metric</th>
              <th className="py-2.5 px-3 font-semibold">Service</th>
              <th className="py-2.5 px-3 font-semibold">Anomaly Type</th>
              <th className="py-2.5 px-3 font-semibold">Current Value</th>
              <th className="py-2.5 px-3 font-semibold">Baseline</th>
              <th className="py-2.5 px-3 font-semibold">Deviation</th>
              <th className="py-2.5 px-3 font-semibold">Detected At</th>
              <th className="py-2.5 px-3 font-semibold">Severity</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/50">
            {displayList.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-8 text-center text-slate-500 font-mono">
                  No telemetry anomalies recorded.
                </td>
              </tr>
            ) : (
              displayList.map((a) => (
                <tr
                  key={a.id}
                  className="hover:bg-surface-hover/70 transition-colors"
                >
                  <td className="py-3 px-3 font-medium text-slate-200">
                    {a.metric}
                  </td>

                  <td className="py-3 px-3 font-mono text-slate-300">
                    {a.service}
                  </td>

                  <td className="py-3 px-3 font-mono text-[11px] text-slate-400">
                    <span className="px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700">
                      {a.anomalyType}
                    </span>
                  </td>

                  <td className="py-3 px-3 font-mono font-bold text-rose-400">
                    {a.currentValue}
                  </td>

                  <td className="py-3 px-3 font-mono text-slate-400">
                    {a.baseline}
                  </td>

                  <td className="py-3 px-3">
                    <span className="font-mono font-bold text-xs px-2 py-0.5 rounded bg-rose-950/60 text-rose-300 border border-rose-800/50">
                      {a.deviation}
                    </span>
                  </td>

                  <td className="py-3 px-3 font-mono text-[11px] text-slate-400">
                    {a.detectedAt}
                  </td>

                  <td className="py-3 px-3">
                    <StatusBadge status={a.severity} size="sm" />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
