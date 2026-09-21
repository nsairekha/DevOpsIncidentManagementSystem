# Prometheus Metrics (STEP 5)

## 1. Why Prometheus is used

The four microservices emit real-time numbers about their own activity
(request counts, latencies, errors, dependency calls). Prometheus scrapes
those numbers every 5 s, stores them as time series, and answers aggregate
questions ("what is the 5xx rate?", "what is P95 latency?") with PromQL.
Detailed per-request context stays in the structured JSON logs, keyed by the
same `X-Request-ID` — metrics for aggregates, logs for individual traces.

## 2. Prometheus architecture

```text
                  Prometheus (:9090)
                       |
          +------------+------------+
          |            |            |
          v            v            v
     user-service order-service payment-service (:8001/:8002/:8003)
                       |
                       v
              notification-service (:8004)
```

Each service exposes `GET /metrics` in Prometheus text format. Prometheus
scrapes `user-service:8001`, `order-service:8002`, `payment-service:8003`,
`notification-service:8004` (Compose DNS names) every 5 s
(`monitoring/prometheus/prometheus.yml`, mounted into the official
`prom/prometheus` container on port 9090).

```text
Metrics → Prometheus (aggregates)
Detailed request context → JSON logs (per request_id)
```

## 3. Metric types

- **Counter** — cumulative events, only ever increases
  (`http_requests_total`, `orders_created_total`, `dependency_errors_total`).
- **Gauge** — point-in-time values that go up and down
  (`http_requests_in_progress`, `service_up`).
- **Histogram** — latency distributions as buckets plus `_sum`/`_count`
  (`http_request_duration_seconds`, `*_processing_duration_seconds`,
  `dependency_request_duration_seconds`). Buckets enable P50/P95/P99 via
  `histogram_quantile()` — never a pre-computed static percentile.

## 4. All important metrics

Common HTTP (every service, `service` label identifies the source):

| Metric | Type | Labels |
|---|---|---|
| `http_requests_total` | Counter | service, method, endpoint, status_code |
| `http_request_duration_seconds` (+`_bucket/_sum/_count`) | Histogram | service, method, endpoint |
| `http_requests_in_progress` | Gauge | service, method |
| `http_request_errors_total` | Counter (4xx/5xx only) | service, method, endpoint, status_code |
| `service_up` | Gauge (1 = healthy) | service |

Process (real values from the running process on Linux):

| Metric | Type |
|---|---|
| `process_cpu_seconds_total` | Counter |
| `process_resident_memory_bytes` | Gauge |

Application (per service, cumulative → Counter; durations → Histogram):

- user-service: `user_requests_total`, `user_lookup_errors_total`
- order-service: `orders_created_total`, `orders_failed_total`,
  `order_processing_duration_seconds`,
  `payment_dependency_requests_total`, `payment_dependency_errors_total`,
  `notification_dependency_requests_total`, `notification_dependency_errors_total`
- payment-service: `payments_total`, `payments_success_total`,
  `payments_failed_total` (0 while the simulation never fails — a truthful
  zero, not a fabricated value), `payment_processing_duration_seconds`
- notification-service: `notifications_total`, `notifications_success_total`,
  `notifications_failed_total` (same note), `notification_processing_duration_seconds`

Dependency (order → payment/notification, §6 design):

| Metric | Labels |
|---|---|
| `dependency_requests_total` | source_service, target_service, endpoint |
| `dependency_request_duration_seconds` (+buckets) | source_service, target_service, endpoint |
| `dependency_errors_total` | source_service, target_service, endpoint |

## 5. Metric labels

`service` / `source_service` / `target_service` locate the series;
`method`, `endpoint`, `status_code` slice HTTP behavior. `endpoint` always
uses the **normalized route template** (`/api/v1/users/{user_id}`), resolved
after routing; requests matching no route are labelled `endpoint="unmatched"`.

## 6. Avoiding high-cardinality labels

IDs that are unbounded per request — `request_id`, `user_id`, `order_id`,
`payment_id`, `notification_id` — are **never** metric labels (each distinct
value would create a new time series and exhaust Prometheus). They remain in
the JSON logs, where the same `X-Request-ID` correlates a trace across
services for future AI-based RCA.

## 7. Request rate

Rates are **derived by Prometheus from counters**, never stored:

```promql
# 1-minute request rate (per service)
sum(rate(http_requests_total[1m])) by (service)

# 5-minute request rate (per service)
sum(rate(http_requests_total[5m])) by (service)

# total requests
sum(http_requests_total)
```

## 8. Error rate

```promql
# 5xx share of traffic (global 5-minute error rate)
sum(rate(http_requests_total{status_code=~"5.."}[5m]))
/
sum(rate(http_requests_total[5m]))

# 4xx requests (client errors)
sum(rate(http_requests_total{status_code=~"4.."}[5m])) by (service)

# application-level failures
sum(rate(orders_failed_total[5m]))
sum(rate(dependency_errors_total[5m])) by (target_service)
```

No percentage is hard-coded anywhere; Prometheus computes the ratio at query
time.

## 9. P50/P95/P99 latency

```promql
# P50 HTTP latency per endpoint
histogram_quantile(0.5, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service, endpoint))

# P95 HTTP latency per endpoint
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service, endpoint))

# P99 HTTP latency per endpoint
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service, endpoint))

# payment processing latency P95 (application histogram)
histogram_quantile(0.95, sum(rate(payment_processing_duration_seconds_bucket[5m])) by (le))

# order → payment dependency latency P95
histogram_quantile(0.95, sum(rate(dependency_request_duration_seconds_bucket{target_service="payment-service"}[5m])) by (le))
```

## 10. Service availability

- `service_up{service="..."}` is set to `1` by each service at startup
  (1 = healthy, 0 = unhealthy).
- Independently, Prometheus' own scrape health (`up{job="..."}`) shows
  whether each target answers. Both are visible on the Targets page; either
  dropping to 0 fires the availability signal. `/health` keeps working as the
  container-level probe.

## 11. Dependency metrics

Recorded by order-service around every downstream HTTP call (count + latency
+ errors, labelled `source_service="order-service"`,
`target_service="payment-service"|"notification-service"`,
`endpoint="/api/v1/payments"|"/api/v1/notifications"`). They power the
distributed RCA of later steps, e.g. "which dependency slowed order
creation?":

```promql
# payment dependency request volume and failure count
sum(dependency_requests_total{target_service="payment-service"})
sum(dependency_errors_total{target_service="payment-service"})

# notification dependency latency P95
histogram_quantile(0.95, sum(rate(dependency_request_duration_seconds_bucket{target_service="notification-service"}[5m])) by (le))
```

## 12. Example PromQL queries

```promql
sum(http_requests_total)                                                  # 1. total HTTP requests
sum(rate(http_requests_total[5m])) by (service)                           # 2. request rate
sum(http_requests_total{status_code=~"4.."})                              # 3. 4xx requests
sum(http_requests_total{status_code=~"5.."})                              # 4. 5xx requests
sum(rate(http_requests_total{status_code=~"5.."}[5m]))                    # 5. error rate (numerator)
/ sum(rate(http_requests_total[5m]))
histogram_quantile(0.5,  sum(rate(http_request_duration_seconds_bucket[5m])) by (le))  # 6. P50
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))  # 7. P95
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))  # 8. P99
sum(http_requests_in_progress)                                            # 9. in-flight
sum(orders_created_total)                                                 # 10. orders created
sum(payments_success_total)                                               # 11. successful payments
sum(payments_failed_total)                                                # 12. failed payments
sum(notification_dependency_errors_total)                                # 13. notification failures (order view)
histogram_quantile(0.95, sum(rate(dependency_request_duration_seconds_bucket{target_service="payment-service"}[5m])) by (le))  # 14. payment dependency latency
histogram_quantile(0.95, sum(rate(dependency_request_duration_seconds_bucket{target_service="notification-service"}[5m])) by (le))  # 15. notification dependency latency
```

## 13. How to access Prometheus

- UI: <http://localhost:9090> (Graphs + Status → Targets; all four jobs
  should show UP).
- API: `curl 'http://localhost:9090/api/v1/query?query=sum(http_requests_total)'`.

## 14. How to generate test traffic

```bash
curl http://localhost:8001/health
curl http://localhost:8001/api/v1/users/1
curl http://localhost:8001/api/v1/users/999          # 404 → error counters
curl -X POST http://localhost:8002/api/v1/orders \
  -H 'Content-Type: application/json' \
  -d '{"user_id":1,"product":"Cloud Monitoring Subscription","quantity":1,"amount":999.0}'
curl http://localhost:8002/api/v1/orders/9999        # 404
```

## 15. Latency experiment

Baseline payment latency, then inject a deterministic 500 ms delay and
re-measure — Prometheus must show the increase in both
`payment_processing_duration_seconds` and the order-service
`dependency_request_duration_seconds{target_service="payment-service"}`:

```bash
PAYMENT_SIMULATED_LATENCY_MS=500 docker compose up -d payment-service
# ... generate payment traffic ...
histogram_quantile(0.95, sum(rate(payment_processing_duration_seconds_bucket[5m])) by (le))
PAYMENT_SIMULATED_LATENCY_MS=0 docker compose up -d payment-service
```

(This is called a latency *change*, not an anomaly — detection comes later.)

## 16. Failure experiment

```bash
docker compose stop payment-service
# ... send an order → 503 payment_service_unavailable ...
# Prometheus: dependency_errors_total rises, 5xx rate rises, order-service stays up
docker compose start payment-service
# ... traffic recovers, error rates decay ...
```

Repeat with `notification-service` (order degrades to
`notification_status: failed`, payment stays successful).

> Scope note: AWS CloudWatch, ML/baselines, AI agents/RCA, blockchain,
> Kubernetes, Grafana, and the dashboard are explicitly out of scope for this
> step.
