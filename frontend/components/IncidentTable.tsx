"use client";

import React, { useState } from "react";
import { Search, ChevronRight, ShieldAlert } from "lucide-react";
import StatusBadge from "./StatusBadge";
import { IncidentRecord } from "../lib/types";

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
    <div className="rounded-xl bg-white border border-slate-200 shadow-sm p-5 flex flex-col justify-between">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-md bg-rose-50 text-rose-600 border border-rose-100">
            <ShieldAlert className="h-4 w-4" />
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
              {filtered.length} incident{filtered.length === 1 ? "" : "s"} tracked
            </p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Search box */}
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Filter incidents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-500 w-36 sm:w-48"
            />
          </div>

          {/* Severity selector */}
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-lg px-2 py-1.5 text-xs text-slate-900 focus:outline-none focus:border-indigo-500"
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
            className="bg-slate-50 border border-slate-200 rounded-lg px-2 py-1.5 text-xs text-slate-900 focus:outline-none focus:border-indigo-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="INVESTIGATING">Investigating</option>
            <option value="RESOLVED">Resolved</option>
          </select>
        </div>
      </div>

      {/* Table Container with Horizontal Scroll */}
      <div className="overflow-x-auto border border-slate-200 rounded-lg bg-white">
        <table className="w-full text-left text-xs border-collapse min-w-[650px]">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50 text-[11px] font-medium text-slate-500">
              <th className="py-2.5 px-3 font-medium">Incident</th>
              <th className="py-2.5 px-3 font-medium">Service</th>
              <th className="py-2.5 px-3 font-medium">Type</th>
              <th className="py-2.5 px-3 font-medium">Severity</th>
              <th className="py-2.5 px-3 font-medium">Detected</th>
              <th className="py-2.5 px-3 font-medium">Status</th>
              {onSelectIncident && <th className="py-2.5 px-3 text-right font-medium">Action</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {displayList.length === 0 ? (
              <tr>
                <td
                  colSpan={onSelectIncident ? 7 : 6}
                  className="py-8 text-center text-slate-400"
                >
                  No incidents matching your filters.
                </td>
              </tr>
            ) : (
              displayList.map((inc) => (
                <tr
                  key={inc.id}
                  onClick={() => onSelectIncident?.(inc)}
                  className="hover:bg-slate-50 transition-colors cursor-pointer group"
                >
                  <td className="py-3 px-3">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[11px] text-indigo-600 font-medium">
                        {inc.id}
                      </span>
                      <span className="font-medium text-slate-900">
                        {inc.incident}
                      </span>
                    </div>
                  </td>

                  <td className="py-3 px-3 text-slate-600">
                    {inc.service}
                  </td>

                  <td className="py-3 px-3">
                    <span className="px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-600 text-[11px]">
                      {inc.type}
                    </span>
                  </td>

                  <td className="py-3 px-3">
                    <StatusBadge status={inc.severity} size="sm" />
                  </td>

                  <td className="py-3 px-3 text-[11px] text-slate-500">
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
                      <span className="inline-flex p-1 text-slate-400 group-hover:text-indigo-600">
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
