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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-xl bg-white border border-slate-200 shadow-sm">
        <div className="flex items-center gap-2.5">
          <span className="relative flex h-2.5 w-2.5">
            {isLive && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75" />
            )}
            <span
              className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                isLive ? "bg-emerald-500" : "bg-amber-500"
              }`}
            />
          </span>
          <div className="text-xs">
            <span className="font-semibold text-slate-900">
              {isLive ? "Live incidents registry" : "Demo data (backend offline)"}
            </span>
            <span className="text-slate-500 ml-2">
              Endpoint: <code className="bg-slate-100 text-slate-600 rounded px-1 font-mono">{API_BASE_URL}/api/incidents</code>
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
        <h2 className="text-xl font-semibold text-slate-900 tracking-tight">
          Incident Response & Triage
        </h2>
        <p className="text-sm text-slate-500">
          Tracking active microservice anomalies, blast radius, and root-cause resolution
        </p>
      </div>

      {/* Summary KPI Cards: Active vs Resolved */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div
          onClick={() => setActiveTab("ACTIVE")}
          className={`rounded-xl bg-white border shadow-sm p-4 flex items-center justify-between cursor-pointer transition-all ${
            activeTab === "ACTIVE"
              ? "border-rose-300 ring-2 ring-rose-100"
              : "border-slate-200 hover:border-rose-200"
          }`}
        >
          <div>
            <span className="text-xs text-slate-500 block font-medium">
              Active incidents
            </span>
            <span className="text-3xl font-semibold text-rose-600 mt-1 block">
              {activeIncidents.length}
            </span>
            <span className="text-xs text-slate-500 mt-1 block">
              Requires immediate mitigation
            </span>
          </div>
          <div className="p-3 rounded-lg bg-rose-50 text-rose-600 border border-rose-100">
            <AlertOctagon className="h-6 w-6" />
          </div>
        </div>

        <div
          onClick={() => setActiveTab("RESOLVED")}
          className={`rounded-xl bg-white border shadow-sm p-4 flex items-center justify-between cursor-pointer transition-all ${
            activeTab === "RESOLVED"
              ? "border-emerald-300 ring-2 ring-emerald-100"
              : "border-slate-200 hover:border-emerald-200"
          }`}
        >
          <div>
            <span className="text-xs text-slate-500 block font-medium">
              Resolved incidents
            </span>
            <span className="text-3xl font-semibold text-emerald-600 mt-1 block">
              {resolvedIncidents.length}
            </span>
            <span className="text-xs text-slate-500 mt-1 block">
              Mitigated in trailing window
            </span>
          </div>
          <div className="p-3 rounded-lg bg-emerald-50 text-emerald-600 border border-emerald-100">
            <CheckCircle className="h-6 w-6" />
          </div>
        </div>
      </div>

      {/* Filter Tabs & Search Controls */}
      <div className="rounded-xl bg-white border border-slate-200 shadow-sm p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          {/* Tabs */}
          <div className="flex items-center bg-slate-100 p-1 rounded-lg border border-slate-200">
            <button
              onClick={() => setActiveTab("ALL")}
              className={`px-3 py-1.5 text-xs rounded-md transition-all ${
                activeTab === "ALL"
                  ? "bg-white shadow-sm text-slate-900 font-medium"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              All Incidents ({incidents.length})
            </button>
            <button
              onClick={() => setActiveTab("ACTIVE")}
              className={`px-3 py-1.5 text-xs rounded-md transition-all ${
                activeTab === "ACTIVE"
                  ? "bg-white shadow-sm text-slate-900 font-medium"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              Active ({activeIncidents.length})
            </button>
            <button
              onClick={() => setActiveTab("RESOLVED")}
              className={`px-3 py-1.5 text-xs rounded-md transition-all ${
                activeTab === "RESOLVED"
                  ? "bg-white shadow-sm text-slate-900 font-medium"
                  : "text-slate-500 hover:text-slate-900"
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
                className="pl-8 pr-3 py-1.5 bg-white border border-slate-300 rounded text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 w-44"
              />
            </div>

            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-white border border-slate-300 rounded px-2.5 py-1.5 text-xs text-slate-700 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
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
        <div className="overflow-x-auto border border-slate-200 rounded-lg bg-white">
          <table className="w-full text-left text-xs border-collapse min-w-[700px]">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-[11px] text-slate-500">
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
            <tbody className="divide-y divide-slate-100">
              {filtered.map((inc) => (
                <tr
                  key={inc.id}
                  onClick={() => setSelectedIncident(inc)}
                  className="hover:bg-slate-50 transition-colors cursor-pointer group"
                >
                  <td className="py-3 px-3 font-semibold text-indigo-600 font-mono">
                    {inc.id}
                  </td>

                  <td className="py-3 px-3">
                    <StatusBadge status={inc.severity} size="sm" />
                  </td>

                  <td className="py-3 px-3 text-slate-900 font-medium">
                    {inc.service}
                  </td>

                  <td className="py-3 px-3 text-slate-900 group-hover:text-indigo-700">
                    {inc.incident}
                  </td>

                  <td className="py-3 px-3 text-slate-500 text-[11px] font-mono">
                    {inc.detectedTime}
                  </td>

                  <td className="py-3 px-3 text-slate-600 text-[11px]">
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
                    <span className="inline-flex p-1 text-slate-400 group-hover:text-indigo-600">
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
          <div className="w-full max-w-xl rounded-xl bg-white border border-slate-200 shadow-xl p-6 space-y-4 text-xs animate-in fade-in-50 zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="flex items-start justify-between border-b border-slate-100 pb-3">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-indigo-600 font-semibold text-sm font-mono">
                    {selectedIncident.id}
                  </span>
                  <StatusBadge status={selectedIncident.severity} size="sm" />
                  <StatusBadge status={selectedIncident.status} size="sm" />
                </div>
                <h3 className="text-base font-semibold text-slate-900">
                  {selectedIncident.incident}
                </h3>
              </div>
              <button
                onClick={() => setSelectedIncident(null)}
                className="p-1 rounded text-slate-500 hover:text-slate-900 hover:bg-slate-100"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Structured Details Grid */}
            <div className="grid grid-cols-2 gap-3 p-3.5 rounded-lg bg-slate-50 border border-slate-200">
              <div>
                <span className="text-[11px] text-slate-500 block">
                  Service
                </span>
                <span className="text-slate-900 font-semibold">{selectedIncident.service}</span>
              </div>
              <div>
                <span className="text-[11px] text-slate-500 block">
                  Detected time
                </span>
                <span className="text-slate-600 font-mono">{selectedIncident.detectedTime}</span>
              </div>
              <div>
                <span className="text-[11px] text-slate-500 block">
                  Duration
                </span>
                <span className="text-slate-600">{selectedIncident.duration}</span>
              </div>
              <div>
                <span className="text-[11px] text-slate-500 block">
                  Audit status
                </span>
                <span className="text-indigo-600 font-medium">
                  {selectedIncident.auditStatus}
                </span>
              </div>
            </div>

            {/* Anomaly */}
            <div>
              <span className="text-slate-600 font-medium block mb-1 text-[11px]">
                Triggering anomaly:
              </span>
              <p className="text-rose-700 p-2.5 rounded bg-rose-50 border border-rose-200">
                {selectedIncident.anomaly}
              </p>
            </div>

            {/* Root Cause */}
            <div>
              <span className="text-slate-600 font-medium block mb-1 text-[11px]">
                Root cause:
              </span>
              <p className="text-amber-700 p-2.5 rounded bg-amber-50 border border-amber-200 leading-relaxed">
                {selectedIncident.rootCause}
              </p>
            </div>

            {/* Resolution */}
            <div>
              <span className="text-slate-600 font-medium block mb-1 text-[11px]">
                Resolution / playbook:
              </span>
              <p className="text-emerald-700 p-2.5 rounded bg-emerald-50 border border-emerald-200 leading-relaxed">
                {selectedIncident.resolution}
              </p>
            </div>

            <div className="pt-3 border-t border-slate-200 flex justify-end">
              <button
                onClick={() => setSelectedIncident(null)}
                className="px-4 py-1.5 rounded-lg bg-white border border-slate-300 hover:bg-slate-50 text-slate-700"
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
