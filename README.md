# AI-Based Cloud Observability System

An AI-driven observability platform for cloud infrastructure. The system is designed to ingest telemetry from distributed microservices, apply machine learning for anomaly detection, and produce an auditable trail of every monitored event — using AI agents, Prometheus and AWS CloudWatch as planned data sources, and a blockchain-based audit trail for tamper-evident record keeping.

> **Status: project foundation only.** The application, microservices, AI agents, and integrations listed in the "Planned modules" section are **not implemented yet**.

## Planned Technology Stack

| Layer        | Technology                                              |
|--------------|---------------------------------------------------------|
| Backend API  | Python 3.11+ · FastAPI · Uvicorn · Pydantic             |
| Data / ML    | pandas · NumPy · scikit-learn · NetworkX                |
| AI Agents    | AI-agent framework for automated incident analysis      |
| Observability| Prometheus · AWS CloudWatch                             |
| Audit trail  | Blockchain-based tamper-evident audit log               |
| Deployment   | Docker · Kubernetes                                     |
| Client       | React / Next.js dashboard                               |
| Delivery     | Distributed microservices · unit testing (pytest)       |

## Planned Modules

- `backend/` — FastAPI application and API layer
- `services/` — distributed microservices
- `ai/` — AI/ML anomaly detection models and AI agents
- `monitoring/` — Prometheus and AWS CloudWatch integration
- `blockchain/` — blockchain audit trail
- `dataset/` — datasets and train/test splits
- `tests/` — unit tests and coverage
- `dashboard/` — React/Next.js dashboard
- `docker/` — container definitions
- `k8s/` — Kubernetes manifests
- `scripts/` — development and operational scripts
- `docs/` — project documentation

## Local Setup

### Prerequisites

- Python 3.11 or newer (this project is developed against Python 3.13)

### 1. Create and activate the virtual environment

```bash
python3 -m venv .venv
```

Activate it:

```bash
# macOS / Linux (zsh, bash)
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Fill in your own values in `.env` (never commit real credentials).

## How to Run

From the project root, with the virtual environment activated:

```bash
# Terminal 1 - main backend (port 8000)
uvicorn backend.app.main:app --reload --port 8000

# Terminal 2 - user microservice (port 8001, runs independently)
uvicorn services.user_service.app.main:app --reload --port 8001

# Terminals 3-5 - distributed services (STEP 3, each independent)
uvicorn services.order_service.app.main:app --reload --port 8002
uvicorn services.payment_service.app.main:app --reload --port 8003
uvicorn services.notification_service.app.main:app --reload --port 8004
```

Then open the interactive docs at <http://127.0.0.1:8000/docs> or check the
health endpoint at <http://127.0.0.1:8000/health>. The versioned API lives
under `/api/v1` (`/api/v1/health`, `/api/v1/`), and the user service answers
at <http://127.0.0.1:8001/health> and
<http://127.0.0.1:8001/api/v1/users/1>. See
`services/user-service/README.md` for the user-service details.

## How to Run with Docker

The four distributed microservices (user, order, payment, notification) run
as containers on the `observability-network` bridge network:

```bash
docker compose up --build -d   # start everything (ports 8001-8004)
docker compose ps              # container + health status
docker compose logs            # structured JSON logs from all services
docker compose down            # stop everything
```

Inside Docker, services resolve each other by Compose service name
(`http://payment-service:8003`, `http://notification-service:8004`). See
`docs/docker-setup.md` (including the architecture diagram, failure drills,
and troubleshooting) and `docs/distributed-system.md` for details.

## Observability

Two sources feed the future baseline engine through one normalized record:

- **Prometheus** — application/HTTP/latency/error/dependency metrics scraped
  from each service's `/metrics` (ports 8001–8004) into Prometheus on
  <http://localhost:9090>. See `docs/prometheus-metrics.md`.
- **AWS CloudWatch** — infrastructure metrics (`CPUUtilization`,
  `NetworkIn/Out`, …) read via boto3 and normalized into `MetricRecord`
  (`source: "cloudwatch"`). Disabled by default (`AWS_ENABLED=false`); the
  backend reports status at `GET /api/v1/cloudwatch/status` and records at
  `GET /api/v1/cloudwatch/metrics` (`?demo=true` serves clearly-marked
  `cloudwatch_demo` records). See `docs/cloudwatch.md` for configuration,
  IAM least-privilege policy, and the Prometheus-vs-CloudWatch split.

Copy `.env.example` to `.env` for local overrides (never commit secrets).

## Metric Pipeline & Baselines

Prometheus and CloudWatch observations normalize into one `MetricRecord`
shape, validate, and feed a statistical baseline engine (mean/median/P50/
P95/P99, moving averages, mean ± 3σ normal bounds with non-negative
clamping, deviations). See `docs/metric-pipeline.md`. Live surface:
`GET /api/v1/metrics`, `/api/v1/metrics/summary`, `/api/v1/baselines`,
`/api/v1/baselines/{metric_name}` (all real calculations, honest empty
responses). Offline: `python scripts/collect_metrics.py` stores
`dataset/raw/`, `python scripts/build_baselines.py` writes
`dataset/processed/baselines/`. No observation is classified here —
baselines only establish behavior for later stages.

> Current status: the FastAPI backend skeleton is implemented (health endpoint,
> config loading), as is the dataset pipeline (reproducible train/validation/test
> splits and per-signal baseline metrics), the anomaly detection core
> (z-score, IQR, and Isolation Forest detectors sharing a common interface),
> Prometheus instrumentation (a /metrics endpoint with HTTP request counters,
> latency histograms, and app metadata), an AWS CloudWatch metrics client
> (boto3-based fetching and normalisation into the internal telemetry format),
> an AI incident-analysis agent (structured findings grounded against
> baselines), a blockchain audit trail (append-only SHA-256 hash-chained
> ledger with tamper-evidence verification), a microservices scaffold
> (service base class, service registry, and event schemas), Docker
> packaging (multi-stage backend image, docker-compose stack with app +
> Prometheus, and a demo Prometheus scrape config under ``docker/prometheus``),
> Kubernetes manifests (namespace, Deployments with probes, ClusterIP
> Services, and ConfigMaps for the backend and Prometheus under ``k8s/``),
> a REST findings API (``POST /api/analyze`` runs the detector + agent
> pipeline and audits every run into the ledger; ``GET /api/audit`` exposes
> the chain and its integrity verdict), and a Next.js dashboard (under
> ``dashboard/``) that surfaces health, audit blocks, and an interactive
> anomaly analysis form proxied to the backend.

## Testing

```bash
pytest --cov=backend --cov-report=term-missing tests/
```