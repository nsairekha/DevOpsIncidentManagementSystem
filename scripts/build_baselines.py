"""Build baseline records from processed observations (STEP 7).

1. Loads MetricRecords (CSV from ``collect_metrics.py``).
2. Groups by metric identity and sorts chronologically.
3. Calculates baseline statistics per group.
4. Saves machine-readable baseline records as JSON under
   ``dataset/processed/baselines/``.

No ML labels are generated here.

Usage::

    python scripts/build_baselines.py [--in PATH] [--out PATH]
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitoring.baseline.service import BaselineService
from monitoring.models.metric import MetricRecord
from monitoring.normalization.normalizer import normalize_all
from scripts.collect_metrics import load_records_csv


def default_input_path() -> str | None:
    """Newest collected CSV under ``dataset/raw/``, if any."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = sorted(glob.glob(os.path.join(root, "dataset", "raw", "metrics_*.csv")))
    return candidates[-1] if candidates else None


def default_output_path() -> str:
    """Output path under ``dataset/processed/baselines/``."""
    from datetime import datetime, timezone

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "dataset", "processed", "baselines", f"baselines_{stamp}.json")


def build_baselines(records: list[MetricRecord]) -> list[dict]:
    """Normalize, group chronologically, and calculate one baseline per group."""
    service = BaselineService()
    return [
        baseline.model_dump(mode="json")
        for baseline in service.build_all(normalize_all(records))
    ]


def save_baselines_json(baselines: list[dict], path: str) -> None:
    """Store baseline records as JSON."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(baselines, handle, indent=2, sort_keys=True)


def main(argv: list[str] | None = None) -> int:
    """Entry point: load observations, build baselines, store JSON."""
    parser = argparse.ArgumentParser(description="Build baseline records")
    parser.add_argument("--in", dest="input", default=None, help="Input CSV path")
    parser.add_argument("--out", dest="output", default=None, help="Output JSON path")
    args = parser.parse_args(argv)

    input_path = args.input or default_input_path()
    if input_path is None:
        print("no collected observations found under dataset/raw/")
        return 1
    records = load_records_csv(input_path)
    baselines = build_baselines(records)
    output_path = args.output or default_output_path()
    save_baselines_json(baselines, output_path)
    print(f"built {len(baselines)} baselines from {len(records)} records -> {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())