"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  Activity,
  AlertOctagon,
  Clock,
  Cpu,
  HardDrive,
  Layers,
  RefreshCw,
  Server,
  ShieldCheck,
  Zap,
  Info,
} from "lucide-react";
import MetricCard from "../../components/MetricCard";
import ServiceCard from "../../components/ServiceCard";
import MetricChart from "../../components/MetricChart";
import ServiceMap from "../../components/ServiceMap";
import IncidentTable from "../../components/IncidentTable";
import AnomalyTable from "../../components/AnomalyTable";
import MonitoringStatus from "../../components/MonitoringStatus";
import RefreshIndicator from "../../components/RefreshIndicator";
import { LoadingState, ErrorState } from "../../components/LoadingState";
import { API_BASE_URL, fetchOverviewData } from "../../lib/api";
import {
  DEMO_ANOMALIES,
  DEMO_INCIDENTS,
  DEMO_KPIS,
  DEMO_MONITORING_SOURCES,
  DEMO_SERVICES,
  DEMO_TIMESERIES_DATA,
} from "../../lib/demo-data";
import { toAnomalyRecord, toIncidentRecord } from "../../lib/metricUtils";
import {
  MetricTimeSeriesPoint,
  MonitoringSourcesData,
  ServiceHealthData,
  SystemKPIs,
} from "../../lib/types";

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Live vs Fallback state
  const [isLive, setIsLive] = useState(false);
  const [allowFallback, setAllowFallback] = useState(true);
  const [promStatusMessage, setPromStatusMessage] = useState<string | null>(null);

  // Data states
  const [kpis, setKpis] = useState<SystemKPIs | null>(null);
  const [services, setServices] = useState<ServiceHealthData[]>([]);
  const [sources, setSources] = useState<MonitoringSourcesData | null>(null);
  const [chartData, setChartData] = useState<MetricTimeSeriesPoint[]>([]);
  const [liveAnomalies, setLiveAnomalies] = useState(
    DEMO_ANOMALIES.map(toAnomalyRecord)
  );
  const [liveIncidents, setLiveIncidents] = useState(
    DEMO_INCIDENTS.map(toIncidentRecord)
  );
  const [baselineMean, setBaselineMean] = useState<number | null>(null);

  const loadDashboard = useCallback(async () => {
    try {
      setRefreshing(true);
      setError(null);

      const overviewRes = await fetchOverviewData();

      if (overviewRes.isLive) {
        setIsLive(true);
        setKpis(overviewRes.kpis);
        setServices(overviewRes.services);
        setSources(overviewRes.sources);
        setChartData(
          overviewRes.chartData.length > 0 ? overviewRes.chartData : []
        );
        setLiveAnomalies(overviewRes.anomalies.map(toAnomalyRecord));
        setLiveIncidents(overviewRes.incidents.map(toIncidentRecord));
        setBaselineMean(
          overviewRes.kpis.p95Latency > 0 ? overviewRes.kpis.p95Latency * 0.7 : null
        );

        if (!overviewRes.sources.prometheus.status.includes("Connected")) {
          setPromStatusMessage("Prometheus unavailable");
        } else {
          setPromStatusMessage(null);
        }
      } else {
        setIsLive(false);
        setError(overviewRes.error || "Backend is offline");

        if (allowFallback) {
          setKpis(DEMO_KPIS);
          setServices(DEMO_SERVICES);
          setSources(DEMO_MONITORING_SOURCES);
          setChartData(DEMO_TIMESERIES_DATA);
          setLiveAnomalies(DEMO_ANOMALIES.map(toAnomalyRecord));
          setLiveIncidents(DEMO_INCIDENTS.map(toIncidentRecord));
          setPromStatusMessage("Prometheus unconfigured in local sandbox");
        } else {
          setKpis(null);
          setServices([]);
          setSources(null);
          setChartData([]);
          setLiveAnomalies([]);
          setLiveIncidents([]);
        }
      }

      setLastUpdated(new Date());
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error connecting to backend";
      setError(msg);
      setIsLive(false);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [allowFallback]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  if (loading && !kpis) {
    return <LoadingState type="full" message="Connecting to live backend API (/api/v1)..." />;
  }

  return (
    <div className="space-y-6">
      {/* Live / Fallback Mode Header Banner */}
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
              {isLive ? "Live backend connected" : "Demo fallback (backend offline)"}
            </span>
            <span className="text-slate-500 ml-2">
              Endpoint: <code className="bg-slate-100 text-slate-600 rounded px-1">{API_BASE_URL}</code>
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <RefreshIndicator
            lastUpdated={lastUpdated}
            onRefresh={loadDashboard}
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

      {/* Backend Error / Prometheus Alert */}
      {error && !isLive && !allowFallback && (
        <ErrorState
          title="Backend Unreachable"
          message={`Could not establish connection to ${API_BASE_URL}. Ensure uvicorn is running: uvicorn backend.app.main:app --port 8000`}
          onRetry={loadDashboard}
        />
      )}

      {/* Page Title & Status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h2 className="text-xl font-semibold text-slate-900 tracking-tight">
            System Overview & SRE Health
          </h2>
          <p className="text-sm text-slate-500">
            Live telemetry data retrieved from FastAPI & Prometheus pipeline
          </p>
        </div>

        {promStatusMessage && (
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-amber-50 text-amber-700 border border-amber-200 text-xs">
            <Info className="h-3.5 w-3.5 shrink-0" />
            <span>{promStatusMessage}</span>
          </div>
        )}
      </div>

      {/* Primary KPI Cards (Availability, Request Rate, Error Rate, P95, P99, CPU, Memory, Active Incidents) */}
      {kpis && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-4 gap-3.5">
          {/* Availability */}
          <MetricCard
            title="System Availability"
            value={kpis.availability > 0 ? `${kpis.availability.toFixed(2)}` : "Unavailable"}
            unit={kpis.availability > 0 ? "%" : ""}
            description={isLive ? "Live from /api/v1/health" : "Demo 99.9% SLA"}
            status={kpis.availability < 99.0 && kpis.availability > 0 ? "warning" : "normal"}
            icon={<Layers className="h-4 w-4" />}
          />

          {/* Request Rate */}
          <MetricCard
            title="Request Rate"
            value={
              kpis.requestRate > 0
                ? kpis.requestRate.toLocaleString()
                : promStatusMessage || "0"
            }
            unit={kpis.requestRate > 0 ? "req/s" : ""}
            description={isLive ? "Live from Prometheus" : "Demo rate"}
            icon={<Zap className="h-4 w-4" />}
          />

          {/* Error Rate */}
          <MetricCard
            title="Error Rate"
            value={`${kpis.errorRate.toFixed(2)}`}
            unit="%"
            description="5xx/4xx proportion"
            status={kpis.errorRate > 1.0 ? "critical" : "normal"}
            icon={<AlertOctagon className="h-4 w-4" />}
          />

          {/* P95 Latency */}
          <MetricCard
            title="P95 Latency"
            value={kpis.p95Latency > 0 ? `${kpis.p95Latency}` : "N/A"}
            unit={kpis.p95Latency > 0 ? "ms" : ""}
            description={baselineMean !== null ? `Baseline: ${baselineMean.toFixed(0)}ms` : "Trailing window"}
            status={kpis.p95Latency > 150 ? "warning" : "normal"}
            icon={<Clock className="h-4 w-4" />}
          />

          {/* P99 Latency */}
          <MetricCard
            title="P99 Latency"
            value={kpis.p99Latency > 0 ? `${kpis.p99Latency}` : "N/A"}
            unit={kpis.p99Latency > 0 ? "ms" : ""}
            description="99th percentile tail"
            status={kpis.p99Latency > 300 ? "critical" : "normal"}
            icon={<Activity className="h-4 w-4" />}
          />

          {/* Active Incidents */}
          <MetricCard
            title="Active Incidents"
            value={kpis.activeIncidents}
            unit={kpis.activeIncidents === 1 ? "incident" : "incidents"}
            description={kpis.activeIncidents === 0 ? "Fleet operating nominally" : "Attention needed"}
            status={kpis.activeIncidents > 0 ? "critical" : "normal"}
            icon={<AlertOctagon className="h-4 w-4" />}
          />

          {/* CPU Usage */}
          <MetricCard
            title="Cluster CPU"
            value={kpis.cpuUsage > 0 ? `${kpis.cpuUsage.toFixed(1)}` : "N/A"}
            unit={kpis.cpuUsage > 0 ? "%" : ""}
            description="Host/container aggregate"
            status={kpis.cpuUsage > 75 ? "warning" : "normal"}
            icon={<Cpu className="h-4 w-4" />}
          />

          {/* Memory Usage */}
          <MetricCard
            title="Cluster Memory"
            value={kpis.memoryUsage > 0 ? `${kpis.memoryUsage.toFixed(1)}` : "N/A"}
            unit={kpis.memoryUsage > 0 ? "%" : ""}
            description="Resident set memory"
            status={kpis.memoryUsage > 80 ? "warning" : "normal"}
            icon={<HardDrive className="h-4 w-4" />}
          />
        </div>
      )}

      {/* Telemetry Charts: A, B, C, D, E */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <MetricChart
          title="A. Request Rate Over Time"
          subtitle={
            isLive
              ? chartData.length > 0
                ? "Calculated from Prometheus http_requests_total"
                : "Insufficient time-series data from API"
              : "Demo telemetry curve"
          }
          data={isLive && chartData.length > 0 ? chartData : DEMO_TIMESERIES_DATA}
          unit="req/s"
          series={[
            {
              key: "requestRate",
              name: "Request Rate",
              color: "#4F46E5",
              strokeWidth: 2,
            },
          ]}
        />

        <MetricChart
          title="B. Error Rate Over Time"
          subtitle={
            isLive
              ? "Error rate metrics not exposed by backend yet"
              : "Percentage of 5xx server responses"
          }
          data={isLive && chartData.length > 0 ? chartData : DEMO_TIMESERIES_DATA}
          unit="%"
          series={[
            {
              key: "errorRate",
              name: "Error Rate (%)",
              color: "#DC2626",
              strokeWidth: 2,
            },
          ]}
        />

        <MetricChart
          title="C. P95 / P99 Latency Over Time"
          subtitle={
            isLive
              ? "From http_request_duration_seconds baselines"
              : "Trailing request duration distribution"
          }
          data={isLive && chartData.length > 0 ? chartData : DEMO_TIMESERIES_DATA}
          unit="ms"
          showLegend={true}
          series={[
            {
              key: "p95Latency",
              name: "P95 Latency",
              color: "#D97706",
              strokeWidth: 2,
            },
            {
              key: "p99Latency",
              name: "P99 Latency",
              color: "#DC2626",
              strokeWidth: 2,
              strokeDasharray: "4 2",
            },
          ]}
        />

        <MetricChart
          title="D & E. Resource Utilization (CPU & Memory)"
          subtitle={
            isLive
              ? "From CloudWatch /api/v1/cloudwatch/metrics"
              : "Aggregate cluster infrastructure load"
          }
          data={isLive && chartData.length > 0 ? chartData : DEMO_TIMESERIES_DATA}
          unit="%"
          showLegend={true}
          series={[
            {
              key: "cpuUtilization",
              name: "CPU Utilization",
              color: "#2563EB",
              strokeWidth: 2,
            },
            {
              key: "memoryUtilization",
              name: "Memory Utilization",
              color: "#7C3AED",
              strokeWidth: 2,
            },
          ]}
        />
      </div>

      {/* Service Health Cards */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-sm font-semibold text-slate-900 tracking-tight">
              Microservice Fleet Status
            </h3>
            <p className="text-xs text-slate-500">
              {isLive
                ? "Live status reported by /api/v1/metrics/summary"
                : "Development fallback preview (Ports 8001-8004)"}
            </p>
          </div>
          <a
            href="/services"
            className="text-sm text-indigo-600 hover:text-indigo-700"
          >
            View all services →
          </a>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {services.map((service) => (
            <ServiceCard key={service.id} service={service} />
          ))}
        </div>
      </div>

      {/* Distributed Service Map */}
      <ServiceMap services={services} />

      {/* Recent Incidents & Anomalies Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <IncidentTable
          incidents={liveIncidents}
          isDemo={!isLive}
          title="Incident Feed"
          limit={3}
        />
        <AnomalyTable
          anomalies={liveAnomalies}
          isDemo={!isLive}
          title="Baseline Anomalies"
          limit={3}
        />
      </div>

      {/* Monitoring Infrastructure Status (Prometheus / CloudWatch) */}
      {sources && (
        <MonitoringStatus data={sources} isDemo={!isLive} />
      )}
    </div>
  );
}
