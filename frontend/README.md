# AI Cloud Observability - Frontend Dashboard

A high-performance, dark SRE-themed cloud observability dashboard for distributed microservices. Built with Next.js 15, TypeScript, Tailwind CSS, Recharts, and Lucide React.

## Features

- **Overview Dashboard (`/dashboard`)**:
  - 6 Core KPI cards: System Availability, Request Rate, Error Rate, P95 Latency, P99 Latency, Active Incidents
  - Real-time Cluster CPU & Memory utilization
  - 5 Time-series charts:
    - Request Rate over time
    - Error Rate over time
    - P95 / P99 Latency percentiles
    - CPU utilization over time
    - Memory utilization over time
  - Microservice health summary & Distributed topology preview
  - Recent incident & anomaly alerts
  - Prometheus and CloudWatch monitoring status
- **Service Fleet Health (`/services`)**:
  - Live health monitoring for `User Service`, `Order Service`, `Payment Service`, and `Notification Service`
  - Per-service metrics: Status (Healthy/Degraded/Down), Availability %, Throughput (req/s), Error %, P95 latency, CPU, and Memory gauges
  - Service detail inspector with downstream dependency mappings
- **Distributed Service Map (`/services` & `/dashboard`)**:
  - Visual dependency flow: `Client → Order Service → Payment Service & Notification Service`, plus `User Service`
  - Dynamic status node badges, latency, and error metrics
  - Visually glowing/pulsing degraded edge connectors showing failure propagation
- **Metrics Explorer (`/metrics`)**:
  - Dedicated time-series explorer with customizable lookback windows (15m, 1h, 6h, 24h) and per-service filtering
- **AI Anomaly Detection (`/anomalies`)**:
  - Filterable anomaly records with baseline deviation percentages (e.g. `+372%`)
  - Interactive AI Anomaly Testing Playground invoking `/api/analyze` with Z-Score, IQR, and Isolation Forest detectors
- **AI Root Cause Analysis (`/rca`)**:
  - Autonomous causal graph inference and fault localization
  - Causal failure chain: Originating fault → Cascading impact → Isolated boundary
  - Incident timeline and automated remediation playbook with one-click fix action
- **Incident Management & Triage (`/incidents`)**:
  - Comprehensive incident registry filterable by Severity (Critical, High, Medium, Low) and Status (Active, Investigating, Resolved)
  - Detail slide-over modal for triage notes, root cause explanations, and lifecycle transitions
- **Blockchain Audit Trail (`/blockchain`)**:
  - Append-only cryptographic ledger verification (`valid: true`)
  - Block explorer inspecting SHA-256 block hashes, parent hashes, event types, and timestamps
- **Responsive Navigation**:
  - Full desktop sidebar + topbar
  - Tablet collapsible sidebar
  - Mobile drawer navigation
  - Horizontally scrollable data tables

## Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Start Development Server
```bash
npm run dev
```
The dashboard will be available at [http://localhost:3000](http://localhost:3000).

### 3. Production Build
```bash
npm run build
npm run start
```

## Backend Connectivity

The frontend connects to the backend API via Next.js proxy rewrites (`/api/backend/*` → `http://127.0.0.1:8000/*`).
When the backend services are offline, the frontend automatically falls back to isolated, realistic demo data with a clear "Demo Mode" indicator, ensuring zero blank screens or broken layouts.
