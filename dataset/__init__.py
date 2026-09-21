"""Dataset pipeline: loading conventions, splits, and baseline metrics."""

from dataset.baseline import (
    SignalBaseline,
    baseline_summary,
    compute_baselines,
    compute_signal_baseline,
)
from dataset.split import DatasetSplit, train_val_test_split

__all__ = [
    "DatasetSplit",
    "SignalBaseline",
    "train_val_test_split",
    "compute_baselines",
    "compute_signal_baseline",
    "baseline_summary",
]