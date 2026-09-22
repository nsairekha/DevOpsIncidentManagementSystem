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

  const [selectedService, setSelectedService] = useState("all");  const [selectedMetric, setSelectedMetric] = useState("Latency");
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
              {isLive ? "Live metric repository" : "Demo baselines (backend offline)"}
            </span>
            <span className="text-slate-500 ml-2">
              Endpoint: <code className="bg-slate-100 text-slate-600 rounded px-1">{API_BASE_URL}/api/v1/baselines</code>
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
              className="text-[11px] px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-600 border border-slate-200 transition-colors"
            >
              {allowFallback ? "Hide Demo Data" : "Show Demo Data"}
            </button>
          )}
        </div>
      </div>

      {backendMessage && (
        <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-sm flex items-center gap-2 text-xs text-slate-600">
          <Info className="h-4 w-4 text-indigo-600 shrink-0" />
          <span>
            Backend status: <strong>{backendMessage}</strong>
          </span>
        </div>
      )}

      <div className="rounded-xl bg-white border border-slate-200 shadow-sm p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold text-slate-900 tracking-tight">
              Metrics & Statistical Baseline Explorer
            </h3>
            <p className="text-xs text-slate-500">
              Correlate live telemetry with dynamic statistical lower & upper bounds
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div>
            <label className="block text-slate-600 font-medium mb-1">
              Filter by service
            </label>
            <select
              value={selectedService}
              onChange={(e) => setSelectedService(e.target.value)}
              className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-900 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
            >
              <option value="all">All Services (Cluster-wide)</option>
              <option value="user-service">User Service</option>
              <option value="order-service">Order Service</option>
              <option value="payment-service">Payment Service</option>
              <option value="notification-service">Notification Service</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-600 font-medium mb-1">
              Select metric signal
            </label>
            <select
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
              className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-900 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
            >
              {metricOptions.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-slate-600 font-medium mb-1">
              Time range
            </label>
            <div className="flex items-center bg-slate-100 p-1 rounded-lg border border-slate-200">
              {["15m", "1h", "6h", "24h"].map((range) => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={`flex-1 py-1 text-xs rounded-md transition-all ${
                    timeRange === range
                      ? "bg-white shadow-sm text-slate-900 font-medium"
                      : "text-slate-500 hover:text-slate-900"
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
        <div className="rounded-xl bg-white border border-slate-200 shadow-sm p-8 text-center text-sm text-slate-500">
          No baseline data available for the selected metric.{" "}
          {isLive ? "Prometheus may be unreachable." : "Enable demo data or connect the backend."}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <div className="rounded-xl bg-white border border-slate-200 shadow-sm p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                  <span className="text-xs text-slate-500 font-medium">
                    Current live metric
                  </span>
                  <h4 className="text-base font-semibold text-slate-900 mt-0.5">
                    {selectedMetric} ({selectedService})
                  </h4>
                </div>
                <span className="px-2.5 py-1 rounded bg-indigo-50 text-indigo-700 border border-indigo-200 text-xs font-medium">
                  Observed
                </span>
              </div>

              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-semibold text-slate-900">
                  {Number((currentBaseline as AnyBaseline).current_value).toFixed(2)}
                </span>
                <span className="text-sm text-slate-500">{unit || "units"}</span>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-3 border-t border-slate-100 text-xs">
                <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                  <span className="text-[11px] text-slate-500 block">
                    Deviation from baseline
                  </span>
                  <div
                    className={`text-sm font-semibold flex items-center gap-1 ${
                      currentBaseline.deviation_percentage > 50
                        ? "text-rose-600"
                        : "text-emerald-600"
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

                <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                  <span className="text-[11px] text-slate-500 block">
                    Deviation absolute
                  </span>
                  <span className="text-sm font-semibold text-slate-900">
                    {currentBaseline.deviation_from_mean >= 0 ? "+" : ""}
                    {currentBaseline.deviation_from_mean.toFixed(2)} {unit}
                  </span>
                </div>
              </div>
            </div>

            <div className="rounded-xl bg-white border border-slate-200 shadow-sm p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                  <span className="text-xs text-slate-500 font-medium">
                    Statistical baseline (normal bounds)
                  </span>
                  <h4 className="text-base font-semibold text-slate-900 mt-0.5">
                    Training reference distribution
                  </h4>
                </div>
                <span className="px-2.5 py-1 rounded bg-slate-100 text-slate-600 border border-slate-200 text-xs font-medium">
                  Expected
                </span>
              </div>

              <div className="grid grid-cols-3 gap-2.5 text-xs">
                {[
                  ["Mean", currentBaseline.mean, "text-slate-900"],
                  ["P50 (Median)", currentBaseline.p50, "text-slate-900"],
                  ["P95", currentBaseline.p95, "text-amber-700"],
                  ["P99", currentBaseline.p99, "text-rose-600"],
                  ["Lower Bound", currentBaseline.normal_lower_bound, "text-emerald-600"],
                  ["Upper Bound", currentBaseline.normal_upper_bound, "text-amber-700"],
                ].map(([label, value, color]) => (
                  <div
                    key={label as string}
                    className="p-2 rounded bg-slate-50 border border-slate-200"
                  >
                    <span className="text-[11px] text-slate-500 block">
                      {label}
                    </span>
                    <span className={`text-sm font-semibold ${color}`}>
                      {Number(value).toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="rounded-xl bg-white border border-slate-200 shadow-sm p-5">
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
                  color: "#4F46E5",
                  strokeWidth: 2,
                },
                {
                  key: "p99Latency",
                  name: "P99 Spike",
                  color: "#DC2626",
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
