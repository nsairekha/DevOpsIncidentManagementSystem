"use client";

import React, { useState } from "react";
import { Filter, Search, ChevronRight, ShieldAlert } from "lucide-react";
import StatusBadge from "./StatusBadge";
import { IncidentRecord, IncidentSeverity, IncidentStatus } from "../lib/types";

interface IncidentTableProps {
  incidents: IncidentRecord[];
  isDemo?: boolean;
  onSelectIncident?: (incident: IncidentRecord) => void;
  title?: string;
  limit?: number;
}

export default function IncidentTable({
  incidents,
  isDemo = false,
  onSelectIncident,
  title = "Recent Incidents",
  limit,
}: IncidentTableProps) {
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchTerm, setSearchTerm] = useState<string>("");

  const filtered = incidents.filter((inc) => {
    if (severityFilter !== "ALL" && inc.severity.toUpperCase() !== severityFilter) {
      return false;
    }
    if (statusFilter !== "ALL" && inc.status.toUpperCase() !== statusFilter) {
      return false;
    }
    if (
      searchTerm &&
      !inc.incident.toLowerCase().includes(searchTerm.toLowerCase()) &&
      !inc.service.toLowerCase().includes(searchTerm.toLowerCase()) &&
      !inc.id.toLowerCase().includes(searchTerm.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  const displayList = limit ? filtered.slice(0, limit) : filtered;

  return (
    <div className="rounded-lg bg-surface border border-border p-5 flex flex-col justify-between">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-md bg-rose-950/60 text-rose-400 border border-rose-800/40">
            <ShieldAlert className="h-4 w-4" />
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
              {filtered.length} incident{filtered.length === 1 ? "" : "s"} tracked
            </p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Search box */}
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-500" />
            <input
              type="text"
              placeholder="Filter incidents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8 pr-3 py-1.5 bg-surface-subtle border border-border rounded text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 w-36 sm:w-48"
            />
          </div>

          {/* Severity selector */}
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="bg-surface-subtle border border-border rounded px-2 py-1.5 text-xs font-mono text-slate-300 focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>

          {/* Status selector */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-surface-subtle border border-border rounded px-2 py-1.5 text-xs font-mono text-slate-300 focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="INVESTIGATING">Investigating</option>
            <option value="RESOLVED">Resolved</option>
          </select>
        </div>
      </div>

      {/* Table Container with Horizontal Scroll */}
      <div className="overflow-x-auto border border-border/80 rounded-md bg-surface-subtle">
        <table className="w-full text-left text-xs border-collapse min-w-[650px]">
          <thead>
            <tr className="border-b border-border bg-slate-900/60 font-mono text-[11px] text-slate-400">
              <th className="py-2.5 px-3 font-semibold">Incident</th>
              <th className="py-2.5 px-3 font-semibold">Service</th>
              <th className="py-2.5 px-3 font-semibold">Type</th>
              <th className="py-2.5 px-3 font-semibold">Severity</th>
              <th className="py-2.5 px-3 font-semibold">Detected</th>
              <th className="py-2.5 px-3 font-semibold">Status</th>
              {onSelectIncident && <th className="py-2.5 px-3 text-right">Action</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-border/50">
            {displayList.length === 0 ? (
              <tr>
                <td
                  colSpan={onSelectIncident ? 7 : 6}
                  className="py-8 text-center text-slate-500 font-mono"
                >
                  No incidents matching your filters.
                </td>
              </tr>
            ) : (
              displayList.map((inc) => (
                <tr
                  key={inc.id}
                  onClick={() => onSelectIncident?.(inc)}
                  className="hover:bg-surface-hover/70 transition-colors cursor-pointer group"
                >
                  <td className="py-3 px-3">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[11px] text-cyan-400/90 font-medium">
                        {inc.id}
                      </span>
                      <span className="font-medium text-slate-200 group-hover:text-white">
                        {inc.incident}
                      </span>
                    </div>
                  </td>

                  <td className="py-3 px-3 font-mono text-slate-300">
                    {inc.service}
                  </td>

                  <td className="py-3 px-3 font-mono text-slate-400">
                    <span className="px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700 text-[11px]">
                      {inc.type}
                    </span>
                  </td>

                  <td className="py-3 px-3">
                    <StatusBadge status={inc.severity} size="sm" />
                  </td>

                  <td className="py-3 px-3 font-mono text-[11px] text-slate-400">
                    {inc.detected}
                  </td>

                  <td className="py-3 px-3">
                    <StatusBadge
                      status={inc.status}
                      size="sm"
                      pulse={inc.status === "Active"}
                    />
                  </td>

                  {onSelectIncident && (
                    <td className="py-3 px-3 text-right">
                      <span className="inline-flex p-1 text-slate-400 group-hover:text-cyan-400">
                        <ChevronRight className="h-4 w-4" />
                      </span>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
