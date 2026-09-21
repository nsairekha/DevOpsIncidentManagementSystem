# Distributed System (STEP 3)

The project is now a realistic distributed system: four independently
deployable FastAPI microservices that communicate over HTTP. No service
imports another service's Python code at runtime.

## 1. Architecture overview

```text
Client
  |
  v
Order Service (8002)
  |
  +----> Payment Service (8003)
  |             |
  |             v
  +----> Notification Service (8004)

User Service (8001) remains independently accessible.
```

`services/common/` holds shared, dependency-free utilities (JSON request
logging with request-ID propagation, an HTTP helper, shared response models,
UTC/latency helpers). Business services depend only on `common`, never on
each other.

## 2. List of services

| Service | Package | Default port | Purpose |
|---|---|---|---|
| user-service | `services/user_service` (`user-service` symlink) | 8001 | Demo user records (in-memory) |
| order-service | `services/order_service` (`order-service` symlink) | 8002 | Order orchestration: charges via payment, notifies via notification |
| payment-service | `services/payment_service` (`payment-service` symlink) | 8003 | Simulated payment processing (no real provider) |
| notification-service | `services/notification_service` (`notification-service` symlink) | 8004 | Simulated delivery (no email/SMS provider) |

The hyphenated folders (`services/user-service`, …) are symlinks to the
importable `*_service` packages, so the spec's folder names exist while
`uvicorn services.order_service.app.main:app` remains valid Python.

## 3. Ports

user-service → **8001** · order-service → **8002** · payment-service → **8003**
· notification-service → **8004**. Each service also accepts `PORT` (and all
other settings) via environment variables.

## 4. API endpoints

Every service exposes:

- `GET /health` — `{status, service, version, environment, timestamp}` (UTC)
- `GET /api/v1/` — service identification + endpoint list
- `GET /api/v1/dependencies` — downstream HTTP dependencies (topology fragment)

Domain APIs:

- user-service: `GET /api/v1/users/{user_id}`
- order-service: `GET /api/v1/orders/{order_id}`, `POST /api/v1/orders`
- payment-service: `POST /api/v1/payments`, `GET /api/v1/payments/{payment_id}`
- notification-service: `POST /api/v1/notifications`

## 5. Service dependencies

```text
order-service ──http──> payment-service (POST /api/v1/payments)
order-service ──http──> notification-service (POST /api/v1/notifications)
payment-service ──> (none)
notification-service ──> (none)
user-service ──> (none)
```

URLs come from configuration (`PAYMENT_SERVICE_URL`,
`NOTIFICATION_SERVICE_URL`) — never hard-coded in business logic. The live
topology is queryable via each service's `/api/v1/dependencies`.

## 6. Request ID propagation

The `X-Request-ID` header propagates across the whole chain:

```text
Client --(X-Request-ID: abc-123)--> order-service
  --(X-Request-ID: abc-123)--> payment-service
  --(X-Request-ID: abc-123)--> notification-service
```

Rules: if the caller supplies an ID it is reused end to end; otherwise the
edge service generates one. Every service echoes the effective ID in its
response header and includes it in every JSON log line, so one distributed
request can later be correlated for observability and root-cause analysis.

## 7. Order → Payment → Notification flow

`POST /api/v1/orders {user_id, product, quantity, amount}`:

1. order-service records the order (`status: created`, first ID is 1001).
2. It calls `POST http://localhost:8003/api/v1/payments` (httpx, 5 s timeout).
3. payment-service simulates the charge and records it (`status: success`).
4. On success, order-service calls `POST http://localhost:8004/api/v1/notifications`
   with `"Order <id> payment successful"`.
5. notification-service records it (`status: sent`).
6. order-service returns `201` with the order enriched by `payment_id`,
   `payment_status: success`, `notification_status: sent`.

## 8. Failure handling

- **payment-service down/timeout** → order-service does NOT crash: it logs the
  dependency failure (with request ID + timing) and returns
  `503 {"error": "payment_service_unavailable", "service": "order-service",
  "request_id": ..., "timestamp": ...}`. The order is kept with
  `payment_status: failed`. A downstream 5xx (or non-`success` body) maps to
  `502 {"error": "payment_failed", ...}` instead.
- **notification-service down** → the payment stands: order-service returns
  `201` with `payment_status: success` but `notification_status: failed`,
  clearly signalling the degraded delivery, and logs the failure.
- Errors are never swallowed silently: every failure path logs and responds
  with a structured body.

## 9. Simulated latency

Each service honors `SIMULATED_LATENCY_MS` (default `0`): when set, e.g. to
`200`, the service sleeps ~200 ms per mutating request before processing.
Deterministic (not random) so latency anomalies can be reproduced on demand
for later observability experiments:

```bash
SIMULATED_LATENCY_MS=200 uvicorn services.payment_service.app.main:app --port 8003
```

## 10. Why this is a distributed system

- **Independent processes**: four codebases, four ports, four deployments;
  any one can be stopped without preventing the others from starting.
- **Network communication**: services interact only through versioned HTTP
  APIs with timeouts — partial failure is a first-class concern (§8).
- **Decentralised state**: each service owns its in-memory store; there is no
  shared database or shared import.
- **Observable interaction**: propagated request IDs plus per-service JSON
  logs and dependency endpoints expose the runtime topology, the foundation
  for tracing, RCA, and anomaly detection in later steps.

## Running the system

```bash
# from the repository root, one terminal per service:
uvicorn services.user_service.app.main:app --port 8001
uvicorn services.order_service.app.main:app --port 8002
uvicorn services.payment_service.app.main:app --port 8003
uvicorn services.notification_service.app.main:app --port 8004
```

Health sweep:

```bash
for p in 8001 8002 8003 8004; do curl -s http://localhost:$p/health; echo; done
```

End-to-end order (watch the same `X-Request-ID` flow through):

```bash
curl -s -X POST http://localhost:8002/api/v1/orders \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: demo-1' \
  -d '{"user_id":1,"product":"Cloud Monitoring Subscription","quantity":1,"amount":999.0}'
```

Failure drills: stop the payment-service and repeat the order call (expect
`503 payment_service_unavailable`); restart it, stop the
notification-service, repeat (expect `201` with
`notification_status: failed`).

Tests (no servers required — downstream HTTP is mocked):

```bash
pytest
```

## Docker preparation (no Kubernetes yet)

Each service satisfies the containerization prerequisites without any
manifests in this step:

- a clear entry point (`services/<name>_service/app/main.py:create_app()`),
- all configuration via environment variables with development defaults,
- `localhost` URLs appear only as development defaults, overridable via
  `*_SERVICE_URL` variables,
- the configured port is exposed from settings (`PORT`).

> Scope note: Prometheus, Grafana, AWS CloudWatch/boto3, ML models, anomaly
> detection, AI agents/RCA, blockchain, Kubernetes manifests, the dashboard,
> and dataset/baseline work are explicitly out of scope for this step and
> live (or will live) elsewhere in the repository.
