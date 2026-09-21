"""Chronological dataset splitting (STEP 8).

Oldest rows → training, next period → validation, latest → independent test.
Rows are never shuffled: shuffling time-series data leaks future patterns
into training and inflates later model scores. Ratios come from the
environment (``DATASET_TRAIN_RATIO`` / ``DATASET_VALIDATION_RATIO`` /
``DATASET_TEST_RATIO``) and must sum to 1.0.
"""

import os

DEFAULT_TRAIN_RATIO = 0.70
DEFAULT_VALIDATION_RATIO = 0.15
DEFAULT_TEST_RATIO = 0.15


def split_ratios(
    train: float | None = None,
    validation: float | None = None,
    test: float | None = None,
) -> tuple[float, float, float]:
    """Resolve split ratios (explicit args beat environment beats defaults).

    Raises:
        ValueError: If the ratios do not sum to 1.0 or are not positive.
    """
    train_ratio = (
        train
        if train is not None
        else float(os.environ.get("DATASET_TRAIN_RATIO", str(DEFAULT_TRAIN_RATIO)))
    )
    validation_ratio = (
        validation
        if validation is not None
        else float(
            os.environ.get("DATASET_VALIDATION_RATIO", str(DEFAULT_VALIDATION_RATIO))
        )
    )
    test_ratio = (
        test
        if test is not None
        else float(os.environ.get("DATASET_TEST_RATIO", str(DEFAULT_TEST_RATIO)))
    )
    total = train_ratio + validation_ratio + test_ratio
    if any(ratio <= 0 for ratio in (train_ratio, validation_ratio, test_ratio)):
        raise ValueError("split ratios must all be positive")
    if abs(total - 1.0) > 1e-9:
        raise ValueError(f"split ratios must sum to 1.0, got {total}")
    return train_ratio, validation_ratio, test_ratio


def chronological_split(
    df,
    train_ratio: float | None = None,
    validation_ratio: float | None = None,
    test_ratio: float | None = None,
    timestamp_column: str = "timestamp",
):
    """Split oldest → train, middle → validation, latest → test.

    The frame is sorted by ``timestamp`` first; row counts follow the
    ratios with the remainder going to the test set, so
    ``train + validation + test == total`` always holds.
    """
    train_r, validation_r, _ = split_ratios(train_ratio, validation_ratio, test_ratio)
    ordered = df.sort_values(timestamp_column).reset_index(drop=True)
    total = len(ordered)
    train_end = int(total * train_r)
    validation_end = train_end + int(total * validation_r)
    train = ordered.iloc[:train_end].reset_index(drop=True)
    validation = ordered.iloc[train_end:validation_end].reset_index(drop=True)
    test = ordered.iloc[validation_end:].reset_index(drop=True)
    return train, validation, test


def split_with_scenario_containment(
    df,
    train_ratio: float | None = None,
    validation_ratio: float | None = None,
    test_ratio: float | None = None,
    timestamp_column: str = "timestamp",
    scenario_column: str = "scenario_id",
):
    """Chronological split with boundaries snapped to scenario edges.

    A controlled experiment window must live wholly in one split — a test
    set previewing a training scenario is leakage. After computing the
    ratio boundaries, each boundary moves forward past any scenario that
    straddles it, so counts stay exact while ratios become approximate
    (reported honestly in metadata).
    """
    train_r, validation_r, _ = split_ratios(train_ratio, validation_ratio, test_ratio)
    ordered = df.sort_values(timestamp_column).reset_index(drop=True)
    total = len(ordered)

    def _straddles(index: int) -> bool:
        if scenario_column not in ordered.columns:
            return False
        if not 0 < index < total:
            return False
        before = ordered[scenario_column].iloc[index - 1]
        after = ordered[scenario_column].iloc[index]
        return (
            before is not None
            and after is not None
            and not _is_missing(before)
            and before == after
        )

    def _snap(index: int) -> int:
        while _straddles(index):
            index += 1
        return min(index, total)

    train_end = _snap(int(total * train_r))
    validation_end = _snap(max(train_end + 1, train_end + int(total * validation_r)))
    train = ordered.iloc[:train_end].reset_index(drop=True)
    validation = ordered.iloc[train_end:validation_end].reset_index(drop=True)
    test = ordered.iloc[validation_end:].reset_index(drop=True)
    return train, validation, test


def _is_missing(value) -> bool:
    """Total missing check: None, NaN, and uncomparable sentinels count as missing."""
    if value is None:
        return True
    try:
        return bool(value != value)
    except TypeError:
        return True


def split_metadata(
    *,
    dataset_version: str,
    train,
    validation,
    test,
    train_ratio: float,
    validation_ratio: float,
    test_ratio: float,
    timestamp_column: str = "timestamp",
) -> dict:
    """Build the split metadata record (real counts, never fabricated)."""
    from datetime import datetime, timezone

    def _bounds(frame) -> tuple[str | None, str | None]:
        if frame.empty:
            return None, None
        stamps = frame[timestamp_column]
        return str(stamps.iloc[0]), str(stamps.iloc[-1])

    def _label_counts(frame) -> dict:
        labels = frame["anomaly_label"] if "anomaly_label" in frame else []
        types = frame["anomaly_type"] if "anomaly_type" in frame else []
        return {
            "normal": int((labels == 0).sum()) if len(frame) else 0,
            "anomalous": int((labels == 1).sum()) if len(frame) else 0,
            "by_type": {str(k): int(v) for k, v in types.value_counts().items()}
            if len(frame)
            else {},
        }

    train_start, train_end = _bounds(train)
    validation_start, validation_end = _bounds(validation)
    test_start, test_end = _bounds(test)
    return {
        "dataset_version": dataset_version,
        "creation_timestamp": datetime.now(timezone.utc).isoformat(),
        "total_rows": len(train) + len(validation) + len(test),
        "train_rows": len(train),
        "validation_rows": len(validation),
        "test_rows": len(test),
        "train_start": train_start,
        "train_end": train_end,
        "validation_start": validation_start,
        "validation_end": validation_end,
        "test_start": test_start,
        "test_end": test_end,
        "train_ratio": train_ratio,
        "validation_ratio": validation_ratio,
        "test_ratio": test_ratio,
        "train_labels": _label_counts(train),
        "validation_labels": _label_counts(validation),
        "test_labels": _label_counts(test),
    }