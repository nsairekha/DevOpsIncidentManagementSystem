# Docker packaging

This folder contains the container-related assets for the
**AI-Based Cloud Observability System**.

## Layout

| Path | Purpose |
|---|---|
| `../Dockerfile` | Multi-stage backend image (builder venv -> slim runtime) |
| `../docker-compose.yml` | Development orchestration: backend app + Prometheus |
| `prometheus/prometheus.yml` | Prometheus scrape configuration mounted into the Prometheus container |
| `../.dockerignore` | Exclusions for the Docker build context |

## Prerequisites

- Docker (engine) with the daemon running. On macOS, start **Docker Desktop**
  and confirm it is running with `docker info`.

## Usage

Build and start the full stack (app + Prometheus):

```bash
docker compose up --build -d
```

Services:

| Service   | URL                           |
|-----------|-------------------------------|
| Backend   | http://localhost:8000         |
| Health    | http://localhost:8000/health  |
| Metrics   | http://localhost:8000/metrics |
| Prometheus| http://localhost:9090         |

Prometheus scrapes the backend every 15 seconds; open the Prometheus UI at
<http://localhost:9090> and query for example `http_requests_total` or
`app_info` to confirm ingestion.

Copy `.env.example` to `.env` to supply real configuration values:

```bash
cp .env.example .env
```

Compose reads `.env` automatically (it is optional — defaults apply without it).
Never commit `.env`; it is gitignored.

Build only the backend image:

```bash
docker build -t ai-cloud-observability .
```

Run just the backend image:

```bash
docker run --rm -p 8000:8000 ai-cloud-observability
```

Inspect the running backend's health:

```bash
curl http://localhost:8000/health
```

## Notes

- The image ships **application packages only** (`backend`, `dataset`, `ai`,
  `monitoring`, `agents`, `blockchain`, `services`); `tests/`, `docs/`,
  `dashboard/`, `k8s/`, and `data/` are excluded from the build context.
- Health status is reported through the container HEALTHCHECK, which the
  Compose service exposes to orchestrators.