"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  AlertOctagon,
  CheckCircle,
  Clock,
  RefreshCw,
  Search,
  ShieldAlert,
  X,
  Layers,
  ChevronRight,
} from "lucide-react";
import StatusBadge from "../../components/StatusBadge";
import RefreshIndicator from "../../components/RefreshIndicator";
import { LoadingState } from "../../components/LoadingState";
import { API_BASE_URL, fetchIncidentsData } from "../../lib/api";
import { DEMO_INCIDENTS, DemoIncident } from "../../lib/demoData";

export default function IncidentsPage() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isLive, setIsLive] = useState(false);
  const [allowFallback, setAllowFallback] = useState(true);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const [incidents, setIncidents] = useState<DemoIncident[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<DemoIncident | null>(null);
  const [activeTab, setActiveTab] = useState<"ALL" | "ACTIVE" | "RESOLVED">("ALL");
  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState("ALL");

  const loadIncidents = useCallback(async () => {
    try {
      setRefreshing(true);
      const res = await fetchIncidentsData();
      if (res.isLive) {
        setIsLive(true);
        setIncidents(res.data);
        setStatusMessage(res.message);
      } else {
        setIsLive(false);
        setStatusMessage(res.message);
        setIncidents(allowFallback ? DEMO_INCIDENTS : []);
      }
      setLastUpdated(new Date());
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [allowFallback]);

  useEffect(() => {
    loadIncidents();
  }, [loadIncidents]);

  const activeIncidents = incidents.filter((i) => i.status === "Active");
  const resolvedIncidents = incidents.filter((i) => i.status === "Resolved");

  const filtered = incidents.filter((inc) => {
    if (activeTab === "ACTIVE" && inc.status !== "Active") return false;
    if (activeTab === "RESOLVED" && inc.status !== "Resolved") return false;
    if (severityFilter !== "ALL" && inc.severity.toUpperCase() !== severityFilter) {
      return false;
    }
    if (
      search &&
      !inc.incident.toLowerCase().includes(search.toLowerCase()) &&
      !inc.service.toLowerCase().includes(search.toLowerCase()) &&
      !inc.id.toLowerCase().includes(search.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  if (loading && incidents.length === 0) {
    return <LoadingState type="table" message="Querying incident repository..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-lg bg-surface border border-border">
        <div className="flex items-center gap-2.5">
          <span className="relative flex h-2.5 w-2.5">
            {isLive && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            )}
            <span
              className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                isLive ? "bg-emerald-400" : "bg-amber-400"
              }`}
            />
          </span>
          <div className="text-xs font-mono">
            <span className="font-bold text-white uppercase tracking-wide">
              {isLive ? "LIVE INCIDENTS REGISTRY" : "DEMO DATA (Backend Offline)"}
            </span>
            <span className="text-slate-400 ml-2">
              Endpoint: <code>{API_BASE_URL}/api/incidents</code>
            </span>
          </div>
        </div>

        <RefreshIndicator
          lastUpdated={lastUpdated}
          onRefresh={loadIncidents}
          intervalSeconds={10}
          isRefreshing={refreshing}
        />
      </div>

      {/* Title */}
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">
          Incident Response & Triage
        </h2>
        <p className="text-xs font-mono text-slate-400">
          Tracking active microservice anomalies, blast radius, and root-cause resolution
        </p>
      </div>

      {/* Summary KPI Cards: Active vs Resolved */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 font-mono">
        <div
          onClick={() => setActiveTab("ACTIVE")}
          className={`rounded-lg bg-surface border p-4 flex items-center justify-between cursor-pointer transition-all ${
            activeTab === "ACTIVE"
              ? "border-rose-500 ring-1 ring-rose-500"
              : "border-rose-900/70 hover:border-rose-700"
          } shadow-[0_0_15px_-3px_rgba(239,68,68,0.15)]`}
        >
          <div>
            <span className="text-[10px] uppercase text-slate-400 block font-semibold">
              ACTIVE INCIDENTS
            </span>
            <span className="text-3xl font-bold text-rose-400 mt-1 block">
              {activeIncidents.length}
            </span>
            <span className="text-[11px] text-slate-400 mt-1 block">
              Requires immediate mitigation
            </span>
          </div>
          <div className="p-3 rounded-lg bg-rose-950 text-rose-400 border border-rose-800">
            <AlertOctagon className="h-6 w-6" />
          </div>
        </div>

        <div
          onClick={() => setActiveTab("RESOLVED")}
          className={`rounded-lg bg-surface border p-4 flex items-center justify-between cursor-pointer transition-all ${
            activeTab === "RESOLVED"
              ? "border-emerald-500 ring-1 ring-emerald-500"
              : "border-emerald-900/70 hover:border-emerald-700"
          }`}
        >
          <div>
            <span className="text-[10px] uppercase text-slate-400 block font-semibold">
              RESOLVED INCIDENTS
            </span>
            <span className="text-3xl font-bold text-emerald-400 mt-1 block">
              {resolvedIncidents.length}
            </span>
            <span className="text-[11px] text-slate-400 mt-1 block">
              Mitigated in trailing window
            </span>
          </div>
          <div className="p-3 rounded-lg bg-emerald-950 text-emerald-400 border border-emerald-800">
            <CheckCircle className="h-6 w-6" />
          </div>
        </div>
      </div>

      {/* Filter Tabs & Search Controls */}
      <div className="rounded-lg bg-surface border border-border p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          {/* Tabs */}
          <div className="flex items-center bg-surface-subtle p-1 rounded-lg border border-border">
            <button
              onClick={() => setActiveTab("ALL")}
              className={`px-3 py-1.5 text-xs font-mono rounded-md transition-all ${
                activeTab === "ALL"
                  ? "bg-slate-800 text-white font-semibold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              All Incidents ({incidents.length})
            </button>
            <button
              onClick={() => setActiveTab("ACTIVE")}
              className={`px-3 py-1.5 text-xs font-mono rounded-md transition-all ${
                activeTab === "ACTIVE"
                  ? "bg-rose-950 text-rose-300 font-semibold border border-rose-800/60"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Active ({activeIncidents.length})
            </button>
            <button
              onClick={() => setActiveTab("RESOLVED")}
              className={`px-3 py-1.5 text-xs font-mono rounded-md transition-all ${
                activeTab === "RESOLVED"
                  ? "bg-emerald-950 text-emerald-300 font-semibold border border-emerald-800/60"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Resolved ({resolvedIncidents.length})
            </button>
          </div>

          {/* Search & Severity Filter */}
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-500" />
              <input
                type="text"
                placeholder="Filter by ID or service..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-8 pr-3 py-1.5 bg-surface-subtle border border-border rounded text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 w-44"
              />
            </div>

            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-surface-subtle border border-border rounded px-2.5 py-1.5 text-xs font-mono text-slate-300 focus:outline-none focus:border-cyan-500"
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>
        </div>

        {/* Table of Incidents */}
        <div className="overflow-x-auto border border-border/80 rounded-md bg-surface-subtle">
          <table className="w-full text-left text-xs border-collapse min-w-[700px]">
            <thead>
              <tr className="border-b border-border bg-slate-900/60 font-mono text-[11px] text-slate-400">
                <th className="py-2.5 px-3 font-semibold">Incident ID</th>
                <th className="py-2.5 px-3 font-semibold">Severity</th>
                <th className="py-2.5 px-3 font-semibold">Service</th>
                <th className="py-2.5 px-3 font-semibold">Incident Title</th>
                <th className="py-2.5 px-3 font-semibold">Detected Time</th>
                <th className="py-2.5 px-3 font-semibold">Duration</th>
                <th className="py-2.5 px-3 font-semibold">Status</th>
                <th className="py-2.5 px-3 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/50 font-mono">
              {filtered.map((inc) => (
                <tr
                  key={inc.id}
                  onClick={() => setSelectedIncident(inc)}
                  className="hover:bg-surface-hover/70 transition-colors cursor-pointer group"
                >
                  <td className="py-3 px-3 font-bold text-cyan-400">
                    {inc.id}
                  </td>

                  <td className="py-3 px-3">
                    <StatusBadge status={inc.severity} size="sm" />
                  </td>

                  <td className="py-3 px-3 text-slate-200 font-medium">
                    {inc.service}
                  </td>

                  <td className="py-3 px-3 font-sans text-white group-hover:text-cyan-300">
                    {inc.incident}
                  </td>

                  <td className="py-3 px-3 text-slate-400 text-[11px]">
                    {inc.detectedTime}
                  </td>

                  <td className="py-3 px-3 text-slate-300 text-[11px]">
                    {inc.duration}
                  </td>

                  <td className="py-3 px-3">
                    <StatusBadge
                      status={inc.status}
                      size="sm"
                      pulse={inc.status === "Active"}
                    />
                  </td>

                  <td className="py-3 px-3 text-right">
                    <span className="inline-flex p-1 text-slate-400 group-hover:text-cyan-400">
                      <ChevronRight className="h-4 w-4" />
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Incident Details Modal:
          Fields required by prompt:
          - ID
          - severity
          - service
          - detected time
          - duration
          - anomaly
          - root cause
          - resolution
          - audit status */}
      {selectedIncident && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-xl rounded-xl bg-surface border border-border shadow-2xl p-6 space-y-4 font-mono text-xs animate-in fade-in-50 zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="flex items-start justify-between border-b border-border/80 pb-3">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-cyan-400 font-bold text-sm">
                    {selectedIncident.id}
                  </span>
                  <StatusBadge status={selectedIncident.severity} size="sm" />
                  <StatusBadge status={selectedIncident.status} size="sm" />
                </div>
                <h3 className="text-base font-bold text-white font-sans">
                  {selectedIncident.incident}
                </h3>
              </div>
              <button
                onClick={() => setSelectedIncident(null)}
                className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Structured Details Grid */}
            <div className="grid grid-cols-2 gap-3 p-3.5 rounded-lg bg-surface-subtle border border-border/60">
              <div>
                <span className="text-[10px] text-slate-400 uppercase block">
                  Service
                </span>
                <span className="text-white font-bold">{selectedIncident.service}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 uppercase block">
                  Detected Time
                </span>
                <span className="text-slate-300">{selectedIncident.detectedTime}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 uppercase block">
                  Duration
                </span>
                <span className="text-slate-300">{selectedIncident.duration}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 uppercase block">
                  Audit Status
                </span>
                <span className="text-cyan-400 font-semibold">
                  {selectedIncident.auditStatus}
                </span>
              </div>
            </div>

            {/* Anomaly */}
            <div>
              <span className="text-slate-400 font-semibold block mb-1 uppercase text-[10px]">
                Triggering Anomaly:
              </span>
              <p className="text-rose-300 font-sans p-2.5 rounded bg-rose-950/20 border border-rose-800/40">
                {selectedIncident.anomaly}
              </p>
            </div>

            {/* Root Cause */}
            <div>
              <span className="text-slate-400 font-semibold block mb-1 uppercase text-[10px]">
                Root Cause:
              </span>
              <p className="text-amber-300/90 font-sans p-2.5 rounded bg-amber-950/20 border border-amber-800/40 leading-relaxed">
                {selectedIncident.rootCause}
              </p>
            </div>

            {/* Resolution */}
            <div>
              <span className="text-slate-400 font-semibold block mb-1 uppercase text-[10px]">
                Resolution / Playbook:
              </span>
              <p className="text-emerald-300 font-sans p-2.5 rounded bg-emerald-950/20 border border-emerald-800/40 leading-relaxed">
                {selectedIncident.resolution}
              </p>
            </div>

            <div className="pt-3 border-t border-border flex justify-end">
              <button
                onClick={() => setSelectedIncident(null)}
                className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
              >
                Close Details
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
