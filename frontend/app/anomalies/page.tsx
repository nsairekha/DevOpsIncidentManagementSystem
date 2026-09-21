"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  AlertTriangle,
  Clock,
  Play,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import StatusBadge from "../../components/StatusBadge";
import RefreshIndicator from "../../components/RefreshIndicator";
import { LoadingState } from "../../components/LoadingState";
import {
  API_BASE_URL,
  fetchAnomaliesData,
  runLiveAnomalyAnalysis,
} from "../../lib/api";
import { DEMO_ANOMALIES, DemoAnomaly } from "../../lib/demoData";
import { AnomalyAnalysisResult } from "../../lib/types";

export default function AnomaliesPage() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isLive, setIsLive] = useState(false);
  const [allowFallback, setAllowFallback] = useState(true);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const [anomalies, setAnomalies] = useState<DemoAnomaly[]>([]);
  const [selectedAnomaly, setSelectedAnomaly] = useState<DemoAnomaly | null>(null);
  const [search, setSearch] = useState("");
  const [serviceFilter, setServiceFilter] = useState("ALL");

  // Anomaly detector playground
  const [detector, setDetector] = useState<"zscore" | "iqr" | "isolation_forest">("zscore");
  const [threshold, setThreshold] = useState("3.0");
  const [signalName, setSignalName] = useState("payment_latency_ms");
  const [referenceWindow, setReferenceWindow] = useState("120, 125, 118, 122, 130, 115, 128, 124, 121, 119");
  const [telemetryWindow, setTelemetryWindow] = useState("124, 122, 850, 126, 920");
  const [runningAnalysis, setRunningAnalysis] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnomalyAnalysisResult | null>(null);

  const loadAnomalies = useCallback(async () => {
    try {
      setRefreshing(true);
      const res = await fetchAnomaliesData();
      if (res.isLive) {
        setIsLive(true);
        setAnomalies(res.data);
        setStatusMessage(res.message);
      } else {
        setIsLive(false);
        setStatusMessage(res.message);
        setAnomalies(allowFallback ? DEMO_ANOMALIES : []);
      }
      setLastUpdated(new Date());
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [allowFallback]);

  useEffect(() => {
    loadAnomalies();
  }, [loadAnomalies]);

  const handleRunAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    setRunningAnalysis(true);
    try {
      const refSamples = referenceWindow
        .split(",")
        .map((s) => parseFloat(s.trim()))
        .filter((n) => !isNaN(n));
      const telSamples = telemetryWindow
        .split(",")
        .map((s) => parseFloat(s.trim()))
        .filter((n) => !isNaN(n));

      const payload = {
        detector,
        threshold: parseFloat(threshold) || 3.0,
        reference: { [signalName]: refSamples.length ? refSamples : [100.0] },
        telemetry: { [signalName]: telSamples.length ? telSamples : [850.0] },
      };

      const result = await runLiveAnomalyAnalysis(payload);
      if (result) {
        setAnalysisResult(result);
      } else {
        // Fallback simulation if backend offline
        setAnalysisResult({
          detector,
          nFindings: 1,
          severity: "high",
          summary: `[Demo Offline Simulator] 1 anomaly detected on signal '${signalName}'. Observed 920 breached normal bounds.`,
          findings: [
            {
              signal: signalName,
              value: 920,
              score: 4.82,
              severity: "high",
              details: `Flagged by ${detector} detector (+372% deviation).`,
              expectedRange: [115, 130],
              timestamp: new Date().toISOString(),
            },
          ],
          audited: true,
          blockHash: "demo_hash_9a8f4c2e",
          eventId: "evt_demo_8921",
          chainValid: true,
        });
      }
    } finally {
      setRunningAnalysis(false);
    }
  };

  const filtered = anomalies.filter((a) => {
    if (serviceFilter !== "ALL" && a.service !== serviceFilter) return false;
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

  if (loading && anomalies.length === 0) {
    return <LoadingState type="table" message="Checking for telemetry anomalies..." />;
  }

  return (
    <div className="space-y-6">
      {/* Live / Demo Header Banner */}
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
              {isLive ? "LIVE ANOMALIES STREAM" : "DEMO DATA (Backend Offline)"}
            </span>
            <span className="text-slate-400 ml-2">
              Source: <code>{API_BASE_URL}/api/v1/baselines</code>
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <RefreshIndicator
            lastUpdated={lastUpdated}
            onRefresh={loadAnomalies}
            intervalSeconds={10}
            isRefreshing={refreshing}
          />
          {!isLive && (
            <button
              onClick={() => setAllowFallback(!allowFallback)}
              className="text-[11px] font-mono px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
            >
              {allowFallback ? "Hide Demo Data" : "Show Demo Data"}
            </button>
          )}
        </div>
      </div>

      {statusMessage && (
        <div className="p-3 rounded-lg bg-surface-subtle border border-border text-xs font-mono text-slate-300">
          {statusMessage}
        </div>
      )}

      {/* Title */}
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">
          Telemetry Anomalies & Outlier Detection
        </h2>
        <p className="text-xs font-mono text-slate-400">
          Unsupervised dynamic thresholding via Z-Score, IQR, and Isolation Forest
        </p>
      </div>

      {/* Main Anomalies Table: Required Columns:
          Time, Service, Metric, Anomaly Type, Current Value, Baseline, Deviation, Severity, Status */}
      <div className="rounded-lg bg-surface border border-border p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-400" />
            <h3 className="text-sm font-semibold text-white">
              Flagged Telemetry Deviations ({filtered.length})
            </h3>
          </div>

          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-500" />
              <input
                type="text"
                placeholder="Search anomalies..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-8 pr-3 py-1.5 bg-surface-subtle border border-border rounded text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 w-36 sm:w-48"
              />
            </div>

            <select
              value={serviceFilter}
              onChange={(e) => setServiceFilter(e.target.value)}
              className="bg-surface-subtle border border-border rounded px-2.5 py-1.5 text-xs font-mono text-slate-300 focus:outline-none focus:border-cyan-500"
            >
              <option value="ALL">All Services</option>
              <option value="Payment Service">Payment Service</option>
              <option value="Order Service">Order Service</option>
              <option value="User Service">User Service</option>
              <option value="Notification Service">Notification Service</option>
            </select>
          </div>
        </div>

        {/* Responsive Table */}
        <div className="overflow-x-auto border border-border/80 rounded-md bg-surface-subtle">
          <table className="w-full text-left text-xs border-collapse min-w-[760px]">
            <thead>
              <tr className="border-b border-border bg-slate-900/60 font-mono text-[11px] text-slate-400">
                <th className="py-2.5 px-3 font-semibold">Time</th>
                <th className="py-2.5 px-3 font-semibold">Service</th>
                <th className="py-2.5 px-3 font-semibold">Metric</th>
                <th className="py-2.5 px-3 font-semibold">Anomaly Type</th>
                <th className="py-2.5 px-3 font-semibold">Current Value</th>
                <th className="py-2.5 px-3 font-semibold">Baseline</th>
                <th className="py-2.5 px-3 font-semibold">Deviation</th>
                <th className="py-2.5 px-3 font-semibold">Severity</th>
                <th className="py-2.5 px-3 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/50 font-mono">
              {filtered.map((a) => (
                <tr
                  key={a.id}
                  onClick={() => setSelectedAnomaly(a)}
                  className="hover:bg-surface-hover/70 transition-colors cursor-pointer group"
                >
                  <td className="py-3 px-3 text-[11px] text-slate-400">
                    {a.time}
                  </td>

                  <td className="py-3 px-3 font-semibold text-slate-200">
                    {a.service}
                  </td>

                  <td className="py-3 px-3 text-cyan-400 font-medium">
                    {a.metric}
                  </td>

                  <td className="py-3 px-3 text-[11px] text-slate-400">
                    <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
                      {a.anomalyType}
                    </span>
                  </td>

                  <td className="py-3 px-3 font-bold text-rose-400">
                    {a.currentValue}
                  </td>

                  <td className="py-3 px-3 text-slate-400">
                    {a.baseline}
                  </td>

                  <td className="py-3 px-3">
                    <span className="font-bold px-2 py-0.5 rounded bg-rose-950/60 text-rose-300 border border-rose-800/50">
                      {a.deviation}
                    </span>
                  </td>

                  <td className="py-3 px-3">
                    <StatusBadge status={a.severity} size="sm" />
                  </td>

                  <td className="py-3 px-3">
                    <StatusBadge
                      status={a.status}
                      size="sm"
                      pulse={a.status === "Active"}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Details View Modal when clicking an anomaly */}
      {selectedAnomaly && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-xl bg-surface border border-border shadow-2xl p-6 space-y-4 font-mono text-xs animate-in fade-in-50 zoom-in-95 duration-150">
            <div className="flex items-start justify-between border-b border-border/80 pb-3">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-cyan-400 font-bold">
                    {selectedAnomaly.id}
                  </span>
                  <StatusBadge status={selectedAnomaly.severity} size="sm" />
                  <StatusBadge status={selectedAnomaly.status} size="sm" />
                </div>
                <h3 className="text-sm font-bold text-white font-sans">
                  {selectedAnomaly.anomalyType} on {selectedAnomaly.service}
                </h3>
              </div>
              <button
                onClick={() => setSelectedAnomaly(null)}
                className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 p-3 rounded-lg bg-surface-subtle border border-border/60">
              <div>
                <span className="text-[10px] text-slate-400 uppercase block">
                  Observed Signal
                </span>
                <span className="text-white font-bold">{selectedAnomaly.metric}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 uppercase block">
                  Anomaly Score
                </span>
                <span className="text-cyan-400 font-bold">
                  {selectedAnomaly.score.toFixed(2)}σ
                </span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 uppercase block">
                  Current vs Baseline
                </span>
                <span className="text-rose-400 font-bold">
                  {selectedAnomaly.currentValue} (Base: {selectedAnomaly.baseline})
                </span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 uppercase block">
                  Deviation
                </span>
                <span className="text-rose-400 font-bold">
                  {selectedAnomaly.deviation}
                </span>
              </div>
            </div>

            <div>
              <span className="text-slate-400 font-semibold block mb-1">
                Diagnostic Details:
              </span>
              <p className="text-slate-300 font-sans leading-relaxed">
                {selectedAnomaly.details}
              </p>
            </div>

            <div className="pt-3 border-t border-border flex justify-end">
              <button
                onClick={() => setSelectedAnomaly(null)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Live AI Anomaly Detection Pipeline Tester */}
      <div className="rounded-lg bg-surface border border-border p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-border/80 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-indigo-950/70 text-indigo-400 border border-indigo-800/50">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">
                Live Anomaly Pipeline Tester (/api/analyze)
              </h3>
              <p className="text-[11px] font-mono text-slate-400">
                Fit training baseline and test live signals with Z-score, IQR, or Isolation Forest
              </p>
            </div>
          </div>
        </div>

        <form onSubmit={handleRunAnalysis} className="space-y-4 text-xs font-mono">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="block text-slate-300 mb-1 font-semibold">
                Detector Model
              </label>
              <select
                value={detector}
                onChange={(e) =>
                  setDetector(
                    e.target.value as "zscore" | "iqr" | "isolation_forest"
                  )
                }
                className="w-full bg-surface-subtle border border-border rounded px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500"
              >
                <option value="zscore">Z-Score (Standard Deviations)</option>
                <option value="iqr">IQR (Interquartile Range)</option>
                <option value="isolation_forest">Isolation Forest (Tree Ensemble)</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-300 mb-1 font-semibold">
                Metric Signal Name
              </label>
              <input
                type="text"
                value={signalName}
                onChange={(e) => setSignalName(e.target.value)}
                className="w-full bg-surface-subtle border border-border rounded px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div>
              <label className="block text-slate-300 mb-1 font-semibold">
                Sensitivity Threshold (σ)
              </label>
              <input
                type="number"
                step="0.5"
                min="1.0"
                max="5.0"
                value={threshold}
                onChange={(e) => setThreshold(e.target.value)}
                className="w-full bg-surface-subtle border border-border rounded px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-300 mb-1 font-semibold">
                Reference Training Window
              </label>
              <textarea
                rows={2}
                value={referenceWindow}
                onChange={(e) => setReferenceWindow(e.target.value)}
                className="w-full bg-surface-subtle border border-border rounded p-2 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-slate-300 mb-1 font-semibold">
                Telemetry Window to Inspect
              </label>
              <textarea
                rows={2}
                value={telemetryWindow}
                onChange={(e) => setTelemetryWindow(e.target.value)}
                className="w-full bg-surface-subtle border border-border rounded p-2 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={runningAnalysis}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold transition-colors disabled:opacity-50"
            >
              <Play className="h-4 w-4 fill-current" />
              <span>
                {runningAnalysis ? "Analyzing Telemetry..." : "Run AI Analysis"}
              </span>
            </button>
          </div>
        </form>

        {/* Live Output */}
        {analysisResult && (
          <div className="rounded-lg bg-surface-subtle border border-border p-4 space-y-3 font-mono text-xs">
            <div className="flex items-center justify-between border-b border-border/60 pb-2">
              <span className="font-bold text-white">
                Detector: {analysisResult.detector} ({analysisResult.nFindings} finding(s))
              </span>
              <StatusBadge status={analysisResult.severity} size="sm" />
            </div>
            <p className="text-slate-300">{analysisResult.summary}</p>
            {analysisResult.findings.map((f, i) => (
              <div
                key={i}
                className="p-2.5 rounded bg-surface border border-border/80 flex items-center justify-between"
              >
                <div>
                  <span className="font-bold text-rose-400">{f.signal}</span>:{" "}
                  <span className="text-white font-bold">{f.value}</span> (Score:{" "}
                  <span className="text-cyan-400">{f.score.toFixed(2)}</span>)
                  <span className="text-slate-400 ml-2">{f.details}</span>
                </div>
                <StatusBadge status={f.severity} size="sm" />
              </div>
            ))}
            {analysisResult.audited && (
              <div className="pt-2 border-t border-border/60 flex items-center justify-between text-[11px] text-slate-400">
                <span className="text-emerald-400 flex items-center gap-1">
                  <ShieldCheck className="h-3.5 w-3.5" /> Chained to Ledger:{" "}
                  <code>{analysisResult.blockHash.slice(0, 16)}...</code>
                </span>
                <span>Event ID: <code>{analysisResult.eventId}</code></span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
