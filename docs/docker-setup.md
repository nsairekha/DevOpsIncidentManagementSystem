# Docker Setup (STEP 4)

Containerize and run the four distributed microservices with Docker Compose.
No databases, queues, Prometheus, or other infrastructure is involved in this
step — only the existing services in lightweight Python images.

## Architecture

```text
                    Docker Network (observability-network, bridge)
                         |
              +----------+----------+
              |                     |
         user-service         order-service (:8002)
          (:8001)                   |
                         +-----------+-----------+
                         |                       |
                         v                       v
                  payment-service      notification-service
                       (:8003)                (:8004)
```

`user-service` is standalone. `order-service` calls payment/notification over
the internal network using Compose DNS names (`http://payment-service:8003`,
`http://notification-service:8004`) — never `localhost`.

## 1. Docker prerequisites

- Docker Engine 24+ with the Compose v2 plugin (`docker compose version`).
- On macOS: Docker Desktop running (`docker info` must show a server version).
- ~2 GB free disk (four slim Python images share base layers).

## 2. Building the images

From the repository root:

```bash
docker compose build
```

Or build one service directly (context must stay the repository root):

```bash
docker build -f services/order_service/Dockerfile -t observability-order-service .
```

Images created: `observability-user-service`, `observability-order-service`,
`observability-payment-service`, `observability-notification-service`
(`:latest`). Each image runs as non-root `appuser` and ships only its
`requirements.txt` deps plus `services/common` and its own package.

## 3. Starting the system

```bash
docker compose up --build -d
```

`order-service` waits for payment/notification to report healthy before
starting (`depends_on` with `service_healthy`).

## 4. Stopping the system

```bash
docker compose down
```

(`docker compose stop <service>` / `docker compose start <service>` pause and
resume single services for failure drills — data is in-memory, so stopped
services lose their recorded orders/payments/notifications.)

## 5. Viewing logs

```bash
docker compose logs                     # all services (structured JSON lines)
docker compose logs order-service
docker compose logs payment-service
docker compose logs notification-service
docker compose logs -f order-service    # follow mode
```

No centralized logging is introduced: every request still logs one JSON line
with `timestamp`, `service`, `method`, `endpoint`, `status_code`,
`request_id`, and `response_time_ms`.

## 6. Checking service health

```bash
docker compose ps                       # container + health status
curl http://localhost:8001/health       # user-service
curl http://localhost:8002/health       # order-service
curl http://localhost:8003/health       # payment-service
curl http://localhost:8004/health       # notification-service
```

Each container also self-checks `/health` every 15 s (HEALTHCHECK).

## 7. Service ports

Host ↔ container mappings are 1:1 with local development:

| Service | Host port | Container port |
|---|---|---|
| user-service | 8001 | 8001 |
| order-service | 8002 | 8002 |
| payment-service | 8003 | 8003 |
| notification-service | 8004 | 8004 |

## 8. Docker network

All services share `observability-network` (bridge). Inspect it with:

```bash
docker network inspect ai-cloud-observability_observability-network
```

## 9. Internal service URLs

| Caller | Target | URL inside Docker |
|---|---|---|
| order-service | payment-service | `http://payment-service:8003` |
| order-service | notification-service | `http://notification-service:8004` |

Injected via `PAYMENT_SERVICE_URL` / `NOTIFICATION_SERVICE_URL` in
`docker-compose.yml`. The `localhost` defaults in code remain only for
non-Docker local development.

## 10. Example order request

```bash
curl -X POST http://localhost:8002/api/v1/orders \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: demo-1' \
  -d '{"user_id":1,"product":"Cloud Monitoring Subscription","quantity":1,"amount":999.0}'
```

Expect `201` with `payment_status: success`, `notification_status: sent`.
Confirm the trace ID in every service's logs:

```bash
docker compose logs | grep demo-1
```

## 11. Failure testing

Payment down (order-service must stay up and answer `503
payment_service_unavailable` with the request ID preserved):

```bash
docker compose stop payment-service
curl -X POST http://localhost:8002/api/v1/orders \
  -H 'Content-Type: application/json' \
  -d '{"user_id":1,"product":"Cloud Monitoring Subscription","quantity":1,"amount":999.0}'
docker compose start payment-service
```

Notification down (payment stands; order answers `201` with
`notification_status: failed`):

```bash
docker compose stop notification-service
# ... same order call ...
docker compose start notification-service
```

Latency injection (payment adds ~500 ms; deterministic, not random):

```bash
PAYMENT_SIMULATED_LATENCY_MS=500 docker compose up -d payment-service
time curl -X POST http://localhost:8003/api/v1/payments \
  -H 'Content-Type: application/json' \
  -d '{"order_id":1001,"user_id":1,"amount":999.0}'
PAYMENT_SIMULATED_LATENCY_MS=0 docker compose up -d payment-service
```

## 12. Troubleshooting common startup issues

- **Daemon not running** (`Cannot connect to the Docker daemon`): start
  Docker Desktop and wait for `docker info` to report a server version.
- **Port already in use**: stop locally-run uvicorn instances on
  8001–8004 before `docker compose up` (`lsof -ti :8001 :8002 :8003 :8004 |
  xargs kill`).
- **`order-service` waits at `waiting for healthy dependencies`**: payment or
  notification is still building/starting — watch `docker compose ps` until
  both are `healthy`.
- **Stale images after code changes**: rebuild with
  `docker compose up --build` (config-only changes need just `up -d`).
- **Settings not applied**: containers read environment from
  `docker-compose.yml`, not from `.env` (which is gitignored and excluded
  from images). Export overrides in the shell, e.g.
  `PAYMENT_SIMULATED_LATENCY_MS=500 docker compose up -d`.
- **Apple Silicon vs cloud hosts**: images build for the local architecture;
  add `--platform` flags only when deploying elsewhere (out of scope).

> Scope note: Prometheus, Grafana, AWS CloudWatch, ML/AI, blockchain,
> Kubernetes manifests, and the dashboard are explicitly out of scope for
> this step.
