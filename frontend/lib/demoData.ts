/**
 * ============================================================================
 * DEMO FALLBACK DATA STORE (DEVELOPMENT ONLY)
 * ============================================================================
 * WARNING: These data structures are strictly isolated for local frontend
 * development when backend microservices or the Prometheus daemon are offline.
 *
 * All records are tagged with isDemo: true.
 * This file is NEVER presented as live production data.
 * ============================================================================
 */

export interface DemoIncident {
  id: string;
  severity: "Critical" | "High" | "Medium" | "Low";
  service: string;
  detectedTime: string;
  duration: string;
  anomaly: string;
  rootCause: string;
  resolution: string;
  auditStatus: string;
  status: "Active" | "Resolved";
  incident: string;
  summary: string;
}

export interface DemoAnomaly {
  id: string;
  time: string;
  service: string;
  metric: string;
  anomalyType: string;
  currentValue: string;
  baseline: string;
  deviation: string;
  severity: "Critical" | "High" | "Medium" | "Low";
  status: "Active" | "Mitigated" | "Resolved";
  score: number;
  details: string;
}

export interface DemoRCA {
  incident: string;
  affectedService: string;
  suspectedRootCause: string;
  evidence: string[];
  affectedDependencies: string[];
  timeline: Array<{
    time: string;
    event: string;
    description: string;
  }>;
  aiExplanation: string;
  recommendedAction: string;
}

export interface DemoBaseline {
  metric_name: string;
  service_name: string;
  source: string;
  current_value: number;
  mean: number;
  p50: number;
  p95: number;
  p99: number;
  normal_lower_bound: number;
  normal_upper_bound: number;
  deviation_percentage: number;
  deviation_from_mean: number;
  observation_count: number;
  unit: string;
}

export const DEMO_IS_FALLBACK = true;

export const DEMO_INCIDENTS: DemoIncident[] = [
  {
    id: "INC-4091",
    severity: "Critical",
    service: "Payment Service",
    detectedTime: "12 mins ago (11:25 UTC)",
    duration: "14m 32s",
    anomaly: "Payment Latency (850ms vs 180ms baseline)",
    rootCause: "Downstream bank acquirer socket timeout cascading into worker pool thread exhaustion.",
    resolution: "Pending operator confirmation: Throttle retry intervals & enable async fallback queue.",
    auditStatus: "Audited on Ledger (Block #3: 0x6e0b4d8a)",
    status: "Active",
    incident: "Payment Gateway Latency Spike Breaches SLA",
    summary: "p95 latency in Payment Service exceeded SLA threshold of 450ms.",
  },
  {
    id: "INC-4088",
    severity: "High",
    service: "Order Service",
    detectedTime: "28 mins ago (11:09 UTC)",
    duration: "28m 10s",
    anomaly: "HTTP 502/504 Error Rate Spike (1.45%)",
    rootCause: "Order service waiting on synchronous payment confirmation from payment-service:8003.",
    resolution: "Applying fast-timeout fallback on order creation route.",
    auditStatus: "Audited on Ledger (Block #4: 0x8c1d3e5a)",
    status: "Active",
    incident: "Cascading Latency in Order Placement Flow",
    summary: "Order placement endpoint experiencing cascading failures due to downstream payment latency.",
  },
  {
    id: "INC-4062",
    severity: "Medium",
    service: "Payment Service",
    detectedTime: "2 hours ago (09:30 UTC)",
    duration: "18m 45s",
    anomaly: "Container CPU Utilization Sustained >85%",
    rootCause: "Inefficient regex token parsing during high-volume batch processing.",
    resolution: "Autoscaler deployed 2 additional container pods; patched parser regex.",
    auditStatus: "Audited on Ledger (Block #2: 0x4f8a2c6e)",
    status: "Resolved",
    incident: "CPU Throttling on Payment Pods",
    summary: "Resolved after horizontal autoscaling and pod redistribution.",
  },
  {
    id: "INC-4054",
    severity: "Low",
    service: "Notification Service",
    detectedTime: "5 hours ago (06:15 UTC)",
    duration: "4m 12s",
    anomaly: "Socket Reconnection Delay",
    rootCause: "Upstream message broker TLS certificate reload momentary disconnect.",
    resolution: "Auto-reconnect completed successfully after 18 seconds.",
    auditStatus: "Audited on Ledger (Block #1: 0x2b7a9f4c)",
    status: "Resolved",
    incident: "Temporary Message Broker Socket Drop",
    summary: "Self-healed via backoff retry loop.",
  },
];

export const DEMO_ANOMALIES: DemoAnomaly[] = [
  {
    id: "ANOM-8921",
    time: "11:28 UTC (8m ago)",
    service: "Payment Service",
    metric: "payment_service_latency",
    anomalyType: "Latency Anomaly (Z-Score)",
    currentValue: "850 ms",
    baseline: "180 ms",
    deviation: "+372.2%",
    severity: "Critical",
    status: "Active",
    score: 4.82,
    details: "Observed value 850ms significantly breaches the 3.0σ statistical threshold.",
  },
  {
    id: "ANOM-8919",
    time: "11:22 UTC (14m ago)",
    service: "Order Service",
    metric: "order_service_error_rate",
    anomalyType: "Error Rate Spike (IQR)",
    currentValue: "1.45%",
    baseline: "0.05%",
    deviation: "+2800.0%",
    severity: "High",
    status: "Active",
    score: 3.91,
    details: "IQR detector flagged upper quartile bound violation on HTTP 5xx codes.",
  },
  {
    id: "ANOM-8915",
    time: "11:10 UTC (26m ago)",
    service: "Payment Service",
    metric: "memory_resident_set_mb",
    anomalyType: "Resource Usage (Isolation Forest)",
    currentValue: "892 MB",
    baseline: "340 MB",
    deviation: "+162.4%",
    severity: "Medium",
    status: "Active",
    score: 2.74,
    details: "Unsupervised Isolation Forest tree flagged abnormal heap allocation rate.",
  },
  {
    id: "ANOM-8902",
    time: "10:55 UTC (41m ago)",
    service: "Order Service",
    metric: "request_duration_seconds",
    anomalyType: "Dependency Latency Propagation",
    currentValue: "290 ms",
    baseline: "45 ms",
    deviation: "+544.4%",
    severity: "High",
    status: "Active",
    score: 3.65,
    details: "Cross-service causal correlation with payment-service duration.",
  },
  {
    id: "ANOM-8894",
    time: "10:15 UTC (1h ago)",
    service: "User Service",
    metric: "user_auth_latency",
    anomalyType: "Transient Cache Jitter",
    currentValue: "38 ms",
    baseline: "18 ms",
    deviation: "+111.1%",
    severity: "Low",
    status: "Resolved",
    score: 1.84,
    details: "Cold cache warm-up delay after rolling container deployment.",
  },
];

export const DEMO_BASELINES: DemoBaseline[] = [
  {
    metric_name: "Latency (p95)",
    service_name: "payment-service",
    source: "prometheus",
    current_value: 850.0,
    mean: 180.5,
    p50: 165.0,
    p95: 195.0,
    p99: 220.0,
    normal_lower_bound: 140.0,
    normal_upper_bound: 240.0,
    deviation_percentage: 370.9,
    deviation_from_mean: 669.5,
    observation_count: 1400,
    unit: "ms",
  },
  {
    metric_name: "Error Rate",
    service_name: "order-service",
    source: "prometheus",
    current_value: 1.45,
    mean: 0.05,
    p50: 0.02,
    p95: 0.08,
    p99: 0.15,
    normal_lower_bound: 0.0,
    normal_upper_bound: 0.1,
    deviation_percentage: 2800.0,
    deviation_from_mean: 1.4,
    observation_count: 1800,
    unit: "%",
  },
  {
    metric_name: "CPU Utilization",
    service_name: "payment-service",
    source: "prometheus",
    current_value: 82.0,
    mean: 38.4,
    p50: 36.0,
    p95: 55.0,
    p99: 68.0,
    normal_lower_bound: 20.0,
    normal_upper_bound: 70.0,
    deviation_percentage: 113.5,
    deviation_from_mean: 43.6,
    observation_count: 900,
    unit: "%",
  },
  {
    metric_name: "Memory Utilization",
    service_name: "payment-service",
    source: "prometheus",
    current_value: 89.0,
    mean: 44.2,
    p50: 42.0,
    p95: 60.0,
    p99: 68.0,
    normal_lower_bound: 30.0,
    normal_upper_bound: 75.0,
    deviation_percentage: 101.4,
    deviation_from_mean: 44.8,
    observation_count: 900,
    unit: "%",
  },
  {
    metric_name: "Request Rate",
    service_name: "order-service",
    source: "prometheus",
    current_value: 620.0,
    mean: 580.0,
    p50: 575.0,
    p95: 650.0,
    p99: 710.0,
    normal_lower_bound: 400.0,
    normal_upper_bound: 750.0,
    deviation_percentage: 6.9,
    deviation_from_mean: 40.0,
    observation_count: 2400,
    unit: "req/s",
  },
];

export const DEMO_RCA: DemoRCA = {
  incident: "INC-4091: Payment Gateway High Latency Spike",
  affectedService: "payment-service (Port 8003)",
  suspectedRootCause: "Downstream acquirer socket timeout cascading into worker pool thread exhaustion.",
  evidence: [
    "p95 latency spiked to 850ms (+372% above 180ms baseline)",
    "CPU sustained >82% across all 3 payment-service container replicas",
    "Cascading timeout errors observed on order-service /api/v1/orders caller",
  ],
  affectedDependencies: [
    "order-service:8002 (upstream caller blocked on HTTP POST /api/v1/payments)",
    "notification-service:8004 (order notifications delayed)",
  ],
  timeline: [
    {
      time: "10:52:14 UTC",
      event: "Z-Score Anomaly Triggered",
      description: "payment_service_latency breached threshold 3.0 (observed score 4.82)",
    },
    {
      time: "11:01:45 UTC",
      event: "IncidentAnalysisAgent Diagnosis",
      description: "Correlated cross-service metrics; blamed payment-service with 94.8% confidence",
    },
    {
      time: "11:08:11 UTC",
      event: "Mitigation Playbook Generated",
      description: "Generated recommendation: patch order-service timeout to 2.5s and throttle retries",
    },
  ],
  aiExplanation:
    "The IncidentAnalysisAgent fitted an unsupervised z-score detector against the 60-minute reference window. It isolated payment-service duration as the root cause with greatest statistical deviation (deviation score 4.82 vs medium threshold 3.0), ruling out client traffic spikes as the primary cause.",
  recommendedAction:
    "Apply circuit breaker throttle on payment retries and enable asynchronous queueing in order-service.",
};

export const DEMO_KPIS = {
  availability: 99.36,
  requestRate: 1420,
  errorRate: 1.08,
  p95Latency: 145,
  p99Latency: 480,
  activeIncidents: 1,
  cpuUsage: 48.2,
  memoryUsage: 59.4,
};

export const DEMO_SERVICES = [
  {
    id: "user-service",
    name: "User Service",
    status: "Healthy" as const,
    availability: 99.98,
    requestRate: 340,
    errorRate: 0.02,
    p95Latency: 18,
    cpu: 24,
    memory: 42,
    port: 8001,
    version: "v1.2.4",
    dependencies: [],
    lastChecked: "Just now",
  },
  {
    id: "order-service",
    name: "Order Service",
    status: "Degraded" as const,
    availability: 99.12,
    requestRate: 620,
    errorRate: 1.45,
    p95Latency: 142,
    cpu: 68,
    memory: 74,
    port: 8002,
    version: "v2.0.1",
    dependencies: ["payment-service", "notification-service"],
    lastChecked: "Just now",
  },
  {
    id: "payment-service",
    name: "Payment Service",
    status: "Degraded" as const,
    availability: 98.4,
    requestRate: 310,
    errorRate: 2.8,
    p95Latency: 480,
    cpu: 82,
    memory: 89,
    port: 8003,
    version: "v1.8.0",
    dependencies: [],
    lastChecked: "Just now",
  },
  {
    id: "notification-service",
    name: "Notification Service",
    status: "Healthy" as const,
    availability: 99.95,
    requestRate: 150,
    errorRate: 0.0,
    p95Latency: 12,
    cpu: 18,
    memory: 31,
    port: 8004,
    version: "v1.1.0",
    dependencies: [],
    lastChecked: "Just now",
  },
];

export const DEMO_MONITORING_SOURCES = {
  prometheus: {
    status: "Connected" as const,
    targetCount: 4,
    healthyTargets: 3,
    url: "http://localhost:9090",
  },
  cloudwatch: {
    status: "Connected" as const,
    enabled: true,
    region: "us-east-1",
    available: true,
    namespace: "AWS/ApplicationSignals",
  },
};

export const DEMO_TIMESERIES_DATA = [
  {
    timestamp: "2026-09-21T10:00:00Z",
    time: "10:00",
    requestRate: 1200,
    errorRate: 0.05,
    p95Latency: 28,
    p99Latency: 65,
    cpuUtilization: 32,
    memoryUtilization: 48,
  },
  {
    timestamp: "2026-09-21T10:15:00Z",
    time: "10:15",
    requestRate: 1260,
    errorRate: 0.04,
    p95Latency: 29,
    p99Latency: 68,
    cpuUtilization: 34,
    memoryUtilization: 49,
  },
  {
    timestamp: "2026-09-21T10:30:00Z",
    time: "10:30",
    requestRate: 1350,
    errorRate: 0.08,
    p95Latency: 35,
    p99Latency: 75,
    cpuUtilization: 38,
    memoryUtilization: 52,
  },
  {
    timestamp: "2026-09-21T10:45:00Z",
    time: "10:45",
    requestRate: 1410,
    errorRate: 0.15,
    p95Latency: 48,
    p99Latency: 110,
    cpuUtilization: 42,
    memoryUtilization: 55,
  },
  {
    timestamp: "2026-09-21T11:00:00Z",
    time: "11:00",
    requestRate: 1450,
    errorRate: 0.65,
    p95Latency: 112,
    p99Latency: 320,
    cpuUtilization: 62,
    memoryUtilization: 68,
  },
  {
    timestamp: "2026-09-21T11:15:00Z",
    time: "11:15",
    requestRate: 1480,
    errorRate: 1.42,
    p95Latency: 175,
    p99Latency: 540,
    cpuUtilization: 78,
    memoryUtilization: 79,
  },
  {
    timestamp: "2026-09-21T11:30:00Z",
    time: "11:30",
    requestRate: 1420,
    errorRate: 1.08,
    p95Latency: 145,
    p99Latency: 480,
    cpuUtilization: 68,
    memoryUtilization: 73,
  },
];

