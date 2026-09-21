import type { DemoAnomaly, DemoIncident, DemoRCA } from "./demoData";
import {
  anomaliesToIncidents,
  baselinesToAnomalies,
  buildServiceHealthList,
  buildTimeSeriesFromRecords,
  computeKPIs,
  KNOWN_SERVICES,
} from "./metricUtils";
import {
  AnomalyAnalysisPayload,
  AnomalyAnalysisResult,
  MetricTimeSeriesPoint,
  MonitoringSourcesData,
  ServiceHealthData,
  SystemKPIs,
} from "./types";

/**
 * Global Base URL configured via NEXT_PUBLIC_API_URL.
 * Defaults to http://localhost:8000 for standard local backend deployment.
 */
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ApiResponse<T> {
  data: T | null;
  isLive: boolean;
  isFallback: boolean;
  statusText: string;
  source: string;
  error?: string | null;
  timestamp: string;
}

export interface BackendHealth {
  status: string;
  service: string;
  environment: string;
  version: string;
  timestamp: string;
}

export interface MetricSummary {
  timestamp: string;
  sources: {
    prometheus?: { available: boolean; metric_count: number };
    cloudwatch?: { available: boolean; metric_count: number };
  };
  services: string[];
}

export interface RawMetricRecord {
  timestamp: string;
  source: string;
  service_name: string | null;
  metric_name: string;
  value: number;
  unit: string | null;
  resource_id: string | null;
  labels: Record<string, string>;
  metadata: Record<string, string>;
}

export interface RawBaselineRecord {
  metric_name: string;
  service_name: string | null;
  source: string;
  resource_id: string | null;
  labels: Record<string, string>;
  observation_count: number;
  mean: number;
  median: number;
  minimum: number;
  maximum: number;
  standard_deviation: number;
  p50: number;
  p95: number;
  p99: number;
  moving_average: number;
  rolling_standard_deviation: number;
  normal_lower_bound: number;
  normal_upper_bound: number;
  current_value: number;
  deviation_from_mean: number;
  deviation_percentage: number;
}

export interface CloudWatchStatus {
  enabled: boolean;
  available: boolean;
  region: string | null;
  namespace: string | null;
  message: string;
}

export interface AuditBlock {
  index: number;
  timestamp: string;
  event_type: string;
  hash: string;
  previous_hash: string;
}

export interface AuditResponse {
  length: number;
  valid: boolean;
  errors: string[];
  last_hash: string;
  blocks: AuditBlock[];
}

/**
 * Generic safe HTTP fetcher with timeout and error capture.
 */
async function fetchEndpoint<T>(
  path: string,
  options?: RequestInit
): Promise<{ ok: boolean; status: number; data?: T; error?: string }> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 4000);

    // If running in browser and targeting same host or standard proxy
    const url = path.startsWith("http") ? path : `${API_BASE_URL}${path}`;

    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });

    clearTimeout(timeoutId);

    if (!res.ok) {
      return {
        ok: false,
        status: res.status,
        error: `HTTP ${res.status}: ${res.statusText}`,
      };
    }

    const data = await res.json();
    return { ok: true, status: res.status, data };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Network failure";
    return { ok: false, status: 0, error: message };
  }
}

/**
 * 1. Backend Health Check
 * Endpoint: GET /api/v1/health (or legacy GET /health)
 */
export async function fetchBackendHealth(): Promise<ApiResponse<BackendHealth>> {
  const res = await fetchEndpoint<BackendHealth>("/api/v1/health");
  if (res.ok && res.data) {
    return {
      data: res.data,
      isLive: true,
      isFallback: false,
      statusText: "Operational",
      source: "FastAPI /api/v1/health",
      timestamp: new Date().toISOString(),
    };
  }

  // Try legacy fallback /health
  const leg = await fetchEndpoint<BackendHealth>("/health");
  if (leg.ok && leg.data) {
    return {
      data: leg.data,
      isLive: true,
      isFallback: false,
      statusText: "Operational",
      source: "FastAPI /health",
      timestamp: new Date().toISOString(),
    };
  }

  return {
    data: null,
    isLive: false,
    isFallback: false,
    statusText: "Offline",
    source: "Unreachable",
    error: res.error || "Backend unreachable",
    timestamp: new Date().toISOString(),
  };
}

/**
 * 2. Metric Pipeline Summary
 * Endpoint: GET /api/v1/metrics/summary
 */
export async function fetchMetricsSummary(): Promise<ApiResponse<MetricSummary>> {
  const res = await fetchEndpoint<MetricSummary>("/api/v1/metrics/summary");
  if (res.ok && res.data) {
    return {
      data: res.data,
      isLive: true,
      isFallback: false,
      statusText: "Active",
      source: "FastAPI /api/v1/metrics/summary",
      timestamp: res.data.timestamp,
    };
  }

  return {
    data: null,
    isLive: false,
    isFallback: false,
    statusText: "Unavailable",
    source: "Unreachable",
    error: res.error,
    timestamp: new Date().toISOString(),
  };
}

/**
 * 3. Unified Metric Records List
 * Endpoint: GET /api/v1/metrics
 */
export async function fetchMetricsList(): Promise<
  ApiResponse<{ count: number; records: RawMetricRecord[]; message?: string }>
> {
  const res = await fetchEndpoint<{
    count: number;
    records: RawMetricRecord[];
    message?: string;
  }>("/api/v1/metrics");

  if (res.ok && res.data) {
    return {
      data: res.data,
      isLive: true,
      isFallback: false,
      statusText: res.data.message || `${res.data.count} records`,
      source: "FastAPI /api/v1/metrics",
      timestamp: new Date().toISOString(),
    };
  }

  return {
    data: null,
    isLive: false,
    isFallback: false,
    statusText: "Prometheus unavailable",
    source: "Unreachable",
    error: res.error,
    timestamp: new Date().toISOString(),
  };
}

/**
 * 4. Baselines Endpoint
 * Endpoint: GET /api/v1/baselines (or GET /api/v1/baselines/{metric_name})
 */
export async function fetchBaselines(
  metricName?: string
): Promise<ApiResponse<{ count: number; baselines: RawBaselineRecord[]; message?: string }>> {
  const path = metricName
    ? `/api/v1/baselines/${encodeURIComponent(metricName)}`
    : "/api/v1/baselines";

  const res = await fetchEndpoint<{
    count: number;
    baselines: RawBaselineRecord[];
    message?: string;
  }>(path);

  if (res.ok && res.data) {
    return {
      data: res.data,
      isLive: true,
      isFallback: false,
      statusText: res.data.message || `${res.data.count} baseline records`,
      source: `FastAPI ${path}`,
      timestamp: new Date().toISOString(),
    };
  }

  return {
    data: null,
    isLive: false,
    isFallback: false,
    statusText: "Baselines unavailable",
    source: "Unreachable",
    error: res.error,
    timestamp: new Date().toISOString(),
  };
}

/**
 * 5. CloudWatch Integration Status
 * Endpoint: GET /api/v1/cloudwatch/status
 */
export async function fetchCloudWatchStatus(): Promise<
  ApiResponse<CloudWatchStatus>
> {
  const res = await fetchEndpoint<CloudWatchStatus>("/api/v1/cloudwatch/status");
  if (res.ok && res.data) {
    return {
      data: res.data,
      isLive: true,
      isFallback: false,
      statusText: res.data.available ? "Connected" : res.data.enabled ? "Enabled" : "Disabled",
      source: "FastAPI /api/v1/cloudwatch/status",
      timestamp: new Date().toISOString(),
    };
  }

  return {
    data: null,
    isLive: false,
    isFallback: false,
    statusText: "CloudWatch unreachable",
    source: "Unreachable",
    error: res.error,
    timestamp: new Date().toISOString(),
  };
}

/**
 * 6. CloudWatch Normalized Metrics
 * Endpoint: GET /api/v1/cloudwatch/metrics
 */
export async function fetchCloudWatchMetrics(params?: {
  metric_name?: string;
  resource_id?: string;
  lookback_minutes?: number;
  statistic?: string;
  demo?: boolean;
}): Promise<ApiResponse<{ count: number; records: RawMetricRecord[] }>> {
  const query = new URLSearchParams();
  if (params?.metric_name) query.set("metric_name", params.metric_name);
  if (params?.resource_id) query.set("resource_id", params.resource_id);
  if (params?.lookback_minutes)
    query.set("lookback_minutes", params.lookback_minutes.toString());
  if (params?.statistic) query.set("statistic", params.statistic);
  if (params?.demo) query.set("demo", "true");

  const path = `/api/v1/cloudwatch/metrics${query.toString() ? `?${query.toString()}` : ""}`;
  const res = await fetchEndpoint<{ count: number; records: RawMetricRecord[] }>(path);

  if (res.ok && res.data) {
    return {
      data: res.data,
      isLive: true,
      isFallback: false,
      statusText: `${res.data.count} CloudWatch records`,
      source: `FastAPI ${path}`,
      timestamp: new Date().toISOString(),
    };
  }

  return {
    data: null,
    isLive: false,
    isFallback: false,
    statusText: "CloudWatch metrics unavailable",
    source: "Unreachable",
    error: res.error,
    timestamp: new Date().toISOString(),
  };
}

/**
 * 7. Blockchain Audit Trail
 * Endpoint: GET /api/audit
 */
export async function fetchAuditTrail(): Promise<
  ApiResponse<AuditResponse>
> {
  const res = await fetchEndpoint<AuditResponse>("/api/audit");
  if (res.ok && res.data) {
    return {
      data: res.data,
      isLive: true,
      isFallback: false,
      statusText: res.data.valid ? "Integrity Verified (Valid)" : "Chain Violated",
      source: "FastAPI /api/audit",
      timestamp: new Date().toISOString(),
    };
  }

  return {
    data: null,
    isLive: false,
    isFallback: false,
    statusText: "Blockchain audit integration not available",
    source: "Unreachable",
    error: res.error || "Blockchain audit integration not available.",
    timestamp: new Date().toISOString(),
  };
}

/**
 * 8. Live Blockchain Verification Trigger
 * Endpoint: GET /api/audit
 */
export async function verifyAuditChain(): Promise<{
  valid: boolean;
  length: number;
  lastHash: string;
  errors: string[];
  source: string;
  isLive: boolean;
}> {
  const res = await fetchEndpoint<AuditResponse>("/api/audit");
  if (res.ok && res.data) {
    return {
      valid: res.data.valid,
      length: res.data.length,
      lastHash: res.data.last_hash,
      errors: res.data.errors,
      source: "Live Blockchain Ledger (/api/audit)",
      isLive: true,
    };
  }

  return {
    valid: false,
    length: 0,
    lastHash: "N/A",
    errors: ["Blockchain audit integration not available."],
    source: "Unreachable",
    isLive: false,
  };
}

/**
 * 9. Anomaly Analysis Pipeline Trigger
 * Endpoint: POST /api/analyze
 */
export async function runLiveAnomalyAnalysis(
  payload: AnomalyAnalysisPayload
): Promise<AnomalyAnalysisResult | null> {
  const res = await fetchEndpoint<{
    detector: string;
    n_findings: number;
    severity: string;
    summary: string;
    findings: Array<{
      signal: string;
      value: number;
      score: number;
      severity: string;
      details: string;
      expected_range?: [number | null, number | null] | null;
      timestamp?: string;
    }>;
    audited: boolean;
    block_hash: string;
    event_id: string;
    chain_valid: boolean;
  }>("/api/analyze", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  if (res.ok && res.data) {
    return {
      detector: res.data.detector,
      nFindings: res.data.n_findings,
      severity: res.data.severity,
      summary: res.data.summary,
      findings: res.data.findings.map((f) => ({
        signal: f.signal,
        value: f.value,
        score: f.score,
        severity: f.severity,
        details: f.details,
        expectedRange: f.expected_range,
        timestamp: f.timestamp,
      })),
      audited: res.data.audited,
      blockHash: res.data.block_hash,
      eventId: res.data.event_id,
      chainValid: res.data.chain_valid,
    };
  }

  return null;
}

/**
 * 10. Service Health Probe (Direct microservices & summary)
 */
export async function probeServiceHealth(
  serviceName: string,
  port: number
): Promise<{ id: string; status: "Healthy" | "Degraded" | "Down"; version: string; isLive: boolean }> {
  const probe = await fetchEndpoint<{ status?: string; version?: string }>(
    `http://localhost:${port}/health`
  );
  if (probe.ok) {
    return {
      id: serviceName,
      status:
        probe.data?.status === "healthy" || probe.data?.status === "ok"
          ? "Healthy"
          : "Degraded",
      version: probe.data?.version || "0.1.0",
      isLive: true,
    };
  }

  return {
    id: serviceName,
    status: "Down",
    version: "N/A",
    isLive: false,
  };
}

/**
 * 11. Overview Aggregated Data
 */
export async function fetchOverviewData(): Promise<{
  kpis: SystemKPIs;
  services: ServiceHealthData[];
  sources: MonitoringSourcesData;
  chartData: MetricTimeSeriesPoint[];
  anomalies: DemoAnomaly[];
  incidents: DemoIncident[];
  isLive: boolean;
  error?: string | null;
}> {
  const [healthRes, summaryRes, cwStatusRes, baselinesRes, metricsRes, cwCpuRes, cwMemRes] =
    await Promise.all([
      fetchBackendHealth(),
      fetchMetricsSummary(),
      fetchCloudWatchStatus(),
      fetchBaselines(),
      fetchMetricsList(),
      fetchCloudWatchMetrics({ metric_name: "CPUUtilization", lookback_minutes: 15 }),
      fetchCloudWatchMetrics({ metric_name: "MemoryUtilization", lookback_minutes: 15 }),
    ]);

  if (healthRes.isLive && summaryRes.data) {
    const prom = summaryRes.data.sources.prometheus;
    const cw = cwStatusRes.data;
    const promActive = Boolean(prom?.available);
    const baselines = baselinesRes.data?.baselines || [];
    const metrics = metricsRes.data?.records || [];
    const cwRecords = [
      ...(cwCpuRes.data?.records || []),
      ...(cwMemRes.data?.records || []),
    ];

    const probes = await Promise.all(
      KNOWN_SERVICES.map((svc) => probeServiceHealth(svc.id, svc.port))
    );

    const services = buildServiceHealthList(baselines, metrics, probes);
    const kpis = computeKPIs(
      baselines,
      metrics,
      healthRes.data?.status,
      cwRecords
    );
    const anomalies = baselinesToAnomalies(baselines);
    const incidents = anomaliesToIncidents(anomalies);
    const chartData = buildTimeSeriesFromRecords(
      [...metrics, ...cwRecords],
      baselines
    );

    return {
      kpis,
      services,
      chartData,
      anomalies,
      incidents,
      sources: {
        prometheus: {
          status: promActive ? "Connected" : "Disconnected",
          targetCount: promActive ? summaryRes.data.services.length : 0,
          healthyTargets: promActive
            ? services.filter((s) => s.status === "Healthy").length
            : 0,
          url: process.env.NEXT_PUBLIC_PROMETHEUS_URL || "http://localhost:9090",
        },
        cloudwatch: {
          status: cw?.enabled
            ? cw.available
              ? "Connected"
              : "Disconnected"
            : "Disabled",
          enabled: Boolean(cw?.enabled),
          region: cw?.region || "us-east-1",
          available: Boolean(cw?.available),
          namespace: cw?.namespace || "AWS/ApplicationSignals",
        },
      },
      isLive: true,
    };
  }

  return {
    kpis: {
      availability: 0,
      requestRate: 0,
      errorRate: 0,
      p95Latency: 0,
      p99Latency: 0,
      activeIncidents: 0,
      cpuUsage: 0,
      memoryUsage: 0,
    },
    services: [],
    chartData: [],
    anomalies: [],
    incidents: [],
    sources: {
      prometheus: {
        status: "Disconnected",
        targetCount: 0,
        healthyTargets: 0,
      },
      cloudwatch: {
        status: "Disabled",
        enabled: false,
        region: "N/A",
        available: false,
      },
    },
    isLive: false,
    error:
      healthRes.error ||
      "Backend offline (Cannot connect to " + API_BASE_URL + ")",
  };
}

/**
 * 11b. Service fleet health (Services page)
 */
export async function fetchServicesData(): Promise<{
  services: ServiceHealthData[];
  isLive: boolean;
  error?: string | null;
}> {
  const [summaryRes, baselinesRes, metricsRes] = await Promise.all([
    fetchMetricsSummary(),
    fetchBaselines(),
    fetchMetricsList(),
  ]);

  if (summaryRes.isLive && summaryRes.data) {
    const baselines = baselinesRes.data?.baselines || [];
    const metrics = metricsRes.data?.records || [];
    const probes = await Promise.all(
      KNOWN_SERVICES.map((svc) => probeServiceHealth(svc.id, svc.port))
    );
    return {
      services: buildServiceHealthList(baselines, metrics, probes),
      isLive: true,
    };
  }

  return {
    services: [],
    isLive: false,
    error: summaryRes.error || "Backend API is offline at " + API_BASE_URL,
  };
}

/**
 * 12. RCA Data Endpoint
 * Requirement: If RCA API is not implemented yet, show "RCA data not available"
 * rather than fake AI output.
 */
export async function fetchRCAData(): Promise<{
  available: boolean;
  data: DemoRCA | null;
  message: string;
  isLive: boolean;
}> {
  // Check if an endpoint like /api/v1/rca or /api/rca exists
  const res = await fetchEndpoint<DemoRCA>("/api/rca");
  if (res.ok && res.data) {
    return {
      available: true,
      data: res.data,
      message: "RCA data retrieved from live backend",
      isLive: true,
    };
  }

  return {
    available: false,
    data: null,
    message: "RCA data not available",
    isLive: false,
  };
}

/**
 * 13. Incidents Data Endpoint
 * No dedicated /api/incidents route — derive from baseline anomalies.
 */
export async function fetchIncidentsData(): Promise<{
  data: DemoIncident[];
  isLive: boolean;
  message: string;
}> {
  const anomaliesRes = await fetchAnomaliesData();
  if (anomaliesRes.isLive) {
    const incidents = anomaliesToIncidents(anomaliesRes.data);
    return {
      data: incidents,
      isLive: true,
      message:
        incidents.length > 0
          ? `${incidents.length} incidents derived from live anomalies`
          : "No active incidents from baseline analysis",
    };
  }

  return {
    data: [],
    isLive: false,
    message: anomaliesRes.message || "Incidents endpoint not available",
  };
}

/**
 * 14. Anomalies Data Endpoint
 * No dedicated /api/anomalies route — derive from /api/v1/baselines deviations.
 */
export async function fetchAnomaliesData(): Promise<{
  data: DemoAnomaly[];
  isLive: boolean;
  message: string;
}> {
  const baselinesRes = await fetchBaselines();
  if (baselinesRes.isLive && baselinesRes.data) {
    const derived = baselinesToAnomalies(baselinesRes.data.baselines);
    return {
      data: derived,
      isLive: true,
      message:
        derived.length > 0
          ? `${derived.length} anomalies derived from live baselines`
          : baselinesRes.data.message || "No baseline deviations detected",
    };
  }

  return {
    data: [],
    isLive: false,
    message: baselinesRes.error || "Baselines unavailable — cannot detect anomalies",
  };
}

/**
 * 15. Metrics explorer data (baselines + time series)
 */
export async function fetchMetricsExplorerData(params?: {
  lookbackMinutes?: number;
}): Promise<{
  baselines: RawBaselineRecord[];
  metrics: RawMetricRecord[];
  chartData: MetricTimeSeriesPoint[];
  isLive: boolean;
  message?: string | null;
}> {
  const lookback = params?.lookbackMinutes ?? 15;
  const [baseRes, metRes, cwCpuRes, cwMemRes] = await Promise.all([
    fetchBaselines(),
    fetchMetricsList(),
    fetchCloudWatchMetrics({
      metric_name: "CPUUtilization",
      lookback_minutes: lookback,
    }),
    fetchCloudWatchMetrics({
      metric_name: "MemoryUtilization",
      lookback_minutes: lookback,
    }),
  ]);

  if (baseRes.isLive) {
    const baselines = baseRes.data?.baselines || [];
    const metrics = metRes.data?.records || [];
    const cwRecords = [
      ...(cwCpuRes.data?.records || []),
      ...(cwMemRes.data?.records || []),
    ];
    return {
      baselines,
      metrics,
      chartData: buildTimeSeriesFromRecords([...metrics, ...cwRecords], baselines),
      isLive: true,
      message: baseRes.data?.message || null,
    };
  }

  return {
    baselines: [],
    metrics: [],
    chartData: [],
    isLive: false,
    message: baseRes.error || "Baselines unavailable",
  };
}
