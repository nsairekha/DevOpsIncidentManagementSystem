export type SystemStatus = "Operational" | "Degraded" | "Critical";
export type ServiceStatus = "Healthy" | "Degraded" | "Down";
export type Environment = "Local" | "AWS";

export interface SystemKPIs {
  availability: number; // e.g. 99.95 (%)
  requestRate: number; // e.g. 1420 (req/s)
  errorRate: number; // e.g. 0.08 (%)
  p95Latency: number; // e.g. 42 (ms)
  p99Latency: number; // e.g. 118 (ms)
  activeIncidents: number; // e.g. 1
  cpuUsage: number; // e.g. 38.4 (%)
  memoryUsage: number; // e.g. 62.1 (%)
}

export interface ServiceHealthData {
  id: string;
  name: string;
  status: ServiceStatus;
  availability: number;
  requestRate: number;
  errorRate: number;
  p95Latency: number;
  cpu: number;
  memory: number;
  port: number;
  version: string;
  dependencies: string[];
  lastChecked: string;
}

export type IncidentType =
  | "High Latency"
  | "High Error Rate"
  | "Service Failure"
  | "Dependency Failure"
  | "Resource Usage";

export type IncidentSeverity = "Critical" | "High" | "Medium" | "Low";
export type IncidentStatus = "Active" | "Investigating" | "Resolved";

export interface IncidentRecord {
  id: string;
  incident: string;
  service: string;
  type: IncidentType;
  severity: IncidentSeverity;
  detected: string;
  status: IncidentStatus;
  summary: string;
  rootCause?: string;
  mitigation?: string;
}

export interface AnomalyRecord {
  id: string;
  metric: string;
  service: string;
  anomalyType: string;
  currentValue: string;
  baseline: string;
  deviation: string;
  detectedAt: string;
  severity: IncidentSeverity;
  score?: number;
  details?: string;
}

export interface PrometheusStatus {
  status: "Connected" | "Disconnected" | "Disabled";
  targetCount: number;
  healthyTargets: number;
  url?: string;
}

export interface CloudWatchStatus {
  status: "Connected" | "Disconnected" | "Disabled";
  enabled: boolean;
  region: string;
  available: boolean;
  namespace?: string;
}

export interface MonitoringSourcesData {
  prometheus: PrometheusStatus;
  cloudwatch: CloudWatchStatus;
}

export interface MetricTimeSeriesPoint {
  timestamp: string;
  time: string;
  requestRate: number;
  errorRate: number;
  p95Latency: number;
  p99Latency: number;
  cpuUtilization: number;
  memoryUtilization: number;
}

export interface BlockchainBlock {
  index: number;
  timestamp: string;
  eventType: string;
  hash: string;
  previousHash: string;
  data?: Record<string, unknown>;
}

export interface BlockchainAuditResponse {
  length: number;
  valid: boolean;
  errors: string[];
  lastHash: string;
  blocks: BlockchainBlock[];
}

export interface AnomalyAnalysisPayload {
  detector: "zscore" | "iqr" | "isolation_forest";
  reference: Record<string, number[]>;
  telemetry: Record<string, number[]>;
  threshold?: number;
}

export interface AnomalyFinding {
  signal: string;
  value: number;
  score: number;
  severity: string;
  details: string;
  expectedRange?: [number | null, number | null] | null;
  timestamp?: string;
}

export interface AnomalyAnalysisResult {
  detector: string;
  nFindings: number;
  severity: string;
  summary: string;
  findings: AnomalyFinding[];
  audited: boolean;
  blockHash: string;
  eventId: string;
  chainValid: boolean;
}
