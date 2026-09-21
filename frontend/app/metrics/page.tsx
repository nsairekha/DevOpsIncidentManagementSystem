"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowDownRight,
  ArrowUpRight,
  Info,
} from "lucide-react";
import MetricChart from "../../components/MetricChart";
import RefreshIndicator from "../../components/RefreshIndicator";
import { LoadingState } from "../../components/LoadingState";
import {
  API_BASE_URL,
  fetchMetricsExplorerData,
  RawBaselineRecord,
} from "../../lib/api";
import { DEMO_BASELINES, DemoBaseline, DEMO_TIMESERIES_DATA } from "../../lib/demo-data";
import { findBaselineForMetric, inferUnit } from "../../lib/metricUtils";
import { MetricTimeSeriesPoint } from "../../lib/types";

// Union type covers both live (RawBaselineRecord) and demo (DemoBaseline) baseline shapes.
type AnyBaseline = RawBaselineRecord | DemoBaseline;

const TIME_RANGE_MINUTES: Record<string, number> = {
  "15m": 15,
  "1h": 60,
  "6h": 360,
  "24h": 1440,
};

export default function MetricsPage() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isLive, setIsLive] = useState(false);
  const [allowFallback, setAllowFallback] = useState(true);
  const [backendMessage, setBackendMessage] = useState<string | null>(null);

  const [selectedService, setSelectedService] = useState("all");
  const [selectedMetric, setSelectedMetric] = useState("Latency");
  const [timeRange, setTimeRange] = useState("15m");

  const [liveBaselines, setLiveBaselines] = useState<RawBaselineRecord[]>([]);
  const [chartData, setChartData] = useState<MetricTimeSeriesPoint[]>([]);

  const metricOptions = [
    "CPU",
    "Memory",
    "Request rate",
    "Throughput",
    "Latency",
    "P50",
    "P95",
    "P99",
    "4xx",
    "5xx",
    "Error rate",
    "Availability",
    "Dependency latency",
    "Dependency errors",
  ];

  const loadMetrics = useCallback(async () => {
    try {
      setRefreshing(true);
      const lookback = TIME_RANGE_MINUTES[timeRange] ?? 15;
      const res = await fetchMetricsExplorerData({ lookbackMinutes: lookback });

      if (res.isLive) {
        setIsLive(true);
        setLiveBaselines(res.baselines);
        setChartData(res.chartData);
        setBackendMessage(res.message || null);
      } else {
        setIsLive(false);
        setLiveBaselines([]);
        setChartData([]);
        setBackendMessage(res.message || "Backend unreachable");
      }

      setLastUpdated(new Date());
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [timeRange]);

  useEffect(() => {
    loadMetrics();
  }, [loadMetrics]);

  const currentBaseline = useMemo((): AnyBaseline | null => {
    if (isLive) {
      const found = findBaselineForMetric(liveBaselines, selectedMetric, selectedService);
      if (found) return found as AnyBaseline;
      if (liveBaselines.length > 0) return liveBaselines[0] as AnyBaseline;
      return null;
    }
    if (allowFallback) {
      return (
        DEMO_BASELINES.find((b) =>
          b.metric_name.toLowerCase().includes(selectedMetric.toLowerCase())
        ) || DEMO_BASELINES[0]
      ) as AnyBaseline;
    }
    return null;
  }, [isLive, liveBaselines, selectedMetric, selectedService, allowFallback]);

  const displayChartData =
    isLive && chartData.length > 0
      ? chartData
      : allowFallback
      ? DEMO_TIMESERIES_DATA
      : [];

  const unit = isLive
    ? inferUnit(currentBaseline as RawBaselineRecord | undefined)
    : (currentBaseline as DemoBaseline)?.unit || "";

  if (loading && !currentBaseline) {
    return <LoadingState type="full" message="Loading metrics from /api/v1/baselines..." />;
  }

  return (
    <div className="space-y-6">
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
              {isLive ? "LIVE METRIC REPOSITORY" : "DEMO BASELINES (Backend Offline)"}
            </span>
            <span className="text-slate-400 ml-2">
              Endpoint: <code>{API_BASE_URL}/api/v1/baselines</code>
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <RefreshIndicator
            lastUpdated={lastUpdated}
            onRefresh={loadMetrics}
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

      {backendMessage && (
        <div className="p-3 rounded-lg bg-surface-subtle border border-border flex items-center gap-2 text-xs font-mono text-slate-300">
          <Info className="h-4 w-4 text-cyan-400 shrink-0" />
          <span>
            Backend status: <strong>{backendMessage}</strong>
          </span>
        </div>
      )}

      <div className="rounded-lg bg-surface border border-border p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold text-white tracking-tight">
              Metrics & Statistical Baseline Explorer
            </h3>
            <p className="text-[11px] font-mono text-slate-400">
              Correlate live telemetry with dynamic statistical lower & upper bounds
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
          <div>
            <label className="block text-slate-400 uppercase text-[10px] mb-1 font-semibold">
              Filter by Service
            </label>
            <select
              value={selectedService}
              onChange={(e) => setSelectedService(e.target.value)}
              className="w-full bg-surface-subtle border border-border rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="all">All Services (Cluster-wide)</option>
              <option value="user-service">User Service</option>
              <option value="order-service">Order Service</option>
              <option value="payment-service">Payment Service</option>
              <option value="notification-service">Notification Service</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-400 uppercase text-[10px] mb-1 font-semibold">
              Select Metric Signal
            </label>
            <select
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
              className="w-full bg-surface-subtle border border-border rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              {metricOptions.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-slate-400 uppercase text-[10px] mb-1 font-semibold">
              Time Range Window
            </label>
            <div className="flex items-center bg-surface-subtle p-1 rounded-lg border border-border">
              {["15m", "1h", "6h", "24h"].map((range) => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={`flex-1 py-1 text-xs font-mono rounded-md transition-all ${
                    timeRange === range
                      ? "bg-cyan-950 text-cyan-300 font-semibold border border-cyan-800/60 shadow-sm"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {range}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {!currentBaseline ? (
        <div className="rounded-lg bg-surface border border-border p-8 text-center text-sm font-mono text-slate-400">
          No baseline data available for the selected metric.{" "}
          {isLive ? "Prometheus may be unreachable." : "Enable demo data or connect the backend."}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 font-mono">
            <div className="rounded-lg bg-surface border border-cyan-800/60 p-5 space-y-4 shadow-[0_0_15px_-3px_rgba(6,182,212,0.15)]">
              <div className="flex items-center justify-between border-b border-border/80 pb-3">
                <div>
                  <span className="text-[10px] uppercase text-cyan-400 font-bold tracking-wider">
                    CURRENT LIVE METRIC
                  </span>
                  <h4 className="text-base font-bold text-white mt-0.5">
                    {selectedMetric} ({selectedService})
                  </h4>
                </div>
                <span className="px-2.5 py-1 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/60 text-xs font-bold">
                  OBSERVED
                </span>
              </div>

              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-white">
                  {Number((currentBaseline as AnyBaseline).current_value).toFixed(2)}
                </span>
                <span className="text-sm text-slate-400">{unit || "units"}</span>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-3 border-t border-border/60 text-xs">
                <div className="p-2.5 rounded bg-surface-subtle border border-border/60">
                  <span className="text-[10px] text-slate-400 uppercase block">
                    Deviation from Baseline
                  </span>
                  <div
                    className={`text-sm font-bold flex items-center gap-1 ${
                      currentBaseline.deviation_percentage > 50
                        ? "text-rose-400"
                        : "text-emerald-400"
                    }`}
                  >
                    {currentBaseline.deviation_percentage > 0 ? (
                      <ArrowUpRight className="h-4 w-4" />
                    ) : (
                      <ArrowDownRight className="h-4 w-4" />
                    )}
                    <span>
                      {currentBaseline.deviation_percentage >= 0 ? "+" : ""}
                      {currentBaseline.deviation_percentage.toFixed(1)}%
                    </span>
                  </div>
                </div>

                <div className="p-2.5 rounded bg-surface-subtle border border-border/60">
                  <span className="text-[10px] text-slate-400 uppercase block">
                    Deviation Absolute
                  </span>
                  <span className="text-sm font-bold text-slate-200">
                    {currentBaseline.deviation_from_mean >= 0 ? "+" : ""}
                    {currentBaseline.deviation_from_mean.toFixed(2)} {unit}
                  </span>
                </div>
              </div>
            </div>

            <div className="rounded-lg bg-surface border border-border p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-border/80 pb-3">
                <div>
                  <span className="text-[10px] uppercase text-indigo-400 font-bold tracking-wider">
                    STATISTICAL BASELINE (NORMAL BOUNDS)
                  </span>
                  <h4 className="text-base font-bold text-white mt-0.5">
                    Training Reference Distribution
                  </h4>
                </div>
                <span className="px-2.5 py-1 rounded bg-indigo-950 text-indigo-300 border border-indigo-800/60 text-xs font-bold">
                  EXPECTED
                </span>
              </div>

              <div className="grid grid-cols-3 gap-2.5 text-xs">
                {[
                  ["Mean", currentBaseline.mean, "text-slate-200"],
                  ["P50 (Median)", currentBaseline.p50, "text-slate-200"],
                  ["P95", currentBaseline.p95, "text-amber-400"],
                  ["P99", currentBaseline.p99, "text-rose-400"],
                  ["Lower Bound", currentBaseline.normal_lower_bound, "text-emerald-400"],
                  ["Upper Bound", currentBaseline.normal_upper_bound, "text-amber-400"],
                ].map(([label, value, color]) => (
                  <div
                    key={label as string}
                    className="p-2 rounded bg-surface-subtle border border-border/60"
                  >
                    <span className="text-[10px] text-slate-400 uppercase block">
                      {label}
                    </span>
                    <span className={`text-sm font-bold ${color}`}>
                      {Number(value).toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="rounded-lg bg-surface border border-border p-5">
            <MetricChart
              title={`${selectedMetric} Time-Series vs Statistical Upper Bound`}
              subtitle={
                isLive
                  ? `Window: ${timeRange} • Source: /api/v1/metrics & CloudWatch`
                  : `Window: ${timeRange} • Demo data`
              }
              data={displayChartData}
              unit={unit}
              height={300}
              showLegend={true}
              series={[
                {
                  key: "p95Latency",
                  name: "Observed " + selectedMetric,
                  color: "#06b6d4",
                  strokeWidth: 2,
                },
                {
                  key: "p99Latency",
                  name: "P99 Spike",
                  color: "#ef4444",
                  strokeWidth: 2,
                  strokeDasharray: "4 2",
                },
              ]}
            />
          </div>
        </>
      )}
    </div>
  );
}
