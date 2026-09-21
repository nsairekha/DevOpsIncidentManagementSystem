# Dataset Pipeline (STEP 8)

```text
Observability (Prometheus + CloudWatch)
     ↓
Metric Collection (scripts/collect_metrics.py → dataset/raw/)
     ↓
Normalization (canonical MetricRecord)
     ↓
Feature Engineering (dataset/feature_engineering.py)
     ↓
Controlled Labeling (scenario windows only)
     ↓
Data Validation (schema + leakage checks)
     ↓
Chronological Split (scripts/split_dataset.py)
     ↓
Training (70%) | Validation (15%) | Independent Test (15%)
```

Quality reporting (`scripts/dataset_report.py`) covers every stage.

## Why chronological splitting

Time-series observations are autocorrelated: neighboring rows share system
state. Random shuffling would place near-duplicates of test rows into
training, letting later models memorize instead of generalize and
inflating scores. Chronological splitting (oldest → train, latest → test)
keeps the test set genuinely future-unseen, mirroring production where
models always face tomorrow's data. Ratios default to 70/15/15
(`DATASET_TRAIN_RATIO` / `DATASET_VALIDATION_RATIO` / `DATASET_TEST_RATIO`,
validated to sum to 1.0).

## Pipeline stages

1. **Metric Collection** — live Prometheus instant queries (+ CloudWatch
   when enabled) stored untouched under `dataset/raw/`.
2. **Normalization** — canonical names, source preserved.
3. **Feature Engineering** — 60 s bins per service, past-only derivations,
   NaN for unavailable signals.
4. **Controlled Labeling** — scenario windows → `anomaly_label=1` with a
   vocabulary-checked `anomaly_type`; everything else stays normal.
5. **Data Validation** — schema, duplicates, scenario containment, row
   accounting.
6. **Chronological Split** — contiguous ranges + `dataset_split.json`
   metadata (version, bounds, ratios, label/type counts).
7. **Quality report** — `dataset_report.json` (counts, missing values,
   services/sources, time range, distributions, per-feature stats).

See `dataset/README.md` for schema, features, labels, experiments,
versioning, and limitations. No ML is implemented or evaluated here.
