"""Split a processed feature table into chronological sets (STEP 8).

1. Loads the processed dataset (CSV).
2. Validates the schema.
3. Sorts chronologically (never shuffles).
4. Removes rows missing timestamps (documented rule).
5. Calculates chronological split boundaries (70/15/15 by default).
6-8. Creates training / validation / independent-test datasets.
9. Saves each split under ``dataset/splits/{train,validation,test}/``.
10. Generates ``dataset/metadata/dataset_split.json``.

Usage::

    python scripts/split_dataset.py [--in PATH] [--version v1.0]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from dataset import splits as split_logic
from dataset.schema import validate_schema
from dataset.validation import (
    check_no_cross_split_duplicates,
    check_row_accounting,
    check_scenario_containment,
)


def default_input_path() -> str | None:
    """Newest processed feature table, if any."""
    import glob

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = sorted(
        glob.glob(os.path.join(root, "dataset", "processed", "features_*.csv"))
    )
    return candidates[-1] if candidates else None


def dataset_version() -> str:
    """Dataset version (explicit releases only, never random)."""
    return os.environ.get("DATASET_VERSION", "v1.0")


def main(argv: list[str] | None = None) -> int:
    """Entry point: validate, split chronologically, store sets + metadata."""
    parser = argparse.ArgumentParser(description="Chronological dataset split")
    parser.add_argument("--in", dest="input", default=None, help="Processed CSV path")
    parser.add_argument("--version", default=None, help="Dataset version label")
    args = parser.parse_args(argv)

    input_path = args.input or default_input_path()
    if input_path is None:
        print("no processed feature table found under dataset/processed/")
        return 1
    frame = pd.read_csv(input_path)
    issues = validate_schema(frame)
    if issues:
        print("schema issues:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    before = len(frame)
    frame = frame.dropna(subset=["timestamp"]).reset_index(drop=True)
    dropped = before - len(frame)
    if dropped:
        print(f"dropped {dropped} rows with missing timestamps")

    train_ratio, validation_ratio, test_ratio = split_logic.split_ratios()
    train, validation, test = split_logic.split_with_scenario_containment(
        frame, train_ratio, validation_ratio, test_ratio
    )

    leakage = check_no_cross_split_duplicates(train, validation, test)
    leakage += check_scenario_containment(
        {"train": train, "validation": validation, "test": test}
    )
    leakage += check_row_accounting(len(frame), train, validation, test)
    if leakage:
        print("leakage/accounting issues:")
        for issue in leakage:
            print(f"  - {issue}")
        return 1

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for name, split in (
        ("train", train),
        ("validation", validation),
        ("test", test),
    ):
        path = os.path.join(root, "dataset", "splits", name, "dataset.csv")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        split.to_csv(path, index=False)

    metadata = split_logic.split_metadata(
        dataset_version=args.version or dataset_version(),
        train=train,
        validation=validation,
        test=test,
        train_ratio=train_ratio,
        validation_ratio=validation_ratio,
        test_ratio=test_ratio,
    )
    metadata_path = os.path.join(root, "dataset", "metadata", "dataset_split.json")
    os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
    with open(metadata_path, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, sort_keys=True)

    print(
        f"split {len(frame)} rows -> train {len(train)}, validation "
        f"{len(validation)}, test {len(test)} [{metadata['dataset_version']}]"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())