import {
  AnomalyRecord,
  IncidentRecord,
  MetricTimeSeriesPoint,
  ServiceHealthData,
  SystemKPIs,
} from "./types";
import { RawBaselineRecord, RawMetricRecord } from "./api";
import { DemoAnomaly, DemoIncident } from "./demoData";

export const KNOWN_SERVICES = [
  { id: "user-service", name: "User Service", port: 8001 },
  { id: "order-service", name: "Order Service", port: 8002 },
  { id: "payment-service", name: "Payment Service", port: 8003 },
  { id: "notification-service", name: "Notification Service", port: 8004 },
] as const;

const ANOMALY_DEVIATION_THRESHOLD = 25;

export function formatServiceName(id: string): string {
  return id
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export function formatServiceLabel(serviceName: string | null | undefined): string {
  if (!serviceName) return "Cluster";
  return formatServiceName(serviceName);
}

function findRecords(
  records: RawMetricRecord[],
  metricName: string,
  serviceName?: string
): RawMetricRecord[] {
  return records.filter((r) => {
    if (!r.metric_name.includes(metricName)) return false;
    if (serviceName && r.service_name && r.service_name !== serviceName) {
      return false;
    }
    return true;
  });
}

function avg(values: number[]): number {
  if (values.length === 0) return 0;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

function sum(values: number[]): number {
  return values.reduce((a, b) => a + b, 0);
}

export function computeKPIs(
  baselines: RawBaselineRecord[],
  metrics: RawMetricRecord[],
  healthStatus?: string,
  cwMetrics: RawMetricRecord[] = []
): SystemKPIs {
  const upRecords = findRecords(metrics, "up");
  const upValues = upRecords.map((r) => r.value);
  const availability =
    upValues.length > 0
      ? (avg(upValues.filter((v) => v >= 1)) / Math.max(upValues.length, 1)) * 100 +
        (avg(upValues) * (100 - 100)) // normalize: fraction up * 100
      : healthStatus === "ok"
      ? 100
      : 0;

  const normalizedAvailability =
    upValues.length > 0 ? avg(upValues) * 100 : healthStatus === "ok" ? 99.9 : 0;

  const requestRecords = findRecords(metrics, "http_requests_total");
  const requestRate = requestRecords.length > 0 ? sum(requestRecords.map((r) => r.value)) : 0;

  const durationBaseline = baselines.find((b) =>
    b.metric_name.includes("http_request_duration")
  );

  const p95Latency = durationBaseline
    ? Math.round(durationBaseline.p95 * 1000)
    : 0;
  const p99Latency = durationBaseline
    ? Math.round(durationBaseline.p99 * 1000)
    : 0;

  const cpuRecords = cwMetrics.filter(
    (r) =>
      r.metric_name.toLowerCase().includes("cpu") ||
      r.metric_name === "CPUUtilization"
  );
  const memRecords = cwMetrics.filter(
    (r) =>
      r.metric_name.toLowerCase().includes("memory") ||
      r.metric_name === "MemoryUtilization"
  );

  const cpuUsage = cpuRecords.length > 0 ? avg(cpuRecords.map((r) => r.value)) : 0;
  const memoryUsage = memRecords.length > 0 ? avg(memRecords.map((r) => r.value)) : 0;

  const anomalies = baselinesToAnomalies(baselines);
  const activeIncidents = anomalies.filter((a) => a.status === "Active").length;

  return {
    availability: Math.min(100, Math.max(0, normalizedAvailability)),
    requestRate: Math.round(requestRate),
    errorRate: 0,
    p95Latency,
    p99Latency,
    activeIncidents,
    cpuUsage,
    memoryUsage,
  };
}

export function buildServiceHealthList(
  baselines: RawBaselineRecord[],
  metrics: RawMetricRecord[],
  probes: Array<{ id: string; status: "Healthy" | "Degraded" | "Down"; version: string; isLive: boolean }>
): ServiceHealthData[] {
  return KNOWN_SERVICES.map((svc) => {
    const probe = probes.find((p) => p.id === svc.id);
    const svcBaselines = baselines.filter((b) => b.service_name === svc.id);
    const svcMetrics = metrics.filter((m) => m.service_name === svc.id);

    const upVal = findRecords(svcMetrics, "up")[0]?.value;
    const availability = upVal !== undefined ? upVal * 100 : probe?.isLive ? 99.9 : 0;

    const requestRate = sum(
      findRecords(svcMetrics, "http_requests_total").map((r) => r.value)
    );

    const durationBaseline = svcBaselines.find((b) =>
      b.metric_name.includes("duration")
    );
    const p95Latency = durationBaseline
      ? Math.round(durationBaseline.p95 * 1000)
      : 0;

    const cpuBaseline = svcBaselines.find((b) =>
      b.metric_name.toLowerCase().includes("cpu")
    );
    const memBaseline = svcBaselines.find((b) =>
      b.metric_name.toLowerCase().includes("memory")
    );

    let status: ServiceHealthData["status"] = "Down";
    if (probe?.isLive) {
      status = probe.status;
    } else if (upVal !== undefined && upVal >= 1) {
      status = "Healthy";
    } else if (availability > 0) {
      status = "Degraded";
    }

    return {
      id: svc.id,
      name: svc.name,
      status,
      availability: Math.round(availability * 100) / 100,
      requestRate: Math.round(requestRate),
      errorRate: 0,
      p95Latency,
      cpu: cpuBaseline?.current_value ?? 0,
      memory: memBaseline?.current_value ?? 0,
      port: svc.port,
      version: probe?.version ?? "N/A",
      dependencies:
        svc.id === "order-service"
          ? ["payment-service", "notification-service"]
          : [],
      lastChecked: new Date().toLocaleTimeString(),
    };
  });
}

function severityFromDeviation(pct: number): DemoAnomaly["severity"] {
  if (pct >= 200) return "Critical";
  if (pct >= 100) return "High";
  if (pct >= 50) return "Medium";
  return "Low";
}

export function baselinesToAnomalies(baselines: RawBaselineRecord[]): DemoAnomaly[] {
  return baselines
    .filter(
      (b) =>
        Math.abs(b.deviation_percentage) >= ANOMALY_DEVIATION_THRESHOLD ||
        b.current_value < b.normal_lower_bound ||
        b.current_value > b.normal_upper_bound
    )
    .map((b, idx) => {
      const unit = b.metric_name.includes("duration")
        ? "s"
        : b.metric_name.includes("rate")
        ? "req/s"
        : "";
      return {
        id: `ANOM-LIVE-${idx + 1}`,
        time: new Date().toLocaleTimeString() + " UTC",
        service: formatServiceLabel(b.service_name),
        metric: b.metric_name,
        anomalyType: "Baseline Deviation",
        currentValue: `${b.current_value.toFixed(2)}${unit ? " " + unit : ""}`,
        baseline: `${b.mean.toFixed(2)}${unit ? " " + unit : ""}`,
        deviation: `${b.deviation_percentage >= 0 ? "+" : ""}${b.deviation_percentage.toFixed(1)}%`,
        severity: severityFromDeviation(Math.abs(b.deviation_percentage)),
        status: "Active" as const,
        score: Math.abs(b.deviation_from_mean) / Math.max(b.standard_deviation, 0.001),
        details: `Current value ${b.current_value.toFixed(2)} deviates ${b.deviation_percentage.toFixed(1)}% from mean ${b.mean.toFixed(2)} (bounds: ${b.normal_lower_bound.toFixed(2)} – ${b.normal_upper_bound.toFixed(2)}).`,
      };
    })
    .sort((a, b) => Math.abs(parseFloat(b.deviation)) - Math.abs(parseFloat(a.deviation)));
}

export function anomaliesToIncidents(anomalies: DemoAnomaly[]): DemoIncident[] {
  return anomalies.map((a, idx) => ({
    id: `INC-LIVE-${idx + 1}`,
    severity: a.severity,
    service: a.service,
    detectedTime: a.time,
    duration: "Ongoing",
    anomaly: `${a.metric}: ${a.currentValue} vs ${a.baseline} baseline`,
    rootCause: "Pending RCA — derived from baseline deviation",
    resolution: "Awaiting operator triage",
    auditStatus: "Not yet audited",
    status: "Active" as const,
    incident: `Anomaly detected on ${a.metric}`,
    summary: a.details,
  }));
}

export function toAnomalyRecord(a: DemoAnomaly): AnomalyRecord {
  return {
    id: a.id,
    metric: a.metric,
    service: a.service,
    anomalyType: a.anomalyType,
    currentValue: a.currentValue,
    baseline: a.baseline,
    deviation: a.deviation,
    detectedAt: a.time,
    severity: a.severity,
    score: a.score,
    details: a.details,
  };
}

export function toIncidentRecord(i: DemoIncident): IncidentRecord {
  return {
    id: i.id,
    incident: i.incident,
    service: i.service,
    type: "High Latency",
    severity: i.severity,
    detected: i.detectedTime,
    status: i.status === "Active" ? "Active" : "Resolved",
    summary: i.summary,
    rootCause: i.rootCause,
    mitigation: i.resolution,
  };
}

export function buildTimeSeriesFromRecords(
  records: RawMetricRecord[],
  baselines: RawBaselineRecord[] = []
): MetricTimeSeriesPoint[] {
  const byTime = new Map<string, MetricTimeSeriesPoint>();

  for (const r of records) {
    const ts = new Date(r.timestamp);
    const timeKey = ts.toISOString();
    const label = ts.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    if (!byTime.has(timeKey)) {
      byTime.set(timeKey, {
        timestamp: timeKey,
        time: label,
        requestRate: 0,
        errorRate: 0,
        p95Latency: 0,
        p99Latency: 0,
        cpuUtilization: 0,
        memoryUtilization: 0,
      });
    }

    const point = byTime.get(timeKey)!;

    if (r.metric_name.includes("http_requests_total")) {
      point.requestRate += r.value;
    } else if (r.metric_name.includes("duration")) {
      point.p95Latency = Math.max(point.p95Latency, r.value * 1000);
      point.p99Latency = Math.max(point.p99Latency, r.value * 1000);
    } else if (
      r.metric_name.toLowerCase().includes("cpu") ||
      r.metric_name === "CPUUtilization"
    ) {
      point.cpuUtilization = r.value;
    } else if (
      r.metric_name.toLowerCase().includes("memory") ||
      r.metric_name === "MemoryUtilization"
    ) {
      point.memoryUtilization = r.value;
    }
  }

  // Fill gaps from baselines when time-series is sparse
  if (byTime.size === 0 && baselines.length > 0) {
    const duration = baselines.find((b) => b.metric_name.includes("duration"));
    const now = new Date();
    return [
      {
        timestamp: now.toISOString(),
        time: now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        requestRate: 0,
        errorRate: 0,
        p95Latency: duration ? duration.p95 * 1000 : 0,
        p99Latency: duration ? duration.p99 * 1000 : 0,
        cpuUtilization: 0,
        memoryUtilization: 0,
      },
    ];
  }

  return Array.from(byTime.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([, point]) => point);
}

export function findBaselineForMetric(
  baselines: RawBaselineRecord[],
  metricLabel: string,
  service?: string
): RawBaselineRecord | undefined {
  const needle = metricLabel.toLowerCase();
  return baselines.find((b) => {
    const nameMatch =
      b.metric_name.toLowerCase().includes(needle) ||
      (needle.includes("latency") && b.metric_name.includes("duration")) ||
      (needle.includes("cpu") && b.metric_name.toLowerCase().includes("cpu")) ||
      (needle.includes("memory") && b.metric_name.toLowerCase().includes("memory")) ||
      (needle.includes("request") && b.metric_name.includes("http_requests"));
    const serviceMatch =
      !service || service === "all" || b.service_name === service;
    return nameMatch && serviceMatch;
  });
}

export function inferUnit(baseline: RawBaselineRecord | undefined): string {
  if (!baseline) return "";
  if (baseline.metric_name.includes("duration")) return "ms";
  if (baseline.metric_name.includes("rate") || baseline.metric_name.includes("requests")) {
    return "req/s";
  }
  if (baseline.metric_name.toLowerCase().includes("cpu")) return "%";
  if (baseline.metric_name.toLowerCase().includes("memory")) return "%";
  return "";
}
