"""Generate the dataset quality report (STEP 8).

Reports row/column counts, missing values, services, sources, timestamp
range, label/anomaly-type distributions, duplicates, invalid values, per
feature min/max/mean/median/std, and split statistics when splits exist.

Usage::

    python scripts/dataset_report.py [--in PATH] [--out PATH]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from dataset.schema import NUMERIC_COLUMNS
from dataset.validation import find_duplicate_rows, missing_value_report
from scripts.split_dataset import default_input_path

NUMERIC_SUMMARY_COLUMNS = tuple(
    col for col in NUMERIC_COLUMNS if col not in ("anomaly_label",)
)


def describe_frame(frame: pd.DataFrame) -> dict:
    """Build the quality report for one feature table."""
    numeric = frame.select_dtypes(include="number")
    summary: dict = {
        "row_count": len(frame),
        "column_count": len(frame.columns),
        "columns": list(frame.columns),
        "missing_value_counts": missing_value_report(frame),
        "unique_services": sorted(str(v) for v in frame["service_name"].dropna().unique())
        if "service_name" in frame
        else [],
        "unique_sources": sorted(str(v) for v in frame["source"].dropna().unique())
        if "source" in frame
        else [],
        "duplicate_count": len(find_duplicate_rows(frame)),
    }
    if "timestamp" in frame and len(frame):
        stamps = pd.to_datetime(frame["timestamp"], utc=True)
        summary["timestamp_start"] = str(stamps.min())
        summary["timestamp_end"] = str(stamps.max())
    if "anomaly_label" in frame:
        labels = frame["anomaly_label"].dropna()
        normal = int((labels == 0).sum())
        anomalous = int((labels == 1).sum())
        total = normal + anomalous
        summary["label_distribution"] = {
            "normal": normal,
            "anomalous": anomalous,
            "normal_percentage": round(normal / total * 100, 2) if total else 0.0,
            "anomalous_percentage": round(anomalous / total * 100, 2)
            if total
            else 0.0,
        }
    if "anomaly_type" in frame:
        summary["anomaly_type_distribution"] = {
            str(k): int(v)
            for k, v in frame["anomaly_type"].value_counts(dropna=False).items()
        }
    features: dict = {}
    for column in NUMERIC_SUMMARY_COLUMNS:
        if column not in numeric:
            continue
        series = numeric[column].dropna()
        if series.empty:
            features[column] = {"count": 0}
            continue
        features[column] = {
            "count": int(series.count()),
            "minimum": float(series.min()),
            "maximum": float(series.max()),
            "mean": float(series.mean()),
            "median": float(series.median()),
            "standard_deviation": float(series.std(ddof=0)),
        }
    summary["feature_statistics"] = features
    return summary


def split_statistics(root: str) -> dict:
    """Summarize stored splits when present (row counts + label splits)."""
    stats: dict = {}
    for name in ("train", "validation", "test"):
        path = os.path.join(root, "dataset", "splits", name, "dataset.csv")
        if not os.path.exists(path):
            continue
        frame = pd.read_csv(path)
        entry: dict = {"rows": len(frame)}
        if "anomaly_label" in frame:
            entry["normal"] = int((frame["anomaly_label"] == 0).sum())
            entry["anomalous"] = int((frame["anomaly_label"] == 1).sum())
        stats[name] = entry
    metadata_path = os.path.join(root, "dataset", "metadata", "dataset_split.json")
    if os.path.exists(metadata_path):
        with open(metadata_path, encoding="utf-8") as handle:
            stats["metadata"] = json.load(handle)
    return stats


def main(argv: list[str] | None = None) -> int:
    """Entry point: describe the feature table and stored splits."""
    parser = argparse.ArgumentParser(description="Dataset quality report")
    parser.add_argument("--in", dest="input", default=None, help="Feature CSV path")
    parser.add_argument("--out", dest="output", default=None, help="Report JSON path")
    args = parser.parse_args(argv)

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = args.input or default_input_path()
    if input_path is None:
        print("no processed feature table found under dataset/processed/")
        return 1
    report = describe_frame(pd.read_csv(input_path))
    report["split_statistics"] = split_statistics(root)
    output_path = args.output or os.path.join(
        root, "dataset", "metadata", "dataset_report.json"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
    print(f"report for {report['row_count']} rows -> {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())