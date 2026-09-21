# Unified Metric Pipeline & Baseline Engine (STEP 7)

Prometheus and CloudWatch observations flow through one pipeline into
statistical baselines. Later stages (dataset generation → splitting →
anomaly detection → AI agents → RCA) consume these outputs; this step
builds no ML and classifies nothing.

```text
Prometheus ───────┐
                   │
                   ▼
             Metric Collector
                   │
CloudWatch ────────┘
                   │
                   ▼
              Normalizer
                   │
                   ▼
             MetricRecord
                   │
                   ▼
             Data Validator
                   │
                   ▼
             Baseline Engine
                   │
                   ▼
             BaselineRecord
```

## 1. Prometheus source

`monitoring/pipeline/collector.py::PrometheusCollector` queries the
Prometheus HTTP API (`/api/v1/query` instant vectors,
`/api/v1/query_range` matrices) and converts results into `MetricRecord`
(`source="prometheus"`, service from the `service`/`job` label).

## 2. CloudWatch source

`monitoring/pipeline/collector.py::CloudWatchCollector` delegates to the
STEP 6 `CloudWatchService` (boto3 stays behind that boundary) and converts
records with `source="cloudwatch"` preserved (`cloudwatch_demo` stays demo).

## 3. Metric normalization

`monitoring/normalization/`: `prometheus.py` (vectors/matrices),
`cloudwatch.py` (records/datapoints), `normalizer.py` (canonical names,
`normalize_all`, `deduplicate`). Raw names map via `CANONICAL_NAMES`
(§5 of the step spec); unmapped names pass through unchanged.

## 4. MetricRecord

`monitoring/models/metric.py`. Fields: `timestamp` (tz-aware UTC),
`source` (prometheus|cloudwatch|cloudwatch_demo — never lost),
`service_name?`, `metric_name` (canonical), `value`, `unit?`,
`resource_id?`, `labels{}`, `metadata{}`. `identity()` groups series by
(source, service, metric, resource, labels).

## 5. Metric registry

`monitoring/pipeline/registry.py`: 30 `MetricDefinition` entries (name,
description, unit, source, type, aggregation, higher/lower_is_worse).
`has_source=false` marks names with no live source yet
(`memory_utilization`, `restart_count`, …) — registered for later, never
claimed present. The registry is metadata for the future AI/ML pipeline,
never an anomaly decider.

## 6. Data validation

`monitoring/validation/validators.py`: per-record checks (datetime
timestamps, finite numeric values, known sources, non-empty names) plus
series checks (chronological ordering, exact duplicates). Missing values
are reported and excluded downstream — never zero-filled, which would
corrupt baselines. All issues carry check names, messages, metric, index.

## 7. Baseline calculation

`monitoring/baseline/calculator.py` (pure functions) +
`service.py` (`BaselineConfig` from `BASELINE_ROLLING_WINDOW=20` /
`BASELINE_STDDEV_MULTIPLIER=3`, grouping oldest-first, one
`BaselineRecord` per identity).

## 8. Mean

Arithmetic mean (`statistics.fmean`) over cleaned observations.

## 9. Median

Middle value (`statistics.median`); robust center alongside the mean.

## 10. Standard deviation

Population std (`statistics.pstdev`; 0.0 for single observations, never
meaningless noise).

## 11. P50

`numpy.percentile(..., 50)` with linear interpolation.

## 12. P95

`numpy.percentile(..., 95)` — the latency SLO workhorse.

## 13. P99

`numpy.percentile(..., 99)` — tail behavior the mean hides.

Mean vs P95/P99: averages collapse the distribution; percentiles expose
tails. Latency SLOs use P95/P99 precisely because a good mean can hide a
terrible tail.

## 14. Moving average

Mean of the latest N observations (N = `BASELINE_ROLLING_WINDOW`),
tracking recent level rather than all-time history.

## 15. Rolling standard deviation

Std over the same trailing window — recent volatility, complementing the
all-time `standard_deviation`.

## 16. Normal bounds

Default `mean ± 3 × standard deviation` (multiplier configurable).
Clamping: when every observation is non-negative (`minimum >= 0`), the
lower bound floors at 0 — utilizations, byte counts, and latencies cannot
be negative, so a negative bound would be an invalid range. Values outside
are **baseline deviations**, not anomalies (no classification in this step).

## 17. Deviation percentage

`deviation_from_mean = current − mean`;
`deviation_percentage = ((current − mean) / mean) × 100`, with a zero mean
safely yielding 0.0 % (no division-by-zero; relative deviation is
undefined without a baseline level).

## 18. Missing data handling

`None`/`NaN` observations are dropped before every calculation; empty or
all-missing series raise `ValueError` instead of returning fabricated
zeros. Groups without usable values are skipped by `build_all`.

## 19. Time-series ordering

Groups sort oldest-first before rolling statistics, moving averages, and
`current_value` (always the latest observation). Order is never shuffled.

## 20. Storage format

- `dataset/raw/metrics_<ts>.csv` — collected observations (flat columns,
  labels/metadata as JSON); written by `scripts/collect_metrics.py`.
- `dataset/processed/baselines/baselines_<ts>.json` — machine-readable
  baseline records; written by `scripts/build_baselines.py`.
- Both are generated artifacts (gitignored, `.gitkeep` dirs committed);
  the design allows a database replacement later. No secrets stored.

## 21. Future use by anomaly detection

`BaselineRecord` (per-identity mean/median/bounds/percentiles/deviations)
is the exact input the dataset-generation → splitting → anomaly-detection
→ agent → RCA chain will consume. Nothing here labels data; it only
establishes statistical behavior.

Backend surface: `GET /api/v1/metrics`, `/api/v1/metrics/summary`,
`/api/v1/baselines`, `/api/v1/baselines/{metric_name}` — all live
calculations with honest empty responses. Collection scripts:
`python scripts/collect_metrics.py --help`,
`python scripts/build_baselines.py --help`.

> Scope note: dataset generation/splitting, ML anomaly detection, AI
> agents/RCA, blockchain, Kubernetes, Grafana, and the dashboard are
> explicitly out of scope (pre-existing files for those areas untouched).
