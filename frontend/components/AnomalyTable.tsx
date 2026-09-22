"use client";

import React, { useState } from "react";
import { Search, TrendingUp } from "lucide-react";
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
    <div className="rounded-xl bg-white border border-slate-200 shadow-sm p-5 flex flex-col justify-between">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-md bg-amber-50 text-amber-600 border border-amber-100">
            <TrendingUp className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-slate-900 tracking-tight">
                {title}
              </h3>
              {isDemo && (
                <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">
                  Demo Fallback
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-500">
              AI baseline deviations detected via Z-score &amp; IQR models
            </p>
          </div>
        </div>

        {/* Filter inputs */}
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search anomalies..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-500 w-36 sm:w-44"
            />
          </div>

          <select
            value={serviceFilter}
            onChange={(e) => setServiceFilter(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-lg px-2 py-1.5 text-xs text-slate-900 focus:outline-none focus:border-indigo-500"
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
      <div className="overflow-x-auto border border-slate-200 rounded-lg bg-white">
        <table className="w-full text-left text-xs border-collapse min-w-[700px]">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50 text-[11px] font-medium text-slate-500">
              <th className="py-2.5 px-3 font-medium">Metric</th>
              <th className="py-2.5 px-3 font-medium">Service</th>
              <th className="py-2.5 px-3 font-medium">Anomaly Type</th>
              <th className="py-2.5 px-3 font-medium">Current Value</th>
              <th className="py-2.5 px-3 font-medium">Baseline</th>
              <th className="py-2.5 px-3 font-medium">Deviation</th>
              <th className="py-2.5 px-3 font-medium">Detected At</th>
              <th className="py-2.5 px-3 font-medium">Severity</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {displayList.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-8 text-center text-slate-400">
                  No telemetry anomalies recorded.
                </td>
              </tr>
            ) : (
              displayList.map((a) => (
                <tr
                  key={a.id}
                  className="hover:bg-slate-50 transition-colors"
                >
                  <td className="py-3 px-3 font-medium text-slate-900">
                    {a.metric}
                  </td>

                  <td className="py-3 px-3 text-slate-600">
                    {a.service}
                  </td>

                  <td className="py-3 px-3 text-[11px]">
                    <span className="px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-600">
                      {a.anomalyType}
                    </span>
                  </td>

                  <td className="py-3 px-3 font-semibold text-rose-600">
                    {a.currentValue}
                  </td>

                  <td className="py-3 px-3 text-slate-500">
                    {a.baseline}
                  </td>

                  <td className="py-3 px-3">
                    <span className="font-semibold text-xs px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200">
                      {a.deviation}
                    </span>
                  </td>

                  <td className="py-3 px-3 text-[11px] text-slate-500">
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
