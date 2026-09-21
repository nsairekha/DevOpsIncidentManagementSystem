# AWS CloudWatch Integration (STEP 6)

The system now has **two** observability sources:

```text
                    Observability System
                           |
             +-------------+-------------+
             |                           |
             v                           v
        Prometheus                  CloudWatch
             |                           |
             v                           v
   Application metrics          AWS infrastructure
   Service metrics              metrics
   Dependency metrics           EC2/resource metrics
             |                           |
             +-------------+-------------+
                           |
                           v
                  Normalized Metric
                      Records
                           |
                           v
                 Future Baseline Engine
```

## 1. Architecture

- **Prometheus** scrapes the FastAPI services (`/metrics`) for application,
  HTTP, latency, error, and dependency metrics.
- **CloudWatch** (`monitoring/cloudwatch/`) reads AWS infrastructure metrics
  through boto3 and normalizes them into `MetricRecord` — the common internal
  format a later baseline/anomaly layer will consume for both sources.
- The FastAPI backend exposes the integration at
  `GET /api/v1/cloudwatch/status` and `GET /api/v1/cloudwatch/metrics`.

## 2. Why CloudWatch is used

Prometheus sees inside our containers; it cannot see the AWS substrate
(EC2 CPU/network/disk, and later RDS/ELB/...). CloudWatch fills that gap
with the cloud provider's own resource telemetry.

## 3. Supported metrics

`CPUUtilization`, `NetworkIn`, `NetworkOut`, `NetworkPacketsIn`,
`NetworkPacketsOut`, `DiskReadBytes`, `DiskWriteBytes`, `DiskReadOps`,
`DiskWriteOps` (`SUPPORTED_METRICS` in `monitoring/cloudwatch/models.py`).
Unknown names are rejected before any AWS call.

## 4. AWS namespaces

Namespace is explicit configuration (`CLOUDWATCH_NAMESPACE`, default
`AWS/EC2`). The integration never assumes a metric exists for a resource:
empty CloudWatch responses yield empty record lists, not invented data.

## 5. Dimensions

Resource targeting uses configurable dimensions
(`CLOUDWATCH_DIMENSION_NAME=InstanceId`,
`CLOUDWATCH_DIMENSION_VALUE=<instance-id>`), overridable per request with
`?resource_id=`. No fake instance ID is hard-coded anywhere: without a
resource the API answers `400` asking for configuration.

## 6. Time windows

`CLOUDWATCH_LOOKBACK_MINUTES` (default 10) defines `[now − lookback, now]`,
always UTC, never the future (`?lookback_minutes=` overrides per request).

## 7. Statistics

`Average` (default), `Minimum`, `Maximum`, plus `Sum` and `SampleCount`,
at a 60 s period (`CLOUDWATCH_PERIOD`). CloudWatch statistics describe how
AWS aggregates raw samples inside each period — unlike Prometheus, where
aggregation (rates, quantiles) happens at query time over scraped series.
See `docs/prometheus-metrics.md` §7–§9 for the Prometheus side.

## 8. Configuration

```bash
AWS_ENABLED=false            # collection off unless explicitly enabled
AWS_REGION=ap-south-1        # visible in /status when enabled
# AWS_ACCESS_KEY_ID=         # or IAM role / ambient credentials
# AWS_SECRET_ACCESS_KEY=
# AWS_SESSION_TOKEN=
CLOUDWATCH_NAMESPACE=AWS/EC2
CLOUDWATCH_DIMENSION_NAME=InstanceId
CLOUDWATCH_DIMENSION_VALUE=
CLOUDWATCH_LOOKBACK_MINUTES=10
CLOUDWATCH_PERIOD=60
```

All variables are optional with safe defaults; see `.env.example`. The
backend Docker image sets `AWS_ENABLED=false` and takes overrides via
`docker run -e AWS_ENABLED=true -e AWS_REGION=...` (never baked in).

## 9. IAM permissions

Least-privilege read-only access. The integration only calls
`GetMetricStatistics`, so the minimum policy is:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "cloudwatch:GetMetricStatistics",
      "cloudwatch:ListMetrics"
    ],
    "Resource": "*"
  }]
}
```

(`GetMetricData` covers the batch API if a later step adopts it.)
Prefer IAM roles for EKS/EC2; never commit keys. No IAM resources are
created by this project.

## 10. Local development

With `AWS_ENABLED=false` (the default) everything runs without credentials:

```bash
curl http://localhost:8000/api/v1/cloudwatch/status
# {"enabled":false,"available":false,"message":"CloudWatch integration is disabled ..."}

curl 'http://localhost:8000/api/v1/cloudwatch/metrics?demo=true'
# 5 records with "source":"cloudwatch_demo" (never "cloudwatch")
```

## 11. Docker configuration

- Images contain **no** credentials (`.env` is gitignored and excluded from
  build contexts).
- Backend image default: `AWS_ENABLED=false`. Enable per container:

```bash
docker run -e AWS_ENABLED=true -e AWS_REGION=ap-south-1 \
  -e AWS_ACCESS_KEY_ID=... -e AWS_SECRET_ACCESS_KEY=... <backend-image>
```

- The Compose microservice stack is unaffected and starts without any AWS
  configuration.

## 12. Error handling

| Situation | Result |
|---|---|
| Disabled | `503` + "integration is disabled" (or status payload) |
| Unknown metric/statistic, no resource, bad lookback | `400` structured detail |
| Missing credentials/region, permissions, network, API errors | `502` with the AWS code (e.g. `AccessDenied`) preserved |
| Empty CloudWatch response | `200` with `count: 0` |

Nothing is silently swallowed; nothing is fabricated.

## 13. Security considerations

- `.env` is gitignored; `.env.example` holds placeholders only.
- Secrets never appear in logs (config objects are never logged), test
  output, READMEs, Dockerfiles, compose files, or committed files.
- Demo mode is namespaced `cloudwatch_demo` at the model level
  (`MetricRecord.source` pattern), so demo data cannot pose as real data.

## 14. Prometheus vs CloudWatch responsibilities

| Concern | Prometheus | CloudWatch |
|---|---|---|
| HTTP requests / latency / errors | ✅ | — |
| Service health / availability | ✅ | — |
| Service dependencies | ✅ | — |
| EC2 CPU / network / disk | — | ✅ |
| AWS resource metrics | — | ✅ |

Local Docker containers are never presented as EC2 instances; the two
sources stay separate until the future baseline engine joins them through
`MetricRecord`.

> Scope note: the baseline/anomaly engine, AI agents/RCA, blockchain,
> Kubernetes, Grafana, and the dashboard are explicitly out of scope for
> this step (pre-existing files for those areas were not touched).
