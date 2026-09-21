# User Service

The first independent microservice of the AI-Based Cloud Observability System.
It serves demo user records from an in-memory store (no database yet) and runs
independently from the main backend on its own port.

> Scope note: monitoring (Prometheus/CloudWatch), AI anomaly detection, the
> blockchain audit trail, Kubernetes manifests, and the dashboard live
> elsewhere in this repository and are **not** part of this service. They are
> implemented as separate steps.

## Purpose

- Demonstrate the distributed-service pattern: own FastAPI app, own config,
  own routers, own tests, own requirements.
- Provide `GET /api/v1/users/{user_id}` for downstream observability demos.

## Architecture

```text
services/user-service/            <- spec folder name (symlink to user_service/)
services/user_service/            <- importable Python package
├── app/
│   ├── main.py                   <- FastAPI app (port 8001)
│   ├── config.py                 <- env-based settings (no .env coupling)
│   ├── api/routes/health.py      <- GET /health
│   ├── api/routes/users.py       <- GET /api/v1/users/{user_id}
│   ├── models/user.py            <- User + HealthResponse models
│   ├── services/user_service.py  <- in-memory user store
│   └── request_logging.py        <- JSON request logs + X-Request-ID
├── tests/                        <- pytest suite
├── requirements.txt              <- standalone dependencies
└── README.md                     <- this file
```

`services/user-service` is a symlink to `services/user_service/` so the folder
keeps the spec's `user-service` name while Python imports use the valid
identifier `services.user_service`.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# standalone alternative:
pip install -r services/user_service/requirements.txt
```

## How to Run

From the repository root, with the virtual environment activated:

```bash
# Terminal 1 - main backend (port 8000)
uvicorn backend.app.main:app --reload --port 8000

# Terminal 2 - user service (port 8001)
uvicorn services.user_service.app.main:app --reload --port 8001
```

Environment overrides:

```bash
SERVICE_NAME=user-service SERVICE_VERSION=1.0.0 APP_ENV=development \
  uvicorn services.user_service.app.main:app --port 8001
```

## Available Endpoints

| Method | URL | Description |
|---|---|---|
| GET | `http://127.0.0.1:8001/health` | Health + identification (name, version, environment, UTC timestamp) |
| GET | `http://127.0.0.1:8001/api/v1/users/{user_id}` | Demo user by ID (try `1`, `2`, `3`) |

Every response carries an `X-Request-ID` header; every request is logged as a
JSON line with timestamp, service, method, endpoint, status code, request ID,
and response time.

## How to Run Tests

```bash
pytest services/user_service/tests/ -v
# or the whole repository suite:
pytest
```