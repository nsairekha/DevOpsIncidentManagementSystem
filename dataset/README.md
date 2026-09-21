# Observability Dataset (STEP 8)

## 1. Dataset purpose

Tabular time-series observations from the distributed system for the future
AI/ML chain: dataset generation → splitting → anomaly detection → AI agents
→ RCA. This step creates data, labels, features, splits, and validation —
no models, no inference, no anomaly classification.

## 2. Schema

`dataset/schema.py::SCHEMA_COLUMNS` (27 required columns): `timestamp`,
`service_name`, `source`, `cpu_usage`, `memory_usage`, `disk_usage`,
`network_in/out`, `request_rate`, `throughput`, `latency_avg/p50/p95/p99`,
`error_rate`, `http_4xx/5xx`, `availability`, `restart_count`,
`timeout_count`, `retry_count`, `dependency_request_count`,
`dependency_latency`, `dependency_error_rate`, `cloudwatch_metrics`,
`anomaly_label`, `anomaly_type` — plus optional `scenario_*` provenance and
`baseline_*` causal columns.

## 3. Feature definitions

See `dataset/feature_engineering.py` docstring. In short: resource/network
fields are last-values per (service, 60 s bin); latency fields aggregate
bin samples (mean + quantiles); `request_rate`/`throughput` derive from
counter diffs (throughput mirrors request_rate — per-status splits are not
collected yet); `dependency_error_rate` divides error/request diffs;
`availability` mirrors `up`; `cloudwatch_metrics` counts CloudWatch
observations per bin. Baseline columns use causal expanding statistics on
latency (else request_rate).

## 4. Label definitions

`anomaly_label`: `0` = normal, `1` = anomalous. Labels come **only** from
recorded controlled-experiment windows (`dataset/labeling.py`), never from
baselines or statistics.

## 5. Anomaly types

Controlled vocabulary (`dataset/schema.py::ANOMALY_TYPES`): `normal`,
`cpu_anomaly`, `memory_anomaly`, `latency_anomaly`, `error_rate_anomaly`,
`traffic_anomaly`, `service_failure`, `dependency_failure`,
`cascading_failure`, `resource_exhaustion`. No free text.

## 6. Data sources

Prometheus instant/range queries (application/HTTP/dependency metrics) via
`scripts/collect_metrics.py`, and CloudWatch via `CloudWatchService` when
enabled (disabled by default; empty when unavailable — never invented).
Every row keeps its `source`.

## 7. Collection process

```bash
python scripts/collect_metrics.py --prometheus-url http://localhost:9090
# → dataset/raw/metrics_<ts>.csv (raw observations, never overwritten later)
python scripts/build_baselines.py  # STEP 7 baselines (separate concern)
```

Feature tables are built in-memory (`build_feature_table`) or stored under
`dataset/processed/features_<ts>.csv` for splitting.

## 8. Controlled experiments

`dataset/experiments.py`: `Scenario` records (id, type, window, affected
services, executed flag). Actually executed windows are listed in
`dataset/metadata/scenarios.json`; CPU/memory stress is interface-only
(`resource_stress_plan`) with host safeguards documented — no measurements
fabricated. Labeling applies only inside recorded windows.

## 9. Train/validation/test split

`scripts/split_dataset.py`: schema-validate → drop timestamp-less rows →
chronological 70/15/15 (env-overridable, sum validated) → oldest train,
latest test → `dataset/splits/{train,validation,test}/dataset.csv` +
`dataset/metadata/dataset_split.json` (version, bounds, ratios, label/type
counts — all real). Split boundaries **snap forward past straddling
scenario windows** (`split_with_scenario_containment`) so no experiment
lands in two splits; ratios become approximate and metadata reports the
real counts.

## 10. Leakage prevention

`dataset/validation.py`: no exact-duplicate rows across splits; no
`scenario_id` spanning splits (windows wholly contained); row accounting
`train + validation + test == total`. Coinciding timestamps across splits
are legitimate for simultaneous multi-service observations — only full-row
duplicates are rejected.

## 11. Missing data

`None`/`NaN` preserved end to end (reported in `dataset_report.json`,
never zero-filled). Counter resets yield NaN rates. Unavailable features
stay NaN with the reason documented (§3).

## 12. Dataset versioning

`DATASET_VERSION` (default `v1.0`), stored in split metadata. Bump the
version (new explicit release, never random) after changing schema,
features, labeling rules, or collection methodology — and document what
changed.

## 13. Limitations

- Instant-query collection gives one observation per series per run; depth
  comes from repeated collection, not from one snapshot.
- `throughput` ≈ `request_rate`; `error_rate`/`http_4xx/5xx` and
  restart/timeout/retry counters have no STEP 8 source (NaN).
- CPU/memory anomaly rows do not exist yet (interface only).
- No model metrics (accuracy/precision/…) exist or are reported — later step.

Data provenance key:

- **REAL OBSERVATIONS** — `dataset/raw/` collected from the live stack.
- **CONTROLLED EXPERIMENT DATA** — rows with `anomaly_label=1` inside a
  registered scenario window in `dataset/metadata/scenarios.json`.
- **SYNTHETIC TEST FIXTURES** — `tests/fixtures/` + `dataset/fixtures/`,
  deterministic, unit-test only, never measurements.
